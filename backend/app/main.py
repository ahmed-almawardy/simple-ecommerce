import logging
import hashlib
import hmac
from urllib.parse import urlencode
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Annotated

import jwt
import stripe
import httpx
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import or_
from sqlalchemy.orm import Session

from . import models
from .config import (
    AUTH_ALGORITHM, AUTH_SECRET, CORS_ORIGINS, CURRENCY, ENABLE_CART_REMINDERS,
    FRONTEND_URL, PAYMENT_PROVIDER, PUBLIC_API_URL, PAYMOB_BASE_URL, PAYMOB_SECRET_KEY,
    PAYMOB_PUBLIC_KEY, PAYMOB_HMAC_SECRET, PAYMOB_PAYMENT_METHODS, STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET,
)
from .database import Base, SessionLocal, engine, get_db
from .emailer import send_payment_success_email, send_welcome_email
from .models import CartItem, Order, OrderItem, Product, User
from .reminders import send_abandoned_cart_reminders
from .schemas import (
    AuthOut, CartAdd, CartQuantity, CheckoutInput, OrderItemOut, OrderOut,
    ProductOut, UserCreate, UserLogin, UserOut,
)
from .security import create_access_token, hash_password, verify_password

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nova-home-tech")
scheduler = BackgroundScheduler(daemon=True, timezone="UTC")
bearer_scheme = HTTPBearer()

SEED_PRODUCTS = [
    {"slug":"front-load-washer","name":"Front-Load Washing Machine","description":"A quiet, energy-conscious front-load washer with generous capacity, multiple fabric programs and a clean, modern finish. Designed to make laundry day simpler.","price_cents":4299900,"category":"Major Appliances","image_url":"https://images.unsplash.com/photo-1587785580224-ff32e30978de?auto=format&fit=crop&w=1100&q=85","is_featured":True,"stock":12},
    {"slug":"inverter-fridge","name":"Inverter Refrigerator","description":"A spacious, frost-free refrigerator with adjustable shelves, dedicated fresh-food storage and efficient cooling for a busy household.","price_cents":5899900,"category":"Major Appliances","image_url":"https://images.unsplash.com/photo-1571175443880-49e1d25b2bc5?auto=format&fit=crop&w=1100&q=85","is_featured":True,"stock":9},
    {"slug":"split-air-conditioner","name":"Inverter Split Air Conditioner","description":"A sleek split AC designed for fast, even cooling, quieter evenings and practical everyday comfort. Capacity and installation options should be confirmed before purchase.","price_cents":3799900,"category":"Major Appliances","image_url":"https://images.unsplash.com/photo-1761656630581-69a58e4e1c09?auto=format&fit=crop&w=1100&q=85","is_featured":False,"stock":14},
    {"slug":"robot-vacuum","name":"Smart Robot Vacuum","description":"A compact automated floor cleaner for everyday dust and debris, with scheduled cleaning and a low-profile design that reaches under furniture.","price_cents":1599900,"category":"Major Appliances","image_url":"https://images.unsplash.com/photo-1563453392212-326f5e854473?auto=format&fit=crop&w=1100&q=85","is_featured":True,"stock":11},
    {"slug":"espresso-machine","name":"Automatic Espresso Machine","description":"Bring café-style coffee home with programmable brewing, a compact countertop footprint and simple controls for your daily cup.","price_cents":999900,"category":"Kitchen Appliances","image_url":"https://images.unsplash.com/photo-1517668808822-9ebb02f2a0e6?auto=format&fit=crop&w=1100&q=85","is_featured":True,"stock":17},
    {"slug":"high-speed-blender","name":"High-Speed Blender","description":"A versatile countertop blender for smoothies, sauces and food preparation, with a sturdy jug and straightforward speed controls.","price_cents":459900,"category":"Kitchen Appliances","image_url":"https://images.unsplash.com/photo-1570222094114-d054a817e56b?auto=format&fit=crop&w=1100&q=85","is_featured":False,"stock":24},
    {"slug":"digital-air-fryer","name":"Digital Air Fryer","description":"A family-friendly air fryer with digital controls and preset cooking modes for convenient everyday meals using less added oil.","price_cents":599900,"category":"Kitchen Appliances","image_url":"https://images.unsplash.com/photo-1585515320310-259814833e62?auto=format&fit=crop&w=1100&q=85","is_featured":True,"stock":20},
    {"slug":"built-in-electric-oven","name":"Built-in Electric Oven","description":"A modern electric oven for everyday baking and roasting, designed to integrate neatly into a contemporary kitchen.","price_cents":1899900,"category":"Kitchen Appliances","image_url":"https://images.unsplash.com/photo-1586201375761-83865001e31c?auto=format&fit=crop&w=1100&q=85","is_featured":False,"stock":8},
    {"slug":"4k-smart-tv-65","name":"65-inch 4K Smart TV","description":"A large 4K smart television with a slim profile and an immersive screen for streaming, movies, gaming and family entertainment.","price_cents":3499900,"category":"TV & Audio","image_url":"https://images.unsplash.com/photo-1593359677879-a4bb92f829d1?auto=format&fit=crop&w=1100&q=85","is_featured":True,"stock":10},
    {"slug":"wireless-headphones","name":"Wireless Noise-Cancelling Headphones","description":"Comfortable over-ear headphones with wireless playback, immersive sound and noise control for commutes, calls and focused listening.","price_cents":799900,"category":"TV & Audio","image_url":"https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=1100&q=85","is_featured":True,"stock":26},
    {"slug":"portable-bluetooth-speaker","name":"Portable Bluetooth Speaker","description":"A compact wireless speaker for clear room-filling sound at home or outdoors, with easy pairing and a portable everyday design.","price_cents":349900,"category":"TV & Audio","image_url":"https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?auto=format&fit=crop&w=1100&q=85","is_featured":False,"stock":31},
    {"slug":"everyday-laptop","name":"Everyday Performance Laptop","description":"A clean, portable laptop for work, study and everyday browsing, built around a slim chassis and a comfortable keyboard.","price_cents":3299900,"category":"Phones & Computing","image_url":"https://images.unsplash.com/photo-1496181133206-80ce9b88a853?auto=format&fit=crop&w=1100&q=85","is_featured":True,"stock":13},
    {"slug":"flagship-smartphone","name":"Flagship Smartphone","description":"A modern smartphone with a vivid display, versatile camera system and a refined design made for everyday communication and creativity.","price_cents":2899900,"category":"Phones & Computing","image_url":"https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?auto=format&fit=crop&w=1100&q=85","is_featured":True,"stock":16},
    {"slug":"amoled-smartwatch","name":"AMOLED Smartwatch","description":"A versatile smartwatch with a bright display, activity tracking, notifications and interchangeable-style bands for work and workouts.","price_cents":699900,"category":"Watches & Wearables","image_url":"https://images.unsplash.com/photo-1546868871-7041f2a55e12?auto=format&fit=crop&w=1100&q=85","is_featured":True,"stock":22},
    {"slug":"fitness-watch","name":"Fitness Tracking Watch","description":"Track daily movement, workouts and activity goals with a lightweight wearable designed for comfortable all-day use.","price_cents":299900,"category":"Watches & Wearables","image_url":"https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=1100&q=85","is_featured":False,"stock":29},
    {"slug":"smart-home-starter-kit","name":"Smart Home Starter Kit","description":"A simple starting point for connected living, with smart lighting accessories and app-based control for selected compatible devices.","price_cents":149900,"category":"Smart Home","image_url":"https://images.unsplash.com/photo-1558002038-1055907df827?auto=format&fit=crop&w=1100&q=85","is_featured":False,"stock":35},
]


def seed_products() -> None:
    db = SessionLocal()
    try:
        # Hide products from the previous starter catalogue if an existing local DB is reused.
        retired_slugs = [
            "velocity-runner", "studio-oversized-tee", "court-classic", "training-shorts",
            "everyday-crew", "utility-duffel", "performance-cap", "daily-runner-2",
            "ribbed-tank", "crossbody-pack",
        ]
        db.query(Product).filter(Product.slug.in_(retired_slugs)).update(
            {Product.is_active: False}, synchronize_session=False
        )
        for item in SEED_PRODUCTS:
            existing = db.query(Product).filter(Product.slug == item["slug"]).first()
            if existing is None:
                db.add(Product(**item))
            else:
                for key, value in item.items():
                    setattr(existing, key, value)
                existing.is_active = True
        db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    seed_products()
    if ENABLE_CART_REMINDERS:
        if not scheduler.running:
            scheduler.add_job(send_abandoned_cart_reminders, "interval", hours=1, id="cart-reminders", replace_existing=True, max_instances=1)
            scheduler.start()
            logger.info("Abandoned cart reminder scheduler started")
    yield
    if scheduler.running:
        scheduler.shutdown(wait=False)


app = FastAPI(
    title="NOVA Home + Tech API",
    version="1.0.0",
    description="E-commerce API for the NOVA Home + Tech Nuxt storefront.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Stripe-Signature"],
)


def get_current_user(credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)], db: Session = Depends(get_db)) -> User:
    token = credentials.credentials
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Your session is invalid or has expired. Please log in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, AUTH_SECRET, algorithms=[AUTH_ALGORITHM])
        subject = payload.get("sub")
        if not subject:
            raise credentials_error
        user_id = int(subject)
    except (jwt.PyJWTError, ValueError, TypeError):
        raise credentials_error
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise credentials_error
    return user


def order_payload(db: Session, order: Order) -> dict:
    items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
    return {
        "id": order.id,
        "amount_cents": order.amount_cents,
        "currency": order.currency,
        "status": order.status,
        "shipping_name": order.shipping_name,
        "shipping_address": order.shipping_address,
        "shipping_phone": order.shipping_phone,
        "shipping_city": order.shipping_city,
        "shipping_country": order.shipping_country,
        "payment_provider": order.payment_provider,
        "created_at": order.created_at,
        "paid_at": order.paid_at,
        "items": [
            {"id": i.id, "product_id": i.product_id, "product_name": i.product_name,
             "product_slug": i.product_slug, "image_url": i.image_url,
             "price_cents": i.price_cents, "quantity": i.quantity}
            for i in items
        ],
    }


def cart_payload(db: Session, user: User) -> dict:
    rows = db.query(CartItem, Product).join(Product, Product.id == CartItem.product_id).filter(
        CartItem.user_id == user.id, Product.is_active.is_(True)
    ).all()
    items = [{"product": ProductOut.model_validate(product).model_dump(), "quantity": row.quantity} for row, product in rows]
    subtotal = sum(product.price_cents * row.quantity for row, product in rows)
    return {"items": items, "subtotal_cents": subtotal, "item_count": sum(row.quantity for row, _ in rows)}


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "nova-home-tech-api"}


@app.post("/api/auth/register", response_model=AuthOut, status_code=201)
def register(payload: UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    email = str(payload.email).strip().lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="An account with this email already exists.")
    user = User(email=email, full_name=payload.full_name.strip(), password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    background_tasks.add_task(send_welcome_email, user.email, user.full_name)
    return {"access_token": create_access_token(user.id), "user": user}


@app.post("/api/auth/login", response_model=AuthOut)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    email = str(payload.email).strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="This account is disabled.")
    return {"access_token": create_access_token(user.id), "user": user}


@app.get("/api/auth/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@app.get("/api/products", response_model=list[ProductOut])
def list_products(
    q: str | None = None,
    category: str | None = None,
    min_price: float | None = Query(default=None, ge=0),
    max_price: float | None = Query(default=None, ge=0),
    sort: str = Query(default="featured", pattern="^(featured|newest|price_asc|price_desc|name)$"),
    featured: bool | None = None,
    limit: int = Query(default=48, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(Product).filter(Product.is_active.is_(True))
    if q and q.strip():
        needle = f"%{q.strip()}%"
        query = query.filter(or_(Product.name.ilike(needle), Product.description.ilike(needle), Product.category.ilike(needle)))
    if category and category.lower() != "all":
        query = query.filter(Product.category.ilike(category.strip()))
    if min_price is not None:
        query = query.filter(Product.price_cents >= int(min_price * 100))
    if max_price is not None:
        query = query.filter(Product.price_cents <= int(max_price * 100))
    if featured is not None:
        query = query.filter(Product.is_featured.is_(featured))
    if sort == "newest":
        query = query.order_by(Product.created_at.desc())
    elif sort == "price_asc":
        query = query.order_by(Product.price_cents.asc())
    elif sort == "price_desc":
        query = query.order_by(Product.price_cents.desc())
    elif sort == "name":
        query = query.order_by(Product.name.asc())
    else:
        query = query.order_by(Product.is_featured.desc(), Product.id.asc())
    return query.offset(offset).limit(limit).all()


@app.get("/api/products/categories", response_model=list[str])
def list_categories(db: Session = Depends(get_db)):
    return [row[0] for row in db.query(Product.category).filter(Product.is_active.is_(True)).distinct().order_by(Product.category).all()]


@app.get("/api/products/{slug}", response_model=ProductOut)
def get_product(slug: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.slug == slug, Product.is_active.is_(True)).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found.")
    return product


@app.get("/api/cart")
def get_cart(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return cart_payload(db, user)


@app.post("/api/cart/items", status_code=200)
def add_cart_item(payload: CartAdd, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    product = db.get(Product, payload.product_id)
    if product is None or not product.is_active:
        raise HTTPException(status_code=404, detail="Product not found.")
    row = db.query(CartItem).filter(CartItem.user_id == user.id, CartItem.product_id == product.id).first()
    new_quantity = payload.quantity + (row.quantity if row else 0)
    if new_quantity > min(product.stock, 20):
        raise HTTPException(status_code=400, detail=f"Only {product.stock} item(s) are currently available.")
    if row:
        row.quantity = new_quantity
        row.updated_at = datetime.utcnow()
    else:
        db.add(CartItem(user_id=user.id, product_id=product.id, quantity=payload.quantity))
    user.cart_updated_at = datetime.utcnow()
    user.last_cart_reminder_at = None
    db.commit()
    return cart_payload(db, user)


@app.put("/api/cart/items/{product_id}")
def set_cart_item(product_id: int, payload: CartQuantity, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    product = db.get(Product, product_id)
    row = db.query(CartItem).filter(CartItem.user_id == user.id, CartItem.product_id == product_id).first()
    if payload.quantity == 0:
        if row:
            db.delete(row)
    else:
        if product is None or not product.is_active:
            raise HTTPException(status_code=404, detail="Product not found.")
        if payload.quantity > min(product.stock, 20):
            raise HTTPException(status_code=400, detail=f"Only {product.stock} item(s) are currently available.")
        if row:
            row.quantity = payload.quantity
            row.updated_at = datetime.utcnow()
        else:
            row = CartItem(user_id=user.id, product_id=product_id, quantity=payload.quantity)
            db.add(row)
    user.cart_updated_at = datetime.utcnow()
    user.last_cart_reminder_at = None
    db.commit()
    return cart_payload(db, user)


@app.delete("/api/cart/items/{product_id}")
def remove_cart_item(product_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.query(CartItem).filter(CartItem.user_id == user.id, CartItem.product_id == product_id).first()
    if row:
        db.delete(row)
        user.cart_updated_at = datetime.utcnow() if db.query(CartItem).filter(CartItem.user_id == user.id).count() > 0 else None
        user.last_cart_reminder_at = None
        db.commit()
    return cart_payload(db, user)


@app.get("/api/orders", response_model=list[OrderOut])
def list_orders(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    orders = db.query(Order).filter(Order.user_id == user.id).order_by(Order.created_at.desc()).all()
    return [order_payload(db, o) for o in orders]


@app.get("/api/orders/{order_id}", response_model=OrderOut)
def get_order(order_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user.id).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found.")
    return order_payload(db, order)


@app.post("/api/checkout/session")
def create_checkout_session(payload: CheckoutInput, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    provider = PAYMENT_PROVIDER
    if provider == "paymob":
        missing = []
        if not PAYMOB_SECRET_KEY: missing.append("PAYMOB_SECRET_KEY")
        if not PAYMOB_PUBLIC_KEY: missing.append("PAYMOB_PUBLIC_KEY")
        if not PAYMOB_HMAC_SECRET: missing.append("PAYMOB_HMAC_SECRET")
        if not PAYMOB_PAYMENT_METHODS: missing.append("PAYMOB_PAYMENT_METHODS (integration ID(s))")
        if not PUBLIC_API_URL.startswith("https://"):
            missing.append("PUBLIC_API_URL (a public HTTPS URL; use an HTTPS tunnel for local webhooks)")
        if missing:
            raise HTTPException(status_code=503, detail="Paymob is not fully configured. Set: " + ", ".join(missing) + ".")
        if CURRENCY.upper() != "EGP":
            raise HTTPException(status_code=503, detail="Paymob Egypt is configured for EGP in this starter. Set CURRENCY=egp.")
    elif provider == "stripe":
        if not STRIPE_SECRET_KEY or not STRIPE_WEBHOOK_SECRET:
            raise HTTPException(status_code=503, detail="Stripe is not fully configured. Set STRIPE_SECRET_KEY and STRIPE_WEBHOOK_SECRET.")
    else:
        raise HTTPException(status_code=503, detail="Unsupported PAYMENT_PROVIDER. Use paymob or stripe.")

    rows = db.query(CartItem, Product).join(Product, Product.id == CartItem.product_id).filter(
        CartItem.user_id == user.id, Product.is_active.is_(True)
    ).all()
    if not rows:
        raise HTTPException(status_code=400, detail="Your cart is empty.")
    for row, product in rows:
        if row.quantity > product.stock:
            raise HTTPException(status_code=400, detail=f"Not enough stock for {product.name}.")
    total = sum(product.price_cents * row.quantity for row, product in rows)
    order = Order(
        user_id=user.id, amount_cents=total, currency=CURRENCY, status="pending",
        shipping_name=payload.shipping_name.strip(), shipping_address=payload.shipping_address.strip(),
        shipping_phone=payload.shipping_phone.strip(), shipping_city=payload.shipping_city.strip(),
        shipping_country=payload.shipping_country.strip().upper(), payment_provider=provider,
    )
    db.add(order)
    db.flush()
    for row, product in rows:
        db.add(OrderItem(order_id=order.id, product_id=product.id, product_name=product.name,
                         product_slug=product.slug, image_url=product.image_url,
                         price_cents=product.price_cents, quantity=row.quantity))
    db.commit()
    db.refresh(order)

    try:
        if provider == "paymob":
            name_parts = payload.shipping_name.strip().split(maxsplit=1)
            first_name = name_parts[0] if name_parts else "Customer"
            last_name = name_parts[1] if len(name_parts) > 1 else "Customer"
            intention = {
                "amount": total,
                "currency": CURRENCY.upper(),
                "payment_methods": PAYMOB_PAYMENT_METHODS,
                "items": [{
                    "name": product.name,
                    "amount": product.price_cents,
                    "description": product.description[:240],
                    "quantity": row.quantity,
                } for row, product in rows],
                "billing_data": {
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": user.email,
                    "phone_number": payload.shipping_phone.strip(),
                    "street": payload.shipping_address.strip(),
                    "building": "NA",
                    "floor": "NA",
                    "apartment": "NA",
                    "city": payload.shipping_city.strip(),
                    "state": payload.shipping_city.strip(),
                    "country": payload.shipping_country.strip().upper(),
                    "postal_code": "NA",
                    "extra_description": f"NOVA order #{order.id}",
                },
                "extras": {"local_order_id": str(order.id)},
                "special_reference": str(order.id),
                "expiration": 3600,
                "notification_url": f"{PUBLIC_API_URL}/api/payments/paymob/webhook",
                "redirection_url": f"{FRONTEND_URL}/checkout/success?order_id={order.id}",
            }
            response = httpx.post(
                f"{PAYMOB_BASE_URL}/v1/intention/",
                headers={"Authorization": f"Token {PAYMOB_SECRET_KEY}", "Content-Type": "application/json"},
                json=intention,
                timeout=25.0,
            )
            if response.status_code >= 400:
                logger.error("Paymob intention failed: status=%s response=%s", response.status_code, response.text[:1000])
                raise RuntimeError("Paymob could not create a payment intention.")
            data = response.json()
            client_secret = data.get("client_secret")
            if not client_secret:
                raise RuntimeError("Paymob did not return a client secret.")
            order.provider_payment_id = str(data.get("id") or data.get("intention_order_id") or "")
            db.commit()
            checkout_url = f"{PAYMOB_BASE_URL}/unifiedcheckout/?" + urlencode({"publicKey": PAYMOB_PUBLIC_KEY, "clientSecret": client_secret})
            return {"checkout_url": checkout_url, "order_id": order.id, "provider": "paymob"}

        stripe.api_key = STRIPE_SECRET_KEY
        session = stripe.checkout.Session.create(
            mode="payment",
            payment_method_types=["card"],
            customer_email=user.email,
            client_reference_id=str(order.id),
            metadata={"order_id": str(order.id), "user_id": str(user.id)},
            line_items=[{
                "price_data": {
                    "currency": CURRENCY,
                    "product_data": {"name": product.name, "images": [product.image_url]},
                    "unit_amount": product.price_cents,
                },
                "quantity": row.quantity,
            } for row, product in rows],
            success_url=f"{FRONTEND_URL}/checkout/success?session_id={{CHECKOUT_SESSION_ID}}&order_id={order.id}",
            cancel_url=f"{FRONTEND_URL}/checkout?canceled=1",
            billing_address_collection="auto",
        )
        order.provider_payment_id = session.id
        db.commit()
        return {"checkout_url": session.url, "order_id": order.id, "provider": "stripe"}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Payment provider checkout creation failed (%s)", provider)
        order.status = "checkout_error"
        db.commit()
        raise HTTPException(status_code=502, detail="Could not start secure payment. Check the payment provider configuration and try again.") from exc


def _paymob_hmac_value(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _paymob_callback_is_valid(obj: dict, received_hmac: str) -> bool:
    if not PAYMOB_HMAC_SECRET or not received_hmac:
        return False
    order_obj = obj.get("order") or {}
    source_data = obj.get("source_data") or {}
    fields = [
        obj.get("amount_cents"), obj.get("created_at"), obj.get("currency"),
        obj.get("error_occured"), obj.get("has_parent_transaction"), obj.get("id"),
        obj.get("integration_id"), obj.get("is_3d_secure"), obj.get("is_auth"),
        obj.get("is_capture"), obj.get("is_refunded"), obj.get("is_standalone_payment"),
        obj.get("is_voided"), order_obj.get("id"), obj.get("owner"), obj.get("pending"),
        source_data.get("pan"), source_data.get("sub_type"), source_data.get("type"), obj.get("success"),
    ]
    message = "".join(_paymob_hmac_value(value) for value in fields).encode("utf-8")
    expected = hmac.new(PAYMOB_HMAC_SECRET.encode("utf-8"), message, hashlib.sha512).hexdigest()
    return hmac.compare_digest(expected.lower(), received_hmac.strip().lower())


@app.post("/api/payments/paymob/webhook")
async def paymob_webhook(request: Request, db: Session = Depends(get_db)):
    if PAYMENT_PROVIDER != "paymob":
        raise HTTPException(status_code=404, detail="Paymob is not the active payment provider.")
    if not PAYMOB_HMAC_SECRET:
        raise HTTPException(status_code=503, detail="Paymob HMAC secret is not configured.")
    try:
        callback = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid Paymob callback payload.") from exc
    obj = callback.get("obj") if isinstance(callback, dict) else None
    if not isinstance(obj, dict):
        raise HTTPException(status_code=400, detail="Missing transaction object.")
    received_hmac = request.query_params.get("hmac", "")
    if not _paymob_callback_is_valid(obj, received_hmac):
        raise HTTPException(status_code=400, detail="Invalid Paymob HMAC signature.")

    order_obj = obj.get("order") or {}
    claims = obj.get("payment_key_claims") or {}
    extras = claims.get("extra") or {}
    local_order_ref = extras.get("local_order_id") or order_obj.get("merchant_order_id")
    try:
        local_order_id = int(local_order_ref)
    except (TypeError, ValueError):
        logger.warning("Verified Paymob callback did not contain a valid local order reference")
        return {"received": True, "matched": False}
    order = db.get(Order, local_order_id)
    if order is None or order.payment_provider != "paymob":
        return {"received": True, "matched": False}

    callback_amount = obj.get("amount_cents")
    callback_currency = str(obj.get("currency") or "").lower()
    successful = obj.get("success") is True and obj.get("pending") is not True and obj.get("error_occured") is not True
    successful = successful and obj.get("is_refunded") is not True and obj.get("is_voided") is not True
    if successful and int(callback_amount or -1) == order.amount_cents and callback_currency == order.currency.lower() and order.status != "paid":
        user = db.get(User, order.user_id)
        order.status = "paid"
        order.provider_payment_id = str(obj.get("id") or order.provider_payment_id or "")
        order.paid_at = datetime.utcnow()
        items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
        email_items = [{"name": i.product_name, "quantity": i.quantity, "price_cents": i.price_cents} for i in items]
        for item in items:
            product = db.get(Product, item.product_id)
            if product:
                product.stock = max(0, product.stock - item.quantity)
        db.query(CartItem).filter(CartItem.user_id == order.user_id).delete(synchronize_session=False)
        if user:
            user.cart_updated_at = None
            user.last_cart_reminder_at = None
        db.commit()
        if user:
            send_payment_success_email(user.email, user.full_name, order.id, order.amount_cents, order.currency, email_items)
    elif successful:
        logger.warning("Paymob callback matched order %s but amount/currency did not match; order not marked paid", order.id)
    return {"received": True}


@app.post("/api/payments/webhook")
@app.post("/api/payments/stripe/webhook")
async def stripe_webhook(request: Request, stripe_signature: str | None = Header(default=None, alias="Stripe-Signature"), db: Session = Depends(get_db)):
    if PAYMENT_PROVIDER != "stripe":
        raise HTTPException(status_code=404, detail="Stripe is not the active payment provider.")
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="Stripe webhook is not configured.")
    raw_body = await request.body()
    try:
        event = stripe.Webhook.construct_event(raw_body, stripe_signature or "", STRIPE_WEBHOOK_SECRET)
    except Exception as exc:
        logger.warning("Invalid Stripe webhook signature")
        raise HTTPException(status_code=400, detail="Invalid Stripe webhook signature.") from exc

    event_type = event["type"]
    if event_type in {"checkout.session.completed", "checkout.session.async_payment_succeeded"}:
        checkout_session = event["data"]["object"]
        order_id_raw = (checkout_session.get("metadata") or {}).get("order_id") or checkout_session.get("client_reference_id")
        paid = checkout_session.get("payment_status") == "paid" or event_type == "checkout.session.async_payment_succeeded"
        if order_id_raw and paid:
            try:
                order_id = int(order_id_raw)
            except (TypeError, ValueError):
                order_id = None
            order = db.get(Order, order_id) if order_id else None
            if order and order.status != "paid":
                user = db.get(User, order.user_id)
                order.status = "paid"
                order.stripe_session_id = checkout_session.get("id") or order.stripe_session_id
                order.paid_at = datetime.now(timezone.utc).replace(tzinfo=None)
                items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
                email_items = [{"name": i.product_name, "quantity": i.quantity, "price_cents": i.price_cents} for i in items]
                for item in items:
                    product = db.get(Product, item.product_id)
                    if product:
                        product.stock = max(0, product.stock - item.quantity)
                db.query(CartItem).filter(CartItem.user_id == order.user_id).delete(synchronize_session=False)
                if user:
                    user.cart_updated_at = None
                    user.last_cart_reminder_at = None
                db.commit()
                if user:
                    send_payment_success_email(user.email, user.full_name, order.id, order.amount_cents, order.currency, email_items)
    return {"received": True}
