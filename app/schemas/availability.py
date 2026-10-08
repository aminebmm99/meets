from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AvailabilityCreate(BaseModel):
    start_time: datetime
    end_time: datetime


class AvailabilityUpdate(BaseModel):
    start_time: datetime
    end_time: datetime


class AvailabilityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    participant_id: int
    start_time: datetime
    end_time: datetime