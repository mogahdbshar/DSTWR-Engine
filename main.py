import os
import requests
import logging
import time
from datetime import datetime

# إعداد السجلات الاحترافية للمراقبة
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')

class DSTWR_Ultimate_Mega_Engine:
    def __init__(self):
        # إعدادات Supabase الـ API الأساسية
        self.base_url = "https://nugskdozmxlgrnkfsxlg.supabase.co/rest/v1"
        self.headers = {
            "apikey": os.getenv("SUPABASE_KEY"),
            "Authorization": f"Bearer {os.getenv('SUPABASE_KEY')}",
            "Content-Type": "application/json",
            "Prefer": "return=representation,resolution=merge-duplicates" # دمج التكرارات تلقائياً بدون أخطاء
        }
        
        # مفاتيح المزودين (الشركاء) للبيانات
        self.api_football_key = os.getenv("API_FOOTBALL_KEY")
        self.sportmonks_key = os.getenv("SPORTMONKS_KEY")
        self.isports_key = os.getenv("ISPORTS_KEY")
        self.football_data_key = os.getenv("FOOTBALL_DATA_KEY")

        # نطاق السنوات لبناء أرشيف ضخم وعميق
        self.seasons = [2022, 2023, 2024, 2025, 2026]
        
        # شبكة الدوريات والبطولات الكبرى والقرية الموحدة (المعرفات متطابقة لمنع تعارض المفاتيح الأجنبية)
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
        """فحص الردود والتعامل الذكي مع كود 409 للتكرار"""
        if response.status_code in [200, 201]:
            logging.info(f"✅ تم الحفظ بنجاح: {context}")
        elif response.status_code == 409:
            logging.warning(f"🔄 تحديث مكرر ذكي لـ [{context}] عبر دمج البيانات.")
        else:
            logging.error(f"❌ خطأ في {context} | الكود: {response.status_code} | الرد: {response.text}")

    def safe_request(self, method, url, **kwargs):
        """حامي الطلبات لتجنب انهيار السكريبت عند تجاوز حد الـ Rate Limit للمفاتيح المجانية"""
        try:
            response = requests.request(method, url, **kwargs)
            if response.status_code == 429:
                logging.warning("⏳ تنبيه: تم الوصول للحد الأقصى للطلبات (Rate Limit). انتظار 60 ثانية للتنظيف...")
                time.sleep(60)
                return requests.request(method, url, **kwargs)
            return response
        except Exception as e:
            logging.error(f"🚨 خطأ اتصال بالشبكة: {e}")
            return None

    def pipeline_1_mega_leagues_and_teams(self):
        """1. ضخ الدوريات، المجموعات، الفرق بكامل الشعارات والترتيب التنافسي الشامل"""
        logging.info("⚡ [DATA INJECTION] بدء ضخ الكيانات والفرق والشعارات الأساسية...")
        for lg in self.leagues:
            # إدخال/تحديث الدوري
            res_lg = self.safe_request("POST", f"{self.base_url}/leagues", headers=self.headers, json={
                "id": lg["af_id"], "name": lg["name"], "country": lg["country"], "code": lg["code"]
            })
            self.check_response(f"الدوري: {lg['name']}", res_lg)

            # جلب الترتيب والفرق من Football-Data
            url = f"https://api.football-data.org/v4/competitions/{lg['code']}/standings"
            res = self.safe_request("GET", url, headers={'X-Auth-Token': self.football_data_key}, timeout=15)
            
            if res and res.status_code == 200:
                standings = res.json().get('standings', [])
                for standing in standings:
                    group_name = standing.get('group', 'Main Table')
                    for item in standing.get('table', []):
                        t = item.get('team', {})
                        
                        # حقن الفريق بالشعار القوي عالي الدقة
                        res_team = self.safe_request("POST", f"{self.base_url}/teams", headers=self.headers, json={
                            "id": t.get('id'), "league_id": lg["af_id"], "name": t.get('name'), "short_name": t.get('shortName'), "logo_url": t.get('crest')
                        })
                        self.check_response(f"الفريق: {t.get('name')}", res_team)
                        
                        # حقن الترتيب الشامل والإحصائي
                        res_st = self.safe_request("POST", f"{self.base_url}/league_standings", headers=self.headers, json={
                            "league_id": lg["af_id"], "team_id": t.get('id'), "group_name": group_name,
                            "played": item.get('playedGames'), "points": item.get('points'), 
                            "won": item.get('won'), "draw": item.get('draw'), "lost": item.get('lost'),
                            "goals_for": item.get('goalsFor'), "goals_against": item.get('goalsAgainst'), "goal_difference": item.get('goalDifference')
                        })
                        self.check_response(f"ترتيب: {t.get('name')}", res_st)
            time.sleep(2)

    def pipeline_2_stadiums_coaches_and_seasons(self):
        """2. أرشيف المواسم التاريخية + الملاعب بكامل سعتها وصورها + بيانات المدربين الفنيين"""
        logging.info("⚡ [INFRASTRUCTURE] ضخ المواسم التاريخية، الملاعب، والأجهزة الفنية...")
        for lg in self.leagues:
            for season in self.seasons:
                # إنشاء سجلات المواسم في الـ DB
                self.safe_request("POST", f"{self.base_url}/seasons", headers=self.headers, json={
                    "id": int(f"{lg['af_id']}{season}"), "league_id": lg["af_id"], "year": season
                })
                
                # جلب الملاعب والفرق والمدربين تفصيلياً من API-Football
                url = "https://api-football-v1.p.rapidapi.com/v3/teams"
                api_headers = {"X-RapidAPI-Key": self.api_football_key, "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"}
                res = self.safe_request("GET", url, headers=api_headers, params={"league": lg["af_id"], "season": season}, timeout=15)
                
                if res and res.status_code == 200:
                    data = res.json().get('response', [])
                    for chunk in data:
                        # 1. الملاعب
                        v = chunk.get('venue', {})
                        if v.get('id'):
                            res_v = self.safe_request("POST", f"{self.base_url}/stadiums", headers=self.headers, json={
                                "id": v.get('id'), "name": v.get('name'), "city": v.get('city'), "capacity": v.get('capacity'), "image_url": v.get('image'), "surface": v.get('surface')
                            })
                            self.check_response(f"ملعب: {v.get('name')}", res_v)
                        
                        # 2. المدربين (Coaches)
                        t_id = chunk.get('team', {}).get('id')
                        url_c = "https://api-football-v1.p.rapidapi.com/v3/coachs"
                        res_c = self.safe_request("GET", url_c, headers=api_headers, params={"team": t_id}, timeout=15)
                        if res_c and res_c.status_code == 200:
                            coaches = res_c.json().get('response', [])
                            for coach in coaches:
                                res_co = self.safe_request("POST", f"{self.base_url}/coaches", headers=self.headers, json={
                                    "id": coach.get('id'), "team_id": t_id, "name": coach.get('name'), "firstname": coach.get('firstname'), "lastname": coach.get('lastname'), "nationality": coach.get('nationality'), "photo_url": coach.get('photo')
                                })
                                self.check_response(f"المدرب: {coach.get('name')}", res_co)
                time.sleep(1)

    def pipeline_3_players_transfers_and_injuries(self):
        """3. الموسوعة البشرية: بيانات اللاعبين كاملة، سوق الانتقالات الحي، وسجل الغيابات والإصابات"""
        logging.info("⚡ [MARKET & HUMAN ASSETS] ضخ قاعدة بيانات اللاعبين، الانتقالات، وقوائم الإصابات الحالية...")
        
        # أ. الانتقالات واللاعبين من SportMonks
        url_tf = "https://api.sportmonks.com/v3/football/transfers"
        params_tf = {"api_token": self.sportmonks_key, "include": "player;team"}
        res_tf = self.safe_request("GET", url_tf, params=params_tf, timeout=15)
        
        if res_tf and res_tf.status_code == 200:
            transfers = res_tf.json().get('data', [])
            for tf in transfers:
                p = tf.get('player', {}).get('data', {})
                if p.get('id'):
                    res_p = self.safe_request("POST", f"{self.base_url}/players", headers=self.headers, json={
                        "id": p.get('id'), "name": p.get('display_name'), "photo_url": p.get('image_path'), "nationality": p.get('nationality'), "position": p.get('position_id')
                    })
                    self.check_response(f"اللاعب: {p.get('display_name')}", res_p)
                    
                    res_tfx = self.safe_request("POST", f"{self.base_url}/transfers", headers=self.headers, json={
                        "id": tf.get('id'), "player_id": p.get('id'), "from_team_id": tf.get('from_team_id'), "to_team_id": tf.get('to_team_id'), "transfer_date": tf.get('date'), "amount": tf.get('amount'), "type": tf.get('type')
                    })
                    self.check_response(f"صفقة انتقال رقم: {tf.get('id')}", res_tfx)

        # ب. الإصابات والغيابات الحية (Injuries & Absences) من API-Football لعام 2026
        api_headers = {"X-RapidAPI-Key": self.api_football_key, "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"}
        for lg in self.leagues:
            url_ij = "https://api-football-v1.p.rapidapi.com/v3/injuries"
            res_ij = self.safe_request("GET", url_ij, headers=api_headers, params={"league": lg["af_id"], "season": 2025}, timeout=15)
            if res_ij and res_ij.status_code == 200:
                injuries = res_ij.json().get('response', [])
                for ij in injuries:
                    p_info = ij.get('player', {})
                    t_info = ij.get('team', {})
                    res_abs = self.safe_request("POST", f"{self.base_url}/player_injuries", headers=self.headers, json={
                        "player_id": p_info.get('id'), "team_id": t_info.get('id'), "league_id": lg["af_id"],
                        "player_name": p_info.get('name'), "type": ij.get('problems', 'Injury'), "reason": ij.get('fixture', {}).get('date')
                    })
                    self.check_response(f"إصابة غياب: {p_info.get('name')}", res_abs)
            time.sleep(1)

    def pipeline_4_global_news_and_notifications(self):
        """4. سيل الأخبار العالمية المحدثة + معالج الإشعارات الذكية للتطبيق الفوري"""
        logging.info("⚡ [NEWS & NOTIFICATIONS] جلب الأخبار وصناعة الإشعارات التنبيهية الفورية...")
        url = "http://api.isportsapi.com/sport/football/news"
        res = self.safe_request("GET", url, params={"api_key": self.isports_key}, timeout=15)
        
        if res and res.status_code == 200:
            news_list = res.json().get('data', [])
            for news in news_list:
                news_id = news.get('newsId')
                title_txt = news.get('title', '')
                
                # 1. ضخ الخبر في جدول الميديا والأخبار
                res_n = self.safe_request("POST", f"{self.base_url}/media_news", headers=self.headers, json={
                    "id": news_id, "title": title_txt, "content": news.get('content'), "source": news.get('source'), "image_url": news.get('imageUrl'), "published_at": news.get('pubTime')
                })
                self.check_response(f"مادة خبرية: {title_txt[:30]}...", res_n)
                
                # 2. توليد إشعار منبثق (Notification Push) تلقائي ذكي ومثير لمستخدمي التطبيق مرتبط بالخبر
                res_notif = self.safe_request("POST", f"{self.base_url}/app_notifications", headers=self.headers, json={
                    "news_id": news_id, "title": "⚡ خبر عاجل في الملاعب العالمية!", "body": f"{title_txt[:80]}... تابع التفاصيل الكاملة الآن داخل التطبيق.", "category": "breaking_news", "sent_at": datetime.now().isoformat()
                })
                self.check_response(f"إشعار تلقائي لخبر: {news_id}", res_notif)

    def pipeline_5_matches_events_and_referees(self):
        """5. جدول المباريات الحية، الحكام، ومجريات وأحداث المباراة (أهداف، كروت، تبديلات) تفصيلياً"""
        logging.info("⚡ [LIVE INFRASTRUCTURE] ضخ جدول مباريات اليوم، طواقم التحكيم، والأحداث العميقة...")
        today = datetime.now().strftime('%Y-%m-%d')
        api_headers = {"X-RapidAPI-Key": self.api_football_key, "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"}
        
        for lg in self.leagues:
            url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
            res = self.safe_request("GET", url, headers=api_headers, params={"league": lg["af_id"], "season": 2025, "date": today}, timeout=15)
            
            if res and res.status_code == 200:
                fixtures = res.json().get('response', [])
                for item in fixtures:
                    f = item.get('fixture', {})
                    teams = item.get('teams', {})
                    goals = item.get('goals', {})
                    match_id = f.get('id')
                    referee_name = f.get('referee', 'Unknown Referee')
                    
                    # 1. إدخال المباراة مع الحكم المسؤول عنها
                    res_m = self.safe_request("POST", f"{self.base_url}/matches", headers=self.headers, json={
                        "id": match_id, "league_id": lg["af_id"], "home_team_id": teams.get('home', {}).get('id'), "away_team_id": teams.get('away', {}).get('id'),
                        "match_date": f.get('date').split('T')[0], "match_time": f.get('date').split('T')[1][:5], "status": f.get('status', {}).get('short'),
                        "referee": referee_name, "venue_id": f.get('venue', {}).get('id')
                    })
                    self.check_response(f"مباراة اليوم: {teams.get('home', {}).get('name')} ضد {teams.get('away', {}).get('name')}", res_m)
                    
                    # 2. حقن تفاصيل النتيجة الحالية
                    res_mr = self.safe_request("POST", f"{self.base_url}/match_results", headers=self.headers, json={
                        "match_id": match_id, "home_score": goals.get('home'), "away_score": goals.get('away')
                    })
                    self.check_response(f"النتيجة الرقمية للمباراة: {match_id}", res_mr)
                    
                    # 3. جلب وحقن أحداث المباراة التفصيلية (الأهداف، الكروت الصفراء/الحمراء، التبديلات) لرفع القيمة التنافسية للبيانات
                    url_ev = "https://api-football-v1.p.rapidapi.com/v3/fixtures/events"
                    res_ev = self.safe_request("GET", url_ev, headers=api_headers, params={"fixture": match_id}, timeout=10)
                    if res_ev and res_ev.status_code == 200:
                        events = res_ev.json().get('response', [])
                        for ev in events:
                            res_sub_ev = self.safe_request("POST", f"{self.base_url}/match_timeline_events", headers=self.headers, json={
                                "match_id": match_id, "minute": ev.get('time', {}).get('elapsed'),
                                "team_id": ev.get('team', {}).get('id'), "player_name": ev.get('player', {}).get('name'),
                                "assist_name": ev.get('assist', {}).get('name'), "event_type": ev.get('type'), "event_detail": ev.get('detail')
                            })
                            self.check_response(f"حدث في اللقاء ({ev.get('type')} - دقيقة {ev.get('time', {}).get('elapsed')})", res_sub_ev)
                time.sleep(1)

    def run_engine(self):
        logging.info("🏁 [START] إطلاق أضخم محرك بيانات رياضي متكامل لـ DSTWR 🚀")
        self.pipeline_1_mega_leagues_and_teams()
        self.pipeline_2_stadiums_coaches_and_seasons()
        self.pipeline_3_players_transfers_and_injuries()
        self.pipeline_4_global_news_and_notifications()
        self.pipeline_5_matches_events_and_referees()
        logging.info("🏆 [MISSION ACCOMPLISHED] تم ملء الخزانات واكتساح الـ Database بالكامل بنجاح ساحق!")

if __name__ == "__main__":
    DSTWR_Ultimate_Mega_Engine().run_engine()
                
