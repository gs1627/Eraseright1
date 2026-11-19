
from difflib import SequenceMatcher
from database.db import get_connection


def discover_records(name="", email="", customer_id=""):
    name = name.strip().casefold()
    email = email.strip().casefold()
    customer_id = customer_id.strip().casefold()

    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM personal_records
        WHERE status = 'ACTIVE'
    """).fetchall()
    conn.close()

    results = []

    for row in rows:
        record = dict(row)

        record_email = record["email"].strip().casefold()
        record_customer_id = record["customer_id"].strip().casefold()
        record_name = record["name"].strip().casefold()

        email_match = bool(email) and email == record_email
        customer_match = (
            bool(customer_id)
            and customer_id == record_customer_id
        )

        similarity = (
            SequenceMatcher(None, name, record_name).ratio()
            if name else 0
        )

        if email_match or customer_match:
            record["match_type"] = "Exact match"
            record["confidence"] = 1.0

        elif similarity >= 0.80:
            record["match_type"] = "Possible name match"
            record["confidence"] = round(similarity, 2)

        else:
            continue

        results.append(record)

    return results
