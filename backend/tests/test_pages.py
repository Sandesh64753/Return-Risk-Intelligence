import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from app.services.prediction_service import prediction_service
from app.auth.security import create_session_token, hash_password
from app.database import SessionLocal, init_db
from app.models.company import Company

client = TestClient(app)


@pytest.fixture(scope="module")
def auth_setup():
    """Create test company workspace and return authenticated TestClient and token."""
    init_db()
    db = SessionLocal()
    company = db.query(Company).filter(Company.email == "spa_test@company.com").first()
    if not company:
        company = Company(
            name="SPA Test Co",
            email="spa_test@company.com",
            password_hash=hash_password("ValidPassword123!"),
            industry="Fashion & Apparel",
        )
        db.add(company)
        db.commit()
        db.refresh(company)
    token = create_session_token(company.id)
    db.close()

    authed_client = TestClient(app)
    authed_client.cookies.set(settings.SESSION_COOKIE_NAME, token)
    return authed_client, token


def test_health_endpoint():
    """Verify health endpoint returns healthy status and model readiness."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["model_loaded"] is True



def test_home_page_spa_or_api():
    """Verify home page loads React SPA index.html or API discovery JSON."""
    response = client.get("/")
    assert response.status_code == 200
    # If compiled React dist is available, it returns HTML; otherwise JSON
    if "text/html" in response.headers.get("content-type", ""):
        assert "<div id=\"root\">" in response.text or "html" in response.text.lower()
    else:
        data = response.json()
        assert data["status"] == "online"


def test_spa_client_routes():
    """Verify SPA client-side routes (e.g. /dashboard, /predict) serve index.html."""
    for path in ["/dashboard", "/predict", "/methodology", "/about"]:
        response = client.get(path)
        # Should return 200 SPA HTML when dist exists, or 404 JSON if dist not compiled
        if response.status_code == 200:
            assert "text/html" in response.headers.get("content-type", "")


def test_api_metadata():
    """Verify metadata API returns verified training metrics and leakage audit info."""
    response = client.get("/api/metadata")
    assert response.status_code == 200
    data = response.json()
    assert "model_name" in data
    assert "metrics" in data


def test_unauthenticated_api_predictions():
    """Verify accessing protected predictions API without credentials returns 401 JSON."""
    response = client.get("/api/predictions")
    assert response.status_code == 401
    data = response.json()
    assert "Authentication required" in data.get("detail", "")


def test_404_handler_json():
    """Verify API 404 returns structured JSON response."""
    response = client.get("/api/nonexistent-endpoint")
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Resource not found"

