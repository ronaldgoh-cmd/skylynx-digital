from sqlalchemy.orm import Session
from .. import models
from ..schemas import EmployeeCreate


def list_employees(db: Session, company_id: int):
    return db.query(models.Employee).filter(models.Employee.company_id == company_id).order_by(models.Employee.id.desc()).all()


def create_employee(db: Session, company_id: int, employee_in: EmployeeCreate):
    emp = models.Employee(
        company_id=company_id,
        name=employee_in.name,
        position=employee_in.position,
        salary=employee_in.salary,
    )
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return emp