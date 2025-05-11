from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError
from .database import engine, Base
from .routers import token, users, tests, progress, leaderboard

app = FastAPI(title="ProgStart - Платформа тестирования по программированию")

# Добавление CORS для фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене лучше указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    Base.metadata.create_all(bind=engine)
except OperationalError:
    import logging
    logging.error("Ошибка подключения к базе данных.")

# Регистрация роутеров
app.include_router(leaderboard.router)  # Корневой роутер для таблицы лидеров
app.include_router(token.router)
app.include_router(users.router)
app.include_router(tests.router)
app.include_router(progress.router)

@app.get("/", tags=["root"])
async def root():
    """
    Корневой эндпоинт с приветствием и инструкциями
    """
    return {
        "message": "Добро пожаловать в API платформы тестирования по программированию ProgStart",
        "docs": "/docs",
        "leaderboard": "/",
        "register": "/users/register",
        "login": "/token",
        "tests": "/tests"
    }