import os
import requests
import logging
import time

# إعداد الـ Logs لمراقبة العمليات لحظة بلحظة
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')

class DSTWR_Master_Engine:
    def __init__(self):
        self.keys = {
            "football": os.getenv("API_FOOTBALL_KEY"),
            "monks": os.getenv("SPORTMONKS_KEY"),
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

    def push(self, table, item_id, data, label):
        try:
            res = requests.post(f"{self.sup_url}/{table}", headers=self.sup_headers, json=data, timeout=10)
            if res.status_code in [200, 201]:
                logging.info(f"✅ تم رفع: {label}")
                self.stats["added"] += 1
            elif res.status_code == 409:
                self.stats["skipped"] += 1
        except Exception as e:
            logging.error(f"❌ خطأ في الرفع: {e}")

    def task_sportmonks(self):
        logging.info("⚽ بدء جلب البيانات (تتبع حي)...")
        # نظام الصفحات لجلب أضخم كمية ممكنة
        for page in range(1, 11): 
            url = f"https://api.sportmonks.com/v3/football/players?api_token={self.keys['monks']}&page={page}&include=team;country;position"
            try:
                with requests.Session() as s:
                    res = s.get(url, timeout=15)
                    if res.status_code != 200: break
                    
                    data = res.json().get('data', [])
                    if not data: break
                    
                    # طباعة تتبع حية للتحقق
                    first_player = data[0].get('display_name', 'Unknown')
                    logging.info(f"🔍 [تتبع] الصفحة {page} بدأت بـ: {first_player}")
                    
                    for p in data:
                        self.push("players", p['id'], {
                            "id": p['id'], 
                            "name": p['display_name'], 
                            "age": p.get('age'),
                            "nationality": p.get('country', {}).get('name') if p.get('country') else "غير محدد",
                            "team_name": p.get('team', {}).get('name') if p.get('team') else "بدون فريق",
                            "image_url": p.get('image_path'), 
                            "position": p.get('position', {}).get('name') if p.get('position') else "غير محدد"
                        }, p['display_name'])
                time.sleep(0.5)
            except Exception as e:
                logging.error(f"❌ خطأ في الصفحة {page}: {e}")
                break

    def run(self):
        logging.info("🚀 بدء تشغيل المحرك الشامل...")
        self.task_sportmonks()
        logging.info("------------------------------------------")
        logging.info(f"📊 التقرير النهائي: تمت إضافة {self.stats['added']}، تخطي {self.stats['skipped']}")
        logging.info("🏆 اكتملت المهمة بنجاح!")

if __name__ == "__main__":
    DSTWR_Master_Engine().run()
