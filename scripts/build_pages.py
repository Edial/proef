#!/usr/bin/env python3
"""Maakt per recept een eigen pagina: recept/<slug>/index.html (https://edial.github.io/proef/recept/<slug>/).

Elke pagina is index.html met <base href="../../">, plus eigen titel, beschrijving, deelvoorbeeld
(og:/twitter:) en receptgegevens voor Google (schema.org Recipe). De site zelf toont daarna het recept.
Draai na elke wijziging aan index.html of een editie; de controle op GitHub faalt als een pagina verouderd is.

Gebruik: python3 scripts/build_pages.py           (pagina's maken of bijwerken, oude weghalen)
         python3 scripts/build_pages.py --check   (alleen controleren; exit 1 als iets niet klopt)
"""
import html
import json
import pathlib
import re
import shutil
import sys

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


def build():
    template = (ROOT / "index.html").read_text()
    assert '<base href="./">' in template, 'index.html mist <base href="./">'
    ids = json.loads((ROOT / "editions" / "index.json").read_text())["editions"]
    pages = {}
    for i in ids:
        ed = json.loads((ROOT / "editions" / f"{i}.json").read_text())
        for r in ed.get("recipes", []):
            pages[r["slug"]] = page(template, r, ed)
    return pages


def main():
    pages = build()
    existing = {p.name for p in OUT.iterdir() if p.is_dir()} if OUT.exists() else set()
    if "--check" in sys.argv:
        bad = [s for s, h in pages.items() if not (OUT / s / "index.html").exists() or (OUT / s / "index.html").read_text() != h]
        extra = sorted(existing - set(pages))
        for s in bad:
            print(f"verouderd of ontbreekt: recept/{s}/")
        for s in extra:
            print(f"hoort niet meer bij een editie: recept/{s}/")
        print(f"{len(pages)} receptpagina's gecontroleerd, {len(bad) + len(extra)} probleem/problemen. Los op met: python3 scripts/build_pages.py")
        return 1 if bad or extra else 0
    for slug, h in pages.items():
        (OUT / slug).mkdir(parents=True, exist_ok=True)
        (OUT / slug / "index.html").write_text(h)
    for slug in existing - set(pages):
        f = OUT / slug / "index.html"
        if f.exists() and MARK in f.read_text():
            shutil.rmtree(OUT / slug)
    print(f"{len(pages)} receptpagina's in recept/.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
