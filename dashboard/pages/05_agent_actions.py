"""
dashboard/pages/05_agent_actions.py
───────────────────────────────────
Intervention Management Dashboard — workflow-first layout.
Tabs (Pending / Completed / Cancelled) appear directly beneath KPIs.
Full CRUD: Edit, Delete, Clear All, Status management, Notes, Reopen.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from bson import ObjectId
from datetime import datetime, timezone
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

AVAILABLE_ACTIONS = [
    "Email Customer",
    "Phone Call",
    "Video Meeting",
    "In-Person Visit",
    "CRM Follow-Up",
    "Notify Team",
]

URGENCY_OPTIONS = ["High", "Medium", "Low"]
URGENCY_SORT = {"high": 0, "medium": 1, "low": 2}


# ╭──────────────────────────────────────────────────────────────────────────╮
# │  DB HELPERS                                                             │
# ╰──────────────────────────────────────────────────────────────────────────╯

def _get_db():
    return connect_to_mongo()


def _reload_and_rerun():
    """Clear cache and rerun the page."""
    load_interventions.clear()
    st.rerun()


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


# ╭──────────────────────────────────────────────────────────────────────────╮
# │  DATA LOADING                                                           │
# ╰──────────────────────────────────────────────────────────────────────────╯

@st.cache_data(ttl=60, show_spinner=False)
def load_interventions() -> pd.DataFrame:
    db = _get_db()
    docs = list(db["interventions"].find())
    df = pd.DataFrame(docs)
    if "_id" in df.columns:
        df["_id"] = df["_id"].astype(str)
    return df


# ╭──────────────────────────────────────────────────────────────────────────╮
# │  CRUD OPERATIONS                                                        │
# ╰──────────────────────────────────────────────────────────────────────────╯

def _update_intervention(doc_id: str, updates: dict) -> bool:
    """Update a single intervention by _id. Always stamps updated_at."""
    try:
        updates["updated_at"] = _now_utc()
        db = _get_db()
        db["interventions"].update_one(
            {"_id": ObjectId(doc_id)},
            {"$set": updates},
        )
        return True
    except Exception:
        return False


def _delete_intervention(doc_id: str) -> bool:
    try:
        db = _get_db()
        db["interventions"].delete_one({"_id": ObjectId(doc_id)})
        return True
    except Exception:
        return False


def _clear_all_interventions() -> int:
    try:
        db = _get_db()
        result = db["interventions"].delete_many({})
        return result.deleted_count
    except Exception:
        return 0


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


def _sort_pending(df: pd.DataFrame) -> pd.DataFrame:
    """Sort pending: highest urgency first, then newest first."""
    if df.empty:
        return df
    df = df.copy()
    if "urgency" in df.columns:
        df["_urg_rank"] = df["urgency"].str.strip().str.lower().map(URGENCY_SORT).fillna(9)
    else:
        df["_urg_rank"] = 9
    sort_col = "created_at" if "created_at" in df.columns else "approved_at"
    if sort_col in df.columns:
        df = df.sort_values(["_urg_rank", sort_col], ascending=[True, False])
    else:
        df = df.sort_values("_urg_rank", ascending=True)
    return df.drop(columns=["_urg_rank"]).reset_index(drop=True)


def _sort_newest(df: pd.DataFrame) -> pd.DataFrame:
    """Sort by newest first (created_at or approved_at)."""
    if df.empty:
        return df
    sort_col = "created_at" if "created_at" in df.columns else "approved_at"
    if sort_col in df.columns:
        return df.sort_values(sort_col, ascending=False).reset_index(drop=True)
    return df


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
            Manage AI-generated interventions — review, approve, edit, and track retention actions.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ╭──────────────────────────────────────────────────────────────────────────╮
# │  SUMMARY METRICS                                                        │
# ╰──────────────────────────────────────────────────────────────────────────╯
status_col = (
    df_all["status"].str.strip().str.lower()
    if "status" in df_all.columns
    else pd.Series(dtype=str)
)
pending_count   = int((status_col == "pending").sum())
completed_count = int((status_col == "completed").sum())
cancelled_count = int((status_col == "cancelled").sum())

urgency_col = (
    df_all["urgency"].str.strip().str.lower()
    if "urgency" in df_all.columns
    else pd.Series(dtype=str)
)
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
# │  INSIGHTS (below metrics, above tabs)                                   │
# ╰──────────────────────────────────────────────────────────────────────────╯
st.markdown('---')
st.markdown('<div class="sec-title">📊 Insights</div>', unsafe_allow_html=True)

ins_c1, ins_c2, ins_c3 = st.columns(3, gap="medium")

# ── 1. Action distribution donut ────────────────────────────────────────
with ins_c1:
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

# ── 2. Urgency breakdown ────────────────────────────────────────────────
with ins_c2:
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

    # Model usage
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

# ── 3. Top interventions ────────────────────────────────────────────────
with ins_c3:
    if "primary_action" in df_all.columns and not df_all.empty:
        top_actions = df_all["primary_action"].value_counts().head(5)
        ta_rows = ""
        colors_cycle = ["#007cf0", "#00dfd8", "#7928ca", "#ff0080", "#f9cb28"]
        for i, (action_name, count) in enumerate(top_actions.items()):
            c = colors_cycle[i % len(colors_cycle)]
            ta_rows += (
                f'<div class="ins-row">'
                f'<span class="lbl" style="max-width:180px;overflow:hidden;'
                f'text-overflow:ellipsis;white-space:nowrap">{action_name}</span>'
                f'<span class="val" style="color:{c}">{count}</span>'
                f'</div>'
            )
        st.markdown(
            f'<div class="ins-card"><h4>🏆 Top Interventions</h4>{ta_rows}</div>',
            unsafe_allow_html=True,
        )

# ╭──────────────────────────────────────────────────────────────────────────╮
# │  CLEAR ALL (compact, beside header)                                     │
# ╰──────────────────────────────────────────────────────────────────────────╯
st.markdown('---')

if not df_all.empty:
    col_clr, _ = st.columns([1, 4])
    with col_clr:
        if st.button("🗑️ Clear All", type="secondary", use_container_width=True):
            st.session_state["confirm_clear_all"] = True

if st.session_state.get("confirm_clear_all"):
    st.warning("⚠️ This will permanently delete **all** intervention records.")
    c_yes, c_no, _ = st.columns([1, 1, 4])
    with c_yes:
        if st.button("✅ Confirm", type="primary", use_container_width=True):
            deleted = _clear_all_interventions()
            st.session_state["confirm_clear_all"] = False
            st.toast(f"🗑️ Deleted {deleted} records.")
            _reload_and_rerun()
    with c_no:
        if st.button("❌ Cancel", use_container_width=True):
            st.session_state["confirm_clear_all"] = False
            st.rerun()


# ╭──────────────────────────────────────────────────────────────────────────╮
# │  WORKFLOW TABS — beneath insights                                       │
# ╰──────────────────────────────────────────────────────────────────────────╯
tab_pending, tab_completed, tab_cancelled = st.tabs(
    [
        f"⏳ Pending ({pending_count})",
        f"✅ Completed ({completed_count})",
        f"🚫 Cancelled ({cancelled_count})",
    ]
)

# ═══════════════════════════════════════════════════════════════════════════
#   PENDING TAB
# ═══════════════════════════════════════════════════════════════════════════
with tab_pending:
    pending_df = (
        df_all[status_col.values == "pending"].copy()
        if not df_all.empty
        else pd.DataFrame()
    )
    pending_df = _sort_pending(pending_df)

    if pending_df.empty:
        st.markdown(
            """
            <div style="background:var(--bg-card);border:1px solid var(--border);
                        border-radius:var(--r-md);padding:2rem;text-align:center">
                <div style="font-size:1.8rem;margin-bottom:.5rem">✨</div>
                <div style="font-size:.92rem;color:var(--text-h);font-weight:600;
                            margin-bottom:.2rem">All clear!</div>
                <div style="font-size:.82rem;color:var(--text-muted);line-height:1.5">
                    No pending interventions. Run the Agent Console to generate
                    new recommendations for at-risk customers.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        for row_idx, (_, r) in enumerate(pending_df.iterrows()):
            doc_id  = str(r.get("_id", ""))
            company = _safe(r.get("company_name"))
            score   = float(r.get("risk_score", 0))
            sc      = _score_color(score)
            label   = _safe(r.get("risk_label"))
            urg     = _safe(r.get("urgency"))
            note    = _safe(r.get("note"), "")

            if not doc_id:
                continue

            # AI recommendation history
            ai_pri = _safe(r.get("ai_primary_action"), "")
            ai_sec = _safe(r.get("ai_secondary_action"), "")
            chosen = _safe(r.get("chosen_action"), "")
            has_override = chosen and ai_pri and chosen != ai_pri

            # Expander title: company · score · risk · urgency · action
            exp_title = (
                f"{company}  ·  {score:.0f}  ·  {label}  ·  "
                f"{urg}  ·  {_safe(r.get('primary_action'))}"
            )

            with st.expander(exp_title, expanded=False):
                # ── Summary row ─────────────────────────────────────────
                st.markdown(
                    f"""
                    <div style="display:flex;flex-wrap:wrap;gap:.8rem;align-items:center;margin-bottom:.6rem">
                        <span style="font-size:1.05rem;font-weight:600;color:var(--text-h)">{company}</span>
                        <span class="sc" style="color:{sc}">{score:.1f}</span>
                        {_risk_badge(label)}
                        {_urgency_badge(urg)}
                        {_tier_badge(_safe(r.get('tier')))}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # ── Details grid ────────────────────────────────────────
                d1, d2 = st.columns(2)
                with d1:
                    st.markdown(
                        f"""
                        <div style="font-size:.7rem;color:var(--text-muted);text-transform:uppercase;
                                    letter-spacing:.06em;font-family:'JetBrains Mono',monospace;margin-bottom:2px">
                            Primary Action</div>
                        <div style="font-size:.92rem;font-weight:600;color:var(--cyan);margin-bottom:.5rem">
                            {_safe(r.get('primary_action'))}</div>
                        <div style="font-size:.7rem;color:var(--text-muted);text-transform:uppercase;
                                    letter-spacing:.06em;font-family:'JetBrains Mono',monospace;margin-bottom:2px">
                            Secondary Action</div>
                        <div style="font-size:.88rem;color:var(--text-p);margin-bottom:.5rem">
                            {_safe(r.get('secondary_action'))}</div>
                        """,
                        unsafe_allow_html=True,
                    )
                with d2:
                    st.markdown(
                        f"""
                        <div style="font-size:.7rem;color:var(--text-muted);text-transform:uppercase;
                                    letter-spacing:.06em;font-family:'JetBrains Mono',monospace;margin-bottom:2px">
                            Follow-up Date</div>
                        <div style="font-size:.88rem;color:var(--text-p);font-family:'JetBrains Mono',monospace;
                                    margin-bottom:.5rem">{_safe(r.get('follow_up_date'))}</div>
                        <div style="font-size:.7rem;color:var(--text-muted);text-transform:uppercase;
                                    letter-spacing:.06em;font-family:'JetBrains Mono',monospace;margin-bottom:2px">
                            Model</div>
                        <div style="margin-bottom:.5rem">{_model_tag(r.get('model_used'))}</div>
                        """,
                        unsafe_allow_html=True,
                    )

                # ── AI Recommendation History ───────────────────────────
                if ai_pri:
                    override_html = ""
                    if has_override:
                        override_html = (
                            f'<div style="font-size:.78rem;color:var(--amber);margin-top:.3rem">'
                            f'⚠️ User overrode AI recommendation. AI suggested: <strong>{ai_pri}</strong>, '
                            f'User chose: <strong>{chosen}</strong></div>'
                        )
                    else:
                        override_html = (
                            '<div style="font-size:.78rem;color:var(--green);margin-top:.3rem">'
                            '✅ User accepted AI recommendation</div>'
                        )

                    st.markdown(
                        f"""
                        <div style="background:rgba(121,40,202,.06);border:1px solid rgba(121,40,202,.12);
                                    border-radius:var(--r-sm);padding:.6rem .8rem;margin:.4rem 0 .6rem">
                            <div style="font-size:.68rem;color:var(--violet);text-transform:uppercase;
                                        letter-spacing:.06em;font-family:'JetBrains Mono',monospace;
                                        margin-bottom:.3rem">AI Recommendation History</div>
                            <div style="font-size:.82rem;color:var(--text-p)">
                                AI Primary: <strong style="color:var(--text-h)">{ai_pri}</strong>
                                &nbsp;·&nbsp;
                                AI Secondary: <strong style="color:var(--text-h)">{ai_sec if ai_sec != '—' else 'N/A'}</strong>
                            </div>
                            {override_html}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                # ── Note display ────────────────────────────────────────
                if note:
                    st.markdown(
                        f'<div style="font-size:.82rem;color:var(--text-p);font-style:italic;'
                        f'margin-bottom:.5rem;padding:.4rem .6rem;border-left:2px solid var(--cyan);'
                        f'background:rgba(0,223,216,.04)">📝 {note}</div>',
                        unsafe_allow_html=True,
                    )

                # ── Edit fields ─────────────────────────────────────────
                e1, e2 = st.columns(2)
                with e1:
                    new_primary = st.selectbox(
                        "Primary Action",
                        AVAILABLE_ACTIONS,
                        index=(
                            AVAILABLE_ACTIONS.index(r.get("primary_action"))
                            if r.get("primary_action") in AVAILABLE_ACTIONS
                            else 0
                        ),
                        key=f"ep_{row_idx}",
                    )
                with e2:
                    new_urgency = st.selectbox(
                        "Urgency",
                        URGENCY_OPTIONS,
                        index=(
                            URGENCY_OPTIONS.index(r.get("urgency").strip().title())
                            if isinstance(r.get("urgency"), str)
                            and r.get("urgency").strip().title() in URGENCY_OPTIONS
                            else 0
                        ),
                        key=f"eu_{row_idx}",
                    )

                new_note = st.text_input(
                    "Add / Edit Note",
                    value=note,
                    key=f"en_{row_idx}",
                    placeholder="Optional note...",
                )

                # ── Action buttons ──────────────────────────────────────
                b1, b2, b3, b4 = st.columns(4)

                with b1:
                    if st.button("💾 Save", key=f"sv_{row_idx}", use_container_width=True):
                        updates = {
                            "primary_action": new_primary,
                            "urgency": new_urgency,
                            "note": new_note.strip() if new_note.strip() else None,
                        }
                        if _update_intervention(doc_id, updates):
                            st.toast(f"✅ Updated **{company}**")
                            _reload_and_rerun()
                        else:
                            st.error("Failed to save.")

                with b2:
                    if st.button("✅ Complete", key=f"cm_{row_idx}", use_container_width=True):
                        updates = {
                            "status": "completed",
                            "completed_at": _now_utc(),
                            "note": new_note.strip() if new_note.strip() else r.get("note"),
                        }
                        if _update_intervention(doc_id, updates):
                            st.toast(f"✅ Marked **{company}** as completed")
                            _reload_and_rerun()

                with b3:
                    if st.button("🚫 Cancel", key=f"cn_{row_idx}", use_container_width=True):
                        updates = {
                            "status": "cancelled",
                            "note": new_note.strip() if new_note.strip() else r.get("note"),
                        }
                        if _update_intervention(doc_id, updates):
                            st.toast(f"🚫 Cancelled **{company}**")
                            _reload_and_rerun()

                with b4:
                    if st.button("🗑️ Delete", key=f"dl_{row_idx}", type="secondary", use_container_width=True):
                        if _delete_intervention(doc_id):
                            st.toast(f"🗑️ Deleted **{company}**")
                            _reload_and_rerun()

        # ── Outreach messages ───────────────────────────────────────────
        st.markdown(
            '<div class="sec-title" style="margin-top:1.2rem">📨 Outreach Messages</div>',
            unsafe_allow_html=True,
        )
        for oi, (_, r) in enumerate(pending_df.iterrows()):
            company = _safe(r.get("company_name"))
            message = _safe(r.get("outreach_message"), "No message generated.")
            risk_lbl = _safe(r.get("risk_label"))
            with st.expander(f"{company}  ·  {risk_lbl}", expanded=False):
                st.markdown(
                    f'<div style="font-size:.88rem;color:var(--text-p);line-height:1.7;'
                    f'padding:0.5rem 0">{message}</div>',
                    unsafe_allow_html=True,
                )


# ═══════════════════════════════════════════════════════════════════════════
#   COMPLETED TAB
# ═══════════════════════════════════════════════════════════════════════════
with tab_completed:
    completed_df = (
        df_all[status_col.values == "completed"].copy()
        if not df_all.empty
        else pd.DataFrame()
    )
    completed_df = _sort_newest(completed_df)

    if completed_df.empty:
        st.markdown(
            """
            <div style="background:var(--bg-card);border:1px solid var(--border);
                        border-radius:var(--r-md);padding:2rem;text-align:center">
                <div style="font-size:1.8rem;margin-bottom:.5rem">📋</div>
                <div style="font-size:.92rem;color:var(--text-h);font-weight:600;
                            margin-bottom:.2rem">No completed interventions yet</div>
                <div style="font-size:.82rem;color:var(--text-muted);line-height:1.5">
                    When you mark pending interventions as completed, they will appear here
                    as part of your retention action history.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        for row_idx, (_, r) in enumerate(completed_df.iterrows()):
            doc_id  = str(r.get("_id", ""))
            company = _safe(r.get("company_name"))
            score   = float(r.get("risk_score", 0))
            sc      = _score_color(score)
            note    = _safe(r.get("note"), "")
            if not doc_id:
                continue

            exp_title = (
                f"{company}  ·  {_safe(r.get('primary_action'))}  ·  "
                f"Completed {_safe(r.get('completed_at'), 'N/A')[:10]}"
            )

            with st.expander(exp_title, expanded=False):
                st.markdown(
                    f"""
                    <div style="display:flex;flex-wrap:wrap;gap:.8rem;align-items:center;margin-bottom:.4rem">
                        <span style="font-size:1.05rem;font-weight:600;color:var(--text-h)">{company}</span>
                        <span class="sc" style="color:{sc}">{score:.1f}</span>
                        {_risk_badge(_safe(r.get('risk_label')))}
                        {_urgency_badge(_safe(r.get('urgency')))}
                    </div>
                    <div style="font-size:.82rem;color:var(--text-p);margin:.3rem 0">
                        <strong>Action:</strong> {_safe(r.get('primary_action'))}
                        &nbsp;·&nbsp;
                        <strong>Model:</strong> {_safe(r.get('model_used'))}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if note:
                    st.markdown(
                        f'<div style="font-size:.82rem;color:var(--text-p);font-style:italic;'
                        f'margin:.3rem 0 .5rem;padding:.4rem .6rem;border-left:2px solid var(--green);'
                        f'background:rgba(80,227,194,.04)">📝 {note}</div>',
                        unsafe_allow_html=True,
                    )

                if st.button("🔄 Reopen as Pending", key=f"reopen_c_{row_idx}", use_container_width=False):
                    if _update_intervention(doc_id, {"status": "pending", "completed_at": None}):
                        st.toast(f"🔄 Reopened **{company}** as Pending")
                        _reload_and_rerun()


# ═══════════════════════════════════════════════════════════════════════════
#   CANCELLED TAB
# ═══════════════════════════════════════════════════════════════════════════
with tab_cancelled:
    cancelled_df = (
        df_all[status_col.values == "cancelled"].copy()
        if not df_all.empty
        else pd.DataFrame()
    )
    cancelled_df = _sort_newest(cancelled_df)

    if cancelled_df.empty:
        st.markdown(
            """
            <div style="background:var(--bg-card);border:1px solid var(--border);
                        border-radius:var(--r-md);padding:2rem;text-align:center">
                <div style="font-size:1.8rem;margin-bottom:.5rem">✅</div>
                <div style="font-size:.92rem;color:var(--text-h);font-weight:600;
                            margin-bottom:.2rem">No cancelled interventions</div>
                <div style="font-size:.82rem;color:var(--text-muted);line-height:1.5">
                    Cancelled interventions are preserved here for audit purposes.
                    You can reopen them if needed.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        for row_idx, (_, r) in enumerate(cancelled_df.iterrows()):
            doc_id  = str(r.get("_id", ""))
            company = _safe(r.get("company_name"))
            score   = float(r.get("risk_score", 0))
            sc      = _score_color(score)
            note    = _safe(r.get("note"), "")
            if not doc_id:
                continue

            exp_title = f"{company}  ·  {_safe(r.get('primary_action'))}"

            with st.expander(exp_title, expanded=False):
                st.markdown(
                    f"""
                    <div style="display:flex;flex-wrap:wrap;gap:.8rem;align-items:center;margin-bottom:.4rem">
                        <span style="font-size:1.05rem;font-weight:600;color:var(--text-h)">{company}</span>
                        <span class="sc" style="color:{sc}">{score:.1f}</span>
                        {_risk_badge(_safe(r.get('risk_label')))}
                        {_urgency_badge(_safe(r.get('urgency')))}
                    </div>
                    <div style="font-size:.82rem;color:var(--text-p);margin:.3rem 0">
                        <strong>Action:</strong> {_safe(r.get('primary_action'))}
                        &nbsp;·&nbsp;
                        <strong>Model:</strong> {_safe(r.get('model_used'))}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if note:
                    st.markdown(
                        f'<div style="font-size:.82rem;color:var(--text-p);font-style:italic;'
                        f'margin:.3rem 0 .5rem;padding:.4rem .6rem;border-left:2px solid var(--text-muted);'
                        f'background:rgba(85,85,85,.04)">📝 {note}</div>',
                        unsafe_allow_html=True,
                    )

                if st.button("🔄 Reopen as Pending", key=f"reopen_x_{row_idx}", use_container_width=False):
                    if _update_intervention(doc_id, {"status": "pending"}):
                        st.toast(f"🔄 Reopened **{company}** as Pending")
                        _reload_and_rerun()


