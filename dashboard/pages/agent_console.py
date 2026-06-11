"""
dashboard/pages/agent_console.py
────────────────────────────────
AI Intelligence Workspace — Radical Information Hierarchy Redesign.
Tabs:
1. Customer Deep Dive
2. Tier Intelligence
3. Portfolio Intelligence
4. Intervention Agent
"""

import os
import sys

_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import streamlit as st
import pandas as pd
from utils.db import connect_to_mongo
from agent.intelligence_client import (
    generate_customer_intelligence,
    generate_tier_analysis,
    generate_portfolio_analysis
)

# ╭──────────────────────────────────────────────────────────────────────────╮
# │  THEME CSS  (Vercel/Linear Dark Aesthetic)                              │
# ╰──────────────────────────────────────────────────────────────────────────╯
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

    :root {
        --bg-page:      #0a0a0a;
        --bg-surface:   #111111;
        --bg-card:      #171717;
        --border:       #222222;
        --border-hover: #333333;
        --text-h:       #ffffff;
        --text-p:       #a1a1a1;
        --text-muted:   #888888;
        --cyan:         #00dfd8;
        --blue:         #0070f3;
        --amber:        #f5a623;
        --red:          #ee0000;
        --green:        #50e3c2;
    }

    /* Base Typography */
    h1, h2, h3, .text-h {
        font-family: 'Inter', system-ui, sans-serif;
        letter-spacing: -0.03em;
        color: var(--text-h);
    }
    
    .mono { font-family: 'JetBrains Mono', monospace; }

    /* Layout Elements */
    .hero-header {
        margin-bottom: 2rem;
        padding-bottom: 1.5rem;
        border-bottom: 1px solid var(--border);
    }
    .hero-title {
        font-size: 2rem;
        font-weight: 600;
        letter-spacing: -0.04em;
        line-height: 1.2;
        margin-bottom: 0.25rem;
    }
    .hero-subtitle {
        font-size: 0.85rem;
        color: var(--text-muted);
        letter-spacing: 0.02em;
    }

    /* Cards */
    .v-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 1.5rem;
        box-shadow: 0 1px 2px rgba(0,0,0,0.2), 0 4px 12px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .v-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.3), 0 8px 24px rgba(0,0,0,0.2);
    }
    .v-card-hero {
        background: var(--bg-surface);
        border: 1px solid var(--border);
        border-top: 2px solid var(--cyan);
        border-radius: 8px;
        padding: 2rem;
        margin: 1.5rem 0;
        box-shadow: 0 4px 24px rgba(0,0,0,0.2);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .v-card-hero:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 28px rgba(0,0,0,0.3);
    }
    .v-eyebrow {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
        text-transform: uppercase;
        color: var(--text-muted);
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }
    .v-value {
        font-size: 1.5rem;
        font-weight: 600;
        color: var(--text-h);
        line-height: 1.3;
    }
    .v-p {
        font-size: 0.95rem;
        color: var(--text-p);
        line-height: 1.6;
    }

    /* KPIs */
    .kpi-row { display: flex; gap: 2rem; margin-bottom: 2rem; }
    .kpi-block { display: flex; flex-direction: column; }
    .kpi-num { font-family: 'JetBrains Mono', monospace; font-size: 2.5rem; font-weight: 600; color: var(--text-h); line-height: 1; letter-spacing: -0.05em; }
    .kpi-lbl { font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; margin-top: 0.5rem; letter-spacing: 0.05em; }

    /* Badges */
    .badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 999px;
        font-size: 0.7rem;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 500;
        text-transform: uppercase;
        border: 1px solid transparent;
    }
    .badge-red { background: rgba(238,0,0,0.1); color: var(--red); border-color: rgba(238,0,0,0.2); }
    .badge-amber { background: rgba(245,166,35,0.1); color: var(--amber); border-color: rgba(245,166,35,0.2); }
    .badge-green { background: rgba(80,227,194,0.1); color: var(--green); border-color: rgba(80,227,194,0.2); }
    .badge-cyan { background: rgba(0,223,216,0.1); color: var(--cyan); border-color: rgba(0,223,216,0.2); }
    .badge-neutral { background: var(--border); color: var(--text-p); border-color: var(--border-hover); }

    /* Utilities & Animations */
    @keyframes slideUpFade {
        0% { opacity: 0; transform: translateY(6px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    .animate-entrance {
        animation: slideUpFade 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }

    .empty-state {
        color: var(--text-muted);
        font-style: italic;
    }
    
    @keyframes shimmer {
        0% { background-position: -1000px 0; }
        100% { background-position: 1000px 0; }
    }
    .shimmer {
        animation: shimmer 2s infinite linear;
        background: linear-gradient(to right, #222 4%, #333 25%, #222 36%);
        background-size: 1000px 100%;
        border-radius: 4px;
    }

    /* Data Tables */
    .v-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
    .v-table th { text-align: left; padding: 0.75rem 1rem; border-bottom: 1px solid var(--border); color: var(--text-muted); font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; text-transform: uppercase; font-weight: 400; }
    .v-table td { padding: 0.75rem 1rem; border-bottom: 1px solid var(--border); color: var(--text-p); }
    .v-table tr:hover td { background: rgba(255,255,255,0.02); }
    
    /* Copilot Process Steps */
    .proc-step { display:flex; gap:14px; transition:opacity .4s; }
    .proc-step-col { display:flex; flex-direction:column; align-items:center; width:28px; flex-shrink:0; }
    .proc-step-dot { width:28px; height:28px; border-radius:50%; display:flex; align-items:center; justify-content:center; flex-shrink:0; border:1px solid; font-size:.8rem; }
    .proc-step-line { width:1px; flex:1; min-height:22px; margin:5px 0 3px; }
    .proc-step-label { font-size:.85rem; padding-top:4px; }
    
    .step-completed .proc-step-dot { background:rgba(80,227,194,.1); border-color:var(--green); color:var(--green); }
    .step-completed .proc-step-line { background:var(--green); opacity:0.5; }
    .step-completed .proc-step-label { color:var(--text-muted); }
    
    .step-active .proc-step-dot { background:transparent; border-color:var(--cyan); }
    .step-active .proc-step-line { background:var(--cyan); opacity:0.3; }
    .step-active .proc-step-label { color:var(--text-h); font-weight:500; }
    
    .step-future .proc-step-dot { background:transparent; border-color:var(--border); color:transparent; }
    .step-future .proc-step-line { background:var(--border); }
    .step-future .proc-step-label { color:var(--text-muted); }

    .pulse { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: var(--cyan); box-shadow: 0 0 0 0 rgba(0,223,216,.4); animation: pulse 2s infinite; }
    @keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(0,223,216,.4); } 70% { box-shadow: 0 0 0 6px rgba(0,223,216,0); } 100% { box-shadow: 0 0 0 0 rgba(0,223,216,0); } }

    /* Shimmer Skeleton */
    .shimmer {
        background: #1e1e1e;
        background-image: linear-gradient(to right, #1e1e1e 0%, #2a2a2a 20%, #1e1e1e 40%, #1e1e1e 100%);
        background-repeat: no-repeat;
        background-size: 800px 100%; 
        animation-duration: 1.5s;
        animation-fill-mode: forwards; 
        animation-iteration-count: infinite;
        animation-name: placeholderShimmer;
        animation-timing-function: linear;
        border-radius: 4px;
    }
    @keyframes placeholderShimmer {
        0% { background-position: -468px 0; }
        100% { background-position: 468px 0; }
    }
    
    /* Hide Streamlit Global Spinner to prevent loading state leaking across tabs */
    [data-testid="stStatusWidget"] {
        display: none !important;
        visibility: hidden !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("Intelligence Workspace")

# ╭──────────────────────────────────────────────────────────────────────────╮
# │  DATA LOADING                                                           │
# ╰──────────────────────────────────────────────────────────────────────────╯
@st.cache_data(ttl=120)
def load_intelligence_data():
    db = connect_to_mongo()
    cust_df = pd.DataFrame(list(db["Customers"].find({}, {"_id": 0})))
    risk_df = pd.DataFrame(list(db["risk_scores"].find({}, {"_id": 0})))
    intv_df = pd.DataFrame(list(db["interventions"].find({}, {"_id": 0})))
    
    if cust_df.empty or risk_df.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        
    merged = pd.merge(cust_df, risk_df, on="customer_id", how="left")
    risky = merged[merged["risk_score"] > 50].copy()
    risky.sort_values("risk_score", ascending=False, inplace=True)
    return cust_df, risk_df, intv_df, merged

cust_df, risk_df, intv_df, merged_df = load_intelligence_data()

# ╭──────────────────────────────────────────────────────────────────────────╮
# │  TABS DEFINITION                                                        │
# ╰──────────────────────────────────────────────────────────────────────────╯
tab1, tab2, tab3, tab4 = st.tabs([
    "Customer Deep Dive", 
    "Tier Intelligence", 
    "Portfolio Intelligence", 
    "🤖 Intervention Agent"
])

def _badge_html(score: float) -> str:
    if score >= 76: return '<span class="badge badge-red">Critical</span>'
    if score >= 51: return '<span class="badge badge-amber">At Risk</span>'
    if score >= 31: return '<span class="badge badge-cyan">Watch</span>'
    return '<span class="badge badge-green">Healthy</span>'

# ==============================================================================
# TAB 1: CUSTOMER DEEP DIVE
# ==============================================================================
with tab1:
    if merged_df.empty:
        st.warning("No customer data available.")
    else:
        st.markdown("<div class='v-eyebrow' style='margin-bottom:0.5rem;'>Search Directory</div>", unsafe_allow_html=True)
        search_query = st.text_input("Search Customer", placeholder="Type company name...", label_visibility="collapsed")
        
        cust_list = merged_df.sort_values("risk_score", ascending=False)
        if search_query:
            cust_list = cust_list[cust_list["company_name"].str.contains(search_query, case=False, na=False)]
            
        if cust_list.empty:
            st.info("No customers match your search.")
        else:
            options = [f"{r['company_name']} (Risk: {r.get('risk_score',0):.1f})" for _, r in cust_list.iterrows()]
            selected_opt = st.selectbox("Select Customer", options, label_visibility="collapsed")
            
            if selected_opt:
                idx = options.index(selected_opt)
                row = cust_list.iloc[idx]
                cid = row["customer_id"]
                
                # Check for cached timestamp
                ts_key = f"ts_deep_dive_{cid}"
                
                # Hero Header
                st.markdown(
                    f"""
                    <div class="hero-header" style="display:flex; justify-content:space-between; align-items:flex-end;">
                        <div>
                            <div class="hero-title">{row['company_name']}</div>
                            <div class="hero-subtitle mono">{cid} • {row['tier']} Tier • {row['city']}</div>
                        </div>
                        <div style="text-align:right;">
                            <div class="mono" style="font-size:2.5rem; font-weight:600; line-height:1; color:var(--text-h);">{row.get('risk_score',0):.1f}</div>
                            <div style="margin-top:0.25rem;">{_badge_html(row.get('risk_score',0))}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True
                )
                
                with st.spinner("Generating deep dive..."):
                    report = generate_customer_intelligence(cid)
                    if ts_key not in st.session_state:
                        import datetime
                        st.session_state[ts_key] = datetime.datetime.now().astimezone().strftime("Generated: %d %b %Y &middot; %H:%M %Z")
                    
                if report:
                    def _val(k):
                        v = report.get(k)
                        return f'<span class="empty-state">Data unavailable</span>' if not v else v

                    st.markdown(f"<div class='mono' style='font-size:0.75rem; color:var(--text-muted); text-align:right; margin-bottom:1rem;'>{st.session_state[ts_key]}</div>", unsafe_allow_html=True)
                    
                    # Executive Diagnosis & Hero Action
                    st.markdown(
                        f"""
                        <div class="v-card animate-entrance">
                            <div class="v-eyebrow">Executive Diagnosis</div>
                            <div class="v-p" style="color:var(--text-h); font-size:1.05rem;">{_val('executive_diagnosis')}</div>
                        </div>
                        
                        <div class="v-card-hero animate-entrance" style="animation-delay: 0.05s;">
                            <div class="v-eyebrow" style="color:var(--cyan);">Retention Strategy</div>
                            <div class="v-value">{_val('retention_strategy')}</div>
                        </div>
                        <div class="v-card animate-entrance" style="animation-delay: 0.1s;">
                            <div class="v-eyebrow">Expected Outcome</div>
                            <div class="v-p" style="color:var(--text-p);">{_val('expected_outcome')}</div>
                        </div>
                        """, unsafe_allow_html=True
                    )
                    
                    with st.expander("View Detailed Analysis"):
                        st.write("**Likely Business Situation**\n\n" + _val("likely_business_situation"))
                        st.write("**Behavioral Changes**\n\n" + _val("behavioral_changes"))
                        st.write("**Revenue Risk Assessment**\n\n" + _val("revenue_risk_assessment"))
                else:
                    st.error("Failed to generate report.")

# ==============================================================================
# TAB 2: TIER INTELLIGENCE
# ==============================================================================
with tab2:
    if merged_df.empty:
        st.warning("No data.")
    else:
        st.markdown("<div class='v-eyebrow' style='margin-bottom:0.5rem;'>Select Tier Segment</div>", unsafe_allow_html=True)
        selected_tier = st.selectbox("Select Tier", ["Gold", "Silver", "Bronze"], label_visibility="collapsed")
        tier_df = merged_df[merged_df["tier"] == selected_tier]
        
        if tier_df.empty:
            st.info(f"No customers in {selected_tier} tier.")
        else:
            ts_key_tier = f"ts_tier_{selected_tier}"
            avg_risk = tier_df["risk_score"].mean()
            at_risk = len(tier_df[tier_df["risk_score"] > 50])
            total = len(tier_df)
            
            st.markdown(
                f"""
                <div class="kpi-row" style="margin-top:1.5rem;">
                    <div class="kpi-block"><div class="kpi-num">{total}</div><div class="kpi-lbl">Customers</div></div>
                    <div class="kpi-block"><div class="kpi-num">{avg_risk:.1f}</div><div class="kpi-lbl">Avg Risk</div></div>
                    <div class="kpi-block"><div class="kpi-num" style="color:var(--red);">{at_risk}</div><div class="kpi-lbl">At Risk</div></div>
                </div>
                """, unsafe_allow_html=True
            )
            
            with st.spinner(f"Analyzing {selected_tier} tier..."):
                report = generate_tier_analysis(selected_tier)
                if ts_key_tier not in st.session_state:
                    import datetime
                    st.session_state[ts_key_tier] = datetime.datetime.now().astimezone().strftime("Generated: %d %b %Y &middot; %H:%M %Z")
                
            if report:
                def _val(k):
                    v = report.get(k)
                    return f'<span class="empty-state">Data unavailable</span>' if not v else v

                st.markdown(f"<div class='mono' style='font-size:0.75rem; color:var(--text-muted); text-align:right; margin-bottom:1rem;'>{st.session_state[ts_key_tier]}</div>", unsafe_allow_html=True)
                st.markdown(
                    f"""
                    <div class="v-card animate-entrance">
                        <div class="v-eyebrow">Tier Health Assessment</div>
                        <div class="v-p" style="color:var(--text-h); font-size:1.05rem;">{_val('tier_health_assessment')}</div>
                    </div>
                    <div class="v-card-hero animate-entrance" style="animation-delay: 0.05s;">
                        <div class="v-eyebrow" style="color:var(--cyan);">Strategic Recommendation</div>
                        <div class="v-value">{_val('strategic_recommendation')}</div>
                    </div>
                    """, unsafe_allow_html=True
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(
                        f"""
                        <div class="v-card animate-entrance" style="animation-delay: 0.1s;">
                            <div class="v-eyebrow">Primary Decay Drivers</div>
                            <div class="v-p">{_val('primary_decay_drivers')}</div>
                        </div>
                        """, unsafe_allow_html=True
                    )
                with col2:
                    st.markdown(
                        f"""
                        <div class="v-card animate-entrance" style="animation-delay: 0.15s;">
                            <div class="v-eyebrow">Expected Business Impact</div>
                            <div class="v-p">{_val('expected_business_impact')}</div>
                        </div>
                        """, unsafe_allow_html=True
                    )

                with st.expander("View Detailed Analysis"):
                    st.write("**Behavioral Pattern Analysis**\n\n" + _val("behavioral_pattern_analysis"))
                    st.write("**Healthy vs. At-Risk Accounts**\n\n" + _val("healthy_vs_at_risk"))
                
                st.markdown("<div class='v-eyebrow' style='margin-top:2rem;'>Top At-Risk Accounts</div>", unsafe_allow_html=True)
                top_accs = tier_df.sort_values("risk_score", ascending=False).head(5)
                table_html = "<table class='v-table'><thead><tr><th>Company</th><th>ID</th><th>Risk Score</th><th>Label</th></tr></thead><tbody>"
                for _, r in top_accs.iterrows():
                    table_html += f"<tr><td>{r['company_name']}</td><td class='mono'>{r['customer_id']}</td><td class='mono'>{r['risk_score']:.1f}</td><td>{_badge_html(r['risk_score'])}</td></tr>"
                table_html += "</tbody></table>"
                st.markdown(f"<div class='v-card' style='padding:0;'>{table_html}</div>", unsafe_allow_html=True)

# ==============================================================================
# TAB 3: PORTFOLIO INTELLIGENCE
# ==============================================================================
with tab3:
    if merged_df.empty:
        st.warning("No data.")
    else:
        ts_key_port = "ts_portfolio_intel"
        total_cust = len(merged_df)
        total_risk = len(merged_df[merged_df["risk_score"] > 50])
        health = 100 - (total_risk / total_cust * 100) if total_cust > 0 else 0
        
        st.markdown(
            f"""
            <div class="hero-header" style="text-align:center;">
                <div class="mono" style="font-size:3.5rem; font-weight:600; color:var(--text-h); line-height:1; letter-spacing:-0.05em;">{health:.1f}%</div>
                <div class="v-eyebrow" style="margin-top:0.75rem;">Portfolio Health Score</div>
            </div>
            """, unsafe_allow_html=True
        )
        
        with st.spinner("Analyzing portfolio risk..."):
            report = generate_portfolio_analysis()
            if ts_key_port not in st.session_state:
                import datetime
                st.session_state[ts_key_port] = datetime.datetime.now().astimezone().strftime("Generated: %d %b %Y &middot; %H:%M %Z")
            
        if report:
            def _val(k):
                v = report.get(k)
                return f'<span class="empty-state">Data unavailable</span>' if not v else v

            st.markdown(f"<div class='mono' style='font-size:0.75rem; color:var(--text-muted); text-align:right; margin-bottom:1rem;'>{st.session_state[ts_key_port]}</div>", unsafe_allow_html=True)
            st.markdown(
                f"""
                <div class="v-card animate-entrance">
                    <div class="v-eyebrow">Portfolio Health</div>
                    <div class="v-p" style="color:var(--text-h); font-size:1.05rem;">{_val('portfolio_health')}</div>
                </div>
                <div class="v-card animate-entrance" style="animation-delay: 0.05s;">
                    <div class="v-eyebrow">Projected Business Impact</div>
                    <div class="v-p">{_val('projected_business_impact')}</div>
                </div>
                <div class="v-card-hero animate-entrance" style="animation-delay: 0.1s;">
                    <div class="v-eyebrow" style="color:var(--amber);">Strategic Recommendations</div>
                    <div class="v-value">{_val('strategic_recommendations')}</div>
                </div>
                """, unsafe_allow_html=True
            )
            
            with st.expander("View Executive Intelligence Brief"):
                st.write("**Largest Revenue Threat**\n\n" + report.get("largest_revenue_threat", ""))
                st.write("**Risk Concentration Analysis**\n\n" + report.get("risk_concentration_analysis", ""))
                st.write("**Emerging Trends**\n\n" + report.get("emerging_trends", ""))
                st.write("**Resource Allocation Priorities**\n\n" + report.get("resource_allocation_priorities", ""))

# ==============================================================================
# TAB 4: INTERVENTION AGENT (Copilot)
# ==============================================================================
with tab4:
    from agent.agent_runner import load_data, get_risky_customers, AVAILABLE_ACTIONS
    from agent.gemini_client import setup_gemini_client
    from utils.agent_worker import create_worker_state, start_worker, stop_worker, approve_current

    PROCESSING_STEPS = ["Load Profile", "Analyze Signals", "Call Gemini", "Format Response"]

    def _get_worker_state(): return st.session_state.get("worker_state")
    def _is_worker_active():
        ws = _get_worker_state()
        return ws and (ws.get("running", False) or ws.get("phase") == "waiting_review")

    def do_start_agent():
        db = connect_to_mongo()
        combined = load_data(db)
        risky = get_risky_customers(combined)
        if risky.empty:
            st.warning("All customers are healthy.")
            st.stop()
        customers = [r.to_dict() for _, r in risky.iterrows()]
        try: gemini_client = setup_gemini_client()
        except SystemExit: st.error("GEMINI_API_KEY not found."); st.stop()

        state = create_worker_state(customers, len(customers))
        st.session_state.worker_state = state
        st.session_state.worker_db = db
        st.session_state.worker_gemini = gemini_client
        start_worker(state, gemini_client, db)
        st.rerun()

    def do_stop_agent():
        ws = _get_worker_state()
        if ws: stop_worker(ws)

    def do_approve_action(action):
        ws = _get_worker_state()
        db = st.session_state.get("worker_db")
        if ws is not None and db is not None: approve_current(ws, action, db)

    ws = _get_worker_state()
    worker_active = _is_worker_active()

    if ws is None or (not worker_active and ws.get("finished") is not True):
        st.markdown(
            """
            <div class="v-card" style="text-align:center; padding:3rem 2rem;">
                <h2 style="margin-bottom:1rem; font-weight:600; letter-spacing:-0.03em;">Intervention Copilot</h2>
                <div class="v-p" style="max-width:500px; margin:0 auto 2rem;">
                    Runs asynchronously to analyze at-risk accounts. Reviews each account and prepares a recommended intervention for your final approval.
                </div>
            </div>
            """, unsafe_allow_html=True
        )
        colA, colB, colC = st.columns([1,1,1])
        with colB:
            if st.button("Start Copilot", type="primary", use_container_width=True):
                do_start_agent()

    elif ws is not None and worker_active:
        if ws.get("toast"):
            st.toast(f"✅ {ws['toast']['action']} saved for {ws['toast']['customer_name']}")
            ws["toast"] = None

        phase = ws["phase"]
        idx = ws["current_idx"]
        total = ws["total"]

        if phase in ("processing", "calling", "advance"):
            c_obj = ws.get("current_customer", {})
            cname = c_obj.get("company_name", "Generating Recommendation...")
            cid = c_obj.get("customer_id", "---")
            tier = c_obj.get("tier", "---")
            score = c_obj.get("risk_score", 0.0)
            
            # Skeleton matching the final UI layout
            st.markdown(
                f"""
                <div class="hero-header" style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:1rem; padding-bottom:1rem;">
                    <div>
                        <div class="hero-title" style="font-size:1.5rem;">{cname}</div>
                        <div class="hero-subtitle mono">ID: {cid} • Tier: {tier}</div>
                    </div>
                    <div style="text-align:right;">
                        <div class="mono" style="font-size:1.8rem; font-weight:600; color:var(--text-h); line-height:1;">{float(score):.1f}</div>
                        <div style="margin-top:0.25rem;">{_badge_html(float(score))}</div>
                    </div>
                </div>
                
                <div class="v-card-hero" style="margin-top:0;">
                    <div style="display:flex; justify-content:space-between; margin-bottom:0.5rem;">
                        <div class="shimmer" style="width:120px; height:12px;"></div>
                        <div class="shimmer" style="width:80px; height:12px;"></div>
                    </div>
                    <div class="shimmer" style="width:250px; height:28px; margin-bottom:1rem;"></div>
                    <div class="shimmer" style="width:100%; height:16px; margin-bottom:0.5rem;"></div>
                    <div class="shimmer" style="width:85%; height:16px;"></div>
                </div>
                
                <div class="v-eyebrow" style="margin-bottom:0.75rem;">Select Final Action</div>
                <div class="shimmer" style="width:150px; height:20px; margin-bottom:1rem;"></div>
                
                <br>
                <div style="display:flex; gap:1rem;">
                    <div class="shimmer" style="flex:1; height:40px; border-radius:4px;"></div>
                    <div class="shimmer" style="flex:1; height:40px; border-radius:4px;"></div>
                    <div class="shimmer" style="flex:1; height:40px; border-radius:4px;"></div>
                </div>
                """, unsafe_allow_html=True
            )
            
            # Use columns to position the Stop Agent button cleanly under the skeleton
            c1, c2, c3 = st.columns([1,1,1])
            with c2:
                if st.button("Stop Agent (Interrupt)", use_container_width=True):
                    do_stop_agent(); st.rerun()

            @st.fragment(run_every=2)
            def _poll_proc():
                _w = st.session_state.get("worker_state")
                if _w and _w.get("phase") not in ("processing", "calling", "advance"): st.rerun()
            _poll_proc()

        elif phase == "waiting_review":
            c = ws["current_customer"]
            r = ws["gemini_result"]
            
            # Record generation time once when it enters review phase
            ts_key_agent = f"ts_agent_run_{ws.get('current_idx')}"
            if ts_key_agent not in st.session_state:
                import datetime
                st.session_state[ts_key_agent] = datetime.datetime.now().astimezone().strftime("Generated: %d %b %Y &middot; %H:%M %Z")
                
            if c and r:
                st.markdown(f"<div class='mono' style='font-size:0.7rem; color:var(--text-muted); text-align:right; margin-bottom:0.5rem;'>{st.session_state[ts_key_agent]}</div>", unsafe_allow_html=True)
                # Customer Header & Metrics
                score = float(c.get('risk_score',0))
                badge = _badge_html(score)
                urgency_color = "var(--red)" if r.get('urgency') == 'High' else "var(--amber)"
                
                st.markdown(
                    f"""
                    <div class="hero-header" style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:1rem; padding-bottom:1rem;">
                        <div>
                            <div class="hero-title" style="font-size:1.5rem;">{c.get('company_name')}</div>
                            <div class="hero-subtitle mono">ID: {c.get('customer_id')} • Tier: {c.get('tier')}</div>
                        </div>
                        <div style="text-align:right;">
                            <div class="mono" style="font-size:1.8rem; font-weight:600; color:var(--text-h); line-height:1;">{score:.1f}</div>
                            <div style="margin-top:0.25rem;">{badge}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True
                )
                
                # Large Recommendation Card
                primary = r.get("primary_action", "")
                reason = r.get("likely_reason", "")
                st.markdown(
                    f"""
                    <div class="v-card-hero animate-entrance" style="margin-top:0;">
                        <div style="display:flex; justify-content:space-between; margin-bottom:0.5rem;">
                            <div class="v-eyebrow" style="color:var(--cyan);">AI Recommendation</div>
                            <div class="v-eyebrow" style="color:{urgency_color};">Urgency: {r.get('urgency', 'Medium')}</div>
                        </div>
                        <div class="v-value" style="font-size:1.8rem; margin-bottom:1rem;">{primary}</div>
                        <div class="v-p">{reason}</div>
                    </div>
                    """, unsafe_allow_html=True
                )
                
                # Action Selection (Wrapped in a form to prevent rerun on selection)
                with st.form("action_selection_form", border=False):
                    st.markdown("<div class='v-eyebrow' style='margin-bottom:0.75rem;'>Select Final Action</div>", unsafe_allow_html=True)
                    
                    # Format available actions
                    action_options = []
                    idx_to_select = 0
                    for i, act in enumerate(AVAILABLE_ACTIONS):
                        if act == primary:
                            action_options.append(f"⭐ {act} (Recommended)")
                            idx_to_select = i
                        else:
                            action_options.append(act)
                            
                    selected_val = st.radio("Select Action", action_options, index=idx_to_select, label_visibility="collapsed")
                    # Clean the selected action from UI sugar
                    final_action = selected_val.replace("⭐ ", "").replace(" (Recommended)", "")
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    col_app, col_skip, col_stop = st.columns(3)
                    with col_app:
                        app_clicked = st.form_submit_button("Approve", type="primary", use_container_width=True)
                    with col_skip:
                        skip_clicked = st.form_submit_button("Skip", use_container_width=True)
                    with col_stop:
                        stop_clicked = st.form_submit_button("Stop Agent", use_container_width=True)
                
                # Handle form submissions outside the form block
                if app_clicked:
                    do_approve_action(final_action)
                    st.rerun()
                if skip_clicked:
                    do_approve_action(None)
                    st.rerun()
                if stop_clicked:
                    do_stop_agent()
                    st.rerun()
                        
                with st.expander("View Full Analysis"):
                    st.write("**Decay Summary:**\n\n" + r.get("decay_summary", ""))
                    st.write("**Priority Reason:**\n\n" + r.get("priority_reason", ""))
                    st.write("**Secondary Action:**\n\n" + r.get("secondary_action", ""))
                    st.write("**Suggested Outreach:**\n\n" + r.get("outreach_message", ""))


    if ws is not None and ws.get("finished") and not worker_active:
        st.success(f"Run Complete. Analyzed {ws.get('total',0)} customers. Saved {ws.get('saved_count',0)}.")
        if st.button("New Run", type="primary"):
            del st.session_state["worker_state"]
            st.rerun()