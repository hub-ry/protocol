import os
from contextlib import asynccontextmanager
from datetime import datetime

import psycopg
from psycopg.rows import dict_row
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


# Read connection string from the environment.
# The default works if you run `docker compose up db` and start the server locally.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://protocol:protocol@localhost:5432/protocol",
)


# --- Database schema ---

async def init_db():
    # autocommit=True is used here so DDL statements (CREATE TABLE, CREATE INDEX)
    # run immediately without being wrapped in a transaction.
    # In PostgreSQL, DDL *can* run inside transactions, but autocommit keeps this simpler.
    async with await psycopg.AsyncConnection.connect(DATABASE_URL, autocommit=True) as conn:
        # Bodyweight log. One row per weigh-in.
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS weight (
                id        SERIAL    PRIMARY KEY,
                weight    REAL      NOT NULL,
                date      DATE      NOT NULL,
                timestamp TIMESTAMP NOT NULL
            )
        """)
        # Lift log. One row per top-set entry.
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS lift (
                id        SERIAL    PRIMARY KEY,
                exercise  TEXT      NOT NULL,
                weight    REAL      NOT NULL,
                date      DATE      NOT NULL,
                timestamp TIMESTAMP NOT NULL
            )
        """)
        # Indexes speed up the common query patterns.
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_weight_date ON weight(date)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_lift_exercise ON lift(exercise)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_lift_date ON lift(date)")


# --- Lifespan ---

# FastAPI's lifespan replaces the old @app.on_event("startup") pattern.
# Everything before `yield` runs when the server starts; after yield runs on shutdown.
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


# --- App setup ---

app = FastAPI(lifespan=lifespan)

# Allow all origins — fine for a single-user home server behind Tailscale.
# If this ever goes public, change allow_origins to your specific IP or domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- DB connection helper ---

# asynccontextmanager turns this into a reusable async context manager.
# Usage:
#   async with get_db() as conn:
#       await conn.execute(...)
# The connection commits on clean exit and rolls back automatically on error.
@asynccontextmanager
async def get_db():
    # row_factory=dict_row makes rows come back as plain dicts:
    # {"weight": 185.4, "date": "2025-08-26"} instead of a tuple (185.4, "2025-08-26")
    async with await psycopg.AsyncConnection.connect(
        DATABASE_URL, row_factory=dict_row
    ) as conn:
        yield conn


# --- Request body models ---

# Pydantic models define what JSON the API accepts.
# FastAPI validates automatically — bad input returns a 422 before our code runs.

class WeightEntry(BaseModel):
    weight: float
    date: str | None = None  # optional: defaults to today if omitted


class Lift(BaseModel):
    weight: float
    date: str | None = None  # optional: defaults to today if omitted


# --- Weight endpoints ---

# Log a bodyweight entry. Called from iOS Shortcuts via Tailscale.
# Example body: {"weight": 185.4}
@app.post("/add_weight")
async def add_weight(entry: WeightEntry):
    date = entry.date or datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.now()

    async with get_db() as conn:
        # %s is psycopg's placeholder — values are escaped automatically,
        # which prevents SQL injection attacks.
        await conn.execute(
            "INSERT INTO weight (weight, date, timestamp) VALUES (%s, %s, %s)",
            (entry.weight, date, timestamp),
        )

    return {"status": "success", "logged": entry}


# Fetch every bodyweight entry, newest first.
@app.get("/weights")
async def get_weights():
    async with get_db() as conn:
        cur = await conn.execute(
            # date::text casts PostgreSQL's DATE type to a "YYYY-MM-DD" string,
            # which is the format the frontend chart already expects.
            "SELECT id, weight, date::text AS date, timestamp FROM weight ORDER BY timestamp DESC"
        )
        rows = await cur.fetchall()

    # Each row is already a dict (from dict_row). FastAPI serializes the list to JSON.
    return rows


# --- Lift endpoints ---

# Log a lift. Exercise name is in the URL so iOS Shortcuts can hardcode one shortcut
# per exercise and only prompt for the weight number.
# Example: POST /lift/bench  with body {"weight": 225}
@app.post("/lift/{exercise}")
async def add_lift(exercise: str, lift: Lift):
    date = lift.date or datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.now()
    # .lower().strip() normalizes "Bench " and "bench" to the same key.
    name = exercise.lower().strip()

    async with get_db() as conn:
        await conn.execute(
            "INSERT INTO lift (exercise, weight, date, timestamp) VALUES (%s, %s, %s, %s)",
            (name, lift.weight, date, timestamp),
        )

    return {"status": "success", "exercise": name, "weight": lift.weight}


# Fetch lifts, newest first. Add ?exercise=bench to filter by movement.
@app.get("/lifts")
async def get_lifts(exercise: str | None = None):
    async with get_db() as conn:
        if exercise:
            cur = await conn.execute(
                "SELECT id, exercise, weight, date::text AS date, timestamp "
                "FROM lift WHERE exercise = %s ORDER BY timestamp DESC",
                (exercise.lower().strip(),),
            )
        else:
            cur = await conn.execute(
                "SELECT id, exercise, weight, date::text AS date, timestamp "
                "FROM lift ORDER BY timestamp DESC"
            )
        rows = await cur.fetchall()

    return rows
