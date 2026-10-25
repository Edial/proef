#!/usr/bin/env python3
"""Meet hoe licht elke receptfoto is en zet `photoGamma` in de editie, zodat alle foto's even licht ogen.

De site past die gamma toe op de foto (donkere foto's worden lichter, zonder dat het wit dichtloopt).
Gebruik: python3 scripts/photo_light.py editions/2026-44.json   (vereist Pillow: pip install pillow)
"""
import concurrent.futures as cf
import io
import json
import sys
import urllib.request

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow ontbreekt: pip install pillow")

UA = "Mozilla/5.0 (Proef photo check)"
TARGET = 0.68          # gemiddelde helderheid (0 = zwart, 1 = wit) waar elke foto op uitkomt
LO, HI = 0.35, 1.3     # grenzen voor de gamma, zodat niets kapot getrokken wordt


def gamma_for(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    im = Image.open(io.BytesIO(urllib.request.urlopen(req, timeout=30).read())).convert("L")
    im.thumbnail((400, 400))
    hist = im.histogram()
    total = sum(hist)
    mean = lambda g: sum(n * (v / 255) ** g for v, n in enumerate(hist)) / total
    lo, hi = LO, HI  # mean(g) daalt als g stijgt
    for _ in range(30):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if mean(mid) > TARGET else (lo, mid)
    return round((lo + hi) / 2, 2), mean(1)


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    path = sys.argv[1]
    ed = json.load(open(path))
    recipes = [r for r in ed.get("recipes", []) if r.get("photo")]
    with cf.ThreadPoolExecutor(5) as pool:
        results = list(pool.map(lambda r: (r, *_safe(r["photo"])), recipes))
    for r, g, before in results:
        if g is None:
            print(f"FOUT  {r['slug']}: {before}")
            continue
        r["photoGamma"] = g
        print(f"{r['slug']:32} helderheid {before:.2f} -> gamma {g}")
    with open(path, "w") as f:
        json.dump(ed, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return 0


def _safe(url):
    try:
        return gamma_for(url)
    except Exception as e:  # noqa: BLE001
        return None, f"{type(e).__name__}: {e}"[:80]


if __name__ == "__main__":
    sys.exit(main())
