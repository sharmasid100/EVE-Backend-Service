from tests.conftest import future_appointment


def _create_booking(client, auth_headers, centre_and_test):
    return client.post(
        "/api/v1/bookings",
        headers=auth_headers,
        json={
            "centre_id": centre_and_test["centre_id"],
            "test_id": centre_and_test["test_id"],
            "appointment_at": future_appointment(),
        },
    ).json()


def test_payment_success(client, auth_headers, centre_and_test):
    booking = _create_booking(client, auth_headers, centre_and_test)
    resp = client.post(
        "/api/v1/payments/",
        headers={**auth_headers, "X-Mock-Payment-Result": "SUCCESS"},
        json={"booking_id": booking["id"]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "SUCCESS"
    assert body["booking_status"] == "CONFIRMED"

    fetched = client.get(f"/api/v1/bookings/{booking['id']}", headers=auth_headers)
    assert fetched.json()["status"] == "CONFIRMED"


def test_payment_failed(client, auth_headers, centre_and_test):
    booking = _create_booking(client, auth_headers, centre_and_test)
    resp = client.post(
        "/payments/",
        headers={**auth_headers, "X-Mock-Payment-Result": "FAILED"},
        json={"booking_id": booking["id"]},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "FAILED"
    assert resp.json()["booking_status"] == "FAILED"


def test_payment_non_pending_conflict(client, auth_headers, centre_and_test):
    booking = _create_booking(client, auth_headers, centre_and_test)
    client.post(f"/api/v1/bookings/{booking['id']}/cancel", headers=auth_headers)
    resp = client.post(
        "/api/v1/payments/",
        headers={**auth_headers, "X-Mock-Payment-Result": "SUCCESS"},
        json={"booking_id": booking["id"]},
    )
    assert resp.status_code == 409
