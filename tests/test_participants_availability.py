from fastapi.testclient import TestClient


def test_add_list_and_remove_participant(
    client: TestClient, seeded, auth_headers
):
    meeting_id = seeded["meeting"].id
    headers = auth_headers()
    added = client.post(
        "/meetings/" + str(meeting_id) + "/participants/",
        headers=headers,
        json={"user_id": seeded["owner"].id},
    )
    assert added.status_code == 200
    participant_id = added.json()["id"]

    listed = client.get(
        "/meetings/" + str(meeting_id) + "/participants/",
        headers=headers,
    )
    assert listed.status_code == 200
    assert len(listed.json()) == 2

    removed = client.delete(
        "/meetings/" + str(meeting_id) + "/participants/" + str(participant_id),
        headers=headers,
    )
    assert removed.status_code == 200


def test_duplicate_participant_is_rejected(
    client: TestClient, seeded, auth_headers
):
    response = client.post(
        "/meetings/" + str(seeded["meeting"].id) + "/participants/",
        headers=auth_headers(),
        json={"user_id": seeded["participant_user"].id},
    )
    assert response.status_code == 409


def test_participant_changes_require_the_organizer(
    client: TestClient, seeded, auth_headers
):
    response = client.post(
        "/meetings/" + str(seeded["meeting"].id) + "/participants/",
        headers=auth_headers("participant@example.com"),
        json={"user_id": seeded["owner"].id},
    )
    assert response.status_code == 403

    response = client.get(
        "/meetings/" + str(seeded["meeting"].id) + "/participants/",
        headers=auth_headers("outsider@example.com"),
    )
    assert response.status_code == 403


def test_availability_create_list_update_delete(
    client: TestClient, seeded, auth_headers
):
    meeting_id = seeded["meeting"].id
    member_headers = auth_headers("participant@example.com")
    created = client.post(
        "/meetings/" + str(meeting_id) + "/availability/",
        headers=member_headers,
        json={
            "start_time": "2026-11-10T09:00:00",
            "end_time": "2026-11-10T12:00:00",
        },
    )
    assert created.status_code == 200
    availability_id = created.json()["id"]

    listed = client.get(
        "/meetings/" + str(meeting_id) + "/availability/",
        headers=auth_headers(),
    )
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    updated = client.put(
        "/meetings/" + str(meeting_id) + "/availability/" + str(availability_id),
        headers=member_headers,
        json={
            "start_time": "2026-11-10T10:00:00",
            "end_time": "2026-11-10T13:00:00",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["start_time"].startswith("2026-11-10T10:00:00")

    deleted = client.delete(
        "/meetings/" + str(meeting_id) + "/availability/" + str(availability_id),
        headers=member_headers,
    )
    assert deleted.status_code == 200


def test_availability_rejects_invalid_time_range(
    client: TestClient, seeded, auth_headers
):
    response = client.post(
        "/meetings/" + str(seeded["meeting"].id) + "/availability/",
        headers=auth_headers("participant@example.com"),
        json={
            "start_time": "2026-11-10T12:00:00",
            "end_time": "2026-11-10T09:00:00",
        },
    )
    assert response.status_code == 422


def test_availability_requires_meeting_participant_and_owner(
    client: TestClient, seeded, auth_headers
):
    meeting_id = seeded["meeting"].id
    created = client.post(
        "/meetings/" + str(meeting_id) + "/availability/",
        headers=auth_headers("participant@example.com"),
        json={
            "start_time": "2026-11-10T09:00:00",
            "end_time": "2026-11-10T10:00:00",
        },
    )
    availability_id = created.json()["id"]

    update = client.put(
        "/meetings/" + str(meeting_id) + "/availability/" + str(availability_id),
        headers=auth_headers(),
        json={
            "start_time": "2026-11-10T10:00:00",
            "end_time": "2026-11-10T11:00:00",
        },
    )
    assert update.status_code == 403

    listing = client.get(
        "/meetings/" + str(meeting_id) + "/availability/",
        headers=auth_headers("outsider@example.com"),
    )
    assert listing.status_code == 403
