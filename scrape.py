import asyncio
from playwright.async_api import async_playwright
import os

BASE_URL = 'https://en.volleyballworld.com/beachvolleyball/competitions/beach-volleyball-world-championships/players'
OUTPUT_DIR = 'data'

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(BASE_URL)

        # Wait a bit to ensure JS finishes loading
        await page.wait_for_timeout(5000)

        # Save full HTML for inspection
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        html = await page.content()
        with open(f"{OUTPUT_DIR}/players_list.html", 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"Saved players list HTML to {OUTPUT_DIR}/players_list.html")
        print("Inspect this file to find the correct selectors for player links and gender.")

        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
