"""Pydantic models for reconciliation runs; they only validate and never change a value."""
from typing import Annotated, Literal

from pydantic import BaseModel, Field, ValidationInfo, model_validator
from pydantic_core import PydanticCustomError

from app.models.types import IsoDate, IsoMonth, StrictInteger

ROW_STATUSES = ("SETTLED", "DECLINED")
VERDICTS = ("MATCHED", "DUE_DAY_DRIFT", "DOUBLE_CHARGE_RISK", "MISSING_FROM_LEDGER", "DECLINED")

RowStatus = Literal[ROW_STATUSES]
Verdict = Literal[VERDICTS]


class GatewayRow(BaseModel):
    """One gateway transaction; the agreement may not exist in the store."""

    gateway_txn_id: str
    agreement_id: str
    amount: Annotated[StrictInteger, Field(gt=0)]  # minor units, VAT included
    currency: str
    status: RowStatus
    attempted_on: IsoDate


class ReconciliationRunRequest(BaseModel):
    """The POST /reconciliation/runs body: only the shape of the month and of each row is checked."""

    month: IsoMonth
    rows: list[GatewayRow]


def find_duplicate_transaction_errors(rows: list[GatewayRow]) -> list[dict]:
    """Return a DUPLICATE_TXN entry for every row whose gateway_txn_id appears more than once."""
    transaction_ids = [row.gateway_txn_id for row in rows]
    duplicated_rows = [row for row in rows if transaction_ids.count(row.gateway_txn_id) > 1]
    return [{"gateway_txn_id": row.gateway_txn_id, "code": "DUPLICATE_TXN"} for row in duplicated_rows]


def find_outside_month_errors(rows: list[GatewayRow], month: str) -> list[dict]:
    """Return a ROW_OUTSIDE_MONTH entry for every row attempted outside the month."""
    outside_rows = [row for row in rows if row.attempted_on.strftime("%Y-%m") != month]
    return [{"gateway_txn_id": row.gateway_txn_id, "code": "ROW_OUTSIDE_MONTH"} for row in outside_rows]


def find_currency_mismatch_errors(rows: list[GatewayRow], agreement_currencies: dict[str, str]) -> list[dict]:
    """Return a CURRENCY_MISMATCH entry for every row of a known agreement whose plan currency differs."""
    known_rows = [row for row in rows if row.agreement_id in agreement_currencies]
    mismatched_rows = [row for row in known_rows if row.currency != agreement_currencies[row.agreement_id]]
    return [{"gateway_txn_id": row.gateway_txn_id, "code": "CURRENCY_MISMATCH"} for row in mismatched_rows]


class ReconciliationRunCreation(ReconciliationRunRequest):
    """A run whose rows follow the rules; validate with context={"agreement_currencies": {agreement_id: currency}}."""

    @model_validator(mode="after")
    def check_rows(self, info: ValidationInfo) -> "ReconciliationRunCreation":
        """Return the run unchanged when no row is a duplicate, outside the month, or in the wrong currency."""
        agreement_currencies = info.context["agreement_currencies"]  # the endpoint reads them from the store
        row_errors = find_duplicate_transaction_errors(self.rows)
        row_errors += find_outside_month_errors(self.rows, self.month)
        row_errors += find_currency_mismatch_errors(self.rows, agreement_currencies)
        if row_errors:
            raise PydanticCustomError("invalid_rows", "invalid rows", {"errors": row_errors})
        return self


class InvoiceReference(BaseModel):
    """The invoice a row is linked to."""

    agreement_id: str
    invoice_no: StrictInteger


class RowResult(BaseModel):
    """A row's verdict, with its linked invoice or None."""

    gateway_txn_id: str
    verdict: Verdict
    invoice: InvoiceReference | None


class VerdictSummary(BaseModel):
    """The number of rows per verdict; every verdict is present, zeros included."""

    MATCHED: StrictInteger
    DUE_DAY_DRIFT: StrictInteger
    DOUBLE_CHARGE_RISK: StrictInteger
    MISSING_FROM_LEDGER: StrictInteger
    DECLINED: StrictInteger


class ExpectedInvoice(BaseModel):
    """An invoice the schedule expects in the run's month; the ones no settled row is linked to are returned."""

    agreement_id: str
    invoice_no: StrictInteger
    due_date: IsoDate
    total: StrictInteger
    currency: str


class ReconciliationRun(BaseModel):
    """A stored run, as returned by POST and GET."""

    id: str
    month: IsoMonth
    summary: VerdictSummary
    rows: list[RowResult]  # in request order
    unmatched_invoices: list[ExpectedInvoice]  # by due_date, then agreement_id, then invoice_no
