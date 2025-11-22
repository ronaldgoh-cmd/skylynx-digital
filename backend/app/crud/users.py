from sqlalchemy.orm import Session
from .. import models, auth
from ..schemas import UserCreate


def get_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(db: Session, user_in: UserCreate):
    hashed = auth.hash_password(user_in.password)
    db_user = models.User(
        company_id=user_in.company_id,
        email=user_in.email,
        password_hash=hashed,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user