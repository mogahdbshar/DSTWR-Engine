import os
import requests
import json
import time
import hashlib
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys

# إعداد الطباعة الفورية
sys.stdout.reconfigure(line_buffering=True)

print("🚀 بدء تشغيل أرشيف كرة القدم الشامل - إصدار المصادر الحقيقية", flush=True)

class UltimateFootballArchive:
    def __init__(self):
        print("📦 تهيئة المتغيرات والاتصالات...", flush=True)
        
        # --- Supabase ---
        self.supabase_url = "https://nugskdozmxlgrnkfsxlg.supabase.co/rest/v1"
        self.supabase_key = os.getenv("SUPABASE_KEY")
        if not self.supabase_key:
            raise Exception("❌ SUPABASE_KEY غير موجود في الأسرار!")
        self.supabase_headers = {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json"
        }
        
        # --- المصادر ---
        # 1. المصدر الأساسي (مجاني، بدون مفتاح)
        self.openfootball_url = "https://raw.githubusercontent.com/openfootball/football.json/master"
        
        # 2. Sportmonks API (للاعبين والمدربين)
        self.sportmonks_key = os.getenv("SPORTMONKS_KEY")
        print(f"   🔑 SPORTMONKS_KEY: {'✅ موجود' if self.sportmonks_key else '❌ مفقود'}")
        
        # 3. API-Football (للإحصائيات والترتيب)
        self.api_football_key = os.getenv("API_FOOTBALL_KEY")
        print(f"   🔑 API_FOOTBALL_KEY: {'✅ موجود' if self.api_football_key else '❌ مفقود'}")
        
        # قائمة الدوريات والمواسم
        self.leagues = [
            {"code": "en.1", "name": "Premier League", "api_id": 39},
            {"code": "es.1", "name": "La Liga", "api_id": 140},
            {"code": "de.1", "name": "Bundesliga", "api_id": 78},
            {"code": "it.1", "name": "Serie A", "api_id": 135},
            {"code": "fr.1", "name": "Ligue 1", "api_id": 61},
            {"code": "nl.1", "name": "Eredivisie", "api_id": 88},
            {"code": "pt.1", "name": "Primeira Liga", "api_id": 94},
            {"code": "tr.1", "name": "Super Lig", "api_id": 203},
            {"code": "ru.1", "name": "Premier Liga", "api_id": 235},
        ]
        self.seasons = list(range(2015, 2026))  # من 2015 إلى 2025
        
        # إحصائيات العملية
        self.stats = {"teams": 0, "stadiums": 0, "matches": 0, "players": 0, "coaches": 0, "match_stats": 0, "standings": 0, "errors": 0}
        self.start_time = datetime.now()
        self.executor = ThreadPoolExecutor(max_workers=3)  # للطلبات المتوازية
        
        print(f"🏟️ عدد الدوريات: {len(self.leagues)}", flush=True)
        print(f"📅 المواسم: {min(self.seasons)} - {max(self.seasons)}", flush=True)
        print("="*70, flush=True)

    # --- دالة الرفع الذكية إلى Supabase (Upsert) ---
    def upsert_to_supabase(self, table, data_list, conflict_key="id"):
        if not data_list:
            return 0
        if not isinstance(data_list, list):
            data_list = [data_list]
        
        inserted_count = 0
        # نرسل البيانات على دفعات صغيرة لتجنب أخطاء الحجم
        for i in range(0, len(data_list), 20):
            batch = data_list[i:i+20]
            try:
                # استخدام Prefer: resolution=merge-duplicates لتنفيذ Upsert
                headers = self.supabase_headers.copy()
                headers["Prefer"] = "resolution=merge-duplicates,return=minimal"
                response = requests.post(f"{self.supabase_url}/{table}", headers=headers, json=batch, timeout=15)
                if response.status_code in [200, 201]:
                    inserted_count += len(batch)
                else:
                    print(f"      ⚠️ فشل رفع دفعة إلى {table}: {response.status_code}", flush=True)
                    self.stats["errors"] += len(batch)
            except Exception as e:
                print(f"      ❌ خطأ في رفع دفعة إلى {table}: {e}", flush=True)
                self.stats["errors"] += len(batch)
            time.sleep(0.1)
        return inserted_count

    # --- المرحلة 1: جلب الأرشيف الأساسي من openfootball ---
    def fetch_historical_data(self):
        print("\n📥 [المرحلة 1/3] جلب البيانات التاريخية (الفرق، المباريات، الملاعب)...", flush=True)
        all_teams, all_stadiums, all_matches = [], [], []
        
        for league in self.leagues:
            for season in self.seasons:
                url = f"{self.openfootball_url}/data/{season}/{league['code']}.json"
                try:
                    resp = requests.get(url, timeout=10)
                    if resp.status_code == 200:
                        data = resp.json()
                        print(f"   ✅ {league['name']} - {season}: {len(data.get('teams', []))} فريق, {len(data.get('matches', []))} مباراة", flush=True)
                        
                        # تجهيز الفرق والملاعب
                        for team in data.get("teams", []):
                            team_id = team.get("id")
                            if team_id:
                                all_teams.append({
                                    "id": team_id,
                                    "name": team.get("name"),
                                    "code": team.get("code"),
                                    "country": team.get("country"),
                                    "league_code": league['code']
                                })
                                if team.get("stadium"):
                                    all_stadiums.append({
                                        "id": f"{team_id}_stadium",
                                        "name": team.get("stadium"),
                                        "team_id": team_id,
                                        "city": team.get("city")
                                    })
                        
                        # تجهيز المباريات
                        for match in data.get("matches", []):
                            match_id = hashlib.md5(f"{league['code']}_{season}_{match.get('date')}_{match.get('team1')}_{match.get('team2')}".encode()).hexdigest()
                            all_matches.append({
                                "id": match_id,
                                "league_id": league['code'],
                                "season": season,
                                "home_team": match.get("team1"),
                                "away_team": match.get("team2"),
                                "home_score": match.get("score1"),
                                "away_score": match.get("score2"),
                                "match_date": match.get("date"),
                                "status": "finished"
                            })
                except Exception as e:
                    pass
                time.sleep(0.2)
        
        print(f"\n   📊 الإجمالي: {len(all_teams)} فريق، {len(all_stadiums)} ملعب، {len(all_matches)} مباراة", flush=True)
        print("   ⬆️ جاري الرفع إلى Supabase...", flush=True)
        self.stats['teams'] = self.upsert_to_supabase("teams", all_teams)
        self.stats['stadiums'] = self.upsert_to_supabase("stadiums", all_stadiums)
        self.stats['matches'] = self.upsert_to_supabase("matches", all_matches)
        print(f"   ✅ تم رفع {self.stats['teams']} فريق، {self.stats['stadiums']} ملعب، {self.stats['matches']} مباراة.", flush=True)

    # --- المرحلة 2: جلب بيانات اللاعبين والمدربين من Sportmonks ---
    def fetch_players_and_coaches(self):
        print("\n👥 [المرحلة 2/3] جلب بيانات اللاعبين والمدربين من Sportmonks...", flush=True)
        if not self.sportmonks_key:
            print("   ⚠️ مفتاح SPORTMONKS_KEY غير موجود. سيتم تخطي هذه المرحلة.", flush=True)
            return
        
        # جلب قائمة الفرق من قاعدة البيانات أولاً
        response = requests.get(f"{self.supabase_url}/teams?select=id&limit=100", headers=self.supabase_headers)
        if response.status_code != 200:
            print("   ❌ فشل جلب قائمة الفرق من Supabase", flush=True)
            return
        teams = response.json()
        
        all_players, all_coaches = [], []
        for team in teams[:50]:  # نبدأ بـ 50 فريقًا لتجنب استنزاف الـ API بسرعة
            team_id = team['id']
            print(f"   🧑‍🏫 معالجة الفريق {team_id}...", flush=True)
            
            # 1. جلب اللاعبين (باستخدام نقطة نهاية الفريق)
            players_url = f"https://soccer.sportmonks.com/api/v2.0/players/team/{team_id}?api_token={self.sportmonks_key}&include=position"
            try:
                resp = requests.get(players_url, timeout=10)
                if resp.status_code == 200:
                    players_data = resp.json().get("data", [])
                    for player in players_data:
                        all_players.append({
                            "id": player['id'],
                            "name": player['display_name'],
                            "team_id": team_id,
                            "position": player.get('position', {}).get('name'),
                            "nationality": player.get('country', {}).get('name'),
                            "updated_at": datetime.now().isoformat()
                        })
                    print(f"      ✅ تم جلب {len(players_data)} لاعب.", flush=True)
                else:
                    print(f"      ⚠️ فشل جلب اللاعبين للفريق {team_id}: {resp.status_code}", flush=True)
            except Exception as e:
                print(f"      ❌ خطأ: {e}", flush=True)
            
            # 2. جلب المدرب (من نقطة نهاية معلومات النادي)
            coach_url = f"https://soccer.sportmonks.com/api/v2.0/teams/{team_id}?api_token={self.sportmonks_key}&include=coach"
            try:
                resp = requests.get(coach_url, timeout=10)
                if resp.status_code == 200:
                    team_info = resp.json().get("data", {})
                    coach = team_info.get('coach', {})
                    if coach:
                        all_coaches.append({
                            "id": coach.get('id'),
                            "name": coach.get('name'),
                            "team_id": team_id,
                            "nationality": coach.get('country', {}).get('name'),
                            "updated_at": datetime.now().isoformat()
                        })
                        print(f"      ✅ تم جلب المدرب {coach.get('name')}.", flush=True)
            except Exception as e:
                print(f"      ❌ خطأ في جلب المدرب: {e}", flush=True)
            
            time.sleep(1)  # تجنب بلوغ حد الـ API
        
        print(f"\n   📊 الإجمالي: {len(all_players)} لاعب، {len(all_coaches)} مدرب", flush=True)
        self.stats['players'] = self.upsert_to_supabase("players", all_players)
        self.stats['coaches'] = self.upsert_to_supabase("coaches", all_coaches)
        print(f"   ✅ تم رفع {self.stats['players']} لاعب و {self.stats['coaches']} مدرب.", flush=True)

    # --- المرحلة 3: جلب الإحصائيات والترتيب من API-Football ---
    def fetch_stats_and_standings(self):
        print("\n📊 [المرحلة 3/3] جلب إحصائيات المباريات والترتيب من API-Football...", flush=True)
        if not self.api_football_key:
            print("   ⚠️ مفتاح API_FOOTBALL_KEY غير موجود. سيتم تخطي هذه المرحلة.", flush=True)
            return
        
        headers = {"X-RapidAPI-Key": self.api_football_key, "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"}
        current_season = 2025
        
        for league in self.leagues:
            league_api_id = league.get('api_id')
            if not league_api_id:
                continue
            
            # 1. الترتيب
            standings_url = "https://api-football-v1.p.rapidapi.com/v3/standings"
            params = {"league": league_api_id, "season": current_season}
            try:
                resp = requests.get(standings_url, headers=headers, params=params, timeout=10)
                if resp.status_code == 200:
                    standings_data = []
                    for item in resp.json().get('response', []):
                        for standing in item.get('league', {}).get('standings', []):
                            for team in standing:
                                standings_data.append({
                                    "id": f"{league_api_id}_{team['team']['id']}_{current_season}",
                                    "league_id": league_api_id,
                                    "team_id": team['team']['id'],
                                    "position": team['rank'],
                                    "points": team['points'],
                                    "played": team['all']['played'],
                                    "updated_at": datetime.now().isoformat()
                                })
                    self.stats['standings'] += self.upsert_to_supabase("league_standings", standings_data)
                    print(f"   ✅ تم تحديث ترتيب {league['name']}.", flush=True)
                else:
                    print(f"   ⚠️ فشل جلب ترتيب {league['name']}: {resp.status_code}", flush=True)
            except Exception as e:
                print(f"   ❌ خطأ: {e}", flush=True)
            
            # 2. إحصائيات المباريات (للبحث عن مباراة حديثة كمثال)
            fixtures_url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
            params_fix = {"league": league_api_id, "season": current_season, "last": 1}
            try:
                resp = requests.get(fixtures_url, headers=headers, params=params_fix, timeout=10)
                if resp.status_code == 200:
                    fixtures = resp.json().get('response', [])
                    for fixture in fixtures:
                        fixture_id = fixture['fixture']['id']
                        stats_url = "https://api-football-v1.p.rapidapi.com/v3/fixtures/statistics"
                        stats_resp = requests.get(stats_url, headers=headers, params={"fixture": fixture_id}, timeout=10)
                        if stats_resp.status_code == 200:
                            stats_list = []
                            for team_stats in stats_resp.json().get('response', []):
                                for stat in team_stats.get('statistics', []):
                                    stats_list.append({
                                        "id": f"{fixture_id}_{team_stats['team']['id']}_{stat['type']}",
                                        "fixture_id": fixture_id,
                                        "team_id": team_stats['team']['id'],
                                        "stat_type": stat['type'],
                                        "value": stat['value']
                                    })
                            self.stats['match_stats'] += self.upsert_to_supabase("match_stats", stats_list)
                            print(f"   ✅ تم تحديث إحصائيات مباراة {fixture_id}.", flush=True)
                else:
                    print(f"   ⚠️ فشل جلب آخر مباراة لـ {league['name']}: {resp.status_code}", flush=True)
            except Exception as e:
                print(f"   ❌ خطأ: {e}", flush=True)
            
            time.sleep(3)  # تجنب بلوغ حد الـ API (100 طلب في اليوم)

    # --- الوظيفة الرئيسية ---
    def run(self):
        print("\n" + "="*70, flush=True)
        print("🏆 بدء تنفيذ عملية أرشفة كرة القدم الشاملة", flush=True)
        print("="*70, flush=True)
        
        self.fetch_historical_data()
        self.fetch_players_and_coaches()
        self.fetch_stats_and_standings()
        
        # الإحصائيات النهائية
        elapsed = (datetime.now() - self.start_time).total_seconds()
        print("\n" + "="*70, flush=True)
        print("🏆 اكتمل الأرشيف!", flush=True)
        print("="*70, flush=True)
        print(f"   ✅ الفرق (teams): {self.stats['teams']}")
        print(f"   ✅ الملاعب (stadiums): {self.stats['stadiums']}")
        print(f"   ✅ المباريات (matches): {self.stats['matches']}")
        print(f"   ✅ اللاعبين (players): {self.stats['players']}")
        print(f"   ✅ المدربين (coaches): {self.stats['coaches']}")
        print(f"   ✅ إحصائيات المباريات (match_stats): {self.stats['match_stats']}")
        print(f"   ✅ الترتيب (standings): {self.stats['standings']}")
        print(f"   ❌ الأخطاء: {self.stats['errors']}")
        print(f"⏱️ الزمن الإجمالي: {elapsed//60:.0f} دقيقة و {elapsed%60:.0f} ثانية")
        print("="*70, flush=True)

if __name__ == "__main__":
    archive = UltimateFootballArchive()
    archive.run()
