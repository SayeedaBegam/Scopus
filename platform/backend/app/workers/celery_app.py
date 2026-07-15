from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery=Celery("utn",broker=settings.redis_url,backend=settings.redis_url,include=["app.workers.tasks"])
celery.conf.update(task_serializer="json",result_serializer="json",timezone="UTC",beat_schedule={"weekly-scopus-sync":{"task":"app.workers.tasks.sync_all","schedule":crontab(hour=2,minute=0,day_of_week="sun")}})
