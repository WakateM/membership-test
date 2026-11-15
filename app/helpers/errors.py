"""Exception handlers that render every error as {"error": {"code": ..., "message": ...}}."""
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.exceptions import HTTPException


VALIDATION_ERROR_CODES = {  # custom model error type -> contract code
    "invalid_phone": "INVALID_PHONE",
    "invalid_range": "INVALID_RANGE",
    "invalid_rows": "INVALID_ROWS",
}
VALIDATION_ERROR_DETAILS = {"invalid_rows": "errors"}  # custom model error type -> context field copied inside "error"


class BusinessError(Exception):
    """An error with the status and code given by a part of the contract, plus optional extra fields."""

    def __init__(self, status_code: int, code: str, message: str, details: dict | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or {}


def error_response(status_code: int, code: str, message: str, details: dict | None = None) -> JSONResponse:
    """Return a JSON response in the contract's error shape, with any extra fields inside "error"."""
    error = {"code": code, "message": message, **(details or {})}
    return JSONResponse(status_code=status_code, content={"error": error})


async def handle_validation_error(request: Request, error: RequestValidationError | ValidationError) -> JSONResponse:
    """Return 422 carrying the first validation message, coded VALIDATION unless its type has its own code."""
    first_error = error.errors()[0]
    error_type = first_error["type"]
    code = VALIDATION_ERROR_CODES.get(error_type, "VALIDATION")
    details = {}
    if error_type in VALIDATION_ERROR_DETAILS:
        detail_field = VALIDATION_ERROR_DETAILS[error_type]
        details[detail_field] = first_error["ctx"][detail_field]
    return error_response(422, code, first_error["msg"], details)


async def handle_business_error(request: Request, error: BusinessError) -> JSONResponse:
    """Return the business error with its own status, code, and extra fields."""
    return error_response(error.status_code, error.code, error.message, error.details)


async def handle_http_error(request: Request, error: HTTPException) -> JSONResponse:
    """Return the HTTP error with its status phrase as the code, for example 404 NOT_FOUND."""
    status_phrase = HTTPStatus(error.status_code).phrase
    code = status_phrase.upper().replace(" ", "_")
    return error_response(error.status_code, code, str(error.detail))


async def handle_unexpected_error(request: Request, error: Exception) -> JSONResponse:
    """Return 500 INTERNAL_ERROR so even crashes keep the error shape."""
    return error_response(500, "INTERNAL_ERROR", "internal server error")


def register_error_handlers(application: FastAPI) -> None:
    """Attach the contract's error handlers to the application."""
    application.add_exception_handler(RequestValidationError, handle_validation_error)
    application.add_exception_handler(ValidationError, handle_validation_error)  # models built inside endpoints
    application.add_exception_handler(BusinessError, handle_business_error)
    application.add_exception_handler(HTTPException, handle_http_error)
    application.add_exception_handler(Exception, handle_unexpected_error)
