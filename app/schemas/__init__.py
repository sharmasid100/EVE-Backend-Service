from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1, max_length=255)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    full_name: str
    created_at: datetime


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CentreCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    location: str = Field(min_length=1, max_length=255)


class TestCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    price: Decimal = Field(gt=0, max_digits=12, decimal_places=2)


class TestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    centre_id: UUID
    name: str
    price: Decimal
    created_at: datetime


class CentreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    location: str
    created_at: datetime


class CentreDetailOut(CentreOut):
    tests: List[TestOut] = []


class PaginatedCentres(BaseModel):
    items: List[CentreOut]
    total: int
    limit: int
    offset: int


class PaginatedTests(BaseModel):
    items: List[TestOut]
    total: int
    limit: int
    offset: int


class BookingCreate(BaseModel):
    centre_id: UUID
    test_id: UUID
    appointment_at: datetime


class BookingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    centre_id: UUID
    test_id: UUID
    appointment_at: datetime
    amount: Decimal
    status: str
    created_at: datetime
    updated_at: datetime


class PaginatedBookings(BaseModel):
    items: List[BookingOut]
    total: int
    limit: int
    offset: int


class PaymentCreate(BaseModel):
    booking_id: UUID


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    booking_id: UUID
    status: str
    provider_event_id: Optional[str]
    amount: Decimal
    created_at: datetime
    updated_at: datetime
    booking_status: Optional[str] = None


class WebhookIn(BaseModel):
    event_id: str = Field(min_length=1, max_length=255)
    booking_id: UUID
    payment_id: Optional[UUID] = None
    status: str = Field(pattern="^(SUCCESS|FAILED)$")


class WebhookOut(BaseModel):
    event_id: str
    payment_id: UUID
    booking_id: UUID
    payment_status: str
    booking_status: str
    idempotent_replay: bool = False
