from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..dependencies import get_current_user
from ..crud import employees

router = APIRouter(prefix="/employees", tags=["employees"])


@router.get("/", response_model=list[schemas.EmployeeOut])
def list_all(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return employees.list_employees(db, company_id=current_user.company_id)


@router.post("/", response_model=schemas.EmployeeOut)
def create(employee_in: schemas.EmployeeCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return employees.create_employee(db, company_id=current_user.company_id, employee_in=employee_in)