from datetime import datetime

from pydantic import BaseModel, validator


class RagAskRequest(BaseModel):
    knowledge_base_id: int
    question: str
    top_k: int = 5
    answer_language: str = "auto"


class RagSourceChunk(BaseModel):
    document_id: int
    filename: str
    chunk_id: int
    chunk_index: int
    content: str
    score: float


class RagAskResponse(BaseModel):
    answer: str
    sources: list[RagSourceChunk]
    history_id: int | None = None


class RagHistoryItem(BaseModel):
    id: int
    knowledge_base_id: int
    user_id: int
    question: str
    answer: str
    sources: list[dict]
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class RagHistoryListResponse(BaseModel):
    knowledge_base_id: int
    total: int
    skip: int
    limit: int
    items: list[RagHistoryItem]


class RagHistoryDeleteResponse(BaseModel):
    knowledge_base_id: int
    deleted_count: int
    message: str    


class RagExportRequest(BaseModel):
    format: str = "pdf"

    @validator("format")
    def validate_format(cls, v):
        if v.lower() not in {"pdf", "markdown"}:
            raise ValueError("format must be 'pdf' or 'markdown'")
        return v.lower()