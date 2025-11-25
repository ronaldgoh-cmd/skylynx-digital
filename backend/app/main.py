# backend/app/main.py
from fastapi import FastAPI
from sqlalchemy import select

from .database import Base, engine, SessionLocal
from . import models
from .routers import auth, employees, salary, leave
from .security import hash_password


def init_db() -> None:
    """
    Create tables and ensure demo company, modules and admin user exist.
    Safe to call multiple times.
    """
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 1) Ensure demo company exists
        company_stmt = select(models.Company).where(models.Company.name == "Skylynx Demo")
        company = db.execute(company_stmt).scalar_one_or_none()
        if company is None:
            company = models.Company(name="Skylynx Demo", is_active=True)
            db.add(company)
            db.commit()
            db.refresh(company)

        # 2) Ensure basic modules exist
        module_names = ["employees", "salary", "leave"]
        modules: list[models.Module] = []
        for name in module_names:
            m_stmt = select(models.Module).where(models.Module.name == name)
            m = db.execute(m_stmt).scalar_one_or_none()
            if m is None:
                m = models.Module(name=name, description=f"{name.title()} module")
                db.add(m)
                db.commit()
                db.refresh(m)
            modules.append(m)

        # 3) Ensure company-module links exist
        for m in modules:
            link_stmt = select(models.CompanyModule).where(
                models.CompanyModule.company_id == company.id,
                models.CompanyModule.module_id == m.id,
            )
            link = db.execute(link_stmt).scalar_one_or_none()
            if link is None:
                link = models.CompanyModule(
                    company_id=company.id,
                    module_id=m.id,
                    is_enabled=True,
                )
                db.add(link)
        db.commit()

        # 4) Ensure admin user exists
        admin_stmt = select(models.User).where(models.User.email == "admin@skylynx.local")
        admin = db.execute(admin_stmt).scalar_one_or_none()
        if admin is None:
            admin = models.User(
                email="admin@skylynx.local",
                hashed_password=hash_password("ChangeMe123!"),
                company_id=company.id,
                is_active=True,
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()


# Run DB init once when the module is imported
init_db()

app = FastAPI(title="Skylynx Digital ERP API")

# Attach routers
app.include_router(auth.router)
app.include_router(employees.router)
app.include_router(salary.router)
app.include_router(leave.router)


@app.get("/")
def root():
    return {"message": "Skylynx Digital API is running"}
