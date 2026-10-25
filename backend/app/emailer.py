import logging
import smtplib
from email.message import EmailMessage
from html import escape
from .config import (
    SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, SMTP_FROM_EMAIL,
    SMTP_FROM_NAME, SMTP_USE_TLS, FRONTEND_URL, CURRENCY,
)

logger = logging.getLogger(__name__)


def send_email(to_email: str, subject: str, html_body: str, text_body: str) -> bool:
    if not SMTP_HOST or not SMTP_FROM_EMAIL:
        logger.warning("SMTP is not configured; email skipped: %s -> %s", subject, to_email)
        return False
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
    msg["To"] = to_email
    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype="html")
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            if SMTP_USE_TLS:
                server.starttls()
            if SMTP_USERNAME:
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        logger.info("Email sent: %s -> %s", subject, to_email)
        return True
    except Exception:
        logger.exception("Failed to send email %s to %s", subject, to_email)
        return False


def send_welcome_email(email: str, full_name: str) -> bool:
    name = escape(full_name)
    link = f"{FRONTEND_URL}/products"
    return send_email(
        email,
        "Welcome to NOVA",
        f"<div style='font-family:Arial,sans-serif;max-width:600px;margin:auto;color:#171717'><h1>Welcome to NOVA, {name}.</h1><p>Your account is ready. Explore new-season essentials curated for better everyday living.</p><p><a href='{link}' style='display:inline-block;background:#111;color:white;padding:14px 22px;text-decoration:none'>SHOP THE STORE</a></p></div>",
        f"Welcome to NOVA, {full_name}. Your account is ready. Shop the collection: {link}",
    )


def send_payment_success_email(email: str, full_name: str, order_id: int, amount_cents: int, currency: str, items: list[dict]) -> bool:
    safe_name = escape(full_name)
    total = f"{amount_cents / 100:,.2f} {currency.upper()}"
    rows = "".join(
        f"<tr><td style='padding:8px 0;border-bottom:1px solid #eee'>{escape(str(i['name']))} × {int(i['quantity'])}</td><td style='padding:8px 0;border-bottom:1px solid #eee;text-align:right'>{(int(i['price_cents']) * int(i['quantity'])) / 100:,.2f} {currency.upper()}</td></tr>"
        for i in items
    )
    html = f"<div style='font-family:Arial,sans-serif;max-width:600px;margin:auto;color:#171717'><h1>Payment confirmed.</h1><p>Hi {safe_name}, we received your payment for order <strong>#{order_id}</strong>.</p><table style='width:100%;border-collapse:collapse'>{rows}<tr><td style='padding:14px 0;font-weight:bold'>Total paid</td><td style='padding:14px 0;text-align:right;font-weight:bold'>{total}</td></tr></table><p>Thanks for shopping with NOVA.</p><p><a href='{FRONTEND_URL}/account'>View your account</a></p></div>"
    plain_items = "\n".join(f"{i['name']} x {i['quantity']}" for i in items)
    return send_email(email, f"Payment confirmed — order #{order_id}", html, f"Hi {full_name}, payment confirmed for order #{order_id}.\n{plain_items}\nTotal paid: {total}\n{FRONTEND_URL}/account")


def send_cart_reminder_email(email: str, full_name: str, items: list[dict]) -> bool:
    safe_name = escape(full_name or "there")
    rows = "".join(
        f"<li style='margin:10px 0'>{escape(str(i['name']))} × {int(i['quantity'])} — {(int(i['price_cents']) * int(i['quantity'])) / 100:,.2f} {CURRENCY.upper()}</li>"
        for i in items
    )
    link = f"{FRONTEND_URL}/cart"
    return send_email(
        email,
        "Still thinking it over? Your cart is waiting",
        f"<div style='font-family:Arial,sans-serif;max-width:600px;margin:auto;color:#171717'><h1>Your picks are still here.</h1><p>Hi {safe_name}, you left a few things in your NOVA cart.</p><ul>{rows}</ul><p><a href='{link}' style='display:inline-block;background:#111;color:white;padding:14px 22px;text-decoration:none'>RETURN TO YOUR CART</a></p><p style='color:#777;font-size:12px'>You are receiving this because you have items in your cart. You can ignore this email if you have already checked out.</p></div>",
        f"Hi {full_name}, your cart is waiting.\n" + "\n".join(f"{i['name']} x {i['quantity']}" for i in items) + f"\nReturn to your cart: {link}",
    )
