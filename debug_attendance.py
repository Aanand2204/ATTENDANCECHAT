
from Attendence.core.clients import create_supabase_client
import pandas as pd

def check_db():
    supabase = create_supabase_client()
    try:
        # Fetch last 10 records
        response = supabase.table("attendance").select("*").order("created_at", desc=True).limit(10).execute()
        data = response.data
        if not data:
            print("No records found.")
            return
            
        df = pd.DataFrame(data)
        print("Recent Attendance Records:")
        # Check if 'teacher' column exists in columns
        if 'teacher' in df.columns:
            print(df[['class_name', 'roll_number', 'name', 'date', 'teacher']])
        else:
            print("Column 'teacher' does NOT exist in the returned data!")
            print(df.columns)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_db()
