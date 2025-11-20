import datetime as dt
from enum import Enum
from typing import Optional, List

from sqlmodel import SQLModel, Field, Relationship


class Role(str, Enum):
    admin = "admin"
    user = "user"


class ResponseType(str, Enum):
    number = "number"
    text = "text"


class Frequency(str, Enum):
    daily = "daily"
    monthly = "monthly"


class Operation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

    sub_operations: List["SubOperation"] = Relationship(back_populates="operation")
    users: List["User"] = Relationship(back_populates="operation")
    questions: List["Question"] = Relationship(back_populates="operation")


class SubOperation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    operation_id: int = Field(foreign_key="operation.id")

    operation: Operation = Relationship(back_populates="sub_operations")
    users: List["User"] = Relationship(back_populates="sub_operation")
    questions: List["Question"] = Relationship(back_populates="sub_operation")


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str
    full_name: Optional[str] = None
    role: Role = Field(default=Role.user)
    is_active: bool = Field(default=True)
    operation_id: Optional[int] = Field(default=None, foreign_key="operation.id")
    sub_operation_id: Optional[int] = Field(default=None, foreign_key="suboperation.id")

    operation: Optional[Operation] = Relationship(back_populates="users")
    sub_operation: Optional[SubOperation] = Relationship(back_populates="users")
    responses: List["Response"] = Relationship(back_populates="user")


class Question(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    prompt: str
    response_type: ResponseType = Field(default=ResponseType.text)
    frequency: Frequency = Field(default=Frequency.daily)
    monthly_day: Optional[int] = None  # working day index in month when applicable
    is_active: bool = Field(default=True)
    operation_id: Optional[int] = Field(default=None, foreign_key="operation.id")
    sub_operation_id: Optional[int] = Field(default=None, foreign_key="suboperation.id")

    operation: Optional[Operation] = Relationship(back_populates="questions")
    sub_operation: Optional[SubOperation] = Relationship(back_populates="questions")
    responses: List["Response"] = Relationship(back_populates="question")


class Response(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    answer_value: str
    answer_date: dt.date = Field(default_factory=lambda: dt.date.today())
    created_at: dt.datetime = Field(default_factory=lambda: dt.datetime.utcnow())
    user_id: int = Field(foreign_key="user.id")
    question_id: int = Field(foreign_key="question.id")

    user: User = Relationship(back_populates="responses")
    question: Question = Relationship(back_populates="responses")
