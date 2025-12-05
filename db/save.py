import psycopg2

def save_rows(rows, conn_string):
    conn = psycopg2.connect(conn_string)
    cur = conn.cursor()

    for row in rows:
        cur.execute("""
            INSERT INTO tsa_realtime
            (airport_code, checkpoint,
             general_status, general_min, general_max,
             pre_status, pre_min, pre_max,
             collected_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            row["airport"],
            row["checkpoint"],
            row["general_status"],
            row["general_min"],
            row["general_max"],
            row["pre_status"],
            row["pre_min"],
            row["pre_max"],
            row["timestamp"]
        ))

    conn.commit()
    cur.close()
    conn.close()
