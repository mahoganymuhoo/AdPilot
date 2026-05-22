from fastapi import APIRouter
from app.api.v1 import metrics, insights, strategies, onboarding, settings

router = APIRouter(prefix="/api/v1")
router.include_router(metrics.router)
router.include_router(insights.router)
router.include_router(strategies.router)
router.include_router(onboarding.router)
router.include_router(settings.router)
