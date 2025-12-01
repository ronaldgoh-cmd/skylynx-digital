# backend/app/schemas.py
from datetime import date
from typing import List, Optional

from pydantic import BaseModel, EmailStr


# ---------------------------------------------------------------------------
# Modules / Companies / Users
# ---------------------------------------------------------------------------


class ModuleBase(BaseModel):
    name: str
    description: Optional[str] = None


class ModuleCreate(ModuleBase):
    pass


class Module(ModuleBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True


class CompanyBase(BaseModel):
    name: str


class CompanyCreate(CompanyBase):
    pass


class Company(CompanyBase):
    id: int
    is_active: bool
    modules: List[Module] = []

    class Config:
        from_attributes = True


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
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    company_id: int
    modules: List[str]


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ---------------------------------------------------------------------------
# Employees / Salary / Leave
# ---------------------------------------------------------------------------


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
        from_attributes = True


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
        from_attributes = True


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
        from_attributes = True


# ---------------------------------------------------------------------------
# Company / User settings for UI
# ---------------------------------------------------------------------------


class CompanySettingsBase(BaseModel):
    name: Optional[str] = None
    detail1: Optional[str] = None
    detail2: Optional[str] = None
    version: Optional[str] = None
    about: Optional[str] = None


class CompanySettingsOut(CompanySettingsBase):
    # Optional so the router can omit them if needed
    id: Optional[int] = None
    company_id: Optional[int] = None
    has_logo: bool = False

    class Config:
        from_attributes = True


class CompanySettingsUpdate(CompanySettingsBase):
    pass


class UserSettingsBase(BaseModel):
    timezone: Optional[str] = None
    theme: Optional[str] = None


class UserSettingsOut(UserSettingsBase):
    id: int

    class Config:
        from_attributes = True


class UserSettingsUpdate(UserSettingsBase):
    pass
