from tests.conftest import future_appointment


def test_webhook_idempotency(client, auth_headers, centre_and_test):
    booking = client.post(
        "/api/v1/bookings",
        headers=auth_headers,
        json={
            "centre_id": centre_and_test["centre_id"],
            "test_id": centre_and_test["test_id"],
            "appointment_at": future_appointment(),
        },
    ).json()

    payload = {
        "event_id": "evt-123",
        "booking_id": booking["id"],
        "status": "SUCCESS",
    }
    headers = {"X-Webhook-Secret": "test-webhook-secret"}

    first = client.post("/payments/webhook/", json=payload, headers=headers)
    assert first.status_code == 200
    assert first.json()["payment_status"] == "SUCCESS"
    assert first.json()["booking_status"] == "CONFIRMED"
    assert first.json()["idempotent_replay"] is False
    payment_id = first.json()["payment_id"]

    second = client.post("/api/v1/payments/webhook/", json=payload, headers=headers)
    assert second.status_code == 200
    assert second.json()["idempotent_replay"] is True
    assert second.json()["payment_id"] == payment_id
    assert second.json()["booking_status"] == "CONFIRMED"

    bookings = client.get("/api/v1/bookings", headers=auth_headers).json()
    assert bookings["total"] == 1
    assert bookings["items"][0]["status"] == "CONFIRMED"


def test_webhook_cancelled_booking_conflict(client, auth_headers, centre_and_test):
    booking = client.post(
        "/api/v1/bookings",
        headers=auth_headers,
        json={
            "centre_id": centre_and_test["centre_id"],
            "test_id": centre_and_test["test_id"],
            "appointment_at": future_appointment(),
        },
    ).json()
    client.post(f"/api/v1/bookings/{booking['id']}/cancel", headers=auth_headers)

    resp = client.post(
        "/payments/webhook/",
        headers={"X-Webhook-Secret": "test-webhook-secret"},
        json={"event_id": "evt-cancel", "booking_id": booking["id"], "status": "SUCCESS"},
    )
    assert resp.status_code == 409


def test_webhook_invalid_secret(client, auth_headers, centre_and_test):
    booking = client.post(
        "/api/v1/bookings",
        headers=auth_headers,
        json={
            "centre_id": centre_and_test["centre_id"],
            "test_id": centre_and_test["test_id"],
            "appointment_at": future_appointment(),
        },
    ).json()
    resp = client.post(
        "/payments/webhook/",
        headers={"X-Webhook-Secret": "wrong"},
        json={"event_id": "evt-bad", "booking_id": booking["id"], "status": "SUCCESS"},
    )
    assert resp.status_code == 401
