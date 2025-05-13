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

# Get templates from application state
def get_templates(request: Request) -> Jinja2Templates:
    return request.app.state.templates

# Function to get current user (if authenticated)
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

# Home page with leaderboard
@router.get("/", response_class=HTMLResponse)
async def home_page(
    request: Request, 
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_optional_user),
    templates: Jinja2Templates = Depends(get_templates)
):
    # Get leaderboard
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
    
    # Convert to list of dictionaries
    leaders_list = [{"username": username, "total_score": total_score} for username, total_score in leaders]
    
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "leaders": leaders_list, "user": current_user}
    )

# Tests list page
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

# Test page
@router.get("/tests/{test_id}", response_class=HTMLResponse)
async def test_page(
    test_id: int,
    request: Request, 
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_optional_user),
    templates: Jinja2Templates = Depends(get_templates)
):
    # If user is not authenticated, redirect to login page
    if not current_user:
        return RedirectResponse(url="/login?next=/tests/" + str(test_id), status_code=302)
    
    test = get_test(db, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    # Set cookie with test ID
    response = templates.TemplateResponse(
        "test_page.html", 
        {"request": request, "test": test, "user": current_user}
    )
    response.set_cookie(key="test_id", value=str(test_id), max_age=1800, httponly=True)
    
    return response

# Profile page
@router.get("/profile", response_class=HTMLResponse)
async def profile_page(
    request: Request, 
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_optional_user),
    templates: Jinja2Templates = Depends(get_templates)
):
    # If user is not authenticated, redirect to login page
    if not current_user:
        return RedirectResponse(url="/login?next=/profile", status_code=302)
    
    # Get user's progress
    progress = get_user_progress(db, current_user.id)
    
    # Get all tests
    tests = get_tests(db)
    tests_dict = {test.id: test for test in tests}
    
    # Group progress by tests
    grouped_progress = {}
    for p in progress:
        if p.test_id not in grouped_progress:
            grouped_progress[p.test_id] = []
        grouped_progress[p.test_id].append(p)
    
    # Calculate total score
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

# Login page
@router.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    next: str = "/",
    templates: Jinja2Templates = Depends(get_templates),
    current_user: Optional[models.User] = Depends(get_optional_user)
):
    # If user is already authenticated, redirect
    if current_user:
        return RedirectResponse(url="/", status_code=302)
    
    return templates.TemplateResponse(
        "login.html", 
        {"request": request, "next": next, "user": None}
    )

# Registration page
@router.get("/register", response_class=HTMLResponse)
async def register_page(
    request: Request,
    templates: Jinja2Templates = Depends(get_templates),
    current_user: Optional[models.User] = Depends(get_optional_user)
):
    # If user is already authenticated, redirect
    if current_user:
        return RedirectResponse(url="/", status_code=302)
    
    return templates.TemplateResponse(
        "register.html", 
        {"request": request, "user": None}
    )