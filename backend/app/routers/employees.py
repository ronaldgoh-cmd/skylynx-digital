# File: backend/app/routers/employees.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import schemas
from ..database import get_db
from ..crud import employees as employees_crud
from ..dependencies import get_current_user

router = APIRouter(prefix="/employees", tags=["employees"])


@router.get("/", response_model=list[schemas.Employee])
def list_employees(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return employees_crud.list_employees(db, company_id=current_user.company_id)


@router.post("/", response_model=schemas.Employee)
def create_employee(payload: schemas.EmployeeCreate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return employees_crud.create_employee(db, company_id=current_user.company_id, payload=payload)