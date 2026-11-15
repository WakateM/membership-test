"""Part 2 test: create a plan and an agreement, then read the agreement's invoice schedule; all money is in minor units."""
from tests.conftest import (
    describe_money,
    member_body,
    minor_unit_label,
    plan_body,
    print_detail,
    print_part_header,
    print_passed,
    print_section,
    print_table,
    report,
)


def test_plan_agreement_and_invoice_schedule(client):
    print_part_header("PART 2 - Plans, agreements and the invoice schedule")

    print_section("Plan")
    response = client.post("/plans", json=plan_body())
    report(1, "POST", "/plans", "anytime-sa, SA, monthly 29900 halalas, joining fee 0 halalas", response)
    plan = response.json()
    assert response.status_code == 201
    assert plan == {"id": "anytime-sa", "country": "SA", "currency": "SAR", "monthly": 29900, "joining_fee": 0}
    print_detail(f"currency     {plan['currency']}")
    print_detail(f"monthly      {describe_money(plan['monthly'], plan['currency'])}")
    print_detail(f"joining fee  {describe_money(plan['joining_fee'], plan['currency'])}")

    print_section("Agreement")
    member = client.post("/members", json=member_body(name="Noura Al Harbi", country="SA", phone="0551234567")).json()
    agreement_fields = {"member_id": member["id"], "plan_id": "anytime-sa", "start_date": "2026-09-20", "due_day": 1}
    response = client.post("/agreements", json=agreement_fields)
    report(2, "POST", "/agreements", "Noura on anytime-sa, start 2026-09-20, due day 1", response)
    agreement = response.json()
    assert response.status_code == 201
    assert agreement == {**agreement_fields, "id": agreement["id"]}
    print_detail(f"id  {agreement['id']}")

    print_section("Invoice schedule")
    invoices_path = f"/agreements/{agreement['id']}/invoices"
    response = client.get(invoices_path, params={"from": "2026-09-01", "to": "2026-12-31"})
    report(3, "GET", "/agreements/{id}/invoices?from=2026-09-01&to=2026-12-31", "September to December", response)
    invoices = response.json()
    assert response.status_code == 200
    print_detail(f"amounts in {minor_unit_label('SAR')}")
    table_rows = []
    for invoice in invoices:
        proration = invoice["proration"]
        proration_text = f"{proration['days']}/{proration['cycle_days']}" if proration else "-"
        table_rows.append([
            str(invoice["invoice_no"]), invoice["kind"], invoice["due_date"], proration_text,
            str(invoice["net"]), str(invoice["vat"]), str(invoice["total"]),
        ])
    print_table(["No", "Kind", "Due date", "Days", "Net", "VAT", "Total"], table_rows)
    assert [invoice["due_date"] for invoice in invoices] == ["2026-09-20", "2026-10-01", "2026-11-01", "2026-12-01"]
    assert invoices[0] == {
        "invoice_no": 1, "due_date": "2026-09-20", "kind": "FIRST",
        "proration": {"days": 11, "cycle_days": 30},
        "net": 10963, "vat": 1644, "total": 12607, "currency": "SAR",  # halalas
    }
    assert invoices[1] == {
        "invoice_no": 2, "due_date": "2026-10-01", "kind": "MONTHLY", "proration": None,
        "net": 29900, "vat": 4485, "total": 34385, "currency": "SAR",  # halalas
    }

    print_section("Rejected request")
    response = client.get(invoices_path, params={"from": "2026-12-31", "to": "2026-09-01"})
    report(4, "GET", "/agreements/{id}/invoices?from=2026-12-31&to=2026-09-01", "to before from", response)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_RANGE"

    print_passed("Part 2")
