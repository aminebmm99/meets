from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Availability, Participant, SchedulingRequest
from app.services.scheduling import find_common_slots


def test_common_availability_is_split_into_duration_slots():
    first = [
        (datetime(2026, 11, 10, 9), datetime(2026, 11, 10, 12)),
    ]
    second = [
        (datetime(2026, 11, 10, 10), datetime(2026, 11, 10, 12)),
    ]

    result = find_common_slots([first, second], 60)
    assert result == [
        (datetime(2026, 11, 10, 10), datetime(2026, 11, 10, 11)),
        (datetime(2026, 11, 10, 11), datetime(2026, 11, 10, 12)),
    ]


def test_overlapping_windows_do_not_duplicate_candidate_slots():
    windows = [[
        (datetime(2026, 11, 10, 9), datetime(2026, 11, 10, 11)),
        (datetime(2026, 11, 10, 10), datetime(2026, 11, 10, 12)),
    ]]

    result = find_common_slots(windows, 60)
    assert result == [
        (datetime(2026, 11, 10, 9), datetime(2026, 11, 10, 10)),
        (datetime(2026, 11, 10, 10), datetime(2026, 11, 10, 11)),
        (datetime(2026, 11, 10, 11), datetime(2026, 11, 10, 12)),
    ]


def test_no_common_availability_returns_no_slots():
    windows = [
        [(datetime(2026, 11, 10, 9), datetime(2026, 11, 10, 10))],
        [(datetime(2026, 11, 10, 11), datetime(2026, 11, 10, 12))],
    ]
    assert find_common_slots(windows, 30) == []


def test_slot_calculation_rejects_non_positive_duration():
    with pytest.raises(ValueError, match="greater than zero"):
        find_common_slots([], 0)


def test_scheduling_request_creation_and_duration_validation(
    client: TestClient, seeded, auth_headers
):
    base_url = "/meetings/" + str(seeded["meeting"].id) + "/scheduling-requests/"
    created = client.post(
        base_url,
        headers=auth_headers(),
        json={"duration_minutes": 30},
    )
    assert created.status_code == 200
    assert created.json()["status"] == "pending"

    invalid = client.post(
        base_url,
        headers=auth_headers(),
        json={"duration_minutes": 0},
    )
    assert invalid.status_code == 422


def test_scheduling_request_requires_organizer(
    client: TestClient, seeded, auth_headers
):
    response = client.post(
        "/meetings/" + str(seeded["meeting"].id) + "/scheduling-requests/",
        headers=auth_headers("participant@example.com"),
        json={"duration_minutes": 30},
    )
    assert response.status_code == 403


def test_calculate_candidate_slots_and_reject_repeat_transition(
    client: TestClient, seeded, auth_headers, db_session: Session
):
    meeting = seeded["meeting"]
    db_session.add(
        Availability(
            participant_id=seeded["participant"].id,
            start_time=datetime(2026, 11, 10, 9),
            end_time=datetime(2026, 11, 10, 11),
        )
    )
    request = SchedulingRequest(
        meeting_id=meeting.id,
        created_by=seeded["owner"].id,
        duration_minutes=60,
        status="pending",
    )
    db_session.add(request)
    db_session.commit()

    response = client.post(
        "/meetings/" + str(meeting.id) + "/scheduling-requests/"
        + str(request.id) + "/calculate",
        headers=auth_headers(),
    )
    assert response.status_code == 200
    assert response.json() == [
        {"start_time": "2026-11-10T09:00:00", "end_time": "2026-11-10T10:00:00"},
        {"start_time": "2026-11-10T10:00:00", "end_time": "2026-11-10T11:00:00"},
    ]

    repeated = client.post(
        "/meetings/" + str(meeting.id) + "/scheduling-requests/"
        + str(request.id) + "/calculate",
        headers=auth_headers(),
    )
    assert repeated.status_code == 400


def test_calculate_with_no_common_availability_returns_empty_list(
    client: TestClient, seeded, auth_headers, db_session: Session
):
    meeting = seeded["meeting"]
    owner_participant = Participant(
        meeting_id=meeting.id,
        user_id=seeded["owner"].id,
        status="invited",
    )
    db_session.add(owner_participant)
    db_session.flush()
    db_session.add_all([
        Availability(
            participant_id=seeded["participant"].id,
            start_time=datetime(2026, 11, 10, 9),
            end_time=datetime(2026, 11, 10, 10),
        ),
        Availability(
            participant_id=owner_participant.id,
            start_time=datetime(2026, 11, 10, 11),
            end_time=datetime(2026, 11, 10, 12),
        ),
    ])
    request = SchedulingRequest(
        meeting_id=meeting.id,
        created_by=seeded["owner"].id,
        duration_minutes=30,
        status="pending",
    )
    db_session.add(request)
    db_session.commit()

    response = client.post(
        "/meetings/" + str(meeting.id) + "/scheduling-requests/"
        + str(request.id) + "/calculate",
        headers=auth_headers(),
    )
    assert response.status_code == 200
    assert response.json() == []


def test_participant_can_find_slots_and_no_availability_returns_empty(
    client: TestClient, seeded, auth_headers, db_session: Session
):
    path = "/meetings/" + str(seeded["meeting"].id) + "/schedule/"
    headers = auth_headers()

    no_availability = client.post(path, headers=headers, json={"duration_minutes": 30})
    assert no_availability.status_code == 200
    assert no_availability.json() == []

    db_session.add(
        Availability(
            participant_id=seeded["participant"].id,
            start_time=datetime(2026, 11, 10, 9),
            end_time=datetime(2026, 11, 10, 10),
        )
    )
    db_session.commit()
    candidates = client.post(path, headers=headers, json={"duration_minutes": 30})
    assert candidates.status_code == 200
    assert len(candidates.json()) == 2


def test_select_slot_cancel_and_complete_transitions(
    client: TestClient, seeded, auth_headers
):
    meeting_id = seeded["meeting"].id
    headers = auth_headers()
    selected = client.post(
        "/meetings/" + str(meeting_id) + "/schedule",
        headers=headers,
        json={
            "start_time": "2026-11-10T09:00:00",
            "end_time": "2026-11-10T10:00:00",
        },
    )
    assert selected.status_code == 200
    assert selected.json()["status"] == "scheduled"

    completed = client.post(
        "/meetings/" + str(meeting_id) + "/complete",
        headers=headers,
    )
    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"

    invalid_cancel = client.post(
        "/meetings/" + str(meeting_id) + "/cancel",
        headers=headers,
    )
    assert invalid_cancel.status_code == 400


def test_invalid_slot_and_cancellation_transitions(
    client: TestClient, seeded, auth_headers
):
    meeting_id = seeded["meeting"].id
    headers = auth_headers()
    invalid_slot = client.post(
        "/meetings/" + str(meeting_id) + "/schedule",
        headers=headers,
        json={
            "start_time": "2026-11-10T10:00:00",
            "end_time": "2026-11-10T09:00:00",
        },
    )
    assert invalid_slot.status_code == 422

    cancelled = client.post(
        "/meetings/" + str(meeting_id) + "/cancel",
        headers=headers,
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"

    repeated_cancel = client.post(
        "/meetings/" + str(meeting_id) + "/cancel",
        headers=headers,
    )
    assert repeated_cancel.status_code == 400

    schedule_cancelled = client.post(
        "/meetings/" + str(meeting_id) + "/schedule",
        headers=headers,
        json={
            "start_time": "2026-11-10T09:00:00",
            "end_time": "2026-11-10T10:00:00",
        },
    )
    assert schedule_cancelled.status_code == 400

    complete_cancelled = client.post(
        "/meetings/" + str(meeting_id) + "/complete",
        headers=headers,
    )
    assert complete_cancelled.status_code == 400
