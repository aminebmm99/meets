from fastapi.testclient import TestClient


def test_meeting_create_get_update_delete(
    client: TestClient, seeded, auth_headers
):
    headers = auth_headers()
    created = client.post(
        "/meetings/",
        headers=headers,
        json={
            "title": "New meeting",
            "description": "Initial details",
            "organization_id": seeded["organization"].id,
        },
    )
    assert created.status_code == 200
    meeting_id = created.json()["id"]
    assert created.json()["organizer_id"] == seeded["owner"].id

    retrieved = client.get("/meetings/" + str(meeting_id), headers=headers)
    assert retrieved.status_code == 200
    assert retrieved.json()["title"] == "New meeting"

    updated = client.put(
        "/meetings/" + str(meeting_id),
        headers=headers,
        json={"title": "Updated meeting", "description": None},
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Updated meeting"

    deleted = client.delete("/meetings/" + str(meeting_id), headers=headers)
    assert deleted.status_code == 200
    assert client.get("/meetings/" + str(meeting_id), headers=headers).status_code == 404


def test_meeting_list_is_scoped_to_user_organization(
    client: TestClient, seeded, auth_headers
):
    response = client.get("/meetings/", headers=auth_headers())
    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [seeded["meeting"].id]

    other_user_meetings = client.get(
        "/meetings/", headers=auth_headers("outsider@example.com")
    )
    assert other_user_meetings.status_code == 200
    assert other_user_meetings.json() == []


def test_meeting_list_supports_pagination(client: TestClient, seeded, auth_headers):
    headers = auth_headers()
    client.post(
        "/meetings/",
        headers=headers,
        json={
            "title": "Second meeting",
            "description": None,
            "organization_id": seeded["organization"].id,
        },
    )
    page = client.get("/meetings/?limit=1&offset=1", headers=headers)
    assert page.status_code == 200
    assert len(page.json()) == 1
    assert page.json()[0]["title"] == "Second meeting"


def test_meeting_creation_rejects_another_organization(
    client: TestClient, seeded, auth_headers
):
    response = client.post(
        "/meetings/",
        headers=auth_headers(),
        json={
            "title": "Unauthorized meeting",
            "description": None,
            "organization_id": seeded["other_organization"].id,
        },
    )
    assert response.status_code == 403


def test_only_organizer_can_update_or_delete_meeting(
    client: TestClient, seeded, auth_headers
):
    headers = auth_headers("participant@example.com")
    meeting_id = seeded["meeting"].id

    update = client.put(
        "/meetings/" + str(meeting_id),
        headers=headers,
        json={"title": "Not allowed", "description": None},
    )
    assert update.status_code == 403

    delete = client.delete("/meetings/" + str(meeting_id), headers=headers)
    assert delete.status_code == 403


def test_meeting_access_is_limited_to_organization(
    client: TestClient, seeded, auth_headers
):
    response = client.get(
        "/meetings/" + str(seeded["meeting"].id),
        headers=auth_headers("outsider@example.com"),
    )
    assert response.status_code == 403
