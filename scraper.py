import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1920,1080')

driver = webdriver.Chrome(options=options)
driver.get("https://en.volleyballworld.com/beachvolleyball/competitions/beach-volleyball-world-championships/schedule/")
time.sleep(5)

team_links = [a.get_attribute('href')
              for a in driver.find_elements(By.CSS_SELECTOR, "a[href*='/teams/']")
              if '/teams/' in a.get_attribute('href')]

data = []

for url in team_links:
    driver.get(url)
    time.sleep(4)
    try:
        driver.find_element(By.XPATH, "//button[contains(.,'Players')]").click()
        time.sleep(2)
        tables = driver.find_elements(By.TAG_NAME, "table")
        if len(tables) > 1:
            rows = tables[1].find_elements(By.TAG_NAME, "tr")
            for row in rows:
                cols = [td.text for td in row.find_elements(By.TAG_NAME, "td")]
                if cols:
                    data.append([url] + cols)
    except Exception as e:
        print(f"Error at {url}: {str(e)}")

driver.quit()
df = pd.DataFrame(data)
df.to_csv("volleyball_players_efficiency.csv", index=False)
print("Done! Results saved to volleyball_players_efficiency.csv")
