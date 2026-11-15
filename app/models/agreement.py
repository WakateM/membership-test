"""Pydantic models for agreements; they only validate and never change a value."""
from typing import Annotated

from pydantic import BaseModel, Field

from app.helpers.config import DUE_DAY_MAX, DUE_DAY_MIN
from app.models.types import IsoDate, StrictInteger


class AgreementCreation(BaseModel):
    """The POST /agreements body; member and plan existence are checked by the endpoint."""

    member_id: str
    plan_id: str
    start_date: IsoDate
    due_day: Annotated[StrictInteger, Field(ge=DUE_DAY_MIN, le=DUE_DAY_MAX)]


class Agreement(AgreementCreation):
    """A stored agreement, as returned: the creation fields plus the generated id."""

    id: str
