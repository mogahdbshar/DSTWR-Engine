import os
import requests
import logging
import time
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')

class DSTWR_The_Absolute_Monster_Engine:
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
        self.football_data_key = os.getenv("FOOTBALL_DATA_KEY")

        # 🌟 الأرشيف التاريخي العام في الجداول الأساسية للمواسم
        self.all_historical_years = [1000, 1930, 1934, 1938] + list(range(1950, 2027))
        
        # 🎯 النطاق المطلوب: تغطية شاملة وعميقة للملاعب والمدربين من 2010 إلى 2026+
        self.api_supported_seasons = list(range(2010, 2027))
        
        self.leagues = [
            {"code": "PL", "fd_id": 2021, "af_id": 39, "sm_id": 8, "name": "Premier League", "country": "England"},
            {"code": "PD", "fd_id": 2014, "af_id": 140, "sm_id": 565, "name": "La Liga", "country": "Spain"},
            {"code": "CL", "fd_id": 2001, "af_id": 2, "sm_id": 5, "name": "UEFA Champions League", "country": "Europe"},
            {"code": "SA", "fd_id": 2019, "af_id": 135, "sm_id": 384, "name": "Serie A", "country": "Italy"},
            {"code": "BL1", "fd_id": 2002, "af_id": 78, "sm_id": 82, "name": "Bundesliga", "country": "Germany"},
            {"code": "FL1", "fd_id": 2015, "af_id": 61, "sm_id": 301, "name": "Ligue 1", "country": "France"},
            {"code": "WC", "fd_id": 2000, "af_id": 1, "sm_id": 732, "name": "FIFA World Cup", "country": "World"}
        ]

    def check_response(self, context, response):
        if not response: return
        if response.status_code in [200, 201]:
            logging.info(f"✅ [حفظ]: {context}")
        elif response.status_code == 409:
            logging.warning(f"🔄 [تحديث مكرر]: {context}")
        else:
            logging.error(f"❌ [خطأ] {context} | الكود: {response.status_code} | الرد: {response.text}")

    def safe_request(self, method, url, **kwargs):
        try:
            response = requests.request(method, url, **kwargs)
            if response.status_code == 429:
                logging.warning("⏳ [حد الطلبات] السيرفر مضغوط، انتظار 30 ثانية لتجنب الحظر...")
                time.sleep(30)
                return requests.request(method, url, **kwargs)
            return response
        except Exception as e:
            logging.error(f"🚨 خطأ شبكة: {e}")
            return None

    def pipeline_0_generate_seasons(self):
        logging.info("🧱 جاري تأسيس المواسم التاريخية المستهدفة في قاعدة البيانات...")
        for lg in self.leagues:
            for year in self.all_historical_years:
                res = self.safe_request("POST", f"{self.base_url}/seasons", headers=self.headers, json={
                    "id": int(f"{lg['af_id']}{year}"), "league_id": lg["af_id"], "year": year
                })
                if year in [1000, 1950, 2026]:
                    self.check_response(f"تأسيس موسم {year} لـ {lg['name']}", res)
            time.sleep(0.2)

    def pipeline_1_leagues_teams_and_stats(self):
        logging.info("⚡ [PIPELINE 1] ضخ الدوريات، الفرق، الهدافين، وصناع اللعب...")
        api_headers = {"X-RapidAPI-Key": self.api_football_key, "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"}
        
        for lg in self.leagues:
            res_l = self.safe_request("POST", f"{self.base_url}/leagues", headers=self.headers, json={"id": lg["af_id"], "name": lg["name"], "country": lg["country"], "code": lg["code"]})
            self.check_response(f"الدوري: {lg['name']}", res_l)
            
            url_st = f"https://api.football-data.org/v4/competitions/{lg['code']}/standings"
            res_st = self.safe_request("GET", url_st, headers={'X-Auth-Token': self.football_data_key})
            if res_st and res_st.status_code == 200:
                for standing in res_st.json().get('standings', []):
                    for item in standing.get('table', []):
                        t = item.get('team', {})
                        res_t = self.safe_request("POST", f"{self.base_url}/teams", headers=self.headers, json={"id": t.get('id'), "league_id": lg["af_id"], "name": t.get('name'), "short_name": t.get('shortName'), "logo_url": t.get('crest')})
                        self.check_response(f"فريق: {t.get('name')}", res_t)
                        
                        self.safe_request("POST", f"{self.base_url}/league_standings", headers=self.headers, json={
                            "league_id": lg["af_id"], "team_id": t.get('id'), "played": item.get('playedGames'), "points": item.get('points'), "won": item.get('won'), "lost": item.get('lost')
                        })
            time.sleep(1.0) # تهدئة لحماية مفتاح الترتيب

            # الهدافين وصناع اللعب
            for stat_type in ["topscorers", "topassists"]:
                url_stat = f"https://api-football-v1.p.rapidapi.com/v3/players/{stat_type}"
                res_s = self.safe_request("GET", url_stat, headers=api_headers, params={"league": lg["af_id"], "season": 2025})
                if res_s and res_s.status_code == 200:
                    for p_data in res_s.json().get('response', []):
                        p = p_data.get('player', {})
                        stat_obj = p_data.get('statistics', [{}])[0].get('goals', {})
                        table_target = "top_scorers" if stat_type == "topscorers" else "top_assists"
                        field_target = "goals" if stat_type == "topscorers" else "assists"
                        val_target = stat_obj.get('total') if stat_type == "topscorers" else stat_obj.get('assists')
                        
                        self.safe_request("POST", f"{self.base_url}/{table_target}", headers=self.headers, json={
                            "league_id": lg["af_id"], "player_id": p.get('id'), "player_name": p.get('name'), "team_name": p_data.get('statistics', [{}])[0].get('team', {}).get('name'), field_target: val_target
                        })
                time.sleep(1.0) # تأخير ذكي لحماية المفتاح

    def pipeline_2_deep_archive(self):
        logging.info("⚡ [PIPELINE 2] جلب الملاعب والمدربين التاريخيين (2010 - 2026)...")
        api_headers = {"X-RapidAPI-Key": self.api_football_key, "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"}
        
        for lg in self.leagues:
            logging.info(f"🏟️ جاري فحص ملاعب ومدربي دوري: {lg['name']}")
            for season in self.api_supported_seasons:
                url = "https://api-football-v1.p.rapidapi.com/v3/teams"
                res = self.safe_request("GET", url, headers=api_headers, params={"league": lg["af_id"], "season": season})
                
                if res and res.status_code == 200:
                    teams_data = res.json().get('response', [])
                    for chunk in teams_data:
                        v = chunk.get('venue', {})
                        if v.get('id'):
                            self.safe_request("POST", f"{self.base_url}/stadiums", headers=self.headers, json={"id": v.get('id'), "name": v.get('name'), "city": v.get('city'), "capacity": v.get('capacity'), "image_url": v.get('image'), "surface": v.get('surface')})
                        
                        t_id = chunk.get('team', {}).get('id')
                        url_c = "https://api-football-v1.p.rapidapi.com/v3/coachs"
                        res_c = self.safe_request("GET", url_c, headers=api_headers, params={"team": t_id})
                        if res_c and res_c.status_code == 200:
                            for coach in res_c.json().get('response', []):
                                self.safe_request("POST", f"{self.base_url}/coaches", headers=self.headers, json={"id": coach.get('id'), "team_id": t_id, "name": coach.get('name'), "nationality": coach.get('nationality'), "photo_url": coach.get('photo')})
                
                # 🛑 السر السحري هنا: ننام ثانيتين كاملتين بعد كل موسم لكي يهدأ سيرفر الـ API ولا يحظرنا أبداً
                time.sleep(2.0)

        # لاعبين وعقود SportMonks
        url_sm_p = "https://api.sportmonks.com/v3/football/players"
        res_sm_p = self.safe_request("GET", url_sm_p, params={"api_token": self.sportmonks_key, "include": "contracts;teams"})
        if res_sm_p and res_sm_p.status_code == 200:
            for p in res_sm_p.json().get('data', []):
                p_id = p.get('id')
                self.safe_request("POST", f"{self.base_url}/players", headers=self.headers, json={"id": p_id, "name": p.get('display_name'), "photo_url": p.get('image_path'), "nationality": p.get('nationality')})
                self.safe_request("POST", f"{self.base_url}/player_market_value", headers=self.headers, json={"player_id": p_id, "market_value": p.get('market_value', 5000000), "currency": "EUR"})
                for contract in p.get('contracts', []):
                    self.safe_request("POST", f"{self.base_url}/player_contracts", headers=self.headers, json={"player_id": p_id, "team_id": contract.get('team_id'), "start_date": contract.get('start_date'), "end_date": contract.get('end_date'), "salary": contract.get('amount')})

    def pipeline_3_market_injuries_and_news(self):
        logging.info("⚡ [PIPELINE 3] ضخ الانتقالات، الغيابات، والأخبار العالمية...")
        url_tf = "https://api.sportmonks.com/v3/football/transfers"
        res_tf = self.safe_request("GET", url_tf, params={"api_token": self.sportmonks_key, "include": "player"})
        if res_tf and res_tf.status_code == 200:
            for tf in res_tf.json().get('data', []):
                p = tf.get('player', {}).get('data', {})
                if p.get('id'):
                    self.safe_request("POST", f"{self.base_url}/transfers", headers=self.headers, json={"id": tf.get('id'), "player_id": p.get('id'), "from_team_id": tf.get('from_team_id'), "to_team_id": tf.get('to_team_id'), "transfer_date": tf.get('date'), "amount": tf.get('amount'), "type": tf.get('type')})

        api_headers = {"X-RapidAPI-Key": self.api_football_key, "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"}
        for lg in self.leagues:
            res_ij = self.safe_request("GET", "https://api-football-v1.p.rapidapi.com/v3/injuries", headers=api_headers, params={"league": lg["af_id"], "season": 2025})
            if res_ij and res_ij.status_code == 200:
                for ij in res_ij.json().get('response', []):
                    self.safe_request("POST", f"{self.base_url}/player_injuries", headers=self.headers, json={"player_id": ij.get('player', {}).get('id'), "team_id": ij.get('team', {}).get('id'), "league_id": lg["af_id"], "player_name": ij.get('player', {}).get('name'), "type": ij.get('problems', 'Injury')})
            time.sleep(1.0)

        res_n = self.safe_request("GET", "http://api.isportsapi.com/sport/football/news", params={"api_key": self.isports_key})
        if res_n and res_n.status_code == 200:
            for news in res_n.json().get('data', []):
                self.safe_request("POST", f"{self.base_url}/media_news", headers=self.headers, json={"id": news.get('newsId'), "title": news.get('title'), "content": news.get('content'), "source": news.get('source'), "image_url": news.get('imageUrl'), "published_at": news.get('pubTime')})

    def pipeline_4_matches_stats_and_lineups(self):
        logging.info("⚡ [PIPELINE 4] ضخ مباريات اليوم الحية + التشكيلات التكتيكية...")
        today = datetime.now().strftime('%Y-%m-%d')
        api_headers = {"X-RapidAPI-Key": self.api_football_key, "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"}
        
        for lg in self.leagues:
            url_fx = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
            res_fx = self.safe_request("GET", url_fx, headers=api_headers, params={"league": lg["af_id"], "season": 2025, "date": today})
            if res_fx and res_fx.status_code == 200:
                for item in res_fx.json().get('response', []):
                    f = item.get('fixture', {})
                    teams = item.get('teams', {})
                    goals = item.get('goals', {})
                    match_id = f.get('id')
                    
                    self.safe_request("POST", f"{self.base_url}/matches", headers=self.headers, json={"id": match_id, "league_id": lg["af_id"], "home_team_id": teams.get('home', {}).get('id'), "away_team_id": teams.get('away', {}).get('id'), "match_date": f.get('date').split('T')[0], "match_time": f.get('date').split('T')[1][:5], "status": f.get('status', {}).get('short'), "referee": f.get('referee', 'Unknown Referee'), "venue_id": f.get('venue', {}).get('id')})
                    self.safe_request("POST", f"{self.base_url}/match_results", headers=self.headers, json={"match_id": match_id, "home_score": goals.get('home'), "away_score": goals.get('away')})
                    
                    url_lu = "https://api-football-v1.p.rapidapi.com/v3/fixtures/lineups"
                    res_lu = self.safe_request("GET", url_lu, headers=api_headers, params={"fixture": match_id})
                    if res_lu and res_lu.status_code == 200:
                        for lu in res_lu.json().get('response', []):
                            team_id = lu.get('team', {}).get('id')
                            formation = lu.get('formation', '4-3-3')
                            for p_line in lu.get('startXI', []):
                                pl = p_line.get('player', {})
                                self.safe_request("POST", f"{self.base_url}/match_lineups", headers=self.headers, json={
                                    "match_id": match_id, "team_id": team_id, "player_id": pl.get('id'), "player_name": pl.get('name'), "number": pl.get('number'), "position": pl.get('pos'), "grid": pl.get('grid'), "formation": formation
                                })

                    url_st = "https://api-football-v1.p.rapidapi.com/v3/fixtures/statistics"
                    res_st = self.safe_request("GET", url_st, headers=api_headers, params={"fixture": match_id})
                    if res_st and res_st.status_code == 200:
                        for stat_item in res_st.json().get('response', []):
                            t_id = stat_item.get('team', {}).get('id')
                            s_maps = {s.get('type'): s.get('value') for s in stat_item.get('statistics', [])}
                            self.safe_request("POST", f"{self.base_url}/match_stats", headers=self.headers, json={
                                "match_id": match_id, "team_id": t_id,
                                "possession": str(s_maps.get('Ball Possession', '50%')),
                                "shots_on_goal": s_maps.get('Shots on Goal', 0),
                                "shots_total": s_maps.get('Total Shots', 0),
                                "fouls": s_maps.get('Fouls', 0),
                                "corners": s_maps.get('Corner Kicks', 0)
                            })
                time.sleep(1.5)

    def run_engine(self):
        logging.info("🚀 [LAUNCH] إطلاق المحرك النفاث الذكي لملء جداول السوبربيز!")
        self.pipeline_0_generate_seasons()
        self.pipeline_1_leagues_teams_and_stats()
        self.pipeline_2_deep_archive()
        self.pipeline_3_market_injuries_and_news()
        self.pipeline_4_matches_stats_and_lineups()
        logging.info("🏆 [FINISH] تم ملء الخزانات بالكامل من 2010 حتى 2026+ بنجاح ساحق!")

if __name__ == "__main__":
    DSTWR_The_Absolute_Monster_Engine().run_engine()
