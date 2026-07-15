import asyncio
from sqlalchemy import select
from app.core.database import SessionLocal
from app.models import Professor
from app.services.scopus.sync import synchronize_professor
from app.workers.celery_app import celery

@celery.task(name="app.workers.tasks.sync_professor")
def sync_professor(professor_id:int):
    with SessionLocal() as db:
        p=db.get(Professor,professor_id)
        if p and p.is_active and p.scopus_author_id: return asyncio.run(synchronize_professor(db,p,"scheduled")).id
@celery.task(name="app.workers.tasks.sync_all")
def sync_all():
    with SessionLocal() as db: ids=list(db.scalars(select(Professor.id).where(Professor.is_active,Professor.scopus_author_id.is_not(None))))
    for pid in ids: sync_professor.delay(pid)
    return len(ids)
