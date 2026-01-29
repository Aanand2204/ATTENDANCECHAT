# Attendence/components/admin_ui.py
import streamlit as st
import pandas as pd
from Attendence.services import auth_service, class_service, attendance_service, github_service, teacher_service, admin_service
from Attendence.core.logger import get_logger
from Attendence.core.utils import current_ist_date

logger = get_logger(__name__)

def show_admin_panel():
    # st.set_page_config is handled in admin_main.py
    st.markdown("""
        <h1 style='text-align: center; color: #DC3545;'>🔑 Admin Control Panel</h1>
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
                success, role = auth_service.authenticate_admin(username, password)
                if success:
                    st.session_state.admin_logged_in = True
                    st.session_state.admin_role = role
                    st.session_state.admin_username = username
                    st.rerun()
                else:
                    st.error("Invalid credentials")
        return

    # Sidebar for Global Actions (Logout)
    role_display = "Superadmin" if st.session_state.admin_role == "superadmin" else "Admin (HOD)"
    with st.sidebar:
        st.write(f"Logged in as **{role_display}**")
        st.write(f"User: `{st.session_state.admin_username}`")
        if st.button("🚪 Logout", key="admin_logout"):
            st.session_state.admin_logged_in = False
            del st.session_state.admin_role
            del st.session_state.admin_username
            st.rerun()

    # Tabs for Admin Functions
    tabs = ["📚 Manage Classes", "👨‍🏫 Manage Teachers"]
    if st.session_state.admin_role == "superadmin":
        tabs.append("🛡️ Manage Admins")
    
    tab_list = st.tabs(tabs)

    with tab_list[0]:
        _render_manage_classes()

    with tab_list[1]:
        _render_manage_teachers()

    if st.session_state.admin_role == "superadmin":
        with tab_list[2]:
            _render_manage_admins()

def _render_manage_classes():
    # Sidebar within tab context isn't ideal for everything, so we put actions in the main area or keep sidebar for global actions
    # But to keep existing flow, we can use the sidebar or top columns
    
    admin_filter = None if st.session_state.admin_role == "superadmin" else st.session_state.admin_username

    # Message System
    if "admin_msg" in st.session_state and st.session_state.admin_msg:
        msg_type, msg_text = st.session_state.admin_msg
        if msg_type == "success":
            st.success(msg_text)
        elif msg_type == "error":
            st.error(msg_text)
        elif msg_type == "warning":
            st.warning(msg_text)
        # Clear after showing
        del st.session_state.admin_msg

    # Fetch classes first so we can use them in delete dropdown
    try:
        classes = class_service.get_all_classes(admin_username=admin_filter)
    except Exception:
        st.error("Failed to fetch classes.")
        classes = []

    col_add, col_del = st.columns(2)
    with col_add:
        with st.expander("➕ Create Class"):
            class_input = st.text_input("New Class Name", key="new_class_input")
            if st.button("Add Class"):
                if class_input.strip():
                    success, msg = class_service.create_class(class_input)
                    if success:
                        if admin_filter:
                            admin_service.assign_classes_to_admin(admin_filter, admin_service.get_admin_classes(admin_filter) + [class_input])
                        st.session_state.admin_msg = ("success", msg)
                        st.rerun()
                    else:
                        st.warning(msg)

    with col_del:
        with st.expander("🗑️ Delete Class"):
             with st.form("delete_class_form"):
                 class_opts = [c["class_name"] for c in classes]
                 delete_target = st.selectbox("Select class to delete", class_opts, index=None, placeholder="Subject...", key="del_class_select")
                 if st.form_submit_button("Delete This Class"):
                     if delete_target:
                         try:
                             class_service.delete_class(delete_target)
                             st.session_state.admin_msg = ("success", f"Class '{delete_target}' deleted.")
                             st.rerun()
                         except Exception:
                             st.error("Failed to delete class.")

    st.divider()

    # Class Controls
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
             class_service.update_class_status(selected_class_name, True, opened_by=st.session_state.admin_username)
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
    admin_filter = None if st.session_state.admin_role == "superadmin" else st.session_state.admin_username

    # Add Teacher (Only Superadmin OR optionally allowed for HOD?)
    # For now, let's keep it restricted to Superadmin as requested "Principal can create HODs"
    # But the prompt says "admins who can then handle their respective teachers"
    # So HODs should be able to create teachers.
    
    with st.expander("➕ Add New Teacher"):
        with st.form("add_teacher_form"):
            new_t_user = st.text_input("Username")
            new_t_pass = st.text_input("Password", type="password")
            new_t_name = st.text_input("Full Name")
            if st.form_submit_button("Create Teacher"):
                success, msg = teacher_service.create_teacher(new_t_user, new_t_pass, new_t_name)
                if success:
                    # If an HOD creates a teacher, automatically assign it to them
                    if admin_filter:
                        admin_service.assign_teachers_to_admin(admin_filter, admin_service.get_admin_teachers(admin_filter) + [new_t_user])
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
    
    st.divider()
    
    # List & Edit Teachers
    teachers = teacher_service.get_all_teachers(admin_username=admin_filter)
    if not teachers:
        st.info("No teachers found.")
        return

    teacher_names = [t["username"] for t in teachers]
    selected_teacher = st.selectbox("Select Teacher to Manage", teacher_names)
    
    if selected_teacher:
        teacher_info = next(t for t in teachers if t["username"] == selected_teacher)
        st.write(f"**Name:** {teacher_info['full_name']}")
        
        # Assign Classes
        all_classes = [c["class_name"] for c in class_service.get_all_classes(admin_username=admin_filter)]
        assigned_classes = teacher_service.get_assigned_classes(selected_teacher)
        
        new_assignments = st.multiselect("Assign Classes", all_classes, default=[c for c in assigned_classes if c in all_classes])
        
        if st.button("💾 Update Assignments"):
            success, msg = teacher_service.assign_classes(selected_teacher, new_assignments)
            if success:
                st.success(msg)
            else:
                st.error(msg)

        st.markdown("---")
        if "confirm_delete_teacher" not in st.session_state:
            st.session_state.confirm_delete_teacher = False

        if not st.session_state.confirm_delete_teacher:
            if st.button("🗑️ Delete Teacher"):
                st.session_state.confirm_delete_teacher = True
                st.rerun()
        else:
            st.warning(f"⚠️ Are you sure you want to delete **{selected_teacher}**? This action cannot be undone.")
            col_conf_1, col_conf_2 = st.columns(2)
            with col_conf_1:
                if st.button("✅ Yes, Delete"):
                    if teacher_service.delete_teacher(selected_teacher):
                        st.success(f"Teacher '{selected_teacher}' deleted.")
                        st.session_state.confirm_delete_teacher = False
                        st.rerun()
            with col_conf_2:
                if st.button("❌ Cancel"):
                    st.session_state.confirm_delete_teacher = False
                    st.rerun()

def _render_manage_admins():
    st.subheader("🛡️ Admin (HOD) Management")
    
    # Create Admin
    with st.expander("➕ Create New Admin (HOD)"):
        with st.form("add_admin_form"):
            new_a_user = st.text_input("Username")
            new_a_pass = st.text_input("Password", type="password")
            if st.form_submit_button("Create Admin"):
                success, msg = admin_service.create_admin(new_a_user, new_a_pass)
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
    
    st.divider()
    
    # List Admins
    admins = admin_service.get_all_admins()
    # Filter out superadmins from management list
    hods = [a for a in admins if a["role"] == "admin"]
    
    if not hods:
        st.info("No HODs found.")
        return

    hod_names = [a["username"] for a in hods]
    selected_hod = st.selectbox("Select Admin to Manage", hod_names)
    
    if selected_hod:
        st.markdown(f"### Managing Assignments for `{selected_hod}`")
        
        # Assign Teachers
        all_teachers = [t["username"] for t in teacher_service.get_all_teachers()]
        assigned_teachers = admin_service.get_admin_teachers(selected_hod)
        
        new_t_assignments = st.multiselect("Assign Teachers", all_teachers, default=[t for t in assigned_teachers if t in all_teachers])
        
        if st.button("💾 Update Teacher Assignments"):
            success, msg = admin_service.assign_teachers_to_admin(selected_hod, new_t_assignments)
            if success: st.success(msg)
            else: st.error(msg)
            
        st.divider()
            
        # Assign Classes
        all_classes = [c["class_name"] for c in class_service.get_all_classes()]
        assigned_classes = admin_service.get_admin_classes(selected_hod)
        
        new_c_assignments = st.multiselect("Assign Classes", all_classes, default=[c for c in assigned_classes if c in all_classes])
        
        if st.button("💾 Update Class Assignments"):
            success, msg = admin_service.assign_classes_to_admin(selected_hod, new_c_assignments)
            if success: st.success(msg)
            else: st.error(msg)

        st.divider()
        if "confirm_delete_admin" not in st.session_state:
            st.session_state.confirm_delete_admin = False

        if not st.session_state.confirm_delete_admin:
            if st.button("🗑️ Delete Admin"):
                st.session_state.confirm_delete_admin = True
                st.rerun()
        else:
            st.warning(f"⚠️ Are you sure you want to delete admin **{selected_hod}**?")
            col_admin_conf_1, col_admin_conf_2 = st.columns(2)
            with col_admin_conf_1:
                if st.button("✅ Yes, Delete Admin"):
                    success, msg = admin_service.delete_admin(selected_hod)
                    if success:
                        st.session_state.confirm_delete_admin = False
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
            with col_admin_conf_2:
                if st.button("❌ Cancel Deletion"):
                    st.session_state.confirm_delete_admin = False
                    st.rerun()
