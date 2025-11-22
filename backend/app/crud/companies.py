from sqlalchemy.orm import Session
from .. import models


def get_company_modules(db: Session, company_id: int):
    rows = (
        db.query(models.Module.code)
        .join(models.CompanyModule, models.CompanyModule.module_id == models.Module.id)
        .filter(models.CompanyModule.company_id == company_id, models.CompanyModule.enabled.is_(True))
        .all()
    )
    return [r[0] for r in rows]