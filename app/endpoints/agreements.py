"""Agreement endpoints: a member may hold several agreements, each on a different plan of the member's country."""
import sqlite3

from fastapi import FastAPI, HTTPException, Query

from app.helpers.database import (
    find_agreement_by_id,
    find_member_by_id,
    find_plan_by_id,
    insert_agreement,
)
from app.helpers.errors import BusinessError
from app.helpers.ids import generate_base62_id
from app.helpers.invoices import build_invoices_in_range
from app.models.agreement import Agreement, AgreementCreation
from app.models.invoice import Invoice, InvoiceRange
from app.models.plan import Plan


def register_agreement_routes(application: FastAPI, database_path: str) -> None:
    """Attach the agreement endpoints to the application."""

    @application.post("/agreements", status_code=201)
    def create_agreement(agreement_creation: AgreementCreation) -> Agreement:
        """Return the new agreement with its generated id."""
        member = find_member_by_id(database_path, agreement_creation.member_id)
        if member is None:
            raise BusinessError(422, "UNKNOWN_MEMBER", "unknown member")
        plan = find_plan_by_id(database_path, agreement_creation.plan_id)
        if plan is None:
            raise BusinessError(422, "UNKNOWN_PLAN", "unknown plan")
        if plan["country"] != member["country"]:
            raise BusinessError(422, "PLAN_COUNTRY_MISMATCH", "plan country mismatch")

        agreement_id = generate_base62_id()
        agreement = Agreement(**agreement_creation.model_dump(), id=agreement_id)
        agreement_row = agreement.model_dump(mode="json")  # json mode writes the date as YYYY-MM-DD
        try:
            insert_agreement(database_path, agreement_row)
        except sqlite3.IntegrityError:  # UNIQUE (member_id, plan_id) decides races between writes
            raise BusinessError(409, "AGREEMENT_EXISTS", "agreement exists")
        return agreement

    @application.get("/agreements/{agreement_id}")
    def get_agreement(agreement_id: str) -> Agreement:
        """Return the agreement with the id."""
        agreement_row = find_agreement_by_id(database_path, agreement_id)
        if agreement_row is None:
            raise HTTPException(404, "agreement not found")
        return Agreement(**agreement_row)

    @application.get("/agreements/{agreement_id}/invoices")
    def get_agreement_invoices(
        agreement_id: str,
        from_text: str = Query(alias="from"),
        to_text: str = Query(alias="to"),
    ) -> list[Invoice]:
        """Return the agreement's invoices due in the range, computed on request; nothing is stored."""
        agreement_row = find_agreement_by_id(database_path, agreement_id)
        if agreement_row is None:  # an unknown agreement wins over a malformed or invalid range
            raise HTTPException(404, "agreement not found")
        invoice_range = InvoiceRange.model_validate({"from": from_text, "to": to_text})

        agreement = Agreement(**agreement_row)
        plan_row = find_plan_by_id(database_path, agreement.plan_id)
        plan = Plan(**plan_row)
        return build_invoices_in_range(agreement, plan, invoice_range.from_date, invoice_range.to_date)
