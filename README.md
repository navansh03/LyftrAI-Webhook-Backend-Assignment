# Lyftr AI — Containerized Webhook Backend

A production-style FastAPI backend service for ingesting WhatsApp-like webhook messages with **HMAC signature verification**, **idempotent storage**, **observability**, and **analytics**.

This project is implemented strictly according to the **Lyftr AI Backend Assignment** specification.
This project is tested using the POSTMAN API testing, a building tool.

---

## 🚀 Features

- HMAC-SHA256 signature verification using raw request body
- Exactly-once message ingestion (idempotent via DB constraints)
- SQLite persistence using Docker volumes
- Pagination and filtering for stored messages
- Message-level analytics endpoint
- Health probes (liveness & readiness)
- Prometheus-style metrics endpoint
- Structured JSON logs (jq-friendly)
- Fully containerized using Docker & Docker Compose

---

## 🧱 Tech Stack

- **Python 3.11**
- **FastAPI**
- **SQLite**
- **Docker & Docker Compose**
- **Prometheus-style metrics (custom, no external libs)**

---

## 📦 How to Run

### Prerequisites
- ```Docker```
- ```Docker Compose```
### Start the service
```
export WEBHOOK_SECRET="testsecret"
make up
```

The API will be available at:
```
http://localhost:8000
```
### Stop the service
```
make down
```
## API Collection (Postman)

A ready-to-use Postman collection is available to test all endpoints:

👉  https://team-rocket-2185.postman.co/workspace/Team-Rocket-Workspace~ace5b198-f2a7-40ad-8ff3-ed54e500add9/collection/33154184-77fbfc16-2041-48f7-8237-c88f21f76670?action=share&creator=33154184

The collection includes:
- Valid & invalid webhook signature examples
- Duplicate message test
- Messages pagination & filters
- Stats endpoint

### 🔌 API Endpoints
#### Health Checks
```
GET /health/live
```
Always returns ```200``` once the app is running.
```
GET /health/ready
```
Returns ```200``` only if:

Database is reachable

```WEBHOOK_SECRET``` is set
Otherwise returns ```503```.

#### Webhook Ingestion

``` POST /webhook ```

Validates:

HMAC-SHA256 signature (```X-Signature``` header)

Payload schema & constraints

Behavior:

Invalid signature → ```401```

Invalid payload → ```422```

New message → stored, ```200```
Duplicate message → ignored, ```200```

Response:

```{ "status": "ok" }```

#### List Messages

```GET /messages```

Query parameters:

```limit``` (default: 50, max: 100)

```offset``` (default: 0)

```from``` (exact match)
```since``` (ISO-8601 timestamp)

```q``` (case-insensitive text search)

Ordering:

```ORDER BY ts ASC, message_id ASC```

#### Stats

```GET /stats```

Returns:

Total messages

Unique senders count

Top 10 senders by message count

First & last message timestamps

#### Metrics (Optional)

```GET /metrics```

Prometheus-style metrics including:

```http_requests_total```

```webhook_requests_total```

### 🧠 Design Decisions
#### HMAC Verification

Signature is computed over raw request body bytes

Constant-time comparison (```hmac.compare_digest```)

Invalid signatures never reach the database

#### Idempotency

Enforced via ```PRIMARY KEY (message_id)```

Duplicate webhook calls return success without reinserting

#### Pagination

total reflects full dataset ignoring limit / offset

Deterministic ordering ensures consistent pagination

#### Observability

One structured JSON log per request

Webhook logs include:

```message_id```

```dup```

```result```

### 🧪 Tests

Test scaffolding is included under /tests for completeness.
Behavior is primarily validated via integration-style checks used by the evaluator.

### 🐳 Project Structure
```
.
├── app/
│   ├── main.py
│   ├── config.py
│   ├── models.py
│   ├── storage.py
│   ├── logging_utils.py
│   ├── metrics.py
│   └── __init__.py
├── tests/
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── requirements.txt
└── README.md
```

### 🧪 Makefile Commands
make up     # Build and start the stack
make down   # Stop and remove containers & volumes
make logs   # Tail API logs
make test   # Placeholder (no automated tests)

### 🤖 Setup Used (AI Disclosure)

##### VS Code

##### GitHub Copilot

##### Occasional ChatGPT assistance

#### ✅ Status

Assignment complete

Evaluator-script compatible

Dockerized & production-style
