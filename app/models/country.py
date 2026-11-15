"""Pydantic model for a country row of the countries table."""
from pydantic import BaseModel


class Country(BaseModel):
    """A supported country: identity, money, VAT, and mobile number masks (X is any digit)."""

    name: str
    code: str
    dial_code: str
    currency: str
    minor_unit: str
    minor_units_per_unit: int
    vat_percent: int
    national_mobile: str
    e164_mobile: str
