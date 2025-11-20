import datetime as dt
from calendar import monthrange
from typing import Iterable

from .models import Frequency, Question


def is_working_day(day: dt.date) -> bool:
    # Monday = 0, Sunday = 6
    return day.weekday() != 6


def working_day_index(day: dt.date) -> int:
    """Return 1-based working day index within the month (Mon-Sat)."""
    count = 0
    for d in iter_month_days(day.year, day.month):
        if is_working_day(d):
            count += 1
        if d == day:
            return count
    return count


def iter_month_days(year: int, month: int) -> Iterable[dt.date]:
    for day in range(1, monthrange(year, month)[1] + 1):
        yield dt.date(year, month, day)


def question_is_due(question: Question, day: dt.date) -> bool:
    if not question.is_active:
        return False
    if question.frequency == Frequency.daily:
        return is_working_day(day)
    if question.frequency == Frequency.monthly:
        if question.monthly_day is None:
            return False
        return is_working_day(day) and working_day_index(day) == question.monthly_day
    return False
