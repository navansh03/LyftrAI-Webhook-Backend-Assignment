import threading
from typing import Dict, Tuple


# Thread-safe counters
_lock = threading.Lock()

# http_requests_total{path, status} -> count
_http_requests: Dict[Tuple[str, int], int] = {}

# webhook_requests_total{result} -> count
_webhook_requests: Dict[str, int] = {}


def increment_http_requests(path: str, status: int) -> None:
    """Increment the http_requests_total counter for a given path and status."""
    with _lock:
        key = (path, status)
        _http_requests[key] = _http_requests.get(key, 0) + 1


def increment_webhook_requests(result: str) -> None:
    """Increment the webhook_requests_total counter for a given result."""
    with _lock:
        _webhook_requests[result] = _webhook_requests.get(result, 0) + 1


def render_metrics() -> str:
    """Render all metrics in Prometheus exposition format."""
    lines = []

    with _lock:
        # http_requests_total
        if _http_requests:
            lines.append("# HELP http_requests_total Total number of HTTP requests")
            lines.append("# TYPE http_requests_total counter")
            for (path, status), count in sorted(_http_requests.items()):
                lines.append(f'http_requests_total{{path="{path}",status="{status}"}} {count}')

        # webhook_requests_total
        if _webhook_requests:
            lines.append("# HELP webhook_requests_total Total number of webhook requests by result")
            lines.append("# TYPE webhook_requests_total counter")
            for result, count in sorted(_webhook_requests.items()):
                lines.append(f'webhook_requests_total{{result="{result}"}} {count}')

    return "\n".join(lines) + "\n" if lines else ""