from scrapers.dca import scrape_dca_wait
from db.save import save_rows

CONN = "postgresql://neondb_owner:npg_vFYqz7NR0xOu@ep-damp-field-a4km4fee-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

rows = scrape_dca_wait()
save_rows(rows, CONN)

print("Saved", len(rows), "rows.")
