from __future__ import annotations

from typing import Generator, Optional

import pytest
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.db import Base, get_db
from app.main import app


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    settings.jwt_secret = "test-secret"
    settings.webhook_secret = "test-webhook-secret"
    settings.payment_force_result = ""

    def override_get_db() -> Generator[Session, None, None]:
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_headers(client: TestClient) -> dict:
    signup = client.post(
        "/api/v1/auth/signup",
        json={"email": "patient@example.com", "password": "password123", "full_name": "Patient One"},
    )
    assert signup.status_code == 201
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "patient@example.com", "password": "password123"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    return {"Authorization": "Bearer {}".format(token)}


@pytest.fixture()
def second_user_headers(client: TestClient) -> dict:
    signup = client.post(
        "/api/v1/auth/signup",
        json={"email": "other@example.com", "password": "password123", "full_name": "Other User"},
    )
    assert signup.status_code == 201
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "other@example.com", "password": "password123"},
    )
    token = login.json()["access_token"]
    return {"Authorization": "Bearer {}".format(token)}


@pytest.fixture()
def centre_and_test(client: TestClient, auth_headers: dict) -> dict:
    centre = client.post(
        "/api/v1/centres",
        headers=auth_headers,
        json={"name": "EVE Labs", "location": "Bangalore"},
    )
    assert centre.status_code == 201
    centre_id = centre.json()["id"]
    test = client.post(
        "/api/v1/centres/{}/tests".format(centre_id),
        headers=auth_headers,
        json={"name": "CBC", "price": "499.00"},
    )
    assert test.status_code == 201
    return {"centre_id": centre_id, "test_id": test.json()["id"], "price": test.json()["price"]}


def future_appointment() -> str:
    return (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
