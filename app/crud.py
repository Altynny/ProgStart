from sqlalchemy.orm import Session
from . import models, schemas, auth

# User operations
def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_pwd = auth.get_password_hash(user.password)
    db_user = models.User(username=user.username, hashed_password=hashed_pwd)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Test operations
def get_tests(db: Session):
    return db.query(models.Test).all()

def get_test(db: Session, test_id: int):
    return db.query(models.Test).filter(models.Test.id == test_id).first()

# Progress operations
def create_progress(db: Session, user_id: int, progress: schemas.ProgressCreate):
    db_prog = models.Progress(user_id=user_id, test_id=progress.test_id, score=progress.score)
    db.add(db_prog)
    db.commit()
    db.refresh(db_prog)
    return db_prog

def get_user_progress(db: Session, user_id: int):
    return db.query(models.Progress).filter(models.Progress.user_id == user_id).all()