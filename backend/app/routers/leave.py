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