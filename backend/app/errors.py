import logging
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from .db import get_conn, log_event

log = logging.getLogger(__name__)


class AppError(Exception):
    """Expected error with a code the frontend can turn into a friendly message."""
    def __init__(self, status: int, code: str, message: str):
        self.status, self.code, self.message = status, code, message


def install_handlers(app: FastAPI):
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError):
        return JSONResponse(status_code=exc.status, content={"error": {"code": exc.code, "message": exc.message}})

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError):
        fields = [".".join(str(x) for x in e["loc"][1:]) for e in exc.errors()]
        return JSONResponse(status_code=422, content={"error": {
            "code": "validation_error", "message": "Please check the information you entered.",
            "fields": fields}})

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception):
        log.exception("Unhandled error on %s", request.url.path)
        try:
            with get_conn() as conn:
                log_event(conn, "error", "api", f"{request.method} {request.url.path}", repr(exc)[:500])
        except Exception:
            pass
        return JSONResponse(status_code=500, content={"error": {"code": "internal_error",
                            "message": "Something went wrong. Please try again."}})
