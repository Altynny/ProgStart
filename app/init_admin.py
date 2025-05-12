import argparse
from sqlalchemy.orm import Session
from .database import SessionLocal
from .admin import create_initial_admin

def init_admin(username: str, password: str):
    """
    Скрипт для создания первого администратора в системе.
    Запускается командой:
    python -c "from app.init_admin import init_admin; init_admin('admin', 'password')"
    """
    db = SessionLocal()
    try:
        admin = create_initial_admin(db, username, password)
        if admin:
            print(f"Администратор '{username}' успешно создан!")
        else:
            print(f"Пользователь '{username}' уже существует.")
    except Exception as e:
        print(f"Ошибка при создании администратора: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Создание первого администратора")
    parser.add_argument("username", help="Имя пользователя")
    parser.add_argument("password", help="Пароль")
    
    args = parser.parse_args()
    init_admin(args.username, args.password)