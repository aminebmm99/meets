from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.models.organization import Organization
from app.schemas.organization import OrganizationCreate, OrganizationResponse


router = APIRouter(
    prefix="/organizations",
    tags=["Organizations"]
)


@router.post(
    "/",
    response_model=OrganizationResponse
)
def create_organization(
    organization_data: OrganizationCreate,
    db: Session = Depends(get_db)
):
    organization = Organization(
        name=organization_data.name
    )

    db.add(organization)
    db.commit()
    db.refresh(organization)

    return organization


@router.get(
    "/{organization_id}",
    response_model=OrganizationResponse
)
def get_organization(
    organization_id: int,
    db: Session = Depends(get_db)
):
    organization = db.get(Organization, organization_id)

    if organization is None:
        raise HTTPException(
            status_code=404,
            detail="Organization not found"
        )

    return organization