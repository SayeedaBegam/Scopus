def test_health(client):
    assert client.get("/api/v1/health").status_code==200

def test_auth_required(client):
    assert client.get("/api/v1/professors").status_code==401

def test_viewer_cannot_create(viewer):
    assert viewer.post("/api/v1/professors",json={"full_name":"No Access"}).status_code==403

def test_admin_professor_lifecycle(admin):
    r=admin.post("/api/v1/professors",json={"full_name":"Prof. Test","scopus_author_id":"57200000001"})
    assert r.status_code==201
    assert admin.post(f"/api/v1/professors/{r.json()['id']}/deactivate").json()["is_active"] is False

def test_admin_can_create_professor_with_blank_optional_fields(admin):
    r=admin.post("/api/v1/professors",json={"full_name":"Prof. Optional","email":"","research_area":""})
    assert r.status_code==201
    assert r.json()["email"] is None
    assert r.json()["research_area"] is None

def test_removing_professor_requires_current_admin_password(admin):
    pid=admin.post("/api/v1/professors",json={"full_name":"Prof. Remove"}).json()["id"]
    wrong=admin.request("DELETE",f"/api/v1/professors/{pid}",json={"password":"wrong-password"})
    assert wrong.status_code==403
    assert admin.get(f"/api/v1/professors/{pid}").status_code==200
    removed=admin.request("DELETE",f"/api/v1/professors/{pid}",json={"password":"TestingPassword!2026"})
    assert removed.status_code==200
    assert removed.json()["removed_id"]==pid
    assert admin.get(f"/api/v1/professors/{pid}").status_code==404

def test_viewer_export_requires_request(admin,client):
    pid=admin.post("/api/v1/professors",json={"full_name":"Prof. Test"}).json()["id"]
    client.post("/api/v1/auth/logout")
    client.post("/api/v1/auth/login",json={"email":"viewer@test.de","password":"TestingPassword!2026"})
    assert client.post(f"/api/v1/exports/professor/{pid}").status_code==403

def test_admin_can_manage_separate_accounts(admin):
    created=admin.post("/api/v1/admin/users",json={"name":"Sayeeda Begam","email":"sayeeda@example.org","password":"ShortSafe!26","role":"admin"})
    assert created.status_code==201
    user_id=created.json()["id"]
    assert created.json()["role"]=="admin"
    updated=admin.patch(f"/api/v1/admin/users/{user_id}",json={"role":"viewer","is_active":False})
    assert updated.status_code==200
    assert updated.json()["role"]=="viewer"
    assert updated.json()["is_active"] is False

def test_duplicate_user_email_is_rejected(admin):
    body={"name":"Viewer One","email":"person@example.org","password":"ShortSafe!26","role":"viewer"}
    assert admin.post("/api/v1/admin/users",json=body).status_code==201
    assert admin.post("/api/v1/admin/users",json=body).status_code==409

def test_scheduled_sync_requires_secret_and_updates_active_professors(admin,client):
    created=admin.post("/api/v1/professors",json={"full_name":"Scheduled Professor","scopus_author_id":"57200000001"})
    assert created.status_code==201
    assert client.post("/api/v1/scheduled/scopus-sync").status_code==401
    assert client.post("/api/v1/scheduled/scopus-sync",headers={"X-Sync-Secret":"wrong"}).status_code==401
    result=client.post("/api/v1/scheduled/scopus-sync",headers={"X-Sync-Secret":"test-scheduled-secret"})
    assert result.status_code==200
    assert result.json()["status"]=="completed"
    assert result.json()["completed"][0]["name"]=="Scheduled Professor"
