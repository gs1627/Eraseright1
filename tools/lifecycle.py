
def get_request_lifecycle(
    records,
    decisions,
    execution_results,
    verification_results,
    execution_completed,
    audit_saved
):
    stages = []

    # Stage 1: Request submission
    stages.append({
        "stage": "Request Submitted",
        "status": "COMPLETED",
        "description": "Privacy request received."
    })

    # Stage 2: Discovery
    stages.append({
        "stage": "Record Discovery",
        "status": "COMPLETED" if records else "PENDING",
        "description": (
            f"{len(records)} matching records discovered."
            if records else "Waiting for matching records."
        )
    })

    # Stage 3: AI decision
    stages.append({
        "stage": "AI Decision Analysis",
        "status": "COMPLETED" if decisions else "PENDING",
        "description": (
            "Proposed actions generated."
            if decisions else "Waiting for decision analysis."
        )
    })

    # Stage 4: Human approval
    approved = sum(
        1 for d in decisions
        if d.get("approval_status") == "APPROVED"
    )

    rejected = sum(
        1 for d in decisions
        if d.get("approval_status") == "REJECTED"
    )

    retained = sum(
        1 for d in decisions
        if d.get("approval_status") == "RETENTION_CONFIRMED"
    )

    flagged = sum(
        1 for d in decisions
        if d.get("approval_status") == "FLAGGED_FOR_REVIEW"
    )

    pending = sum(
        1 for d in decisions
        if d.get("approval_status", "PENDING") == "PENDING"
    )

    resolved = approved + rejected + retained

    if not decisions or pending == len(decisions):
        approval_status = "PENDING"
    elif pending > 0 or flagged > 0:
        approval_status = "REVIEW REQUIRED" if flagged else "IN PROGRESS"
    elif resolved == len(decisions):
        approval_status = "COMPLETED"
    else:
        approval_status = "IN PROGRESS"

    stages.append({
        "stage": "Human Approval",
        "status": approval_status,
        "description": (
            f"{approved} approved, {rejected} rejected, "
            f"{retained} retention confirmed, {flagged} flagged, "
            f"{pending} pending."
        )
    })

    # Stage 5: Execution
    stages.append({
        "stage": "Action Execution",
        "status": "COMPLETED" if execution_completed else "PENDING",
        "description": (
            f"{len(execution_results)} execution results recorded."
            if execution_completed
            else "Waiting for approved actions."
        )
    })

    # Stage 6: Verification
    if verification_results:
        failed = sum(
            1 for v in verification_results
            if v.get("verification") == "FAILED"
        )

        stages.append({
            "stage": "Post-Execution Verification",
            "status": "REVIEW REQUIRED" if failed else "COMPLETED",
            "description": (
                f"{len(verification_results) - failed} verified, "
                f"{failed} failed."
            )
        })
    else:
        stages.append({
            "stage": "Post-Execution Verification",
            "status": "PENDING",
            "description": "Waiting for post-execution verification."
        })

    # Stage 7: Audit and certificate
    stages.append({
        "stage": "Audit & Certification",
        "status": "COMPLETED" if audit_saved else "PENDING",
        "description": (
            "Audit log saved and certificate available."
            if audit_saved else "Waiting for completed processing."
        )
    })

    return stages
