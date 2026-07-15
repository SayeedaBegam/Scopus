import csv, hashlib, io
from fastapi import HTTPException

ALIASES={"authors":["authors","author(s)"],"title":["title","document title"],"year":["year","publication year"],"source":["source title","journal"],"affiliations":["affiliations","author affiliations"],"authors_with_affiliations":["authors with affiliations"],"doi":["doi"],"eid":["eid"],"citations":["cited by"],"document_type":["document type"]}
def parse_csv(data:bytes):
    text=None
    for encoding in ("utf-8-sig","utf-8","latin-1"):
        try: text=data.decode(encoding); break
        except UnicodeDecodeError: pass
    dialect=csv.Sniffer().sniff(text[:4096],delimiters=",;\t"); rows=list(csv.DictReader(io.StringIO(text),dialect=dialect)); columns=list(rows[0]) if rows else []
    mapping={key:next((c for c in columns if c.strip().casefold() in options),None) for key,options in ALIASES.items()}
    missing=[x for x in ("title","year","affiliations") if not mapping[x]]
    return {"mapping":mapping,"missing_required":missing,"rows":rows,"preview":rows[:10]}
def synthetic_eid(row,mapping): return "CSV-"+hashlib.sha256(f"{row.get(mapping['title'])}|{row.get(mapping['year'])}|{row.get(mapping['doi'])}".encode()).hexdigest()[:24]
