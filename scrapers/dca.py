from typing import List, Tuple, Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import time

URL = "https://www.flyreagan.com/travel-information/security-information"

# Row shape for tsa_waits:
# (airport_code, checkpoint, lane_type, status, wait_min, wait_max, source_raw, collected_at)
Row = Tuple[str, str, str, str, Optional[int], Optional[int], Optional[str], datetime]


def parse_wait(cell_text: str) -> Tuple[str, Optional[int], Optional[int]]:
    """
    Robustly parse a wait time cell from DCA.

    Returns:
        (status, wait_min, wait_max)

        status: "Open", "Closed", or "Unknown"
        wait_min / wait_max: ints in minutes, or None if not applicable.
    """
    if not cell_text:
        return "Closed", None, None

    t = cell_text.strip().lower()
    if not t:
        return "Closed", None, None

    # Closed or not yet open
    if "closed" in t or t == "--" or "opens" in t:
        return "Closed", None, None

    # Handle "No Wait" style text as essentially 0–5 minutes
    if "no wait" in t:
        return "Open", 0, 5

    # Normalize punctuation: turn en-dashes etc. into standard hyphen
    t = t.replace("–", "-").replace("—", "-")

    # Extract only digits and hyphens, everything else becomes space
    cleaned = ""
    for c in t:
        if c.isdigit() or c == "-":
            cleaned += c
        else:
            cleaned += " "

    parts = [p for p in cleaned.split() if p]

    if not parts:
        return "Unknown", None, None

    # Case: a token like "4-7"
    for token in parts:
        if "-" in token:
            bits = [b for b in token.split("-") if b]
            if len(bits) == 2:
                try:
                    lo = int(bits[0])
                    hi = int(bits[1])
                    # If somehow reversed, fix it
                    if hi < lo:
                        lo, hi = hi, lo
                    return "Open", lo, hi
                except ValueError:
                    return "Unknown", None, None

    # Case: two separate integers ["4", "7"]
    if len(parts) >= 2:
        try:
            lo = int(parts[0])
            hi = int(parts[1])
            if hi < lo:
                lo, hi = hi, lo
            return "Open", lo, hi
        except ValueError:
            return "Unknown", None, None

    # Case: single integer ["5"] ⇒ 0–5
    if len(parts) == 1:
        try:
            hi = int(parts[0])
            return "Open", 0, hi
        except ValueError:
            return "Unknown", None, None

    return "Unknown", None, None


def scrape_dca_wait(collected_at: datetime) -> List[Row]:
    """
    Scrape TSA wait times for DCA and return one row per lane (general / precheck).

    Args:
        collected_at: datetime (UTC) when the data was pulled, supplied by caller.

    Returns:
        List of rows shaped for tsa_waits:
        (airport_code, checkpoint, lane_type, status, wait_min, wait_max, source_raw, collected_at)
    """
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(URL)
        # Give the page a moment to load the table
        time.sleep(3)

        soup = BeautifulSoup(driver.page_source, "html.parser")
    finally:
        driver.quit()

    rows = soup.select("#resp-table-body .resp-table-row")

    results: List[Row] = []
    airport_code = "DCA"

    for row in rows:
        cells = row.select(".table-body-cell")
        if len(cells) < 3:
            continue

        checkpoint = cells[0].get_text(strip=True)
        general_raw = cells[1].get_text(strip=True)
        pre_raw = cells[2].get_text(strip=True)

        gen_status, gen_min, gen_max = parse_wait(general_raw)
        pre_status, pre_min, pre_max = parse_wait(pre_raw)

        # General lane row
        results.append(
            (
                airport_code,
                checkpoint,
                "general",
                gen_status,
                gen_min,
                gen_max,
                general_raw if general_raw else None,
                collected_at,
            )
        )

        # Precheck lane row
        results.append(
            (
                airport_code,
                checkpoint,
                "precheck",
                pre_status,
                pre_min,
                pre_max,
                pre_raw if pre_raw else None,
                collected_at,
            )
        )

    return results


if __name__ == "__main__":
    # Simple manual test: run locally and print rows
    now_utc = datetime.now(timezone.utc)
    scraped_rows = scrape_dca_wait(collected_at=now_utc)
    for r in scraped_rows:
        print(r)
