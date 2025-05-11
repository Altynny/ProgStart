from fastapi import APIRouter, Depends, HTTPException, Response, Cookie, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from .. import crud, schemas, models, auth
from ..deps import get_db
from pydantic import BaseModel

router = APIRouter(prefix="/tests", tags=["tests"])

# Схема для отправки ответов
class Answer(BaseModel):
    question_id: int
    selected_option_id: int

class SubmitAnswers(BaseModel):
    answers: List[Answer]  # список пар {question_id: int, selected_option_id: int}

@router.get("/", response_model=List[schemas.Test])
async def list_tests(db: Session = Depends(get_db)):
    """Получение списка всех тестов"""
    return crud.get_tests(db)

@router.get("/{test_id}", response_model=schemas.Test)
async def get_test(
    test_id: int, 
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Получение конкретного теста по ID и установка куки
    """
    test = crud.get_test(db, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Тест не найден")
    
    # Устанавливаем куки с ID теста (срок действия 30 минут)
    response.set_cookie(
        key="test_id", 
        value=str(test_id), 
        max_age=1800,  # 30 минут в секундах
        httponly=True,
        samesite="lax"  # Важно для работы куки в современных браузерах
    )
    
    return test

@router.post("/{test_id}/submit")
async def submit_test(
    test_id: int,
    answers: SubmitAnswers,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(auth.get_current_user)
):
    """
    Отправка ответов на тест и проверка результатов
    """
    # Получаем куки из запроса напрямую
    cookies = request.cookies
    current_test_id = cookies.get("test_id")
    
    # Вывод отладочной информации
    print(f"Current test_id from cookie: {current_test_id}")
    print(f"Test ID from URL: {test_id}")
    print(f"Answers received: {answers}")
    
    # Проверяем совпадение test_id из URL с test_id из куки
    if not current_test_id or int(current_test_id) != test_id:
        return JSONResponse(
            status_code=400,
            content={"detail": "Невозможно отправить ответы. Куки теста не установлены или истекли"}
        )
    
    # Получаем тест из БД
    test = crud.get_test(db, test_id)
    if not test:
        return JSONResponse(
            status_code=404,
            content={"detail": "Тест не найден"}
        )
    
    # Проверяем ответы и подсчитываем баллы
    score = 0
    max_score = len(test.questions)
    
    # Создаем словарь для быстрого поиска
    answer_map = {answer.question_id: answer.selected_option_id for answer in answers.answers}
    
    # Для каждого вопроса проверяем правильность ответа
    for question in test.questions:
        if question.id in answer_map and answer_map[question.id] == question.correct_option_id:
            score += 1
    
    # Сохраняем прогресс пользователя
    progress = crud.create_progress(
        db, 
        current_user.id, 
        schemas.ProgressCreate(test_id=test_id, score=score)
    )
    
    # Возвращаем результат
    return {"id": progress.id, "test_id": progress.test_id, "score": progress.score}

@router.get("/{test_id}/result", response_model=schemas.ProgressOut)
async def get_test_result(
    test_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(auth.get_current_user)
):
    """
    Получение результата конкретного теста для пользователя
    """
    # Получаем все записи прогресса для пользователя по данному тесту
    user_progress = db.query(models.Progress).filter(
        models.Progress.user_id == current_user.id,
        models.Progress.test_id == test_id
    ).order_by(models.Progress.id.desc()).first()
    
    if not user_progress:
        raise HTTPException(
            status_code=404, 
            detail="Результат не найден. Возможно, вы не проходили этот тест."
        )
    
    return user_progress