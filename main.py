import os
import requests
import json

# جلب المفاتيح من خزانة GitHub Secrets
KEYS = {
    "isports": os.getenv("ISPORTS_KEY"),
    "sportmonks": os.getenv("SPORTMONKS_KEY"),
    "api_football": os.getenv("API_FOOTBALL_KEY"),
    "football_data": os.getenv("FOOTBALL_DATA_KEY")
}

def fetch_live_data():
    # هنا سنطبق خوارزمية التبديل (Failover)
    # 1. حاول iSportsAPI
    # 2. إذا فشل، انتقل لـ Sportmonks
    # 3. ادمج البيانات في ملف واحد
    data = {"status": "success", "matches": []}
    # (سيتم إضافة منطق السحب هنا لكل مصدر)
    return data

def save_to_final_json(data):
    with open('live_data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    combined_data = fetch_live_data()
    save_to_final_json(combined_data)
    print("تم تحديث البيانات بنجاح في السحابة!")
  
