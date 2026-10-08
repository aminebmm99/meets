from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.responses import FileResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.api.meetings import router as meetings_router
from app.api.dependencies import get_db
from app.api.organizations import router as organizations_router
from app.api.users import router as users_router
from app.api.auth import router as auth_router
from app.api.participants import router as participants_router
from app.api.availability import router as availability_router
app = FastAPI(
    title="Meets API",
    description="Meeting scheduling backend",
    version="1.0.0"
)

WEB_PAGE = Path(__file__).parent / "static" / "index.html"


@app.get("/", include_in_schema=False)
def home_page():
    return FileResponse(WEB_PAGE)


app.include_router(organizations_router)
app.include_router(users_router)
app.include_router(auth_router)
app.include_router(meetings_router)
app.include_router(participants_router)
app.include_router(availability_router)
from app.api.scheduling import router as scheduling_router
from app.api.scheduling_requests import (
    router as scheduling_requests_router
)
app.include_router(scheduling_router)
app.include_router(scheduling_requests_router)

@app.get("/health")
def health_check():
    return {
        "status": "ok"
    }


@app.get("/health/db")
def database_health_check(
    db: Session = Depends(get_db)
):
    result = db.execute(text("SELECT 1"))

    return {
        "database": result.scalar() == 1
    }
