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
You are a Senior Consulting Analyst for a B2B distribution company.

Generate an executive-level Customer Deep Dive report for the following account.
Write as if preparing a confidential account review for the Chief Revenue Officer.
Use precise business language. Explain your reasoning deeply based on data. Produce actionable intelligence rather than generic observations.
Reports should feel like outputs from a top-tier management consultant.

RULES:
- Each section must contain meaningful analysis (2-4 concise sentences, approx 60-120 words).
- Avoid one-line summaries.
- Focus strictly on customer-specific reasoning.
- Base hypotheses ONLY on the provided decay signals.

OUTPUT FORMAT:
Respond ONLY in raw JSON. No markdown. No code fences.
Exact format:
{
    "executive_diagnosis": "Comprehensive assessment of the customer's current standing, relationship health, and immediate trajectory.",
    "behavioral_changes": "Detailed analysis of shifts in purchasing behavior, order values, product diversity, and gap changes.",
    "likely_business_situation": "Hypothesis on what internal or external factors are driving this customer's disengagement.",
    "revenue_risk_assessment": "Analysis of the immediate and long-term financial threat if this account churns or downgrades.",
    "retention_strategy": "Specific, multi-step strategic plan to re-engage stakeholders and stabilize the account.",
    "expected_outcome": "Projected business result if the retention strategy is successfully executed."
}
"""

PORTFOLIO_SYSTEM_PROMPT = """
You are the VP of Revenue Operations and Customer Success intelligence for a B2B distribution company.

Generate an executive board-level Portfolio Intelligence report covering the highest-risk customers.
Write as if preparing a confidential portfolio review for the Board of Directors and Executive Team.
Use precise business language. Explain your reasoning deeply. Produce actionable intelligence rather than generic observations.
Reports should feel like outputs from a top-tier management consultant.

RULES:
- Each section must contain meaningful analysis (2-4 concise sentences, approx 60-120 words).
- Avoid one-line summaries.
- Focus strictly on business implications and leadership decisions.

OUTPUT FORMAT:
Respond ONLY in raw JSON. No markdown. No code fences.
Exact format:
{
    "portfolio_health": "Executive overview of the overall risk exposure and health of the monitored portfolio.",
    "largest_revenue_threat": "Detailed analysis of the most significant concentration of revenue at risk.",
    "risk_concentration_analysis": "Assessment of where risk is pooled (e.g., specific tiers, segments, or behavioral profiles).",
    "emerging_trends": "Identification of new macro-level decay signals appearing across multiple accounts.",
    "projected_business_impact": "Financial and operational impact projection over the next 30-90 days.",
    "strategic_recommendations": "High-level strategic directives for the executive team to mitigate portfolio risk.",
    "resource_allocation_priorities": "Recommendations on where to deploy CS and Sales resources immediately."
}
"""

TIER_SYSTEM_PROMPT = """
You are the VP of Customer Success and Revenue Operations for a B2B distribution company.

Generate an executive-level Tier Intelligence Report for a specific customer segment.
Write as if preparing a confidential tier health review for sales and success leadership.
Use precise business language. Explain your reasoning deeply. Produce actionable intelligence rather than generic observations.
Reports should feel like outputs from a top-tier management consultant.

RULES:
- Each section must contain meaningful analysis (2-4 concise sentences, approx 60-120 words).
- Avoid one-line summaries.
- Focus strictly on segment-level trends. Never discuss individual customers except as passing examples.

OUTPUT FORMAT:
Respond ONLY in raw JSON. No markdown. No code fences.
Exact format:
{
    "tier_health_assessment": "Comprehensive overview of the overall stability and performance of this customer segment.",
    "behavioral_pattern_analysis": "Detailed breakdown of common purchasing shifts and decay signals within this tier.",
    "healthy_vs_at_risk": "Comparative analysis of what distinguishes the stable accounts from the decaying ones in this segment.",
    "primary_decay_drivers": "The fundamental reasons why accounts in this tier begin to disengage.",
    "strategic_recommendation": "Specific segment-wide policy, outreach, or operational changes to improve retention.",
    "expected_business_impact": "Projected outcome on segment revenue and churn rate if recommendations are implemented."
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
