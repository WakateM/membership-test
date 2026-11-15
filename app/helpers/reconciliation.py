"""Reconciliation: link each settled gateway row to an invoice the schedule expects in the month, then give it a verdict."""
import calendar
import datetime
from collections import Counter

from app.helpers.config import AMOUNT_TOLERANCE_MINOR_UNITS
from app.helpers.invoices import build_invoices_in_range
from app.models.agreement import Agreement
from app.models.invoice import Invoice
from app.models.plan import Plan
from app.models.reconciliation import (
    VERDICTS,
    ExpectedInvoice,
    GatewayRow,
    InvoiceReference,
    ReconciliationRun,
    ReconciliationRunCreation,
    RowResult,
    Verdict,
    VerdictSummary,
)


def find_month_bounds(month: str) -> tuple[datetime.date, datetime.date]:
    """Return the first and last day of the YYYY-MM month."""
    year_text, month_text = month.split("-")
    year = int(year_text)
    month_number = int(month_text)
    days_in_month = calendar.monthrange(year, month_number)[1]
    return datetime.date(year, month_number, 1), datetime.date(year, month_number, days_in_month)


def to_expected_invoice(agreement_id: str, invoice: Invoice) -> ExpectedInvoice:
    """Return the invoice with its agreement id, keeping only the fields reconciliation uses."""
    return ExpectedInvoice(
        agreement_id=agreement_id,
        invoice_no=invoice.invoice_no,
        due_date=invoice.due_date,
        total=invoice.total,
        currency=invoice.currency,
    )


def build_expected_invoices(agreements: list[Agreement], plans: dict[str, Plan], month: str) -> list[ExpectedInvoice]:
    """Return every invoice, from every agreement, whose due date falls in the month."""
    first_day, last_day = find_month_bounds(month)
    expected_invoices = []
    for agreement in agreements:
        plan = plans[agreement.plan_id]
        invoices = build_invoices_in_range(agreement, plan, first_day, last_day)
        expected_invoices += [to_expected_invoice(agreement.id, invoice) for invoice in invoices]
    return expected_invoices


def find_invoice_key(invoice: ExpectedInvoice) -> tuple[str, int]:
    """Return the (agreement_id, invoice_no) pair that identifies the invoice."""
    return invoice.agreement_id, invoice.invoice_no


def is_candidate(row: GatewayRow, invoice: ExpectedInvoice) -> bool:
    """Return whether the invoice is the row's agreement's and its total is within the tolerance of the amount."""
    amount_difference = abs(invoice.total - row.amount)
    is_same_agreement = invoice.agreement_id == row.agreement_id
    return is_same_agreement and amount_difference <= AMOUNT_TOLERANCE_MINOR_UNITS


def pick_linked_invoice(row: GatewayRow, expected_invoices: list[ExpectedInvoice]) -> ExpectedInvoice | None:
    """Return the settled row's candidate with the earliest due date, or None for a declined row or no candidate."""
    if row.status == "DECLINED":
        return None
    candidates = [invoice for invoice in expected_invoices if is_candidate(row, invoice)]  # linked invoices still count
    if not candidates:
        return None
    return min(candidates, key=lambda invoice: (invoice.due_date, invoice.invoice_no))


def decide_verdict(row: GatewayRow, linked_invoice: ExpectedInvoice | None, linked_row_counts: Counter) -> Verdict:
    """Return the row's verdict from its status, its linked invoice, and how many settled rows share that invoice."""
    if row.status == "DECLINED":
        return "DECLINED"
    if linked_invoice is None:
        return "MISSING_FROM_LEDGER"
    if linked_row_counts[find_invoice_key(linked_invoice)] > 1:
        return "DOUBLE_CHARGE_RISK"
    if row.attempted_on == linked_invoice.due_date:
        return "MATCHED"
    return "DUE_DAY_DRIFT"


def build_row_result(row: GatewayRow, linked_invoice: ExpectedInvoice | None, linked_row_counts: Counter) -> RowResult:
    """Return the row's verdict and its linked invoice reference, or None when it has none."""
    verdict = decide_verdict(row, linked_invoice, linked_row_counts)
    invoice_reference = None
    if linked_invoice is not None:
        invoice_reference = InvoiceReference(agreement_id=linked_invoice.agreement_id, invoice_no=linked_invoice.invoice_no)
    return RowResult(gateway_txn_id=row.gateway_txn_id, verdict=verdict, invoice=invoice_reference)


def build_summary(row_results: list[RowResult]) -> VerdictSummary:
    """Return the number of rows per verdict, zeros included."""
    verdict_counts = Counter(row_result.verdict for row_result in row_results)
    return VerdictSummary(**{verdict: verdict_counts[verdict] for verdict in VERDICTS})


def reconcile_run(run_id: str, run_creation: ReconciliationRunCreation, expected_invoices: list[ExpectedInvoice]) -> ReconciliationRun:
    """Return the run's verdicts, summary, and unmatched invoices; each row is linked on its own, so row order never matters."""
    rows = run_creation.rows
    linked_invoices = [pick_linked_invoice(row, expected_invoices) for row in rows]
    linked_keys = [find_invoice_key(invoice) for invoice in linked_invoices if invoice is not None]
    linked_row_counts = Counter(linked_keys)
    row_results = [build_row_result(row, invoice, linked_row_counts) for row, invoice in zip(rows, linked_invoices)]

    unmatched_invoices = [invoice for invoice in expected_invoices if find_invoice_key(invoice) not in linked_row_counts]
    unmatched_invoices.sort(key=lambda invoice: (invoice.due_date, invoice.agreement_id, invoice.invoice_no))
    return ReconciliationRun(
        id=run_id,
        month=run_creation.month,
        summary=build_summary(row_results),
        rows=row_results,
        unmatched_invoices=unmatched_invoices,
    )
