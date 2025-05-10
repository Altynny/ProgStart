from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import crud, schemas, auth
from ..deps import get_db

router = APIRouter(prefix="/auth", tags=["users"])

@router.post("/register", response_model=schemas.UserOut)
async def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, user.username)
    if db_user:
        raise HTTPException(status_code=409, detail="Username already registered")
    return crud.create_user(db, user)

@router.get("/me", response_model=schemas.UserOut)
async def read_users_me(current_user = Depends(auth.get_current_user)):
    return current_user