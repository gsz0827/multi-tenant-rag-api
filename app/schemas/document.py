from datetime import datetime

from pydantic import BaseModel

from typing import Any


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


class DocumentProcessResult(BaseModel):
    id: int
    status: str
    text_length: int
    message: str


class DocumentPrepareAsyncResult(BaseModel):
    document_id: int
    task_id: str | None = None
    status: str
    message: str


class DocumentIngestionStatusResult(BaseModel):
    document_id: int
    document_status: str
    task_id: str | None = None
    celery_status: str | None = None
    error_message: str | None = None
    result: Any | None = None


class DocumentPrepareBatchAsyncItem(BaseModel):
    document_id: int
    filename: str
    status: str
    task_id: str | None = None
    message: str


class DocumentPrepareBatchAsyncResult(BaseModel):
    knowledge_base_id: int
    total_count: int
    queued_count: int
    skipped_count: int
    results: list[DocumentPrepareBatchAsyncItem]


class DocumentIngestionStatusBatchItem(BaseModel):
    document_id: int
    filename: str
    document_status: str
    task_id: str | None = None
    celery_status: str | None = None
    error_message: str | None = None


class DocumentIngestionStatusBatchResult(BaseModel):
    knowledge_base_id: int
    total_count: int
    completed_count: int
    failed_count: int
    queued_count: int
    processing_count: int
    pending_count: int
    results: list[DocumentIngestionStatusBatchItem]