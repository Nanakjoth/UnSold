"""Central API error type and handler.

Every error leaves the API as ``{"error": {"code", "message"}}`` with a correct
status. Stack traces, prompts, private fields, and raw model output never reach
the client (spec section 9).
"""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse

from .observability import log_event


class ApiError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


def not_found(message: str = "Not found.") -> ApiError:
    return ApiError(404, "not_found", message)


def forbidden(message: str = "You do not have access to this resource.") -> ApiError:
    return ApiError(403, "forbidden", message)


def bad_request(message: str) -> ApiError:
    return ApiError(400, "bad_request", message)


def install_error_handlers(app) -> None:
    from .auth import AuthError
    from .rate_limit import _RateLimited, rate_limit_response

    @app.exception_handler(ApiError)
    async def _api_error(_request: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @app.exception_handler(AuthError)
    async def _auth_error(_request: Request, exc: AuthError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @app.exception_handler(_RateLimited)
    async def _rate_limited(_request: Request, _exc: _RateLimited) -> JSONResponse:
        return rate_limit_response()

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        # Log the category only — never the exception text, which could contain
        # user content from a downstream library.
        log_event(
            "unhandled_error",
            path=request.url.path,
            error_type=type(exc).__name__,
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "internal_error",
                    "message": "Something went wrong on our side. Please try again.",
                }
            },
        )
