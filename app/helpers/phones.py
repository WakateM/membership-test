"""Mobile number shapes per country, built from each Country's national and E.164 masks."""
import re

from app.helpers.countries import COUNTRIES
from app.models.country import Country


def split_mobile_mask(mask: str) -> tuple[str, int]:
    """Return the fixed leading characters and the count of free digits, e.g. "05X XXX XXXX" -> ("05", 8)."""
    compact_mask = mask.replace(" ", "")
    fixed_part = compact_mask.rstrip("X")
    free_digit_count = len(compact_mask) - len(fixed_part)
    return fixed_part, free_digit_count


def build_national_pattern(country: Country) -> re.Pattern:
    """Return the pattern of the country's national mobile, capturing the free digits."""
    fixed_part, free_digit_count = split_mobile_mask(country.national_mobile)
    return re.compile(f"{re.escape(fixed_part)}([0-9]{{{free_digit_count}}})")


def build_international_pattern(country: Country) -> re.Pattern:
    """Return the pattern of the country's E.164 mobile with the + optional, capturing the free digits."""
    fixed_part, free_digit_count = split_mobile_mask(country.e164_mobile)
    fixed_digits = fixed_part.removeprefix("+")
    return re.compile(rf"\+?{re.escape(fixed_digits)}([0-9]{{{free_digit_count}}})")


NATIONAL_PATTERNS = {code: build_national_pattern(country) for code, country in COUNTRIES.items()}
INTERNATIONAL_PATTERNS = {code: build_international_pattern(country) for code, country in COUNTRIES.items()}


def is_national_mobile(phone: str, country: str) -> bool:
    """Return True when the phone is a national mobile number of the given country."""
    national_pattern = NATIONAL_PATTERNS[country]
    return national_pattern.fullmatch(phone) is not None


def is_national_mobile_of_any_country(phone: str) -> bool:
    """Return True when the phone is a national mobile number of at least one allowed country."""
    return any(national_pattern.fullmatch(phone) for national_pattern in NATIONAL_PATTERNS.values())


def find_international_country(phone: str) -> str | None:
    """Return the country whose international mobile shape the phone matches, or None."""
    for country, international_pattern in INTERNATIONAL_PATTERNS.items():
        if international_pattern.fullmatch(phone) is not None:
            return country
    return None


def find_phone_country(phone: str, country: str | None) -> str | None:
    """Return the phone's country: the given country when the phone is its national mobile, else the dial code's country, else None."""
    if country is not None and is_national_mobile(phone, country):
        return country
    return find_international_country(phone)


def to_e164_phone(phone: str, country: str) -> str:
    """Return the phone in the country's E.164 form, the one spelling stored and compared."""
    phone_match = INTERNATIONAL_PATTERNS[country].fullmatch(phone) or NATIONAL_PATTERNS[country].fullmatch(phone)
    free_digits = phone_match.group(1)
    e164_fixed_part, _ = split_mobile_mask(COUNTRIES[country].e164_mobile)
    return f"{e164_fixed_part}{free_digits}"
