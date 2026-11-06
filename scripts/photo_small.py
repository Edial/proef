#!/usr/bin/env python3
"""Zoekt per receptfoto de officiële kleinere versies op de bronsite en zet `photoSet` in de editie:
[{"w": 768, "url": "…"}, …]. De site kiest daaruit met srcset de maat die past bij het scherm. Zo laadt een
tegel van 400 px niet meer een foto van 4000 px. Het blijven bestanden van de bron (geen kopie, zie REDACTIE.md).

Waar de kleinere versies vandaan komen:
- WordPress maakt bij elke upload vaste maten (naam-768x512.jpg, -1024x…, -1536x…). We rekenen ze uit vanaf de
  maat van het origineel en zoeken ook op de receptpagina naar varianten van dezelfde foto.
- Condé Nast (Bon Appétit, Epicurious): de breedte staat in de url (w_3968,h_2232,c_limit) en is aan te passen.
- Urls met ?w= (Jetpack/Tachyon) idem.
Elke kandidaat wordt opgehaald en gemeten (met Referer van Proef, zoals een bezoeker); alleen wat echt bestaat telt.

Gebruik: python3 scripts/photo_small.py editions/2026-45.json   (vereist Pillow)
"""
import concurrent.futures as cf
import io
import json
import re
import sys
import urllib.parse
import urllib.request

from PIL import Image

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 Chrome/126 Safari/537.36"
REFERER = "https://edial.github.io/proef/"
WANT = (480, 640, 768, 800, 1024, 1200, 1536)   # breedtes die we proberen; de site gebruikt er een paar van
MIN_W, MAX_W = 300, 1700


def fetch(url, limit=6_000_000):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": REFERER, "Accept": "image/avif,image/webp,image/*,*/*"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.headers.get("Content-Type", ""), r.read(limit)


def width_of(url):
    """Breedte van een afbeelding, of None als hij niet bestaat of geen afbeelding is."""
    try:
        ctype, data = fetch(url)
        if not ctype.startswith("image/"):
            return None
        return Image.open(io.BytesIO(data)).size[0]
    except Exception:  # noqa: BLE001
        return None


def wp_candidates(url, size, page_html):
    """WordPress: naam-WxH.ext vanaf de maat van het origineel, plus varianten die op de receptpagina staan."""
    m = re.match(r"(.+/wp-content/uploads/.+?)(-\d+x\d+|-scaled)?(\.(?:jpe?g|png|webp))$", url, re.I)
    if not m:
        return set()
    stem, ext = m.group(1), m.group(3)
    out = set()
    if size:
        w0, h0 = size
        for w in WANT:
            if w < w0:
                for h in {round(h0 * w / w0), int(h0 * w / w0)}:
                    out.add(f"{stem}-{w}x{h}{ext}")
    name = re.escape(stem.rsplit("/", 1)[-1])
    for found in re.findall(r"https?://[^\s\"'<>]*?" + name + r"-\d+x\d+\.(?:jpe?g|png|webp)", page_html or "", re.I):
        out.add(found.replace("&amp;", "&"))
    return out


def conde_candidates(url):
    if not re.search(r"/w_\d+(,h_\d+)?,c_limit/", url):
        return set()
    return {re.sub(r"/w_\d+(,h_\d+)?,c_limit/", f"/w_{w},c_limit/", url) for w in WANT}


def query_candidates(url):
    p = urllib.parse.urlsplit(url)
    q = urllib.parse.parse_qs(p.query)
    if "w" not in q:
        return set()
    out = set()
    for w in WANT:
        q2 = {**{k: v[0] for k, v in q.items()}, "w": str(w)}
        out.add(urllib.parse.urlunsplit(p._replace(query=urllib.parse.urlencode(q2))))
    return out


def photo_set(r):
    url = r.get("photo")
    if not url:
        return None
    try:
        _, data = fetch(url)
        size = Image.open(io.BytesIO(data)).size
    except Exception:  # noqa: BLE001
        size = None
    page = ""
    if "/wp-content/uploads/" in url and (r.get("photoCredit") or {}).get("url"):
        try:
            page = fetch(r["photoCredit"]["url"], 3_000_000)[1].decode("utf-8", "replace")
        except Exception:  # noqa: BLE001
            page = ""
    cands = wp_candidates(url, size, page) | conde_candidates(url) | query_candidates(url)
    cands.discard(url)
    found = {}
    with cf.ThreadPoolExecutor(6) as pool:
        for c, w in zip(cands, pool.map(width_of, cands)):
            if w and MIN_W <= w <= MAX_W and w not in found:
                found[w] = c
    if not found:
        return None
    # het origineel als grootste maat, als het niet extreem groot is (anders de grootste variant)
    if size and size[0] <= 2400 and size[0] > max(found):
        found[size[0]] = url
    return [{"w": w, "url": found[w]} for w in sorted(found)]


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    path = sys.argv[1]
    ed = json.load(open(path))
    recipes = [r for r in ed["recipes"] if r.get("photo")]
    with cf.ThreadPoolExecutor(4) as pool:
        sets = list(pool.map(photo_set, recipes))
    for r, s in zip(recipes, sets):
        if s:
            r["photoSet"] = s
            print(f"{r['slug'][:34]:34} {len(s)} maten: {', '.join(str(x['w']) for x in s)}")
        else:
            r.pop("photoSet", None)
            print(f"{r['slug'][:34]:34} geen kleinere versie gevonden, origineel blijft")
    with open(path, "w") as f:
        json.dump(ed, f, ensure_ascii=False, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
