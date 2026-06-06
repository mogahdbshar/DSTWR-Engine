import os
import requests
import hashlib
import time
import sys
import pandas as pd
import io

# تثبيت pandas إذا لم يكن موجوداً (للمرة الأولى فقط)
try:
    import pandas as pd
except ImportError:
    os.system('pip install pandas')
    import pandas as pd

sys.stdout.reconfigure(line_buffering=True)

print("="*80, flush=True)
print("🏆 رفع المباريات - النسخة النهائية (باستخدام Pandas)", flush=True)
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

# ========== جلب المباريات باستخدام Pandas ==========
print("\n📥 جلب المباريات من المصادر...", flush=True)

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
        # استخدام pandas لقراءة CSV مباشرة
        df = pd.read_csv(url)
        
        # تجاهل الصفوف الفارغة
        df = df.dropna(subset=['Date', 'HomeTeam', 'AwayTeam'])
        
        match_count = 0
        for _, row in df.iterrows():
            match_date = str(row['Date']).strip()
            home_team = str(row['HomeTeam']).strip()
            away_team = str(row['AwayTeam']).strip()
            home_score = row['FTHG'] if pd.notna(row['FTHG']) else 0
            away_score = row['FTAG'] if pd.notna(row['FTAG']) else 0
            
            # التحقق من صحة التاريخ
            if not match_date or len(match_date) < 8:
                continue
            
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
                    "home_score": int(home_score) if pd.notna(home_score) else 0,
                    "away_score": int(away_score) if pd.notna(away_score) else 0,
                    "match_date": match_date,
                    "status": "finished",
                    "season_year": int(season.split('-')[1]) + 2000
                })
                match_count += 1
        
        print(f"      ✅ {match_count} مباراة صالحة", flush=True)
        
    except Exception as e:
        print(f"      ❌ خطأ في تحميل {season}: {str(e)[:100]}", flush=True)
    
    time.sleep(0.5)

print(f"\n   📊 إجمالي المباريات الصالحة: {len(all_matches)}", flush=True)

# ========== رفع المباريات ==========
if all_matches:
    print("\n📤 رفع المباريات إلى Supabase...", flush=True)
    
    uploaded = 0
    headers_upsert = headers.copy()
    headers_upsert["Prefer"] = "resolution=merge-duplicates"
    
    # رفع على دفعات صغيرة
    batch_size = 50
    for i in range(0, len(all_matches), batch_size):
        batch = all_matches[i:i+batch_size]
        try:
            resp = requests.post(f"{SUPABASE_URL}/matches", headers=headers_upsert, json=batch, timeout=30)
            if resp.status_code in [200, 201]:
                uploaded += len(batch)
                print(f"   ✅ دفعة {i//batch_size + 1}/{(len(all_matches)+batch_size-1)//batch_size}: تم رفع {len(batch)} مباراة", flush=True)
            else:
                print(f"   ❌ فشل الدفعة {i//batch_size + 1}: {resp.status_code}", flush=True)
                if "duplicate" in resp.text.lower():
                    print(f"      ⚠️ تكرار في البيانات", flush=True)
        except Exception as e:
            print(f"   ❌ خطأ: {str(e)}", flush=True)
        time.sleep(0.2)
    
    print(f"\n   ✅ تم رفع {uploaded}/{len(all_matches)} مباراة", flush=True)
else:
    print("\n⚠️ لا توجد مباريات صالحة للرفع!", flush=True)

# ========== النتيجة ==========
print("\n" + "="*80, flush=True)
print("🏆 اكتمل!", flush=True)
print("="*80, flush=True)

resp = requests.get(f"{SUPABASE_URL}/matches?select=id", headers=headers)
matches_total = len(resp.json()) if resp.status_code == 200 else 0
print(f"📊 المباريات في Supabase: {matches_total}")
print("="*80, flush=True)
