# File: backend/app/routers/company_settings.py
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Response
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models, schemas
from ..security import get_current_user

router = APIRouter(
    prefix="/company",
    tags=["company"],
)


def _get_or_create_company_settings(db: Session, company_id: int) -> models.CompanySettings:
    cs = (
        db.query(models.CompanySettings)
        .filter(models.CompanySettings.company_id == company_id)
        .first()
    )
    if cs is None:
        # try to pull name from Company table
        company = db.query(models.Company).filter(models.Company.id == company_id).first()
        name = company.name if company else "Company"
        cs = models.CompanySettings(
            company_id=company_id,
            name=name,
            detail1="",
            detail2="",
            version="",
            about="",
        )
        db.add(cs)
        db.commit()
        db.refresh(cs)
    return cs


@router.get("/settings", response_model=schemas.CompanySettingsOut)
def get_company_settings(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return the current company's header/settings info.
    """
    cs = _get_or_create_company_settings(db, current_user.company_id)
    return cs


@router.put("/settings", response_model=schemas.CompanySettingsOut)
def update_company_settings(
    payload: schemas.CompanySettingsUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update the current company's settings text fields (name, detail1, detail2, version, about).
    """
    cs = _get_or_create_company_settings(db, current_user.company_id)

    cs.name = payload.name
    cs.detail1 = payload.detail1 or ""
    cs.detail2 = payload.detail2 or ""
    cs.version = payload.version or ""
    cs.about = payload.about or ""

    db.commit()
    db.refresh(cs)
    return cs


@router.get("/logo")
def get_company_logo(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return the company logo as raw bytes (PNG), or 404 if none.
    """
    cs = (
        db.query(models.CompanySettings)
        .filter(models.CompanySettings.company_id == current_user.company_id)
        .first()
    )
    if cs is None or not cs.logo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No logo set")

    return Response(content=cs.logo, media_type="image/png")


@router.put("/logo", status_code=status.HTTP_204_NO_CONTENT)
async def update_company_logo(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update the company logo with an uploaded image file.
    """
    data = await file.read()
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")

    cs = _get_or_create_company_settings(db, current_user.company_id)
    cs.logo = data
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
