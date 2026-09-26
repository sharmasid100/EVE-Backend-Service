# CLAUDE.md — EVE Diagnostic Booking Backend (SSOT)

This file is the **final and only** source of truth for implementation.
Do not invent alternate stacks, APIs, enums, or folder layouts.
Do not add Redis, Celery, or rate limiting unless this file is updated first.

## Boundary (non-negotiable)

- All files live under `/Users/kmishra/Desktop/eve` only.
- No read/write/modify/delete outside that folder.
- Follow this document for every implementation decision.

## Locked technology choices

| Decision | Choice |
|---|---|
| Language | Python 3.12 |
| Framework | FastAPI |
| ORM / DB | SQLAlchemy 2.x + Alembic + PostgreSQL 16 |
| Auth | JWT access tokens via `python-jose` + `passlib[bcrypt]` |
| Config | `pydantic-settings` + env vars |
| Tests | `pytest` + `httpx` + in-process SQLite (tests) / Postgres (compose) |
| Containers | `Dockerfile` + `docker-compose.yml` (app + Postgres) |
| Package mgmt | `pyproject.toml` + `requirements.txt` |
| Logging | `structlog` JSON logs |
| Pagination | Offset `limit` / `offset` on list endpoints |

**Out of scope for v1:** Redis, Celery, rate limiting, webhook retries.

## Repository structure

```
eve/
??? CLAUDE.md
??? README.md
??? .gitignore
??? .env.example
??? Dockerfile
??? docker-compose.yml
??? pyproject.toml
??? requirements.txt
??? alembic.ini
??? alembic/
?   ??? versions/
??? app/
?   ??? __init__.py
?   ??? main.py
?   ??? config.py
?   ??? db.py
?   ??? deps.py
?   ??? models/
?   ??? schemas/
?   ??? api/
?   ??? services/
?   ??? core/
??? tests/
??? scripts/
    ??? seed.py
```

## Data model

### Enums (exact)

- Booking status: `PENDING` | `CONFIRMED` | `FAILED` | `CANCELLED`
- Payment status: `SUCCESS` | `FAILED` | `PENDING`

### Tables

- **User**: `id` (UUID PK), `email` (unique), `hashed_password`, `full_name`, `created_at`
- **DiagnosticCentre**: `id` (UUID PK), `name`, `location`, `created_at`
- **DiagnosticTest**: `id` (UUID PK), `centre_id` (FK), `name`, `price` (Numeric), `created_at`
- **Booking**: `id` (UUID PK), `user_id` (FK), `centre_id` (FK), `test_id` (FK), `appointment_at`, `amount` (Numeric), `status`, `created_at`, `updated_at`
- **Payment**: `id` (UUID PK), `booking_id` (FK), `status`, `provider_event_id` (unique, nullable), `amount`, `created_at`, `updated_at`
- **WebhookEvent**: `event_id` (PK string), `payment_id` (FK), `processed_at`, `payload` (JSON)

### Invariants

1. `Booking.amount` = selected `DiagnosticTest.price` at booking time (snapshot).
2. `DiagnosticTest` must belong to the same `DiagnosticCentre` on the booking.
3. Only the booking owner can cancel or initiate payment for that booking.
4. Terminal booking states: `CONFIRMED`, `FAILED`, `CANCELLED`.
5. Payments/webhooks must never reopen a `CANCELLED` booking.
6. Access to another user's booking returns **404** (do not leak existence).

## API contracts

Base URL: `/api/v1`. Versioned routes are canonical.
Compatibility aliases (same handlers): `POST /payments/` and `POST /payments/webhook/`.

### Auth

| Method | Path | Auth | Body | Success |
|---|---|---|---|---|
| POST | `/api/v1/auth/signup` | no | `{email, password, full_name}` | `201` user (no password) |
| POST | `/api/v1/auth/login` | no | `{email, password}` | `200` `{access_token, token_type}` |

- Email format validated; password min 8 chars; duplicate email ? `409`.

### Centres & tests

| Method | Path | Auth | Notes |
|---|---|---|---|
| GET | `/api/v1/centres` | yes | paginated `limit`/`offset` |
| POST | `/api/v1/centres` | yes | `{name, location}` |
| GET | `/api/v1/centres/{centre_id}` | yes | include nested tests |
| GET | `/api/v1/centres/{centre_id}/tests` | yes | paginated |
| POST | `/api/v1/centres/{centre_id}/tests` | yes | `{name, price}` price > 0 |

### Bookings

| Method | Path | Auth | Notes |
|---|---|---|---|
| POST | `/api/v1/bookings` | yes | `{centre_id, test_id, appointment_at}` ? `PENDING` |
| GET | `/api/v1/bookings` | yes | own bookings only, paginated |
| GET | `/api/v1/bookings/{booking_id}` | yes | owner only else `404` |
| POST | `/api/v1/bookings/{booking_id}/cancel` | yes | only if `PENDING` ? `CANCELLED` |

### Payments

| Method | Path | Auth | Behavior |
|---|---|---|---|
| POST | `/api/v1/payments/` | yes | body `{booking_id}`. Outcome: env `PAYMENT_FORCE_RESULT` if set; else header `X-Mock-Payment-Result: SUCCESS\|FAILED` if set; else deterministic hash (~80% SUCCESS). SUCCESS ? payment SUCCESS + booking CONFIRMED. FAILED ? payment FAILED + booking FAILED. Reject if booking not PENDING or not owned. |
| POST | `/api/v1/payments/webhook/` | no JWT; optional `X-Webhook-Secret` | body `{event_id, booking_id, payment_id?, status}` (`SUCCESS`\|`FAILED`). Idempotent on `event_id`: store in `WebhookEvent`; duplicate returns `200` with prior result, no state change. Never move CANCELLED bookings ? `409`. Invalid secret when configured ? `401`. |

## State machine

```
[*] ? PENDING (create booking)
PENDING ? CONFIRMED (payment/webhook SUCCESS)
PENDING ? FAILED (payment/webhook FAILED)
PENDING ? CANCELLED (user cancel)
CONFIRMED / FAILED / CANCELLED are terminal
```

## Edge cases (must have tests)

- Invalid signup/login ? `422`
- Duplicate email ? `409`
- Missing/invalid JWT ? `401`
- Another user's booking ? `404`
- Unknown IDs ? `404`
- Test not belonging to centre ? `400`
- Appointment in the past ? `400`
- Pay or cancel non-PENDING ? `409`
- Duplicate webhook `event_id` ? `200`, no duplicate payment
- Webhook for cancelled booking ? `409`
- Invalid webhook secret (when configured) ? `401`

## Env vars (`.env.example`)

- `DATABASE_URL`
- `JWT_SECRET`
- `JWT_ALGORITHM=HS256`
- `ACCESS_TOKEN_EXPIRE_MINUTES=60`
- `WEBHOOK_SECRET`
- `PAYMENT_FORCE_RESULT=` (empty by default)

## Docker

- `db`: `postgres:16-alpine`, volume, healthcheck
- `api`: build Dockerfile, depends_on healthy db, Alembic upgrade then uvicorn, `8000:8000`

## Implementation order

1. This CLAUDE.md (done when present)
2. Scaffold: `.gitignore`, `.env.example`, `pyproject.toml`, `requirements.txt`, `Dockerfile`, `docker-compose.yml`
3. App skeleton: config, db, models, Alembic initial migration
4. Auth
5. Centres + tests + seed
6. Bookings
7. Payments + webhook idempotency
8. Structured logging + OpenAPI tags
9. Tests
10. README.md
11. `git init` only when the user asks; do not commit secrets

## Definition of done

- `docker compose up --build` boots API + Postgres
- Swagger at `/docs`
- All required assignment features work end-to-end
- Webhook idempotency proven by tests
- README covers run instructions, endpoints, schema, assumptions, improvements
- `.gitignore` excludes `.env`, `__pycache__`, `.venv`, `.pytest_cache`, IDE files, `*.pyc`
- No secrets committed
- Everything under `/Users/kmishra/Desktop/eve` only
