import os
import requests
import logging
from loguru import logger

# إعداد Loguru
logger.add(lambda msg: print(msg, end=""), format="{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}", level="INFO")

class DSTWR_Sync_Engine:
    def __init__(self):
        self.monks_key = os.getenv("SPORTMONKS_KEY")
        self.sup_key = os.getenv("SUPABASE_KEY")
        self.sup_url = "https://nugskdozmxlgrnkfsxlg.supabase.co/rest/v1/players"
        
        # تصحيح الخطأ: تم إصلاح الـ f-string هنا
        self.sup_headers = {
            "apikey": self.sup_key,
            "Authorization": f"Bearer {self.sup_key}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates"
        }

    def push_to_supabase(self, player_data):
        try:
            response = requests.post(self.sup_url, headers=self.sup_headers, json=player_data, timeout=10)
            
            if response.status_code in [200, 201]:
                logger.info(f"✅ تم بنجاح: {player_data.get('name')}")
            else:
                # هذه الرسالة ستكشف لنا لماذا يرفض سوبربيز البيانات (كود 400)
                logger.error(f"❌ فشل رفع {player_data.get('name')} | الكود: {response.status_code} | الرسالة: {response.text}")
                
        except Exception as e:
            logger.error(f"❌ خطأ في الاتصال بسوبربيز: {e}")

    def run(self):
        logger.info("🚀 بدء تشغيل المحرك بعد تصحيح الأخطاء...")
        url = f"https://api.sportmonks.com/v3/football/players?api_token={self.monks_key}&include=team;country;position"
        
        try:
            res = requests.get(url, timeout=20)
            if res.status_code != 200:
                logger.error(f"❌ فشل الاتصال بـ Sportmonks | الكود: {res.status_code}")
                return

            players = res.json().get('data', [])
            logger.info(f"🔍 تم استلام {len(players)} لاعب.")

            for p in players:
                # نرسل البيانات الأساسية المطابقة للجدول
                payload = {
                    "id": p['id'],
                    "name": p.get('display_name', 'Unknown')
                    # ملاحظة: إذا استمر خطأ 400، سنعرف السبب من رسالة الخطأ في الـ Log
                }
                self.push_to_supabase(payload)
                
        except Exception as e:
            logger.error(f"❌ خطأ عام: {e}")

if __name__ == "__main__":
    engine = DSTWR_Sync_Engine()
    engine.run()
