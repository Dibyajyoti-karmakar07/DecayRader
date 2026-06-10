"""
dashboard/pages/agent_console.py
────────────────────────────────
Agent Console — UI layer only.
Processing runs in a background daemon thread (agent_worker.py).
This page only reads shared state and renders progress.
Processing survives page navigation.
"""

from __future__ import annotations

import streamlit as st
from utils.db import connect_to_mongo

AVAILABLE_ACTIONS = [
    "Email Customer",
    "Phone Call",
    "Video Meeting",
    "In-Person Visit",
    "CRM Follow-Up",
    "Notify Team",
]

PROCESSING_STEPS = [
    "Customer profile loaded",
    "Risk signals loaded",
    "Gemini prompt generated",
    "Gemini API called",
    "Parsing response",
    "Ready for review",
]


def _score_color(s: float) -> str:
    if s >= 76:
        return "#ff4d6a"
    if s >= 51:
        return "#f9cb28"
    if s >= 31:
        return "#007cf0"
    return "#50e3c2"


def _risk_badge(label: str) -> str:
    cls = {
        "Critical": "rl-critical",
        "At Risk": "rl-atrisk",
        "Watch": "rl-watch",
        "Healthy": "rl-healthy",
    }.get(str(label), "")
    return f'<span class="rl {cls}">{label}</span>'


# ╭──────────────────────────────────────────────────────────────────────────╮
# │  WORKER STATE ACCESS                                                    │
# ╰──────────────────────────────────────────────────────────────────────────╯

def _get_worker_state() -> dict | None:
    """Get the shared worker state dict from session_state."""
    return st.session_state.get("worker_state")


def _is_worker_alive() -> bool:
    """Check if the background worker thread is still running."""
    ws = _get_worker_state()
    if ws is None:
        return False
    t = ws.get("_thread")
    return t is not None and t.is_alive()


def _is_worker_active() -> bool:
    """True if a worker exists and hasn't finished."""
    ws = _get_worker_state()
    if ws is None:
        return False
    return ws.get("running", False) or ws.get("phase") == "waiting_review"


# ╭──────────────────────────────────────────────────────────────────────────╮
# │  START / STOP                                                           │
# ╰──────────────────────────────────────────────────────────────────────────╯

def start_agent():
    from agent.agent_runner import load_data, get_risky_customers
    from utils.agent_worker import create_worker_state, start_worker

    db = connect_to_mongo()
    combined = load_data(db)
    risky = get_risky_customers(combined)

    if risky.empty:
        st.markdown(
            """
            <div style="background:var(--bg-card);border:1px solid var(--border);
                        border-radius:var(--r-md);padding:2rem;text-align:center;margin:1rem 0">
                <div style="font-size:1.8rem;margin-bottom:.5rem">✅</div>
                <div style="font-size:.95rem;color:var(--text-h);font-weight:600;
                            margin-bottom:.2rem">All customers are healthy</div>
                <div style="font-size:.82rem;color:var(--text-muted);line-height:1.5">
                    No customers with a risk score above 50 were found.
                    DecayRader is actively monitoring — check back later.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.stop()

    customers = [r.to_dict() for _, r in risky.iterrows()]

    try:
        from agent.gemini_client import setup_gemini_client
        gemini_client = setup_gemini_client()
    except SystemExit:
        st.error("GEMINI_API_KEY not found. Add it to a .env file in the project root.")
        st.stop()

    # Create shared state and start the background thread
    state = create_worker_state(customers, len(customers))
    st.session_state.worker_state = state
    st.session_state.worker_db = db
    st.session_state.worker_gemini = gemini_client

    start_worker(state, gemini_client, db)
    st.rerun()


def stop_agent():
    from utils.agent_worker import stop_worker
    ws = _get_worker_state()
    if ws:
        stop_worker(ws)
        ws["logs"].append("🛑 Agent stopped by user.")


def approve_action(action: str | None):
    from utils.agent_worker import approve_current
    ws = _get_worker_state()
    db = st.session_state.get("worker_db")
    if ws and db:
        approve_current(ws, action, db)


# ╭──────────────────────────────────────────────────────────────────────────╮
# │  RENDER HELPERS                                                         │
# ╰──────────────────────────────────────────────────────────────────────────╯

def render_customer_card(customer: dict, result: dict, dimmed: bool = False):
    cid = customer.get("customer_id")
    name = customer.get("company_name")
    score = float(customer.get("risk_score", 0))
    label = str(customer.get("risk_label", ""))
    sc = _score_color(score)
    dim_style = (
        "opacity:0.35;filter:blur(1.2px);pointer-events:none;user-select:none"
        if dimmed
        else ""
    )
    dim_label = (
        '<div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);'
        'z-index:10;font-size:.82rem;color:var(--text-muted);'
        'font-family:JetBrains Mono,monospace;letter-spacing:.04em;'
        'background:rgba(10,10,10,.7);padding:6px 16px;border-radius:100px">'
        'PREVIOUS ANALYSIS</div>'
        if dimmed
        else ""
    )

    st.html(
        f"""
        <div style="position:relative;transition:opacity .4s,filter .4s;{dim_style}">
            {dim_label}
            <div style="background:var(--bg-card);border:1px solid var(--border);
                        border-radius:var(--r-md);padding:1.3rem 1.5rem;
                        margin-bottom:1rem;position:relative;overflow:hidden">
                <div style="position:absolute;top:0;left:0;width:3px;height:100%;
                            background:{sc}"></div>
                <div style="display:flex;align-items:center;gap:1rem;flex-wrap:wrap;
                            margin-bottom:.6rem">
                    <span style="font-size:1.15rem;font-weight:600;color:var(--text-h)">
                        {name}</span>
                    <span style="font-size:1.3rem;font-weight:700;color:{sc};
                                font-family:'JetBrains Mono',monospace">
                        {score:.1f}</span>
                    {_risk_badge(label)}
                    <span style="font-size:.78rem;color:var(--text-muted)">{cid}</span>
                </div>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:.8rem;
                            margin-top:.6rem">
                    <div>
                        <div style="font-size:.7rem;color:var(--text-muted);
                                    text-transform:uppercase;letter-spacing:.06em;
                                    font-family:'JetBrains Mono',monospace;margin-bottom:2px">
                            Decay Summary</div>
                        <div style="font-size:.88rem;color:var(--text-p);line-height:1.6">
                            {result.get('decay_summary', 'N/A')}</div>
                    </div>
                    <div>
                        <div style="font-size:.7rem;color:var(--text-muted);
                                    text-transform:uppercase;letter-spacing:.06em;
                                    font-family:'JetBrains Mono',monospace;margin-bottom:2px">
                            Likely Reason</div>
                        <div style="font-size:.88rem;color:var(--text-p);line-height:1.6">
                            {result.get('likely_reason', 'N/A')}</div>
                    </div>
                </div>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:.8rem;
                            margin-top:.8rem">
                    <div>
                        <div style="font-size:.7rem;color:var(--text-muted);
                                    text-transform:uppercase;letter-spacing:.06em;
                                    font-family:'JetBrains Mono',monospace;margin-bottom:2px">
                            Recommended Action</div>
                        <div style="font-size:.95rem;font-weight:600;color:var(--cyan)">
                            {result.get('primary_action', 'N/A')}</div>
                    </div>
                    <div>
                        <div style="font-size:.7rem;color:var(--text-muted);
                                    text-transform:uppercase;letter-spacing:.06em;
                                    font-family:'JetBrains Mono',monospace;margin-bottom:2px">
                            Secondary Action</div>
                        <div style="font-size:.88rem;color:var(--text-p)">
                            {result.get('secondary_action', 'N/A')}</div>
                    </div>
                </div>
                <div style="margin-top:.8rem">
                    <div style="font-size:.7rem;color:var(--text-muted);
                                text-transform:uppercase;letter-spacing:.06em;
                                font-family:'JetBrains Mono',monospace;margin-bottom:2px">
                        Urgency</div>
                    <div style="font-size:.88rem;font-weight:600">{result.get('urgency', 'N/A')}</div>
                </div>
            </div>
        </div>
        """
    )


def render_processing_panel(
    customer_name: str = "",
    current_idx: int = 0,
    total: int = 0,
    step: int = 4,
):
    steps_html = ""
    for i, step_name in enumerate(PROCESSING_STEPS):
        is_last = i == len(PROCESSING_STEPS) - 1
        if i < step:
            row_class = "proc-step step-completed"
            row_opacity = "0.55"
        elif i == step:
            row_class = "proc-step step-active"
            row_opacity = "1.0"
        else:
            row_class = "proc-step step-future"
            row_opacity = "0.35"

        steps_html += f"""
        <div class="{row_class}" data-step="{i}" style="opacity:{row_opacity}">
            <div class="proc-step-col">
                <div class="proc-step-dot">
                    <span class="check-icon">&#10003;</span>
                    <span class="pulse-icon"><span class="step-pulse"></span></span>
                    <span class="circle-icon">&#9675;</span>
                </div>
                {'' if is_last else '<div class="proc-step-line"></div>'}
            </div>
            <div class="proc-step-body" style="padding-bottom:{'0' if is_last else '6px'}">
                <div class="proc-step-label">{step_name}</div>
            </div>
        </div>
        """

    st.html(
        f"""
        <style>
        .proc-panel {{
            max-width:650px; margin:1rem auto 2.5rem; padding:0 1rem;
        }}
        .proc-header {{
            text-align:center; margin-bottom:1.5rem;
        }}
        .proc-badge {{
            display:inline-flex; align-items:center; gap:7px;
            background:rgba(0,223,216,.07); border:1px solid rgba(0,223,216,.14);
            border-radius:100px; padding:3px 14px;
            font-size:.68rem; color:var(--cyan);
            font-family:JetBrains Mono,monospace; letter-spacing:.02em;
            margin-bottom:.65rem; text-transform:uppercase;
        }}
        .proc-badge-dot {{
            display:inline-block; width:7px; height:7px; border-radius:50%;
            background:var(--cyan);
            animation:think-pulse 1.4s ease-in-out infinite;
        }}
        .proc-customer-name {{
            font-size:.9rem; color:var(--text-p); font-weight:400;
        }}
        .proc-counter {{
            font-size:.7rem; color:var(--text-muted); margin-top:.2rem;
            font-family:JetBrains Mono,monospace;
        }}
        .proc-card {{
            background:var(--bg-card); border:1px solid var(--border);
            border-radius:var(--r-md); padding:1.15rem 1.35rem;
        }}
        .proc-step {{
            display:flex; gap:14px; transition:opacity .4s;
        }}
        .proc-step-col {{
            display:flex; flex-direction:column; align-items:center;
            width:28px; flex-shrink:0;
        }}
        .proc-step-dot {{
            width:28px; height:28px; border-radius:50%; display:flex;
            align-items:center; justify-content:center; flex-shrink:0;
            border:1.5px solid; transition:border-color .4s,background .4s;
            font-size:.8rem;
        }}
        .proc-step-line {{
            width:1.5px; flex:1; min-height:22px; margin:5px 0 3px;
            transition:background .4s,opacity .4s;
        }}
        .proc-step-body {{
            flex:1; padding-top:4px;
        }}
        .proc-step-label {{
            font-size:.85rem; letter-spacing:-.01em;
            transition:color .4s,font-weight .4s;
        }}
        .check-icon {{ display:none; color:var(--green); font-weight:600; font-size:.82rem; }}
        .pulse-icon {{ display:none; }}
        .circle-icon {{ color:#2a2a2a; font-size:.72rem; }}
        .step-completed .check-icon {{ display:block !important; }}
        .step-completed .circle-icon {{ display:none !important; }}
        .step-completed .proc-step-dot {{
            background:rgba(80,227,194,.15); border-color:var(--green);
        }}
        .step-completed .proc-step-label {{
            color:var(--text-muted); font-weight:400;
        }}
        .step-completed .proc-step-line {{
            background:var(--green); opacity:0.8;
        }}
        .step-active .pulse-icon {{ display:block !important; }}
        .step-active .circle-icon {{ display:none !important; }}
        .step-active .proc-step-dot {{
            background:transparent; border-color:var(--cyan);
        }}
        .step-active .proc-step-label {{
            color:var(--text-h); font-weight:500;
        }}
        .step-active .proc-step-line {{
            background:var(--cyan); opacity:0.3;
        }}
        .step-future .proc-step-dot {{
            background:transparent; border-color:#2a2a2a;
        }}
        .step-future .proc-step-label {{
            color:#333; font-weight:400;
        }}
        .step-future .proc-step-line {{
            background:#1a1a1a; opacity:0.3;
        }}
        .proc-status {{
            text-align:center; font-size:.78rem; color:var(--text-muted);
            font-family:JetBrains Mono,monospace; margin-top:.65rem;
            padding:2px 0; letter-spacing:.01em;
        }}
        .proc-status-dot {{
            display:inline-block; width:4px; height:4px; border-radius:50%;
            background:var(--text-muted); margin-left:6px;
            animation:st-dot 1s ease-in-out infinite;
        }}
        @keyframes st-dot {{
            0%,100%{{opacity:1}}
            50%{{opacity:.2}}
        }}
        </style>

        <div class="proc-panel">
            <div class="proc-header">
                <div class="proc-badge">
                    <span class="proc-badge-dot"></span>
                    Analyzing
                </div>
                <div class="proc-customer-name">{customer_name}</div>
                <div class="proc-counter">Customer {current_idx + 1} of {total}</div>
            </div>

            <div class="proc-card">
                {steps_html}
            </div>

            <div class="proc-status">
                Analyzing customer signals and generating intervention recommendation...<span class="proc-status-dot"></span>
            </div>
        </div>
        """
    )


# ── Page ──────────────────────────────────────────────────────────────────────

st.markdown(
    """
    <style>
    .rl { display: inline-block; padding: 2px 10px; border-radius: 100px;
          font-size: 0.72rem; font-weight: 500;
          font-family: 'JetBrains Mono', monospace; }
    .rl-critical  { background: rgba(255,77,106,.12); color: #ff4d6a; }
    .rl-atrisk    { background: rgba(249,203,40,.12); color: #f9cb28; }
    .rl-watch     { background: rgba(0,124,240,.12);  color: #007cf0; }
    .rl-healthy   { background: rgba(80,227,194,.12); color: #50e3c2; }

    .thinking-dot {
        display: inline-block; width: 7px; height: 7px; border-radius: 50%;
        background: var(--cyan);
        animation: think-pulse 1.4s ease-in-out infinite;
    }
    @keyframes think-pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.3; transform: scale(0.7); }
    }

    .step-pulse {
        display: inline-block; width: 9px; height: 9px; border-radius: 50%;
        background: var(--cyan);
        animation: step-pulse 1.6s ease-in-out infinite;
    }
    @keyframes step-pulse {
        0%, 100% { box-shadow: 0 0 0 0 rgba(0,223,216,.4); }
        50% { box-shadow: 0 0 0 6px rgba(0,223,216,0); }
    }

    .toast-save {
        max-width:420px; margin:0 auto 1rem;
        background:rgba(80,227,194,.08); border:1px solid rgba(80,227,194,.18);
        border-radius:var(--r-md); padding:1rem 1.25rem;
        transition:opacity .3s,transform .3s;
        position:relative; overflow:hidden;
    }
    .toast-save::after {
        content:''; position:absolute; bottom:0; left:0; height:2px;
        background:var(--green); border-radius:2px;
        animation:toast-shrink 2.2s linear forwards;
    }
    @keyframes toast-shrink {
        from { width:100%; }
        to { width:0%; }
    }

    [data-testid="stStatusWidget"] > div > div:first-child { display: none; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <h1 style="font-size:1.55rem;font-weight:600;margin-bottom:0.1rem">🤖 Agent Console</h1>
    <p style="color:var(--text-muted);font-size:.85rem;margin-top:0">
        Run the DecayRader AI agent on at-risk customers and choose
        interventions — one customer at a time.
    </p>
    """,
    unsafe_allow_html=True,
)

st.markdown("---")


# ╭──────────────────────────────────────────────────────────────────────────╮
# │  READ WORKER STATE                                                      │
# ╰──────────────────────────────────────────────────────────────────────────╯
ws = _get_worker_state()
worker_alive = _is_worker_alive()
worker_active = _is_worker_active()


# ── IDLE STATE ──────────────────────────────────────────────────────────────

if ws is None or (not worker_active and ws.get("finished") is not True):
    st.markdown(
        """
        <div style="background:var(--bg-card);border:1px solid var(--border);
                    border-radius:var(--r-md);padding:1.8rem 2rem;margin-bottom:1.2rem">
            <div style="font-size:.95rem;color:var(--text-h);font-weight:600;
                        margin-bottom:.6rem">How it works</div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:.6rem .8rem">
                <div style="font-size:.82rem;color:var(--text-p);line-height:1.5">
                    <span style="color:var(--cyan);font-weight:600">1.</span>
                    Load at-risk customers from behavioral signals</div>
                <div style="font-size:.82rem;color:var(--text-p);line-height:1.5">
                    <span style="color:var(--cyan);font-weight:600">2.</span>
                    Gemini AI analyzes each customer's decay pattern</div>
                <div style="font-size:.82rem;color:var(--text-p);line-height:1.5">
                    <span style="color:var(--cyan);font-weight:600">3.</span>
                    AI recommends personalized retention interventions</div>
                <div style="font-size:.82rem;color:var(--text-p);line-height:1.5">
                    <span style="color:var(--cyan);font-weight:600">4.</span>
                    You approve, override, or skip each recommendation</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("🚀 Run Agent", type="primary", use_container_width=False):
        start_agent()


# ── RUNNING STATE ───────────────────────────────────────────────────────────

if ws is not None and worker_active:
    # Show toast from background worker
    if ws.get("toast"):
        t = ws["toast"]
        st.toast(
            f"**✅ Intervention Saved** — {t['action']} recorded for **{t['customer_name']}**"
        )
        ws["toast"] = None

    total = ws["total"]
    idx = ws["current_idx"]
    phase = ws["phase"]

    # Show previous customer (dimmed)
    if ws.get("prev_customer") and ws.get("prev_result"):
        render_customer_card(ws["prev_customer"], ws["prev_result"], dimmed=True)

    # Counter
    st.markdown(
        f'<div style="color:var(--text-muted);font-size:.82rem;margin-bottom:.75rem">'
        f"Customer <strong style='color:var(--text-h)'>{idx + 1}</strong>"
        f" of <strong style='color:var(--text-h)'>{total}</strong></div>",
        unsafe_allow_html=True,
    )

    # ── Processing / Calling phase (Gemini is working in the background) ──
    if phase in ("processing", "calling"):
        customer_obj = ws.get("current_customer")
        cname = customer_obj.get("company_name", "") if customer_obj else ""

        render_processing_panel(
            customer_name=cname,
            current_idx=idx,
            total=total,
            step=ws.get("processing_step", 4),
        )

        if st.button("⏹ Stop Agent", key="stop_processing", type="primary"):
            stop_agent()
            st.rerun()

        # Non-blocking auto-refresh: fragment reruns itself every 2s,
        # then triggers a full page rerun to pick up worker state changes.
        @st.fragment(run_every=2)
        def _poll_worker():
            _ws = st.session_state.get("worker_state")
            if _ws and _ws.get("phase") not in ("processing", "calling"):
                st.rerun()
        _poll_worker()

    # ── Waiting for review (Gemini finished, human must decide) ───────────
    elif phase == "waiting_review":
        customer = ws["current_customer"]
        result = ws["gemini_result"]

        if customer and result:
            render_customer_card(customer, result, dimmed=False)

            st.markdown(
                '<div style="font-size:.82rem;font-weight:600;color:var(--text-h);'
                'margin-bottom:.5rem;margin-top:1.2rem">Choose an action:</div>',
                unsafe_allow_html=True,
            )

            col_actions = st.columns(3)
            for i, action in enumerate(AVAILABLE_ACTIONS):
                recommended = result.get("primary_action", "")
                is_rec = action == recommended
                label = f"⭐ {action}" if is_rec else action
                with col_actions[i % 3]:
                    if st.button(label, key=f"act_{i}", use_container_width=True,
                                 type="primary" if is_rec else "secondary"):
                        approve_action(action)
                        st.rerun()

            with col_actions[2]:
                if st.button("⏭️ Skip", key="act_skip", use_container_width=True):
                    approve_action(None)
                    st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("⏹ Stop Agent", type="primary", use_container_width=False):
                stop_agent()
                st.rerun()

        elif idx < total:
            st.markdown(
                '<div style="font-size:.88rem;color:var(--text-muted);font-style:italic">' 
                'Gemini could not generate a result for this customer. '
                'The agent will automatically advance.</div>',
                unsafe_allow_html=True,
            )

    # ── Advance phase (brief transition before next customer) ─────────────
    elif phase == "advance":
        st.markdown(
            '<div style="text-align:center;padding:1rem 0">' 
            '<div style="font-size:.82rem;color:var(--text-muted);'
            'font-family:JetBrains Mono,monospace">' 
            '⏳ Loading next customer…</div></div>',
            unsafe_allow_html=True,
        )

        @st.fragment(run_every=1)
        def _poll_advance():
            _ws = st.session_state.get("worker_state")
            if _ws and _ws.get("phase") != "advance":
                st.rerun()
        _poll_advance()


# ── FINISHED STATE ──────────────────────────────────────────────────────────

if ws is not None and ws.get("finished") and not worker_active:
    st.markdown("---")

    total = ws.get("total", 0)
    saved = ws.get("saved_count", 0)
    skipped = ws.get("skipped_count", 0)
    failed = ws.get("failed_count", 0)
    already = ws.get("already_count", 0)

    if ws.get("stopped"):
        st.markdown(
            '<div style="background:rgba(249,203,40,.06);border:1px solid rgba(249,203,40,.15);'
            'border-radius:var(--r-md);padding:1rem 1.3rem;margin-bottom:1rem">'
            '<div style="font-size:.95rem;font-weight:600;color:var(--amber);margin-bottom:.2rem">'
            '🛑 Agent Run Stopped</div>'
            f'<div style="font-size:.82rem;color:var(--text-p)">'
            f'Processed <strong style="color:var(--text-h)">{saved + skipped + failed}</strong> of '
            f'<strong style="color:var(--text-h)">{total}</strong> customers before stopping.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="background:rgba(80,227,194,.06);border:1px solid rgba(80,227,194,.15);'
            'border-radius:var(--r-md);padding:1rem 1.3rem;margin-bottom:1rem">'
            '<div style="font-size:.95rem;font-weight:600;color:var(--green);margin-bottom:.2rem">'
            '✅ Agent Run Complete</div>'
            f'<div style="font-size:.82rem;color:var(--text-p)">'
            f'Successfully analyzed <strong style="color:var(--text-h)">{total}</strong> at-risk customers. '
            f'<strong style="color:var(--green)">{saved}</strong> interventions saved to database.</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    # Summary cards
    st.markdown(
        f"""
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:.8rem;margin:.8rem 0 1.2rem">
            <div style="background:var(--bg-card);border:1px solid var(--border);
                        border-radius:var(--r-md);padding:1rem 1.2rem;text-align:center">
                <div style="font-size:1.5rem;font-weight:700;color:var(--cyan);line-height:1">{total}</div>
                <div style="font-size:.68rem;color:var(--text-muted);margin-top:4px;
                            font-family:'JetBrains Mono',monospace;text-transform:uppercase;
                            letter-spacing:.06em">Analyzed</div>
            </div>
            <div style="background:var(--bg-card);border:1px solid var(--border);
                        border-radius:var(--r-md);padding:1rem 1.2rem;text-align:center">
                <div style="font-size:1.5rem;font-weight:700;color:var(--green);line-height:1">{saved}</div>
                <div style="font-size:.68rem;color:var(--text-muted);margin-top:4px;
                            font-family:'JetBrains Mono',monospace;text-transform:uppercase;
                            letter-spacing:.06em">Saved</div>
            </div>
            <div style="background:var(--bg-card);border:1px solid var(--border);
                        border-radius:var(--r-md);padding:1rem 1.2rem;text-align:center">
                <div style="font-size:1.5rem;font-weight:700;color:var(--text-muted);line-height:1">{skipped + already}</div>
                <div style="font-size:.68rem;color:var(--text-muted);margin-top:4px;
                            font-family:'JetBrains Mono',monospace;text-transform:uppercase;
                            letter-spacing:.06em">Skipped</div>
            </div>
            <div style="background:var(--bg-card);border:1px solid var(--border);
                        border-radius:var(--r-md);padding:1rem 1.2rem;text-align:center">
                <div style="font-size:1.5rem;font-weight:700;color:{'var(--red)' if failed > 0 else 'var(--text-muted)'};line-height:1">{failed}</div>
                <div style="font-size:.68rem;color:var(--text-muted);margin-top:4px;
                            font-family:'JetBrains Mono',monospace;text-transform:uppercase;
                            letter-spacing:.06em">Failed</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Execution log
    logs = ws.get("logs", [])
    if logs:
        with st.expander(f"📋 Execution Log ({len(logs)} entries)", expanded=True):
            log_html = ""
            for log in logs:
                # Color code log entries
                if log.startswith("✅"):
                    color = "var(--green)"
                elif log.startswith("⚠️") or log.startswith("❌"):
                    color = "var(--red)"
                elif log.startswith("⏭️"):
                    color = "var(--text-muted)"
                elif log.startswith("🛑"):
                    color = "var(--amber)"
                elif log.startswith("💥"):
                    color = "var(--pink)"
                else:
                    color = "var(--text-p)"
                log_html += (
                    f'<div style="font-size:.8rem;color:{color};padding:3px 0;'
                    f'font-family:\'JetBrains Mono\',monospace;line-height:1.5">{log}</div>'
                )
            st.markdown(log_html, unsafe_allow_html=True)
    else:
        st.markdown(
            '<div style="font-size:.82rem;color:var(--text-muted);font-style:italic">' 
            'No log entries recorded.</div>',
            unsafe_allow_html=True,
        )

    # Navigation hint
    st.markdown(
        '<div style="font-size:.8rem;color:var(--text-muted);margin-top:.8rem">'
        '📌 Visit <strong style="color:var(--text-p)">Agent Actions</strong> to manage, '
        'edit, or complete saved interventions.</div>',
        unsafe_allow_html=True,
    )

    if st.button("🔄 New Run", type="primary", use_container_width=False):
        if "worker_state" in st.session_state:
            del st.session_state["worker_state"]
        if "worker_db" in st.session_state:
            del st.session_state["worker_db"]
        if "worker_gemini" in st.session_state:
            del st.session_state["worker_gemini"]
        st.rerun()