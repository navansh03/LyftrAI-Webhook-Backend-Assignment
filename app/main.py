import hmac
import hashlib
import time
import uuid
import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field, field_validator

from app.config import get_config
from app.logging_utils import get_logger, log_request
from app.models import init_db
from app import storage
from app import metrics

logger = get_logger()


class WebhookPayload(BaseModel):
    message_id: str = Field(..., min_length=1)
    from_msisdn: str = Field(..., alias="from", pattern=r"^\+\d+$")
    to: str = Field(..., pattern=r"^\+\d+$")
    ts: str
    text: Optional[str] = Field(None, max_length=4096)

    @field_validator("ts")
    @classmethod
    def validate_ts(cls, v: str) -> str:
        try:
            datetime.fromisoformat(v.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError("ts must be a valid ISO-8601 UTC timestamp")
        return v

    model_config = {"populate_by_name": True}


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
    metrics.increment_http_requests(path=request.url.path, status=response.status_code)
    # Skip logging for webhook endpoint (handled separately)
    # if request.url.path != "/webhook":
    #     log_request(
    #         logger=logger,
    #         request_id=request_id,
    #         method=request.method,
    #         path=request.url.path,
    #         status=response.status_code,
    #         latency_ms=latency_ms,
    #     )

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


@app.post("/webhook")
async def webhook(request: Request):
    start_time = time.time()
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    config = get_config()

    # 1. Read raw request body
    raw_body = await request.body()

    # 2. Validate HMAC signature
    signature_header = request.headers.get("X-Signature")
    expected_signature = hmac.new(
        config.WEBHOOK_SECRET.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    if not signature_header or not hmac.compare_digest(signature_header, expected_signature):
        latency_ms = (time.time() - start_time) * 1000
        log_request(
            logger=logger,
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status=401,
            latency_ms=latency_ms,
            result="invalid_signature",
        )
        metrics.increment_http_requests("invalid_signature", 401)
        return JSONResponse(status_code=401, content={"detail": "invalid signature"})

    # 3. Parse & validate payload (FastAPI-style 422 on failure)
    try:
        payload = WebhookPayload.model_validate_json(raw_body)
    except Exception:
        latency_ms = (time.time() - start_time) * 1000
        log_request(
            logger=logger,
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status=422,
            latency_ms=latency_ms,
            result="validation_error",
        )
        metrics.increment_http_requests("validation_error", 422)
        raise  # Let FastAPI return 422

    # 4. Prepare message for storage
    message = {
        "message_id": payload.message_id,
        "from_msisdn": payload.from_msisdn,
        "to_msisdn": payload.to,
        "ts": payload.ts,
        "text": payload.text,
        "created_at": datetime.now(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z"),
    }

    # 5. Insert message (idempotent)
    created = storage.insert_message(message)

    if created:
        result = "created"
        dup = False
    else:
        result = "duplicate"
        dup = True
    metrics.increment_webhook_requests(result)
    # 6. Log success
    latency_ms = (time.time() - start_time) * 1000
    log_request(
        logger=logger,
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        status=200,
        latency_ms=latency_ms,
        message_id=payload.message_id,
        dup=dup,
        result=result,
    )

    # 7. Return success response
    return {"status": "ok"}

@app.get("/messages")
async def get_messages(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    from_msisdn: Optional[str] = Query(default=None, alias="from"),
    since: Optional[str] = Query(default=None),
    q: Optional[str] = Query(default=None),
):
    # Fetch messages from storage
    data, total = storage.list_messages(
        limit=limit,
        offset=offset,
        from_msisdn=from_msisdn,
        since=since,
        q=q,
    )

    # Map response: from_msisdn -> "from", exclude created_at
    response_data = []
    for row in data:
        response_data.append({
            "message_id": row["message_id"],
            "from": row["from_msisdn"],
            "to": row["to_msisdn"],
            "ts": row["ts"],
            "text": row["text"],
        })

    return {
        "data": response_data,
        "total": total,
        "limit": limit,
        "offset": offset,
    }

@app.get("/stats")
async def get_stats():
    return storage.get_stats()

@app.get("/metrics")
async def get_metrics():
    return PlainTextResponse(content=metrics.render_metrics(), media_type="text/plain")