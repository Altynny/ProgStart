from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from pathlib import Path
import datetime
from .database import engine, Base, SessionLocal
from .routers import token, users, tests, progress, pages, admin
from .auth import get_current_user
from .deps import get_db
from . import crud, models
from .admin import create_initial_admin

app = FastAPI(title="ProgStart - Платформа тестирования по программированию")

# CORS настройки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешаем все источники (в продакшене лучше указать конкретные)
    allow_credentials=True,  # Важно для работы с куки
    allow_methods=["*"],  # Разрешаем все методы (GET, POST и т.д.)
    allow_headers=["*"],  # Разрешаем все заголовки
)

# Путь к директории с шаблонами и статическими файлами
templates_dir = Path(__file__).parent / "templates"
static_dir = Path(__file__).parent / "static"

# Создаем директории, если они не существуют
templates_dir.mkdir(exist_ok=True)
static_dir.mkdir(exist_ok=True)

# Настраиваем шаблонизатор Jinja2
templates = Jinja2Templates(directory=str(templates_dir))
app.state.templates = templates

# Настраиваем статические файлы
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

try:
    # Создаем таблицы в базе данных
    Base.metadata.create_all(bind=engine)
    
    # Создаем роль администратора, если ее еще нет
    db = SessionLocal()
    try:
        admin_role = db.query(models.Role).filter(models.Role.name == "admin").first()
        if not admin_role:
            admin_role = models.Role(name="admin", description="Администратор системы")
            db.add(admin_role)
            db.commit()
    finally:
        db.close()
except OperationalError:
    import logging
    logging.error("Ошибка подключения к базе данных.")

# Регистрация роутеров
app.include_router(pages.router)  # Роутер для рендеринга страниц
app.include_router(token.router)  # Роутер для аутентификации
app.include_router(users.router)  # Роутер для пользователей
app.include_router(tests.router)  # Роутер для тестов
app.include_router(progress.router)  # Роутер для прогресса
app.include_router(admin.router)  # Роутер для админки

@app.middleware("http")
async def add_global_context(request: Request, call_next):
    """
    Добавляет глобальный контекст для всех шаблонов
    """
    # Добавляем текущий год для футера
    request.state.current_year = datetime.datetime.now().year
    
    response = await call_next(request)
    
    # Исправление заголовков для работы с куки
    response.headers["SameSite"] = "Lax"
    
    return response

# Обновляем Jinja2Templates для добавления глобальных переменных
@app.on_event("startup")
async def startup_event():
    templates.env.globals["current_year"] = datetime.datetime.now().year