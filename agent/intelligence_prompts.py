# agent/intelligence_prompts.py
# ───────────────────────────────
# Gemini prompts for AI Customer Intelligence Reports.
# Follows the same pattern as agent/prompts.py.

import logging

logger = logging.getLogger(__name__)

# =========================================================
# SYSTEM PROMPT
# =========================================================

INTELLIGENCE_SYSTEM_PROMPT = """
You are a customer success intelligence analyst for a B2B distribution company.

Generate an executive-level intelligence report for the following customer account.
Write as if preparing a confidential account review for the customer success manager.
Use business language. Avoid technical jargon. Be specific and actionable.

LIKELY REASON RULES:
- You are forming a hypothesis, not stating a fact.
- Always use language like: "may indicate", "could suggest", "possibly"
- Never state a cause as certain. You do not have enough data to be certain.
- Base hypotheses ONLY on the provided decay signals.
- Do not invent information about competitors, pricing, contracts,
  supplier changes, budgets, or internal company decisions unless directly
  supported by the provided data.

OUTPUT FORMAT:
Respond ONLY in raw JSON. No markdown. No code fences. No explanation before or after.
Exact format:
{
    "executive_summary": "2-3 sentence overview of the customer's current situation and trajectory",
    "key_risk_drivers": "List the top 3 specific business factors driving this customer's risk score. Be concrete.",
    "likely_business_situation": "What is probably happening inside this customer's business? Why are they disengaging? (Follow Likely Reason Rules)",
    "potential_business_impact": "What revenue and relationship impact could occur if no action is taken?",
    "retention_opportunities": "What specific opportunities exist to re-engage this customer?",
    "recommended_next_actions": "3 specific, actionable steps the account manager should take this week",
    "priority_level": "High, Medium, or Low",
    "immediate_action": "The single most important thing to do right now",
    "expected_outcome": "What should happen if the recommended actions are followed?"
}
"""

PORTFOLIO_SYSTEM_PROMPT = """
You are the VP of Revenue Operations and Customer Success intelligence for a B2B distribution company.

Generate an executive-level Portfolio Risk Analysis report covering the top highest-risk customers.
Write as if preparing a confidential portfolio review for the VP of Sales and Customer Success Director.
Use business language. Avoid technical machine learning explanations. Be specific, strategic, and actionable.

LIKELY REASON RULES:
- You are forming a hypothesis based on behavioral signals, not stating absolute facts.
- Use language like: "may indicate", "suggests a trend of", "possibly driven by"
- Base hypotheses ONLY on the provided aggregated decay signals.
- Do not invent information about external market forces, specific competitors, pricing, or internal company decisions unless directly supported by the data.

OUTPUT FORMAT:
Respond ONLY in raw JSON. No markdown. No code fences. No explanation before or after.
Exact format:
{
    "executive_summary": "High-level summary of the portfolio's current risk exposure",
    "common_risk_patterns": "What behavioral patterns are shared among these at-risk customers?",
    "top_risk_drivers": "The primary factors driving decay across the portfolio",
    "tier_distribution": "Analysis of risk concentration across customer tiers (Gold/Silver/Bronze)",
    "emerging_trends": "What new trends are appearing in the decay signals?",
    "business_impact": "Potential revenue and relationship impact if these accounts churn",
    "recommended_actions": "Strategic portfolio-level actions for the success team",
    "executive_recommendation": "The single most important strategic directive"
}
"""

TIER_SYSTEM_PROMPT = """
You are the VP of Customer Success and Revenue Operations for a B2B distribution company.

Generate an executive-level Tier Intelligence Report for a specific customer tier.
Write as if preparing a confidential tier health review for sales and success leadership.
Use business language. Avoid technical machine learning explanations. Be specific, strategic, and actionable.

LIKELY REASON RULES:
- You are forming a hypothesis based on behavioral signals, not stating absolute facts.
- Use language like: "may indicate", "suggests a trend of", "possibly driven by"
- Base hypotheses ONLY on the provided aggregated decay signals.
- Do not invent information about external market forces, specific competitors, pricing, or internal company decisions unless directly supported by the data.

OUTPUT FORMAT:
Respond ONLY in raw JSON. No markdown. No code fences. No explanation before or after.
Exact format:
{
    "executive_summary": "High-level summary of the health and risk profile of this customer tier",
    "customer_count": "Brief statement of total customer volume in this tier",
    "average_risk_score": "Brief summary of average risk and exposure in this tier",
    "risk_distribution": "Analysis of risk concentration across different segments within this tier",
    "top_risk_drivers": "The primary factors driving decay in this tier",
    "highest_risk_customers": "Strategic concerns regarding the top at-risk accounts in this tier",
    "behavioral_patterns": "What behavioral patterns are common in the disengaging customers of this tier?",
    "business_impact": "Potential revenue and relationship impact if these accounts churn",
    "recommended_actions": "Strategic tier-level actions for the success team",
    "executive_recommendation": "The single most important strategic directive"
}
"""

# =========================================================
# REQUIRED FIELDS FOR VALIDATION
# =========================================================

REQUIRED_INPUT_FIELDS = [
    "customer_id",
    "company_name",
    "tier"
]


def _safe_float(val, default: float = 0.0) -> float:
    """Safely convert val to float. Handle None, NaN, invalid inputs without raising errors."""
    if val is None:
        return default
    try:
        import pandas as pd
        if pd.isna(val):
            return default
    except ImportError:
        if val != val:
            return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _fmt(val, fallback: str = "\u2014") -> str:
    """Format a value for prompt interpolation — handles None, NaN, empty."""
    if val is None:
        return fallback
    try:
        import pandas as pd
        if pd.isna(val) or str(val).strip() == "":
            return fallback
    except ImportError:
        if val != val or str(val).strip() == "":
            return fallback
    return str(val)


def build_intelligence_prompt(cust, risk=None, intv=None) -> str:
    """Build the data portion of the intelligence prompt from customer records.

    Parameters
    ----------
    cust  : pd.Series — customer profile row
    risk  : pd.Series or None — risk_scores row
    intv  : pd.Series or None — first intervention row

    Returns
    -------
    str — formatted customer data section for the prompt.
    """
    missing = [
        field for field in REQUIRED_INPUT_FIELDS
        if field not in cust or cust[field] is None
    ]

    if missing:
        logger.warning(
            f"Intelligence prompt missing fields for customer "
            f"{cust.get('customer_id', 'UNKNOWN')}: {missing}. "
            f"Gemini reasoning may be inaccurate."
        )

    company = _fmt(cust.get("company_name"))
    cid = _fmt(cust.get("customer_id"))
    tier = _fmt(cust.get("tier"))
    city = _fmt(cust.get("city"))
    acct_mgr = _fmt(cust.get("account_manager"))

    prompt = f"""
CUSTOMER PROFILE:
- Company: {company}
- Customer ID: {cid}
- Tier: {tier}
- City: {city}
- Account Manager: {acct_mgr}
"""

    if risk is not None:
        prompt += f"""
RISK ASSESSMENT:
- Risk Score: {_safe_float(risk.get('risk_score', 0)):.1f} / 100
- Risk Label: {_fmt(risk.get('risk_label'))}
- Business Risk Score: {_safe_float(risk.get('business_risk_score', 0)):.1f}
- Anomaly Risk Score: {_safe_float(risk.get('anomaly_risk_score', 0)):.1f}
- Is Anomaly: {bool(risk.get('is_anomaly', False))}

BEHAVIORAL SIGNALS:
- Average Order Value Change: {_safe_float(risk.get('aov_change_pct', 0)):+.1f}%
- Purchase Gap Change: {_safe_float(risk.get('gap_change_pct', 0)):+.1f}%
- Product Diversity Delta: {_safe_float(risk.get('diversity_delta', 0)):+.2f}
"""

    if intv is not None:
        prompt += f"""
EXISTING INTERVENTION DATA:
- Decay Summary: {_fmt(intv.get('decay_summary'), 'Not available')}
- Priority Reason: {_fmt(intv.get('priority_reason'), 'Not available')}
- Likely Reason: {_fmt(intv.get('likely_reason'), 'Not available')}
- Primary Action: {_fmt(intv.get('primary_action'), 'Not available')}
- Secondary Action: {_fmt(intv.get('secondary_action'), 'Not available')}
- Urgency: {_fmt(intv.get('urgency'), 'Not available')}
"""

    return prompt.strip()


def build_portfolio_analysis_prompt(top_risk_df) -> str:
    """Build the data portion of the portfolio analysis prompt.

    Parameters
    ----------
    top_risk_df : pd.DataFrame — top highest-risk customers with profile and risk scores.

    Returns
    -------
    str — formatted portfolio data section.
    """
    if top_risk_df is None or top_risk_df.empty:
        return "No risk data available."

    total_customers = len(top_risk_df)
    avg_risk = _safe_float(top_risk_df['risk_score'].mean()) if 'risk_score' in top_risk_df.columns else 0.0

    if 'tier' in top_risk_df.columns:
        tiers = top_risk_df['tier'].value_counts().to_dict()
        tier_str = ", ".join([f"{k}: {v}" for k, v in tiers.items()])
    else:
        tier_str = "Unknown"

    if 'risk_label' in top_risk_df.columns:
        labels = top_risk_df['risk_label'].value_counts().to_dict()
        label_str = ", ".join([f"{k}: {v}" for k, v in labels.items()])
    else:
        label_str = "Unknown"

    prompt = f"""
PORTFOLIO OVERVIEW (TOP {total_customers} AT-RISK ACCOUNTS):
- Average Risk Score: {avg_risk:.1f} / 100
- Tier Distribution: {tier_str}
- Risk Segment Distribution: {label_str}

ACCOUNT DETAILS:
"""

    for _, row in top_risk_df.head(20).iterrows():
        cid = _fmt(row.get('customer_id'))
        company = _fmt(row.get('company_name'))
        tier = _fmt(row.get('tier'))
        score = _safe_float(row.get('risk_score', 0))
        label = _fmt(row.get('risk_label'))

        aov = _safe_float(row.get('aov_change_pct', 0))
        gap = _safe_float(row.get('gap_change_pct', 0))
        div_d = _safe_float(row.get('diversity_delta', 0))

        prompt += f"- {company} ({cid}) | Tier: {tier} | Score: {score:.1f} ({label}) | AOV: {aov:+.1f}% | Gap: {gap:+.1f}% | Div Δ: {div_d:+.2f}\n"

    return prompt.strip()


def build_tier_analysis_prompt(tier_name: str, tier_df) -> str:
    """Build the data portion of the tier intelligence prompt.

    Parameters
    ----------
    tier_name : str — the name of the tier (e.g. Gold, Silver, Bronze)
    tier_df : pd.DataFrame — customer and risk data filtered for this tier

    Returns
    -------
    str — formatted tier data section.
    """
    if tier_df is None or tier_df.empty:
        return f"No customer data available for Tier: {tier_name}."

    total_customers = len(tier_df)
    avg_risk = _safe_float(tier_df['risk_score'].mean()) if 'risk_score' in tier_df.columns else 0.0

    if 'risk_label' in tier_df.columns:
        labels = tier_df['risk_label'].value_counts().to_dict()
        label_str = ", ".join([f"{k}: {v}" for k, v in labels.items()])
    else:
        label_str = "Unknown"

    avg_aov = _safe_float(tier_df['aov_change_pct'].mean()) if 'aov_change_pct' in tier_df.columns else 0.0
    avg_gap = _safe_float(tier_df['gap_change_pct'].mean()) if 'gap_change_pct' in tier_df.columns else 0.0
    avg_div_d = _safe_float(tier_df['diversity_delta'].mean()) if 'diversity_delta' in tier_df.columns else 0.0

    prompt = f"""
TIER ANALYSIS OVERVIEW:
- Customer Tier: {tier_name}
- Total Customer Count: {total_customers}
- Average Risk Score: {avg_risk:.1f} / 100
- Risk Segment Distribution: {label_str}
- Average Behavioral Signals in Tier:
  * Avg Average Order Value Change: {avg_aov:+.1f}%
  * Avg Purchase Gap Change: {avg_gap:+.1f}%
  * Avg Product Diversity Delta: {avg_div_d:+.2f}

TOP AT-RISK ACCOUNTS IN THIS TIER:
"""
    top_at_risk = tier_df
    if 'risk_score' in tier_df.columns:
        top_at_risk = tier_df.sort_values(by='risk_score', ascending=False)

    for _, row in top_at_risk.head(10).iterrows():
        cid = _fmt(row.get('customer_id'))
        company = _fmt(row.get('company_name'))
        score = _safe_float(row.get('risk_score', 0))
        label = _fmt(row.get('risk_label'))
        aov = _safe_float(row.get('aov_change_pct', 0))
        gap = _safe_float(row.get('gap_change_pct', 0))
        div_d = _safe_float(row.get('diversity_delta', 0))

        prompt += f"- {company} ({cid}) | Score: {score:.1f} ({label}) | AOV: {aov:+.1f}% | Gap: {gap:+.1f}% | Div Δ: {div_d:+.2f}\n"

    return prompt.strip()
