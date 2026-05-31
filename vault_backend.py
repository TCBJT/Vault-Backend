# =====================================================
# ASHEN-VAULT244466666 — vault_backend.py
# Runs on Render. Receives live stats from ProBook,
# serves them to the website.
# =====================================================

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os, time

app = FastAPI()

# Allow the website to fetch stats from anywhere
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# -------------------------------------------------------
# Secret key — set this as an environment variable on
# Render called VAULT_SECRET. Your ProBook sends it with
# every push. If it doesn't match, data is rejected.
# -------------------------------------------------------
VAULT_SECRET = os.environ.get("VAULT_SECRET", "")

# In-memory store — holds the latest stats from ProBook
latest_stats = {
    "cpu":              0,
    "ram":              0,
    "ram_total_gb":     0,
    "storage":          0,
    "storage_total_gb": 0,
    "uptime_seconds":   0,
    "net_sent_mb":      0,
    "net_recv_mb":      0,
    "online":           False,
    "last_seen":        None,   # timestamp of last push from ProBook
}

# -------------------------------------------------------
# Data model for incoming stats from ProBook
# -------------------------------------------------------
class StatsPayload(BaseModel):
    secret:           str
    cpu:              float
    ram:              float
    ram_total_gb:     float
    storage:          float
    storage_total_gb: float
    uptime_seconds:   int
    net_sent_mb:      float
    net_recv_mb:      float

# -------------------------------------------------------
# POST /push — ProBook sends stats here every second
# -------------------------------------------------------
@app.post("/push")
def push_stats(payload: StatsPayload):
    # Validate secret key
    if not VAULT_SECRET or payload.secret != VAULT_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret key.")

    # Update in-memory store
    latest_stats.update({
        "cpu":              round(payload.cpu),
        "ram":              round(payload.ram),
        "ram_total_gb":     payload.ram_total_gb,
        "storage":          round(payload.storage),
        "storage_total_gb": payload.storage_total_gb,
        "uptime_seconds":   payload.uptime_seconds,
        "net_sent_mb":      payload.net_sent_mb,
        "net_recv_mb":      payload.net_recv_mb,
        "online":           True,
        "last_seen":        time.time(),
    })

    return {"status": "ok"}

# -------------------------------------------------------
# GET /stats — website fetches stats from here
# -------------------------------------------------------
@app.get("/stats")
def get_stats():
    # Mark offline if ProBook hasn't pushed in 10 seconds
    if latest_stats["last_seen"] is None:
        latest_stats["online"] = False
    elif time.time() - latest_stats["last_seen"] > 10:
        latest_stats["online"] = False

    return latest_stats

# -------------------------------------------------------
# GET / — health check so Render knows it's alive
# -------------------------------------------------------
@app.get("/")
def root():
    return {"status": "ASHEN-VAULT backend online"}
