import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models.company import Company
from app.models.prediction import PredictionRecord
from app.models.actual_return import ActualReturnRecord
from app.models.recommendation import RecommendationRecord


from sqlalchemy.pool import StaticPool

@pytest.fixture(scope="module")
def multi_company_client():
    # Use SQLite in-memory with StaticPool for thread-safe test execution
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


def test_company_registration_and_auth(multi_company_client):
    client = multi_company_client

    # 1. Register Company A
    reg_a = client.post("/api/auth/register", json={
        "name": "Alpha Corp",
        "email": "ops@alpha.com",
        "password": "SecurePassword123!",
        "confirm_password": "SecurePassword123!",
        "industry": "Fashion & Apparel",
    })
    assert reg_a.status_code == 200
    data_a = reg_a.json()
    assert data_a["success"] is True
    assert data_a["company"]["name"] == "Alpha Corp"
    assert data_a["company"]["email"] == "ops@alpha.com"
    company_a_id = data_a["company"]["id"]

    # Check /api/auth/me
    me_a = client.get("/api/auth/me")
    assert me_a.status_code == 200
    assert me_a.json()["authenticated"] is True
    assert me_a.json()["company"]["id"] == company_a_id

    # 2. Duplicate registration attempt should fail with 409
    dup = client.post("/api/auth/register", json={
        "name": "Alpha Corp Copy",
        "email": "ops@alpha.com",
        "password": "SecurePassword123!",
        "confirm_password": "SecurePassword123!",
    })
    assert dup.status_code == 409

    # 3. Log out Company A
    logout_res = client.post("/api/auth/logout")
    assert logout_res.status_code == 200
    me_logged_out = client.get("/api/auth/me")
    assert me_logged_out.json()["authenticated"] is False

    # 4. Register Company B
    reg_b = client.post("/api/auth/register", json={
        "name": "Beta Retail",
        "email": "admin@betaretail.com",
        "password": "BetaPassword456!",
        "confirm_password": "BetaPassword456!",
        "industry": "Consumer Electronics",
    })
    assert reg_b.status_code == 200
    data_b = reg_b.json()
    assert data_b["company"]["name"] == "Beta Retail"
    assert data_b["company"]["id"] != company_a_id


def test_multi_company_data_isolation(multi_company_client):
    client = multi_company_client

    # 1. Sign in as Company A (Alpha Corp)
    login_a = client.post("/api/auth/login", json={
        "email": "ops@alpha.com",
        "password": "SecurePassword123!",
    })
    assert login_a.status_code == 200
    alpha_id = login_a.json()["company"]["id"]

    # 2. Company A runs a prediction
    pred_payload = {
        "product_category": "Fashion",
        "sub_category": "Women",
        "brand": "Brand_10",
        "product_identifier": "SKU-ALPHA-01",
        "product_price": 499.0,
        "discount_percent": 30.0,
        "product_rating": 4.1,
        "review_count": 50,
        "fragile_item": 0,
        "warranty_available": 1,
        "defect_rate": 0.04,
        "seller_rating": 4.4,
        "fulfillment_type": "Marketplace Fulfilled",
        "payment_method": "Credit Card",
        "quantity": 1,
        "shipping_distance_km": 250.0,
        "wishlist_before_purchase": 1,
        "product_page_views": 18,
    }
    pred_res_a = client.post("/api/predict", json=pred_payload)
    assert pred_res_a.status_code == 200
    pred_data_a = pred_res_a.json()
    record_id_a = pred_data_a["record_id"]
    assert record_id_a is not None

    # Company A seeds demo returns
    seed_a = client.post("/api/import/demo-seed")
    assert seed_a.status_code == 200
    seed_json = seed_a.json()
    assert (seed_json.get("inserted") or seed_json.get("inserted_count") or 0) > 0

    # Company A checks predictions
    preds_a = client.get("/api/predictions")
    assert preds_a.status_code == 200
    assert preds_a.json()["total"] >= 1
    assert any(p["id"] == record_id_a for p in preds_a.json()["records"])

    # Company A checks dashboard
    dash_a = client.get("/api/dashboard")
    assert dash_a.status_code == 200
    assert dash_a.json()["total_known_orders"] > 0

    # 3. Log out Company A and Sign in as Company B (Beta Retail)
    client.post("/api/auth/logout")
    login_b = client.post("/api/auth/login", json={
        "email": "admin@betaretail.com",
        "password": "BetaPassword456!",
    })
    assert login_b.status_code == 200

    # 4. Verify Company B CANNOT see Company A's data
    preds_b = client.get("/api/predictions")
    assert preds_b.status_code == 200
    assert preds_b.json()["total"] == 0  # 0 predictions for Beta Retail!
    assert len(preds_b.json()["records"]) == 0

    dash_b = client.get("/api/dashboard")
    assert dash_b.status_code == 200
    assert dash_b.json()["total_predictions"] == 0
    assert dash_b.json()["total_known_orders"] == 0  # 0 known orders for Beta Retail!

    # 5. Direct access attempt to Company A's prediction record ID from Company B must be blocked (404)
    direct_access = client.get(f"/api/predictions/{record_id_a}")
    assert direct_access.status_code == 404


def test_csv_import_and_template(multi_company_client):
    client = multi_company_client

    # Sign in as Beta Retail
    client.post("/api/auth/login", json={
        "email": "admin@betaretail.com",
        "password": "BetaPassword456!",
    })

    # Download template
    tmpl = client.get("/api/import/template")
    assert tmpl.status_code == 200
    assert "order_reference" in tmpl.text
    assert "was_returned" in tmpl.text

    # Upload valid CSV with 2 rows and 1 duplicate
    csv_data = """order_reference,product_identifier,product_category,sub_category,brand,product_price,discount_percent,fulfillment_type,payment_method,quantity,defect_rate,order_date,return_date,was_returned,return_reason
ORD-TEST-001,SKU-BETA-01,Electronics,Laptops,Brand_1,1200.0,10.0,Marketplace Fulfilled,Credit Card,1,0.02,2026-03-01,,0,
ORD-TEST-002,SKU-BETA-02,Fashion,Women,Brand_2,150.0,50.0,Seller Fulfilled,COD,2,0.08,2026-03-02,2026-03-08,1,Defective
ORD-TEST-001,SKU-BETA-01,Electronics,Laptops,Brand_1,1200.0,10.0,Marketplace Fulfilled,Credit Card,1,0.02,2026-03-01,,0,
"""
    files = {"file": ("test_orders.csv", csv_data, "text/csv")}
    upload_res = client.post("/api/import", files=files)
    assert upload_res.status_code == 200
    up_json = upload_res.json()
    assert up_json["inserted"] == 2
    assert up_json["duplicates"] == 1
    assert up_json["total_errors"] == 0

    # Dashboard should now show 2 known orders for Company B
    dash_b = client.get("/api/dashboard")
    assert dash_b.json()["total_known_orders"] == 2
    assert dash_b.json()["actual_returns"] == 1
    assert dash_b.json()["actual_return_rate"] == 50.0


def test_analytics_and_performance_endpoints(multi_company_client):
    client = multi_company_client

    # Sign in as Alpha Corp (which seeded 150 records)
    client.post("/api/auth/login", json={
        "email": "ops@alpha.com",
        "password": "SecurePassword123!",
    })

    # Test Analytics
    analytics_res = client.get("/api/analytics?segment=product_category&min_samples=2")
    assert analytics_res.status_code == 200
    analytics_data = analytics_res.json()
    assert analytics_data["segment"] == "product_category"
    assert len(analytics_data["segment_data"]) > 0

    first_segment = analytics_data["segment_data"][0]
    assert "ci_low" in first_segment
    assert "ci_high" in first_segment
    if first_segment["ci_low"] is not None and first_segment["ci_high"] is not None:
        assert first_segment["ci_low"] <= first_segment["return_rate"] <= first_segment["ci_high"]

    # Test feature factor correlations
    assert "feature_correlations" in analytics_data
    assert len(analytics_data["feature_correlations"]) > 0

    # Test Performance
    perf_res = client.get("/api/performance?window_days=30")
    assert perf_res.status_code == 200
    perf_data = perf_res.json()
    assert "window_days" in perf_data
    assert "current_period" in perf_data
    assert "previous_period" in perf_data


def test_recommendation_lifecycle(multi_company_client):
    client = multi_company_client

    # Sign in as Alpha Corp
    client.post("/api/auth/login", json={
        "email": "ops@alpha.com",
        "password": "SecurePassword123!",
    })

    # Fetch recommendations
    recs_res = client.get("/api/recommendations")
    assert recs_res.status_code == 200
    recs = recs_res.json()
    assert isinstance(recs, list)

    if len(recs) > 0:
        first_rec = recs[0]
        rec_id = first_rec["id"]

        # Update recommendation to implemented
        up_res = client.post(f"/api/recommendations/{rec_id}/status", json={
            "status": "implemented",
            "implementation_date": "2026-03-01",
            "review_notes": "Added high-density bubble wrap and pre-dispatch SMS verification.",
        })
        assert up_res.status_code == 200
        assert up_res.json()["status"] == "implemented"

        # Verify updated status
        verify_res = client.get("/api/recommendations?status_filter=implemented")
        assert verify_res.status_code == 200
        implemented_ids = [r["id"] for r in verify_res.json()]
        assert rec_id in implemented_ids
