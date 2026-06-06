import os
import requests
import hashlib
import time
import sys
from datetime import datetime

sys.stdout.reconfigure(line_buffering=True)

print("="*80, flush=True)
print("🏆 أرشيف كرة القدم - رفع المباريات والفرق", flush=True)
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

# ========== 1. جلب الفرق الموجودة ==========
print("\n📥 [1/4] جلب الفرق الموجودة في Supabase...", flush=True)
resp = requests.get(f"{SUPABASE_URL}/teams?select=id,name", headers=headers)
existing_teams = {}
team_id_map = {}
if resp.status_code == 200:
    for team in resp.json():
        existing_teams[team["name"]] = team["id"]
        team_id_map[team["name"]] = team["id"]
print(f"   ✅ {len(existing_teams)} فريق موجود", flush=True)

# ========== 2. جلب الدوريات الموجودة ==========
print("\n📥 [2/4] جلب الدوريات الموجودة...", flush=True)
resp = requests.get(f"{SUPABASE_URL}/leagues?select=id,name", headers=headers)
leagues = {}
if resp.status_code == 200:
    for league in resp.json():
        leagues[league["name"]] = league["id"]
print(f"   ✅ {len(leagues)} دوري موجود", flush=True)

# تحديد معرف الدوري الإنجليزي
league_id = leagues.get("Premier League", 2021)

# ========== 3. جلب المباريات ==========
print("\n📥 [3/4] جلب المباريات من المصادر...", flush=True)

all_matches = []
new_teams = {}
team_counter = max(existing_teams.values()) if existing_teams else 1000

# قائمة المواسم
seasons_data = [
    ("https://www.football-data.co.uk/mmz4281/1516/E0.csv", "2015-16"),
    ("https://www.football-data.co.uk/mmz4281/1617/E0.csv", "2016-17"),
    ("https://www.football-data.co.uk/mmz4281/1718/E0.csv", "2017-18"),
    ("https://www.football-data.co.uk/mmz4281/1819/E0.csv", "2018-19"),
    ("https://www.football-data.co.uk/mmz4281/1920/E0.csv", "2019-20"),
    ("https://www.football-data.co.uk/mmz4281/2021/E0.csv", "2020-21"),
    ("https://www.football-data.co.uk/mmz4281/2122/E0.csv", "2021-22"),
    ("https://www.football-data.co.uk/mmz4281/2223/E0.csv", "2022-23"),
    ("https://www.football-data.co.uk/mmz4281/2324/E0.csv", "2023-24"),
    ("https://www.football-data.co.uk/mmz4281/2425/E0.csv", "2024-25"),
]

for url, season in seasons_data:
    print(f"   📥 موسم {season}...", flush=True)
    try:
        resp = requests.get(url, timeout=30)
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
                
                if not home_team or not away_team:
                    continue
                
                # إضافة فرق جديدة
                for team in [home_team, away_team]:
                    if team not in existing_teams and team not in new_teams:
                        team_counter += 1
                        new_teams[team] = team_counter
                
                home_id = existing_teams.get(home_team, new_teams.get(home_team))
                away_id = existing_teams.get(away_team, new_teams.get(away_team))
                
                if not home_id or not away_id:
                    continue
                
                match_id = hashlib.md5(f"{season}_{home_team}_{away_team}_{match_date}".encode()).hexdigest()
                
                all_matches.append({
                    "id": match_id,
                    "league_id": league_id,
                    "season": season,
                    "home_team_id": home_id,
                    "away_team_id": away_id,
                    "home_score": int(home_score) if home_score.isdigit() else 0,
                    "away_score": int(away_score) if away_score.isdigit() else 0,
                    "match_date": match_date,
                    "status": "finished"
                })
            
            print(f"      ✅ {len(lines)-1} مباراة", flush=True)
    except Exception as e:
        print(f"      ❌ خطأ: {str(e)[:50]}", flush=True)
    time.sleep(0.3)

print(f"\n   📊 إجمالي المباريات المجلوبة: {len(all_matches)}", flush=True)
print(f"   🆕 فرق جديدة: {len(new_teams)}", flush=True)

# ========== 4. رفع البيانات ==========
print("\n📤 [4/4] رفع البيانات إلى Supabase...", flush=True)

# رفع الفرق الجديدة
teams_list = []
for name, tid in new_teams.items():
    teams_list.append({
        "id": tid,
        "name": name,
        "short_name": name[:20],
        "league_id": league_id,
        "logo_url": None
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
        check = requests.get(f"{SUPABASE_URL}/matches?id=eq.{match['id']}", headers=headers)
        if check.status_code == 200 and check.json():
            match_uploaded += 1
            continue
        
        resp = requests.post(f"{SUPABASE_URL}/matches", headers=headers, json=match, timeout=10)
        if resp.status_code in [200, 201]:
            match_uploaded += 1
    except:
        pass
    
    if (i + 1) % 200 == 0:
        print(f"   ✅ تم رفع {i+1}/{len(all_matches)} مباراة (نجاح: {match_uploaded})", flush=True)
    time.sleep(0.01)

print(f"\n   ✅ تم رفع {match_uploaded}/{len(all_matches)} مباراة", flush=True)

# ========== النتيجة النهائية ==========
print("\n" + "="*80, flush=True)
print("🏆 اكتمل رفع البيانات!", flush=True)
print("="*80, flush=True)

# إحصائيات نهائية
resp = requests.get(f"{SUPABASE_URL}/teams?select=id", headers=headers)
teams_total = len(resp.json()) if resp.status_code == 200 else 0

resp = requests.get(f"{SUPABASE_URL}/matches?select=id", headers=headers)
matches_total = len(resp.json()) if resp.status_code == 200 else 0

print(f"\n📊 الوضع النهائي في Supabase:")
print(f"   ✅ الفرق (teams): {teams_total}")
print(f"   ✅ المباريات (matches): {matches_total}")
print("="*80, flush=True)
