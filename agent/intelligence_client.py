# agent/intelligence_client.py
# ─────────────────────────────────
# Gemini client for AI Customer Intelligence Reports using MCP.

import json
import logging
from agent.gemini_client import parse_gemini_json
from agent.mcp_agent import run_mcp_agent_sync
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

def generate_customer_intelligence(customer_id: str) -> dict | None:
    """Generate an AI Customer Intelligence Report via Gemini + MCP Tools."""
    prompt = build_intelligence_prompt(customer_id)
    full_prompt = f"{INTELLIGENCE_SYSTEM_PROMPT}\n\n{prompt}"

    logger.info(f"Generating Intelligence Report via MCP for {customer_id}...")
    response_text = run_mcp_agent_sync(full_prompt)

    if not response_text:
        return None

    parsed = parse_gemini_json(response_text)
    if not isinstance(parsed, dict):
        return None

    missing_keys = [k for k in REQUIRED_OUTPUT_KEYS if k not in parsed]
    if missing_keys:
        logger.warning(f"Response missing keys for {customer_id}: {missing_keys}")
        return None

    parsed["_model_used"] = "gemini-3.1-flash-lite (MCP)"
    return parsed


def generate_portfolio_analysis() -> dict | None:
    """Generate an AI Portfolio Risk Analysis Report via Gemini + MCP Tools."""
    prompt = build_portfolio_analysis_prompt()
    full_prompt = f"{PORTFOLIO_SYSTEM_PROMPT}\n\n{prompt}"

    logger.info("Generating Portfolio Analysis via MCP...")
    response_text = run_mcp_agent_sync(full_prompt)

    if not response_text:
        return None

    parsed = parse_gemini_json(response_text)
    if not isinstance(parsed, dict):
        return None

    missing_keys = [k for k in PORTFOLIO_REQUIRED_OUTPUT_KEYS if k not in parsed]
    if missing_keys:
        logger.warning(f"Response missing keys for Portfolio Analysis: {missing_keys}")
        return None

    parsed["_model_used"] = "gemini-3.1-flash-lite (MCP)"
    return parsed


def generate_tier_analysis(tier_name: str) -> dict | None:
    """Generate an AI Tier Intelligence Report via Gemini + MCP Tools."""
    prompt = build_tier_analysis_prompt(tier_name)
    full_prompt = f"{TIER_SYSTEM_PROMPT}\n\n{prompt}"

    logger.info(f"Generating Tier Intelligence Report for Tier {tier_name} via MCP...")
    response_text = run_mcp_agent_sync(full_prompt)

    if not response_text:
        return None

    parsed = parse_gemini_json(response_text)
    if not isinstance(parsed, dict):
        return None

    missing_keys = [k for k in TIER_REQUIRED_OUTPUT_KEYS if k not in parsed]
    if missing_keys:
        logger.warning(f"Response missing keys for Tier Analysis ({tier_name}): {missing_keys}")
        return None

    parsed["_model_used"] = "gemini-3.1-flash-lite (MCP)"
    return parsed
