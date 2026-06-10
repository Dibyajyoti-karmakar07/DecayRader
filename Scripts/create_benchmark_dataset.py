import os
import json
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
        raise ValueError(
            "MONGODB_URI not found in .env"
        )

    client = MongoClient(
        mongodb_uri,
        tlsCAFile=certifi.where()
    )

    client.admin.command("ping")

    logger.info(
        "Connected to MongoDB Atlas successfully"
    )

    return client["DecayRader"]


# =========================================================
# LOAD + MERGE DATA
# =========================================================

def load_data(db):

    customers = list(
        db["Customers"].find()
    )

    risks = list(
        db["risk_scores"].find()
    )

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

    logger.info(
        f"Loaded {len(combined_df)} customers"
    )

    return combined_df


# =========================================================
# SHOW RISK DISTRIBUTION
# =========================================================

def show_distribution(combined_df):

    print("\n=== RISK LABEL DISTRIBUTION ===\n")

    print(
        combined_df["risk_label"]
        .value_counts()
    )

    print()


# =========================================================
# CREATE BENCHMARK SET
# =========================================================

def create_benchmark_dataset(combined_df):

    benchmark_df = pd.concat([
        combined_df[
            combined_df["risk_label"] == "Healthy"
        ].head(5),

        combined_df[
            combined_df["risk_label"] == "Watch"
        ].head(5),

        combined_df[
            combined_df["risk_label"] == "At Risk"
        ].head(5),

        combined_df[
            combined_df["risk_label"] == "Critical"
        ].head(5)
    ])

    benchmark_df = benchmark_df.sample(
        frac=1,
        random_state=42
    )

    benchmark_df = benchmark_df[[
        "customer_id",
        "tier",
        "risk_score",
        "risk_label",
        "aov_change_pct",
        "gap_change_pct",
        "diversity_delta"
    ]]

    return benchmark_df


# =========================================================
# SAVE JSON
# =========================================================

def save_dataset(benchmark_df):

    os.makedirs(
        "../evaluation",
        exist_ok=True
    )

    output_path = (
        "evaluation/test_customers.json"
    )

    benchmark_df.to_json(
        output_path,
        orient="records",
        indent=4
    )

    logger.info(
        f"Saved benchmark dataset to "
        f"{output_path}"
    )

    logger.info(
        f"Total benchmark customers: "
        f"{len(benchmark_df)}"
    )


# =========================================================
# MAIN
# =========================================================

def main():

    db = connect_to_mongo()

    combined_df = load_data(db)

    show_distribution(combined_df)

    benchmark_df = create_benchmark_dataset(
        combined_df
    )

    save_dataset(benchmark_df)

    print("\n=== BENCHMARK SAMPLE ===\n")

    print(
        benchmark_df[
            [
                "customer_id",
                "risk_label",
                "risk_score"
            ]
        ]
    )


if __name__ == "__main__":
    main()