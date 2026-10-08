from pydantic import BaseModel, ConfigDict


class ParticipantCreate(BaseModel):
    user_id: int


class ParticipantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    meeting_id: int
    status: str