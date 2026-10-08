from datetime import datetime

from pydantic import BaseModel, model_validator


class SelectSlotRequest(BaseModel):
    start_time: datetime
    end_time: datetime

    @model_validator(mode="after")
    def validate_time_range(self):
        start_is_naive = self.start_time.utcoffset() is None
        end_is_naive = self.end_time.utcoffset() is None
        if start_is_naive != end_is_naive:
            raise ValueError("Both times must use the same timezone format")
        if self.start_time >= self.end_time:
            raise ValueError("Start time must be before end time")
        return self