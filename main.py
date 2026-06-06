import os
import requests
import time
from loguru import logger

# إعداد الطباعة بشكل نظيف
logger.add(lambda msg: print(msg, end=""), format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}", level="INFO")

class DSTWR_Universal_Engine:
    def __init__(self):
        # جلب جميع المفاتيح اللي عندك حرفياً من البيئة
        self.api_football_key = os.getenv("API_FOOTBALL_KEY")
        self.sportmonks_key = os.getenv("SPORTMONKS_KEY")
        self.football_data_key = os.getenv("FOOTBALL_DATA_KEY")
        self.isports_key = os.getenv("ISPORTS_KEY")
        
        # إعدادات سوبربيز الثابتة
        self.sup_key = os.getenv("SUPABASE_KEY")
        self.sup_url = "https://nugskdozmxlgrnkfsxlg.supabase.co/rest/v1/players"
        self.headers_sup = {
            "apikey": self.sup_key,
            "Authorization": f"Bearer {self.sup_key}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates"
        }

    def upload_to_supabase(self, players_list):
        """دالة موحدة لرفع أي قائمة لاعبين إلى سوبربيز"""
        if not players_list:
            return
        
        logger.info(f"📦 جاري تحضير دفعة من {len(players_list)} لاعب للرفع إلى Supabase...")
        try:
            res = requests.post(self.sup_url, headers=self.headers_sup, json=players_list, timeout=30)
            if res.status_code in [200, 201]:
                logger.info(f"✅ نجح الرفع! تم تحديث/إضافة {len(players_list)} لاعب بنجاح.")
            else:
                logger.error(f"❌ فشل الرفع لسوبربيز | كود: {res.status_code} | الرد: {res.text}")
        except Exception as e:
            logger.error(f"❌ خطأ أثناء الرفع: {e}")

    def try_sportmonks(self):
        """المحرك الأول: Sportmonks API v3"""
        if not self.sportmonks_key:
            return False
        
        logger.info("📡 [محرك Sportmonks] جاري محاولة جلب اللاعبين...")
        # طلب مسار اللاعبين الرسمي لـ Sportmonks v3
        url = f"https://api.sportmonks.com/v3/football/players?api_token={self.sportmonks_key}"
        try:
            res = requests.get(url, timeout=30)
            if res.status_code == 200:
                data = res.json().get('data', [])
                logger.info(f"🎉 نجح اتصال Sportmonks! وجدنا {len(data)} لاعب.")
                
                payload = []
                for p in data:
                    payload.append({
                        "id": p.get('id'),
                        "name": p.get('display_name') or p.get('name', 'Unknown'),
                        "firstname": p.get('firstname'),
                        "lastname": p.get('lastname'),
                        "nationality": p.get('nationality', {}).get('name') if isinstance(p.get('nationality'), dict) else None,
                        "photo": p.get('image_path'),
                        "league_name": "Sportmonks Data"
                    })
                self.upload_to_supabase(payload)
                return True
            else:
                logger.warning(f"⚠️ مفتاح Sportmonks رد بكود: {res.status_code}")
        except Exception as e:
            logger.error(f"❌ خطأ محرك Sportmonks: {e}")
        return False

    def try_api_football(self):
        """المحرك الثاني: API-Football (RapidAPI/Api-Sports)"""
        if not self.api_football_key:
            return False
            
        logger.info("📡 [محرك API-Football] جاري محاولة الجلب الدوري الإنجليزي 2025...")
        url = "https://v3.football.api-sports.io/players?league=39&season=2025&page=1"
        headers = {"x-apisports-key": self.api_football_key}
        
        try:
            res = requests.get(url, headers=headers, timeout=30)
            json_data = res.json()
            
            if json_data.get('response'):
                results = json_data['response']
                logger.info(f"🎉 نجح اتصال API-Football! وجدنا {len(results)} لاعب.")
                
                payload = []
                for item in results:
                    p = item.get('player', {})
                    st = item.get('statistics', [{}])[0]
                    payload.append({
                        "id": p.get('id'),
                        "name": p.get('name'),
                        "firstname": p.get('firstname'),
                        "lastname": p.get('lastname'),
                        "age": p.get('age'),
                        "nationality": p.get('nationality'),
                        "photo": p.get('photo'),
                        "team_name": st.get('team', {}).get('name'),
                        "league_name": "Premier League"
                    })
                self.upload_to_supabase(payload)
                return True
            else:
                logger.warning(f"⚠️ مفتاح API-Football لم يرجع بيانات أو به خطأ: {json_data.get('errors')}")
        except Exception as e:
            logger.error(f"❌ خطأ محرك API-Football: {e}")
        return False

    def try_football_data(self):
        """المحرك الثالث: Football-Data.org"""
        if not self.football_data_key:
            return False
            
        logger.info("📡 [محرك Football-Data] جاري محاولة جلب الفرق واللاعبين...")
        url = "https://api.football-data.org/v4/competitions/PL/teams" # الدوري الانجليزي كمثال
        headers = {"X-Auth-Token": self.football_data_key}
        
        try:
            res = requests.get(url, headers=headers, timeout=30)
            if res.status_code == 200:
                teams = res.json().get('teams', [])
                logger.info(f"🎉 نجح اتصال Football-Data! جاري سحب لاعبي الفرق...")
                
                payload = []
                for team in teams[:3]: # نأخذ أول 3 فرق لتفادي الـ Rate Limit
                    squad = team.get('squad', [])
                    for p in squad:
                        payload.append({
                            "id": p.get('id'),
                            "name": p.get('name'),
                            "team_name": team.get('name'),
                            "league_name": "Premier League (FD)"
                        })
                self.upload_to_supabase(payload)
                return True
            else:
                logger.warning(f"⚠️ مفتاح Football-Data رد بكود: {res.status_code}")
        except Exception as e:
            logger.error(f"❌ خطأ محرك Football-Data: {e}")
        return False

    def start_engine(self):
        logger.info("🚀 [DSTWR] تم إطلاق المحرك الشامل لفحص واصطياد المفاتيح الشغالة...")
        
        # تجربة المحركات واحد تلو الآخر، أول واحد ينجح ويجيب بيانات بيوقف الباقي عشان ما نخلص الكوتا
        if self.try_sportmonks():
            logger.info("🏁 تمت العملية بنجاح عبر محرك Sportmonks.")
            return
            
        if self.try_api_football():
            logger.info("🏁 تمت العملية بنجاح عبر محرك API-Football.")
            return
            
        if self.try_football_data():
            logger.info("🏁 تمت العملية بنجاح عبر محرك Football-Data.")
            return
            
        logger.error("❌ انتهت المحاولات! كل المفاتيح اللي أرسلتها واجهت مشاكل في الروابط أو الصلاحيات.")

if __name__ == "__main__":
    DSTWR_Universal_Engine().start_engine()
