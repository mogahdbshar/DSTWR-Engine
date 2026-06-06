import os
import requests
import hashlib
import time
import sys
import pandas as pd
from datetime import datetime

sys.stdout.reconfigure(line_buffering=True)

print("="*80, flush=True)
print("🏆 باور بانك كرة القدم - كل شيء من كل مكان", flush=True)
print("="*80, flush=True)

SUPABASE_URL = "https://nugskdozmxlgrnkfsxlg.supabase.co/rest/v1"
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")
SPORTMONKS_KEY = os.getenv("SPORTMONKS_KEY")
FOOTBALL_DATA_KEY = os.getenv("FOOTBALL_DATA_KEY")
ISPORTS_KEY = os.getenv("ISPORTS_KEY")

if not SUPABASE_KEY:
    print("❌ SUPABASE_KEY غير موجود!", flush=True)
    sys.exit(1)

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# ========== جميع الدوريات ==========
LEAGUES = [
    {"id": 2021, "code": "E0", "name": "Premier League", "country": "England"},
    {"id": 2014, "code": "SP1", "name": "La Liga", "country": "Spain"},
    {"id": 2019, "code": "I1", "name": "Serie A", "country": "Italy"},
    {"id": 2015, "code": "D1", "name": "Bundesliga", "country": "Germany"},
    {"id": 2016, "code": "F1", "name": "Ligue 1", "country": "France"},
    {"id": 2023, "code": "N1", "name": "Eredivisie", "country": "Netherlands"},
    {"id": 2024, "code": "P1", "name": "Primeira Liga", "country": "Portugal"},
    {"id": 2025, "code": "T1", "name": "Super Lig", "country": "Turkey"},
    {"id": 2049, "code": "BR1", "name": "Serie A Brazil", "country": "Brazil"},
    {"id": 2058, "code": "US1", "name": "MLS", "country": "USA"},
    {"id": 2066, "code": "SA1", "name": "Saudi Pro League", "country": "Saudi Arabia"},
    {"id": 2096, "code": "EG1", "name": "Egyptian League", "country": "Egypt"},
]

print(f"\n🏟️ معالجة {len(LEAGUES)} دوري...", flush=True)

# ========== 1. جلب المباريات ==========
print("\n📥 [1/6] جلب المباريات...", flush=True)

all_matches = []
all_teams = {}
team_counter = 100000

# جلب الفرق الموجودة
resp = requests.get(f"{SUPABASE_URL}/teams?select=id,name", headers=headers)
existing_teams = {team["name"]: team["id"] for team in resp.json()} if resp.status_code == 200 else {}

for league in LEAGUES:
    print(f"   📥 {league['name']}...", flush=True)
    for season_code in ["2425", "2324", "2223"]:
        year = f"20{season_code[:2]}-{season_code[2:]}"
        url = f"https://www.football-data.co.uk/mmz4281/{season_code}/{league['code']}.csv"
        try:
            df = pd.read_csv(url)
            for _, row in df.iterrows():
                try:
                    match_date = str(row['Date']).strip()
                    home_team = str(row['HomeTeam']).strip()
                    away_team = str(row['AwayTeam']).strip()
                    home_score = int(row['FTHG']) if pd.notna(row['FTHG']) else 0
                    away_score = int(row['FTAG']) if pd.notna(row['FTAG']) else 0
                    
                    # إضافة فرق جديدة
                    for team in [home_team, away_team]:
                        if team not in existing_teams and team not in all_teams:
                            team_counter += 1
                            all_teams[team] = {"id": team_counter, "name": team, "league_id": league["id"]}
                    
                    home_id = existing_teams.get(home_team, all_teams.get(home_team, {}).get("id"))
                    away_id = existing_teams.get(away_team, all_teams.get(away_team, {}).get("id"))
                    
                    if home_id and away_id:
                        match_id = hashlib.md5(f"{league['id']}_{year}_{home_team}_{away_team}".encode()).hexdigest()
                        all_matches.append({
                            "id": match_id, "league_id": league["id"], "season": year,
                            "home_team_id": home_id, "away_team_id": away_id,
                            "home_score": home_score, "away_score": away_score,
                            "match_date": match_date, "status": "finished"
                        })
                except:
                    pass
        except:
            pass
        time.sleep(0.2)
    time.sleep(0.5)

print(f"   ✅ {len(all_matches)} مباراة", flush=True)

# رفع الفرق الجديدة
print("\n📤 رفع الفرق الجديدة...", flush=True)
for team_name, team_data in all_teams.items():
    try:
        team_obj = {"id": team_data["id"], "name": team_name, "league_id": team_data["league_id"]}
        requests.post(f"{SUPABASE_URL}/teams", headers=headers, json=team_obj, timeout=10)
    except:
        pass
print(f"   ✅ {len(all_teams)} فريق جديد", flush=True)

# رفع المباريات
print("\n📤 رفع المباريات...", flush=True)
headers_upsert = headers.copy()
headers_upsert["Prefer"] = "resolution=merge-duplicates"
for i in range(0, len(all_matches), 100):
    batch = all_matches[i:i+100]
    try:
        requests.post(f"{SUPABASE_URL}/matches", headers=headers_upsert, json=batch, timeout=30)
        print(f"   ✅ دفعة {i//100 + 1}/{(len(all_matches)+99)//100}", flush=True)
    except:
        pass
    time.sleep(0.1)

# ========== 2. جلب اللاعبين والمدربين من API Football ==========
print("\n👥 [2/6] جلب اللاعبين والمدربين...", flush=True)

if API_FOOTBALL_KEY:
    api_headers = {"X-RapidAPI-Key": API_FOOTBALL_KEY, "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"}
    all_players = []
    all_coaches = []
    
    for team_id in list(set([t["league_id"] for t in all_teams.values()] + [team["id"] for team in existing_teams.values()]))[:30]:
        url = f"https://api-football-v1.p.rapidapi.com/v3/players"
        params = {"team": team_id, "season": 2024}
        try:
            resp = requests.get(url, headers=api_headers, params=params, timeout=15)
            if resp.status_code == 200:
                for p in resp.json().get("response", []):
                    player = p.get("player", {})
                    if player.get("id"):
                        all_players.append({
                            "id": player["id"], "name": player["name"],
                            "age": player.get("age"), "nationality": player.get("nationality"),
                            "photo_url": player.get("photo"), "team_id": team_id
                        })
        except:
            pass
        time.sleep(0.5)
    
    if all_players:
        for i in range(0, len(all_players), 100):
            requests.post(f"{SUPABASE_URL}/players", headers=headers_upsert, json=all_players[i:i+100])
        print(f"   ✅ {len(all_players)} لاعب", flush=True)

# ========== 3. جلب شعارات الفرق ==========
print("\n🖼️ [3/6] جلب شعارات الفرق...", flush=True)

resp = requests.get(f"{SUPABASE_URL}/teams?select=id,name", headers=headers)
teams_list = resp.json() if resp.status_code == 200 else []
for team in teams_list[:100]:
    team_name = team["name"].replace(" ", "_")
    logo_url = f"https://logo.clearbit.com/{team_name}.com"
    try:
        requests.patch(f"{SUPABASE_URL}/teams?id=eq.{team['id']}", headers=headers, json={"logo_url": logo_url})
    except:
        pass
print(f"   ✅ شعارات لـ {len(teams_list[:100])} فريق", flush=True)

# ========== 4. جلب الترتيب من Football Data ==========
print("\n📊 [4/6] جلب الترتيب...", flush=True)
if FOOTBALL_DATA_KEY:
    for league in LEAGUES[:5]:
        code_map = {"Premier League": "PL", "La Liga": "PD", "Serie A": "SA", "Bundesliga": "BL1", "Ligue 1": "FL1"}
        code = code_map.get(league["name"])
        if code:
            url = f"https://api.football-data.org/v4/competitions/{code}/standings"
            headers_fd = {"X-Auth-Token": FOOTBALL_DATA_KEY}
            try:
                resp = requests.get(url, headers=headers_fd, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    for standing in data.get("standings", []):
                        for item in standing.get("table", []):
                            team = item.get("team", {})
                            standings_data = {
                                "id": f"{league['id']}_{team.get('id')}_{datetime.now().year}",
                                "league_id": league["id"], "team_id": team.get("id"),
                                "position": item.get("position"), "points": item.get("points")
                            }
                            requests.post(f"{SUPABASE_URL}/league_standings", headers=headers, json=standings_data)
                    print(f"   ✅ {league['name']}", flush=True)
            except:
                pass
            time.sleep(12)
else:
    print("   ⚠️ مفتاح Football Data غير موجود", flush=True)

# ========== 5. جلب الأخبار ==========
print("\n📰 [5/6] جلب الأخبار...", flush=True)
if ISPORTS_KEY:
    try:
        url = f"http://api.isportsapi.com/sport/football/news?api_key={ISPORTS_KEY}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            for news in resp.json().get("data", [])[:50]:
                if news.get("newsId"):
                    news_data = {
                        "id": news["newsId"], "title": news["title"],
                        "content": news.get("content", "")[:500], "source": news.get("source"),
                        "image_url": news.get("imageUrl"), "published_at": news.get("pubTime")
                    }
                    requests.post(f"{SUPABASE_URL}/media_news", headers=headers, json=news_data)
            print(f"   ✅ أخبار", flush=True)
    except:
        pass

# ========== 6. إحصائيات ==========
print("\n📊 [6/6] جمع الإحصائيات...", flush=True)
resp = requests.get(f"{SUPABASE_URL}/teams?select=id", headers=headers)
teams_total = len(resp.json()) if resp.status_code == 200 else 0
resp = requests.get(f"{SUPABASE_URL}/matches?select=id", headers=headers)
matches_total = len(resp.json()) if resp.status_code == 200 else 0
resp = requests.get(f"{SUPABASE_URL}/players?select=id", headers=headers)
players_total = len(resp.json()) if resp.status_code == 200 else 0

# ========== النتيجة ==========
print("\n" + "="*80, flush=True)
print("🏆 اكتمل الباور بانك!", flush=True)
print("="*80, flush=True)
print(f"   ✅ الفرق: {teams_total}")
print(f"   ✅ المباريات: {matches_total}")
print(f"   ✅ اللاعبين: {players_total}")
print(f"   ✅ الدوريات: {len(LEAGUES)}")
print("="*80, flush=True)
