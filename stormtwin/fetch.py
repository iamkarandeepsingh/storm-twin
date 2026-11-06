"""Download every API entity into data/raw/<Entity>.json (stdlib only, paginated).

Run on a machine that can reach the API:
    export FLEET_API_KEY=...   (PowerShell: $env:FLEET_API_KEY="...")
    python -m stormtwin fetch
"""
import json
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def _get(url, key, retries=3):
    req = urllib.request.Request(url, headers={"X-Api-Key": key, "Accept": "application/json"})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (400, 401, 404):
                raise SystemExit(f"HTTP {e.code} for {url.split('?')[0]}: {e.read()[:200]!r}")
            if attempt == retries - 1:
                raise
        except urllib.error.URLError:
            if attempt == retries - 1:
                raise
        time.sleep(2 * (attempt + 1))


def fetch_entity(base, key, entity, page_size):
    rows, cursor = [], None
    while True:
        params = {"resultsLimit": page_size}
        if cursor:
            params["cursor"] = cursor
        page = _get(f"{base}/{entity}?{urllib.parse.urlencode(params)}", key)
        rows.extend(page.get("data", []))
        cursor = page.get("next")
        if not cursor:
            return rows


def run(cfg, root):
    key = os.environ.get(cfg["api_key_env"])
    if not key:
        raise SystemExit(f"Set the {cfg['api_key_env']} environment variable first.")
    out = root / cfg["raw_dir"]
    out.mkdir(parents=True, exist_ok=True)
    manifest = {"fetched_at_utc": datetime.now(timezone.utc).isoformat(), "base_url": cfg["api_base_url"], "counts": {}}
    for entity in cfg["entities"]:
        rows = fetch_entity(cfg["api_base_url"], key, entity, cfg["page_size"])
        (out / f"{entity}.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
        manifest["counts"][entity] = len(rows)
        print(f"{entity:20s} {len(rows):6d}")
    (out / "_manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print(f"Saved to {out}")
