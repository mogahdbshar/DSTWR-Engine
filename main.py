import os
import requests
import time
import sys
from datetime import datetime

# Force stdout to print immediately
sys.stdout.reconfigure(line_buffering=True)

print("🚀 بدء تشغيل السكربت...", flush=True)

class CompleteFootballArchive:
    def __init__(self):
        print("📦 تهيئة المتغيرات...", flush=True)
        
        self.supabase_url = "https://nugskdozmxlgrnkfsxlg.supabase.co/rest/v1"
        self.supabase_key = os.getenv("SUPABASE_KEY")
        self.supabase_headers = {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json"
        }
        
        self.api_football_key = os.getenv("API_FOOTBALL_KEY")
        self.sportmonks_key = os.getenv("SPORTMONKS_KEY")
        self.football_data_key = os.getenv("FOOTBALL_DATA_KEY")
        self.isports_key = os.getenv("ISPORTS_KEY")
        
        print(f"✅ Supabase: {'موجود' if self.supabase_key else 'مفقود'}", flush=True)
        print(f"✅ API Football: {'موجود' if self.api_football_key else 'مفقود'}", flush=True)
        
        # ALL leagues (not just 7)
        self.leagues = [
            {"id": 39, "name": "Premier League"},
            {"id": 140, "name": "La Liga"},
            {"id": 135, "name": "Serie A"},
            {"id": 78, "name": "Bundesliga"},
            {"id": 61, "name": "Ligue 1"},
            {"id": 2, "name": "Champions League"},
            {"id": 1, "name": "World Cup"},
            {"id": 3, "name": "Europa League"},
            {"id": 4, "name": "Conference League"},
            {"id": 9, "name": "Serie B"},
            {"id": 40, "name": "Championship"},
            {"id": 41, "name": "League One"},
            {"id": 42, "name": "League Two"},
            {"id": 79, "name": "2. Bundesliga"},
            {"id": 62, "name": "Ligue 2"},
            {"id": 88, "name": "Eredivisie"},
            {"id": 94, "name": "Primeira Liga"},
            {"id": 71, "name": "Serie A Brazil"},
            {"id": 119, "name": "Liga Profesional"},
            {"id": 253, "name": "MLS"},
            {"id": 262, "name": "Saudi Pro League"},
            {"id": 169, "name": "CSL"},
            {"id": 98, "name": "J1 League"},
            {"id": 283, "name": "Belgium Pro League"},
            {"id": 218, "name": "Super Lig"},
            {"id": 188, "name": "Premier Liga"},
            {"id": 106, "name": "Super League Greece"},
            {"id": 113, "name": "Allsvenskan"},
            {"id": 103, "name": "Eliteserien"},
            {"id": 111, "name": "Ekstraklasa"},
            {"id": 81, "name": "Scottish Premiership"},
            {"id": 154, "name": "Chilean Primera"},
            {"id": 138, "name": "Liga MX"},
        ]
        
        # ALL seasons from 2000 to 2026
        self.seasons = list(range(2000, 2027))
        
        self.stats = {"teams": 0, "players": 0, "matches": 0, "events": 0, "stadiums": 0, "coaches": 0, "news": 0}
        self.start_time = datetime.now()
        
        print(f"🏟️ عدد الدوريات: {len(self.leagues)}", flush=True)
        print(f"📅 المواسم: {min(self.seasons)} - {max(self.seasons)}", flush=True)
        print("="*70, flush=True)
    
    def upsert_to_supabase(self, table, data, id_field="id"):
        """رفع مع تجاوز التكرار"""
        if not data or not data.get(id_field):
            return False
        
        try:
            # Check exists
            check_url = f"{self.supabase_url}/{table}?{id_field}=eq.{data[id_field]}"
            resp = requests.get(check_url, headers=self.supabase_headers, timeout=5)
            
            if resp.status_code == 200 and resp.json():
                return True  # Already exists, skip silently
            
            # Insert
            insert_url = f"{self.supabase_url}/{table}"
            resp = requests.post(insert_url, headers=self.supabase_headers, json=data, timeout=10)
            
            if resp.status_code in [200, 201]:
                print(f"✅ [{table}] {data.get('name', data.get('title', str(data.get(id_field))))[:50]}", flush=True)
                return True
            elif resp.status_code == 409:
                return True  # Duplicate
            else:
                print(f"⚠️ [{table}] فشل: {resp.status_code}", flush=True)
                return False
        except Exception as e:
            print(f"❌ [{table}] خطأ: {str(e)[:50]}", flush=True)
            return False
    
    def fetch_all_teams_stadiums_coaches(self):
        """جلب كل الفرق وكل الملاعب وكل المدربين من كل الدوريات"""
        print("\n🏟️ [المرحلة 1] جلب كل الفرق والملاعب والمدربين...", flush=True)
        
        headers = {
            "X-RapidAPI-Key": self.api_football_key,
            "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
        }
        
        for idx, league in enumerate(self.leagues):
            print(f"\n📌 [{idx+1}/{len(self.leagues)}] {league['name']}", flush=True)
            
            url = "https://api-football-v1.p.rapidapi.com/v3/teams"
            
            try:
                resp = requests.get(url, headers=headers, params={"league": league["id"], "season": 2025}, timeout=20)
                
                if resp.status_code == 200:
                    data = resp.json().get("response", [])
                    print(f"   عدد الفرق: {len(data)}", flush=True)
                    
                    for item in data:
                        team = item.get("team", {})
                        venue = item.get("venue", {})
                        coach = item.get("coach", {})
                        
                        if team.get("id"):
                            if self.upsert_to_supabase("teams", {
                                "id": team.get("id"), "name": team.get("name"),
                                "code": team.get("code"), "country": team.get("country"),
                                "founded": team.get("founded"), "logo_url": team.get("logo")
                            }):
                                self.stats["teams"] += 1
                        
                        if venue.get("id"):
                            if self.upsert_to_supabase("stadiums", {
                                "id": venue.get("id"), "name": venue.get("name"),
                                "city": venue.get("city"), "capacity": venue.get("capacity"),
                                "image_url": venue.get("image")
                            }):
                                self.stats["stadiums"] += 1
                        
                        if coach.get("id"):
                            if self.upsert_to_supabase("coaches", {
                                "id": coach.get("id"), "name": coach.get("name"),
                                "nationality": coach.get("nationality"), "photo_url": coach.get("photo")
                            }):
                                self.stats["coaches"] += 1
                else:
                    print(f"   ❌ فشل: HTTP {resp.status_code}", flush=True)
                    
            except Exception as e:
                print(f"   ❌ خطأ: {str(e)[:50]}", flush=True)
            
            time.sleep(1)
    
    def fetch_all_players(self):
        """جلب كل اللاعبين من كل الفرق"""
        print("\n👥 [المرحلة 2] جلب كل اللاعبين...", flush=True)
        
        # Get all teams from Supabase
        url = f"{self.supabase_url}/teams?select=id"
        resp = requests.get(url, headers=self.supabase_headers, timeout=10)
        
        if resp.status_code != 200:
            print("❌ فشل جلب الفرق من Supabase", flush=True)
            return
        
        teams = resp.json()
        print(f"📊 عدد الفرق الكلي: {len(teams)}", flush=True)
        
        headers = {
            "X-RapidAPI-Key": self.api_football_key,
            "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
        }
        
        for idx, team in enumerate(teams):
            team_id = team["id"]
            print(f"\n👕 [{idx+1}/{len(teams)}] فريق ID: {team_id}", flush=True)
            
            try:
                players_url = "https://api-football-v1.p.rapidapi.com/v3/players"
                resp = requests.get(players_url, headers=headers, params={"team": team_id, "season": 2025}, timeout=20)
                
                if resp.status_code == 200:
                    players_data = resp.json().get("response", [])
                    print(f"   عدد اللاعبين: {len(players_data)}", flush=True)
                    
                    for item in players_data:
                        player = item.get("player", {})
                        if player.get("id"):
                            if self.upsert_to_supabase("players", {
                                "id": player.get("id"), "name": player.get("name"),
                                "firstname": player.get("firstname"), "lastname": player.get("lastname"),
                                "age": player.get("age"), "nationality": player.get("nationality"),
                                "height": player.get("height"), "weight": player.get("weight"),
                                "photo_url": player.get("photo"), "team_id": team_id
                            }):
                                self.stats["players"] += 1
                else:
                    print(f"   ❌ فشل: HTTP {resp.status_code}", flush=True)
                    
            except Exception as e:
                print(f"   ❌ خطأ: {str(e)[:50]}", flush=True)
            
            time.sleep(0.5)
    
    def fetch_all_matches(self):
        """جلب كل المباريات لكل موسم من 2000 إلى 2026"""
        print("\n📅 [المرحلة 3] جلب كل المباريات...", flush=True)
        print(f"📆 المواسم: {len(self.seasons)} موسماً", flush=True)
        
        headers = {
            "X-RapidAPI-Key": self.api_football_key,
            "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
        }
        
        total_combinations = len(self.leagues) * len([s for s in self.seasons if s >= 2015])
        current = 0
        
        for league in self.leagues:
            for season in self.seasons:
                if season < 2015:  # API Football data starts 2015
                    continue
                    
                current += 1
                print(f"\n⚽ [{current}/{total_combinations}] {league['name']} - موسم {season}", flush=True)
                
                try:
                    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
                    resp = requests.get(url, headers=headers, params={"league": league["id"], "season": season}, timeout=20)
                    
                    if resp.status_code == 200:
                        fixtures = resp.json().get("response", [])
                        print(f"   عدد المباريات: {len(fixtures)}", flush=True)
                        
                        for fixture in fixtures:
                            f = fixture.get("fixture", {})
                            teams = fixture.get("teams", {})
                            goals = fixture.get("goals", {})
                            
                            if f.get("id"):
                                if self.upsert_to_supabase("matches", {
                                    "id": f.get("id"), "league_id": league["id"], "season": season,
                                    "home_team_id": teams.get("home", {}).get("id"),
                                    "away_team_id": teams.get("away", {}).get("id"),
                                    "home_score": goals.get("home"), "away_score": goals.get("away"),
                                    "match_date": f.get("date", "").split("T")[0] if f.get("date") else None,
                                    "status": f.get("status", {}).get("short")
                                }):
                                    self.stats["matches"] += 1
                                
                                # Fetch events for each match
                                self.fetch_match_events(f.get("id"))
                    else:
                        print(f"   ❌ فشل: HTTP {resp.status_code}", flush=True)
                        
                except Exception as e:
                    print(f"   ❌ خطأ: {str(e)[:50]}", flush=True)
                
                time.sleep(1)
    
    def fetch_match_events(self, match_id):
        """جلب أحداث المباراة"""
        if not match_id:
            return
        
        headers = {
            "X-RapidAPI-Key": self.api_football_key,
            "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
        }
        
        try:
            url = "https://api-football-v1.p.rapidapi.com/v3/fixtures/events"
            resp = requests.get(url, headers=headers, params={"fixture": match_id}, timeout=15)
            
            if resp.status_code == 200:
                events = resp.json().get("response", [])
                for event in events:
                    if self.upsert_to_supabase("match_events", {
                        "id": f"{match_id}_{event.get('time', {}).get('elapsed')}_{event.get('player_id')}",
                        "match_id": match_id, "event_type": event.get("type"),
                        "player_id": event.get("player_id"), "player_name": event.get("player"),
                        "minute": event.get("time", {}).get("elapsed")
                    }):
                        self.stats["events"] += 1
        except:
            pass
    
    def fetch_news(self):
        """جلب الأخبار"""
        print("\n📰 [المرحلة 4] جلب الأخبار...", flush=True)
        
        if not self.isports_key:
            print("⚠️ مفتاح iSports غير موجود", flush=True)
            return
        
        try:
            url = f"http://api.isportsapi.com/sport/football/news?api_key={self.isports_key}"
            resp = requests.get(url, timeout=15)
            
            if resp.status_code == 200:
                news_list = resp.json().get("data", [])
                print(f"📊 عدد الأخبار: {len(news_list)}", flush=True)
                
                for news in news_list:
                    if news.get("newsId"):
                        if self.upsert_to_supabase("media_news", {
                            "id": news.get("newsId"), "title": news.get("title"),
                            "content": news.get("content", "")[:1000], "source": news.get("source"),
                            "image_url": news.get("imageUrl"), "published_at": news.get("pubTime")
                        }):
                            self.stats["news"] += 1
            else:
                print(f"❌ فشل: HTTP {resp.status_code}", flush=True)
                
        except Exception as e:
            print(f"❌ خطأ: {str(e)[:50]}", flush=True)
    
    def run(self):
        """تشغيل السكربت"""
        print("\n" + "="*70, flush=True)
        print("🏆 أرشيف كرة القدم الشامل - كل الفرق - كل اللاعبين - كل المباريات", flush=True)
        print("="*70, flush=True)
        
        try:
            self.fetch_all_teams_stadiums_coaches()
            self.fetch_all_players()
            self.fetch_all_matches()
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
        print(f"   ✅ الأخبار: {self.stats['news']}", flush=True)
        print(f"⏱️ الزمن: {elapsed:.2f} ثانية", flush=True)
        print("="*70, flush=True)

if __name__ == "__main__":
    print("🔥 بدء التشغيل...", flush=True)
    archive = CompleteFootballArchive()
    archive.run()
    print("✅ اكتمل", flush=True)
