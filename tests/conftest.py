"""Shared test setup: a fresh server and database per test, plus request body builders and coloured printing helpers."""
from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient

from app.helpers.countries import COUNTRIES
from app.main import create_application

MINOR_UNIT_NAMES = {country.currency: country.minor_unit for country in COUNTRIES.values()}  # SAR -> halalas
LINE_WIDTH = 78
STYLES = {  # ANSI escape codes
    "reset": "\033[0m",
    "bold": "\033[1m",
    "dim": "\033[2m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
}
VERDICT_COLORS = {
    "MATCHED": "green",
    "DUE_DAY_DRIFT": "yellow",
    "DOUBLE_CHARGE_RISK": "red",
    "MISSING_FROM_LEDGER": "red",
    "DECLINED": "yellow",
}


@pytest.fixture
def database_path(tmp_path) -> str:
    """Return a path for a throwaway database inside pytest's temporary folder."""
    return str(tmp_path / "test.sqlite3")


@pytest.fixture
def client(database_path):
    """Return a test client with the application's startup (database creation) already run."""
    application = create_application(database_path)
    with TestClient(application, raise_server_exceptions=False) as test_client:
        yield test_client


def member_body(name: str, country: str, phone: str) -> dict:
    """Return a POST /members body with the given fields."""
    return {"name": name, "country": country, "phone": phone}


def plan_body(**changes) -> dict:
    """Return the specification's POST /plans body with the given fields replaced; amounts are in minor units."""
    body = {"id": "anytime-sa", "country": "SA", "monthly": 29900, "joining_fee": 0}
    return {**body, **changes}


def paint(text: str, *style_names: str) -> str:
    """Return the text wrapped in the named ANSI styles."""
    style_codes = "".join(STYLES[style_name] for style_name in style_names)
    return f"{style_codes}{text}{STYLES['reset']}"


def minor_unit_label(currency: str) -> str:
    """Return the currency's minor unit with its currency, for example "halalas (SAR minor units)"."""
    minor_unit = MINOR_UNIT_NAMES[currency]
    return f"{minor_unit} ({currency} minor units)"


def describe_money(amount: int, currency: str) -> str:
    """Return the amount in bold, labelled with its minor unit, for example "34385 halalas (SAR minor units)"."""
    bold_amount = paint(str(amount), "bold")
    return f"{bold_amount} {minor_unit_label(currency)}"


def print_part_header(title: str) -> None:
    """Print a banner that opens a part's test."""
    rule = paint("=" * LINE_WIDTH, "cyan")
    print(f"\n\n{rule}\n{paint('  ' + title, 'bold', 'cyan')}\n{rule}")


def print_section(title: str) -> None:
    """Print a sub-heading inside a part."""
    print(f"\n{paint('-- ' + title + ' ', 'bold', 'blue')}{paint('-' * (LINE_WIDTH - len(title) - 4), 'blue')}")


def status_color(status_code: int) -> str:
    """Return the colour for the status class: green for 2xx, yellow for 4xx, red otherwise."""
    if status_code < 300:
        return "green"
    if status_code < 500:
        return "yellow"
    return "red"


def report(step_number: int, method: str, path: str, description: str, response) -> None:
    """Print one numbered request and its status, plus the error code when the response is an error."""
    response_body = response.json()
    error_code = ""
    if isinstance(response_body, dict) and "error" in response_body:
        error_code = response_body["error"]["code"]
    status_phrase = HTTPStatus(response.status_code).phrase
    color = status_color(response.status_code)
    step_label = paint(f"[{step_number}]", "bold")
    method_label = paint(method.ljust(4), "bold", "magenta")
    print(f"\n  {step_label} {method_label} {path}")
    print(f"      {paint(description, 'dim')}")
    print(f"      -> {paint(f'{response.status_code} {status_phrase}', 'bold', color)} {paint(error_code, 'bold', color)}")


def print_detail(text: str) -> None:
    """Print an indented detail line under a request."""
    print(f"         {text}")


def print_table(headers: list[str], rows: list[list[str]], row_colors: list[str | None] | None = None) -> None:
    """Print an aligned table under a request; each row may carry one colour."""
    widths = [len(header) for header in headers]
    for row in rows:
        widths = [max(width, len(cell)) for width, cell in zip(widths, row)]
    header_line = "  ".join(header.ljust(width) for header, width in zip(headers, widths))
    print_detail(paint(header_line, "bold"))
    print_detail(paint("-" * len(header_line), "dim"))
    row_colors = row_colors or [None] * len(rows)
    for row, row_color in zip(rows, row_colors):
        row_line = "  ".join(cell.ljust(width) for cell, width in zip(row, widths))  # pad before painting
        print_detail(paint(row_line, row_color) if row_color else row_line)


def print_passed(title: str) -> None:
    """Print the closing line of a part whose checks all passed."""
    print(f"\n  {paint('PASS', 'bold', 'green')} {paint(title + ': every check held', 'green')}")
