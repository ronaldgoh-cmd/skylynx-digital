from sqlalchemy.orm import Session
from .. import models
from ..schemas import LeaveCreate


def list_leaves(db: Session, company_id: int):
    return db.query(models.Leave).filter(models.Leave.company_id == company_id).order_by(models.Leave.id.desc()).all()


def create_leave(db: Session, company_id: int, leave_in: LeaveCreate):
    leave = models.Leave(
        company_id=company_id,
        employee_id=leave_in.employee_id,
        start_date=leave_in.start_date,
        end_date=leave_in.end_date,
        status=leave_in.status,
    )
    db.add(leave)
    db.commit()
    db.refresh(leave)
    return leave