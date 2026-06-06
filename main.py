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
            res = requests.post(f"{self.sup_url}/{table}", headers=self.sup_headers, json=data, timeout=10)
            if res.status_code in [200, 201]:
                logging.info(f"✅ [{source}] | {table} | تم رفع: {label}")
                self.cache.add(item_id)
                self.stats["added"] += 1
            elif res.status_code == 409:
                self.stats["skipped"] += 1
        except Exception as e:
            logging.error(f"❌ خطأ في {source}: {e}")

    # 1. API-Football: جلب شامل للفرق واللاعبين
    def task_football_api(self):
        headers = {"X-RapidAPI-Key": self.keys["football"], "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"}
        for league in [39, 140, 135]: # يمكنك إضافة المزيد
            res = requests.get(f"https://api-football-v1.p.rapidapi.com/v3/players", headers=headers, params={"league": league, "season": 2025, "page": 1})
            if res.status_code == 200:
                for p in res.json().get('response', []):
                    info = p['player']
                    self.push("API-Football", "players", info['id'], {
                        "id": info['id'], "name": info['name'], "age": info['age'], 
                        "nationality": info['nationality'], "image_url": info['photo']
                    }, info['name'])

    # 2. Sportmonks: نظام الصفحات الشامل (أضخم قاعدة بيانات)
    def task_sportmonks(self):
        for page in range(1, 100): # سيسحب حتى 100 صفحة
            url = f"https://api.sportmonks.com/v3/football/players?api_token={self.keys['monks']}&page={page}&include=team;country;position"
            res = requests.get(url, timeout=15)
            if res.status_code == 200:
                data = res.json().get('data', [])
                if not data: break
                for p in data:
                    self.push("Sportmonks", "players", p['id'], {
                        "id": p['id'], "name": p['display_name'], "age": p.get('age'),
                        "nationality": p.get('country', {}).get('name'),
                        "team_name": p.get('team', {}).get('name'),
                        "image_url": p.get('image_path'), "position": p.get('position', {}).get('name')
                    }, p['display_name'])
                logging.info(f"📄 تمت معالجة صفحة Sportmonks رقم {page}")
                time.sleep(0.5)

    # 3. iSports: جلب أخبار شامل
    def task_isports(self):
        res = requests.get("http://api.isportsapi.com/sport/football/news", params={"api_key": self.keys["isports"]})
        if res.status_code == 200:
            for n in res.json().get('data', []):
                self.push("iSports", "media_news", n['newsId'], {"id": n['newsId'], "title": n['title'], "content": n['content']}, n['title'][:20])

    def run(self):
        logging.info("🚀 بدء تشغيل محرك البيانات الضخمة (Big Data Engine)...")
        self.task_football_api()
        self.task_sportmonks()
        self.task_isports()
        
        logging.info("------------------------------------------")
        logging.info(f"📊 التقرير النهائي: تمت إضافة {self.stats['added']}، تخطي {self.stats['skipped']}")
        logging.info("🏆 انتهت المهمة بنجاح!")

if __name__ == "__main__":
    DSTWR_Master_Engine().run()
        
