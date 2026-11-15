"""Pydantic models for plans; they only validate and never change a value."""
from typing import Annotated

from pydantic import BaseModel, Field

from app.helpers.countries import CountryCode
from app.models.types import StrictInteger


class PlanCreation(BaseModel):
    """The POST /plans body; amounts are in minor units, before VAT."""

    id: str
    country: CountryCode
    monthly: Annotated[StrictInteger, Field(gt=0)]
    joining_fee: Annotated[StrictInteger, Field(ge=0)]


class Plan(PlanCreation):
    """A stored plan, as returned: the creation fields plus the country's currency."""

    currency: str
