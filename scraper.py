import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
import time

# Chrome options
options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1920,1080')

# Use CHROMEDRIVER_PATH from env
chromedriver_path = os.environ.get('CHROMEDRIVER_PATH', 'chromedriver')

try:
    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=options)
except WebDriverException as e:
    print(f"Failed to start Chrome WebDriver: {e}")
    exit(1)

driver.get("https://en.volleyballworld.com/beachvolleyball/competitions/beach-volleyball-world-championships/schedule/")
time.sleep(5)

# Get team links
team_links = [a.get_attribute('href')
              for a in driver.find_elements(By.CSS_SELECTOR, "a[href*='/teams/']")]

data = []

for url in team_links:
    driver.get(url)
    time.sleep(4)
    try:
        # Open the Players tab
        driver.find_element(By.XPATH, "//button[contains(.,'Players')]").click()
        time.sleep(2)

        tables = driver.find_elements(By.TAG_NAME, "table")
        if len(tables) > 1:
            rows = tables[1].find_elements(By.TAG_NAME, "tr")
            headers = [th.text.lower() for th in tables[1].find_elements(By.TAG_NAME, "th")]

            # Find column indices
            idx_map = {}
            for stat in ['player', 'serve', 'receive', 'attack', 'block', 'dig']:
                for i, h in enumerate(headers):
                    if stat in h:
                        idx_map[stat] = i
                        break

            # Extract player name + efficiency columns
            for row in rows:
                cols = [td.text for td in row.find_elements(By.TAG_NAME, "td")]
                if cols:
                    filtered = [cols[idx_map[stat]] if stat in idx_map else '' for stat in ['player','serve','receive','attack','block','dig']]
                    data.append([url] + filtered)

    except Exception as e:
        print(f"Error at {url}: {e}")

driver.quit()

# Save CSV with player names and efficiencies
df = pd.DataFrame(data, columns=['team_url','player','serve_eff','receive_eff','attack_eff','block_eff','dig_eff'])
df.to_csv("volleyball_players_efficiency.csv", index=False)
print("Done! Results saved to volleyball_players_efficiency.csv")
