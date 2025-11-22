from sqlalchemy.orm import Session
from .. import models
from ..schemas import SalaryCreate


def list_salaries(db: Session, company_id: int):
    return db.query(models.Salary).filter(models.Salary.company_id == company_id).order_by(models.Salary.id.desc()).all()


def create_salary(db: Session, company_id: int, salary_in: SalaryCreate):
    sal = models.Salary(
        company_id=company_id,
        employee_id=salary_in.employee_id,
        amount=salary_in.amount,
        period_start=salary_in.period_start,
        period_end=salary_in.period_end,
    )
    db.add(sal)
    db.commit()
    db.refresh(sal)
    return sal