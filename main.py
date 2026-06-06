import os
import requests
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')

class DSTWR_Diagnostic_Engine:
    def __init__(self):
        self.monks_key = os.getenv("SPORTMONKS_KEY")
        self.sup_url = "https://nugskdozmxlgrnkfsxlg.supabase.co/rest/v1/players"
        self.sup_headers = {
            "apikey": os.getenv("SUPABASE_KEY"),
            "Authorization": f"Bearer {os.getenv('SUPABASE_KEY')}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates"
        }

    def run_diagnosis(self):
        logging.info("🚀 بدء فحص اتصال Sportmonks...")
        # نستخدم رابط عام للبيانات
        url = f"https://api.sportmonks.com/v3/football/players?api_token={self.monks_key}"
        
        try:
            res = requests.get(url, timeout=20)
            logging.info(f"🔍 [الاستجابة] كود الحالة: {res.status_code}")
            
            data_json = res.json()
            
            # طباعة هيكل الرد لمعرفة أين تقع البيانات
            logging.info(f"🔍 [هيكل البيانات] مفاتيح الرد: {list(data_json.keys())}")
            
            if 'data' in data_json:
                data = data_json['data']
                logging.info(f"🔍 [الكمية] عدد اللاعبين الموجودين: {len(data)}")
                
                if len(data) > 0:
                    logging.info(f"✅ أول لاعب هو: {data[0].get('display_name')}")
                    # محاولة رفع أول لاعب
                    player = data[0]
                    payload = {
                        "id": player['id'],
                        "name": player.get('display_name', 'Unknown'),
                        "age": player.get('age', 0)
                    }
                    upload = requests.post(self.sup_url, headers=self.sup_headers, json=payload)
                    logging.info(f"📤 [رفع] نتيجة محاولة رفع أول لاعب: {upload.status_code}")
                else:
                    logging.warning("⚠️ الرد يحتوي على قائمة فارغة!")
            else:
                logging.error(f"❌ لم يتم العثور على مفتاح 'data' في الرد. الرد الكامل: {data_json}")
                
        except Exception as e:
            logging.error(f"❌ خطأ في الاتصال: {e}")

if __name__ == "__main__":
    DSTWR_Diagnostic_Engine().run_diagnosis()
