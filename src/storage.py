import json
import os
import time
from dataclasses import asdict
from .models import TestResult

_STORAGE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage", "data")


def _ensure():
    os.makedirs(_STORAGE, exist_ok=True)


def save_session(name: str, results: list[TestResult]) -> str:
    _ensure()
    session = {
        "name": name,
        "timestamp": time.time(),
        "results": [asdict(r) for r in results],
    }
    path = os.path.join(_STORAGE, f"{int(time.time_ns())}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(session, f, indent=2)
    return path


def load_sessions() -> list[dict]:
    _ensure()
    sessions = []
    for fn in sorted(os.listdir(_STORAGE), reverse=True):
        if not fn.endswith(".json"):
            continue
        try:
            with open(os.path.join(_STORAGE, fn), encoding="utf-8") as f:
                sessions.append({"_file": fn, **json.load(f)})
        except Exception:
            pass
    return sessions


def delete_session(filename: str) -> None:
    path = os.path.join(_STORAGE, filename)
    if os.path.exists(path):
        os.unlink(path)


def results_from_session(session: dict) -> list[TestResult]:
    return [TestResult(**r) for r in session.get("results", [])]
