# File: backend/app/schemas.py (NEW FILE)
from datetime import date
from typing import List, Optional
from pydantic import BaseModel, EmailStr

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

class EmployeeBase(BaseModel):
    name: str
    role: str | None = None
    hire_date: date | None = None

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