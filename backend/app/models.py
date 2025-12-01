# backend/app/models.py
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    Date,
    Numeric,
    UniqueConstraint,
    LargeBinary,
)
from sqlalchemy.orm import relationship

from .database import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)

    # Relationships
    modules = relationship(
        "CompanyModule",
        back_populates="company",
        cascade="all, delete-orphan",
    )
    users = relationship(
        "User",
        back_populates="company",
        cascade="all, delete-orphan",
    )
    employees = relationship(
        "Employee",
        back_populates="company",
        cascade="all, delete-orphan",
    )
    salaries = relationship(
        "Salary",
        back_populates="company",
        cascade="all, delete-orphan",
    )
    leaves = relationship(
        "Leave",
        back_populates="company",
        cascade="all, delete-orphan",
    )
    # One row of UI header info per company
    settings = relationship(
        "CompanySettings",
        back_populates="company",
        uselist=False,
        cascade="all, delete-orphan",
    )


class Module(Base):
    __tablename__ = "modules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)

    company_links = relationship(
        "CompanyModule",
        back_populates="module",
        cascade="all, delete-orphan",
    )


class CompanyModule(Base):
    __tablename__ = "company_modules"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"))
    module_id = Column(Integer, ForeignKey("modules.id", ondelete="CASCADE"))
    is_enabled = Column(Boolean, default=True)

    company = relationship("Company", back_populates="modules")
    module = relationship("Module", back_populates="company_links")

    __table_args__ = (
        UniqueConstraint("company_id", "module_id", name="uix_company_module"),
    )


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"))
    is_active = Column(Boolean, default=True)

    company = relationship("Company", back_populates="users")
    # One set of UI preferences per user
    settings = relationship(
        "UserSettings",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    name = Column(String, nullable=False)
    role = Column(String, nullable=True)
    hire_date = Column(Date, nullable=True)

    company = relationship("Company", back_populates="employees")
    salaries = relationship(
        "Salary",
        back_populates="employee",
        cascade="all, delete-orphan",
    )
    leaves = relationship(
        "Leave",
        back_populates="employee",
        cascade="all, delete-orphan",
    )


class Salary(Base):
    __tablename__ = "salaries"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"))
    amount = Column(Numeric(12, 2), nullable=False)
    pay_date = Column(Date, nullable=False)

    company = relationship("Company", back_populates="salaries")
    employee = relationship("Employee", back_populates="salaries")


class Leave(Base):
    __tablename__ = "leaves"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"))
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(String, default="pending")

    company = relationship("Company", back_populates="leaves")
    employee = relationship("Employee", back_populates="leaves")


class CompanySettings(Base):
    """
    Shared header info per company (used by main_window & Company Settings dialog).
    """
    __tablename__ = "company_settings"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )

    name = Column(String, nullable=True)
    detail1 = Column(String, nullable=True)
    detail2 = Column(String, nullable=True)
    version = Column(String, nullable=True)
    about = Column(String, nullable=True)
    # Stored as PNG bytes from the desktop app
    logo = Column(LargeBinary, nullable=True)

    company = relationship("Company", back_populates="settings")


class UserSettings(Base):
    """
    Per-user UI preferences (timezone, light/dark theme, etc.).
    """
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )
    timezone = Column(String, nullable=True)
    theme = Column(String, nullable=True)

    user = relationship("User", back_populates="settings")
