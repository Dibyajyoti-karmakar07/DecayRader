"""
dashboard/app.py
────────────────
Entry-point for the DecayRader Streamlit dashboard.

    streamlit run dashboard/app.py
"""

import streamlit as st
# pyrefly: ignore [missing-import]
from utils.db import check_connection, get_db_stats

# ╭──────────────────────────────────────────────────────────────────────────╮
# │  PAGE CONFIG                                                            │
# ╰──────────────────────────────────────────────────────────────────────────╯
st.set_page_config(
    page_title="DecayRader",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ╭──────────────────────────────────────────────────────────────────────────╮
# │  DARK THEME CSS                                                         │
# ╰──────────────────────────────────────────────────────────────────────────╯
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    :root {
        --bg-primary:     #0a0a0a;
        --bg-surface:     #111111;
        --bg-card:        #161616;
        --border:         #1e1e1e;
        --border-hover:   #2a2a2a;
        --text-h:         #ededed;
        --text-p:         #a1a1a1;
        --text-muted:     #555555;
        --cyan:           #00dfd8;
        --blue:           #007cf0;
        --violet:         #7928ca;
        --pink:           #ff0080;
        --amber:          #f9cb28;
        --red:            #ff4d6a;
        --gradient:       linear-gradient(135deg, #007cf0, #00dfd8, #7928ca, #ff0080);
        --r-sm:           6px;
        --r-md:           10px;
        --r-lg:           14px;
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
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown li,
    section[data-testid="stSidebar"] .stMarkdown span {
        color: var(--text-p) !important;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
    }
    h1, h2, h3 {
        font-family: 'Inter', system-ui, sans-serif !important;
        color: var(--text-h) !important;
        letter-spacing: -0.03em;
    }

    /* ── brand ──────────────────────────────────────────────────────── */
    .brand-logo {
        font-size: 1.5rem; font-weight: 700; letter-spacing: -0.04em;
        color: var(--text-h) !important; margin-bottom: 2px;
    }
    .brand-logo .accent {
        background: var(--gradient);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .brand-tag {
        font-size: 0.72rem; color: var(--text-muted) !important;
        letter-spacing: 0.02em; margin-bottom: 1rem;
    }

    /* ── status badge ───────────────────────────────────────────────── */
    .badge {
        display: inline-flex; align-items: center; gap: 8px;
        padding: 5px 14px; border-radius: 100px;
        font-size: 0.78rem; font-weight: 500;
        font-family: 'JetBrains Mono', monospace;
    }
    .badge-ok {
        background: rgba(0,223,216,.08); border: 1px solid rgba(0,223,216,.2);
        color: var(--cyan);
    }
    .badge-err {
        background: rgba(255,77,106,.08); border: 1px solid rgba(255,77,106,.2);
        color: var(--red);
    }
    .dot {
        width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
    }
    .dot-g { background: var(--cyan); box-shadow: 0 0 6px rgba(0,223,216,.5); }
    .dot-r { background: var(--red);  box-shadow: 0 0 6px rgba(255,77,106,.5); }

    /* ── sidebar nav ────────────────────────────────────────────────── */
    .nav-head {
        font-size: 0.68rem; font-weight: 600; text-transform: uppercase;
        letter-spacing: 0.08em; color: var(--text-muted) !important;
        margin: 1.4rem 0 0.45rem; font-family: 'JetBrains Mono', monospace !important;
    }
    .nav-row {
        display: flex; align-items: center; gap: 10px;
        padding: 7px 12px; border-radius: var(--r-sm);
        font-size: 0.86rem; color: var(--text-p) !important;
        transition: background .15s; margin-bottom: 1px;
    }
    .nav-row:hover { background: rgba(255,255,255,.04); color: var(--text-h) !important; }
    .nav-ico { font-size: 1rem; width: 22px; text-align: center; flex-shrink: 0; }

    .sb-hr { border: none; border-top: 1px solid var(--border); margin: 1rem 0; }

    /* ── welcome card ───────────────────────────────────────────────── */
    .welcome {
        background: var(--bg-card); border: 1px solid var(--border);
        border-radius: var(--r-lg); padding: 2.4rem 2.6rem;
        position: relative; overflow: hidden; margin-bottom: 1.5rem;
    }
    .welcome::before {
        content: ''; position: absolute; top: 0; left: 0; right: 0;
        height: 3px; background: var(--gradient);
    }
    .welcome h2 { font-size: 1.6rem; font-weight: 600; margin-bottom: .5rem; }
    .welcome p  { color: var(--text-p) !important; font-size: 1rem; line-height: 1.75; }

    /* ── stat cards row ─────────────────────────────────────────────── */
    .stat-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 1rem; margin-top: 1rem;
    }
    .stat-card {
        background: var(--bg-surface); border: 1px solid var(--border);
        border-radius: var(--r-md); padding: 1.25rem 1.4rem;
        transition: border-color .2s, transform .15s;
    }
    .stat-card:hover { border-color: var(--border-hover); transform: translateY(-2px); }
    .stat-val {
        font-size: 1.65rem; font-weight: 700; letter-spacing: -0.03em;
    }
    .stat-lbl {
        font-size: 0.74rem; color: var(--text-muted);
        margin-top: 4px; font-family: 'JetBrains Mono', monospace;
    }

    /* ── db summary table ───────────────────────────────────────────── */
    .db-table {
        width: 100%; border-collapse: collapse; margin-top: .75rem;
        font-family: 'JetBrains Mono', monospace; font-size: 0.82rem;
    }
    .db-table th {
        text-align: left; padding: 8px 12px; color: var(--text-muted);
        border-bottom: 1px solid var(--border); font-weight: 500;
        text-transform: uppercase; font-size: 0.7rem; letter-spacing: 0.06em;
    }
    .db-table td {
        padding: 8px 12px; color: var(--text-p);
        border-bottom: 1px solid #1a1a1a;
    }
    .db-table tr:last-child td { border-bottom: none; }

    /* ── hide chrome ────────────────────────────────────────────────── */
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    header[data-testid="stHeader"] {background: transparent !important;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ╭──────────────────────────────────────────────────────────────────────────╮
# │  SIDEBAR                                                                │
# ╰──────────────────────────────────────────────────────────────────────────╯
with st.sidebar:
    st.markdown(
        '<div class="brand-logo">Decay<span class="accent">Rader</span> 📡</div>'
        '<div class="brand-tag">Customer Decay Intelligence</div>',
        unsafe_allow_html=True,
    )

    is_connected = check_connection()
    if is_connected:
        st.markdown(
            '<div class="badge badge-ok"><span class="dot dot-g"></span>MongoDB Connected</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="badge badge-err"><span class="dot dot-r"></span>MongoDB Offline</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<hr class="sb-hr">', unsafe_allow_html=True)
    st.markdown('<div class="nav-head">Navigation</div>', unsafe_allow_html=True)

    for ico, name in [
        ("📊", "Overview"),
        ("🎯", "Risk Ranking"),
        ("👤", "Customer Detail"),
        ("⏳", "Time Machine"),
        ("🤖", "Agent Actions"),
    ]:
        st.markdown(
            f'<div class="nav-row"><span class="nav-ico">{ico}</span>{name}</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<hr class="sb-hr">', unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:.7rem;color:#444;font-family:\'JetBrains Mono\',monospace">'
        "v0.1.0-alpha · DecayRader</div>",
        unsafe_allow_html=True,
    )

# ╭──────────────────────────────────────────────────────────────────────────╮
# │  MAIN — Welcome                                                         │
# ╰──────────────────────────────────────────────────────────────────────────╯
st.markdown(
    """
    <div class="welcome">
        <h2>Welcome to DecayRader 📡</h2>
        <p>
            <strong style="color:#ededed">DecayRader</strong> is an AI-powered
            customer-decay intelligence platform that detects early signs of
            customer disengagement before traditional churn models sound the alarm.
        </p>
        <p>
            The system ingests transactional data from MongoDB, engineers
            behavioural features — purchase-gap drift, AOV shifts, and category-diversity
            changes — then runs an <strong style="color:#ededed">Isolation Forest</strong>
            anomaly-detection model fused with rule-based business scoring to
            produce a unified <strong style="color:#ededed">0–100 risk score</strong>
            for every customer.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ╭──────────────────────────────────────────────────────────────────────────╮
# │  SYSTEM STATUS CARDS                                                    │
# ╰──────────────────────────────────────────────────────────────────────────╯
st.markdown("### System Status")

db_stats = get_db_stats() if is_connected else None

if db_stats:
    cards_html = f"""
    <div class="stat-grid">
        <div class="stat-card">
            <div class="stat-val" style="color:var(--cyan)">●&nbsp;Online</div>
            <div class="stat-lbl">MongoDB Cluster</div>
        </div>
        <div class="stat-card">
            <div class="stat-val" style="color:var(--blue)">{db_stats['collection_count']}</div>
            <div class="stat-lbl">Collections</div>
        </div>
        <div class="stat-card">
            <div class="stat-val" style="color:var(--violet)">{db_stats['total_documents']:,}</div>
            <div class="stat-lbl">Total Documents</div>
        </div>
        <div class="stat-card">
            <div class="stat-val" style="color:var(--amber)">{db_stats['data_size_mb']}&nbsp;MB</div>
            <div class="stat-lbl">Data Size</div>
        </div>
        <div class="stat-card">
            <div class="stat-val" style="color:var(--pink)">{db_stats['storage_size_mb']}&nbsp;MB</div>
            <div class="stat-lbl">Storage Size</div>
        </div>
    </div>
    """
    st.markdown(cards_html, unsafe_allow_html=True)
else:
    cards_html = """
    <div class="stat-grid">
        <div class="stat-card">
            <div class="stat-val" style="color:var(--red)">●&nbsp;Offline</div>
            <div class="stat-lbl">MongoDB Cluster</div>
        </div>
        <div class="stat-card">
            <div class="stat-val" style="color:var(--text-muted)">—</div>
            <div class="stat-lbl">Collections</div>
        </div>
        <div class="stat-card">
            <div class="stat-val" style="color:var(--text-muted)">—</div>
            <div class="stat-lbl">Total Documents</div>
        </div>
        <div class="stat-card">
            <div class="stat-val" style="color:var(--text-muted)">—</div>
            <div class="stat-lbl">Data Size</div>
        </div>
        <div class="stat-card">
            <div class="stat-val" style="color:var(--text-muted)">—</div>
            <div class="stat-lbl">Storage Size</div>
        </div>
    </div>
    """
    st.markdown(cards_html, unsafe_allow_html=True)

# ╭──────────────────────────────────────────────────────────────────────────╮
# │  DATABASE STATUS SUMMARY                                                │
# ╰──────────────────────────────────────────────────────────────────────────╯
st.markdown("### Database Summary")

if db_stats and db_stats["collections"]:
    rows = ""
    for col_name in sorted(db_stats["collections"]):
        count = db_stats["document_counts"].get(col_name, 0)
        rows += f"<tr><td>{col_name}</td><td style='text-align:right'>{count:,}</td></tr>"

    st.markdown(
        f"""
        <div style="background:var(--bg-card);border:1px solid var(--border);
                    border-radius:var(--r-md);padding:1.2rem 1.5rem;margin-top:.25rem">
            <table class="db-table">
                <thead>
                    <tr><th>Collection</th><th style="text-align:right">Documents</th></tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )
elif is_connected:
    st.info("Connected to MongoDB but no collections found in the DecayRader database.")
else:
    st.warning("Cannot retrieve database summary — MongoDB is unreachable.")
