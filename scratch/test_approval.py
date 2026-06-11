import os
import sys

# Add project root to path
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from dashboard.utils.db import connect_to_mongo
from dashboard.utils.agent_worker import approve_current, create_worker_state

def test_approval():
    print("Testing intervention approval...")
    db = connect_to_mongo()
    state = create_worker_state([{"customer_id": "TEST-001", "company_name": "Test Co", "tier": "Gold"}], 1)
    state["current_customer"] = state["customers"][0]
    state["gemini_result"] = {
        "primary_action": "Email Customer",
        "secondary_action": "Phone Call",
        "urgency": "High",
        "outreach_message": "Hello",
        "likely_reason": "Test",
        "priority_reason": "Test",
        "decay_summary": "Test",
        "model_used": "Test"
    }

    try:
        # Simulate do_approve_action check
        ws = state
        if ws is not None and db is not None:
            approve_current(ws, "Email Customer", db)
        print("Success! No NotImplementedError thrown.")
        return True
    except Exception as e:
        print(f"Failed! Exception: {e}")
        return False

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    test_approval()
