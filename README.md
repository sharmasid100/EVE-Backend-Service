# EVE Diagnostic Booking API

Backend service for diagnostic test bookings and simulated payments (EVE Healthcare SDE Intern assignment).

## Stack

- Python 3.12 + FastAPI
- PostgreSQL 16 + SQLAlchemy 2 + Alembic
- JWT authentication
- Docker Compose

## Quick start (Docker)

```bash
cd eve
cp .env.example .env   # optional; compose uses .env.example by default
docker compose up --build
```

- API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- Health: http://localhost:8000/health

Seed demo centres/tests (after API is up, from another shell):

```bash
docker compose exec api python -m scripts.seed
```

## Local development (without Docker for the app)

1. Start Postgres (or use the `db` service from compose).
2. Create a virtualenv and install dependencies:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=postgresql+psycopg2://eve:eve@localhost:5432/eve
export JWT_SECRET=dev-secret
export WEBHOOK_SECRET=dev-webhook-secret
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

## Tests

```bash
pip install -r requirements.txt
pytest -q
```

Tests use an in-memory SQLite database and do not require Postgres.

## API overview

All authenticated routes expect `Authorization: Bearer <access_token>`.

### Auth

| Method | Path | Auth |
|---|---|---|
| POST | `/api/v1/auth/signup` | no |
| POST | `/api/v1/auth/login` | no |

Signup body:

```json
{"email": "patient@example.com", "password": "password123", "full_name": "Patient One"}
```

Login body:

```json
{"email": "patient@example.com", "password": "password123"}
```

### Centres & tests

| Method | Path |
|---|---|
| GET/POST | `/api/v1/centres` |
| GET | `/api/v1/centres/{centre_id}` |
| GET/POST | `/api/v1/centres/{centre_id}/tests` |

### Bookings

| Method | Path |
|---|---|
| POST/GET | `/api/v1/bookings` |
| GET | `/api/v1/bookings/{booking_id}` |
| POST | `/api/v1/bookings/{booking_id}/cancel` |

Create booking:

```json
{
  "centre_id": "<uuid>",
  "test_id": "<uuid>",
  "appointment_at": "2026-12-01T10:00:00+00:00"
}
```

Statuses: `PENDING`, `CONFIRMED`, `FAILED`, `CANCELLED`.

### Payments

Canonical and assignment-compatible paths:

| Method | Path | Auth |
|---|---|---|
| POST | `/api/v1/payments/` or `/payments/` | JWT |
| POST | `/api/v1/payments/webhook/` or `/payments/webhook/` | `X-Webhook-Secret` |

Simulate payment (force outcome in tests/demos):

```bash
curl -X POST http://localhost:8000/api/v1/payments/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Mock-Payment-Result: SUCCESS" \
  -H "Content-Type: application/json" \
  -d '{"booking_id":"<uuid>"}'
```

Webhook (idempotent on `event_id`):

```bash
curl -X POST http://localhost:8000/payments/webhook/ \
  -H "X-Webhook-Secret: dev-webhook-secret" \
  -H "Content-Type: application/json" \
  -d '{"event_id":"evt-1","booking_id":"<uuid>","status":"SUCCESS"}'
```

## Database schema

- **users** — account credentials
- **diagnostic_centres** — centre name + location
- **diagnostic_tests** — tests offered by a centre + price
- **bookings** — user, centre, test, appointment, amount snapshot, status
- **payments** — payment attempt linked to a booking
- **webhook_events** — `event_id` primary key for webhook idempotency

## Important assumptions

1. Booking amount is snapshotted from the test price at booking time.
2. Accessing another user's booking returns **404** (no existence leak).
3. Only `PENDING` bookings can be paid or cancelled.
4. Webhooks never reopen `CANCELLED` bookings (`409`).
5. Duplicate webhook `event_id` returns the prior result with `idempotent_replay: true`.
6. Payment simulation prefers `PAYMENT_FORCE_RESULT` env, then `X-Mock-Payment-Result`, else a deterministic ~80% SUCCESS hash.

## What I would improve with more time

- Redis caching for centre/test catalogue
- Celery/background jobs for async payment confirmation
- Rate limiting on auth and webhook endpoints
- Retry/dead-letter handling for webhook processing
- Role-based access (admin vs patient) for centre management
- Stronger observability (OpenTelemetry traces/metrics)

## Project layout

See `CLAUDE.md` for the locked architecture and contracts (single source of truth).
