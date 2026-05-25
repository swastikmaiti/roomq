"""FastAPI application: CORS, the error handler, and route wiring.

The backend is stateless — every handler is a plain request against the DB, so
Uvicorn can run multiple workers and any worker can serve any request.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.errors import APIError
from app.routes import (
    admin,
    agenda,
    agents,
    leave,
    messages,
    rooms,
    snapshot,
    stats,
    transcript,
)

settings = get_settings()

app = FastAPI(title="Agent Meeting Room", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
    allow_credentials=False,
)


@app.exception_handler(APIError)
async def _handle_api_error(_request: Request, exc: APIError) -> JSONResponse:
    """Render every APIError as ``{"error": "<code>"}`` with its HTTP status."""
    return JSONResponse(status_code=exc.status_code, content={"error": exc.code})


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


for _module in (rooms, agents, messages, leave, agenda, transcript, snapshot, stats, admin):
    app.include_router(_module.router)
