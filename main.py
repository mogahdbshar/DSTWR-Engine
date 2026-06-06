import os
import requests
import soccerdata as sd
from loguru import logger

logger.add(lambda msg: print(msg, end=""), format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}", level="INFO")

class DSTWR_SoccerData_Engine:
    def __init__(self):
        self.sup_key = os.getenv("SUPABASE_KEY")
        self.sup_url = "https://nugskdozmxlgrnkfsxlg.supabase.co/rest/v1/players"
        self.headers_sup = {
            "apikey": self.sup_key,
            "Authorization": f"Bearer {self.sup_key}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates"
        }

    def run(self):
        logger.info("🚀 [DSTWR] بدء تشغيل المحرك المعتمد على SoccerData...")
        
        try:
            # استخدام كشاف FBref لجلب إحصائيات اللاعبين في الدوري الإنجليزي (ENG-Premier League)
            # ملاحظة: يمكنك تغيير الموسم إلى '2025' أو '2026' حسب المتوفر في الموقع
            logger.info("📡 جاري قشط بيانات اللاعبين من FBref...")
            fbref = sd.FBref(leagues="ENG-Premier League", seasons="2025")
            
            # جلب جدول إحصائيات اللاعبين العام
            df = fbref.read_player_season_stats(stat_type="standard")
            
            # إعادة ضبط الـ Index لسهولة قراءة أسماء اللاعبين
            df = df.reset_index()
            
            # استخراج اللاعبين الفريدين لمنع التكرار قبل الرفع
            unique_players = df[['player']].drop_duplicates()
            logger.info(f"📊 تم العثور على {len(unique_players)} لاعب فريد في الدوري.")

            payload = []
            # توليد معرف (ID) رقمي بسيط أو استخدام الاسم كـ ID مؤقت إذا كان جدولك يقبل ذلك
            for index, row in unique_players.iterrows():
                player_name = row['player']
                
                # هيكلة البيانات لتطابق جدولك (id و name)
                # توليد ID فريد بناءً على الـ index الحالي لتفادي مشاكل الـ Primary Key
                payload.append({
                    "id": 900000 + index, # نطاق مخصص للاعبي السكرايبر
                    "name": player_name
                })

            if payload:
                logger.info(f"📦 جاري رفع {len(payload)} لاعب إلى Supabase...")
                res = requests.post(self.sup_url, headers=self.headers_sup, json=payload, timeout=30)
                
                if res.status_code in [200, 201]:
                    logger.info("✅ مبروك يا عامر! نجح القشط والرفع بالكامل بدون أي مفاتيح API!")
                else:
                    logger.error(f"❌ فشل الرفع لسوبربيز | كود: {res.status_code} | الرد: {res.text}")
            else:
                logger.warning("⚠️ لم يتم العثور على لاعبين في الملف المستخرج.")

        except Exception as e:
            logger.error(f"❌ حدث خطأ أثناء تشغيل محرك SoccerData: {e}")

if __name__ == "__main__":
    DSTWR_SoccerData_Engine().run()
