from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.auth_dependencies import get_current_user
from app.api.dependencies import get_db
from app.models.meeting import Meeting
from app.models.scheduling_request import SchedulingRequest
from app.models.user import User
from app.schemas.scheduling_request import (
    SchedulingRequestCreate,
    SchedulingRequestResponse
)

router = APIRouter(
    prefix="/meetings/{meeting_id}/scheduling-requests",
    tags=["Scheduling Requests"]
)


@router.post(
    "/",
    response_model=SchedulingRequestResponse
)
def create_scheduling_request(
    meeting_id: int,
    request_data: SchedulingRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    meeting = db.get(Meeting, meeting_id)

    if meeting is None:
        raise HTTPException(
            status_code=404,
            detail="Meeting not found"
        )

    if meeting.organizer_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Only the organizer can request scheduling"
        )

    scheduling_request = SchedulingRequest(
        meeting_id=meeting_id,
        created_by=current_user.id,
        duration_minutes=request_data.duration_minutes,
        status="pending"
    )

    db.add(scheduling_request)
    db.commit()
    db.refresh(scheduling_request)

    return scheduling_request

from app.models.availability import Availability
from app.models.participant import Participant
from app.schemas.scheduling_request import SchedulingSlot
from app.services.scheduling import find_common_slots

@router.post(
    "/{request_id}/calculate",
    response_model=list[SchedulingSlot]
)
def calculate_scheduling_request(
    meeting_id: int,
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    meeting = db.get(Meeting, meeting_id)

    if meeting is None:
        raise HTTPException(
            status_code=404,
            detail="Meeting not found"
        )

    if meeting.organizer_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Only the organizer can calculate scheduling"
        )

    scheduling_request = db.get(
        SchedulingRequest,
        request_id
    )

    if scheduling_request is None:
        raise HTTPException(
            status_code=404,
            detail="Scheduling request not found"
        )

    if scheduling_request.meeting_id != meeting_id:
        raise HTTPException(
            status_code=400,
            detail="Scheduling request does not belong to this meeting"
        )

    if scheduling_request.status != "pending":
        raise HTTPException(
            status_code=400,
            detail="Only pending scheduling requests can be calculated"
        )

    participants = (
        db.query(Participant)
        .filter(
            Participant.meeting_id == meeting_id
        )
        .all()
    )

    if not participants:
        raise HTTPException(
            status_code=400,
            detail="Meeting has no participants"
        )

    availability_windows = []

    for participant in participants:
        slots = (
            db.query(Availability)
            .filter(
                Availability.participant_id == participant.id
            )
            .order_by(Availability.start_time)
            .all()
        )

        if not slots:
            return []

        participant_slots = [
            (
                slot.start_time,
                slot.end_time
            )
            for slot in slots
        ]

        availability_windows.append(
            participant_slots
        )

    common_slots = find_common_slots(
        availability_windows,
        scheduling_request.duration_minutes
    )

    scheduling_request.status = "calculated"

    db.commit()

    return [
        SchedulingSlot(
            start_time=start,
            end_time=end
        )
        for start, end in common_slots
    ]