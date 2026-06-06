import os
import requests
import hashlib
import time
import sys

sys.stdout.reconfigure(line_buffering=True)

print("="*80, flush=True)
print("🏆 سكربت ذكي - يتكيف مع هيكل Supabase تلقائياً", flush=True)
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

# ========== 1. اكتشاف هيكل جدول matches ==========
print("\n🔍 [1/3] اكتشاف هيكل جدول matches...", flush=True)

# نحاول نعرف الأعمدة الموجودة
existing_columns = set()

# طريقة 1: نجيب سجل موجود
resp = requests.get(f"{SUPABASE_URL}/matches?limit=1", headers=headers)
if resp.status_code == 200:
    data = resp.json()
    if data:
        existing_columns = set(data[0].keys())
        print(f"   ✅ الأعمدة الموجودة: {', '.join(existing_columns)}", flush=True)

# طريقة 2: نجرب نضيف سجل تجريبي ونشوف الخطأ
if not existing_columns:
    test_match = {"id": "test_123", "home": "test"}
    resp = requests.post(f"{SUPABASE_URL}/matches", headers=headers, json=test_match, timeout=5)
    if resp.status_code == 400:
        error_msg = resp.text
        # استخراج أسماء الأعمدة من رسالة الخطأ
        import re
        found = re.findall(r"'(\w+)' column", error_msg)
        for col in found:
            existing_columns.add(col)
    print(f"   ✅ تم اكتشاف {len(existing_columns)} عمود", flush=True)

if not existing_columns:
    print("   ⚠️ لم نتمكن من اكتشاف الأعمدة، سيتم استخدام الأعمدة الافتراضية", flush=True)
    existing_columns = {"id", "home_team", "away_team", "home_score", "away_score", "date"}

# ========== 2. جلب المباريات ==========
print("\n📥 [2/3] جلب المباريات من المصادر...", flush=True)

all_matches = []
new_teams = {}
team_counter = 1000

# جلب الفرق الموجودة
resp = requests.get(f"{SUPABASE_URL}/teams?select=id,name", headers=headers)
existing_teams = {team["name"]: team["id"] for team in resp.json()} if resp.status_code == 200 else {}
print(f"   ✅ {len(existing_teams)} فريق موجود", flush=True)

# مصدر البيانات
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
                
                if not home_team or not away_team:
                    continue
                
                # إضافة فرق جديدة
                for team in [home_team, away_team]:
                    if team not in existing_teams and team not in new_teams:
                        team_counter += 1
                        new_teams[team] = team_counter
                
                # بناء كائن المباراة حسب الأعمدة الموجودة
                match_obj = {"id": hashlib.md5(f"{season}_{home_team}_{away_team}_{match_date}".encode()).hexdigest()}
                
                # إضافة الأعمدة الموجودة فقط
                if "home_team" in existing_columns:
                    match_obj["home_team"] = home_team
                if "home_team_id" in existing_columns:
                    match_obj["home_team_id"] = existing_teams.get(home_team, new_teams.get(home_team))
                if "away_team" in existing_columns:
                    match_obj["away_team"] = away_team
                if "away_team_id" in existing_columns:
                    match_obj["away_team_id"] = existing_teams.get(away_team, new_teams.get(away_team))
                if "home_score" in existing_columns:
                    match_obj["home_score"] = int(home_score) if home_score.isdigit() else 0
                if "away_score" in existing_columns:
                    match_obj["away_score"] = int(away_score) if away_score.isdigit() else 0
                if "date" in existing_columns or "match_date" in existing_columns:
                    date_col = "match_date" if "match_date" in existing_columns else "date"
                    match_obj[date_col] = match_date
                if "season" in existing_columns:
                    match_obj["season"] = season
                
                all_matches.append(match_obj)
            
            print(f"      ✅ {len(lines)-1} مباراة", flush=True)
    except Exception as e:
        print(f"      ❌ خطأ: {str(e)[:50]}", flush=True)

print(f"\n   📊 إجمالي المباريات: {len(all_matches)}", flush=True)

# ========== 3. رفع البيانات ==========
print("\n📤 [3/3] رفع البيانات إلى Supabase...", flush=True)

# رفع الفرق الجديدة
teams_list = []
for name, tid in new_teams.items():
    teams_list.append({
        "id": tid,
        "name": name,
        "short_name": name[:20],
        "league_id": 2021
    })

for team in teams_list:
    try:
        check = requests.get(f"{SUPABASE_URL}/teams?id=eq.{team['id']}", headers=headers)
        if check.status_code == 200 and check.json():
            continue
        requests.post(f"{SUPABASE_URL}/teams", headers=headers, json=team, timeout=10)
    except:
        pass
    time.sleep(0.02)
print(f"   ✅ تم رفع {len(teams_list)} فريق جديد", flush=True)

# رفع المباريات
match_count = 0
for i, match in enumerate(all_matches):
    try:
        # تأكد من وجود id
        if not match.get("id"):
            continue
        
        resp = requests.post(f"{SUPABASE_URL}/matches", headers=headers, json=match, timeout=10)
        if resp.status_code in [200, 201, 409]:
            match_count += 1
        elif i < 5:
            print(f"   ⚠️ فشل: {resp.status_code} - {resp.text[:80] if resp.text else ''}", flush=True)
    except Exception as e:
        if i < 5:
            print(f"   ❌ خطأ: {str(e)[:50]}", flush=True)
    
    if (i + 1) % 100 == 0:
        print(f"   ✅ تم رفع {i+1}/{len(all_matches)} مباراة (نجاح: {match_count})", flush=True)
    time.sleep(0.01)

print(f"\n   ✅ تم رفع {match_count}/{len(all_matches)} مباراة", flush=True)

# ========== النتيجة ==========
print("\n" + "="*80, flush=True)
print("🏆 اكتمل!", flush=True)
print("="*80, flush=True)

# إحصائيات نهائية
resp = requests.get(f"{SUPABASE_URL}/teams?select=id", headers=headers)
teams_total = len(resp.json()) if resp.status_code == 200 else 0

resp = requests.get(f"{SUPABASE_URL}/matches?select=id", headers=headers)
matches_total = len(resp.json()) if resp.status_code == 200 else 0

print(f"📊 الفرق (teams): {teams_total}")
print(f"📊 المباريات (matches): {matches_total}")
print("="*80, flush=True)
