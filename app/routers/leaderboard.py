from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from .. import models, schemas
from ..deps import get_db

router = APIRouter(tags=["leaderboard"])

class UserScore(schemas.BaseModel):
    username: str
    total_score: int
    
    class Config:
        from_attributes = True

@router.get("/", response_model=list[UserScore])
async def get_leaderboard(db: Session = Depends(get_db)):
    """
    Получение таблицы лидеров - список пользователей с суммарным количеством баллов,
    отсортированный по убыванию баллов
    """
    # Получаем сумму баллов каждого пользователя
    leaders = db.query(
        models.User.username,
        func.sum(models.Progress.score).label("total_score")
    ).join(
        models.Progress, models.User.id == models.Progress.user_id
    ).group_by(
        models.User.id
    ).order_by(
        func.sum(models.Progress.score).desc()
    ).all()
    
    # Преобразуем результаты в нужный формат
    return [{"username": username, "total_score": total_score} for username, total_score in leaders]