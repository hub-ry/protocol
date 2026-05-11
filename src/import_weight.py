"""
One-time script to seed the database with historical weight data from data/weight.json.

Run after the app has started (so init_db() has created the tables):

    docker compose exec app python src/import_weight.py

Safe to re-run — existing rows are skipped, not duplicated.
"""

import json
import os
from datetime import datetime

import psycopg

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://protocol:protocol@localhost:5432/protocol",
)
JSON_PATH = "./data/weight.json"


def import_weights():
    with open(JSON_PATH) as f:
        records = json.load(f)

    imported = 0
    skipped = 0

    # psycopg.connect() is the synchronous version — no async/await needed for a script.
    # It works identically to AsyncConnection but blocks until each query completes,
    # which is fine here since we're running this as a one-shot command, not a server.
    with psycopg.connect(DATABASE_URL) as conn:
        for record in records:
            date = record["date"]
            weight = record["weight"]

            # Check for an existing row with the same date and weight before inserting.
            existing = conn.execute(
                "SELECT id FROM weight WHERE date = %s AND weight = %s",
                (date, weight),
            ).fetchone()

            if existing:
                skipped += 1
                continue

            # Use midnight on the record's date as the timestamp so ORDER BY timestamp
            # gives the same chronological order as ORDER BY date for historical imports.
            timestamp = datetime.strptime(date, "%Y-%m-%d")
            conn.execute(
                "INSERT INTO weight (weight, date, timestamp) VALUES (%s, %s, %s)",
                (weight, date, timestamp),
            )
            imported += 1

    print(f"Done — imported {imported}, skipped {skipped} duplicates")


if __name__ == "__main__":
    import_weights()
