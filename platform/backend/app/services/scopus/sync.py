import hashlib
import json
import re
from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import (
    Institution,
    InstitutionAlias,
    InternationalCollaboration,
    Professor,
    ProfessorPublication,
    Publication,
    PublicationAuthorAffiliation,
    ReviewItem,
    ReviewStatus,
    SyncRun,
)
from app.services.affiliations.normalizer import resolve_affiliation
from app.services.scopus.client import get_scopus_client


PARSER_VERSION = 3


def _value(data, *keys, default=None):
    for key in keys:
        if data.get(key) not in (None, ""):
            return data[key]
    return default


def _as_list(value):
    if value in (None, ""):
        return []
    return value if isinstance(value, list) else [value]


def _integer(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _author_name(author: dict) -> str | None:
    preferred = author.get("preferred-name") or {}
    return _value(
        author,
        "ce:indexed-name",
        default=_value(preferred, "ce:indexed-name")
        or " ".join(
            part
            for part in (
                _value(author, "ce:given-name", default=_value(preferred, "ce:given-name")),
                _value(author, "ce:surname", default=_value(preferred, "ce:surname")),
            )
            if part
        )
        or None,
    )


def _author_group_details(response: dict) -> dict[str, dict]:
    item = response.get("item") or {}
    head = ((item.get("bibrecord") or {}).get("head") or {}) if isinstance(item, dict) else {}
    groups: dict[str, dict] = {}
    for group in _as_list(head.get("author-group")):
        group_authors = [name for name in (_author_name(author) for author in _as_list(group.get("author"))) if name]
        for affiliation in _as_list(group.get("affiliation")):
            affiliation_id_data = affiliation.get("affiliation-id") or {}
            affiliation_id = affiliation.get("@afid") or affiliation_id_data.get("@afid")
            if not affiliation_id:
                continue
            organizations = [
                value.get("$") if isinstance(value, dict) else str(value)
                for value in _as_list(affiliation.get("organization"))
            ]
            organizations = [value for value in organizations if value]
            details = groups.setdefault(str(affiliation_id), {"authors": [], "departments": []})
            details["authors"].extend(group_authors)
            details["departments"].extend(organizations[:-1] if len(organizations) > 1 else [])
            details["source_text"] = affiliation.get("ce:source-text") or details.get("source_text")
            details["country"] = affiliation.get("country") or details.get("country")
            details["organization"] = organizations[-1] if organizations else details.get("organization")
    return groups


def _live_affiliations(response: dict, authors: list[dict]) -> list[dict]:
    group_details = _author_group_details(response)
    authors_by_affiliation: dict[str, list[str]] = {}
    for author in authors:
        name = _author_name(author)
        for affiliation in _as_list(author.get("affiliation")):
            affiliation_id = affiliation.get("@id") or affiliation.get("id")
            if affiliation_id and name:
                authors_by_affiliation.setdefault(str(affiliation_id), []).append(name)

    normalized = []
    for affiliation in _as_list(response.get("affiliation")):
        affiliation_id = affiliation.get("@id") or affiliation.get("id")
        group = group_details.get(str(affiliation_id), {})
        name = affiliation.get("affilname") or affiliation.get("name") or group.get("organization") or "Unknown institution"
        city = affiliation.get("affiliation-city") or affiliation.get("city")
        country = affiliation.get("affiliation-country") or affiliation.get("country") or group.get("country")
        raw = group.get("source_text") or ", ".join(dict.fromkeys(str(part) for part in (name, city, country) if part))
        researcher_names = group.get("authors") or authors_by_affiliation.get(str(affiliation_id), [])
        normalized.append(
            {
                "id": str(affiliation_id) if affiliation_id else None,
                "name": name,
                "country": country,
                "raw": raw,
                "author": "; ".join(dict.fromkeys(researcher_names)) or None,
                "department": "; ".join(dict.fromkeys(group.get("departments", []))) or None,
            }
        )
    return normalized


def parse_publication_details(details: dict) -> dict:
    """Normalize both Elsevier's nested live response and the flat mock format."""
    response = details.get("abstracts-retrieval-response")
    if not isinstance(response, dict):
        response = details
    core = response.get("coredata")
    if not isinstance(core, dict):
        core = details

    live_authors = _as_list((response.get("authors") or {}).get("author")) if isinstance(response.get("authors"), dict) else []
    authors = live_authors or _as_list(details.get("authors"))
    affiliations = _live_affiliations(response, authors) if response is not details else _as_list(details.get("affiliations"))

    date_value = _value(core, "year", "prism:coverDate", "prism:coverDisplayDate")
    year_match = re.search(r"\b(?:19|20)\d{2}\b", str(date_value or ""))
    year = int(year_match.group()) if year_match else None

    return {
        "eid": _value(core, "eid", default=_value(details, "eid", "dc:identifier")),
        "scopus_id": _value(core, "scopus_id", "dc:identifier"),
        "doi": _value(core, "doi", "prism:doi"),
        "title": _value(core, "title", "dc:title", default="Untitled"),
        "source_title": _value(core, "source_title", "prism:publicationName"),
        "year": year,
        "document_type": _value(core, "document_type", "subtypeDescription"),
        "author_count": len(authors),
        "citation_count": _integer(_value(core, "citation_count", "citedby-count", default=0)),
        "affiliations": affiliations,
    }


def _fingerprint(details: dict) -> str:
    source = {key: value for key, value in details.items() if key != "_fingerprint"}
    encoded = json.dumps(source, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str).encode()
    return f"v{PARSER_VERSION}:{hashlib.sha256(encoded).hexdigest()}"


def _institution(db: Session, aff: dict):
    raw = aff.get("raw") or aff.get("name", "")
    result = resolve_affiliation(raw, aff.get("name"), aff.get("country"), aff.get("id"))
    inst = None
    if aff.get("id"):
        inst = db.scalar(select(Institution).where(Institution.scopus_affiliation_id == str(aff["id"])))
    if not inst:
        alias = db.scalar(select(InstitutionAlias).where(InstitutionAlias.normalized_alias == result.normalized_alias))
        inst = db.get(Institution, alias.institution_id) if alias else None
    if not inst:
        inst = Institution(
            scopus_affiliation_id=str(aff["id"]) if aff.get("id") else None,
            canonical_name=result.canonical_name,
            country=result.country,
            country_code=result.country_code,
            is_german=result.is_german,
            is_utn=result.is_utn,
            verified=not result.needs_review,
        )
        db.add(inst)
        db.flush()
        db.add(
            InstitutionAlias(
                institution_id=inst.id,
                alias=result.canonical_name,
                normalized_alias=result.normalized_alias,
                source="scopus",
            )
        )
    return inst, result


def _apply_details(db: Session, pub: Publication, professor: Professor, details: dict, run: SyncRun | None = None):
    parsed = parse_publication_details(details)
    pub.scopus_id = parsed["scopus_id"]
    pub.doi = parsed["doi"]
    pub.title = parsed["title"]
    pub.source_title = parsed["source_title"]
    pub.year = parsed["year"]
    pub.document_type = parsed["document_type"]
    pub.author_count = parsed["author_count"]
    pub.citation_count = parsed["citation_count"]
    pub.raw_metadata_json = {
        **{key: value for key, value in details.items() if key != "_fingerprint"},
        "_fingerprint": _fingerprint(details),
    }
    pub.last_scopus_updated_at = datetime.now(timezone.utc)
    db.flush()

    db.execute(delete(PublicationAuthorAffiliation).where(PublicationAuthorAffiliation.publication_id == pub.id))
    db.execute(
        delete(InternationalCollaboration).where(
            InternationalCollaboration.publication_id == pub.id,
            InternationalCollaboration.professor_id == professor.id,
        )
    )
    seen = set()
    for aff in parsed["affiliations"]:
        inst, result = _institution(db, aff)
        db.flush()
        db.add(
            PublicationAuthorAffiliation(
                publication_id=pub.id,
                institution_id=inst.id,
                raw_affiliation_text=aff.get("raw") or aff.get("name", ""),
                raw_affiliation_json=aff,
                department_text=aff.get("department"),
            )
        )
        if result.needs_review:
            db.add(
                ReviewItem(
                    entity_type="institution",
                    entity_id=inst.id,
                    reason="Country or institution needs review",
                    original_value_json=aff,
                    proposed_value_json={"country": result.country},
                )
            )
            if run:
                run.review_items_created += 1
        if inst.is_german or inst.is_utn or not inst.country or inst.id in seen:
            continue
        seen.add(inst.id)
        db.add(
            InternationalCollaboration(
                publication_id=pub.id,
                professor_id=professor.id,
                institution_id=inst.id,
                country=inst.country,
                country_code=inst.country_code,
                year=pub.year,
                confidence_score=result.confidence,
                review_status=ReviewStatus.pending if result.needs_review else ReviewStatus.verified,
                international_coauthor=aff.get("author"),
                partner_department=aff.get("department"),
            )
        )


def reprocess_professor_metadata(db: Session, professor: Professor) -> int:
    publications = db.scalars(
        select(Publication)
        .join(ProfessorPublication)
        .where(ProfessorPublication.professor_id == professor.id)
    ).all()
    for pub in publications:
        _apply_details(db, pub, professor, pub.raw_metadata_json)
    professor.last_successful_sync_at = datetime.now(timezone.utc)
    db.commit()
    return len(publications)


async def synchronize_professor(db: Session, professor: Professor, sync_type="incremental"):
    if not professor.scopus_author_id:
        raise ValueError("Confirm a Scopus Author ID before updating")
    run = SyncRun(professor_id=professor.id, sync_type=sync_type)
    db.add(run)
    db.commit()
    client = get_scopus_client()
    try:
        entries = await client.search_publications_by_author(professor.scopus_author_id)
        run.records_fetched = len(entries)
        for entry in entries:
            eid = _value(entry, "eid", "dc:identifier")
            if not eid:
                continue
            existing = db.scalar(select(Publication).where(Publication.scopus_eid == eid))
            details = await client.get_abstract_details(eid) or entry
            fingerprint = _fingerprint(details)
            if existing and existing.raw_metadata_json.get("_fingerprint") == fingerprint:
                run.records_skipped += 1
                pub = existing
            else:
                parsed = parse_publication_details(details)
                pub = existing or Publication(scopus_eid=eid, title=parsed["title"])
                if not existing:
                    db.add(pub)
                    run.records_created += 1
                else:
                    run.records_updated += 1
                db.flush()
                _apply_details(db, pub, professor, details, run)
            if not db.get(ProfessorPublication, {"professor_id": professor.id, "publication_id": pub.id}):
                db.add(ProfessorPublication(professor_id=professor.id, publication_id=pub.id))
        professor.last_successful_sync_at = datetime.now(timezone.utc)
        run.status = "completed"
        run.completed_at = datetime.now(timezone.utc)
        run.api_requests = client.requests
        remaining = client.quota.get("X-RateLimit-Remaining")
        run.quota_remaining = int(remaining) if remaining else None
        db.commit()
        return run
    except Exception as exc:
        db.rollback()
        run = db.get(SyncRun, run.id)
        run.status = "failed"
        run.completed_at = datetime.now(timezone.utc)
        run.error_message = str(exc)
        db.commit()
        raise
