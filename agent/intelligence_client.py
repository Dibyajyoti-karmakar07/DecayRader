# agent/intelligence_client.py
# ─────────────────────────────────
# Gemini client for AI Customer Intelligence Reports.
# Follows the same pattern as agent/gemini_client.py.

import time
import json
import logging

from agent.gemini_client import setup_gemini_client, FALLBACK_MODELS, parse_gemini_json
from agent.intelligence_prompts import (
    INTELLIGENCE_SYSTEM_PROMPT, 
    build_intelligence_prompt,
    PORTFOLIO_SYSTEM_PROMPT,
    build_portfolio_analysis_prompt,
    TIER_SYSTEM_PROMPT,
    build_tier_analysis_prompt
)

logger = logging.getLogger(__name__)


# =========================================================
# REQUIRED FIELDS FOR VALIDATION
# =========================================================

REQUIRED_OUTPUT_KEYS = [
    "executive_diagnosis",
    "behavioral_changes",
    "likely_business_situation",
    "revenue_risk_assessment",
    "retention_strategy",
    "expected_outcome"
]

PORTFOLIO_REQUIRED_OUTPUT_KEYS = [
    "portfolio_health",
    "largest_revenue_threat",
    "risk_concentration_analysis",
    "emerging_trends",
    "projected_business_impact",
    "strategic_recommendations",
    "resource_allocation_priorities"
]

TIER_REQUIRED_OUTPUT_KEYS = [
    "tier_health_assessment",
    "behavioral_pattern_analysis",
    "healthy_vs_at_risk",
    "primary_decay_drivers",
    "strategic_recommendation",
    "expected_business_impact"
]




def generate_customer_intelligence(cust, risk=None, intv=None) -> dict | None:
    """Generate an AI Customer Intelligence Report via Gemini.

    Builds a prompt from customer profile / risk / intervention data,
    sends it to Gemini with model fallback, and returns the parsed JSON.

    Parameters
    ----------
    cust  : pd.Series — customer profile row
    risk  : pd.Series or None — risk_scores row
    intv  : pd.Series or None — first intervention row

    Returns
    -------
    dict | None — parsed intelligence report or None on failure.
    """
    try:
        client = setup_gemini_client()
    except (Exception, SystemExit):
        return None

    prompt = build_intelligence_prompt(cust, risk, intv)
    full_prompt = f"{INTELLIGENCE_SYSTEM_PROMPT}\n\n{prompt}"

    for model in FALLBACK_MODELS:

        max_retries = 2
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                logger.info(
                    f"Generating Intelligence Report via {model} for "
                    f"{cust.get('customer_id', 'UNKNOWN')} "
                    f"(attempt {attempt + 1}/{max_retries})..."
                )

                response = client.models.generate_content(
                    model=model,
                    contents=full_prompt,
                    config={"temperature": 0.3},
                )
                
                if not response.text:
                    logger.warning(
                        f"{model} returned empty response for "
                        f"{cust.get('customer_id', 'UNKNOWN')} "
                        f"— trying next model..."
                    )
                    break

                parsed = parse_gemini_json(response.text)

                if not isinstance(parsed, dict):
                    logger.warning(
                        f"{model} returned non-dictionary JSON for "
                        f"{cust.get('customer_id', 'UNKNOWN')} — trying next model..."
                    )
                    break

                # Validate all required keys are present
                missing_keys = [
                    k for k in REQUIRED_OUTPUT_KEYS if k not in parsed
                ]

                if missing_keys:
                    logger.warning(
                        f"{model} response missing keys for "
                        f"{cust.get('customer_id', 'UNKNOWN')}: "
                        f"{missing_keys} — trying next model..."
                    )
                    break

                parsed["_model_used"] = model
                
                logger.info(
                    f"{model} Intelligence Report generated successfully for "
                    f"{cust.get('customer_id', 'UNKNOWN')}"
                )
                
                return parsed

            except json.JSONDecodeError as e:
                logger.warning(
                    f"{model} returned malformed JSON for "
                    f"{cust.get('customer_id', 'UNKNOWN')}: {e} "
                    f"— trying next model..."
                )
                break

            except Exception as e:
                if (
                    "429" in str(e) or "503" in str(e)
                ) and attempt < max_retries - 1:
                    logger.warning(
                        f"{model} rate limited or unavailable for "
                        f"{cust.get('customer_id', 'UNKNOWN')}. "
                        f"Waiting {retry_delay}s before retry..."
                    )
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue

                logger.warning(
                    f"{model} failed for "
                    f"{cust.get('customer_id', 'UNKNOWN')} "
                    f"— trying next model..."
                )
                break

    logger.error(
        f"All models failed for Intelligence Report on "
        f"{cust.get('customer_id', 'UNKNOWN')}"
    )
    return None


def generate_portfolio_analysis(top_risk_df) -> dict | None:
    """Generate an AI Portfolio Risk Analysis Report via Gemini.

    Builds a prompt from top at-risk customer data,
    sends it to Gemini with model fallback, and returns the parsed JSON.

    Parameters
    ----------
    top_risk_df : pd.DataFrame — top highest-risk customers with profile and risk scores.

    Returns
    -------
    dict | None — parsed portfolio analysis report or None on failure.
    """
    if top_risk_df is None or top_risk_df.empty:
        logger.warning("generate_portfolio_analysis called with empty DataFrame. Aborting.")
        return None
    try:
        client = setup_gemini_client()
    except (Exception, SystemExit):
        return None

    prompt = build_portfolio_analysis_prompt(top_risk_df)
    full_prompt = f"{PORTFOLIO_SYSTEM_PROMPT}\n\n{prompt}"

    for model in FALLBACK_MODELS:

        max_retries = 2
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                logger.info(
                    f"Generating Portfolio Analysis via {model} "
                    f"(attempt {attempt + 1}/{max_retries})..."
                )

                response = client.models.generate_content(
                    model=model,
                    contents=full_prompt,
                    config={"temperature": 0.3},
                )
                
                if not response.text:
                    logger.warning(f"{model} returned empty response for Portfolio Analysis — trying next model...")
                    break

                parsed = parse_gemini_json(response.text)

                if not isinstance(parsed, dict):
                    logger.warning(f"{model} returned non-dictionary JSON for Portfolio Analysis — trying next model...")
                    break

                # Validate all required keys are present
                missing_keys = [
                    k for k in PORTFOLIO_REQUIRED_OUTPUT_KEYS if k not in parsed
                ]

                if missing_keys:
                    logger.warning(
                        f"{model} response missing keys for Portfolio Analysis: "
                        f"{missing_keys} — trying next model..."
                    )
                    break

                parsed["_model_used"] = model
                
                logger.info(f"{model} Portfolio Analysis generated successfully")
                
                return parsed

            except json.JSONDecodeError as e:
                logger.warning(f"{model} returned malformed JSON for Portfolio Analysis: {e} — trying next model...")
                break

            except Exception as e:
                if (
                    "429" in str(e) or "503" in str(e)
                ) and attempt < max_retries - 1:
                    logger.warning(f"{model} rate limited or unavailable for Portfolio Analysis. Waiting {retry_delay}s before retry...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue

                logger.warning(f"{model} failed for Portfolio Analysis — trying next model...")
                break

    logger.error("All models failed for Portfolio Analysis")
    return None


def generate_tier_analysis(tier_name: str, tier_df) -> dict | None:
    """Generate an AI Tier Intelligence Report via Gemini.

    Builds a prompt from aggregated customer data for a specific tier,
    sends it to Gemini with model fallback, and returns the parsed JSON.

    Parameters
    ----------
    tier_name : str — name of the tier (e.g. Gold, Silver, Bronze)
    tier_df : pd.DataFrame — customer and risk data filtered for this tier

    Returns
    -------
    dict | None — parsed tier analysis report or None on failure.
    """
    if tier_df is None or tier_df.empty:
        logger.warning(f"generate_tier_analysis called with empty DataFrame for {tier_name}. Aborting.")
        return None
    try:
        client = setup_gemini_client()
    except (Exception, SystemExit):
        return None

    prompt = build_tier_analysis_prompt(tier_name, tier_df)
    full_prompt = f"{TIER_SYSTEM_PROMPT}\n\n{prompt}"

    for model in FALLBACK_MODELS:

        max_retries = 2
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                logger.info(
                    f"Generating Tier Intelligence Report for Tier {tier_name} via {model} "
                    f"(attempt {attempt + 1}/{max_retries})..."
                )

                response = client.models.generate_content(
                    model=model,
                    contents=full_prompt,
                    config={"temperature": 0.3},
                )
                
                if not response.text:
                    logger.warning(f"{model} returned empty response for Tier Analysis ({tier_name}) — trying next model...")
                    break

                parsed = parse_gemini_json(response.text)

                if not isinstance(parsed, dict):
                    logger.warning(f"{model} returned non-dictionary JSON for Tier Analysis ({tier_name}) — trying next model...")
                    break

                # Validate all required keys are present
                missing_keys = [
                    k for k in TIER_REQUIRED_OUTPUT_KEYS if k not in parsed
                ]

                if missing_keys:
                    logger.warning(
                        f"{model} response missing keys for Tier Analysis ({tier_name}): "
                        f"{missing_keys} — trying next model..."
                    )
                    break

                parsed["_model_used"] = model
                
                logger.info(f"{model} Tier Analysis ({tier_name}) generated successfully")
                
                return parsed

            except json.JSONDecodeError as e:
                logger.warning(f"{model} returned malformed JSON for Tier Analysis ({tier_name}): {e} — trying next model...")
                break

            except Exception as e:
                if (
                    "429" in str(e) or "503" in str(e)
                ) and attempt < max_retries - 1:
                    logger.warning(f"{model} rate limited or unavailable for Tier Analysis ({tier_name}). Waiting {retry_delay}s before retry...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue

                logger.warning(f"{model} failed for Tier Analysis ({tier_name}) — trying next model...")
                break

    logger.error(f"All models failed for Tier Analysis ({tier_name})")
    return None

