# agent/gemini_client.py

import os
import sys
import time
import json
import logging

# Allow running directly OR as part of the agent package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from google import genai

from agent.prompts import SYSTEM_PROMPT, build_customer_prompt


# =========================================================
# LOGGING SETUP
# =========================================================

logger = logging.getLogger(__name__)


# =========================================================
# CONSTANTS
# =========================================================

FALLBACK_MODELS = [
    "gemini-3.5-flash",       # Primary — best quality, 20 RPD
    "gemini-2.0-flash",       # Fallback 1 — 1500 RPD
    "gemini-1.5-flash",       # Fallback 2 — 1500 RPD
    "gemini-3.1-flash-lite",  # Fallback 3 — 1000 RPD
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


# =========================================================
# SETUP CLIENT
# =========================================================

def setup_gemini_client():
    """
    Loads API key from .env and returns a configured Gemini client.
    """

    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        logger.error("GEMINI_API_KEY not found in .env file")
        raise SystemExit(1)

    logger.info("Gemini client initialized successfully")

    return genai.Client(api_key=api_key)


# =========================================================
# CALL GEMINI
# =========================================================

def call_gemini(client, customer: dict) -> dict:
    """
    Sends customer data to Gemini with model fallback.

    Tries each model in FALLBACK_MODELS order.
    If a model is rate limited, unavailable, returns malformed
    JSON, or missing required keys — falls back to next model.

    Input  : customer dict with profile + decay signals
    Output : dict with keys —
                decay_summary, priority_reason, likely_reason,
                primary_action, secondary_action,
                outreach_message, urgency, model_used

    Returns None if all models fail.
    """

    customer_prompt = build_customer_prompt(customer)
    full_prompt     = f"{SYSTEM_PROMPT}\n\n{customer_prompt}"

    for model in FALLBACK_MODELS:

        max_retries = 3
        retry_delay = 5

        for attempt in range(max_retries):

            try:
                logger.info(
                    f"Calling {model} for "
                    f"{customer.get('customer_id', 'UNKNOWN')} "
                    f"(attempt {attempt + 1}/{max_retries})..."
                )

                response = client.models.generate_content(
                    model=model,
                    contents=full_prompt,
                    config={"temperature": 0.2}
                )

                # Guard against empty response
                if not response.text:
                    logger.warning(
                        f"{model} returned empty response for "
                        f"{customer.get('customer_id', 'UNKNOWN')} "
                        f"— trying next model..."
                    )
                    break

                raw_text = response.text.strip()

                # Strip markdown code fences robustly
                if raw_text.startswith("```"):
                    raw_text = raw_text.replace("```json", "")
                    raw_text = raw_text.replace("```", "")
                    raw_text = raw_text.strip()

                parsed = json.loads(raw_text)

                # Validate all required keys are present
                missing_keys = [
                    k for k in REQUIRED_KEYS if k not in parsed
                ]

                if missing_keys:
                    logger.warning(
                        f"{model} response missing keys for "
                        f"{customer.get('customer_id', 'UNKNOWN')}: "
                        f"{missing_keys} — trying next model..."
                    )
                    break

                # Store which model was actually used
                parsed["model_used"] = model

                logger.info(
                    f"{model} response received for "
                    f"{customer.get('customer_id', 'UNKNOWN')}"
                )

                return parsed

            except json.JSONDecodeError as e:
                logger.warning(
                    f"{model} returned malformed JSON for "
                    f"{customer.get('customer_id', 'UNKNOWN')}: {e} "
                    f"— trying next model..."
                )
                break

            except Exception as e:
                if (
                    "429" in str(e) or "503" in str(e)
                ) and attempt < max_retries - 1:
                    logger.warning(
                        f"{model} rate limited or unavailable for "
                        f"{customer.get('customer_id', 'UNKNOWN')}. "
                        f"Waiting {retry_delay}s before retry..."
                    )
                    time.sleep(retry_delay)
                    retry_delay *= 2  # 5s → 10s → 20s
                    continue

                logger.warning(
                    f"{model} failed for "
                    f"{customer.get('customer_id', 'UNKNOWN')} "
                    f"— trying next model..."
                )
                break

    logger.error(
        f"All models failed for "
        f"{customer.get('customer_id', 'UNKNOWN')}"
    )
    return None