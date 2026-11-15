"""Reconciliation run endpoints: a run is stored and read back by id; it never changes members or agreements."""
from fastapi import FastAPI, HTTPException

from app.helpers.database import (
    find_agreement_currency,
    find_reconciliation_run_by_id,
    insert_reconciliation_run,
    list_agreements,
    list_plans,
)
from app.helpers.ids import generate_base62_id
from app.helpers.reconciliation import build_expected_invoices, reconcile_run
from app.models.agreement import Agreement
from app.models.plan import Plan
from app.models.reconciliation import ReconciliationRun, ReconciliationRunCreation, ReconciliationRunRequest


def find_agreement_currencies(database_path: str, agreement_ids: set[str]) -> dict[str, str]:
    """Return the plan currency of each known agreement among the ids; unknown ids are left out."""
    agreement_currencies = {}
    for agreement_id in agreement_ids:
        currency = find_agreement_currency(database_path, agreement_id)
        if currency is not None:
            agreement_currencies[agreement_id] = currency
    return agreement_currencies


def register_reconciliation_routes(application: FastAPI, database_path: str) -> None:
    """Attach the reconciliation run endpoints to the application."""

    @application.post("/reconciliation/runs", status_code=201)
    def create_reconciliation_run(run_request: ReconciliationRunRequest) -> ReconciliationRun:
        """Return the new run: each row's verdict, the summary, and the month's unmatched invoices."""
        agreement_ids = {row.agreement_id for row in run_request.rows}
        agreement_currencies = find_agreement_currencies(database_path, agreement_ids)
        validation_context = {"agreement_currencies": agreement_currencies}
        request_body = run_request.model_dump()
        run_creation = ReconciliationRunCreation.model_validate(request_body, context=validation_context)  # 422 INVALID_ROWS

        agreements = [Agreement(**row) for row in list_agreements(database_path)]
        plans = {row["id"]: Plan(**row) for row in list_plans(database_path)}
        expected_invoices = build_expected_invoices(agreements, plans, run_creation.month)
        run_id = generate_base62_id()
        run = reconcile_run(run_id, run_creation, expected_invoices)
        insert_reconciliation_run(database_path, {"id": run.id, "body": run.model_dump_json()})
        return run

    @application.get("/reconciliation/runs/{run_id}")
    def get_reconciliation_run(run_id: str) -> ReconciliationRun:
        """Return the stored run with the id."""
        run_row = find_reconciliation_run_by_id(database_path, run_id)
        if run_row is None:
            raise HTTPException(404, "reconciliation run not found")
        return ReconciliationRun.model_validate_json(run_row["body"])
