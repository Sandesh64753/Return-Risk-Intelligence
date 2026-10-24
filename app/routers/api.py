import io
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, File, HTTPException, Request, Response, UploadFile, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.config import settings
from app.database import get_db
from app.models.company import Company
from app.models.prediction import PredictionRecord
from app.models.product import Product
from app.models.recommendation import RecommendationRecord
from app.auth.security import (
    hash_password,
    verify_password,
    create_session_token,
    decode_session_token,
)
from app.auth.dependencies import (
    get_current_company,
    get_current_company_optional,
)
from app.schemas import (
    PredictionInput,
    PredictionResponse,
    HealthResponse,
    CompanyRegisterInput,
    CompanyLoginInput,
    RecommendationUpdateInput,
    VALID_CATEGORIES,
    ALL_BRANDS,
    ALL_FULFILLMENT_TYPES,
    ALL_PAYMENT_METHODS,
)
from app.services.prediction_service import prediction_service
from app.services.analytics_service import analytics_service
from app.services.recommendation_service import recommendation_service
from app.services.import_service import import_service, EXPECTED_CSV_HEADERS

router = APIRouter(tags=["API"])

DEMO_PRESETS = {
    "preset_1": {
        "name": "Standard Verified Electronics",
        "description": "High-ticket electronics, marketplace fulfilled, standard payment with warranty.",
        "data": {
            "product_category": "Electronics",
            "sub_category": "Laptops",
            "brand": "Brand_15",
            "product_identifier": "SKU-ELEC-PRO-01",
            "product_price": 1250.0,
            "discount_percent": 15.0,
            "product_rating": 4.5,
            "review_count": 85,
            "fragile_item": 0,
            "warranty_available": 1,
            "defect_rate": 0.02,
            "seller_rating": 4.7,
            "fulfillment_type": "Marketplace Fulfilled",
            "payment_method": "Credit Card",
            "quantity": 1,
            "shipping_distance_km": 280.0,
            "wishlist_before_purchase": 1,
            "product_page_views": 24,
        },
    },
    "preset_2": {
        "name": "High-Risk Discount Apparel",
        "description": "Deep discount apparel, COD payment, seller fulfilled, multiple units.",
        "data": {
            "product_category": "Fashion",
            "sub_category": "Women",
            "brand": "Brand_5",
            "product_identifier": "SKU-FASH-SUM-02",
            "product_price": 140.0,
            "discount_percent": 55.0,
            "product_rating": 3.1,
            "review_count": 28,
            "fragile_item": 0,
            "warranty_available": 0,
            "defect_rate": 0.09,
            "seller_rating": 3.4,
            "fulfillment_type": "Seller Fulfilled",
            "payment_method": "COD",
            "quantity": 3,
            "shipping_distance_km": 1150.0,
            "wishlist_before_purchase": 0,
            "product_page_views": 4,
        },
    },
    "preset_3": {
        "name": "Fragile Home Goods with Defect Alert",
        "description": "Breakable home merchandise, seller fulfilled, elevated manufacturer defect rate.",
        "data": {
            "product_category": "Home",
            "sub_category": "Kitchen",
            "brand": "Brand_22",
            "product_identifier": "SKU-HOME-KIT-03",
            "product_price": 290.0,
            "discount_percent": 30.0,
            "product_rating": 3.6,
            "review_count": 42,
            "fragile_item": 1,
            "warranty_available": 0,
            "defect_rate": 0.14,
            "seller_rating": 3.6,
            "fulfillment_type": "Seller Fulfilled",
            "payment_method": "UPI",
            "quantity": 2,
            "shipping_distance_km": 820.0,
            "wishlist_before_purchase": 0,
            "product_page_views": 8,
        },
    },
}


# ==========================================
# 1. Health and Metadata
# ==========================================

@router.get("/health", response_model=HealthResponse, summary="Application and model health check")
async def health_check() -> HealthResponse:
    """Return operational status and model readiness without exposing private paths or secrets."""
    model_ready = prediction_service.is_ready()
    status_str = "healthy" if model_ready else "degraded"
    metadata = prediction_service.get_metadata()

    return HealthResponse(
        status=status_str,
        model_loaded=model_ready,
        model_name=metadata.get("model_name"),
        threshold=metadata.get("threshold"),
        feature_count=len(metadata.get("features", [])),
        version=settings.VERSION,
    )


@router.get("/api/metadata", summary="Retrieve model metadata and performance metrics")
async def get_model_metadata():
    if not prediction_service.is_ready():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Prediction model is not ready.",
        )
    return prediction_service.get_metadata()


@router.get("/api/categories", summary="Supported categorical taxonomy and feature options")
async def get_taxonomy():
    return {
        "categories": VALID_CATEGORIES,
        "brands": ALL_BRANDS,
        "fulfillment_types": ALL_FULFILLMENT_TYPES,
        "payment_methods": ALL_PAYMENT_METHODS,
    }


@router.get("/api/presets", summary="Get demonstration presets for testing")
async def get_presets():
    return DEMO_PRESETS


# ==========================================
# 2. Authentication API (for React frontend)
# ==========================================

@router.get("/api/auth/me", summary="Get currently authenticated company profile")
async def get_current_user_profile(
    company: Optional[Company] = Depends(get_current_company_optional),
):
    if not company:
        return {"authenticated": False, "company": None}
    return {
        "authenticated": True,
        "company": {
            "id": company.id,
            "name": company.name,
            "email": company.email,
            "industry": company.industry,
            "created_at": str(company.created_at),
        },
    }


@router.post("/api/auth/register", summary="Register a new company workspace")
async def api_register(
    payload: CompanyRegisterInput,
    response: Response,
    db: Session = Depends(get_db),
):
    if payload.password != payload.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Passwords do not match.",
        )

    existing = db.query(Company).filter(Company.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this company email is already registered.",
        )

    pwd_hash = hash_password(payload.password)
    new_company = Company(
        name=payload.name,
        email=payload.email,
        password_hash=pwd_hash,
        industry=payload.industry,
        is_active=True,
    )
    db.add(new_company)
    db.commit()
    db.refresh(new_company)

    token = create_session_token(new_company.id)
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=token,
        max_age=settings.SESSION_MAX_AGE_SECONDS,
        httponly=True,
        samesite=settings.COOKIE_SAMESITE,
        secure=settings.COOKIE_SECURE,
    )
    return {
        "success": True,
        "company": {
            "id": new_company.id,
            "name": new_company.name,
            "email": new_company.email,
            "industry": new_company.industry,
        },
    }


@router.post("/api/auth/login", summary="Sign in to company workspace")
async def api_login(
    payload: CompanyLoginInput,
    response: Response,
    db: Session = Depends(get_db),
):
    company = db.query(Company).filter(Company.email == payload.email, Company.is_active == True).first()
    if not company or not verify_password(payload.password, company.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please verify your credentials.",
        )

    token = create_session_token(company.id)
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=token,
        max_age=settings.SESSION_MAX_AGE_SECONDS,
        httponly=True,
        samesite=settings.COOKIE_SAMESITE,
        secure=settings.COOKIE_SECURE,
    )
    return {
        "success": True,
        "company": {
            "id": company.id,
            "name": company.name,
            "email": company.email,
            "industry": company.industry,
        },
    }


@router.post("/api/auth/logout", summary="Log out of company workspace")
async def api_logout(response: Response):
    response.delete_cookie(
        key=settings.SESSION_COOKIE_NAME,
        httponly=True,
        samesite=settings.COOKIE_SAMESITE,
        secure=settings.COOKIE_SECURE,
    )
    return {"success": True}


# ==========================================
# 3. Prediction API
# ==========================================

@router.post(
    "/api/predict",
    response_model=PredictionResponse,
    summary="Generate pre-shipment return risk prediction",
    status_code=status.HTTP_200_OK,
)
async def predict_api(
    payload: PredictionInput,
    company: Optional[Company] = Depends(get_current_company_optional),
    db: Session = Depends(get_db),
) -> PredictionResponse:
    if not prediction_service.is_ready():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Prediction model is not loaded or unavailable on this server.",
        )

    try:
        response = prediction_service.predict(
            input_data=payload,
            db=db if company else None,
            company_id=company.id if company else None,
            source="api",
        )
        return response
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation error during feature engineering: {str(ve)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during prediction inference: {str(e)}",
        )


@router.get("/api/predictions", summary="Get paginated historical predictions for authenticated company")
async def get_predictions_api(
    page: int = 1,
    page_size: int = 15,
    risk_level: Optional[str] = None,
    category: Optional[str] = None,
    company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    offset = max(0, (page - 1) * page_size)
    query = db.query(PredictionRecord).filter(PredictionRecord.company_id == company.id)

    if risk_level and risk_level != "all":
        query = query.filter(PredictionRecord.risk_level == risk_level)
    if category and category != "all":
        query = query.filter(PredictionRecord.input_features.like(f'%"product_category": "{category}"%'))

    total_count = query.count()
    records = query.order_by(desc(PredictionRecord.created_at)).offset(offset).limit(page_size).all()
    total_pages = max(1, (total_count + page_size - 1) // page_size)

    items = []
    for r in records:
        f = r.get_features_dict()
        items.append({
            "id": r.id,
            "created_at": r.created_at.strftime("%Y-%m-%d %H:%M"),
            "category": f.get("product_category", "-"),
            "sub_category": f.get("sub_category", "-"),
            "brand": f.get("brand", "-"),
            "sku": r.product.product_identifier if r.product else "-",
            "prob_pct": round(r.predicted_return_probability * 100.0, 1),
            "predicted_class": r.predicted_return_class,
            "risk_label": r.risk_label,
            "risk_level": r.risk_level,
            "source": r.prediction_source,
        })

    return {
        "total": total_count,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "records": items,
    }


@router.get("/api/predictions/{prediction_id}", summary="Get single prediction detail")
async def get_prediction_detail_api(
    prediction_id: int,
    company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    record = (
        db.query(PredictionRecord)
        .filter(
            PredictionRecord.id == prediction_id,
            PredictionRecord.company_id == company.id,  # STRICT COMPANY ISOLATION
        )
        .first()
    )
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction record not found.")

    features = record.get_features_dict()
    category = features.get("product_category", "")
    sku = record.product.product_identifier if record.product else None

    comparison = analytics_service.get_historical_context_for_prediction(
        db=db,
        company_id=company.id,
        category=category,
        sku=sku,
    )

    return {
        "id": record.id,
        "created_at": record.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "model_version": record.model_version,
        "predicted_class": record.predicted_return_class,
        "prob_pct": round(record.predicted_return_probability * 100.0, 1),
        "threshold_pct": round(record.decision_threshold * 100.0, 1),
        "risk_label": record.risk_label,
        "risk_level": record.risk_level,
        "source": record.prediction_source,
        "features": features,
        "comparison": comparison.model_dump(),
    }


# ==========================================
# 4. Dashboard & Analytics API
# ==========================================

@router.get("/api/dashboard", summary="Company operational return analytics data")
async def get_dashboard_api(
    company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    stats = analytics_service.get_dashboard_summary(db, company.id)
    # Convert recent_predictions to serialized dicts
    recent_serialized = []
    for pred in stats.get("recent_predictions", []):
        f = pred.get_features_dict()
        recent_serialized.append({
            "id": pred.id,
            "created_at": pred.created_at.strftime("%Y-%m-%d %H:%M"),
            "category": f.get("product_category", "-"),
            "sub_category": f.get("sub_category", "-"),
            "sku": pred.product.product_identifier if pred.product else "-",
            "prob_pct": round(pred.predicted_return_probability * 100.0, 1),
            "predicted_class": pred.predicted_return_class,
            "risk_label": pred.risk_label,
            "risk_level": pred.risk_level,
        })
    stats["recent_predictions"] = recent_serialized
    return stats


@router.get("/api/analytics", summary="Get historical returns segmentation and factor correlations")
async def get_analytics_api(
    segment: str = "product_category",
    min_samples: int = 5,
    company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    valid_segments = [
        "product_category", "sub_category", "brand", "product_identifier",
        "fulfillment_type", "payment_method", "return_reason"
    ]
    if segment not in valid_segments:
        segment = "product_category"

    safe_min = max(1, min(100, min_samples))
    segment_data = analytics_service.get_segment_breakdown(db, company.id, segment, safe_min)
    correlations = analytics_service.get_feature_correlations(db, company.id)

    return {
        "segment": segment,
        "min_samples": safe_min,
        "segment_data": segment_data,
        "feature_correlations": correlations,
    }


@router.get("/api/performance", summary="Get period-over-period performance comparison")
async def get_performance_api(
    window_days: int = 30,
    company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    safe_window = 30 if window_days not in [14, 30, 60, 90] else window_days
    comparison = analytics_service.get_period_comparison(db, company.id, safe_window)
    return comparison


# ==========================================
# 5. Recommendations API
# ==========================================

@router.get("/api/recommendations", summary="Get return reduction recommendations and impact tracking")
async def get_recommendations_api(
    status_filter: Optional[str] = "all",
    company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    recommendation_service.generate_recommendations(db, company.id)
    recs = recommendation_service.get_recommendations(db, company.id, status_filter)

    items = []
    for r in recs:
        impact = None
        if r.status == "implemented" and r.implementation_date:
            impact = recommendation_service.get_implementation_impact(db, company.id, r.id)
        items.append({
            "id": r.id,
            "segment_type": r.segment_type,
            "segment_identifier": r.segment_identifier,
            "category": r.category,
            "sub_category": r.sub_category,
            "title": r.recommendation_title,
            "text": r.recommendation_text,
            "evidence": r.get_evidence_dict(),
            "suggested_action": r.suggested_action,
            "status": r.status,
            "implementation_date": str(r.implementation_date) if r.implementation_date else None,
            "review_notes": r.review_notes,
            "created_at": r.created_at.strftime("%Y-%m-%d"),
            "impact": impact,
        })
    return items


@router.post("/api/recommendations/{rec_id}/status", summary="Update recommendation status and review notes")
async def update_recommendation_status_api(
    rec_id: int,
    payload: RecommendationUpdateInput,
    company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    parsed_date = None
    if payload.implementation_date:
        try:
            parsed_date = datetime.strptime(payload.implementation_date.strip(), "%Y-%m-%d").date()
        except ValueError:
            pass

    updated = recommendation_service.update_status(
        db=db,
        company_id=company.id,
        recommendation_id=rec_id,
        new_status=payload.status,
        review_notes=payload.review_notes,
        implementation_date=parsed_date,
    )
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found.")
    return {"success": True, "status": updated.status}


# ==========================================
# 6. Ingestion & Demo Data API
# ==========================================

@router.post("/api/import", summary="Upload CSV of historical returns")
async def api_upload_csv(
    file: UploadFile = File(...),
    company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File exceeds 10 MB limit.")

    try:
        csv_text = contents.decode("utf-8")
    except UnicodeDecodeError:
        try:
            csv_text = contents.decode("latin-1")
        except Exception:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid file encoding.")

    result = import_service.parse_and_validate_csv(csv_text, db, company.id)
    return result


@router.get("/api/import/template", summary="Download CSV template")
async def api_download_template():
    csv_text = import_service.get_csv_template_content()
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=return_records_template.csv"},
    )


@router.post("/api/import/demo-seed", summary="Seed sample records for current company")
async def api_demo_seed(
    company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    res = import_service.seed_demo_data_for_company(db, company.id)
    if not res.get("success"):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=res.get("error"))
    return res
