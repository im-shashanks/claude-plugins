#!/usr/bin/env python3
"""Shaktra HTML review server.

Serves a single annotatable HTML review document on 127.0.0.1, persists
annotations to JSON, and exits when the reviewer clicks "Review Complete".

Usage:
    python3 review_server.py <doc.html> [--annotations PATH] [--port N]

Prints the review URL to stdout, then blocks until the reviewer completes
the review. The process exiting is the completion signal: launch this in a
background Bash task and read the annotations file when it exits.

Endpoints (all scoped under a random URL token):
    GET    /<token>/                        the review document
    GET    /<token>/api/annotations         current annotations JSON
    POST   /<token>/api/annotations         append one annotation
    DELETE /<token>/api/annotations/<id>    remove one annotation
    POST   /<token>/api/complete            write .complete flag and exit
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import sys
import tempfile
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

MAX_BODY_BYTES = 64 * 1024
ANNOTATION_FIELDS = {"type", "section_id", "quote", "text", "question_id"}
ANNOTATION_TYPES = {"annotation", "question_response"}


def atomic_write_json(path: Path, data: dict) -> None:
    """Write JSON via tmp file + rename so readers never see a torn file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


class ReviewState:
    """Annotation store backed by a JSON file, guarded by a lock."""

    def __init__(self, doc_path: Path, annotations_path: Path):
        self.doc_path = doc_path
        self.annotations_path = annotations_path
        self.complete_path = annotations_path.with_name(
            annotations_path.name.replace(".annotations.json", "") + ".complete"
        )
        self.lock = threading.Lock()
        self.data = self._load()

    def _load(self) -> dict:
        if self.annotations_path.exists():
            with open(self.annotations_path, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and isinstance(data.get("annotations"), list):
                return data
        return {"doc": self.doc_path.name, "complete": False, "annotations": []}

    def add(self, fields: dict) -> dict:
        with self.lock:
            entry = {
                "id": f"a{len(self.data['annotations']) + 1}-{secrets.token_hex(3)}",
                "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }
            entry.update({k: fields.get(k) for k in ANNOTATION_FIELDS})
            self.data["annotations"].append(entry)
            atomic_write_json(self.annotations_path, self.data)
            return entry

    def delete(self, annotation_id: str) -> bool:
        with self.lock:
            before = len(self.data["annotations"])
            self.data["annotations"] = [
                a for a in self.data["annotations"] if a.get("id") != annotation_id
            ]
            if len(self.data["annotations"]) == before:
                return False
            atomic_write_json(self.annotations_path, self.data)
            return True

    def mark_complete(self) -> None:
        with self.lock:
            self.data["complete"] = True
            atomic_write_json(self.annotations_path, self.data)
            self.complete_path.parent.mkdir(parents=True, exist_ok=True)
            self.complete_path.write_text(
                datetime.now(timezone.utc).isoformat(timespec="seconds") + "\n",
                encoding="utf-8",
            )


class ReviewHandler(BaseHTTPRequestHandler):
    state: ReviewState
    token: str
    server_ref: ThreadingHTTPServer

    def log_message(self, *args):  # keep stdout clean — URL only
        pass

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, status: int, obj: dict) -> None:
        self._send(status, json.dumps(obj).encode(), "application/json; charset=utf-8")

    def _route(self) -> str | None:
        """Strip the token prefix; return the sub-path or None if bad token."""
        prefix = f"/{self.token}"
        path = self.path.split("?", 1)[0]
        if path == prefix or path.startswith(prefix + "/"):
            return path[len(prefix):] or "/"
        return None

    def _read_body(self) -> dict | None:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0 or length > MAX_BODY_BYTES:
            return None
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return None

    def do_GET(self):
        route = self._route()
        if route is None:
            return self._send_json(404, {"error": "not found"})
        if route == "/":
            body = self.state.doc_path.read_bytes()
            return self._send(200, body, "text/html; charset=utf-8")
        if route == "/api/annotations":
            with self.state.lock:
                return self._send_json(200, self.state.data)
        return self._send_json(404, {"error": "not found"})

    def do_POST(self):
        route = self._route()
        if route is None:
            return self._send_json(404, {"error": "not found"})
        if route == "/api/annotations":
            body = self._read_body()
            if (
                not isinstance(body, dict)
                or body.get("type") not in ANNOTATION_TYPES
                or not isinstance(body.get("text"), str)
                or not body["text"].strip()
            ):
                return self._send_json(400, {"error": "invalid annotation"})
            entry = self.state.add(body)
            return self._send_json(201, entry)
        if route == "/api/complete":
            self.state.mark_complete()
            self._send_json(200, {"complete": True})
            threading.Thread(target=self.server_ref.shutdown, daemon=True).start()
            return None
        return self._send_json(404, {"error": "not found"})

    def do_DELETE(self):
        route = self._route()
        if route is None or not route.startswith("/api/annotations/"):
            return self._send_json(404, {"error": "not found"})
        annotation_id = route[len("/api/annotations/"):]
        if self.state.delete(annotation_id):
            return self._send_json(200, {"deleted": annotation_id})
        return self._send_json(404, {"error": "unknown annotation id"})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("doc", help="Path to the review HTML document")
    parser.add_argument("--annotations", help="Annotations JSON path (default: .shaktra/reviews/<doc>.annotations.json)")
    parser.add_argument("--port", type=int, default=0, help="Port (default: random free port)")
    args = parser.parse_args()

    doc_path = Path(args.doc).resolve()
    if not doc_path.is_file():
        print(f"error: document not found: {doc_path}", file=sys.stderr)
        return 1

    if args.annotations:
        annotations_path = Path(args.annotations).resolve()
    else:
        annotations_path = (
            Path.cwd() / ".shaktra" / "reviews" / f"{doc_path.stem}.annotations.json"
        )

    token = secrets.token_urlsafe(12)
    state = ReviewState(doc_path, annotations_path)

    handler = type(
        "BoundHandler", (ReviewHandler,), {"state": state, "token": token}
    )
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    handler.server_ref = server

    url = f"http://127.0.0.1:{server.server_address[1]}/{token}/"
    print(f"Review server running: {url}")
    print(f"Annotations: {annotations_path}")
    sys.stdout.flush()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    print(f"Review complete. Annotations saved to {annotations_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
