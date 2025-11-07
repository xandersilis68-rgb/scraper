import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import datetime
import os
import json

BASE_URL = 'https://en.volleyballworld.com/beachvolleyball/competitions/beach-volleyball-world-championships/players'
OUTPUT_DIR = 'data'
COLUMNS = ['player_id','name','serve','reception','attack','block','dig','timestamp']

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(BASE_URL)
        await page.wait_for_selector('a.player-card__link')  # wait for JS to load links

        # Get all men player links
        player_links = await page.query_selector_all('a.player-card__link')
        players = []
        for link in player_links:
            gender_elem = await link.query_selector('.player-card__gender')
            gender = (await gender_elem.inner_text()).strip() if gender_elem else ''
            if gender != 'M':
                continue
            href = await link.get_attribute('href')
            player_id = int(href.split('/')[-1].split('#')[0])
            players.append({'id': player_id, 'url': 'https://en.volleyballworld.com'+href})

        print(f"Found {len(players)} men players")

        data = []
        for pinfo in players:
            await page.goto(pinfo['url'])
            await page.wait_for_selector('h1.player-detail__name')
            name = (await page.inner_text('h1.player-detail__name')).strip()
            
            def extract_efficiency(keyword):
                elems = page.locator(f"div:has-text('{keyword}')")
                if elems.count() == 0:
                    return None
                text = elems.nth(0).inner_text()
                return float(''.join([c for c in text if c.isdigit() or c=='.']))

            rec = {
                'player_id': pinfo['id'],
                'name': name,
                'serve': extract_efficiency('Serve efficiency'),
                'reception': extract_efficiency('Reception efficiency'),
                'attack': extract_efficiency('Attack efficiency'),
                'block': extract_efficiency('Block efficiency'),
                'dig': extract_efficiency('Dig efficiency'),
                'timestamp': datetime.datetime.utcnow().isoformat()
            }
            data.append(rec)
            print(f"Scraped {name} ({pinfo['id']})")

        await browser.close()

        # Save files
        df = pd.DataFrame(data, columns=COLUMNS)
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        now_str = datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')

        df.to_csv(f"{OUTPUT_DIR}/efficiencies_{now_str}.csv", index=False)
        with open(f"{OUTPUT_DIR}/efficiencies_{now_str}.json",'w', encoding='utf-8') as f:
            json.dump(data,f,indent=2)

        # Latest files
        df.to_csv(f"{OUTPUT_DIR}/efficiencies_latest.csv", index=False)
        with open(f"{OUTPUT_DIR}/efficiencies_latest.json",'w', encoding='utf-8') as f:
            json.dump(data,f,indent=2)

        # Markdown table for GitHub Pages
        df.to_markdown(f"{OUTPUT_DIR}/efficiencies_latest.md", index=False)

if __name__=='__main__':
    asyncio.run(main())
