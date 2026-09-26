from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import PaymentCreate, PaymentOut, WebhookIn, WebhookOut
from app.services import payment_service

router = APIRouter(tags=["payments"])


@router.post("/api/v1/payments/", response_model=PaymentOut)
@router.post("/payments/", response_model=PaymentOut)
def create_payment(
    payload: PaymentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    x_mock_payment_result: Optional[str] = Header(default=None, alias="X-Mock-Payment-Result"),
) -> PaymentOut:
    return payment_service.create_payment(db, user, payload, x_mock_payment_result)


@router.post("/api/v1/payments/webhook/", response_model=WebhookOut)
@router.post("/payments/webhook/", response_model=WebhookOut)
def payment_webhook(
    payload: WebhookIn,
    db: Session = Depends(get_db),
    x_webhook_secret: Optional[str] = Header(default=None, alias="X-Webhook-Secret"),
) -> WebhookOut:
    return payment_service.process_webhook(db, payload, x_webhook_secret)
