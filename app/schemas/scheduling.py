from datetime import datetime

from pydantic import BaseModel


class SchedulingRequestCreate(BaseModel):
    duration_minutes: int


class SchedulingSlot(BaseModel):
    start_time: datetime
    end_time: datetime