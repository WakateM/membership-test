"""The invoice schedule, computed on request: due dates, proration, and VAT, all in integer minor units."""
import calendar
import datetime

from app.helpers.countries import COUNTRIES
from app.models.agreement import Agreement
from app.models.invoice import Invoice, Proration
from app.models.plan import Plan


def shift_month(year: int, month: int, month_offset: int) -> tuple[int, int]:
    """Return the (year, month) that is month_offset months after the given one (negative goes back)."""
    month_index = year * 12 + (month - 1) + month_offset
    shifted_year, shifted_month_index = divmod(month_index, 12)
    return shifted_year, shifted_month_index + 1


def due_date_in_month(year: int, month: int, due_day: int) -> datetime.date:
    """Return the due date in the month: min(due_day, days in that month)."""
    days_in_month = calendar.monthrange(year, month)[1]
    return datetime.date(year, month, min(due_day, days_in_month))


def find_next_due_date(start_date: datetime.date, due_day: int) -> datetime.date:
    """Return N, the first due date strictly after the start date."""
    due_date_in_start_month = due_date_in_month(start_date.year, start_date.month, due_day)
    if due_date_in_start_month > start_date:
        return due_date_in_start_month
    next_year, next_month = shift_month(start_date.year, start_date.month, 1)
    return due_date_in_month(next_year, next_month, due_day)


def divide_rounding_half_up(numerator: int, denominator: int) -> int:
    """Return numerator / denominator rounded half up to a whole number, using integers only (both non-negative)."""
    return (2 * numerator + denominator) // (2 * denominator)


def find_due_date(agreement: Agreement, invoice_no: int) -> datetime.date:
    """Return the invoice's due date: the start date for invoice 1, then N, then one month after another."""
    if invoice_no == 1:
        return agreement.start_date
    next_due_date = find_next_due_date(agreement.start_date, agreement.due_day)
    year, month = shift_month(next_due_date.year, next_due_date.month, invoice_no - 2)
    return due_date_in_month(year, month, agreement.due_day)


def build_first_invoice_proration(agreement: Agreement) -> Proration:
    """Return the first invoice's proration: days = N - start, cycle_days = N - P."""
    next_due_date = find_next_due_date(agreement.start_date, agreement.due_day)
    previous_year, previous_month = shift_month(next_due_date.year, next_due_date.month, -1)
    previous_due_date = due_date_in_month(previous_year, previous_month, agreement.due_day)
    days = (next_due_date - agreement.start_date).days
    cycle_days = (next_due_date - previous_due_date).days
    return Proration(days=days, cycle_days=cycle_days)


def build_invoice(agreement: Agreement, plan: Plan, invoice_no: int) -> Invoice:
    """Return the invoice at position invoice_no of the agreement's schedule."""
    if invoice_no == 1:
        kind = "FIRST"
        proration = build_first_invoice_proration(agreement)
        prorated_amount = divide_rounding_half_up(plan.monthly * proration.days, proration.cycle_days)  # rounding 1
        net = prorated_amount + plan.joining_fee
    else:
        kind = "MONTHLY"
        proration = None
        net = plan.monthly

    vat_percent = COUNTRIES[plan.country].vat_percent
    vat = divide_rounding_half_up(net * vat_percent, 100)  # rounding 2
    return Invoice(
        invoice_no=invoice_no,
        due_date=find_due_date(agreement, invoice_no),
        kind=kind,
        proration=proration,
        net=net,
        vat=vat,
        total=net + vat,
        currency=plan.currency,
    )


def build_invoices_in_range(
    agreement: Agreement, plan: Plan, from_date: datetime.date, to_date: datetime.date
) -> list[Invoice]:
    """Return the schedule's invoices due from from_date to to_date, inclusive; due dates only ever increase."""
    invoices = []
    invoice_no = 1
    due_date = find_due_date(agreement, invoice_no)
    while due_date <= to_date:
        if due_date >= from_date:
            invoices.append(build_invoice(agreement, plan, invoice_no))
        invoice_no += 1
        due_date = find_due_date(agreement, invoice_no)
    return invoices
