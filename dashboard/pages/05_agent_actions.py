"""
dashboard/pages/05_agent_actions.py
───────────────────────────────────
Intervention Management Dashboard — view, filter, and inspect
AI-generated retention interventions across Pending / Completed / Cancelled.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.db import connect_to_mongo

# ╭──────────────────────────────────────────────────────────────────────────╮
# │  PAGE CONFIG                                                            │
# ╰──────────────────────────────────────────────────────────────────────────╯
st.set_page_config(
    page_title="Agent Actions — DecayRader",
    page_icon="🤖",
    layout="wide",
)

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
    .page-sub {
        font-size: 0.85rem; color: var(--text-muted); margin-top: 2px;
    }

    /* ── KPI cards ──────────────────────────────────────────────────── */
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
    .m-card.c-amber::before  { background: var(--amber); }
    .m-card.c-green::before  { background: var(--green); }
    .m-card.c-muted::before  { background: var(--text-muted); }
    .m-card.c-red::before    { background: var(--red); }
    .m-val {
        font-size: 1.75rem; font-weight: 700;
        letter-spacing: -0.03em; line-height: 1;
    }
    .m-lbl {
        font-size: 0.7rem; color: var(--text-muted); margin-top: 5px;
        font-family: 'JetBrains Mono', monospace;
        text-transform: uppercase; letter-spacing: 0.06em;
    }

    /* ── section title ──────────────────────────────────────────────── */
    .sec-title {
        font-size: 1rem; font-weight: 600; color: var(--text-h);
        margin: 1.5rem 0 0.5rem; letter-spacing: -0.02em;
    }

    /* ── tables ─────────────────────────────────────────────────────── */
    .tb-wrap {
        background: var(--bg-card); border: 1px solid var(--border);
        border-radius: var(--r-md); overflow-x: auto; margin-top: 0.4rem;
    }
    .tb {
        width: 100%; border-collapse: collapse; font-size: 0.82rem;
    }
    .tb th {
        text-align: left; padding: 10px 12px; color: var(--text-muted);
        border-bottom: 1px solid var(--border); font-weight: 500;
        text-transform: uppercase; font-size: 0.68rem;
        letter-spacing: 0.06em;
        font-family: 'JetBrains Mono', monospace; white-space: nowrap;
    }
    .tb td {
        padding: 9px 12px; color: var(--text-p);
        border-bottom: 1px solid #1a1a1a; vertical-align: top;
    }
    .tb tr:last-child td { border-bottom: none; }
    .tb tr:hover td { background: rgba(255,255,255,.02); }
    .tb td.name { color: var(--text-h); font-weight: 500; white-space: nowrap; }

    /* ── badges ─────────────────────────────────────────────────────── */
    .rl {
        display: inline-block; padding: 2px 10px; border-radius: 100px;
        font-size: 0.72rem; font-weight: 500;
        font-family: 'JetBrains Mono', monospace;
    }
    .rl-critical  { background: rgba(255,77,106,.12); color: #ff4d6a; }
    .rl-atrisk    { background: rgba(249,203,40,.12); color: #f9cb28; }
    .rl-watch     { background: rgba(0,124,240,.12);  color: #007cf0; }
    .rl-healthy   { background: rgba(80,227,194,.12); color: #50e3c2; }

    .urg {
        display: inline-block; padding: 2px 10px; border-radius: 100px;
        font-size: 0.72rem; font-weight: 500;
        font-family: 'JetBrains Mono', monospace;
    }
    .urg-high   { background: rgba(255,77,106,.12); color: #ff4d6a; }
    .urg-medium { background: rgba(249,203,40,.12); color: #f9cb28; }
    .urg-low    { background: rgba(80,227,194,.12); color: #50e3c2; }

    .tier {
        display: inline-block; padding: 2px 8px; border-radius: 4px;
        font-size: 0.7rem; font-weight: 500;
        font-family: 'JetBrains Mono', monospace;
    }
    .tier-gold   { background: rgba(249,203,40,.1); color: #f9cb28; }
    .tier-silver { background: rgba(161,161,161,.1); color: #a1a1a1; }
    .tier-bronze { background: rgba(205,127,50,.12); color: #cd7f32; }

    .model-tag {
        display: inline-block; padding: 2px 8px; border-radius: 4px;
        font-size: 0.68rem; font-weight: 500;
        font-family: 'JetBrains Mono', monospace;
        background: rgba(121,40,202,.1); color: #a78bfa;
    }

    /* ── score pill ─────────────────────────────────────────────────── */
    .sc {
        font-family: 'JetBrains Mono', monospace;
        font-weight: 600; font-size: 0.8rem;
    }

    /* ── insight cards ──────────────────────────────────────────────── */
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
        padding: 5px 0; border-bottom: 1px solid #1a1a1a; font-size: 0.8rem;
    }
    .ins-row:last-child { border-bottom: none; }
    .ins-row .lbl { color: var(--text-p); }
    .ins-row .val {
        font-weight: 600; font-family: 'JetBrains Mono', monospace;
    }

    /* ── note text ──────────────────────────────────────────────────── */
    .note-text {
        font-size: 0.8rem; color: var(--text-p);
        font-style: italic; max-width: 300px;
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
# │  CONSTANTS                                                              │
# ╰──────────────────────────────────────────────────────────────────────────╯
PLOTLY_LAYOUT = dict(
    paper_bgcolor="#0a0a0a",
    plot_bgcolor="#0a0a0a",
    font=dict(family="Inter, system-ui, sans-serif", color="#a1a1a1", size=12),
)

# ╭──────────────────────────────────────────────────────────────────────────╮
# │  DATA LOADING                                                           │
# ╰──────────────────────────────────────────────────────────────────────────╯

@st.cache_data(ttl=60, show_spinner=False)
def load_interventions() -> pd.DataFrame:
    db = connect_to_mongo()
    docs = list(db["interventions"].find())
    df = pd.DataFrame(docs)
    df.drop(columns=["_id"], errors="ignore", inplace=True)
    return df


# ╭──────────────────────────────────────────────────────────────────────────╮
# │  HELPERS                                                                │
# ╰──────────────────────────────────────────────────────────────────────────╯

def _risk_badge(label: str) -> str:
    cls = {
        "Critical": "rl-critical", "At Risk": "rl-atrisk",
        "Watch": "rl-watch", "Healthy": "rl-healthy",
    }.get(str(label), "")
    return f'<span class="rl {cls}">{label}</span>'


def _urgency_badge(urgency: str) -> str:
    u = str(urgency).strip().lower()
    cls = {"high": "urg-high", "medium": "urg-medium", "low": "urg-low"}.get(u, "")
    return f'<span class="urg {cls}">{urgency}</span>'


def _tier_badge(tier: str) -> str:
    t = str(tier).strip().lower()
    cls = {"gold": "tier-gold", "silver": "tier-silver", "bronze": "tier-bronze"}.get(t, "")
    return f'<span class="tier {cls}">{tier}</span>'


def _model_tag(model: str) -> str:
    m = str(model) if pd.notna(model) else "—"
    if m == "—":
        return '<span style="color:var(--text-muted)">—</span>'
    return f'<span class="model-tag">{m}</span>'


def _score_color(score) -> str:
    try:
        s = float(score)
    except (ValueError, TypeError):
        return "#555"
    if s >= 76:
        return "#ff4d6a"
    if s >= 51:
        return "#f9cb28"
    if s >= 31:
        return "#007cf0"
    return "#50e3c2"


def _safe(val, fallback: str = "—") -> str:
    if pd.isna(val) or val is None or str(val).strip() == "":
        return fallback
    return str(val)


# ╭──────────────────────────────────────────────────────────────────────────╮
# │  LOAD DATA                                                              │
# ╰──────────────────────────────────────────────────────────────────────────╯
try:
    df_all = load_interventions()
except Exception as exc:
    st.error(f"Failed to load interventions from MongoDB: {exc}")
    st.stop()

# ╭──────────────────────────────────────────────────────────────────────────╮
# │  PAGE HEADER                                                            │
# ╰──────────────────────────────────────────────────────────────────────────╯
st.markdown(
    """
    <div class="page-header">
        <h1>🤖 Agent Actions</h1>
        <div class="page-sub">
            AI-generated intervention recommendations for at-risk customers.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ╭──────────────────────────────────────────────────────────────────────────╮
# │  SUMMARY METRICS                                                        │
# ╰──────────────────────────────────────────────────────────────────────────╯
status_col = df_all["status"].str.strip().str.lower() if "status" in df_all.columns else pd.Series(dtype=str)
pending_count = int((status_col == "pending").sum())
completed_count = int((status_col == "completed").sum())
cancelled_count = int((status_col == "cancelled").sum())

urgency_col = df_all["urgency"].str.strip().str.lower() if "urgency" in df_all.columns else pd.Series(dtype=str)
high_urgency = int((urgency_col == "high").sum())

st.markdown(
    f"""
    <div class="m-grid">
        <div class="m-card c-amber">
            <div class="m-val" style="color:var(--amber)">{pending_count}</div>
            <div class="m-lbl">Pending</div>
        </div>
        <div class="m-card c-green">
            <div class="m-val" style="color:var(--green)">{completed_count}</div>
            <div class="m-lbl">Completed</div>
        </div>
        <div class="m-card c-muted">
            <div class="m-val" style="color:var(--text-muted)">{cancelled_count}</div>
            <div class="m-lbl">Cancelled</div>
        </div>
        <div class="m-card c-red">
            <div class="m-val" style="color:var(--red)">{high_urgency}</div>
            <div class="m-lbl">High Urgency</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ╭──────────────────────────────────────────────────────────────────────────╮
# │  TABS + INSIGHTS (two-column layout)                                    │
# ╰──────────────────────────────────────────────────────────────────────────╯
col_main, col_insights = st.columns([2.4, 1], gap="large")

# ═══════════════════════════════════════════════════════════════════════════
#   LEFT COLUMN — Tabs
# ═══════════════════════════════════════════════════════════════════════════
with col_main:
    tab_pending, tab_completed, tab_cancelled = st.tabs(
        [f"⏳ Pending ({pending_count})", f"✅ Completed ({completed_count})", f"🚫 Cancelled ({cancelled_count})"]
    )

    # ── Pending Tab ─────────────────────────────────────────────────────
    with tab_pending:
        pending_df = df_all[status_col.values == "pending"].copy() if not df_all.empty else pd.DataFrame()

        if pending_df.empty:
            st.info("No pending interventions.")
        else:
            if "risk_score" in pending_df.columns:
                pending_df = pending_df.sort_values("risk_score", ascending=False)

            rows = ""
            for _, r in pending_df.iterrows():
                sc = r.get("risk_score", 0)
                sc_color = _score_color(sc)
                rows += f"""
                <tr>
                    <td class="name">{_safe(r.get('company_name'))}</td>
                    <td>{_tier_badge(_safe(r.get('tier')))}</td>
                    <td><span class="sc" style="color:{sc_color}">{float(sc):.1f}</span></td>
                    <td>{_risk_badge(_safe(r.get('risk_label')))}</td>
                    <td>{_urgency_badge(_safe(r.get('urgency')))}</td>
                    <td>{_safe(r.get('primary_action'))}</td>
                    <td style="color:var(--text-muted);font-size:.78rem">{_safe(r.get('secondary_action'))}</td>
                    <td style="font-family:'JetBrains Mono',monospace;font-size:.75rem">{_safe(r.get('follow_up_date'))}</td>
                    <td>{_model_tag(r.get('model_used'))}</td>
                </tr>"""

            st.markdown(
                f"""
                <div class="tb-wrap">
                    <table class="tb">
                        <thead><tr>
                            <th>Company</th><th>Tier</th><th>Score</th>
                            <th>Risk</th><th>Urgency</th><th>Primary Action</th>
                            <th>Secondary</th><th>Follow-up</th><th>Model</th>
                        </tr></thead>
                        <tbody>{rows}</tbody>
                    </table>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Expandable outreach messages
            st.markdown(
                '<div class="sec-title" style="margin-top:1.2rem">📨 Outreach Messages</div>',
                unsafe_allow_html=True,
            )
            for _, r in pending_df.iterrows():
                company = _safe(r.get("company_name"))
                message = _safe(r.get("outreach_message"), "No message generated.")
                risk_lbl = _safe(r.get("risk_label"))
                with st.expander(f"{company}  ·  {risk_lbl}", expanded=False):
                    st.markdown(
                        f'<div style="font-size:.88rem;color:var(--text-p);line-height:1.7;'
                        f'padding:0.5rem 0">{message}</div>',
                        unsafe_allow_html=True,
                    )

    # ── Completed Tab ───────────────────────────────────────────────────
    with tab_completed:
        completed_df = df_all[status_col.values == "completed"].copy() if not df_all.empty else pd.DataFrame()

        if completed_df.empty:
            st.info("No completed interventions.")
        else:
            rows = ""
            for _, r in completed_df.iterrows():
                note_val = _safe(r.get("note"))
                note_html = f'<span class="note-text">{note_val}</span>' if note_val != "—" else '<span style="color:var(--text-muted)">—</span>'
                rows += f"""
                <tr>
                    <td class="name">{_safe(r.get('company_name'))}</td>
                    <td>{_safe(r.get('primary_action'))}</td>
                    <td style="font-family:'JetBrains Mono',monospace;font-size:.75rem">{_safe(r.get('completed_at'))}</td>
                    <td>{note_html}</td>
                    <td>{_model_tag(r.get('model_used'))}</td>
                </tr>"""

            st.markdown(
                f"""
                <div class="tb-wrap">
                    <table class="tb">
                        <thead><tr>
                            <th>Company</th><th>Primary Action</th>
                            <th>Completed At</th><th>Note</th><th>Model</th>
                        </tr></thead>
                        <tbody>{rows}</tbody>
                    </table>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ── Cancelled Tab ───────────────────────────────────────────────────
    with tab_cancelled:
        cancelled_df = df_all[status_col.values == "cancelled"].copy() if not df_all.empty else pd.DataFrame()

        if cancelled_df.empty:
            st.info("No cancelled interventions.")
        else:
            rows = ""
            for _, r in cancelled_df.iterrows():
                note_val = _safe(r.get("note"))
                note_html = f'<span class="note-text">{note_val}</span>' if note_val != "—" else '<span style="color:var(--text-muted)">—</span>'
                rows += f"""
                <tr>
                    <td class="name">{_safe(r.get('company_name'))}</td>
                    <td>{_safe(r.get('primary_action'))}</td>
                    <td style="font-family:'JetBrains Mono',monospace;font-size:.75rem">{_safe(r.get('approved_at'))}</td>
                    <td>{note_html}</td>
                </tr>"""

            st.markdown(
                f"""
                <div class="tb-wrap">
                    <table class="tb">
                        <thead><tr>
                            <th>Company</th><th>Primary Action</th>
                            <th>Approved At</th><th>Note</th>
                        </tr></thead>
                        <tbody>{rows}</tbody>
                    </table>
                </div>
                """,
                unsafe_allow_html=True,
            )

# ═══════════════════════════════════════════════════════════════════════════
#   RIGHT COLUMN — Insights
# ═══════════════════════════════════════════════════════════════════════════
with col_insights:
    st.markdown('<div class="sec-title">Insights</div>', unsafe_allow_html=True)

    # ── 1. Action type distribution (donut) ─────────────────────────────
    if "primary_action" in df_all.columns and not df_all.empty:
        action_dist = df_all["primary_action"].value_counts().head(6)

        palette = ["#007cf0", "#00dfd8", "#7928ca", "#ff0080", "#f9cb28", "#50e3c2"]
        fig_actions = go.Figure(
            go.Pie(
                labels=action_dist.index.tolist(),
                values=action_dist.values.tolist(),
                hole=0.6,
                marker=dict(
                    colors=palette[: len(action_dist)],
                    line=dict(color="#0a0a0a", width=2),
                ),
                textinfo="label",
                textfont=dict(size=10, family="Inter"),
                hovertemplate="<b>%{label}</b><br>Count: %{value}<extra></extra>",
                sort=False,
            )
        )
        fig_actions.update_layout(
            **PLOTLY_LAYOUT,
            showlegend=False,
            height=230,
            margin=dict(l=10, r=10, t=25, b=10),
            annotations=[
                dict(
                    text="<b>Actions</b>",
                    x=0.5, y=0.5,
                    font=dict(size=13, color="#ededed", family="Inter"),
                    showarrow=False,
                )
            ],
        )
        st.markdown(
            '<div class="ins-card"><h4>🎬 Action Distribution</h4></div>',
            unsafe_allow_html=True,
        )
        st.plotly_chart(fig_actions, use_container_width=True, config={"displayModeBar": False})

    # ── 2. Urgency distribution ─────────────────────────────────────────
    if "urgency" in df_all.columns and not df_all.empty:
        urg_dist = (
            df_all["urgency"]
            .str.strip()
            .str.capitalize()
            .value_counts()
            .reindex(["High", "Medium", "Low"], fill_value=0)
        )
        urg_colors = {"High": "#ff4d6a", "Medium": "#f9cb28", "Low": "#50e3c2"}
        urg_rows = ""
        for label, count in urg_dist.items():
            pct = (count / len(df_all) * 100) if len(df_all) else 0
            c = urg_colors.get(label, "#555")
            bar_w = max(pct, 2)
            urg_rows += (
                f'<div class="ins-row">'
                f'<span class="lbl">{_urgency_badge(label)}</span>'
                f'<span class="val" style="color:{c}">{count}'
                f' <span style="font-size:.68rem;color:var(--text-muted)">({pct:.0f}%)</span></span>'
                f'</div>'
            )
        st.markdown(
            f'<div class="ins-card"><h4>⚡ Urgency Breakdown</h4>{urg_rows}</div>',
            unsafe_allow_html=True,
        )

    # ── 3. Model usage breakdown ────────────────────────────────────────
    if "model_used" in df_all.columns and not df_all.empty:
        model_dist = df_all["model_used"].dropna().value_counts().head(5)
        model_rows = ""
        for model_name, count in model_dist.items():
            model_rows += (
                f'<div class="ins-row">'
                f'<span class="lbl">{_model_tag(model_name)}</span>'
                f'<span class="val" style="color:var(--violet)">{count}</span>'
                f'</div>'
            )
        st.markdown(
            f'<div class="ins-card"><h4>🧠 Model Usage</h4>{model_rows}</div>',
            unsafe_allow_html=True,
        )

    # ── 4. Top recommended intervention types ───────────────────────────
    if "primary_action" in df_all.columns and not df_all.empty:
        top_actions = df_all["primary_action"].value_counts().head(5)
        ta_rows = ""
        colors_cycle = ["#007cf0", "#00dfd8", "#7928ca", "#ff0080", "#f9cb28"]
        for i, (action_name, count) in enumerate(top_actions.items()):
            c = colors_cycle[i % len(colors_cycle)]
            ta_rows += (
                f'<div class="ins-row">'
                f'<span class="lbl" style="max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{action_name}</span>'
                f'<span class="val" style="color:{c}">{count}</span>'
                f'</div>'
            )
        st.markdown(
            f'<div class="ins-card"><h4>🏆 Top Interventions</h4>{ta_rows}</div>',
            unsafe_allow_html=True,
        )
