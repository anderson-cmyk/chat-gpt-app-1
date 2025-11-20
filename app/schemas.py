import datetime as dt
from typing import Optional, List

from pydantic import BaseModel, Field

from .models import Role, ResponseType, Frequency


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None


class UserCreate(BaseModel):
    username: str
    password: str
    full_name: Optional[str] = None
    role: Role = Role.user
    operation_id: Optional[int] = None
    sub_operation_id: Optional[int] = None


class UserRead(BaseModel):
    id: int
    username: str
    full_name: Optional[str] = None
    role: Role
    is_active: bool
    operation_id: Optional[int]
    sub_operation_id: Optional[int]

    class Config:
        from_attributes = True


class OperationCreate(BaseModel):
    name: str


class OperationRead(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class SubOperationCreate(BaseModel):
    name: str
    operation_id: int


class SubOperationRead(BaseModel):
    id: int
    name: str
    operation_id: int

    class Config:
        from_attributes = True


class QuestionCreate(BaseModel):
    prompt: str
    response_type: ResponseType
    frequency: Frequency
    monthly_day: Optional[int] = Field(default=None, ge=1, le=31)
    is_active: bool = True
    operation_id: Optional[int] = None
    sub_operation_id: Optional[int] = None


class QuestionRead(BaseModel):
    id: int
    prompt: str
    response_type: ResponseType
    frequency: Frequency
    monthly_day: Optional[int]
    is_active: bool
    operation_id: Optional[int]
    sub_operation_id: Optional[int]

    class Config:
        from_attributes = True


class ResponseCreate(BaseModel):
    question_id: int
    answer_value: str
    answer_date: Optional[dt.date] = None


class ResponseRead(BaseModel):
    id: int
    question_id: int
    user_id: int
    answer_value: str
    answer_date: dt.date
    created_at: dt.datetime

    class Config:
        from_attributes = True


class QuestionWithAnswer(BaseModel):
    question: QuestionRead
    answer: Optional[ResponseRead]


class CompletionSnapshot(BaseModel):
    working_day: dt.date
    total_users: int
    completed_users: int
    pending_users: int


class PivotEntry(BaseModel):
    answer_date: dt.date
    operation: Optional[str] = None
    sub_operation: Optional[str] = None
    username: Optional[str] = None
    metric: float
    aggregation: str
    question_id: int


class PivotRequest(BaseModel):
    date_from: Optional[dt.date] = None
    date_to: Optional[dt.date] = None
    aggregation: str = "avg"  # avg|sum
