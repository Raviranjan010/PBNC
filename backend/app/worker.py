import logging
import threading
from backend.app.core.celery_app import celery_app
from backend.app.core import database
from backend.app.services.pipeline import ExtractionPipeline

logger = logging.getLogger(__name__)

@celery_app.task(name="process_document_task", bind=True, max_retries=2)
def process_document_task(self, document_id: str, job_id: str):
    """
    Celery background worker task for processing uploaded documents.
    """
    logger.info(f"Starting Celery processing task for document {document_id}, job {job_id}")
    db = database.SyncSessionLocal()
    try:
        ExtractionPipeline.execute_pipeline(db, document_id, job_id)
    except Exception as exc:
        logger.error(f"Error processing document {document_id}: {exc}")
        # Retry for transient failures if needed
        try:
            self.retry(exc=exc, countdown=5)
        except Exception:
            pass
    finally:
        db.close()

def dispatch_document_task(document_id: str, job_id: str) -> None:
    """
    Dispatches document to Celery. If Celery task_always_eager is enabled or
    broker is unavailable, executes in-process or via thread.
    """
    from backend.app.core.config import settings
    if settings.CELERY_TASK_ALWAYS_EAGER:
        db = database.SyncSessionLocal()
        try:
            ExtractionPipeline.execute_pipeline(db, document_id, job_id)
        finally:
            db.close()
        return

    try:
        process_document_task.delay(document_id, job_id)
    except Exception as exc:
        logger.warning(f"Celery broker unavailable ({exc}); falling back to background thread execution.")
        def run_sync():
            db = database.SyncSessionLocal()
            try:
                ExtractionPipeline.execute_pipeline(db, document_id, job_id)
            finally:
                db.close()
        t = threading.Thread(target=run_sync, daemon=True)
        t.start()
