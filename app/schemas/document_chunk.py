from datetime import datetime

from pydantic import BaseModel


class DocumentChunkRead(BaseModel):
    id: int
    document_id: int
    chunk_index: int
    content: str
    content_length: int
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentChunkResult(BaseModel):
    document_id: int
    chunk_count: int
    message: str
