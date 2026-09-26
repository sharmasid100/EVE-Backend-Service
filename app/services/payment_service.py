from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.core.exceptions import conflict, not_found, unauthorized
from app.models import Booking, BookingStatus, Payment, PaymentStatus, User, WebhookEvent
from app.schemas import PaymentCreate, PaymentOut, WebhookIn, WebhookOut
import hashlib


def create_payment(
    db: Session,
    user: User,
    payload: PaymentCreate,
    mock_result_header: Optional[str] = None,
) -> PaymentOut:
    booking = db.get(Booking, payload.booking_id)
    if booking is None or booking.user_id != user.id:
        raise not_found("Booking not found")
    if booking.status != BookingStatus.PENDING:
        raise conflict("Only PENDING bookings can be paid")

    outcome = _resolve_outcome(str(booking.id), mock_result_header)
    payment_status = PaymentStatus.SUCCESS if outcome == "SUCCESS" else PaymentStatus.FAILED
    booking_status = BookingStatus.CONFIRMED if outcome == "SUCCESS" else BookingStatus.FAILED

    payment = Payment(
        booking_id=booking.id,
        status=payment_status,
        amount=booking.amount,
        provider_event_id="sim-{}-{}".format(booking.id, payment_status.value),
    )
    booking.status = booking_status
    db.add(payment)
    db.commit()
    db.refresh(payment)
    db.refresh(booking)

    return PaymentOut(
        id=payment.id,
        booking_id=payment.booking_id,
        status=payment.status.value,
        provider_event_id=payment.provider_event_id,
        amount=payment.amount,
        created_at=payment.created_at,
        updated_at=payment.updated_at,
        booking_status=booking.status.value,
    )


def process_webhook(
    db: Session,
    payload: WebhookIn,
    webhook_secret_header: Optional[str],
) -> WebhookOut:
    if settings.webhook_secret and webhook_secret_header != settings.webhook_secret:
        raise unauthorized("Invalid webhook secret")

    existing_event = db.get(WebhookEvent, payload.event_id)
    if existing_event is not None:
        payment = db.get(Payment, existing_event.payment_id)
        if payment is None:
            raise not_found("Payment not found for webhook event")
        booking = db.get(Booking, payment.booking_id)
        if booking is None:
            raise not_found("Booking not found for webhook event")
        return WebhookOut(
            event_id=existing_event.event_id,
            payment_id=payment.id,
            booking_id=booking.id,
            payment_status=payment.status.value,
            booking_status=booking.status.value,
            idempotent_replay=True,
        )

    booking = db.get(Booking, payload.booking_id)
    if booking is None:
        raise not_found("Booking not found")

    if booking.status == BookingStatus.CANCELLED:
        raise conflict("Cannot update a CANCELLED booking via webhook")

    payment = None
    if payload.payment_id is not None:
        payment = db.get(Payment, payload.payment_id)
        if payment is None or payment.booking_id != booking.id:
            raise not_found("Payment not found")
    else:
        payment = (
            db.query(Payment)
            .filter(Payment.booking_id == booking.id)
            .order_by(Payment.created_at.desc())
            .first()
        )
        if payment is None:
            payment = Payment(
                booking_id=booking.id,
                status=PaymentStatus.PENDING,
                amount=booking.amount,
                provider_event_id=None,
            )
            db.add(payment)
            db.flush()

    payment_status = PaymentStatus.SUCCESS if payload.status == "SUCCESS" else PaymentStatus.FAILED
    booking_status = BookingStatus.CONFIRMED if payload.status == "SUCCESS" else BookingStatus.FAILED

    if payment.status == payment_status and payment.status != PaymentStatus.PENDING:
        event = WebhookEvent(
            event_id=payload.event_id,
            payment_id=payment.id,
            payload=payload.model_dump(mode="json"),
        )
        db.add(event)
        db.commit()
        return WebhookOut(
            event_id=payload.event_id,
            payment_id=payment.id,
            booking_id=booking.id,
            payment_status=payment.status.value,
            booking_status=booking.status.value,
            idempotent_replay=False,
        )

    if booking.status == BookingStatus.PENDING:
        payment.status = payment_status
        if payment.provider_event_id is None:
            payment.provider_event_id = payload.event_id
        booking.status = booking_status
    elif payment.status == PaymentStatus.PENDING:
        payment.status = payment_status
        if payment.provider_event_id is None:
            payment.provider_event_id = payload.event_id
    else:
        event = WebhookEvent(
            event_id=payload.event_id,
            payment_id=payment.id,
            payload=payload.model_dump(mode="json"),
        )
        db.add(event)
        db.commit()
        return WebhookOut(
            event_id=payload.event_id,
            payment_id=payment.id,
            booking_id=booking.id,
            payment_status=payment.status.value,
            booking_status=booking.status.value,
            idempotent_replay=False,
        )

    event = WebhookEvent(
        event_id=payload.event_id,
        payment_id=payment.id,
        payload=payload.model_dump(mode="json"),
    )
    db.add(event)
    db.commit()
    db.refresh(payment)
    db.refresh(booking)

    return WebhookOut(
        event_id=payload.event_id,
        payment_id=payment.id,
        booking_id=booking.id,
        payment_status=payment.status.value,
        booking_status=booking.status.value,
        idempotent_replay=False,
    )


def _resolve_outcome(booking_id: str, mock_result_header: Optional[str]) -> str:
    forced = (settings.payment_force_result or "").strip().upper()
    if forced in {"SUCCESS", "FAILED"}:
        return forced

    if mock_result_header:
        header = mock_result_header.strip().upper()
        if header in {"SUCCESS", "FAILED"}:
            return header

    digest = hashlib.sha256(booking_id.encode("utf-8")).hexdigest()
    return "SUCCESS" if int(digest[:2], 16) % 10 < 8 else "FAILED"
