from pydantic import BaseModel


class DocumentEmbeddingResult(BaseModel):
    document_id: int
    embedded_chunk_count: int
    message: str
