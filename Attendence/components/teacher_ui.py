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
    col_title, col_ref = st.columns([4, 1])
    with col_title:
        st.subheader("📝 Take Attendance")
    with col_ref:
        if st.button("🔄 Refresh", key="t_refresh_top"):
            attendance_service.fetch_attendance_records.clear()
            st.rerun()
    
    selected_class = st.selectbox("Select Class", assigned_classes, key="teacher_class_select")
    
    # We need to fetch full class info to get the status
    all_class_info = class_service.get_all_classes()
    class_info = next((c for c in all_class_info if c["class_name"] == selected_class), None)

    if not class_info:
        st.error("Class details not found.")
        return

    is_open = class_info.get("is_open", False)
    status_md = f"Status: **{'OPEN' if is_open else 'CLOSED'}**"
    if is_open and class_info.get("opened_by"):
        status_md += f" (by {class_info['opened_by']})"
    st.info(status_md)
    st.caption(f"Daily Limit: {class_info.get('daily_limit', 10)}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Open Attendance", key="t_open"):
            # Check if this specific class is already open (potentially by someone else)
            if class_info.get("is_open"):
                opener = class_info.get("opened_by", "another teacher")
                st.error(f"⚠️ Class '{selected_class}' is already currently open by **{opener}**.")
                # We stop here to match the requirement "No 2 teachers can open the same classroom"
            else:
                 # Check for other open classes assigned to this teacher (Single Active Class Restriction)
                 # MUST ensure we only count classes opened BY THIS TEACHER
                other_open = [
                    c["class_name"] 
                    for c in all_class_info 
                    if c["class_name"] in assigned_classes 
                    and c["class_name"] != selected_class 
                    and c.get("is_open")
                    and c.get("opened_by") == st.session_state.teacher_username
                ]
                
                if other_open:
                    st.error(f"⚠️ You already have attendance open for: **{other_open[0]}**. Please close it first.")
                else:
                    class_service.update_class_status(selected_class, True, st.session_state.teacher_username)
                    st.rerun()
    with col2:
        if st.button("❌ Close Attendance", key="t_close"):
            opener = class_info.get("opened_by")
            current_user = st.session_state.teacher_username
            
            if opener and opener != current_user:
                st.error(f"⚠️ You cannot close this class. It was opened by **{opener}**.")
            else:
                class_service.update_class_status(selected_class, False)
                st.rerun()
    
    with st.expander("⚙️ Update Class Settings"):
        st.caption("Change the attendance code or daily limit for this class.")
        new_code = st.text_input("Attendance Code", value=class_info.get("code", ""), key="t_new_code")
        new_limit = st.number_input("Daily Limit", min_value=1, value=int(class_info.get("daily_limit", 10)), step=1, key="t_new_limit")
        if st.button("💾 Save Settings", key="t_save_settings"):
            class_service.update_class_settings(selected_class, new_code, new_limit)
            st.session_state.teacher_msg = "Settings updated successfully!"
            st.rerun()
            
    if "teacher_msg" in st.session_state and st.session_state.teacher_msg:
        st.success(st.session_state.teacher_msg)
        del st.session_state.teacher_msg

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
