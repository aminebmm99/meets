from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.auth_dependencies import get_current_user
from app.api.dependencies import get_db
from app.models.availability import Availability
from app.models.meeting import Meeting
from app.models.participant import Participant
from app.models.user import User
from app.schemas.scheduling import (
    SchedulingRequestCreate,
    SchedulingSlot
)
from app.services.scheduling import find_common_slots

router = APIRouter(
    prefix="/meetings/{meeting_id}/schedule",
    tags=["Scheduling"]
)
@router.post(
    "/",
    response_model=list[SchedulingSlot]
)
def find_scheduling_slots(
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

    if meeting.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this meeting"
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
                availability.start_time,
                availability.end_time
            )
            for availability in slots
        ]

        availability_windows.append(
            participant_slots
        )

    common_slots = find_common_slots(
        availability_windows,
        request_data.duration_minutes
    )

    return [
        SchedulingSlot(
            start_time=start,
            end_time=end
        )
        for start, end in common_slots
    ]