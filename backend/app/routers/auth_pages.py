import logging
from typing import Optional
from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.company import Company
from app.schemas import CompanyRegisterInput, CompanyLoginInput
from app.auth.security import (
    hash_password,
    verify_password,
    create_session_token,
    generate_csrf_token,
    verify_csrf_token,
)
from app.auth.dependencies import get_current_company_optional

logger = logging.getLogger("prduct_return_prediction.auth_pages")
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

router = APIRouter(include_in_schema=False)


def _get_auth_context(request: Request, errors: Optional[dict] = None, form_data: Optional[dict] = None) -> dict:
    session_cookie = request.cookies.get(settings.SESSION_COOKIE_NAME) or ""
    csrf_token = generate_csrf_token(session_cookie)
    return {
        "request": request,
        "csrf_token": csrf_token,
        "errors": errors or {},
        "form_data": form_data or {},
        "current_company": None,
    }


@router.get("/register", response_class=HTMLResponse)
async def register_page(
    request: Request,
    db: Session = Depends(get_db),
):
    """Render company registration page."""
    current_company = get_current_company_optional(request, db)
    if current_company:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    context = _get_auth_context(request)
    context.update({"page_title": "Company Registration | Workspace Setup"})
    return templates.TemplateResponse(request=request, name="register.html", context=context)


@router.post("/register", response_class=HTMLResponse)
async def handle_registration(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    industry: Optional[str] = Form(None),
    csrf_token: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """Process company workspace registration with server-side validation and secure password hashing."""
    session_cookie = request.cookies.get(settings.SESSION_COOKIE_NAME) or ""
    if not verify_csrf_token(session_cookie, csrf_token or ""):
        context = _get_auth_context(request, {"_general": "Session security token expired. Please try again."})
        context.update({"page_title": "Company Registration"})
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context=context,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    raw_data = {
        "name": name.strip(),
        "email": email.strip(),
        "password": password,
        "confirm_password": confirm_password,
        "industry": industry.strip() if industry else None,
    }

    errors = {}
    if password != confirm_password:
        errors["confirm_password"] = "Passwords do not match."

    try:
        validated = CompanyRegisterInput(**raw_data)
    except ValidationError as ve:
        for err in ve.errors():
            loc = str(err["loc"][-1])
            errors[loc] = err["msg"]

    if errors:
        context = _get_auth_context(request, errors, raw_data)
        context.update({"page_title": "Company Registration"})
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context=context,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    # Check for existing email (case-insensitive)
    existing = db.query(Company).filter(Company.email == validated.email).first()
    if existing:
        errors["email"] = "An account with this company email address is already registered."
        context = _get_auth_context(request, errors, raw_data)
        context.update({"page_title": "Company Registration"})
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context=context,
            status_code=status.HTTP_409_CONFLICT,
        )

    # Hash password using Argon2id
    pwd_hash = hash_password(validated.password)

    # Persist new company
    new_company = Company(
        name=validated.name,
        email=validated.email,
        password_hash=pwd_hash,
        industry=validated.industry,
        is_active=True,
    )
    db.add(new_company)
    db.commit()
    db.refresh(new_company)

    logger.info(f"Registered new company workspace: id={new_company.id}, email='{new_company.email}'")

    # Generate session cookie
    token = create_session_token(new_company.id)
    response = RedirectResponse(url="/dashboard?registered=1", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=token,
        max_age=settings.SESSION_MAX_AGE_SECONDS,
        httponly=True,
        samesite=settings.COOKIE_SAMESITE,
        secure=settings.COOKIE_SECURE,
    )
    return response


@router.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    next: Optional[str] = None,
    message: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Render company authentication login page."""
    current_company = get_current_company_optional(request, db)
    if current_company:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    context = _get_auth_context(request)
    context.update({
        "page_title": "Company Sign In",
        "next": next or "/dashboard",
        "info_message": "You have been successfully logged out." if message == "logged_out" else None,
    })
    return templates.TemplateResponse(request=request, name="login.html", context=context)


@router.post("/login", response_class=HTMLResponse)
async def handle_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    next: Optional[str] = Form("/dashboard"),
    csrf_token: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """Authenticate company credentials and issue signed session cookie."""
    session_cookie = request.cookies.get(settings.SESSION_COOKIE_NAME) or ""
    if not verify_csrf_token(session_cookie, csrf_token or ""):
        context = _get_auth_context(request, {"_general": "Session security token expired. Please try again."})
        context.update({"page_title": "Company Sign In", "next": next})
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context=context,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    norm_email = email.strip().lower()
    company = db.query(Company).filter(Company.email == norm_email, Company.is_active == True).first()

    if not company or not verify_password(password, company.password_hash):
        errors = {"_general": "Invalid email address or password. Please verify your credentials."}
        context = _get_auth_context(request, errors, {"email": norm_email})
        context.update({"page_title": "Company Sign In", "next": next})
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context=context,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    # Valid authentication
    token = create_session_token(company.id)
    target_url = next if (next and next.startswith("/") and not next.startswith("//")) else "/dashboard"
    response = RedirectResponse(url=target_url, status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=token,
        max_age=settings.SESSION_MAX_AGE_SECONDS,
        httponly=True,
        samesite=settings.COOKIE_SAMESITE,
        secure=settings.COOKIE_SECURE,
    )
    return response


@router.get("/logout")
@router.post("/logout")
async def handle_logout(request: Request):
    """Invalidate authenticated session by clearing the session cookie."""
    response = RedirectResponse(url="/login?message=logged_out", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(
        key=settings.SESSION_COOKIE_NAME,
        httponly=True,
        samesite=settings.COOKIE_SAMESITE,
        secure=settings.COOKIE_SECURE,
    )
    return response
