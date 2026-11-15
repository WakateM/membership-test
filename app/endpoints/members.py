"""Member endpoints: the endpoint cleans the input, the model validates it."""
import re
import sqlite3

from fastapi import FastAPI, HTTPException

from app.helpers.config import PHONE_CHARACTERS_TO_REMOVE
from app.helpers.database import find_member_by_phone, insert_member
from app.helpers.errors import BusinessError
from app.helpers.ids import generate_base62_id
from app.models.member import Member, MemberLookup, MemberRegistration, MemberRegistrationRequest
from app.helpers.phones import find_phone_country, to_e164_phone

REMOVABLE_PHONE_CHARACTERS = re.compile(f"[{re.escape(PHONE_CHARACTERS_TO_REMOVE)}]")


def clean_phone(phone: str) -> str:
    """Return the phone without spaces, hyphens, and round brackets."""
    return REMOVABLE_PHONE_CHARACTERS.sub("", phone)


def register_member_routes(application: FastAPI, database_path: str) -> None:
    """Attach the member endpoints to the application."""

    @application.post("/members", status_code=201)
    def register_member(request_body: MemberRegistrationRequest) -> dict:
        """Return the newly registered member with its generated id and E.164 phone."""
        trimmed_name = request_body.name.strip()
        cleaned_phone = clean_phone(request_body.phone)
        registration = MemberRegistration(
            name=trimmed_name,
            country=request_body.country,
            phone=cleaned_phone,
        )

        # A national number is read in the member's country; an international one in its dial code's country.
        phone_country = find_phone_country(registration.phone, registration.country)
        e164_phone = to_e164_phone(registration.phone, phone_country)

        member_id = generate_base62_id()
        member = {**registration.model_dump(), "id": member_id, "phone": e164_phone}
        try:
            insert_member(database_path, member)
        except sqlite3.IntegrityError:  # the UNIQUE phone column decides races between writes
            existing_member = find_member_by_phone(database_path, e164_phone)
            details = {"existing_member_id": existing_member["id"]}
            raise BusinessError(409, "PHONE_TAKEN", "phone taken", details)
        return {"id": member_id, "name": member["name"], "country": member["country"], "phone": e164_phone}

    @application.get("/members/lookup")
    def lookup_member(phone: str, country: str | None = None) -> Member:
        """Return the member holding the phone, in any spelling."""
        lookup = MemberLookup(phone=clean_phone(phone), country=country)

        # The model has already rejected anything that is not a national or international mobile.
        phone_country = find_phone_country(lookup.phone, lookup.country)
        if phone_country is None:
            raise BusinessError(422, "PHONE_NEEDS_COUNTRY", "phone needs country")
        if lookup.country is not None and phone_country != lookup.country:
            raise BusinessError(422, "PHONE_COUNTRY_MISMATCH", "phone country mismatch")

        e164_phone = to_e164_phone(lookup.phone, phone_country)
        member_row = find_member_by_phone(database_path, e164_phone)
        if member_row is None:
            raise HTTPException(404, "member not found")
        return Member(**member_row)
