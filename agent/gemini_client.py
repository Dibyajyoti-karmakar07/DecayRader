# agent/gemini_client.py

import os
import time
import json
import logging

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

MODEL_NAME = "gemini-3.5-flash"

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
    Sends a customer's data to Gemini and returns parsed JSON.

    Input  : customer dict with profile + decay signals
    Output : dict with keys —
                decay_summary, priority_reason, likely_reason,
                primary_action, secondary_action,
                outreach_message, urgency

    Returns None if the API call or JSON parsing fails.
    """

    customer_prompt = build_customer_prompt(customer)
    full_prompt     = f"{SYSTEM_PROMPT}\n\n{customer_prompt}"

    max_retries = 3
    retry_delay = 5

    for attempt in range(max_retries):

        try:
            logger.info(
                f"Calling Gemini for "
                f"{customer.get('customer_id', 'UNKNOWN')} "
                f"(attempt {attempt + 1}/{max_retries})..."
            )

            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=full_prompt,
                config={"temperature": 0.2}
            )

            # Guard against empty response
            if not response.text:
                logger.error(
                    f"Gemini returned empty response for "
                    f"{customer.get('customer_id', 'UNKNOWN')}"
                )
                return None

            raw_text = response.text.strip()

            # Strip markdown code fences robustly
            if raw_text.startswith("```"):
                raw_text = raw_text.replace("```json", "")
                raw_text = raw_text.replace("```", "")
                raw_text = raw_text.strip()

            parsed = json.loads(raw_text)

            # Validate all required keys are present
            missing_keys = [k for k in REQUIRED_KEYS if k not in parsed]

            if missing_keys:
                logger.error(
                    f"Gemini response missing keys for "
                    f"{customer.get('customer_id', 'UNKNOWN')}: "
                    f"{missing_keys}"
                )
                return None

            logger.info(
                f"Gemini response received for "
                f"{customer.get('customer_id', 'UNKNOWN')}"
            )

            return parsed

        except json.JSONDecodeError as e:
            logger.error(
                f"Failed to parse Gemini JSON for "
                f"{customer.get('customer_id', 'UNKNOWN')}: {e}"
            )
            return None

        except Exception as e:
            if "429" in str(e) and attempt < max_retries - 1:
                logger.warning(
                    f"Rate limited for "
                    f"{customer.get('customer_id', 'UNKNOWN')}. "
                    f"Waiting {retry_delay}s before retry..."
                )
                time.sleep(retry_delay)
                retry_delay *= 2  # 5s → 10s → 20s
                continue

            logger.error(
                f"Gemini API call failed for "
                f"{customer.get('customer_id', 'UNKNOWN')}: {e}"
            )
            return None

    logger.error(
        f"All {max_retries} attempts failed for "
        f"{customer.get('customer_id', 'UNKNOWN')}"
    )
    return None