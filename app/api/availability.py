from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.auth_dependencies import get_current_user
from app.api.dependencies import get_db
from app.models.availability import Availability
from app.models.meeting import Meeting
from app.models.participant import Participant
from app.models.user import User
from app.schemas.availability import (
    AvailabilityCreate,
    AvailabilityResponse,
    AvailabilityUpdate
)

router = APIRouter(
    prefix="/meetings/{meeting_id}/availability",
    tags=["Availability"]
)


@router.post(
    "/",
    response_model=AvailabilityResponse
)
def create_availability(
    meeting_id: int,
    availability_data: AvailabilityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    meeting = db.get(Meeting, meeting_id)

    if meeting is None:
        raise HTTPException(
            status_code=404,
            detail="Meeting not found"
        )

    participant = (
        db.query(Participant)
        .filter(
            Participant.meeting_id == meeting_id,
            Participant.user_id == current_user.id
        )
        .first()
    )

    if participant is None:
        raise HTTPException(
            status_code=403,
            detail="You are not a participant of this meeting"
        )

    if availability_data.start_time >= availability_data.end_time:
        raise HTTPException(
            status_code=400,
            detail="Start time must be before end time"
        )

    availability = Availability(
        participant_id=participant.id,
        start_time=availability_data.start_time,
        end_time=availability_data.end_time
    )

    db.add(availability)
    db.commit()
    db.refresh(availability)

    return availability


@router.put(
    "/{availability_id}",
    response_model=AvailabilityResponse
)
def update_availability(
    meeting_id: int,
    availability_id: int,
    availability_data: AvailabilityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    availability = db.get(
        Availability,
        availability_id
    )

    if availability is None:
        raise HTTPException(
            status_code=404,
            detail="Availability not found"
        )

    participant = db.get(
        Participant,
        availability.participant_id
    )

    if participant is None:
        raise HTTPException(
            status_code=404,
            detail="Participant not found"
        )

    if participant.meeting_id != meeting_id:
        raise HTTPException(
            status_code=400,
            detail="Availability does not belong to this meeting"
        )

    if participant.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only update your own availability"
        )

    if availability_data.start_time >= availability_data.end_time:
        raise HTTPException(
            status_code=400,
            detail="Start time must be before end time"
        )

    availability.start_time = availability_data.start_time
    availability.end_time = availability_data.end_time

    db.commit()
    db.refresh(availability)

    return availability

@router.delete(
    "/{availability_id}"
)
def delete_availability(
    meeting_id: int,
    availability_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    availability = db.get(
        Availability,
        availability_id
    )

    if availability is None:
        raise HTTPException(
            status_code=404,
            detail="Availability not found"
        )

    participant = db.get(
        Participant,
        availability.participant_id
    )

    if participant is None:
        raise HTTPException(
            status_code=404,
            detail="Participant not found"
        )

    if participant.meeting_id != meeting_id:
        raise HTTPException(
            status_code=400,
            detail="Availability does not belong to this meeting"
        )

    if participant.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only delete your own availability"
        )

    db.delete(availability)
    db.commit()

    return {
        "message": "Availability deleted successfully"
    }