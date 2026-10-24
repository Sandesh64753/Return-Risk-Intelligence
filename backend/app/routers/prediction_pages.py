import json
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, Form, Request, status, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.config import settings
from app.database import get_db
from app.models.company import Company
from app.models.prediction import PredictionRecord
from app.models.product import Product
from app.auth.dependencies import get_current_company
from app.auth.security import generate_csrf_token, verify_csrf_token
from app.schemas import (
    PredictionInput,
    VALID_CATEGORIES,
    ALL_PRODUCT_CATEGORIES,
    ALL_SUB_CATEGORIES,
    ALL_BRANDS,
    ALL_FULFILLMENT_TYPES,
    ALL_PAYMENT_METHODS,
)
from app.services.prediction_service import prediction_service
from app.services.analytics_service import analytics_service

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

router = APIRouter(include_in_schema=False)

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


def _get_predict_context(
    request: Request,
    current_company: Company,
    form_data: Optional[dict] = None,
    errors: Optional[dict] = None,
) -> dict:
    session_cookie = request.cookies.get(settings.SESSION_COOKIE_NAME) or ""
    csrf_token = generate_csrf_token(session_cookie)

    default_data = {
        "product_category": "Fashion",
        "sub_category": "Women",
        "brand": "Brand_10",
        "product_identifier": "SKU-FASH-100",
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
    }
    if form_data:
        default_data.update(form_data)

    return {
        "request": request,
        "current_company": current_company,
        "csrf_token": csrf_token,
        "categories": ALL_PRODUCT_CATEGORIES,
        "valid_categories_json": json.dumps(VALID_CATEGORIES),
        "brands": ALL_BRANDS,
        "fulfillment_types": ALL_FULFILLMENT_TYPES,
        "payment_methods": ALL_PAYMENT_METHODS,
        "presets": DEMO_PRESETS,
        "presets_json": json.dumps({k: v["data"] for k, v in DEMO_PRESETS.items()}),
        "form_data": default_data,
        "errors": errors or {},
        "threshold": round(prediction_service.threshold, 4),
        "model_ready": prediction_service.is_ready(),
    }


@router.get("/predict", response_class=HTMLResponse)
async def predict_page(
    request: Request,
    current_company: Company = Depends(get_current_company),
):
    """Render the pre-shipment risk evaluation form for authenticated company."""
    context = _get_predict_context(request, current_company)
    context.update({"page_title": "Order Return Risk Evaluation"})
    return templates.TemplateResponse(request=request, name="predict.html", context=context)


@router.post("/predict", response_class=HTMLResponse)
async def handle_predict_form(
    request: Request,
    product_category: str = Form(...),
    sub_category: str = Form(...),
    brand: str = Form(...),
    product_price: float = Form(...),
    discount_percent: float = Form(...),
    product_rating: float = Form(...),
    review_count: int = Form(...),
    fragile_item: int = Form(...),
    warranty_available: int = Form(...),
    defect_rate: float = Form(...),
    seller_rating: float = Form(...),
    fulfillment_type: str = Form(...),
    payment_method: str = Form(...),
    quantity: int = Form(...),
    shipping_distance_km: float = Form(...),
    wishlist_before_purchase: int = Form(...),
    product_page_views: int = Form(...),
    product_identifier: Optional[str] = Form(None),
    csrf_token: Optional[str] = Form(None),
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    """Validate submitted order inputs, run ML inference, persist audit record, and render results."""
    session_cookie = request.cookies.get(settings.SESSION_COOKIE_NAME) or ""
    if not verify_csrf_token(session_cookie, csrf_token or ""):
        context = _get_predict_context(request, current_company, errors={"_general": "Session security token expired. Please re-submit."})
        context.update({"page_title": "Order Risk Evaluation", "form_error": "Session token expired."})
        return templates.TemplateResponse(
            request=request,
            name="predict.html",
            context=context,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    raw_data = {
        "product_category": product_category,
        "sub_category": sub_category,
        "brand": brand,
        "product_identifier": product_identifier.strip() if product_identifier else None,
        "product_price": product_price,
        "discount_percent": discount_percent,
        "product_rating": product_rating,
        "review_count": review_count,
        "fragile_item": fragile_item,
        "warranty_available": warranty_available,
        "defect_rate": defect_rate,
        "seller_rating": seller_rating,
        "fulfillment_type": fulfillment_type,
        "payment_method": payment_method,
        "quantity": quantity,
        "shipping_distance_km": shipping_distance_km,
        "wishlist_before_purchase": wishlist_before_purchase,
        "product_page_views": product_page_views,
    }

    errors = {}
    try:
        validated_input = PredictionInput(**raw_data)
    except ValidationError as ve:
        for err in ve.errors():
            loc = str(err["loc"][-1])
            errors[loc] = err["msg"]
        context = _get_predict_context(request, current_company, raw_data, errors)
        context.update({
            "page_title": "Order Risk Evaluation",
            "form_error": "Please correct the highlighted input fields.",
        })
        return templates.TemplateResponse(
            request=request,
            name="predict.html",
            context=context,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    if not prediction_service.is_ready():
        context = _get_predict_context(request, current_company, raw_data)
        context.update({
            "page_title": "Order Risk Evaluation",
            "system_error": "Model inference service is currently initializing or unavailable.",
        })
        return templates.TemplateResponse(
            request=request,
            name="predict.html",
            context=context,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    try:
        result = prediction_service.predict(
            input_data=validated_input,
            db=db,
            company_id=current_company.id,
            source="manual_form",
        )
    except Exception as e:
        context = _get_predict_context(request, current_company, raw_data)
        context.update({
            "page_title": "Order Risk Evaluation",
            "system_error": f"Error running inference: {str(e)}",
        })
        return templates.TemplateResponse(
            request=request,
            name="predict.html",
            context=context,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return templates.TemplateResponse(
        request=request,
        name="result.html",
        context={
            "page_title": "Prediction Assessment & Historical Analysis",
            "current_company": current_company,
            "result": result,
            "threshold": round(prediction_service.threshold, 4),
        },
    )


@router.get("/predictions", response_class=HTMLResponse)
async def predictions_history_page(
    request: Request,
    risk_level: Optional[str] = None,
    category: Optional[str] = None,
    page: int = 1,
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    """View paginated prediction history strictly scoped to the authenticated company."""
    page_size = 15
    offset = max(0, (page - 1) * page_size)

    query = db.query(PredictionRecord).filter(PredictionRecord.company_id == current_company.id)

    if risk_level and risk_level != "all":
        query = query.filter(PredictionRecord.risk_level == risk_level)
    if category and category != "all":
        query = query.filter(PredictionRecord.input_features.like(f'%"product_category": "{category}"%'))

    total_count = query.count()
    records = query.order_by(desc(PredictionRecord.created_at)).offset(offset).limit(page_size).all()

    total_pages = max(1, (total_count + page_size - 1) // page_size)

    # Process features for tabular display
    processed_records = []
    for r in records:
        f = r.get_features_dict()
        processed_records.append({
            "id": r.id,
            "created_at": r.created_at,
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

    return templates.TemplateResponse(
        request=request,
        name="predictions_history.html",
        context={
            "page_title": f"{current_company.name} | Prediction History",
            "current_company": current_company,
            "records": processed_records,
            "total_count": total_count,
            "page": page,
            "total_pages": total_pages,
            "risk_level": risk_level or "all",
            "category": category or "all",
            "categories": ALL_PRODUCT_CATEGORIES,
        },
    )


@router.get("/predictions/{prediction_id}", response_class=HTMLResponse)
async def prediction_detail_page(
    request: Request,
    prediction_id: int,
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    """View single prediction detail with strict company data isolation."""
    record = (
        db.query(PredictionRecord)
        .filter(
            PredictionRecord.id == prediction_id,
            PredictionRecord.company_id == current_company.id,  # STRICT COMPANY ISOLATION
        )
        .first()
    )
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction record not found or access denied.",
        )

    features = record.get_features_dict()
    category = features.get("product_category", "")
    sku = record.product.product_identifier if record.product else None

    # Fetch contextual historical comparison
    comparison = analytics_service.get_historical_context_for_prediction(
        db=db,
        company_id=current_company.id,
        category=category,
        sku=sku,
    )

    return templates.TemplateResponse(
        request=request,
        name="prediction_detail.html",
        context={
            "page_title": f"Prediction Audit #{record.id}",
            "current_company": current_company,
            "record": record,
            "features": features,
            "comparison": comparison,
            "prob_pct": round(record.predicted_return_probability * 100.0, 1),
            "thresh_pct": round(record.decision_threshold * 100.0, 1),
        },
    )
