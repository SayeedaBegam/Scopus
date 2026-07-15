from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from app.models import Role, ReviewStatus

class ORM(BaseModel): model_config=ConfigDict(from_attributes=True)
class Login(BaseModel): email: EmailStr; password: str
class UserOut(ORM): id:int; name:str; email:EmailStr; role:Role; is_active:bool
class ProfessorCreate(BaseModel):
    full_name:str=Field(min_length=2,max_length=240); academic_title:str|None=None; department_id:int|None=None; lab_id:int|None=None; research_area:str|None=None; email:EmailStr|None=None; orcid:str|None=None; scopus_author_id:str|None=None; institution_name:str="University of Technology Nuremberg"; photo_url:str|None=None

    @field_validator("email", "research_area", mode="before")
    @classmethod
    def blank_optional_fields_are_none(cls, value):
        return None if isinstance(value, str) and not value.strip() else value
class ProfessorPatch(BaseModel):
    full_name:str|None=None; academic_title:str|None=None; department_id:int|None=None; lab_id:int|None=None; research_area:str|None=None; email:EmailStr|None=None; orcid:str|None=None; institution_name:str|None=None; photo_url:str|None=None
class ProfessorDelete(BaseModel): password:str=Field(min_length=1,max_length=200)
class ProfessorOut(ORM):
    id:int; full_name:str; academic_title:str|None; department_id:int|None; lab_id:int|None; research_area:str|None; email:str|None; orcid:str|None; scopus_author_id:str|None; scopus_profile_url:str|None; institution_name:str; photo_url:str|None; profile_status:str; is_active:bool; last_successful_sync_at:datetime|None; metrics:dict[str,Any]={}
class ScopusSearch(BaseModel): surname:str; given_name:str|None=None; institution:str|None="University of Technology Nuremberg"; orcid:str|None=None
class ConfirmProfile(BaseModel): scopus_author_id:str; is_primary:bool=True
class CollaborationPatch(BaseModel): institution_id:int|None=None; country:str|None=None; country_code:str|None=None; review_status:ReviewStatus|None=None; notes:str|None=None
class ReviewPatch(BaseModel): status:ReviewStatus; proposed_value_json:dict[str,Any]={}; notes:str|None=None
class DownloadCreate(BaseModel): report_scope:str; professor_id:int|None=None; filters_json:dict[str,Any]={}; reason:str=Field(min_length=3,max_length=2000)
class Decision(BaseModel): reviewer_note:str|None=None
class UserCreate(BaseModel):
    name:str=Field(min_length=2,max_length=200); email:EmailStr; password:str=Field(min_length=12,max_length=200); role:Role=Role.viewer
class UserPatch(BaseModel):
    name:str|None=Field(default=None,min_length=2,max_length=200); email:EmailStr|None=None; password:str|None=Field(default=None,min_length=12,max_length=200); role:Role|None=None; is_active:bool|None=None
