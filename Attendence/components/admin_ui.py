# Attendence/components/admin_ui.py
import streamlit as st
import pandas as pd
from Attendence.services import auth_service, class_service, attendance_service, github_service, teacher_service
from Attendence.core.logger import get_logger
from Attendence.core.utils import current_ist_date

logger = get_logger(__name__)

def show_admin_panel():
    # st.set_page_config is handled in admin_main.py
    st.markdown("""
        <h1 style='text-align: center; color: #DC3545;'>🔑 Superadmin Control Panel</h1>
        <hr style='border-top: 1px solid #bbb;' />
    """, unsafe_allow_html=True)

    # Login
    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False

    if not st.session_state.admin_logged_in:
        with st.form("admin_login"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("🔐 Login"):
                if auth_service.authenticate_admin(username, password):
                    st.session_state.admin_logged_in = True
                    st.rerun()
                else:
                    st.error("Invalid credentials")
        return

    # Sidebar for Global Actions (Logout)
    with st.sidebar:
        st.write("Logged in as **Superadmin**")
        if st.button("🚪 Logout", key="admin_logout"):
            st.session_state.admin_logged_in = False
            st.rerun()

    # Tabs for Admin Functions
    tab_classes, tab_teachers = st.tabs(["📚 Manage Classes", "👨‍🏫 Manage Teachers"])

    with tab_classes:
        _render_manage_classes()

    with tab_teachers:
        _render_manage_teachers()

def _render_manage_classes():
    # Sidebar within tab context isn't ideal for everything, so we put actions in the main area or keep sidebar for global actions
    # But to keep existing flow, we can use the sidebar or top columns
    
    col_add, col_del = st.columns(2)
    with col_add:
        with st.expander("➕ Create Class"):
            class_input = st.text_input("New Class Name", key="new_class_input")
            if st.button("Add Class"):
                if class_input.strip():
                    success, msg = class_service.create_class(class_input)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.warning(msg)

    with col_del:
        with st.expander("🗑️ Delete Class"):
             delete_target = st.text_input("Enter class to delete", key="del_class_input")
             if st.button("Delete This Class"):
                 if delete_target.strip():
                     try:
                         class_service.delete_class(delete_target)
                         st.success(f"Class '{delete_target}' deleted.")
                         st.rerun()
                     except Exception:
                         st.error("Failed to delete class.")

    st.divider()

    # Class Controls
    try:
        classes = class_service.get_all_classes()
    except Exception:
        st.error("Failed to fetch classes.")
        return

    if not classes:
        st.warning("No classes found.")
        return

    class_names = [c["class_name"] for c in classes]
    
    # Persist selection
    if "admin_selected_class" not in st.session_state:
        st.session_state.admin_selected_class = class_names[0] if class_names else None

    # Sync
    if st.session_state.admin_selected_class not in class_names and class_names:
        st.session_state.admin_selected_class = class_names[0]
        
    selected_class_name = st.selectbox("📚 Select a Class to Manage", class_names, index=class_names.index(st.session_state.admin_selected_class) if st.session_state.admin_selected_class in class_names else 0)
    st.session_state.admin_selected_class = selected_class_name
    
    config = next((c for c in classes if c["class_name"] == selected_class_name), None)

    st.markdown(f"**Current Code:** `{config['code']}` | **Limit:** `{config['daily_limit']}`")

    is_open = config.get("is_open", False)
    st.caption(f"Status: **{'OPEN' if is_open else 'CLOSED'}**")
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("✅ Open Attendance"):
             class_service.update_class_status(selected_class_name, True)
             st.rerun()
    with c2:
        if st.button("❌ Close Attendance"):
            class_service.update_class_status(selected_class_name, False)
            st.rerun()

    with st.expander("🔄 Update Settings"):
        new_code = st.text_input("New Code", value=config["code"])
        new_limit = st.number_input("New Limit", min_value=1, value=config["daily_limit"], step=1)
        if st.button("Save Settings"):
            class_service.update_class_settings(selected_class_name, new_code, new_limit)
            st.success("Settings updated.")
            st.rerun()

    # Matrix
    try:
        records = attendance_service.fetch_attendance_records(selected_class_name)
    except Exception:
        return

    if records:
        df = pd.DataFrame(records)
        df["status"] = "P"
        pivot_df = df.pivot_table(index=["roll_number", "name"], columns="date", values="status", aggfunc="first", fill_value="A").reset_index()
        pivot_df["roll_number"] = pd.to_numeric(pivot_df["roll_number"], errors="coerce")
        pivot_df = pivot_df.dropna(subset=["roll_number"])
        pivot_df["roll_number"] = pivot_df["roll_number"].astype(int)
        pivot_df = pivot_df.sort_values("roll_number")

        st.dataframe(pivot_df, width="stretch")

        csv = pivot_df.to_csv(index=False)
        st.download_button("Download CSV", csv.encode(), f"{selected_class_name}.csv", "text/csv")

        if st.button("Push to GitHub"):
            success, msg = github_service.push_attendance_matrix(selected_class_name, csv)
            if success: st.success(msg)
            else: st.error(msg)
    else:
        st.info("No records found.")

def _render_manage_teachers():
    st.subheader("👨‍🏫 Teacher Management")
    
    # Add Teacher
    with st.expander("➕ Add New Teacher"):
        with st.form("add_teacher_form"):
            new_t_user = st.text_input("Username")
            new_t_pass = st.text_input("Password", type="password")
            new_t_name = st.text_input("Full Name")
            if st.form_submit_button("Create Teacher"):
                success, msg = teacher_service.create_teacher(new_t_user, new_t_pass, new_t_name)
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
    
    st.divider()
    
    # List & Edit Teachers
    teachers = teacher_service.get_all_teachers()
    if not teachers:
        st.info("No teachers found.")
        return

    teacher_names = [t["username"] for t in teachers]
    selected_teacher = st.selectbox("Select Teacher to Manage", teacher_names)
    
    if selected_teacher:
        teacher_info = next(t for t in teachers if t["username"] == selected_teacher)
        st.write(f"**Name:** {teacher_info['full_name']}")
        
        # Assign Classes
        all_classes = [c["class_name"] for c in class_service.get_all_classes()]
        assigned_classes = teacher_service.get_assigned_classes(selected_teacher)
        
        new_assignments = st.multiselect("Assign Classes", all_classes, default=[c for c in assigned_classes if c in all_classes])
        
        if st.button("💾 Update Assignments"):
            success, msg = teacher_service.assign_classes(selected_teacher, new_assignments)
            if success:
                st.success(msg)
            else:
                st.error(msg)

        st.markdown("---")
        if st.button("🗑️ Delete Teacher"):
            if teacher_service.delete_teacher(selected_teacher):
                st.success("Teacher deleted.")
                st.rerun()
