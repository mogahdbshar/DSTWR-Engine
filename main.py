import os
import requests
import json
import time
import hashlib
import csv
import io
from datetime import datetime
import sys

sys.stdout.reconfigure(line_buffering=True)

print("🚀 بدء تشغيل أرشيف كرة القدم الشامل - إصدار متعدد المصادر", flush=True)

class UltimateFootballArchive:
    def __init__(self):
        print("📦 تهيئة المتغيرات...", flush=True)
        
        # Supabase
        self.supabase_url = "https://nugskdozmxlgrnkfsxlg.supabase.co/rest/v1"
        self.supabase_key = os.getenv("SUPABASE_KEY")
        if not self.supabase_key:
            raise Exception("❌ SUPABASE_KEY غير موجود!")
        self.supabase_headers = {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json"
        }
        
        # عناوين المصادر
        self.football_json_url = "https://raw.githubusercontent.com/openfootball/football.json/master"
        self.worldcup_url = "https://raw.githubusercontent.com/openfootball/worldcup.json/master"
        self.club_dataset_url = "https://raw.githubusercontent.com/xgabora/Club-Football-Match-Data-2000-2025/main/matches.csv"
        
        # قائمة الدوريات (42 دوري)
        self.leagues = [
            {"code": "en.1", "name": "Premier League", "api_id": 39},
            {"code": "en.2", "name": "Championship", "api_id": 40},
            {"code": "de.1", "name": "Bundesliga", "api_id": 78},
            {"code": "de.2", "name": "2. Bundesliga", "api_id": 79},
            {"code": "es.1", "name": "La Liga", "api_id": 140},
            {"code": "es.2", "name": "Segunda Division", "api_id": 141},
            {"code": "it.1", "name": "Serie A", "api_id": 135},
            {"code": "it.2", "name": "Serie B", "api_id": 136},
            {"code": "fr.1", "name": "Ligue 1", "api_id": 61},
            {"code": "fr.2", "name": "Ligue 2", "api_id": 62},
            {"code": "nl.1", "name": "Eredivisie", "api_id": 88},
            {"code": "pt.1", "name": "Primeira Liga", "api_id": 94},
            {"code": "tr.1", "name": "Super Lig", "api_id": 203},
            {"code": "ru.1", "name": "Premier Liga", "api_id": 235},
            {"code": "be.1", "name": "Pro League", "api_id": 144},
            {"code": "sc.1", "name": "Scottish Premiership", "api_id": 179},
            {"code": "at.1", "name": "Austrian Bundesliga", "api_id": 218},
            {"code": "ch.1", "name": "Swiss Super League", "api_id": 253},
            {"code": "gr.1", "name": "Super League Greece", "api_id": 197},
            {"code": "cz.1", "name": "Czech First League", "api_id": 274},
            {"code": "hr.1", "name": "Croatian League", "api_id": 276},
            {"code": "dk.1", "name": "Danish Superliga", "api_id": 271},
            {"code": "se.1", "name": "Allsvenskan", "api_id": 272},
            {"code": "no.1", "name": "Eliteserien", "api_id": 273},
            {"code": "pl.1", "name": "Ekstraklasa", "api_id": 278},
            {"code": "ua.1", "name": "Premier League Ukraine", "api_id": 275},
            {"code": "jp.1", "name": "J1 League", "api_id": 281},
            {"code": "kr.1", "name": "K League", "api_id": 284},
            {"code": "cn.1", "name": "Chinese Super League", "api_id": 282},
            {"code": "au.1", "name": "A-League", "api_id": 285},
            {"code": "us.1", "name": "MLS", "api_id": 253},
            {"code": "br.1", "name": "Serie A Brazil", "api_id": 71},
            {"code": "ar.1", "name": "Liga Profesional", "api_id": 119},
            {"code": "mx.1", "name": "Liga MX", "api_id": 262},
            {"code": "cl.1", "name": "Chilean Primera", "api_id": 296},
        ]
        
        # المواسم من 2000 إلى 2027
        self.seasons = list(range(2000, 2028))
        
        # كؤوس العالم من 2010 إلى 2026 (المستقبلية)
        self.world_cups = [
            {"year": 2010, "name": "South Africa 2010"},
            {"year": 2014, "name": "Brazil 2014"},
            {"year": 2018, "name": "Russia 2018"},
            {"year": 2022, "name": "Qatar 2022"},
            {"year": 2026, "name": "USA-Canada-Mexico 2026"},
        ]
        
        # إحصائيات العملية
        self.stats = {
            "teams": 0, "stadiums": 0, "matches": 0,
            "players": 0, "coaches": 0, "standings": 0,
            "errors": 0, "total": 0
        }
        self.start_time = datetime.now()
        
        print(f"🏟️ عدد الدوريات: {len(self.leagues)}", flush=True)
        print(f"📅 المواسم: {min(self.seasons)} - {max(self.seasons)}", flush=True)
        print("🌍 كؤوس العالم المستهدفة: 2010, 2014, 2018, 2022, 2026", flush=True)
        print("="*70, flush=True)

    # --- دالة الرفع الذكية (Upsert) ---
    def upsert_to_supabase(self, table, data_list, conflict_key="id"):
        if not data_list:
            return 0
        if not isinstance(data_list, list):
            data_list = [data_list]
        
        inserted_count = 0
        for i in range(0, len(data_list), 50):
            batch = data_list[i:i+50]
            try:
                headers = self.supabase_headers.copy()
                headers["Prefer"] = "resolution=merge-duplicates,return=minimal"
                response = requests.post(f"{self.supabase_url}/{table}", headers=headers, json=batch, timeout=15)
                if response.status_code in [200, 201]:
                    inserted_count += len(batch)
                    self.stats["total"] += len(batch)
                    if table in self.stats:
                        self.stats[table] += len(batch)
                else:
                    print(f"      ⚠️ فشل رفع دفعة إلى {table}: {response.status_code}", flush=True)
                    self.stats["errors"] += len(batch)
            except Exception as e:
                print(f"      ❌ خطأ في رفع دفعة: {str(e)[:50]}", flush=True)
                self.stats["errors"] += len(batch)
            time.sleep(0.1)
        return inserted_count

    # ========== المرحلة 1: بيانات الدوريات ==========
    def fetch_leagues_data(self):
        print("\n📥 [المرحلة 1/3] جلب بيانات الدوريات (2010-2027)...", flush=True)
        all_teams, all_stadiums, all_matches = [], [], []
        
        for league in self.leagues:
            print(f"\n   🏟️ معالجة: {league['name']}", flush=True)
            for season in self.seasons:
                if season < 2010:
                    continue
                url = f"{self.football_json_url}/data/{season}/{league['code']}.json"
                try:
                    resp = requests.get(url, timeout=10)
                    if resp.status_code == 200:
                        data = resp.json()
                        print(f"      ✅ موسم {season}: {len(data.get('teams', []))} فريق, {len(data.get('matches', []))} مباراة", flush=True)
                        
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
                time.sleep(0.1)
        
        print(f"\n   📊 إجمالي البيانات المجمعة: {len(all_teams)} فريق, {len(all_stadiums)} ملعب, {len(all_matches)} مباراة", flush=True)
        print("   ⬆️ جاري الرفع إلى Supabase...", flush=True)
        self.stats['teams'] = self.upsert_to_supabase("teams", all_teams)
        self.stats['stadiums'] = self.upsert_to_supabase("stadiums", all_stadiums)
        self.stats['matches'] = self.upsert_to_supabase("matches", all_matches)
        print(f"   ✅ تم رفع {self.stats['teams']} فريق، {self.stats['stadiums']} ملعب، {self.stats['matches']} مباراة.", flush=True)

    # ========== المرحلة 2: بيانات كأس العالم (حتى 2026) ==========
    def fetch_worldcup_data(self):
        print("\n🌍 [المرحلة 2/3] جلب بيانات كأس العالم (2010-2026)...", flush=True)
        all_matches = []
        
        for cup in self.world_cups:
            year = cup['year']
            url = f"{self.worldcup_url}/worldcup_{year}.json"
            print(f"   📅 معالجة: كأس العالم {cup['name']}", flush=True)
            try:
                resp = requests.get(url, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    rounds = data.get('rounds', [])
                    match_count = 0
                    for r in rounds:
                        for match in r.get('matches', []):
                            match_count += 1
                            match_id = f"wc_{year}_{match.get('num')}"
                            all_matches.append({
                                "id": match_id,
                                "tournament": "FIFA World Cup",
                                "season": year,
                                "home_team": match.get('team1', {}).get('name'),
                                "away_team": match.get('team2', {}).get('name'),
                                "home_score": match.get('score1'),
                                "away_score": match.get('score2'),
                                "match_date": match.get('date'),
                                "status": "finished"
                            })
                    print(f"      ✅ تم تجميع {match_count} مباراة", flush=True)
                else:
                    print(f"      ⚠️ لا توجد بيانات متاحة (الرمز {resp.status_code})", flush=True)
            except Exception as e:
                print(f"      ❌ فشل: {str(e)[:50]}", flush=True)
            time.sleep(0.5)
        
        if all_matches:
            print(f"\n   📊 إجمالي مباريات كأس العالم المجمعة: {len(all_matches)}", flush=True)
            self.upsert_to_supabase("matches", all_matches)
        else:
            print("   ⚠️ لم يتم العثور على بيانات.", flush=True)

    # ========== المرحلة 3: بيانات Club Football Dataset الضخمة ==========
    def fetch_club_dataset(self):
        print("\n📊 [المرحلة 3/3] جلب البيانات الضخمة (Club Football Dataset)...", flush=True)
        print("   📥 تحميل الملف (51 MB)... قد يستغرق دقيقة.", flush=True)
        
        try:
            resp = requests.get(self.club_dataset_url, timeout=60)
            if resp.status_code != 200:
                print(f"   ❌ فشل التحميل: HTTP {resp.status_code}", flush=True)
                return
            
            print("   ✅ تم التحميل. بدء المعالجة...", flush=True)
            csv_reader = csv.DictReader(io.StringIO(resp.text))
            
            all_matches = []
            all_stats = []
            match_count = 0
            
            for row in csv_reader:
                match_count += 1
                match_id = hashlib.md5(f"{row.get('date')}_{row.get('home_team')}_{row.get('away_team')}_{row.get('league')}".encode()).hexdigest()
                
                # تجهيز بيانات المباراة الأساسية
                all_matches.append({
                    "id": match_id,
                    "league_id": row.get('league'),
                    "season": row.get('season'),
                    "home_team": row.get('home_team'),
                    "away_team": row.get('away_team'),
                    "home_score": row.get('home_score'),
                    "away_score": row.get('away_score'),
                    "match_date": row.get('date'),
                    "status": "finished"
                })
                
                # تجهيز الإحصائيات (الأهداف، الكروت، إلخ)
                if 'home_goals' in row:
                    all_stats.append({
                        "id": f"{match_id}_home",
                        "match_id": match_id,
                        "team": "home",
                        "goals": row.get('home_goals'),
                        "assists": row.get('home_assists'),
                        "cards": row.get('home_cards'),
                        "possession": row.get('home_possession'),
                        "shots": row.get('home_shots'),
                        "corners": row.get('home_corners'),
                    })
                    all_stats.append({
                        "id": f"{match_id}_away",
                        "match_id": match_id,
                        "team": "away",
                        "goals": row.get('away_goals'),
                        "assists": row.get('away_assists'),
                        "cards": row.get('away_cards'),
                        "possession": row.get('away_possession'),
                        "shots": row.get('away_shots'),
                        "corners": row.get('away_corners'),
                    })
                
                if match_count % 50000 == 0:
                    print(f"      ✅ تمت معالجة {match_count} مباراة...", flush=True)
            
            print(f"\n   📊 الإجمالي: {len(all_matches)} مباراة, {len(all_stats)} إحصائية", flush=True)
            print("   ⬆️ جاري الرفع إلى Supabase...", flush=True)
            
            self.stats['matches'] += self.upsert_to_supabase("matches", all_matches)
            self.stats['match_stats'] = self.upsert_to_supabase("match_stats", all_stats)
            
            print(f"   ✅ تم رفع {self.stats['matches']} مباراة و {self.stats['match_stats']} إحصائية.", flush=True)
            
        except Exception as e:
            print(f"   ❌ فشل معالجة Club Dataset: {str(e)}", flush=True)

    # ========== التشغيل الرئيسي ==========
    def run(self):
        print("\n" + "="*70, flush=True)
        print("🏆 بدء تنفيذ عملية أرشفة كرة القدم الشاملة", flush=True)
        print("="*70, flush=True)
        
        self.fetch_leagues_data()
        self.fetch_worldcup_data()
        self.fetch_club_dataset()
        
        # الإحصائيات النهائية
        elapsed = (datetime.now() - self.start_time).total_seconds()
        print("\n" + "="*70, flush=True)
        print("🏆 اكتمل الأرشيف!", flush=True)
        print("="*70, flush=True)
        print(f"   ✅ الفرق (teams): {self.stats.get('teams', 0)}")
        print(f"   ✅ الملاعب (stadiums): {self.stats.get('stadiums', 0)}")
        print(f"   ✅ المباريات (matches): {self.stats.get('matches', 0)}")
        print(f"   ✅ إحصائيات (match_stats): {self.stats.get('match_stats', 0)}")
        print(f"   ❌ الأخطاء: {self.stats['errors']}")
        print(f"   📊 إجمالي المعالجة: {self.stats['total']}")
        print(f"⏱️ الزمن الإجمالي: {elapsed//60:.0f} دقيقة و {elapsed%60:.0f} ثانية")
        print("="*70, flush=True)

if __name__ == "__main__":
    archive = UltimateFootballArchive()
    archive.run()
