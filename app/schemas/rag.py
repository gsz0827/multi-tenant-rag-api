from datetime import datetime

from pydantic import BaseModel


class RagAskRequest(BaseModel):
    knowledge_base_id: int
    question: str
    top_k: int = 5


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