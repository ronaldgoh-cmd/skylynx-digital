# backend/app/routers/settings.py
from __future__ import annotations

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    UploadFile,
    File,
    Response,
)
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..security import get_current_user

router = APIRouter(tags=["settings"])


# ---------- Company settings ----------


@router.get("/company/settings", response_model=schemas.CompanySettingsOut)
def get_company_settings(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Return the CompanySettings for the logged-in user's company.
    If missing, create a default row.
    """
    company_id = current_user.company_id
    if company_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not attached to a company.",
        )

    cs = (
        db.query(models.CompanySettings)
        .filter(models.CompanySettings.company_id == company_id)
        .first()
    )
    if cs is None:
        cs = models.CompanySettings(
            company_id=company_id,
            name="Skylynx Demo",
            detail1="",
            detail2="",
            version="1.0.0",
            about="",
        )
        db.add(cs)
        db.commit()
        db.refresh(cs)

    return schemas.CompanySettingsOut(
        id=cs.id,
        company_id=cs.company_id,
        name=cs.name,
        detail1=cs.detail1,
        detail2=cs.detail2,
        version=cs.version,
        about=cs.about,
        has_logo=bool(cs.logo),
    )


@router.put("/company/settings", response_model=schemas.CompanySettingsOut)
def update_company_settings(
    payload: schemas.CompanySettingsUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Update company settings for the logged-in user's company.
    Only non-None fields are updated.
    """
    company_id = current_user.company_id
    if company_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not attached to a company.",
        )

    cs = (
        db.query(models.CompanySettings)
        .filter(models.CompanySettings.company_id == company_id)
        .first()
    )
    if cs is None:
        cs = models.CompanySettings(
            company_id=company_id,
            name="Skylynx Demo",
            detail1="",
            detail2="",
            version="1.0.0",
            about="",
        )
        db.add(cs)
        db.commit()
        db.refresh(cs)

    for field in ["name", "detail1", "detail2", "version", "about"]:
        value = getattr(payload, field)
        if value is not None:
            setattr(cs, field, value)

    db.commit()
    db.refresh(cs)

    return schemas.CompanySettingsOut(
        id=cs.id,
        company_id=cs.company_id,
        name=cs.name,
        detail1=cs.detail1,
        detail2=cs.detail2,
        version=cs.version,
        about=cs.about,
        has_logo=bool(cs.logo),
    )


@router.get("/company/logo")
def get_company_logo(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Return the company logo bytes (PNG) if set.
    """
    company_id = current_user.company_id
    if company_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not attached to a company.",
        )

    cs = (
        db.query(models.CompanySettings)
        .filter(models.CompanySettings.company_id == company_id)
        .first()
    )
    if cs is None or not cs.logo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No logo set.")

    return Response(content=cs.logo, media_type="image/png")


@router.post("/company/logo")
async def upload_company_logo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Upload/replace the company logo (stored as PNG bytes).
    """
    company_id = current_user.company_id
    if company_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not attached to a company.",
        )

    data = await file.read()
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty logo file.",
        )

    cs = (
        db.query(models.CompanySettings)
        .filter(models.CompanySettings.company_id == company_id)
        .first()
    )
    if cs is None:
        cs = models.CompanySettings(company_id=company_id)
        db.add(cs)
        db.commit()
        db.refresh(cs)

    cs.logo = data
    db.commit()

    return {"ok": True}


# ---------- User settings ----------


@router.get("/user/settings/me", response_model=schemas.UserSettingsOut)
def get_my_user_settings(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Read the current user's UI settings.
    If missing, create a default row.
    """
    us = (
        db.query(models.UserSettings)
        .filter(models.UserSettings.user_id == current_user.id)
        .first()
    )
    if us is None:
        us = models.UserSettings(
            user_id=current_user.id,
            timezone="Asia/Singapore",
            theme="light",
        )
        db.add(us)
        db.commit()
        db.refresh(us)

    return schemas.UserSettingsOut(
        id=us.id,
        user_id=us.user_id,
        timezone=us.timezone,
        theme=us.theme,
    )


@router.put("/user/settings/me", response_model=schemas.UserSettingsOut)
def update_my_user_settings(
    payload: schemas.UserSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Update the current user's UI settings.
    """
    us = (
        db.query(models.UserSettings)
        .filter(models.UserSettings.user_id == current_user.id)
        .first()
    )
    if us is None:
        us = models.UserSettings(
            user_id=current_user.id,
            timezone="Asia/Singapore",
            theme="light",
        )
        db.add(us)
        db.commit()
        db.refresh(us)

    if payload.timezone is not None:
        us.timezone = payload.timezone
    if payload.theme is not None:
        us.theme = payload.theme

    db.commit()
    db.refresh(us)

    return schemas.UserSettingsOut(
        id=us.id,
        user_id=us.user_id,
        timezone=us.timezone,
        theme=us.theme,
    )
