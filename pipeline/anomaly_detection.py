import os
import logging

import certifi
import pandas as pd

from dotenv import load_dotenv
from pymongo import MongoClient
from sklearn.ensemble import IsolationForest

# =========================
# CONFIGURATION
# =========================

DATABASE_NAME = "DecayRader"
FEATURES_COLLECTION = "features"
RISK_COLLECTION = "risk_scores"

MODEL_FEATURES = [
    "gap_change_pct",
    "aov_change_pct",
    "diversity_delta"
]

CONTAMINATION_RATE = 0.15

# Rule-based score weights
AOV_WEIGHT = 0.50
GAP_WEIGHT = 0.30
DIVERSITY_WEIGHT = 10

# Hybrid scoring weights
BUSINESS_SCORE_WEIGHT = 0.70
ANOMALY_SCORE_WEIGHT = 0.30

# =========================
# LOGGING SETUP
# =========================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


def get_risk_label(score: float) -> str:
    if score <= 30:
        return "Healthy"
    elif score <= 50:
        return "Watch"
    elif score <= 75:
        return "At Risk"
    else:
        return "Critical"


def connect_to_mongo():
    load_dotenv()
    mongodb_uri = os.getenv("MONGODB_URI")

    if not mongodb_uri:
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


def load_features(db):
    logger.info("Loading features from MongoDB...")
    features_data = list(db[FEATURES_COLLECTION].find())
    features_df = pd.DataFrame(features_data)

    if features_df.empty:
        logger.error("Features collection is empty!")
        raise SystemExit(1)

    if "_id" in features_df.columns:
        features_df = features_df.drop(columns=["_id"])

    logger.info(f"Loaded {len(features_df)} customer feature records")

    required_columns = [
        "customer_id",
        "gap_change_pct",
        "aov_change_pct",
        "diversity_delta"
    ]

    missing_columns = [col for col in required_columns if col not in features_df.columns]
    if missing_columns:
        logger.error(f"Missing required columns: {missing_columns}")
        raise SystemExit(1)

    return features_df


def run_isolation_forest(features_df):
    logger.info("Running Isolation Forest model...")

    feature_matrix = features_df[MODEL_FEATURES]

    model = IsolationForest(
        contamination=CONTAMINATION_RATE,
        random_state=42
    )
    model.fit(feature_matrix)

    anomaly_scores = model.decision_function(feature_matrix)
    predictions = model.predict(feature_matrix)

    features_df["anomaly_score"] = anomaly_scores
    features_df["is_anomaly"] = predictions

    logger.info("Isolation Forest completed successfully!")
    logger.info(
        f"Anomaly score range: {anomaly_scores.min():.4f} to {anomaly_scores.max():.4f}"
    )

    return features_df, anomaly_scores


def calculate_scores(features_df, anomaly_scores):
    logger.info("Normalizing anomaly scores...")

    min_score = anomaly_scores.min()
    max_score = anomaly_scores.max()

    # Invert so lower anomaly score = higher risk
    anomaly_risk_scores = (
        (max_score - anomaly_scores) / (max_score - min_score)
    ) * 100

    features_df["anomaly_risk_score"] = anomaly_risk_scores.round(2)

    logger.info("Calculating business risk scores...")

    business_risk_scores = (
        features_df["aov_change_pct"].abs() * AOV_WEIGHT
        + features_df["gap_change_pct"].abs() * GAP_WEIGHT
        + features_df["diversity_delta"].abs() * DIVERSITY_WEIGHT
    ).clip(0, 100)

    features_df["business_risk_score"] = business_risk_scores.round(2)

    logger.info("Combining anomaly + business risk scores...")

    final_risk_scores = (
        features_df["business_risk_score"] * BUSINESS_SCORE_WEIGHT
        + features_df["anomaly_risk_score"] * ANOMALY_SCORE_WEIGHT
    ).clip(0, 100)

    features_df["risk_score"] = final_risk_scores.round(2)
    features_df["risk_label"] = features_df["risk_score"].apply(get_risk_label)

    return features_df


def save_risk_scores(db, features_df):
    logger.info("Saving risk scores to MongoDB...")

    risk_records = features_df[
        [
            "customer_id",
            "gap_change_pct",
            "aov_change_pct",
            "diversity_delta",
            "business_risk_score",
            "anomaly_risk_score",
            "anomaly_score",
            "is_anomaly",
            "risk_score",
            "risk_label"
        ]
    ].to_dict(orient="records")

    db[RISK_COLLECTION].delete_many({})
    db[RISK_COLLECTION].insert_many(risk_records)

    logger.info(f"Successfully saved {len(risk_records)} risk records to MongoDB!")


def print_output_tables(features_df):
    features_df = features_df.sort_values(by="risk_score", ascending=False)

    print("\n========== FULL RISK TABLE ==========\n")
    print(
        features_df[
            [
                "customer_id",
                "risk_score",
                "risk_label",
                "business_risk_score",
                "anomaly_risk_score",
                "anomaly_score",
                "is_anomaly"
            ]
        ].to_string(index=False)
    )

    print("\n========== RISK LABEL COUNTS ==========\n")
    label_counts = (
        features_df["risk_label"]
        .value_counts()
        .reindex(["Critical", "At Risk", "Watch", "Healthy"], fill_value=0)
        .reset_index()
    )
    label_counts.columns = ["risk_label", "count"]
    print(label_counts.to_string(index=False))

    print("\n========== CUSTOMERS BY RISK LABEL ==========\n")
    for label in ["Critical", "At Risk", "Watch", "Healthy"]:
        subset = features_df[features_df["risk_label"] == label]
        print(f"\n--- {label} ({len(subset)}) ---")
        if subset.empty:
            print("None")
        else:
            print(
                subset[
                    [
                        "customer_id",
                        "risk_score",
                        "risk_label",
                        "business_risk_score",
                        "anomaly_risk_score"
                    ]
                ].to_string(index=False)
            )


def main():
    client = connect_to_mongo()
    db = client[DATABASE_NAME]

    features_df = load_features(db)
    logger.info("Preview of features dataframe:")
    print(features_df.head())

    features_df, anomaly_scores = run_isolation_forest(features_df)
    features_df = calculate_scores(features_df, anomaly_scores)

    print_output_tables(features_df)
    save_risk_scores(db, features_df)

    logger.info("Anomaly detection pipeline completed successfully!")


if __name__ == "__main__":
    main()