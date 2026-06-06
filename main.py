import os
import requests
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')

class DSTWR_Master_Engine:
    def __init__(self):
        self.keys = {
            "monks": os.getenv("SPORTMONKS_KEY"),
            "supabase": os.getenv("SUPABASE_KEY")
        }
        self.sup_url = "https://nugskdozmxlgrnkfsxlg.supabase.co/rest/v1"
        self.sup_headers = {
            "apikey": self.keys["supabase"],
            "Authorization": f"Bearer {self.keys['supabase']}",
            "Content-Type": "application/json",
            "Prefer": "return=representation, resolution=merge-duplicates"
        }
        self.stats = {"processed": 0}

    def push(self, table, data):
        """رفع وتحديث البيانات (Upsert)"""
        try:
            # نرسل البيانات مباشرة، وسوبربيز تتعامل مع التحديث التلقائي
            res = requests.post(f"{self.sup_url}/{table}", headers=self.sup_headers, json=data, timeout=10)
            if res.status_code in [200, 201]:
                self.stats["processed"] += 1
                return True
        except Exception as e:
            logging.error(f"❌ خطأ: {e}")
        return False

    def task_sportmonks(self):
        logging.info("⚽ بدء مزامنة البيانات (وضع التحديث التلقائي)...")
        for page in range(1, 11): 
            url = f"https://api.sportmonks.com/v3/football/players?api_token={self.keys['monks']}&page={page}&include=team;country;position"
            try:
                res = requests.get(url, timeout=15)
                data = res.json().get('data', [])
                
                if not data: break
                
                logging.info(f"🔍 [تتبع] معالجة الصفحة {page} - ({len(data)} لاعب)")
                
                for p in data:
                    player_data = {
                        "id": p['id'], 
                        "name": p['display_name'], 
                        "age": p.get('age'),
                        "nationality": p.get('country', {}).get('name') if p.get('country') else "غير محدد",
                        "team_name": p.get('team', {}).get('name') if p.get('team') else "بدون فريق",
                        "image_url": p.get('image_path'), 
                        "position": p.get('position', {}).get('name') if p.get('position') else "غير محدد"
                    }
                    self.push("players", player_data)
                
                time.sleep(0.5)
            except Exception as e:
                logging.error(f"❌ خطأ في الصفحة {page}: {e}")
                break

    def run(self):
        logging.info("🚀 بدء تشغيل محرك المزامنة الذكي...")
        self.task_sportmonks()
        logging.info(f"📊 التقرير النهائي: تم معالجة {self.stats['processed']} سجل بنجاح.")
        logging.info("🏆 اكتملت المهمة!")

if __name__ == "__main__":
    DSTWR_Master_Engine().run()
