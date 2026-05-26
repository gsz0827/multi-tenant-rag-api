from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    username: str | None = None
    full_name: str | None = None


class UserRead(BaseModel):
    id: int
    email: EmailStr
    username: str | None = None
    full_name: str | None = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True