import os
import requests
import time
from loguru import logger

logger.add(lambda msg: print(msg, end=""), format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}", level="INFO")

class DSTWR_Ultra_Database_Engine:
    def __init__(self):
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
        
        self.leagues = {
            39: "الدوري الإنجليزي الممتاز",
            140: "الدوري الإسباني (La Liga)"
        }
        # تجربة موسمين لضمان اصطياد البيانات
        self.seasons_to_try = [2025, 2026]

    def sync_players(self):
        logger.info("🔥 [DSTWR ENGINE] بدء الفحص الشامل للمواسم والدوريات...")
        total_uploaded = 0

        for season in self.seasons_to_try:
            for league_id, league_name in self.leagues.items():
                logger.info(f"🏟️ فحص: {league_name} | الموسم: {season}...")
                
                url = f"https://v3.football.api-sports.io/players?league={league_id}&season={season}&page=1"
                
                try:
                    res = requests.get(url, headers=self.headers_api, timeout=30)
                    json_data = res.json()
                    
                    # طباعة تشخيصية لنرى ما الذي يرسله السيرفر فعلياً
                    logger.info(f"📡 رد السيرفر الأولي: {str(json_data)[:200]}")
                    
                    results = json_data.get('response', [])
                    
                    if not results:
                        logger.warning(f"⚠️ لا توجد بيانات في هذا الموسم {season} لهذا الدوري.")
                        continue
                    
                    logger.info(f"📦 تم العثور على {len(results)} لاعب! جاري الرفع...")
                    
                    batch_payload = []
                    for item in results:
                        player = item.get('player', {})
                        statistics = item.get('statistics', [{}])[0]
                        
                        batch_payload.append({
                            "id": player.get('id'),
                            "name": player.get('name', 'Unknown'),
                            "firstname": player.get('firstname'),
                            "lastname": player.get('lastname'),
                            "age": player.get('age'),
                            "nationality": player.get('nationality'),
                            "team_name": statistics.get('team', {}).get('name'),
                            "league_name": league_name
                        })
                    
                    if batch_payload:
                        sup_res = requests.post(self.sup_url, headers=self.headers_sup, json=batch_payload, timeout=30)
                        if sup_res.status_code in [200, 201]:
                            total_uploaded += len(batch_payload)
                            logger.info(f"✅ تم رفع {len(batch_payload)} لاعب بنجاح.")
                        else:
                            logger.error(f"❌ خطأ سوبربيز: {sup_res.text}")
                            
                except Exception as e:
                    logger.error(f"❌ خطأ غير متوقع: {e}")
                    
        logger.info(f"🏁 انتهى البحث. إجمالي ما تم رفعه: {total_uploaded}")

if __name__ == "__main__":
    DSTWR_Ultra_Database_Engine().sync_players()
