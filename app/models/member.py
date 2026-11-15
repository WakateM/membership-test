"""Pydantic models for members; they only validate and never change a value."""
from typing import Annotated

from pydantic import AfterValidator, BaseModel, StringConstraints, model_validator
from pydantic_core import PydanticCustomError

from app.helpers.config import MEMBER_NAME_MAX_LENGTH, MEMBER_NAME_MIN_LENGTH
from app.helpers.countries import CountryCode
from app.helpers.phones import (
    find_international_country,
    is_national_mobile,
    is_national_mobile_of_any_country,
)


def check_name_is_trimmed(name: str) -> str:
    """Return the name unchanged when it has no whitespace at the start or end."""
    if name != name.strip():
        raise PydanticCustomError("untrimmed_name", "name must not start or end with whitespace")
    return name


MemberName = Annotated[
    str,
    StringConstraints(min_length=MEMBER_NAME_MIN_LENGTH, max_length=MEMBER_NAME_MAX_LENGTH),
    AfterValidator(check_name_is_trimmed),
]


def invalid_phone_error() -> PydanticCustomError:
    """Return the single error raised for every rejected phone number."""
    return PydanticCustomError("invalid_phone", "invalid phone")


class MemberRegistrationRequest(BaseModel):
    """The raw POST /members body: only presence and types are checked before the endpoint cleans it."""

    name: str
    country: str
    phone: str


class MemberRegistration(BaseModel):
    """A member as submitted for registration."""

    name: MemberName
    country: CountryCode
    phone: str

    @model_validator(mode="after")
    def check_phone(self) -> "MemberRegistration":
        """Return the member unchanged when the phone is a national mobile of its country or an international mobile of any country."""
        is_national = is_national_mobile(self.phone, self.country)
        international_country = find_international_country(self.phone)
        if not is_national and international_country is None:
            raise invalid_phone_error()
        return self


class Member(MemberRegistration):
    """A stored member, as returned by lookup: the registration fields plus the generated id."""

    id: str


class MemberLookup(BaseModel):
    """A phone lookup; the country is optional and only used for national numbers."""

    phone: str
    country: CountryCode | None = None

    @model_validator(mode="after")
    def check_phone(self) -> "MemberLookup":
        """Return the lookup unchanged when the phone is international, or national in the given country (any country if none is given)."""
        international_country = find_international_country(self.phone)
        if self.country is None:
            is_national = is_national_mobile_of_any_country(self.phone)
        else:
            is_national = is_national_mobile(self.phone, self.country)
        if not is_national and international_country is None:
            raise invalid_phone_error()
        return self
