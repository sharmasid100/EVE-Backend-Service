from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import bad_request, conflict, not_found
from app.models import Booking, BookingStatus, DiagnosticCentre, DiagnosticTest, User
from app.schemas import BookingCreate, BookingOut, PaginatedBookings


def create_booking(db: Session, user: User, payload: BookingCreate) -> BookingOut:
    centre = db.get(DiagnosticCentre, payload.centre_id)
    if centre is None:
        raise not_found("Diagnostic centre not found")

    test = db.get(DiagnosticTest, payload.test_id)
    if test is None:
        raise not_found("Diagnostic test not found")

    if test.centre_id != payload.centre_id:
        raise bad_request("Diagnostic test does not belong to the specified centre")

    appointment_at = payload.appointment_at
    if appointment_at.tzinfo is None:
        appointment_at = appointment_at.replace(tzinfo=timezone.utc)
    if appointment_at <= datetime.now(timezone.utc):
        raise bad_request("Appointment must be in the future")

    booking = Booking(
        user_id=user.id,
        centre_id=payload.centre_id,
        test_id=payload.test_id,
        appointment_at=appointment_at,
        amount=test.price,
        status=BookingStatus.PENDING,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return _to_out(booking)


def list_bookings(db: Session, user: User, limit: int, offset: int) -> PaginatedBookings:
    query = db.query(Booking).filter(Booking.user_id == user.id)
    total = query.count()
    items = query.order_by(Booking.created_at.desc()).offset(offset).limit(limit).all()
    return PaginatedBookings(
        items=[_to_out(b) for b in items],
        total=total,
        limit=limit,
        offset=offset,
    )


def get_booking(db: Session, user: User, booking_id: UUID) -> BookingOut:
    booking = _get_owned_booking(db, user, booking_id)
    return _to_out(booking)


def cancel_booking(db: Session, user: User, booking_id: UUID) -> BookingOut:
    booking = _get_owned_booking(db, user, booking_id)
    if booking.status != BookingStatus.PENDING:
        raise conflict("Only PENDING bookings can be cancelled")
    booking.status = BookingStatus.CANCELLED
    db.commit()
    db.refresh(booking)
    return _to_out(booking)


def _get_owned_booking(db: Session, user: User, booking_id: UUID) -> Booking:
    booking = db.get(Booking, booking_id)
    if booking is None or booking.user_id != user.id:
        raise not_found("Booking not found")
    return booking


def _to_out(booking: Booking) -> BookingOut:
    return BookingOut(
        id=booking.id,
        user_id=booking.user_id,
        centre_id=booking.centre_id,
        test_id=booking.test_id,
        appointment_at=booking.appointment_at,
        amount=booking.amount,
        status=booking.status.value,
        created_at=booking.created_at,
        updated_at=booking.updated_at,
    )
