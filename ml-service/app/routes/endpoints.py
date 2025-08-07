from fastapi import APIRouter
from app.routes.api import model  # Use `select` for async queries

router = APIRouter()

router.include_router(model.router, prefix="/api", tags=["Endpoints"])

