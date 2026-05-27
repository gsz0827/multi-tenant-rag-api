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

class DocumentPrepareItemResult(BaseModel):
    document_id: int
    filename: str
    status: str
    text_length: int = 0
    chunk_count: int = 0
    embedded_chunk_count: int = 0
    message: str


class DocumentPrepareBatchResult(BaseModel):
    knowledge_base_id: int
    total_count: int
    success_count: int
    failed_count: int
    results: list[DocumentPrepareItemResult]