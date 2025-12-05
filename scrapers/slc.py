# scrapers/slc.py

import math
import re
import time
from datetime import datetime
from typing import List, Dict

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


SLC_URL = "https://slcairport.com/"
AIRPORT_CODE = "SLC"
CHECKPOINT_NAME = "main"      # single main checkpoint
LANE_TYPE = "overall"         # combined wait for all lanes


def create_driver() -> webdriver.Chrome:
    """
    Create a headless Chrome WebDriver (works in GitHub Actions and locally).
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def parse_slc_wait_text(text: str) -> int | None:
    """
    Parse SLC's time string into an integer number of minutes.

    Examples of expected input:
        "6 minutes and 18 seconds"
        "3 minutes"
        "45 seconds"
        "No wait"

    Returns:
        int minutes (rounded UP) or None if we can't parse.
    """
    if not text:
        return None

    s = text.strip().lower()

    if "no wait" in s:
        return 0

    # Extract minutes and seconds if present
    m_min = re.search(r"(\d+)\s*minute", s)
    m_sec = re.search(r"(\d+)\s*second", s)

    minutes = int(m_min.group(1)) if m_min else 0
    seconds = int(m_sec.group(1)) if m_sec else 0

    total_seconds = minutes * 60 + seconds
    if total_seconds < 0:
        return None

    # Round UP so 6m18s -> 7 minutes
    return int(math.ceil(total_seconds / 60)) if total_seconds > 0 else 0


def scrape_slc_wait(collected_at: datetime) -> List[Dict]:
    """
    Scrape SLC's estimated security screening wait time.

    Returns a list of row dicts shaped for tsa_waits,
    ready to be passed into db.save.save_rows().
    """
    driver = create_driver()
    wait_text = ""

    try:
        driver.get(SLC_URL)

        # Wait up to 20 seconds for the "time" span to appear
        wait = WebDriverWait(driver, 20)
        time_element = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div.labels span.time")
            )
        )

        wait_text = time_element.text.strip()
        wait_minutes = parse_slc_wait_text(wait_text)

        if wait_minutes is None:
            status = "Unknown"
            wait_min = None
            wait_max = None
        else:
            status = "Open"
            wait_min = wait_minutes
            wait_max = wait_minutes

    finally:
        driver.quit()

    row = {
        "airport_code": AIRPORT_CODE,
        "checkpoint": CHECKPOINT_NAME,
        "lane_type": LANE_TYPE,
        "status": status,
        "wait_min": wait_min,
        "wait_max": wait_max,
        "source_raw": wait_text,
        "collected_at": collected_at,
    }

    return [row]


if __name__ == "__main__":
    # Small manual test runner
    from datetime import timezone

    now = datetime.now(timezone.utc)
    rows = scrape_slc_wait(collected_at=now)
    for r in rows:
        print(
            f"SLC scrape result: wait={r['wait_min']} min, "
            f"status={r['status']}, raw='{r['source_raw']}'"
        )
