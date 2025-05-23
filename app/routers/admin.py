from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, crud, admin
from ..deps import get_db

router = APIRouter(prefix="/admin", tags=["admin"])

# Get templates from application state
def get_templates(request: Request) -> Jinja2Templates:
    return request.app.state.templates

# Check admin permissions
async def check_admin(
    request: Request,
    templates: Jinja2Templates = Depends(get_templates),
    current_user: models.User = Depends(admin.admin_required)
):
    """
    Checks if user is admin and returns templates
    """
    return templates, current_user

# Admin dashboard page
@router.get("/", response_class=HTMLResponse)
async def admin_panel(
    request: Request, 
    db: Session = Depends(get_db),
    check: tuple = Depends(check_admin)
):
    templates, current_user = check
    
    # Get statistics
    users_count = db.query(models.User).count()
    tests_count = db.query(models.Test).count()
    progress_count = db.query(models.Progress).count()
    
    return templates.TemplateResponse(
        "admin/index.html", 
        {
            "request": request,
            "user": current_user,
            "users_count": users_count,
            "tests_count": tests_count,
            "progress_count": progress_count
        }
    )

# User management
@router.get("/users", response_class=HTMLResponse)
async def admin_users(
    request: Request,
    db: Session = Depends(get_db),
    check: tuple = Depends(check_admin)
):
    templates, current_user = check
    
    # Get all users
    users = crud.get_users(db)
    roles = db.query(models.Role).all()
    
    return templates.TemplateResponse(
        "admin/users.html", 
        {
            "request": request,
            "user": current_user,
            "users": users,
            "roles": roles
        }
    )

# User management API
@router.post("/users/create", response_model=schemas.UserOut)
async def create_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(admin.admin_required)
):
    db_user = crud.get_user_by_username(db, user.username)
    if db_user:
        raise HTTPException(status_code=409, detail="Username already exists")
    
    return crud.create_admin_user(db, user)

@router.put("/users/{user_id}", response_model=schemas.UserOut)
async def update_user(
    user_id: int,
    user_data: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(admin.admin_required)
):
    # Don't allow editing self to prevent losing admin rights
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="You cannot edit your own account through this API")
    
    db_user = crud.update_user(db, user_id, user_data)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return db_user

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(admin.admin_required)
):
    # Don't allow deleting self
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account")
    
    result = crud.delete_user(db, user_id)
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User deleted successfully"}

# Test management
@router.get("/tests", response_class=HTMLResponse)
async def admin_tests(
    request: Request,
    db: Session = Depends(get_db),
    check: tuple = Depends(check_admin)
):
    templates, current_user = check
    
    # Get all tests
    tests = crud.get_tests(db)
    
    return templates.TemplateResponse(
        "admin/tests.html", 
        {
            "request": request,
            "user": current_user,
            "tests": tests
        }
    )

@router.get("/tests/create", response_class=HTMLResponse)
async def create_test_page(
    request: Request,
    check: tuple = Depends(check_admin)
):
    templates, current_user = check
    
    return templates.TemplateResponse(
        "admin/test_form.html", 
        {
            "request": request,
            "user": current_user,
            "test": None,
            "action": "create"
        }
    )

@router.get("/tests/{test_id}/edit", response_class=HTMLResponse)
async def edit_test_page(
    test_id: int,
    request: Request,
    db: Session = Depends(get_db),
    check: tuple = Depends(check_admin)
):
    templates, current_user = check
    
    # Get test for editing
    test = crud.get_test(db, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    return templates.TemplateResponse(
        "admin/test_form.html", 
        {
            "request": request,
            "user": current_user,
            "test": test,
            "action": "edit"
        }
    )

# Test management API
@router.post("/tests", response_model=schemas.Test)
async def create_test(
    test: schemas.TestCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(admin.admin_required)
):
    return crud.create_test(db, test)

@router.put("/tests/{test_id}", response_model=schemas.Test)
async def update_test(
    test_id: int,
    test_data: schemas.TestUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(admin.admin_required)
):
    db_test = crud.update_test(db, test_id, test_data)
    if not db_test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    return db_test

@router.delete("/tests/{test_id}")
async def delete_test(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(admin.admin_required)
):
    result = crud.delete_test(db, test_id)
    if not result:
        raise HTTPException(status_code=404, detail="Test not found")
    
    return {"message": "Test deleted successfully"}