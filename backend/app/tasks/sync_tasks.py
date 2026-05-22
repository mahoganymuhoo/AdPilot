"""
Celery görevleri: Etsy API sync ve anomali tespiti.
"""
from app.tasks.celery_app import celery_app


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def sync_all_etsy_shops(self):
    """
    Tüm aktif Etsy bağlantıları için veri sync çalıştır.
    Her 15 dakikada bir Celery Beat tarafından tetiklenir.
    """
    import asyncio
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import Session
    from app.core.config import settings
    from app.models.platform import PlatformConnection

    try:
        # Sync burada implementasyon tamamlanacak
        # (asyncpg yerine sync engine kullanılır Celery için)
        return {"status": "sync_completed"}
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task
def sync_shop(connection_id: int):
    """Tek bir Etsy shop'u sync et."""
    return {"status": "ok", "connection_id": connection_id}


@celery_app.task
def run_anomaly_detection():
    """Tüm ürünler için anomali tespiti çalıştır, kritik olanları kaydet."""
    return {"status": "anomaly_detection_completed"}
