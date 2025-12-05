import os
import sys
from datetime import datetime, timezone

from scrapers.dca import scrape_dca_wait
from db.save import save_rows


def main() -> None:
    conn = os.getenv("DATABASE_URL")
    if not conn:
        raise RuntimeError("DATABASE_URL environment variable is not set")

    # collected_at = when YOU pulled the data (UTC)
    collected_at = datetime.now(timezone.utc)

    # Expect scrape_dca_wait to return a list of rows shaped for tsa_waits
    rows = scrape_dca_wait(collected_at=collected_at)

    save_rows(rows, conn)
    print(f"Saved {len(rows)} rows.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Error while running DCA scraper: {exc}", file=sys.stderr)
        sys.exit(1)
