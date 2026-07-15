import re, unicodedata
from dataclasses import dataclass
from app.core.config import settings

COUNTRIES={
 "germany":("Germany","DE"),"deutschland":("Germany","DE"),"de":("Germany","DE"),"deu":("Germany","DE"),
 "united kingdom":("United Kingdom","GB"),"uk":("United Kingdom","GB"),"england":("United Kingdom","GB"),
 "canada":("Canada","CA"),"united states":("United States","US"),"usa":("United States","US"),
 "france":("France","FR"),"spain":("Spain","ES"),"italy":("Italy","IT"),"austria":("Austria","AT"),
 "switzerland":("Switzerland","CH"),"netherlands":("Netherlands","NL"),"china":("China","CN"),
 "japan":("Japan","JP"),"australia":("Australia","AU"),"india":("India","IN"),"singapore":("Singapore","SG")}

def normalize(value:str)->str:
    value=unicodedata.normalize("NFKC",value or "").casefold().replace("univ.","university")
    return re.sub(r"\s+"," ",re.sub(r"[^\w\s]"," ",value)).strip()

def country_from(raw:str, structured:str|None=None):
    candidates=[structured or ""]+list(reversed([p.strip() for p in (raw or "").split(",")]))
    for part in candidates:
        key=normalize(part)
        if key in COUNTRIES: return (*COUNTRIES[key],1.0)
    text=f" {normalize(raw)} "
    for key,(name,code) in COUNTRIES.items():
        if f" {key} " in text: return name,code,.85
    if any(x in text for x in (" munich "," nuremberg "," nürnberg "," berlin "," erlangen "," hamburg ")): return "Germany","DE",.7
    return None,None,0.0

def is_utn(name:str,affiliation_id:str|None=None)->bool:
    ids={x.strip() for x in settings.utn_affiliation_ids.split(",") if x.strip()}
    aliases={normalize(x) for x in settings.utn_aliases.split("|")}
    return bool(affiliation_id and affiliation_id in ids) or normalize(name) in aliases

@dataclass
class Resolution:
    canonical_name:str; normalized_alias:str; country:str|None; country_code:str|None; confidence:float; is_german:bool; is_utn:bool; needs_review:bool

def resolve_affiliation(raw:str,name:str|None=None,country:str|None=None,affiliation_id:str|None=None)->Resolution:
    canonical=(name or (raw.split(",")[0] if raw else "Unknown institution")).strip()
    c,code,score=country_from(raw,country)
    utn=is_utn(canonical,affiliation_id); german=code=="DE"
    return Resolution(canonical,normalize(canonical),c,code,score,german,utn,not c or score<.8)
