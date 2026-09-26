from datetime import datetime, timedelta, timezone

from tests.conftest import future_appointment


def test_create_list_get_booking(client, auth_headers, centre_and_test):
    create = client.post(
        "/api/v1/bookings",
        headers=auth_headers,
        json={
            "centre_id": centre_and_test["centre_id"],
            "test_id": centre_and_test["test_id"],
            "appointment_at": future_appointment(),
        },
    )
    assert create.status_code == 201
    booking = create.json()
    assert booking["status"] == "PENDING"
    assert booking["amount"] == "499.00"

    listed = client.get("/api/v1/bookings", headers=auth_headers)
    assert listed.status_code == 200
    assert listed.json()["total"] == 1

    fetched = client.get(f"/api/v1/bookings/{booking['id']}", headers=auth_headers)
    assert fetched.status_code == 200
    assert fetched.json()["id"] == booking["id"]


def test_booking_other_user_returns_404(client, auth_headers, second_user_headers, centre_and_test):
    create = client.post(
        "/api/v1/bookings",
        headers=auth_headers,
        json={
            "centre_id": centre_and_test["centre_id"],
            "test_id": centre_and_test["test_id"],
            "appointment_at": future_appointment(),
        },
    )
    booking_id = create.json()["id"]
    resp = client.get(f"/api/v1/bookings/{booking_id}", headers=second_user_headers)
    assert resp.status_code == 404


def test_past_appointment_rejected(client, auth_headers, centre_and_test):
    past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    resp = client.post(
        "/api/v1/bookings",
        headers=auth_headers,
        json={
            "centre_id": centre_and_test["centre_id"],
            "test_id": centre_and_test["test_id"],
            "appointment_at": past,
        },
    )
    assert resp.status_code == 400


def test_test_centre_mismatch(client, auth_headers, centre_and_test):
    other = client.post(
        "/api/v1/centres",
        headers=auth_headers,
        json={"name": "Other", "location": "Pune"},
    ).json()
    resp = client.post(
        "/api/v1/bookings",
        headers=auth_headers,
        json={
            "centre_id": other["id"],
            "test_id": centre_and_test["test_id"],
            "appointment_at": future_appointment(),
        },
    )
    assert resp.status_code == 400


def test_cancel_pending_booking(client, auth_headers, centre_and_test):
    booking = client.post(
        "/api/v1/bookings",
        headers=auth_headers,
        json={
            "centre_id": centre_and_test["centre_id"],
            "test_id": centre_and_test["test_id"],
            "appointment_at": future_appointment(),
        },
    ).json()
    cancel = client.post(f"/api/v1/bookings/{booking['id']}/cancel", headers=auth_headers)
    assert cancel.status_code == 200
    assert cancel.json()["status"] == "CANCELLED"

    again = client.post(f"/api/v1/bookings/{booking['id']}/cancel", headers=auth_headers)
    assert again.status_code == 409
