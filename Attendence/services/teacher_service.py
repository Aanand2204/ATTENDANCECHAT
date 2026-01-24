import streamlit as st
from Attendence.core.clients import create_supabase_client
from Attendence.core.logger import get_logger

logger = get_logger(__name__)

def create_teacher(username, password, full_name, supabase=None):
    if not supabase:
        supabase = create_supabase_client()
    try:
        # Check if exists
        exists = supabase.table("teachers").select("username").eq("username", username).execute().data
        if exists:
            return False, "Teacher already exists."
        
        supabase.table("teachers").insert({
            "username": username,
            "password": password,
            "full_name": full_name
        }).execute()
        get_all_teachers.clear()
        return True, f"Teacher '{username}' created."
    except Exception as e:
        logger.exception(f"Failed to create teacher {username}")
        return False, str(e)

def delete_teacher(username, supabase=None):
    if not supabase:
        supabase = create_supabase_client()
    try:
        supabase.table("teachers").delete().eq("username", username).execute()
        # Cascade delete should handle teacher_classes, but we can be explicit if needed
        # supabase.table("teacher_classes").delete().eq("teacher_username", username).execute()
        get_all_teachers.clear()
        return True, f"Teacher '{username}' deleted."
    except Exception as e:
        logger.exception(f"Failed to delete teacher {username}")
        return False, str(e)

@st.cache_data(ttl=60)
def get_all_teachers(supabase=None):
    if not supabase:
        supabase = create_supabase_client()
    try:
        response = supabase.table("teachers").select("*").execute()
        return response.data if response.data else []
    except Exception:
        logger.exception("Failed to fetch teachers")
        return []

def assign_classes(username, class_names, supabase=None):
    """
    Overwrites the assigned classes for a teacher.
    """
    if not supabase:
        supabase = create_supabase_client()
    try:
        # First remove all existing assignments
        supabase.table("teacher_classes").delete().eq("teacher_username", username).execute()
        
        # Add new assignments
        if class_names:
            data = [{"teacher_username": username, "class_name": c} for c in class_names]
            supabase.table("teacher_classes").insert(data).execute()
        
        get_assigned_classes.clear()
        return True, "Assignments updated."
    except Exception as e:
        logger.exception(f"Failed to assign classes to {username}")
        return False, str(e)

@st.cache_data(ttl=60)
def get_assigned_classes(username, supabase=None):
    if not supabase:
        supabase = create_supabase_client()
    try:
        response = supabase.table("teacher_classes").select("class_name").eq("teacher_username", username).execute()
        return [r["class_name"] for r in response.data] if response.data else []
    except Exception:
        logger.exception(f"Failed to fetch assigned classes for {username}")
        return []
