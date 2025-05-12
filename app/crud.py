from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from . import models, schemas, auth

# Role operations
def get_role_by_name(db: Session, name: str):
    return db.query(models.Role).filter(models.Role.name == name).first()

def create_role(db: Session, role: schemas.RoleCreate):
    db_role = models.Role(**role.dict())
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role

# User operations
def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserIn):
    hashed_pwd = auth.get_password_hash(user.password)
    db_user = models.User(username=user.username, hashed_password=hashed_pwd)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_admin_user(db: Session, user: schemas.UserCreate):
    # Создаем пользователя
    hashed_pwd = auth.get_password_hash(user.password)
    db_user = models.User(username=user.username, hashed_password=hashed_pwd)
    
    # Если пользователь должен быть админом, добавляем роль
    if user.is_admin:
        admin_role = get_role_by_name(db, "admin")
        if not admin_role:
            admin_role = create_role(db, schemas.RoleCreate(name="admin", description="Администратор системы"))
        db_user.roles.append(admin_role)
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: int, user_data: schemas.UserUpdate):
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    # Обновляем поля, если они указаны
    if user_data.username is not None:
        db_user.username = user_data.username
    
    if user_data.password is not None:
        db_user.hashed_password = auth.get_password_hash(user_data.password)
    
    if user_data.is_active is not None:
        db_user.is_active = user_data.is_active
    
    # Обновляем роли, если они указаны
    if user_data.roles is not None:
        # Очищаем текущие роли
        db_user.roles = []
        
        # Добавляем новые роли
        for role_id in user_data.roles:
            role = db.query(models.Role).filter(models.Role.id == role_id).first()
            if role:
                db_user.roles.append(role)
    
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int):
    db_user = get_user(db, user_id)
    if db_user:
        # Благодаря cascade в моделях, все связанные записи будут удалены автоматически
        db.delete(db_user)
        db.commit()
        return True
    return False

# Test operations
def get_tests(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Test).offset(skip).limit(limit).all()

def get_test(db: Session, test_id: int):
    return db.query(models.Test).filter(models.Test.id == test_id).first()

def create_test(db: Session, test: schemas.TestCreate):
    # Создаем тест
    db_test = models.Test(title=test.title, description=test.description)
    db.add(db_test)
    db.flush()  # Чтобы получить ID теста
    
    # Создаем вопросы и варианты ответов
    for question_data in test.questions:
        db_question = models.Question(
            test_id=db_test.id,
            text=question_data.text
        )
        db.add(db_question)
        db.flush()  # Чтобы получить ID вопроса
        
        # Создаем варианты ответов
        options = []
        for i, option_data in enumerate(question_data.options):
            db_option = models.Option(
                question_id=db_question.id,
                text=option_data.text
            )
            db.add(db_option)
            db.flush()  # Чтобы получить ID варианта
            options.append(db_option)
        
        # Устанавливаем правильный вариант ответа
        if 0 <= question_data.correct_option_index < len(options):
            db_question.correct_option_id = options[question_data.correct_option_index].id
    
    db.commit()
    db.refresh(db_test)
    return db_test

def update_test(db: Session, test_id: int, test_data: schemas.TestUpdate):
    db_test = get_test(db, test_id)
    if not db_test:
        return None
    
    # Обновляем основные поля теста
    if test_data.title is not None:
        db_test.title = test_data.title
    if test_data.description is not None:
        db_test.description = test_data.description
    
    # Если есть вопросы для обновления
    if test_data.questions is not None:
        # Обрабатываем каждый вопрос
        for question_data in test_data.questions:
            # Если вопрос имеет ID, обновляем существующий
            if question_data.id is not None:
                db_question = db.query(models.Question).filter(
                    models.Question.id == question_data.id,
                    models.Question.test_id == test_id
                ).first()
                
                if db_question:
                    db_question.text = question_data.text
                    
                    # Обновляем варианты ответов
                    if question_data.options:
                        # Создаем словарь для текущих вариантов
                        current_options = {opt.id: opt for opt in db_question.options}
                        new_options = []
                        
                        for option_data in question_data.options:
                            # Если вариант имеет ID, обновляем существующий
                            if option_data.id is not None and option_data.id in current_options:
                                opt = current_options[option_data.id]
                                opt.text = option_data.text
                                new_options.append(opt)
                            else:
                                # Иначе создаем новый вариант
                                db_option = models.Option(
                                    question_id=db_question.id,
                                    text=option_data.text
                                )
                                db.add(db_option)
                                db.flush()
                                new_options.append(db_option)
                        
                        # Удаляем варианты, которых нет в обновлении
                        for opt_id, opt in current_options.items():
                            if opt not in new_options:
                                db.delete(opt)
                        
                        # Обновляем правильный вариант
                        if question_data.correct_option_index is not None and question_data.correct_option_index < len(new_options):
                            db_question.correct_option_id = new_options[question_data.correct_option_index].id
            else:
                # Иначе создаем новый вопрос
                db_question = models.Question(
                    test_id=test_id,
                    text=question_data.text
                )
                db.add(db_question)
                db.flush()
                
                # Создаем варианты ответов
                options = []
                for option_data in question_data.options:
                    db_option = models.Option(
                        question_id=db_question.id,
                        text=option_data.text
                    )
                    db.add(db_option)
                    db.flush()
                    options.append(db_option)
                
                # Устанавливаем правильный вариант ответа
                if question_data.correct_option_index is not None and question_data.correct_option_index < len(options):
                    db_question.correct_option_id = options[question_data.correct_option_index].id
    
    db.commit()
    db.refresh(db_test)
    return db_test

def delete_test(db: Session, test_id: int):
    db_test = get_test(db, test_id)
    if db_test:
        # Благодаря cascade в моделях, все связанные записи будут удалены автоматически
        db.delete(db_test)
        db.commit()
        return True
    return False

# Progress operations
def create_progress(db: Session, user_id: int, progress: schemas.ProgressCreate):
    db_prog = models.Progress(user_id=user_id, test_id=progress.test_id, score=progress.score)
    db.add(db_prog)
    db.commit()
    db.refresh(db_prog)
    return db_prog

def get_user_progress(db: Session, user_id: int):
    return db.query(models.Progress).filter(models.Progress.user_id == user_id).all()

def get_test_results(db: Session, test_id: int):
    return db.query(models.Progress).filter(models.Progress.test_id == test_id).all()

def get_leaderboard(db: Session, limit: int = 10):
    leaders = db.query(
        models.User.id,
        models.User.username,
        func.sum(models.Progress.score).label("total_score")
    ).join(
        models.Progress, models.User.id == models.Progress.user_id
    ).group_by(
        models.User.id
    ).order_by(
        func.sum(models.Progress.score).desc()
    ).limit(limit).all()
    
    return leaders