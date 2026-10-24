from typing import Optional
from fastapi import Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.company import Company
from app.auth.security import decode_session_token, verify_csrf_token


class AuthenticationRequiredException(Exception):
    """Raised when an unauthenticated request attempts to access a protected page."""
    def __init__(self, redirect_url: str = "/login"):
        self.redirect_url = redirect_url


def get_current_company_optional(
    request: Request,
    db: Session = Depends(get_db),
) -> Optional[Company]:
    """Retrieve the authenticated company from session cookie, or None if unauthenticated."""
    cookie = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if not cookie:
        return None

    company_id = decode_session_token(cookie)
    if not company_id:
        return None

    company = (
        db.query(Company)
        .filter(Company.id == company_id, Company.is_active == True)
        .first()
    )
    return company


def get_current_company(
    request: Request,
    db: Session = Depends(get_db),
) -> Company:
    """Enforce authentication dependency for protected routes and APIs."""
    company = get_current_company_optional(request, db)
    if company is None:
        if request.url.path.startswith("/api/") or request.headers.get("accept") == "application/json":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required. Please log in with your company credentials.",
            )
        # For server-rendered browser pages, redirect to login
        raise AuthenticationRequiredException(redirect_url=f"/login?next={request.url.path}")
    return company


def validate_csrf(request: Request, submitted_token: Optional[str] = None) -> bool:
    """Validate CSRF token against active session cookie or header."""
    cookie = request.cookies.get(settings.SESSION_COOKIE_NAME) or ""
    token = submitted_token or request.headers.get("X-CSRF-Token")
    if not token:
        return False
    return verify_csrf_token(cookie, token)
