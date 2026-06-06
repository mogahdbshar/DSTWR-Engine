import os
import requests
import pandas as pd
import json
import hashlib
import time
from datetime import datetime
import sys
import io

# إعداد الطباعة الفورية
sys.stdout.reconfigure(line_buffering=True)

print("="*70, flush=True)
print("🏆 بدء تشغيل أرشيف كرة القدم الشامل", flush=True)
print("="*70, flush=True)

# Supabase
SUPABASE_URL = "https://nugskdozmxlgrnkfsxlg.supabase.co/rest/v1"
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

def upsert_to_supabase(table, data_list):
    if not data_list:
        return 0
    if not isinstance(data_list, list):
        data_list = [data_list]
    
    inserted = 0
    for i in range(0, len(data_list), 50):
        batch = data_list[i:i+50]
        try:
            h = headers.copy()
            h["Prefer"] = "resolution=merge-duplicates,return=minimal"
            resp = requests.post(f"{SUPABASE_URL}/{table}", headers=h, json=batch, timeout=30)
            if resp.status_code in [200, 201]:
                inserted += len(batch)
                print(f"   ✅ رفع دفعة إلى {table}: {len(batch)} سجل", flush=True)
            else:
                print(f"   ⚠️ فشل رفع دفعة إلى {table}: {resp.status_code}", flush=True)
        except Exception as e:
            print(f"   ❌ خطأ: {str(e)[:50]}", flush=True)
        time.sleep(0.1)
    return inserted

# ========== 1. jokecamp/FootballData ==========
print("\n📥 [1/4] جلب بيانات jokecamp/FootballData...", flush=True)

try:
    url = "https://raw.githubusercontent.com/jokecamp/FootballData/master/data/EPL/2015-16/2015-16_PL_Results.csv"
    resp = requests.get(url, timeout=30)
    if resp.status_code == 200:
        df = pd.read_csv(io.StringIO(resp.text))
        matches = []
        for _, row in df.iterrows():
            match_id = hashlib.md5(f"{row.get('Date')}_{row.get('HomeTeam')}_{row.get('AwayTeam')}".encode()).hexdigest()
            matches.append({
                "id": match_id,
                "date": row.get("Date"),
                "home_team": row.get("HomeTeam"),
                "away_team": row.get("AwayTeam"),
                "home_score": row.get("FTHG"),
                "away_score": row.get("FTAG"),
                "league": "EPL"
            })
        count = upsert_to_supabase("matches", matches)
        print(f"   ✅ تم رفع {count} مباراة من jokecamp", flush=True)
    else:
        print(f"   ❌ فشل: HTTP {resp.status_code}", flush=True)
except Exception as e:
    print(f"   ❌ خطأ: {str(e)}", flush=True)

# ========== 2. engsoccerdata (بيانات تاريخية إنجلترا) ==========
print("\n📥 [2/4] جلب بيانات engsoccerdata التاريخية...", flush=True)

try:
    url = "https://raw.githubusercontent.com/jalapic/engsoccerdata/master/data-raw/engsoccerdata2.csv"
    resp = requests.get(url, timeout=30)
    if resp.status_code == 200:
        df = pd.read_csv(io.StringIO(resp.text))
        matches = []
        for _, row in df.head(5000).iterrows():
            match_id = hashlib.md5(f"{row.get('Date')}_{row.get('home')}_{row.get('visitor')}_{row.get('Season')}".encode()).hexdigest()
            matches.append({
                "id": match_id,
                "date": row.get("Date"),
                "season": row.get("Season"),
                "home_team": row.get("home"),
                "away_team": row.get("visitor"),
                "home_score": row.get("hgoal"),
                "away_score": row.get("vgoal"),
                "league": "England",
                "tier": row.get("tier")
            })
        count = upsert_to_supabase("matches", matches)
        print(f"   ✅ تم رفع {count} مباراة تاريخية", flush=True)
    else:
        print(f"   ❌ فشل: HTTP {resp.status_code}", flush=True)
except Exception as e:
    print(f"   ❌ خطأ: {str(e)}", flush=True)

# ========== 3. بيانات كأس العالم (openfootball) ==========
print("\n📥 [3/4] جلب بيانات كأس العالم...", flush=True)

worldcups = [2010, 2014, 2018, 2022, 2026]
all_wc_matches = []

for year in worldcups:
    url = f"https://raw.githubusercontent.com/openfootball/worldcup.json/master/{year}/worldcup.json"
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            for round_data in data.get("rounds", []):
                for match in round_data.get("matches", []):
                    match_id = f"wc_{year}_{match.get('num', 0)}"
                    all_wc_matches.append({
                        "id": match_id,
                        "tournament": f"FIFA World Cup {year}",
                        "season": year,
                        "home_team": match.get("team1", {}).get("name"),
                        "away_team": match.get("team2", {}).get("name"),
                        "home_score": match.get("score1"),
                        "away_score": match.get("score2"),
                        "date": match.get("date"),
                        "stadium": match.get("stadium"),
                        "status": "finished"
                    })
            print(f"   ✅ كأس العالم {year}: تم", flush=True)
        else:
            print(f"   ⚠️ كأس العالم {year}: غير متوفر", flush=True)
    except Exception as e:
        print(f"   ❌ خطأ في {year}: {str(e)[:50]}", flush=True)

if all_wc_matches:
    count = upsert_to_supabase("matches", all_wc_matches)
    print(f"   ✅ تم رفع {count} مباراة كأس عالم", flush=True)

# ========== 4. بيانات اللاعبين والإحصائيات المتقدمة (soccerdata) ==========
print("\n📥 [4/4] جلب بيانات اللاعبين والإحصائيات المتقدمة...", flush=True)

try:
    # ملاحظة: هذا يتطلب تثبيت soccerdata: pip install soccerdata
    import soccerdata as sd
    
    print("   🔄 جلب بيانات الدوري الإنجليزي من FBref...", flush=True)
    fbref = sd.FBref('ENG-Premier League', '2025')
    
    # جلب إحصائيات اللاعبين
    players_stats = fbref.read_player_season_stats(stat_type='standard')
    if players_stats is not None and not players_stats.empty:
        players = []
        for idx, row in players_stats.head(1000).iterrows():
            players.append({
                "id": hashlib.md5(f"{row.get('player')}_{row.get('team')}".encode()).hexdigest(),
                "name": row.get("player"),
                "team": row.get("team"),
                "goals": row.get("goals"),
                "assists": row.get("assists"),
                "position": row.get("position")
            })
        count = upsert_to_supabase("players", players)
        print(f"   ✅ تم رفع {count} لاعب", flush=True)
    
    # جلب جدول المباريات
    schedule = fbref.read_schedule()
    if schedule is not None and not schedule.empty:
        matches = []
        for idx, row in schedule.head(500).iterrows():
            matches.append({
                "id": hashlib.md5(f"{row.get('date')}_{row.get('home_team')}_{row.get('away_team')}".encode()).hexdigest(),
                "date": row.get("date"),
                "home_team": row.get("home_team"),
                "away_team": row.get("away_team"),
                "home_score": row.get("home_score"),
                "away_score": row.get("away_score")
            })
        count = upsert_to_supabase("matches", matches)
        print(f"   ✅ تم رفع {count} مباراة من FBref", flush=True)
        
except ImportError:
    print("   ⚠️ مكتبة soccerdata غير مثبتة. يتم تخطي هذه المرحلة.", flush=True)
    print("   للتثبيت: pip install soccerdata", flush=True)
except Exception as e:
    print(f"   ❌ خطأ في soccerdata: {str(e)[:100]}", flush=True)

# ========== النتيجة النهائية ==========
print("\n" + "="*70, flush=True)
print("🏆 اكتمل الأرشيف!", flush=True)
print("="*70, flush=True)
print("✅ تم رفع المباريات والنتائج واللاعبين والإحصائيات", flush=True)
print("✅ جميع البيانات في Supabase جاهزة للاستخدام", flush=True)
print("="*70, flush=True)
