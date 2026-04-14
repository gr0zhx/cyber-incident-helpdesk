from unittest.mock import MagicMock, patch

import fakeredis
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware

from app.database.models import Admin
from app.web.dependencies import get_current_admin, get_db_session
from app.web.routes.admin_rag import router
from app.web.services.rag_service import RagService


@pytest.fixture
def client():
    admin = Admin(id=1, username="admin1", email="a@x.com", full_name="A",
                  password_hash="h", is_active=True)

    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="k")
    app.dependency_overrides[get_current_admin] = lambda: admin
    app.dependency_overrides[get_db_session] = lambda: iter([MagicMock()])
    app.include_router(router)
    return TestClient(app)


def test_rag_page_renders(client):
    fake_r = fakeredis.FakeStrictRedis(decode_responses=False)
    with patch("app.web.routes.admin_rag._redis_client", return_value=fake_r), \
         patch.object(RagService, "get_collection_info",
                      return_value={"total_vectors": 10, "status": "green"}), \
         patch.object(RagService, "list_documents", return_value=[]):
        r = client.get("/admin/rag")
    assert r.status_code == 200
    assert "Knowledge Base" in r.text


def test_rag_reindex_redirects(client):
    fake_r = fakeredis.FakeStrictRedis(decode_responses=False)
    with patch("app.web.routes.admin_rag._redis_client", return_value=fake_r), \
         patch.object(RagService, "list_documents", return_value=[]):
        r = client.post("/admin/rag/reindex", data={"csrf_token": "x"}, follow_redirects=False)
    assert r.status_code in (302, 303)
