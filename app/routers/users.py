from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from .. import crud, schemas, auth
from ..deps import get_db

router = APIRouter(prefix="/users", tags=["users"])

class UserRegistrationResponse(schemas.BaseModel):
    message: str

@router.post("/register", response_model=UserRegistrationResponse)
async def register(user: schemas.UserIn, db: Session = Depends(get_db)):
    """
    Регистрация нового пользователя
    """
    db_user = crud.get_user_by_username(db, user.username)
    if db_user:
        raise HTTPException(status_code=409, detail="Имя пользователя уже занято")
    crud.create_user(db, user)
    return {"message": "Пользователь успешно зарегистрирован"}

@router.post("/logout")
async def logout(response: Response):
    """
    Выход из системы (удаление токена из куки)
    """
    # Очищаем куки с токеном
    response.delete_cookie(key="access_token")
    return {"message": "Вы успешно вышли из системы"}

@router.get("/me", response_model=schemas.UserOut)
async def read_users_me(current_user = Depends(auth.get_current_active_user)):
    """
    Получение информации о текущем пользователе
    """
    return current_user