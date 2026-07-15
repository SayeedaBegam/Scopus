from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.models import Department,Institution,InternationalCollaboration,Professor,ProfessorPublication,Publication,ReviewItem,ReviewStatus

def analytics(db:Session,professor_id:int|None=None):
    collab=select(InternationalCollaboration)
    pubs=select(ProfessorPublication.publication_id)
    if professor_id: collab=collab.where(InternationalCollaboration.professor_id==professor_id); pubs=pubs.where(ProfessorPublication.professor_id==professor_id)
    collaborations=db.scalars(collab).all(); pub_ids=set(db.scalars(pubs).all()); publications=db.scalars(select(Publication).where(Publication.id.in_(pub_ids))).all() if pub_ids else []
    institutions={x.id:x for x in db.scalars(select(Institution)).all()}; professors={x.id:x for x in db.scalars(select(Professor)).all()}
    def counts(values):
        out={}
        for value in values:
            if value is not None: out[str(value)]=out.get(str(value),0)+1
        return [{"name":k,"value":v} for k,v in sorted(out.items(),key=lambda x:(-x[1],x[0]))]
    professor_rows=[]
    for p in professors.values():
        if professor_id and p.id!=professor_id: continue
        if not professor_id and not p.is_active: continue
        rows=[x for x in collaborations if x.professor_id==p.id]
        professor_rows.append({"id":p.id,"name":p.full_name,"international_publications":len({x.publication_id for x in rows}),"partner_institutions":len({x.institution_id for x in rows}),"partner_countries":len({x.country for x in rows}),"collaboration_records":len(rows)})
    professor_rows.sort(key=lambda x:(-x["international_publications"],x["name"]))
    return {"summary":{"professors_monitored":db.scalar(select(func.count()).select_from(Professor).where(Professor.is_active)) if not professor_id else 1,"total_publications":len(publications),"international_publications":len({x.publication_id for x in collaborations}),"collaboration_records":len(collaborations),"partner_countries":len({x.country for x in collaborations}),"partner_institutions":len({x.institution_id for x in collaborations}),"needs_review":db.scalar(select(func.count()).select_from(ReviewItem).where(ReviewItem.status==ReviewStatus.pending))},"by_year":counts(x.year for x in collaborations),"publications_by_year":counts(x.year for x in publications),"by_country":counts(x.country for x in collaborations),"by_institution":counts(institutions[x.institution_id].canonical_name for x in collaborations if x.institution_id in institutions),"by_professor":counts(professors[x.professor_id].full_name for x in collaborations if x.professor_id in professors),"professor_directory":professor_rows}
