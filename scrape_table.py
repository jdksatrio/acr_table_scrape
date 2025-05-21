from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urljoin
import requests, pandas as pd
from bs4 import BeautifulSoup
import time, os
import tqdm

driver = webdriver.Chrome()
driver.get("https://gravitas.acr.org/acportal")
WebDriverWait(driver, 10).until(lambda d: d.execute_script("return document.readyState") == "complete")

# Step 1: Get all <a> inside .spanResolutionDocTitle
link_elements = driver.find_elements(By.CSS_SELECTOR, '.spanResolutionDocTitle a')

# Step 2: Get full URLs from hrefs
base_url = "https://gravitas.acr.org/acportal"  # Replace with your real base domain
links = [urljoin(base_url, a.get_attribute("href")) for a in link_elements]

def scrape_scenario(scenario_url: str) -> list[dict]:
    """Return a list of dictionaries—one per procedure row."""
    html = requests.get(scenario_url, timeout=10).text
    soup = BeautifulSoup(html, "lxml")

    # 1) Variant description (if present)
    variant_li = soup.select_one('a[href^="#variant"]')  # first bullet under Variants
    variant = variant_li.get_text(strip=True) if variant_li else ""

    # 2) Locate the clinical table
    table = soup.select_one("table.tblResDocs")
    rows = []
    if not table:
        return rows                        # no data found

    # scenario text & id live in <td rowspan="…"> cells of the first <tr>
    curr_scenario = curr_id = None

    for tr in table.select("tbody > tr"):
        tds = tr.find_all("td", recursive=False)

        # if the first col has rowspan, it appears only on first procedure row
        if len(tds[0].find_all("span")) >= 1 and tds[0]["rowspan"]:
            curr_scenario = tds[0].get_text(strip=True)
            curr_id       = tds[1].get_text(strip=True)

            # shift pointer so indices below align with per-procedure cols
            proc_td, adult_td, peds_td, cat_td = tds[2:6]
        else:
            # we’re in a subsequent row of the same scenario
            proc_td, adult_td, peds_td, cat_td = tds[0:4]

        rows.append({
            "variant"                : variant,
            "scenario"               : curr_scenario,
            "scenario_id"            : curr_id,
            "procedure"              : proc_td.get_text(" ", strip=True),
            "adult_rrl"              : adult_td.get_text(" ", strip=True),
            "peds_rrl"               : peds_td.get_text(" ", strip=True),
            "appropriateness_category": cat_td.get_text(" ", strip=True)
        })

    return rows

df = pd.DataFrame(list)

for link in links:
    data = scrape_scenario(link)
    df_temp = pd.DataFrame(data)
    df = pd.concat([df, df_temp])

csv_path = "acr_scenarios.csv"

first_time = not os.path.isfile(csv_path)

with open(csv_path, mode="a", newline="", encoding="utf-8") as f:
    for link in tqdm(links, desc="Scraping"):
        print(f"Processing link number ")
        try:
            rows = scrape_scenario(link)          
            if not rows:                         
                continue

            df_temp = pd.DataFrame(rows)
            df_temp.to_csv(
                f,                                
                index=False,
                header=first_time,               
                mode="a"
            )
            first_time = False                    

        except Exception as e:
            print(f"error on {link}: {e}")