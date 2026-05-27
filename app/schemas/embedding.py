from pydantic import BaseModel


class DocumentEmbeddingResult(BaseModel):
    document_id: int
    embedded_chunk_count: int
    message: str


class DocumentPrepareResult(BaseModel):
    document_id: int
    status: str
    text_length: int
    chunk_count: int
    embedded_chunk_count: int
    message: str