
from pathlib import Path
import re

POLICY_PATH = Path(__file__).resolve().parent / "policies.txt"


def retrieve_policy(data_type):

    if not POLICY_PATH.exists():
        return "Policy file missing. Human review required."

    text = POLICY_PATH.read_text(encoding="utf-8")

    sections = re.split(
        r"(?=POLICY\s+\d+:)",
        text,
        flags=re.IGNORECASE
    )

    policy_map = {
        "Email": ["POLICY 1"],
        "Phone": ["POLICY 1"],
        "Shipping Address": ["POLICY 2"],
        "Invoice": ["POLICY 3"],
        "Support Ticket": ["POLICY 4"]
    }

    required = policy_map.get(data_type, [])

    matched = []

    for section in sections:
        for policy_id in required:
            if section.upper().startswith(policy_id):
                matched.append(section.strip())

    for section in sections:
        heading = section.strip().upper()

        if heading.startswith("POLICY 5") or heading.startswith("POLICY 6"):
            matched.append(section.strip())

    if matched:
        return "\n\n".join(matched)

    return "No matching policy found. Human review required."
