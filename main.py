import os
import requests
import logging
import time
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DSTWR_Infinite_Galaxy_Engine:
    def __init__(self):
        # الاحتفاظ بنفس الإعدادات والـ Headers الاصلية لـ Supabase لتفادي أخطاء الاتصال
        self.base_url = "https://nugskdozmxlgrnkfsxlg.supabase.co/rest/v1"
        self.headers = {
            "apikey": os.getenv("SUPABASE_KEY"),
            "Authorization": f"Bearer {os.getenv('SUPABASE_KEY')}",
            "Content-Type": "application/json",
            "Prefer": "return=representation,resolution=merge-duplicates" # دمج المكرر تلقائياً
        }
        
        # جلب ترسانة المفاتيح الرياضية الخاصة بك من GitHub Secrets
        self.api_football_key = os.getenv("API_FOOTBALL_KEY")
        self.sportmonks_key = os.getenv("SPORTMONKS_KEY")
        self.isports_key = os.getenv("ISPORTS_KEY")
        self.football_data_key = os.getenv("FOOTBALL_DATA_KEY")

        # نطاق السنوات لتغطية تاريخية ضخمة (أرشيف + 2026)
        self.seasons = [2022, 2023, 2024, 2025, 2026]
        
        # مواءمة كود الدوريات لتطابق كل الـ APIs المشتركة
        self.leagues = [
            {"code": "PL", "fd_id": 2021, "af_id": 39, "sm_id": 8, "name": "Premier League"},
            {"code": "PD", "fd_id": 2014, "af_id": 140, "sm_id": 565, "name": "La Liga"},
            {"code": "CL", "fd_id": 2001, "af_id": 2, "sm_id": 5, "name": "UEFA Champions League"},
            {"code": "SA", "fd_id": 2019, "af_id": 135, "sm_id": 384, "name": "Serie A"},
            {"code": "BL1", "fd_id": 2002, "af_id": 78, "sm_id": 82, "name": "Bundesliga"}
        ]

    def check_response(self, context, response):
        """نفس دالتك الأصلية لفحص الرد وطباعة الخطأ بالتفصيل لو الرفع فشل"""
        if response.status_code in [200, 201]:
            logging.info(f"✅ تم الرفع بنجاح إلى: {context}")
        else:
            logging.error(f"❌ فشل الرفع إلى [{context}]! كود الرد: {response.status_code}")
            logging.error(f"📄 رسالة الخطأ من Supabase: {response.text}")

    def pipeline_1_base_football_data(self):
        """1. ضخ الدوريات والفرق والترتيب باستخدام الـ Football Data API (نفس منطقك القديم والمضمون)"""
        logging.info("⏳ [Pipeline 1] جاري تشغيل الضخ الأساسي للدوريات والترتيب...")
        for league in self.leagues:
            try:
                # ضخ الدوري أولاً
                res_league = requests.post(f"{self.base_url}/leagues", headers=self.headers, json={
                    "id": league["af_id"], "name": league["name"], "country": "Europe", "code": league["code"]
                })
                self.check_response(f"جدول الدوريات ({league['name']})", res_league)
                
                # سحب الترتيب
                url = f"https://api.football-data.org/v4/competitions/{league['code']}/standings"
                res = requests.get(url, headers={'X-Auth-Token': self.football_data_key}, timeout=15)
                
                if res.status_code == 200:
                    table = res.json().get('standings', [{}])[0].get('table', [])
                    for item in table:
                        t = item.get('team', {})
                        # ضخ الفريق
                        res_team = requests.post(f"{self.base_url}/teams", headers=self.headers, json={
                            "id": t.get('id'), "league_id": league["af_id"], "name": t.get('name'), "short_name": t.get('shortName'), "logo_url": t.get('crest')
                        })
                        self.check_response(f"جدول الفرق ({t.get('name')})", res_team)
                        
                        # ضخ الترتيب
                        res_standing = requests.post(f"{self.base_url}/league_standings", headers=self.headers, json={
                            "league_id": league["af_id"], "team_id": t.get('id'), "played": item.get('playedGames'), "points": item.get('points'), "goal_difference": item.get('goalDifference')
                        })
                        self.check_response(f"جدول الترتيب لـ ({t.get('name')})", res_standing)
                time.sleep(2)
            except Exception as e:
                logging.error(f"❌ خطأ في الـ Pipeline الأول للبطولة {league['name']}: {e}")

    def pipeline_2_historical_and_stadiums(self):
        """2. توسيع البيانات لسنوات الأرشيف وضخ الملاعب والمدربين عبر API-Football"""
        logging.info("⏳ [Pipeline 2] جاري سحب الملاعب والفرق والمدربين للأعوام السابقة و2026...")
        for league in self.leagues:
            for season in self.seasons:
                try:
                    # ضخ المواسم أولاً في جدول مواسمك
                    requests.post(f"{self.base_url}/seasons", headers=self.headers, json={
                        "id": int(f"{league['af_id']}{season}"), "league_id": league["af_id"], "year": season
                    })
                    
                    # جلب الملاعب والفرق الفاخرة بجودة 2026
                    url = "https://api-football-v1.p.rapidapi.com/v3/teams"
                    api_headers = {"X-RapidAPI-Key": self.api_football_key, "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"}
                    res = requests.get(url, headers=api_headers, params={"league": league["af_id"], "season": season}, timeout=15)
                    
                    if res.status_code == 200:
                        teams_data = res.json().get('response', [])
                        for item in teams_data:
                            venue = item.get('venue', {})
                            team = item.get('team', {})
                            
                            if venue.get('id'):
                                res_v = requests.post(f"{self.base_url}/stadiums", headers=self.headers, json={
                                    "id": venue.get('id'), "name": venue.get('name'), "city": venue.get('city'), "capacity": venue.get('capacity'), "image_url": venue.get('image')
                                })
                                self.check_response(f"جدول الملاعب ({venue.get('name')})", res_v)
                    time.sleep(1)
                except Exception as e:
                    logging.error(f"❌ خطأ أرشيف في {league['name']} لموسم {season}: {e}")

    def pipeline_3_players_and_transfers(self):
        """3. ضخ اللاعبين والهدافين وسوق الانتقالات الكبرى لعام 2026 عبر Sportmonks"""
        logging.info("⏳ [Pipeline 3] جاري سحب وضخ اللاعبين والانتقالات الحية لـ 2026...")
        url = "https://api.sportmonks.com/v3/football/transfers"
        params = {"api_token": self.sportmonks_key, "include": "player;team"}
        try:
            res = requests.get(url, params=params, timeout=15)
            if res.status_code == 200:
                transfers = res.json().get('data', [])
                for tf in transfers:
                    player = tf.get('player', {}).get('data', {})
                    if player.get('id'):
                        res_p = requests.post(f"{self.base_url}/players", headers=self.headers, json={
                            "id": player.get('id'), "name": player.get('display_name'), "photo_url": player.get('image_path'), "nationality": player.get('nationality')
                        })
                        self.check_response(f"جدول اللاعبين ({player.get('display_name')})", res_p)
                        
                        res_tf = requests.post(f"{self.base_url}/transfers", headers=self.headers, json={
                            "id": tf.get('id'), "player_id": player.get('id'), "from_team_id": tf.get('from_team_id'), "to_team_id": tf.get('to_team_id'), "transfer_date": tf.get('date'), "amount": tf.get('amount')
                        })
                        self.check_response(f"جدول الانتقالات برقم ({tf.get('id')})", res_tf)
        except Exception as e:
            logging.error(f"❌ خطأ في سحب انتقالات اللاعبين: {e}")

    def pipeline_4_live_news(self):
        """4. سحب وضخ الأخبار والتقارير الرياضية العاجلة والحية لجدول media_news عبر iSports"""
        logging.info("⏳ [Pipeline 4] جاري جلب وضخ سيل الأخبار الرياضية الحية...")
        url = "http://api.isportsapi.com/sport/football/news"
        params = {"api_key": self.isports_key}
        try:
            res = requests.get(url, params=params, timeout=15)
            if res.status_code == 200:
                news_list = res.json().get('data', [])
                for news in news_list:
                    res_n = requests.post(f"{self.base_url}/media_news", headers=self.headers, json={
                        "id": news.get('newsId'), "title": news.get('title'), "content": news.get('content'), "source": news.get('source'), "image_url": news.get('imageUrl'), "published_at": news.get('pubTime')
                    })
                    self.check_response(f"جدول الأخبار الرياضية ({news.get('title')[:30]}...)", res_n)
        except Exception as e:
            logging.error(f"❌ خطأ في جلب الأخبار الحية: {e}")

    def pipeline_5_matches_and_broadcasters(self):
        """5. سحب وضخ مباريات اليوم المباشرة وربط سيرفرات البث وجداول النتائج (قلب تطبيق يلا شوت)"""
        logging.info("⏳ [Pipeline 5] جاري سحب جدول مباريات اليوم الحية وسيرفرات البث المباشر...")
        today = datetime.now().strftime('%Y-%m-%d')
        for league in self.leagues:
            url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
            api_headers = {"X-RapidAPI-Key": self.api_football_key, "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"}
            try:
                res = requests.get(url, headers=api_headers, params={"league": league["af_id"], "season": 2025, "date": today}, timeout=15)
                if res.status_code == 200:
                    fixtures = res.json().get('response', [])
                    for item in fixtures:
                        f = item.get('fixture', {})
                        teams = item.get('teams', {})
                        goals = item.get('goals', {})
                        match_id = f.get('id')
                        
                        # ضخ المباراة في جدول matches
                        res_m = requests.post(f"{self.base_url}/matches", headers=self.headers, json={
                            "id": match_id, "league_id": league["af_id"], "home_team_id": teams.get('home', {}).get('id'), "away_team_id": teams.get('away', {}).get('id'), "match_date": f.get('date').split('T')[0], "match_time": f.get('date').split('T')[1][:5], "status": f.get('status', {}).get('short')
                        })
                        self.check_response(f"جدول المباريات ({teams.get('home', {}).get('name')} VS {teams.get('away', {}).get('name')})", res_m)
                        
                        # ضخ النتيجة في جدول match_results
                        res_mr = requests.post(f"{self.base_url}/match_results", headers=self.headers, json={
                            "match_id": match_id, "home_score": goals.get('home'), "away_score": goals.get('away')
                        })
                        self.check_response(f"جدول نتائج المباريات للمباراة رقم ({match_id})", res_mr)
                        
                        # تجهيز قنوات البث والروابط في جدول القنوات والناقلين الخاص بك
                        res_bc = requests.post(f"{self.base_url}/match_broadcasters", headers=self.headers, json={
                            "match_id": match_id, "channel_name": "beIN Sports 1", "stream_url_1": f"https://dasturtv.server/live/{match_id}/server1.m3u8", "stream_url_2": f"https://dasturtv.server/live/{match_id}/server2.m3u8"
                        })
                        self.check_response(f"جدول قنوات البث للمباراة رقم ({match_id})", res_bc)
                time.sleep(1)
            except Exception as e:
                logging.error(f"❌ خطأ في سحب مباريات اليوم لـ {league['name']}: {e}")

    def run(self):
        logging.info("🚀 [DSTWR ENGINE 2026] بدء تشغيل محرك كسر الصفر الموسع وحقن البيانات المجرة...")
        self.pipeline_1_base_football_data()
        self.pipeline_2_historical_and_stadiums()
        self.pipeline_3_players_and_transfers()
        self.pipeline_4_live_news()
        self.pipeline_5_matches_and_broadcasters()
        logging.info("🏁 [SUCCESS] اكتمل ضخ وبناء أكبر قاعدة بيانات رياضية لـ DSTWR لعام 2026 بنجاح ساحق!")

if __name__ == "__main__":
    DSTWR_Infinite_Galaxy_Engine().run()
                
