from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.company import Company
from app.auth.dependencies import get_current_company
from app.auth.security import generate_csrf_token
from app.services.analytics_service import analytics_service

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

router = APIRouter(include_in_schema=False)


@router.get("/analytics", response_class=HTMLResponse)
async def analytics_page(
    request: Request,
    segment: str = "product_category",
    min_samples: int = 5,
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    """Render historical return analytics with segmentation, confidence intervals, and factor analysis."""
    session_cookie = request.cookies.get(settings.SESSION_COOKIE_NAME) or ""
    csrf_token = generate_csrf_token(session_cookie)

    # Allowed breakdown dimensions
    valid_segments = {
        "product_category": "Product Category",
        "sub_category": "Sub-Category",
        "brand": "Manufacturer Brand",
        "product_identifier": "Product SKU",
        "fulfillment_type": "Fulfillment Channel",
        "payment_method": "Payment Method",
        "return_reason": "Return Reason Distribution",
    }
    if segment not in valid_segments:
        segment = "product_category"

    safe_min_samples = max(1, min(100, min_samples))

    segment_data = analytics_service.get_segment_breakdown(
        db=db,
        company_id=current_company.id,
        segment_field=segment,
        min_sample_size=safe_min_samples,
    )

    feature_correlations = analytics_service.get_feature_correlations(
        db=db,
        company_id=current_company.id,
    )

    return templates.TemplateResponse(
        request=request,
        name="analytics.html",
        context={
            "page_title": f"{current_company.name} | Historical Return Analytics",
            "current_company": current_company,
            "csrf_token": csrf_token,
            "segments_map": valid_segments,
            "current_segment": segment,
            "current_segment_name": valid_segments[segment],
            "min_samples": safe_min_samples,
            "segment_data": segment_data,
            "feature_correlations": feature_correlations,
        },
    )


@router.get("/performance", response_class=HTMLResponse)
async def performance_page(
    request: Request,
    window_days: int = 30,
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    """Render performance trend monitoring page comparing equivalent observation periods."""
    session_cookie = request.cookies.get(settings.SESSION_COOKIE_NAME) or ""
    csrf_token = generate_csrf_token(session_cookie)

    safe_window = 30 if window_days not in [14, 30, 60, 90] else window_days

    comparison = analytics_service.get_period_comparison(
        db=db,
        company_id=current_company.id,
        window_days=safe_window,
    )

    return templates.TemplateResponse(
        request=request,
        name="performance.html",
        context={
            "page_title": f"{current_company.name} | Return Performance & Improvement Monitoring",
            "current_company": current_company,
            "csrf_token": csrf_token,
            "window_days": safe_window,
            "comparison": comparison,
        },
    )
