from scrapers.dca import scrape_dca_wait
from db.save import save_rows
import os
import sys


def main() -> None:
    conn = os.getenv("DATABASE_URL")
    if not conn:
        # Fail loudly so you notice misconfig in Actions or locally
        raise RuntimeError("DATABASE_URL environment variable is not set.")

    rows = scrape_dca_wait()
    save_rows(rows, conn)
    print("Saved", len(rows), "rows.")


if __name__ == "__main__":
    # Optional: basic guard for unexpected exceptions with a non-zero exit
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        print(f"Error while running DCA scraper: {exc}", file=sys.stderr)
        sys.exit(1)
