
import os
import json
from langchain_groq import ChatGroq


def get_llm():
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError("GROQ_API_KEY is missing from environment variables.")

    return ChatGroq(
        model="openai/gpt-oss-20b",
        temperature=0
    )


def review_decisions(records, decisions, policy_evidence=None):
    """
    Independently reviews proposed privacy actions.

    The review agent can flag risks but cannot approve
    or execute any destructive action.
    """

    if not decisions:
        return {
            "status": "REVIEW_REQUIRED",
            "summary": "No decisions were provided for review.",
            "issues": ["Decision list is empty."],
            "recommendations": []
        }

    llm = get_llm()

    prompt = f"""
You are EraseRight's independent Privacy Review Agent.

Your job is to critically review the proposed decisions made
by another AI agent.

Check:
1. Whether the identity match is sufficiently reliable.
2. Whether the proposed action is supported by the available evidence.
3. Whether deletion could affect legally required records.
4. Whether anonymization or retention should be considered.
5. Whether any decision requires human review.
6. Whether the explanation is consistent with the evidence.

IMPORTANT:
- Never approve or execute a deletion.
- Never assume that missing policy evidence means deletion is allowed.
- Flag uncertain or unsupported decisions.
- Human approval is mandatory before execution.

RECORDS:
{json.dumps(records, default=str, indent=2)}

PROPOSED DECISIONS:
{json.dumps(decisions, default=str, indent=2)}

POLICY EVIDENCE:
{json.dumps(policy_evidence or [], default=str, indent=2)}

Return ONLY valid JSON in this format:
{{
    "status": "PASSED or REVIEW_REQUIRED",
    "summary": "Short overall review",
    "issues": ["Issue 1", "Issue 2"],
    "recommendations": [
        {{
            "record_id": "record ID",
            "recommendation": "REVIEW or RETAIN or DELETE or ANONYMIZE",
            "reason": "Explanation"
        }}
    ]
}}

Use REVIEW_REQUIRED whenever important evidence is missing,
identity is uncertain, or a decision appears risky.
"""

    try:
        response = llm.invoke(prompt)
        content = response.content.strip()

        if content.startswith("```"):
            content = content.split("\n", 1)[1]
            content = content.rsplit("```", 1)[0].strip()

        result = json.loads(content)

        if result.get("status") not in ["PASSED", "REVIEW_REQUIRED"]:
            raise ValueError("Invalid review status.")

        result["status"] = (
            "REVIEW_REQUIRED"
            if result["status"] != "PASSED"
            else "PASSED"
        )

        return result

    except Exception as error:
        return {
            "status": "REVIEW_REQUIRED",
            "summary": "Automated review could not be completed safely.",
            "issues": [str(error)],
            "recommendations": []
        }
