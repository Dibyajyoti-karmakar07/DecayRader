
import os
import logging

import pandas as pd
import certifi
from dotenv import load_dotenv
from pymongo import MongoClient


# =========================================================
# LOGGING SETUP
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


# =========================================================
# CONNECT TO MONGODB
# =========================================================

def connect_to_mongo():

    load_dotenv()

    mongodb_uri = os.getenv("MONGODB_URI")

    if not mongodb_uri:
        logger.error("MONGODB_URI not found in .env file")
        raise SystemExit(1)

    logger.info("Connecting to MongoDB Atlas...")

    try:
        client = MongoClient(
            mongodb_uri,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=5000
        )

        client.admin.command("ping")

        logger.info("Connected to MongoDB Atlas successfully!")

        return client

    except Exception as e:
        logger.error(f"Failed to connect to MongoDB Atlas: {e}")
        raise SystemExit(1)


# =========================================================
# LOAD DATA
# =========================================================

def load_data(db):

    logger.info("Loading data from MongoDB Atlas...")

    customers_data = list(db["Customers"].find())
    risks_data = list(db["risk_scores"].find())

    customers_df = pd.DataFrame(customers_data)
    risks_df = pd.DataFrame(risks_data)

    if "_id" in customers_df.columns:
        customers_df = customers_df.drop(columns=["_id"])

    if "_id" in risks_df.columns:
        risks_df = risks_df.drop(columns=["_id"])

    logger.info(
        f"Loaded {len(customers_df)} customers and "
        f"{len(risks_df)} risk records"
    )

    return customers_df, risks_df


# =========================================================
# COMBINE CUSTOMER DATA
# =========================================================

def combine_customer_data(customers_df, risks_df):

    logger.info("Combining customer profile and risk data...")

    combined_df = pd.merge(
        customers_df,
        risks_df,
        on="customer_id",
        how="inner"
    )

    logger.info(
        f"Successfully combined {len(combined_df)} customer records"
    )

    return combined_df


# =========================================================
# FILTER RISKY CUSTOMERS
# =========================================================

def get_risky_customers(combined_df):

    logger.info("Filtering risky customers...")

    risky_df = combined_df[
        combined_df["risk_score"] > 50
    ].copy()

    risky_df = risky_df.sort_values(
        by="risk_score",
        ascending=False
    )

    logger.info(
        f"Found {len(risky_df)} risky customers"
    )

    return risky_df


# =========================================================
# DISPLAY INVESTIGATIONS
# =========================================================

def display_investigations(risky_df):

    logger.info("Displaying customer investigations...")

    for _, customer in risky_df.iterrows():

        print("\n" + "=" * 70)

        print(
            f"Company Name  : "
            f"{customer.get('company_name', 'N/A')}"
        )

        print(
            f"Customer ID   : "
            f"{customer['customer_id']}"
        )

        print(
            f"Tier          : "
            f"{customer.get('tier', 'N/A')}"
        )

        print(
            f"City          : "
            f"{customer.get('city', 'N/A')}"
        )

        print(
            f"Account Mgr   : "
            f"{customer.get('account_manager', 'N/A')}"
        )

        print("-" * 70)

        print(
            f"Risk Score    : "
            f"{customer['risk_score']:.2f}"
        )

        print(
            f"Risk Label    : "
            f"{customer['risk_label']}"
        )

        print(
            f"AOV Change    : "
            f"{customer['aov_change_pct']:.2f}%"
        )

        print(
            f"Gap Change    : "
            f"{customer['gap_change_pct']:.2f}%"
        )

        print(
            f"Diversity Δ   : "
            f"{customer['diversity_delta']:.2f}"
        )

        print("=" * 70)


# =========================================================
# MAIN
# =========================================================

def main():

    client = connect_to_mongo()

    db = client["DecayRader"]

    customers_df, risks_df = load_data(db)

    combined_df = combine_customer_data(
        customers_df,
        risks_df
    )

    risky_df = get_risky_customers(
        combined_df
    )

    display_investigations(
        risky_df
    )

    logger.info(
        "Agent Runner V1 completed successfully!"
    )


if __name__ == "__main__":
    main()



























































