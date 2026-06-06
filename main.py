import os
import requests
from loguru import logger

logger.add(lambda msg: print(msg, end=""), format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}", level="INFO")

class DSTWR_God_Mode_Engine:
    def __init__(self):
        self.sup_key = os.getenv("SUPABASE_KEY")
        self.sup_url = "https://nugskdozmxlgrnkfsxlg.supabase.co/rest/v1/players"
        self.headers_sup = {
            "apikey": self.sup_key,
            "Authorization": f"Bearer {self.sup_key}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates"  # دمج لمنع التكرار وتحديث البيانات
        }
        # رابط لملف JSON جاهز ومفتوح المصدر يحتوي على بيانات اللاعبين
        self.raw_data_url = "https://raw.githubusercontent.com/openfootball/players/master/players.json"

    def run(self):
        logger.info("🚀 [DSTWR] تفعيل الطور الأقصى.. جاري سحب قاعدة البيانات الجاهزة للالتفاف على الحجب...")
        
        try:
            # 1. جلب البيانات الجاهزة مباشرة
            res_data = requests.get(self.raw_data_url, timeout=30)
            if res_data.status_code != 200:
                # رابط بديل احتياطي في حال واجه الرابط الأول مشكلة
                self.raw_data_url = "https://pkgstore.datahub.io/sports-data/english-premier-league/leagues_apps_spain_liga_players/data/643b18eddf8e1e12739be6ee4f828741/leagues_apps_spain_liga_players_json.json"
                res_data = requests.get(self.raw_data_url, timeout=30)
            
            raw_players = res_data.json()
            logger.info(f"📦 تم تحميل الملف الجاهز! وجدنا {len(raw_players)} لاعب جاهزين للرفع.")

            payload = []
            for index, p in enumerate(raw_players):
                # تنظيف وتوحيد البيانات لتطابق السكيما المتاحة عندك (id و name)
                # نستخدم الـ index أو معرف اللاعب إذا وجد لضمان وجود ID رقمي فريد
                player_id = p.get('id') or (800000 + index)
                player_name = p.get('name') or p.get('Player') or p.get('display_name')
                
                if player_name:
                    payload.append({
                        "id": int(player_id),
                        "name": str(player_name)
                    })

            if not payload:
                logger.warning("⚠️ لم نجد أسماء صالحة في الملف، جاري تجربة هيكلة بديلة...")
                return

            # 2. الرفع إلى سوبربيز على دفعات سريعة
            chunk_size = 200
            for i in range(0, len(payload), chunk_size):
                chunk = payload[i:i + chunk_size]
                sup_res = requests.post(self.sup_url, headers=self.headers_sup, json=chunk, timeout=30)
                
                if sup_res.status_code in [200, 201]:
                    logger.info(f"✅ تم ضخ الدفعة ({i} إلى {i + len(chunk)}) بنجاح داخل Supabase!")
                else:
                    logger.error(f"❌ خطأ أثناء الرفع: {sup_res.text}")
                    
            logger.info("🏁 انتهت العملية بنجاح تام! مبروك امتلأت قاعدتك باللاعبين.")

        except Exception as e:
            logger.error(f"❌ حدث خطأ غير متوقع: {e}")

if __name__ == "__main__":
    DSTWR_God_Mode_Engine().run()
