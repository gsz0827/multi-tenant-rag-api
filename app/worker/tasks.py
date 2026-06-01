from app.db.session import SessionLocal
from app.services.document_ingestion import prepare_document_for_rag_sync
from app.worker.celery_app import celery_app


@celery_app.task(bind=True, name="documents.prepare")
def prepare_document_task(self, document_id: int, force: bool = False) -> dict:
    db = SessionLocal()

    try:
        result = prepare_document_for_rag_sync(
            db=db,
            document_id=document_id,
            force=force,
        )
        return result
    finally:
        db.close()