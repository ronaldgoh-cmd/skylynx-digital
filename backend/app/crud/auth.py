# File: backend/app/crud/auth.py (NEW FILE)
from sqlalchemy.orm import Session
from .. import models, security


def authenticate_user(db: Session, email: str, password: str):
    user = db.query(models.User).filter(models.User.email == email, models.User.is_active == True).first()
    if not user:
        return None
    if not security.verify_password(password, user.hashed_password):
        return None
    return user


def create_user(db: Session, email: str, password: str, company_id: int):
    hashed = security.hash_password(password)
    user = models.User(email=email, hashed_password=hashed, company_id=company_id)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_company_modules(db: Session, company_id: int):
    q = (
        db.query(models.Module.name)
        .join(models.CompanyModule, models.Module.id == models.CompanyModule.module_id)
        .filter(models.CompanyModule.company_id == company_id, models.CompanyModule.is_enabled == True, models.Module.is_active == True)
    )
    return [row.name for row in q.all()]