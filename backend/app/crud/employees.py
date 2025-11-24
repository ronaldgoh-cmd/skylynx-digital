# File: backend/app/crud/employees.py (NEW FILE)
from sqlalchemy.orm import Session
from .. import models, schemas


def list_employees(db: Session, company_id: int):
    return db.query(models.Employee).filter(models.Employee.company_id == company_id).all()


def create_employee(db: Session, company_id: int, payload: schemas.EmployeeCreate):
    emp = models.Employee(company_id=company_id, **payload.dict())
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return emp