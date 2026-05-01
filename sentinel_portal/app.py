import streamlit as st
import bcrypt
from db import get_connection
from styles import load_css, show_sidebar_user

st.set_page_config(
    page_title="Sentinel Incident Portal",
    page_icon="🛡️",
    layout="centered"
)

st.markdown(load_css(), unsafe_allow_html=True)

# Hide sidebar on login page
st.markdown("""
<style>
    [data-testid="stSidebar"] { display: none; }
    [data-testid="collapsedControl"] { display: none; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title-text">🛡️ SENTINEL</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle-text">Incident Management Portal</div>', unsafe_allow_html=True)

st.subheader("🔐 Secure Login")
username = st.text_input("Username", placeholder="Enter your username")
password = st.text_input("Password", type="password", placeholder="Enter your password")

if st.button("Login", use_container_width=True):
    if username and password:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.UserID, u.Username, r.RoleName, ul.PasswordHash
            FROM USERS u
            JOIN ROLES r ON u.RoleID = r.RoleID
            JOIN USER_LOGIN ul ON u.UserID = ul.UserID
            WHERE u.Username = ?
        """, (username,))
        row = cursor.fetchone()
        conn.close()

        if row:
            stored_hash = row[3].encode('utf-8')
            if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
                st.session_state['logged_in'] = True
                st.session_state['username'] = row[1]
                st.session_state['role'] = row[2]
                st.session_state['user_id'] = row[0]
                st.success(f"Welcome, {row[1]}!")
                st.switch_page("pages/Incidents.py")
            else:
                st.error("❌ Invalid password.")
        else:
            st.error("❌ User not found.")
    else:
        st.warning("⚠️ Please enter both username and password.")