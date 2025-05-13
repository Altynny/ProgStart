from fastapi import APIRouter, Depends, HTTPException, Response, Cookie, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from .. import crud, schemas, models, auth
from ..deps import get_db
from pydantic import BaseModel

router = APIRouter(prefix="/tests", tags=["tests"])

# Schema for submitting answers
class Answer(BaseModel):
    question_id: int
    selected_option_id: int

class SubmitAnswers(BaseModel):
    answers: List[Answer]  # list of pairs {question_id: int, selected_option_id: int}

@router.get("/", response_model=List[schemas.Test])
async def list_tests(db: Session = Depends(get_db)):
    """Get all available tests"""
    return crud.get_tests(db)

@router.get("/{test_id}", response_model=schemas.Test)
async def get_test(
    test_id: int, 
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Get a specific test by ID and set cookie
    """
    test = crud.get_test(db, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    # Set cookie with test ID (30 minutes expiration)
    response.set_cookie(
        key="test_id", 
        value=str(test_id), 
        max_age=1800,  # 30 minutes in seconds
        httponly=True,
        samesite="lax"  # Important for modern browsers
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
    Submit test answers and calculate results
    """
    # Get cookie from request
    cookies = request.cookies
    current_test_id = cookies.get("test_id")
    
    # Debug information
    print(f"Current test_id from cookie: {current_test_id}")
    print(f"Test ID from URL: {test_id}")
    print(f"Answers received: {answers}")
    
    # Check if test_id from URL matches test_id from cookie
    if not current_test_id or int(current_test_id) != test_id:
        return JSONResponse(
            status_code=400,
            content={"detail": "Cannot submit answers. Test cookie is not set or has expired"}
        )
    
    # Get test from database
    test = crud.get_test(db, test_id)
    if not test:
        return JSONResponse(
            status_code=404,
            content={"detail": "Test not found"}
        )
    
    # Check answers and calculate score
    score = 0
    max_score = len(test.questions)
    
    # Create dictionary for quick lookup
    answer_map = {answer.question_id: answer.selected_option_id for answer in answers.answers}
    
    # Check each question for correct answers
    for question in test.questions:
        if question.id in answer_map and answer_map[question.id] == question.correct_option_id:
            score += 1
    
    # Save user's progress
    progress = crud.create_progress(
        db, 
        current_user.id, 
        schemas.ProgressCreate(test_id=test_id, score=score)
    )
    
    # Return result
    return {"id": progress.id, "test_id": progress.test_id, "score": progress.score}

@router.get("/{test_id}/result", response_model=schemas.ProgressOut)
async def get_test_result(
    test_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(auth.get_current_user)
):
    """
    Get results for a specific test for the user
    """
    # Get all progress records for user for this test
    user_progress = db.query(models.Progress).filter(
        models.Progress.user_id == current_user.id,
        models.Progress.test_id == test_id
    ).order_by(models.Progress.id.desc()).first()
    
    if not user_progress:
        raise HTTPException(
            status_code=404, 
            detail="Result not found. You may not have taken this test."
        )
    
    return user_progress