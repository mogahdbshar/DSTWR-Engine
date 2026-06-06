import os
import requests
import hashlib
import time
import sys

sys.stdout.reconfigure(line_buffering=True)

print("="*80, flush=True)
print("🏆 نظام توحيد بيانات كرة القدم - مع تشخيص الأخطاء", flush=True)
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

# ========== 1. جلب البيانات الموجودة ==========
print("\n📥 [1/4] جلب البيانات الموجودة...", flush=True)

resp = requests.get(f"{SUPABASE_URL}/teams?select=id,name", headers=headers)
existing_teams = {team["name"]: team["id"] for team in resp.json()} if resp.status_code == 200 else {}
print(f"   ✅ {len(existing_teams)} فريق موجود", flush=True)

# ========== 2. تعيين المعرفات ==========
league_mapping = {
    "Premier League": 2021,
    "La Liga": 2014,
    "Bundesliga": 78,
    "Serie A": 135,
    "Ligue 1": 61,
}

# ========== 3. جلب المباريات ==========
print("\n📥 [2/4] جلب المباريات...", flush=True)

all_matches = []
new_teams = {}
team_counter = max(existing_teams.values()) if existing_teams else 1000

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
                if len(parts) < 6:
                    continue
                
                home_team = parts[2].strip()
                away_team = parts[3].strip()
                home_score = parts[4].strip()
                away_score = parts[5].strip()
                match_date = parts[0].strip()
                
                # التحقق من صحة البيانات
                if not home_team or not away_team:
                    continue
                if home_score == '' or away_score == '':
                    continue
                
                # إضافة الفرق الجديدة
                for team in [home_team, away_team]:
                    if team not in existing_teams and team not in new_teams:
                        team_counter += 1
                        new_teams[team] = team_counter
                
                # الحصول على معرفات الفرق
                home_id = existing_teams.get(home_team, new_teams.get(home_team))
                away_id = existing_teams.get(away_team, new_teams.get(away_team))
                
                if not home_id or not away_id:
                    continue
                
                # إنشاء معرف المباراة
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
                    "status": "finished"
                })
            
            print(f"      ✅ {len(lines)-1} مباراة", flush=True)
    except Exception as e:
        print(f"      ❌ خطأ: {str(e)[:50]}", flush=True)

print(f"\n   📊 إجمالي المباريات المجلوبة: {len(all_matches)}", flush=True)

# ========== 4. رفع الفرق الجديدة ==========
print("\n📤 [3/4] رفع الفرق الجديدة...", flush=True)

teams_list = []
for name, tid in new_teams.items():
    teams_list.append({
        "id": tid,
        "name": name,
        "short_name": name[:20],
        "logo_url": None,
        "league_id": 2021
    })

for team in teams_list:
    try:
        # التحقق من الوجود
        check = requests.get(f"{SUPABASE_URL}/teams?id=eq.{team['id']}", headers=headers)
        if check.status_code == 200 and check.json():
            continue
        
        resp = requests.post(f"{SUPABASE_URL}/teams", headers=headers, json=team, timeout=10)
        if resp.status_code not in [200, 201, 409]:
            print(f"   ⚠️ فشل رفع {team['name']}: {resp.status_code}", flush=True)
    except Exception as e:
        print(f"   ❌ {team['name']}: {str(e)[:30]}", flush=True)
    time.sleep(0.02)

print(f"   ✅ تم رفع {len(teams_list)} فريق جديد", flush=True)

# ========== 5. رفع المباريات (مع التحقق) ==========
print("\n📤 [4/4] رفع المباريات...", flush=True)

match_count = 0
total = len(all_matches)

for i, match in enumerate(all_matches):
    try:
        # تأكد من صحة البيانات
        if not match["id"] or not match["home_team_id"] or not match["away_team_id"]:
            continue
        
        # رفع مباشر بدون التحقق المسبق (للتوفير)
        resp = requests.post(f"{SUPABASE_URL}/matches", headers=headers, json=match, timeout=10)
        
        if resp.status_code in [200, 201]:
            match_count += 1
        elif resp.status_code == 409:
            match_count += 1  # مكرر
        else:
            # طباعة أول 5 أخطاء فقط
            if match_count < 5:
                print(f"   ⚠️ فشل رفع مباراة {i+1}: HTTP {resp.status_code}", flush=True)
                print(f"      السبب: {resp.text[:100] if resp.text else 'لا يوجد سبب'}", flush=True)
        
    except Exception as e:
        if match_count < 5:
            print(f"   ❌ خطأ في مباراة {i+1}: {str(e)[:50]}", flush=True)
    
    if (i + 1) % 100 == 0:
        print(f"   ✅ تم معالجة {i+1}/{total} مباراة (ناجحة: {match_count})", flush=True)
    
    time.sleep(0.02)

print(f"\n   ✅ تم رفع {match_count}/{total} مباراة", flush=True)

# ========== النتيجة النهائية ==========
print("\n" + "="*80, flush=True)
print("🏆 اكتمل!", flush=True)
print("="*80, flush=True)

# جلب الإحصائيات النهائية
resp = requests.get(f"{SUPABASE_URL}/teams?select=id", headers=headers)
teams_total = len(resp.json()) if resp.status_code == 200 else 0

resp = requests.get(f"{SUPABASE_URL}/matches?select=id", headers=headers)
matches_total = len(resp.json()) if resp.status_code == 200 else 0

print(f"📊 الفرق (teams): {teams_total}")
print(f"📊 المباريات (matches): {matches_total}")
print("="*80, flush=True)
