#!/usr/bin/env python3
"""Maakt per recept een eigen pagina: recept/<slug>/index.html (https://edial.github.io/proef/recept/<slug>/).

Elke pagina is index.html met <base href="../../">, plus eigen titel, beschrijving, deelvoorbeeld
(og:/twitter:) en receptgegevens voor Google (schema.org Recipe). De site zelf toont daarna het recept.
Daarnaast data/makers.json: per recept de maker (kok, blog of magazine uit data/sources.csv, met naam, foto en bio)
voor het kaartje op de receptpagina. Een recept zonder `source` vindt zijn maker via de website van photoCredit.url.
Draai na elke wijziging aan index.html, een editie of data/sources.csv; de controle op GitHub faalt als iets verouderd is.

Gebruik: python3 scripts/build_pages.py           (pagina's maken of bijwerken, oude weghalen)
         python3 scripts/build_pages.py --check   (alleen controleren; exit 1 als iets niet klopt)
"""
import csv
import html
import json
import pathlib
import re
import shutil
import sys
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = "https://edial.github.io/proef/"
OUT = ROOT / "recept"
MARK = "<!-- gemaakt door scripts/build_pages.py, niet met de hand bewerken -->"


def qty(i):
    if i.get("qty") is None:
        return i["item"]
    q = i["qty"]
    q = int(q) if float(q).is_integer() else str(q).replace(".", ",")
    return f"{q} {i.get('unit') or ''} {i['item']}".replace("  ", " ")


def page(template, r, ed):
    url = f"{SITE}recept/{r['slug']}/"
    title = f"{r['title']} · Proef"
    desc = r.get("dek") or ""
    e = lambda s: html.escape(s, quote=True)
    ld = {
        "@context": "https://schema.org", "@type": "Recipe", "name": r["title"], "description": desc,
        "image": [r["photo"]] if r.get("photo") else [], "url": url, "inLanguage": "nl",
        "datePublished": ed["date"], "author": {"@type": "Organization", "name": "Proef", "url": SITE},
        "recipeCategory": r.get("category", ""), "keywords": ", ".join(r.get("tags", [])),
        "recipeYield": f"{r.get('servings', '')} {r.get('servingsLabel', 'personen')}".strip(),
        "totalTime": f"PT{r['minutes']}M" if r.get("minutes") else None,
        "recipeIngredient": [qty(i) for i in r.get("ingredients", [])],
        "recipeInstructions": [{"@type": "HowToStep", "text": s} for s in r.get("steps", [])],
    }
    if r.get("photoCredit"):
        ld["isBasedOn"] = r["photoCredit"].get("url")
    ld = {k: v for k, v in ld.items() if v not in (None, "", [])}
    head = "\n".join([
        MARK,
        f'<link rel="canonical" href="{url}">',
        f'<meta property="og:type" content="article">',
        f'<meta property="og:site_name" content="Proef">',
        f'<meta property="og:title" content="{e(r["title"])}">',
        f'<meta property="og:description" content="{e(desc)}">',
        f'<meta property="og:url" content="{url}">',
        *([f'<meta property="og:image" content="{e(r["photo"])}">'] if r.get("photo") else []),
        f'<meta name="twitter:card" content="summary_large_image">',
        '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False).replace("</", "<\\/") + "</script>",
    ])
    out = template.replace('<base href="./">', '<base href="../../">', 1)
    out = re.sub(r"<title>.*?</title>", f"<title>{e(title)}</title>", out, count=1, flags=re.S)
    out = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{e(desc)}">', out, count=1)
    return out.replace("</head>", head + "\n</head>", 1)


MAKERS = ROOT / "data" / "makers.json"


def host(url):
    h = urllib.parse.urlsplit(url or "").hostname or ""
    return h[4:] if h.startswith("www.") else h


def makers(recipes):
    """{"makers": {id: {...}}, "recipes": {slug: id}}: alleen de bronnen die in een editie staan."""
    with (ROOT / "data" / "sources.csv").open(newline="") as f:
        src = {r["id"]: r for r in csv.DictReader(f)}
    by_host = {host(r["site"]): i for i, r in src.items() if r.get("site")}
    out, links = {}, {}
    for r in recipes:
        credit = r.get("photoCredit") or {}
        i = r.get("source") if r.get("source") in src else by_host.get(host(credit.get("url")))
        if not i:
            continue
        s = src[i]
        links[r["slug"]] = i
        out[i] = {k: v for k, v in {
            "name": s["name"], "person": s.get("person"), "avatar": s.get("avatar"), "bio": s.get("bio"),
            "site": s.get("site"), "instagram": s.get("instagram"), "country": s.get("country"),
            "affiliation": s.get("affiliation"),
        }.items() if v}
    return {"makers": dict(sorted(out.items())), "recipes": links}


def build():
    template = (ROOT / "index.html").read_text()
    assert '<base href="./">' in template, 'index.html mist <base href="./">'
    ids = json.loads((ROOT / "editions" / "index.json").read_text())["editions"]
    pages, recipes = {}, []
    for i in ids:
        ed = json.loads((ROOT / "editions" / f"{i}.json").read_text())
        for r in ed.get("recipes", []):
            pages[r["slug"]] = page(template, r, ed)
            recipes.append(r)
    return pages, json.dumps(makers(recipes), ensure_ascii=False, indent=1) + "\n"


def main():
    pages, mk = build()
    existing = {p.name for p in OUT.iterdir() if p.is_dir()} if OUT.exists() else set()
    if "--check" in sys.argv:
        bad = [s for s, h in pages.items() if not (OUT / s / "index.html").exists() or (OUT / s / "index.html").read_text() != h]
        extra = sorted(existing - set(pages))
        for s in bad:
            print(f"verouderd of ontbreekt: recept/{s}/")
        for s in extra:
            print(f"hoort niet meer bij een editie: recept/{s}/")
        stale = not MAKERS.exists() or MAKERS.read_text() != mk
        if stale:
            print("verouderd of ontbreekt: data/makers.json")
        print(f"{len(pages)} receptpagina's gecontroleerd, {len(bad) + len(extra) + stale} probleem/problemen. Los op met: python3 scripts/build_pages.py")
        return 1 if bad or extra or stale else 0
    for slug, h in pages.items():
        (OUT / slug).mkdir(parents=True, exist_ok=True)
        (OUT / slug / "index.html").write_text(h)
    for slug in existing - set(pages):
        f = OUT / slug / "index.html"
        if f.exists() and MARK in f.read_text():
            shutil.rmtree(OUT / slug)
    MAKERS.write_text(mk)
    print(f"{len(pages)} receptpagina's in recept/, makers in data/makers.json.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
