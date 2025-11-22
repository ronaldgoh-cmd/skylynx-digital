from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from .. import models, schemas, auth
from ..dependencies import get_db_session
from ..crud import users, companies

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db_session)):
    user = users.get_by_email(db, form_data.username)
    if not user or not auth.verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    modules = companies.get_company_modules(db, user.company_id)
    token = auth.create_access_token({"sub": str(user.id), "company_id": user.company_id, "modules": modules})
    return schemas.Token(access_token=token, company_id=user.company_id, modules=modules)