import os
import requests
import json
from datetime import datetime

print("🔍 بدء فحص المخزن في Supabase...", flush=True)

SUPABASE_URL = "https://nugskdozmxlgrnkfsxlg.supabase.co/rest/v1"
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# قائمة الجداول اللي عندك
tables = [
    "teams", "players", "matches", "stadiums", "coaches", 
    "match_events", "match_stats", "match_lineups", "transfers",
    "player_injuries", "media_news", "league_standings", "api_logs"
]

print("\n" + "="*60)
print("📊 إحصائيات الجداول في Supabase:")
print("="*60)

total_records = 0

for table in tables:
    try:
        # Get count from each table
        url = f"{SUPABASE_URL}/{table}?select=id&limit=0"
        resp = requests.get(url, headers=headers)
        
        # Try to get count from header or by counting
        count_url = f"{SUPABASE_URL}/{table}?select=id"
        count_resp = requests.get(count_url, headers=headers)
        
        if count_resp.status_code == 200:
            data = count_resp.json()
            count = len(data)
            total_records += count
            print(f"   📌 {table}: {count} سجل")
        else:
            print(f"   ❌ {table}: فشل ({count_resp.status_code})")
            
    except Exception as e:
        print(f"   ⚠️ {table}: خطأ - {str(e)[:30]}")

print("="*60)
print(f"📊 إجمالي السجلات: {total_records}")
print("="*60)

# عرض عينة من كل جدول
print("\n📋 عينات من الجداول (أول 3 سجلات لكل جدول):")
print("="*60)

for table in tables:
    try:
        url = f"{SUPABASE_URL}/{table}?select=*&limit=3"
        resp = requests.get(url, headers=headers)
        
        if resp.status_code == 200:
            data = resp.json()
            if data:
                print(f"\n📁 {table}:")
                for item in data:
                    # Show first 3 fields only
                    preview = {k: str(v)[:40] for k, v in list(item.items())[:3]}
                    print(f"   → {json.dumps(preview, ensure_ascii=False)}")
            else:
                print(f"\n📁 {table}: (فارغ)")
    except Exception as e:
        print(f"\n📁 {table}: خطأ - {str(e)[:30]}")

print("\n" + "="*60)
print("✅ اكتمل الفحص")
print("="*60)
