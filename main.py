import os
import requests
import hashlib
import json
import time
from datetime import datetime

# =========================
# ⚙️ إعدادات Supabase
# =========================
SUPABASE_URL = "https://nugskdozmxlgrnkfsxlg.supabase.co/rest/v1"
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates"
}

# =========================
# 🧠 أدوات مساعدة
# =========================
def make_id(*args):
    raw = "_".join([str(a).strip().lower() for a in args if a])
    return hashlib.sha256(raw.encode()).hexdigest()


def log(msg):
    print(f"🔹 {msg}", flush=True)


def safe_get(url):
    """يحمي من JSONDecodeError"""
    try:
        r = requests.get(url, timeout=30)
        if r.status_code != 200:
            log(f"فشل المصدر: HTTP {r.status_code}")
            return None

        try:
            return r.json()
        except:
            return json.loads(r.text)

    except Exception as e:
        log(f"خطأ تحميل: {str(e)[:80]}")
        return None


def push(table, data):
    if not data:
        return 0

    success = 0

    for i in range(0, len(data), 200):
        batch = data[i:i+200]

        try:
            r = requests.post(
                f"{SUPABASE_URL}/{table}",
                headers=HEADERS,
                json=batch,
                timeout=30
            )

            if r.status_code in [200, 201]:
                success += len(batch)
                log(f"تم رفع {len(batch)} سجل إلى {table}")
            else:
                log(f"خطأ رفع {table}: {r.status_code}")

        except Exception as e:
            log(f"استثناء رفع: {str(e)[:60]}")

        time.sleep(0.1)

    return success


# =========================
# ⚽ المحرك العالمي
# =========================
class FootballEnginePRO:

    def run(self):
        print("\n==============================")
        print("🌍 تشغيل قاعدة بيانات كرة القدم العالمية PRO")
        print("==============================\n")

        teams = self.load_teams()
        players = self.load_players()
        matches = self.load_matches()

        print("\n==============================")
        print("🏁 انتهى بناء القاعدة")
        print("==============================")

        log(f"الفرق: {len(teams)}")
        log(f"اللاعبين: {len(players)}")
        log(f"المباريات: {len(matches)}")

    # =========================
    # 🏟️ الفرق (مصدر ثابت شغال)
    # =========================
    def load_teams(self):
        log("تحميل الفرق...")

        url = "https://raw.githubusercontent.com/openfootball/football.json/master/data/2024/en.1.json"
        data = safe_get(url)

        if not data:
            return []

        league_id = make_id("premier league", "england")
        teams = []

        for t in data.get("teams", []):
            teams.append({
                "id": make_id(t.get("name"), "england"),
                "name": t.get("name"),
                "code": t.get("code"),
                "league_id": league_id
            })

        push("teams", teams)
        return teams

    # =========================
    # 👤 اللاعبين (API ثابت)
    # =========================
    def load_players(self):
        log("تحميل اللاعبين...")

        url = "https://www.thesportsdb.com/api/v1/json/3/searchplayers.php?t=Arsenal"
        data = safe_get(url)

        if not data:
            return []

        players = []

        for p in data.get("player", []):
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
    # ⚽ المباريات (مصدر صحيح)
    # =========================
    def load_matches(self):
        log("تحميل المباريات...")

        url = "https://raw.githubusercontent.com/openfootball/football.json/master/data/2024/en.1.json"
        data = safe_get(url)

        if not data:
            return []

        matches = []

        for m in data.get("matches", []):
            matches.append({
                "id": make_id(m.get("date"), m.get("team1"), m.get("team2")),
                "date": m.get("date"),
                "home": m.get("team1"),
                "away": m.get("team2"),
                "score": f"{m.get('score1')}-{m.get('score2')}"
            })

        push("matches", matches)
        return matches


# =========================
# 🚀 تشغيل يدوي فقط (GitHub Actions)
# =========================
if __name__ == "__main__":
    FootballEnginePRO().run()
