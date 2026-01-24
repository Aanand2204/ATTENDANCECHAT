import streamlit as st
import pandas as pd
from Attendence.services import auth_service, class_service, attendance_service, teacher_service
from Attendence.components.analytics_ui import show_analytics_panel
from Attendence.components.chatbot_ui import show_chatbot_panel
from Attendence.core.logger import get_logger

logger = get_logger(__name__)

def show_teacher_panel():
    st.set_page_config(page_title="Teacher Portal", layout="wide", page_icon="🏫")
    st.markdown("""
        <h1 style='text-align: center; color: #4CAF50;'>🏫 Teacher Portal</h1>
        <hr style='border-top: 1px solid #bbb;' />
    """, unsafe_allow_html=True)

    # Login Logic
    if "teacher_logged_in" not in st.session_state:
        st.session_state.teacher_logged_in = False
        st.session_state.teacher_username = None

    if not st.session_state.teacher_logged_in:
        with st.form("teacher_login"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Log In"):
                if auth_service.authenticate_teacher(username, password):
                    st.session_state.teacher_logged_in = True
                    st.session_state.teacher_username = username
                    st.rerun()
                else:
                    st.error("Invalid credentials.")
        return

    # Logout
    with st.sidebar:
        st.write(f"Logged in as: **{st.session_state.teacher_username}**")
        if st.button("🚪 Logout"):
            st.session_state.teacher_logged_in = False
            st.session_state.teacher_username = None
            st.rerun()

    # Capabilities
    tabs = st.tabs(["📝 Attendance", "📊 Analytics", "🤖 Chatbot"])

    # Fetch assigned classes
    try:
        assigned_classes = teacher_service.get_assigned_classes(st.session_state.teacher_username)
    except Exception:
        st.error("Could not fetch your classes.")
        assigned_classes = []

    if not assigned_classes:
        st.info("You don't have any classes assigned yet.")
        return

    with tabs[0]:
        _render_attendance_controls(assigned_classes)

    with tabs[1]:
        show_analytics_panel(allowed_classes=assigned_classes)

    with tabs[2]:
        show_chatbot_panel(allowed_classes=assigned_classes)

def _render_attendance_controls(assigned_classes):
    st.subheader("📝 Take Attendance")
    
    selected_class = st.selectbox("Select Class", assigned_classes, key="teacher_class_select")
    
    # We need to fetch full class info to get the status
    all_class_info = class_service.get_all_classes()
    class_info = next((c for c in all_class_info if c["class_name"] == selected_class), None)

    if not class_info:
        st.error("Class details not found.")
        return

    is_open = class_info.get("is_open", False)
    st.info(f"Status: **{'OPEN' if is_open else 'CLOSED'}**")
    st.caption(f"Daily Limit: {class_info.get('daily_limit', 10)}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Open Attendance", key="t_open"):
            # Optional: Check if other classes are open if we want to enforce single active class rule here too
            class_service.update_class_status(selected_class, True)
            st.rerun()
    with col2:
        if st.button("❌ Close Attendance", key="t_close"):
            class_service.update_class_status(selected_class, False)
            st.rerun()
    
    st.divider()
    st.write("### Today's Status")
    
    records = attendance_service.fetch_attendance_records(selected_class)
    if records:
        df = pd.DataFrame(records)
        df["status"] = "P"
        pivot_df = df.pivot_table(index=["roll_number", "name"], columns="date", values="status", aggfunc="first", fill_value="A").reset_index()
        st.dataframe(pivot_df, width="stretch")
    else:
        st.info("No records found.")
