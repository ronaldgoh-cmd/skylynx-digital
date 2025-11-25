# File: backend/app/crud/salary.py
from sqlalchemy.orm import Session
from .. import models, schemas


def list_salaries(db: Session, company_id: int):
    return (
        db.query(models.Salary)
        .filter(models.Salary.company_id == company_id)
        .all()
    )


def create_salary(db: Session, company_id: int, payload: schemas.SalaryCreate):
    record = models.Salary(company_id=company_id, **payload.dict())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record