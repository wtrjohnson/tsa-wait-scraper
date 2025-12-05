from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from datetime import datetime
import time

URL = "https://www.flyreagan.com/travel-information/security-information"


def parse_wait(cell_text):
    """
    Robustly parse a wait time cell from DCA.
    Returns: (status, min, max)
    """

    if not cell_text:
        return "Closed", None, None

    t = cell_text.strip().lower()

    # Closed
    if "closed" in t or t == "--":
        return "Closed", None, None

    if "opens" in t:
        return "Closed", None, None

    # Normalize punctuation: turn en-dashes etc. into standard hyphen
    t = t.replace("–", "-").replace("—", "-")

    # Extract only digits and hyphens
    cleaned = ""
    for c in t:
        if c.isdigit() or c == "-":
            cleaned += c
        else:
            cleaned += " "

    parts = [p for p in cleaned.split() if p]

    # Case: "< 5 mins" → parts might be ["5"]
    if len(parts) == 1:
        # Example: "5"
        try:
            return "Open", 0, int(parts[0])
        except ValueError:
            return "Unknown", None, None

    # Case: "4-7" or "4 - 7"
    if len(parts) == 1 and "-" in parts[0]:
        try:
            lo, hi = parts[0].split("-")
            return "Open", int(lo), int(hi)
        except:
            return "Unknown", None, None

    # Case: properly split range ["4", "7"]
    if len(parts) == 2:
        try:
            return "Open", int(parts[0]), int(parts[1])
        except:
            return "Unknown", None, None

    return "Unknown", None, None



def scrape_dca_wait():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    driver.get(URL)
    time.sleep(3)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    rows = soup.select("#resp-table-body .resp-table-row")

    results = []
    for row in rows:
        cells = row.select(".table-body-cell")
        if len(cells) < 3:
            continue

        checkpoint = cells[0].get_text(strip=True)
        general = cells[1].get_text(strip=True)
        pre = cells[2].get_text(strip=True)

        gen_status, gen_min, gen_max = parse_wait(general)
        pre_status, pre_min, pre_max = parse_wait(pre)

        results.append({
            "airport": "DCA",
            "checkpoint": checkpoint,
            "general_status": gen_status,
            "general_min": gen_min,
            "general_max": gen_max,
            "pre_status": pre_status,
            "pre_min": pre_min,
            "pre_max": pre_max,
            "timestamp": datetime.utcnow()
        })

    return results


if __name__ == "__main__":
    rows = scrape_dca_wait()
    for r in rows:
        print(r)
