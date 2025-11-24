# File: backend/app/models.py (NEW FILE)
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Date, Numeric, UniqueConstraint
from sqlalchemy.orm import relationship
from .database import Base

class Company(Base):
    __tablename__ = "companies"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
    modules = relationship("CompanyModule", back_populates="company", cascade="all, delete")
    users = relationship("User", back_populates="company")

class Module(Base):
    __tablename__ = "modules"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    company_links = relationship("CompanyModule", back_populates="module")

class CompanyModule(Base):
    __tablename__ = "company_modules"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"))
    module_id = Column(Integer, ForeignKey("modules.id", ondelete="CASCADE"))
    is_enabled = Column(Boolean, default=True)

    company = relationship("Company", back_populates="modules")
    module = relationship("Module", back_populates="company_links")

    __table_args__ = (UniqueConstraint("company_id", "module_id", name="uix_company_module"),)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"))
    is_active = Column(Boolean, default=True)

    company = relationship("Company", back_populates="users")

class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), index=True)
    name = Column(String, nullable=False)
    role = Column(String, nullable=True)
    hire_date = Column(Date, nullable=True)

class Salary(Base):
    __tablename__ = "salaries"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    amount = Column(Numeric(12, 2), nullable=False)
    pay_date = Column(Date, nullable=False)

class Leave(Base):
    __tablename__ = "leaves"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(String, default="pending")