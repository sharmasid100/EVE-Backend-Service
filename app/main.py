from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

import structlog
from fastapi import APIRouter, FastAPI

from app.api import auth, bookings, centres, payments

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    logger.info("app_started", service="eve-diagnostic-booking")
    yield


app = FastAPI(
    title="EVE Diagnostic Booking API",
    description="Backend service for diagnostic test bookings and simulated payments.",
    version="1.0.0",
    lifespan=lifespan,
)

api_v1 = APIRouter(prefix="/api/v1")
api_v1.include_router(auth.router)
api_v1.include_router(centres.router)
api_v1.include_router(bookings.router)

app.include_router(api_v1)
app.include_router(payments.router)


@app.get("/health", tags=["health"])
def health() -> dict:
    return {"status": "ok"}
