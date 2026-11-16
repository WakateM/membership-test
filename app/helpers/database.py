"""SQLite setup and queries: a fresh database file is created every time the server starts."""
import sqlite3
from contextlib import closing
from pathlib import Path


def initialize_database(database_path: str, schema_statements: list[str]) -> None:
    """Delete any existing database file and create a new one with the given schema."""
    database_file = Path(database_path)
    database_file.unlink(missing_ok=True)
    database_file.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(database_file)) as connection:
        for statement in schema_statements:
            connection.execute(statement)
        connection.commit()


def execute_write(database_path: str, statement: str, parameters: dict) -> None:
    """Run one write statement in its own transaction; constraint failures raise sqlite3.IntegrityError."""
    with closing(sqlite3.connect(database_path)) as connection:
        with connection:  # commits on success, rolls back on error
            connection.execute(statement, parameters)


def fetch_one(database_path: str, query: str, parameters: tuple) -> dict | None:
    """Return the first row of the query as a dict keyed by column name, or None."""
    with closing(sqlite3.connect(database_path)) as connection:
        cursor = connection.execute(query, parameters)
        row = cursor.fetchone()
    if row is None:
        return None
    column_names = [column[0] for column in cursor.description]
    return dict(zip(column_names, row))


def fetch_all(database_path: str, query: str, parameters: tuple) -> list[dict]:
    """Return every row of the query as dicts keyed by column name."""
    with closing(sqlite3.connect(database_path)) as connection:
        cursor = connection.execute(query, parameters)
        rows = cursor.fetchall()
    column_names = [column[0] for column in cursor.description]
    return [dict(zip(column_names, row)) for row in rows]


def insert_member(database_path: str, member: dict) -> None:
    """Store the member; raises sqlite3.IntegrityError when the phone is already taken."""
    statement = "INSERT INTO members (id, name, country, phone) VALUES (:id, :name, :country, :phone)"
    execute_write(database_path, statement, member)


def find_member_by_phone(database_path: str, phone: str) -> dict | None:
    """Return the member holding the E.164 phone, or None."""
    query = "SELECT id, name, country, phone FROM members WHERE phone = ?"
    return fetch_one(database_path, query, (phone,))


def find_member_by_id(database_path: str, member_id: str) -> dict | None:
    """Return the member with the id, or None."""
    query = "SELECT id, name, country, phone FROM members WHERE id = ?"
    return fetch_one(database_path, query, (member_id,))


def insert_plan(database_path: str, plan: dict) -> None:
    """Store the plan; raises sqlite3.IntegrityError when the id is already taken."""
    statement = (
        "INSERT INTO plans (id, country, currency, monthly, joining_fee)"
        " VALUES (:id, :country, :currency, :monthly, :joining_fee)"
    )
    execute_write(database_path, statement, plan)


def find_plan_by_id(database_path: str, plan_id: str) -> dict | None:
    """Return the plan with the id, or None."""
    query = "SELECT id, country, currency, monthly, joining_fee FROM plans WHERE id = ?"
    return fetch_one(database_path, query, (plan_id,))


def insert_agreement(database_path: str, agreement: dict) -> None:
    """Store the agreement, with start_date as YYYY-MM-DD text."""
    statement = (
        "INSERT INTO agreements (id, member_id, plan_id, start_date, due_day)"
        " VALUES (:id, :member_id, :plan_id, :start_date, :due_day)"
    )
    execute_write(database_path, statement, agreement)


def find_agreement_by_id(database_path: str, agreement_id: str) -> dict | None:
    """Return the agreement with the id, or None."""
    query = "SELECT id, member_id, plan_id, start_date, due_day FROM agreements WHERE id = ?"
    return fetch_one(database_path, query, (agreement_id,))


def list_plans(database_path: str) -> list[dict]:
    """Return every plan."""
    query = "SELECT id, country, currency, monthly, joining_fee FROM plans"
    return fetch_all(database_path, query, ())


def list_agreements(database_path: str) -> list[dict]:
    """Return every agreement."""
    query = "SELECT id, member_id, plan_id, start_date, due_day FROM agreements"
    return fetch_all(database_path, query, ())


def find_agreement_currency(database_path: str, agreement_id: str) -> str | None:
    """Return the currency of the agreement's plan, or None when the agreement is unknown."""
    query = (
        "SELECT plans.currency FROM agreements"
        " JOIN plans ON plans.id = agreements.plan_id WHERE agreements.id = ?"
    )
    row = fetch_one(database_path, query, (agreement_id,))
    if row is None:
        return None
    return row["currency"]


def insert_reconciliation_run(database_path: str, run: dict) -> None:
    """Store the run with its whole response body as JSON text."""
    statement = "INSERT INTO reconciliation_runs (id, body) VALUES (:id, :body)"
    execute_write(database_path, statement, run)


def find_reconciliation_run_by_id(database_path: str, run_id: str) -> dict | None:
    """Return the run with the id, or None."""
    query = "SELECT id, body FROM reconciliation_runs WHERE id = ?"
    return fetch_one(database_path, query, (run_id,))
