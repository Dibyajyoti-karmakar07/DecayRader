"""
dashboard/pages/03_customer_detail.py
─────────────────────────────────────
Customer Deep Dive — profile card, risk gauge, signal breakdown,
risk explanation, intervention history, and executive summary.
"""

import os
import sys

_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.db import connect_to_mongo
from agent.intelligence_client import generate_customer_intelligence

# ╭──────────────────────────────────────────────────────────────────────────╮
# │  THEME CSS                                                              │
# ╰──────────────────────────────────────────────────────────────────────────╯
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    :root {
        --bg-primary:   #0a0a0a;
        --bg-surface:   #111111;
        --bg-card:      #161616;
        --border:       #1e1e1e;
        --border-hover: #2a2a2a;
        --text-h:       #ededed;
        --text-p:       #a1a1a1;
        --text-muted:   #555555;
        --cyan:         #00dfd8;
        --blue:         #007cf0;
        --violet:       #7928ca;
        --pink:         #ff0080;
        --amber:        #f9cb28;
        --red:          #ff4d6a;
        --green:        #50e3c2;
        --gradient:     linear-gradient(135deg, #007cf0, #00dfd8, #7928ca, #ff0080);
        --r-sm:         6px;
        --r-md:         10px;
        --r-lg:         14px;
    }

    .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stHeader"] {
        background-color: var(--bg-primary) !important;
    }
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d0d0d, #111111) !important;
        border-right: 1px solid var(--border) !important;
    }
    html, body, [class*="css"] {
        font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
    }
    h1, h2, h3 {
        font-family: 'Inter', system-ui, sans-serif !important;
        color: var(--text-h) !important; letter-spacing: -0.03em;
    }

    /* ── page header ────────────────────────────────────────────────── */
    .page-header { margin-bottom: 0.2rem; }
    .page-header h1 {
        font-size: 1.55rem; font-weight: 600; margin: 0;
        color: var(--text-h) !important;
    }
    .page-sub { font-size: 0.85rem; color: var(--text-muted); margin-top: 2px; }

    /* ── section title ──────────────────────────────────────────────── */
    .sec-title {
        font-size: 1rem; font-weight: 600; color: var(--text-h);
        margin: 1.5rem 0 0.5rem; letter-spacing: -0.02em;
    }

    /* ── profile card ───────────────────────────────────────────────── */
    .profile-card {
        background: var(--bg-card); border: 1px solid var(--border);
        border-radius: var(--r-lg); padding: 1.6rem 1.8rem;
        position: relative; overflow: hidden;
    }
    .profile-card::before {
        content: ''; position: absolute; top: 0; left: 0; right: 0;
        height: 3px; background: var(--gradient);
    }
    .profile-header {
        display: flex; align-items: center; gap: 16px;
        margin-bottom: 1.1rem;
    }
    .profile-avatar {
        width: 52px; height: 52px; border-radius: 12px;
        background: linear-gradient(135deg, #007cf0, #00dfd8);
        display: flex; align-items: center; justify-content: center;
        font-size: 1.4rem; font-weight: 700; color: #fff;
        flex-shrink: 0;
    }
    .profile-name {
        font-size: 1.25rem; font-weight: 600; color: var(--text-h);
        letter-spacing: -0.02em; line-height: 1.2;
    }
    .profile-id {
        font-size: 0.72rem; color: var(--text-muted);
        font-family: 'JetBrains Mono', monospace; margin-top: 2px;
    }
    .profile-grid {
        display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
        gap: 0.9rem; margin-top: 0.5rem;
    }
    .profile-field .pf-label {
        font-size: 0.66rem; text-transform: uppercase; letter-spacing: 0.07em;
        color: var(--text-muted); font-family: 'JetBrains Mono', monospace;
        margin-bottom: 3px;
    }
    .profile-field .pf-value {
        font-size: 0.92rem; color: var(--text-h); font-weight: 500;
    }

    /* ── tier + risk badges ─────────────────────────────────────────── */
    .badge-pill {
        display: inline-block; padding: 2px 10px; border-radius: 100px;
        font-size: 0.72rem; font-weight: 500;
        font-family: 'JetBrains Mono', monospace;
    }
    .bp-critical  { background: rgba(255,77,106,.12); color: #ff4d6a; }
    .bp-atrisk    { background: rgba(249,203,40,.12); color: #f9cb28; }
    .bp-watch     { background: rgba(0,124,240,.12);  color: #007cf0; }
    .bp-healthy   { background: rgba(80,227,194,.12); color: #50e3c2; }
    .bp-gold      { background: rgba(249,203,40,.1);  color: #f9cb28; }
    .bp-silver    { background: rgba(161,161,161,.1); color: #a1a1a1; }
    .bp-bronze    { background: rgba(205,127,50,.12); color: #cd7f32; }

    /* Utilities */
    .empty-state {
        color: var(--text-muted);
        font-style: italic;
    }

    /* ── risk score cards ───────────────────────────────────────────── */
    .rs-grid {
        display: grid; grid-template-columns: repeat(3, 1fr);
        gap: 0.9rem; margin-top: 0.6rem;
    }
    @media (max-width: 700px) { .rs-grid { grid-template-columns: 1fr; } }
    .rs-card {
        background: var(--bg-surface); border: 1px solid var(--border);
        border-radius: var(--r-md); padding: 1rem 1.2rem;
        text-align: center;
    }
    .rs-val {
        font-size: 1.55rem; font-weight: 700; letter-spacing: -0.03em;
    }
    .rs-lbl {
        font-size: 0.68rem; color: var(--text-muted); margin-top: 4px;
        font-family: 'JetBrains Mono', monospace;
        text-transform: uppercase; letter-spacing: 0.06em;
    }

    /* ── signal bars ────────────────────────────────────────────────── */
    .sig-grid {
        display: grid; grid-template-columns: repeat(3, 1fr);
        gap: 1rem; margin-top: 0.5rem;
    }
    @media (max-width: 700px) { .sig-grid { grid-template-columns: 1fr; } }
    .sig-card {
        background: var(--bg-card); border: 1px solid var(--border);
        border-radius: var(--r-md); padding: 1.1rem 1.3rem;
    }
    .sig-label {
        font-size: 0.68rem; color: var(--text-muted);
        font-family: 'JetBrains Mono', monospace;
        text-transform: uppercase; letter-spacing: 0.06em;
        margin-bottom: 6px;
    }
    .sig-val {
        font-size: 1.35rem; font-weight: 700; letter-spacing: -0.02em;
        margin-bottom: 6px;
    }
    .sig-bar-track {
        height: 6px; border-radius: 3px; background: #1e1e1e;
        overflow: hidden; position: relative;
    }
    .sig-bar-fill {
        height: 100%; border-radius: 3px;
        position: absolute; top: 0;
    }

    /* ── explanation panel ───────────────────────────────────────────── */
    .expl-card {
        background: var(--bg-card); border: 1px solid var(--border);
        border-radius: var(--r-md); padding: 1.2rem 1.4rem;
        margin-bottom: 0.8rem;
    }
    .expl-card h4 {
        font-size: 0.78rem; font-weight: 600; color: var(--text-muted);
        text-transform: uppercase; letter-spacing: 0.05em;
        font-family: 'JetBrains Mono', monospace;
        margin: 0 0 0.4rem;
    }
    .expl-card p {
        font-size: 0.9rem; color: var(--text-p); line-height: 1.7;
        margin: 0;
    }

    /* ── history table ──────────────────────────────────────────────── */
    .ht-wrap {
        background: var(--bg-card); border: 1px solid var(--border);
        border-radius: var(--r-md); overflow-x: auto; margin-top: 0.4rem;
    }
    .ht {
        width: 100%; border-collapse: collapse; font-size: 0.82rem;
    }
    .ht th {
        text-align: left; padding: 10px 12px; color: var(--text-muted);
        border-bottom: 1px solid var(--border); font-weight: 500;
        text-transform: uppercase; font-size: 0.68rem;
        letter-spacing: 0.06em;
        font-family: 'JetBrains Mono', monospace; white-space: nowrap;
    }
    .ht td {
        padding: 9px 12px; color: var(--text-p);
        border-bottom: 1px solid #1a1a1a;
    }
    .ht tr:last-child td { border-bottom: none; }
    .ht tr:hover td { background: rgba(255,255,255,.02); }

    /* ── urgency / status ───────────────────────────────────────────── */
    .urg { display: inline-block; padding: 2px 10px; border-radius: 100px;
           font-size: 0.72rem; font-weight: 500;
           font-family: 'JetBrains Mono', monospace; }
    .urg-high   { background: rgba(255,77,106,.12); color: #ff4d6a; }
    .urg-medium { background: rgba(249,203,40,.12); color: #f9cb28; }
    .urg-low    { background: rgba(80,227,194,.12); color: #50e3c2; }
    .st-badge { display: inline-block; padding: 2px 10px; border-radius: 100px;
                font-size: 0.72rem; font-weight: 500;
                font-family: 'JetBrains Mono', monospace; }
    .st-pending   { background: rgba(249,203,40,.12); color: #f9cb28; }
    .st-completed { background: rgba(80,227,194,.12); color: #50e3c2; }
    .st-cancelled { background: rgba(85,85,85,.15);   color: #888; }

    /* ── exec summary ───────────────────────────────────────────────── */
    .exec-card {
        background: var(--bg-card); border: 1px solid var(--border);
        border-radius: var(--r-lg); padding: 1.4rem 1.6rem;
        position: relative; overflow: hidden; margin-top: 0.5rem;
    }
    .exec-card::before {
        content: ''; position: absolute; top: 0; left: 0;
        width: 3px; height: 100%; background: var(--violet);
    }
    .exec-card p {
        font-size: 0.92rem; color: var(--text-p); line-height: 1.8; margin: 0;
    }

    /* ── hide chrome ────────────────────────────────────────────────── */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header[data-testid="stHeader"] {background: transparent !important;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ╭──────────────────────────────────────────────────────────────────────────╮
# │  DATA LOADING                                                           │
# ╰──────────────────────────────────────────────────────────────────────────╯

@st.cache_data(ttl=120, show_spinner=False)
def load_customers() -> pd.DataFrame:
    db = connect_to_mongo()
    df = pd.DataFrame(list(db["Customers"].find()))
    df.drop(columns=["_id"], errors="ignore", inplace=True)
    return df


@st.cache_data(ttl=120, show_spinner=False)
def load_risk_scores() -> pd.DataFrame:
    db = connect_to_mongo()
    df = pd.DataFrame(list(db["risk_scores"].find()))
    df.drop(columns=["_id"], errors="ignore", inplace=True)
    return df


@st.cache_data(ttl=60, show_spinner=False)
def load_interventions() -> pd.DataFrame:
    db = connect_to_mongo()
    df = pd.DataFrame(list(db["interventions"].find()))
    df.drop(columns=["_id"], errors="ignore", inplace=True)
    return df


# ╭──────────────────────────────────────────────────────────────────────────╮
# │  HELPERS                                                                │
# ╰──────────────────────────────────────────────────────────────────────────╯

def _safe(val, fallback: str = "—") -> str:
    if pd.isna(val) or val is None or str(val).strip() == "":
        return fallback
    return str(val)


def _risk_cls(label: str) -> str:
    return {"Critical": "bp-critical", "At Risk": "bp-atrisk",
            "Watch": "bp-watch", "Healthy": "bp-healthy"}.get(str(label), "")


def _risk_color(label: str) -> str:
    return {"Critical": "#ff4d6a", "At Risk": "#f9cb28",
            "Watch": "#007cf0", "Healthy": "#50e3c2"}.get(str(label), "#555")


def _score_color(score: float) -> str:
    if score >= 76: return "#ff4d6a"
    if score >= 51: return "#f9cb28"
    if score >= 31: return "#007cf0"
    return "#50e3c2"


def _tier_cls(tier: str) -> str:
    return {"Gold": "bp-gold", "Silver": "bp-silver",
            "Bronze": "bp-bronze"}.get(str(tier), "")


def _urgency_badge(val: str) -> str:
    u = str(val).strip().lower()
    cls = {"high": "urg-high", "medium": "urg-medium", "low": "urg-low"}.get(u, "")
    return f'<span class="urg {cls}">{val}</span>'


def _status_badge(val: str) -> str:
    s = str(val).strip().lower()
    cls = {"pending": "st-pending", "completed": "st-completed",
           "cancelled": "st-cancelled"}.get(s, "")
    return f'<span class="st-badge {cls}">{val}</span>'


# ╭──────────────────────────────────────────────────────────────────────────╮
# │  LOAD DATA                                                              │
# ╰──────────────────────────────────────────────────────────────────────────╯
try:
    customers_df = load_customers()
    risk_df = load_risk_scores()
    interventions_df = load_interventions()
except Exception as exc:
    st.error(f"Failed to load data from MongoDB: {exc}")
    st.stop()

# ╭──────────────────────────────────────────────────────────────────────────╮
# │  PAGE HEADER                                                            │
# ╰──────────────────────────────────────────────────────────────────────────╯
st.markdown(
    """
    <div class="page-header">
        <h1>👤 Customer Detail</h1>
        <div class="page-sub">
            Review detailed behavioral risk analysis, deep dive intelligence, and historical interventions for a specific account.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ╭──────────────────────────────────────────────────────────────────────────╮
# │  CUSTOMER SELECTOR                                                      │
# ╰──────────────────────────────────────────────────────────────────────────╯
if customers_df.empty:
    st.warning("No customers found in the database.")
    st.stop()

# Build lookup: display company_name, track customer_id
cust_options = customers_df[["customer_id", "company_name"]].drop_duplicates()
cust_options = cust_options.sort_values("company_name").reset_index(drop=True)
display_names = cust_options["company_name"].tolist()

selected_name = st.selectbox(
    "Select a customer",
    display_names,
    index=0,
    placeholder="Choose a company…",
)

selected_id = cust_options.loc[
    cust_options["company_name"] == selected_name, "customer_id"
].values[0]

# ── Fetch rows for selected customer ───────────────────────────────────────
cust_row = customers_df[customers_df["customer_id"] == selected_id].iloc[0]
risk_row = risk_df[risk_df["customer_id"] == selected_id]
has_risk = not risk_row.empty
if has_risk:
    risk_row = risk_row.iloc[0]

intv_rows = interventions_df[interventions_df["customer_id"] == selected_id] if not interventions_df.empty else pd.DataFrame()
has_intv = not intv_rows.empty
intv_first = intv_rows.iloc[0] if has_intv else None

# ╭──────────────────────────────────────────────────────────────────────────╮
# │  PROFILE + GAUGE  (two-column)                                          │
# ╰──────────────────────────────────────────────────────────────────────────╯
col_profile, col_gauge = st.columns([1.3, 1], gap="large")

# ── 3. Profile Card ────────────────────────────────────────────────────────
with col_profile:
    company = _safe(cust_row.get("company_name"))
    initials = "".join(w[0] for w in company.split()[:2]).upper() if company != "—" else "?"
    tier = _safe(cust_row.get("tier"))
    tier_cls = _tier_cls(tier)

    st.markdown(
        f"""
        <div class="profile-card">
            <div class="profile-header">
                <div class="profile-avatar">{initials}</div>
                <div>
                    <div class="profile-name">{company}</div>
                    <div class="profile-id">ID: {selected_id}</div>
                </div>
            </div>
            <div class="profile-grid">
                <div class="profile-field">
                    <div class="pf-label">City</div>
                    <div class="pf-value">{_safe(cust_row.get('city'))}</div>
                </div>
                <div class="profile-field">
                    <div class="pf-label">Tier</div>
                    <div class="pf-value"><span class="badge-pill {tier_cls}">{tier}</span></div>
                </div>
                <div class="profile-field">
                    <div class="pf-label">Account Manager</div>
                    <div class="pf-value">{_safe(cust_row.get('account_manager'))}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ── 4. Risk Analysis — Gauge ───────────────────────────────────────────────
with col_gauge:
    if has_risk:
        score = float(risk_row.get("risk_score", 0))
        label = _safe(risk_row.get("risk_label"))
        sc_color = _score_color(score)
        lbl_cls = _risk_cls(label)

        fig_gauge = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=score,
                number=dict(
                    font=dict(size=42, color=sc_color, family="Inter"),
                    suffix="",
                ),
                gauge=dict(
                    axis=dict(range=[0, 100], tickwidth=0, tickcolor="#1e1e1e",
                              tickfont=dict(color="#555", size=10)),
                    bar=dict(color=sc_color, thickness=0.35),
                    bgcolor="#1e1e1e",
                    borderwidth=0,
                    steps=[
                        dict(range=[0, 30], color="rgba(80,227,194,.08)"),
                        dict(range=[30, 50], color="rgba(0,124,240,.08)"),
                        dict(range=[50, 75], color="rgba(249,203,40,.08)"),
                        dict(range=[75, 100], color="rgba(255,77,106,.08)"),
                    ],
                    threshold=dict(
                        line=dict(color=sc_color, width=3),
                        thickness=0.8,
                        value=score,
                    ),
                ),
            )
        )
        fig_gauge.update_layout(
            paper_bgcolor="#0a0a0a",
            plot_bgcolor="#0a0a0a",
            font=dict(family="Inter", color="#a1a1a1"),
            height=220,
            margin=dict(l=30, r=30, t=40, b=10),
        )
        st.plotly_chart(fig_gauge, use_container_width=True, config={"displayModeBar": False})

        # Sub-scores
        brs = float(risk_row.get("business_risk_score", 0))
        ars = float(risk_row.get("anomaly_risk_score", 0))
        st.markdown(
            f"""
            <div class="rs-grid">
                <div class="rs-card">
                    <div class="rs-val" style="color:{sc_color}">
                        <span class="badge-pill {lbl_cls}">{label}</span>
                    </div>
                    <div class="rs-lbl">Risk Label</div>
                </div>
                <div class="rs-card">
                    <div class="rs-val" style="color:var(--blue)">{brs:.1f}</div>
                    <div class="rs-lbl">Business Risk</div>
                </div>
                <div class="rs-card">
                    <div class="rs-val" style="color:var(--violet)">{ars:.1f}</div>
                    <div class="rs-lbl">Anomaly Risk</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div style="background:var(--bg-card);border:1px solid var(--border);
                        border-radius:var(--r-md);padding:2rem;text-align:center;margin-top:1rem">
                <div style="font-size:1.6rem;margin-bottom:.4rem">📊</div>
                <div style="font-size:.92rem;color:var(--text-h);font-weight:600;
                            margin-bottom:.2rem">No risk score data</div>
                <div style="font-size:.82rem;color:var(--text-muted);line-height:1.5">
                    Risk scores have not been computed for this customer yet.
                    Run the data pipeline to generate scores.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ╭──────────────────────────────────────────────────────────────────────────╮
# │  5. SIGNAL BREAKDOWN                                                    │
# ╰──────────────────────────────────────────────────────────────────────────╯
if has_risk:
    st.markdown('<div class="sec-title">Signal Breakdown</div>', unsafe_allow_html=True)

    signals = [
        ("AOV Change", "aov_change_pct"),
        ("Gap Change", "gap_change_pct"),
        ("Diversity Δ", "diversity_delta"),
    ]

    cards_html = '<div class="sig-grid">'
    for sig_label, field in signals:
        raw = risk_row.get(field, 0)
        try:
            val = float(raw)
        except (ValueError, TypeError):
            val = 0.0

        is_neg = val < 0
        color = "#ff4d6a" if is_neg else "#50e3c2"
        abs_val = abs(val)
        bar_pct = min(abs_val, 100)

        # For the bar: negative fills from right, positive from left
        if is_neg:
            fill_style = f"right:0;width:{bar_pct}%;background:{color}"
        else:
            fill_style = f"left:0;width:{bar_pct}%;background:{color}"

        cards_html += f"""
        <div class="sig-card">
            <div class="sig-label">{sig_label}</div>
            <div class="sig-val" style="color:{color}">{val:+.2f}%</div>
            <div class="sig-bar-track">
                <div class="sig-bar-fill" style="{fill_style}"></div>
            </div>
        </div>"""

    cards_html += "</div>"
    st.markdown(cards_html, unsafe_allow_html=True)

# ╭──────────────────────────────────────────────────────────────────────────╮
# │  6. RISK EXPLANATION PANEL                                              │
# ╰──────────────────────────────────────────────────────────────────────────╯
# Fields come from interventions if present
_likely = _safe(intv_first.get("likely_reason") if has_intv else None, "")
_priority = _safe(intv_first.get("priority_reason") if has_intv else None, "")
_decay = _safe(intv_first.get("decay_summary") if has_intv else None, "")

if _likely or _priority or _decay:
    st.markdown('<div class="sec-title">Risk Explanation</div>', unsafe_allow_html=True)

    col_e1, col_e2 = st.columns(2, gap="medium")
    with col_e1:
        if _decay:
            st.markdown(
                f'<div class="expl-card"><h4>Decay Summary</h4><p>{_decay}</p></div>',
                unsafe_allow_html=True,
            )
        if _likely:
            st.markdown(
                f'<div class="expl-card"><h4>Likely Reason</h4><p>{_likely}</p></div>',
                unsafe_allow_html=True,
            )
    with col_e2:
        if _priority:
            st.markdown(
                f'<div class="expl-card"><h4>Priority Reason</h4><p>{_priority}</p></div>',
                unsafe_allow_html=True,
            )

# ╭──────────────────────────────────────────────────────────────────────────╮
# │  7. INTERVENTION HISTORY                                                │
# ╰──────────────────────────────────────────────────────────────────────────╯
st.markdown('<div class="sec-title">Intervention History</div>', unsafe_allow_html=True)

if not has_intv:
    st.markdown(
        """
        <div style="background:var(--bg-card);border:1px solid var(--border);
                    border-radius:var(--r-md);padding:1.8rem;text-align:center;margin-top:.4rem">
            <div style="font-size:1.6rem;margin-bottom:.4rem">📨</div>
            <div style="font-size:.92rem;color:var(--text-h);font-weight:600;
                        margin-bottom:.2rem">No interventions yet</div>
            <div style="font-size:.82rem;color:var(--text-muted);line-height:1.5">
                This customer has not been analyzed by the Agent Console.
                Run the AI agent to generate intervention recommendations.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    rows_html = ""
    for _, r in intv_rows.iterrows():
        rows_html += f"""
        <tr>
            <td>{_safe(r.get('primary_action'))}</td>
            <td style="color:var(--text-muted);font-size:.8rem">{_safe(r.get('secondary_action'))}</td>
            <td>{_urgency_badge(_safe(r.get('urgency')))}</td>
            <td>{_status_badge(_safe(r.get('status')))}</td>
            <td style="font-family:'JetBrains Mono',monospace;font-size:.75rem">{_safe(r.get('approved_at'))}</td>
            <td style="font-family:'JetBrains Mono',monospace;font-size:.75rem">{_safe(r.get('follow_up_date'))}</td>
            <td style="font-family:'JetBrains Mono',monospace;font-size:.75rem">{_safe(r.get('completed_at'))}</td>
        </tr>"""

    st.markdown(
        f"""
        <div class="ht-wrap">
            <table class="ht">
                <thead><tr>
                    <th>Primary Action</th>
                    <th>Secondary</th>
                    <th>Urgency</th>
                    <th>Status</th>
                    <th>Approved At</th>
                    <th>Follow-up</th>
                    <th>Completed At</th>
                </tr></thead>
                <tbody>{rows_html}</tbody>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ╭──────────────────────────────────────────────────────────────────────────╮
# │  8. EXECUTIVE SUMMARY                                                   │
# ╰──────────────────────────────────────────────────────────────────────────╯
st.markdown('<div class="sec-title">Executive Summary</div>', unsafe_allow_html=True)

# Build summary from available data
summary_parts: list[str] = []

if has_risk:
    score = float(risk_row.get("risk_score", 0))
    label = _safe(risk_row.get("risk_label"))
    company = _safe(cust_row.get("company_name"))
    summary_parts.append(
        f"<strong style='color:var(--text-h)'>{company}</strong> currently has a "
        f"risk score of <strong style='color:{_score_color(score)}'>{score:.1f}</strong>, "
        f"placing them in the <strong style='color:{_risk_color(label)}'>{label}</strong> segment."
    )

    # Signal commentary
    aov = float(risk_row.get("aov_change_pct", 0))
    gap = float(risk_row.get("gap_change_pct", 0))
    div_d = float(risk_row.get("diversity_delta", 0))

    signal_notes = []
    if aov < -5:
        signal_notes.append(f"declining average order value ({aov:+.1f}%)")
    elif aov > 5:
        signal_notes.append(f"increasing average order value ({aov:+.1f}%)")

    if gap > 10:
        signal_notes.append(f"widening purchase gaps ({gap:+.1f}%)")
    elif gap < -10:
        signal_notes.append(f"shortening purchase gaps ({gap:+.1f}%)")

    if div_d < -0.5:
        signal_notes.append(f"reduced category diversity ({div_d:+.2f})")
    elif div_d > 0.5:
        signal_notes.append(f"increased category diversity ({div_d:+.2f})")

    if signal_notes:
        summary_parts.append(
            "The customer has experienced " + ", ".join(signal_notes) + "."
        )

if has_intv:
    primary = _safe(intv_first.get("primary_action"))
    secondary = _safe(intv_first.get("secondary_action"))
    urgency = _safe(intv_first.get("urgency"))

    action_text = f"Recommended intervention is <strong style='color:var(--text-h)'>{primary}</strong>"
    if secondary and secondary != "—":
        action_text += f" followed by <strong style='color:var(--text-h)'>{secondary}</strong>"
    action_text += f" with <strong>{urgency}</strong> urgency."
    summary_parts.append(action_text)

if not summary_parts:
    summary_parts.append("Insufficient data to generate an executive summary for this customer.")

st.markdown(
    f"""
    <div class="exec-card">
        <p>{'<br><br>'.join(summary_parts)}</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ╭──────────────────────────────────────────────────────────────────────────╮
# │  9. AI CUSTOMER INTELLIGENCE REPORT                                      │
# ╰──────────────────────────────────────────────────────────────────────────╯

st.markdown(
    '<div class="sec-title" style="margin-top:2.2rem">🧠 AI Customer Intelligence Report</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div style="font-size:.82rem;color:var(--text-muted);margin-bottom:.8rem">'
    'Gemini-powered executive analysis for account managers and customer success teams.</div>',
    unsafe_allow_html=True,
)


# ── 9a. Risk Assessment Summary ────────────────────────────────────────────
if has_risk:
    score = float(risk_row.get("risk_score", 0))
    label = _safe(risk_row.get("risk_label"))
    brs = float(risk_row.get("business_risk_score", 0))
    ars = float(risk_row.get("anomaly_risk_score", 0))
    is_anomaly = bool(risk_row.get("is_anomaly", False))
    sc_color = _score_color(score)

    st.markdown(
        f"""
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:.8rem;margin-bottom:1rem">
            <div style="background:var(--bg-card);border:1px solid var(--border);
                        border-radius:var(--r-md);padding:1rem 1.2rem;text-align:center">
                <div style="font-size:1.4rem;font-weight:700;color:{sc_color};line-height:1">{score:.1f}</div>
                <div style="font-size:.68rem;color:var(--text-muted);margin-top:4px;
                            font-family:'JetBrains Mono',monospace;text-transform:uppercase;
                            letter-spacing:.06em">Risk Score</div>
            </div>
            <div style="background:var(--bg-card);border:1px solid var(--border);
                        border-radius:var(--r-md);padding:1rem 1.2rem;text-align:center">
                <div style="font-size:1rem;font-weight:600;color:{_risk_color(label)};line-height:1.4">
                    <span class="badge-pill {_risk_cls(label)}">{label}</span></div>
                <div style="font-size:.68rem;color:var(--text-muted);margin-top:4px;
                            font-family:'JetBrains Mono',monospace;text-transform:uppercase;
                            letter-spacing:.06em">Risk Label</div>
            </div>
            <div style="background:var(--bg-card);border:1px solid var(--border);
                        border-radius:var(--r-md);padding:1rem 1.2rem;text-align:center">
                <div style="font-size:1.4rem;font-weight:700;color:var(--blue);line-height:1">{brs:.1f}</div>
                <div style="font-size:.68rem;color:var(--text-muted);margin-top:4px;
                            font-family:'JetBrains Mono',monospace;text-transform:uppercase;
                            letter-spacing:.06em">Business Risk</div>
            </div>
            <div style="background:var(--bg-card);border:1px solid var(--border);
                        border-radius:var(--r-md);padding:1rem 1.2rem;text-align:center">
                <div style="font-size:1.4rem;font-weight:700;color:{'var(--red)' if is_anomaly else 'var(--green)'};line-height:1">
                    {ars:.1f}{'  ⚠️' if is_anomaly else ''}</div>
                <div style="font-size:.68rem;color:var(--text-muted);margin-top:4px;
                            font-family:'JetBrains Mono',monospace;text-transform:uppercase;
                            letter-spacing:.06em">Anomaly Risk</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── 9b. Behavioral Signal Analysis ─────────────────────────────────────────
if has_risk:
    aov = float(risk_row.get("aov_change_pct", 0))
    gap = float(risk_row.get("gap_change_pct", 0))
    div_d = float(risk_row.get("diversity_delta", 0))

    def _signal_interpretation(name: str, value: float, context: str) -> str:
        """Generate business-language interpretation for a signal."""
        if name == "aov_change_pct":
            if value < -15:
                return f"Severe spending decline ({value:+.1f}%). {context} is significantly reducing order sizes, suggesting budget cuts or competitive displacement."
            elif value < -5:
                return f"Moderate spending decline ({value:+.1f}%). {context} may be consolidating vendors or experiencing budget pressure."
            elif value > 5:
                return f"Spending is increasing ({value:+.1f}%). This is a positive signal indicating growing engagement."
            else:
                return f"Spending is stable ({value:+.1f}%). No significant change in average order value."
        elif name == "gap_change_pct":
            if value > 30:
                return f"Critical ordering gap increase ({value:+.1f}%). {context} is ordering far less frequently — strong disengagement signal."
            elif value > 10:
                return f"Ordering frequency is declining ({value:+.1f}%). Time between purchases is widening."
            elif value < -10:
                return f"Ordering frequency is increasing ({value:+.1f}%). The customer is purchasing more often."
            else:
                return f"Ordering frequency is stable ({value:+.1f}%). No significant change in purchase cadence."
        elif name == "diversity_delta":
            if value < -1.5:
                return f"Severe product diversity loss ({value:+.2f}). {context} has dramatically narrowed their product selection — possible consolidation or loss of use cases."
            elif value < -0.5:
                return f"Product diversity is declining ({value:+.2f}). The customer is buying from fewer categories."
            elif value > 0.5:
                return f"Product diversity is growing ({value:+.2f}). The customer is exploring more categories — healthy engagement."
            else:
                return f"Product mix is stable ({value:+.2f}). No significant shift in category breadth."
        return ""

    company = _safe(cust_row.get("company_name"))
    signals_data = [
        ("Average Order Value", "aov_change_pct", aov, "var(--red)" if aov < -5 else "var(--green)" if aov > 5 else "var(--text-muted)"),
        ("Purchase Frequency Gap", "gap_change_pct", gap, "var(--red)" if gap > 10 else "var(--green)" if gap < -10 else "var(--text-muted)"),
        ("Product Diversity", "diversity_delta", div_d, "var(--red)" if div_d < -0.5 else "var(--green)" if div_d > 0.5 else "var(--text-muted)"),
    ]

    with st.expander("📊 Behavioral Signal Analysis", expanded=True):
        for sig_name, sig_field, sig_val, sig_color in signals_data:
            interpretation = _signal_interpretation(sig_field, sig_val, company)
            st.markdown(
                f"""
                <div style="background:var(--bg-card);border:1px solid var(--border);
                            border-radius:var(--r-md);padding:1rem 1.2rem;margin-bottom:.6rem">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.4rem">
                        <span style="font-size:.82rem;font-weight:600;color:var(--text-h)">{sig_name}</span>
                        <span style="font-size:1rem;font-weight:700;color:{sig_color};
                                     font-family:'JetBrains Mono',monospace">{sig_val:+.1f}{'%' if 'pct' in sig_field else ''}</span>
                    </div>
                    <div style="font-size:.8rem;color:var(--text-p);line-height:1.6">{interpretation}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ── 9c. AI Executive Analysis (Gemini) ────────────────────────────────────
# (Prompt construction and Gemini handling moved to
#  agent/intelligence_prompts.py + agent/intelligence_client.py)


# Cache key for session state
_cache_key = f"intel_report_{selected_id}"

# Generate or retrieve cached report
with st.expander("🧠 AI Executive Analysis", expanded=True):
    col_gen, _ = st.columns([1, 3])
    with col_gen:
        regenerate = st.button("🔄 Generate Report", key="gen_intel_report")

    if regenerate or _cache_key not in st.session_state:
        if has_risk or has_intv:
            with st.spinner("Generating intelligence report with Gemini AI..."):
                report = generate_customer_intelligence(selected_id)
                st.session_state[_cache_key] = report
        else:
            st.session_state[_cache_key] = None

    report = st.session_state.get(_cache_key)

    if report is not None:
        from datetime import datetime
        from zoneinfo import ZoneInfo
        import uuid
        now_ts = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%d %b %Y · %H:%M IST")
        ref_id = f"AX-{uuid.uuid4().hex[:4].upper()}"
        st.markdown(
            f"""
            <div style="display:flex; flex-wrap:wrap; gap:1.5rem; align-items:center; margin: 0.5rem 0 1.5rem 0; padding: 0 4px; font-size:0.75rem; color:var(--text-muted); font-family:'JetBrains Mono', monospace;">
                <span>⚡ AI Generated Report</span>
                <span>🧠 Powered by Gemini 3.1 Flash Lite</span>
                <span>🔌 MongoDB MCP Server</span>
                <span>📄 Ref: {ref_id}</span>
                <span>📅 Generated: {now_ts}</span>
            </div>
            """,
            unsafe_allow_html=True
        )

    if report is None:
        st.markdown(
            """
            <div style="background:var(--bg-card);border:1px solid var(--border);
                        border-radius:var(--r-md);padding:1.5rem;text-align:center">
                <div style="font-size:1.4rem;margin-bottom:.4rem">🤖</div>
                <div style="font-size:.92rem;color:var(--text-h);font-weight:600;
                            margin-bottom:.2rem">Intelligence report unavailable</div>
                <div style="font-size:.82rem;color:var(--text-muted);line-height:1.5">
                    Gemini AI could not generate a report for this customer.
                    Click <strong>Generate Report</strong> to retry.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        def _val(k):
            v = report.get(k)
            return f'<span class="empty-state">Data unavailable</span>' if not v else v

        # Executive Diagnosis
        st.markdown(
            f"""
            <div style="background:var(--bg-card);border:1px solid var(--border);
                        border-radius:var(--r-lg);padding:1.3rem 1.5rem;margin-bottom:.8rem;
                        position:relative;overflow:hidden">
                <div style="position:absolute;top:0;left:0;width:3px;height:100%;background:var(--violet)"></div>
                <div style="font-size:.68rem;color:var(--violet);text-transform:uppercase;
                            letter-spacing:.06em;font-family:'JetBrains Mono',monospace;
                            margin-bottom:.4rem;font-weight:600">Executive Diagnosis</div>
                <div style="font-size:.9rem;color:var(--text-p);line-height:1.7">{_val("executive_diagnosis")}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Behavioral Changes + Likely Business Situation (two columns)
        r1, r2 = st.columns(2, gap="medium")
        with r1:
            st.markdown(
                f"""
                <div style="background:var(--bg-card);border:1px solid var(--border);
                            border-radius:var(--r-md);padding:1.1rem 1.3rem;height:100%">
                    <div style="font-size:.68rem;color:var(--amber);text-transform:uppercase;
                                letter-spacing:.06em;font-family:'JetBrains Mono',monospace;
                                margin-bottom:.5rem;font-weight:600">⚠️ Behavioral Changes</div>
                    <div style="font-size:.85rem;color:var(--text-p);line-height:1.7">{_val("behavioral_changes")}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with r2:
            st.markdown(
                f"""
                <div style="background:var(--bg-card);border:1px solid var(--border);
                            border-radius:var(--r-md);padding:1.1rem 1.3rem;height:100%">
                    <div style="font-size:.68rem;color:var(--cyan);text-transform:uppercase;
                                letter-spacing:.06em;font-family:'JetBrains Mono',monospace;
                                margin-bottom:.5rem;font-weight:600">🏢 Likely Business Situation</div>
                    <div style="font-size:.85rem;color:var(--text-p);line-height:1.7">{_val("likely_business_situation")}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Revenue Risk Assessment (full width)
        st.markdown(
            f"""
            <div style="background:var(--bg-card);border:1px solid var(--border);
                        border-radius:var(--r-md);padding:1.1rem 1.3rem;margin-top:.8rem">
                <div style="font-size:.68rem;color:var(--pink);text-transform:uppercase;
                            letter-spacing:.06em;font-family:'JetBrains Mono',monospace;
                            margin-bottom:.5rem;font-weight:600">💥 Revenue Risk Assessment</div>
                <div style="font-size:.85rem;color:var(--text-p);line-height:1.7">{_val("revenue_risk_assessment")}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ── 9d. Executive Recommendation ──────────────────────────────────────────
if report is not None:
    def _val_rec(k):
        v = report.get(k)
        return f'<span class="empty-state">Data unavailable</span>' if not v else v

    strategy = _val_rec("retention_strategy")
    outcome = _val_rec("expected_outcome")

    html_content = f"""
<div style="background:var(--bg-card);border:1px solid var(--border);border-radius:var(--r-lg);padding:1.4rem 1.6rem;margin-top:1rem;position:relative;overflow:hidden">
<div style="position:absolute;top:0;left:0;right:0;height:3px;background:var(--gradient)"></div>
<div style="font-size:.68rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:.06em;font-family:'JetBrains Mono',monospace;margin-bottom:.8rem;font-weight:600">Executive Recommendation</div>
<div style="display:grid;grid-template-columns:140px 1fr;gap:.6rem;align-items:start">
<div style="font-size:.75rem;color:var(--text-muted);font-weight:500;text-transform:uppercase;letter-spacing:.04em">Retention Strategy</div>
<div style="font-size:.88rem;color:var(--text-h);line-height:1.6">{strategy}</div>
<div style="font-size:.75rem;color:var(--text-muted);font-weight:500;text-transform:uppercase;letter-spacing:.04em">Expected Outcome</div>
<div style="font-size:.88rem;color:var(--text-p);line-height:1.6">{outcome}</div>
</div>
</div>
"""
    st.markdown(html_content, unsafe_allow_html=True)

