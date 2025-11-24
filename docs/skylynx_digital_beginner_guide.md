# Skylynx Digital Beginner Guide: From Zero to Online Multi-Tenant ERP

This guide is written for absolute beginners. Every step tells you exactly what to click and what to type. Replace any placeholder like `<YOUR_DB_PASSWORD_HERE>` with your real secret values (keep them private!).

---
## Quick Goals (what we are trying to achieve)
- Put your existing Python/PySide desktop ERP online with a central FastAPI backend and PostgreSQL database on Google Cloud.
- Support multiple companies (multi-tenant) with module on/off per company.
- Keep one codebase so fixing a module once updates it for every company that uses it.
- Package the desktop app as a Windows installer that talks to the online API.

---
## High-Level Roadmap (10–15 steps)
1. Install Python (3.11 recommended) and PyCharm; open the project.
2. Create and activate a virtual environment in the project folder using PyCharm Terminal.
3. Install dependencies (FastAPI, SQLAlchemy, PySide6, requests, etc.).
4. Run the existing desktop app locally to confirm PyCharm and venv are working.
5. Design the multi-tenant database (companies, users, modules, employees, salary, leave, company-module mapping).
6. Build the FastAPI backend with clean file structure (`backend/app/...`) and create API endpoints for auth, employees, salary, leave.
7. Refactor the desktop client to call the backend API instead of any local database: login → company selection → show modules → data CRUD via HTTP.
8. Add simple near-real-time updates using polling (e.g., every 5–10 seconds) in the desktop app UI.
9. Containerize the backend with Docker and prepare `requirements.txt` for deployment.
10. Create Google Cloud project, enable billing and required APIs, and set up Cloud SQL (PostgreSQL).
11. Deploy the Dockerized backend to Cloud Run connected to Cloud SQL; set environment variables for secrets and database URL.
12. Run database migrations (Alembic) on the Cloud SQL database.
13. Package the desktop client with PyInstaller into a Windows installer and configure it to point to the Cloud Run URL.
14. Roll out module updates centrally (backend + client) so all companies benefit automatically.
15. Maintain a repeatable workflow: develop locally → commit → deploy backend → rebuild installer when needed.

---
# PART A: Local Setup on Your Computer
Follow these steps in order. Use PyCharm’s built-in Terminal (bottom of the IDE) unless stated otherwise.

### A1. Install Python 3.11 (if not already installed)
1. Open your web browser.
2. Go to https://www.python.org/downloads/
3. Click **Download Python 3.11.x** (latest 3.11 release).
4. Run the installer:
   - Check **Add Python to PATH**.
   - Click **Install Now** and finish.

### A2. Install PyCharm
1. Go to https://www.jetbrains.com/pycharm/download/
2. Download **PyCharm Community** (free) or **Professional** if you have a license.
3. Run the installer and accept defaults.

### A3. Open the project in PyCharm
1. Launch PyCharm.
2. On the Welcome screen, click **Open**.
3. Browse to your project folder (e.g., `C:\Users\<YOU>\skylynx-digital`), select it, and click **OK**.

### A4. Create and activate a virtual environment (venv)
1. In PyCharm, open the **Terminal** (bottom panel). You should see the project path.
2. Type this command and press **Enter** (creates a venv named `.venv`):
   ```bash
   python -m venv .venv
   ```
3. Activate the venv:
   - On Windows (PyCharm Terminal):
     ```bash
     .venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source .venv/bin/activate
     ```
4. You should see `(.venv)` at the start of the terminal prompt. That means the venv is active.

### A5. Upgrade pip and install dependencies
1. With the venv active, run:
   ```bash
   python -m pip install --upgrade pip
   ```
2. Install core libraries for backend and desktop client:
   ```bash
   python -m pip install fastapi uvicorn[standard] sqlalchemy alembic psycopg2-binary python-dotenv pydantic[email] passlib[bcrypt] python-jose[cryptography] requests PySide6
   ```
   - **fastapi**: web API framework.
   - **uvicorn**: server to run FastAPI locally.
   - **sqlalchemy**, **alembic**: database ORM and migrations.
   - **psycopg2-binary**: PostgreSQL driver.
   - **python-dotenv**: load env variables from `.env`.
   - **pydantic[email]**: data validation.
   - **passlib[bcrypt]** and **python-jose[cryptography]**: for password hashing and JWT auth.
   - **requests**: for the desktop app to call the API.
   - **PySide6**: your Qt GUI toolkit.

### A6. Run the existing desktop app locally (sanity check)
1. In PyCharm, open the **Terminal** (ensure `(.venv)` is active).
2. If your app has an entry script (example `skylynx_digital/__main__.py`), run:
   ```bash
   python -m skylynx_digital
   ```
3. Confirm the UI launches. Close it after verifying.

---
# PART B: Backend Design and Refactor (FastAPI)
We will create a clean backend folder: `backend/app`. All code will live there. File paths below are relative to the project root.

### B1. Target folder structure
```
backend/
  app/
    main.py
    config.py
    database.py
    models.py
    schemas.py
    security.py
    crud/
      __init__.py
      auth.py
      employees.py
      salary.py
      leave.py
    routers/
      __init__.py
      auth.py
      employees.py
      salary.py
      leave.py
    dependencies.py
```

### B2. Environment file for local dev
Create a `.env` file in the project root (same level as `backend/`). **Do NOT commit real secrets.**
```
# File: .env (NEW)
DATABASE_URL=postgresql+psycopg2://<YOUR_DB_USER_HERE>:<YOUR_DB_PASSWORD_HERE>@localhost:5432/skylynx_local
JWT_SECRET=<YOUR_RANDOM_SECRET_KEY_HERE>
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
```

### B3. Config helper
Create the config loader.
```
# File: backend/app/config.py (NEW FILE)
from pydantic import BaseSettings, AnyUrl

class Settings(BaseSettings):
    database_url: AnyUrl
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings(
    _env_file=".env",
    _env_file_encoding="utf-8",
)
```

### B4. Database connection
```
# File: backend/app/database.py (NEW FILE)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency for FastAPI routes

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### B5. Models (multi-tenant and modules)
```
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
```

### B6. Pydantic schemas
```
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
```

### B7. Security utilities (password hashing + JWT)
```
# File: backend/app/security.py (NEW FILE)
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt
from passlib.context import CryptContext
from .config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.jwt_expire_minutes))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)
```

### B8. CRUD helpers
```
# File: backend/app/crud/auth.py (NEW FILE)
from sqlalchemy.orm import Session
from .. import models, security


def authenticate_user(db: Session, email: str, password: str):
    user = db.query(models.User).filter(models.User.email == email, models.User.is_active == True).first()
    if not user:
        return None
    if not security.verify_password(password, user.hashed_password):
        return None
    return user


def create_user(db: Session, email: str, password: str, company_id: int):
    hashed = security.hash_password(password)
    user = models.User(email=email, hashed_password=hashed, company_id=company_id)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_company_modules(db: Session, company_id: int):
    q = (
        db.query(models.Module.name)
        .join(models.CompanyModule, models.Module.id == models.CompanyModule.module_id)
        .filter(models.CompanyModule.company_id == company_id, models.CompanyModule.is_enabled == True, models.Module.is_active == True)
    )
    return [row.name for row in q.all()]
```

```
# File: backend/app/crud/employees.py (NEW FILE)
from sqlalchemy.orm import Session
from .. import models, schemas


def list_employees(db: Session, company_id: int):
    return db.query(models.Employee).filter(models.Employee.company_id == company_id).all()


def create_employee(db: Session, company_id: int, payload: schemas.EmployeeCreate):
    emp = models.Employee(company_id=company_id, **payload.dict())
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return emp
```

```
# File: backend/app/crud/salary.py (NEW FILE)
from sqlalchemy.orm import Session
from .. import models, schemas


def list_salaries(db: Session, company_id: int):
    return db.query(models.Salary).filter(models.Salary.company_id == company_id).all()


def create_salary(db: Session, company_id: int, payload: schemas.SalaryCreate):
    record = models.Salary(company_id=company_id, **payload.dict())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
```

```
# File: backend/app/crud/leave.py (NEW FILE)
from sqlalchemy.orm import Session
from .. import models, schemas


def list_leaves(db: Session, company_id: int):
    return db.query(models.Leave).filter(models.Leave.company_id == company_id).all()


def create_leave(db: Session, company_id: int, payload: schemas.LeaveCreate):
    record = models.Leave(company_id=company_id, **payload.dict())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
```

### B9. Dependencies (auth + db)
```
# File: backend/app/dependencies.py (NEW FILE)
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from .database import get_db
from .config import settings
from . import models

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id: int | None = payload.get("sub")
        company_id: int | None = payload.get("company_id")
        if user_id is None or company_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.id == user_id, models.User.company_id == company_id, models.User.is_active == True).first()
    if user is None:
        raise credentials_exception
    return user
```

### B10. Routers
```
# File: backend/app/routers/auth.py (NEW FILE)
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from .. import schemas, security, models
from ..dependencies import get_current_user
from ..database import get_db
from ..crud import auth as auth_crud
from ..config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/token", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = auth_crud.authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect username or password")
    modules = auth_crud.get_company_modules(db, user.company_id)
    access_token = security.create_access_token(
        data={"sub": str(user.id), "company_id": user.company_id, "modules": modules},
        expires_delta=timedelta(minutes=settings.jwt_expire_minutes),
    )
    return schemas.Token(access_token=access_token, company_id=user.company_id, modules=modules, token_type="bearer")

@router.post("/signup", response_model=schemas.User)
def signup(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = auth_crud.create_user(db, email=payload.email, password=payload.password, company_id=payload.company_id)
    return user

@router.get("/me", response_model=schemas.User)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user
```

```
# File: backend/app/routers/employees.py (NEW FILE)
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import schemas
from ..dependencies import get_current_user
from ..database import get_db
from ..crud import employees as employees_crud

router = APIRouter(prefix="/employees", tags=["employees"])

@router.get("/", response_model=list[schemas.Employee])
def list_employees(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return employees_crud.list_employees(db, company_id=current_user.company_id)

@router.post("/", response_model=schemas.Employee)
def create_employee(payload: schemas.EmployeeCreate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return employees_crud.create_employee(db, company_id=current_user.company_id, payload=payload)
```

```
# File: backend/app/routers/salary.py (NEW FILE)
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import schemas
from ..dependencies import get_current_user
from ..database import get_db
from ..crud import salary as salary_crud

router = APIRouter(prefix="/salary", tags=["salary"])

@router.get("/", response_model=list[schemas.Salary])
def list_salary(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return salary_crud.list_salaries(db, company_id=current_user.company_id)

@router.post("/", response_model=schemas.Salary)
def create_salary(payload: schemas.SalaryCreate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return salary_crud.create_salary(db, company_id=current_user.company_id, payload=payload)
```

```
# File: backend/app/routers/leave.py (NEW FILE)
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import schemas
from ..dependencies import get_current_user
from ..database import get_db
from ..crud import leave as leave_crud

router = APIRouter(prefix="/leave", tags=["leave"])

@router.get("/", response_model=list[schemas.Leave])
def list_leave(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return leave_crud.list_leaves(db, company_id=current_user.company_id)

@router.post("/", response_model=schemas.Leave)
def create_leave(payload: schemas.LeaveCreate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return leave_crud.create_leave(db, company_id=current_user.company_id, payload=payload)
```

### B11. Main app entrypoint
```
# File: backend/app/main.py (NEW FILE)
from fastapi import FastAPI
from .database import Base, engine
from .routers import auth, employees, salary, leave

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Skylynx Digital ERP API")

app.include_router(auth.router)
app.include_router(employees.router)
app.include_router(salary.router)
app.include_router(leave.router)

@app.get("/")
def root():
    return {"message": "Skylynx Digital API is running"}
```

### B12. Run backend locally
1. In PyCharm Terminal (venv active), start the server:
   ```bash
   uvicorn backend.app.main:app --reload
   ```
2. Open your browser and visit http://127.0.0.1:8000/docs to test the API.

### B13. Alembic migrations (optional but recommended)
1. Initialize Alembic inside `backend/`:
   ```bash
   cd backend
   alembic init migrations
   ```
2. Edit `alembic.ini`: set `sqlalchemy.url = env` and load from `.env`.
3. In `migrations/env.py`, import models and use `settings.database_url` to connect.
4. Generate migration:
   ```bash
   alembic revision --autogenerate -m "init"
   ```
5. Apply migration:
   ```bash
   alembic upgrade head
   ```

---
# PART C: Multi-Company and Module Control
- **companies table**: stores each company.
- **modules table**: master list of available modules (Employee Management, Salary Management, Leave Management, etc.).
- **company_modules table**: which company has which module enabled.
- **users table**: each user belongs to a company.

### Login flow
1. User enters email + password in the desktop app.
2. Desktop sends POST to `/auth/token` (username=email, password=password).
3. Backend returns JWT token + `company_id` + list of enabled module names.
4. Desktop stores the token in memory (and optionally in a config file) and uses it for subsequent API calls.

### Showing/hiding modules in the desktop client
- After login, the response includes `modules` (e.g., `["employees", "salary"]`).
- In your PySide UI code, check this list and only show menu items/buttons for modules present in `modules`.
- Example: if "salary" is missing, hide the Salary Management button.

### Company data isolation
- Every table (employees, salaries, leaves) has `company_id` column.
- All CRUD queries **must** filter by `company_id` from the logged-in user to keep data separated.

---
# PART D: Real-Time / Live Updates (Simple Polling)
For beginners, polling is easiest: the client asks the server for updates every few seconds.

### How to implement polling in PySide
1. In the relevant window (e.g., Employee list), create a QTimer that triggers every 5–10 seconds.
2. On each trigger, call the API endpoint and refresh the table.

Example snippet:
```
# File: skylynx_digital/ui/employees.py (REPLACE or ADAPT)
from PySide6 import QtWidgets, QtCore
import requests

API_BASE = "https://<YOUR_CLOUD_RUN_URL>/"  # set via config file
TOKEN = None  # set after login

class EmployeeWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.table = QtWidgets.QTableWidget()
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.table)
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.refresh_employees)
        self.timer.start(7000)  # every 7 seconds

    def set_token(self, token: str):
        global TOKEN
        TOKEN = token

    def refresh_employees(self):
        headers = {"Authorization": f"Bearer {TOKEN}"}
        resp = requests.get(API_BASE + "employees/", headers=headers, timeout=10)
        resp.raise_for_status()
        employees = resp.json()
        self.update_table(employees)

    def update_table(self, employees):
        self.table.setRowCount(len(employees))
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Role"])
        for row, emp in enumerate(employees):
            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(str(emp["id"])))
            self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(emp["name"]))
            self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(emp.get("role", "")))
```

---
# PART E: Deployment on Google Cloud (Cloud Run + Cloud SQL)
This path is intentionally slow and hand-holding: Dockerized FastAPI → Cloud Run (serverless) → Cloud SQL (PostgreSQL). Follow each step in order to avoid missing a toggle.

### E1. Before you start (5-minute prep)
1. Open a Google Chrome/Edge tab at https://console.cloud.google.com/ and sign in with the Google account that owns billing rights.
2. Open a second tab for these docs so you can switch back and forth while clicking things.
3. Keep a notepad for copy/pasting the **Project ID**, **Region**, and **Instance connection name** as you create them (these are needed later when deploying).

### E2. Create a Google Cloud project and attach billing
1. In the Cloud Console, click the **Project dropdown** in the top bar (next to the Google Cloud logo).
2. Click **New Project**.
3. Enter **Project name**: `skylynx-digital` (or your company name). Leave **Location** as the default organization if unsure.
4. Click **Create**. Wait for the small notification that the project was created.
5. Immediately click the **Project dropdown** again and select the new project to make sure it is active.
6. Attach billing: **Navigation menu (☰)** → **Billing** → if prompted, click **Link a billing account**, choose your billing account, then click **Set account**. This prevents API errors later.

### E3. Enable required APIs (prevents “permission denied” errors later)
1. Confirm you are still in the new project (Project name shows in the top bar).
2. Go to **Navigation menu (☰)** → **APIs & Services** → **Enabled APIs & services** → **+ ENABLE APIS AND SERVICES**.
3. Search and enable each of these one by one (click the result → **Enable**):
   - **Cloud Run Admin API**
   - **Cloud SQL Admin API**
   - **Secret Manager API** (recommended for storing passwords/keys)

### E4. Install and initialize the Google Cloud SDK on your PC
1. Download from https://cloud.google.com/sdk/docs/install.
2. Run the installer and accept defaults. When it finishes, open a **new terminal** (PyCharm Terminal is fine) so `gcloud` is on PATH.
3. Initialize and set defaults:
   ```bash
   gcloud init
   gcloud auth login           # opens a browser; pick the same account as above
   gcloud config set project <YOUR_PROJECT_ID>
   gcloud config set compute/region <YOUR_REGION>   # e.g., us-central1
   gcloud config set compute/zone <YOUR_ZONE>       # e.g., us-central1-a
   ```
   Replace placeholders with the Project ID shown in the console (not the display name) and a nearby region/zone.

### E5. Create Cloud SQL (PostgreSQL) instance and database
1. In the Cloud Console: **Navigation menu (☰)** → **SQL** → **Create instance**.
2. Choose **PostgreSQL**.
3. Fill the form:
   - **Instance ID**: `skylynx-postgres` (recommended; lowercase, numbers, hyphens only).
   - **Password**: create a strong password and save it as `<YOUR_DB_PASSWORD_HERE>`.
   - **Region/Zone**: keep defaults unless you have a specific need.
   - Leave machine size/storage at the smallest defaults for testing.
4. Click **Create** and wait until the status turns **RUNNING**.
5. Inside the instance page, go to **Users** → **Add user account**:
   - **User name**: `skylynx-app`
   - **Password**: reuse `<YOUR_DB_PASSWORD_HERE>` or create a new one and note it.
6. Still in the instance, go to **Databases** → **Create database**:
   - **Database name**: `skylynx` (recommended).
7. Copy the **Instance connection name** from the Overview tab (format: `project:region:instance`). You will paste this into the `.env` and Cloud Run command.

### E6. Store secrets safely (recommended even for tests)
- Keep placeholders in code (`<YOUR_DB_USER_HERE>`, `<YOUR_DB_PASSWORD_HERE>`, `<YOUR_CLOUD_SQL_CONNECTION_NAME>`).
- To avoid hard-coding secrets: **Navigation menu (☰)** → **Security** → **Secret Manager** → **Create Secret**.
  - Name secrets like `db-password` and `jwt-secret` and paste the values.
  - Later, map these secrets to environment variables in Cloud Run.

### E7. Dockerize the backend
Create Dockerfile at project root.
```
# File: Dockerfile (NEW FILE)
FROM python:3.11-slim

WORKDIR /app

# Install system deps for psycopg2
RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
COPY .env.example ./.env.example

ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

Create a deployment requirements list (include FastAPI + DB libs).
```
# File: requirements.txt (REPLACE CONTENT WITH)
fastapi
uvicorn[standard]
sqlalchemy
alembic
psycopg2-binary
python-dotenv
pydantic[email]
passlib[bcrypt]
python-jose[cryptography]
requests
PySide6
```

Add an `.env.example` for reference (no secrets):
```
# File: .env.example (NEW FILE)
DATABASE_URL=postgresql+psycopg2://<YOUR_DB_USER_HERE>:<YOUR_DB_PASSWORD_HERE>@/<YOUR_DB_NAME_HERE>?host=/cloudsql/<YOUR_CONNECTION_NAME_HERE>
JWT_SECRET=<YOUR_RANDOM_SECRET_KEY_HERE>
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
```

### E8. Build and test Docker locally
1. From project root (venv not required):
   ```bash
   docker build -t skylynx-backend:local .
   ```
2. Run locally (replace placeholders):
   ```bash
   docker run -p 8080:8080 \
     -e DATABASE_URL="postgresql+psycopg2://<USER>:<PASSWORD>@localhost:5432/skylynx_local" \
     -e JWT_SECRET="<YOUR_RANDOM_SECRET_KEY_HERE>" \
     skylynx-backend:local
   ```
3. Visit http://127.0.0.1:8080/docs to test.

### E9. Deploy to Cloud Run (with Cloud SQL)
1. Authenticate Docker with Google:
   ```bash
   gcloud auth configure-docker
   ```
2. Build and push image to Artifact Registry (replace `REGION`):
   ```bash
   gcloud builds submit --tag REGION-docker.pkg.dev/PROJECT_ID/skylynx-repo/skylynx-backend:latest .
   ```
3. Deploy to Cloud Run:
   ```bash
   gcloud run deploy skylynx-backend \
     --image REGION-docker.pkg.dev/PROJECT_ID/skylynx-repo/skylynx-backend:latest \
     --platform managed \
     --region REGION \
     --add-cloudsql-instances <YOUR_CONNECTION_NAME_HERE> \
     --set-env-vars DATABASE_URL="postgresql+psycopg2://<USER>:<PASSWORD>@/<DB_NAME>?host=/cloudsql/<YOUR_CONNECTION_NAME_HERE>" \
     --set-env-vars JWT_SECRET="<YOUR_RANDOM_SECRET_KEY_HERE>" \
     --allow-unauthenticated
   ```
4. After deployment, Cloud Run shows a public HTTPS URL (e.g., `https://skylynx-backend-xxxx.a.run.app`). Use this as `API_BASE` in the desktop app.

### E10. Connect Cloud Run to Cloud SQL securely
- The `--add-cloudsql-instances` flag attaches the Cloud SQL instance.
- Ensure the service account used by Cloud Run has `Cloud SQL Client` role.

### E11. Run migrations on Cloud SQL
1. Use Cloud Shell or your local machine (with Cloud SQL proxy or direct socket) and run:
   ```bash
   cd backend
   alembic upgrade head
   ```
   Make sure `DATABASE_URL` points to the Cloud SQL socket path as in `.env.example`.


# PART F: Desktop Installer with PyInstaller
### F1. Install PyInstaller (inside venv)
```bash
python -m pip install pyinstaller
```

### F2. Create a config file for the API URL
```
# File: skylynx_digital/config.py (NEW or UPDATE)
API_BASE = "https://skylynx-backend-xxxx.a.run.app/"  # replace with your Cloud Run URL
```

### F3. Build the executable
1. In PyCharm Terminal (venv active), run:
   ```bash
   pyinstaller --name "SkylynxDigital" --onefile --noconsole skylynx_digital/__main__.py
   ```
2. After it finishes, check `dist/SkylynxDigital.exe` (Windows) or `dist/SkylynxDigital` (macOS/Linux).
3. Distribute the `.exe` along with a small `config.ini` or `.env` (if needed) containing `API_BASE`.

### F4. How the installer knows the backend URL
- Store `API_BASE` in `skylynx_digital/config.py` or a separate `config.ini` next to the executable.
- On startup, your app imports this value to send requests to the backend.

---
# PART G: Updating Modules for All Companies
- **Backend-only changes** (e.g., fix Employee endpoints): deploy a new Docker image to Cloud Run. All companies see the change immediately because they share the backend.
- **Desktop UI changes** (e.g., new Salary screen): rebuild the PyInstaller executable and distribute to clients. The backend API stays the same, so companies using the module benefit once they run the updated installer.
- **Module toggles per company**: update rows in `company_modules` table (via admin UI or direct SQL). When users log in, the `/auth/token` response includes the updated module list, so the desktop app shows/hides modules instantly after next login (or after the next polling refresh if you cache modules locally).

---
## Everyday Workflow (simple checklist)
1. Develop locally (PyCharm, venv on) and run `uvicorn backend.app.main:app --reload`.
2. Test with http://127.0.0.1:8000/docs and the desktop app pointing to `http://127.0.0.1:8000/`.
3. Commit code to Git.
4. Build and push Docker image; deploy to Cloud Run.
5. Run Alembic migrations against Cloud SQL.
6. Rebuild PyInstaller executable if desktop UI changed.
7. Distribute the new installer; all companies automatically use enabled modules based on backend data.

---
## Safety Reminders
- Never commit real passwords, API keys, or connection strings. Use placeholders and environment variables.
- Keep your `.env` file out of version control. Use `.env.example` as a template.
- Grant the least privileges necessary to service accounts and database users.

You now have a step-by-step, beginner-friendly path to move Skylynx Digital from a local desktop app to an online, multi-tenant ERP with centralized backend and per-company module control.
