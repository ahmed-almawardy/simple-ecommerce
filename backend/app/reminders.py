import logging
from datetime import datetime, timedelta
from sqlalchemy import and_, or_
from .config import CART_REMINDER_AFTER_HOURS, CART_REMINDER_REPEAT_HOURS
from .database import SessionLocal
from .emailer import send_cart_reminder_email
from .models import CartItem, Product, User

logger = logging.getLogger(__name__)

def send_abandoned_cart_reminders() -> None:
    now = datetime.utcnow()
    old_enough = now - timedelta(hours=CART_REMINDER_AFTER_HOURS)
    reminder_due = now - timedelta(hours=CART_REMINDER_REPEAT_HOURS)
    db = SessionLocal()
    try:
        users = db.query(User).filter(
            User.cart_updated_at.is_not(None),
            User.cart_updated_at <= old_enough,
            or_(User.last_cart_reminder_at.is_(None), User.last_cart_reminder_at <= reminder_due),
        ).all()
        for user in users:
            cart_rows = db.query(CartItem, Product).join(Product, Product.id == CartItem.product_id).filter(
                CartItem.user_id == user.id, Product.is_active.is_(True)
            ).all()
            if not cart_rows:
                continue
            items = [{"name": product.name, "quantity": row.quantity, "price_cents": product.price_cents} for row, product in cart_rows]
            if send_cart_reminder_email(user.email, user.full_name, items):
                user.last_cart_reminder_at = now
                db.commit()
    except Exception:
        logger.exception("Abandoned-cart reminder job failed")
        db.rollback()
    finally:
        db.close()
