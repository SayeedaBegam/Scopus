import asyncio, os
from sqlalchemy import select
from app.core.database import Base,SessionLocal,engine
from app.core.security import hash_password
from app.models import Department,Lab,Professor,ProfessorScopusId,Role,User
from app.services.scopus.sync import synchronize_professor

def seed(sync_mock=True):
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        admin_password=os.getenv("SEED_ADMIN_PASSWORD","DevAdmin!Change2026")
        viewer_password=os.getenv("SEED_VIEWER_PASSWORD","DevViewer!Change2026")
        if not db.scalar(select(User).where(User.email=="admin@utn.de")): db.add_all([User(name="Development Admin",email="admin@utn.de",password_hash=hash_password(admin_password),role=Role.admin),User(name="Development Viewer",email="viewer@utn.de",password_hash=hash_password(viewer_password),role=Role.viewer)])
        if not db.scalar(select(Department)):
            cs=Department(name="Computer Science and Artificial Intelligence",code="CSAI"); eng=Department(name="Engineering",code="ENG"); db.add_all([cs,eng]); db.flush(); labs=[Lab(department_id=cs.id,name="Machine Learning Lab"),Lab(department_id=cs.id,name="Data Systems Lab"),Lab(department_id=eng.id,name="Robotics Lab")]; db.add_all(labs); db.flush()
            specs=[("Prof. Anna Keller","57200000001",cs.id,labs[0].id,"Machine learning"),("Prof. Markus Vogel","57200000002",cs.id,labs[1].id,"Data systems"),("Prof. Lena Hoffmann","57200000003",eng.id,labs[2].id,"Robotics")]
            for name,sid,did,lid,area in specs:
                p=Professor(full_name=name,academic_title="Professor",department_id=did,lab_id=lid,research_area=area,email=name.split()[-1].lower()+"@utn.de",scopus_author_id=sid,scopus_profile_url=f"https://www.scopus.com/authid/detail.uri?authorId={sid}",profile_status="confirmed"); db.add(p); db.flush(); db.add(ProfessorScopusId(professor_id=p.id,scopus_author_id=sid,is_primary=True))
        db.commit()
        if sync_mock:
            for p in db.scalars(select(Professor).where(Professor.scopus_author_id.is_not(None))).all(): asyncio.run(synchronize_professor(db,p,"seed"))
if __name__=="__main__": seed()
