import os
import requests
import hashlib
import time
import sys
import pandas as pd
from datetime import datetime

sys.stdout.reconfigure(line_buffering=True)

print("="*80, flush=True)
print("🏆 باور بانك كرة القدم - النسخة النهائية الكاملة (كل شيء)", flush=True)
print("="*80, flush=True)

SUPABASE_URL = "https://nugskdozmxlgrnkfsxlg.supabase.co/rest/v1"
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")
ISPORTS_KEY = os.getenv("ISPORTS_KEY")

if not SUPABASE_KEY:
    print("❌ SUPABASE_KEY غير موجود!", flush=True)
    sys.exit(1)

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# إحصائيات
stats = {
    "teams_added": 0, "matches_added": 0, "players_added": 0,
    "logos_added": 0, "news_added": 0, "errors": 0
}

# الدوريات
LEAGUES = [
    {"id": 2021, "code": "E0", "name": "Premier League"},
    {"id": 2014, "code": "SP1", "name": "La Liga"},
    {"id": 2019, "code": "I1", "name": "Serie A"},
    {"id": 2015, "code": "D1", "name": "Bundesliga"},
    {"id": 2016, "code": "F1", "name": "Ligue 1"},
    {"id": 2023, "code": "N1", "name": "Eredivisie"},
    {"id": 2024, "code": "P1", "name": "Primeira Liga"},
    {"id": 2025, "code": "T1", "name": "Super Lig"},
    {"id": 2049, "code": "BR1", "name": "Brasileirão"},
    {"id": 2058, "code": "US1", "name": "MLS"},
    {"id": 2066, "code": "SA1", "name": "Saudi Pro League"},
]

# ========== 1. الفرق الموجودة ==========
print("\n🔍 [1/6] جلب الفرق الموجودة...", flush=True)
resp = requests.get(f"{SUPABASE_URL}/teams?select=id,name", headers=headers)
existing_teams = {}
if resp.status_code == 200:
    for team in resp.json():
        existing_teams[team["name"]] = team["id"]
print(f"   ✅ {len(existing_teams)} فريق موجود", flush=True)

# ========== 2. جلب المباريات والفرق الجديدة ==========
print("\n📥 [2/6] جلب المباريات...", flush=True)

all_matches = []
new_teams = {}
team_counter = max(existing_teams.values()) if existing_teams else 100000

for league in LEAGUES:
    print(f"   📥 {league['name']}...", flush=True)
    for season_code in ["2425", "2324", "2223"]:
        year = f"20{season_code[:2]}-{season_code[2:]}"
        url = f"https://www.football-data.co.uk/mmz4281/{season_code}/{league['code']}.csv"
        try:
            df = pd.read_csv(url)
            for _, row in df.iterrows():
                try:
                    home_team = str(row['HomeTeam']).strip()
                    away_team = str(row['AwayTeam']).strip()
                    home_score = int(row['FTHG']) if pd.notna(row['FTHG']) else 0
                    away_score = int(row['FTAG']) if pd.notna(row['FTAG']) else 0
                    match_date = str(row['Date']).strip()
                    
                    for team in [home_team, away_team]:
                        if team not in existing_teams and team not in new_teams:
                            team_counter += 1
                            new_teams[team] = team_counter
                            print(f"      🆕 فريق جديد: {team} (ID: {team_counter})", flush=True)
                            stats["teams_added"] += 1
                    
                    home_id = existing_teams.get(home_team) or new_teams.get(home_team)
                    away_id = existing_teams.get(away_team) or new_teams.get(away_team)
                    
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
        time.sleep(0.1)

print(f"   ✅ {len(all_matches)} مباراة", flush=True)

# ========== 3. رفع الفرق الجديدة ==========
print("\n📤 [3/6] رفع الفرق الجديدة...", flush=True)
for team_name, team_id in new_teams.items():
    try:
        team_obj = {"id": team_id, "name": team_name}
        requests.post(f"{SUPABASE_URL}/teams", headers=headers, json=team_obj, timeout=10)
    except:
        stats["errors"] += 1
print(f"   ✅ {len(new_teams)} فريق جديد", flush=True)

# ========== 4. رفع المباريات ==========
print("\n📤 [4/6] رفع المباريات...", flush=True)
headers_upsert = headers.copy()
headers_upsert["Prefer"] = "resolution=merge-duplicates"
for i in range(0, len(all_matches), 100):
    batch = all_matches[i:i+100]
    try:
        requests.post(f"{SUPABASE_URL}/matches", headers=headers_upsert, json=batch, timeout=30)
        stats["matches_added"] += len(batch)
        if i % 500 == 0:
            print(f"   ✅ دفعة {i//100 + 1}/{(len(all_matches)+99)//100}", flush=True)
    except:
        stats["errors"] += len(batch)
    time.sleep(0.05)

# ========== 5. جلب اللاعبين ==========
print("\n👥 [5/6] جلب اللاعبين...", flush=True)

if API_FOOTBALL_KEY:
    api_headers = {"X-RapidAPI-Key": API_FOOTBALL_KEY, "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"}
    all_players = []
    
    team_ids = list(existing_teams.values()) + list(new_teams.values())
    team_ids = list(set(team_ids))[:50]
    
    print(f"   📋 جلب لاعبين لـ {len(team_ids)} فريق", flush=True)
    
    for team_id in team_ids:
        url = "https://api-football-v1.p.rapidapi.com/v3/players"
        params = {"team": team_id, "season": 2024}
        try:
            resp = requests.get(url, headers=api_headers, params=params, timeout=15)
            if resp.status_code == 200:
                data = resp.json().get("response", [])
                for p in data:
                    player = p.get("player", {})
                    if player.get("id"):
                        all_players.append({
                            "id": player["id"], "name": player.get("name"),
                            "age": player.get("age"), "nationality": player.get("nationality"),
                            "photo_url": player.get("photo"), "team_id": team_id
                        })
                print(f"   ✅ فريق {team_id}: {len(data)} لاعب", flush=True)
        except:
            pass
        time.sleep(0.3)
    
    if all_players:
        for i in range(0, len(all_players), 100):
            try:
                requests.post(f"{SUPABASE_URL}/players", headers=headers_upsert, json=all_players[i:i+100])
                stats["players_added"] += len(all_players[i:i+100])
            except:
                pass
        print(f"   ✅ تم رفع {stats['players_added']} لاعب", flush=True)

# ========== 6. جلب الشعارات ==========
print("\n🖼️ [6/6] جلب شعارات الفرق...", flush=True)

# جلب جميع الفرق
resp = requests.get(f"{SUPABASE_URL}/teams?select=id,name", headers=headers)
teams_list = resp.json() if resp.status_code == 200 else []
print(f"   📋 تحديث شعارات {len(teams_list)} فريق", flush=True)

for team in teams_list[:150]:
    team_id = team["id"]
    team_name = team["name"].replace(" ", "_").replace("&", "").replace("'", "").lower()
    logo_url = None
    
    # TheSportsDB
    try:
        url = f"https://www.thesportsdb.com/api/v1/json/3/searchteams.php?t={team_name}"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200 and resp.json().get("teams"):
            logo_url = resp.json()["teams"][0].get("strTeamBadge")
    except:
        pass
    
    # Wikipedia بديل
    if not logo_url:
        try:
            url = f"https://en.wikipedia.org/w/api.php?action=query&titles={team_name}&prop=pageimages&format=json&pithumbsize=200"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                pages = resp.json().get("query", {}).get("pages", {})
                for page in pages.values():
                    if page.get("thumbnail", {}).get("source"):
                        logo_url = page["thumbnail"]["source"]
                        break
        except:
            pass
    
    if logo_url:
        try:
            requests.patch(f"{SUPABASE_URL}/teams?id=eq.{team_id}", headers=headers, json={"logo_url": logo_url}, timeout=10)
            stats["logos_added"] += 1
            print(f"   ✅ {team['name'][:30]}...", flush=True)
        except:
            pass
    time.sleep(0.1)

print(f"   ✅ تم تحديث {stats['logos_added']} شعار", flush=True)

# ========== 7. جلب الأخبار ==========
if ISPORTS_KEY:
    print("\n📰 [7/6] جلب الأخبار...", flush=True)
    try:
        url = f"http://api.isportsapi.com/sport/football/news?api_key={ISPORTS_KEY}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            for news in resp.json().get("data", [])[:50]:
                if news.get("newsId"):
                    news_data = {
                        "id": news["newsId"], "title": news["title"],
                        "content": news.get("content", "")[:500],
                        "source": news.get("source"), "image_url": news.get("imageUrl"),
                        "published_at": news.get("pubTime")
                    }
                    try:
                        check = requests.get(f"{SUPABASE_URL}/media_news?id=eq.{news_data['id']}", headers=headers)
                        if check.status_code != 200 or not check.json():
                            requests.post(f"{SUPABASE_URL}/media_news", headers=headers, json=news_data)
                            stats["news_added"] += 1
                    except:
                        pass
            print(f"   ✅ تم رفع {stats['news_added']} خبر", flush=True)
    except:
        print("   ⚠️ فشل جلب الأخبار", flush=True)

# ========== النتيجة النهائية ==========
print("\n" + "="*80, flush=True)
print("🏆 اكتمل الباور بانك!", flush=True)
print("="*80, flush=True)
print(f"   ✅ الفرق الجديدة: {stats['teams_added']}")
print(f"   ✅ المباريات الجديدة: {stats['matches_added']}")
print(f"   ✅ اللاعبين الجدد: {stats['players_added']}")
print(f"   ✅ الشعارات الجديدة: {stats['logos_added']}")
print(f"   ✅ الأخبار الجديدة: {stats['news_added']}")
print(f"   ❌ الأخطاء: {stats['errors']}")
print("="*80, flush=True)

# إحصائيات نهائية
resp = requests.get(f"{SUPABASE_URL}/teams?select=id", headers=headers)
teams_total = len(resp.json()) if resp.status_code == 200 else 0
resp = requests.get(f"{SUPABASE_URL}/matches?select=id", headers=headers)
matches_total = len(resp.json()) if resp.status_code == 200 else 0
resp = requests.get(f"{SUPABASE_URL}/players?select=id", headers=headers)
players_total = len(resp.json()) if resp.status_code == 200 else 0
print(f"\n📊 إجمالي في Supabase:")
print(f"   🏟️ الفرق: {teams_total}")
print(f"   ⚽ المباريات: {matches_total}")
print(f"   👥 اللاعبين: {players_total}")
print("="*80, flush=True)
