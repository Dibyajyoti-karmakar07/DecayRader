import os
import certifi
import logging
import numpy as np
import pandas as pd

from dotenv import load_dotenv
from pymongo import MongoClient


# =========================================================
# LOGGING CONFIG
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


# =========================================================
# LOAD ENV VARIABLES
# =========================================================

load_dotenv()

MONGO_URI = os.getenv("MONGODB_URI")

if not MONGO_URI:
    raise ValueError("MONGODB_URI not found in .env file")

# =========================================================
# CONNECT TO MONGODB
# =========================================================

def connect_to_mongodb():

    logging.info("Connecting to MongoDB Atlas...")

    try:
        client = MongoClient(
            MONGO_URI,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=5000
        )

        client.admin.command("ping")

        logging.info("Connected to MongoDB Atlas successfully!")

        return client

    except Exception as e:
        logging.error("MongoDB connection failed!")
        logging.error(e)
        raise


# =========================================================
# LOAD DATA FROM MONGODB
# =========================================================

def load_data(db):

    collections = db.list_collection_names()

    logging.info(f"Available collections: {collections}")

    required_collections = ["Orders", "Customers"]

    for collection in required_collections:
        if collection not in collections:
            raise ValueError(f"{collection} collection not found!")

    logging.info("Loading Orders collection...")
    orders_data = list(db["Orders"].find())

    logging.info("Loading Customers collection...")
    customers_data = list(db["Customers"].find())

    orders_df = pd.DataFrame(orders_data)
    customers_df = pd.DataFrame(customers_data)

    logging.info(f"Loaded {len(orders_df)} orders")
    logging.info(f"Loaded {len(customers_df)} customers")

    return orders_df, customers_df


# =========================================================
# VALIDATE ORDERS DATA
# =========================================================

def validate_orders_data(orders_df):

    required_columns = [
        "customer_id",
        "order_date",
        "order_amount",
        "products"
    ]

    for column in required_columns:
        if column not in orders_df.columns:
            raise ValueError(f"Missing required column: {column}")

    logging.info("Orders data validation successful!")


# =========================================================
# FEATURE ENGINEERING
# =========================================================

def engineer_features(orders_df):

    logging.info("Starting feature engineering...")

    # -----------------------------------------
    # CLEANING
    # -----------------------------------------

    orders_df["order_date"] = pd.to_datetime(
        orders_df["order_date"],
        errors="coerce"
    )

    orders_df = orders_df.dropna(subset=["order_date"])

    orders_df = orders_df.sort_values(
        by=["customer_id", "order_date"]
    )

    # -----------------------------------------
    # DAYS SINCE PREVIOUS ORDER
    # -----------------------------------------

    orders_df["days_since_prev_order"] = (
        orders_df
        .groupby("customer_id")["order_date"]
        .diff()
        .dt.days
    )

    # -----------------------------------------
    # SPLIT BASELINE VS RECENT
    # -----------------------------------------

    cutoff_date = pd.Timestamp("2023-10-01")

    baseline_df = orders_df[
        orders_df["order_date"] < cutoff_date
    ]

    recent_df = orders_df[
        orders_df["order_date"] >= cutoff_date
    ]

    logging.info(f"Baseline orders: {len(baseline_df)}")
    logging.info(f"Recent orders: {len(recent_df)}")

    # -----------------------------------------
    # FEATURE 1:
    # ORDER FREQUENCY CHANGE
    # -----------------------------------------

    baseline_gap = (
        baseline_df
        .groupby("customer_id")["days_since_prev_order"]
        .mean()
    )

    recent_gap = (
        recent_df
        .groupby("customer_id")["days_since_prev_order"]
        .mean()
    )

    gap_change_pct = (
        (
            (recent_gap - baseline_gap)
            /
            baseline_gap.replace(0, np.nan)
        ) * 100
    ).round(2)

    # -----------------------------------------
    # FEATURE 2:
    # AVERAGE ORDER VALUE CHANGE
    # -----------------------------------------

    baseline_spend = (
        baseline_df
        .groupby("customer_id")["order_amount"]
        .mean()
    )

    recent_spend = (
        recent_df
        .groupby("customer_id")["order_amount"]
        .mean()
    )

    aov_change_pct = (
        (
            (recent_spend - baseline_spend)
            /
            baseline_spend.replace(0, np.nan)
        ) * 100
    ).round(2)

    # -----------------------------------------
    # FEATURE 3:
    # PRODUCT DIVERSITY CHANGE
    # -----------------------------------------

    baseline_diversity = (
        baseline_df
        .groupby("customer_id")["products"]
        .apply(
            lambda x: x.apply(
                lambda p: len(p) if isinstance(p, list) else 0
            ).mean()
        )
    )

    recent_diversity = (
        recent_df
        .groupby("customer_id")["products"]
        .apply(
            lambda x: x.apply(
                lambda p: len(p) if isinstance(p, list) else 0
            ).mean()
        )
    )

    diversity_delta = (
        recent_diversity - baseline_diversity
    ).round(2)

    # -----------------------------------------
    # COMBINE FEATURES
    # -----------------------------------------

    features_df = pd.DataFrame({
        "gap_change_pct": gap_change_pct,
        "aov_change_pct": aov_change_pct,
        "diversity_delta": diversity_delta
    }).reset_index()

    features_df = features_df.fillna(0)

    logging.info("Feature engineering completed!")

    return features_df


# =========================================================
# SAVE FEATURES TO MONGODB
# =========================================================

def save_features(db, features_df):

    logging.info("Saving features to MongoDB...")

    features_records = features_df.to_dict("records")

    if len(features_records) == 0:
        logging.warning("No feature records to save!")
        return

    # Hackathon prototype approach
    db["features"].drop()

    db["features"].insert_many(features_records)

    logging.info(
        f"Saved {len(features_records)} feature records!"
    )


# =========================================================
# MAIN PIPELINE
# =========================================================

def main():

    client = connect_to_mongodb()

    # CHANGE DB NAME IF NEEDED
    db = client["DecayRader"]

    orders_df, customers_df = load_data(db)

    validate_orders_data(orders_df)

    features_df = engineer_features(orders_df)

    logging.info("Feature preview:")
    logging.info(f"\n{features_df.head(10)}")

    save_features(db, features_df)

    logging.info("Feature engineering pipeline completed successfully!")


# =========================================================
# RUN SCRIPT
# =========================================================

if __name__ == "__main__":
    main()