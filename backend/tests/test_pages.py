import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from app.services.prediction_service import prediction_service
from app.auth.security import create_session_token, generate_csrf_token, hash_password
from app.database import SessionLocal, init_db
from app.models.company import Company

client = TestClient(app)


@pytest.fixture(scope="module")
def auth_setup():
    """Create test company workspace and return authenticated TestClient and token."""
    init_db()
    db = SessionLocal()
    company = db.query(Company).filter(Company.email == "pages_test@company.com").first()
    if not company:
        company = Company(
            name="Pages Test Co",
            email="pages_test@company.com",
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


def test_home_page():
    """Verify home page loads successfully with expected status code and core headers."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Pre-Shipment Product Return Risk Analysis" in response.text
    assert "Evaluate an Order" in response.text
    assert "ReturnRisk" in response.text


def test_unauthenticated_predict_redirect():
    """Verify that accessing protected prediction console without login redirects to /login."""
    response = client.get("/predict", follow_redirects=False)
    assert response.status_code == 303
    assert "/login" in response.headers.get("location", "")


def test_predict_page_get(auth_setup):
    """Verify prediction form page loads with input controls and demo presets for authenticated company."""
    authed_client, _ = auth_setup
    response = authed_client.get("/predict")
    assert response.status_code == 200
    assert "Order Return Risk Evaluation" in response.text
    assert "product_category" in response.text
    assert "product_price" in response.text
    assert "Quick Test Presets" in response.text


def test_predict_page_post_success(auth_setup):
    """Verify form submission executes inference, persists to database, and renders result template."""
    authed_client, token = auth_setup
    csrf = generate_csrf_token(token)
    form_data = {
        "product_category": "Fashion",
        "sub_category": "Women",
        "brand": "Brand_10",
        "product_identifier": "SKU-TEST-01",
        "product_price": 599.0,
        "discount_percent": 25.0,
        "product_rating": 4.2,
        "review_count": 65,
        "fragile_item": 0,
        "warranty_available": 1,
        "defect_rate": 0.03,
        "seller_rating": 4.5,
        "fulfillment_type": "Marketplace Fulfilled",
        "payment_method": "Credit Card",
        "quantity": 1,
        "shipping_distance_km": 350.0,
        "wishlist_before_purchase": 1,
        "product_page_views": 15,
        "csrf_token": csrf,
    }
    response = authed_client.post("/predict", data=form_data)
    assert response.status_code == 200
    assert "Return Risk Assessment" in response.text
    assert "Estimated Probability" in response.text
    assert ("Higher return risk" in response.text) or ("Lower return risk" in response.text)
    assert "Company Historical Performance Comparison" in response.text


def test_predict_page_post_validation_error(auth_setup):
    """Verify invalid inputs trigger 422 status and display form validation error messages."""
    authed_client, token = auth_setup
    csrf = generate_csrf_token(token)
    invalid_data = {
        "product_category": "Fashion",
        "sub_category": "Women",
        "brand": "Brand_10",
        "product_price": -50.0,  # Invalid: negative price
        "discount_percent": 25.0,
        "product_rating": 6.5,  # Invalid: rating > 5.0
        "review_count": 65,
        "fragile_item": 0,
        "warranty_available": 1,
        "defect_rate": 0.03,
        "seller_rating": 4.5,
        "fulfillment_type": "Marketplace Fulfilled",
        "payment_method": "Credit Card",
        "quantity": 0,  # Invalid: quantity < 1
        "shipping_distance_km": 350.0,
        "wishlist_before_purchase": 1,
        "product_page_views": 15,
        "csrf_token": csrf,
    }
    response = authed_client.post("/predict", data=invalid_data)
    assert response.status_code == 422
    assert "Please correct the highlighted input fields." in response.text


def test_methodology_page():
    """Verify methodology documentation page displays verified training metrics and leakage audit."""
    response = client.get("/methodology")
    assert response.status_code == 200
    assert "Model Methodology &amp; Validation" in response.text or "Model Methodology & Validation" in response.text
    assert "79.96%" in response.text
    assert "88.75%" in response.text
    assert "delayed_delivery" in response.text


def test_about_page():
    """Verify about page loads with architecture and technical stack information."""
    response = client.get("/about")
    assert response.status_code == 200
    assert "About ReturnRisk Intelligence" in response.text or "About This System" in response.text
    assert "FastAPI" in response.text


def test_404_handler_html():
    """Verify custom 404 handler returns clean error page for nonexistent routes."""
    response = client.get("/nonexistent-page-path")
    assert response.status_code == 404
    assert "Page Not Located" in response.text or "Page Not Found" in response.text


def test_404_handler_json():
    """Verify API 404 returns structured JSON response."""
    response = client.get("/api/nonexistent-endpoint")
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Resource not found"
