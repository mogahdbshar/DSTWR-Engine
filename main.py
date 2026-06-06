import os
import requests
from loguru import logger

class DSTWR_Multi_Engine:
    def __init__(self):
        # قاموس يربط المفاتيح بالروابط الصحيحة لكل مزود
        self.providers = {
            "SPORTMONKS": {
                "key": os.getenv("SPORTMONKS_KEY"),
                "url": "https://api.sportmonks.com/v3/football/players"
            },
            "API_FOOTBALL": {
                "key": os.getenv("API_FOOTBALL_KEY"),
                "url": "https://v3.football.api-sports.io/players"
            }
        }
        self.sup_url = "https://nugskdozmxlgrnkfsxlg.supabase.co/rest/v1/players"
        self.sup_headers = {
            "apikey": os.getenv("SUPABASE_KEY"),
            "Authorization": f"Bearer {os.getenv('SUPABASE_KEY')}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates"
        }

    def fetch_data(self):
        # نبدأ بـ API-Football (لأنه الأكثر شيوعاً)
        provider = self.providers["API_FOOTBALL"]
        headers = {"x-apisports-key": provider["key"]}
        params = {"league": 39, "season": 2025} # الدوري الإنجليزي كمثال
        
        logger.info(f"🚀 محاولة الاتصال بـ API-Football...")
        res = requests.get(provider["url"], headers=headers, params=params)
        
        if res.status_code == 200:
            logger.info("✅ نجح الاتصال بـ API-Football!")
            return res.json().get('response', [])
        else:
            logger.error(f"❌ فشل الاتصال بـ API-Football | الكود: {res.status_code} | الرسالة: {res.text}")
            return []

    def run(self):
        data = self.fetch_data()
        for item in data[:5]: # رفع تجريبي
            player = item.get('player', {})
            payload = {"id": player.get('id'), "name": player.get('name')}
            requests.post(self.sup_url, headers=self.sup_headers, json=payload)
            logger.info(f"✅ تم معالجة: {payload['name']}")

if __name__ == "__main__":
    DSTWR_Multi_Engine().run()
