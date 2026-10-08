from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from typing import Optional

from app.api.dependencies import get_db
from app.models.organization import Organization
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate
)


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
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Organization name already exists"
        )
    db.refresh(organization)

    return organization


@router.get(
    "/",
    response_model=list[OrganizationResponse]
)
def get_organizations(
    db: Session = Depends(get_db),
    limit: Optional[int] = Query(None, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    query = db.query(Organization).order_by(Organization.id)
    if limit is not None:
        query = query.limit(limit)
    organizations = query.offset(offset).all()

    return organizations


@router.put(
    "/{organization_id}",
    response_model=OrganizationResponse
)
def update_organization(
    organization_id: int,
    organization_data: OrganizationUpdate,
    db: Session = Depends(get_db)
):
    organization = db.get(Organization, organization_id)

    if organization is None:
        raise HTTPException(
            status_code=404,
            detail="Organization not found"
        )

    organization.name = organization_data.name

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Organization name already exists"
        )
    db.refresh(organization)

    return organization


@router.delete(
    "/{organization_id}"
)
def delete_organization(
    organization_id: int,
    db: Session = Depends(get_db)
):
    organization = db.get(Organization, organization_id)

    if organization is None:
        raise HTTPException(
            status_code=404,
            detail="Organization not found"
        )

    db.delete(organization)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Organization cannot be deleted while it has related records"
        )

    return {
        "message": "Organization deleted successfully"
    }