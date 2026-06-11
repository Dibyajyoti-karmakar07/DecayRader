# agent/intelligence_client.py
# ─────────────────────────────────
# Gemini client for AI Customer Intelligence Reports using MCP.

import json
import logging
from agent.gemini_client import parse_gemini_json, setup_gemini_client, FALLBACK_MODELS
from utils.db import connect_to_mongo
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
# PYTHON-ONLY WORKAROUND (BYPASS MCP FOR HACKATHON STABILITY)
# =========================================================
def _generate_direct_gemini(system_prompt: str, user_prompt: str, data_context: dict) -> str | None:
    """Fallback: Call Gemini directly with the fetched MongoDB data, bypassing MCP."""
    try:
        client = setup_gemini_client()
    except Exception as e:
        logger.error(f"Failed to setup Gemini client: {e}")
        return None
        
    context_str = json.dumps(data_context, default=str, indent=2)
    # Give Gemini the exact data it would have fetched via MCP
    full_prompt = f"{system_prompt}\n\n[DATABASE CONTEXT FETCHED VIA DIRECT PYTHON]\n{context_str}\n\n{user_prompt}"
    
    for model in FALLBACK_MODELS:
        try:
            logger.info(f"Trying direct Gemini call with model: {model}")
            response = client.models.generate_content(
                model=model,
                contents=full_prompt,
                config={"temperature": 0.2}
            )
            if response.text:
                return response.text
        except Exception as e:
            logger.warning(f"Direct Gemini call failed for {model}: {e}")
            continue
    return None

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

import streamlit as st

@st.cache_data(ttl=3600, show_spinner=False)
def generate_customer_intelligence(customer_id: str) -> dict | None:
    """Generate an AI Customer Intelligence Report via Gemini + MCP Tools."""
    prompt = build_intelligence_prompt(customer_id)
    
    # 1. Fetch data directly from Mongo
    db = connect_to_mongo()
    customer = db["Customers"].find_one({"customer_id": customer_id}, {"_id": 0})
    risk = db["risk_scores"].find_one({"customer_id": customer_id}, {"_id": 0})
    features = db["features"].find_one({"customer_id": customer_id}, {"_id": 0})
    interventions = list(db["interventions"].find({"customer_id": customer_id}, {"_id": 0}))
    
    data_context = {
        "customer_profile": customer,
        "risk_data": risk,
        "features": features,
        "interventions": interventions
    }

    logger.info(f"Generating Intelligence Report via DIRECT Python for {customer_id}...")
    response_text = _generate_direct_gemini(INTELLIGENCE_SYSTEM_PROMPT, prompt, data_context)

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


@st.cache_data(ttl=3600, show_spinner=False)
def generate_portfolio_analysis() -> dict | None:
    """Generate an AI Portfolio Risk Analysis Report via Gemini + MCP Tools."""
    prompt = build_portfolio_analysis_prompt()
    
    # 1. Fetch data directly from Mongo
    db = connect_to_mongo()
    risky_scores = list(db["risk_scores"].find({"risk_score": {"$gt": 50}}, {"_id": 0}))
    risky_cids = [r["customer_id"] for r in risky_scores]
    customers = list(db["Customers"].find({"customer_id": {"$in": risky_cids}}, {"_id": 0}))
    
    data_context = {
        "portfolio_risk_scores": risky_scores,
        "portfolio_customers": customers
    }

    logger.info("Generating Portfolio Analysis via DIRECT Python...")
    response_text = _generate_direct_gemini(PORTFOLIO_SYSTEM_PROMPT, prompt, data_context)

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


@st.cache_data(ttl=3600, show_spinner=False)
def generate_tier_analysis(tier_name: str) -> dict | None:
    """Generate an AI Tier Intelligence Report via Gemini + MCP Tools."""
    prompt = build_tier_analysis_prompt(tier_name)
    
    # 1. Fetch data directly from Mongo
    db = connect_to_mongo()
    customers = list(db["Customers"].find({"tier": tier_name}, {"_id": 0}))
    cids = [c["customer_id"] for c in customers]
    risk_scores = list(db["risk_scores"].find({"customer_id": {"$in": cids}}, {"_id": 0}))
    
    data_context = {
        "tier_customers": customers,
        "tier_risk_scores": risk_scores
    }

    logger.info(f"Generating Tier Intelligence Report for Tier {tier_name} via DIRECT Python...")
    response_text = _generate_direct_gemini(TIER_SYSTEM_PROMPT, prompt, data_context)

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
