from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SchedulingRequestCreate(BaseModel):
    duration_minutes: int = Field(gt=0)


class SchedulingSlot(BaseModel):
    start_time: datetime
    end_time: datetime


class SchedulingRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    meeting_id: int
    created_by: int
    duration_minutes: int
    status: str
    created_at: datetime