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
from app.services.prediction_service import prediction_service

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

router = APIRouter(include_in_schema=False)


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(
    request: Request,
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    """Render company operations dashboard with scoped returns intelligence and activity."""
    session_cookie = request.cookies.get(settings.SESSION_COOKIE_NAME) or ""
    csrf_token = generate_csrf_token(session_cookie)

    stats = analytics_service.get_dashboard_summary(db, current_company.id)

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "page_title": f"{current_company.name} | Operations Dashboard",
            "current_company": current_company,
            "csrf_token": csrf_token,
            "stats": stats,
            "threshold": round(prediction_service.threshold, 4),
            "model_ready": prediction_service.is_ready(),
        },
    )
