# File: backend/app/crud/leave.py (NEW FILE)
from sqlalchemy.orm import Session
from .. import models, schemas


def list_leaves(db: Session, company_id: int):
    return db.query(models.Leave).filter(models.Leave.company_id == company_id).all()


def create_leave(db: Session, company_id: int, payload: schemas.LeaveCreate):
    record = models.Leave(company_id=company_id, **payload.dict())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record