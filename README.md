# NOVA Home + Tech — Nuxt + FastAPI e-commerce starter

A responsive, premium home appliances and consumer electronics storefront. The demo catalogue covers washing machines, refrigerators, air conditioners, robot vacuums, kitchen appliances, smart TVs, audio, laptops, smartphones, smartwatches and smart-home products. NOVA is an original demo brand.

## Included

- **Nuxt 3 + Vue 3** storefront: landing page, featured products, category navigation, search, category/price filters, sorting, product detail pages, local guest cart, login/register, account/order history and checkout pages.
- **FastAPI backend**: product catalog, SQLAlchemy database, product seed data, user registration/login, JWT authentication, persistent carts for signed-in users, orders and stock tracking.
- **Paymob Unified Checkout (Egypt-first default)** using the Intention API and HMAC-SHA512 verified webhook; optional Stripe Checkout for businesses eligible to use Stripe.
- **Email workflows**: welcome/registration email, payment-success email and hourly abandoned-cart reminder job (defaults to remind after 4 hours, at most once every 24 hours).
- Dockerfiles and `docker-compose.yml` for a containerized local run.

The seed catalog uses remote Unsplash image URLs. Replace these with your own licensed product photography before launch.

## 1. Requirements

- Python 3.11 or 3.12 recommended
- Node.js 20.19+ or 22+
- npm
- A Paymob merchant account for Egypt (sandbox/test keys are recommended for development; Stripe is an optional alternative)
- SMTP credentials from your email provider for real email delivery

## 2. Run locally without Docker

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API creates `store.db` and inserts demo products on first start.

- API health: http://localhost:8000/api/health
- Interactive API docs: http://localhost:8000/docs

Open `backend/.env` and update `AUTH_SECRET`, Paymob credentials / public callback URL and SMTP settings before using those integrations. Empty SMTP settings intentionally disable outgoing emails; the app logs when an email is skipped.

### Frontend

In a second terminal:

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Open http://localhost:3000. `NUXT_PUBLIC_API_BASE` must point to an API URL reachable from the browser, usually `http://localhost:8000/api` in local development.

## 3. Test the main user journey

1. Open the storefront and browse the seeded products/categories.
2. Add products to the cart. Guests can keep a local cart; sign in or register to sync it with the API and enable reminder emails.
3. Register an account. Once SMTP is configured, the welcome email is sent after registration.
4. Open the cart, continue to checkout, enter your delivery name, phone, city and address, then continue to hosted Paymob Checkout (after configuring Paymob).
5. After a successful payment, Paymob sends a signed webhook to the backend. The order is marked `paid` only after HMAC verification and amount/currency checks, then the saved cart is cleared and a receipt email is sent.
6. To test abandoned-cart email, sign in, add something to the cart, configure SMTP and set `CART_REMINDER_AFTER_HOURS=0` in a development-only `.env`. The scheduler checks hourly, so for an immediate local test call `send_abandoned_cart_reminders()` from a Python shell. Restore a positive delay before deployment.

## 4. Configure Paymob test payments (recommended for Egypt)

This starter defaults to `PAYMENT_PROVIDER=paymob` and `CURRENCY=egp`. Paymob’s current Intention API flow creates a payment intention on the backend and redirects the customer to Paymob-hosted Unified Checkout. Payment status is only updated from a valid HMAC-verified webhook; the browser redirect is not treated as proof of payment.

1. Create or open your merchant account in the [Paymob Egypt portal](https://accept.paymob.com/) and use the Paymob dashboard’s test/sandbox credentials.
2. In `backend/.env`, configure the secret key, public key, HMAC secret, and the Integration ID(s) enabled for your test credentials:

   ```dotenv
   PAYMENT_PROVIDER=paymob
   CURRENCY=egp
   PAYMOB_BASE_URL=https://accept.paymob.com
   PAYMOB_SECRET_KEY=sk_test_your_secret_key
   PAYMOB_PUBLIC_KEY=pk_test_your_public_key
   PAYMOB_HMAC_SECRET=your_webhook_hmac_secret
   PAYMOB_PAYMENT_METHODS=123456
   PUBLIC_API_URL=https://your-public-api.example.com
   ```

   Replace the example ID with your own enabled Paymob integration ID. IDs must match the test/live mode of the key. You can comma-separate multiple IDs if Paymob has enabled them for your account.

3. Paymob must reach your `notification_url` over the public internet. For local development, start an HTTPS tunnel to FastAPI, such as `ngrok http 8000`, then set `PUBLIC_API_URL` to the HTTPS forwarding origin shown by the tunnel, for example `https://abc123.ngrok-free.app`. Restart the API after changing `.env`.
4. Create an account, add products, continue to checkout, and submit a delivery phone number and address. Your backend creates a Paymob Intention (`POST /v1/intention/`) then redirects to its hosted checkout.
5. Configure your Paymob account to send transaction-processed callbacks to `https://YOUR_PUBLIC_API/api/payments/paymob/webhook`, if the dashboard requires callback configuration. The app also passes this URL in the Intention request.
6. Complete a sandbox payment. Paymob’s verified callback will set the order to `paid`, clear the saved cart, update stock, and trigger the payment-confirmation email. Test methods and payment options depend on your enabled Paymob account configuration.

Official reference: [Create Intention](https://developers.paymob.com/paymob-docs/intention-apis/create-intention), [Transaction callbacks](https://developers.paymob.com/paymob-docs/developers/webhook-callbacks-and-hmac/transaction-callbacks), [HMAC](https://developers.paymob.com/paymob-docs/developers/webhook-callbacks-and-hmac/hmac).

### Optional Stripe mode

To use Stripe instead, configure `PAYMENT_PROVIDER=stripe`, `CURRENCY` to a currency supported by your Stripe integration, `STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SECRET`. Point Stripe CLI at `localhost:8000/api/payments/stripe/webhook` (or use the compatibility endpoint `/api/payments/webhook`):

```bash
stripe listen --forward-to localhost:8000/api/payments/stripe/webhook
```

Copy the CLI’s `whsec_...` value to `STRIPE_WEBHOOK_SECRET`. Use test mode and a Stripe test card such as `4242 4242 4242 4242`. **Stripe business-account eligibility is country-specific; the official supported-country list currently does not include Egypt.** See [Stripe global availability](https://stripe.com/global).

Never put either provider’s secret keys in Nuxt’s public runtime config.

## 5. Configure SMTP mail

Set these backend environment variables using the values provided by your mail host:

```dotenv
SMTP_HOST=smtp.your-provider.com
SMTP_PORT=587
SMTP_USERNAME=your-mailbox-user
SMTP_PASSWORD=your-mailbox-password
SMTP_FROM_EMAIL=orders@your-domain.com
SMTP_FROM_NAME=NOVA Store
SMTP_USE_TLS=true
```

Use an authenticated mailbox and a sender/domain verified with the provider. Don't commit secrets to Git. Delivery providers may need SPF/DKIM/DMARC set up for reliable inbox placement.

## 6. Run with Docker Compose

From the project root:

```bash
cp .env.example .env
# Edit .env and set a real long AUTH_SECRET plus Paymob/SMTP settings when ready.
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend docs: http://localhost:8000/docs

For local Docker, the browser still calls `http://localhost:8000/api`; this is why `NUXT_PUBLIC_API_BASE` uses localhost rather than the Compose service name. For Paymob webhooks, set `PUBLIC_API_URL` to a reachable HTTPS origin and ensure your tunnel or deployed API is reachable. If deploying the frontend at another domain, update `CORS_ORIGINS` and `FRONTEND_URL` accordingly.

## 7. Before production

- Use PostgreSQL (and a migration tool such as Alembic) instead of SQLite for concurrent production traffic.
- Set a strong random `AUTH_SECRET`, TLS/HTTPS, exact CORS origins, secure hosting/secrets, backups and monitoring.
- Use a dedicated worker/queue (e.g. Celery/RQ + Redis) for reminders and email delivery. The included APScheduler is a convenient starter and should run in **one** API process only; multiple replicas could otherwise send duplicate reminders.
- Add rate limiting, email verification/password reset, inventory reservation/expiry for pending payments, refund/cancellation flows, privacy/terms and local tax/shipping rules.
- Validate country-specific payment provider availability, currency support, email compliance, consumer law and tax requirements before launch.
- Add tests and database migrations before changing the schema in a deployed environment.

## Project structure

```text
nova-home-tech/
├── backend/
│   ├── app/                 # FastAPI routes, models, email and reminder job
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── assets/css/          # Responsive storefront styles
│   ├── components/          # Product card
│   ├── composables/         # API, auth and cart state
│   ├── pages/               # Landing, products, cart, checkout, account/auth
│   └── nuxt.config.ts
├── docker-compose.yml
└── README.md
```
