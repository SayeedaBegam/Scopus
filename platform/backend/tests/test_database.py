from app.core.database import sqlalchemy_database_url


def test_provider_postgres_urls_use_psycopg_v3():
    assert sqlalchemy_database_url("postgresql://user:pass@host/db?sslmode=require")=="postgresql+psycopg://user:pass@host/db?sslmode=require"
    assert sqlalchemy_database_url("postgres://user:pass@host/db")=="postgresql+psycopg://user:pass@host/db"
    assert sqlalchemy_database_url("sqlite:///./local.db")=="sqlite:///./local.db"
