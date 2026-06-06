import os
import requests
import hashlib
import time
import sys
import csv
import io

sys.stdout.reconfigure(line_buffering=True)

print("="*80, flush=True)
print("🏆 رفع المباريات - تصحيح مشكلة التاريخ", flush=True)
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
print("\n📥 جلب الفرق الموجودة...", flush=True)
resp = requests.get(f"{SUPABASE_URL}/teams?select=id,name", headers=headers)
teams = {}
if resp.status_code == 200:
    for team in resp.json():
        teams[team["name"]] = team["id"]
print(f"   ✅ {len(teams)} فريق", flush=True)

# ========== جلب المباريات بشكل صحيح ==========
print("\n📥 جلب المباريات من المصادر...", flush=True)

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
            # استخدام csv reader لقراءة الملف بشكل صحيح
            content = resp.text
            csv_reader = csv.reader(io.StringIO(content))
            header = next(csv_reader)  # تخطي الهيدر
            
            match_count = 0
            for row in csv_reader:
                if len(row) < 6:
                    continue
                
                # التأكد من أن التاريخ هو تاريخ وليس نصاً عشوائياً
                match_date = row[0].strip()
                if not match_date or match_date.startswith('Date') or not match_date[0].isdigit():
                    continue
                
                home_team = row[2].strip()
                away_team = row[3].strip()
                home_score = row[4].strip()
                away_score = row[5].strip()
                
                home_id = teams.get(home_team)
                away_id = teams.get(away_team)
                
                if home_id and away_id and home_score.isdigit() and away_score.isdigit():
                    match_id = hashlib.md5(f"{season}_{home_team}_{away_team}_{match_date}".encode()).hexdigest()
                    all_matches.append({
                        "id": match_id,
                        "league_id": 2021,
                        "season": season,
                        "home_team_id": home_id,
                        "away_team_id": away_id,
                        "home_score": int(home_score),
                        "away_score": int(away_score),
                        "match_date": match_date,
                        "status": "finished",
                        "season_year": int(season.split('-')[1]) + 2000 if '-' in season else 2025
                    })
                    match_count += 1
            
            print(f"      ✅ {match_count} مباراة صالحة", flush=True)
        else:
            print(f"      ⚠️ HTTP {resp.status_code}", flush=True)
    except Exception as e:
        print(f"      ❌ خطأ: {str(e)[:50]}", flush=True)
    time.sleep(0.5)

print(f"\n   📊 إجمالي المباريات الصالحة للرفع: {len(all_matches)}", flush=True)

# ========== رفع المباريات ==========
print("\n📤 رفع المباريات إلى Supabase...", flush=True)

if not all_matches:
    print("   ⚠️ لا توجد مباريات صالحة للرفع!", flush=True)
    sys.exit(0)

uploaded = 0
headers_upsert = headers.copy()
headers_upsert["Prefer"] = "resolution=merge-duplicates"

# رفع على دفعات صغيرة (50 مباراة لكل دفعة)
for i in range(0, len(all_matches), 50):
    batch = all_matches[i:i+50]
    try:
        resp = requests.post(f"{SUPABASE_URL}/matches", headers=headers_upsert, json=batch, timeout=30)
        if resp.status_code in [200, 201]:
            uploaded += len(batch)
            print(f"   ✅ دفعة {i//50 + 1}/{(len(all_matches)+49)//50}: تم رفع {len(batch)} مباراة", flush=True)
        else:
            print(f"   ❌ فشل الدفعة {i//50 + 1}: {resp.status_code}", flush=True)
            print(f"      السبب: {resp.text[:100]}", flush=True)
    except Exception as e:
        print(f"   ❌ خطأ في الدفعة {i//50 + 1}: {str(e)}", flush=True)
    time.sleep(0.2)

print(f"\n   ✅ تم رفع {uploaded}/{len(all_matches)} مباراة", flush=True)

# ========== النتيجة ==========
print("\n" + "="*80, flush=True)
print("🏆 اكتمل!", flush=True)
print("="*80, flush=True)

resp = requests.get(f"{SUPABASE_URL}/matches?select=id", headers=headers)
matches_total = len(resp.json()) if resp.status_code == 200 else 0
print(f"📊 المباريات في Supabase: {matches_total}")
print("="*80, flush=True)
