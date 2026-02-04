# admin_main.py (Deprecated)
import streamlit as st

st.set_page_config(page_title="Redirecting...", layout="centered")

st.warning("### ⚠️ This page is deprecated.")
st.write("The Admin dashboard has been separated into two distinct portals:")

col1, col2 = st.columns(2)
with col1:
    st.info("🛡️ **Superadmin Portal**")
    st.write("Run: `streamlit run superadmin_main.py`")
with col2:
    st.info("👨‍🏫 **HOD Portal**")
    st.write("Run: `streamlit run hod_main.py`")

st.divider()
st.write("Please use the appropriate file for your role.")
