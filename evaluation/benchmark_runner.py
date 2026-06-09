# evaluation/benchmark_runner.py

import os
import sys
import json
import time
import logging
from typing import Optional, Any

import pandas as pd
from dotenv import load_dotenv
from google import genai

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.prompts import SYSTEM_PROMPT, build_customer_prompt

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

MODELS = [
    "gemini-3.5-flash",
    "gemini-3-flash",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-3.1-flash-lite"
]

REQUIRED_KEYS = [
    "decay_summary",
    "priority_reason",
    "likely_reason",
    "primary_action",
    "secondary_action",
    "outreach_message",
    "urgency"
]

EVAL_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_CUSTOMERS_PATH = os.path.join(EVAL_DIR, "test_customers.json")
HUMAN_LABELS_PATH = os.path.join(EVAL_DIR, "human_labels.csv")
RESULTS_CSV_PATH = os.path.join(EVAL_DIR, "benchmark_results.csv")
REPORT_PATH = os.path.join(EVAL_DIR, "benchmark_report.md")


# =========================================================
# SETUP
# =========================================================

def setup_gemini_client() -> genai.Client:
    """
    Loads API key from .env and returns a configured Gemini client.

    Returns:
        genai.Client configured with GEMINI_API_KEY

    Raises:
        SystemExit if GEMINI_API_KEY not found
    """

    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        logger.error("GEMINI_API_KEY not found in .env file")
        raise SystemExit(1)

    logger.info("Gemini client initialized successfully")

    return genai.Client(api_key=api_key)


# =========================================================
# LOAD DATA
# =========================================================

def load_customers() -> list[dict]:
    """
    Loads test customers from evaluation/test_customers.json.

    Returns:
        List of customer dicts with required benchmark fields

    Raises:
        SystemExit if file not found or invalid JSON
    """

    if not os.path.exists(TEST_CUSTOMERS_PATH):
        logger.error(f"test_customers.json not found at {TEST_CUSTOMERS_PATH}")
        raise SystemExit(1)

    try:
        with open(TEST_CUSTOMERS_PATH, "r") as f:
            customers = json.load(f)
        logger.info(f"Loaded {len(customers)} test customers")
        return customers
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse test_customers.json: {e}")
        raise SystemExit(1)


def load_labels() -> pd.DataFrame:
    """
    Loads human labels from evaluation/human_labels.csv.

    Columns:
        customer_id, expected_action, expected_urgency

    Returns:
        DataFrame with human ground truth expectations

    Raises:
        SystemExit if file not found or invalid CSV
    """

    if not os.path.exists(HUMAN_LABELS_PATH):
        logger.error(f"human_labels.csv not found at {HUMAN_LABELS_PATH}")
        raise SystemExit(1)

    try:
        labels_df = pd.read_csv(HUMAN_LABELS_PATH)
        logger.info(f"Loaded {len(labels_df)} human labels")
        return labels_df
    except Exception as e:
        logger.error(f"Failed to parse human_labels.csv: {e}")
        raise SystemExit(1)


# =========================================================
# RUN MODEL
# =========================================================

def call_gemini_with_timing(
    client: genai.Client,
    model: str,
    customer: dict
) -> tuple[Optional[dict], float, bool]:
    """
    Sends customer data to Gemini model with timing and validation.

    Args:
        client: Gemini client instance
        model: Model name to call (e.g., "gemini-3.5-flash")
        customer: Customer dict with profile and decay signals

    Returns:
        Tuple of (parsed_json, latency_seconds, is_valid)
        - parsed_json: Dict with response or None if failed
        - latency_seconds: Float seconds for API call
        - is_valid: Boolean whether JSON is valid

    Logs errors for failures but does not raise exceptions
    """

    customer_prompt = build_customer_prompt(customer)
    full_prompt = f"{SYSTEM_PROMPT}\n\n{customer_prompt}"

    customer_id = customer.get("customer_id", "UNKNOWN")
    max_retries = 3
    retry_delay = 5

    for attempt in range(max_retries):

        try:
            logger.info(
                f"Calling {model} for {customer_id} "
                f"(attempt {attempt + 1}/{max_retries})..."
            )

            start_time = time.time()

            response = client.models.generate_content(
                model=model,
                contents=full_prompt,
                config={"temperature": 0.2}
            )

            latency = time.time() - start_time

            # Guard against empty response
            if not response.text:
                logger.error(f"{model} returned empty response for {customer_id}")
                return (None, latency, False)

            raw_text = response.text.strip()

            # Strip markdown code fences
            if raw_text.startswith("```"):
                raw_text = raw_text.replace("```json", "")
                raw_text = raw_text.replace("```", "")
                raw_text = raw_text.strip()

            parsed = json.loads(raw_text)

            # Validate all required keys are present
            missing_keys = [k for k in REQUIRED_KEYS if k not in parsed]

            if missing_keys:
                logger.error(
                    f"{model} response missing keys for {customer_id}: {missing_keys}"
                )
                return (parsed, latency, False)

            logger.info(f"{model} response received for {customer_id}")

            return (parsed, latency, True)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse {model} JSON for {customer_id}: {e}")
            return (None, 0, False)

        except Exception as e:
            if ("429" in str(e) or "503" in str(e)) and attempt < max_retries - 1:
                logger.warning(
                    f"Rate limited for {customer_id}. "
                    f"Waiting {retry_delay}s before retry..."
                )
                time.sleep(retry_delay)
                retry_delay *= 2
                continue

            logger.error(f"{model} API call failed for {customer_id}: {e}")
            return (None, 0, False)

    logger.error(f"All {max_retries} attempts failed for {customer_id}")
    return (None, 0, False)


# =========================================================
# EVALUATE
# =========================================================

def evaluate_predictions(
    model: str,
    customers: list[dict],
    labels_df: pd.DataFrame,
    client: genai.Client
) -> list[dict]:
    """
    Evaluates a single model against all test customers.

    Args:
        model: Model name to evaluate
        customers: List of test customer dicts
        labels_df: DataFrame with human labels
        client: Gemini client instance

    Returns:
        List of result dicts, one per customer, with columns:
        - model
        - customer_id
        - expected_action
        - predicted_action
        - action_correct
        - expected_urgency
        - predicted_urgency
        - urgency_correct
        - latency_seconds
        - success
    """

    results = []

    for customer in customers:

        customer_id = customer.get("customer_id")

        # Find human labels for this customer
        label_row = labels_df[labels_df["customer_id"] == customer_id]

        if label_row.empty:
            logger.warning(f"No label found for {customer_id}, skipping")
            continue

        expected_action = label_row["expected_action"].values[0]
        expected_urgency = label_row["expected_urgency"].values[0]

        # Call model
        parsed_json, latency, is_valid = call_gemini_with_timing(
            client, model, customer
        )

        # Extract predictions
        if parsed_json and is_valid:
            predicted_action = parsed_json.get("primary_action", "Unknown")
            predicted_urgency = parsed_json.get("urgency", "Unknown")
            success = True
        else:
            predicted_action = "Parse Error"
            predicted_urgency = "Parse Error"
            success = False

        # Compare predictions (case-insensitive)
        action_correct = (
            str(predicted_action).lower().strip()
            == str(expected_action).lower().strip()
        )

        urgency_correct = (
            str(predicted_urgency).lower().strip()
            == str(expected_urgency).lower().strip()
        )

        result = {
            "model": model,
            "customer_id": customer_id,
            "expected_action": expected_action,
            "predicted_action": predicted_action,
            "action_correct": action_correct,
            "expected_urgency": expected_urgency,
            "predicted_urgency": predicted_urgency,
            "urgency_correct": urgency_correct,
            "latency_seconds": latency,
            "success": success
        }

        results.append(result)

        # Rate limit between calls
        time.sleep(1)

    return results


# =========================================================
# SAVE RESULTS
# =========================================================

def save_results(all_results: list[dict]) -> None:
    """
    Saves benchmark results to evaluation/benchmark_results.csv.

    Args:
        all_results: List of result dicts from all models and customers
    """

    results_df = pd.DataFrame(all_results)

    results_df.to_csv(RESULTS_CSV_PATH, index=False)

    logger.info(f"Saved {len(results_df)} results to {RESULTS_CSV_PATH}")


# =========================================================
# CALCULATE METRICS
# =========================================================

def calculate_model_metrics(results_df: pd.DataFrame) -> dict:
    """
    Calculates aggregate metrics for each model from results DataFrame.

    Args:
        results_df: DataFrame with columns from save_results

    Returns:
        Dict mapping model_name to metrics dict with keys:
        - total_cases
        - successful_calls
        - failed_calls
        - success_rate
        - json_validity_rate
        - action_accuracy
        - urgency_accuracy
        - average_latency_seconds
    """

    metrics = {}

    for model in MODELS:

        model_results = results_df[results_df["model"] == model]

        if len(model_results) == 0:
            continue

        total_cases = len(model_results)
        successful_calls = model_results["success"].sum()
        failed_calls = total_cases - successful_calls

        success_rate = (successful_calls / total_cases) * 100 if total_cases > 0 else 0
        json_validity_rate = (
            (model_results["success"].sum() / total_cases) * 100
            if total_cases > 0
            else 0
        )
        action_accuracy = (
            (model_results["action_correct"].sum() / total_cases) * 100
            if total_cases > 0
            else 0
        )
        urgency_accuracy = (
            (model_results["urgency_correct"].sum() / total_cases) * 100
            if total_cases > 0
            else 0
        )
        average_latency = model_results["latency_seconds"].mean()

        metrics[model] = {
            "total_cases": total_cases,
            "successful_calls": successful_calls,
            "failed_calls": failed_calls,
            "success_rate": success_rate,
            "json_validity_rate": json_validity_rate,
            "action_accuracy": action_accuracy,
            "urgency_accuracy": urgency_accuracy,
            "average_latency_seconds": average_latency
        }

    return metrics


# =========================================================
# GENERATE REPORT
# =========================================================

def generate_report(metrics: dict) -> None:
    """
    Generates benchmark_report.md with model rankings and metrics.

    Args:
        metrics: Dict mapping model_name to metrics dict
    """

    # Rank models by:
    # 1. action_accuracy
    # 2. urgency_accuracy
    # 3. success_rate
    # 4. average_latency (lower is better)

    ranked_models = sorted(
        metrics.items(),
        key=lambda x: (
            -x[1]["action_accuracy"],
            -x[1]["urgency_accuracy"],
            -x[1]["success_rate"],
            x[1]["average_latency_seconds"]
        )
    )

    report_lines = []

    report_lines.append("# Benchmark Report")
    report_lines.append("")
    report_lines.append("## Summary")
    report_lines.append("")
    report_lines.append(f"Models evaluated: {len(metrics)}")
    report_lines.append("")

    # Detail section for each model
    report_lines.append("## Model Performance")
    report_lines.append("")

    for i, (model, m) in enumerate(ranked_models, 1):
        report_lines.append(f"### {i}. {model}")
        report_lines.append("")
        report_lines.append(f"- **Total Cases:** {m['total_cases']}")
        report_lines.append(f"- **Successful Calls:** {m['successful_calls']} / {m['total_cases']}")
        report_lines.append(f"- **Success Rate:** {m['success_rate']:.2f}%")
        report_lines.append(f"- **JSON Validity Rate:** {m['json_validity_rate']:.2f}%")
        report_lines.append(f"- **Action Accuracy:** {m['action_accuracy']:.2f}%")
        report_lines.append(f"- **Urgency Accuracy:** {m['urgency_accuracy']:.2f}%")
        report_lines.append(f"- **Average Latency:** {m['average_latency_seconds']:.2f}s")
        report_lines.append("")

    # Winner
    if ranked_models:
        winner, winner_metrics = ranked_models[0]
        report_lines.append("## Winner")
        report_lines.append("")
        report_lines.append(
            f"**{winner}** has the best overall performance "
            f"({winner_metrics['action_accuracy']:.2f}% action accuracy, "
            f"{winner_metrics['urgency_accuracy']:.2f}% urgency accuracy)"
        )
        report_lines.append("")

    report_content = "\n".join(report_lines)

    with open(REPORT_PATH, "w") as f:
        f.write(report_content)

    logger.info(f"Saved report to {REPORT_PATH}")


# =========================================================
# MAIN
# =========================================================

def main():
    """
    Orchestrates the full benchmark run:
    1. Loads test customers and human labels
    2. For each model, evaluates all customers
    3. Saves results to CSV
    4. Calculates metrics
    5. Generates markdown report
    """

    logger.info("Starting benchmark run...")

    client = setup_gemini_client()

    customers = load_customers()
    labels_df = load_labels()

    all_results = []

    for model in MODELS:
        logger.info(f"Evaluating {model}...")
        model_results = evaluate_predictions(model, customers, labels_df, client)
        all_results.extend(model_results)

    logger.info(f"Completed {len(all_results)} total evaluations")

    save_results(all_results)

    results_df = pd.read_csv(RESULTS_CSV_PATH)
    metrics = calculate_model_metrics(results_df)

    generate_report(metrics)

    logger.info("Benchmark complete!")

    # Print summary to console
    logger.info("\n" + "=" * 60)
    logger.info("BENCHMARK SUMMARY")
    logger.info("=" * 60)

    for model in MODELS:
        if model in metrics:
            m = metrics[model]
            logger.info(f"\n{model}:")
            logger.info(f"  Total Cases: {m['total_cases']}")
            logger.info(f"  Success Rate: {m['success_rate']:.2f}%")
            logger.info(f"  Action Accuracy: {m['action_accuracy']:.2f}%")
            logger.info(f"  Urgency Accuracy: {m['urgency_accuracy']:.2f}%")
            logger.info(f"  Average Latency: {m['average_latency_seconds']:.2f}s")


if __name__ == "__main__":
    main()
