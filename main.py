import os
import requests
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DSTWR_VerifiedEngine:
    def __init__(self):
        self.base_url = "https://nugskdozmxlgrnkfsxlg.supabase.co/rest/v1"
        self.headers = {
            "apikey": os.getenv("SUPABASE_KEY"),
            "Authorization": f"Bearer {os.getenv('SUPABASE_KEY')}",
            "Content-Type": "application/json",
            "Prefer": "return=representation,resolution=merge-duplicates"
        }
        self.token = os.getenv("FOOTBALL_DATA_KEY")
        # التركيز على دوريين مدعومين مجاناً 100% لكسر الصفر
        self.leagues = [
            {"code": "PL", "id": 2021, "name": "Premier League"},
            {"code": "PD", "id": 2014, "name": "La Liga"}
        ]

    def run(self):
        logging.info("🚀 بدء تشغيل محرك كسر الصفر المضمون...")
        
        for league in self.leagues:
            logging.info(f"⏳ جاري سحب {league['name']}...")
            try:
                # ضخ الدوري أولاً
                requests.post(f"{self.base_url}/leagues", headers=self.headers, json={
                    "id": league["id"], "name": league["name"], "country": "Europe", "code": league["code"]
                })
                
                # سحب الترتيب والفرق
                url = f"https://api.football-data.org/v4/competitions/{league['code']}/standings"
                res = requests.get(url, headers={'X-Auth-Token': self.token}, timeout=15)
                
                if res.status_code == 200:
                    table = res.json().get('standings', [{}])[0].get('table', [])
                    logging.info(f"📦 تم جلب {len(table)} فريق لـ {league['name']}")
                    
                    for item in table:
                        t = item.get('team', {})
                        # ضخ الفريق
                        requests.post(f"{self.base_url}/teams", headers=self.headers, json={
                            "id": t.get('id'), "league_id": league["id"], "name": t.get('name'), "short_name": t.get('shortName'), "logo_url": t.get('crest')
                        })
                        # ضخ الترتيب
                        requests.post(f"{self.base_url}/league_standings", headers=self.headers, json={
                            "league_id": league["id"], "team_id": t.get('id'), "played": item.get('playedGames'), "points": item.get('points'), "goal_difference": item.get('goalDifference')
                        })
                else:
                    logging.warning(f"⚠️ الموقع الخارجي رفض الطلب بكود: {res.status_code} - {res.text}")
                
                time.sleep(3) # تأخير ذكي لتجنب الحظر المؤقت (Rate Limit)
            except Exception as e:
                logging.error(f"❌ خطأ: {e}")

if __name__ == "__main__":
    DSTWR_VerifiedEngine().run()
