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