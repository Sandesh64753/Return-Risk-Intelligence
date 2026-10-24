from datetime import datetime
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, Form, Request, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.company import Company
from app.models.recommendation import RecommendationRecord
from app.auth.dependencies import get_current_company
from app.auth.security import generate_csrf_token, verify_csrf_token
from app.services.recommendation_service import recommendation_service

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

router = APIRouter(include_in_schema=False)


@router.get("/recommendations", response_class=HTMLResponse)
async def recommendations_page(
    request: Request,
    status_filter: Optional[str] = "all",
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    """Render actionable recommendations with supporting evidence, review controls, and impact tracking."""
    session_cookie = request.cookies.get(settings.SESSION_COOKIE_NAME) or ""
    csrf_token = generate_csrf_token(session_cookie)

    # 1. Trigger automated evaluation of return data to identify new opportunities
    recommendation_service.generate_recommendations(db, current_company.id)

    # 2. Fetch scoped recommendations
    recs = recommendation_service.get_recommendations(db, current_company.id, status_filter=status_filter)

    # 3. For implemented recommendations, compute before-and-after outcome impact
    impacts = {}
    for r in recs:
        if r.status == "implemented" and r.implementation_date:
            impacts[r.id] = recommendation_service.get_implementation_impact(db, current_company.id, r.id)

    return templates.TemplateResponse(
        request=request,
        name="recommendations.html",
        context={
            "page_title": f"{current_company.name} | Return Reduction Recommendations",
            "current_company": current_company,
            "csrf_token": csrf_token,
            "status_filter": status_filter or "all",
            "recommendations": recs,
            "impacts": impacts,
        },
    )


@router.post("/recommendations/{rec_id}/status")
async def update_recommendation_status(
    request: Request,
    rec_id: int,
    status_val: str = Form(..., alias="status"),
    review_notes: Optional[str] = Form(None),
    implementation_date: Optional[str] = Form(None),
    csrf_token: Optional[str] = Form(None),
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    """Update recommendation status, implementation date, and review notes with strict company scoping."""
    session_cookie = request.cookies.get(settings.SESSION_COOKIE_NAME) or ""
    if not verify_csrf_token(session_cookie, csrf_token or ""):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session security token expired.",
        )

    parsed_date = None
    if implementation_date:
        try:
            parsed_date = datetime.strptime(implementation_date.strip(), "%Y-%m-%d").date()
        except ValueError:
            pass

    updated = recommendation_service.update_status(
        db=db,
        company_id=current_company.id,
        recommendation_id=rec_id,
        new_status=status_val,
        review_notes=review_notes,
        implementation_date=parsed_date,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation not found or access denied.",
        )

    return RedirectResponse(
        url="/recommendations?updated=1",
        status_code=status.HTTP_303_SEE_OTHER,
    )
