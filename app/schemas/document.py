from datetime import datetime

from pydantic import BaseModel


class DocumentCreate(BaseModel):
    knowledge_base_id: int
    filename: str
    content_type: str | None = None
    file_size: int | None = None


class DocumentRead(BaseModel):
    id: int
    knowledge_base_id: int
    filename: str
    content_type: str | None = None
    file_size: int | None = None
    status: str
    error_message: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True
