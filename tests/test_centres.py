def test_create_and_list_centres(client, auth_headers):
    create = client.post(
        "/api/v1/centres",
        headers=auth_headers,
        json={"name": "EVE Labs", "location": "Mumbai"},
    )
    assert create.status_code == 201
    centre_id = create.json()["id"]

    listed = client.get("/api/v1/centres", headers=auth_headers)
    assert listed.status_code == 200
    assert listed.json()["total"] == 1

    detail = client.get(f"/api/v1/centres/{centre_id}", headers=auth_headers)
    assert detail.status_code == 200
    assert detail.json()["name"] == "EVE Labs"


def test_create_test_for_centre(client, auth_headers, centre_and_test):
    tests = client.get(
        f"/api/v1/centres/{centre_and_test['centre_id']}/tests",
        headers=auth_headers,
    )
    assert tests.status_code == 200
    assert tests.json()["total"] == 1
    assert tests.json()["items"][0]["name"] == "CBC"
