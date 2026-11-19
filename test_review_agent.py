
from pathlib import Path
from dotenv import load_dotenv
import json

# Load the project's .env file
project_folder = Path(__file__).resolve().parent
load_dotenv(project_folder / ".env")

from agents.review_agent import review_decisions

records = [
    {
        "id": 999,
        "customer_id": "TEST001",
        "name": "Test User",
        "email": "test@example.com",
        "source": "Test Database",
        "data_type": "Email",
        "data_value": "test@example.com",
        "status": "ACTIVE"
    }
]

decisions = [
    {
        "record_id": 999,
        "action": "DELETE",
        "reason": "The record appears to match the erasure request.",
        "approval_status": "PENDING"
    }
]

policy_evidence = [
    {
        "content": "Personal data erasure requests must be assessed against applicable retention requirements."
    }
]

print("\n🛡️ EraseRight Review Agent Test")
print("-" * 40)

try:
    result = review_decisions(
        records=records,
        decisions=decisions,
        policy_evidence=policy_evidence
    )

    print("\nReview Result:")
    print(json.dumps(result, indent=4))

    print("\nReview Status:", result.get("status"))

except Exception as error:
    print("\nTest failed:")
    print(error)
