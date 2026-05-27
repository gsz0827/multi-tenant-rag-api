from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    knowledge_base_id: int
    query: str
    top_k: int = Field(default=5, ge=1, le=20)


class SearchResultChunk(BaseModel):
    document_id: int
    document_filename: str
    chunk_id: int
    chunk_index: int
    content: str
    score: float


class SearchResponse(BaseModel):
    knowledge_base_id: int
    query: str
    results: list[SearchResultChunk]
