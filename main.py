import os
import requests
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DSTWR_ErrorHunterEngine:
    def __init__(self):
        self.base_url = "https://nugskdozmxlgrnkfsxlg.supabase.co/rest/v1"
        self.headers = {
            "apikey": os.getenv("SUPABASE_KEY"),
            "Authorization": f"Bearer {os.getenv('SUPABASE_KEY')}",
            "Content-Type": "application/json",
            "Prefer": "return=representation,resolution=merge-duplicates"
        }
        self.token = os.getenv("FOOTBALL_DATA_KEY")
        self.leagues = [
            {"code": "PL", "id": 2021, "name": "Premier League"},
            {"code": "PD", "id": 2014, "name": "La Liga"}
        ]

    def check_response(self, context, response):
        """فحص الرد وطباعة الخطأ بالتفصيل لو الرفع فشل"""
        if response.status_code in [200, 201]:
            logging.info(f"✅ تم الرفع بنجاح إلى: {context}")
        else:
            logging.error(f"❌ فشل الرفع إلى [{context}]! كود الرد: {response.status_code}")
            logging.error(f"📄 رسالة الخطأ من Supabase: {response.text}")

    def run(self):
        logging.info("🚀 بدء تشغيل محرك كسر الصفر وصيد الأخطاء...")
        
        for league in self.leagues:
            logging.info(f"⏳ جاري سحب {league['name']}...")
            try:
                # 1. ضخ الدوري أولاً وفحصه
                res_league = requests.post(f"{self.base_url}/leagues", headers=self.headers, json={
                    "id": league["id"], "name": league["name"], "country": "Europe", "code": league["code"]
                })
                self.check_response(f"جدول الدوريات ({league['name']})", res_league)
                
                # سحب الترتيب والفرق من الـ API
                url = f"https://api.football-data.org/v4/competitions/{league['code']}/standings"
                res = requests.get(url, headers={'X-Auth-Token': self.token}, timeout=15)
                
                if res.status_code == 200:
                    table = res.json().get('standings', [{}])[0].get('table', [])
                    logging.info(f"📦 تم جلب {len(table)} فريق لـ {league['name']}. بدء محاولة الضخ...")
                    
                    for item in table:
                        t = item.get('team', {})
                        
                        # 2. ضخ الفريق وفحصه
                        res_team = requests.post(f"{self.base_url}/teams", headers=self.headers, json={
                            "id": t.get('id'), "league_id": league["id"], "name": t.get('name'), "short_name": t.get('shortName'), "logo_url": t.get('crest')
                        })
                        self.check_response(f"جدول الفرق ({t.get('name')})", res_team)
                        
                        # 3. ضخ الترتيب وفحصه
                        res_standing = requests.post(f"{self.base_url}/league_standings", headers=self.headers, json={
                            "league_id": league["id"], "team_id": t.get('id'), "played": item.get('playedGames'), "points": item.get('points'), "goal_difference": item.get('goalDifference')
                        })
                        self.check_response(f"جدول الترتيب لـ ({t.get('name')})", res_standing)
                else:
                    logging.warning(f"⚠️ الموقع الخارجي رفض الطلب بكود: {res.status_code} - {res.text}")
                
                time.sleep(3)
            except Exception as e:
                logging.error(f"❌ خطأ عام غير متوقع: {e}")

if __name__ == "__main__":
    DSTWR_ErrorHunterEngine().run()
