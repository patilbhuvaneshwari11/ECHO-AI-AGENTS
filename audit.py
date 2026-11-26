import json
import time
from pathlib import Path

LOG_FILE = Path(__file__).resolve().parent / "audit.log"


def log(event, role, details):
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    entry = {"time": now, "event": event, "role": role, "details": details}
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def read_log():
    if not LOG_FILE.exists():
        return []
    with open(LOG_FILE, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]