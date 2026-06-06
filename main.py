import os
import requests
import hashlib
import time
import sys
import re
from datetime import datetime, timedelta

sys.stdout.reconfigure(line_buffering=True)

print("="*80, flush=True)
print("🏆 السكربت النهائي - أرشيف كامل + بيانات حديثة", flush=True)
print("="*80, flush=True)

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

# ========== 1. معرفة هيكل الجدول ==========
print("\n🔍 [1/5] اكتشاف هيكل جدول matches...", flush=True)

required_columns = {}
test_match = {"id": "test_cols_123"}
resp = requests.post(f"{SUPABASE_URL}/matches", headers=headers, json=test_match, timeout=5)

if resp.status_code == 400:
    missing = re.findall(r"'(\w+)' column", resp.text)
    for col in missing:
        required_columns[col] = "text"
    
    # كشف أنواع الأعمدة
    type_hints = re.findall(r"invalid input syntax for type (\w+):", resp.text)
    print(f"   ✅ الأعمدة المطلوبة: {len(required_columns)} عمود", flush=True)

if not required_columns:
    required_columns = {
        "id": "text", "home_team": "text", "away_team": "text",
        "home_score": "integer", "away_score": "integer", 
        "match_date": "text", "season": "text"
    }
    print(f"   ⚠️ استخدام الأعمدة الافتراضية", flush=True)

# ========== 2. جلب الفرق الموجودة ==========
print("\n📥 [2/5] جلب الفرق الموجودة...", flush=True)
resp = requests.get(f"{SUPABASE_URL}/teams?select=id,name", headers=headers)
existing_teams = {team["name"]: team["id"] for team in resp.json()} if resp.status_code == 200 else {}
print(f"   ✅ {len(existing_teams)} فريق موجود", flush=True)

# ========== 3. جلب البيانات القديمة (أرشيف 2015-2024) ==========
print("\n📥 [3/5] جلب الأرشيف القديم (2015-2024)...", flush=True)

all_matches = []
new_teams = {}
team_counter = max(existing_teams.values()) if existing_teams else 1000

# مواسم قديمة
old_seasons = [
    ("https://www.football-data.co.uk/mmz4281/1516/E0.csv", "2015-16"),
    ("https://www.football-data.co.uk/mmz4281/1617/E0.csv", "2016-17"),
    ("https://www.football-data.co.uk/mmz4281/1718/E0.csv", "2017-18"),
    ("https://www.football-data.co.uk/mmz4281/1819/E0.csv", "2018-19"),
    ("https://www.football-data.co.uk/mmz4281/1920/E0.csv", "2019-20"),
    ("https://www.football-data.co.uk/mmz4281/2021/E0.csv", "2020-21"),
    ("https://www.football-data.co.uk/mmz4281/2122/E0.csv", "2021-22"),
    ("https://www.football-data.co.uk/mmz4281/2223/E0.csv", "2022-23"),
    ("https://www.football-data.co.uk/mmz4281/2324/E0.csv", "2023-24"),
]

for url, season in old_seasons:
    print(f"   📥 موسم {season}...", flush=True)
    try:
        resp = requests.get(url, timeout=20)
        if resp.status_code == 200:
            lines = resp.text.strip().split('\n')
            for line in lines[1:]:
                parts = line.split(',')
                if len(parts) < 6:
                    continue
                
                home_team = parts[2].strip()
                away_team = parts[3].strip()
                home_score = parts[4].strip()
                away_score = parts[5].strip()
                match_date = parts[0].strip()
                
                # إضافة فرق جديدة
                for team in [home_team, away_team]:
                    if team not in existing_teams and team not in new_teams:
                        team_counter += 1
                        new_teams[team] = team_counter
                
                # بناء كائن المباراة
                match_obj = {"id": hashlib.md5(f"{season}_{home_team}_{away_team}_{match_date}".encode()).hexdigest()}
                
                for col, col_type in required_columns.items():
                    if col == "home_team":
                        match_obj[col] = home_team
                    elif col == "away_team":
                        match_obj[col] = away_team
                    elif col == "home_score":
                        match_obj[col] = int(home_score) if home_score.isdigit() else 0
                    elif col == "away_score":
                        match_obj[col] = int(away_score) if away_score.isdigit() else 0
                    elif col in ["date", "match_date"]:
                        match_obj[col] = match_date
                    elif col == "season":
                        match_obj[col] = season
                
                all_matches.append(match_obj)
            
            print(f"      ✅ {len(lines)-1} مباراة", flush=True)
    except Exception as e:
        print(f"      ❌ خطأ: {str(e)[:50]}", flush=True)
    time.sleep(0.3)

# ========== 4. جلب البيانات الحديثة (مباريات اليوم والقادمة) ==========
print("\n📥 [4/5] جلب البيانات الحديثة (مباريات اليوم)...", flush=True)

today = datetime.now().strftime('%Y-%m-%d')
next_week = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')

# محاولة جلب مباريات اليوم من مصدر بديل
try:
    # استخدام football-data.co.uk للموسم الحالي
    url = "https://www.football-data.co.uk/mmz4281/2425/E0.csv"
    resp = requests.get(url, timeout=20)
    if resp.status_code == 200:
        lines = resp.text.strip().split('\n')
        future_matches = []
        
        for line in lines[1:]:
            parts = line.split(',')
            if len(parts) < 6:
                continue
            
            match_date = parts[0].strip()
            # جلب مباريات من اليوم أو الأسبوع القادم
            if match_date >= today and match_date <= next_week:
                home_team = parts[2].strip()
                away_team = parts[3].strip()
                
                match_obj = {"id": hashlib.md5(f"future_{match_date}_{home_team}_{away_team}".encode()).hexdigest()}
                
                for col, col_type in required_columns.items():
                    if col == "home_team":
                        match_obj[col] = home_team
                    elif col == "away_team":
                        match_obj[col] = away_team
                    elif col in ["date", "match_date"]:
                        match_obj[col] = match_date
                    elif col == "status":
                        match_obj[col] = "scheduled"
                    elif col == "season":
                        match_obj[col] = "2024-25"
                
                future_matches.append(match_obj)
                all_matches.append(match_obj)
        
        print(f"   ✅ مباريات اليوم والأسبوع القادم: {len(future_matches)}", flush=True)
except Exception as e:
    print(f"   ⚠️ لم نتمكن من جلب المباريات الحديثة: {str(e)[:50]}", flush=True)

print(f"\n   📊 إجمالي المباريات المجلوبة: {len(all_matches)}", flush=True)
print(f"   🆕 فرق جديدة: {len(new_teams)}", flush=True)

# ========== 5. رفع البيانات ==========
print("\n📤 [5/5] رفع البيانات إلى Supabase...", flush=True)

# رفع الفرق الجديدة
teams_list = []
for name, tid in new_teams.items():
    teams_list.append({
        "id": tid,
        "name": name,
        "short_name": name[:20],
        "league_id": 2021
    })

team_uploaded = 0
for team in teams_list:
    try:
        check = requests.get(f"{SUPABASE_URL}/teams?id=eq.{team['id']}", headers=headers)
        if check.status_code == 200 and check.json():
            continue
        resp = requests.post(f"{SUPABASE_URL}/teams", headers=headers, json=team, timeout=10)
        if resp.status_code in [200, 201]:
            team_uploaded += 1
    except:
        pass
    time.sleep(0.02)

print(f"   ✅ تم رفع {team_uploaded}/{len(teams_list)} فريق جديد", flush=True)

# رفع المباريات
match_uploaded = 0
for i, match in enumerate(all_matches):
    try:
        # التحقق من الوجود
        check = requests.get(f"{SUPABASE_URL}/matches?id=eq.{match['id']}", headers=headers)
        if check.status_code == 200 and check.json():
            match_uploaded += 1
            continue
        
        resp = requests.post(f"{SUPABASE_URL}/matches", headers=headers, json=match, timeout=10)
        if resp.status_code in [200, 201]:
            match_uploaded += 1
        elif resp.status_code == 409:
            match_uploaded += 1
    except Exception as e:
        pass
    
    if (i + 1) % 200 == 0:
        print(f"   ✅ تم رفع {i+1}/{len(all_matches)} مباراة (نجاح: {match_uploaded})", flush=True)
    time.sleep(0.01)

print(f"   ✅ تم رفع {match_uploaded}/{len(all_matches)} مباراة", flush=True)

# ========== النتيجة النهائية ==========
print("\n" + "="*80, flush=True)
print("🏆 اكتمل الأرشيف!", flush=True)
print("="*80, flush=True)

# إحصائيات نهائية
resp = requests.get(f"{SUPABASE_URL}/teams?select=id", headers=headers)
teams_total = len(resp.json()) if resp.status_code == 200 else 0

resp = requests.get(f"{SUPABASE_URL}/matches?select=id", headers=headers)
matches_total = len(resp.json()) if resp.status_code == 200 else 0

print(f"\n📊 الوضع النهائي في Supabase:")
print(f"   ✅ الفرق (teams): {teams_total} (+{team_uploaded})")
print(f"   ✅ المباريات (matches): {matches_total} (+{match_uploaded})")
print(f"\n📅 التغطية الزمنية: 2015-16 إلى 2024-25 + مباريات الأسبوع القادم")
print("="*80, flush=True)
