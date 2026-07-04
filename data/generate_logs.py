import json
import random
import time

# Simulates realistic infra metrics with gradual trends instead of pure randomness
SERVERS = ["db-server-1", "app-server-2", "edge-server-3"]

# Each server has a baseline and a "drift" pattern to mimic real degradation
BASELINES = {
    "db-server-1": {"cpu": 40, "mem": 45, "disk_io": 150, "temp": 55, "drift": "disk"},
    "app-server-2": {"cpu": 35, "mem": 50, "disk_io": 100, "temp": 50, "drift": "mem"},
    "edge-server-3": {"cpu": 30, "mem": 40, "disk_io": 80, "temp": 60, "drift": "temp"},
}

# Tracks how many times each server has been queried, to simulate gradual drift over time
_call_count = {s: 0 for s in SERVERS}


def get_metrics(server_id: str) -> dict:
    if server_id not in BASELINES:
        server_id = random.choice(SERVERS)

    base = BASELINES[server_id]
    _call_count[server_id] += 1
    step = _call_count[server_id]

    # Small random noise around baseline for realism
    cpu = base["cpu"] + random.randint(-5, 5)
    mem = base["mem"] + random.randint(-5, 5)
    disk_io = base["disk_io"] + random.randint(-20, 20)
    temp = base["temp"] + random.randint(-3, 3)

    # Apply gradual drift on the server's designated weak point, capped at realistic max
    if base["drift"] == "disk":
        disk_io = min(base["disk_io"] + step * 40, 950)
    elif base["drift"] == "mem":
        mem = min(base["mem"] + step * 5, 95)
    elif base["drift"] == "temp":
        temp = min(base["temp"] + step * 3, 90)

    return {
        "server_id": server_id,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "cpu_percent": cpu,
        "memory_percent": mem,
        "disk_io_mbps": disk_io,
        "temp_celsius": temp,
    }


def reset_drift(server_id: str = None):
    # Resets drift counters, e.g. after a simulated fix has been "applied"
    if server_id:
        _call_count[server_id] = 0
    else:
        for s in SERVERS:
            _call_count[s] = 0


if __name__ == "__main__":
    # Quick manual test: print a few readings to see the drift pattern
    for server in SERVERS:
        print(json.dumps(get_metrics(server), indent=2))