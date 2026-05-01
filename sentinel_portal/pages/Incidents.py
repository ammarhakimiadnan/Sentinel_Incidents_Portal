import streamlit as st
import pandas as pd
import plotly.express as px
from db import (get_connection, get_incidents, get_active_incident_ids,
                get_resolved_incident_ids, insert_incident,
                resolve_incident, delete_incident, get_incidents_over_time)
from styles import load_css, show_sidebar_user

# ── Setup ──
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.warning("Please log in first.")
    st.stop()

st.set_page_config(page_title="Incidents", page_icon="🚨", layout="wide")
st.markdown(load_css(), unsafe_allow_html=True)
show_sidebar_user()

st.markdown("# 🚨 Incident Dashboard")
st.divider()

# ── 1. Top Metrics Row ──
conn = get_connection()
cursor = conn.cursor()
cursor.execute("SELECT Severity FROM INCIDENTS WHERE Status = 'Active'")
all_severities = [row[0] for row in cursor.fetchall()]
cursor.execute("""
    SELECT 
        SUM(CASE WHEN Status='Active'   THEN 1 ELSE 0 END) AS Active,
        SUM(CASE WHEN Status='Resolved' THEN 1 ELSE 0 END) AS Resolved,
        COUNT(*) AS Total
    FROM INCIDENTS
""")
totals = cursor.fetchone()
conn.close()

total = len(all_severities)
critical = all_severities.count("Critical")
high = all_severities.count("High")
medium = all_severities.count("Medium")
low = all_severities.count("Low")

c1, c2, c3, c4, c5 = st.columns(5)
metrics = [
    (c1, total, "Active Incidents", "#00B4D8"),
    (c2, critical, "Critical", "#FF4444"),
    (c3, high, "High", "#FF8800"),
    (c4, medium, "Medium", "#FFD700"),
    (c5, low, "Low", "#00CC66"),
]
for col, val, label, color in metrics:
    with col:
        st.markdown(f"""<div class='metric-card'>
            <div class='metric-value' style='color:{color};'>{val}</div>
            <div class='metric-label'>{label}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── 2. Dashboard Grid (Charts) ──
col_left, col_right = st.columns([2, 1])

with col_left:
    st.markdown('<div class="section-header">📈 Trend Analytics</div>', unsafe_allow_html=True)
    time_data = get_incidents_over_time()
    if time_data:
        # FIX: Explicitly convert rows to lists to avoid shape errors
        data = [list(row) for row in time_data]
        df = pd.DataFrame(data, columns=['Date', 'Type', 'Count'])
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Pivot the data for the area chart
        df_pivot = df.pivot_table(index='Date', columns='Type', values='Count', aggfunc='sum').fillna(0)
        
        fig = px.area(
            df_pivot, 
            line_shape='spline',
            color_discrete_sequence=px.colors.qualitative.Dark24
        )
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            hovermode="x unified", margin=dict(l=0, r=0, t=20, b=0),
            xaxis=dict(showgrid=False, color="#8B949E"),
            yaxis=dict(showgrid=True, gridcolor="#30363D", color="#8B949E"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No timeline data available.")

with col_right:
    st.markdown('<div class="section-header">📊 Severity Breakdown</div>', unsafe_allow_html=True)
    severity_df = pd.DataFrame({"Severity": ["Critical", "High", "Medium", "Low"], "Count": [critical, high, medium, low]})
    
    fig_bar = px.bar(
        severity_df, x="Severity", y="Count",
        color="Severity", color_discrete_map={"Critical": "#FF4444", "High": "#FF8800", "Medium": "#FFD700", "Low": "#00CC66"}
    )
    fig_bar.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(color="#8B949E"), yaxis=dict(showgrid=True, gridcolor="#30363D", color="#8B949E"),
        showlegend=False, margin=dict(l=0, r=0, t=0, b=0)
    )
    st.plotly_chart(fig_bar, use_container_width=True)

st.divider()

# ── 3. Actions & Management ──
role = st.session_state['role']
btn_cols = st.columns([1, 1, 1, 3])

with btn_cols[0]:
    if role in ['Admin', 'Analyst'] and st.button("➕ Report Incident", use_container_width=True):
        st.session_state['show_modal'] = 'report'
with btn_cols[1]:
    if role in ['Admin', 'Analyst'] and st.button("✅ Resolve Incident", use_container_width=True):
        st.session_state['show_modal'] = 'resolve'
with btn_cols[2]:
    if role == 'Admin' and st.button("🗑️ Delete Incident", use_container_width=True):
        st.session_state['show_modal'] = 'delete'

# ── Modals Logic ──
if st.session_state.get('show_modal'):
    with st.container(border=True):
        modal = st.session_state['show_modal']
        
        if modal == 'report':
            st.markdown("### ➕ Report New Incident")
            col1, col2 = st.columns(2)
            with col1:
                inc_type = st.selectbox("Incident Type", ["Phishing", "Unauthorised Access", "Data Leak", "Malware", "Ransomware", "Brute Force", "DDoS", "Insider Threat", "Social Engineering", "Other"])
                severity = st.radio("Severity", ["Low", "Medium", "High", "Critical"], horizontal=True)
            with col2:
                details = st.text_area("Details", placeholder="Describe the incident...", height=120)
            
            ca, cb = st.columns(2)
            if ca.button("🚨 Submit", use_container_width=True):
                if details:
                    insert_incident(inc_type, severity, details, st.session_state['user_id'])
                    st.success("✅ Incident reported and encrypted!")
                    st.session_state['show_modal'] = None
                    st.rerun()
                else:
                    st.warning("Please fill in the details.")
            if cb.button("✖ Cancel", use_container_width=True):
                st.session_state['show_modal'] = None
                st.rerun()

        elif modal == 'resolve':
            st.markdown("### ✅ Resolve Incident")
            active_ids = get_active_incident_ids()
            if active_ids:
                options = {f"#{r[0]} — {r[1]}": r[0] for r in active_ids}
                selected = st.selectbox("Select Incident", list(options.keys()))
                ca, cb = st.columns(2)
                if ca.button("✅ Confirm Resolve", use_container_width=True):
                    resolve_incident(options[selected], st.session_state['user_id'])
                    st.success(f"✅ #{options[selected]} resolved!")
                    st.session_state['show_modal'] = None
                    st.rerun()
                if cb.button("✖ Cancel", use_container_width=True):
                    st.session_state['show_modal'] = None
                    st.rerun()
            else:
                st.info("No active incidents.")
                if st.button("✖ Close"):
                    st.session_state['show_modal'] = None
                    st.rerun()

        elif modal == 'delete':
            st.markdown("### 🗑️ Delete Incident")
            all_ids = get_active_incident_ids() + get_resolved_incident_ids()
            if all_ids:
                options = {f"#{r[0]} — {r[1]}": r[0] for r in all_ids}
                selected = st.selectbox("Select Incident to Delete", list(options.keys()))
                confirm = st.checkbox("I confirm permanent deletion")
                ca, cb = st.columns(2)
                if ca.button("🗑️ Confirm Delete", use_container_width=True, type="primary"):
                    if confirm:
                        delete_incident(options[selected], st.session_state['user_id'])
                        st.success("🗑️ Deleted successfully.")
                        st.session_state['show_modal'] = None
                        st.rerun()
                    else:
                        st.error("Please confirm first.")
                if cb.button("✖ Cancel", use_container_width=True):
                    st.session_state['show_modal'] = None
                    st.rerun()
            else:
                st.info("No incidents available.")
                if st.button("✖ Close"):
                    st.session_state['show_modal'] = None
                    st.rerun()

st.divider()

# ── 4. Records Section ──
st.markdown('<div class="section-header">📋 Incident Records</div>', unsafe_allow_html=True)
can_decrypt = role in ['Admin', 'Analyst']
show_decrypted = (st.toggle("🔓 Show Decrypted Details", value=False) if can_decrypt else False)

tab1, tab2 = st.tabs(["🔴 Active", "✅ Resolved"])

def render_incidents(rows, resolved=False):
    if rows:
        col_a, col_b = st.columns(2)
        for i, row in enumerate(rows):
            color = {"Critical": "#FF4444", "High": "#FF8800", "Medium": "#FFD700", "Low": "#00CC66"}.get(row[2], "#888")
            badge = f"<b style='color:#00CC66;'>✅ RESOLVED</b>" if resolved else f"<b style='color:{color};'>[{row[2]}]</b>"
            card = f"""<div style='background:#161B22; border:1px solid #30363D; border-left:3px solid {color}; border-radius:8px; padding:10px; margin-bottom:10px;'>
                {badge} <b>#{row[0]} — {row[1]}</b><br>
                <span style='color:#8B949E; font-size:0.8rem;'>👤 {row[4]} | 🕒 {row[5]}</span><br>
                <span style='font-size:0.9rem;'>{row[3]}</span></div>"""
            (col_a if i % 2 == 0 else col_b).markdown(card, unsafe_allow_html=True)
    else:
        st.info("No incidents found.")

with tab1:
    render_incidents(get_incidents(decrypt=show_decrypted, status='Active'))
with tab2:
    render_incidents(get_incidents(decrypt=show_decrypted, status='Resolved'), resolved=True)