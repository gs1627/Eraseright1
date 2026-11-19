
import json
import uuid
from datetime import datetime, timezone

from database.db import get_connection


def initialize_audit_table():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id TEXT UNIQUE,
            requester_name TEXT,
            requester_email TEXT,
            customer_id TEXT,
            request_type TEXT,
            decisions TEXT,
            execution_results TEXT,
            verification_results TEXT,
            created_at TEXT
        )
    """)

    conn.commit()
    conn.close()


def save_audit_log(
    requester_name,
    requester_email,
    customer_id,
    request_type,
    decisions,
    execution_results,
    verification_results
):

    conn = get_connection()
    cursor = conn.cursor()

    request_id = str(uuid.uuid4())

    created_at = datetime.now(
        timezone.utc
    ).astimezone().isoformat()

    cursor.execute("""
        INSERT INTO audit_logs (
            request_id,
            requester_name,
            requester_email,
            customer_id,
            request_type,
            decisions,
            execution_results,
            verification_results,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        request_id,
        requester_name,
        requester_email,
        customer_id,
        request_type,
        json.dumps(decisions),
        json.dumps(execution_results),
        json.dumps(verification_results),
        created_at
    ))

    conn.commit()
    conn.close()

    return request_id


def get_audit_logs():

    conn = get_connection()

    rows = conn.execute("""
        SELECT * FROM audit_logs
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return [dict(row) for row in rows]
