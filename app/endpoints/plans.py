"""Plan endpoints: plans are created through the API, never seeded."""
import sqlite3

from fastapi import FastAPI

from app.helpers.countries import COUNTRIES
from app.helpers.database import insert_plan
from app.helpers.errors import BusinessError
from app.models.plan import Plan, PlanCreation


def register_plan_routes(application: FastAPI, database_path: str) -> None:
    """Attach the plan endpoints to the application."""

    @application.post("/plans", status_code=201)
    def create_plan(plan_creation: PlanCreation) -> Plan:
        """Return the new plan with its currency taken from the plan's country."""
        currency = COUNTRIES[plan_creation.country].currency
        plan = Plan(**plan_creation.model_dump(), currency=currency)
        try:
            insert_plan(database_path, plan.model_dump())
        except sqlite3.IntegrityError:  # the id PRIMARY KEY decides races between writes
            raise BusinessError(409, "PLAN_EXISTS", "plan exists")
        return plan
