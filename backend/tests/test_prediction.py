import pytest
import numpy as np
import pandas as pd
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.config import settings
from app.schemas import PredictionInput
from app.services.prediction_service import prediction_service

client = TestClient(app)

SAMPLE_LOW_RISK = {
    "product_category": "Electronics",
    "sub_category": "Laptops",
    "brand": "Brand_15",
    "product_price": 1250.0,
    "discount_percent": 10.0,
    "product_rating": 4.8,
    "review_count": 95,
    "fragile_item": 0,
    "warranty_available": 1,
    "defect_rate": 0.01,
    "seller_rating": 4.9,
    "fulfillment_type": "Marketplace Fulfilled",
    "payment_method": "Credit Card",
    "quantity": 1,
    "shipping_distance_km": 200.0,
    "wishlist_before_purchase": 1,
    "product_page_views": 30,
}

SAMPLE_HIGH_RISK = {
    "product_category": "Fashion",
    "sub_category": "Women",
    "brand": "Brand_5",
    "product_price": 120.0,
    "discount_percent": 60.0,
    "product_rating": 2.2,
    "review_count": 25,
    "fragile_item": 1,
    "warranty_available": 0,
    "defect_rate": 0.22,
    "seller_rating": 2.6,
    "fulfillment_type": "Seller Fulfilled",
    "payment_method": "COD",
    "quantity": 4,
    "shipping_distance_km": 1250.0,
    "wishlist_before_purchase": 0,
    "product_page_views": 3,
}


def test_model_artifact_exists_and_loads():
    """Verify model artifact exists, loads, and initializes with all expected metadata."""
    assert settings.ARTIFACT_PATH.exists(), f"Artifact missing at {settings.ARTIFACT_PATH}"
    assert prediction_service.is_ready() is True
    assert prediction_service.model_name == "Logistic Regression"
    assert len(prediction_service.expected_features) == 17
    assert 0.39 < prediction_service.threshold < 0.40


def test_prediction_service_valid_low_risk():
    """Verify prediction service returns Lower return risk for clean, certified item."""
    validated = PredictionInput(**SAMPLE_LOW_RISK)
    result = prediction_service.predict(validated)

    assert result.predicted_class == 0
    assert result.risk_label == "Lower return risk"
    assert result.return_probability < prediction_service.threshold
    assert result.probability_percent < 39.8
    assert "submitted_inputs" in result.model_dump()


def test_prediction_service_valid_high_risk():
    """Verify prediction service returns Higher return risk for high-defect COD order."""
    validated = PredictionInput(**SAMPLE_HIGH_RISK)
    result = prediction_service.predict(validated)

    assert result.predicted_class == 1
    assert result.risk_label == "Higher return risk"
    assert result.return_probability >= prediction_service.threshold
    assert result.probability_percent >= 39.7
    assert len(result.key_factors) > 0


def test_prediction_unknown_category_handled():
    """Verify that unknown/unseen categories are gracefully handled without crashing inference."""
    data = dict(SAMPLE_LOW_RISK)
    data["product_category"] = "Automotive"  # Unseen in training
    data["sub_category"] = "Tires"           # Unseen in training
    data["brand"] = "Brand_99"               # Unseen in training

    validated = PredictionInput(**data)
    result = prediction_service.predict(validated)
    assert result is not None
    assert isinstance(result.return_probability, float)


def test_prediction_invalid_rating_bounds():
    """Verify Pydantic rejects product rating exceeding 5.0 or below 1.0."""
    data = dict(SAMPLE_LOW_RISK)
    data["product_rating"] = 5.5
    with pytest.raises(ValidationError):
        PredictionInput(**data)

    data["product_rating"] = 0.5
    with pytest.raises(ValidationError):
        PredictionInput(**data)


def test_prediction_negative_price():
    """Verify Pydantic rejects negative or zero product price."""
    data = dict(SAMPLE_LOW_RISK)
    data["product_price"] = -10.0
    with pytest.raises(ValidationError):
        PredictionInput(**data)

    data["product_price"] = 0.0
    with pytest.raises(ValidationError):
        PredictionInput(**data)


def test_api_predict_endpoint_success():
    """Verify POST /api/predict returns structured JSON matching PredictionResponse schema."""
    response = client.post("/api/predict", json=SAMPLE_LOW_RISK)
    assert response.status_code == 200
    data = response.json()

    assert "predicted_class" in data
    assert "risk_label" in data
    assert "return_probability" in data
    assert "threshold" in data
    assert data["predicted_class"] == 0
    assert data["risk_label"] == "Lower return risk"


def test_api_predict_endpoint_validation_error():
    """Verify POST /api/predict returns 422 Unprocessable Entity on missing required fields."""
    incomplete_data = {"product_category": "Fashion"}
    response = client.post("/api/predict", json=incomplete_data)
    assert response.status_code == 422


def test_health_endpoint():
    """Verify GET /health returns application status and model readiness."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "healthy"
    assert data["model_loaded"] is True
    assert data["model_name"] == "Logistic Regression"
    assert data["threshold"] is not None
    assert data["feature_count"] == 17


def test_threshold_application():
    """Verify the operational threshold strictly governs the binary predicted_class."""
    # Build test records and verify consistency
    validated_low = PredictionInput(**SAMPLE_LOW_RISK)
    res_low = prediction_service.predict(validated_low)
    expected_class_low = 1 if res_low.return_probability >= prediction_service.threshold else 0
    assert res_low.predicted_class == expected_class_low

    validated_high = PredictionInput(**SAMPLE_HIGH_RISK)
    res_high = prediction_service.predict(validated_high)
    expected_class_high = 1 if res_high.return_probability >= prediction_service.threshold else 0
    assert res_high.predicted_class == expected_class_high


def test_agreement_with_notebook_test_sample():
    """Verify prediction service reproduces raw pipeline output with zero numerical divergence."""
    pipe = prediction_service.pipeline
    threshold = prediction_service.threshold

    validated = PredictionInput(**SAMPLE_LOW_RISK)
    feat_dict = validated.get_features_dict()
    df_raw = pd.DataFrame([feat_dict])[prediction_service.expected_features]

    raw_prob = float(pipe.predict_proba(df_raw)[0, 1])
    raw_pred = int(raw_prob >= threshold)

    service_res = prediction_service.predict(validated)
    assert np.isclose(service_res.return_probability, round(raw_prob, 4), atol=1e-6)
    assert service_res.predicted_class == raw_pred
