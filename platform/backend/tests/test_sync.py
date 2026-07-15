def test_sync_is_idempotent_and_excludes_germany(admin):
    pid=admin.post("/api/v1/professors",json={"full_name":"Prof. Anna Keller","scopus_author_id":"57200000001"}).json()["id"]
    first=admin.post(f"/api/v1/professors/{pid}/sync")
    assert first.status_code==200 and first.json()["created"]==4
    collabs=admin.get(f"/api/v1/collaborations?professor_id={pid}").json()
    assert len(collabs)==4 and all(x["country"]!="Germany" for x in collabs)
    assert all(x["institution_name"] and x["publication_title"] for x in collabs)
    assert all(x["author_count"] > 0 for x in collabs)
    second=admin.post(f"/api/v1/professors/{pid}/sync")
    assert second.status_code==200 and second.json()["created"]==0
    assert len(admin.get(f"/api/v1/collaborations?professor_id={pid}").json())==4

def test_missing_doi_is_stored(admin):
    pid=admin.post("/api/v1/professors",json={"full_name":"Anna","scopus_author_id":"57200000001"}).json()["id"]
    admin.post(f"/api/v1/professors/{pid}/sync")
    assert any(x["doi"] is None for x in admin.get(f"/api/v1/professors/{pid}/publications").json())
