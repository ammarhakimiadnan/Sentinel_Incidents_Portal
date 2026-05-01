import streamlit as st
import pandas as pd
from db import (get_connection, get_incidents, get_active_incident_ids,
                get_resolved_incident_ids, insert_incident,
                resolve_incident, delete_incident)
from styles import load_css, show_sidebar_user

if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.warning("Please log in first.")
    st.stop()

st.set_page_config(page_title="Incidents", page_icon="🚨", layout="wide")
st.markdown(load_css(), unsafe_allow_html=True)
show_sidebar_user()

st.markdown("# 🚨 Incident Dashboard")
st.divider()

# Metrics
conn = get_connection()
cursor = conn.cursor()
cursor.execute("SELECT Severity FROM INCIDENTS WHERE Status = 'Active'")
all_severities = [row[0] for row in cursor.fetchall()]
conn.close()

total    = len(all_severities)
critical = all_severities.count("Critical")
high     = all_severities.count("High")
medium   = all_severities.count("Medium")
low      = all_severities.count("Low")

c1, c2, c3, c4, c5 = st.columns(5)
for col, val, label, color in [
    (c1, total,    "Active Incidents", "#00B4D8"),
    (c2, critical, "Critical",         "#FF4444"),
    (c3, high,     "High",             "#FF8800"),
    (c4, medium,   "Medium",           "#FFD700"),
    (c5, low,      "Low",              "#00CC66"),
]:
    with col:
        st.markdown(f"""<div class='metric-card'>
            <div class='metric-value' style='color:{color};'>{val}</div>
            <div class='metric-label'>{label}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Action buttons
role = st.session_state['role']
btn_cols = st.columns([1, 1, 1, 3])

with btn_cols[0]:
    if role in ['Admin', 'Analyst']:
        if st.button("➕ Report Incident", use_container_width=True):
            st.session_state['show_modal'] = 'report'

with btn_cols[1]:
    if role in ['Admin', 'Analyst']:
        if st.button("✅ Resolve Incident", use_container_width=True):
            st.session_state['show_modal'] = 'resolve'

with btn_cols[2]:
    if role == 'Admin':
        if st.button("🗑️ Delete Incident", use_container_width=True):
            st.session_state['show_modal'] = 'delete'

# ── Report Modal ──
if st.session_state.get('show_modal') == 'report':
    with st.container(border=True):
        st.markdown("### ➕ Report New Incident")
        col1, col2 = st.columns(2)
        with col1:
            inc_type = st.selectbox("Incident Type", [
                "Phishing", "Unauthorised Access", "Data Leak",
                "Malware", "Ransomware", "Brute Force",
                "DDoS", "Insider Threat", "Social Engineering", "Other"
            ])
            severity = st.radio("Severity", ["Low", "Medium", "High", "Critical"],
                                horizontal=True)
        with col2:
            details = st.text_area("Details",
                                   placeholder="Describe the incident...",
                                   height=120)
        ca, cb = st.columns(2)
        with ca:
            if st.button("🚨 Submit", use_container_width=True):
                if details:
                    insert_incident(inc_type, severity, details,
                                    st.session_state['user_id'])
                    st.success("✅ Incident reported and encrypted!")
                    st.session_state['show_modal'] = None
                    st.rerun()
                else:
                    st.warning("Please fill in the details.")
        with cb:
            if st.button("✖ Cancel", use_container_width=True):
                st.session_state['show_modal'] = None
                st.rerun()

# ── Resolve Modal ──
if st.session_state.get('show_modal') == 'resolve':
    with st.container(border=True):
        st.markdown("### ✅ Resolve Incident")
        st.caption("Marks the incident as resolved. It stays in records.")
        active_ids = get_active_incident_ids()
        if active_ids:
            options = {f"#{r[0]} — {r[1]}": r[0] for r in active_ids}
            selected = st.selectbox("Select Incident", list(options.keys()))
            ca, cb = st.columns(2)
            with ca:
                if st.button("✅ Confirm Resolve", use_container_width=True):
                    resolve_incident(options[selected],
                                     st.session_state['user_id'])
                    st.success(f"✅ {selected} marked as resolved!")
                    st.session_state['show_modal'] = None
                    st.rerun()
            with cb:
                if st.button("✖ Cancel ", use_container_width=True):
                    st.session_state['show_modal'] = None
                    st.rerun()
        else:
            st.info("No active incidents to resolve.")
            if st.button("✖ Close"):
                st.session_state['show_modal'] = None
                st.rerun()

# ── Delete Modal ──
if st.session_state.get('show_modal') == 'delete':
    with st.container(border=True):
        st.markdown("### 🗑️ Delete Incident")
        st.warning("⚠️ This permanently removes the incident. Cannot be undone.")
        all_ids = get_active_incident_ids() + get_resolved_incident_ids()
        if all_ids:
            options = {f"#{r[0]} — {r[1]}": r[0] for r in all_ids}
            selected = st.selectbox("Select Incident to Delete",
                                    list(options.keys()))
            confirm = st.checkbox(
                f"I confirm permanent deletion of **{selected}**")
            ca, cb = st.columns(2)
            with ca:
                if st.button("🗑️ Confirm Delete",
                             use_container_width=True, type="primary"):
                    if confirm:
                        delete_incident(options[selected],
                                        st.session_state['user_id'])
                        st.success(f"🗑️ {selected} permanently deleted.")
                        st.session_state['show_modal'] = None
                        st.rerun()
                    else:
                        st.error("Please check the confirmation box.")
            with cb:
                if st.button("✖ Cancel  ", use_container_width=True):
                    st.session_state['show_modal'] = None
                    st.rerun()
        else:
            st.info("No incidents available.")
            if st.button("✖ Close "):
                st.session_state['show_modal'] = None
                st.rerun()

st.divider()

# Chart + Incident list
left, right = st.columns([1, 2])

with left:
    st.markdown('<div class="section-header">📊 Severity Breakdown</div>',
                unsafe_allow_html=True)
    if all_severities:
        chart_data = pd.DataFrame({
            "Severity": ["Critical", "High", "Medium", "Low"],
            "Count":    [critical,   high,   medium,   low]
        })
        st.bar_chart(chart_data.set_index("Severity"), color="#00B4D8")

with right:
    st.markdown('<div class="section-header">📋 Incident Records</div>',
                unsafe_allow_html=True)
    can_decrypt = role in ['Admin', 'Analyst']
    show_decrypted = (st.toggle("🔓 Show Decrypted Details", value=False)
                      if can_decrypt else False)
    if not can_decrypt:
        st.caption("🔒 Details are encrypted. Contact Admin for access.")

    tab1, tab2 = st.tabs(["🔴 Active", "✅ Resolved"])

    def render_incidents(rows, resolved=False):
        if rows:
            for row in rows:
                color = {"Critical": "#FF4444", "High": "#FF8800",
                         "Medium":   "#FFD700", "Low":  "#00CC66"
                         }.get(row[2], "#888")
                badge = (f"<b style='color:#00CC66;'>✅ RESOLVED</b>"
                         if resolved
                         else f"<b style='color:{color};'>[{row[2]}]</b>")
                border_color = "#00CC66" if resolved else color
                st.markdown(f"""
                <div style='background:#161B22; border:1px solid #30363D;
                            border-left:3px solid {border_color};
                            border-radius:8px; padding:0.75rem 1rem;
                            margin-bottom:0.5rem;'>
                    {badge} <b>#{row[0]} — {row[1]}</b><br>
                    <span style='color:#8B949E; font-size:0.85rem;'>
                        👤 {row[4]} &nbsp;|&nbsp; 🕒 {row[5]}
                    </span><br>
                    <span style='font-size:0.9rem;'>📝 {row[3]}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No incidents found.")

    with tab1:
        render_incidents(get_incidents(decrypt=show_decrypted, status='Active'))
    with tab2:
        render_incidents(get_incidents(decrypt=show_decrypted, status='Resolved'),
                         resolved=True)