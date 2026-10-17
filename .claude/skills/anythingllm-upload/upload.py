"""Upload Markdown notes to a local AnythingLLM instance without creating duplicates.

  python upload.py list                      # workspaces: slug | name | doc count
  python upload.py create "Name"             # create workspace, print its slug
  python upload.py upload <slug> <files...>  # upload (or reuse) + embed into workspace

Config: ~/.anythingllm.json  {"url": "http://localhost:8085", "api_key": "..."}
Env vars ANYTHINGLLM_URL / ANYTHINGLLM_API_KEY override it.
"""
import json, os, sys, warnings
from datetime import datetime, timezone
from pathlib import Path

warnings.filterwarnings("ignore")  # requests' urllib3/chardet version nag
import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")  # Windows console is cp1252; titles are Chinese

CONFIG = Path.home() / ".anythingllm.json"
cfg = json.loads(CONFIG.read_text()) if CONFIG.exists() else {}
URL = os.environ.get("ANYTHINGLLM_URL") or cfg.get("url")
KEY = os.environ.get("ANYTHINGLLM_API_KEY") or cfg.get("api_key")
if not (URL and KEY):
    sys.exit(f'Missing url/api_key. Create {CONFIG} with {{"url": "http://host:port", "api_key": "..."}}')
BASE = URL.rstrip("/") + "/api/v1"
H = {"Authorization": f"Bearer {KEY}"}


def api(method, path, **kw):
    r = requests.request(method, BASE + path, headers=H, timeout=300, **kw)
    if not r.ok:
        sys.exit(f"{method} {path} -> HTTP {r.status_code}: {r.text[:300]}")
    return r.json()


def workspaces():
    return api("GET", "/workspaces")["workspaces"]


def stored_docs():
    """title -> [(location, published datetime or None)] for every document in storage."""
    out = {}
    def walk(node, folder=""):
        for item in node.get("items", []):
            if "items" in item:
                walk(item, item["name"])
            else:
                try:
                    pub = datetime.strptime(item.get("published", ""), "%m/%d/%Y, %I:%M:%S %p")
                except ValueError:
                    pub = None
                out.setdefault(item.get("title"), []).append((f"{folder}/{item['name']}", pub))
    walk(api("GET", "/documents")["localFiles"])
    return out


def upload(slug, files):
    # Exact slug lookup: slugs are lowercase and case-sensitive; a wrong slug returns {"workspace": []}.
    ws = api("GET", f"/workspace/{slug}")["workspace"]
    if not ws:
        sys.exit(f"No workspace with slug {slug!r}. Run: python upload.py list")
    in_ws = {d["docpath"] for d in ws[0]["documents"]}
    stored = stored_docs()
    adds, deletes = [], []
    for f in map(Path, files):
        copies = sorted(stored.get(f.name, []), key=lambda c: c[1] or datetime.min)
        # "published" is the server's UTC wall clock (Docker default TZ), second precision.
        mtime = datetime.fromtimestamp(int(f.stat().st_mtime), timezone.utc).replace(tzinfo=None)
        newest = copies[-1] if copies else None
        if newest and newest[1] and newest[1] >= mtime:
            loc, status = newest[0], "reused stored copy"
        else:
            with f.open("rb") as fh:
                res = api("POST", "/document/upload", files={"file": (f.name, fh, "text/markdown")})
            if not res.get("success") or not res.get("documents"):
                print(f"FAILED  {f.name}: {res.get('error')}")
                continue
            loc, status = res["documents"][0]["location"], "uploaded"
            deletes += [c[0] for c in copies if c[0] in in_ws]  # swap stale copy out of this workspace
        if loc in in_ws:
            print(f"SKIP    {f.name}: already in {slug}")
        else:
            adds.append(loc)
            print(f"ADD     {f.name}: {status}")
    if adds or deletes:
        api("POST", f"/workspace/{slug}/update-embeddings", json={"adds": adds, "deletes": deletes})
    print(f"done: {len(adds)} added, {len(deletes)} stale removed from {slug}")


if __name__ == "__main__":
    cmd, *args = sys.argv[1:] or ["list"]
    if cmd == "list":
        for w in workspaces():
            n = len(api("GET", f"/workspace/{w['slug']}")["workspace"][0]["documents"])
            print(f"{w['slug']} | {w['name']} | {n} docs")
    elif cmd == "create":
        print(api("POST", "/workspace/new", json={"name": args[0]})["workspace"]["slug"])
    elif cmd == "upload":
        upload(args[0], args[1:])
    else:
        sys.exit(__doc__)
