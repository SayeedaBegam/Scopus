# Entity relationship diagram

```mermaid
erDiagram
  USERS ||--o{ AUDIT_LOGS : performs
  USERS ||--o{ DOWNLOAD_REQUESTS : requests
  DEPARTMENTS ||--o{ LABS : contains
  DEPARTMENTS ||--o{ PROFESSORS : groups
  LABS ||--o{ PROFESSORS : groups
  PROFESSORS ||--o{ PROFESSOR_SCOPUS_IDS : confirms
  PROFESSORS ||--o{ PROFESSOR_PUBLICATIONS : owns
  PUBLICATIONS ||--o{ PROFESSOR_PUBLICATIONS : links
  PUBLICATIONS ||--o{ PUBLICATION_AUTHOR_AFFILIATIONS : contains
  AUTHORS ||--o{ PUBLICATION_AUTHOR_AFFILIATIONS : has
  INSTITUTIONS ||--o{ PUBLICATION_AUTHOR_AFFILIATIONS : identifies
  INSTITUTIONS ||--o{ INSTITUTION_ALIASES : normalizes
  PROFESSORS ||--o{ INTERNATIONAL_COLLABORATIONS : reports
  PUBLICATIONS ||--o{ INTERNATIONAL_COLLABORATIONS : generates
  INSTITUTIONS ||--o{ INTERNATIONAL_COLLABORATIONS : partners
  PROFESSORS ||--o{ SYNC_RUNS : records
```

Primary duplicate defenses are unique Scopus EID, unique professor/publication links, unique normalized institution aliases, and unique `(publication_id, professor_id, institution_id)` collaborations.
