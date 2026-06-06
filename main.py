import os
import requests
import time
from loguru import logger

# إعدادات طباعة احترافية ونظيفة
logger.add(
    lambda msg: print(msg, end=""), 
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}", 
    level="INFO"
)

class DSTWR_Ultra_Database_Engine:
    def __init__(self):
        # جلب المفاتيح من بيئة العمل
        self.api_key = os.getenv("API_FOOTBALL_KEY")
        self.sup_key = os.getenv("SUPABASE_KEY")
        self.sup_url = "https://nugskdozmxlgrnkfsxlg.supabase.co/rest/v1/players"
        
        self.headers_api = {"x-apisports-key": self.api_key}
        self.headers_sup = {
            "apikey": self.sup_key,
            "Authorization": f"Bearer {self.sup_key}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates"  # دمج وتحديث البيانات تلقائياً لمنع التكرار
        }
        
        # أقوى الدوريات العالمية التي سنبني بها القاعدة الضخمة
        self.leagues = {
            39: "الدوري الإنجليزي الممتاز",
            140: "الدوري الإسباني (La Liga)",
            135: "الدوري الإيطالي (Serie A)",
            78: "الدوري الألماني (Bundesliga)",
            61: "الدوري الفرنسي (Ligue 1)"
        }
        self.current_season = 2025  # الموسم الحالي المستقر للبيانات

    def sync_players(self):
        logger.info("🔥 [DSTWR ENGINE] تم إطلاق المحرك الخارق لبناء القاعدة الضخمة...")
        
        if not self.api_key or not self.sup_key:
            logger.error("❌ خطأ بيئي: تأكد من إضافة API_FOOTBALL_KEY و SUPABASE_KEY في الـ Secrets!")
            return

        total_uploaded = 0

        # المرور على كل دوري في القائمة
        for league_id, league_name in self.leagues.items():
            logger.info(f"=== 🏟️ بدء جلب بيانات: {league_name} (ID: {league_id}) ===")
            
            page = 1
            while True:
                logger.info(f"📡 جاري سحب الصفحة {page} من الـ API...")
                url = f"https://v3.football.api-sports.io/players?league={league_id}&season={self.current_season}&page={page}"
                
                try:
                    res = requests.get(url, headers=self.headers_api, timeout=30)
                    
                    if res.status_code != 200:
                        logger.error(f"❌ خطأ من السيرفر بكود: {res.status_code}")
                        break
                        
                    json_data = res.json()
                    results = json_data.get('response', [])
                    
                    # إذا انتهت الصفحات ولم نجد لاعبين نخرج من الحلقة وننتقل للدوري التالي
                    if not results:
                        logger.info(f"✨ انتهت صفحات {league_name}.")
                        break
                    
                    logger.info(f"📦 تم العثور على {len(results)} لاعب في الصفحة {page}. جاري التحضير للرفع...")
                    
                    batch_payload = []
                    for item in results:
                        player = item.get('player', {})
                        statistics = item.get('statistics', [{}])[0]  # جلب إحصائيات الفريق الحالي
                        
                        # هيكلة البيانات الضخمة والشاملة لكل لاعب
                        player_payload = {
                            "id": player.get('id'),
                            "name": player.get('name', 'Unknown'),
                            "firstname": player.get('firstname'),
                            "lastname": player.get('lastname'),
                            "age": player.get('age'),
                            "nationality": player.get('nationality'),
                            "height": player.get('height'),
                            "weight": player.get('weight'),
                            "injured": player.get('injured'),
                            "photo": player.get('photo'),
                            "team_name": statistics.get('team', {}).get('name'),
                            "league_name": league_name
                        }
                        batch_payload.append(player_payload)
                    
                    # رفع دفعة كاملة (Batch) لتسريع العملية وتقليل الضغط على السيرفر
                    if batch_payload:
                        sup_res = requests.post(self.sup_url, headers=self.headers_sup, json=batch_payload, timeout=30)
                        if sup_res.status_code in [200, 201]:
                            total_uploaded += len(batch_payload)
                            logger.info(f"✅ تم بنجاح رفع وتحديث {len(batch_payload)} لاعب في Supabase.")
                        else:
                            logger.error(f"❌ فشل رفع الدفعة! كود سوبربيز: {sup_res.status_code} | التفاصيل: {sup_res.text}")
                    
                    # الانتقال للصفحة التالية
                    page += 1
                    
                    # الحسابات المجانية تطلب راحة ثانية بين الطلبات تجنباً للحظر (Rate Limit)
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"❌ حدث خطأ غير متوقع أثناء معالجة البيانات: {e}")
                    break
                    
        logger.info(f"🏁 [مهمة ناجحة] تم الانتهاء بالكامل! إجمالي اللاعبين في قاعدتك الآن: {total_uploaded} لاعب.")

if __name__ == "__main__":
    engine = DSTWR_Ultra_Database_Engine()
    engine.sync_players()
