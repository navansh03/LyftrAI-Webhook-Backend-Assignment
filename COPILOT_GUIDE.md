# Lyftr Backend Assignment — Copilot Execution Guide

You are assisting with a production-grade FastAPI backend.
STRICT RULES:
- Follow the assignment spec exactly.
- Do NOT invent behavior.
- Do NOT add features not asked.
- Prefer clarity over cleverness.
- Use standard library where possible.
- All configuration via environment variables.
- SQLite only.

We are building step by step. Only generate code for the CURRENT STEP.

---

## STEP 1 — config.py (Environment & Startup Validation)

Task:
- Load env vars:
  - DATABASE_URL
  - LOG_LEVEL (default INFO)
  - WEBHOOK_SECRET
- If WEBHOOK_SECRET is missing or empty:
  - Raise an exception on startup OR
  - Make readiness check fail (preferred: fail fast)

Requirements:
- No hardcoded defaults for secrets
- DATABASE_URL format: sqlite:////data/app.db

Generate:
- config.py with a Config class or simple functions
- Minimal, clean, testable

Wait for confirmation before next step. and do not do anything which is not mentioned in the step.
