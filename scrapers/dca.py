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
    Parse a DCA wait-time cell.

    Returns:
        status (str): "Open", "Closed", or "Unknown"
        min (int or None)
        max (int or None)
    """
    if not cell_text:
        return "Closed", None, None

    t = cell_text.strip().lower()

    # Explicit closed behavior
    if "closed" in t or t == "--":
        return "Closed", None, None

    # If lane hasn't opened yet
    if "opens" in t:
        return "Closed", None, None

    # Extract numeric content from cases like "< 5 mins" or "4-7 mins"
    digits = "".join([c if c.isdigit() or c == "-" else " " for c in t])
    parts = [p for p in digits.split() if p]

    # "< 5 mins" → treat as 0–5
    if len(parts) == 1:
        return "Open", 0, int(parts[0])

    # "4-7 mins"
    if len(parts) == 2:
        return "Open", int(parts[0]), int(parts[1])

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
