"""Download the raw corpus described in config/sources.yaml into data/raw/.

Usage:
    python scripts/download_sources.py            # download whatever is missing
    python scripts/download_sources.py --force    # re-download everything

Writes data/raw/manifest.json, which records url, sha256, size, Last-Modified
and retrieval time for each file. That gives you provenance for citations, and
lets you diff the manifest to see when CRA or Justice updates a source.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import requests
import yaml

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
CONFIG = ROOT / "config" / "sources.yaml"
HEADERS = {"User-Agent": "taxrag-research-downloader/0.1"}
DELAY_S = 0.5  # be polite to government servers

FOLIO_CHAPTER_RE = re.compile(r'href="([^"]*income-tax-folio-s(\d)-f\d+-c\d+[^"]*\.html)"')
FOLIO_PAGE_RE = re.compile(r'href="([^"]*/income-tax-folios-index/series-(\d)-[^"]*\.html)"')


def fetch(url: str) -> requests.Response:
    r = requests.get(url, headers=HEADERS, timeout=60)
    time.sleep(DELAY_S)
    return r


def save(url: str, rel_out: str, manifest: dict, force: bool, **meta) -> bool:
    out = RAW / rel_out
    if out.exists() and not force and rel_out in manifest:
        print(f"  skip  {rel_out}")
        return True
    r = fetch(url)
    ctype = r.headers.get("Content-Type", "")
    # canada.ca serves an HTML 404 page for missing PDFs, so check status and type
    if r.status_code != 200 or (rel_out.endswith(".pdf") and "pdf" not in ctype):
        print(f"  MISS  {r.status_code} {url}")
        return False
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(r.content)
    manifest[rel_out] = {
        "url": url,
        "sha256": hashlib.sha256(r.content).hexdigest(),
        "bytes": len(r.content),
        "last_modified": r.headers.get("Last-Modified"),
        "retrieved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        **meta,
    }
    print(f"  ok    {rel_out} ({len(r.content) / 1e6:.2f} MB)")
    return True


def crawl_folios(cfg: dict, manifest: dict, force: bool) -> list[str]:
    missing = []
    index_html = fetch(cfg["index_url"]).text
    folio_pages = sorted({
        urljoin(cfg["index_url"], href)
        for href, series in FOLIO_PAGE_RE.findall(index_html)
        if int(series) in cfg["include_series"]
    })
    chapters: dict[str, int] = {}
    for page in folio_pages:
        html = fetch(page).text
        for href, series in FOLIO_CHAPTER_RE.findall(html):
            if int(series) in cfg["include_series"]:
                chapters[urljoin(page, href)] = int(series)
    print(f"  found {len(chapters)} folio chapters across {len(folio_pages)} folio pages")
    for url, series in sorted(chapters.items()):
        name = url.rsplit("/", 1)[-1]
        if not save(url, f"folios/series-{series}/{name}", manifest, force,
                    source_type="folio", series=series):
            missing.append(url)
    return missing


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    cfg = yaml.safe_load(CONFIG.read_text())
    manifest_path = RAW / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    missing: list[str] = []

    try:
        print("Legislation")
        for s in cfg["legislation"]:
            if not save(s["url"], s["out"], manifest, args.force,
                        source_type="legislation", id=s["id"], title=s["title"]):
                missing.append(s["id"])

        print("CRA guides")
        for g in cfg["guides"]:
            for url in g["urls"]:
                if save(url, f"guides/{url.rsplit('/', 1)[-1]}", manifest, args.force,
                        source_type="guide", id=g["id"], title=g["title"]):
                    break
            else:
                missing.append(g["id"])

        print("Reference pages")
        for p in cfg["reference_pages"]:
            if not save(p["url"], f"reference/{p['id']}.html", manifest, args.force,
                        source_type="reference", id=p["id"], title=p["title"]):
                missing.append(p["id"])

        print("Income Tax Folios")
        missing += crawl_folios(cfg["folios"], manifest, args.force)
    finally:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True))

    print(f"\n{len(manifest)} files in manifest; {len(missing)} missing: {missing or '-'}")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
