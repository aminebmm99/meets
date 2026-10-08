from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class MeetingCreate(BaseModel):
    title: str
    description: Optional[str] = None
    organization_id: int


class MeetingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: Optional[str]
    organizer_id: int
    organization_id: int
    created_at: datetime

class MeetingUpdate(BaseModel):
    title: str
    description: Optional[str] = None