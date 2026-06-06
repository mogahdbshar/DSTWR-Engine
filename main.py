import os
import requests
import hashlib
import time
from datetime import datetime
import sys

sys.stdout.reconfigure(line_buffering=True)

print("="*70, flush=True)
print("🏆 أرشيف كرة القدم - المصادر الموثوقة فقط", flush=True)
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

def upsert_to_supabase(table, data_list):
    if not data_list:
        return 0
    inserted = 0
    for i in range(0, len(data_list), 50):
        batch = data_list[i:i+50]
        try:
            h = headers.copy()
            h["Prefer"] = "resolution=merge-duplicates,return=minimal"
            resp = requests.post(f"{SUPABASE_URL}/{table}", headers=h, json=batch, timeout=30)
            if resp.status_code in [200, 201]:
                inserted += len(batch)
                print(f"   ✅ رفع {len(batch)} إلى {table}", flush=True)
        except Exception as e:
            print(f"   ❌ خطأ: {str(e)[:50]}", flush=True)
        time.sleep(0.1)
    return inserted

all_matches = []
all_teams = set()

# ========== 1. كأس العالم 2018 ==========
print("\n📥 [1/3] كأس العالم 2018...", flush=True)
url = "https://raw.githubusercontent.com/openfootball/worldcup.json/master/2018/worldcup.json"
try:
    resp = requests.get(url, timeout=15)
    if resp.status_code == 200:
        data = resp.json()
        count = 0
        for r in data.get("rounds", []):
            for m in r.get("matches", []):
                count += 1
                mid = f"wc_2018_{m.get('num', count)}"
                all_matches.append({
                    "id": mid, "date": m.get("date"),
                    "home_team": m.get("team1", {}).get("name"),
                    "away_team": m.get("team2", {}).get("name"),
                    "home_score": m.get("score1"), "away_score": m.get("score2"),
                    "league": "World Cup 2018", "season": 2018,
                    "stadium": m.get("stadium")
                })
                all_teams.add(m.get("team1", {}).get("name"))
                all_teams.add(m.get("team2", {}).get("name"))
        print(f"   ✅ {count} مباراة", flush=True)
except Exception as e:
    print(f"   ❌ خطأ: {str(e)[:50]}", flush=True)

# ========== 2. كأس العالم 2022 ==========
print("\n📥 [2/3] كأس العالم 2022...", flush=True)
url = "https://raw.githubusercontent.com/openfootball/worldcup.json/master/2022/worldcup.json"
try:
    resp = requests.get(url, timeout=15)
    if resp.status_code == 200:
        data = resp.json()
        count = 0
        for r in data.get("rounds", []):
            for m in r.get("matches", []):
                count += 1
                mid = f"wc_2022_{m.get('num', count)}"
                all_matches.append({
                    "id": mid, "date": m.get("date"),
                    "home_team": m.get("team1", {}).get("name"),
                    "away_team": m.get("team2", {}).get("name"),
                    "home_score": m.get("score1"), "away_score": m.get("score2"),
                    "league": "World Cup 2022", "season": 2022,
                    "stadium": m.get("stadium")
                })
                all_teams.add(m.get("team1", {}).get("name"))
                all_teams.add(m.get("team2", {}).get("name"))
        print(f"   ✅ {count} مباراة", flush=True)
except Exception as e:
    print(f"   ❌ خطأ: {str(e)[:50]}", flush=True)

# ========== 3. بيانات إضافية من football-data.co.uk ==========
print("\n📥 [3/3] بيانات إضافية (الدوري الإنجليزي)...", flush=True)

# محاولة جلب من football-data.co.uk (بديل)
urls = [
    ("https://www.football-data.co.uk/mmz4281/2425/E0.csv", "EPL 2024-25"),
    ("https://www.football-data.co.uk/mmz4281/2324/E0.csv", "EPL 2023-24"),
]

for url, name in urls:
    try:
        print(f"   📥 {name}...", flush=True)
        resp = requests.get(url, timeout=20)
        if resp.status_code == 200:
            lines = resp.text.strip().split('\n')
            for line in lines[1:]:
                parts = line.split(',')
                if len(parts) >= 6:
                    mid = hashlib.md5(f"{parts[0]}_{parts[1]}_{parts[2]}".encode()).hexdigest()
                    all_matches.append({
                        "id": mid, "date": parts[0],
                        "home_team": parts[2], "away_team": parts[3],
                        "home_score": int(parts[4]) if parts[4].isdigit() else None,
                        "away_score": int(parts[5]) if parts[5].isdigit() else None,
                        "league": name, "season": name.split()[1]
                    })
                    all_teams.add(parts[2]); all_teams.add(parts[3])
            print(f"      ✅ {len(lines)-1} مباراة", flush=True)
        else:
            print(f"      ⚠️ HTTP {resp.status_code}", flush=True)
    except Exception as e:
        print(f"      ❌ {str(e)[:50]}", flush=True)
    time.sleep(0.5)

# ========== الرفع ==========
print("\n" + "="*70, flush=True)
print("📤 رفع البيانات إلى Supabase...", flush=True)
print("="*70, flush=True)

if all_matches:
    count = upsert_to_supabase("matches", all_matches)
    print(f"\n✅ تم رفع {count} مباراة", flush=True)

if all_teams:
    teams_list = [{"id": hashlib.md5(t.encode()).hexdigest(), "name": t} for t in all_teams]
    count = upsert_to_supabase("teams", teams_list)
    print(f"✅ تم رفع {count} فريق", flush=True)

print("\n" + "="*70, flush=True)
print("🏆 اكتمل!", flush=True)
print(f"📊 إجمالي المباريات: {len(all_matches)}")
print(f"📊 إجمالي الفرق: {len(all_teams)}")
print("="*70, flush=True)
