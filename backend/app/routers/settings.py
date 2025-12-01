# backend/app/routers/settings.py
from __future__ import annotations

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Response,
    status,
)
from sqlalchemy.orm import Session
from sqlalchemy import select

from .. import models, schemas
from ..database import get_db
from .auth import get_current_user

router = APIRouter(tags=["settings"])


# ---------- Company settings ----------


@router.get(
    "/company/settings",
    response_model=schemas.CompanySettingsOut,
)
def get_company_settings(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Return the company settings for the logged-in user's company.
    If none exist yet, create a default row.
    """
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not linked to a company.",
        )

    # Find or create settings row
    stmt = select(models.CompanySettings).where(
        models.CompanySettings.company_id == current_user.company_id
    )
    cs = db.execute(stmt).scalar_one_or_none()

    if cs is None:
        # Look up company name for a nicer default
        company = db.get(models.Company, current_user.company_id)
        name = company.name if company else "Company"
        cs = models.CompanySettings(
            company_id=current_user.company_id,
            name=name,
            detail1="",
            detail2="",
            version=None,
            about=None,
            logo=None,
        )
        db.add(cs)
        db.commit()
        db.refresh(cs)

    return schemas.CompanySettingsOut(
        name=cs.name,
        detail1=cs.detail1,
        detail2=cs.detail2,
        version=cs.version,
        about=cs.about,
        has_logo=bool(cs.logo),
    )


@router.put(
    "/company/settings",
    response_model=schemas.CompanySettingsOut,
)
def update_company_settings(
    payload: schemas.CompanySettingsUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Update basic company settings fields for the logged-in user's company.
    """
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not linked to a company.",
        )

    stmt = select(models.CompanySettings).where(
        models.CompanySettings.company_id == current_user.company_id
    )
    cs = db.execute(stmt).scalar_one_or_none()

    if cs is None:
        # Create if missing
        company = db.get(models.Company, current_user.company_id)
        name = company.name if company else "Company"
        cs = models.CompanySettings(
            company_id=current_user.company_id,
            name=name,
            detail1="",
            detail2="",
            version=None,
            about=None,
            logo=None,
        )
        db.add(cs)
        db.commit()
        db.refresh(cs)

    # Only overwrite fields that are provided (not None)
    if payload.name is not None:
        cs.name = payload.name
    if payload.detail1 is not None:
        cs.detail1 = payload.detail1
    if payload.detail2 is not None:
        cs.detail2 = payload.detail2
    if payload.version is not None:
        cs.version = payload.version
    if payload.about is not None:
        cs.about = payload.about

    db.commit()
    db.refresh(cs)

    return schemas.CompanySettingsOut(
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
    Return the company logo as raw PNG bytes.
    """
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not linked to a company.",
        )

    stmt = select(models.CompanySettings).where(
        models.CompanySettings.company_id == current_user.company_id
    )
    cs = db.execute(stmt).scalar_one_or_none()

    if cs is None or not cs.logo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Logo not set.",
        )

    return Response(content=cs.logo, media_type="image/png")


@router.post("/company/logo", status_code=status.HTTP_204_NO_CONTENT)
async def upload_company_logo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Upload or replace the company logo. We store raw bytes as PNG in the DB.
    """
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not linked to a company.",
        )

    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file.",
        )

    stmt = select(models.CompanySettings).where(
        models.CompanySettings.company_id == current_user.company_id
    )
    cs = db.execute(stmt).scalar_one_or_none()

    if cs is None:
        company = db.get(models.Company, current_user.company_id)
        name = company.name if company else "Company"
        cs = models.CompanySettings(
            company_id=current_user.company_id,
            name=name,
            detail1="",
            detail2="",
            version=None,
            about=None,
            logo=None,
        )
        db.add(cs)
        db.commit()
        db.refresh(cs)

    cs.logo = content
    db.commit()
    # 204 → no body


# ---------- User settings ----------


@router.get(
    "/user/settings/me",
    response_model=schemas.UserSettingsOut,
)
def get_my_settings(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Return (and lazily create) user-specific settings for the logged-in user.
    """
    stmt = select(models.UserSettings).where(
        models.UserSettings.user_id == current_user.id
    )
    us = db.execute(stmt).scalar_one_or_none()

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
        timezone=us.timezone,
        theme=us.theme,
    )


@router.put(
    "/user/settings/me",
    response_model=schemas.UserSettingsOut,
)
def update_my_settings(
    payload: schemas.UserSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Update timezone/theme for the logged-in user.
    """
    stmt = select(models.UserSettings).where(
        models.UserSettings.user_id == current_user.id
    )
    us = db.execute(stmt).scalar_one_or_none()

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
        timezone=us.timezone,
        theme=us.theme,
    )
