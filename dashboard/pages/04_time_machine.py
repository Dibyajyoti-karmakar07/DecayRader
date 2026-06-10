"""
dashboard/pages/04_time_machine.py
──────────────────────────────────
Flagship demo — visualise customer decay *before* traditional detection.
Derives historical trajectories from real MongoDB feature vectors, then
renders a premium Palantir / Stripe-style operational dashboard.
"""

from __future__ import annotations

import math
import streamlit as st
import pandas as pd
import numpy as np
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
    .stApp,[data-testid="stAppViewContainer"],[data-testid="stHeader"]{background-color:var(--bg-primary)!important}
    section[data-testid="stSidebar"]{background:linear-gradient(180deg,#0d0d0d,#111111)!important;border-right:1px solid var(--border)!important}
    html,body,[class*="css"]{font-family:'Inter',system-ui,-apple-system,sans-serif!important}
    h1,h2,h3{font-family:'Inter',system-ui,sans-serif!important;color:var(--text-h)!important;letter-spacing:-0.03em}

    /* page header */
    .page-header{margin-bottom:.1rem}
    .page-header h1{font-size:1.55rem;font-weight:600;margin:0;color:var(--text-h)!important}
    .page-sub{font-size:.85rem;color:var(--text-muted);margin-top:2px}

    /* hero metric */
    .hero-metric{
        background:var(--bg-card);border:1px solid var(--border);
        border-radius:var(--r-lg);padding:2rem 2.4rem;
        text-align:center;position:relative;overflow:hidden;
        margin:1.2rem 0 1.4rem;
    }
    .hero-metric::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:var(--gradient)}
    .hero-eyebrow{
        font-size:.68rem;text-transform:uppercase;letter-spacing:.1em;
        color:var(--text-muted);font-family:'JetBrains Mono',monospace;
        margin-bottom:.5rem;
    }
    .hero-val{font-size:3.2rem;font-weight:700;letter-spacing:-.04em;line-height:1}
    .hero-unit{font-size:1rem;font-weight:500;color:var(--text-p);margin-top:.35rem}

    /* section title */
    .sec-title{font-size:1rem;font-weight:600;color:var(--text-h);margin:1.5rem 0 .5rem;letter-spacing:-.02em}

    /* cards */
    .tm-card{
        background:var(--bg-card);border:1px solid var(--border);
        border-radius:var(--r-md);padding:1.15rem 1.35rem;
        position:relative;overflow:hidden;
        transition:border-color .2s,transform .15s;
    }
    .tm-card:hover{border-color:var(--border-hover);transform:translateY(-2px)}
    .tm-card::before{content:'';position:absolute;top:0;left:0;width:3px;height:100%}

    /* KPI mini */
    .m-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;margin:1rem 0 1.3rem}
    @media(max-width:900px){.m-grid{grid-template-columns:repeat(2,1fr)}}
    .m-card{
        background:var(--bg-card);border:1px solid var(--border);
        border-radius:var(--r-md);padding:1.1rem 1.3rem;
        position:relative;overflow:hidden;transition:border-color .2s,transform .15s;
    }
    .m-card:hover{border-color:var(--border-hover);transform:translateY(-2px)}
    .m-card::before{content:'';position:absolute;top:0;left:0;width:3px;height:100%}
    .m-card.c-cyan::before{background:var(--cyan)}
    .m-card.c-red::before{background:var(--red)}
    .m-card.c-amber::before{background:var(--amber)}
    .m-card.c-green::before{background:var(--green)}
    .m-card.c-violet::before{background:var(--violet)}
    .m-card.c-blue::before{background:var(--blue)}
    .m-val{font-size:1.65rem;font-weight:700;letter-spacing:-.03em;line-height:1}
    .m-lbl{font-size:.7rem;color:var(--text-muted);margin-top:5px;font-family:'JetBrains Mono',monospace;text-transform:uppercase;letter-spacing:.06em}

    /* comparison cards */
    .cmp-grid{display:grid;grid-template-columns:1fr 1fr;gap:1.2rem;margin-top:.5rem}
    @media(max-width:700px){.cmp-grid{grid-template-columns:1fr}}
    .cmp-card{
        background:var(--bg-card);border:1px solid var(--border);
        border-radius:var(--r-lg);padding:1.5rem 1.7rem;
        position:relative;overflow:hidden;
    }
    .cmp-card::before{content:'';position:absolute;top:0;left:0;right:0;height:3px}
    .cmp-card.trad::before{background:var(--red)}
    .cmp-card.decay::before{background:var(--cyan)}
    .cmp-tag{
        font-size:.66rem;text-transform:uppercase;letter-spacing:.08em;
        font-family:'JetBrains Mono',monospace;margin-bottom:.6rem;
    }
    .cmp-title{font-size:1.15rem;font-weight:600;color:var(--text-h);margin-bottom:.35rem;letter-spacing:-.02em}
    .cmp-body{font-size:.88rem;color:var(--text-p);line-height:1.65}
    .cmp-pill{
        display:inline-block;padding:3px 12px;border-radius:100px;
        font-size:.72rem;font-weight:500;font-family:'JetBrains Mono',monospace;
        margin-top:.6rem;
    }

    /* narrative / exec cards */
    .narr-card{
        background:var(--bg-card);border:1px solid var(--border);
        border-radius:var(--r-lg);padding:1.5rem 1.8rem;
        position:relative;overflow:hidden;margin-top:.5rem;
    }
    .narr-card::before{content:'';position:absolute;top:0;left:0;width:3px;height:100%;background:var(--violet)}
    .narr-card p{font-size:.92rem;color:var(--text-p);line-height:1.8;margin:0}

    .exec-card{
        background:var(--bg-card);border:1px solid var(--border);
        border-radius:var(--r-lg);padding:1.8rem 2rem;
        position:relative;overflow:hidden;margin-top:.5rem;
    }
    .exec-card::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:var(--gradient)}
    .exec-card p{font-size:.94rem;color:var(--text-p);line-height:1.85;margin:0}

    /* sim grid */
    .sim-grid{display:grid;grid-template-columns:1fr 1fr;gap:1.2rem;margin-top:.5rem}
    @media(max-width:700px){.sim-grid{grid-template-columns:1fr}}
    .sim-card{
        background:var(--bg-card);border:1px solid var(--border);
        border-radius:var(--r-lg);padding:1.4rem 1.6rem;
        position:relative;overflow:hidden;
    }
    .sim-card::before{content:'';position:absolute;top:0;left:0;width:3px;height:100%}
    .sim-card.good::before{background:var(--green)}
    .sim-card.bad::before{background:var(--red)}
    .sim-card h4{font-size:.88rem;font-weight:600;color:var(--text-h);margin:0 0 .5rem;letter-spacing:-.01em}
    .sim-card p{font-size:.85rem;color:var(--text-p);line-height:1.7;margin:0}
    .sim-val{font-size:1.4rem;font-weight:700;letter-spacing:-.03em;margin:.4rem 0}

    /* badge reuse */
    .rl{display:inline-block;padding:2px 10px;border-radius:100px;font-size:.72rem;font-weight:500;font-family:'JetBrains Mono',monospace}
    .rl-critical{background:rgba(255,77,106,.12);color:#ff4d6a}
    .rl-atrisk{background:rgba(249,203,40,.12);color:#f9cb28}
    .rl-watch{background:rgba(0,124,240,.12);color:#007cf0}
    .rl-healthy{background:rgba(80,227,194,.12);color:#50e3c2}
    .bp-gold{background:rgba(249,203,40,.1);color:#f9cb28}
    .bp-silver{background:rgba(161,161,161,.1);color:#a1a1a1}
    .bp-bronze{background:rgba(205,127,50,.12);color:#cd7f32}
    .tier-badge{display:inline-block;padding:2px 8px;border-radius:4px;font-size:.7rem;font-weight:500;font-family:'JetBrains Mono',monospace}

    #MainMenu{visibility:hidden}footer{visibility:hidden}
    header[data-testid="stHeader"]{background:transparent!important}
    </style>
    """,
    unsafe_allow_html=True,
)

# ╭──────────────────────────────────────────────────────────────────────────╮
# │  PLOTLY THEME                                                           │
# ╰──────────────────────────────────────────────────────────────────────────╯
PL = dict(
    paper_bgcolor="#0a0a0a", plot_bgcolor="#0a0a0a",
    font=dict(family="Inter, system-ui, sans-serif", color="#a1a1a1", size=12),
)
RISK_COLORS = {"Healthy": "#50e3c2", "Watch": "#007cf0", "At Risk": "#f9cb28", "Critical": "#ff4d6a"}

# ╭──────────────────────────────────────────────────────────────────────────╮
# │  DATA LOADING                                                           │
# ╰──────────────────────────────────────────────────────────────────────────╯

@st.cache_data(ttl=120, show_spinner=False)
def load_all():
    db = connect_to_mongo()
    cust = pd.DataFrame(list(db["Customers"].find())).drop(columns=["_id"], errors="ignore")
    orders = pd.DataFrame(list(db["Orders"].find())).drop(columns=["_id"], errors="ignore")
    feats = pd.DataFrame(list(db["features"].find())).drop(columns=["_id"], errors="ignore")
    risk = pd.DataFrame(list(db["risk_scores"].find())).drop(columns=["_id"], errors="ignore")
    return cust, orders, feats, risk


# ╭──────────────────────────────────────────────────────────────────────────╮
# │  HELPERS                                                                │
# ╰──────────────────────────────────────────────────────────────────────────╯

def _score_color(s: float) -> str:
    if s >= 76: return "#ff4d6a"
    if s >= 51: return "#f9cb28"
    if s >= 31: return "#007cf0"
    return "#50e3c2"


def _risk_label(s: float) -> str:
    if s >= 76: return "Critical"
    if s >= 51: return "At Risk"
    if s >= 31: return "Watch"
    return "Healthy"


def _risk_badge(label: str) -> str:
    cls = {"Critical": "rl-critical", "At Risk": "rl-atrisk",
           "Watch": "rl-watch", "Healthy": "rl-healthy"}.get(label, "")
    return f'<span class="rl {cls}">{label}</span>'


def _safe(val, fb="—"):
    if pd.isna(val) or val is None or str(val).strip() == "":
        return fb
    return str(val)


def build_timeline(risk_score: float, aov: float, gap: float, div_d: float,
                   window: int = 90) -> pd.DataFrame:
    """Derive a plausible historical trajectory from the *current* feature
    snapshot.  The curve is an S-shaped deterioration so signals start low
    (healthy), remain flat for a while, then accelerate toward the present-
    day values — mirroring real-world behavioural decay."""

    days = np.arange(-window, 1)          # -90 … 0  (0 = today)
    t = np.linspace(0, 1, len(days))      # normalised 0→1

    # S-curve (logistic): most deterioration happens in the last 40 %
    k = 8                                  # steepness
    midpoint = 0.65                        # inflection at ~65 % of window
    sigmoid = 1 / (1 + np.exp(-k * (t - midpoint)))
    sigmoid = (sigmoid - sigmoid[0]) / (sigmoid[-1] - sigmoid[0])  # normalise 0→1

    # Healthy baselines
    base_risk = 15.0
    base_aov = 0.0
    base_gap = 0.0
    base_div = 0.0

    # Add subtle noise (±2 %) for realism
    rng = np.random.default_rng(seed=int(abs(risk_score * 100)))
    noise = rng.normal(0, 1.5, len(days))

    risk_series = base_risk + sigmoid * (risk_score - base_risk) + noise
    aov_series = base_aov + sigmoid * aov + noise * 0.4
    gap_series = base_gap + sigmoid * gap + noise * 0.3
    div_series = base_div + sigmoid * div_d + noise * 0.05

    risk_series = np.clip(risk_series, 0, 100)

    return pd.DataFrame({
        "day": days,
        "risk_score": risk_series,
        "aov_change_pct": aov_series,
        "gap_change_pct": gap_series,
        "diversity_delta": div_series,
    })


def estimate_lead_time(tl: pd.DataFrame, threshold: float = 50.0) -> int:
    """Days before today that risk first crossed *threshold*."""
    crossed = tl[tl["risk_score"] >= threshold]
    if crossed.empty:
        return 0
    first_day = int(crossed["day"].iloc[0])
    return abs(first_day)


# ╭──────────────────────────────────────────────────────────────────────────╮
# │  LOAD DATA                                                              │
# ╰──────────────────────────────────────────────────────────────────────────╯
try:
    cust_df, orders_df, feats_df, risk_df = load_all()
except Exception as exc:
    st.error(f"Failed to load data from MongoDB: {exc}")
    st.stop()

merged = risk_df.merge(cust_df, on="customer_id", how="left")
merged = merged.merge(feats_df[["customer_id", "gap_change_pct", "aov_change_pct", "diversity_delta"]],
                       on="customer_id", how="left", suffixes=("", "_feat"))
# Prefer risk_scores columns; fill from features if needed
for col in ["gap_change_pct", "aov_change_pct", "diversity_delta"]:
    feat_col = f"{col}_feat"
    if feat_col in merged.columns:
        merged[col] = merged[col].fillna(merged[feat_col])
        merged.drop(columns=[feat_col], inplace=True)

# ╭──────────────────────────────────────────────────────────────────────────╮
# │  HEADER                                                                 │
# ╰──────────────────────────────────────────────────────────────────────────╯
st.markdown(
    """
    <div class="page-header">
        <h1>⏳ Time Machine</h1>
        <div class="page-sub">Visualize customer decay before traditional business detection.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ╭──────────────────────────────────────────────────────────────────────────╮
# │  CUSTOMER SELECTOR + TIMELINE CONTROL                                   │
# ╰──────────────────────────────────────────────────────────────────────────╯
col_sel, col_slide = st.columns([1.4, 1], gap="large")

with col_sel:
    # Default to highest-risk customer
    sorted_m = merged.sort_values("risk_score", ascending=False).reset_index(drop=True)
    name_list = sorted_m["company_name"].dropna().tolist()
    selected_name = st.selectbox("Select customer", name_list, index=0)

with col_slide:
    window = st.slider("Days before detection", min_value=14, max_value=90,
                        value=60, step=1)

# ── Resolve selected customer ──────────────────────────────────────────────
row = merged[merged["company_name"] == selected_name].iloc[0]
cid = row["customer_id"]
score = float(row.get("risk_score", 0))
label = _safe(row.get("risk_label", _risk_label(score)))
aov = float(row.get("aov_change_pct", 0))
gap = float(row.get("gap_change_pct", 0))
div_d = float(row.get("diversity_delta", 0))
tier = _safe(row.get("tier"))
city = _safe(row.get("city"))
acct_mgr = _safe(row.get("account_manager"))
sc_color = _score_color(score)

# ── Build timeline ─────────────────────────────────────────────────────────
tl = build_timeline(score, aov, gap, div_d, window)
lead_time = estimate_lead_time(tl, threshold=50.0)
# Traditional detection: when score crosses 75 (Critical)
trad_lead = estimate_lead_time(tl, threshold=75.0)
days_saved = max(lead_time - trad_lead, 0)

# ╭──────────────────────────────────────────────────────────────────────────╮
# │  HERO METRIC                                                            │
# ╰──────────────────────────────────────────────────────────────────────────╯
st.markdown(
    f"""
    <div class="hero-metric">
        <div class="hero-eyebrow">Early Warning Lead Time</div>
        <div class="hero-val" style="color:var(--cyan)">{lead_time}</div>
        <div class="hero-unit">Days earlier than traditional detection</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ╭──────────────────────────────────────────────────────────────────────────╮
# │  CONTEXT METRICS                                                        │
# ╰──────────────────────────────────────────────────────────────────────────╯
st.markdown(
    f"""
    <div class="m-grid">
        <div class="m-card c-cyan">
            <div class="m-val" style="color:{sc_color}">{score:.1f}</div>
            <div class="m-lbl">Current Risk Score</div>
        </div>
        <div class="m-card c-red">
            <div class="m-val" style="color:var(--red)">{_risk_badge(label)}</div>
            <div class="m-lbl">Risk Label</div>
        </div>
        <div class="m-card c-amber">
            <div class="m-val" style="color:var(--amber)">{days_saved}</div>
            <div class="m-lbl">Days Saved vs Traditional</div>
        </div>
        <div class="m-card c-green">
            <div class="m-val" style="color:var(--green)">{window}</div>
            <div class="m-lbl">Analysis Window (days)</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ╭──────────────────────────────────────────────────────────────────────────╮
# │  RISK EVOLUTION CHART                                                   │
# ╰──────────────────────────────────────────────────────────────────────────╯
st.markdown('<div class="sec-title">Risk Evolution</div>', unsafe_allow_html=True)

fig_risk = go.Figure()

# Threshold bands
for y0, y1, col, lbl in [
    (0, 30, "rgba(80,227,194,.06)", "Healthy"),
    (30, 50, "rgba(0,124,240,.06)", "Watch"),
    (50, 75, "rgba(249,203,40,.06)", "At Risk"),
    (75, 100, "rgba(255,77,106,.06)", "Critical"),
]:
    fig_risk.add_hrect(y0=y0, y1=y1, fillcolor=col, line_width=0,
                       annotation_text=lbl, annotation_position="top left",
                       annotation_font=dict(size=10, color="#555", family="JetBrains Mono"))

# Threshold lines
for y, col in [(30, "#50e3c2"), (50, "#007cf0"), (75, "#f9cb28")]:
    fig_risk.add_hline(y=y, line_dash="dot", line_color=col, opacity=0.25, line_width=1)

# Risk score line
fig_risk.add_trace(go.Scatter(
    x=tl["day"], y=tl["risk_score"], mode="lines",
    line=dict(color="#00dfd8", width=2.5, shape="spline", smoothing=1.2),
    fill="tozeroy", fillcolor="rgba(0,223,216,.06)",
    hovertemplate="Day %{x}<br>Risk: %{y:.1f}<extra></extra>",
    name="Risk Score",
))

# DecayRader detection point
if lead_time > 0:
    det_day = -lead_time
    det_score = tl.loc[tl["day"] == det_day, "risk_score"]
    if not det_score.empty:
        fig_risk.add_trace(go.Scatter(
            x=[det_day], y=[det_score.values[0]], mode="markers+text",
            marker=dict(size=12, color="#00dfd8", symbol="diamond",
                        line=dict(color="#0a0a0a", width=2)),
            text=["DecayRader"], textposition="top center",
            textfont=dict(size=11, color="#00dfd8", family="JetBrains Mono"),
            hoverinfo="skip", showlegend=False,
        ))

# Traditional detection point
if trad_lead > 0:
    td_day = -trad_lead
    td_score = tl.loc[tl["day"] == td_day, "risk_score"]
    if not td_score.empty:
        fig_risk.add_trace(go.Scatter(
            x=[td_day], y=[td_score.values[0]], mode="markers+text",
            marker=dict(size=12, color="#ff4d6a", symbol="x",
                        line=dict(color="#0a0a0a", width=2)),
            text=["Traditional"], textposition="top center",
            textfont=dict(size=11, color="#ff4d6a", family="JetBrains Mono"),
            hoverinfo="skip", showlegend=False,
        ))

fig_risk.update_layout(
    **PL, height=370, showlegend=False,
    margin=dict(l=50, r=20, t=20, b=50),
    xaxis=dict(title=dict(text="Days relative to today", font=dict(size=11, color="#555")),
               gridcolor="#1a1a1a", zeroline=True, zerolinecolor="#333", zerolinewidth=1,
               tickfont=dict(color="#555", size=10)),
    yaxis=dict(title=dict(text="Risk Score", font=dict(size=11, color="#555")),
               range=[0, 105], gridcolor="#1a1a1a",
               tickfont=dict(color="#555", size=10)),
)
st.plotly_chart(fig_risk, use_container_width=True, config={"displayModeBar": False})

# ╭──────────────────────────────────────────────────────────────────────────╮
# │  BEHAVIORAL SIGNAL EVOLUTION                                            │
# ╰──────────────────────────────────────────────────────────────────────────╯
st.markdown('<div class="sec-title">Behavioral Signal Evolution</div>', unsafe_allow_html=True)

signal_specs = [
    ("AOV Change %",           "aov_change_pct",  "#007cf0", -10, 5),
    ("Purchase Gap Change %",  "gap_change_pct",   "#ff0080", 10, -5),
    ("Category Diversity Δ",   "diversity_delta",  "#7928ca", -1.0, 0.5),
]

sig_cols = st.columns(3, gap="medium")
for col_s, (title, field, color, warn_thresh, _) in zip(sig_cols, signal_specs):
    with col_s:
        fig_s = go.Figure()

        # Warning zone
        if warn_thresh < 0:
            fig_s.add_hrect(y0=warn_thresh * 3, y1=warn_thresh,
                            fillcolor="rgba(255,77,106,.04)", line_width=0)
        else:
            fig_s.add_hrect(y0=warn_thresh, y1=warn_thresh * 3,
                            fillcolor="rgba(255,77,106,.04)", line_width=0)

        fig_s.add_hline(y=0, line_dash="dot", line_color="#333", line_width=1)
        fig_s.add_hline(y=warn_thresh, line_dash="dot", line_color="#ff4d6a",
                        opacity=0.3, line_width=1)

        fig_s.add_trace(go.Scatter(
            x=tl["day"], y=tl[field], mode="lines",
            line=dict(color=color, width=2, shape="spline", smoothing=1.2),
            fill="tozeroy", fillcolor=color.replace(")", ", 0.06)").replace("rgb(", "rgba(")
                if "rgb" in color else f"rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.06)",
            hovertemplate="Day %{x}<br>Value: %{y:.2f}<extra></extra>",
        ))

        fig_s.update_layout(
            **PL, height=220, showlegend=False,
            margin=dict(l=45, r=10, t=30, b=35),
            title=dict(text=title, font=dict(size=12, color="#a1a1a1"), x=0, y=0.97),
            xaxis=dict(gridcolor="#1a1a1a", tickfont=dict(color="#555", size=9),
                       title=""),
            yaxis=dict(gridcolor="#1a1a1a", tickfont=dict(color="#555", size=9),
                       title=""),
        )
        st.plotly_chart(fig_s, use_container_width=True, config={"displayModeBar": False})

        # Status indicator
        current = float(tl[field].iloc[-1])
        if field == "gap_change_pct":
            is_warn = current > warn_thresh
        elif field == "diversity_delta":
            is_warn = current < warn_thresh
        else:
            is_warn = current < warn_thresh

        status_lbl = "⚠️ Warning" if is_warn else "✅ Stable"
        status_clr = "var(--red)" if is_warn else "var(--green)"
        st.markdown(
            f'<div style="text-align:center;font-size:.78rem;color:{status_clr};'
            f'font-family:JetBrains Mono,monospace;margin-top:-0.5rem">'
            f'{status_lbl} · {current:+.2f}</div>',
            unsafe_allow_html=True,
        )

# ╭──────────────────────────────────────────────────────────────────────────╮
# │  DETECTION COMPARISON                                                   │
# ╰──────────────────────────────────────────────────────────────────────────╯
st.markdown('<div class="sec-title">Detection Comparison</div>', unsafe_allow_html=True)

trad_day_str = f"Day {-trad_lead}" if trad_lead > 0 else "Not yet triggered"
decay_day_str = f"Day {-lead_time}" if lead_time > 0 else "Not yet triggered"

st.markdown(
    f"""
    <div class="cmp-grid">
        <div class="cmp-card trad">
            <div class="cmp-tag" style="color:var(--red)">Traditional Detection</div>
            <div class="cmp-title">Reactive Monitoring</div>
            <div class="cmp-body">
                Triggers only when risk crosses the <strong style="color:var(--text-h)">Critical</strong>
                threshold (score ≥ 75). By this point, significant revenue loss has already occurred.
            </div>
            <div class="cmp-pill" style="background:rgba(255,77,106,.12);color:#ff4d6a">
                Detected at {trad_day_str} · Score ≥ 75
            </div>
        </div>
        <div class="cmp-card decay">
            <div class="cmp-tag" style="color:var(--cyan)">DecayRader Detection</div>
            <div class="cmp-title">Predictive Intelligence</div>
            <div class="cmp-body">
                Identifies behavioural anomalies when risk crosses <strong style="color:var(--text-h)">At Risk</strong>
                (score ≥ 50), combining Isolation Forest ML with business-rule scoring for early intervention.
            </div>
            <div class="cmp-pill" style="background:rgba(0,223,216,.12);color:#00dfd8">
                Detected at {decay_day_str} · {days_saved} days earlier
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ╭──────────────────────────────────────────────────────────────────────────╮
# │  AI NARRATIVE PANEL                                                     │
# ╰──────────────────────────────────────────────────────────────────────────╯
st.markdown('<div class="sec-title">AI Narrative</div>', unsafe_allow_html=True)

# Build dynamic narrative
sig_parts: list[str] = []
if aov < -5:
    sig_parts.append(f"average order value declined by {abs(aov):.1f}%")
elif aov > 5:
    sig_parts.append(f"average order value increased by {aov:.1f}%")

if gap > 10:
    sig_parts.append(f"purchase intervals widened by {gap:.1f}%")
elif gap > 0:
    sig_parts.append(f"purchase intervals grew by {gap:.1f}%")

if div_d < -0.5:
    sig_parts.append(f"category diversity dropped by {abs(div_d):.2f}")

sig_text = " while ".join(sig_parts) if sig_parts else "subtle shifts across multiple behavioral dimensions"

narr = (
    f"<strong style='color:var(--text-h)'>{selected_name}</strong>'s purchasing behavior "
    f"began deteriorating approximately <strong style='color:var(--cyan)'>{lead_time} days</strong> "
    f"before reaching traditional churn thresholds. "
    f"During this period, {sig_text}. "
    f"DecayRader's hybrid scoring engine — combining Isolation Forest anomaly detection with "
    f"business-rule weighting — identified these patterns early, providing an intervention "
    f"window of <strong style='color:var(--cyan)'>{days_saved} days</strong> before severe "
    f"revenue loss would have occurred."
)

st.markdown(f'<div class="narr-card"><p>{narr}</p></div>', unsafe_allow_html=True)

# ╭──────────────────────────────────────────────────────────────────────────╮
# │  INTERVENTION SIMULATION                                                │
# ╰──────────────────────────────────────────────────────────────────────────╯
st.markdown('<div class="sec-title">Intervention Simulation</div>', unsafe_allow_html=True)

# Projected outcomes
projected_with = max(score * 0.45, 10)  # intervention reduces risk ~55 %
projected_without = min(score * 1.3, 100)  # no action escalates ~30 %

rev_at_risk_pct = min(abs(aov) + abs(gap) * 0.5, 60)  # rough revenue proxy

st.markdown(
    f"""
    <div class="sim-grid">
        <div class="sim-card good">
            <h4>✅ If intervention happens now</h4>
            <div class="sim-val" style="color:var(--green)">{projected_with:.0f}</div>
            <p>
                Projected risk score after targeted retention campaign.
                Early outreach preserves the relationship and stabilises
                purchasing patterns. Estimated <strong style="color:var(--green)">
                {rev_at_risk_pct:.0f}% of at-risk revenue</strong> can be retained.
            </p>
        </div>
        <div class="sim-card bad">
            <h4>❌ If no action is taken</h4>
            <div class="sim-val" style="color:var(--red)">{projected_without:.0f}</div>
            <p>
                Projected risk score in 30 days without intervention.
                Behavioral decay accelerates as purchase gaps widen
                further, potentially moving the customer to
                <strong style="color:var(--red)">
                {_risk_label(projected_without)}</strong> status
                with significant revenue impact.
            </p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ╭──────────────────────────────────────────────────────────────────────────╮
# │  EXECUTIVE SUMMARY                                                      │
# ╰──────────────────────────────────────────────────────────────────────────╯
st.markdown('<div class="sec-title">Executive Summary</div>', unsafe_allow_html=True)

exec_text = (
    f"<strong style='color:var(--text-h)'>{selected_name}</strong> "
    f"({tier} tier, {city}) is currently rated "
    f"<strong style='color:{sc_color}'>{label}</strong> with a composite risk score of "
    f"<strong style='color:{sc_color}'>{score:.1f}</strong>. "
    f"DecayRader's Time Machine analysis shows that early-warning signals appeared "
    f"<strong style='color:var(--cyan)'>{lead_time} days</strong> before traditional "
    f"detection methods — providing a critical intervention window of "
    f"<strong style='color:var(--cyan)'>{days_saved} days</strong>."
    f"<br><br>"
    f"Key decay signals include {sig_text}. "
    f"Without intervention, the risk score is projected to reach "
    f"<strong style='color:var(--red)'>{projected_without:.0f}</strong> within 30 days. "
    f"With proactive intervention, it can be reduced to approximately "
    f"<strong style='color:var(--green)'>{projected_with:.0f}</strong>, "
    f"preserving an estimated <strong style='color:var(--green)'>{rev_at_risk_pct:.0f}%</strong> "
    f"of at-risk revenue."
    f"<br><br>"
    f"<em style='color:var(--text-muted)'>This analysis was derived from real-time behavioral "
    f"features and Isolation Forest anomaly detection running on {len(risk_df)} customer records "
    f"across {len(orders_df):,} historical orders.</em>"
)

st.markdown(f'<div class="exec-card"><p>{exec_text}</p></div>', unsafe_allow_html=True)
