from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import crud, schemas
from ..deps import get_db

router = APIRouter(prefix="/tests", tags=["tests"])

@router.get("/", response_model=list[schemas.Test])
async def list_tests(db: Session = Depends(get_db)):
    return crud.get_tests(db)

@router.get("/{test_id}", response_model=schemas.Test)
async def get_test(test_id: int, db: Session = Depends(get_db)):
    test = crud.get_test(db, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    return test