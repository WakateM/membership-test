"""The supported countries, loaded from COUNTRY_TABLE into Country models."""
from typing import Literal

from app.helpers.config import COUNTRY_TABLE
from app.models.country import Country

COUNTRIES = {row["code"]: Country(**row) for row in COUNTRY_TABLE}
COUNTRY_CODES = tuple(COUNTRIES)
CountryCode = Literal[COUNTRY_CODES]  # a tuple inside Literal[...] allows each of its values
