from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from typing import Optional
from sqlalchemy.orm import Session

from app.api.auth_dependencies import get_current_user
from app.api.dependencies import get_db
from app.models.meeting import Meeting
from app.models.participant import Participant
from app.models.user import User
from app.schemas.participant import (
    ParticipantCreate,
    ParticipantResponse
)

router = APIRouter(
    prefix="/meetings/{meeting_id}/participants",
    tags=["Participants"]
)


@router.post(
    "/",
    response_model=ParticipantResponse
)
def add_participant(
    meeting_id: int,
    participant_data: ParticipantCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    meeting = db.get(Meeting, meeting_id)

    if meeting is None:
        raise HTTPException(
            status_code=404,
            detail="Meeting not found"
        )

    # Only the organizer can add participants
    if meeting.organizer_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Only the organizer can add participants"
        )

    user = db.get(User, participant_data.user_id)

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # User must belong to the same organization
    if user.organization_id != meeting.organization_id:
        raise HTTPException(
            status_code=403,
            detail="User does not belong to the meeting organization"
        )

    existing_participant = (
        db.query(Participant)
        .filter(
            Participant.user_id == participant_data.user_id,
            Participant.meeting_id == meeting_id
        )
        .first()
    )

    if existing_participant is not None:
        raise HTTPException(
            status_code=409,
            detail="User is already a participant"
        )

    participant = Participant(
        user_id=participant_data.user_id,
        meeting_id=meeting_id,
        status="invited"
    )

    db.add(participant)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="User is already a participant"
        )
    db.refresh(participant)

    return participant
@router.get(
    "/",
    response_model=list[ParticipantResponse]
)
def get_participants(
    meeting_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: Optional[int] = Query(None, ge=1, le=100),
    offset: int = Query(0, ge=0)
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

    query = (
        db.query(Participant)
        .filter(Participant.meeting_id == meeting_id)
        .order_by(Participant.id)
    )
    if limit is not None:
        query = query.limit(limit)
    participants = query.offset(offset).all()

    return participants






@router.delete(
    "/{participant_id}"
)
def remove_participant(
    meeting_id: int,
    participant_id: int,
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
            detail="Only the organizer can remove participants"
        )

    participant = db.get(Participant, participant_id)

    if participant is None:
        raise HTTPException(
            status_code=404,
            detail="Participant not found"
        )

    if participant.meeting_id != meeting_id:
        raise HTTPException(
            status_code=400,
            detail="Participant does not belong to this meeting"
        )

    db.delete(participant)
    db.commit()

    return {
        "message": "Participant removed successfully"
    }