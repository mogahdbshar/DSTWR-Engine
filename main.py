import os
import requests
import hashlib
import time
import sys

sys.stdout.reconfigure(line_buffering=True)

print("="*80, flush=True)
print("🏆 نظام توحيد بيانات كرة القدم - الحفاظ على البيانات الموجودة + إضافة جديدة", flush=True)
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

# ========== 1. جلب البيانات الموجودة من Supabase ==========
print("\n📥 [1/5] جلب البيانات الموجودة من Supabase...", flush=True)

# جلب الفرق الموجودة
resp = requests.get(f"{SUPABASE_URL}/teams?select=id,name,league_id", headers=headers)
existing_teams = {}
if resp.status_code == 200:
    for team in resp.json():
        existing_teams[team["name"]] = team["id"]
print(f"   ✅ تم جلب {len(existing_teams)} فريق موجود", flush=True)

# جلب الدوريات الموجودة
resp = requests.get(f"{SUPABASE_URL}/leagues?select=id,name", headers=headers)
existing_leagues = {}
if resp.status_code == 200:
    for league in resp.json():
        existing_leagues[league["name"]] = league["id"]
print(f"   ✅ تم جلب {len(existing_leagues)} دوري موجود", flush=True)

# ========== 2. تعيين المعرفات ==========
print("\n📋 [2/5] توحيد المعرفات...", flush=True)

# دوريات جديدة (إذا ما كانت موجودة)
league_mapping = {
    "Premier League": existing_leagues.get("Premier League", 2021),
    "La Liga": existing_leagues.get("La Liga", 2014),
    "Bundesliga": existing_leagues.get("Bundesliga", 2015),
    "Serie A": existing_leagues.get("Serie A", 2019),
    "Ligue 1": existing_leagues.get("Ligue 1", 2015),
}

print(f"   🏆 معرفات الدوريات المستخدمة:", flush=True)
for name, lid in league_mapping.items():
    print(f"      {name}: {lid}", flush=True)

# ========== 3. جلب المباريات ==========
print("\n📥 [3/5] جلب المباريات من football-data.co.uk...", flush=True)

all_matches = []
new_teams = {}
team_counter = max(existing_teams.values()) if existing_teams else 1000

# المواسم
seasons = [
    ("https://www.football-data.co.uk/mmz4281/2425/E0.csv", "2024-25", "Premier League"),
    ("https://www.football-data.co.uk/mmz4281/2324/E0.csv", "2023-24", "Premier League"),
]

for url, season, league_name in seasons:
    print(f"   📥 موسم {season} - {league_name}...", flush=True)
    try:
        resp = requests.get(url, timeout=20)
        if resp.status_code == 200:
            lines = resp.text.strip().split('\n')
            league_id = league_mapping.get(league_name, 2021)
            
            for line in lines[1:]:
                parts = line.split(',')
                if len(parts) >= 6:
                    home_team = parts[2].strip()
                    away_team = parts[3].strip()
                    home_score = parts[4].strip()
                    away_score = parts[5].strip()
                    match_date = parts[0].strip()
                    
                    # معالجة الفرق الجديدة
                    for team in [home_team, away_team]:
                        if team not in existing_teams and team not in new_teams:
                            team_counter += 1
                            new_teams[team] = team_counter
                            print(f"      🆕 فريق جديد: {team} (ID: {team_counter})", flush=True)
                    
                    # الحصول على معرفات الفرق
                    home_id = existing_teams.get(home_team, new_teams.get(home_team))
                    away_id = existing_teams.get(away_team, new_teams.get(away_team))
                    
                    # إنشاء معرف المباراة
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
    time.sleep(0.5)

print(f"\n   📊 إجمالي المباريات المجلوبة: {len(all_matches)}", flush=True)
print(f"   🆕 فرق جديدة: {len(new_teams)}", flush=True)

# ========== 4. رفع الفرق الجديدة ==========
print("\n📤 [4/5] رفع الفرق الجديدة إلى Supabase...", flush=True)

new_teams_list = []
for name, tid in new_teams.items():
    new_teams_list.append({
        "id": tid,
        "name": name,
        "short_name": name[:20],
        "logo_url": None,
        "league_id": 2021  # افتراضي
    })

team_count = 0
for team in new_teams_list:
    try:
        resp = requests.post(f"{SUPABASE_URL}/teams", headers=headers, json=team, timeout=10)
        if resp.status_code in [200, 201]:
            team_count += 1
        elif resp.status_code == 409:
            team_count += 1
    except Exception as e:
        print(f"   ⚠️ فشل رفع {team['name']}: {str(e)[:30]}", flush=True)
    time.sleep(0.02)

print(f"   ✅ تم رفع {team_count}/{len(new_teams_list)} فريق جديد", flush=True)

# ========== 5. رفع المباريات ==========
print("\n📤 [5/5] رفع المباريات إلى Supabase...", flush=True)

match_count = 0
total = len(all_matches)

for i, match in enumerate(all_matches):
    try:
        # التحقق من الوجود
        check = requests.get(f"{SUPABASE_URL}/matches?id=eq.{match['id']}", headers=headers)
        if check.status_code == 200 and check.json():
            match_count += 1
            continue
        
        resp = requests.post(f"{SUPABASE_URL}/matches", headers=headers, json=match, timeout=10)
        if resp.status_code in [200, 201]:
            match_count += 1
        elif resp.status_code == 409:
            match_count += 1
    except Exception as e:
        pass
    
    if (i + 1) % 100 == 0:
        print(f"   ✅ تم رفع {i+1}/{total} مباراة", flush=True)
    time.sleep(0.01)

print(f"   ✅ تم رفع {match_count} مباراة", flush=True)

# ========== النتيجة النهائية ==========
print("\n" + "="*80, flush=True)
print("🏆 اكتمل توحيد البيانات!", flush=True)
print("="*80, flush=True)

# جلب الإحصائيات النهائية
resp = requests.get(f"{SUPABASE_URL}/teams?select=id", headers=headers)
teams_total = len(resp.json()) if resp.status_code == 200 else 0

resp = requests.get(f"{SUPABASE_URL}/matches?select=id", headers=headers)
matches_total = len(resp.json()) if resp.status_code == 200 else 0

print(f"\n📊 الوضع النهائي في Supabase:")
print(f"   ✅ الفرق (teams): {teams_total} (زيادة {team_count})")
print(f"   ✅ المباريات (matches): {matches_total} (زيادة {match_count})")
print(f"   ✅ الدوريات (leagues): {len(existing_leagues)} (محفوظة)")
print(f"   ✅ ترتيب (league_standings): محفوظ")

print("\n🔗 الترابط الآن:")
print("   ✓ المباريات مرتبطة بالفرق عبر home_team_id و away_team_id")
print("   ✓ المباريات مرتبطة بالدوريات عبر league_id")
print("   ✓ الفرق مرتبطة بالدوريات عبر league_id")

print("\n" + "="*80, flush=True)
