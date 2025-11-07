import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import datetime
import os
import json

MASTER_URL = "https://en.volleyballworld.com/beachvolleyball/competitions/beach-volleyball-world-championships/standings/men/"
OUTPUT_DIR = "data"
COLUMNS = ["player_id","name","serve","reception","attack","block","dig","timestamp"]

async def get_team_links(page):
    await page.goto(MASTER_URL)
    # Wait for teams table to load dynamically
    await page.wait_for_selector("a[href*='/teams/men/']")
    team_anchors = await page.query_selector_all("a[href*='/teams/men/']")
    links = []
    for a in team_anchors:
        href = await a.get_attribute("href")
        if href and "/players/" in href:
            full_url = "https://en.volleyballworld.com" + href
            if full_url not in links:
                links.append(full_url)
    return links

async def get_player_links(page, team_url):
    await page.goto(team_url)
    await page.wait_for_selector("a[href*='/players/']")
    player_anchors = await page.query_selector_all("a[href*='/players/']")
    links = []
    for a in player_anchors:
        href = await a.get_attribute("href")
        if href:
            full_url = "https://en.volleyballworld.com" + href
            if full_url not in links:
                links.append(full_url)
    return links

async def scrape_player(page, player_url):
    await page.goto(player_url)
    await page.wait_for_selector("h1.player-detail__name")
    name = (await page.inner_text("h1.player-detail__name")).strip()
    
    def extract_eff(keyword):
        elems = page.locator(f"div:has-text('{keyword}')")
        if (await elems.count()) == 0:
            return None
        txt = await elems.nth(0).inner_text()
        cleaned = ''.join([c for c in txt if c.isdigit() or c=='.'])
        try:
            return float(cleaned)
        except:
            return None
    
    player_id = int(player_url.rstrip("/").split("/")[-1].split("#")[0])
    
    return {
        "player_id": player_id,
        "name": name,
        "serve": extract_eff("Serve efficiency"),
        "reception": extract_eff("Reception efficiency"),
        "attack": extract_eff("Attack efficiency"),
        "block": extract_eff("Block efficiency"),
        "dig": extract_eff("Dig efficiency"),
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # 1️⃣ Get all team links
        team_links = await get_team_links(page)
        print(f"Found {len(team_links)} teams")
        
        # 2️⃣ Get all player links
        all_player_links = []
        for team_url in team_links:
            players = await get_player_links(page, team_url)
            all_player_links.extend(players)
        all_player_links = list(set(all_player_links))
        print(f"Found {len(all_player_links)} players")
        
        # 3️⃣ Scrape each player
        data = []
        for i, player_url in enumerate(all_player_links):
            try:
                rec = await scrape_player(page, player_url)
                data.append(rec)
                print(f"[{i+1}/{len(all_player_links)}] Scraped {rec['name']}")
            except Exception as e:
                print(f"Failed to scrape {player_url}: {e}")
        
        await browser.close()
        
        # 4️⃣ Save CSV / JSON / Markdown
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
        
        # Markdown
        df.to_markdown(f"{OUTPUT_DIR}/efficiencies_latest.md", index=False)
        print("Scraping complete!")

if __name__ == "__main__":
    asyncio.run(main())
