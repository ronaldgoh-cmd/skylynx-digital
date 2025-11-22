from sqlalchemy.orm import Session
from .. import models


def seed_modules(db: Session):
    default_modules = [
        {"code": "EMP", "name": "Employee Management"},
        {"code": "SAL", "name": "Salary Management"},
        {"code": "LEAVE", "name": "Leave Management"},
    ]
    for mod in default_modules:
        existing = db.query(models.Module).filter(models.Module.code == mod["code"]).first()
        if not existing:
            db.add(models.Module(code=mod["code"], name=mod["name"]))
    db.commit()