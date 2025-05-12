from pydantic import BaseModel
from typing import List, Optional

# Roles
class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None

class RoleCreate(RoleBase):
    pass

class RoleOut(RoleBase):
    id: int
    class Config:
        from_attributes = True

# Users
class UserIn(BaseModel):
    username: str
    password: str

class UserCreate(UserIn):
    is_admin: bool = False

class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    roles: Optional[List[int]] = None

class UserOut(BaseModel):
    id: int
    username: str
    is_active: bool
    roles: List[RoleOut] = []
    class Config:
        from_attributes = True

# Auth
class Token(BaseModel):
    access_token: str
    token_type: str

# Options
class OptionBase(BaseModel):
    text: str

class OptionCreate(OptionBase):
    pass

class OptionUpdate(OptionBase):
    id: Optional[int] = None

class Option(OptionBase):
    id: int
    class Config:
        from_attributes = True

# Questions
class QuestionBase(BaseModel):
    text: str

class QuestionCreate(QuestionBase):
    options: List[OptionCreate]
    correct_option_index: int  # Индекс правильного варианта (0-based)

class QuestionUpdate(QuestionBase):
    id: Optional[int] = None
    options: List[OptionUpdate]
    correct_option_index: Optional[int] = None

class Question(QuestionBase):
    id: int
    options: List[Option]
    class Config:
        from_attributes = True

# Tests
class TestBase(BaseModel):
    title: str
    description: Optional[str] = None

class TestCreate(TestBase):
    questions: List[QuestionCreate]

class TestUpdate(TestBase):
    questions: Optional[List[QuestionUpdate]] = None

class Test(TestBase):
    id: int
    questions: List[Question]
    class Config:
        from_attributes = True

class TestListItem(TestBase):
    id: int
    question_count: int
    class Config:
        from_attributes = True

# Progress
class ProgressCreate(BaseModel):
    test_id: int
    score: int

class ProgressOut(BaseModel):
    id: int
    test_id: int
    score: int
    class Config:
        from_attributes = True