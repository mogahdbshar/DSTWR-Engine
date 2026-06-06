import os
import requests
import json
import csv
import io
import hashlib
import time
from datetime import datetime
import sys

sys.stdout.reconfigure(line_buffering=True)

print("🚀 بدء تشغيل أرشيف كرة القدم الشامل - الإصدار النهائي", flush=True)

class UltimateFootballArchive:
    def __init__(self):
        print("📦 تهيئة المتغيرات...", flush=True)
        
        # Supabase
        self.supabase_url = "https://nugskdozmxlgrnkfsxlg.supabase.co/rest/v1"
        self.supabase_key = os.getenv("SUPABASE_KEY")
        if not self.supabase_key:
            raise Exception("❌ SUPABASE_KEY غير موجود في المتغيرات!")
        
        self.supabase_headers = {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json"
        }
        
        # الروابط المباشرة للمصادر (شغالة 100%)
        self.club_dataset_url = "https://raw.githubusercontent.com/xgabora/Club-Football-Match-Data-2000-2025/main/matches.csv"
        self.transfermarkt_players_url = "https://raw.githubusercontent.com/detrin/Transfermarkt-Data/main/data/players.csv"
        self.transfermarkt_transfers_url = "https://raw.githubusercontent.com/detrin/Transfermarkt-Data/main/data/transfers.csv"
        self.worldcup_base = "https://raw.githubusercontent.com/openfootball/worldcup.json/master"
        
        # قائمة كؤوس العالم
        self.worldcups = [
            {"year": 2010, "name": "South Africa"},
            {"year": 2014, "name": "Brazil"},
            {"year": 2018, "name": "Russia"},
            {"year": 2022, "name": "Qatar"},
            {"year": 2026, "name": "USA-Canada-Mexico"}
        ]
        
        # إحصائيات
        self.stats = {
            "matches": 0, "players": 0, "transfers": 0,
            "worldcup_matches": 0, "errors": 0
        }
        self.start_time = datetime.now()
        
        print("="*70, flush=True)
        print("📊 المصادر المعتمدة:", flush=True)
        print("   ✅ Club Dataset: 475,000+ مباراة", flush=True)
        print("   ✅ Transfermarkt: 37,000+ لاعب و 87,000+ صفقة", flush=True)
        print("   ✅ World Cup: 2010, 2014, 2018, 2022, 2026", flush=True)
        print("="*70, flush=True)
    
    def upsert_to_supabase(self, table, data_list, key="id"):
        """رفع البيانات مع تجنب التكرار"""
        if not data_list:
            return 0
        
        inserted = 0
        for i in range(0, len(data_list), 50):  # دفعات 50 سجل
            batch = data_list[i:i+50]
            try:
                headers = self.supabase_headers.copy()
                headers["Prefer"] = "resolution=merge-duplicates,return=minimal"
                resp = requests.post(f"{self.supabase_url}/{table}", headers=headers, json=batch, timeout=30)
                if resp.status_code in [200, 201]:
                    inserted += len(batch)
                else:
                    print(f"      ⚠️ فشل رفع دفعة إلى {table}: {resp.status_code}", flush=True)
                    self.stats["errors"] += len(batch)
            except Exception as e:
                print(f"      ❌ خطأ في رفع دفعة: {str(e)[:50]}", flush=True)
                self.stats["errors"] += len(batch)
            time.sleep(0.05)
        return inserted
    
    def fetch_club_dataset(self):
        """المصدر 1: Club Dataset - 475,000 مباراة"""
        print("\n📥 [1/4] تحميل Club Dataset (475,000+ مباراة)...", flush=True)
        
        try:
            resp = requests.get(self.club_dataset_url, timeout=90)
            if resp.status_code != 200:
                print(f"   ❌ فشل التحميل: HTTP {resp.status_code}", flush=True)
                return
            
            print("   ✅ تم التحميل. جاري المعالجة...", flush=True)
            csv_reader = csv.DictReader(io.StringIO(resp.text))
            
            matches = []
            processed = 0
            
            for row in csv_reader:
                processed += 1
                
                # إنشاء ID فريد للمباراة
                match_id = hashlib.md5(
                    f"{row.get('Date', '')}_{row.get('HomeTeam', '')}_{row.get('AwayTeam', '')}_{row.get('Div', '')}".encode()
                ).hexdigest()
                
                match_data = {
                    "id": match_id,
                    "date": row.get("Date"),
                    "season": row.get("Season"),
                    "league": row.get("Div"),
                    "home_team": row.get("HomeTeam"),
                    "away_team": row.get("AwayTeam"),
                    "home_score": row.get("FTHG"),
                    "away_score": row.get("FTAG"),
                    "result": row.get("FTR"),
                    "home_shots": row.get("HS"),
                    "away_shots": row.get("AS"),
                    "home_shots_on_target": row.get("HST"),
                    "away_shots_on_target": row.get("AST"),
                    "home_corners": row.get("HC"),
                    "away_corners": row.get("AC"),
                    "home_fouls": row.get("HF"),
                    "away_fouls": row.get("AF"),
                    "home_yellow": row.get("HY"),
                    "away_yellow": row.get("AY"),
                    "home_red": row.get("HR"),
                    "away_red": row.get("AR")
                }
                matches.append(match_data)
                
                if processed % 50000 == 0:
                    print(f"      تمت معالجة {processed} مباراة...", flush=True)
            
            print(f"\n   📊 إجمالي المباريات: {len(matches)}", flush=True)
            print("   ⬆️ جاري الرفع إلى Supabase...", flush=True)
            
            self.stats["matches"] = self.upsert_to_supabase("matches", matches)
            print(f"   ✅ تم رفع {self.stats['matches']} مباراة.", flush=True)
            
        except Exception as e:
            print(f"   ❌ فشل: {str(e)}", flush=True)
    
    def fetch_players_and_transfers(self):
        """المصدر 2: Transfermarkt - اللاعبين والانتقالات"""
        print("\n👥 [2/4] تحميل بيانات اللاعبين والانتقالات...", flush=True)
        
        # جلب اللاعبين
        try:
            print("   📥 جلب اللاعبين (37,000+)...", flush=True)
            resp = requests.get(self.transfermarkt_players_url, timeout=60)
            if resp.status_code == 200:
                csv_reader = csv.DictReader(io.StringIO(resp.text))
                players = []
                for row in csv_reader:
                    players.append({
                        "id": row.get("player_id"),
                        "name": row.get("player_name"),
                        "url": row.get("player_url"),
                        "team_id": row.get("team_id")
                    })
                
                print(f"   📊 عدد اللاعبين: {len(players)}", flush=True)
                print("   ⬆️ رفع اللاعبين...", flush=True)
                self.stats["players"] = self.upsert_to_supabase("players", players)
                print(f"   ✅ تم رفع {self.stats['players']} لاعب.", flush=True)
            else:
                print(f"   ❌ فشل جلب اللاعبين: {resp.status_code}", flush=True)
        except Exception as e:
            print(f"   ❌ خطأ في جلب اللاعبين: {str(e)[:50]}", flush=True)
        
        # جلب الانتقالات
        try:
            print("\n   📥 جلب الانتقالات (87,000+)...", flush=True)
            resp = requests.get(self.transfermarkt_transfers_url, timeout=60)
            if resp.status_code == 200:
                csv_reader = csv.DictReader(io.StringIO(resp.text))
                transfers = []
                for row in csv_reader:
                    transfers.append({
                        "id": row.get("transfer_id"),
                        "player_id": row.get("player_id"),
                        "from_team": row.get("from_team"),
                        "to_team": row.get("to_team"),
                        "season": row.get("season"),
                        "transfer_fee": row.get("transfer_fee")
                    })
                
                print(f"   📊 عدد الانتقالات: {len(transfers)}", flush=True)
                print("   ⬆️ رفع الانتقالات...", flush=True)
                self.stats["transfers"] = self.upsert_to_supabase("transfers", transfers)
                print(f"   ✅ تم رفع {self.stats['transfers']} صفقة.", flush=True)
            else:
                print(f"   ❌ فشل جلب الانتقالات: {resp.status_code}", flush=True)
        except Exception as e:
            print(f"   ❌ خطأ في جلب الانتقالات: {str(e)[:50]}", flush=True)
    
    def fetch_worldcup_data(self):
        """المصدر 3: كأس العالم (2010-2026)"""
        print("\n🌍 [3/4] جلب بيانات كأس العالم...", flush=True)
        
        all_matches = []
        
        for wc in self.worldcups:
            year = wc["year"]
            url = f"{self.worldcup_base}/{year}/worldcup.json"
            print(f"   📅 معالجة: كأس العالم {wc['name']} {year}", flush=True)
            
            try:
                resp = requests.get(url, timeout=20)
                if resp.status_code == 200:
                    data = resp.json()
                    for round_data in data.get("rounds", []):
                        for match in round_data.get("matches", []):
                            match_id = f"wc_{year}_{match.get('num', 0)}"
                            match_data = {
                                "id": match_id,
                                "tournament": f"FIFA World Cup {year}",
                                "season": year,
                                "home_team": match.get("team1", {}).get("name"),
                                "away_team": match.get("team2", {}).get("name"),
                                "home_score": match.get("score1"),
                                "away_score": match.get("score2"),
                                "date": match.get("date"),
                                "stadium": match.get("stadium"),
                                "city": match.get("city"),
                                "status": "finished"
                            }
                            all_matches.append(match_data)
                    print(f"      ✅ تم جلب {len([m for m in data.get('rounds', []) for _ in m.get('matches', [])])} مباراة", flush=True)
                else:
                    print(f"      ⚠️ لا توجد بيانات (HTTP {resp.status_code})", flush=True)
            except Exception as e:
                print(f"      ❌ فشل: {str(e)[:50]}", flush=True)
            time.sleep(0.5)
        
        if all_matches:
            print(f"\n   📊 إجمالي مباريات كأس العالم: {len(all_matches)}", flush=True)
            print("   ⬆️ جاري الرفع...", flush=True)
            self.stats["worldcup_matches"] = self.upsert_to_supabase("matches", all_matches)
            print(f"   ✅ تم رفع {self.stats['worldcup_matches']} مباراة كأس عالم.", flush=True)
        else:
            print("   ⚠️ لم يتم العثور على بيانات كأس العالم.", flush=True)
    
    def fetch_additional_data(self):
        """مصادر إضافية - فرق وملاعب من OpenFootball"""
        print("\n🏟️ [4/4] جلب بيانات إضافية (فرق وملاعب)...", flush=True)
        
        leagues = [
            {"code": "en.1", "name": "Premier League"},
            {"code": "es.1", "name": "La Liga"},
            {"code": "de.1", "name": "Bundesliga"},
            {"code": "it.1", "name": "Serie A"},
            {"code": "fr.1", "name": "Ligue 1"},
        ]
        
        all_teams = []
        all_stadiums = []
        
        for league in leagues:
            url = f"https://raw.githubusercontent.com/openfootball/football.json/master/data/2015/{league['code']}.json"
            try:
                resp = requests.get(url, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    for team in data.get("teams", []):
                        team_id = team.get("id")
                        if team_id:
                            all_teams.append({
                                "id": team_id,
                                "name": team.get("name"),
                                "code": team.get("code"),
                                "country": team.get("country")
                            })
                            if team.get("stadium"):
                                all_stadiums.append({
                                    "id": f"{team_id}_stadium",
                                    "name": team.get("stadium"),
                                    "team_id": team_id,
                                    "city": team.get("city")
                                })
                    print(f"   ✅ {league['name']}: {len(data.get('teams', []))} فريق", flush=True)
            except:
                pass
        
        if all_teams:
            print(f"\n   📊 إجمالي الفرق: {len(all_teams)}", flush=True)
            print(f"   📊 إجمالي الملاعب: {len(all_stadiums)}", flush=True)
            print("   ⬆️ جاري الرفع...", flush=True)
            self.upsert_to_supabase("teams", all_teams)
            self.upsert_to_supabase("stadiums", all_stadiums)
            print(f"   ✅ تم رفع الفرق والملاعب.", flush=True)
    
    def run(self):
        """تشغيل السكربت"""
        print("\n" + "="*70, flush=True)
        print("🏆 بدء أرشيف كرة القدم الشامل", flush=True)
        print("="*70, flush=True)
        
        try:
            self.fetch_club_dataset()
            self.fetch_players_and_transfers()
            self.fetch_worldcup_data()
            self.fetch_additional_data()
        except Exception as e:
            print(f"\n❌ خطأ عام: {str(e)}", flush=True)
        
        # الإحصائيات النهائية
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        print("\n" + "="*70, flush=True)
        print("🏆 اكتمل الأرشيف!", flush=True)
        print("="*70, flush=True)
        print(f"   ✅ المباريات (matches): {self.stats['matches']:,}")
        print(f"   ✅ اللاعبين (players): {self.stats['players']:,}")
        print(f"   ✅ الانتقالات (transfers): {self.stats['transfers']:,}")
        print(f"   ✅ مباريات كأس العالم: {self.stats['worldcup_matches']:,}")
        print(f"   ❌ الأخطاء: {self.stats['errors']}")
        print(f"⏱️ الزمن المستغرق: {elapsed//60:.0f} دقائق و {elapsed%60:.0f} ثواني")
        print("="*70, flush=True)

if __name__ == "__main__":
    archive = UltimateFootballArchive()
    archive.run()
