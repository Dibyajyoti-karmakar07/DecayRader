# agent/agent_runner.py

import os
import sys
import logging

import pandas as pd
import certifi
from dotenv import load_dotenv
from pymongo import MongoClient

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
    """

    print("\n" + "=" * 60)
    print(f"  CUSTOMER REPORT")
    print("=" * 60)
    print(f"  Customer ID    : {customer.get('customer_id')}")
    print(f"  Company        : {customer.get('company_name')}")
    print(f"  City           : {customer.get('city')}")
    print(f"  Tier           : {customer.get('tier')}")
    print(f"  Account Mgr    : {customer.get('account_manager')}")
    print(f"  Risk Score     : {customer.get('risk_score'):.2f}")
    print(f"  Risk Label     : {customer.get('risk_label')}")
    print("-" * 60)
    print(f"  Decay Summary  : {gemini_result.get('decay_summary')}")
    print(f"  Priority       : {gemini_result.get('priority_reason')}")
    print(f"  Likely Reason  : {gemini_result.get('likely_reason')}")
    print("-" * 60)
    print(f"  Primary Action : {gemini_result.get('primary_action')}")
    print(f"  Secondary      : {gemini_result.get('secondary_action')}")
    print(f"  Urgency        : {gemini_result.get('urgency')}")
    print("-" * 60)
    print(f"  Outreach Msg   :")
    print(f"  {gemini_result.get('outreach_message')}")
    print("=" * 60)


# =========================================================
# CONFIRMATION PROMPT
# =========================================================

def ask_confirmation(customer: dict) -> str:
    """
    Asks the user to approve, skip, or quit for each customer.
    Returns 'yes', 'skip', or 'quit'.
    """

    while True:

        answer = input(
            f"\n  Approve intervention for "
            f"{customer.get('company_name')}? "
            f"(yes / skip / quit): "
        ).strip().lower()

        if answer in ["yes", "skip", "quit"]:
            return answer

        print("  Please type yes, skip, or quit.")


# =========================================================
# MAIN AGENT LOOP
# =========================================================

def main():

    logger.info("DecayRader Agent Runner V2 starting...")

    # Setup connections
    db            = connect_to_mongo()
    gemini_client = setup_gemini_client()

    # Load data
    combined_df   = load_data(db)
    risky_df      = get_risky_customers(combined_df)

    # Counters
    approved = 0
    skipped  = 0

    # Agent loop
    for _, customer in risky_df.iterrows():

        customer    = customer.to_dict()
        customer_id = customer.get("customer_id")

        print(f"\n  Processing {customer_id} — "
              f"{customer.get('company_name')}...")

        # Skip if already processed
        if already_processed(db, customer_id):
            logger.info(
                f"{customer_id} already has an approved "
                f"intervention — skipping"
            )
            skipped += 1
            continue

        # Call Gemini
        gemini_result = call_gemini(gemini_client, customer)

        if gemini_result is None:
            logger.error(
                f"Gemini failed for {customer_id} — skipping"
            )
            skipped += 1
            continue

        # Show report
        display_report(customer, gemini_result)

        # Ask for confirmation
        decision = ask_confirmation(customer)

        if decision == "quit":
            logger.info("User quit the agent loop.")
            break

        elif decision == "skip":
            logger.info(f"Skipped {customer_id}")
            skipped += 1
            continue

        elif decision == "yes":
            success = save_intervention(db, customer, gemini_result)

            if success:
                print(f"\n  ✅ Intervention saved for "
                      f"{customer.get('company_name')}")
                approved += 1
            else:
                print(f"\n  ❌ Failed to save intervention "
                      f"for {customer.get('company_name')}")

    # Final summary
    print("\n" + "=" * 60)
    print(f"  AGENT RUN COMPLETE")
    print(f"  Approved : {approved}")
    print(f"  Skipped  : {skipped}")
    print("=" * 60)

    logger.info("DecayRader Agent Runner V2 finished.")


if __name__ == "__main__":
    main()