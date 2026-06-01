from app.db.session import SessionLocal
from app.models.document import Document
from app.services.document_ingestion import prepare_document_for_rag_sync
from app.worker.celery_app import celery_app


@celery_app.task(bind=True, name="documents.prepare")
def prepare_document_task(self, document_id: int, force: bool = False) -> dict:
    db = SessionLocal()

    try:
        document = db.query(Document).filter(Document.id == document_id).first()

        if document is None:
            raise ValueError("Document not found")

        if document.status == "cancelled":
            return {
                "document_id": document.id,
                "status": document.status,
                "text_length": len(document.extracted_text or ""),
                "chunk_count": 0,
                "embedded_chunk_count": 0,
                "message": "Document ingestion task was cancelled",
            }

        document.status = "processing"
        document.error_message = None
        db.commit()

        result = prepare_document_for_rag_sync(
            db=db,
            document_id=document_id,
            force=force,
        )

        return result

    except Exception as exc:
        db.rollback()

        document = db.query(Document).filter(Document.id == document_id).first()

        if document is not None and document.status != "cancelled":
            document.status = "failed"
            document.error_message = str(exc)
            db.commit()

        raise

    finally:
        db.close()