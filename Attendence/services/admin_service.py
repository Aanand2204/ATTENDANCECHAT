# Attendence/services/admin_service.py
import streamlit as st
from Attendence.core.clients import create_supabase_client
from Attendence.core.logger import get_logger

logger = get_logger(__name__)

def create_admin(username, password, role="admin", supabase=None):
    if not supabase:
        supabase = create_supabase_client()
    try:
        # Check if exists
        exists = supabase.table("admins").select("username").eq("username", username).execute().data
        if exists:
            return False, "Admin already exists."
        
        supabase.table("admins").insert({
            "username": username,
            "password": password,
            "role": role
        }).execute()
        get_all_admins.clear()
        return True, f"Admin '{username}' created."
    except Exception as e:
        logger.exception(f"Failed to create admin {username}")
        return False, str(e)

def delete_admin(username, supabase=None):
    if not supabase:
        supabase = create_supabase_client()
    try:
        supabase.table("admins").delete().eq("username", username).execute()
        get_all_admins.clear()
        return True, f"Admin '{username}' deleted."
    except Exception as e:
        logger.exception(f"Failed to delete admin {username}")
        return False, str(e)

@st.cache_data(ttl=60)
def get_all_admins(supabase=None):
    if not supabase:
        supabase = create_supabase_client()
    try:
        response = supabase.table("admins").select("*").execute()
        return response.data if response.data else []
    except Exception:
        logger.exception("Failed to fetch admins")
        return []

def assign_teachers_to_admin(admin_username, teacher_usernames, supabase=None):
    if not supabase:
        supabase = create_supabase_client()
    try:
        # Remove old assignments
        supabase.table("admin_teachers").delete().eq("admin_username", admin_username).execute()
        
        # Add new ones
        if teacher_usernames:
            data = [{"admin_username": admin_username, "teacher_username": t} for t in teacher_usernames]
            supabase.table("admin_teachers").insert(data).execute()
        
        get_admin_teachers.clear()
        return True, "Teacher assignments updated."
    except Exception as e:
        logger.exception(f"Failed to assign teachers to {admin_username}")
        return False, str(e)

def assign_classes_to_admin(admin_username, class_names, supabase=None):
    if not supabase:
        supabase = create_supabase_client()
    try:
        # Remove old assignments
        supabase.table("admin_classes").delete().eq("admin_username", admin_username).execute()
        
        # Add new ones
        if class_names:
            data = [{"admin_username": admin_username, "class_name": c} for c in class_names]
            supabase.table("admin_classes").insert(data).execute()
        
        get_admin_classes.clear()
        return True, "Class assignments updated."
    except Exception as e:
        logger.exception(f"Failed to assign classes to {admin_username}")
        return False, str(e)

@st.cache_data(ttl=60)
def get_admin_teachers(admin_username, supabase=None):
    if not supabase:
        supabase = create_supabase_client()
    try:
        response = supabase.table("admin_teachers").select("teacher_username").eq("admin_username", admin_username).execute()
        return [r["teacher_username"] for r in response.data] if response.data else []
    except Exception:
        logger.exception(f"Failed to fetch teachers for admin {admin_username}")
        return []

@st.cache_data(ttl=60)
def get_admin_classes(admin_username, supabase=None):
    if not supabase:
        supabase = create_supabase_client()
    try:
        response = supabase.table("admin_classes").select("class_name").eq("admin_username", admin_username).execute()
        return [r["class_name"] for r in response.data] if response.data else []
    except Exception:
        logger.exception(f"Failed to fetch classes for admin {admin_username}")
        return []
