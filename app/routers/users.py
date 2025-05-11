from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import crud, schemas, auth
from ..deps import get_db

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/register", response_model=schemas.UserOut)
async def register(user: schemas.UserIn, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, user.username)
    if db_user:
        raise HTTPException(status_code=409, detail="Username already taken")
    crud.create_user(db, user)
    return {"message": f"Succesfully validated"}

# @router.post("/login")
# async def auth_user(user: schemas.UserIn, db: Session = Depends(get_db)):
#     db_user = crud.get_user_by_username(db, user.username)
#     if not db_user:
#         raise HTTPException(status_code=401, detail="Wrong login or password")
#     access_token = auth.create_access_token({"sub": str(db_user.id)})
#     response.set_cookie(key="users_access_token", value=access_token, httponly=True)
#     return {'access_token': access_token, 'refresh_token': None}



@router.get("/me", response_model=schemas.UserOut)
async def read_users_me(current_user = Depends(auth.get_current_active_user)):
    return current_user