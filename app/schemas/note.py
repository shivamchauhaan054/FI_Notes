from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class NoteCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=1, max_length=5000)

    @field_validator("title", "content")
    @classmethod
    def not_empty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("must not be empty")
        return value.strip()


class NoteUpdate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=1, max_length=5000)

    @field_validator("title", "content")
    @classmethod
    def not_empty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("must not be empty")
        return value.strip()


class NoteResponse(BaseModel):
    id: int
    title: str
    content: str
    owner_id: int
    is_pinned: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NoteVersionResponse(BaseModel):
    version_number: int
    title: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PinResponse(BaseModel):
    message: str
    is_pinned: bool


class ShareNoteRequest(BaseModel):
    share_with_email: EmailStr
