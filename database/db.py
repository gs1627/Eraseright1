
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "eraseright.db"


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS personal_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            source TEXT NOT NULL,
            data_type TEXT NOT NULL,
            data_value TEXT NOT NULL,
            status TEXT DEFAULT 'ACTIVE'
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM personal_records")
    count = cursor.fetchone()[0]

    if count == 0:
        sample_records = [
            ("C101", "Aarav Sharma", "aarav@example.com",
             "Customers DB", "Email", "aarav@example.com"),
            ("C101", "Aarav Sharma", "aarav@example.com",
             "Orders DB", "Shipping Address", "12 MG Road, Bengaluru"),
            ("C101", "Aarav Sharma", "aarav@example.com",
             "Marketing DB", "Phone", "+91-9000000001"),
            ("C102", "Priya Nair", "priya@example.com",
             "Customers DB", "Email", "priya@example.com"),
            ("C103", "Rahul Kumar", "rahul@example.com",
             "Customers DB", "Email", "rahul@example.com"),
            ("C103", "Rahul Kumar", "rahul@example.com",
             "Billing DB", "Invoice", "INV-2026-103"),
            ("C104", "Aarav Sharma", "aarav.work@example.com",
             "Support DB", "Support Ticket", "Ticket #4501")
        ]

        cursor.executemany("""
            INSERT INTO personal_records
            (customer_id, name, email, source, data_type, data_value)
            VALUES (?, ?, ?, ?, ?, ?)
        """, sample_records)

    conn.commit()
    conn.close()


def get_all_records():
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM personal_records
        WHERE status = 'ACTIVE'
    """).fetchall()
    conn.close()
    return [dict(row) for row in rows]
