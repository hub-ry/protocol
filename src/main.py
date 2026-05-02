from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from contextlib import contextmanager
import sqlite3
import os


app = FastAPI()

# Allow all origins — fine for a single-user home server.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# data can live in /data folder
DATA_DIR = "./data"
DB_PATH = os.path.join(DATA_DIR, "life.db")


os.makedirs(DATA_DIR, exist_ok=True)

# this library/code just helps safely open and close
# databse connection with BETTER syntax 
@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


  # --- Database schema setup ---
# Creates the tables the first time the app runs. After that the IF NOT EXISTS makes it a no-op.
def init_db():
    with get_db() as conn:
        # executescript lets us run multiple SQL statements separated by semicolons in one call.
        conn.executescript("""
            -- Table for body weight entries
            CREATE TABLE IF NOT EXISTS weight (
                id INTEGER PRIMARY KEY AUTOINCREMENT,   -- auto-incrementing unique row ID
                weight REAL NOT NULL,                   -- weight value (REAL = float)
                date TEXT NOT NULL,                     -- date as YYYY-MM-DD string
                timestamp TEXT NOT NULL                 -- full ISO timestamp for precise ordering
            );

            -- Table for individual gym sets
            CREATE TABLE IF NOT EXISTS gym_set (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exercise TEXT NOT NULL,                 -- normalized exercise name, e.g. "bench press"
                weight REAL NOT NULL,                   -- weight lifted in this set
                reps INTEGER NOT NULL,                  -- number of reps in this set
                date TEXT NOT NULL,
                timestamp TEXT NOT NULL
            );

            -- Indexes make WHERE/ORDER BY queries on these columns much faster as data grows.
            CREATE INDEX IF NOT EXISTS idx_gym_exercise ON gym_set(exercise);
            CREATE INDEX IF NOT EXISTS idx_gym_date ON gym_set(date);
            CREATE INDEX IF NOT EXISTS idx_weight_date ON weight(date);
        """)


# Run the schema setup as soon as the module is imported (i.e. when the server starts).
init_db()


# --- Request body models ---
# Pydantic models define the shape of incoming JSON. FastAPI auto-validates against these.

class WeightEntry(BaseModel):
    weight: float                              # required: the weight to log
    date: str | None = None                    # optional: defaults to today if not provided


class GymSet(BaseModel):
    exercise: str                              # required: name of the exercise
    weight: float                              # required: weight used for this set
    reps: int                                  # required: number of reps completed
    date: str | None = None                    # optional: defaults to today


# --- Weight endpoints ---

# POST endpoint to add a weight entry. The `entry` argument is auto-parsed from the request JSON.
@app.post("/add_weight")
async def add_weight(entry: WeightEntry):
    # Use today's date if the caller didn't provide one.
    date = entry.date or datetime.now().strftime("%Y-%m-%d")

    # Full ISO timestamp (e.g. "2026-05-02T00:14:23.123456") for precise sorting.
    timestamp = datetime.now().isoformat()

    with get_db() as conn:
        # Parameterized query — the ? placeholders prevent SQL injection by escaping values safely.
        conn.execute(
            "INSERT INTO weight (weight, date, timestamp) VALUES (?, ?, ?)",
            (entry.weight, date, timestamp),
        )

    # Return a JSON response confirming the insert. FastAPI auto-converts dicts to JSON.
    return {"status": "success", "logged": entry}


# GET endpoint to fetch every weight entry, newest first.
@app.get("/weights")
async def get_weights():
    with get_db() as conn:
        # ORDER BY timestamp DESC = most recent entries first.
        rows = conn.execute(
            "SELECT * FROM weight ORDER BY timestamp DESC"
        ).fetchall()

    # sqlite3.Row objects aren't directly JSON serializable, so convert each to a plain dict.
    return [dict(row) for row in rows]


# --- Gym endpoints ---

# POST endpoint to log a single set.
@app.post("/add_set")
async def add_set(entry: GymSet):
    date = entry.date or datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.now().isoformat()

    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO gym_set (exercise, weight, reps, date, timestamp)
            VALUES (?, ?, ?, ?, ?)
            """,
            # .lower().strip() normalizes "Bench Press " and "bench press" to the same key.
            (entry.exercise.lower().strip(), entry.weight, entry.reps, date, timestamp),
        )

    return {"status": "success", "logged": entry}


# GET endpoint to fetch sets, optionally filtered by exercise name (e.g. /sets?exercise=bench press).
@app.get("/sets")
async def get_sets(exercise: str | None = None):
    with get_db() as conn:
        if exercise:
            # If a filter was provided, only return matching rows.
            rows = conn.execute(
                "SELECT * FROM gym_set WHERE exercise = ? ORDER BY timestamp DESC",
                (exercise.lower().strip(),),
            ).fetchall()
        else:
            # No filter — return everything.
            rows = conn.execute(
                "SELECT * FROM gym_set ORDER BY timestamp DESC"
            ).fetchall()

    return [dict(row) for row in rows]