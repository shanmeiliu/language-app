import psycopg
from contextlib import contextmanager

@contextmanager
def db_connection(db_connection_string):
    conn = psycopg.connect(db_connection_string)
    try:
        conn.autocommit = False
        cur = conn.cursor()
        try:
            yield cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
    finally:
        conn.close()