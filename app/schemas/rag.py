from pydantic import BaseModel


class RagAskRequest(BaseModel):
    knowledge_base_id: int
    question: str
    top_k: int = 5


class RagSourceChunk(BaseModel):
    document_id: int
    chunk_id: int
    chunk_index: int
    content: str
    score: float


class RagAskResponse(BaseModel):
    answer: str
    sources: list[RagSourceChunk]
