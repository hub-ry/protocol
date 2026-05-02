import json
import os
import sqlite3
from contextlib import contextmanager

DATA_DIR = "./data"
DB_PATH = os.path.join(DATA_DIR, "life.db")
JSON_PATH = os.path.join(DATA_DIR, "weight.json")

os.makedirs(DATA_DIR, exist_ok=True)


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS weight (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                weight REAL NOT NULL,
                date TEXT NOT NULL,
                timestamp TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_weight_date ON weight(date);
        """)


def import_weights():
    with open(JSON_PATH) as f:
        records = json.load(f)

    imported = 0
    skipped = 0

    with get_db() as conn:
        for record in records:
            date = record["date"]
            weight = record["weight"]

            # Check for an existing row with the same date and weight to avoid duplicates.
            existing = conn.execute(
                "SELECT id FROM weight WHERE date = ? AND weight = ?",
                (date, weight),
            ).fetchone()

            if existing:
                skipped += 1
                continue

            # Use midnight on the record's date as the timestamp so ORDER BY timestamp
            # gives the same chronological order as ORDER BY date.
            conn.execute(
                "INSERT INTO weight (weight, date, timestamp) VALUES (?, ?, ?)",
                (weight, date, date + "T00:00:00"),
            )
            imported += 1

    print(f"Imported {imported}, skipped {skipped}")


if __name__ == "__main__":
    init_db()
    import_weights()
