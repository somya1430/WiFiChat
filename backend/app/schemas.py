from datetime import datetime

from pydantic import BaseModel, Field


class RoomCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class RoomRead(BaseModel):
    id: int
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageCreate(BaseModel):
    author_name: str = Field(min_length=1, max_length=30)
    body: str = Field(min_length=1, max_length=2000)


class MessageRead(BaseModel):
    id: int
    room_id: int
    author_name: str
    body: str
    created_at: datetime
