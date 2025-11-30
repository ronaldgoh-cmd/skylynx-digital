# File: backend/app/routers/user_settings.py
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models, schemas
from ..security import get_current_user

router = APIRouter(
    prefix="/user/settings",
    tags=["user-settings"],
)


def _get_or_create_user_settings(db: Session, user_id: int) -> models.UserSettings:
    us = (
        db.query(models.UserSettings)
        .filter(models.UserSettings.user_id == user_id)
        .first()
    )
    if us is None:
        us = models.UserSettings(
            user_id=user_id,
            timezone="Asia/Singapore",
            theme="light",
        )
        db.add(us)
        db.commit()
        db.refresh(us)
    return us


@router.get("/me", response_model=schemas.UserSettingsOut)
def get_my_settings(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return the current user's settings (timezone, theme).
    """
    us = _get_or_create_user_settings(db, current_user.id)
    return us


@router.put("/me", response_model=schemas.UserSettingsOut)
def update_my_settings(
    payload: schemas.UserSettingsUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update the current user's settings.
    """
    us = _get_or_create_user_settings(db, current_user.id)

    us.timezone = payload.timezone
    us.theme = payload.theme

    db.commit()
    db.refresh(us)
    return us
