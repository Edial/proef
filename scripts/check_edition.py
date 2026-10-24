#!/usr/bin/env python3
"""Controleert alle edities in editions/ op de regels uit REDACTIE.md en FERMENTATIE.md.

Gebruik: python3 scripts/check_edition.py      (exit 1 bij fouten)
"""
import datetime as dt
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
ED = ROOT / "editions"
TINTS = {"sage", "sky", "blush", "persimmon", "mustard"}
OLD_TINTS = {"lavender", "peach", "rose", "butter"}  # uit de eerste versie, nog geldig
COVERS = {"navy", "ink", "kaki", "moss"}
UNITS = {"g", "ml", ""}
RESERVED = re.compile(r"^(deze-week|archief|zoek|fermentatie|editie-.*|fermentatie-.*)$")
SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

errors, warnings = [], []


def err(where, msg):
    errors.append(f"{where}: {msg}")


def warn(where, msg):
    warnings.append(f"{where}: {msg}")


def need(obj, keys, where):
    for k in keys:
        if obj.get(k) in (None, "", []):
            err(where, f"veld '{k}' ontbreekt of is leeg")


def check_ingredients(items, where):
    for i, ing in enumerate(items or []):
        w = f"{where} ingrediënt {i + 1}"
        if not ing.get("item"):
            err(w, "geen omschrijving")
        if ing.get("qty") is not None and not isinstance(ing["qty"], (int, float)):
            err(w, "qty moet een getal zijn")
        if (ing.get("unit") or "") not in UNITS:
            err(w, f"eenheid '{ing.get('unit')}' is niet metrisch (alleen g, ml of leeg)")


def check_recipe(r, where, seen):
    need(r, ["slug", "title", "dek", "category", "minutes", "servings", "ingredients", "steps", "photo", "photoCredit", "tint", "glyph", "trend"], where)
    slug = r.get("slug", "")
    if slug and not SLUG.match(slug):
        err(where, f"slug '{slug}' mag alleen kleine letters, cijfers en streepjes bevatten")
    if RESERVED.match(slug or ""):
        err(where, f"slug '{slug}' botst met een vaste route van de site")
    if slug in seen:
        err(where, f"slug '{slug}' bestaat al in {seen[slug]}")
    seen[slug] = where
    if r.get("tint") and r["tint"] not in TINTS | OLD_TINTS:
        err(where, f"tint '{r['tint']}' is onbekend ({', '.join(sorted(TINTS))})")
    if r.get("glyph") and len(r["glyph"]) != 1:
        err(where, "glyph moet precies één teken zijn")
    if not str(r.get("photo", "")).startswith("https://"):
        err(where, "photo moet een https-link zijn")
    t = r.get("trend") or {}
    if r.get("trend") and not (t.get("text") and t.get("source")):
        err(where, "trend heeft 'source' en 'text' nodig")
    if re.search(r"[+-]\d+\s?%", t.get("text", "")):
        err(where, "trend-tekst bevat een kaal percentage; schrijf het in woorden")
    if not r.get("tip"):
        warn(where, "geen tip (voor kinderen)")
    check_ingredients(r.get("ingredients"), where)


def check_ferment(f, where, recipes, seen):
    need(f, ["slug", "title", "glyph", "lede", "teaser", "ingredients", "steps", "ok", "bad", "kids", "sources", "timeline", "science"], where)
    slug = f.get("slug", "")
    if slug in seen:
        err(where, f"slug '{slug}' bestaat al in {seen[slug]}")
    seen[slug] = where
    if f.get("usedIn") and f["usedIn"] not in {r.get("slug") for r in recipes}:
        err(where, f"usedIn '{f['usedIn']}' is geen recept uit deze editie")
    check_ingredients(f.get("ingredients"), where)
    # FERMENTATIE.md §2: zout gewogen in grammen
    salts = [i for i in f.get("ingredients", []) if "zout" in i.get("item", "").lower()]
    if not salts:
        err(where, "geen zout in de ingrediënten (FERMENTATIE.md §2)")
    for s in salts:
        if s.get("unit") != "g":
            err(where, "zout moet in grammen gewogen worden (FERMENTATIE.md §2)")
        if "jodium" not in s.get("item", "").lower():
            err(where, "zout moet 'zonder jodium' vermelden (FERMENTATIE.md §2)")
    text = " ".join(f.get("steps", []) + [x.get("text", "") for x in f.get("timeline", [])] + [x.get("value", "") for x in f.get("facts", [])]).lower()
    checks = [
        (r"1[89]\s?[–-]\s?2[0-2]\s?°c|\b(18|19|20|21|22)\s?°c", "geen aanrecht-temperatuur tussen 18 en 22 °C (§3)"),
        (r"5\s?cm", "geen 5 cm kopruimte (§5)"),
        (r"onder|boven de", "niets over de groente onder het vocht houden (§5)"),
        (r"pekel", "geen pekel om bij te vullen (§2)"),
        (r"ph", "geen pH-controle genoemd (§4)"),
        (r"heet|sop|schoon", "niets over een schone pot (§5)"),
        (r"koelkast", "niets over bewaren in de koelkast (§7)"),
    ]
    for pattern, msg in checks:
        if not re.search(pattern, text):
            err(where, msg)
    bad = f.get("bad", "").lower()
    for word in ("schimmel", "slijm", "rot"):
        if word not in bad:
            err(where, f"'bad' noemt '{word}' niet als reden om weg te gooien (§6)")
    for s in f.get("sources", []):
        if not str(s.get("url", "")).startswith("https://"):
            err(where, "elke bron heeft een https-link nodig")


def main():
    try:
        index = json.loads((ED / "index.json").read_text())
    except Exception as e:  # noqa: BLE001
        print(f"editions/index.json is niet te lezen: {e}")
        return 1
    ids = index.get("editions", [])
    if len(ids) != len(set(ids)):
        err("index.json", "een editie staat er dubbel in")
    seen, numbers, prev_cover = {}, {}, None
    md = (ROOT / "FERMENTATIE.md").read_text() if (ROOT / "FERMENTATIE.md").exists() else ""
    library = md.split("## 9.", 1)[1].split("## Bronnen", 1)[0].lower() if "## 9." in md else ""
    recent_ferments = []
    for eid in reversed(ids):  # oud naar nieuw
        path = ED / f"{eid}.json"
        where = f"editions/{eid}.json"
        if not path.exists():
            err("index.json", f"{eid} staat in de lijst maar het bestand bestaat niet")
            continue
        try:
            ed = json.loads(path.read_text())
        except json.JSONDecodeError as e:
            err(where, f"geen geldige JSON: {e}")
            continue
        need(ed, ["id", "number", "year", "week", "date", "intro", "recipes"], where)
        if ed.get("id") != eid:
            err(where, f"id '{ed.get('id')}' hoort '{eid}' te zijn")
        try:
            d = dt.date.fromisoformat(ed.get("date", ""))
            y, w, _ = d.isocalendar()
            if (y, w) != (ed.get("year"), ed.get("week")) or eid != f"{y}-{w:02d}":
                err(where, f"datum {d} valt in week {y}-{w:02d}, niet in {eid}")
            if d.weekday() != 5:
                warn(where, f"datum {d} is geen zaterdag")
        except ValueError:
            err(where, "date moet JJJJ-MM-DD zijn")
        n = ed.get("number")
        if n in numbers:
            err(where, f"nummer {n} is al gebruikt door {numbers[n]}")
        numbers[n] = eid
        cover = (ed.get("cover") or {}).get("color")
        if cover and cover not in COVERS:
            err(where, f"cover.color '{cover}' is onbekend ({', '.join(sorted(COVERS))})")
        if cover and cover == prev_cover:
            warn(where, "zelfde omslagkleur als de vorige editie")
        prev_cover = cover or prev_cover
        recipes = ed.get("recipes", [])
        if not 4 <= len(recipes) <= 6:
            err(where, f"{len(recipes)} recepten; verwacht 5 (4 tot 6)")
        for i, r in enumerate(recipes):
            check_recipe(r, f"{where} recept {i + 1} ({r.get('slug', '?')})", seen)
        if "ferment" in ed:
            check_ferment(ed["ferment"], f"{where} ferment", recipes, seen)
            title = ed["ferment"].get("title", "").lower()
            if library and title and title not in library:
                warn(f"{where} ferment", f"'{ed['ferment'].get('title')}' staat niet in de bibliotheek (FERMENTATIE.md §9); laat een mens het nalopen")
            if title in recent_ferments[-4:]:
                warn(f"{where} ferment", "zelfde ferment als in een van de laatste 4 edities")
            recent_ferments.append(title)
        elif n and n >= 2:
            err(where, "geen Fermentatie van de week")
    for w in warnings:
        print("let op:", w)
    for e in errors:
        print("FOUT:  ", e)
    print(f"{len(ids)} editie(s) gecontroleerd: {len(errors)} fout(en), {len(warnings)} waarschuwing(en).")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
