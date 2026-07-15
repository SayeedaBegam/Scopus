from app.services.scopus.sync import parse_publication_details


def test_nested_live_abstract_response_is_normalized():
    details = {
        "abstracts-retrieval-response": {
            "coredata": {
                "eid": "2-s2.0-123",
                "dc:identifier": "SCOPUS_ID:123",
                "dc:title": "A live publication",
                "prism:publicationName": "Research Journal",
                "prism:coverDate": "2026-03-14",
                "prism:doi": "10.1000/live",
                "citedby-count": "17",
                "subtypeDescription": "Article",
            },
            "authors": {
                "author": [
                    {
                        "ce:indexed-name": "Researcher A.",
                        "affiliation": {"@id": "AFF-1"},
                    }
                ]
            },
            "affiliation": {
                "@id": "AFF-1",
                "affilname": "Example University",
                "affiliation-city": "Example City",
                "affiliation-country": "France",
            },
            "item": {
                "bibrecord": {
                    "head": {
                        "author-group": {
                            "affiliation": {
                                "@afid": "AFF-1",
                                "country": "France",
                                "organization": [{"$": "Vision Lab"}, {"$": "Example University"}],
                                "ce:source-text": "Vision Lab, Example University",
                            },
                            "author": {"ce:indexed-name": "Researcher A."},
                        }
                    }
                }
            },
        }
    }

    parsed = parse_publication_details(details)

    assert parsed["title"] == "A live publication"
    assert parsed["source_title"] == "Research Journal"
    assert parsed["year"] == 2026
    assert parsed["doi"] == "10.1000/live"
    assert parsed["citation_count"] == 17
    assert parsed["author_count"] == 1
    assert parsed["affiliations"] == [
        {
            "id": "AFF-1",
            "name": "Example University",
            "country": "France",
            "raw": "Vision Lab, Example University",
            "author": "Researcher A.",
            "department": "Vision Lab",
        }
    ]
