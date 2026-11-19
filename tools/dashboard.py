
import json

from database.db import get_connection


def get_dashboard_metrics():

    conn = get_connection()

    try:
        rows = conn.execute("""
            SELECT
                decisions,
                execution_results,
                verification_results
            FROM audit_logs
        """).fetchall()
    finally:
        conn.close()

    metrics = {
        "total_requests": len(rows),
        "total_records_reviewed": 0,
        "approved_actions": 0,
        "rejected_actions": 0,
        "pending_actions": 0,
        "successful_deletions": 0,
        "successful_anonymizations": 0,
        "verified_actions": 0,
        "failed_verifications": 0
    }

    for row in rows:

        decisions = json.loads(row["decisions"] or "[]")
        execution_results = json.loads(
            row["execution_results"] or "[]"
        )
        verification_results = json.loads(
            row["verification_results"] or "[]"
        )

        metrics["total_records_reviewed"] += len(decisions)

        for decision in decisions:

            status = decision.get("approval_status", "PENDING")

            if status == "APPROVED":
                metrics["approved_actions"] += 1

            elif status == "REJECTED":
                metrics["rejected_actions"] += 1

            elif status in (
                "PENDING",
                "FLAGGED_FOR_REVIEW"
            ):
                metrics["pending_actions"] += 1

        for result in execution_results:

            if result.get("status") != "SUCCESS":
                continue

            if result.get("action") == "DELETE":
                metrics["successful_deletions"] += 1

            elif result.get("action") == "ANONYMIZE":
                metrics["successful_anonymizations"] += 1

        for result in verification_results:

            if result.get("verification") == "VERIFIED":
                metrics["verified_actions"] += 1

            elif result.get("verification") == "FAILED":
                metrics["failed_verifications"] += 1

    return metrics


def get_recent_audit_activity(limit=10):

    conn = get_connection()

    try:
        rows = conn.execute("""
            SELECT
                request_id,
                requester_name,
                customer_id,
                request_type,
                created_at,
                decisions,
                execution_results,
                verification_results
            FROM audit_logs
            ORDER BY id DESC
            LIMIT ?
        """, (limit,)).fetchall()
    finally:
        conn.close()

    activity = []

    for row in rows:

        activity.append({
            "request_id": row["request_id"],
            "requester": row["requester_name"],
            "customer_id": row["customer_id"],
            "request_type": row["request_type"],
            "created_at": row["created_at"],
            "decisions": json.loads(row["decisions"] or "[]"),
            "execution_results": json.loads(
                row["execution_results"] or "[]"
            ),
            "verification_results": json.loads(
                row["verification_results"] or "[]"
            )
        })

    return activity
