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