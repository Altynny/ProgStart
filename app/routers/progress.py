from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import crud, schemas
from ..deps import get_db
from ..auth import get_current_user

router = APIRouter(prefix="/progress", tags=["progress"])

@router.post("/", response_model=schemas.ProgressOut)
async def save_progress(progress: schemas.ProgressCreate,
                        db: Session = Depends(get_db),
                        current_user = Depends(get_current_user)):
    return crud.create_progress(db, current_user.id, progress)

@router.get("/", response_model=list[schemas.ProgressOut])
async def read_progress(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return crud.get_user_progress(db, current_user.id)