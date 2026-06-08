# agent/agent_runner.py

import time
import logging

import pandas as pd

from agent.gemini_client import setup_gemini_client, call_gemini
from agent.mcp_actions import connect_to_mongo, save_intervention, already_processed


# =========================================================
# LOGGING SETUP
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


# =========================================================
# CONSTANTS
# =========================================================

MAX_CUSTOMERS = 15


# =========================================================
# LOAD DATA
# =========================================================

def load_data(db):
    """
    Loads and merges Customers + risk_scores from MongoDB.
    Returns a combined DataFrame.
    """

    logger.info("Loading data from MongoDB...")

    customers = list(db["Customers"].find())
    risks     = list(db["risk_scores"].find())

    customers_df = pd.DataFrame(customers).drop(
        columns=["_id"],
        errors="ignore"
    )

    risks_df = pd.DataFrame(risks).drop(
        columns=["_id"],
        errors="ignore"
    )

    combined_df = pd.merge(
        customers_df,
        risks_df,
        on="customer_id",
        how="inner"
    )

    logger.info(f"Loaded {len(combined_df)} combined customer records")

    return combined_df


# =========================================================
# GET RISKY CUSTOMERS
# =========================================================

def get_risky_customers(combined_df):
    """
    Filters customers with risk_score > 50.
    Sorts by risk_score descending.
    Returns top MAX_CUSTOMERS.
    """

    risky_df = combined_df[
        combined_df["risk_score"] > 50
    ].copy()

    risky_df = risky_df.sort_values(
        by="risk_score",
        ascending=False
    )

    top_customers = risky_df.head(MAX_CUSTOMERS)

    logger.info(
        f"Found {len(top_customers)} risky customers to process"
    )

    return top_customers


# =========================================================
# DISPLAY REPORT
# =========================================================

def display_report(customer: dict, gemini_result: dict):
    """
    Prints the Gemini intervention report for one customer.
    Handles missing or non-numeric risk_score and missing gemini_result.
    """

    # Safely format risk_score
    risk_score = customer.get("risk_score")
    try:
        risk_score_str = f"{float(risk_score):.2f}"
    except (TypeError, ValueError):
        risk_score_str = "N/A"

    # Safely extract gemini_result fields
    if not isinstance(gemini_result, dict):
        gemini_result = {}

    decay_summary    = gemini_result.get("decay_summary",    "N/A")
    priority_reason  = gemini_result.get("priority_reason",  "N/A")
    likely_reason    = gemini_result.get("likely_reason",    "N/A")
    primary_action   = gemini_result.get("primary_action",   "N/A")
    secondary_action = gemini_result.get("secondary_action", "N/A")
    urgency          = gemini_result.get("urgency",          "N/A")
    outreach_message = gemini_result.get("outreach_message", "N/A")

    print("\n" + "=" * 60)
    print(f"  CUSTOMER REPORT")
    print("=" * 60)
    print(f"  Customer ID    : {customer.get('customer_id')}")
    print(f"  Company        : {customer.get('company_name')}")
    print(f"  City           : {customer.get('city')}")
    print(f"  Tier           : {customer.get('tier')}")
    print(f"  Account Mgr    : {customer.get('account_manager')}")
    print(f"  Risk Score     : {risk_score_str}")
    print(f"  Risk Label     : {customer.get('risk_label')}")
    print("-" * 60)
    print(f"  Decay Summary  : {decay_summary}")
    print(f"  Priority       : {priority_reason}")
    print(f"  Likely Reason  : {likely_reason}")
    print("-" * 60)
    print(f"  Primary Action : {primary_action}")
    print(f"  Secondary      : {secondary_action}")
    print(f"  Urgency        : {urgency}")
    print("-" * 60)
    print(f"  Outreach Msg   :")
    print(f"  {outreach_message}")
    print("=" * 60)

# =========================================================
# AVAILABLE ACTIONS
# =========================================================

AVAILABLE_ACTIONS = [
    "Email Customer",
    "Phone Call",
    "Video Meeting",
    "In-Person Visit",
    "CRM Follow-Up",
    "Notify Team"
]

# =========================================================
# CONFIRMATION PROMPT
# =========================================================

def ask_confirmation_with_actions(
    customer: dict,
    gemini_result: dict
) -> tuple:
    """
    Shows Gemini's recommended action and lets the user
    accept it, choose a different one, skip, or quit.

    Returns a tuple: (decision, chosen_action)
        decision      : 'yes', 'skip', or 'quit'
        chosen_action : the action string or None
    """

    recommended = gemini_result.get("primary_action", "N/A")

    while True:

        print(f"\n  Gemini recommends : {recommended}")
        print(f"  ─" * 30)
        print(f"  1. Accept recommendation  ({recommended})")
        print(f"  2. Choose different action")
        print(f"  3. Skip this customer")
        print(f"  4. Quit")

        choice = input(
            f"\n  Enter choice (1/2/3/4): "
        ).strip()

        if choice == "1":
            return ("yes", recommended)

        elif choice == "2":
            print(f"\n  Available Actions:")
            for i, action in enumerate(AVAILABLE_ACTIONS, start=1):
                print(f"  {i}. {action}")

            action_choice = input(
                f"\n  Enter choice (1-{len(AVAILABLE_ACTIONS)}): "
            ).strip()

            if action_choice.isdigit():
                index = int(action_choice) - 1
                if 0 <= index < len(AVAILABLE_ACTIONS):
                    chosen = AVAILABLE_ACTIONS[index]
                    logger.info(
                        f"User overrode action for "
                        f"{customer.get('customer_id')} "
                        f"from '{recommended}' to '{chosen}'"
                    )
                    return ("yes", chosen)

            print("  Invalid choice. Please try again.")

        elif choice == "3":
            return ("skip", None)

        elif choice == "4":
            return ("quit", None)

        else:
            print("  Please enter 1, 2, 3, or 4.")


# =========================================================
# ANONYMIZE CUSTOMER DATA
# =========================================================

def anonymize_customer(customer: dict) -> dict:
    """
    Strips personally identifiable fields before sending to Gemini.
    Only decay signals and non-identifying context are sent.
    """

    return {
        "customer_id"    : customer.get("customer_id"),
        "tier"           : customer.get("tier"),
        "risk_score"     : customer.get("risk_score"),
        "risk_label"     : customer.get("risk_label"),
        "aov_change_pct" : customer.get("aov_change_pct"),
        "gap_change_pct" : customer.get("gap_change_pct"),
        "diversity_delta": customer.get("diversity_delta")
    }


# =========================================================
# MAIN AGENT LOOP
# =========================================================

def main():

    logger.info("DecayRader Agent Runner V3 starting...")

    # Setup connections
    db            = connect_to_mongo()
    gemini_client = setup_gemini_client()

    # Load data
    combined_df   = load_data(db)
    risky_df      = get_risky_customers(combined_df)

    # Counters
    already_done  = 0
    gemini_failed = 0
    user_skipped  = 0
    approved      = 0

    # Agent loop
    for _, customer in risky_df.iterrows():

        customer    = customer.to_dict()
        customer_id = customer.get("customer_id")

        print(f"\n  Processing {customer_id} — "
              f"{customer.get('company_name')}...")

        # Skip if already processed
        if already_processed(db, customer_id):
            logger.info(
                f"{customer_id} already has a pending "
                f"intervention — skipping"
            )
            already_done += 1
            continue

        # Anonymize before sending to Gemini
        anonymous     = anonymize_customer(customer)
        gemini_result = call_gemini(gemini_client, anonymous)

        if gemini_result is None:
            logger.error(
                f"Gemini failed for {customer_id} — skipping"
            )
            gemini_failed += 1
            continue

        # Rate limit protection
        time.sleep(1)

        # Show report
        display_report(customer, gemini_result)

        # Ask for confirmation
        decision, chosen_action = ask_confirmation_with_actions(
            customer,
            gemini_result
        )

        if decision == "quit":
            logger.info("User quit the agent loop.")
            break

        elif decision == "skip":
            logger.info(f"User skipped {customer_id}")
            user_skipped += 1
            continue

        elif decision == "yes":
            # Override primary_action with user's choice
            gemini_result["primary_action"] = chosen_action

            success = save_intervention(db, customer, gemini_result)

            if success:
                print(f"\n  ✅ Intervention saved — "
                      f"{chosen_action} for "
                      f"{customer.get('company_name')}")
                approved += 1
            else:
                print(f"\n  ❌ Failed to save — check logs")

    # Final summary
    print("\n" + "=" * 60)
    print(f"  AGENT RUN COMPLETE")
    print(f"  Approved       : {approved}")
    print(f"  User Skipped   : {user_skipped}")
    print(f"  Already Done   : {already_done}")
    print(f"  Gemini Failed  : {gemini_failed}")
    print("=" * 60)

    logger.info("DecayRader Agent Runner V3 finished.")


if __name__ == "__main__":
    main()