import os
import requests
import json
import sys

sys.stdout.reconfigure(line_buffering=True)

print("="*80, flush=True)
print("🔍 تشخيص قاعدة بيانات Supabase", flush=True)
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

# قائمة الجداول
tables = ["teams", "matches", "leagues", "players", "coaches", "stadiums", "league_standings"]

print("\n📊 فحص جميع الجداول:\n", flush=True)

for table in tables:
    print(f"📁 جدول: {table}", flush=True)
    
    # 1. جلب عدد السجلات
    try:
        resp = requests.get(f"{SUPABASE_URL}/{table}?select=id&limit=1", headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            count_resp = requests.get(f"{SUPABASE_URL}/{table}?select=id", headers=headers)
            if count_resp.status_code == 200:
                count = len(count_resp.json())
            else:
                count = len(data) if data else 0
            print(f"   📊 عدد السجلات: {count}", flush=True)
        else:
            print(f"   ❌ فشل الوصول: HTTP {resp.status_code}", flush=True)
            continue
    except Exception as e:
        print(f"   ❌ خطأ: {str(e)[:50]}", flush=True)
        continue
    
    # 2. جلب أسماء الأعمدة (أول سجل)
    try:
        resp = requests.get(f"{SUPABASE_URL}/{table}?limit=1", headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            if data:
                columns = list(data[0].keys())
                print(f"   📋 الأعمدة: {', '.join(columns)}", flush=True)
            else:
                print(f"   📋 الجدول فاضي (لا توجد عينة)", flush=True)
        else:
            print(f"   ⚠️ لا يمكن جلب العينة: {resp.status_code}", flush=True)
    except Exception as e:
        print(f"   ⚠️ خطأ: {str(e)[:50]}", flush=True)
    
    # 3. عرض عينة من البيانات (أول سجلين)
    if count > 0:
        try:
            resp = requests.get(f"{SUPABASE_URL}/{table}?limit=2", headers=headers)
            if resp.status_code == 200:
                samples = resp.json()
                for idx, sample in enumerate(samples):
                    # اختصار البيانات الطويلة
                    short_sample = {}
                    for k, v in list(sample.items())[:4]:
                        if isinstance(v, str) and len(v) > 30:
                            short_sample[k] = v[:27] + "..."
                        else:
                            short_sample[k] = v
                    print(f"   🧪 عينة {idx+1}: {json.dumps(short_sample, ensure_ascii=False)}", flush=True)
        except:
            pass
    
    print("", flush=True)

# ========== فحص الروابط (Foreign Keys) ==========
print("\n" + "="*80, flush=True)
print("🔗 فحص العلاقات (Foreign Keys):", flush=True)
print("="*80, flush=True)

try:
    # جلب بعض المباريات مع الفرق
    resp = requests.get(f"{SUPABASE_URL}/matches?limit=5", headers=headers)
    if resp.status_code == 200:
        matches = resp.json()
        if matches:
            print(f"\n📊 عينة من المباريات (أول {len(matches)}):", flush=True)
            for match in matches:
                match_id = match.get("id", "?")
                home_id = match.get("home_team_id", "?")
                away_id = match.get("away_team_id", "?")
                home_score = match.get("home_score", "?")
                away_score = match.get("away_score", "?")
                season = match.get("season", "?")
                print(f"   🏆 {match_id[:20]}... | {home_id} vs {away_id} | {home_score}-{away_score} | {season}", flush=True)
        else:
            print("\n⚠️ لا توجد مباريات في الجدول!", flush=True)
    else:
        print(f"\n❌ فشل جلب المباريات: {resp.status_code}", flush=True)
except Exception as e:
    print(f"\n❌ خطأ: {str(e)[:100]}", flush=True)

# ========== فحص الفرق ==========
try:
    resp = requests.get(f"{SUPABASE_URL}/teams?limit=10", headers=headers)
    if resp.status_code == 200:
        teams = resp.json()
        print(f"\n🏟️ عينة من الفرق (أول {len(teams)}):", flush=True)
        for team in teams[:5]:
            team_id = team.get("id", "?")
            name = team.get("name", "?")
            league_id = team.get("league_id", "?")
            print(f"   ⚽ {team_id} | {name} | league_id: {league_id}", flush=True)
    else:
        print(f"\n❌ فشل جلب الفرق: {resp.status_code}", flush=True)
except Exception as e:
    print(f"\n❌ خطأ: {str(e)[:100]}", flush=True)

# ========== التقرير النهائي ==========
print("\n" + "="*80, flush=True)
print("📋 التقرير النهائي:", flush=True)
print("="*80, flush=True)

# جلب إجمالي المباريات
try:
    resp = requests.get(f"{SUPABASE_URL}/matches?select=id", headers=headers)
    matches_total = len(resp.json()) if resp.status_code == 200 else 0
    print(f"   📊 المباريات (matches): {matches_total}", flush=True)
except:
    print(f"   📊 المباريات (matches): غير معروف", flush=True)

# جلب إجمالي الفرق
try:
    resp = requests.get(f"{SUPABASE_URL}/teams?select=id", headers=headers)
    teams_total = len(resp.json()) if resp.status_code == 200 else 0
    print(f"   📊 الفرق (teams): {teams_total}", flush=True)
except:
    print(f"   📊 الفرق (teams): غير معروف", flush=True)

# جلب إجمالي الدوريات
try:
    resp = requests.get(f"{SUPABASE_URL}/leagues?select=id", headers=headers)
    leagues_total = len(resp.json()) if resp.status_code == 200 else 0
    print(f"   📊 الدوريات (leagues): {leagues_total}", flush=True)
except:
    print(f"   📊 الدوريات (leagues): غير معروف", flush=True)

print("\n💡 بناءً على النتيجة أعلاه، سأعرف المشكلة بالضبط وأصلحها.", flush=True)
print("="*80, flush=True)
