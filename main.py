import os
import requests
import logging
import time
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')

class DSTWR_Direct_Fast_Engine:
    def __init__(self):
        self.base_url = "https://nugskdozmxlgrnkfsxlg.supabase.co/rest/v1"
        self.headers = {
            "apikey": os.getenv("SUPABASE_KEY"),
            "Authorization": f"Bearer {os.getenv('SUPABASE_KEY')}",
            "Content-Type": "application/json",
            "Prefer": "return=representation,resolution=merge-duplicates"
        }
        
        self.api_football_key = os.getenv("API_FOOTBALL_KEY")
        self.sportmonks_key = os.getenv("SPORTMONKS_KEY")
        self.isports_key = os.getenv("ISPORTS_KEY")

        self.leagues = [
            {"code": "PL", "af_id": 39, "name": "Premier League"},
            {"code": "PD", "af_id": 140, "name": "La Liga"},
            {"code": "CL", "af_id": 2, "name": "UEFA Champions League"},
            {"code": "SA", "af_id": 135, "name": "Serie A"},
            {"code": "BL1", "af_id": 78, "name": "Bundesliga"},
            {"code": "FL1", "af_id": 61, "name": "Ligue 1"},
            {"code": "WC", "af_id": 1, "name": "FIFA World Cup"}
        ]

    def check_response(self, context, response):
        if not response: return False
        if response.status_code in [200, 201]:
            logging.info(f"📥 [تم الرفع الحقيقي] -> {context}")
            return True
        elif response.status_code == 409:
            return True
        else:
            logging.error(f"❌ [خطأ رفع] {context} | الكود: {response.status_code}")
            return False

    def safe_request(self, method, url, **kwargs):
        # جعلنا وقت الانتظار عند الحظر 65 ثانية لضمان تصفير عداد الدقيقة بالسيرفر الخارجي
        delay = 65  
        for i in range(3):
            try:
                response = requests.request(method, url, **kwargs)
                if response.status_code == 429:
                    logging.warning(f"⏳ [حد الطلبات 429] السيرفر مقفل دقيقتنا الحالية. نوم إجباري لـ {delay} ثانية لتصفير العداد والعبور...")
                    time.sleep(delay)
                    continue
                return response
            except Exception:
                time.sleep(5)
        return None

    def fetch_stadiums_and_coaches(self):
        logging.info("⚡ [خطوة 1] جلب الملاعب والمدربين للموسم الحالي مباشرة...")
        api_headers = {"X-RapidAPI-Key": self.api_football_key, "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"}
        
        for lg in self.leagues:
            logging.info(f"🏟️ جاري فحص ملاعم وطواقم دوري: {lg['name']}")
            url = "https://api-football-v1.p.rapidapi.com/v3/teams"
            res = self.safe_request("GET", url, headers=api_headers, params={"league": lg["af_id"], "season": 2025})
            
            if res and res.status_code == 200:
                for chunk in res.json().get('response', []):
                    v = chunk.get('venue', {})
                    if v.get('id'):
                        res_v = self.safe_request("POST", f"{self.base_url}/stadiums", headers=self.headers, json={
                            "id": v.get('id'), "name": v.get('name'), "city": v.get('city'), 
                            "capacity": v.get('capacity'), "image_url": v.get('image'), "surface": v.get('surface')
                        })
                        self.check_response(f"الملعب: {v.get('name')}", res_v)
                    
                    t_id = chunk.get('team', {}).get('id')
                    coach = chunk.get('coach', {})
                    if coach.get('id'):
                        res_coach = self.safe_request("POST", f"{self.base_url}/coaches", headers=self.headers, json={
                            "id": coach.get('id'), "team_id": t_id, "name": coach.get('name'), 
                            "nationality": coach.get('nationality'), "photo_url": coach.get('photo')
                        })
                        self.check_response(f"المدرب: {coach.get('name')}", res_coach)
            
            # زيادة وقت الانتظار بين الدوريات لتهدئة معدل الدقيقة
            time.sleep(8)

    def fetch_top_stats(self):
        logging.info("⚡ [خطوة 2] جلب هدافي وصناع لعب الموسم الحالي...")
        api_headers = {"X-RapidAPI-Key": self.api_football_key, "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"}
        
        for lg in self.leagues:
            for stat_type in ["topscorers", "topassists"]:
                url = f"https://api-football-v1.p.rapidapi.com/v3/players/{stat_type}"
                res = self.safe_request("GET", url, headers=api_headers, params={"league": lg["af_id"], "season": 2025})
                if res and res.status_code == 200:
                    for p_data in res.json().get('response', []):
                        p = p_data.get('player', {})
                        stat_obj = p_data.get('statistics', [{}])[0].get('goals', {})
                        table = "top_scorers" if stat_type == "topscorers" else "top_assists"
                        field = "goals" if stat_type == "topscorers" else "assists"
                        val = stat_obj.get('total') if stat_type == "topscorers" else stat_obj.get('assists')
                        
                        res_stat = self.safe_request("POST", f"{self.base_url}/{table}", headers=self.headers, json={
                            "league_id": lg["af_id"], "player_id": p.get('id'), "player_name": p.get('name'), 
                            "team_name": p_data.get('statistics', [{}])[0].get('team', {}).get('name'), field: val
                        })
                        self.check_response(f"إحصائية {stat_type}: {p.get('name')}", res_stat)
                
                # انتظار 8 ثوانٍ بين جلب الهدافين وجلب صناع اللعب لنفس الدوري
                time.sleep(8)

    def fetch_live_data_and_news(self):
        logging.info("⚡ [خطوة 3] ضخ الانتقالات والغيابات والأخبار العالمية...")
        res_n = self.safe_request("GET", "http://api.isportsapi.com/sport/football/news", params={"api_key": self.isports_key})
        if res_n and res_n.status_code == 200:
            for news in res_n.json().get('data', []):
                if news.get('newsId'):
                    res_news = self.safe_request("POST", f"{self.base_url}/media_news", headers=self.headers, json={
                        "id": news.get('newsId'), "title": news.get('title'), "content": news.get('content'), 
                        "source": news.get('source'), "image_url": news.get('imageUrl'), "published_at": news.get('pubTime')
                    })
                    self.check_response(f"خبر: {news.get('title')[:20]}...", res_news)

    def fetch_today_matches(self):
        logging.info("⚡ [خطوة 4] جلب مباريات اليوم وتشكيلاتها الحية...")
        today = datetime.now().strftime('%Y-%m-%d')
        api_headers = {"X-RapidAPI-Key": self.api_football_key, "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"}
        
        for lg in self.leagues:
            res = self.safe_request("GET", "https://api-football-v1.p.rapidapi.com/v3/fixtures", headers=api_headers, params={"league": lg["af_id"], "season": 2025, "date": today})
            if res and res.status_code == 200:
                for item in res.json().get('response', []):
                    f = item.get('fixture', {})
                    teams = item.get('teams', {})
                    match_id = f.get('id')
                    
                    res_m = self.safe_request("POST", f"{self.base_url}/matches", headers=self.headers, json={
                        "id": match_id, "league_id": lg["af_id"], "home_team_id": teams.get('home', {}).get('id'), 
                        "away_team_id": teams.get('away', {}).get('id'), "match_date": f.get('date').split('T')[0], 
                        "match_time": f.get('date').split('T')[1][:5], "status": f.get('status', {}).get('short')
                    })
                    self.check_response(f"مباراة اليوم ID: {match_id}", res_m)
            time.sleep(5)

    def start(self):
        logging.info("🚀 تشغيل المحرك المصفى ذو التبريد الذكي للطلبات الحالية...")
        self.fetch_stadiums_and_coaches()
        
        # 🟢 تبريد إستراتيجي: ننام دقيقة كاملة هنا لتصفير عداد الدقيقة تماماً قبل بدء خطوة الهدافين
        logging.info("💤 تبريد إستراتيجي لمدة 60 ثانية لتصفير حصة الدقيقة في السيرفر الخارجي...")
        time.sleep(60)
        
        self.fetch_top_stats()
        self.fetch_live_data_and_news()
        self.fetch_today_matches()
        logging.info("🏆 انتهى السكربت بنجاح واستهلاك آمن ومحمي!")

if __name__ == "__main__":
    DSTWR_Direct_Fast_Engine().start()
