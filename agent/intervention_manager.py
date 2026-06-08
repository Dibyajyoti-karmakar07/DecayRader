# agent/intervention_manager.py

import os
import sys
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.mcp_actions import (
    connect_to_mongo,
    get_pending_interventions,
    get_completed_interventions,
    update_intervention_status,
    delete_intervention
)


# =========================================================
# LOGGING SETUP
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


# =========================================================
# DISPLAY PENDING INTERVENTIONS
# =========================================================

def display_pending(interventions: list):
    """
    Prints all pending interventions in a numbered list.
    """

    if not interventions:
        print("\n  No pending interventions found.")
        return

    print("\n" + "=" * 60)
    print("  PENDING INTERVENTIONS")
    print("=" * 60)

    for i, doc in enumerate(interventions, start=1):
        print(f"\n  [{i}] {doc.get('company_name')} "
              f"({doc.get('customer_id')})")
        print(f"      Risk Score     : {doc.get('risk_score'):.2f} "
              f"— {doc.get('risk_label')}")
        print(f"      Primary Action : {doc.get('primary_action')}")
        print(f"      Urgency        : {doc.get('urgency')}")
        print(f"      Approved On    : {doc.get('approved_at')[:10]}")
        print(f"      Follow Up By   : {doc.get('follow_up_date')[:10]}")

    print("\n" + "=" * 60)


# =========================================================
# DISPLAY COMPLETED INTERVENTIONS
# =========================================================

def display_completed(interventions: list):
    """
    Prints all completed interventions as history.
    """

    if not interventions:
        print("\n  No completed interventions yet.")
        return

    print("\n" + "=" * 60)
    print("  INTERVENTION HISTORY")
    print("=" * 60)

    for doc in interventions:
        print(f"\n  {doc.get('company_name')} "
              f"({doc.get('customer_id')})")
        print(f"      Action         : {doc.get('primary_action')}")
        print(f"      Completed On   : {doc.get('completed_at')[:10]}")
        print(f"      Note           : "
              f"{doc.get('note') or 'No note added'}")

    print("\n" + "=" * 60)


# =========================================================
# MARK AS COMPLETED
# =========================================================

def mark_completed(db, interventions: list):
    """
    Lets user pick a pending intervention, mark it complete,
    and optionally add a note.
    """

    if not interventions:
        print("\n  No pending interventions to complete.")
        return

    display_pending(interventions)

    choice = input(
        "\n  Enter number to mark as completed "
        "(or 0 to cancel): "
    ).strip()

    if not choice.isdigit():
        print("  Invalid input.")
        return

    index = int(choice) - 1

    if choice == "0":
        return

    if index < 0 or index >= len(interventions):
        print("  Invalid number.")
        return

    selected     = interventions[index]
    customer_id  = selected.get("customer_id")
    company_name = selected.get("company_name")

    print(f"\n  Marking {company_name} as completed...")

    note = input(
        f"  Add a note (optional — press Enter to skip): "
    ).strip()

    note = note if note else None

    success = update_intervention_status(
        db,
        customer_id,
        "completed",
        note=note
    )

    if success:
        print(f"\n  ✅ {company_name} marked as completed.")
        if note:
            print(f"  Note saved: {note}")
    else:
        print(f"\n  ❌ Failed to update — check logs.")


# =========================================================
# DELETE INTERVENTION
# =========================================================

def delete_pending(db, interventions: list):
    """
    Lets user pick and permanently delete a pending intervention.
    """

    if not interventions:
        print("\n  No pending interventions to delete.")
        return

    display_pending(interventions)

    choice = input(
        "\n  Enter number to delete "
        "(or 0 to cancel): "
    ).strip()

    if not choice.isdigit():
        print("  Invalid input.")
        return

    if choice == "0":
        return

    index = int(choice) - 1

    if index < 0 or index >= len(interventions):
        print("  Invalid number.")
        return

    selected     = interventions[index]
    customer_id  = selected.get("customer_id")
    company_name = selected.get("company_name")

    confirm = input(
        f"\n  Are you sure you want to delete "
        f"{company_name}? (yes/no): "
    ).strip().lower()

    if confirm != "yes":
        print("  Cancelled.")
        return

    success = delete_intervention(db, customer_id)

    if success:
        print(f"\n  ✅ Intervention for {company_name} deleted.")
    else:
        print(f"\n  ❌ Failed to delete — check logs.")


# =========================================================
# MAIN MENU
# =========================================================

def main():

    logger.info("Intervention Manager starting...")

    db = connect_to_mongo()

    while True:

        print("\n" + "=" * 60)
        print("  DECAYRADER — INTERVENTION MANAGER")
        print("=" * 60)
        print("  1. View pending interventions")
        print("  2. Mark intervention as completed")
        print("  3. View history (completed)")
        print("  4. Delete a pending intervention")
        print("  5. Exit")
        print("=" * 60)

        choice = input("\n  Enter choice (1-5): ").strip()

        if choice == "1":
            pending = get_pending_interventions(db)
            display_pending(pending)

        elif choice == "2":
            pending = get_pending_interventions(db)
            mark_completed(db, pending)

        elif choice == "3":
            completed = get_completed_interventions(db)
            display_completed(completed)

        elif choice == "4":
            pending = get_pending_interventions(db)
            delete_pending(db, pending)

        elif choice == "5":
            logger.info("Intervention Manager exiting.")
            print("\n  Goodbye.")
            break

        else:
            print("  Please enter 1, 2, 3, 4, or 5.")


if __name__ == "__main__":
    main()