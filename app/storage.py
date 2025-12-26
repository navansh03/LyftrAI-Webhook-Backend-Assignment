import sqlite3
from typing import Optional

from app.config import get_config


def _get_connection() -> sqlite3.Connection:
    """Get a new database connection."""
    config = get_config()
    db_path = config.get_database_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def insert_message(message: dict) -> bool:
    """
    Insert a message into the messages table.

    Args:
        message: Dict with keys: message_id, from_msisdn, to_msisdn, ts, text, created_at

    Returns:
        True if inserted (new message), False if duplicate (message_id exists)

    Raises:
        sqlite3.Error for any other database error
    """
    conn = _get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO messages (message_id, from_msisdn, to_msisdn, ts, text, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                message["message_id"],
                message["from_msisdn"],
                message["to_msisdn"],
                message["ts"],
                message.get("text"),
                message["created_at"],
            ),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Duplicate message_id (PRIMARY KEY violation)
        return False
    finally:
        conn.close()


def list_messages(
    limit: int,
    offset: int,
    from_msisdn: Optional[str] = None,
    since: Optional[str] = None,
    q: Optional[str] = None,
) -> tuple[list[dict], int]:
    """
    List messages with optional filters and pagination.

    Args:
        limit: Maximum number of results to return
        offset: Number of results to skip
        from_msisdn: Filter by exact sender match
        since: Filter by ts >= since
        q: Filter by case-insensitive substring match on text

    Returns:
        Tuple of (list of message dicts, total count ignoring limit/offset)
    """
    conn = _get_connection()
    try:
        cursor = conn.cursor()

        # Build WHERE clause
        conditions = []
        params = []

        if from_msisdn is not None:
            conditions.append("from_msisdn = ?")
            params.append(from_msisdn)

        if since:
            conditions.append("ts >= ?")
            params.append(since)

        if q:
            conditions.append("text IS NOT NULL AND LOWER(text) LIKE LOWER(?)")
            params.append(f"%{q}%")

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        # Get total count
        count_query = f"SELECT COUNT(*) FROM messages {where_clause}"
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]

        # Get paginated data
        data_query = f"""
            SELECT message_id, from_msisdn, to_msisdn, ts, text, created_at
            FROM messages
            {where_clause}
            ORDER BY ts ASC, message_id ASC
            LIMIT ? OFFSET ?
        """
        cursor.execute(data_query, params + [limit, offset])
        rows = cursor.fetchall()

        # Convert rows to dicts
        data = [dict(row) for row in rows]

        return data, total
    finally:
        conn.close()


def get_stats() -> dict:
    """
    Get statistics about stored messages.

    Returns:
        Dict with:
        - total_messages: int
        - senders_count: int (unique senders)
        - messages_per_sender: list of {"from_msisdn": str, "count": int} (top 10)
        - first_message_ts: str or None
        - last_message_ts: str or None
    """
    conn = _get_connection()
    try:
        cursor = conn.cursor()

        # Total messages
        cursor.execute("SELECT COUNT(*) FROM messages")
        total_messages = cursor.fetchone()[0]

        # Unique senders count
        cursor.execute("SELECT COUNT(DISTINCT from_msisdn) FROM messages")
        senders_count = cursor.fetchone()[0]

        # Top 10 senders by message count
        cursor.execute(
            """
            SELECT from_msisdn, COUNT(*) as count
            FROM messages
            GROUP BY from_msisdn
            ORDER BY count DESC
            LIMIT 10
        """
        )
        messages_per_sender = [
            {"from": row["from_msisdn"], "count": row["count"]}
            for row in cursor.fetchall()
        ]

        # First and last message timestamps
        cursor.execute("SELECT MIN(ts) FROM messages")
        first_row = cursor.fetchone()
        first_message_ts = first_row[0] if first_row else None

        cursor.execute("SELECT MAX(ts) FROM messages")
        last_row = cursor.fetchone()
        last_message_ts = last_row[0] if last_row else None

        return {
            "total_messages": total_messages,
            "senders_count": senders_count,
            "messages_per_sender": messages_per_sender,
            "first_message_ts": first_message_ts,
            "last_message_ts": last_message_ts,
        }
    finally:
        conn.close()
