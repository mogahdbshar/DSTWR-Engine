import os
import requests
import sys

sys.stdout.reconfigure(line_buffering=True)

SUPABASE_URL = "https://nugskdozmxlgrnkfsxlg.supabase.co/rest/v1"
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

print("\n🔍 فحص هيكل جدول matches:", flush=True)

# جلب معلومات الأعمدة
resp = requests.get(f"{SUPABASE_URL}/matches?limit=1", headers=headers)

if resp.status_code == 200:
    if resp.json():
        columns = list(resp.json()[0].keys())
        print(f"   ✅ الأعمدة: {', '.join(columns)}", flush=True)
    else:
        print(f"   ⚠️ الجدول فاضي، نحتاج نجرب insert تجريبي", flush=True)
        
        # تجربة insert تجريبي لمعرفة الأعمدة المطلوبة
        test = {"id": "test_123"}
        resp2 = requests.post(f"{SUPABASE_URL}/matches", headers=headers, json=test)
        if resp2.status_code == 400:
            import re
            missing = re.findall(r"'(\w+)' column", resp2.text)
            print(f"   📋 الأعمدة المطلوبة: {missing}", flush=True)
else:
    print(f"   ❌ فشل: {resp.status_code}", flush=True)
