import os
import requests
import time
import sys
from datetime import datetime

sys.stdout.reconfigure(line_buffering=True)

print("🚀 بدء تشغيل السكربت - الإصدار المعتمد على Sportmonks", flush=True)

class SportmonksFootballArchive:
    def __init__(self):
        print("📦 تهيئة المتغيرات...", flush=True)
        
        # Supabase
        self.supabase_url = "https://nugskdozmxlgrnkfsxlg.supabase.co/rest/v1"
        self.supabase_key = os.getenv("SUPABASE_KEY")
        self.supabase_headers = {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json"
        }
        
        # API Keys
        self.sportmonks_key = os.getenv("SPORTMONKS_KEY")
        self.football_data_key = os.getenv("FOOTBALL_DATA_KEY")
        self.isports_key = os.getenv("ISPORTS_KEY")
        
        print(f"✅ Sportmonks: {'موجود' if self.sportmonks_key else 'مفقود'}", flush=True)
        print(f"✅ Football Data: {'موجود' if self.football_data_key else 'مفقود'}", flush=True)
        print(f"✅ iSports: {'موجود' if self.isports_key else 'مفقود'}", flush=True)
        
        # Sportmonks API base
        self.sportmonks_base = "https://soccer.sportmonks.com/api/v2.0"
        
        # All leagues (Sportmonks IDs)
        self.leagues = [
            {"id": 8, "name": "Premier League"},
            {"id": 564, "name": "La Liga"},
            {"id": 384, "name": "Serie A"},
            {"id": 82, "name": "Bundesliga"},
            {"id": 301, "name": "Ligue 1"},
            {"id": 1, "name": "Champions League"},
            {"id": 5, "name": "World Cup"},
            {"id": 2, "name": "Europa League"},
            {"id": 3, "name": "Conference League"},
            {"id": 386, "name": "Serie B"},
            {"id": 9, "name": "Championship"},
            {"id": 10, "name": "League One"},
            {"id": 11, "name": "League Two"},
            {"id": 84, "name": "2. Bundesliga"},
            {"id": 302, "name": "Ligue 2"},
            {"id": 88, "name": "Eredivisie"},
            {"id": 94, "name": "Primeira Liga"},
            {"id": 71, "name": "Serie A Brazil"},
            {"id": 122, "name": "Liga Profesional"},
            {"id": 233, "name": "MLS"},
            {"id": 253, "name": "Saudi Pro League"},
            {"id": 169, "name": "CSL"},
            {"id": 98, "name": "J1 League"},
            {"id": 283, "name": "Belgium Pro League"},
            {"id": 218, "name": "Super Lig"},
            {"id": 188, "name": "Premier Liga"},
            {"id": 113, "name": "Super League Greece"},
            {"id": 106, "name": "Allsvenskan"},
            {"id": 103, "name": "Eliteserien"},
            {"id": 111, "name": "Ekstraklasa"},
            {"id": 81, "name": "Scottish Premiership"},
            {"id": 154, "name": "Chilean Primera"},
            {"id": 138, "name": "Liga MX"},
            {"id": 89, "name": "Pro League"},
            {"id": 191, "name": "Croatian League"},
            {"id": 130, "name": "Danish Superliga"},
            {"id": 144, "name": "Swiss Super League"},
            {"id": 101, "name": "Austrian Bundesliga"},
            {"id": 112, "name": "Czech League"},
            {"id": 200, "name": "Romanian Liga"},
            {"id": 300, "name": "Bulgarian League"},
        ]
        
        # Seasons from 2015 to 2026
        self.seasons = list(range(2015, 2027))
        
        # Stats
        self.stats = {
            "teams": 0, "players": 0, "matches": 0, 
            "events": 0, "stadiums": 0, "coaches": 0,
            "news": 0, "standings": 0, "errors": 0
        }
        
        self.start_time = datetime.now()
        
        print(f"🏟️ عدد الدوريات: {len(self.leagues)}", flush=True)
        print(f"📅 المواسم: {min(self.seasons)} - {max(self.seasons)}", flush=True)
        print("="*70, flush=True)
    
    def upsert_to_supabase(self, table, data, id_field="id"):
        """رفع مع تجنب التكرار"""
        if not data or not data.get(id_field):
            return False
        
        try:
            # Check if exists
            check_url = f"{self.supabase_url}/{table}?{id_field}=eq.{data[id_field]}"
            resp = requests.get(check_url, headers=self.supabase_headers, timeout=5)
            
            if resp.status_code == 200 and resp.json():
                return True  # Already exists
            
            # Insert
            insert_url = f"{self.supabase_url}/{table}"
            resp = requests.post(insert_url, headers=self.supabase_headers, json=data, timeout=10)
            
            if resp.status_code in [200, 201]:
                print(f"   ✅ [{table}] {str(data.get('name', data.get('title', '')))[:40]}", flush=True)
                return True
            elif resp.status_code == 409:
                return True
            else:
                print(f"   ⚠️ [{table}] فشل: {resp.status_code}", flush=True)
                return False
        except Exception as e:
            print(f"   ❌ [{table}] خطأ: {str(e)[:50]}", flush=True)
            return False
    
    def sportmonks_request(self, endpoint, params=None):
        """طلب من Sportmonks مع التعامل مع الأخطاء"""
        if not self.sportmonks_key:
            return None
        
        url = f"{self.sportmonks_base}/{endpoint}"
        all_params = {"api_token": self.sportmonks_key, "include": "venue,coach"}
        if params:
            all_params.update(params)
        
        try:
            resp = requests.get(url, params=all_params, timeout=15)
            if resp.status_code == 200:
                return resp.json().get("data", [])
            else:
                print(f"   ⚠️ Sportmonks خطأ: {resp.status_code}", flush=True)
                return None
        except Exception as e:
            print(f"   ❌ Sportmonks استثناء: {str(e)[:50]}", flush=True)
            return None
    
    def fetch_all_teams_stadiums_coaches(self):
        """جلب كل الفرق والملاعب والمدربين من Sportmonks"""
        print("\n🏟️ [المرحلة 1] جلب كل الفرق والملاعب والمدربين...", flush=True)
        
        for idx, league in enumerate(self.leagues):
            print(f"\n📌 [{idx+1}/{len(self.leagues)}] {league['name']}", flush=True)
            
            # Get teams by league
            teams = self.sportmonks_request(f"teams/season/{league['id']}")
            
            if teams:
                print(f"   عدد الفرق: {len(teams)}", flush=True)
                
                for team in teams:
                    team_id = team.get("id")
                    team_name = team.get("name")
                    
                    # Team
                    if team_id:
                        if self.upsert_to_supabase("teams", {
                            "id": team_id,
                            "name": team_name,
                            "code": team.get("code"),
                            "country": team.get("country", {}).get("name") if team.get("country") else None,
                            "logo_url": team.get("logo_path"),
                        }):
                            self.stats["teams"] += 1
                    
                    # Stadium (venue)
                    venue = team.get("venue")
                    if venue and venue.get("id"):
                        if self.upsert_to_supabase("stadiums", {
                            "id": venue.get("id"),
                            "name": venue.get("name"),
                            "city": venue.get("city"),
                            "capacity": venue.get("capacity"),
                            "surface": venue.get("surface"),
                            "image_url": venue.get("image_path")
                        }):
                            self.stats["stadiums"] += 1
                    
                    # Coach
                    coach = team.get("coach")
                    if coach and coach.get("id"):
                        if self.upsert_to_supabase("coaches", {
                            "id": coach.get("id"),
                            "name": coach.get("name"),
                            "nationality": coach.get("country", {}).get("name") if coach.get("country") else None,
                            "photo_url": coach.get("image_path")
                        }):
                            self.stats["coaches"] += 1
            
            time.sleep(0.5)  # Small delay between leagues
    
    def fetch_all_players(self):
        """جلب كل اللاعبين من الفرق الموجودة في Supabase"""
        print("\n👥 [المرحلة 2] جلب كل اللاعبين...", flush=True)
        
        # Get teams from Supabase
        url = f"{self.supabase_url}/teams?select=id&limit=200"
        resp = requests.get(url, headers=self.supabase_headers, timeout=10)
        
        if resp.status_code != 200:
            print("❌ فشل جلب الفرق من Supabase", flush=True)
            return
        
        teams = resp.json()
        print(f"📊 عدد الفرق: {len(teams)}", flush=True)
        
        for idx, team in enumerate(teams):
            team_id = team["id"]
            print(f"\n👕 [{idx+1}/{len(teams)}] فريق ID: {team_id}", flush=True)
            
            # Get players by team
            players = self.sportmonks_request(f"players/team/{team_id}")
            
            if players:
                print(f"   عدد اللاعبين: {len(players)}", flush=True)
                
                for player in players:
                    if player.get("id"):
                        birth = player.get("date_of_birth")
                        if self.upsert_to_supabase("players", {
                            "id": player.get("id"),
                            "name": player.get("name"),
                            "firstname": player.get("firstname"),
                            "lastname": player.get("lastname"),
                            "age": player.get("age"),
                            "nationality": player.get("country", {}).get("name") if player.get("country") else None,
                            "height": player.get("height"),
                            "weight": player.get("weight"),
                            "position": player.get("position", {}).get("name") if player.get("position") else None,
                            "photo_url": player.get("image_path"),
                            "team_id": team_id
                        }):
                            self.stats["players"] += 1
            
            time.sleep(0.5)
    
    def fetch_all_matches(self):
        """جلب كل المباريات لجميع المواسم"""
        print("\n📅 [المرحلة 3] جلب كل المباريات...", flush=True)
        
        total = len(self.leagues) * len(self.seasons)
        current = 0
        
        for league in self.leagues:
            for season in self.seasons:
                current += 1
                print(f"\n⚽ [{current}/{total}] {league['name']} - موسم {season}", flush=True)
                
                # Get fixtures for season
                fixtures = self.sportmonks_request(f"fixtures/between/2015-01-01/2026-12-31", 
                                                    params={"league_id": league["id"]})
                
                if fixtures:
                    print(f"   عدد المباريات: {len(fixtures)}", flush=True)
                    
                    for fixture in fixtures:
                        match_id = fixture.get("id")
                        
                        if match_id:
                            # Match data
                            if self.upsert_to_supabase("matches", {
                                "id": match_id,
                                "league_id": league["id"],
                                "season": season,
                                "home_team_id": fixture.get("localTeam", {}).get("id"),
                                "away_team_id": fixture.get("visitorTeam", {}).get("id"),
                                "home_score": fixture.get("scores", {}).get("localteam_score"),
                                "away_score": fixture.get("scores", {}).get("visitorteam_score"),
                                "match_date": fixture.get("starting_at", "").split("T")[0] if fixture.get("starting_at") else None,
                                "status": fixture.get("status_short")
                            }):
                                self.stats["matches"] += 1
                            
                            # Fetch events for this match
                            self.fetch_match_events(match_id)
                
                time.sleep(0.5)
    
    def fetch_match_events(self, match_id):
        """جلب أحداث المباراة"""
        events = self.sportmonks_request(f"events/{match_id}")
        
        if events:
            for event in events:
                if self.upsert_to_supabase("match_events", {
                    "id": f"{match_id}_{event.get('minute')}_{event.get('player_id')}",
                    "match_id": match_id,
                    "event_type": event.get("type"),
                    "player_id": event.get("player_id"),
                    "player_name": event.get("player", {}).get("name") if event.get("player") else None,
                    "minute": event.get("minute")
                }):
                    self.stats["events"] += 1
    
    def fetch_standings_football_data(self):
        """جلب الترتيب من Football Data (احتياطي)"""
        print("\n🏆 [المرحلة 4] جلب ترتيب الدوريات (Football Data)...", flush=True)
        
        if not self.football_data_key:
            print("⚠️ مفتاح Football Data غير موجود", flush=True)
            return
        
        leagues_fd = {
            "PL": "Premier League",
            "PD": "La Liga",
            "SA": "Serie A",
            "BL1": "Bundesliga",
            "FL1": "Ligue 1",
            "CL": "Champions League"
        }
        
        for code, name in leagues_fd.items():
            print(f"\n📌 {name}", flush=True)
            url = f"https://api.football-data.org/v4/competitions/{code}/standings"
            headers = {"X-Auth-Token": self.football_data_key}
            
            try:
                resp = requests.get(url, headers=headers, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    for standing in data.get("standings", []):
                        for item in standing.get("table", []):
                            team = item.get("team", {})
                            if self.upsert_to_supabase("league_standings", {
                                "id": f"{data.get('competition', {}).get('id')}_{team.get('id')}_{datetime.now().year}",
                                "league_id": data.get("competition", {}).get("id"),
                                "team_id": team.get("id"),
                                "position": item.get("position"),
                                "played": item.get("playedGames"),
                                "points": item.get("points")
                            }):
                                self.stats["standings"] += 1
                time.sleep(12)  # Respect rate limit
            except Exception as e:
                print(f"   ❌ خطأ: {str(e)[:50]}", flush=True)
    
    def fetch_news(self):
        """جلب الأخبار من iSports"""
        print("\n📰 [المرحلة 5] جلب الأخبار...", flush=True)
        
        if not self.isports_key:
            print("⚠️ مفتاح iSports غير موجود", flush=True)
            return
        
        try:
            url = f"http://api.isportsapi.com/sport/football/news?api_key={self.isports_key}"
            resp = requests.get(url, timeout=10)
            
            if resp.status_code == 200:
                news_list = resp.json().get("data", [])[:100]
                print(f"📊 عدد الأخبار: {len(news_list)}", flush=True)
                
                for news in news_list:
                    if news.get("newsId"):
                        if self.upsert_to_supabase("media_news", {
                            "id": news.get("newsId"),
                            "title": news.get("title"),
                            "content": news.get("content", "")[:1000],
                            "source": news.get("source"),
                            "image_url": news.get("imageUrl"),
                            "published_at": news.get("pubTime")
                        }):
                            self.stats["news"] += 1
        except Exception as e:
            print(f"❌ خطأ: {str(e)[:50]}", flush=True)
    
    def run(self):
        """تشغيل السكربت"""
        print("\n" + "="*70, flush=True)
        print("🏆 أرشيف كرة القدم الشامل - إصدار Sportmonks", flush=True)
        print("="*70, flush=True)
        
        try:
            self.fetch_all_teams_stadiums_coaches()
            self.fetch_all_players()
            self.fetch_all_matches()
            self.fetch_standings_football_data()
            self.fetch_news()
        except Exception as e:
            print(f"\n❌ خطأ عام: {str(e)}", flush=True)
        
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        print("\n" + "="*70, flush=True)
        print("🏆 النتائج النهائية:", flush=True)
        print(f"   ✅ الفرق: {self.stats['teams']}", flush=True)
        print(f"   ✅ الملاعب: {self.stats['stadiums']}", flush=True)
        print(f"   ✅ المدربين: {self.stats['coaches']}", flush=True)
        print(f"   ✅ اللاعبين: {self.stats['players']}", flush=True)
        print(f"   ✅ المباريات: {self.stats['matches']}", flush=True)
        print(f"   ✅ أحداث المباريات: {self.stats['events']}", flush=True)
        print(f"   ✅ الترتيب: {self.stats['standings']}", flush=True)
        print(f"   ✅ الأخبار: {self.stats['news']}", flush=True)
        print(f"   ❌ الأخطاء: {self.stats['errors']}", flush=True)
        print(f"⏱️ الزمن: {elapsed:.2f} ثانية", flush=True)
        print("="*70, flush=True)

if __name__ == "__main__":
    print("🔥 بدء التشغيل...", flush=True)
    archive = SportmonksFootballArchive()
    archive.run()
    print("✅ اكتمل السكربت بنجاح", flush=True)
