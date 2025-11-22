from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..dependencies import get_current_user
from ..crud import companies

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("/me", response_model=schemas.CompanyOut)
def my_company(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    company = db.query(models.Company).filter(models.Company.id == current_user.company_id).first()
    if not company:
        return None
    module_codes = companies.get_company_modules(db, company.id)
    company.modules = [models.Module(id=0, code=code, name="") for code in module_codes]
    return company