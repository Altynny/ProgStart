from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import Optional
from .. import models, auth
from ..deps import get_db
from ..crud import get_tests, get_test, get_user_progress

router = APIRouter(tags=["pages"])

# Получаем шаблонизатор из состояния приложения
def get_templates(request: Request) -> Jinja2Templates:
    return request.app.state.templates

# Функция для получения текущего пользователя (если он авторизован)
async def get_optional_user(
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(auth.get_token_from_cookie_or_header)
):
    try:
        if token:
            user = await auth.get_current_user(token=token, db=db)
            return user
        return None
    except HTTPException:
        return None

# Главная страница с таблицей лидеров
@router.get("/", response_class=HTMLResponse)
async def home_page(
    request: Request, 
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_optional_user),
    templates: Jinja2Templates = Depends(get_templates)
):
    # Получаем таблицу лидеров
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
    
    # Преобразуем в список словарей
    leaders_list = [{"username": username, "total_score": total_score} for username, total_score in leaders]
    
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "leaders": leaders_list, "user": current_user}
    )

# Страница списка тестов
@router.get("/tests", response_class=HTMLResponse)
async def tests_list_page(
    request: Request, 
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_optional_user),
    templates: Jinja2Templates = Depends(get_templates)
):
    tests = get_tests(db)
    return templates.TemplateResponse(
        "tests_list.html", 
        {"request": request, "tests": tests, "user": current_user}
    )

# Страница теста
@router.get("/tests/{test_id}", response_class=HTMLResponse)
async def test_page(
    test_id: int,
    request: Request, 
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_optional_user),
    templates: Jinja2Templates = Depends(get_templates)
):
    # Если пользователь не авторизован, перенаправляем на страницу входа
    if not current_user:
        return RedirectResponse(url="/login?next=/tests/" + str(test_id), status_code=302)
    
    test = get_test(db, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Тест не найден")
    
    # Устанавливаем cookie с ID теста
    response = templates.TemplateResponse(
        "test_page.html", 
        {"request": request, "test": test, "user": current_user}
    )
    response.set_cookie(key="test_id", value=str(test_id), max_age=1800, httponly=True)
    
    return response

# Страница профиля
@router.get("/profile", response_class=HTMLResponse)
async def profile_page(
    request: Request, 
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_optional_user),
    templates: Jinja2Templates = Depends(get_templates)
):
    # Если пользователь не авторизован, перенаправляем на страницу входа
    if not current_user:
        return RedirectResponse(url="/login?next=/profile", status_code=302)
    
    # Получаем прогресс пользователя
    progress = get_user_progress(db, current_user.id)
    
    # Получаем все тесты
    tests = get_tests(db)
    tests_dict = {test.id: test for test in tests}
    
    # Группируем прогресс по тестам
    grouped_progress = {}
    for p in progress:
        if p.test_id not in grouped_progress:
            grouped_progress[p.test_id] = []
        grouped_progress[p.test_id].append(p)
    
    # Подсчитываем общее количество баллов
    total_score = sum(p.score for p in progress)
    
    return templates.TemplateResponse(
        "profile.html", 
        {
            "request": request, 
            "user": current_user, 
            "progress": grouped_progress,
            "tests": tests_dict,
            "total_score": total_score
        }
    )

# Страница входа
@router.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    next: str = "/",
    templates: Jinja2Templates = Depends(get_templates),
    current_user: Optional[models.User] = Depends(get_optional_user)
):
    # Если пользователь уже авторизован, перенаправляем его
    if current_user:
        return RedirectResponse(url="/", status_code=302)
    
    return templates.TemplateResponse(
        "login.html", 
        {"request": request, "next": next, "user": None}
    )

# Страница регистрации
@router.get("/register", response_class=HTMLResponse)
async def register_page(
    request: Request,
    templates: Jinja2Templates = Depends(get_templates),
    current_user: Optional[models.User] = Depends(get_optional_user)
):
    # Если пользователь уже авторизован, перенаправляем его
    if current_user:
        return RedirectResponse(url="/", status_code=302)
    
    return templates.TemplateResponse(
        "register.html", 
        {"request": request, "user": None}
    )