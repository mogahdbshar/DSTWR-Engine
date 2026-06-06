import os
import requests
from loguru import logger

# إعداد اللوجر
logger.add(lambda msg: print(msg, end=""), format="{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}", level="INFO")

class DSTWR_Final_Engine:
    def __init__(self):
        # المفاتيح من متغيرات البيئة
        self.api_key = os.getenv("API_FOOTBALL_KEY")
        self.sup_key = os.getenv("SUPABASE_KEY")
        self.sup_url = "https://nugskdozmxlgrnkfsxlg.supabase.co/rest/v1/players"
        
        self.headers_api = {"x-apisports-key": self.api_key}
        self.headers_sup = {
            "apikey": self.sup_key,
            "Authorization": f"Bearer {self.sup_key}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates"
        }

    def run(self):
        logger.info("🚀 بدء تشغيل المحرك النهائي...")
        
        # الرابط الصحيح والموثق لـ API-Football للحصول على قائمة اللاعبين (الدوري الإنجليزي كمثال)
        url = "https://v3.football.api-sports.io/players?league=39&season=2025"
        
        try:
            logger.info("📡 الاتصال بـ API-Football...")
            res = requests.get(url, headers=self.headers_api, timeout=20)
            
            if res.status_code != 200:
                logger.error(f"❌ فشل الاتصال! كود الحالة: {res.status_code} | الرسالة: {res.text}")
                return

            data = res.json().get('response', [])
            logger.info(f"✅ تم جلب {len(data)} لاعب بنجاح.")

            for item in data:
                player = item.get('player', {})
                payload = {
                    "id": player.get('id'),
                    "name": player.get('name', 'Unknown')
                }
                
                # رفع البيانات لسوبربيز
                resp = requests.post(self.sup_url, headers=self.headers_sup, json=payload)
                if resp.status_code in [200, 201]:
                    logger.info(f"✨ تم رفع اللاعب: {payload['name']}")
                else:
                    logger.error(f"⚠️ فشل رفع {payload['name']} | كود: {resp.status_code} | تفاصيل: {resp.text}")
                    
        except Exception as e:
            logger.error(f"❌ حدث خطأ غير متوقع: {e}")

if __name__ == "__main__":
    DSTWR_Final_Engine().run()
