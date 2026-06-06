import os
import requests
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')

class DSTWR_Master_Engine:
    def __init__(self):
        self.keys = {
            "football": os.getenv("API_FOOTBALL_KEY"),
            "data": os.getenv("FOOTBALL_DATA_KEY"),
            "monks": os.getenv("SPORTMONKS_KEY"),
            "isports": os.getenv("ISPORTS_KEY"),
            "supabase": os.getenv("SUPABASE_KEY")
        }
        self.sup_url = "https://nugskdozmxlgrnkfsxlg.supabase.co/rest/v1"
        self.sup_headers = {
            "apikey": self.keys["supabase"],
            "Authorization": f"Bearer {self.keys['supabase']}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates"
        }
        self.stats = {"added": 0, "skipped": 0}
        self.cache = set()

    def push(self, source, table, item_id, data, label):
        if item_id in self.cache: return
        try:
            res = requests.post(f"{self.sup_url}/{table}", headers=self.sup_headers, json=data, timeout=5)
            if res.status_code in [200, 201]:
                logging.info(f"✅ [{source}] | {table} | تم رفع: {label}")
                self.cache.add(item_id)
                self.stats["added"] += 1
            elif res.status_code == 409:
                self.stats["skipped"] += 1
        except Exception as e:
            logging.error(f"❌ خطأ في {source}: {e}")

    # 1. API-Football (المصدر الرئيسي)
    def task_football_api(self):
        headers = {"X-RapidAPI-Key": self.keys["football"], "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"}
        res = requests.get("https://api-football-v1.p.rapidapi.com/v3/teams", headers=headers, params={"league": 39, "season": 2025})
        if res.status_code == 200:
            for t in res.json().get('response', []):
                self.push("API-Football", "teams", t['team']['id'], {"id": t['team']['id'], "name": t['team']['name']}, t['team']['name'])

    # 2. Football-Data (الترتيب)
    def task_football_data(self):
        headers = {"X-Auth-Token": self.keys["data"]}
        res = requests.get("https://api.football-data.org/v4/competitions/PL/standings", headers=headers)
        if res.status_code == 200:
            for s in res.json().get('standings', [])[0].get('table', []):
                team = s['team']
                self.push("Football-Data", "league_standings", team['id'], {"team_id": team['id'], "name": team['name'], "points": s['points']}, team['name'])

    # 3. Sportmonks (بيانات عميقة)
    def task_sportmonks(self):
        res = requests.get(f"https://api.sportmonks.com/v3/football/players?api_token={self.keys['monks']}")
        if res.status_code == 200:
            for p in res.json().get('data', []):
                self.push("Sportmonks", "players", p['id'], {"id": p['id'], "name": p['display_name']}, p['display_name'])

    # 4. iSports (أخبار)
    def task_isports(self):
        res = requests.get("http://api.isportsapi.com/sport/football/news", params={"api_key": self.keys["isports"]})
        if res.status_code == 200:
            for n in res.json().get('data', []):
                self.push("iSports", "media_news", n['newsId'], {"id": n['newsId'], "title": n['title']}, n['title'][:15])

    def run(self):
        logging.info("🚀 بدء تشغيل المحرك الموحد بكامل المصادر...")
        self.task_football_api()
        self.task_football_data()
        self.task_sportmonks()
        self.task_isports()
        
        logging.info("------------------------------------------")
        logging.info(f"📊 تقرير الأداء النهائي: تمت إضافة {self.stats['added']}، تخطي {self.stats['skipped']}")
        logging.info("🏆 اكتملت المهمة بنجاح!")

if __name__ == "__main__":
    DSTWR_Master_Engine().run()
