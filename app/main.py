"""FastAPI server entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.helpers.config import DATABASE_PATH, SCHEMA_STATEMENTS
from app.helpers.database import initialize_database
from app.helpers.errors import register_error_handlers
from app.endpoints.agreements import register_agreement_routes
from app.endpoints.members import register_member_routes
from app.endpoints.plans import register_plan_routes
from app.endpoints.reconciliation import register_reconciliation_routes


def create_application(database_path: str) -> FastAPI:
    """Return a FastAPI application backed by a fresh SQLite database at database_path."""

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        initialize_database(database_path, SCHEMA_STATEMENTS)
        yield

    application = FastAPI(title="Server", lifespan=lifespan)
    register_error_handlers(application)
    register_member_routes(application, database_path)
    register_plan_routes(application, database_path)
    register_agreement_routes(application, database_path)
    register_reconciliation_routes(application, database_path)

    @application.get("/health")
    def get_health() -> dict:
        """Return the server status."""
        return {"status": "ok"}

    return application


application = create_application(DATABASE_PATH)
