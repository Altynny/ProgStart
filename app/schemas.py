from pydantic import BaseModel
from typing import List, Optional

# Users
class UserIn(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    is_active: bool
    class Config:
        from_attributes = True

# Auth
class Token(BaseModel):
    access_token: str
    token_type: str

# Tests
class Option(BaseModel):
    id: int
    text: str
    class Config:
        from_attributes = True

class Question(BaseModel):
    id: int
    text: str
    options: List[Option]
    class Config:
        from_attributes = True

class Test(BaseModel):
    id: int
    title: str
    description: Optional[str]
    questions: List[Question]
    class Config:
        from_attributes = True

class ProgressCreate(BaseModel):
    test_id: int
    score: int

class ProgressOut(BaseModel):
    id: int
    test_id: int
    score: int
    class Config:
        from_attributes = True