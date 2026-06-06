import os
import requests
import json
import sys

sys.stdout.reconfigure(line_buffering=True)

print("="*80, flush=True)
print("📊 تقرير شامل عن بيانات Supabase", flush=True)
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

# قائمة جميع الجداول (من اللي شفناها في حسابك)
TABLES = [
    "teams", "players", "matches", "stadiums", "coaches", 
    "match_events", "match_stats", "match_lineups", "transfers",
    "player_injuries", "media_news", "league_standings", "leagues"
]

report = {}

print("\n🔍 جلب معلومات الجداول...\n", flush=True)

for table in TABLES:
    print(f"📁 جدول: {table}", flush=True)
    
    # 1. جلب عدد السجلات
    try:
        resp = requests.get(f"{SUPABASE_URL}/{table}?select=id&limit=0", headers=headers)
        if resp.status_code == 200:
            # نحتاج نجيب العدد الفعلي
            count_resp = requests.get(f"{SUPABASE_URL}/{table}?select=id", headers=headers)
            if count_resp.status_code == 200:
                count = len(count_resp.json())
                print(f"   📊 عدد السجلات: {count}", flush=True)
            else:
                count = 0
                print(f"   📊 عدد السجلات: 0", flush=True)
        else:
            count = 0
            print(f"   📊 عدد السجلات: 0 (HTTP {resp.status_code})", flush=True)
    except Exception as e:
        count = 0
        print(f"   ❌ خطأ في الجدول: {str(e)[:50]}", flush=True)
    
    # 2. جلب عينة من البيانات (أول 3 سجلات)
    if count > 0:
        try:
            sample_resp = requests.get(f"{SUPABASE_URL}/{table}?limit=3", headers=headers)
            if sample_resp.status_code == 200:
                samples = sample_resp.json()
                print(f"   📋 عينة (أول {len(samples)} سجل):", flush=True)
                for idx, sample in enumerate(samples):
                    # عرض المفتاح الأساسي وبعض الحقول المهمة
                    sample_info = {}
                    for key in list(sample.keys())[:5]:  # أول 5 أعمدة فقط
                        val = sample[key]
                        if isinstance(val, str) and len(val) > 30:
                            val = val[:27] + "..."
                        sample_info[key] = val
                    print(f"      سجل {idx+1}: {json.dumps(sample_info, ensure_ascii=False)}", flush=True)
        except Exception as e:
            print(f"   ⚠️ خطأ في جلب العينة: {str(e)[:50]}", flush=True)
    else:
        print(f"   📋 الجدول فاضي (لا توجد بيانات)", flush=True)
    
    print("", flush=True)  # سطر فارغ
    report[table] = {"count": count}

# ========== ملخص ==========
print("="*80, flush=True)
print("📊 ملخص عام:", flush=True)
print("="*80, flush=True)

total_records = 0
for table, data in report.items():
    total_records += data["count"]
    if data["count"] > 0:
        print(f"   ✅ {table}: {data['count']} سجل", flush=True)

print(f"\n📊 إجمالي السجلات في قاعدة البيانات: {total_records}", flush=True)

if total_records == 0:
    print("\n⚠️ قاعدة البيانات فاضية تماماً!", flush=True)
    print("   سنبدأ من الصفر ببناء الهيكل الموحد.", flush=True)
else:
    print("\n💡 نصيحة: البيانات الموجودة حالياً غير مترابطة بشكل كامل.", flush=True)
    print("   نقترح توحيد الهيكل وإعادة البيانات بشكل منظم.", flush=True)

print("="*80, flush=True)
