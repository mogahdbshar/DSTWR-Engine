import os
import requests
import json

# جلب المفاتيح من GitHub Secrets
KEYS = {
    "isports": os.getenv("ISPORTS_KEY"),
    "sportmonks": os.getenv("SPORTMONKS_KEY"),
    "api_football": os.getenv("API_FOOTBALL_KEY"),
    "football_data": os.getenv("FOOTBALL_DATA_KEY")
}

def fetch_data():
    # هذا هيكل البيانات الموحد الذي سيقرأه تطبيقك
    final_data = {
        "metadata": {"source": "DSTWR-Engine", "status": "active"},
        "matches": []
    }

    # مثال: جلب البيانات من football-data.org (الدوريات والترتيب)
    try:
        url = "https://api.football-data.org/v4/competitions/PL/standings"
        headers = {'X-Auth-Token': KEYS["football_data"]}
        response = requests.get(url, headers=headers).json()
        
        # تحويل البيانات إلى تنسيقنا الموحد (التعريب)
        for item in response['standings'][0]['table']:
            final_data['matches'].append({
                "team": item['team']['shortName'],
                "position": item['position'],
                "points": item['points'],
                "logo": item['team']['crest']
            })
    except Exception as e:
        print(f"Error fetching data: {e}")

    return final_data

def main():
    data = fetch_data()
    # حفظ الملف ليرفعه GitHub تلقائياً
    with open('live_data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print("تمت عملية الدمج والتعريب بنجاح!")

if __name__ == "__main__":
    main()
