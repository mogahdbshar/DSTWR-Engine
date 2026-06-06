import os
import requests
import hashlib
import time
import sys

sys.stdout.reconfigure(line_buffering=True)

print("="*80, flush=True)
print("🏆 رفع المباريات - حل نهائي", flush=True)
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

# ========== جلب الفرق ==========
print("\n📥 جلب الفرق...", flush=True)
resp = requests.get(f"{SUPABASE_URL}/teams?select=id,name", headers=headers)
teams = {}
if resp.status_code == 200:
    for team in resp.json():
        teams[team["name"]] = team["id"]
print(f"   ✅ {len(teams)} فريق", flush=True)

# ========== جلب المباريات ==========
print("\n📥 جلب المباريات...", flush=True)

all_matches = []
seasons = [
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
    ("https://www.football-data.co.uk/mmz4281/2526/E0.csv", "2025-26"),
]

for url, season in seasons:
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
                
                home_id = teams.get(home_team)
                away_id = teams.get(away_team)
                
                if home_id and away_id:
                    match_id = hashlib.md5(f"{season}_{home_team}_{away_team}_{match_date}".encode()).hexdigest()
                    all_matches.append({
                        "id": match_id,
                        "league_id": 2021,
                        "season": season,
                        "home_team_id": home_id,
                        "away_team_id": away_id,
                        "home_score": int(home_score) if home_score.isdigit() else 0,
                        "away_score": int(away_score) if away_score.isdigit() else 0,
                        "match_date": match_date,
                        "status": "finished",
                        "season_year": int(season.split('-')[1]) + 2000
                    })
            print(f"      ✅ {len(lines)-1} مباراة", flush=True)
    except Exception as e:
        print(f"      ❌ خطأ: {str(e)[:50]}", flush=True)
    time.sleep(0.5)

print(f"\n   📊 إجمالي المباريات: {len(all_matches)}", flush=True)

# ========== رفع المباريات باستخدام upsert ==========
print("\n📤 رفع المباريات (upsert)...", flush=True)

uploaded = 0
headers_upsert = headers.copy()
headers_upsert["Prefer"] = "resolution=merge-duplicates"

for i in range(0, len(all_matches), 100):
    batch = all_matches[i:i+100]
    try:
        # استخدام upsert لتجنب التكرار
        resp = requests.post(f"{SUPABASE_URL}/matches", headers=headers_upsert, json=batch, timeout=30)
        if resp.status_code in [200, 201]:
            uploaded += len(batch)
            print(f"   ✅ رفع دفعة {i//100 + 1}/{(len(all_matches)+99)//100} ({len(batch)} مباراة)", flush=True)
        else:
            print(f"   ❌ فشل الدفعة {i//100 + 1}: {resp.status_code}", flush=True)
            print(f"      السبب: {resp.text[:200]}", flush=True)
    except Exception as e:
        print(f"   ❌ خطأ في الدفعة {i//100 + 1}: {str(e)}", flush=True)
    time.sleep(0.5)

print(f"\n   ✅ تم رفع {uploaded}/{len(all_matches)} مباراة", flush=True)

# ========== النتيجة ==========
print("\n" + "="*80, flush=True)
print("🏆 اكتمل!", flush=True)
print("="*80, flush=True)

resp = requests.get(f"{SUPABASE_URL}/matches?select=id", headers=headers)
matches_total = len(resp.json()) if resp.status_code == 200 else 0
print(f"📊 المباريات في Supabase: {matches_total}")
print("="*80, flush=True)
