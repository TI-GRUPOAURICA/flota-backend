import os
import requests
from dotenv import load_dotenv

load_dotenv("c:/Users/Leonar/OneDrive - ylsolutionsperu.com/YL SOLUTIONS/GRUPO AURICA/Proyectos/FlotaVechicular/flota-backend/.env")

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()

def supabase_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

res = requests.get(f"{SUPABASE_URL}/rest/v1/vehiculos?limit=1", headers=supabase_headers())
print(res.status_code)
print(res.json())
