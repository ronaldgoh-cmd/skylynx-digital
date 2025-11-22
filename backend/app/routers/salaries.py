from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..dependencies import get_current_user
from ..crud import salaries

router = APIRouter(prefix="/salaries", tags=["salaries"])


@router.get("/", response_model=list[schemas.SalaryOut])
def list_all(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db_session)):
    return salaries.list_salaries(db, company_id=current_user.company_id)


@router.post("/", response_model=schemas.SalaryOut)
def create(
    salary_in: schemas.SalaryCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    return salaries.create_salary(db, company_id=current_user.company_id, salary_in=salary_in)