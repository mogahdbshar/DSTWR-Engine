import os
import requests
import logging
import time
from datetime import datetime

# إعداد الـ Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')

class DSTWR_Ultimate_Engine:
    def __init__(self):
        # 1. التحقق من وجود جميع المفاتيح المطلوبة
        required_keys = ["SUPABASE_KEY", "API_FOOTBALL_KEY", "SPORTMONKS_KEY", "ISPORTS_KEY", "FOOTBALL_DATA_KEY"]
        missing = [key for key in required_keys if not os.getenv(key)]
        if missing:
            logging.error(f"🚨 مفاتيح مفقودة في GitHub Secrets: {missing}")
            exit(1)

        self.base_url = "https://nugskdozmxlgrnkfsxlg.supabase.co/rest/v1"
        self.headers = {
            "apikey": os.getenv("SUPABASE_KEY"),
            "Authorization": f"Bearer {os.getenv('SUPABASE_KEY')}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates"
        }
        
        self.api_football_key = os.getenv("API_FOOTBALL_KEY")
        self.isports_key = os.getenv("ISPORTS_KEY")
        
        # الذاكرة المؤقتة للتخطي الذكي + إحصائيات التقرير
        self.cache = {} 
        self.stats = {"added": 0, "skipped": 0}
        
        self.leagues = [
            {"af_id": 39, "name": "Premier League"}, {"af_id": 140, "name": "La Liga"},
            {"af_id": 2, "name": "Champions League"}, {"af_id": 135, "name": "Serie A"},
            {"af_id": 78, "name": "Bundesliga"}, {"af_id": 61, "name": "Ligue 1"},
            {"af_id": 1, "name": "World Cup"}
        ]

    def push(self, table, item_id, data, label):
        """رفع ذكي: يرفع فقط إذا لم يكن الـ ID موجوداً في الذاكرة"""
        if table not in self.cache: self.cache[table] = set()
        if item_id in self.cache[table]: return 
        
        try:
            res = requests.post(f"{self.base_url}/{table}", headers=self.headers, json=data, timeout=5)
            if res.status_code in [200, 201]:
                logging.info(f"✅ [{table.upper()}] تم رفع: {label}")
                self.cache[table].add(item_id)
                self.stats["added"] += 1
            elif res.status_code == 409:
                self.cache[table].add(item_id)
                self.stats["skipped"] += 1
        except Exception as e:
            logging.error(f"⚠️ خطأ في {table}: {e}")

    def fetch_stadiums_and_coaches(self):
        logging.info("⚡ [خطوة 1] مزامنة الملاعب والمدربين...")
        headers = {"X-RapidAPI-Key": self.api_football_key, "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"}
        for lg in self.leagues:
            res = requests.get("https://api-football-v1.p.rapidapi.com/v3/teams", headers=headers, params={"league": lg["af_id"], "season": 2025})
            if res.status_code == 200:
                for t in res.json().get('response', []):
                    v = t.get('venue', {})
                    if v.get('id'): self.push("stadiums", v['id'], {"id": v['id'], "name": v['name'], "city": v['city']}, v['name'])
                    c = t.get('coach', {})
                    if c.get('id'): self.push("coaches", c['id'], {"id": c['id'], "name": c['name']}, c['name'])
            time.sleep(0.5)

    def fetch_top_stats(self):
        logging.info("⚡ [خطوة 2] مزامنة الهدافين وصناع اللعب...")
        headers = {"X-RapidAPI-Key": self.api_football_key, "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"}
        for lg in self.leagues:
            for stat in ["topscorers", "topassists"]:
                res = requests.get(f"https://api-football-v1.p.rapidapi.com/v3/players/{stat}", headers=headers, params={"league": lg["af_id"], "season": 2025})
                if res.status_code == 200:
                    for p in res.json().get('response', []):
                        pid = p.get('player', {}).get('id')
                        if pid: self.push(stat, pid, {"player_id": pid, "player_name": p['player']['name']}, p['player']['name'])
            time.sleep(0.5)

    def fetch_news(self):
        logging.info("⚡ [خطوة 3] مزامنة الأخبار الحية...")
        res = requests.get("http://api.isportsapi.com/sport/football/news", params={"api_key": self.isports_key})
        if res.status_code == 200:
            for n in res.json().get('data', []):
                self.push("media_news", n['newsId'], {"id": n['newsId'], "title": n['title']}, n['title'][:20])

    def fetch_matches(self):
        logging.info("⚡ [خطوة 4] مزامنة مباريات اليوم...")
        today = datetime.now().strftime('%Y-%m-%d')
        headers = {"X-RapidAPI-Key": self.api_football_key, "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"}
        for lg in self.leagues:
            res = requests.get("https://api-football-v1.p.rapidapi.com/v3/fixtures", headers=headers, params={"league": lg["af_id"], "date": today})
            if res.status_code == 200:
                for m in res.json().get('response', []):
                    mid = m['fixture']['id']
                    self.push("matches", mid, {"id": mid, "league_id": lg["af_id"], "status": m['fixture']['status']['short']}, str(mid))
            time.sleep(0.5)

    def start(self):
        logging.info("🚀 بدء تشغيل المحرك الشامل المطور...")
        self.fetch_stadiums_and_coaches()
        self.fetch_top_stats()
        self.fetch_news()
        self.fetch_matches()
        
        logging.info("------------------------------------------")
        logging.info(f"📊 تقرير المزامنة النهائي:")
        logging.info(f"✅ تم إضافة: {self.stats['added']} عنصر جديد.")
        logging.info(f"⏭️ تم تخطي: {self.stats['skipped']} عنصر مكرر.")
        logging.info("🏆 انتهت المهمة بنجاح وأمان!")

if __name__ == "__main__":
    DSTWR_Ultimate_Engine().start()
