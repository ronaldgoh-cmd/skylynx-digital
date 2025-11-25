Below is a more complete “v2” guide with:

* Corrected sequence (local → cloud project → DB → deployment → desktop).
* A clearer split between:

  * Local development with SQLite.
  * Production on Google Cloud SQL (PostgreSQL).
* A proper VM section (optional) and a Cloud Run section (recommended).
* Extra detail on where to click, what to type, and how pieces fit together.

You can treat this as the new master guide for Skylynx Digital.

---

# Skylynx Digital – Complete Beginner Guide (v2)

Target: Windows user, PyCharm, Google Cloud, existing PySide6 desktop ERP.

---

## 0. Architecture and Sequence Overview

### 0.1 What you are building

1. **Backend**

   * FastAPI app (`backend/app/...`).
   * Multi-tenant data model (companies, users, modules, employees, salary, leave).
   * Central database: **Cloud SQL (PostgreSQL)** in Google Cloud.

2. **Desktop Client**

   * Your existing PySide6 ERP.
   * Runs on users’ Windows PCs as an `.exe` built by PyInstaller.
   * Talks to the backend via HTTPS (`API_BASE` URL).

3. **Cloud Infrastructure (Google Cloud)**

   * **Project**: e.g., `skylynx-digital`.
   * **Cloud SQL (PostgreSQL)** instance holding data.
   * **Backend deployment** (choose one):

     * **Option A (Recommended): Cloud Run** – serverless Docker container.
     * **Option B (Optional): Compute Engine VM** – a virtual machine where you run Docker manually.

### 0.2 Correct high-level sequence

1. Local machine setup (Python, PyCharm, Docker, gcloud).
2. Local project setup:

   * Create venv.
   * Install libraries.
   * Build backend folder structure.
   * Use **SQLite** locally to keep it simple.
3. Run backend locally and confirm API works (`/docs`).
4. Confirm desktop app can talk to local backend (`http://127.0.0.1:8000`).
5. Set up Google Cloud project + billing + required APIs.
6. Create Cloud SQL (PostgreSQL) instance and database.
7. Build Docker image for backend.
8. Deploy backend:

   * Option A: Cloud Run (recommended).
   * Option B: VM with Docker (optional).
9. Point desktop client to cloud URL.
10. Build installer with PyInstaller and distribute.

You **must** be able to do steps 2–4 reliably before touching Google Cloud.

---

# PART 1 – Local Machine Setup

### 1.1 Install core tools (do this once)

1. **Python 3.11**

   * Browser → [https://www.python.org/downloads/](https://www.python.org/downloads/)
   * Click **Download Python 3.11.x**.
   * Run installer:

     * Tick **Add Python to PATH**.
     * Click **Install Now**.

2. **Git**

   * Browser → [https://git-scm.com/download/win](https://git-scm.com/download/win)
   * Install with defaults (for future use with GitHub).

3. **Docker Desktop**

   * Browser → [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/)
   * Download for Windows.
   * Install and log in if asked.
   * Start Docker Desktop and ensure it’s running (whale icon in system tray).

4. **Google Cloud SDK (gcloud)**

   * Browser → [https://cloud.google.com/sdk/docs/install](https://cloud.google.com/sdk/docs/install)
   * Download Windows installer.
   * Install with defaults.
   * After install, open a new **Command Prompt** or **PowerShell** and run:

     ```bash
     gcloud --version
     ```

     to check it works.

5. **PyCharm**

   * Browser → [https://www.jetbrains.com/pycharm/download/](https://www.jetbrains.com/pycharm/download/)
   * Install **Community Edition** (free).
   * Run it once to finish setup.

### 1.2 Open your project in PyCharm

1. Start **PyCharm**.
2. On the welcome screen, click **Open**.
3. Navigate to your folder, for example:

   * `C:\Users\rev-e\Desktop\skylynx-digital`
4. Select the folder and click **OK**.
5. Wait for indexing to finish (bottom status bar).

---

# PART 2 – Virtual Environment and Local Backend

We keep **local backend** using **SQLite** for simplicity. Production will use PostgreSQL.

### 2.1 Create and activate virtual environment (.venv)

1. In PyCharm, bottom panel → **Terminal**.
2. Ensure the working directory is your project root, e.g.:

   ```
   PS C:\Users\rev-e\Desktop\skylynx-digital>
   ```
3. Create venv:

   ```bash
   python -m venv .venv
   ```
4. Activate venv (PowerShell in PyCharm):

   ```bash
   .venv\Scripts\activate
   ```

   After this, your prompt should start with `(.venv)`.

> If you see a “running scripts is disabled” error, one-time fix (run in a normal PowerShell **as Administrator**):
>
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
> ```
>
> Then close and reopen PyCharm and activate `.venv` again.

### 2.2 Upgrade pip and install dependencies (local dev)

With `(.venv)` active in the PyCharm Terminal:

```bash
python -m pip install --upgrade pip
python -m pip install fastapi uvicorn[standard] sqlalchemy alembic psycopg2-binary python-dotenv pydantic[email] passlib[bcrypt] python-jose[cryptography] requests PySide6 pyinstaller
```

You will use:

* FastAPI, Uvicorn → backend.
* SQLAlchemy, Alembic → ORM + migrations.
* psycopg2-binary → PostgreSQL driver (for later).
* python-dotenv → load `.env`.
* pydantic → schemas.
* passlib, python-jose → auth.
* requests → desktop calls backend.
* PySide6 → GUI.
* pyinstaller → later for `.exe`.

---

# PART 3 – Backend Folder Structure and Code

This part lives under `backend/app` in your project.

### 3.1 Create backend folder structure

Under your project root, create the following folders and files:

```text
backend/
  app/
    __init__.py
    main.py
    config.py
    database.py
    models.py
    schemas.py
    security.py
    dependencies.py
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
```

In PyCharm:

* Right-click project root → **New → Directory** → `backend`.
* Right-click `backend` → New → Directory → `app`.
* Right-click `app` → New → Python Package (or Directory+`__init__.py`) for `crud` and `routers`.

### 3.2 `.env` for local development (SQLite)

Create a file `.env` at the project root (same level as `backend`):

```ini
# File: .env (LOCAL DEV)
DATABASE_URL=sqlite:///./skylynx_local.db

JWT_SECRET=change_this_to_a_random_long_string
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
```

* `skylynx_local.db` will be created in the project root folder.
* For dev, `JWT_SECRET` can be any long random text. For production you will use a secret in Cloud.

### 3.3 `config.py` – simple environment loader

```python
# File: backend/app/config.py
import os
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
JWT_SECRET = os.getenv("JWT_SECRET", "change-me")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))
```

### 3.4 `database.py` – SQLAlchemy engine & session

```python
# File: backend/app/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import DATABASE_URL

if DATABASE_URL is None:
    raise RuntimeError("DATABASE_URL is not set. Check your .env file.")

# SQLite needs special connect_args
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency: yield a DB session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 3.5 `models.py` – multi-tenant tables

```python
# File: backend/app/models.py
from sqlalchemy import (
    Column, Integer, String, Boolean, ForeignKey, Date, Numeric, UniqueConstraint
)
from sqlalchemy.orm import relationship
from .database import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)

    modules = relationship("CompanyModule", back_populates="company", cascade="all, delete-orphan")
    users = relationship("User", back_populates="company")


class Module(Base):
    __tablename__ = "modules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)

    company_links = relationship("CompanyModule", back_populates="module", cascade="all, delete-orphan")


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

### 3.6 `schemas.py` – Pydantic models (I/O)

```python
# File: backend/app/schemas.py
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
```

### 3.7 `security.py` – password hashing + JWT

```python
# File: backend/app/security.py
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt
from passlib.context import CryptContext
from .config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_MINUTES

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=JWT_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
```

### 3.8 CRUD modules

`crud/auth.py`:

```python
# File: backend/app/crud/auth.py
from sqlalchemy.orm import Session
from .. import models, security


def authenticate_user(db: Session, email: str, password: str):
    user = db.query(models.User).filter(
        models.User.email == email,
        models.User.is_active.is_(True),
    ).first()
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
        .filter(
            models.CompanyModule.company_id == company_id,
            models.CompanyModule.is_enabled.is_(True),
            models.Module.is_active.is_(True),
        )
    )
    return [row.name for row in q.all()]
```

`crud/employees.py`:

```python
# File: backend/app/crud/employees.py
from sqlalchemy.orm import Session
from .. import models, schemas


def list_employees(db: Session, company_id: int):
    return (
        db.query(models.Employee)
        .filter(models.Employee.company_id == company_id)
        .all()
    )


def create_employee(db: Session, company_id: int, payload: schemas.EmployeeCreate):
    emp = models.Employee(company_id=company_id, **payload.dict())
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return emp
```

`crud/salary.py`:

```python
# File: backend/app/crud/salary.py
from sqlalchemy.orm import Session
from .. import models, schemas


def list_salaries(db: Session, company_id: int):
    return (
        db.query(models.Salary)
        .filter(models.Salary.company_id == company_id)
        .all()
    )


def create_salary(db: Session, company_id: int, payload: schemas.SalaryCreate):
    record = models.Salary(company_id=company_id, **payload.dict())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
```

`crud/leave.py`:

```python
# File: backend/app/crud/leave.py
from sqlalchemy.orm import Session
from .. import models, schemas


def list_leaves(db: Session, company_id: int):
    return (
        db.query(models.Leave)
        .filter(models.Leave.company_id == company_id)
        .all()
    )


def create_leave(db: Session, company_id: int, payload: schemas.LeaveCreate):
    record = models.Leave(company_id=company_id, **payload.dict())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
```

### 3.9 `dependencies.py` – current user from JWT

```python
# File: backend/app/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from .database import get_db
from .config import JWT_SECRET, JWT_ALGORITHM
from . import models

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        company_id = payload.get("company_id")
        if user_id is None or company_id is None:
            raise credentials_exception
        try:
            user_id_int = int(user_id)
        except (TypeError, ValueError):
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = (
        db.query(models.User)
        .filter(
            models.User.id == user_id_int,
            models.User.company_id == company_id,
            models.User.is_active.is_(True),
        )
        .first()
    )
    if user is None:
        raise credentials_exception
    return user
```

### 3.10 Routers

`routers/auth.py`:

```python
# File: backend/app/routers/auth.py
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .. import schemas, models, security
from ..database import get_db
from ..crud import auth as auth_crud
from ..config import JWT_EXPIRE_MINUTES
from ..dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = auth_crud.authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect username or password")
    modules = auth_crud.get_company_modules(db, user.company_id)
    access_token = security.create_access_token(
        data={"sub": str(user.id), "company_id": user.company_id, "modules": modules},
        expires_delta=timedelta(minutes=JWT_EXPIRE_MINUTES),
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

`routers/employees.py`:

```python
# File: backend/app/routers/employees.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import schemas
from ..database import get_db
from ..crud import employees as employees_crud
from ..dependencies import get_current_user

router = APIRouter(prefix="/employees", tags=["employees"])


@router.get("/", response_model=list[schemas.Employee])
def list_employees(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return employees_crud.list_employees(db, company_id=current_user.company_id)


@router.post("/", response_model=schemas.Employee)
def create_employee(payload: schemas.EmployeeCreate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return employees_crud.create_employee(db, company_id=current_user.company_id, payload=payload)
```

`routers/salary.py`:

```python
# File: backend/app/routers/salary.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import schemas
from ..database import get_db
from ..crud import salary as salary_crud
from ..dependencies import get_current_user

router = APIRouter(prefix="/salary", tags=["salary"])


@router.get("/", response_model=list[schemas.Salary])
def list_salary(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return salary_crud.list_salaries(db, company_id=current_user.company_id)


@router.post("/", response_model=schemas.Salary)
def create_salary(payload: schemas.SalaryCreate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return salary_crud.create_salary(db, company_id=current_user.company_id, payload=payload)
```

`routers/leave.py`:

```python
# File: backend/app/routers/leave.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import schemas
from ..database import get_db
from ..crud import leave as leave_crud
from ..dependencies import get_current_user

router = APIRouter(prefix="/leave", tags=["leave"])


@router.get("/", response_model=list[schemas.Leave])
def list_leave(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return leave_crud.list_leaves(db, company_id=current_user.company_id)


@router.post("/", response_model=schemas.Leave)
def create_leave(payload: schemas.LeaveCreate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return leave_crud.create_leave(db, company_id=current_user.company_id, payload=payload)
```

### 3.11 `main.py` – app entrypoint + automatic initial data

Add automatic seeding of one demo company + modules + admin user when DB is empty.

```python
# File: backend/app/main.py
from fastapi import FastAPI

from .database import Base, engine, SessionLocal
from . import models
from .routers import auth, employees, salary, leave
from .security import hash_password


def init_db():
    # Create tables
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Only seed if there are zero companies
        if db.query(models.Company).count() == 0:
            company = models.Company(name="Skylynx Demo", is_active=True)
            db.add(company)
            db.commit()
            db.refresh(company)

            module_names = ["employees", "salary", "leave"]
            modules = []
            for name in module_names:
                m = models.Module(name=name, description=f"{name.title()} module")
                db.add(m)
                modules.append(m)
            db.commit()
            for m in modules:
                db.refresh(m)

            for m in modules:
                link = models.CompanyModule(company_id=company.id, module_id=m.id, is_enabled=True)
                db.add(link)
            db.commit()

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


init_db()

app = FastAPI(title="Skylynx Digital ERP API")

app.include_router(auth.router)
app.include_router(employees.router)
app.include_router(salary.router)
app.include_router(leave.router)


@app.get("/")
def root():
    return {"message": "Skylynx Digital API is running"}
```

* Default login after first run:

  * Email: `admin@skylynx.local`
  * Password: `ChangeMe123!`
    Change this later in production.

---

# PART 4 – Run Backend Locally and Test

### 4.1 Run backend on localhost

1. In PyCharm Terminal, ensure:

   * You are in project root.
   * `(.venv)` is active.

2. Run:

   ```bash
   uvicorn backend.app.main:app --reload
   ```

3. Output should show:

   * `Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)`

### 4.2 Test API via browser (Swagger)

1. Open browser → go to:

   * [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
   * You should see `{"message": "Skylynx Digital API is running"}`.

2. Go to:

   * [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
   * Swagger UI should load.

3. Test login:

   * Click `/auth/token` → **POST** → **Try it out**.
   * Under `username` enter: `admin@skylynx.local`
   * `password`: `ChangeMe123!`
   * Click **Execute**.
   * You should get a `200` response with `access_token`, `company_id`, and `modules`.

4. Copy the `access_token`.
   At top of Swagger screen:

   * Click **Authorize**.
   * In `value` field type: `Bearer <paste-token-here>` (include the `Bearer ` prefix).
   * Click **Authorize** → **Close**.

5. Test employees:

   * `/employees/` → GET → **Try it out** → **Execute**.
   * Should return `[]` initially.

---

# PART 5 – Hook Desktop App to Local Backend (Development)

From now on, the desktop app **must not** talk to any local SQLite db directly. It should call HTTP APIs.

### 5.1 Create a simple config for API URL

Example:

```python
# File: skylynx_digital/config.py
API_BASE = "http://127.0.0.1:8000/"
```

Later, for production, you will replace this with the Cloud Run or VM URL.

### 5.2 Example: employees screen using polling

Example structure:

```python
# File: skylynx_digital/ui/employees.py
from PySide6 import QtWidgets, QtCore
import requests

from skylynx_digital.config import API_BASE


class EmployeeWindow(QtWidgets.QWidget):
    def __init__(self, token: str, parent=None):
        super().__init__(parent)
        self.token = token

        self.table = QtWidgets.QTableWidget()
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.table)

        # Poll every 7 seconds
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.refresh_employees)
        self.timer.start(7000)

        # First load
        self.refresh_employees()

    def refresh_employees(self):
        headers = {"Authorization": f"Bearer {self.token}"}
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

Your login dialog should:

1. Collect email + password.
2. POST to `/auth/token`.
3. Store `access_token`, `company_id`, `modules`.
4. Show/hide modules based on `modules`.
5. Pass `access_token` into windows like `EmployeeWindow`.

Once this is working against `http://127.0.0.1:8000/`, then you can move everything to the cloud.

---

# PART 6 – Google Cloud Project, APIs, and Cloud SQL

### 6.1 Create Google Cloud project and attach billing

1. Go to [https://console.cloud.google.com/](https://console.cloud.google.com/) (Chrome recommended).
2. Top bar → **Project selector** → **New Project**.
3. **Project name**: `skylynx-digital` (or similar).
4. Click **Create**.
5. After creation, top bar → select this new project.
6. Left menu (☰) → **Billing**.
   If prompted, link a billing account → choose your account → **Set account**.

### 6.2 Enable required APIs

1. Left menu (☰) → **APIs & Services → Library**.
2. Enable these (search each exact name):

   * **Cloud Run Admin API**
   * **Cloud SQL Admin API**
   * **Artifact Registry API**
   * **Cloud Build API**
   * **Compute Engine API** (needed for VM option)
   * **Secret Manager API** (recommended, later)
3. For each:

   * Click result → **Enable**.

### 6.3 Authenticate gcloud and set defaults (from your PC)

1. Open new terminal **outside** PyCharm (Command Prompt or PowerShell).

2. Run:

   ```bash
   gcloud init
   ```

   * Choose **Log in** and pick same Google account.
   * Select the `skylynx-digital` project when prompted.

3. Set default region/zone (example: `asia-southeast1` and `asia-southeast1-a`; adjust as you wish):

   ```bash
   gcloud config set compute/region asia-southeast1
   gcloud config set compute/zone asia-southeast1-a
   ```

### 6.4 Create Cloud SQL PostgreSQL instance

1. In console: left menu (☰) → **SQL**.

2. Click **Create instance**.

3. Choose **PostgreSQL**.

4. Configuration:

   * **Instance ID**: `skylynx-postgres`
   * **Password**: choose a strong password and save it as `DB_PASSWORD`.
   * Machine type: smallest default is fine for testing.
   * Networking: public IP is fine for dev; you don’t need to configure private IP yet.

5. Click **Create** and wait until status is **RUNNING**.

6. Create DB user:

   * Inside instance → **Users** tab → **Add user account**.
   * Username: `skylynx_app`
   * Password: same as `DB_PASSWORD` or another strong one (note it).

7. Create database:

   * Instance → **Databases** tab → **Create database**.
   * Name: `skylynx`.

8. Note down:

   * Project ID: `skylynx-digital` (from top bar).
   * Region: e.g. `asia-southeast1`.
   * Instance connection name: look in Overview; format: `skylynx-digital:asia-southeast1:skylynx-postgres`.

For Cloud Run deployment you will use a “socket-style” `DATABASE_URL`.

---

# PART 7 – Dockerize the Backend

### 7.1 Backend-only `requirements-backend.txt`

Create file in project root:

```text
# File: requirements-backend.txt
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
```

(Desktop-specific things like PySide6 and pyinstaller are not needed inside the container.)

### 7.2 Dockerfile

Create `Dockerfile` at project root:

```dockerfile
# File: Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
 && rm -rf /var/lib/apt/lists/*

COPY requirements-backend.txt ./requirements-backend.txt
RUN pip install --no-cache-dir -r requirements-backend.txt

# Copy backend code
COPY backend ./backend

ENV PYTHONUNBUFFERED=1

# FastAPI app
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### 7.3 Test Docker image locally (optional but recommended)

1. Make sure Docker Desktop is running.

2. From **project root** (not inside backend):

   ```bash
   docker build -t skylynx-backend:local .
   ```

3. Run the container with local SQLite:

   In PowerShell, keep the command **on one line** (PowerShell does not use `\` like bash):

   ```powershell
   docker run -p 8080:8080 `
     -e DATABASE_URL="sqlite:///./skylynx_local.db" `
     -e JWT_SECRET="change_this_to_a_random_long_string" `
     skylynx-backend:local
   ```

   Or in one single line (no backticks):

   ```powershell
   docker run -p 8080:8080 -e DATABASE_URL="sqlite:///./skylynx_local.db" -e JWT_SECRET="change_this_to_a_random_long_string" skylynx-backend:local
   ```

4. Test in browser:

   * [http://127.0.0.1:8080/](http://127.0.0.1:8080/) → should respond.
   * [http://127.0.0.1:8080/docs](http://127.0.0.1:8080/docs) → Swagger.

If this works, your container is OK.

---

# PART 8 – Option A (Recommended): Deploy to Cloud Run

### 8.1 Create Artifact Registry repository

1. Console left menu (☰) → **Artifact Registry → Repositories**.
2. Click **Create repository**.
3. Settings:

   * Name: `skylynx-backend-repo`
   * Format: `Docker`
   * Mode: Standard.
   * Region: pick same as Cloud SQL (e.g. `asia-southeast1`).
4. Click **Create**.

Repository path will be like:
`asia-southeast1-docker.pkg.dev/skylynx-digital/skylynx-backend-repo`

### 8.2 Build and push image using Cloud Build

From your project root on your PC:

```bash
gcloud builds submit \
  --tag asia-southeast1-docker.pkg.dev/skylynx-digital/skylynx-backend-repo/skylynx-backend:latest .
```

* Replace `asia-southeast1` with your chosen region if different.
* This uploads code and builds the image in Google Cloud.

### 8.3 Deploy to Cloud Run

Use the Cloud SQL **instance connection name** from earlier, e.g. `skylynx-digital:asia-southeast1:skylynx-postgres`.

You will set `DATABASE_URL` to use the Cloud SQL unix socket:

```bash
gcloud run deploy skylynx-backend \
  --image asia-southeast1-docker.pkg.dev/skylynx-digital/skylynx-backend-repo/skylynx-backend:latest \
  --platform managed \
  --region asia-southeast1 \
  --allow-unauthenticated \
  --add-cloudsql-instances skylynx-digital:asia-southeast1:skylynx-postgres \
  --set-env-vars DATABASE_URL="postgresql+psycopg2://skylynx_app:DB_PASSWORD@/skylynx?host=/cloudsql/skylynx-digital:asia-southeast1:skylynx-postgres" \
  --set-env-vars JWT_SECRET="change_this_to_a_strong_random_secret"
```

Important notes:

* Replace `DB_PASSWORD` with your actual DB user password.
* For production, avoid special characters like `@`, `:` or `/` in passwords unless you know how to URL-encode them.
* Keep region and instance names consistent.

After a successful deploy, the command will print a URL like:

`https://skylynx-backend-xxxxx-asia-southeast1.a.run.app`

This is your **API_BASE** for production.

### 8.4 Test Cloud Run endpoint

1. Open the Cloud Run URL in browser:

   * `https://skylynx-backend-xxxxx-asia-southeast1.a.run.app/`
   * Should show `{"message":"Skylynx Digital API is running"}`.

2. Try `/docs`:

   * `https://skylynx-backend-xxxxx-asia-southeast1.a.run.app/docs`
   * Use Swagger to test `/auth/token` with:

     * `admin@skylynx.local` / `ChangeMe123!`.

If login works, you are now fully running on Cloud Run + Cloud SQL.

---

# PART 9 – Option B: Run on a Compute Engine VM (Alternative)

Use this if you prefer managing your own Linux VM instead of Cloud Run. Backend will still use Cloud SQL.

### 9.1 Create the VM

1. Console left menu (☰) → **Compute Engine → VM instances**.
2. Click **Create instance**.
3. Basic settings:

   * Name: `skylynx-backend-vm`
   * Region: same as Cloud SQL if possible (e.g. `asia-southeast1`).
   * Machine type: small one (e.g. `e2-micro`) is fine for testing.
4. Boot disk:

   * Linux → Debian or Ubuntu LTS.
5. Firewall:

   * Tick **Allow HTTP traffic**.
6. Access scopes / IAM:

   * Under **Identity and API access**, choose:

     * **Service account**: default is ok for tests.
     * **Access scopes**: “Allow full access to all Cloud APIs” (for dev) or custom with at least Cloud SQL.
7. Click **Create**.

### 9.2 SSH into VM and set up Docker

1. In VM list, click **SSH** next to `skylynx-backend-vm` (opens web SSH).

2. Inside SSH terminal:

   ```bash
   sudo apt-get update
   sudo apt-get install -y docker.io git
   sudo systemctl enable docker
   sudo systemctl start docker
   ```

3. Add your user to docker group (optional convenience):

   ```bash
   sudo usermod -aG docker $USER
   ```

   Logout & log in again for this to take effect.

### 9.3 Pull container image and run

From VM SSH terminal:

```bash
gcloud auth configure-docker
docker pull asia-southeast1-docker.pkg.dev/skylynx-digital/skylynx-backend-repo/skylynx-backend:latest
```

Run container (using Cloud SQL socket is more complex on VM, so for dev you can use Cloud SQL public IP instead):

1. In Cloud SQL console → instance → **Connections**:

   * Enable **Public IP**.
   * Add authorized network `0.0.0.0/0` for dev (do this only in dev; restrict later).

2. Note the **Public IP address** of the instance, e.g. `34.xx.xx.xx`.

3. On the VM:

   ```bash
   docker run -d --name skylynx-backend \
     -p 80:8080 \
     -e DATABASE_URL="postgresql+psycopg2://skylynx_app:DB_PASSWORD@34.xx.xx.xx:5432/skylynx" \
     -e JWT_SECRET="change_this_to_a_strong_random_secret" \
     asia-southeast1-docker.pkg.dev/skylynx-digital/skylynx-backend-repo/skylynx-backend:latest
   ```

* VM’s external IP will now serve the backend on port 80, so you can hit:

  * `http://<VM_EXTERNAL_IP>/`
  * `http://<VM_EXTERNAL_IP>/docs`

Cloud Run **or** VM is enough; do not use both for production unless you know what you are doing.

---

# PART 10 – Alembic Migrations (Optional but Recommended)

Right now `init_db()` creates tables automatically. For serious use, you should move to Alembic.

Minimal workflow:

1. In PyCharm Terminal (project root, venv active):

   ```bash
   cd backend
   alembic init migrations
   ```

2. In `alembic.ini`, set:

   ```ini
   sqlalchemy.url = env
   ```

3. In `migrations/env.py`, modify to load `DATABASE_URL` from your config:

   ```python
   from logging.config import fileConfig
   from sqlalchemy import engine_from_config, pool
   from alembic import context

   from app.database import Base
   from app import models
   from app.config import DATABASE_URL
   ```

   And in `run_migrations_offline` / `run_migrations_online` functions, use `DATABASE_URL` instead of reading from `alembic.ini`.

4. Generate migration:

   ```bash
   alembic revision --autogenerate -m "init"
   ```

5. Apply migration locally:

   ```bash
   alembic upgrade head
   ```

6. To run migrations against Cloud SQL:

   * Temporarily set `.env` `DATABASE_URL` to Cloud SQL string (socket or public IP).
   * Run `alembic upgrade head` again (from your PC or VM).

---

# PART 11 – Desktop Installer with PyInstaller

### 11.1 Configure production API URL

Create/update:

```python
# File: skylynx_digital/config.py
API_BASE = "https://skylynx-backend-xxxxx-asia-southeast1.a.run.app/"
```

Use your actual Cloud Run URL (or VM URL if using VM).

### 11.2 Build executable

In PyCharm Terminal (project root, `.venv` active):

```bash
pyinstaller --name "SkylynxDigital" --onefile --noconsole skylynx_digital/__main__.py
```

* After completion, check `dist/SkylynxDigital.exe`.

Distribute:

* `SkylynxDigital.exe`
* Any config file if you prefer external `API_BASE` config instead of hardcoded.

---

# PART 12 – Per-Company Modules and Multi-Tenancy

1. Each company uses the **same backend** and **same database** but has its own `company_id`.
2. On login:

   * `/auth/token` returns `company_id` and `modules` list (e.g. `["employees", "salary"]`).
   * Desktop UI:

     * Only shows modules present in `modules`.
3. Data isolation:

   * Every query in CRUD filters by `company_id` from `current_user`.
   * Employees of Company A are never visible to Company B because each CRUD function uses that `company_id` filter.

To enable/disable modules per company:

* Update `company_modules` table (via SQL, admin tool, or later via admin API) to set `is_enabled` true/false.

---

# PART 13 – End-to-End Checklist (First-Time Run)

1. Local:

   * venv created and activated.
   * `.env` with SQLite `DATABASE_URL`.
   * Backend files created as above.
   * `uvicorn backend.app.main:app --reload` runs without error.
   * Swagger `/docs` works.
   * Login with `admin@skylynx.local` / `ChangeMe123!` works.
   * Desktop app can log in and call `/employees/`.

2. Cloud SQL + Cloud Run:

   * Project created and billing attached.
   * APIs enabled.
   * Cloud SQL instance + database + user created.
   * Docker image built and pushed to Artifact Registry.
   * Cloud Run service deployed with correct `DATABASE_URL` and `JWT_SECRET`.
   * Cloud Run URL returns message and `/docs` works.
   * Login to Cloud Run `/auth/token` with demo admin works.

3. Desktop production:

   * `API_BASE` updated to Cloud Run URL.
   * PyInstaller build succeeds.
   * Running `.exe` on another machine can log in and see live data.

---

If you want, you can next ask for a focused mini-guide on any one part (e.g., “only show me the exact steps to connect Cloud Run to Cloud SQL again” or “rewrite my login dialog.py to call /auth/token using this backend”).
