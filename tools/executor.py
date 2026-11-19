
from database.db import get_connection


def execute_approved_actions(decisions):

    results = []

    conn = get_connection()
    cursor = conn.cursor()

    try:

        for decision in decisions:

            record_id = decision["record_id"]
            action = decision["action"]
            approval = decision["approval_status"]

            # Never execute rejected, pending or retained records
            if approval != "APPROVED":
                continue

            if action == "DELETE":

                cursor.execute(
                    "SELECT id FROM personal_records WHERE id = ?",
                    (record_id,)
                )

                record = cursor.fetchone()

                if record:

                    cursor.execute(
                        "DELETE FROM personal_records WHERE id = ?",
                        (record_id,)
                    )

                    results.append({
                        "record_id": record_id,
                        "action": "DELETE",
                        "status": "SUCCESS",
                        "message": "Record successfully deleted."
                    })

                else:

                    results.append({
                        "record_id": record_id,
                        "action": "DELETE",
                        "status": "NOT FOUND",
                        "message": "Record does not exist."
                    })

            elif action == "ANONYMIZE":

                cursor.execute(
                    """
                    UPDATE personal_records
                    SET name = ?,
                        email = ?,
                        customer_id = ?,
                        data_value = ?
                    WHERE id = ?
                    """,
                    (
                        "ANONYMIZED",
                        f"anonymous_{record_id}@example.invalid",
                        f"ANON-{record_id}",
                        "ANONYMIZED",
                        record_id
                    )
                )

                if cursor.rowcount > 0:

                    results.append({
                        "record_id": record_id,
                        "action": "ANONYMIZE",
                        "status": "SUCCESS",
                        "message": "Record successfully anonymized."
                    })

                else:

                    results.append({
                        "record_id": record_id,
                        "action": "ANONYMIZE",
                        "status": "NOT FOUND",
                        "message": "Record does not exist."
                    })

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

    return results


def verify_execution(results):

    conn = get_connection()
    cursor = conn.cursor()

    verification = []

    try:

        for result in results:

            record_id = result["record_id"]

            cursor.execute(
                "SELECT id, name, email, customer_id, data_value "
                "FROM personal_records WHERE id = ?",
                (record_id,)
            )

            record = cursor.fetchone()

            if result["action"] == "DELETE":

                verified = record is None

            elif result["action"] == "ANONYMIZE":

                verified = (
                    record is not None
                    and record["name"] == "ANONYMIZED"
                    and record["email"] ==
                    f"anonymous_{record_id}@example.invalid"
                    and record["customer_id"] == f"ANON-{record_id}"
                    and record["data_value"] == "ANONYMIZED"
                )

            else:
                verified = False

            verification.append({
                "record_id": record_id,
                "action": result["action"],
                "verification": (
                    "VERIFIED" if verified else "FAILED"
                )
            })

    finally:
        conn.close()

    return verification
