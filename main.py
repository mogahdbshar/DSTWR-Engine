import os
import requests
import hashlib
import json
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

# =========================
# 🧠 أدوات النظام
# =========================

def log(msg):
    print(f"🔹 {msg}", flush=True)

def make_id(*args):
    raw = "_".join([str(a).strip().lower() for a in args if a])
    return hashlib.sha256(raw.encode()).hexdigest()

def safe_json(url):
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        try:
            return r.json()
        except:
            return json.loads(r.text)
    except Exception as e:
        log(f"فشل المصدر: {str(e)[:80]}")
        return None

def push(table, data):
    if not data:
        return 0

    success = 0

    for i in range(0, len(data), 300):
        batch = data[i:i+300]

        try:
            r = requests.post(
                f"{SUPABASE_URL}/{table}",
                headers=HEADERS,
                json=batch,
                timeout=40
            )

            if r.status_code in [200, 201]:
                success += len(batch)
                log(f"{table}: رفع {len(batch)} سجل")
            else:
                log(f"{table}: خطأ {r.status_code}")

        except Exception as e:
            log(f"خطأ رفع: {str(e)[:60]}")

        time.sleep(0.1)

    return success


# =========================
# 🏆 المحرك العالمي
# =========================

class GlobalFootballEngine:

    def run(self):
        print("\n==============================")
        print("🌍 تشغيل قاعدة بيانات كرة القدم العالمية")
        print("==============================\n")

        teams = self.load_teams()
        players = self.load_players()
        matches = self.load_matches()
        transfers = self.load_transfers()

        print("\n==============================")
        print("🏁 انتهى بناء القاعدة العالمية")
        print("==============================")

        log(f"الفرق: {len(teams)}")
        log(f"اللاعبين: {len(players)}")
        log(f"المباريات: {len(matches)}")
        log(f"الانتقالات: {len(transfers)}")

    # =========================
    # الفرق (أوروبا + دوريات)
    # =========================
    def load_teams(self):
        log("تحميل الفرق العالمية...")

        leagues = [
            "en.1", "es.1", "de.1", "it.1", "fr.1"
        ]

        all_teams = []

        for lg in leagues:
            url = f"https://raw.githubusercontent.com/openfootball/football.json/master/data/2023/{lg}.json"
            data = safe_json(url)

            if not data:
                continue

            league_id = make_id(lg)

            for t in data.get("teams", []):
                all_teams.append({
                    "id": make_id(t.get("name"), lg),
                    "name": t.get("name"),
                    "code": t.get("code"),
                    "league_id": league_id
                })

        push("teams", all_teams)
        return all_teams

    # =========================
    # اللاعبين (عالمي)
    # =========================
    def load_players(self):
        log("تحميل اللاعبين العالميين...")

        url = "https://www.thesportsdb.com/api/v1/json/3/searchplayers.php?p="
        data = safe_json(url)

        players = []

        if data and "player" in data:
            for p in data["player"]:
                players.append({
                    "id": make_id(p.get("idPlayer")),
                    "name": p.get("strPlayer"),
                    "team": p.get("strTeam"),
                    "position": p.get("strPosition"),
                    "nationality": p.get("strNationality")
                })

        push("players", players)
        return players

    # =========================
    # المباريات (أوروبا كاملة)
    # =========================
    def load_matches(self):
        log("تحميل المباريات العالمية...")

        leagues = ["en.1", "es.1", "de.1", "it.1", "fr.1"]

        matches = []

        for lg in leagues:
            url = f"https://raw.githubusercontent.com/openfootball/football.json/master/data/2023/{lg}.json"
            data = safe_json(url)

            if not data:
                continue

            for m in data.get("matches", []):
                matches.append({
                    "id": make_id(m.get("date"), m.get("team1"), m.get("team2")),
                    "league": lg,
                    "date": m.get("date"),
                    "home": m.get("team1"),
                    "away": m.get("team2"),
                    "score": f"{m.get('score1')}-{m.get('score2')}"
                })

                if len(matches) % 1000 == 0:
                    log(f"تم تجهيز {len(matches)} مباراة")

        push("matches", matches)
        return matches

    # =========================
    # الانتقالات
    # =========================
    def load_transfers(self):
        log("تحميل الانتقالات العالمية...")

        url = "https://raw.githubusercontent.com/detrin/Transfermarkt-Data/main/data/transfers.csv"

        try:
            r = requests.get(url, timeout=40)
            lines = r.text.split("\n")

            transfers = []

            for line in lines[1:20000]:  # حماية من الضغط
                parts = line.split(",")

                if len(parts) < 5:
                    continue

                transfers.append({
                    "id": make_id(line),
                    "player": parts[0],
                    "from_team": parts[1],
                    "to_team": parts[2],
                    "fee": parts[3]
                })

            push("transfers", transfers)
            return transfers

        except Exception as e:
            log(f"فشل الانتقالات: {str(e)[:80]}")
            return []


# =========================
# 🚀 تشغيل يدوي فقط
# =========================

if __name__ == "__main__":
    GlobalFootballEngine().run()
