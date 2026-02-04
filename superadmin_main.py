# superadmin_main.py
import streamlit as st
from Attendence.components.admin_ui import show_superadmin_panel
from Attendence.components.analytics_ui import show_analytics_panel
from Attendence.components.chatbot_ui import show_chatbot_panel

st.set_page_config(
    page_title="Superadmin Dashboard",
    page_icon="🛡️",
    layout="wide"
)

st.markdown(
    """
    <h1 style='text-align: center; color: #DC3545;'>🛡️ Superadmin Dashboard</h1>
    <hr style='border-top: 1px solid #bbb;'/></br>
    """,
    unsafe_allow_html=True
)

# Initialize session state for login if not present
if "superadmin_logged_in" not in st.session_state:
    st.session_state.superadmin_logged_in = False

if not st.session_state.superadmin_logged_in:
    show_superadmin_panel()
else:
    admin_tab, analytics_tab , chatbot_tab = st.tabs(["🛡️ Superadmin Panel", "📊 Analytics", "🤖 Chatbot"])

    with admin_tab:
        show_superadmin_panel()

    with analytics_tab:
        show_analytics_panel(allowed_classes=None)

    with chatbot_tab:
        show_chatbot_panel(allowed_classes=None)
