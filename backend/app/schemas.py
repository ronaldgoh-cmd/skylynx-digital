# backend/app/schemas.py
from __future__ import annotations

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, EmailStr


# ---------- Modules / companies / users ----------


class ModuleBase(BaseModel):
    name: str
    description: Optional[str] = None


class ModuleCreate(ModuleBase):
    pass


class Module(ModuleBase):
    id: int
    is_active: bool

    class Config:
        orm_mode = True


class CompanyBase(BaseModel):
    name: str


class CompanyCreate(CompanyBase):
    pass


class Company(CompanyBase):
    id: int
    is_active: bool
    modules: List[Module] = []

    class Config:
        orm_mode = True


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    company_id: int


class User(BaseModel):
    id: int
    email: EmailStr
    company_id: int
    is_active: bool

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    company_id: int
    modules: List[str]


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ---------- Employees / salary / leave ----------


class EmployeeBase(BaseModel):
    name: str
    role: Optional[str] = None
    hire_date: Optional[date] = None


class EmployeeCreate(EmployeeBase):
    pass


class Employee(EmployeeBase):
    id: int
    company_id: int

    class Config:
        orm_mode = True


class SalaryBase(BaseModel):
    employee_id: int
    amount: float
    pay_date: date


class SalaryCreate(SalaryBase):
    pass


class Salary(SalaryBase):
    id: int
    company_id: int

    class Config:
        orm_mode = True


class LeaveBase(BaseModel):
    employee_id: int
    start_date: date
    end_date: date
    status: str = "pending"


class LeaveCreate(LeaveBase):
    pass


class Leave(LeaveBase):
    id: int
    company_id: int

    class Config:
        orm_mode = True


# ---------- Company / user settings for UI ----------


class CompanySettingsBase(BaseModel):
    name: Optional[str] = None
    detail1: Optional[str] = None
    detail2: Optional[str] = None
    version: Optional[str] = None
    about: Optional[str] = None


class CompanySettingsOut(CompanySettingsBase):
    """
    What the API returns to the desktop app for /company/settings.
    """
    id: int
    company_id: int
    has_logo: bool = False

    class Config:
        orm_mode = True


class CompanySettingsUpdate(CompanySettingsBase):
    """
    Partial update: any field can be omitted (left as None) and will not be changed.
    """
    pass


class UserSettingsBase(BaseModel):
    timezone: Optional[str] = None
    theme: Optional[str] = None


class UserSettingsOut(UserSettingsBase):
    id: int
    user_id: int

    class Config:
        orm_mode = True


class UserSettingsUpdate(UserSettingsBase):
    """
    Partial update: timezone and/or theme may be provided.
    """
    pass
