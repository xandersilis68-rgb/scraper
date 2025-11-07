import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import os
import json
import time
import random
from datetime import datetime as dt

# ---------------- CONFIG ----------------
BASE_URL = 'https://en.volleyballworld.com/beachvolleyball/competitions/beach-volleyball-world-championships/players/'
OUTPUT_DIR = 'data'
COLUMNS = ['player_id','name','serve','reception','attack','block','dig','timestamp']

# Tournament dates (UTC) — adjust to real 2025 WC dates
TOURNAMENT_START = dt(2025, 6, 1)
TOURNAMENT_END   = dt(2025, 6, 30)

# Exit if tournament is not running
now = dt.utcnow()
if now < TOURNAMENT_START:
    print(f"Tournament has not started yet ({now.date()} < {TOURNAMENT_START.date()}) → skipping scrape")
    exit(0)
if now > TOURNAMENT_END:
    print(f"Tournament is over ({now.date()} > {TOURNAMENT_END.date()}) → skipping scrape")
    exit(0)

# --------------- HELPER ----------------
def get_html(url, retries=5, delay=2):
    headers = {'User-Agent': 'Mozilla/5.0'}
    for i in range(retries):
        try:
            r = requests.get(url, headers=headers)
            if r.status_code == 200:
                return r.text
            print(f"[Retry {i+1}/{retries}] {url} → status={r.status_code}")
        except Exception as e:
            print(f"[Retry {i+1}/{retries}] exception: {e}")
        time.sleep(delay + random.random()*2)
    raise Exception(f"Failed to fetch {url} after {retries} retries")

# --------------- PLAYER DISCOVERY ----------------
def discover_player_ids():
    url = 'https://en.volleyballworld.com/beachvolleyball/competitions/beach-volleyball-world-championships/people/players/'
    html = get_html(url)
    soup = BeautifulSoup(html, 'html.parser')
    ids = []
    for card in soup.select('div.card-player'):
        g = card.select_one('.card-player__gender')
        if not g or g.get_text(strip=True) != 'M':  # MEN ONLY
            continue
        link = card.select_one('a[href*="/players/"]')
        if not link:
            continue
        href = link.get('href')
        parts = href.split('/')
        try:
            pid = int(parts[-1].split('#')[0])
            ids.append(pid)
        except:
            continue
    return sorted(set(ids))

# --------------- PLAYER SCRAPE ----------------
def fetch_player_efficiency(player_id):
    headers = {'User-Agent': 'Mozilla/5.0'}
    for attempt in range(6):
        try:
            r = requests.get(f"{BASE_URL}{player_id}", headers=headers)
            if r.status_code == 200:
                break
            print(f"[PID {player_id}] retry {attempt+1}/6 → status={r.status_code}")
        except Exception as e:
            print(f"[PID {player_id}] retry {attempt+1}/6 exception: {e}")
        time.sleep(2 + random.random()*2)
    else:
        print(f"[PID {player_id}] FAILED permanently")
        return {
            'player_id': player_id,
            'name': f'player_{player_id}',
            'serve': None,'reception':None,'attack':None,'block':None,'dig':None,
            'timestamp': datetime.datetime.utcnow().isoformat()
        }

    soup = BeautifulSoup(r.text, 'html.parser')
    name_tag = soup.select_one('h1.player-detail__name')
    name = name_tag.get_text(strip=True) if name_tag else f"player_{player_id}"

    def get_value(keyword):
        block = soup.find(lambda tag: tag.name=='div' and keyword in tag.get_text())
        if not block: return None
        txt = block.get_text(strip=True).replace(keyword,'').replace('%','').strip()
        try: return float(txt)
        except: return None

    return {
        'player_id': player_id,
        'name': name,
        'serve': get_value('Serve efficiency'),
        'reception': get_value('Reception efficiency'),
        'attack': get_value('Attack efficiency'),
        'block': get_value('Block efficiency'),
        'dig': get_value('Dig efficiency'),
        'timestamp': datetime.datetime.utcnow().isoformat()
    }

# ---------------- MAIN ----------------
def main():
    player_ids = discover_player_ids()
    print(f"Discovered {len(player_ids)} MEN players")
    data = []
    for pid in player_ids:
        rec = fetch_player_efficiency(pid)
        print(f"Fetched {pid} → {rec['name']}")
        data.append(rec)

    df = pd.DataFrame(data, columns=COLUMNS)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    now_str = datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')

    # timestamped files
    df.to_csv(f"{OUTPUT_DIR}/efficiencies_{now_str}.csv", index=False)
    with open(f"{OUTPUT_DIR}/efficiencies_{now_str}.json",'w', encoding='utf-8') as f:
        json.dump(data,f,indent=2)

    # latest files
    df.to_csv(f"{OUTPUT_DIR}/efficiencies_latest.csv", index=False)
    with open(f"{OUTPUT_DIR}/efficiencies_latest.json",'w', encoding='utf-8') as f:
        json.dump(data,f,indent=2)

if __name__=='__main__':
    main()
