import os
import sys
from datetime import datetime, timezone
from typing import Callable, List, Dict

from scrapers.dca import scrape_dca_wait
from scrapers.slc import scrape_slc_wait
from db.save import save_rows


ScraperFunc = Callable[..., List[Dict]]


def run_single_airport(
    name: str,
    scrape_func: ScraperFunc,
    collected_at,
    conn_str: str,
) -> bool:
    """
    Run one airport scraper, save rows, and log result.

    Returns True on success, False on failure.
    """
    try:
        rows = scrape_func(collected_at=collected_at)
        save_rows(rows, conn_str)
        print(f"{name}: saved {len(rows)} rows.")
        return True
    except Exception as exc:
        print(f"{name}: ERROR while running scraper: {exc}", file=sys.stderr)
        return False


def main() -> None:
    conn = os.getenv("DATABASE_URL")
    if not conn:
        raise RuntimeError("DATABASE_URL environment variable is not set")

    collected_at = datetime.now(timezone.utc)

    # Add new airports here as you create new scrapers
    success = True
    success &= run_single_airport("DCA", scrape_dca_wait, collected_at, conn)
    success &= run_single_airport("SLC", scrape_slc_wait, collected_at, conn)

    if not success:
        # Non-zero exit so GitHub Actions shows failure
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Error while running all scrapers: {exc}", file=sys.stderr)
        sys.exit(1)
