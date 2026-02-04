# hod_main.py
import streamlit as st
from Attendence.components.admin_ui import show_hod_panel
from Attendence.components.analytics_ui import show_analytics_panel
from Attendence.components.chatbot_ui import show_chatbot_panel
from Attendence.services import admin_service

st.set_page_config(
    page_title="HOD Dashboard",
    page_icon="👨‍🏫",
    layout="wide"
)

st.markdown(
    """
    <h1 style='text-align: center; color: #007BFF;'>👨‍🏫 HOD Dashboard</h1>
    <hr style='border-top: 1px solid #bbb;'/></br>
    """,
    unsafe_allow_html=True
)

# Initialize session state for login if not present
if "hod_logged_in" not in st.session_state:
    st.session_state.hod_logged_in = False

if not st.session_state.hod_logged_in:
    show_hod_panel()
else:
    # Get assigned classes for HOD
    allowed_classes = admin_service.get_admin_classes(st.session_state.admin_username)
    
    admin_tab, analytics_tab , chatbot_tab = st.tabs(["👨‍🏫 HOD Panel", "📊 Analytics", "🤖 Chatbot"])

    with admin_tab:
        show_hod_panel()

    with analytics_tab:
        show_analytics_panel(allowed_classes=allowed_classes)

    with chatbot_tab:
        show_chatbot_panel(allowed_classes=allowed_classes)
