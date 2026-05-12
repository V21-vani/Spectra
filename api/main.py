import asyncio
import csv
import io
import json
import os
import sys
import tempfile
import threading
from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

# Resolve parent src/ package
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.models import TestResult
from src.parser import parse_junit_xml
from src.runner import run_pytest
from src import storage

app = FastAPI(title="Spectra API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for the current session
_results: list[TestResult] = []


# ── Results ───────────────────────────────────────────────────────────────────

@app.get("/api/results")
def get_results():
    return [asdict(r) for r in _results]


@app.post("/api/results")
def add_result(data: dict):
    if any(r.test_file == data.get("test_file") and r.test_name == data.get("test_name")
           for r in _results):
        raise HTTPException(400, "Duplicate: test_file + test_name already exists")
    r = TestResult(
        test_file=data["test_file"],
        test_name=data["test_name"],
        status=data.get("status", "PASSED"),
        duration=float(data.get("duration", 0)),
        coverage=float(data.get("coverage", 0)),
        error_message=data.get("error_message"),
    )
    _results.append(r)
    return asdict(r)


@app.delete("/api/results")
def clear_results():
    _results.clear()
    return {"ok": True}


@app.delete("/api/results/{test_id}")
def delete_result(test_id: str):
    before = len(_results)
    _results[:] = [r for r in _results if r.id != test_id]
    if len(_results) == before:
        raise HTTPException(404, "Test not found")
    return {"ok": True}


# ── Import ────────────────────────────────────────────────────────────────────

@app.post("/api/import/xml")
async def import_xml(file: UploadFile = File(...)):
    content = await file.read()
    fd, tmp = tempfile.mkstemp(suffix=".xml")
    try:
        os.write(fd, content)
        os.close(fd)
        results, err = parse_junit_xml(tmp)
        if err:
            raise HTTPException(400, err)
        _results.clear()
        _results.extend(results)
        return [asdict(r) for r in results]
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


@app.post("/api/import/json")
async def import_json(file: UploadFile = File(...)):
    content = await file.read()
    try:
        data = json.loads(content)
        if not isinstance(data, list):
            raise ValueError("Expected a JSON array")
        loaded = [TestResult(**item) for item in data]
        _results.clear()
        _results.extend(loaded)
        return [asdict(r) for r in loaded]
    except Exception as exc:
        raise HTTPException(400, str(exc))


# ── Export ────────────────────────────────────────────────────────────────────

@app.get("/api/export/csv")
def export_csv():
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["test_file", "test_name", "status", "duration_ms", "coverage_pct", "error"])
    for r in _results:
        w.writerow([r.test_file, r.test_name, r.status,
                    r.duration, r.coverage, r.error_message or ""])
    buf.seek(0)
    return StreamingResponse(
        io.BytesIO(buf.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=spectra_export.csv"},
    )


@app.get("/api/export/json")
def export_json():
    payload = json.dumps([asdict(r) for r in _results], indent=2).encode()
    return StreamingResponse(
        io.BytesIO(payload),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=spectra_export.json"},
    )


# ── Sessions ──────────────────────────────────────────────────────────────────

@app.get("/api/sessions")
def list_sessions():
    return storage.load_sessions()


@app.post("/api/sessions")
def save_session(data: dict):
    name = data.get("name", "Unnamed")
    path = storage.save_session(name, _results)
    return {"ok": True, "path": path}


@app.delete("/api/sessions/{filename}")
def delete_session(filename: str):
    storage.delete_session(filename)
    return {"ok": True}


@app.post("/api/sessions/{filename}/load")
def load_session(filename: str):
    sessions = storage.load_sessions()
    session = next((s for s in sessions if s.get("_file") == filename), None)
    if not session:
        raise HTTPException(404, "Session not found")
    _results.clear()
    _results.extend(storage.results_from_session(session))
    return [asdict(r) for r in _results]


# ── WebSocket: live pytest runner ─────────────────────────────────────────────

@app.websocket("/ws/run")
async def run_ws(ws: WebSocket):
    await ws.accept()
    try:
        data = await ws.receive_json()
    except Exception:
        return

    path = data.get("path", "").strip()
    coverage = bool(data.get("coverage", False))

    if not path or not os.path.exists(path):
        await ws.send_json({"type": "error", "message": f"Path not found: {path!r}"})
        return

    loop = asyncio.get_running_loop()
    queue: asyncio.Queue = asyncio.Queue()

    def on_line(line: str):
        loop.call_soon_threadsafe(queue.put_nowait, {"type": "line", "text": line})

    def worker():
        results, _, err = run_pytest(path, on_line=on_line, coverage=coverage)
        _results.clear()
        _results.extend(results)
        loop.call_soon_threadsafe(queue.put_nowait, {
            "type": "done",
            "results": [asdict(r) for r in results],
            "error": err or "",
        })

    threading.Thread(target=worker, daemon=True).start()

    while True:
        try:
            msg = await asyncio.wait_for(queue.get(), timeout=600.0)
            await ws.send_json(msg)
            if msg["type"] in ("done", "error"):
                break
        except (asyncio.TimeoutError, Exception):
            break


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
