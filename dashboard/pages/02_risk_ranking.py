"""
dashboard/pages/02_risk_ranking.py
──────────────────────────────────
Customer Risk Ranking — searchable, filterable table of all customers
ranked by composite decay-risk score, with an insights panel.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.db import connect_to_mongo

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
        color: var(--text-h) !important;
        letter-spacing: -0.03em;
    }

    /* ── page header ────────────────────────────────────────────────── */
    .page-header { margin-bottom: 0.2rem; }
    .page-header h1 {
        font-size: 1.55rem; font-weight: 600; margin: 0;
        color: var(--text-h) !important;
    }
    .page-sub {
        font-size: 0.85rem; color: var(--text-muted); margin-top: 2px;
    }

    /* ── KPI mini cards ─────────────────────────────────────────────── */
    .m-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem; margin: 1.1rem 0 1.4rem;
    }
    @media (max-width: 900px) { .m-grid { grid-template-columns: repeat(2, 1fr); } }
    .m-card {
        background: var(--bg-card); border: 1px solid var(--border);
        border-radius: var(--r-md); padding: 1.15rem 1.35rem;
        position: relative; overflow: hidden;
        transition: border-color .2s, transform .15s;
    }
    .m-card:hover { border-color: var(--border-hover); transform: translateY(-2px); }
    .m-card::before {
        content: ''; position: absolute; top: 0; left: 0;
        width: 3px; height: 100%;
    }
    .m-card.c-cyan::before   { background: var(--cyan); }
    .m-card.c-blue::before   { background: var(--blue); }
    .m-card.c-red::before    { background: var(--red); }
    .m-card.c-amber::before  { background: var(--amber); }
    .m-val {
        font-size: 1.75rem; font-weight: 700;
        letter-spacing: -0.03em; line-height: 1;
    }
    .m-lbl {
        font-size: 0.7rem; color: var(--text-muted); margin-top: 5px;
        font-family: 'JetBrains Mono', monospace;
        text-transform: uppercase; letter-spacing: 0.06em;
    }

    /* ── section heading ────────────────────────────────────────────── */
    .sec-title {
        font-size: 1rem; font-weight: 600; color: var(--text-h);
        margin: 1.6rem 0 0.5rem; letter-spacing: -0.02em;
    }

    /* ── risk table ─────────────────────────────────────────────────── */
    .rt-wrap {
        background: var(--bg-card); border: 1px solid var(--border);
        border-radius: var(--r-md); overflow-x: auto; margin-top: 0.4rem;
    }
    .rt {
        width: 100%; border-collapse: collapse; font-size: 0.82rem;
    }
    .rt th {
        text-align: left; padding: 10px 12px; color: var(--text-muted);
        border-bottom: 1px solid var(--border); font-weight: 500;
        text-transform: uppercase; font-size: 0.68rem;
        letter-spacing: 0.06em;
        font-family: 'JetBrains Mono', monospace;
        white-space: nowrap;
    }
    .rt td {
        padding: 9px 12px; color: var(--text-p);
        border-bottom: 1px solid #1a1a1a; white-space: nowrap;
    }
    .rt tr:last-child td { border-bottom: none; }
    .rt tr:hover td { background: rgba(255,255,255,.02); }
    .rt td.name { color: var(--text-h); font-weight: 500; }

    /* ── risk badge ─────────────────────────────────────────────────── */
    .rl {
        display: inline-block; padding: 2px 10px; border-radius: 100px;
        font-size: 0.72rem; font-weight: 500;
        font-family: 'JetBrains Mono', monospace;
    }
    .rl-critical  { background: rgba(255,77,106,.12); color: #ff4d6a; }
    .rl-atrisk    { background: rgba(249,203,40,.12); color: #f9cb28; }
    .rl-watch     { background: rgba(0,124,240,.12);  color: #007cf0; }
    .rl-healthy   { background: rgba(80,227,194,.12); color: #50e3c2; }

    /* ── progress bar for risk score ────────────────────────────────── */
    .prog-wrap {
        display: flex; align-items: center; gap: 8px;
    }
    .prog-bar {
        flex: 1; height: 6px; border-radius: 3px;
        background: #1e1e1e; overflow: hidden; min-width: 60px;
    }
    .prog-fill { height: 100%; border-radius: 3px; }
    .prog-val {
        font-size: 0.78rem; font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
        min-width: 32px; text-align: right;
    }

    /* ── insight panel cards ────────────────────────────────────────── */
    .ins-card {
        background: var(--bg-card); border: 1px solid var(--border);
        border-radius: var(--r-md); padding: 1.1rem 1.3rem;
        margin-bottom: 1rem;
    }
    .ins-card h4 {
        font-size: 0.82rem; font-weight: 600; color: var(--text-h);
        margin: 0 0 0.6rem; letter-spacing: -0.01em;
    }
    .ins-row {
        display: flex; justify-content: space-between; align-items: center;
        padding: 5px 0; border-bottom: 1px solid #1a1a1a;
        font-size: 0.8rem;
    }
    .ins-row:last-child { border-bottom: none; }
    .ins-row .lbl { color: var(--text-p); }
    .ins-row .val { font-weight: 600; font-family: 'JetBrains Mono', monospace; }

    /* ── tier badge ─────────────────────────────────────────────────── */
    .tier {
        display: inline-block; padding: 2px 8px; border-radius: 4px;
        font-size: 0.7rem; font-weight: 500;
        font-family: 'JetBrains Mono', monospace;
    }
    .tier-gold   { background: rgba(249,203,40,.1); color: #f9cb28; }
    .tier-silver { background: rgba(161,161,161,.1); color: #a1a1a1; }
    .tier-bronze { background: rgba(205,127,50,.12); color: #cd7f32; }

    /* ── hide chrome ────────────────────────────────────────────────── */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header[data-testid="stHeader"] {background: transparent !important;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ╭──────────────────────────────────────────────────────────────────────────╮
# │  CONSTANTS                                                              │
# ╰──────────────────────────────────────────────────────────────────────────╯
RISK_ORDER = ["Healthy", "Watch", "At Risk", "Critical"]
RISK_COLORS = {
    "Healthy":  "#50e3c2",
    "Watch":    "#007cf0",
    "At Risk":  "#f9cb28",
    "Critical": "#ff4d6a",
}
PLOTLY_LAYOUT = dict(
    paper_bgcolor="#0a0a0a",
    plot_bgcolor="#0a0a0a",
    font=dict(family="Inter, system-ui, sans-serif", color="#a1a1a1", size=12),
    margin=dict(l=0, r=0, t=30, b=0),
)

# ╭──────────────────────────────────────────────────────────────────────────╮
# │  DATA LOADING                                                           │
# ╰──────────────────────────────────────────────────────────────────────────╯

@st.cache_data(ttl=120, show_spinner=False)
def load_data() -> pd.DataFrame:
    """Load Customers + risk_scores, merge on customer_id."""
    db = connect_to_mongo()

    customers = pd.DataFrame(list(db["Customers"].find()))
    customers.drop(columns=["_id"], errors="ignore", inplace=True)

    risk = pd.DataFrame(list(db["risk_scores"].find()))
    risk.drop(columns=["_id"], errors="ignore", inplace=True)

    merged = risk.merge(customers, on="customer_id", how="left")
    return merged


# ╭──────────────────────────────────────────────────────────────────────────╮
# │  HELPERS                                                                │
# ╰──────────────────────────────────────────────────────────────────────────╯

def _risk_badge(label: str) -> str:
    cls = {
        "Critical": "rl-critical", "At Risk": "rl-atrisk",
        "Watch": "rl-watch", "Healthy": "rl-healthy",
    }.get(label, "")
    return f'<span class="rl {cls}">{label}</span>'


def _tier_badge(tier: str) -> str:
    t = str(tier).strip().lower()
    cls = {"gold": "tier-gold", "silver": "tier-silver", "bronze": "tier-bronze"}.get(t, "")
    return f'<span class="tier {cls}">{tier}</span>'


def _score_color(score: float) -> str:
    if score >= 76:
        return "#ff4d6a"
    if score >= 51:
        return "#f9cb28"
    if score >= 31:
        return "#007cf0"
    return "#50e3c2"


def _progress_bar(score: float) -> str:
    color = _score_color(score)
    pct = min(max(score, 0), 100)
    return (
        f'<div class="prog-wrap">'
        f'<div class="prog-bar"><div class="prog-fill" style="width:{pct}%;background:{color}"></div></div>'
        f'<span class="prog-val" style="color:{color}">{score:.1f}</span>'
        f'</div>'
    )


def _fmt_pct(val) -> str:
    try:
        v = float(val)
        color = "#ff4d6a" if v < 0 else "#50e3c2"
        return f'<span style="color:{color};font-family:JetBrains Mono,monospace;font-size:.78rem">{v:+.1f}%</span>'
    except (ValueError, TypeError):
        return '<span style="color:var(--text-muted)">—</span>'


# ╭──────────────────────────────────────────────────────────────────────────╮
# │  LOAD DATA                                                              │
# ╰──────────────────────────────────────────────────────────────────────────╯
try:
    df_all = load_data()
except Exception as exc:
    st.error(f"Failed to load data from MongoDB: {exc}")
    st.stop()

# ╭──────────────────────────────────────────────────────────────────────────╮
# │  PAGE HEADER                                                            │
# ╰──────────────────────────────────────────────────────────────────────────╯
st.markdown(
    """
    <div class="page-header">
        <h1>🎯 Customer Risk Ranking</h1>
        <div class="page-sub">
            Customers ranked by composite decay-risk score — higher scores
            indicate stronger signals of disengagement.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ╭──────────────────────────────────────────────────────────────────────────╮
# │  FILTERS ROW                                                            │
# ╰──────────────────────────────────────────────────────────────────────────╯
f1, f2, f3 = st.columns([2, 1, 1], gap="medium")

with f1:
    search = st.text_input(
        "Search by company name",
        placeholder="Type a company name…",
        label_visibility="collapsed",
    )

with f2:
    tier_options = ["All", "Gold", "Silver", "Bronze"]
    tier_filter = st.selectbox("Tier", tier_options, index=0, label_visibility="collapsed")

with f3:
    risk_options = ["All"] + RISK_ORDER
    risk_filter = st.selectbox("Risk Label", risk_options, index=0, label_visibility="collapsed")

# ── Apply filters ───────────────────────────────────────────────────────────
df = df_all.copy()

if search:
    df = df[df["company_name"].str.contains(search, case=False, na=False)]

if tier_filter != "All":
    df = df[df["tier"] == tier_filter]

if risk_filter != "All":
    df = df[df["risk_label"] == risk_filter]

df = df.sort_values("risk_score", ascending=False).reset_index(drop=True)

# ╭──────────────────────────────────────────────────────────────────────────╮
# │  SUMMARY METRICS                                                        │
# ╰──────────────────────────────────────────────────────────────────────────╯
total_shown = len(df)
avg_risk = df["risk_score"].mean() if total_shown else 0
critical_count = int((df["risk_label"] == "Critical").sum())
at_risk_count = int((df["risk_label"] == "At Risk").sum())

st.markdown(
    f"""
    <div class="m-grid">
        <div class="m-card c-cyan">
            <div class="m-val" style="color:var(--cyan)">{total_shown}</div>
            <div class="m-lbl">Customers Shown</div>
        </div>
        <div class="m-card c-blue">
            <div class="m-val" style="color:var(--blue)">{avg_risk:.1f}</div>
            <div class="m-lbl">Avg Risk Score</div>
        </div>
        <div class="m-card c-red">
            <div class="m-val" style="color:var(--red)">{critical_count}</div>
            <div class="m-lbl">Critical</div>
        </div>
        <div class="m-card c-amber">
            <div class="m-val" style="color:var(--amber)">{at_risk_count}</div>
            <div class="m-lbl">At Risk</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ╭──────────────────────────────────────────────────────────────────────────╮
# │  MAIN TABLE + INSIGHTS (two-column)                                     │
# ╰──────────────────────────────────────────────────────────────────────────╯
col_table, col_insights = st.columns([2.4, 1], gap="large")

# ── Risk Table ──────────────────────────────────────────────────────────────
with col_table:
    st.markdown('<div class="sec-title">Risk Table</div>', unsafe_allow_html=True)

    if df.empty:
        st.markdown(
            """
            <div style="background:var(--bg-card);border:1px solid var(--border);
                        border-radius:var(--r-md);padding:2rem;text-align:center;margin-top:.4rem">
                <div style="font-size:1.6rem;margin-bottom:.4rem">🔍</div>
                <div style="font-size:.92rem;color:var(--text-h);font-weight:600;
                            margin-bottom:.2rem">No customers match your filters</div>
                <div style="font-size:.82rem;color:var(--text-muted);line-height:1.5">
                    Try adjusting the search term, tier, or risk label filter above.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        rows_html = ""
        for _, r in df.iterrows():
            rows_html += f"""
            <tr>
                <td style="font-family:JetBrains Mono,monospace;font-size:.75rem;color:var(--text-muted)">{r.get('customer_id','—')}</td>
                <td class="name">{r.get('company_name','—')}</td>
                <td>{r.get('city','—')}</td>
                <td>{_tier_badge(r.get('tier','—'))}</td>
                <td>{r.get('account_manager','—')}</td>
                <td style="min-width:130px">{_progress_bar(r.get('risk_score',0))}</td>
                <td>{_risk_badge(r.get('risk_label','—'))}</td>
                <td>{_fmt_pct(r.get('aov_change_pct'))}</td>
                <td>{_fmt_pct(r.get('gap_change_pct'))}</td>
                <td>{_fmt_pct(r.get('diversity_delta'))}</td>
            </tr>"""

        st.markdown(
            f"""
            <div class="rt-wrap">
                <table class="rt">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Company</th>
                            <th>City</th>
                            <th>Tier</th>
                            <th>Account Mgr</th>
                            <th>Risk Score</th>
                            <th>Risk Label</th>
                            <th>AOV Δ</th>
                            <th>Gap Δ</th>
                            <th>Diversity Δ</th>
                        </tr>
                    </thead>
                    <tbody>{rows_html}</tbody>
                </table>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ── Insights Panel ──────────────────────────────────────────────────────────
with col_insights:
    st.markdown('<div class="sec-title">Insights</div>', unsafe_allow_html=True)

    # -- Top 5 highest-risk customers --
    top5 = df_all.nlargest(5, "risk_score")
    top5_rows = ""
    for _, r in top5.iterrows():
        color = _score_color(r["risk_score"])
        top5_rows += (
            f'<div class="ins-row">'
            f'<span class="lbl">{r.get("company_name","—")}</span>'
            f'<span class="val" style="color:{color}">{r["risk_score"]:.1f}</span>'
            f'</div>'
        )
    st.markdown(
        f'<div class="ins-card"><h4>⚠️ Top 5 Highest Risk</h4>{top5_rows}</div>',
        unsafe_allow_html=True,
    )

    # -- Average risk score by tier --
    if "tier" in df_all.columns:
        tier_avg = (
            df_all.groupby("tier")["risk_score"]
            .mean()
            .sort_values(ascending=False)
        )
        tier_rows = ""
        for tier_name, avg in tier_avg.items():
            color = _score_color(avg)
            tier_rows += (
                f'<div class="ins-row">'
                f'<span class="lbl">{_tier_badge(tier_name)}</span>'
                f'<span class="val" style="color:{color}">{avg:.1f}</span>'
                f'</div>'
            )
        st.markdown(
            f'<div class="ins-card"><h4>📊 Average Risk by Tier</h4>{tier_rows}</div>',
            unsafe_allow_html=True,
        )

    # -- Risk distribution summary --
    dist = (
        df_all["risk_label"]
        .value_counts()
        .reindex(RISK_ORDER, fill_value=0)
    )
    dist_rows = ""
    for label, count in dist.items():
        color = RISK_COLORS.get(label, "#555")
        pct = (count / len(df_all) * 100) if len(df_all) else 0
        dist_rows += (
            f'<div class="ins-row">'
            f'<span class="lbl">{_risk_badge(label)}</span>'
            f'<span class="val" style="color:{color}">{count} <span style="font-size:.7rem;color:var(--text-muted)">({pct:.0f}%)</span></span>'
            f'</div>'
        )
    st.markdown(
        f'<div class="ins-card"><h4>📉 Risk Distribution</h4>{dist_rows}</div>',
        unsafe_allow_html=True,
    )
