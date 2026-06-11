"""
dashboard/app.py
────────────────
Entry-point for the DecayRader Streamlit dashboard.

    streamlit run dashboard/app.py
"""

import os
import sys
import streamlit as st
from utils.db import check_connection

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

st.set_page_config(
    page_title="DecayRader",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

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
        --green:          #50e3c2;
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

    .sb-hr { border: none; border-top: 1px solid var(--border); margin: 1rem 0; }

    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    header[data-testid="stHeader"] {background: transparent !important;}
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown(
        '<div class="brand-logo">Decay<span class="accent">Rader</span> 📡</div>'
        '<div class="brand-tag">AI-Powered Customer Decay Intelligence</div>',
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

    st.markdown(
        '<div style="font-size:.75rem;color:#444;margin-top:.6rem;line-height:1.5">'
        'Detect revenue decay before it becomes visible in traditional KPIs. '
        'Powered by behavioral signal analysis and Gemini AI.</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<hr class="sb-hr">', unsafe_allow_html=True)

overview = st.Page("pages/01_overview.py", title="Overview", icon="🏠")
risk_ranking = st.Page("pages/02_risk_ranking.py", title="Risk Ranking", icon="📊")
customer_detail = st.Page("pages/03_customer_detail.py", title="Customer Detail", icon="👤")
time_machine = st.Page("pages/04_time_machine.py", title="Time Machine", icon="⏳")
agent_console = st.Page("pages/agent_console.py", title="Agent Console", icon="🤖", default=True)
agent_actions = st.Page("pages/05_agent_actions.py", title="Action Tracker", icon="📋")

pg = st.navigation(
    {
        "🤖 AGENT": [agent_console],
        "📊 INTELLIGENCE": [overview, risk_ranking, customer_detail, time_machine, agent_actions],
    },
    position="sidebar",
)
pg.run()

with st.sidebar:
    st.markdown('<hr class="sb-hr">', unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:.7rem;color:#444;font-family:\'JetBrains Mono\',monospace">'
        "v1.0.0 · DecayRader · Hackathon Demo</div>",
        unsafe_allow_html=True,
    )
