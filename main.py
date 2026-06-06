import os
import requests
import hashlib
import csv
import io
import time
from datetime import datetime

SUPABASE_URL = "https://nugskdozmxlgrnkfsxlg.supabase.co/rest/v1"
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates"
}

# ======================
# ID ثابت عالمي
# ======================
def make_id(*args):
    raw = "_".join([str(a).strip().lower() for a in args if a])
    return hashlib.sha256(raw.encode()).hexdigest()

# ======================
# رفع قوي + Retry
# ======================
def push(table, data, retries=3):
    if not data:
        return 0

    success = 0

    for i in range(0, len(data), 300):
        batch = data[i:i+300]

        for attempt in range(retries):
            try:
                r = requests.post(
                    f"{SUPABASE_URL}/{table}",
                    headers=HEADERS,
                    json=batch,
                    timeout=40
                )

                if r.status_code in [200, 201]:
                    success += len(batch)
                    break
                else:
                    print(f"⚠️ {table} failed {r.status_code}")

            except Exception as e:
                print("❌ retry error:", str(e)[:80])
                time.sleep(1)

        time.sleep(0.1)

    print(f"✅ {table} inserted: {success}")
    return success


# ======================
# ENGINE
# ======================
class FootballDB:

    def load_leagues_teams(self):
        url = "https://raw.githubusercontent.com/openfootball/football.json/master/data/2023/en.1.json"
        data = requests.get(url).json()

        league_id = make_id("premier league", "england")

        leagues = [{
            "id": league_id,
            "name": "Premier League",
            "country": "England"
        }]

        teams = []

        for t in data.get("teams", []):
            teams.append({
                "id": make_id(t.get("name"), "england"),
                "name": t.get("name"),
                "code": t.get("code"),
                "league_id": league_id
            })

        push("leagues", leagues)
        push("teams", teams)

        return teams

    def load_players(self):
        url = "https://www.thesportsdb.com/api/v1/json/3/searchplayers.php?t=Arsenal"
        data = requests.get(url).json()

        players = []

        for p in data.get("player", []):
            players.append({
                "id": make_id(p.get("idPlayer")),
                "name": p.get("strPlayer"),
                "team": p.get("strTeam"),
                "position": p.get("strPosition")
            })

        push("players", players)

    def load_matches(self):
        url = "https://raw.githubusercontent.com/openfootball/football.json/master/data/2023/en.1.json"
        data = requests.get(url).json()

        matches = []

        league_id = make_id("premier league", "england")

        for m in data.get("matches", []):
            matches.append({
                "id": make_id(m.get("date"), m.get("team1"), m.get("team2")),
                "league_id": league_id,
                "date": m.get("date"),
                "home": m.get("team1"),
                "away": m.get("team2"),
                "score": f"{m.get('score1')}-{m.get('score2')}"
            })

            if len(matches) >= 800:
                push("matches", matches)
                matches = []

        push("matches", matches)

    def run(self):
        print("🚀 STARTING FAST FOOTBALL DB")

        teams = self.load_leagues_teams()
        self.load_players()
        self.load_matches()

        print("🏁 DONE")


if __name__ == "__main__":
    FootballDB().run()
