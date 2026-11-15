"""Field types shared by several models."""
import datetime
import re
from typing import Annotated, Any

from pydantic import BeforeValidator, Strict
from pydantic_core import PydanticCustomError

ISO_DATE_PATTERN = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
ISO_MONTH_PATTERN = re.compile(r"[0-9]{4}-(0[1-9]|1[0-2])")


def check_iso_date_text(value: Any) -> Any:
    """Return the value unchanged when it is a date or text shaped exactly YYYY-MM-DD."""
    if isinstance(value, datetime.date) and not isinstance(value, datetime.datetime):
        return value
    if isinstance(value, str) and ISO_DATE_PATTERN.fullmatch(value):
        return value
    raise PydanticCustomError("iso_date", "date must be YYYY-MM-DD")


def check_iso_month_text(value: Any) -> Any:
    """Return the value unchanged when it is text shaped exactly YYYY-MM with a month from 01 to 12."""
    if isinstance(value, str) and ISO_MONTH_PATTERN.fullmatch(value):
        return value
    raise PydanticCustomError("iso_month", "month must be YYYY-MM")


IsoMonth = Annotated[str, BeforeValidator(check_iso_month_text)]  # kept as text, e.g. "2026-10"
IsoDate = Annotated[datetime.date, BeforeValidator(check_iso_date_text)]  # works for JSON bodies and query text
StrictInteger = Annotated[int, Strict()]  # rejects "1", 1.0 and true
