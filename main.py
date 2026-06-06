import os
import requests
import hashlib
import time
import sys
import json

sys.stdout.reconfigure(line_buffering=True)

print("="*70, flush=True)
print("🏆 أرشيف كرة القدم - متوافق مع هيكل Supabase", flush=True)
print("="*70, flush=True)

SUPABASE_URL = "https://nugskdozmxlgrnkfsxlg.supabase.co/rest/v1"
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_KEY:
    print("❌ SUPABASE_KEY غير موجود!", flush=True)
    sys.exit(1)

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# ========== 1. جلب هيكل جميع الجداول ==========
print("\n📋 [1/4] جلب هيكل الجداول من Supabase...", flush=True)

tables = ["matches", "teams", "players", "stadiums", "coaches", "transfers"]
table_schemas = {}

for table in tables:
    print(f"   🔍 جدول: {table}", flush=True)
    try:
        # نجيب سجل واحد عشان نشوف الأعمدة
        resp = requests.get(f"{SUPABASE_URL}/{table}?limit=1", headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            if data:
                columns = list(data[0].keys())
                table_schemas[table] = columns
                print(f"      ✅ الأعمدة: {', '.join(columns[:5])}{'...' if len(columns) > 5 else ''}", flush=True)
            else:
                # الجدول فاضي، نجرب نضيف سجل تجريبي؟
                print(f"      ⚠️ الجدول فاضي - سنستخدم الهيكل الافتراضي", flush=True)
                table_schemas[table] = ["id", "name", "created_at"]  # افتراضي
        else:
            print(f"      ❌ فشل: {resp.status_code}", flush=True)
            table_schemas[table] = ["id", "name"]  # افتراضي
    except Exception as e:
        print(f"      ❌ خطأ: {str(e)[:50]}", flush=True)
        table_schemas[table] = ["id", "name"]  # افتراضي
    time.sleep(0.2)

# ========== 2. عرض الهيكل المستخدم ==========
print("\n📊 [2/4] الهيكل المعتمد:", flush=True)
for table, cols in table_schemas.items():
    print(f"   📁 {table}: {len(cols)} عمود", flush=True)

# ========== 3. جلب البيانات ==========
print("\n📥 [3/4] جلب البيانات من المصادر...", flush=True)

all_matches = []
all_teams = set()

# EPL data
urls = [
    ("https://www.football-data.co.uk/mmz4281/2425/E0.csv", "2024-25"),
    ("https://www.football-data.co.uk/mmz4281/2324/E0.csv", "2023-24"),
]

for url, season in urls:
    print(f"   📥 EPL {season}...", flush=True)
    try:
        resp = requests.get(url, timeout=20)
        if resp.status_code == 200:
            lines = resp.text.strip().split('\n')
            for line in lines[1:]:
                parts = line.split(',')
                if len(parts) >= 6:
                    home_score = parts[4].strip()
                    away_score = parts[5].strip()
                    
                    # بناء الكائن حسب الهيكل الموجود
                    match_obj = {}
                    if "id" in table_schemas.get("matches", []):
                        match_obj["id"] = hashlib.md5(f"{season}_{parts[2]}_{parts[3]}_{parts[0]}".encode()).hexdigest()
                    if "date" in table_schemas.get("matches", []):
                        match_obj["date"] = parts[0].strip()
                    if "home_team" in table_schemas.get("matches", []):
                        match_obj["home_team"] = parts[2].strip()
                    if "away_team" in table_schemas.get("matches", []):
                        match_obj["away_team"] = parts[3].strip()
                    if "home_score" in table_schemas.get("matches", []):
                        match_obj["home_score"] = int(home_score) if home_score.isdigit() else 0
                    if "away_score" in table_schemas.get("matches", []):
                        match_obj["away_score"] = int(away_score) if away_score.isdigit() else 0
                    if "league" in table_schemas.get("matches", []):
                        match_obj["league"] = "Premier League"
                    if "season" in table_schemas.get("matches", []):
                        match_obj["season"] = season
                    
                    all_matches.append(match_obj)
                    all_teams.add(parts[2].strip())
                    all_teams.add(parts[3].strip())
            print(f"      ✅ {len(lines)-1} مباراة", flush=True)
    except Exception as e:
        print(f"      ❌ خطأ: {str(e)[:50]}", flush=True)

# ========== 4. رفع البيانات ==========
print("\n📤 [4/4] رفع البيانات إلى Supabase...", flush=True)

def upsert_data(table, data_list):
    if not data_list:
        print(f"   ⚠️ لا توجد بيانات لـ {table}", flush=True)
        return 0
    
    inserted = 0
    total = len(data_list)
    print(f"   📤 رفع {total} سجل إلى {table}...", flush=True)
    
    for i, item in enumerate(data_list):
        try:
            # استخدام upsert مع تجاهل التكرار
            resp = requests.post(f"{SUPABASE_URL}/{table}", headers=headers, json=item, timeout=10)
            if resp.status_code in [200, 201]:
                inserted += 1
            elif resp.status_code == 409:
                inserted += 1  # مكرر، نعتبره نجاح
            else:
                if i < 5:  # نطبع أول 5 أخطاء فقط
                    print(f"      ⚠️ فشل سجل {i+1}: {resp.status_code}", flush=True)
        except Exception as e:
            if i < 5:
                print(f"      ❌ خطأ في سجل {i+1}: {str(e)[:50]}", flush=True)
        
        if (i + 1) % 100 == 0:
            print(f"      ✅ تم رفع {i+1}/{total}", flush=True)
        time.sleep(0.02)
    
    print(f"   ✅ تم رفع {inserted}/{total} إلى {table}", flush=True)
    return inserted

# رفع المباريات
if all_matches:
    match_count = upsert_data("matches", all_matches)
else:
    match_count = 0

# رفع الفرق
if all_teams:
    teams_list = []
    for team in all_teams:
        team_obj = {}
        if "id" in table_schemas.get("teams", []):
            team_obj["id"] = hashlib.md5(team.encode()).hexdigest()
        if "name" in table_schemas.get("teams", []):
            team_obj["name"] = team
        if "source" in table_schemas.get("teams", []):
            team_obj["source"] = "football-data.co.uk"
        teams_list.append(team_obj)
    
    team_count = upsert_data("teams", teams_list)
else:
    team_count = 0

# ========== النتيجة النهائية ==========
print("\n" + "="*70, flush=True)
print("🏆 اكتمل!", flush=True)
print("="*70, flush=True)
print(f"📊 المباريات المرفوعة: {match_count}")
print(f"📊 الفرق المرفوعة: {team_count}")
print("="*70, flush=True)
