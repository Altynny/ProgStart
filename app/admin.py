from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from . import models, auth
from .deps import get_db

async def is_admin(
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
) -> bool:
    """
    Проверяет, является ли текущий пользователь администратором
    """
    # Проверяем наличие роли "admin" у пользователя
    for role in current_user.roles:
        if role.name == "admin":
            return True
    
    return False

async def admin_required(
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Middleware для проверки прав администратора
    """
    is_admin_user = await is_admin(current_user, db)
    
    if not is_admin_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для выполнения данной операции"
        )
    
    return current_user

def create_initial_admin(db: Session, username: str, password: str) -> Optional[models.User]:
    """
    Создает первого администратора в системе, если он еще не существует
    """
    # Проверяем, есть ли уже пользователь с таким именем
    existing_user = db.query(models.User).filter(models.User.username == username).first()
    if existing_user:
        return None
    
    # Создаем роль администратора, если она еще не существует
    admin_role = db.query(models.Role).filter(models.Role.name == "admin").first()
    if not admin_role:
        admin_role = models.Role(name="admin", description="Администратор системы")
        db.add(admin_role)
        db.flush()
    
    # Создаем пользователя-администратора
    hashed_pwd = auth.get_password_hash(password)
    admin_user = models.User(username=username, hashed_password=hashed_pwd)
    admin_user.roles.append(admin_role)
    
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    
    return admin_user