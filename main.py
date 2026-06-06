import os
import requests
import time
from loguru import logger

logger.add(lambda msg: print(msg, end=""), format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}", level="INFO")

class DSTWR_Mega_Database_Engine:
    def __init__(self):
        # جمع كل المفاتيح من الـ Environment Variables الممررة من جيت هاب
        self.api_key = os.getenv("API_FOOTBALL_KEY")
        self.sup_key = os.getenv("SUPABASE_KEY")
        self.sup_url = "https://nugskdozmxlgrnkfsxlg.supabase.co/rest/v1/players"
        
        self.headers_sup = {
            "apikey": self.sup_key,
            "Authorization": f"Bearer {self.sup_key}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates"
        }
        
        # قائمة أقوى الدوريات لجلب قاعدة بيانات ضخمة
        self.leagues = {
            39: "الدوري الإنجليزي الممتاز",
            140: "الدوري الإسباني (La Liga)",
            135: "الدوري الإيطالي (Serie A)",
            78: "الدوري الألماني (Bundesliga)",
            61: "الدوري الفرنسي (Ligue 1)"
        }
        self.season = 2025 # الموسم الأكثر استقراراً للبيانات الكاملة

    def sync_api_football(self):
        if not self.api_key:
            logger.warning("⚠️ مفتاح API_FOOTBALL_KEY غير متوفر في البيئة حالياً.")
            return False

        logger.info("🔥 [DSTWR] تم تفعيل محرك API-Football المحدث... جاري سحب الدوريات صفحة صفحة.")
        total_uploaded = 0
        headers_api = {"x-apisports-key": self.api_key}

        for league_id, league_name in self.leagues.items():
            logger.info(f"🏟️ جاري جلب: {league_name}")
            page = 1
            while True:
                url = f"https://v3.football.api-sports.io/players?league={league_id}&season={self.season}&page={page}"
                try:
                    res = requests.get(url, headers=headers_api, timeout=30)
                    json_data = res.json()
                    
                    if "errors" in json_data and json_data["errors"]:
                        if "token" in json_data["errors"]:
                            logger.error(f"❌ خطأ بالمفتاح: {json_data['errors']['token']}")
                            return False

                    results = json_data.get('response', [])
                    if not results:
                        logger.info(f"✨ انتهت صفحات {league_name}.")
                        break

                    batch_payload = []
                    for item in results:
                        player = item.get('player', {})
                        stats = item.get('statistics', [{}])[0]
                        batch_payload.append({
                            "id": player.get('id'),
                            "name": player.get('name', 'Unknown'),
                            "firstname": player.get('firstname'),
                            "lastname": player.get('lastname'),
                            "age": player.get('age'),
                            "nationality": player.get('nationality'),
                            "photo": player.get('photo'),
                            "team_name": stats.get('team', {}).get('name'),
                            "league_name": league_name
                        })

                    if batch_payload:
                        sup_res = requests.post(self.sup_url, headers=self.headers_sup, json=batch_payload, timeout=30)
                        if sup_res.status_code in [200, 201]:
                            total_uploaded += len(batch_payload)
                            logger.info(f"✅ تم رفع {len(batch_payload)} لاعب إلى Supabase.")
                        else:
                            logger.error(f"❌ خطأ سوبربيز: {sup_res.text}")

                    page += 1
                    time.sleep(1) # تجنب الحظر

                except Exception as e:
                    logger.error(f"❌ خطأ أثناء التشغيل: {e}")
                    break

        logger.info(f"🏁 اكتمل الرفع الشامل! إجمالي اللاعبين المضافين: {total_uploaded}")
        return True

    def run(self):
        logger.info("🚀 إطلاق المحرك الشامل الضخم لإصطياد المفاتيح الناجحة...")
        # تشغيل محرك سحب البيانات الرئيسي
        success = self.sync_api_football()
        if not success:
            logger.error("❌ فشل تشغيل المحرك الرئيسي بسبب إعدادات المفتاح بالـ YAML. يرجى تعديل الـ YAML كما هو موضح.")

if __name__ == "__main__":
    DSTWR_Mega_Database_Engine().run()
