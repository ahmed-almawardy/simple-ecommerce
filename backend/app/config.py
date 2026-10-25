import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    return default if value is None else value.strip().lower() in {"1", "true", "yes", "on"}

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'store.db'}")
AUTH_SECRET = os.getenv("AUTH_SECRET", "dev-only-change-this-secret-before-deploying")
AUTH_ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "10080"))
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/")
CORS_ORIGINS = [x.strip() for x in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",") if x.strip()]
CURRENCY = os.getenv("CURRENCY", "egp").lower()
PAYMENT_PROVIDER = os.getenv("PAYMENT_PROVIDER", "paymob").strip().lower()
PUBLIC_API_URL = os.getenv("PUBLIC_API_URL", "http://localhost:8000").rstrip("/")
PAYMOB_BASE_URL = os.getenv("PAYMOB_BASE_URL", "https://accept.paymob.com").rstrip("/")
PAYMOB_SECRET_KEY = os.getenv("PAYMOB_SECRET_KEY", "")
PAYMOB_PUBLIC_KEY = os.getenv("PAYMOB_PUBLIC_KEY", "")
PAYMOB_HMAC_SECRET = os.getenv("PAYMOB_HMAC_SECRET", "")
PAYMOB_PAYMENT_METHODS_RAW = os.getenv("PAYMOB_PAYMENT_METHODS", "")
PAYMOB_PAYMENT_METHODS = [int(x.strip()) if x.strip().isdigit() else x.strip() for x in PAYMOB_PAYMENT_METHODS_RAW.split(",") if x.strip()]
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
ENABLE_CART_REMINDERS = env_bool("ENABLE_CART_REMINDERS", True)
CART_REMINDER_AFTER_HOURS = int(os.getenv("CART_REMINDER_AFTER_HOURS", "4"))
CART_REMINDER_REPEAT_HOURS = int(os.getenv("CART_REMINDER_REPEAT_HOURS", "24"))

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USERNAME)
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "NOVA Home + Tech")
SMTP_USE_TLS = env_bool("SMTP_USE_TLS", True)
