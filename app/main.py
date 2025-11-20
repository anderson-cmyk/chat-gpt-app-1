import datetime as dt
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select, func

from .auth import (
    authenticate_user,
    create_access_token,
    get_current_active_user,
    require_admin,
    get_password_hash,
)
from .config import get_settings
from .database import init_db, get_session
from .models import User, Operation, SubOperation, Question, Response, ResponseType, Role
from .schemas import (
    Token,
    UserCreate,
    UserRead,
    OperationCreate,
    OperationRead,
    SubOperationCreate,
    SubOperationRead,
    QuestionCreate,
    QuestionRead,
    ResponseCreate,
    ResponseRead,
    QuestionWithAnswer,
    CompletionSnapshot,
    PivotEntry,
    PivotRequest,
)
from .utils import question_is_due, working_day_index, is_working_day

settings = get_settings()
app = FastAPI(title=settings.app_name)

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static", html=True), name="static")


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/")
def index():
    return FileResponse("static/index.html")


@app.post("/auth/token", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)
):
    user = authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token({"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/auth/me", response_model=UserRead)
def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user


@app.post("/admin/users", response_model=UserRead)
def create_user(user_in: UserCreate, session: Session = Depends(get_session), _: User = Depends(require_admin)):
    if session.exec(select(User).where(User.username == user_in.username)).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    user = User(
        username=user_in.username,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role=user_in.role,
        operation_id=user_in.operation_id,
        sub_operation_id=user_in.sub_operation_id,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@app.get("/admin/users", response_model=List[UserRead])
def list_users(session: Session = Depends(get_session), _: User = Depends(require_admin)):
    return session.exec(select(User)).all()


@app.post("/admin/operations", response_model=OperationRead)
def create_operation(op_in: OperationCreate, session: Session = Depends(get_session), _: User = Depends(require_admin)):
    op = Operation(name=op_in.name)
    session.add(op)
    session.commit()
    session.refresh(op)
    return op


@app.get("/admin/operations", response_model=List[OperationRead])
def list_operations(session: Session = Depends(get_session), _: User = Depends(require_admin)):
    return session.exec(select(Operation)).all()


@app.post("/admin/sub-operations", response_model=SubOperationRead)
def create_sub_operation(so_in: SubOperationCreate, session: Session = Depends(get_session), _: User = Depends(require_admin)):
    operation = session.get(Operation, so_in.operation_id)
    if not operation:
        raise HTTPException(status_code=404, detail="Operation not found")
    sub = SubOperation(name=so_in.name, operation_id=so_in.operation_id)
    session.add(sub)
    session.commit()
    session.refresh(sub)
    return sub


@app.get("/admin/sub-operations", response_model=List[SubOperationRead])
def list_sub_operations(session: Session = Depends(get_session), _: User = Depends(require_admin)):
    return session.exec(select(SubOperation)).all()


@app.post("/admin/questions", response_model=QuestionRead)
def create_question(q_in: QuestionCreate, session: Session = Depends(get_session), _: User = Depends(require_admin)):
    if q_in.frequency == Frequency.monthly and not q_in.monthly_day:
        raise HTTPException(status_code=400, detail="monthly_day is required for monthly questions")
    question = Question(**q_in.model_dump())
    session.add(question)
    session.commit()
    session.refresh(question)
    return question


@app.get("/admin/questions", response_model=List[QuestionRead])
def list_questions(session: Session = Depends(get_session), _: User = Depends(require_admin)):
    return session.exec(select(Question)).all()


@app.get("/questions/today", response_model=List[QuestionWithAnswer])
def get_today_questions(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
    date: Optional[dt.date] = None,
):
    target_date = date or dt.date.today()
    if not is_working_day(target_date):
        return []

    query = select(Question).where(Question.is_active == True)  # noqa: E712
    if current_user.operation_id:
        query = query.where((Question.operation_id == current_user.operation_id) | (Question.operation_id.is_(None)))
    if current_user.sub_operation_id:
        query = query.where((Question.sub_operation_id == current_user.sub_operation_id) | (Question.sub_operation_id.is_(None)))

    questions = session.exec(query).all()
    due_questions = [q for q in questions if question_is_due(q, target_date)]

    answers = session.exec(
        select(Response).where(Response.user_id == current_user.id, Response.answer_date == target_date)
    ).all()
    answer_map = {(a.question_id, a.answer_date): a for a in answers}

    result = [
        QuestionWithAnswer(question=q, answer=answer_map.get((q.id, target_date)))
        for q in due_questions
    ]
    return result


@app.post("/responses", response_model=ResponseRead)
def create_response(
    response_in: ResponseCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
):
    question = session.get(Question, response_in.question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    answer_date = response_in.answer_date or dt.date.today()
    if not question_is_due(question, answer_date):
        raise HTTPException(status_code=400, detail="Question is not scheduled for this date")

    # ensure only one answer per day
    existing = session.exec(
        select(Response).where(
            Response.question_id == question.id,
            Response.user_id == current_user.id,
            Response.answer_date == answer_date,
        )
    ).first()
    if existing:
        existing.answer_value = response_in.answer_value
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing

    response = Response(
        question_id=question.id,
        user_id=current_user.id,
        answer_value=response_in.answer_value,
        answer_date=answer_date,
    )
    session.add(response)
    session.commit()
    session.refresh(response)
    return response


@app.get("/dashboard/completion", response_model=CompletionSnapshot)
def completion(
    session: Session = Depends(get_session),
    _: User = Depends(require_admin),
    date: Optional[dt.date] = None,
):
    working_day = date or dt.date.today()
    if not is_working_day(working_day):
        raise HTTPException(status_code=400, detail="The provided date is not a working day")

    total_users = session.exec(select(func.count()).select_from(User)).one()
    answered_users = session.exec(
        select(func.count(func.distinct(Response.user_id))).where(Response.answer_date == working_day)
    ).one()
    pending = max(total_users - answered_users, 0)
    return CompletionSnapshot(
        working_day=working_day,
        total_users=total_users,
        completed_users=answered_users,
        pending_users=pending,
    )


@app.post("/dashboard/pivot", response_model=List[PivotEntry])
def pivot(
    payload: PivotRequest,
    session: Session = Depends(get_session),
    _: User = Depends(require_admin),
):
    query = (
        select(
            Response.answer_date,
            Operation.name.label("operation"),
            SubOperation.name.label("sub_operation"),
            User.username,
            Response.answer_value,
            Response.question_id,
            Question.response_type,
        )
        .join(User, User.id == Response.user_id)
        .join(Question, Question.id == Response.question_id)
        .join(Operation, Operation.id == Question.operation_id, isouter=True)
        .join(SubOperation, SubOperation.id == Question.sub_operation_id, isouter=True)
    )

    if payload.date_from:
        query = query.where(Response.answer_date >= payload.date_from)
    if payload.date_to:
        query = query.where(Response.answer_date <= payload.date_to)

    rows = session.exec(query).all()
    entries: List[PivotEntry] = []
    for row in rows:
        try:
            value = float(row.answer_value)
        except ValueError:
            value = 0.0
        entries.append(
            PivotEntry(
                answer_date=row.answer_date,
                operation=row.operation,
                sub_operation=row.sub_operation,
                username=row.username,
                metric=value,
                aggregation=payload.aggregation,
                question_id=row.question_id,
            )
        )

    # simple aggregation by day/question/operation
    key_fn = lambda e: (e.answer_date, e.question_id, e.operation, e.sub_operation, e.username)
    grouped = {}
    for entry in entries:
        grouped.setdefault(key_fn(entry), []).append(entry.metric)

    collapsed: List[PivotEntry] = []
    for key, values in grouped.items():
        if payload.aggregation == "sum":
            metric = sum(values)
        else:
            metric = sum(values) / len(values)
        answer_date, question_id, operation, sub_operation, username = key
        collapsed.append(
            PivotEntry(
                answer_date=answer_date,
                operation=operation,
                sub_operation=sub_operation,
                username=username,
                metric=metric,
                aggregation=payload.aggregation,
                question_id=question_id,
            )
        )
    return collapsed


@app.get("/health")
def health():
    today = dt.date.today()
    return {
        "status": "ok",
        "today": str(today),
        "working_day_index": working_day_index(today),
    }
