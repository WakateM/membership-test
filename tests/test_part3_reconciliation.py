"""Part 3 test: reconcile one month of gateway rows, then read the run back; all money is in minor units."""
from tests.conftest import (
    MINOR_UNIT_NAMES,
    VERDICT_COLORS,
    describe_money,
    member_body,
    plan_body,
    print_detail,
    print_part_header,
    print_passed,
    print_section,
    print_table,
    report,
)

SAUDI_OCTOBER_TOTAL = 34385  # halalas: invoice 2, 29900 + 15% VAT, due 2026-10-01
BAHRAINI_OCTOBER_TOTAL = 26950  # fils: invoice 2, 24500 + 10% VAT, due 2026-10-01


def create_agreement(client, member: dict, plan: dict) -> str:
    """Return the id of a new agreement, starting 2026-09-20 with due day 1, for a new member and plan."""
    member_id = client.post("/members", json=member).json()["id"]
    client.post("/plans", json=plan)
    agreement_fields = {"member_id": member_id, "plan_id": plan["id"], "start_date": "2026-09-20", "due_day": 1}
    return client.post("/agreements", json=agreement_fields).json()["id"]


def test_reconciliation_run(client):
    print_part_header("PART 3 - Reconciling the gateway file")

    print_section("Setup")
    saudi_member = member_body(name="Noura Al Harbi", country="SA", phone="0551234567")
    saudi_agreement_id = create_agreement(client, saudi_member, plan_body())
    bahraini_member = member_body(name="Ali", country="BH", phone="36001234")
    bahraini_plan = plan_body(id="anytime-bh", country="BH", monthly=24500)  # fils
    bahraini_agreement_id = create_agreement(client, bahraini_member, bahraini_plan)
    print_detail(f"SA agreement {saudi_agreement_id}: October invoice {describe_money(SAUDI_OCTOBER_TOTAL, 'SAR')}")
    print_detail(f"BH agreement {bahraini_agreement_id}: October invoice {describe_money(BAHRAINI_OCTOBER_TOTAL, 'BHD')}")

    print_section("Run for 2026-10")
    rows = [
        {"gateway_txn_id": "T-88121", "agreement_id": saudi_agreement_id, "amount": SAUDI_OCTOBER_TOTAL,
         "currency": "SAR", "status": "SETTLED", "attempted_on": "2026-10-01"},
        {"gateway_txn_id": "T-88122", "agreement_id": bahraini_agreement_id, "amount": BAHRAINI_OCTOBER_TOTAL,
         "currency": "BHD", "status": "DECLINED", "attempted_on": "2026-10-02"},
    ]
    response = client.post("/reconciliation/runs", json={"month": "2026-10", "rows": rows})
    report(1, "POST", "/reconciliation/runs", "T-88121 SETTLED in SAR, T-88122 DECLINED in BHD", response)
    run = response.json()
    assert response.status_code == 201
    assert run == {
        "id": run["id"],
        "month": "2026-10",
        "summary": {"MATCHED": 1, "DUE_DAY_DRIFT": 0, "DOUBLE_CHARGE_RISK": 0, "MISSING_FROM_LEDGER": 0, "DECLINED": 1},
        "rows": [
            {"gateway_txn_id": "T-88121", "verdict": "MATCHED",
             "invoice": {"agreement_id": saudi_agreement_id, "invoice_no": 2}},
            {"gateway_txn_id": "T-88122", "verdict": "DECLINED", "invoice": None},
        ],
        "unmatched_invoices": [
            {"agreement_id": bahraini_agreement_id, "invoice_no": 2,
             "due_date": "2026-10-01", "total": BAHRAINI_OCTOBER_TOTAL, "currency": "BHD"},  # fils
        ],
    }

    print_detail("rows")
    row_cells = []
    row_colors = []
    for row, row_result in zip(rows, run["rows"]):
        invoice_text = f"invoice {row_result['invoice']['invoice_no']}" if row_result["invoice"] else "-"
        unit_text = f"{MINOR_UNIT_NAMES[row['currency']]} ({row['currency']})"
        row_cells.append([row["gateway_txn_id"], row["status"], str(row["amount"]), unit_text, invoice_text, row_result["verdict"]])
        row_colors.append(VERDICT_COLORS[row_result["verdict"]])
    print_table(["Txn", "Status", "Amount", "Minor unit", "Linked to", "Verdict"], row_cells, row_colors)

    print_detail("")
    print_detail("summary")
    summary_cells = [[verdict, str(count)] for verdict, count in run["summary"].items()]
    print_table(["Verdict", "Rows"], summary_cells)

    print_detail("")
    print_detail("unmatched invoices")
    unmatched_cells = []
    for invoice in run["unmatched_invoices"]:
        unit_text = f"{MINOR_UNIT_NAMES[invoice['currency']]} ({invoice['currency']})"
        unmatched_cells.append([str(invoice["invoice_no"]), invoice["due_date"], str(invoice["total"]), unit_text])
    print_table(["No", "Due date", "Total", "Minor unit"], unmatched_cells)

    print_section("Read back")
    response = client.get(f"/reconciliation/runs/{run['id']}")
    report(2, "GET", f"/reconciliation/runs/{run['id']}", "the stored run", response)
    assert response.status_code == 200
    assert response.json() == run
    print_detail("same body as the POST response")

    print_section("Rejected request")
    duplicated_rows = [rows[0], rows[0]]
    response = client.post("/reconciliation/runs", json={"month": "2026-10", "rows": duplicated_rows})
    report(3, "POST", "/reconciliation/runs", "T-88121 sent twice", response)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_ROWS"
    duplicate_entry = {"gateway_txn_id": "T-88121", "code": "DUPLICATE_TXN"}
    assert response.json()["error"]["errors"] == [duplicate_entry, duplicate_entry]
    for entry in response.json()["error"]["errors"]:
        print_detail(f"{entry['gateway_txn_id']}  {entry['code']}")

    print_passed("Part 3")
