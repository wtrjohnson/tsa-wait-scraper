from typing import Iterable, Sequence
import psycopg2
from psycopg2.extras import execute_values


def save_rows(rows: Sequence[tuple], conn_str: str) -> None:
    if not rows:
        return

    insert_sql = """
        INSERT INTO tsa_waits (
            airport_code,
            checkpoint,
            lane_type,
            status,
            wait_min,
            wait_max,
            source_raw,
            collected_at
        )
        VALUES %s
        ON CONFLICT (airport_code, checkpoint, lane_type, collected_at)
        DO UPDATE SET
            status     = EXCLUDED.status,
            wait_min   = EXCLUDED.wait_min,
            wait_max   = EXCLUDED.wait_max,
            source_raw = EXCLUDED.source_raw;
    """

    with psycopg2.connect(conn_str) as conn:
        with conn.cursor() as cur:
            execute_values(cur, insert_sql, rows)
        conn.commit()
