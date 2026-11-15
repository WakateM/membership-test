"""Pydantic models for invoices; they only validate and never change a value."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic_core import PydanticCustomError

from app.helpers.config import MAX_INVOICE_RANGE_DAYS
from app.models.types import IsoDate, StrictInteger


class InvoiceRange(BaseModel):
    """The from/to query of GET /agreements/{id}/invoices; both inclusive, filtering on due_date."""

    model_config = ConfigDict(populate_by_name=True)

    from_date: IsoDate = Field(alias="from")  # "from" is a Python keyword
    to_date: IsoDate = Field(alias="to")

    @model_validator(mode="after")
    def check_range(self) -> "InvoiceRange":
        """Return the range unchanged when to is not before from and at most MAX_INVOICE_RANGE_DAYS after it."""
        range_days = (self.to_date - self.from_date).days
        if range_days < 0 or range_days > MAX_INVOICE_RANGE_DAYS:
            raise PydanticCustomError("invalid_range", "invalid range")
        return self


class Proration(BaseModel):
    """The first invoice's share of a cycle: days = N - start, cycle_days = N - P."""

    days: StrictInteger
    cycle_days: StrictInteger


class Invoice(BaseModel):
    """A computed invoice, as returned; nothing is stored."""

    invoice_no: StrictInteger
    due_date: IsoDate
    kind: Literal["FIRST", "MONTHLY"]
    proration: Proration | None
    net: StrictInteger
    vat: StrictInteger
    total: StrictInteger
    currency: str
