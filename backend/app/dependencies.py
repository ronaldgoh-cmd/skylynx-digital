# File: backend/app/dependencies.py (NEW FILE)
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from .database import get_db
from .config import settings
from . import models

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id: int | None = payload.get("sub")
        company_id: int | None = payload.get("company_id")
        if user_id is None or company_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.id == user_id, models.User.company_id == company_id, models.User.is_active == True).first()
    if user is None:
        raise credentials_exception
    return user