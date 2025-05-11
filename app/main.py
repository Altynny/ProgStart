from fastapi import FastAPI
from sqlalchemy.exc import OperationalError
from .database import engine, Base
from .routers import token, users, tests, progress

app = FastAPI(title="ProgStart")

try:
    Base.metadata.create_all(bind=engine)
except OperationalError:
    import logging
    logging.error("Database connection error.")

app.include_router(token.router)
app.include_router(users.router)
app.include_router(tests.router)
app.include_router(progress.router)