# Skylynx Digital: Beginner Guide to Move Desktop ERP Online (FastAPI + Google Cloud Run + Cloud SQL + PySide6)

**You are starting from zero. Follow the steps in order. Always replace placeholder values (shown like `<PLACEHOLDER>`) with your own secrets. Never commit real passwords or keys to Git.**

---

## What this guide does
- Move your existing Python/PySide desktop ERP to a cloud-backed, multi-tenant system for **Skylynx Digital**.
- Build one shared backend (FastAPI + PostgreSQL) that serves all companies.
- Keep your PySide6 desktop UI but make it call HTTP APIs instead of a local database.
- Package the desktop client as an installer and deploy the backend to Google Cloud (Docker → Cloud Run → Cloud SQL).

---

## Quick understanding of your goal (simple bullets)
- You want the ERP to run online with a central backend on Google Cloud.
- Multiple companies should use the same backend but only see the modules they are allowed to use.
- Desktop apps should talk to the backend via APIs (no direct DB access) and refresh automatically.
- You need a beginner-friendly, step-by-step setup from empty computer to deployed system.
- You want a repeatable way to ship updates to all companies.

---

## High-level roadmap (10–15 steps)
1. Install Python 3.11 and PyCharm.
2. Open the project in PyCharm and create a virtual environment.
3. Install all required packages (backend + client).
4. Sketch the database for multi-tenant + modules (PostgreSQL).
5. Build the FastAPI backend (auth, employees, salary, leave, company-module mapping).
6. Run the backend locally and test endpoints.
7. Refactor the PySide6 client to use HTTP APIs (login, company selection, module visibility, polling).
8. Add simple polling for near real-time updates.
9. Containerize the backend with Docker.
10. Create a Google Cloud project, billing, and enable APIs.
11. Create Cloud SQL (PostgreSQL) and set connection details.
12. Deploy the Docker image to Cloud Run and connect it to Cloud SQL.
13. Run database migrations in Cloud SQL.
14. Package the desktop client with PyInstaller (Windows .exe).
15. Roll out module updates centrally (backend) and repackage client when UI changes.

---

# PART A: Local setup on your computer

Follow every step carefully. Use the PyCharm **Terminal** (bottom of the window) unless stated otherwise.

### 1) Install Python 3.11
1. Go to https://www.python.org/downloads/.
2. Click **Download Python 3.11.x** for Windows.
3. Run the installer. On the first screen, **tick** “Add Python 3.11 to PATH”, then click **Install Now**.
4. After installation, open **Command Prompt** (press Windows key, type `cmd`, press Enter).
5. Type `python --version` and press Enter. You should see `Python 3.11.x`.

### 2) Install PyCharm Community (free)
1. Go to https://www.jetbrains.com/pycharm/download.
2. Download **PyCharm Community** for Windows.
3. Run the installer and accept defaults.
4. Open PyCharm once installed.

### 3) Open your project in PyCharm
1. In PyCharm, on the welcome screen, click **Open**.
2. Browse to your project folder (where this repository is located) and click **OK**.
3. Wait for indexing to finish.

### 4) Create and activate a virtual environment (venv)
1. In PyCharm, open **File** → **Settings** → **Project: skylynx-digital** → **Python Interpreter**.
2. Click the gear icon ⚙️ → **Add**.
3. Select **Virtualenv Environment**.
4. Location: keep the default inside the project (e.g., `<PROJECT_PATH>\.venv`).
5. Base interpreter: choose **Python 3.11**.
6. Click **OK**. PyCharm will create and activate the venv for the project.
7. In the PyCharm **Terminal**, confirm venv is active: you should see `(.venv)` at the start of the prompt.

### 5) Install dependencies
We’ll use FastAPI, SQLAlchemy, Alembic, Uvicorn, psycopg2-binary, PySide6, requests, and PyInstaller.

In the PyCharm **Terminal**, type (one command):
```bash
pip install fastapi[all] sqlalchemy alembic uvicorn psycopg2-binary python-dotenv pydantic requests PySide6 pyinstaller
```
- `pip install ...` downloads and installs packages into your venv.

### 6) Verify you can run a basic script (quick check)
1. In the terminal, run:
   ```bash
   python -c "print('Python OK')"
   ```
2. You should see `Python OK`. If not, ensure the venv is active.

---

# PART B: Backend design and refactor (FastAPI)
We will place backend code under `backend/app/`.

## 1) Database schema (PostgreSQL, multi-tenant, modules)
- Use a **single shared database** with a `company_id` column on every table that holds company-specific data.
- Tables:
  - `companies`: list of companies (id, name, is_active).
  - `modules`: list of modules (id, code, name).
  - `company_modules`: which modules each company can use (company_id, module_id, enabled).
  - `users`: user accounts linked to a company (id, company_id, email, password_hash, role).
  - `employees`: employee records (id, company_id, name, position, salary, etc.).
  - `salaries`: salary entries (id, company_id, employee_id, amount, period_start, period_end).
  - `leaves`: leave requests (id, company_id, employee_id, start_date, end_date, status).
- Index every `company_id` column for performance.
- This pattern keeps all tenants in one DB while cleanly filtering by `company_id` in every query.

## 2) Backend file structure
Create these files (relative to project root):
```
backend/
  app/
    __init__.py
    main.py
    config.py
    database.py
    models.py
    schemas.py
    auth.py
    deps.py
    crud/
      __init__.py
      employees.py
      salaries.py
      leaves.py
      users.py
      companies.py
      modules.py
    routers/
      __init__.py
      auth.py
      employees.py
      salaries.py
      leaves.py
      companies.py
```

### File: backend/app/config.py (NEW FILE)
**Purpose:** load environment variables for DB and secrets.
```python
import os
from dotenv import load_dotenv

load_dotenv()

# Always replace placeholders when deploying
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://<DB_USER>:<DB_PASSWORD>@localhost:5432/<DB_NAME>"
)
SECRET_KEY = os.getenv("SECRET_KEY", "<CHANGE_ME_TO_RANDOM_STRING>")
ACCESS_TOKEN_EXPIRE_MINUTES = 60
```

### File: backend/app/database.py (NEW FILE)
**Purpose:** create SQLAlchemy engine and session.
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import DATABASE_URL

engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()

# Dependency for FastAPI routes

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### File: backend/app/models.py (NEW FILE)
**Purpose:** define database tables.
```python
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Date, Numeric
from sqlalchemy.orm import relationship
from .database import Base

class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    modules = relationship("CompanyModule", back_populates="company")
    users = relationship("User", back_populates="company")

class Module(Base):
    __tablename__ = "modules"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, nullable=False)  # e.g., EMP, SAL, LEAVE
    name = Column(String, nullable=False)
    company_links = relationship("CompanyModule", back_populates="module")

class CompanyModule(Base):
    __tablename__ = "company_modules"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), index=True, nullable=False)
    module_id = Column(Integer, ForeignKey("modules.id"), index=True, nullable=False)
    enabled = Column(Boolean, default=True)

    company = relationship("Company", back_populates="modules")
    module = relationship("Module", back_populates="company_links")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="user")

    company = relationship("Company", back_populates="users")

class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), index=True, nullable=False)
    name = Column(String, nullable=False)
    position = Column(String, nullable=False)
    salary = Column(Numeric(12, 2), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Salary(Base):
    __tablename__ = "salaries"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), index=True, nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)

class Leave(Base):
    __tablename__ = "leaves"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), index=True, nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(String, default="pending")
```

### File: backend/app/schemas.py (NEW FILE)
**Purpose:** Pydantic schemas for request/response.
```python
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
```

### File: backend/app/auth.py (NEW FILE)
**Purpose:** handle password hashing and JWT tokens.
```python
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from .config import SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES

ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
```

### File: backend/app/deps.py (NEW FILE)
**Purpose:** reusable dependencies for FastAPI routes.
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from .database import get_db
from .auth import ALGORITHM
from .config import SECRET_KEY
from . import models

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        company_id: int = payload.get("company_id")
        if user_id is None or company_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.id == user_id, models.User.company_id == company_id).first()
    if user is None:
        raise credentials_exception
    return user
```

### CRUD files (NEW FILES)

**File: backend/app/crud/users.py**
```python
from sqlalchemy.orm import Session
from .. import models, auth
from ..schemas import UserCreate


def get_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(db: Session, user_in: UserCreate):
    hashed = auth.hash_password(user_in.password)
    db_user = models.User(
        company_id=user_in.company_id,
        email=user_in.email,
        password_hash=hashed,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
```

**File: backend/app/crud/companies.py**
```python
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
```

**File: backend/app/crud/modules.py**
```python
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
```

**File: backend/app/crud/employees.py**
```python
from sqlalchemy.orm import Session
from .. import models
from ..schemas import EmployeeCreate


def list_employees(db: Session, company_id: int):
    return db.query(models.Employee).filter(models.Employee.company_id == company_id).order_by(models.Employee.id.desc()).all()


def create_employee(db: Session, company_id: int, employee_in: EmployeeCreate):
    emp = models.Employee(
        company_id=company_id,
        name=employee_in.name,
        position=employee_in.position,
        salary=employee_in.salary,
    )
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return emp
```

**File: backend/app/crud/salaries.py**
```python
from sqlalchemy.orm import Session
from .. import models
from ..schemas import SalaryCreate


def list_salaries(db: Session, company_id: int):
    return db.query(models.Salary).filter(models.Salary.company_id == company_id).order_by(models.Salary.id.desc()).all()


def create_salary(db: Session, company_id: int, salary_in: SalaryCreate):
    sal = models.Salary(
        company_id=company_id,
        employee_id=salary_in.employee_id,
        amount=salary_in.amount,
        period_start=salary_in.period_start,
        period_end=salary_in.period_end,
    )
    db.add(sal)
    db.commit()
    db.refresh(sal)
    return sal
```

**File: backend/app/crud/leaves.py**
```python
from sqlalchemy.orm import Session
from .. import models
from ..schemas import LeaveCreate


def list_leaves(db: Session, company_id: int):
    return db.query(models.Leave).filter(models.Leave.company_id == company_id).order_by(models.Leave.id.desc()).all()


def create_leave(db: Session, company_id: int, leave_in: LeaveCreate):
    leave = models.Leave(
        company_id=company_id,
        employee_id=leave_in.employee_id,
        start_date=leave_in.start_date,
        end_date=leave_in.end_date,
        status=leave_in.status,
    )
    db.add(leave)
    db.commit()
    db.refresh(leave)
    return leave
```

### Routers (NEW FILES)

**File: backend/app/routers/auth.py**
```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from .. import models, schemas, auth
from ..database import get_db
from ..crud import users, companies

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = users.get_by_email(db, form_data.username)
    if not user or not auth.verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    modules = companies.get_company_modules(db, user.company_id)
    token = auth.create_access_token({"sub": str(user.id), "company_id": user.company_id, "modules": modules})
    return schemas.Token(access_token=token, company_id=user.company_id, modules=modules)
```

**File: backend/app/routers/employees.py**
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import schemas, models
from ..database import get_db
from ..deps import get_current_user
from ..crud import employees

router = APIRouter(prefix="/employees", tags=["employees"])


@router.get("/", response_model=list[schemas.EmployeeOut])
def list_all(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return employees.list_employees(db, company_id=current_user.company_id)


@router.post("/", response_model=schemas.EmployeeOut)
def create(employee_in: schemas.EmployeeCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return employees.create_employee(db, company_id=current_user.company_id, employee_in=employee_in)
```

**File: backend/app/routers/salaries.py**
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import schemas, models
from ..database import get_db
from ..deps import get_current_user
from ..crud import salaries

router = APIRouter(prefix="/salaries", tags=["salaries"])


@router.get("/", response_model=list[schemas.SalaryOut])
def list_all(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return salaries.list_salaries(db, company_id=current_user.company_id)


@router.post("/", response_model=schemas.SalaryOut)
def create(salary_in: schemas.SalaryCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return salaries.create_salary(db, company_id=current_user.company_id, salary_in=salary_in)
```

**File: backend/app/routers/leaves.py**
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import schemas, models
from ..database import get_db
from ..deps import get_current_user
from ..crud import leaves

router = APIRouter(prefix="/leaves", tags=["leaves"])


@router.get("/", response_model=list[schemas.LeaveOut])
def list_all(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return leaves.list_leaves(db, company_id=current_user.company_id)


@router.post("/", response_model=schemas.LeaveOut)
def create(leave_in: schemas.LeaveCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return leaves.create_leave(db, company_id=current_user.company_id, leave_in=leave_in)
```

**File: backend/app/routers/companies.py**
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import schemas, models
from ..database import get_db
from ..deps import get_current_user
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
```

### File: backend/app/main.py (NEW FILE)
**Purpose:** FastAPI app entry point.
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine, SessionLocal
from .crud.modules import seed_modules
from . import models
from .routers import auth, employees, salaries, leaves, companies

# Create tables
Base.metadata.create_all(bind=engine)

# Seed default modules
with SessionLocal() as db:
    seed_modules(db)

app = FastAPI(title="Skylynx Digital ERP API")

# Allow desktop clients to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # in production, restrict to your domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(employees.router)
app.include_router(salaries.router)
app.include_router(leaves.router)
app.include_router(companies.router)

@app.get("/")
def read_root():
    return {"status": "ok", "service": "Skylynx Digital ERP"}
```

## 3) Run the backend locally
1. In PyCharm **Terminal**, run:
   ```bash
   uvicorn backend.app.main:app --reload
   ```
2. Open your browser to http://127.0.0.1:8000/docs to see interactive API docs.
3. Stop the server with `Ctrl+C` in the terminal.

## 4) Database initialization locally
- For quick local tests, you can use SQLite by changing `DATABASE_URL` to `sqlite:///./local.db` in `backend/app/config.py`.
- For production, keep PostgreSQL and set environment variable `DATABASE_URL` accordingly.

---

# PART C: Multi-company and module control

1. **Companies table**: stores each company (e.g., “Company A”, “Company B”).
2. **Modules table + seed**: pre-load `EMP`, `SAL`, `LEAVE` codes.
3. **Company_modules table**: links companies to modules; toggle `enabled` per module.
4. **Login flow**:
   - User submits email/password to `/auth/login`.
   - Backend checks password, fetches `company_id` and that company’s modules.
   - Backend returns a JWT token plus `company_id` and list of module codes.
5. **Client behavior**:
   - Store token in memory (never hard-code secrets).
   - Show/hide UI buttons based on module codes (e.g., show Salary only if `"SAL"` is present).

---

# PART D: Real-time / live updates (simple polling)

**Approach:** every 5–10 seconds, the client calls the relevant list endpoint and refreshes the table.

Example for employees:
1. Store `API_BASE_URL` (e.g., `https://<YOUR_CLOUD_RUN_URL>`)
2. After login, start a QTimer in PySide6 that runs every 8 seconds.
3. In the timer callback, call `GET /employees/` with the `Authorization: Bearer <token>` header.
4. Update the table model with the latest data.
5. Do similar polling for salaries/leaves if those modules are enabled.

Pseudo-code snippet inside your PySide6 main window (replace your existing DB calls):
```python
# Inside your main window class
from PySide6.QtCore import QTimer
import requests

API_BASE_URL = "https://<YOUR_CLOUD_RUN_URL>"  # set via config file

def start_polling(self):
    self.timer = QTimer()
    self.timer.timeout.connect(self.refresh_employees)
    self.timer.start(8000)  # every 8 seconds


def refresh_employees(self):
    headers = {"Authorization": f"Bearer {self.auth_token}"}
    resp = requests.get(f"{API_BASE_URL}/employees/", headers=headers, timeout=10)
    data = resp.json()
    # TODO: update your table model with `data`
```

---

# PART E: Deployment on Google Cloud (single clear path)
We will use **Docker + Cloud Run + Cloud SQL (PostgreSQL)**.

### 1) Create Google Cloud project and enable billing
1. Go to https://console.cloud.google.com/ (sign in).
2. Top bar: click the project drop-down → **New Project**.
3. Name: `skylynx-digital` (or any name) → **Create**.
4. Switch to the new project (top bar).
5. Left menu (☰) → **Billing** → connect a billing account.

### 2) Enable required APIs
1. Left menu (☰) → **APIs & Services** → **Enable APIs and Services**.
2. Search and enable:
   - **Cloud Run API**
   - **Cloud SQL Admin API**
   - **Secret Manager API** (optional but recommended)

### 3) Create Cloud SQL for PostgreSQL
1. Left menu (☰) → **SQL** → click **Create Instance**.
2. Choose **PostgreSQL**.
3. Instance ID: `skylynx-postgres`.
4. Set password: choose a strong password (use `<YOUR_DB_PASSWORD_HERE>` placeholder in code). Write it down.
5. Choose region/zone near you.
6. Machine type: start with the smallest (e.g., `db-f1-micro`).
7. Click **Create** and wait.
8. After creation, click the instance → **Databases** tab → **Create database**.
   - Name: `skylynx_db` → **Create**.

### 4) Connection info to keep
- Instance connection name: find it on the instance overview (looks like `project:region:skylynx-postgres`).
- Database name: `skylynx_db`.
- User: `postgres` (or custom).
- Password: your chosen password.

### 5) Store secrets safely
- Use environment variables in Cloud Run:
  - `DATABASE_URL=postgresql+psycopg2://<DB_USER>:<YOUR_DB_PASSWORD_HERE>@/<DB_NAME>?host=/cloudsql/<INSTANCE_CONNECTION_NAME>`
  - `SECRET_KEY=<YOUR_RANDOM_SECRET>`
- Never hard-code real passwords in code or Git.

### 6) Dockerize the backend
Create two files in project root.

**File: requirements.txt (REPLACE CONTENTS WITH THIS)**
```
alembic
fastapi[all]
psycopg2-binary
python-dotenv
pydantic
PySide6
requests
SQLAlchemy
uvicorn
passlib[bcrypt]
python-jose
``` 

**File: Dockerfile (NEW FILE or replace existing)**
```dockerfile
# Use Python 3.11 slim image
FROM python:3.11-slim

# Set workdir
WORKDIR /app

# Install system deps for psycopg2
RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

# Copy dependency file and install
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend ./backend

# Expose port
EXPOSE 8080

# Command to run FastAPI with Uvicorn on Cloud Run expected port 8080
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### 7) Build and push Docker image
Use Cloud Shell or local terminal with gcloud installed.
1. In terminal:
   ```bash
   gcloud auth login
   gcloud config set project <YOUR_GCP_PROJECT_ID>
   gcloud auth configure-docker
   docker build -t gcr.io/<YOUR_GCP_PROJECT_ID>/skylynx-backend:latest .
   docker push gcr.io/<YOUR_GCP_PROJECT_ID>/skylynx-backend:latest
   ```

### 8) Deploy to Cloud Run
1. In console: Left menu (☰) → **Cloud Run** → **Create service**.
2. Service name: `skylynx-backend`.
3. Region: choose same as Cloud SQL.
4. Deployment platform: **Fully managed**.
5. Container image: `gcr.io/<YOUR_GCP_PROJECT_ID>/skylynx-backend:latest`.
6. Click **Container, variables & secrets, connections, security**:
   - **Environment variables**:
     - `DATABASE_URL` = `postgresql+psycopg2://<DB_USER>:<YOUR_DB_PASSWORD_HERE>@/<DB_NAME>?host=/cloudsql/<INSTANCE_CONNECTION_NAME>`
     - `SECRET_KEY` = `<YOUR_RANDOM_SECRET>`
   - **Connections** → **Cloud SQL connections** → **Add connection** → select your instance.
7. **Allow unauthenticated invocations** (for testing; lock down later).
8. Click **Create** and wait.
9. Copy the service URL (e.g., `https://skylynx-backend-abc123.run.app`). This is your `API_BASE_URL`.

### 9) Run database migrations (simple approach)
Because we used `Base.metadata.create_all`, the tables are created automatically on first run. For future changes, set up Alembic. For now:
1. Temporarily run Cloud Run with the `DATABASE_URL` pointing to Cloud SQL.
2. On first start, tables will be created.
3. Verify by connecting via **Cloud SQL → INSTANCE → Connect** and checking tables.

### 10) HTTPS
- Cloud Run gives HTTPS by default on its URL.
- Use this URL in your desktop client.

---

# PART F: Desktop client refactor and installer (PySide6)

## 1) How the client talks to the backend
- Replace direct DB calls with HTTP requests using `requests` library.
- Store `API_BASE_URL` and `auth_token` after login.

**Login example (inside your login form):**
```python
import requests
API_BASE_URL = "https://<YOUR_CLOUD_RUN_URL>"

def login(self, email: str, password: str):
    data = {"username": email, "password": password}
    resp = requests.post(f"{API_BASE_URL}/auth/login", data=data, timeout=10)
    if resp.status_code == 200:
        body = resp.json()
        self.auth_token = body["access_token"]
        self.company_id = body["company_id"]
        self.enabled_modules = body["modules"]  # ["EMP", "SAL", "LEAVE"]
        return True
    else:
        return False
```

**Showing modules based on company permissions:**
```python
# After login
if "SAL" in self.enabled_modules:
    self.salary_button.show()
else:
    self.salary_button.hide()

if "LEAVE" in self.enabled_modules:
    self.leave_button.show()
else:
    self.leave_button.hide()
```

**Fetching employees:**
```python
headers = {"Authorization": f"Bearer {self.auth_token}"}
resp = requests.get(f"{API_BASE_URL}/employees/", headers=headers, timeout=10)
employees = resp.json()
# Update your UI table with this list
```

## 2) Polling for live updates
- After login, call `start_polling()` (shown earlier) to refresh every 8 seconds.
- Repeat for salaries and leaves if their modules are enabled.

## 3) Packaging with PyInstaller (Windows .exe)
1. In PyCharm **Terminal** (venv active), run:
   ```bash
   pyinstaller --noconfirm --onefile --name SkylynxDigitalClient --add-data "path/to/your/ui_files;ui_files" main.py
   ```
   - Replace `main.py` with your client entry script.
   - Adjust `--add-data` paths for your .ui or asset files (Windows uses `;` separator).
2. After it finishes, find the executable in `dist/SkylynxDigitalClient.exe`.
3. Create a simple config file (e.g., `config.ini`) that stores `API_BASE_URL`, and read it in your code so the exe knows where to connect.

Example `config.ini`:
```
[server]
api_base_url = https://<YOUR_CLOUD_RUN_URL>
```

Reading it in Python:
```python
import configparser
config = configparser.ConfigParser()
config.read('config.ini')
API_BASE_URL = config['server']['api_base_url']
```

Include `config.ini` next to the `.exe` on each client machine.

---

# PART G: Updating modules for all companies

1. **Backend updates (one place):**
   - Fix a bug in the Employee module → change code in backend (e.g., `routers/employees.py`).
   - Build and push a new Docker image → redeploy to Cloud Run.
   - All companies instantly get the new API behavior because they share the backend.

2. **Client updates (when UI changes):**
   - If only backend logic changes (no UI change), clients might not need updates because API outputs stay the same.
   - If UI or client logic changes, rebuild the PyInstaller .exe and distribute it. The backend URL in `config.ini` stays the same, so clients connect to the new backend automatically.

3. **Module toggles per company:**
   - In the database, update `company_modules.enabled` for that company.
   - Next login or poll, the client reads `modules` from `/auth/login` response and shows/hides features instantly.

4. **Database migrations (future):**
   - Use Alembic to manage schema changes. Run migrations locally, build/push a new image, and Cloud Run will apply migrations on start (or use a one-time migration job). For now, `Base.metadata.create_all` handles initial tables.

---

## Quick testing locally (smoke test)
1. Run PostgreSQL locally or use SQLite for quick test (`DATABASE_URL=sqlite:///./local.db`).
2. Start backend: `uvicorn backend.app.main:app --reload`.
3. Create a company, module links, and user directly in DB (use a DB tool or psql). Example SQL:
   ```sql
   INSERT INTO companies (name, is_active) VALUES ('Company A', true);
   INSERT INTO modules (code, name) VALUES ('EMP', 'Employee Management') ON CONFLICT DO NOTHING;
   INSERT INTO company_modules (company_id, module_id, enabled) VALUES (1, 1, true);
   INSERT INTO users (company_id, email, password_hash, role) VALUES (1, 'admin@a.com', '$2b$12$...hash...', 'admin');
   ```
   - Use `auth.hash_password('yourpassword')` in a quick Python shell to generate a hash.
4. Call `/auth/login` via Swagger UI at http://127.0.0.1:8000/docs and test the endpoints.

---

## Reminders
- Always keep secrets out of Git. Use placeholders in code and set real values via environment variables.
- Use the new brand name **Skylynx Digital** everywhere.
- When unsure, redeploy the backend after code changes and rebuild the client installer for UI changes.

You now have a full path from zero to a cloud-hosted, multi-tenant FastAPI backend with a PySide6 desktop client for **Skylynx Digital**.
