import streamlit as st

def load_css():
    return """
<style>
    /* ── Metric / Stat Cards ── */
    .metric-card, .stat-card {
        background: #161B22;
        border: 1px solid #30363D;
        border-radius: 10px;
        padding: 1rem 1.5rem;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .metric-value, .stat-value {
        font-size: 2rem;
        font-weight: 700;
    }
    .metric-label, .stat-label {
        color: #8B949E;
        font-size: 0.85rem;
        margin-top: 4px;
    }

    /* ── Section Headers ── */
    .section-header {
        border-left: 3px solid #00B4D8;
        padding-left: 10px;
        margin: 1.5rem 0 1rem 0;
        font-size: 1.1rem;
        font-weight: 600;
    }

    /* ── Incident Cards ── */
    .incident-card {
        background: #161B22;
        border: 1px solid #30363D;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin-bottom: 0.5rem;
    }

    /* ── Audit Log Rows ── */
    .audit-row {
        background: #161B22;
        border: 1px solid #30363D;
        border-radius: 8px;
        padding: 0.6rem 1rem;
        margin-bottom: 0.4rem;
        font-size: 0.85rem;
    }

    /* ── Login Box ── */
    .login-box {
        background: #161B22;
        padding: 2rem;
        border-radius: 12px;
        border: 1px solid #30363D;
        margin-top: 2rem;
    }
    .title-text {
        font-size: 2rem;
        font-weight: 700;
        color: #00B4D8;
        text-align: center;
    }
    .subtitle-text {
        color: #8B949E;
        text-align: center;
        margin-bottom: 2rem;
    }

    /* ── Severity Colors ── */
    .critical { color: #FF4444; }
    .high     { color: #FF8800; }
    .medium   { color: #FFD700; }
    .low      { color: #00CC66; }
</style>
"""

def show_sidebar_user():
    with st.sidebar:
        st.markdown(f"""
        <div style='padding: 0.5rem 0;'>
            <div style='font-size:0.85rem; color:#8B949E;'>Logged in as</div>
            <div style='font-size:1rem; font-weight:600; color:#C9D1D9;'>
                👤 {st.session_state['username']}
            </div>
            <div style='font-size:0.8rem; color:#00B4D8; margin-top:2px;'>
                🔑 {st.session_state['role']}
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.clear()
            st.switch_page("app.py")