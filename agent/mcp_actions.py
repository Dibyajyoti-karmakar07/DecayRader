# agent/mcp_actions.py

import os
import logging

from datetime import datetime, timezone, timedelta

import certifi
from dotenv import load_dotenv
from pymongo import MongoClient


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

def save_intervention(
    db,
    customer: dict,
    gemini_result: dict,
    chosen_action: str | None = None,
) -> bool:
    """
    Saves an approved intervention to the interventions collection.

    Input  : db handle, customer dict, gemini_result dict,
             chosen_action (the action the human actually selected)
    Output : True if saved successfully, False if failed
    """

    try:
        ai_primary   = gemini_result.get("primary_action")
        ai_secondary = gemini_result.get("secondary_action")

        # If user chose a different action than AI recommended,
        # primary_action = user choice, secondary = AI primary.
        # If user chose same as AI, keep AI secondary as-is.
        if chosen_action and chosen_action != ai_primary:
            final_primary   = chosen_action
            final_secondary = ai_primary
        else:
            final_primary   = ai_primary
            final_secondary = ai_secondary

        now_utc = datetime.now(timezone.utc).isoformat()

        document = {
            # Customer profile
            "customer_id"      : customer.get("customer_id"),
            "company_name"     : customer.get("company_name"),
            "city"             : customer.get("city"),
            "tier"             : customer.get("tier"),
            "account_manager"  : customer.get("account_manager"),
            "risk_score"       : customer.get("risk_score"),
            "risk_label"       : customer.get("risk_label"),

            # Gemini reasoning
            "decay_summary"    : gemini_result.get("decay_summary"),
            "priority_reason"  : gemini_result.get("priority_reason"),
            "likely_reason"    : gemini_result.get("likely_reason"),
            "outreach_message" : gemini_result.get("outreach_message"),
            "urgency"          : gemini_result.get("urgency"),
            "model_used"       : gemini_result.get("model_used"),

            # Actions — what AI suggested vs what human chose
            "ai_primary_action"  : ai_primary,
            "ai_secondary_action": ai_secondary,
            "chosen_action"      : chosen_action or ai_primary,
            "primary_action"     : final_primary,
            "secondary_action"   : final_secondary,

            # Metadata
            "status"           : "pending",
            "created_at"       : now_utc,
            "approved_at"      : now_utc,
            "follow_up_date"   : (
                datetime.now(timezone.utc) + timedelta(days=14)
            ).isoformat(),
            "completed_at"     : None,
            "note"             : None
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
    Returns True only if a PENDING intervention exists.
    Completed and cancelled interventions allow re-processing.
    """

    existing = db["interventions"].find_one({
        "customer_id": customer_id,
        "status"     : "pending"
    })

    return existing is not None


# =========================================================
# UPDATE INTERVENTION STATUS
# =========================================================

def update_intervention_status(
    db,
    customer_id: str,
    new_status: str,
    note: str = None
) -> bool:
    """
    Updates the status of an existing intervention.
    Optionally saves a completion note.
    Valid statuses: pending, completed, cancelled
    """

    try:
        update_fields = {"status": new_status}

        if new_status == "completed":
            update_fields["completed_at"] = datetime.now(
                timezone.utc
            ).isoformat()

        if note:
            update_fields["note"] = note

        db["interventions"].update_one(
            {"customer_id": customer_id},
            {"$set": update_fields}
        )

        logger.info(
            f"{customer_id} status updated to {new_status}"
        )
        return True

    except Exception as e:
        logger.error(
            f"Failed to update status for {customer_id}: {e}"
        )
        return False


# =========================================================
# DELETE INTERVENTION (SOFT DELETE)
# =========================================================

def delete_intervention(db, customer_id: str) -> bool:
    """
    Soft deletes a pending intervention by marking it cancelled.
    Document stays in MongoDB for audit trail.
    """

    try:
        result = db["interventions"].update_one(
            {
                "customer_id": customer_id,
                "status"     : "pending"
            },
            {"$set": {"status": "cancelled"}}
        )

        if result.matched_count == 0:
            logger.warning(
                f"No pending intervention found for {customer_id}"
            )
            return False

        logger.info(
            f"Intervention cancelled for {customer_id}"
        )
        return True

    except Exception as e:
        logger.error(
            f"Failed to cancel intervention for {customer_id}: {e}"
        )
        return False


# =========================================================
# GET LAST COMPLETED INTERVENTION
# =========================================================

def get_last_completed_intervention(db, customer_id: str) -> dict:
    """
    Returns the most recent completed intervention for a customer.
    Used by agent_runner to show history before processing.
    """

    result = db["interventions"].find_one(
        {
            "customer_id": customer_id,
            "status"     : "completed"
        },
        sort=[("completed_at", -1)]
    )

    return result


# =========================================================
# GET PENDING INTERVENTIONS
# =========================================================

def get_pending_interventions(db) -> list:
    """
    Returns all interventions with status = pending.
    """

    results = list(db["interventions"].find({"status": "pending"}))
    logger.info(f"Found {len(results)} pending interventions")
    return results


# =========================================================
# GET COMPLETED INTERVENTIONS
# =========================================================

def get_completed_interventions(db) -> list:
    """
    Returns all interventions with status = completed.
    """

    results = list(db["interventions"].find({"status": "completed"}))
    logger.info(f"Found {len(results)} completed interventions")
    return results


# =========================================================
# GET CANCELLED INTERVENTIONS
# =========================================================

def get_cancelled_interventions(db) -> list:
    """
    Returns all interventions with status = cancelled.
    """

    results = list(db["interventions"].find({"status": "cancelled"}))
    logger.info(f"Found {len(results)} cancelled interventions")
    return results