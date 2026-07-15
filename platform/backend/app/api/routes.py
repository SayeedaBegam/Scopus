import csv,io,json,os,secrets
from datetime import datetime,timezone
from fastapi import APIRouter,BackgroundTasks,Depends,File,Header,HTTPException,Query,Response,UploadFile
from fastapi.responses import JSONResponse,StreamingResponse
from sqlalchemy import delete,func,or_,select
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.core.security import allow,current_user,hash_password,make_token,verify_password
from app.models import *
from app.schemas import *
from app.services.affiliations.normalizer import resolve_affiliation
from app.services.analytics.service import analytics
from app.services.exports.excel import export_workbook
from app.services.imports import parse_csv,synthetic_eid
from app.services.scopus.client import get_scopus_client
from app.services.scopus.sync import synchronize_professor

router=APIRouter()
def audit(db,user,action,entity,obj,old=None,new=None): db.add(AuditLog(user_id=user.id,action=action,entity_type=entity,entity_id=obj,old_value_json=old or {},new_value_json=new or {}))
def professor_dict(db,p):
    pubs=db.scalar(select(func.count()).select_from(ProfessorPublication).where(ProfessorPublication.professor_id==p.id)); cs=db.scalars(select(InternationalCollaboration).where(InternationalCollaboration.professor_id==p.id)).all()
    return {**ProfessorOut.model_validate(p).model_dump(exclude={"metrics"}),"metrics":{"total_publications":pubs,"international_publications":len({x.publication_id for x in cs}),"collaborations":len(cs),"institutions":len({x.institution_id for x in cs}),"countries":len({x.country for x in cs}),"top_country":max({x.country for x in cs},key=lambda c:sum(y.country==c for y in cs),default=None)}}

@router.get("/health")
def health(): return {"status":"ok","service":"utn-collaboration-api","scopus_mode":settings.scopus_mode}
@router.post("/scheduled/scopus-sync")
async def scheduled_scopus_sync(x_sync_secret:str|None=Header(default=None),db:Session=Depends(get_db)):
    if not settings.scheduled_sync_secret:
        raise HTTPException(503,"Scheduled synchronization is not configured")
    if not x_sync_secret or not secrets.compare_digest(x_sync_secret,settings.scheduled_sync_secret):
        raise HTTPException(401,"Invalid synchronization secret")
    professors=db.scalars(select(Professor).where(Professor.is_active.is_(True),Professor.scopus_author_id.is_not(None)).order_by(Professor.id)).all()
    completed=[]; failed=[]
    for professor in professors:
        try:
            run=await synchronize_professor(db,professor,"scheduled")
            completed.append({"professor_id":professor.id,"name":professor.full_name,"fetched":run.records_fetched})
        except Exception as exc:
            failed.append({"professor_id":professor.id,"name":professor.full_name,"error":str(exc)[:500]})
    payload={"status":"completed" if not failed else "completed_with_errors","completed":completed,"failed":failed}
    return JSONResponse(status_code=502,content=payload) if failed else payload
@router.post("/auth/login")
def login(body:Login,response:Response,db:Session=Depends(get_db)):
    user=db.scalar(select(User).where(User.email==body.email.lower()))
    if not user or not user.is_active or not verify_password(body.password,user.password_hash): raise HTTPException(401,"Invalid email or password")
    response.set_cookie("utn_session",make_token(user),httponly=True,samesite="lax",secure=settings.environment=="production",max_age=settings.access_token_minutes*60); return {"user":UserOut.model_validate(user)}
@router.post("/auth/logout")
def logout(response:Response): response.delete_cookie("utn_session"); return {"ok":True}
@router.get("/auth/me",response_model=UserOut)
def me(user=Depends(current_user)): return user

@router.get("/professors")
def professors(q:str|None=None,active:bool=True,include_inactive:bool=False,db:Session=Depends(get_db),_=Depends(current_user)):
    stmt=select(Professor)
    if q: stmt=stmt.where(Professor.full_name.ilike(f"%{q}%"))
    if not include_inactive: stmt=stmt.where(Professor.is_active==active)
    return [professor_dict(db,p) for p in db.scalars(stmt.order_by(Professor.full_name)).all()]
@router.post("/professors",status_code=201)
def add_professor(body:ProfessorCreate,db:Session=Depends(get_db),user=Depends(allow(Role.admin))):
    p=Professor(**body.model_dump(),profile_status="confirmed" if body.scopus_author_id else "unconfirmed"); db.add(p); db.flush()
    if p.scopus_author_id: db.add(ProfessorScopusId(professor_id=p.id,scopus_author_id=p.scopus_author_id,is_primary=True))
    audit(db,user,"create","professor",p.id,new=body.model_dump(mode="json")); db.commit(); return professor_dict(db,p)
@router.get("/professors/{professor_id}")
def professor(professor_id:int,db:Session=Depends(get_db),_=Depends(current_user)):
    p=db.get(Professor,professor_id)
    if not p: raise HTTPException(404,"Professor not found")
    return professor_dict(db,p)
@router.patch("/professors/{professor_id}")
def patch_professor(professor_id:int,body:ProfessorPatch,db:Session=Depends(get_db),user=Depends(allow(Role.admin))):
    p=db.get(Professor,professor_id)
    if not p: raise HTTPException(404,"Professor not found")
    old=professor_dict(db,p); [setattr(p,k,v) for k,v in body.model_dump(exclude_unset=True).items()]; audit(db,user,"update","professor",p.id,old=old,new=body.model_dump(exclude_unset=True,mode="json")); db.commit(); return professor_dict(db,p)
def _set_professor_active(professor_id:int,active:bool,db:Session,user:User):
    p=db.get(Professor,professor_id)
    if not p: raise HTTPException(404,"Professor not found")
    p.is_active=active; audit(db,user,"activate" if active else "deactivate","professor",p.id); db.commit(); return {"is_active":p.is_active}
@router.post("/professors/{professor_id}/activate")
def activate_professor(professor_id:int,db:Session=Depends(get_db),user=Depends(allow(Role.admin))): return _set_professor_active(professor_id,True,db,user)
@router.post("/professors/{professor_id}/deactivate")
def deactivate_professor(professor_id:int,db:Session=Depends(get_db),user=Depends(allow(Role.admin))): return _set_professor_active(professor_id,False,db,user)
@router.delete("/professors/{professor_id}")
def delete_professor(professor_id:int,body:ProfessorDelete,db:Session=Depends(get_db),user=Depends(allow(Role.admin))):
    if not verify_password(body.password,user.password_hash): raise HTTPException(403,"Admin password is incorrect")
    professor=db.get(Professor,professor_id)
    if not professor: raise HTTPException(404,"Professor not found")
    publication_ids=set(db.scalars(select(ProfessorPublication.publication_id).where(ProfessorPublication.professor_id==professor_id)).all())
    old={"id":professor.id,"full_name":professor.full_name,"scopus_author_id":professor.scopus_author_id}
    db.execute(delete(DownloadRequest).where(DownloadRequest.professor_id==professor_id))
    db.execute(delete(SyncRun).where(SyncRun.professor_id==professor_id))
    db.execute(delete(InternationalCollaboration).where(InternationalCollaboration.professor_id==professor_id))
    db.execute(delete(ProfessorPublication).where(ProfessorPublication.professor_id==professor_id))
    db.execute(delete(ProfessorScopusId).where(ProfessorScopusId.professor_id==professor_id))
    db.delete(professor); db.flush()
    if publication_ids:
        shared=set(db.scalars(select(ProfessorPublication.publication_id).where(ProfessorPublication.publication_id.in_(publication_ids))).all())
        orphaned=publication_ids-shared
        if orphaned:
            db.execute(delete(InternationalCollaboration).where(InternationalCollaboration.publication_id.in_(orphaned)))
            db.execute(delete(PublicationAuthorAffiliation).where(PublicationAuthorAffiliation.publication_id.in_(orphaned)))
            db.execute(delete(Publication).where(Publication.id.in_(orphaned)))
    audit(db,user,"delete","professor",professor_id,old=old); db.commit()
    return {"removed_id":professor_id,"removed_name":old["full_name"]}
@router.post("/professors/search-scopus")
async def search_scopus(body:ScopusSearch,_=Depends(allow(Role.admin)),client=Depends(get_scopus_client)): return await client.search_authors(body.surname,body.given_name,body.institution,body.orcid)
@router.post("/professors/{professor_id}/confirm-scopus-profile")
def confirm(professor_id:int,body:ConfirmProfile,db:Session=Depends(get_db),user=Depends(allow(Role.admin))):
    p=db.get(Professor,professor_id)
    if not p: raise HTTPException(404,"Professor not found")
    if db.scalar(select(ProfessorScopusId).where(ProfessorScopusId.scopus_author_id==body.scopus_author_id,ProfessorScopusId.professor_id!=professor_id)): raise HTTPException(409,"This Scopus profile is linked to another professor")
    link=db.scalar(select(ProfessorScopusId).where(ProfessorScopusId.professor_id==professor_id,ProfessorScopusId.scopus_author_id==body.scopus_author_id))
    if not link: db.add(ProfessorScopusId(professor_id=professor_id,scopus_author_id=body.scopus_author_id,is_primary=body.is_primary))
    if body.is_primary: p.scopus_author_id=body.scopus_author_id; p.scopus_profile_url=f"https://www.scopus.com/authid/detail.uri?authorId={body.scopus_author_id}"; p.profile_status="confirmed"
    audit(db,user,"confirm_scopus_profile","professor",p.id,new=body.model_dump()); db.commit(); return professor_dict(db,p)
@router.post("/professors/{professor_id}/sync")
async def sync(professor_id:int,db:Session=Depends(get_db),_=Depends(allow(Role.admin))):
    p=db.get(Professor,professor_id)
    if not p: raise HTTPException(404,"Professor not found")
    try: run=await synchronize_professor(db,p,"manual"); return {"sync_run_id":run.id,"status":run.status,"fetched":run.records_fetched,"created":run.records_created,"updated":run.records_updated}
    except ValueError as e: raise HTTPException(422,str(e))
@router.get("/professors/{professor_id}/sync-runs")
def sync_runs(professor_id:int,db:Session=Depends(get_db),_=Depends(current_user)): return db.scalars(select(SyncRun).where(SyncRun.professor_id==professor_id).order_by(SyncRun.started_at.desc())).all()

@router.get("/publications")
def publications(year:int|None=None,db:Session=Depends(get_db),_=Depends(current_user)):
    stmt=select(Publication); stmt=stmt.where(Publication.year==year) if year else stmt; return db.scalars(stmt.order_by(Publication.year.desc())).all()
@router.get("/professors/{professor_id}/publications")
def professor_publications(professor_id:int,db:Session=Depends(get_db),_=Depends(current_user)): return db.scalars(select(Publication).join(ProfessorPublication).where(ProfessorPublication.professor_id==professor_id)).all()
@router.get("/collaborations")
def collaborations(professor_id:int|None=None,country:str|None=None,db:Session=Depends(get_db),_=Depends(current_user)):
    stmt=select(InternationalCollaboration); stmt=stmt.where(InternationalCollaboration.professor_id==professor_id) if professor_id else stmt; stmt=stmt.where(InternationalCollaboration.country==country) if country else stmt
    items=db.scalars(stmt).all()
    institutions={x.id:x for x in db.scalars(select(Institution).where(Institution.id.in_({x.institution_id for x in items}))).all()} if items else {}
    publications={x.id:x for x in db.scalars(select(Publication).where(Publication.id.in_({x.publication_id for x in items}))).all()} if items else {}
    return [{
        "id":item.id,"publication_id":item.publication_id,"professor_id":item.professor_id,"institution_id":item.institution_id,
        "international_coauthor":item.international_coauthor,"partner_department":item.partner_department,"country":item.country,
        "country_code":item.country_code,"year":item.year,"confidence_score":item.confidence_score,"review_status":item.review_status,
        "notes":item.notes,"institution_name":institutions[item.institution_id].canonical_name if item.institution_id in institutions else "Unknown institution",
        "publication_title":publications[item.publication_id].title if item.publication_id in publications else "Untitled",
        "source_title":publications[item.publication_id].source_title if item.publication_id in publications else None,
        "doi":publications[item.publication_id].doi if item.publication_id in publications else None,
        "author_count":publications[item.publication_id].author_count if item.publication_id in publications else 0,
        "citation_count":publications[item.publication_id].citation_count if item.publication_id in publications else 0,
        "scopus_eid":publications[item.publication_id].scopus_eid if item.publication_id in publications else None,
    } for item in items]
@router.patch("/collaborations/{item_id}")
def patch_collaboration(item_id:int,body:CollaborationPatch,db:Session=Depends(get_db),user=Depends(allow(Role.admin,Role.reviewer))):
    item=db.get(InternationalCollaboration,item_id)
    if not item: raise HTTPException(404,"Collaboration not found")
    [setattr(item,k,v) for k,v in body.model_dump(exclude_unset=True).items()]; audit(db,user,"update","collaboration",item.id,new=body.model_dump(exclude_unset=True,mode="json")); db.commit(); return item
@router.delete("/collaborations/{item_id}",status_code=204)
def remove_collaboration(item_id:int,db:Session=Depends(get_db),user=Depends(allow(Role.admin))): item=db.get(InternationalCollaboration,item_id); db.delete(item) if item else None; audit(db,user,"remove","collaboration",item_id); db.commit()

@router.get("/analytics/overall")
def overall(db:Session=Depends(get_db),_=Depends(current_user)): return analytics(db)
@router.get("/analytics/professors/{professor_id}")
def professor_analytics(professor_id:int,db:Session=Depends(get_db),_=Depends(current_user)): return analytics(db,professor_id)
@router.get("/reviews")
def reviews(status:ReviewStatus|None=ReviewStatus.pending,db:Session=Depends(get_db),_=Depends(allow(Role.admin,Role.reviewer))): stmt=select(ReviewItem); stmt=stmt.where(ReviewItem.status==status) if status else stmt; return db.scalars(stmt).all()
@router.patch("/reviews/{item_id}")
def review(item_id:int,body:ReviewPatch,db:Session=Depends(get_db),user=Depends(allow(Role.admin,Role.reviewer))):
    item=db.get(ReviewItem,item_id)
    if not item: raise HTTPException(404,"Review item not found")
    item.status=body.status; item.proposed_value_json=body.proposed_value_json; item.notes=body.notes; item.reviewed_by=user.id; item.reviewed_at=datetime.now(timezone.utc); audit(db,user,"review","review_item",item.id,new=body.model_dump(mode="json")); db.commit(); return item
@router.post("/institutions/merge")
def merge_institutions(source_id:int,target_id:int,db:Session=Depends(get_db),user=Depends(allow(Role.admin,Role.reviewer))):
    if source_id==target_id or not db.get(Institution,target_id): raise HTTPException(422,"Choose two different institutions")
    for row in db.scalars(select(InstitutionAlias).where(InstitutionAlias.institution_id==source_id)): row.institution_id=target_id
    for row in db.scalars(select(PublicationAuthorAffiliation).where(PublicationAuthorAffiliation.institution_id==source_id)): row.institution_id=target_id
    for row in db.scalars(select(InternationalCollaboration).where(InternationalCollaboration.institution_id==source_id)):
        duplicate=db.scalar(select(InternationalCollaboration).where(InternationalCollaboration.publication_id==row.publication_id,InternationalCollaboration.professor_id==row.professor_id,InternationalCollaboration.institution_id==target_id)); db.delete(row) if duplicate else setattr(row,"institution_id",target_id)
    source=db.get(Institution,source_id); db.delete(source); audit(db,user,"merge","institution",target_id,old={"source_id":source_id}); db.commit(); return {"merged":True}

@router.post("/imports/scopus-csv")
async def upload_csv(file:UploadFile=File(...),_=Depends(allow(Role.admin))):
    if not file.filename.lower().endswith(".csv"): raise HTTPException(415,"Upload a CSV file")
    data=await file.read(settings.max_csv_bytes+1)
    if len(data)>settings.max_csv_bytes: raise HTTPException(413,"CSV file is too large")
    parsed=parse_csv(data); return {"import_id":"preview","mapping":parsed["mapping"],"missing_required":parsed["missing_required"],"preview":parsed["preview"],"total_rows":len(parsed["rows"])}
@router.post("/imports/{import_id}/confirm")
async def confirm_csv(import_id:str,professor_id:int,file:UploadFile=File(...),db:Session=Depends(get_db),_=Depends(allow(Role.admin))):
    data=await file.read(settings.max_csv_bytes+1); parsed=parse_csv(data)
    if parsed["missing_required"]: raise HTTPException(422,{"missing_required":parsed["missing_required"]})
    p=db.get(Professor,professor_id)
    if not p: raise HTTPException(404,"Professor not found")
    created=0
    for row in parsed["rows"]:
        m=parsed["mapping"]; eid=row.get(m["eid"]) if m["eid"] else synthetic_eid(row,m); pub=db.scalar(select(Publication).where(Publication.scopus_eid==eid))
        if not pub: pub=Publication(scopus_eid=eid,doi=row.get(m["doi"]) if m["doi"] else None,title=row[m["title"]],source_title=row.get(m["source"]) if m["source"] else None,year=int(row[m["year"]]),document_type=row.get(m["document_type"]) if m["document_type"] else None,raw_metadata_json={"csv":row}); db.add(pub); db.flush(); created+=1
        if not db.get(ProfessorPublication,{"professor_id":p.id,"publication_id":pub.id}): db.add(ProfessorPublication(professor_id=p.id,publication_id=pub.id))
        for raw in row[m["affiliations"]].split(";"):
            res=resolve_affiliation(raw); inst=db.scalar(select(Institution).where(Institution.canonical_name==res.canonical_name,Institution.country_code==res.country_code))
            if not inst: inst=Institution(canonical_name=res.canonical_name,country=res.country,country_code=res.country_code,is_german=res.is_german,is_utn=res.is_utn,verified=not res.needs_review); db.add(inst); db.flush()
            if res.needs_review: db.add(ReviewItem(entity_type="institution",entity_id=inst.id,reason="CSV affiliation needs review",original_value_json={"raw":raw}))
            if not res.is_german and not res.is_utn and res.country and not db.scalar(select(InternationalCollaboration).where(InternationalCollaboration.publication_id==pub.id,InternationalCollaboration.professor_id==p.id,InternationalCollaboration.institution_id==inst.id)): db.add(InternationalCollaboration(publication_id=pub.id,professor_id=p.id,institution_id=inst.id,country=res.country,country_code=res.country_code,year=pub.year,confidence_score=res.confidence,review_status=ReviewStatus.pending if res.needs_review else ReviewStatus.verified))
    db.commit(); return {"created_publications":created,"processed_rows":len(parsed["rows"])}

def export_response(data:bytes,name:str): return StreamingResponse(io.BytesIO(data),media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",headers={"Content-Disposition":f'attachment; filename="{name}"'})
@router.post("/exports/professor/{professor_id}")
def export_professor(professor_id:int,db:Session=Depends(get_db),user=Depends(current_user)):
    if user.role==Role.viewer: raise HTTPException(403,"Request download access before exporting")
    return export_response(export_workbook(db,professor_id),f"professor-{professor_id}.xlsx")
@router.post("/exports/overall")
def export_overall(db:Session=Depends(get_db),user=Depends(allow(Role.admin))): return export_response(export_workbook(db),"utn-international-collaborations.xlsx")
@router.post("/download-requests",status_code=201)
def request_download(body:DownloadCreate,db:Session=Depends(get_db),user=Depends(current_user)): item=DownloadRequest(requested_by=user.id,**body.model_dump()); db.add(item); db.commit(); return item
@router.get("/download-requests")
def downloads(db:Session=Depends(get_db),user=Depends(current_user)): stmt=select(DownloadRequest); stmt=stmt if user.role==Role.admin else stmt.where(DownloadRequest.requested_by==user.id); return db.scalars(stmt.order_by(DownloadRequest.requested_at.desc())).all()
@router.patch("/download-requests/{item_id}/{decision}")
def decide_download(item_id:int,decision:str,body:Decision,db:Session=Depends(get_db),user=Depends(allow(Role.admin))):
    if decision not in ("approve","reject"): raise HTTPException(404)
    item=db.get(DownloadRequest,item_id)
    if not item: raise HTTPException(404,"Request not found")
    item.status="approved" if decision=="approve" else "rejected"; item.reviewed_by=user.id; item.reviewer_note=body.reviewer_note; item.reviewed_at=datetime.now(timezone.utc); db.commit(); return item
@router.get("/admin/sync-runs")
def all_syncs(db:Session=Depends(get_db),_=Depends(allow(Role.admin))): return db.scalars(select(SyncRun).order_by(SyncRun.started_at.desc())).all()
@router.get("/admin/audit-logs")
def audit_logs(db:Session=Depends(get_db),_=Depends(allow(Role.admin))): return db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc())).all()
@router.get("/admin/users")
def users(db:Session=Depends(get_db),_=Depends(allow(Role.admin))): return db.scalars(select(User).order_by(User.name)).all()
@router.post("/admin/users",status_code=201)
def create_user(body:UserCreate,db:Session=Depends(get_db),admin=Depends(allow(Role.admin))):
    email=body.email.lower()
    if db.scalar(select(User).where(User.email==email)): raise HTTPException(409,"An account with this email already exists")
    user=User(name=body.name.strip(),email=email,password_hash=hash_password(body.password),role=body.role)
    db.add(user); db.flush(); audit(db,admin,"create","user",user.id,new={"name":user.name,"email":user.email,"role":user.role.value}); db.commit()
    return UserOut.model_validate(user)
@router.patch("/admin/users/{user_id}",response_model=UserOut)
def update_user(user_id:int,body:UserPatch,db:Session=Depends(get_db),admin=Depends(allow(Role.admin))):
    user=db.get(User,user_id)
    if not user: raise HTTPException(404,"Account not found")
    changes=body.model_dump(exclude_unset=True)
    if user.id==admin.id and (changes.get("is_active") is False or ("role" in changes and changes["role"]!=Role.admin)):
        raise HTTPException(422,"You cannot deactivate or remove the administrator role from your own account")
    if "email" in changes:
        email=str(changes["email"]).lower()
        if db.scalar(select(User).where(User.email==email,User.id!=user.id)): raise HTTPException(409,"An account with this email already exists")
        user.email=email
    if "name" in changes: user.name=changes["name"].strip()
    if "role" in changes: user.role=changes["role"]
    if "is_active" in changes: user.is_active=changes["is_active"]
    if changes.get("password"): user.password_hash=hash_password(changes["password"])
    public_changes={key:(value.value if isinstance(value,Role) else value) for key,value in changes.items() if key!="password"}
    if "password" in changes: public_changes["password_reset"]=True
    audit(db,admin,"update","user",user.id,new=public_changes); db.commit()
    return UserOut.model_validate(user)
