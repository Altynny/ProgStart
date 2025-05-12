from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Text, Table
from sqlalchemy.orm import relationship
from .database import Base

# Таблица связи многие-ко-многим между пользователями и ролями
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE")),
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"))
)

class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255))
    
    users = relationship("User", secondary=user_roles, back_populates="roles")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(128), nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Связь с ролями
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    
    # Связь с прогрессом с cascade удалением
    progress = relationship("Progress", back_populates="user", cascade="all, delete-orphan")

class Test(Base):
    __tablename__ = "tests"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    description = Column(Text)
    
    # Связь с вопросами с cascade удалением
    questions = relationship("Question", back_populates="test", cascade="all, delete-orphan")

class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("tests.id", ondelete="CASCADE"))
    text = Column(Text, nullable=False)
    correct_option_id = Column(Integer, ForeignKey("options.id", ondelete="SET NULL"), nullable=True)

    options = relationship(
        "Option",
        back_populates="question",
        foreign_keys="Option.question_id",
        cascade="all, delete-orphan"
    )

    test = relationship("Test", back_populates="questions")

class Option(Base):
    __tablename__ = "options"
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"))
    text = Column(String(200), nullable=False)

    question = relationship(
        "Question",
        back_populates="options",
        foreign_keys=[question_id]
    )

class Progress(Base):
    __tablename__ = "progress"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    test_id = Column(Integer, ForeignKey("tests.id", ondelete="CASCADE"))
    score = Column(Integer)
    user = relationship("User", back_populates="progress")