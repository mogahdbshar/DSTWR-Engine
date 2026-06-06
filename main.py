import os
import requests
import json
import hashlib
import time
from datetime import datetime
import sys

sys.stdout.reconfigure(line_buffering=True)

print("="*70, flush=True)
print("🏆 الأرشيف الشامل لكرة القدم - كل المصادر مرة واحدة", flush=True)
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

# ========== كل المباريات من كل المصادر ==========
all_matches = []
all_teams = set()

# 1. jokecamp/FootballData - EPL من 2015 إلى 2019
print("\n📥 [1/6] EPL (jokecamp)...", flush=True)
for year in range(2015, 2020):
    url = f"https://raw.githubusercontent.com/jokecamp/FootballData/master/data/EPL/{year}-{year+1}/{year}-{year+1}_PL_Results.csv"
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            lines = resp.text.strip().split('\n')
            for line in lines[1:]:
                parts = line.split(',')
                if len(parts) >= 5:
                    mid = hashlib.md5(f"{parts[0]}_{parts[1]}_{parts[2]}".encode()).hexdigest()
                    all_matches.append({
                        "id": mid, "date": parts[0],
                        "home_team": parts[1], "away_team": parts[2],
                        "home_score": int(parts[3]) if parts[3].isdigit() else None,
                        "away_score": int(parts[4]) if parts[4].isdigit() else None,
                        "league": "EPL", "season": year
                    })
                    all_teams.add(parts[1]); all_teams.add(parts[2])
            print(f"   ✅ {year}-{year+1}: {len(lines)-1} مباراة", flush=True)
    except: pass
    time.sleep(0.3)

# 2. كأس العالم (2010-2026)
print("\n📥 [2/6] كأس العالم...", flush=True)
for year in [2010, 2014, 2018, 2022, 2026]:
    url = f"https://raw.githubusercontent.com/openfootball/worldcup.json/master/{year}/worldcup.json"
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            count = 0
            for r in data.get("rounds", []):
                for m in r.get("matches", []):
                    count += 1
                    mid = f"wc_{year}_{m.get('num', count)}"
                    all_matches.append({
                        "id": mid, "date": m.get("date"),
                        "home_team": m.get("team1", {}).get("name"),
                        "away_team": m.get("team2", {}).get("name"),
                        "home_score": m.get("score1"), "away_score": m.get("score2"),
                        "league": f"World Cup {year}", "season": year,
                        "stadium": m.get("stadium")
                    })
                    all_teams.add(m.get("team1", {}).get("name"))
                    all_teams.add(m.get("team2", {}).get("name"))
            print(f"   ✅ {year}: {count} مباراة", flush=True)
    except: pass
    time.sleep(0.3)

# 3. engsoccerdata (تاريخ إنجلترا)
print("\n📥 [3/6] التاريخ الإنجليزي (1888-2016)...", flush=True)
try:
    resp = requests.get("https://raw.githubusercontent.com/jalapic/engsoccerdata/master/data-raw/engsoccerdata2.csv", timeout=30)
    if resp.status_code == 200:
        lines = resp.text.strip().split('\n')
        for line in lines[1:5000]:
            parts = line.split(',')
            if len(parts) >= 6:
                mid = hashlib.md5(f"{parts[0]}_{parts[2]}_{parts[3]}_{parts[1]}".encode()).hexdigest()
                all_matches.append({
                    "id": mid, "date": parts[0], "season": parts[1],
                    "home_team": parts[2], "away_team": parts[3],
                    "home_score": int(parts[4]) if parts[4].isdigit() else None,
                    "away_score": int(parts[5]) if parts[5].isdigit() else None,
                    "league": "England", "tier": parts[6] if len(parts) > 6 else None
                })
                all_teams.add(parts[2]); all_teams.add(parts[3])
        print(f"   ✅ {len(lines)-1} مباراة تاريخية", flush=True)
except: pass

# 4. La Liga (الدوري الإسباني)
print("\n📥 [4/6] La Liga...", flush=True)
for year in range(2015, 2020):
    url = f"https://raw.githubusercontent.com/jokecamp/FootballData/master/data/La_Liga/{year}-{year+1}/{year}-{year+1}_La_Liga.csv"
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            lines = resp.text.strip().split('\n')
            for line in lines[1:]:
                parts = line.split(',')
                if len(parts) >= 5:
                    mid = hashlib.md5(f"laliga_{parts[0]}_{parts[1]}_{parts[2]}".encode()).hexdigest()
                    all_matches.append({
                        "id": mid, "date": parts[0],
                        "home_team": parts[1], "away_team": parts[2],
                        "home_score": int(parts[3]) if parts[3].isdigit() else None,
                        "away_score": int(parts[4]) if parts[4].isdigit() else None,
                        "league": "La Liga", "season": year
                    })
                    all_teams.add(parts[1]); all_teams.add(parts[2])
            print(f"   ✅ {year}-{year+1}: {len(lines)-1} مباراة", flush=True)
    except: pass
    time.sleep(0.3)

# 5. Bundesliga (الدوري الألماني)
print("\n📥 [5/6] Bundesliga...", flush=True)
for year in range(2015, 2020):
    url = f"https://raw.githubusercontent.com/jokecamp/FootballData/master/data/Bundesliga/{year}-{year+1}/{year}-{year+1}_Bundesliga.csv"
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            lines = resp.text.strip().split('\n')
            for line in lines[1:]:
                parts = line.split(',')
                if len(parts) >= 5:
                    mid = hashlib.md5(f"bundesliga_{parts[0]}_{parts[1]}_{parts[2]}".encode()).hexdigest()
                    all_matches.append({
                        "id": mid, "date": parts[0],
                        "home_team": parts[1], "away_team": parts[2],
                        "home_score": int(parts[3]) if parts[3].isdigit() else None,
                        "away_score": int(parts[4]) if parts[4].isdigit() else None,
                        "league": "Bundesliga", "season": year
                    })
                    all_teams.add(parts[1]); all_teams.add(parts[2])
            print(f"   ✅ {year}-{year+1}: {len(lines)-1} مباراة", flush=True)
    except: pass
    time.sleep(0.3)

# 6. Serie A (الدوري الإيطالي)
print("\n📥 [6/6] Serie A...", flush=True)
for year in range(2015, 2020):
    url = f"https://raw.githubusercontent.com/jokecamp/FootballData/master/data/Serie_A/{year}-{year+1}/{year}-{year+1}_Serie_A.csv"
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            lines = resp.text.strip().split('\n')
            for line in lines[1:]:
                parts = line.split(',')
                if len(parts) >= 5:
                    mid = hashlib.md5(f"seriea_{parts[0]}_{parts[1]}_{parts[2]}".encode()).hexdigest()
                    all_matches.append({
                        "id": mid, "date": parts[0],
                        "home_team": parts[1], "away_team": parts[2],
                        "home_score": int(parts[3]) if parts[3].isdigit() else None,
                        "away_score": int(parts[4]) if parts[4].isdigit() else None,
                        "league": "Serie A", "season": year
                    })
                    all_teams.add(parts[1]); all_teams.add(parts[2])
            print(f"   ✅ {year}-{year+1}: {len(lines)-1} مباراة", flush=True)
    except: pass
    time.sleep(0.3)

# ========== الرفع إلى Supabase ==========
print("\n" + "="*70, flush=True)
print("📤 رفع البيانات إلى Supabase...", flush=True)
print("="*70, flush=True)

# رفع المباريات
if all_matches:
    count = upsert_to_supabase("matches", all_matches)
    print(f"\n✅ تم رفع {count} مباراة", flush=True)

# رفع الفرق
if all_teams:
    teams_list = [{"id": hashlib.md5(t.encode()).hexdigest(), "name": t} for t in all_teams]
    count = upsert_to_supabase("teams", teams_list)
    print(f"✅ تم رفع {count} فريق", flush=True)

# ========== النتيجة النهائية ==========
print("\n" + "="*70, flush=True)
print("🏆 اكتمل الأرشيف!", flush=True)
print("="*70, flush=True)
print(f"📊 إجمالي المباريات: {len(all_matches)}")
print(f"📊 إجمالي الفرق: {len(all_teams)}")
print("✅ جميع البيانات في Supabase")
print("="*70, flush=True)
