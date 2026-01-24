# Attendence/services/auth_service.py
from Attendence.core.config import get_env


def authenticate_admin(username, password):
    """
    Verifies admin credentials against the Supabase 'admins' table.
    """
    from Attendence.core.clients import create_supabase_client
    supabase = create_supabase_client()
    try:
        response = supabase.table("admins").select("password").eq("username", username).execute()
        if response.data:
            # In a real app, use hashing!
            return response.data[0]["password"] == password
    except Exception:
        pass
    return False

def authenticate_teacher(username, password):
    """
    Verifies teacher credentials against the database.
    """
    from Attendence.core.clients import create_supabase_client
    supabase = create_supabase_client()
    try:
        response = supabase.table("teachers").select("password").eq("username", username).execute()
        if response.data:
            # In a real app, use hashing!
            return response.data[0]["password"] == password
    except Exception:
        pass
    return False
