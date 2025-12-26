import json
import logging
import os
from datetime import datetime, timezone
from typing import Optional


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat().replace("+00:00", "Z"),
            "level": record.levelname,
            "request_id": getattr(record, "request_id", None),
            "method": getattr(record, "method", None),
            "path": getattr(record, "path", None),
            "status": getattr(record, "status", None),
            "latency_ms": getattr(record, "latency_ms", None),
        }

        # Add optional webhook fields if present
        if hasattr(record, "message_id"):
            log_obj["message_id"] = record.message_id
        if hasattr(record, "dup"):
            log_obj["dup"] = record.dup
        if hasattr(record, "result"):
            log_obj["result"] = record.result

        return json.dumps(log_obj)


def get_logger(name: str = "lyftr_webhook") -> logging.Logger:
    """
    Returns a configured logger with JSON formatting.
    Respects LOG_LEVEL environment variable (default: INFO).
    """
    logger = logging.getLogger(name)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logger.setLevel(getattr(logging, log_level, logging.INFO))

    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)
    logger.propagate = False

    return logger


def log_request(
    logger: logging.Logger,
    request_id: str,
    method: str,
    path: str,
    status: int,
    latency_ms: float,
    message_id: Optional[str] = None,
    dup: Optional[bool] = None,
    result: Optional[str] = None,
) -> None:
    """
    Logs a single request summary with structured JSON output.

    Args:
        logger: Logger instance from get_logger()
        request_id: Unique request identifier
        method: HTTP method (GET, POST, etc.)
        path: Request path
        status: HTTP status code
        latency_ms: Request latency in milliseconds
        message_id: Webhook message ID (optional)
        dup: Whether message is a duplicate (optional)
        result: Processing result (optional)
    """
    extra = {
        "request_id": request_id,
        "method": method,
        "path": path,
        "status": status,
        "latency_ms": float(latency_ms),
    }

    if message_id is not None:
        extra["message_id"] = message_id
    if dup is not None:
        extra["dup"] = dup
    if result is not None:
        extra["result"] = result

    logger.info("", extra=extra)