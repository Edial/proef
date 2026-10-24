#!/usr/bin/env python3
"""Controleert in één keer of foto's en bronlinks van een editie bereikbaar zijn.

Gebruik: python3 scripts/check_photos.py editions/2026-44.json   (exit 1 als een foto niet werkt)
"""
import concurrent.futures as cf
import json
import sys
import urllib.request

UA = "Mozilla/5.0 (Proef link check)"


def probe(url):
    for method in ("HEAD", "GET"):
        try:
            req = urllib.request.Request(url, method=method, headers={"User-Agent": UA, "Range": "bytes=0-1023"})
            with urllib.request.urlopen(req, timeout=20) as res:
                return res.status, res.headers.get("Content-Type", "")
        except Exception as e:  # noqa: BLE001
            err = e
    return None, f"{type(err).__name__}: {err}"[:80]


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    ed = json.load(open(sys.argv[1]))
    checks = []
    for r in ed.get("recipes", []):
        checks.append(("foto", r["slug"], r.get("photo", ""), True))
        for link in r.get("links", []) + ([r["photoCredit"]] if r.get("photoCredit") else []):
            checks.append(("link", r["slug"], link.get("url", ""), False))
    for s in (ed.get("ferment") or {}).get("sources", []):
        checks.append(("bron", "ferment", s.get("url", ""), False))
    bad = 0
    with cf.ThreadPoolExecutor(8) as pool:
        for (kind, slug, url, must_be_image), (status, info) in zip(checks, pool.map(lambda c: probe(c[2]), checks)):
            ok = status is not None and status < 400 and (not must_be_image or info.startswith("image/"))
            if not ok:
                bad += kind == "foto"
                print(f"FOUT  {kind:4} {slug}: {url} -> {status or ''} {info}")
    print(f"{len(checks)} links gecontroleerd, {bad} foto('s) werken niet.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
