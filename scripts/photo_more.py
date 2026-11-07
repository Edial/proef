#!/usr/bin/env python3
"""Zoekt per recept de andere foto's van hetzelfde gerecht op de bronpagina en zet ze in `photos` in de editie:
[{"url": "…", "w": 1200, "h": 1800, "thumb": "…-150x150.jpg"}, …]. De receptpagina toont ze als kleine reeks onder de hoofdfoto. De hoofdfoto
(`photo`) blijft altijd de foto van het gerecht als het af is; die wordt hier nooit vervangen.

Zo kiezen we (alleen WordPress-sites, de meeste blogs):
- alleen foto's uit de uploadmap van de bron met dezelfde naam als de hoofdfoto (tom-yum-noodle-soup-5.jpg bij
  tom-yum-noodle-soup-11.jpg), in de volgorde van de pagina: meestal eerst de stappen, dan het eindresultaat;
- geen Pinterest-plaatjes en geen dubbele (dezelfde foto in een andere maat);
- elke foto wordt opgehaald zoals een lezer van Proef dat doet (met Referer); wat de bron weigert, valt af;
- heeft de bron geen kleine versie, dan laadt het voorbeeldje het origineel: alleen als dat onder 200 KB blijft.
Voor de kleine reeks zoeken we de vierkante WordPress-maat (-150x150) of een andere kleine maat van de bron.
Het blijven bestanden van de bron (geen kopie, zie REDACTIE.md). Hooguit MAX foto's per recept.

Gebruik: python3 scripts/photo_more.py editions/2026-45.json   (vereist Pillow)
"""
import concurrent.futures as cf
import html
import io
import json
import re
import sys
import urllib.request

from PIL import Image

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 Chrome/126 Safari/537.36"
REFERER = "https://edial.github.io/proef/"
MAX = 6
MIN_W = 500
MAX_BYTES = 200_000   # zonder kleine versie laadt het voorbeeldje het origineel; daarboven slaan we de foto over
SKIP = re.compile(r"pin(terest)?\b|-pin\d*\.|collage|ebook|logo|avatar|author", re.I)
IMG = re.compile(r"https?://[^\s\"'<>()]+?/wp-content/uploads/[^\s\"'<>()]+?\.(?:jpe?g|png|webp)", re.I)


def fetch(url, limit=6_000_000):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": REFERER, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.headers.get("Content-Type", ""), r.read(limit)


def base(url):
    """Naam zonder maat en zonder volgnummer: …/tom-yum-noodle-soup-11-768x512.jpg → tom-yum-noodle-soup."""
    name = url.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    name = re.sub(r"(-\d+x\d+|-scaled|-e\d{10,})+$", "", name)
    name = re.sub(r"([-_](\d+[a-z]?|[ivx]+|w\d+))+$", "", name, flags=re.I)
    return name.lower().rstrip("s")


def original(url):
    """De volle versie van een WordPress-upload (zonder -768x512), via de eigen domeinnaam van de hoofdfoto."""
    return re.sub(r"(-\d+x\d+|-scaled)(?=\.\w+$)", "", url)


def size_of(url):
    """(breedte, hoogte, bytes) van een afbeelding, of None als hij niet bestaat of geen afbeelding is."""
    try:
        ctype, data = fetch(url, 20_000_000)
        if not ctype.startswith("image/"):
            return None
        return (*Image.open(io.BytesIO(data)).size, len(data))
    except Exception:  # noqa: BLE001
        return None


def thumb(url, size, page):
    """De kleinste versie van dezelfde foto op de bron (vierkant 150x150 als die er is, anders tot 640 breed), of None."""
    stem, ext = url.rsplit(".", 1)
    name = re.escape(stem.rsplit("/", 1)[-1])
    seen = {(int(a), int(b)) for a, b in re.findall(r"/" + name + r"-(\d+)x(\d+)\." + re.escape(ext), page)}
    cands = [(150, 150)] + sorted(c for c in seen if 120 <= c[0] <= 640 and c != (150, 150))
    if size:
        cands.append((300, round(300 * size[1] / size[0])))
    for w, h in dict.fromkeys(cands):
        u = f"{stem}-{w}x{h}.{ext}"
        if size_of(u):
            return u
    return None


def more(r):
    hero, page_url = r.get("photo") or "", (r.get("photoCredit") or {}).get("url")
    if "/wp-content/uploads/" not in hero or not page_url:
        return None, "geen WordPress-foto"
    try:
        page = html.unescape(fetch(page_url, 4_000_000)[1].decode("utf-8", "replace"))
    except Exception as e:  # noqa: BLE001
        return None, f"pagina niet bereikbaar ({type(e).__name__})"
    # vanaf de body: de kop van de pagina (preload, og:image) noemt dezelfde foto's in een andere volgorde
    start = max(page.find("</head>"), 0)
    want, host = base(hero), hero.split("/wp-content/uploads/")[0]
    stem = lambda u: original(u).rsplit("/", 1)[-1].rsplit(".", 1)[0].lower()   # zelfde foto als .jpg en .webp
    seen, cands = {stem(hero)}, []
    for u in IMG.findall(page[start:]) or IMG.findall(page):
        name = original(u).rsplit("/", 1)[-1]
        if SKIP.search(name) or not base(u).startswith(want[: max(8, int(len(want) * .8))]) or stem(u) in seen:
            continue
        seen.add(stem(u))
        cands.append(host + "/wp-content/uploads/" + original(u).split("/wp-content/uploads/", 1)[1])
    with cf.ThreadPoolExecutor(6) as pool:
        sizes = list(pool.map(size_of, cands[: MAX * 2]))
    found = [({"url": u, "w": s[0], "h": s[1]}, s[2]) for u, s in zip(cands, sizes) if s and s[0] >= MIN_W]
    with cf.ThreadPoolExecutor(6) as pool:
        thumbs = list(pool.map(lambda x: thumb(x[0]["url"], (x[0]["w"], x[0]["h"]), page), found))
    out = []
    for (p, size), t in zip(found, thumbs):
        if t:
            p["thumb"] = t
        elif size > MAX_BYTES:   # geen kleine versie en zwaar: als voorbeeldje te traag, dus niet tonen
            continue
        out.append(p)
    return out[:MAX] or None, f"{len(cands)} kandidaten"


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    path = sys.argv[1]
    ed = json.load(open(path))
    with cf.ThreadPoolExecutor(4) as pool:
        res = list(pool.map(more, ed["recipes"]))
    for r, (photos, why) in zip(ed["recipes"], res):
        if photos:
            r["photos"] = photos
            print(f"{r['slug'][:34]:34} {len(photos)} extra foto's")
        else:
            r.pop("photos", None)
            print(f"{r['slug'][:34]:34} geen extra foto's ({why})")
    with open(path, "w") as f:
        json.dump(ed, f, ensure_ascii=False, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
