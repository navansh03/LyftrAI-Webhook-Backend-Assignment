import time
import uuid
import sqlite3
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.config import get_config
from app.logging_utils import get_logger, log_request
from app.models import init_db


logger = get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Fail fast if config is invalid
    get_config()

    # Ensure DB schema exists
    init_db()

    yield
    # No cleanup needed for SQLite


app = FastAPI(lifespan=lifespan)


@app.middleware("http")
async def request_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()

    request.state.request_id = request_id

    response = await call_next(request)

    latency_ms = (time.time() - start_time) * 1000

    log_request(
        logger=logger,
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        latency_ms=latency_ms,
    )

    return response


@app.get("/health/live")
async def health_live():
    return {"status": "live"}


@app.get("/health/ready")
async def health_ready():
    try:
        config = get_config()

        # Check DB reachability
        db_path = config.get_database_path()
        conn = sqlite3.connect(db_path)
        conn.close()

        return {"status": "ready"}
    except Exception:
        return JSONResponse(status_code=503, content={"status": "not_ready"})
