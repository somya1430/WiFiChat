from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class Credentials(BaseModel):
    username: str = Field(min_length=3, max_length=30)
    password: str = Field(min_length=8, max_length=72)

    @field_validator("password")
    @classmethod
    def password_fits_bcrypt(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must be at most 72 UTF-8 bytes")
        return value


class UserRead(BaseModel):
    id: int
    username: str

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class RoomCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class RoomRead(BaseModel):
    id: int
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageCreate(BaseModel):
    body: str = Field(min_length=1, max_length=2000)


class MessageRead(BaseModel):
    id: int
    room_id: int
    author_name: str
    body: str
    created_at: datetime


class ParticipantRead(BaseModel):
    id: int
    username: str
