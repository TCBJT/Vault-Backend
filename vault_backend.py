# =====================================================
# ASHEN-VAULT244466666 — vault_backend.py
# Runs on Render. Receives live stats from ProBook,
# serves them to the website.
# =====================================================

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os, time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

VAULT_SECRET = os.environ.get("VAULT_SECRET", "")

# In-memory store
latest_stats = {
    "cpu":              0,
    "ram":              0,
    "ram_total_gb":     0,
    "storage":          0,
    "storage_total_gb": 0,
    "uptime_seconds":   0,
    "net_sent_mb":      0,
    "net_recv_mb":      0,
    "net_io_pct":       0,
    "disk_io_pct":      0,
    "process_pct":      0,
    "process_count":    0,
    "online":           False,
    "last_seen":        None,
}

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
    net_io_pct:       float
    disk_io_pct:      float
    process_pct:      float
    process_count:    int

@app.post("/push")
def push_stats(payload: StatsPayload):
    if not VAULT_SECRET or payload.secret != VAULT_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret key.")

    latest_stats.update({
        "cpu":              round(payload.cpu),
        "ram":              round(payload.ram),
        "ram_total_gb":     payload.ram_total_gb,
        "storage":          round(payload.storage),
        "storage_total_gb": payload.storage_total_gb,
        "uptime_seconds":   payload.uptime_seconds,
        "net_sent_mb":      payload.net_sent_mb,
        "net_recv_mb":      payload.net_recv_mb,
        "net_io_pct":       payload.net_io_pct,
        "disk_io_pct":      payload.disk_io_pct,
        "process_pct":      payload.process_pct,
        "process_count":    payload.process_count,
        "online":           True,
        "last_seen":        time.time(),
    })
    return {"status": "ok"}

@app.get("/stats")
def get_stats():
    if latest_stats["last_seen"] is None:
        latest_stats["online"] = False
    elif time.time() - latest_stats["last_seen"] > 10:
        latest_stats["online"] = False
    return latest_stats

@app.get("/")
def root():
    return {"status": "ASHEN-VAULT backend online"}
