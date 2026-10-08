from datetime import datetime

from pydantic import BaseModel, Field


class SchedulingRequestCreate(BaseModel):
    duration_minutes: int = Field(gt=0)


class SchedulingSlot(BaseModel):
    start_time: datetime
    end_time: datetime