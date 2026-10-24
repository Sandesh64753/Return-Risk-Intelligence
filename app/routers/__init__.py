from app.routers.pages import router as pages_router
from app.routers.auth_pages import router as auth_router
from app.routers.dashboard_pages import router as dashboard_router
from app.routers.prediction_pages import router as prediction_router
from app.routers.analytics_pages import router as analytics_router
from app.routers.recommendation_pages import router as recommendation_router
from app.routers.import_pages import router as import_router
from app.routers.api import router as api_router

__all__ = [
    "pages_router",
    "auth_router",
    "dashboard_router",
    "prediction_router",
    "analytics_router",
    "recommendation_router",
    "import_router",
    "api_router",
]
