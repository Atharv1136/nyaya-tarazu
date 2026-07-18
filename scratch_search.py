import os
from dotenv import load_dotenv
from supabase import create_client

ROOT_ENV = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(ROOT_ENV)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    res_old = supabase.table("legal_sections").select("chunk_id", count="exact").eq("code_era", "old").limit(1).execute()
    print("Old code sections count:", res_old.count)
except Exception as e:
    print("Failed to count old:", e)

try:
    res_new = supabase.table("legal_sections").select("chunk_id", count="exact").eq("code_era", "new").limit(1).execute()
    print("New code sections count:", res_new.count)
except Exception as e:
    print("Failed to count new:", e)
