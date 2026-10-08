from fastapi.testclient import TestClient


def test_organization_create_and_list(client: TestClient):
    created = client.post("/organizations/", json={"name": "Acme"})
    assert created.status_code == 200
    organization_id = created.json()["id"]

    listed = client.get("/organizations/")
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [organization_id]


def test_organization_list_supports_pagination(client: TestClient):
    client.post("/organizations/", json={"name": "First"})
    client.post("/organizations/", json={"name": "Second"})

    page = client.get("/organizations/?limit=1&offset=1")
    assert page.status_code == 200
    assert len(page.json()) == 1
    assert page.json()[0]["name"] == "Second"


def test_duplicate_organization_name_returns_conflict(client: TestClient):
    assert client.post("/organizations/", json={"name": "Acme"}).status_code == 200
    duplicate = client.post("/organizations/", json={"name": "Acme"})
    assert duplicate.status_code == 409


def test_organization_update_and_delete(client: TestClient):
    created = client.post("/organizations/", json={"name": "Old name"})
    organization_id = created.json()["id"]

    updated = client.put(
        "/organizations/" + str(organization_id),
        json={"name": "New name"},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "New name"

    deleted = client.delete("/organizations/" + str(organization_id))
    assert deleted.status_code == 200
    assert deleted.json()["message"] == "Organization deleted successfully"


def test_missing_organization_returns_not_found(client: TestClient):
    response = client.put("/organizations/999", json={"name": "Missing"})
    assert response.status_code == 404

    response = client.delete("/organizations/999")
    assert response.status_code == 404
