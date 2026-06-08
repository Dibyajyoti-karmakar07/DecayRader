# agent/mcp_actions.py

import os
import sys
import logging

from datetime import datetime, timezone

import certifi
from dotenv import load_dotenv
from pymongo import MongoClient

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# =========================================================
# LOGGING SETUP
# =========================================================

logger = logging.getLogger(__name__)


# =========================================================
# CONNECT TO MONGODB
# =========================================================

def connect_to_mongo():
    """
    Loads MongoDB URI from .env and returns db handle.
    """

    load_dotenv()

    mongodb_uri = os.getenv("MONGODB_URI")

    if not mongodb_uri:
        logger.error("MONGODB_URI not found in .env file")
        raise SystemExit(1)

    try:
        client = MongoClient(
            mongodb_uri,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=5000
        )

        client.admin.command("ping")

        logger.info("Connected to MongoDB Atlas successfully")

        return client["DecayRader"]

    except Exception as e:
        logger.error(f"Failed to connect to MongoDB Atlas: {e}")
        raise SystemExit(1)


# =========================================================
# SAVE INTERVENTION
# =========================================================

def save_intervention(db, customer: dict, gemini_result: dict) -> bool:
    """
    Saves an approved intervention to the interventions collection.

    Input  : db handle, customer dict, gemini_result dict
    Output : True if saved successfully, False if failed
    """

    try:

        document = {
            # Customer profile
            "customer_id"     : customer.get("customer_id"),
            "company_name"    : customer.get("company_name"),
            "city"            : customer.get("city"),
            "tier"            : customer.get("tier"),
            "account_manager" : customer.get("account_manager"),
            "risk_score"      : customer.get("risk_score"),
            "risk_label"      : customer.get("risk_label"),

            # Gemini reasoning
            "decay_summary"   : gemini_result.get("decay_summary"),
            "priority_reason" : gemini_result.get("priority_reason"),
            "likely_reason"   : gemini_result.get("likely_reason"),
            "primary_action"  : gemini_result.get("primary_action"),
            "secondary_action": gemini_result.get("secondary_action"),
            "outreach_message": gemini_result.get("outreach_message"),
            "urgency"         : gemini_result.get("urgency"),

            # Metadata
            "status"          : "approved",
            "approved_at"     : datetime.now(timezone.utc).isoformat()
        }

        db["interventions"].insert_one(document)

        logger.info(
            f"Intervention saved for "
            f"{customer.get('customer_id')} — "
            f"{customer.get('company_name')}"
        )

        return True

    except Exception as e:
        logger.error(
            f"Failed to save intervention for "
            f"{customer.get('customer_id')}: {e}"
        )
        return False


# =========================================================
# CHECK FOR DUPLICATE
# =========================================================

def already_processed(db, customer_id: str) -> bool:
    """
    Checks if an intervention already exists for this customer.
    Prevents duplicate entries on re-runs.
    """

    existing = db["interventions"].find_one(
        {"customer_id": customer_id}
    )

    return existing is not None