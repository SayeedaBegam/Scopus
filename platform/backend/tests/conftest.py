import os
os.environ["DATABASE_URL"]="sqlite:///./test-utn.db"
os.environ["SCOPUS_MODE"]="mock"
os.environ["SECRET_KEY"]="test-secret-key-with-at-least-32-characters"
os.environ["SCHEDULED_SYNC_SECRET"]="test-scheduled-secret"
import pytest
from fastapi.testclient import TestClient
from app.core.database import Base,SessionLocal,engine
from app.core.security import hash_password
from app.main import app
from app.models import Role,User

@pytest.fixture(autouse=True)
def database():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        db.add_all([User(name="Admin",email="admin@test.de",password_hash=hash_password("TestingPassword!2026"),role=Role.admin),User(name="Viewer",email="viewer@test.de",password_hash=hash_password("TestingPassword!2026"),role=Role.viewer)])
        db.commit()
    yield

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def admin(client):
    client.post("/api/v1/auth/login",json={"email":"admin@test.de","password":"TestingPassword!2026"})
    return client

@pytest.fixture
def viewer(client):
    client.post("/api/v1/auth/login",json={"email":"viewer@test.de","password":"TestingPassword!2026"})
    return client
