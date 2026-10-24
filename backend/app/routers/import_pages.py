from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, Request, UploadFile, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.company import Company
from app.auth.dependencies import get_current_company
from app.auth.security import generate_csrf_token, verify_csrf_token
from app.services.import_service import import_service, EXPECTED_CSV_HEADERS

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

router = APIRouter(include_in_schema=False)


@router.get("/import", response_class=HTMLResponse)
async def import_page(
    request: Request,
    current_company: Company = Depends(get_current_company),
):
    """Render historical data import page with schema documentation and file upload."""
    session_cookie = request.cookies.get(settings.SESSION_COOKIE_NAME) or ""
    csrf_token = generate_csrf_token(session_cookie)

    return templates.TemplateResponse(
        request=request,
        name="import.html",
        context={
            "page_title": f"{current_company.name} | Historical Data Import",
            "current_company": current_company,
            "csrf_token": csrf_token,
            "headers": EXPECTED_CSV_HEADERS,
            "import_result": None,
        },
    )


@router.get("/import/template")
async def download_csv_template(
    current_company: Company = Depends(get_current_company),
):
    """Download standardized CSV schema template for historical actual return records."""
    csv_text = import_service.get_csv_template_content()
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=return_records_template.csv"},
    )


@router.post("/import", response_class=HTMLResponse)
async def handle_csv_import(
    request: Request,
    file: UploadFile = File(...),
    csrf_token: Optional[str] = Form(None),
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    """Process uploaded CSV file, validate schema and datatypes, and persist records scoped to company."""
    session_cookie = request.cookies.get(settings.SESSION_COOKIE_NAME) or ""
    if not verify_csrf_token(session_cookie, csrf_token or ""):
        context = {
            "request": request,
            "page_title": f"{current_company.name} | Historical Data Import",
            "current_company": current_company,
            "csrf_token": generate_csrf_token(session_cookie),
            "headers": EXPECTED_CSV_HEADERS,
            "import_error": "Session security token expired. Please try again.",
            "import_result": None,
        }
        return templates.TemplateResponse(request=request, name="import.html", context=context, status_code=status.HTTP_400_BAD_REQUEST)

    # Validate file size (10MB limit)
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        context = {
            "request": request,
            "page_title": f"{current_company.name} | Historical Data Import",
            "current_company": current_company,
            "csrf_token": generate_csrf_token(session_cookie),
            "headers": EXPECTED_CSV_HEADERS,
            "import_error": "File size exceeds the 10 MB limit.",
            "import_result": None,
        }
        return templates.TemplateResponse(request=request, name="import.html", context=context, status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

    try:
        csv_text = contents.decode("utf-8")
    except UnicodeDecodeError:
        try:
            csv_text = contents.decode("latin-1")
        except Exception:
            context = {
                "request": request,
                "page_title": f"{current_company.name} | Historical Data Import",
                "current_company": current_company,
                "csrf_token": generate_csrf_token(session_cookie),
                "headers": EXPECTED_CSV_HEADERS,
                "import_error": "Could not decode file content. Please upload a standard UTF-8 encoded CSV.",
                "import_result": None,
            }
            return templates.TemplateResponse(request=request, name="import.html", context=context, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

    result = import_service.parse_and_validate_csv(
        csv_content=csv_text,
        db=db,
        company_id=current_company.id,  # STRICT COMPANY SCOPING
    )

    return templates.TemplateResponse(
        request=request,
        name="import.html",
        context={
            "page_title": f"{current_company.name} | Import Results",
            "current_company": current_company,
            "csrf_token": generate_csrf_token(session_cookie),
            "headers": EXPECTED_CSV_HEADERS,
            "import_result": result,
            "filename": file.filename,
        },
    )


@router.post("/import/demo-seed")
async def handle_demo_seed(
    request: Request,
    csrf_token: Optional[str] = Form(None),
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    """Seed sample historical records from repository dataset into current company workspace."""
    session_cookie = request.cookies.get(settings.SESSION_COOKIE_NAME) or ""
    if not verify_csrf_token(session_cookie, csrf_token or ""):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Security token expired.")

    res = import_service.seed_demo_data_for_company(db, current_company.id)
    if not res.get("success"):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=res.get("error"))

    return RedirectResponse(
        url="/dashboard?seeded=1",
        status_code=status.HTTP_303_SEE_OTHER,
    )
