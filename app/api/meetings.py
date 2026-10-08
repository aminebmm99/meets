from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.auth_dependencies import get_current_user
from app.api.dependencies import get_db
from app.models.meeting import Meeting
from app.models.organization import Organization
from app.models.user import User
from app.schemas.meeting import (
    MeetingCreate,
    MeetingResponse,
    MeetingUpdate
)

router = APIRouter(
    prefix="/meetings",
    tags=["Meetings"]
)


@router.post(
    "/",
    response_model=MeetingResponse
)
def create_meeting(
    meeting_data: MeetingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    organization = db.get(
        Organization,
        meeting_data.organization_id
    )

    if organization is None:
        raise HTTPException(
            status_code=404,
            detail="Organization not found"
        )

    if current_user.organization_id != organization.id:
        raise HTTPException(
            status_code=403,
            detail="You do not belong to this organization"
        )

    meeting = Meeting(
        title=meeting_data.title,
        description=meeting_data.description,
        organizer_id=current_user.id,
        organization_id=organization.id
    )

    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    return meeting


@router.get(
    "/",
    response_model=list[MeetingResponse]
)
def get_meetings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    meetings = (
        db.query(Meeting)
        .filter(
            Meeting.organization_id == current_user.organization_id
        )
        .all()
    )

    return meetings


@router.get(
    "/{meeting_id}",
    response_model=MeetingResponse
)
def get_meeting(
    meeting_id: int,
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

    return meeting


@router.put(
    "/{meeting_id}",
    response_model=MeetingResponse
)
def update_meeting(
    meeting_id: int,
    meeting_data: MeetingUpdate,
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
            detail="Only the organizer can update this meeting"
        )

    meeting.title = meeting_data.title
    meeting.description = meeting_data.description

    db.commit()
    db.refresh(meeting)

    return meeting


@router.delete(
    "/{meeting_id}"
)
def delete_meeting(
    meeting_id: int,
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
            detail="Only the organizer can delete this meeting"
        )

    db.delete(meeting)
    db.commit()

    return {
        "message": "Meeting deleted successfully"
    }