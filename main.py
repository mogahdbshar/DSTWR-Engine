import os
import requests
import hashlib
import time
import sys
import pandas as pd

sys.stdout.reconfigure(line_buffering=True)

print("="*80, flush=True)
print("🏆 الحل النهائي - التحقق والرفع", flush=True)
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

# ========== 1. التحقق من وجود الدوري ==========
print("\n🔍 [1/4] التحقق من جدول leagues...", flush=True)

# جلب جميع الدوريات
resp = requests.get(f"{SUPABASE_URL}/leagues", headers=headers)
leagues = {}
if resp.status_code == 200:
    for league in resp.json():
        leagues[league["id"]] = league["name"]
    print(f"   ✅ الدوريات الموجودة: {len(leagues)}")
    
    # البحث عن الدوري الإنجليزي
    premier_league_id = None
    for lid, name in leagues.items():
        if "Premier" in name or "premier" in name:
            premier_league_id = lid
            print(f"   🏆 تم العثور على الدوري الإنجليزي: ID {lid} - {name}")
            break
    
    if not premier_league_id:
        print("   ❌ لم يتم العثور على الدوري الإنجليزي!")
        print("   سيتم إنشاؤه...")
        
        # إنشاء الدوري الإنجليزي
        new_league = {
            "id": 2021,
            "name": "Premier League",
            "name_ar": "الدوري الإنجليزي الممتاز",
            "country": "England",
            "country_ar": "إنجلترا",
            "code": "PL"
        }
        resp = requests.post(f"{SUPABASE_URL}/leagues", headers=headers, json=new_league)
        if resp.status_code in [200, 201]:
            premier_league_id = 2021
            print(f"   ✅ تم إنشاء الدوري الإنجليزي برقم {premier_league_id}")
        else:
            print(f"   ❌ فشل إنشاء الدوري: {resp.text}")
            sys.exit(1)
else:
    print(f"   ❌ فشل جلب الدوريات: {resp.status_code}")
    sys.exit(1)

# ========== 2. جلب الفرق ==========
print("\n🏟️ [2/4] جلب الفرق الموجودة...", flush=True)
resp = requests.get(f"{SUPABASE_URL}/teams?select=id,name", headers=headers)
teams = {}
if resp.status_code == 200:
    for team in resp.json():
        teams[team["name"]] = team["id"]
print(f"   ✅ {len(teams)} فريق", flush=True)

# ========== 3. جلب المباريات باستخدام Pandas ==========
print("\n📥 [3/4] جلب المباريات من المصادر...", flush=True)

all_matches = []
seasons_urls = [
    ("1516", "2015-16"),
    ("1617", "2016-17"),
    ("1718", "2017-18"),
    ("1819", "2018-19"),
    ("1920", "2019-20"),
    ("2021", "2020-21"),
    ("2122", "2021-22"),
    ("2223", "2022-23"),
    ("2324", "2023-24"),
    ("2425", "2024-25"),
    ("2526", "2025-26"),
]

for code, season in seasons_urls:
    url = f"https://www.football-data.co.uk/mmz4281/{code}/E0.csv"
    print(f"   📥 موسم {season}...", flush=True)
    
    try:
        df = pd.read_csv(url)
        df = df.dropna(subset=['Date', 'HomeTeam', 'AwayTeam'])
        
        match_count = 0
        for _, row in df.iterrows():
            match_date = str(row['Date']).strip()
            home_team = str(row['HomeTeam']).strip()
            away_team = str(row['AwayTeam']).strip()
            home_score = row['FTHG'] if pd.notna(row['FTHG']) else 0
            away_score = row['FTAG'] if pd.notna(row['FTAG']) else 0
            
            if not match_date or len(match_date) < 8:
                continue
            
            home_id = teams.get(home_team)
            away_id = teams.get(away_team)
            
            if home_id and away_id:
                match_id = hashlib.md5(f"{season}_{home_team}_{away_team}_{match_date}".encode()).hexdigest()
                all_matches.append({
                    "id": match_id,
                    "league_id": premier_league_id,
                    "season": season,
                    "home_team_id": home_id,
                    "away_team_id": away_id,
                    "home_score": int(home_score),
                    "away_score": int(away_score),
                    "match_date": match_date,
                    "status": "finished",
                    "season_year": int(season.split('-')[1]) + 2000
                })
                match_count += 1
        
        print(f"      ✅ {match_count} مباراة صالحة", flush=True)
        
    except Exception as e:
        print(f"      ❌ خطأ: {str(e)[:100]}", flush=True)
    
    time.sleep(0.5)

print(f"\n   📊 إجمالي المباريات الصالحة: {len(all_matches)}", flush=True)

# ========== 4. رفع المباريات (سجل سجل) ==========
print("\n📤 [4/4] رفع المباريات إلى Supabase (سجل سجل)...", flush=True)

if not all_matches:
    print("   ⚠️ لا توجد مباريات للرفع!", flush=True)
    sys.exit(0)

uploaded = 0
failed_count = 0

for i, match in enumerate(all_matches):
    try:
        # التحقق من وجود المباراة
        check_resp = requests.get(f"{SUPABASE_URL}/matches?id=eq.{match['id']}", headers=headers)
        if check_resp.status_code == 200 and check_resp.json():
            uploaded += 1
            continue
        
        # رفع المباراة
        resp = requests.post(f"{SUPABASE_URL}/matches", headers=headers, json=match, timeout=10)
        if resp.status_code in [200, 201]:
            uploaded += 1
        elif resp.status_code == 409:
            uploaded += 1
        else:
            failed_count += 1
            if failed_count <= 5:  # طباعة أول 5 أخطاء فقط
                print(f"   ❌ فشل رفع مباراة {i+1}: {resp.status_code}", flush=True)
                print(f"      السبب: {resp.text[:100]}", flush=True)
    
    except Exception as e:
        failed_count += 1
        if failed_count <= 5:
            print(f"   ❌ خطأ في المباراة {i+1}: {str(e)}", flush=True)
    
    if (i + 1) % 200 == 0:
        print(f"   ✅ تم رفع {i+1}/{len(all_matches)} (نجاح: {uploaded})", flush=True)
    
    time.sleep(0.05)

print(f"\n   ✅ تم رفع {uploaded}/{len(all_matches)} مباراة بنجاح", flush=True)
print(f"   ❌ فشل {failed_count} مباراة", flush=True)

# ========== النتيجة النهائية ==========
print("\n" + "="*80, flush=True)
print("🏆 اكتمل!", flush=True)
print("="*80, flush=True)

resp = requests.get(f"{SUPABASE_URL}/matches?select=id", headers=headers)
matches_total = len(resp.json()) if resp.status_code == 200 else 0
print(f"📊 إجمالي المباريات في Supabase: {matches_total}")
print("="*80, flush=True)
