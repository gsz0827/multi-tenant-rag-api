from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "multi_tenant_rag_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.worker.tasks"],
)

celery_app.conf.task_track_started = True
celery_app.conf.task_routes = {
    "documents.prepare": {"queue": "ingestion"},
}
