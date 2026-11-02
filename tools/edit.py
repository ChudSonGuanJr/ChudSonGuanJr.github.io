"""Temporary local edit mode for the portfolio.

Run:  python tools/edit.py
Opens the editor in your browser. Save writes content/projects.json and rebuilds
the site. The previous version is kept as content/projects.backup.json.
Runs on this computer only and has no effect on the published site until you
commit and push. Press Ctrl+C here to stop it.
"""
import functools
import json
import re
import shutil
import sys
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import build

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content/projects.json"
BACKUP = ROOT / "content/projects.backup.json"
PORT = 8000
ORIGIN = f"http://127.0.0.1:{PORT}"
IMAGE_TYPES = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_UPLOAD = 30 * 1024 * 1024


def content_version():
    return str(CONTENT.stat().st_mtime_ns)


def project_folder(slug):
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", slug or ""):
        raise ValueError("Bad project name")
    return ROOT / "assets/img" / slug


def free_name(folder, name):
    """Returns a safe filename that does not clash with anything in the folder."""
    source = Path(name)
    if source.suffix.lower() not in IMAGE_TYPES:
        raise ValueError("Only jpg, png, webp and gif images can be added")
    stem = re.sub(r"[^a-z0-9-]+", "-", source.stem.lower()).strip("-") or "image"
    candidate = f"{stem}{source.suffix.lower()}"
    number = 2
    while (folder / candidate).exists():
        candidate = f"{stem}-{number}{source.suffix.lower()}"
        number += 1
    return candidate


class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        if not self.path.startswith("/assets/fonts/"):
            self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self):
        if urlparse(self.path).path == "/api/version":
            self.reply(200, {"version": content_version()})
        else:
            super().do_GET()

    def do_POST(self):
        url = urlparse(self.path)
        actions = {"/api/save": self.save, "/api/upload": self.upload, "/api/copy": self.copy}
        if url.path not in actions or self.headers.get("Origin") != ORIGIN:
            self.send_error(403)
            return
        try:
            length = int(self.headers["Content-Length"])
            if length > MAX_UPLOAD:
                raise ValueError("That file is over 30 MB")
            actions[url.path](self.rfile.read(length), parse_qs(url.query))
        except Exception as error:
            self.reply(500, {"error": str(error)})

    def upload(self, body, query):
        folder = project_folder(query["project"][0])
        folder.mkdir(parents=True, exist_ok=True)
        name = free_name(folder, query["name"][0])
        (folder / name).write_bytes(body)
        self.reply(200, {"file": name})

    def copy(self, body, _query):
        request = json.loads(body.decode("utf-8"))
        target = project_folder(request["to"])
        target.mkdir(parents=True, exist_ok=True)
        source = project_folder(request["from"]) / Path(request["file"]).name
        name = free_name(target, source.name)
        shutil.copy2(source, target / name)
        self.reply(200, {"file": name})

    def save(self, body, _query):
        # A tab opened before the latest change would silently undo it.
        if self.headers.get("X-Content-Version") != content_version():
            raise ValueError("this tab is out of date. Reload it and make your change again")
        data = json.loads(body.decode("utf-8"))
        if not data["projects"] or not data["site"]["hero"]:
            raise ValueError("The site needs at least one project and a header image")
        shutil.copy2(CONTENT, BACKUP)
        CONTENT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        try:
            build.main()
        except Exception:
            shutil.copy2(BACKUP, CONTENT)
            build.main()
            raise
        self.reply(200, {"ok": True, "version": content_version()})

    def reply(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


def main():
    handler = functools.partial(Handler, directory=str(ROOT))
    server = ThreadingHTTPServer(("127.0.0.1", PORT), handler)
    url = f"{ORIGIN}/tools/editor.html"
    print(f"Edit mode: {url}\nPress Ctrl+C to stop.")
    if "--no-browser" not in sys.argv:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
