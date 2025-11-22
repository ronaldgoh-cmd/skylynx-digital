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