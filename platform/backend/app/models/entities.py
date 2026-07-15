import enum
from datetime import datetime, timezone
from sqlalchemy import Boolean, Date, DateTime, Enum, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


def now(): return datetime.now(timezone.utc)
class Role(str, enum.Enum): admin="admin"; viewer="viewer"; reviewer="reviewer"
class ReviewStatus(str, enum.Enum): pending="pending"; verified="verified"; rejected="rejected"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)


class User(TimestampMixin, Base):
    __tablename__="users"
    id: Mapped[int]=mapped_column(primary_key=True); name: Mapped[str]=mapped_column(String(200)); email: Mapped[str]=mapped_column(String(320),unique=True,index=True)
    password_hash: Mapped[str]=mapped_column(String(255)); role: Mapped[Role]=mapped_column(Enum(Role),default=Role.viewer); is_active: Mapped[bool]=mapped_column(Boolean,default=True)

class Department(Base):
    __tablename__="departments"
    id: Mapped[int]=mapped_column(primary_key=True); name: Mapped[str]=mapped_column(String(200),unique=True); code: Mapped[str]=mapped_column(String(30),unique=True); is_active: Mapped[bool]=mapped_column(Boolean,default=True)

class Lab(Base):
    __tablename__="labs"
    id: Mapped[int]=mapped_column(primary_key=True); department_id: Mapped[int]=mapped_column(ForeignKey("departments.id")); name: Mapped[str]=mapped_column(String(200)); is_active: Mapped[bool]=mapped_column(Boolean,default=True)
    __table_args__=(UniqueConstraint("department_id","name"),)

class Professor(TimestampMixin, Base):
    __tablename__="professors"
    id: Mapped[int]=mapped_column(primary_key=True); full_name: Mapped[str]=mapped_column(String(240),index=True); academic_title: Mapped[str|None]=mapped_column(String(100))
    department_id: Mapped[int|None]=mapped_column(ForeignKey("departments.id")); lab_id: Mapped[int|None]=mapped_column(ForeignKey("labs.id")); research_area: Mapped[str|None]=mapped_column(String(300)); email: Mapped[str|None]=mapped_column(String(320)); orcid: Mapped[str|None]=mapped_column(String(40)); scopus_author_id: Mapped[str|None]=mapped_column(String(40),index=True); scopus_profile_url: Mapped[str|None]=mapped_column(String(500)); institution_name: Mapped[str]=mapped_column(String(250),default="University of Technology Nuremberg"); photo_url: Mapped[str|None]=mapped_column(String(500)); profile_status: Mapped[str]=mapped_column(String(30),default="unconfirmed"); is_active: Mapped[bool]=mapped_column(Boolean,default=True); last_successful_sync_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True))
    department: Mapped[Department|None]=relationship(); lab: Mapped[Lab|None]=relationship()

class ProfessorScopusId(Base):
    __tablename__="professor_scopus_ids"
    id: Mapped[int]=mapped_column(primary_key=True); professor_id: Mapped[int]=mapped_column(ForeignKey("professors.id",ondelete="CASCADE")); scopus_author_id: Mapped[str]=mapped_column(String(40),unique=True); is_primary: Mapped[bool]=mapped_column(Boolean,default=False); confirmed_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)

class Publication(TimestampMixin, Base):
    __tablename__="publications"
    id: Mapped[int]=mapped_column(primary_key=True); scopus_eid: Mapped[str]=mapped_column(String(100),unique=True,index=True); scopus_id: Mapped[str|None]=mapped_column(String(50)); doi: Mapped[str|None]=mapped_column(String(300),index=True); title: Mapped[str]=mapped_column(Text); source_title: Mapped[str|None]=mapped_column(String(500)); year: Mapped[int|None]=mapped_column(Integer,index=True); publication_date: Mapped[datetime|None]=mapped_column(Date); document_type: Mapped[str|None]=mapped_column(String(100)); author_count: Mapped[int]=mapped_column(Integer,default=0); citation_count: Mapped[int]=mapped_column(Integer,default=0); raw_metadata_json: Mapped[dict]=mapped_column(JSON,default=dict); first_imported_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now); last_scopus_updated_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True))

class ProfessorPublication(Base):
    __tablename__="professor_publications"
    professor_id: Mapped[int]=mapped_column(ForeignKey("professors.id",ondelete="CASCADE"),primary_key=True); publication_id: Mapped[int]=mapped_column(ForeignKey("publications.id",ondelete="CASCADE"),primary_key=True); is_primary_utn_professor: Mapped[bool]=mapped_column(Boolean,default=True)

class Author(Base):
    __tablename__="authors"
    id: Mapped[int]=mapped_column(primary_key=True); scopus_author_id: Mapped[str|None]=mapped_column(String(40),unique=True); full_name: Mapped[str]=mapped_column(String(240)); orcid: Mapped[str|None]=mapped_column(String(40)); raw_metadata_json: Mapped[dict]=mapped_column(JSON,default=dict)

class Institution(TimestampMixin, Base):
    __tablename__="institutions"
    id: Mapped[int]=mapped_column(primary_key=True); scopus_affiliation_id: Mapped[str|None]=mapped_column(String(50),unique=True); canonical_name: Mapped[str]=mapped_column(String(500),index=True); city: Mapped[str|None]=mapped_column(String(200)); country: Mapped[str|None]=mapped_column(String(100)); country_code: Mapped[str|None]=mapped_column(String(3)); is_german: Mapped[bool]=mapped_column(Boolean,default=False,index=True); is_utn: Mapped[bool]=mapped_column(Boolean,default=False); verified: Mapped[bool]=mapped_column(Boolean,default=False)

class InstitutionAlias(Base):
    __tablename__="institution_aliases"
    id: Mapped[int]=mapped_column(primary_key=True); institution_id: Mapped[int]=mapped_column(ForeignKey("institutions.id",ondelete="CASCADE")); alias: Mapped[str]=mapped_column(String(500)); normalized_alias: Mapped[str]=mapped_column(String(500),unique=True,index=True); source: Mapped[str]=mapped_column(String(30),default="scopus")

class PublicationAuthorAffiliation(Base):
    __tablename__="publication_author_affiliations"
    id: Mapped[int]=mapped_column(primary_key=True); publication_id: Mapped[int]=mapped_column(ForeignKey("publications.id",ondelete="CASCADE")); author_id: Mapped[int|None]=mapped_column(ForeignKey("authors.id")); institution_id: Mapped[int|None]=mapped_column(ForeignKey("institutions.id")); department_text: Mapped[str|None]=mapped_column(String(500)); raw_affiliation_text: Mapped[str]=mapped_column(Text); raw_affiliation_json: Mapped[dict]=mapped_column(JSON,default=dict)

class InternationalCollaboration(TimestampMixin, Base):
    __tablename__="international_collaborations"
    id: Mapped[int]=mapped_column(primary_key=True); publication_id: Mapped[int]=mapped_column(ForeignKey("publications.id",ondelete="CASCADE")); professor_id: Mapped[int]=mapped_column(ForeignKey("professors.id",ondelete="CASCADE")); institution_id: Mapped[int]=mapped_column(ForeignKey("institutions.id")); international_coauthor: Mapped[str|None]=mapped_column(String(240)); partner_department: Mapped[str|None]=mapped_column(String(500)); country: Mapped[str]=mapped_column(String(100)); country_code: Mapped[str|None]=mapped_column(String(3)); year: Mapped[int|None]=mapped_column(Integer); confidence_score: Mapped[float]=mapped_column(Float,default=1); review_status: Mapped[ReviewStatus]=mapped_column(Enum(ReviewStatus),default=ReviewStatus.verified); notes: Mapped[str|None]=mapped_column(Text)
    __table_args__=(UniqueConstraint("publication_id","professor_id","institution_id",name="uq_collaboration"),)

class ReviewItem(Base):
    __tablename__="review_items"
    id: Mapped[int]=mapped_column(primary_key=True); entity_type: Mapped[str]=mapped_column(String(50)); entity_id: Mapped[int|None]=mapped_column(Integer); reason: Mapped[str]=mapped_column(String(200)); original_value_json: Mapped[dict]=mapped_column(JSON,default=dict); proposed_value_json: Mapped[dict]=mapped_column(JSON,default=dict); status: Mapped[ReviewStatus]=mapped_column(Enum(ReviewStatus),default=ReviewStatus.pending); assigned_to: Mapped[int|None]=mapped_column(ForeignKey("users.id")); reviewed_by: Mapped[int|None]=mapped_column(ForeignKey("users.id")); reviewed_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True)); notes: Mapped[str|None]=mapped_column(Text)

class SyncRun(Base):
    __tablename__="sync_runs"
    id: Mapped[int]=mapped_column(primary_key=True); professor_id: Mapped[int]=mapped_column(ForeignKey("professors.id")); sync_type: Mapped[str]=mapped_column(String(30)); started_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now); completed_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True)); status: Mapped[str]=mapped_column(String(30),default="running"); api_requests: Mapped[int]=mapped_column(Integer,default=0); records_fetched: Mapped[int]=mapped_column(Integer,default=0); records_created: Mapped[int]=mapped_column(Integer,default=0); records_updated: Mapped[int]=mapped_column(Integer,default=0); records_skipped: Mapped[int]=mapped_column(Integer,default=0); review_items_created: Mapped[int]=mapped_column(Integer,default=0); error_message: Mapped[str|None]=mapped_column(Text); quota_remaining: Mapped[int|None]=mapped_column(Integer)

class DownloadRequest(Base):
    __tablename__="download_requests"
    id: Mapped[int]=mapped_column(primary_key=True); requested_by: Mapped[int]=mapped_column(ForeignKey("users.id")); report_scope: Mapped[str]=mapped_column(String(30)); professor_id: Mapped[int|None]=mapped_column(ForeignKey("professors.id")); filters_json: Mapped[dict]=mapped_column(JSON,default=dict); reason: Mapped[str]=mapped_column(Text); status: Mapped[str]=mapped_column(String(30),default="pending"); reviewed_by: Mapped[int|None]=mapped_column(ForeignKey("users.id")); reviewer_note: Mapped[str|None]=mapped_column(Text); requested_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now); reviewed_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True)); exported_file_path: Mapped[str|None]=mapped_column(String(500))

class AuditLog(Base):
    __tablename__="audit_logs"
    id: Mapped[int]=mapped_column(primary_key=True); user_id: Mapped[int|None]=mapped_column(ForeignKey("users.id")); action: Mapped[str]=mapped_column(String(100)); entity_type: Mapped[str]=mapped_column(String(50)); entity_id: Mapped[int|None]=mapped_column(Integer); old_value_json: Mapped[dict]=mapped_column(JSON,default=dict); new_value_json: Mapped[dict]=mapped_column(JSON,default=dict); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
