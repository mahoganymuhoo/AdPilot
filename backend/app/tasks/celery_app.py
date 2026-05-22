from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "adpilot",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.sync_tasks", "app.tasks.strategy_monitor"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_soft_time_limit=300,  # 5 dakika
    task_time_limit=600,       # 10 dakika
    beat_schedule={
        "sync-etsy-every-15-minutes": {
            "task": "app.tasks.sync_tasks.sync_all_etsy_shops",
            "schedule": settings.ETSY_SYNC_INTERVAL_SECONDS,
        },
        "run-anomaly-detection-hourly": {
            "task": "app.tasks.sync_tasks.run_anomaly_detection",
            "schedule": crontab(minute=0),  # Her saat başı
        },
        "check-active-strategies-hourly": {
            "task": "app.tasks.strategy_monitor.check_active_strategies",
            "schedule": crontab(minute=30),  # Her saat 30'unda (anomali ile çakışmasın)
        },
    },
)
