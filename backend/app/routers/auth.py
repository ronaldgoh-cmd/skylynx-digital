# File: backend/app/routers/auth.py
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .. import schemas, models, security
from ..database import get_db
from ..crud import auth as auth_crud
from ..config import JWT_EXPIRE_MINUTES
from ..dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = auth_crud.authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect username or password")
    modules = auth_crud.get_company_modules(db, user.company_id)
    access_token = security.create_access_token(
        data={"sub": str(user.id), "company_id": user.company_id, "modules": modules},
        expires_delta=timedelta(minutes=JWT_EXPIRE_MINUTES),
    )
    return schemas.Token(access_token=access_token, company_id=user.company_id, modules=modules, token_type="bearer")


@router.post("/signup", response_model=schemas.User)
def signup(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = auth_crud.create_user(db, email=payload.email, password=payload.password, company_id=payload.company_id)
    return user


@router.get("/me", response_model=schemas.User)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user