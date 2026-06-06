import os
import requests
import logging
from loguru import logger

# إعداد Loguru لتتبع احترافي
logger.add(lambda msg: print(msg, end=""), format="{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}", level="INFO")

class DSTWR_Sync_Engine:
    def __init__(self):
        self.monks_key = os.getenv("SPORTMONKS_KEY")
        # تأكد أن هذا الرابط هو رابط الـ API الخاص بجدولك في سوبربيز
        self.sup_url = "https://nugskdozmxlgrnkfsxlg.supabase.co/rest/v1/players"
        self.sup_headers = {
            "apikey": os.getenv("SUPABASE_KEY"),
            "Authorization": f"Bearer {os.getenv("SUPABASE_KEY")}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates"
        }

    def push_to_supabase(self, player_data):
        try:
            response = requests.post(self.sup_url, headers=self.sup_headers, json=player_data, timeout=10)
            
            if response.status_code in [200, 201]:
                logger.info(f"✅ تم بنجاح: {player_data.get('name')}")
            else:
                # هنا ستظهر رسالة الخطأ الحقيقية من سوبربيز التي نحتاجها للتشخيص
                logger.error(f"❌ فشل رفع {player_data.get('name')} | الكود: {response.status_code} | الرسالة: {response.text}")
                
        except Exception as e:
            logger.error(f"❌ خطأ في الاتصال بسوبربيز: {e}")

    def run(self):
        logger.info("🚀 بدء تشغيل المحرك الشامل للبيانات...")
        url = f"https://api.sportmonks.com/v3/football/players?api_token={self.monks_key}&include=team;country;position"
        
        try:
            res = requests.get(url, timeout=20)
            if res.status_code != 200:
                logger.error(f"❌ فشل الاتصال بـ Sportmonks | الكود: {res.status_code}")
                return

            players = res.json().get('data', [])
            logger.info(f"🔍 تم استلام {len(players)} لاعب من المصدر.")

            for p in players:
                # نرسل البيانات الأساسية (تأكد أن أسماء المفاتيح تطابق أعمدة الجدول في سوبربيز)
                payload = {
                    "id": p['id'],
                    "name": p.get('display_name', 'Unknown'),
                    "age": p.get('age'),
                    "nationality": p.get('country', {}).get('name') if p.get('country') else None,
                    "team_name": p.get('team', {}).get('name') if p.get('team') else None,
                    "position": p.get('position', {}).get('name') if p.get('position') else None
                }
                self.push_to_supabase(payload)
                
        except Exception as e:
            logger.error(f"❌ خطأ عام: {e}")

if __name__ == "__main__":
    engine = DSTWR_Sync_Engine()
    engine.run()
