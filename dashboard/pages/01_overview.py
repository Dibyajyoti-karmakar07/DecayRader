"""
dashboard/pages/01_overview.py
──────────────────────────────
Business Health Dashboard — fleet-wide KPIs, risk distribution,
top-risk customers, and recent interventions.
"""

import os
import sys

# Ensure project root is in sys.path for local imports
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.db import connect_to_mongo
from agent.intelligence_client import (
    generate_portfolio_analysis,
    generate_tier_analysis
)

# ╭──────────────────────────────────────────────────────────────────────────╮
# │  THEME CSS  (mirrors app.py dark Vercel aesthetic)                      │
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
        color: var(--text-h) !important;
        letter-spacing: -0.03em;
    }

    /* ── page header ────────────────────────────────────────────────── */
    .page-header {
        display: flex; align-items: center; gap: 12px;
        margin-bottom: 0.25rem;
    }
    .page-header h1 {
        font-size: 1.55rem; font-weight: 600; margin: 0;
    }
    .page-header .sub {
        font-size: 0.85rem; color: var(--text-muted);
    }

    /* ── KPI card grid ──────────────────────────────────────────────── */
    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
        margin: 1.25rem 0 1.5rem;
    }
    @media (max-width: 900px) {
        .kpi-grid { grid-template-columns: repeat(2, 1fr); }
    }
    .kpi {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: var(--r-md);
        padding: 1.3rem 1.5rem;
        position: relative;
        overflow: hidden;
        transition: border-color .2s, transform .15s;
    }
    .kpi:hover {
        border-color: var(--border-hover);
        transform: translateY(-2px);
    }
    .kpi::before {
        content: '';
        position: absolute; top: 0; left: 0;
        width: 3px; height: 100%;
    }
    .kpi.cyan::before   { background: var(--cyan); }
    .kpi.red::before    { background: var(--red); }
    .kpi.amber::before  { background: var(--amber); }
    .kpi.green::before  { background: var(--green); }
    .kpi-val {
        font-size: 2rem; font-weight: 700;
        letter-spacing: -0.03em; line-height: 1;
    }
    .kpi-lbl {
        font-size: 0.72rem; color: var(--text-muted);
        margin-top: 6px;
        font-family: 'JetBrains Mono', monospace;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }

    /* ── section titles ─────────────────────────────────────────────── */
    .sec-title {
        font-size: 1rem; font-weight: 600; color: var(--text-h);
        margin: 1.75rem 0 0.6rem; letter-spacing: -0.02em;
    }

    /* ── intervention table ─────────────────────────────────────────── */
    .iv-wrap {
        background: var(--bg-card); border: 1px solid var(--border);
        border-radius: var(--r-md); overflow-x: auto;
        margin-top: 0.5rem;
    }
    .iv-table {
        width: 100%; border-collapse: collapse;
        font-size: 0.82rem;
    }
    .iv-table th {
        text-align: left; padding: 10px 14px;
        color: var(--text-muted);
        border-bottom: 1px solid var(--border);
        font-weight: 500; text-transform: uppercase;
        font-size: 0.68rem; letter-spacing: 0.06em;
        font-family: 'JetBrains Mono', monospace;
    }
    .iv-table td {
        padding: 10px 14px; color: var(--text-p);
        border-bottom: 1px solid #1a1a1a;
    }
    .iv-table tr:last-child td { border-bottom: none; }
    .iv-table tr:hover td { background: rgba(255,255,255,.02); }

    /* ── risk badges ────────────────────────────────────────────────── */
    .rl { display: inline-block; padding: 2px 10px; border-radius: 100px;
          font-size: 0.72rem; font-weight: 500;
          font-family: 'JetBrains Mono', monospace; }
    .rl-critical  { background: rgba(255,77,106,.12); color: #ff4d6a; }
    .rl-atrisk    { background: rgba(249,203,40,.12); color: #f9cb28; }
    .rl-watch     { background: rgba(0,124,240,.12);  color: #007cf0; }
    .rl-healthy   { background: rgba(80,227,194,.12); color: #50e3c2; }

    .urg-high     { color: #ff4d6a; font-weight: 600; }
    .urg-medium   { color: #f9cb28; }
    .urg-low      { color: #50e3c2; }

    .st-pending   { color: var(--amber); }
    .st-completed { color: var(--green); }
    .st-cancelled { color: var(--text-muted); }

    /* ── hide chrome ────────────────────────────────────────────────── */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header[data-testid="stHeader"] {background: transparent !important;}

    /* ── portfolio intelligence cards ───────────────────────────────── */
    .intel-container {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: var(--r-lg);
        padding: 1.5rem;
        margin-top: 1rem;
        margin-bottom: 1.5rem;
    }
    .intel-header {
        font-size: 0.78rem; font-weight: 600; color: var(--text-muted);
        text-transform: uppercase; letter-spacing: 0.05em;
        font-family: 'JetBrains Mono', monospace;
        margin-bottom: 0.4rem;
    }
    .intel-card {
        background: #111111;
        border: 1px solid var(--border);
        border-radius: var(--r-md);
        padding: 1.2rem;
        margin-bottom: 1rem;
        position: relative;
        overflow: hidden;
    }
    .intel-card::before {
        content: ''; position: absolute; top: 0; left: 0;
        width: 3px; height: 100%;
    }
    .intel-card.blue::before { background: var(--blue); }
    .intel-card.violet::before { background: var(--violet); }
    .intel-card.pink::before { background: var(--pink); }
    .intel-card.amber::before { background: var(--amber); }
    .intel-card.red::before { background: var(--red); }
    .intel-card.green::before { background: var(--green); }
    .intel-card.cyan::before { background: var(--cyan); }
    </style>
    """,
    unsafe_allow_html=True,
)

# ╭──────────────────────────────────────────────────────────────────────────╮
# │  DATA LOADING                                                           │
# ╰──────────────────────────────────────────────────────────────────────────╯

RISK_ORDER = ["Healthy", "Watch", "At Risk", "Critical"]
RISK_COLORS = {
    "Healthy":  "#50e3c2",
    "Watch":    "#007cf0",
    "At Risk":  "#f9cb28",
    "Critical": "#ff4d6a",
}

# ── Plotly global layout for dark theme ─────────────────────────────────────
PLOTLY_LAYOUT = dict(
    paper_bgcolor="#0a0a0a",
    plot_bgcolor="#0a0a0a",
    font=dict(family="Inter, system-ui, sans-serif", color="#a1a1a1", size=12),
    margin=dict(l=0, r=0, t=30, b=0),
)


@st.cache_data(ttl=120, show_spinner=False)
def load_customers() -> pd.DataFrame:
    db = connect_to_mongo()
    docs = list(db["Customers"].find())
    df = pd.DataFrame(docs)
    df.drop(columns=["_id"], errors="ignore", inplace=True)
    return df


@st.cache_data(ttl=120, show_spinner=False)
def load_risk_scores() -> pd.DataFrame:
    db = connect_to_mongo()
    docs = list(db["risk_scores"].find())
    df = pd.DataFrame(docs)
    df.drop(columns=["_id"], errors="ignore", inplace=True)
    return df


@st.cache_data(ttl=60, show_spinner=False)
def load_interventions() -> pd.DataFrame:
    db = connect_to_mongo()
    docs = list(db["interventions"].find())
    df = pd.DataFrame(docs)
    df.drop(columns=["_id"], errors="ignore", inplace=True)
    return df


# ╭──────────────────────────────────────────────────────────────────────────╮
# │  HELPER — risk-label badge HTML                                         │
# ╰──────────────────────────────────────────────────────────────────────────╯

def _risk_badge(label: str) -> str:
    cls_map = {
        "Critical": "rl-critical",
        "At Risk":  "rl-atrisk",
        "Watch":    "rl-watch",
        "Healthy":  "rl-healthy",
    }
    cls = cls_map.get(label, "")
    return f'<span class="rl {cls}">{label}</span>'


def _urgency_html(urgency: str) -> str:
    u = str(urgency).strip().lower()
    if u == "high":
        return '<span class="urg-high">High</span>'
    elif u == "medium":
        return '<span class="urg-medium">Medium</span>'
    return f'<span class="urg-low">{urgency}</span>'


def _status_html(status: str) -> str:
    s = str(status).strip().lower()
    if s == "pending":
        return '<span class="st-pending">pending</span>'
    elif s == "completed":
        return '<span class="st-completed">completed</span>'
    elif s == "cancelled":
        return '<span class="st-cancelled">cancelled</span>'
    return f"<span>{status}</span>"


# ╭──────────────────────────────────────────────────────────────────────────╮
# │  MAIN RENDER                                                            │
# ╰──────────────────────────────────────────────────────────────────────────╯

try:
    customers_df = load_customers()
    risk_df = load_risk_scores()
    interventions_df = load_interventions()
except Exception as exc:
    st.error(f"Failed to load data from MongoDB: {exc}")
    st.stop()

# ── Merge customer names into risk data ─────────────────────────────────────
if "customer_id" in risk_df.columns and "customer_id" in customers_df.columns:
    risk_merged = risk_df.merge(
        customers_df[["customer_id", "company_name", "tier"]],
        on="customer_id",
        how="left",
    )
else:
    risk_merged = risk_df.copy()
    if "company_name" not in risk_merged.columns:
        risk_merged["company_name"] = risk_merged.get("customer_id", "Unknown")


# ── Page header ─────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="page-header">
        <h1>📊 Overview</h1>
        <span class="sub">Real-time customer health monitoring across your entire portfolio</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# ╭──────────────────────────────────────────────────────────────────────────╮
# │  KPI CARDS                                                              │
# ╰──────────────────────────────────────────────────────────────────────────╯
total = len(risk_df)
label_counts = risk_df["risk_label"].value_counts()
critical = int(label_counts.get("Critical", 0))
at_risk = int(label_counts.get("At Risk", 0))
healthy = int(label_counts.get("Healthy", 0))

st.markdown(
    f"""
    <div class="kpi-grid">
        <div class="kpi cyan">
            <div class="kpi-val" style="color:var(--cyan)">{total}</div>
            <div class="kpi-lbl">Total Customers</div>
        </div>
        <div class="kpi red">
            <div class="kpi-val" style="color:var(--red)">{critical}</div>
            <div class="kpi-lbl">Critical</div>
        </div>
        <div class="kpi amber">
            <div class="kpi-val" style="color:var(--amber)">{at_risk}</div>
            <div class="kpi-lbl">At Risk</div>
        </div>
        <div class="kpi green">
            <div class="kpi-val" style="color:var(--green)">{healthy}</div>
            <div class="kpi-lbl">Healthy</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ╭──────────────────────────────────────────────────────────────────────────╮
# │  CHARTS — two-column layout                                            │
# ╰──────────────────────────────────────────────────────────────────────────╯
col_donut, col_bar = st.columns([1, 1.6], gap="large")

# ── 1. Risk Distribution Donut ──────────────────────────────────────────────
with col_donut:
    st.markdown('<div class="sec-title">Risk Distribution</div>', unsafe_allow_html=True)

    dist = (
        risk_df["risk_label"]
        .value_counts()
        .reindex(RISK_ORDER, fill_value=0)
    )

    fig_donut = go.Figure(
        go.Pie(
            labels=dist.index.tolist(),
            values=dist.values.tolist(),
            hole=0.62,
            marker=dict(
                colors=[RISK_COLORS[l] for l in dist.index],
                line=dict(color="#0a0a0a", width=2),
            ),
            textinfo="label+value",
            textfont=dict(size=12, family="Inter, sans-serif"),
            hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Share: %{percent}<extra></extra>",
            sort=False,
        )
    )
    fig_donut.update_layout(
        **PLOTLY_LAYOUT,
        showlegend=False,
        height=360,
        annotations=[
            dict(
                text=f"<b>{total}</b><br><span style='font-size:11px;color:#555'>customers</span>",
                x=0.5, y=0.5,
                font=dict(size=28, color="#ededed", family="Inter"),
                showarrow=False,
            )
        ],
    )
    st.plotly_chart(fig_donut, use_container_width=True, config={"displayModeBar": False})

# ── 2. Top 10 Customers by Risk Score ───────────────────────────────────────
with col_bar:
    st.markdown('<div class="sec-title">Top 10 Customers by Risk Score</div>', unsafe_allow_html=True)

    top10 = (
        risk_merged.nlargest(10, "risk_score")
        .sort_values("risk_score", ascending=True)  # ascending for horizontal bar
    )

    bar_colors = [RISK_COLORS.get(lbl, "#555") for lbl in top10["risk_label"]]

    fig_bar = go.Figure(
        go.Bar(
            x=top10["risk_score"],
            y=top10["company_name"],
            orientation="h",
            marker=dict(
                color=bar_colors,
                line=dict(width=0),
                cornerradius=4,
            ),
            text=top10["risk_score"].round(1).astype(str),
            textposition="outside",
            textfont=dict(size=11, color="#a1a1a1", family="JetBrains Mono"),
            hovertemplate="<b>%{y}</b><br>Risk Score: %{x:.1f}<extra></extra>",
        )
    )
    fig_bar.update_layout(
        **PLOTLY_LAYOUT,
        height=360,
        xaxis=dict(
            range=[0, 105],
            showgrid=True,
            gridcolor="#1e1e1e",
            gridwidth=1,
            zeroline=False,
            tickfont=dict(color="#555", size=10),
        ),
        yaxis=dict(
            tickfont=dict(color="#a1a1a1", size=11, family="Inter"),
            automargin=True,
        ),
        bargap=0.3,
    )
    st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})

# ╭──────────────────────────────────────────────────────────────────────────╮
# │  RECENT INTERVENTIONS TABLE                                             │
# ╰──────────────────────────────────────────────────────────────────────────╯
st.markdown('<div class="sec-title">Recent Interventions</div>', unsafe_allow_html=True)

if interventions_df.empty:
    st.markdown(
        """
        <div style="background:var(--bg-card);border:1px solid var(--border);
                    border-radius:var(--r-md);padding:2rem 2.5rem;text-align:center;
                    margin-top:.5rem">
            <div style="font-size:2rem;margin-bottom:.6rem">💭</div>
            <div style="font-size:.95rem;color:var(--text-h);font-weight:600;
                        margin-bottom:.3rem">No interventions yet</div>
            <div style="font-size:.82rem;color:var(--text-muted);line-height:1.6;
                        max-width:420px;margin:0 auto">
                Run the <strong style="color:var(--cyan)">Agent Console</strong>
                to analyze at-risk customers with Gemini AI and generate
                retention interventions.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    display_cols = ["company_name", "risk_label", "primary_action", "urgency", "status"]
    available_cols = [c for c in display_cols if c in interventions_df.columns]

    if not available_cols:
        st.warning("Intervention data does not contain the expected columns.")
    else:
        recent = interventions_df[available_cols].head(15)

        rows_html = ""
        for _, row in recent.iterrows():
            company = row.get("company_name", "—")
            risk_lbl = row.get("risk_label", "—")
            action = row.get("primary_action", "—")
            urgency = row.get("urgency", "—")
            status = row.get("status", "—")

            rows_html += f"""
            <tr>
                <td style="color:var(--text-h);font-weight:500">{company}</td>
                <td>{_risk_badge(risk_lbl)}</td>
                <td>{action}</td>
                <td>{_urgency_html(urgency)}</td>
                <td>{_status_html(status)}</td>
            </tr>
            """

        st.markdown(
            f"""
            <div class="iv-wrap">
                <table class="iv-table">
                    <thead>
                        <tr>
                            <th>Company</th>
                            <th>Risk</th>
                            <th>Primary Action</th>
                            <th>Urgency</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>{rows_html}</tbody>
                </table>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ╭──────────────────────────────────────────────────────────────────────────╮
# │  🧠 PORTFOLIO RISK INTELLIGENCE                                          │
# └──────────────────────────────────────────────────────────────────────────╯
st.markdown('<div class="sec-title" style="margin-top:2rem">🧠 Portfolio Risk Intelligence</div>', unsafe_allow_html=True)

with st.container():
    st.markdown(
        """
        <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:var(--r-lg);padding:2rem;text-align:center;">
            <div style="font-size:1.1rem; color:var(--text-h); font-weight:500; margin-bottom:0.5rem;">
                Executive Portfolio Analysis has moved.
            </div>
            <div style="font-size:0.9rem; color:var(--text-p); margin-bottom:1.5rem; max-width:600px; margin-left:auto; margin-right:auto;">
                To reduce cognitive load and centralize AI operations, the Portfolio Risk Intelligence module has been fully integrated into the <b>Intelligence Workspace</b>.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# ╭──────────────────────────────────────────────────────────────────────────╮
# │  🧠 TIER INTELLIGENCE                                                      │
# ╰──────────────────────────────────────────────────────────────────────────╯
st.markdown('<div class="sec-title" style="margin-top:2rem">🧠 Tier Intelligence</div>', unsafe_allow_html=True)

with st.container():
    col_tier_desc, col_tier_sel, col_tier_btn = st.columns([2.5, 1, 1.2], gap="medium")
    with col_tier_desc:
        st.markdown(
            """
            <div style="font-size:0.85rem; color:var(--text-p); line-height:1.6; margin-bottom:1rem;">
                Select a customer tier (Gold, Silver, or Bronze) to run an executive-level tier health analysis, 
                risk distributions, behavioral patterns, business impact, and specific recommended directives.
            </div>
            """,
            unsafe_allow_html=True
        )
    with col_tier_sel:
        selected_tier = st.selectbox("Select Tier", options=["Gold", "Silver", "Bronze"], label_visibility="collapsed")
    with col_tier_btn:
        generate_tier_clicked = st.button("Generate Tier Analysis", type="primary", use_container_width=True)

    tier_cache_key = f"tier_intel_{selected_tier.lower()}"
    if tier_cache_key not in st.session_state:
        st.session_state[tier_cache_key] = None

    if generate_tier_clicked:
        with st.spinner(f"Analyzing health & risk patterns for {selected_tier} Tier..."):
            try:
                # Filter risk_merged by the selected tier
                tier_df = risk_merged[risk_merged["tier"] == selected_tier]
                if tier_df.empty:
                    st.warning(f"No customer data found for Tier: {selected_tier}.")
                else:
                    report = generate_tier_analysis(selected_tier, tier_df)
                    if report:
                        st.session_state[tier_cache_key] = report
                        st.success(f"{selected_tier} Tier Intelligence generated successfully!")
                    else:
                        st.error(f"Failed to generate Tier Intelligence for {selected_tier}. Gemini fallback failed.")
            except Exception as e:
                st.error(f"An unexpected error occurred: {str(e)}")

    # Render tier report if cached in session state
    tier_report = st.session_state[tier_cache_key]
    if tier_report:
        model_used = tier_report.get("_model_used") or "Unknown"
        st.markdown(
            f"""
            <div style="display:flex; justify-content:space-between; align-items:center; margin: 0.5rem 0 1rem 0; padding: 0 4px;">
                <div style="font-size:0.75rem; color:var(--text-muted);">
                    AI Model: <code style="font-family:'JetBrains Mono'; color:var(--cyan);">{model_used}</code>
                </div>
                <div style="font-size:0.75rem; color:var(--text-muted);">
                    Context Scope: <strong>{selected_tier} Tier Customer Base</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        def _val(k):
            v = tier_report.get(k)
            return f'<span class="empty-state">Data unavailable</span>' if not v else v

        col_sum, col_rec = st.columns([1.2, 1], gap="medium")
        with col_sum:
            st.markdown(
                f"""
                <div class="intel-card blue">
                    <div class="intel-header">Tier Health Assessment</div>
                    <div style="font-size:0.9rem; color:var(--text-p); line-height:1.6;">
                        {_val("tier_health_assessment")}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with col_rec:
            st.markdown(
                f"""
                <div class="intel-card red">
                    <div class="intel-header">Strategic Recommendation</div>
                    <div style="font-size:0.9rem; color:var(--text-p); line-height:1.6; font-weight:500;">
                        {_val("strategic_recommendation")}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        col_l, col_r = st.columns(2, gap="medium")
        with col_l:
            st.markdown(
                f"""
                <div class="intel-card cyan">
                    <div class="intel-header">Healthy vs At-Risk Comparison</div>
                    <div style="font-size:0.88rem; color:var(--text-p); line-height:1.6;">
                        {_val("healthy_vs_at_risk")}
                    </div>
                </div>
                <div class="intel-card amber">
                    <div class="intel-header">Primary Decay Drivers</div>
                    <div style="font-size:0.88rem; color:var(--text-p); line-height:1.6;">
                        {_val("primary_decay_drivers")}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with col_r:
            st.markdown(
                f"""
                <div class="intel-card pink">
                    <div class="intel-header">Behavioral Pattern Analysis</div>
                    <div style="font-size:0.88rem; color:var(--text-p); line-height:1.6;">
                        {_val("behavioral_pattern_analysis")}
                    </div>
                </div>
                <div class="intel-card orange" style="position:relative; overflow:hidden;">
                    <style>
                        .intel-card.orange::before {{ background: #f97316; }}
                    </style>
                    <div class="intel-header">Business Impact Assessment</div>
                    <div style="font-size:0.88rem; color:var(--text-p); line-height:1.6;">
                        {tier_report.get("business_impact") or ""}
                    </div>
                </div>
                <div class="intel-card green">
                    <div class="intel-header">Recommended Actions</div>
                    <div style="font-size:0.88rem; color:var(--text-p); line-height:1.6;">
                        {tier_report.get("recommended_actions") or ""}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
