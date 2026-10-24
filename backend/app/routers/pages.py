from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.auth.dependencies import get_current_company_optional
from app.auth.security import generate_csrf_token
from app.services.prediction_service import prediction_service

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

router = APIRouter(include_in_schema=False)


@router.get("/", response_class=HTMLResponse)
async def home_page(
    request: Request,
    db: Session = Depends(get_db),
):
    """Render the main landing page with workflow explanation and realistic preview."""
    current_company = get_current_company_optional(request, db)
    session_cookie = request.cookies.get(settings.SESSION_COOKIE_NAME) or ""
    csrf_token = generate_csrf_token(session_cookie)

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "page_title": "Product Return Risk Intelligence Platform",
            "threshold": round(prediction_service.threshold, 4),
            "model_ready": prediction_service.is_ready(),
            "current_company": current_company,
            "csrf_token": csrf_token,
        },
    )


@router.get("/methodology", response_class=HTMLResponse)
async def methodology_page(
    request: Request,
    db: Session = Depends(get_db),
):
    """Render technical methodology, data leakage audit, and model comparison documentation."""
    current_company = get_current_company_optional(request, db)
    metadata = prediction_service.get_metadata()
    return templates.TemplateResponse(
        request=request,
        name="methodology.html",
        context={
            "page_title": "Model Methodology & Validation",
            "metadata": metadata,
            "threshold": round(prediction_service.threshold, 4),
            "current_company": current_company,
        },
    )


@router.get("/about", response_class=HTMLResponse)
async def about_page(
    request: Request,
    db: Session = Depends(get_db),
):
    """Render system architecture and project background."""
    current_company = get_current_company_optional(request, db)
    return templates.TemplateResponse(
        request=request,
        name="about.html",
        context={
            "page_title": "About This System",
            "version": settings.VERSION,
            "current_company": current_company,
        },
    )
