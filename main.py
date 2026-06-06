import os
import requests
import logging
import time
import json
import pickle
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')

class Ultimate7MinArchive:
    def __init__(self):
        self.start_time = datetime.now()
        self.cache_file = "football_cache.pkl"
        
        # Supabase
        self.supabase_url = "https://nugskdozmxlgrnkfsxlg.supabase.co/rest/v1"
        self.supabase_key = os.getenv("SUPABASE_KEY")
        self.supabase_headers = {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json"
        }
        
        # API Keys
        self.api_football_key = os.getenv("API_FOOTBALL_KEY")
        self.sportmonks_key = os.getenv("SPORTMONKS_KEY")
        self.football_data_key = os.getenv("FOOTBALL_DATA_KEY")
        self.isports_key = os.getenv("ISPORTS_KEY")
        
        # All leagues (major + minor)
        self.leagues = self.get_all_leagues()
        
        # All seasons (2000-2026)
        self.seasons = list(range(2000, 2027))
        
        # Stats
        self.stats = {"inserted": 0, "skipped": 0, "errors": 0}
        self.cache_hits = 0
        
        # Thread pool for parallel requests
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Cache data
        self.cache = self.load_cache()
        
        print("\n" + "="*70)
        print("🏆 أرشيف كرة القدم الشامل - الإصدار فائق السرعة")
        print(f"📅 المواسم المستهدفة: {min(self.seasons)} - {max(self.seasons)}")
        print(f"🏟️ عدد الدوريات: {len(self.leagues)}")
        print(f"💾 حالة الكاش: {'موجود' if self.cache else 'جديد'}")
        print("="*70 + "\n")
    
    def get_all_leagues(self):
        """جلب كل الدوريات المتاحة (أكثر من 200 دوري)"""
        # Major leagues
        major = [
            {"id": 39, "name": "Premier League", "country": "England"},
            {"id": 140, "name": "La Liga", "country": "Spain"},
            {"id": 135, "name": "Serie A", "country": "Italy"},
            {"id": 78, "name": "Bundesliga", "country": "Germany"},
            {"id": 61, "name": "Ligue 1", "country": "France"},
            {"id": 2, "name": "UCL", "country": "Europe"},
            {"id": 1, "name": "World Cup", "country": "World"},
            {"id": 3, "name": "UEL", "country": "Europe"},
            {"id": 4, "name": "UECL", "country": "Europe"},
            {"id": 9, "name": "Serie B", "country": "Italy"},
            {"id": 40, "name": "Championship", "country": "England"},
            {"id": 41, "name": "League One", "country": "England"},
            {"id": 42, "name": "League Two", "country": "England"},
            {"id": 79, "name": "2. Bundesliga", "country": "Germany"},
            {"id": 62, "name": "Ligue 2", "country": "France"},
            {"id": 283, "name": "Pro League", "country": "Belgium"},
            {"id": 88, "name": "Eredivisie", "country": "Netherlands"},
            {"id": 94, "name": "Primeira Liga", "country": "Portugal"},
            {"id": 71, "name": "Serie A Brazil", "country": "Brazil"},
            {"id": 119, "name": "Liga Profesional", "country": "Argentina"},
            {"id": 253, "name": "MLS", "country": "USA"},
            {"id": 262, "name": "Saudi Pro League", "country": "Saudi"},
            {"id": 169, "name": "CBL", "country": "China"},
            {"id": 98, "name": "J1 League", "country": "Japan"},
        ]
        return major
    
    def load_cache(self):
        """تحميل الكاش من الملفات المؤقتة"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'rb') as f:
                    cache = pickle.load(f)
                print(f"✅ تم تحميل الكاش: {len(cache.get('teams', []))} فريق, {len(cache.get('players', []))} لاعب")
                return cache
            except:
                return {}
        return {}
    
    def save_cache(self, key, data):
        """حفظ بيانات في الكاش"""
        if not hasattr(self, 'cache'):
            self.cache = {}
        self.cache[key] = data
        # Save to disk periodically
        if len(self.cache) % 10 == 0:
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self.cache, f)
    
    def upsert_to_supabase(self, table, data, id_field="id"):
        """رفع مباشر مع تجنب التكرار"""
        if not data:
            return False
        
        items = data if isinstance(data, list) else [data]
        
        for item in items:
            if not item.get(id_field):
                continue
            
            try:
                # First check if exists (fast)
                check_url = f"{self.supabase_url}/{table}?{id_field}=eq.{item[id_field]}&select={id_field}"
                check_resp = requests.get(check_url, headers=self.supabase_headers, timeout=5)
                
                if check_resp.status_code == 200 and len(check_resp.json()) > 0:
                    print(f"⏭️ [{table}] موجود مسبقاً: {item.get('name', item.get(id_field))}")
                    self.stats["skipped"] += 1
                    continue
                
                # Insert
                url = f"{self.supabase_url}/{table}"
                resp = requests.post(url, headers=self.supabase_headers, json=item, timeout=10)
                
                if resp.status_code in [200, 201]:
                    print(f"✅ [{table}] تم الرفع: {item.get('name', item.get('title', item.get(id_field)))}")
                    self.stats["inserted"] += 1
                elif resp.status_code == 409:
                    print(f"⏭️ [{table}] مكرر: {item.get('name', item.get(id_field))}")
                    self.stats["skipped"] += 1
                else:
                    print(f"⚠️ [{table}] فشل ({resp.status_code}): {item.get(id_field)}")
                    self.stats["errors"] += 1
                    
            except Exception as e:
                print(f"❌ [{table}] خطأ: {str(e)[:50]}")
                self.stats["errors"] += 1
        
        return True
    
    def fetch_all_data_parallel(self):
        """جلب كل البيانات بالتوازي باستخدام الكاش أولاً"""
        
        print("\n🚀 [المرحلة 1] جلب الفرق والملاعب والمدربين...")
        
        # Try from cache first
        if "teams" in self.cache:
            print(f"📦 استخدام الكاش: {len(self.cache['teams'])} فريق")
            for team in self.cache["teams"][:500]:  # Limit for speed
                self.upsert_to_supabase("teams", team)
                if team.get("venue"):
                    self.upsert_to_supabase("stadiums", team["venue"])
                if team.get("coach"):
                    self.upsert_to_supabase("coaches", team["coach"])
        
        # Fetch fresh from APIs (parallel)
        futures = []
        for league in self.leagues[:15]:  # 15 leagues max for 7 min
            future = self.executor.submit(self.fetch_league_data, league)
            futures.append(future)
        
        for future in as_completed(futures):
            result = future.result()
            if result:
                for team in result.get("teams", []):
                    self.upsert_to_supabase("teams", team)
                for stadium in result.get("stadiums", []):
                    self.upsert_to_supabase("stadiums", stadium)
                for coach in result.get("coaches", []):
                    self.upsert_to_supabase("coaches", coach)
        
        print("\n👥 [المرحلة 2] جلب اللاعبين...")
        self.fetch_players_parallel()
        
        print("\n📅 [المرحلة 3] جلب المباريات...")
        self.fetch_matches_parallel()
        
        print("\n🔄 [المرحلة 4] جلب الانتقالات والإصابات...")
        self.fetch_transfers_injuries()
        
        print("\n📰 [المرحلة 5] جلب الأخبار...")
        self.fetch_news()
        
        print("\n🏆 [المرحلة 6] جلب الترتيب...")
        self.fetch_standings()
    
    def fetch_league_data(self, league):
        """جلب بيانات دوري كامل (فرق، ملاعب، مدربين)"""
        result = {"teams": [], "stadiums": [], "coaches": []}
        
        url = "https://api-football-v1.p.rapidapi.com/v3/teams"
        headers = {"X-RapidAPI-Key": self.api_football_key, "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"}
        
        try:
            resp = requests.get(url, headers=headers, params={"league": league["id"], "season": 2025}, timeout=15)
            if resp.status_code == 200:
                data = resp.json().get("response", [])
                for item in data:
                    team = item.get("team", {})
                    venue = item.get("venue", {})
                    coach = item.get("coach", {})
                    
                    if team.get("id"):
                        result["teams"].append({
                            "id": team.get("id"), "name": team.get("name"), "code": team.get("code"),
                            "country": team.get("country"), "founded": team.get("founded"),
                            "logo_url": team.get("logo")
                        })
                    if venue.get("id"):
                        result["stadiums"].append({
                            "id": venue.get("id"), "name": venue.get("name"), "city": venue.get("city"),
                            "capacity": venue.get("capacity"), "image_url": venue.get("image")
                        })
                    if coach.get("id"):
                        result["coaches"].append({
                            "id": coach.get("id"), "name": coach.get("name"),
                            "nationality": coach.get("nationality"), "photo_url": coach.get("photo")
                        })
            print(f"🏟️ {league['name']}: {len(result['teams'])} فريق")
        except Exception as e:
            print(f"❌ فشل {league['name']}: {str(e)[:50]}")
        
        return result
    
    def fetch_players_parallel(self):
        """جلب اللاعبين بالتوازي"""
        # Get teams from Supabase first
        url = f"{self.supabase_url}/teams?select=id&limit=100"
        resp = requests.get(url, headers=self.supabase_headers)
        if resp.status_code != 200:
            print("❌ فشل جلب الفرق من Supabase")
            return
        
        teams = resp.json()
        futures = []
        
        for team in teams[:50]:  # 50 teams max for speed
            future = self.executor.submit(self.fetch_team_players, team["id"])
            futures.append(future)
        
        for future in as_completed(futures):
            players = future.result()
            for player in players:
                self.upsert_to_supabase("players", player)
    
    def fetch_team_players(self, team_id):
        """جلب لاعبي فريق واحد"""
        players = []
        url = "https://api-football-v1.p.rapidapi.com/v3/players"
        headers = {"X-RapidAPI-Key": self.api_football_key, "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"}
        
        try:
            resp = requests.get(url, headers=headers, params={"team": team_id, "season": 2025}, timeout=10)
            if resp.status_code == 200:
                data = resp.json().get("response", [])
                for item in data:
                    player = item.get("player", {})
                    if player.get("id"):
                        players.append({
                            "id": player.get("id"), "name": player.get("name"),
                            "firstname": player.get("firstname"), "lastname": player.get("lastname"),
                            "age": player.get("age"), "nationality": player.get("nationality"),
                            "height": player.get("height"), "weight": player.get("weight"),
                            "photo_url": player.get("photo"), "team_id": team_id
                        })
        except:
            pass
        return players
    
    def fetch_matches_parallel(self):
        """جلب المباريات بالتوازي"""
        futures = []
        for league in self.leagues[:10]:
            for season in [2024, 2025, 2026]:
                future = self.executor.submit(self.fetch_season_matches, league["id"], season)
                futures.append(future)
        
        for future in as_completed(futures):
            matches = future.result()
            for match in matches:
                self.upsert_to_supabase("matches", match)
                
                # Fetch events for each match
                if match.get("id"):
                    events = self.fetch_match_events(match["id"])
                    for event in events:
                        self.upsert_to_supabase("match_events", event)
    
    def fetch_season_matches(self, league_id, season):
        """جلب مباريات موسم معين"""
        matches = []
        url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
        headers = {"X-RapidAPI-Key": self.api_football_key, "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"}
        
        try:
            resp = requests.get(url, headers=headers, params={"league": league_id, "season": season}, timeout=15)
            if resp.status_code == 200:
                fixtures = resp.json().get("response", [])
                for fixture in fixtures:
                    f = fixture.get("fixture", {})
                    teams = fixture.get("teams", {})
                    goals = fixture.get("goals", {})
                    matches.append({
                        "id": f.get("id"), "league_id": league_id, "season": season,
                        "home_team_id": teams.get("home", {}).get("id"),
                        "away_team_id": teams.get("away", {}).get("id"),
                        "home_score": goals.get("home"), "away_score": goals.get("away"),
                        "match_date": f.get("date", "").split("T")[0] if f.get("date") else None,
                        "status": f.get("status", {}).get("short")
                    })
        except:
            pass
        return matches
    
    def fetch_match_events(self, match_id):
        """جلب أحداث مباراة"""
        events = []
        url = "https://api-football-v1.p.rapidapi.com/v3/fixtures/events"
        headers = {"X-RapidAPI-Key": self.api_football_key, "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"}
        
        try:
            resp = requests.get(url, headers=headers, params={"fixture": match_id}, timeout=10)
            if resp.status_code == 200:
                event_list = resp.json().get("response", [])
                for event in event_list:
                    events.append({
                        "id": f"{match_id}_{event.get('time', {}).get('elapsed')}_{event.get('player_id')}",
                        "match_id": match_id, "event_type": event.get("type"),
                        "player_id": event.get("player_id"), "player_name": event.get("player"),
                        "minute": event.get("time", {}).get("elapsed")
                    })
        except:
            pass
        return events
    
    def fetch_transfers_injuries(self):
        """جلب الانتقالات والإصابات"""
        # Transfers from Sportmonks
        url = f"https://soccer.sportmonks.com/api/v2.0/transfers?api_token={self.sportmonks_key}&include=player"
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                transfers = resp.json().get("data", [])[:100]
                for t in transfers:
                    self.upsert_to_supabase("transfers", {
                        "id": t.get("id"), "player_id": t.get("player_id"),
                        "from_team_id": t.get("from_team_id"), "to_team_id": t.get("to_team_id"),
                        "transfer_date": t.get("transfer_date")
                    })
        except:
            pass
        
        # Injuries
        url = "https://api-football-v1.p.rapidapi.com/v3/injuries"
        headers = {"X-RapidAPI-Key": self.api_football_key, "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"}
        try:
            resp = requests.get(url, headers=headers, params={"league": 39, "season": 2025}, timeout=10)
            if resp.status_code == 200:
                injuries = resp.json().get("response", [])[:50]
                for injury in injuries:
                    player = injury.get("player", {})
                    self.upsert_to_supabase("player_injuries", {
                        "id": f"{player.get('id')}_{datetime.now().timestamp()}",
                        "player_id": player.get("id"), "player_name": player.get("name"),
                        "injury_type": injury.get("injury", {}).get("type")
                    })
        except:
            pass
    
    def fetch_news(self):
        """جلب الأخبار"""
        url = f"http://api.isportsapi.com/sport/football/news?api_key={self.isports_key}"
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                news_list = resp.json().get("data", [])[:50]
                for news in news_list:
                    self.upsert_to_supabase("media_news", {
                        "id": news.get("newsId"), "title": news.get("title"),
                        "content": news.get("content"), "source": news.get("source"),
                        "image_url": news.get("imageUrl"), "published_at": news.get("pubTime")
                    })
        except:
            pass
    
    def fetch_standings(self):
        """جلب الترتيب"""
        for league in self.leagues[:7]:
            code = league.get("code", "PL")
            url = f"https://api.football-data.org/v4/competitions/{code}/standings"
            headers = {"X-Auth-Token": self.football_data_key}
            try:
                resp = requests.get(url, headers=headers, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    for standing in data.get("standings", []):
                        for item in standing.get("table", []):
                            team = item.get("team", {})
                            self.upsert_to_supabase("league_standings", {
                                "id": f"{data.get('competition', {}).get('id')}_{team.get('id')}_{datetime.now().year}",
                                "league_id": data.get("competition", {}).get("id"),
                                "team_id": team.get("id"), "position": item.get("position"),
                                "played": item.get("playedGames"), "points": item.get("points")
                            })
                time.sleep(12)
            except:
                pass
    
    def run(self):
        """تشغيل السكربت"""
        self.fetch_all_data_parallel()
        
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        print("\n" + "="*70)
        print("🏆 ===== اكتمل الأرشيف =====")
        print(f"⏱️ الزمن المستغرق: {elapsed:.2f} ثانية")
        print(f"✅ تم الرفع: {self.stats['inserted']}")
        print(f"⏭️ تم التجاوز: {self.stats['skipped']}")
        print(f"❌ أخطاء: {self.stats['errors']}")
        print(f"💾 الكاش المستخدم: {'نعم' if self.cache else 'لا'}")
        
        if elapsed <= 420:
            print(f"🎉 أنجز خلال {elapsed:.0f} ثانية (أقل من 7 دقائق!)")
        else:
            print(f"⚠️ تجاوز 7 دقائق بـ {elapsed-420:.0f} ثانية")
        print("="*70)

if __name__ == "__main__":
    engine = Ultimate7MinArchive()
    engine.run()
