import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import os
import json

BASE_URL = 'https://en.volleyballworld.com/beachvolleyball/competitions/beach-volleyball-world-championships/players/'
OUTPUT_DIR = 'data'
COLUMNS = ['player_id','name','serve','reception','attack','block','dig','timestamp']

def discover_player_ids():
    url = 'https://en.volleyballworld.com/beachvolleyball/competitions/beach-volleyball-world-championships/players/?gender=men'
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    ids = []
    for link in soup.select('a[href*="/players/"]'):
        href = link.get('href')
        parts = href.split('/')
        try:
            pid = int(parts[-1].split('#')[0])
            ids.append(pid)
        except:
            continue
    return sorted(set(ids))

def fetch_player_efficiency(player_id):
    url = f"{BASE_URL}{player_id}"
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')

    name_tag = soup.select_one('h1.player-detail__name')
    name = name_tag.get_text(strip=True) if name_tag else f"player_{player_id}"

    def get_value(keyword):
        el = soup.find(lambda tag: tag.name=='div' and keyword in tag.get_text())
        if el:
            t = el.get_text(strip=True).replace(keyword,'').replace('%','').strip()
            try: return float(t)
            except: return None
        return None

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

def main():
    player_ids = discover_player_ids()
    print(f"Discovered {len(player_ids)} players")
    data=[]
    for pid in player_ids:
        try:
            rec = fetch_player_efficiency(pid)
            print(f"Fetched {pid} => {rec['name']}")
            data.append(rec)
        except Exception as e:
            print("error",pid,e)
    df = pd.DataFrame(data, columns=COLUMNS)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    now = datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    df.to_csv(f"{OUTPUT_DIR}/efficiencies_{now}.csv", index=False)
    with open(f"{OUTPUT_DIR}/efficiencies_{now}.json",'w') as f:
        json.dump(data,f,indent=2)

    df.to_csv(f"{OUTPUT_DIR}/efficiencies_latest.csv", index=False)
    with open(f"{OUTPUT_DIR}/efficiencies_latest.json",'w') as f:
        json.dump(data,f,indent=2)

if __name__=='__main__':
    main()
