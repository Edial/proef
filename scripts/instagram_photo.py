#!/usr/bin/env python3
"""Haalt voor recepten die van Instagram zelf komen (veld `instagram`, geen `photo`) de afbeelding van de post op
(bij een reel het omslagbeeld) en bewaart die in assets/ig/<code>.jpg. Het adres bij Instagram verloopt na een paar
dagen; daarom staat de foto bij Proef zelf, met de naam van de maker en een link naar de post erbij (photoCredit).
Lukt het niet, dan blijft het recept zonder foto: de site toont dan de post zelf, na een klik.

Gebruik: python3 scripts/instagram_photo.py editions/2026-47.json   (vereist IG_TOKEN, IG_USER_ID en Pillow)
"""
import csv
import io
import json
import pathlib
import sys
import urllib.request

from PIL import Image

import instagram
import instagram_trend

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = "https://edial.github.io/proef/"
OUT = ROOT / "assets" / "ig"
MAX_W = 1200


def handle_for(url):
    """Het account van een post: via data/posts.csv (bron) en data/sources.csv (instagram-handle)."""
    with (ROOT / "data" / "posts.csv").open(newline="") as f:
        source = next((p["source"] for p in csv.DictReader(f) if p["url"] == url or instagram_trend.code(p["url"]) == instagram_trend.code(url)), None)
    with (ROOT / "data" / "sources.csv").open(newline="") as f:
        return next((r["instagram"].strip().lstrip("@") for r in csv.DictReader(f) if r["id"] == source), None)


def main():
    path = pathlib.Path(sys.argv[1])
    ed = json.loads(path.read_text())
    todo = [r for r in ed.get("recipes", []) if r.get("instagram") and not r.get("photo")]
    if todo and not instagram.enabled():
        return print("IG_TOKEN of IG_USER_ID ontbreekt: geen foto's opgehaald.")
    for r in todo:
        code = instagram_trend.code(r["instagram"])
        try:
            handle = handle_for(r["instagram"])
            url, kind = instagram.photo(handle, code) if handle else (None, "account niet gevonden")
            if not url:
                print(f"{r['slug'][:34]:34} geen foto: {kind}")
                continue
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=30) as res:
                img = Image.open(io.BytesIO(res.read())).convert("RGB")
            if img.width > MAX_W:
                img = img.resize((MAX_W, round(img.height * MAX_W / img.width)), Image.LANCZOS)
            OUT.mkdir(parents=True, exist_ok=True)
            img.save(OUT / f"{code}.jpg", quality=82, optimize=True)
            r["photo"] = f"{SITE}assets/ig/{code}.jpg"
            r["photoFrom"] = "instagram"
            print(f"{r['slug'][:34]:34} foto van @{handle} ({kind}, {img.width}×{img.height})")
        except Exception as e:  # noqa: BLE001
            print(f"{r['slug'][:34]:34} geen foto: {type(e).__name__}: {e}"[:150])
    path.write_text(json.dumps(ed, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
