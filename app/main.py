from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.api.organizations import router as organizations_router


app = FastAPI(
    title="Meets API",
    description="Meeting scheduling backend",
    version="1.0.0"
)


app.include_router(organizations_router)


@app.get("/health")
def health_check():
    return {
        "status": "ok"
    }


@app.get("/health/db")
def database_health_check(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT 1"))

    return {
        "database": result.scalar() == 1
    }