### Vision

#### Palantir-ing Myself
The vision of this application is to track as much data about myself as possible while learning new tech stacks.

#### Data I will collect
Complete:
- Body Weight
- New "Bests" in the Gym

Maybe One Day:
- Sleep
- Basically anything is possible

#### Why this format for a gym app?
The gym app market is very saturated. The idea behind building my own was purely for the excuse to use a dedicated Linux PC, Tailscale, and to get comfortable with real infrastructure.

#### Tech Stack

- **Backend**
  - Python, FastAPI, Pydantic, Uvicorn
  - PostgreSQL 17
  - psycopg (v3) — async PostgreSQL driver

- **Frontend**
  - React 18, Vite
  - Recharts

- **Ops**
  - Docker + Docker Compose
  - nginx (serves the frontend and proxies `/api/*` to the backend)
  - systemd (auto-starts the stack on boot)
  - Tailscale (private network access from phone)
  - Apple Shortcuts (sends weight data to the API)

#### Running it

```bash
# Start everything
docker compose up -d

# Seed historical data (first time only)
docker compose exec app python src/import_weight.py

# Stop everything
docker compose down
```

#### Access

| What | URL |
|---|---|
| Dashboard | http://100.89.197.38 |
| API | http://100.89.197.38:8000 |

#### Logging weight from iPhone (Shortcuts)

- Method: `POST`
- URL: `http://100.89.197.38:8000/add_weight`
- Body: `{"weight": 185.4}`

#### Auto-start on boot

The `protocol.service` systemd unit starts the Docker Compose stack on every boot.
To install it:

```bash
sudo cp protocol.service /etc/systemd/system/protocol.service
sudo systemctl enable --now protocol
```
