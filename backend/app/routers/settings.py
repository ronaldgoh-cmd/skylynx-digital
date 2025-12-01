# backend/app/routers/settings.py
from __future__ import annotations

from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Response,
)
from sqlalchemy.orm import Session
from sqlalchemy import select

from .. import models, schemas
from ..database import SessionLocal
from .auth import get_current_user

router = APIRouter(tags=["settings"])


# Local get_db helper (safe – only used in this router)
def get_db() -> Any:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------- Company settings ----------


@router.get("/company/settings", response_model=schemas.CompanySettingsOut)
def get_company_settings(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.CompanySettingsOut:
    """
    Return the company header/settings for the logged-in user's company.
    If missing, create a simple default row.
    """
    company_id = current_user.company_id
    if company_id is None:
        raise HTTPException(status_code=400, detail="User is not linked to any company")

    stmt = select(models.CompanySettings).where(
        models.CompanySettings.company_id == company_id
    )
    cs = db.execute(stmt).scalar_one_or_none()

    if cs is None:
        # Create a default row for this company
        cs = models.CompanySettings(
            company_id=company_id,
            name="Skylynx Demo",
            detail1="",
            detail2="",
            version="",
            about="",
        )
        db.add(cs)
        db.commit()
        db.refresh(cs)

    return schemas.CompanySettingsOut(
        id=cs.id,
        company_id=cs.company_id,
        name=cs.name or "",
        detail1=cs.detail1 or "",
        detail2=cs.detail2 or "",
        version=cs.version or "",
        about=cs.about or "",
        has_logo=bool(cs.logo),
    )


@router.put("/company/settings", response_model=schemas.CompanySettingsOut)
def update_company_settings(
    payload: schemas.CompanySettingsUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.CompanySettingsOut:
    """
    Update the company settings for the logged-in user's company.
    Only fields provided in the payload are updated.
    """
    company_id = current_user.company_id
    if company_id is None:
        raise HTTPException(status_code=400, detail="User is not linked to any company")

    stmt = select(models.CompanySettings).where(
        models.CompanySettings.company_id == company_id
    )
    cs = db.execute(stmt).scalar_one_or_none()

    if cs is None:
        cs = models.CompanySettings(
            company_id=company_id,
            name="Skylynx Demo",
            detail1="",
            detail2="",
            version="",
            about="",
        )
        db.add(cs)
        db.commit()
        db.refresh(cs)

    update_data = payload.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(cs, field, value)

    db.commit()
    db.refresh(cs)

    return schemas.CompanySettingsOut(
        id=cs.id,
        company_id=cs.company_id,
        name=cs.name or "",
        detail1=cs.detail1 or "",
        detail2=cs.detail2 or "",
        version=cs.version or "",
        about=cs.about or "",
        has_logo=bool(cs.logo),
    )


@router.get("/company/logo")
def get_company_logo(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    """
    Return the company logo image (PNG bytes).
    """
    company_id = current_user.company_id
    if company_id is None:
        raise HTTPException(status_code=400, detail="User is not linked to any company")

    stmt = select(models.CompanySettings).where(
        models.CompanySettings.company_id == company_id
    )
    cs = db.execute(stmt).scalar_one_or_none()

    if cs is None or not cs.logo:
        raise HTTPException(status_code=404, detail="No logo configured for this company")

    # We always store PNG from the desktop client
    return Response(content=cs.logo, media_type="image/png")


@router.post("/company/logo")
async def upload_company_logo(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    Upload/replace the company logo.

    The desktop client already converts images to PNG before upload,
    but we accept any image/* content-type and store the raw bytes.
    """
    company_id = current_user.company_id
    if company_id is None:
        raise HTTPException(status_code=400, detail="User is not linked to any company")

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty file")

    stmt = select(models.CompanySettings).where(
        models.CompanySettings.company_id == company_id
    )
    cs = db.execute(stmt).scalar_one_or_none()

    if cs is None:
        cs = models.CompanySettings(
            company_id=company_id,
            name="Skylynx Demo",
            detail1="",
            detail2="",
            version="",
            about="",
            logo=contents,
        )
        db.add(cs)
    else:
        cs.logo = contents

    db.commit()
    return {"ok": True}


# ---------- User settings (per login user) ----------


@router.get("/user/settings/me", response_model=schemas.UserSettingsOut)
def get_my_settings(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.UserSettingsOut:
    """
    Return the settings row for the current user.
    Create a default one if missing.
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


@router.put("/user/settings/me", response_model=schemas.UserSettingsOut)
def update_my_settings(
    payload: schemas.UserSettingsUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.UserSettingsOut:
    """
    Update settings for the current user.
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

    update_data = payload.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(us, field, value)

    db.commit()
    db.refresh(us)

    return schemas.UserSettingsOut(
        id=us.id,
        timezone=us.timezone,
        theme=us.theme,
    )
