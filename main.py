import os
import requests
import json
import hashlib
import time
from datetime import datetime
import sys

sys.stdout.reconfigure(line_buffering=True)

print("="*70, flush=True)
print("🏆 الأرشيف الشامل لكرة القدم - تشخيص الأخطاء", flush=True)
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

# إحصائيات الأخطاء
errors = []
success_count = 0

def test_url(url, description):
    global success_count
    try:
        print(f"\n🔍 اختبار: {description}", flush=True)
        print(f"   📍 الرابط: {url}", flush=True)
        resp = requests.get(url, timeout=15)
        print(f"   📊 حالة HTTP: {resp.status_code}", flush=True)
        if resp.status_code == 200:
            content = resp.text
            lines = content.strip().split('\n')
            print(f"   ✅ نجاح: {len(lines)} سطر", flush=True)
            success_count += 1
            return resp
        else:
            print(f"   ❌ فشل: HTTP {resp.status_code}", flush=True)
            errors.append(f"{description}: HTTP {resp.status_code}")
            return None
    except requests.exceptions.Timeout:
        print(f"   ❌ وقت الاستجابة انتهى (Timeout)", flush=True)
        errors.append(f"{description}: Timeout")
    except requests.exceptions.ConnectionError:
        print(f"   ❌ خطأ في الاتصال (Connection Error)", flush=True)
        errors.append(f"{description}: Connection Error")
    except Exception as e:
        print(f"   ❌ خطأ غير متوقع: {str(e)[:100]}", flush=True)
        errors.append(f"{description}: {str(e)[:50]}")
    return None

print("\n" + "="*70, flush=True)
print("📡 اختبار جميع المصادر:")
print("="*70, flush=True)

# ========== اختبار جميع الروابط ==========

# 1. jokecamp EPL
test_url("https://raw.githubusercontent.com/jokecamp/FootballData/master/data/EPL/2015-16/2015-16_PL_Results.csv", "EPL 2015-16")

# 2. كأس العالم
test_url("https://raw.githubusercontent.com/openfootball/worldcup.json/master/2018/worldcup.json", "كأس العالم 2018")

# 3. engsoccerdata
test_url("https://raw.githubusercontent.com/jalapic/engsoccerdata/master/data-raw/engsoccerdata2.csv", "البيانات التاريخية إنجلترا")

# 4. La Liga
test_url("https://raw.githubusercontent.com/jokecamp/FootballData/master/data/La_Liga/2015-16/2015-16_La_Liga.csv", "La Liga 2015-16")

# 5. Bundesliga
test_url("https://raw.githubusercontent.com/jokecamp/FootballData/master/data/Bundesliga/2015-16/2015-16_Bundesliga.csv", "Bundesliga 2015-16")

# 6. Serie A
test_url("https://raw.githubusercontent.com/jokecamp/FootballData/master/data/Serie_A/2015-16/2015-16_Serie_A.csv", "Serie A 2015-16")

# 7. روابط بديلة لكأس العالم
test_url("https://raw.githubusercontent.com/openfootball/worldcup.json/master/2022/worldcup.json", "كأس العالم 2022")

# 8. مصدر بديل للدوريات
test_url("https://raw.githubusercontent.com/openfootball/football.json/master/data/2015/en.1.json", "Premier League (openfootball)")

# ========== تقرير الأخطاء ==========
print("\n" + "="*70, flush=True)
print("📊 تقرير التشخيص:")
print("="*70, flush=True)
print(f"✅ المصادر الناجحة: {success_count}/8")
print(f"❌ المصادر الفاشلة: {len(errors)}/8")

if errors:
    print("\n🔴 تفاصيل الأخطاء:")
    for i, err in enumerate(errors, 1):
        print(f"   {i}. {err}")

print("\n" + "="*70, flush=True)
print("🔍 تحليل المشكلة:")
print("="*70, flush=True)

if success_count == 0:
    print("❌ جميع المصادر فشلت!")
    print("   الأسباب المحتملة:")
    print("   1. GitHub raw URLs تغيرت أو حذفت")
    print("   2. المستودعات تغير هيكلها")
    print("   3. GitHub يحظر الطلبات من GitHub Actions?")
    print("\n💡 الحل المقترح:")
    print("   البحث عن مصادر جديدة محدثة")
else:
    print(f"✅ {success_count} مصدر شغال. نقدر نكمل معهم.")

print("="*70, flush=True)
