from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr

class ModuleBase(BaseModel):
    code: str
    name: str

class ModuleOut(ModuleBase):
    id: int

    class Config:
        orm_mode = True

class CompanyBase(BaseModel):
    name: str

class CompanyOut(CompanyBase):
    id: int
    is_active: bool
    modules: List[ModuleOut] = []

    class Config:
        orm_mode = True

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str
    company_id: int

class UserOut(UserBase):
    id: int
    company_id: int
    role: str

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
    position: str
    salary: float

class EmployeeCreate(EmployeeBase):
    pass

class EmployeeOut(EmployeeBase):
    id: int
    company_id: int
    created_at: datetime

    class Config:
        orm_mode = True

class SalaryBase(BaseModel):
    employee_id: int
    amount: float
    period_start: date
    period_end: date

class SalaryCreate(SalaryBase):
    pass

class SalaryOut(SalaryBase):
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

class LeaveOut(LeaveBase):
    id: int
    company_id: int

    class Config:
        orm_mode = True