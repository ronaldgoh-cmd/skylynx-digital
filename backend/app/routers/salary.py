# File: backend/app/routers/salary.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import schemas
from ..database import get_db
from ..crud import salary as salary_crud
from ..dependencies import get_current_user

router = APIRouter(prefix="/salary", tags=["salary"])


@router.get("/", response_model=list[schemas.Salary])
def list_salary(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return salary_crud.list_salaries(db, company_id=current_user.company_id)


@router.post("/", response_model=schemas.Salary)
def create_salary(payload: schemas.SalaryCreate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return salary_crud.create_salary(db, company_id=current_user.company_id, payload=payload)