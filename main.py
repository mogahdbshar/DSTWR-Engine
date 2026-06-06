import os
import requests
import hashlib
import time
from datetime import datetime
import sys

sys.stdout.reconfigure(line_buffering=True)

print("="*70, flush=True)
print("🏆 أرشيف كرة القدم - إصدار مع تصحيح رفع Supabase", flush=True)
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
    """رفع البيانات مع تجنب التكرار - نسخة مبسطة"""
    if not data_list:
        print(f"   ⚠️ لا توجد بيانات لرفعها إلى {table}", flush=True)
        return 0
    
    inserted = 0
    total = len(data_list)
    print(f"   📤 بدء رفع {total} سجل إلى {table}...", flush=True)
    
    for i, item in enumerate(data_list):
        try:
            # رفع كل سجل على حدة عشان نعرف وين المشكلة
            resp = requests.post(f"{SUPABASE_URL}/{table}", headers=headers, json=item, timeout=10)
            if resp.status_code in [200, 201]:
                inserted += 1
                if (i + 1) % 50 == 0:
                    print(f"      ✅ رفع {i+1}/{total}", flush=True)
            elif resp.status_code == 409:
                # مكرر، نتجاوز
                inserted += 1
            else:
                print(f"      ⚠️ فشل رفع سجل {i+1}: HTTP {resp.status_code}", flush=True)
                print(f"         البيانات: {item.get('id', 'no id')[:50]}", flush=True)
        except Exception as e:
            print(f"      ❌ خطأ في السجل {i+1}: {str(e)[:50]}", flush=True)
        
        # تأخير بسيط عشان ما نضغط على Supabase
        if i % 20 == 0:
            time.sleep(0.05)
    
    print(f"   ✅ تم رفع {inserted}/{total} إلى {table}", flush=True)
    return inserted

# ========== جلب البيانات ==========
all_matches = []
all_teams = set()

print("\n📥 جلب بيانات EPL...", flush=True)

urls = [
    ("https://www.football-data.co.uk/mmz4281/2425/E0.csv", "2024-25"),
    ("https://www.football-data.co.uk/mmz4281/2324/E0.csv", "2023-24"),
]

for url, season in urls:
    print(f"   📥 موسم {season}...", flush=True)
    try:
        resp = requests.get(url, timeout=20)
        if resp.status_code == 200:
            lines = resp.text.strip().split('\n')
            for line in lines[1:]:
                parts = line.split(',')
                if len(parts) >= 6:
                    # تنظيف البيانات قبل الرفع
                    home_score = parts[4].strip()
                    away_score = parts[5].strip()
                    
                    match_data = {
                        "id": hashlib.md5(f"{season}_{parts[2]}_{parts[3]}_{parts[0]}".encode()).hexdigest(),
                        "date": parts[0].strip(),
                        "home_team": parts[2].strip(),
                        "away_team": parts[3].strip(),
                        "home_score": int(home_score) if home_score.isdigit() else 0,
                        "away_score": int(away_score) if away_score.isdigit() else 0,
                        "league": "Premier League",
                        "season": season
                    }
                    all_matches.append(match_data)
                    all_teams.add(parts[2].strip())
                    all_teams.add(parts[3].strip())
            print(f"      ✅ {len(lines)-1} مباراة", flush=True)
    except Exception as e:
        print(f"      ❌ خطأ: {str(e)[:50]}", flush=True)
    time.sleep(0.5)

# ========== رفع المباريات ==========
print("\n" + "="*70, flush=True)
print("📤 رفع البيانات إلى Supabase...", flush=True)
print("="*70, flush=True)

if all_matches:
    print(f"\n📊 المباريات: {len(all_matches)}", flush=True)
    match_count = upsert_to_supabase("matches", all_matches)
    print(f"\n✅ تم رفع {match_count} مباراة", flush=True)

# ========== رفع الفرق ==========
if all_teams:
    print(f"\n📊 الفرق: {len(all_teams)}", flush=True)
    teams_list = []
    for team in all_teams:
        if team:  # نتأكد إنه مو فارغ
            teams_list.append({
                "id": hashlib.md5(team.encode()).hexdigest(),
                "name": team,
                "source": "football-data.co.uk"
            })
    
    team_count = upsert_to_supabase("teams", teams_list)
    print(f"✅ تم رفع {team_count} فريق", flush=True)

# ========== النتيجة النهائية ==========
print("\n" + "="*70, flush=True)
print("🏆 اكتمل!", flush=True)
print(f"📊 إجمالي المباريات المرفوعة: {match_count if all_matches else 0}")
print(f"📊 إجمالي الفرق المرفوعة: {team_count if all_teams else 0}")
print("="*70, flush=True)
