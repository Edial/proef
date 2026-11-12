#!/usr/bin/env python3
"""Controleert alle edities in editions/ op de regels uit REDACTIE.md en FERMENTATIE.md.

Gepubliceerd is wat in editions/index.json staat. Een nieuwere editions/<id>.json die daar nog niet in staat, is een
concept: de wekelijkse routine schrijft het, de Action "Trends en foto's meten" meet het en zet het pas live
(in index.json) als het de regels haalt. Het nieuwste concept wordt ook gecontroleerd.

Trendregel (vanaf editie 4, oudere edities blijven zoals ze zijn): minstens 3 van de recepten zijn echt in trek,
en minstens 1 daarvan is trending op Instagram. In trek is: Google Trends zegt Nieuw, Seizoen, Piek of Stijgt, of de
Instagram-post achter het recept (veld `instagram`) is trending volgens scripts/instagram_trend.py: een uitschieter
(minstens 5× normaal voor dat account, afgelopen 4 weken) of een oudere post die er deze week veel bij kreeg.
- Nog niet gemeten (concept, direct na het schrijven): de eerste zoekterm (trendTerms[0]) is een stijger uit
  data/buzz.json die Google Trends al in trek noemt, of de Instagram-post staat in de lijst van instagram_trend.py.
- Gemeten (--gemeten <id>, in de Action na de meting): de gemeten labels (`spark` en `igTrend`) tellen. Ontbreekt de
  meting, dan telt het recept niet mee.

Gebruik: python3 scripts/check_edition.py                    (exit 1 bij fouten)
         python3 scripts/check_edition.py --gemeten 2026-46   (trendregel op de gemeten labels van die editie)
"""
import datetime as dt
import json
import pathlib
import re
import sys

import instagram_trend

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


VIDEO_IDS = {"youtube": r"[\w-]{11}", "instagram": r"[\w-]{5,40}", "tiktok": r"\d{8,25}"}


def check_video(v, where):
    """Optioneel: een video van de maker zelf. Het recept staat er altijd ook in tekst bij (ingredients en steps)."""
    if v is None:
        return
    if not isinstance(v, dict):
        return err(where, "video moet een object zijn met platform, id en url")
    platform = v.get("platform")
    if platform not in VIDEO_IDS:
        return err(where, f"video.platform '{platform}' is onbekend ({', '.join(VIDEO_IDS)})")
    if not re.fullmatch(VIDEO_IDS[platform], str(v.get("id", ""))):
        err(where, f"video.id '{v.get('id')}' is geen geldig {platform}-id")
    if not str(v.get("url", "")).startswith("https://"):
        err(where, "video.url moet een https-link zijn")
    if "vertical" in v and not isinstance(v["vertical"], bool):
        err(where, "video.vertical moet true of false zijn")


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
    check_video(r.get("video"), where)
    t = r.get("trend") or {}
    if r.get("trend") and not (t.get("text") and t.get("source")):
        err(where, "trend heeft 'source' en 'text' nodig")
    if re.search(r"[+-]\d+\s?%", t.get("text", "")):
        err(where, "trend-tekst bevat een kaal percentage; schrijf het in woorden")
    if not r.get("tip"):
        warn(where, "geen tip (voor kinderen)")
    check_ingredients(r.get("ingredients"), where)
    if not r.get("trendTerms"):
        warn(where, "geen trendTerms (zoektermen voor Google Trends); de titel wordt gebruikt")
    elif not (isinstance(r["trendTerms"], list) and all(isinstance(x, str) and x.strip() for x in r["trendTerms"]) and len(r["trendTerms"]) <= 3):
        err(where, "trendTerms moet een lijst van 1 tot 3 zoektermen zijn")
    check_signals(r.get("signals"), where)
    if r.get("source") and r["source"] not in SOURCES:
        err(where, f"source '{r['source']}' staat niet in data/sources.csv")
    if r.get("instagram") and not instagram_trend.code(r["instagram"]):
        err(where, "instagram moet de url van een Instagram-post zijn (https://www.instagram.com/p/… of /reel/…)")
    sp = r.get("spark")
    if sp is not None:
        if sp.get("label") not in SPARK_LABELS:
            err(where, f"spark.label '{sp.get('label')}' is onbekend ({', '.join(sorted(SPARK_LABELS))})")
        if not (isinstance(sp.get("weeks"), list) and len(sp["weeks"]) == 52 and all(isinstance(x, int) for x in sp["weeks"])):
            err(where, "spark.weeks moet 52 hele getallen zijn (maak spark met scripts/trends_spark.py)")
        if not sp.get("text"):
            err(where, "spark.text ontbreekt")


SOURCES = {}
if (ROOT / "data" / "sources.csv").exists():
    import csv
    with (ROOT / "data" / "sources.csv").open(newline="") as _f:
        SOURCES = {row["id"]: row for row in csv.DictReader(_f)}
SPARK_LABELS = {"Nieuw", "Seizoen", "Piek", "Stijgt", "Stabiel", "Dalend"}
TRENDING = {"Nieuw", "Seizoen", "Piek", "Stijgt"}
TREND_RULE_FROM = 4   # editienummer vanaf waar de trendregel hard is; 1 t/m 3 blijven zoals ze zijn
MEASURED = sys.argv[sys.argv.index("--gemeten") + 1] if "--gemeten" in sys.argv else None


def rising_trending():
    """{zoekterm: label} van de stijgers in data/buzz.json die Google Trends al in trek noemt."""
    try:
        b = json.loads((ROOT / "data" / "buzz.json").read_text())
    except Exception:  # noqa: BLE001
        return {}
    return {r["phrase"].lower(): r["google"]["label"] for r in b.get("rising", [])
            if (r.get("google") or {}).get("label") in TRENDING}


def trend_rule(ed, where, concept):
    """Minstens 3 recepten echt in trek, waarvan minstens 1 op Instagram. Fout vanaf editie TREND_RULE_FROM,
    daarvoor alleen een waarschuwing (en geen Instagram-eis)."""
    recipes = ed.get("recipes", [])
    hard = (ed.get("number") or 0) >= TREND_RULE_FROM and not ed.get("trendUitzondering")  # met de hand toch gepubliceerd
    if concept and MEASURED != ed.get("id"):
        rising = rising_trending()
        ig_now = {instagram_trend.code(s["url"]) for s in instagram_trend.trending(
            dt.date.fromisoformat(ed["date"]) if ed.get("date") else None)}
        google = [r for r in recipes if ((r.get("trendTerms") or [""])[0] or "").lower() in rising]
        insta = [r for r in recipes if instagram_trend.code(r.get("instagram")) in ig_now]
        good = {r["slug"] for r in google + insta}
        if hard and len(good) < 3:
            options = ", ".join(sorted(rising)) or "(data/buzz.json heeft nog geen stijgers met een Google-label)"
            err(where, f"maar {len(good)} recepten zijn nu al aantoonbaar in trek (nodig: 3). Zet bij een recept een stijger "
                       f"als eerste trendTerm ({options}) of de url van een post uit TRENDING OP INSTAGRAM als \"instagram\".")
        if hard and not insta:
            err(where, "geen enkel recept komt uit TRENDING OP INSTAGRAM (nodig: minstens 1). Kies een gerecht uit die lijst "
                       "(python3 scripts/summary.py) en zet de url van de post in het recept als \"instagram\".")
        return
    google = [r for r in recipes if (r.get("spark") or {}).get("label") in TRENDING]
    insta = [r for r in recipes if instagram_trend.counts(r.get("igTrend"))]
    good = {r["slug"] for r in google + insta}
    if len(good) < 3:
        labels = ", ".join(f"{r.get('slug')}: {(r.get('spark') or {}).get('label', 'niet gemeten')}"
                           + (f" / Instagram {r['igTrend']['ratio']}×" if r.get("igTrend") else "") for r in recipes)
        msg = (f"maar {len(good)} van de {len(recipes)} recepten zijn echt in trek (nodig: 3; Google Trends Nieuw, Seizoen, "
               f"Piek of Stijgt, of trending op Instagram). {labels}")
        (err if hard else warn)(where, msg)
    if hard and not insta:
        err(where, "geen recept is gemeten trending op Instagram (nodig: minstens 1 met een igTrend die meetelt: "
                   "uitschieter of groeit nu, zie scripts/instagram_trend.py).")
SIGNAL_KEYS = {"source", "metric", "value", "unit", "period", "geo", "url", "note"}


def check_signals(items, where):
    for i, s in enumerate(items or []):
        w = f"{where} signal {i + 1}"
        if not isinstance(s, dict):
            err(w, "moet een object zijn")
            continue
        if set(s) - SIGNAL_KEYS:
            err(w, f"onbekende velden {sorted(set(s) - SIGNAL_KEYS)} (toegestaan: {', '.join(sorted(SIGNAL_KEYS))})")
        need(s, ["source", "metric", "period"], w)
        if "value" in s and not isinstance(s["value"], (int, float)):
            err(w, "value moet een getal zijn (zet tekst in 'note')")


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
    # Hoeveel maak je?: groente + water (base) en zout moeten herkenbaar zijn, zout 2–5 % van dat gewicht
    ings = f.get("ingredients", [])
    base = [i for i in ings if i.get("base")]
    if not base:
        err(where, "geen ingrediënten met \"base\": true (groente en water die samen het gewicht voor 'Hoeveel maak je?' vormen)")
    for i in base:
        if i.get("unit") not in ("g", "ml") or not isinstance(i.get("qty"), (int, float)):
            err(where, f"base-ingrediënt '{i.get('item')}' moet in g of ml")
    salt = [i for i in ings if i.get("salt")]
    if len(salt) != 1:
        err(where, "precies één ingrediënt moet \"salt\": true hebben")
    elif base and f.get("saltMode") != "afspoelen":
        total = sum(i.get("qty") or 0 for i in base)
        pct = salt[0]["qty"] / total * 100 if total else 0
        if not 2 <= pct <= 5:
            err(where, f"zout is {pct:.1f} % van groente + water; moet 2–5 % zijn (FERMENTATIE.md §2)")
    keys = {i.get("key") for i in ings if i.get("key")} | {"totaal"}
    for s in f.get("steps", []):
        for k in re.findall(r"\{([a-z]+)\}", s):
            if k not in keys:
                err(where, f"stap gebruikt {{{k}}}, maar geen ingrediënt heeft \"key\": \"{k}\"")
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
    # het nieuwste concept (een editie die nog niet in index.json staat) controleren we mee, als nieuwste editie
    concepts = sorted(p.stem for p in ED.glob("*-*.json") if p.stem not in ids and (not ids or p.stem > max(ids)))
    concept = concepts[-1] if concepts else None
    if MEASURED and MEASURED not in ids + concepts:
        err("--gemeten", f"editions/{MEASURED}.json bestaat niet")
    ids_all = ([concept] if concept else []) + ids
    seen, numbers, prev_cover = {}, {}, None
    md = (ROOT / "FERMENTATIE.md").read_text() if (ROOT / "FERMENTATIE.md").exists() else ""
    library = md.split("## 9.", 1)[1].split("## Bronnen", 1)[0].lower() if "## 9." in md else ""
    recent_ferments = []
    for eid in reversed(ids_all):  # oud naar nieuw
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
        m = ed.get("mail")
        if m is not None:
            if not isinstance(m.get("subject"), str) or not 10 <= len(m["subject"]) <= 70:
                err(where, "mail.subject moet tekst zijn van 10 tot 70 tekens (langer valt weg in de inbox)")
            if m.get("preview") is not None and (not isinstance(m["preview"], str) or len(m["preview"]) > 120):
                err(where, "mail.preview mag hooguit 120 tekens zijn")
        elif ed.get("number", 0) >= 3:
            err(where, "mail.subject ontbreekt: schrijf een onderwerpregel voor de nieuwsbrief (REDACTIE.md stap 7)")
        # nog niet gemeten maar wel in index.json: dan zou het live staan zonder dat de trendregel getoetst is
        if eid != concept and (ed.get("number") or 0) >= TREND_RULE_FROM and not ed.get("trendUitzondering") \
                and not any(r.get("spark") for r in ed.get("recipes", [])):
            err(where, "staat in editions/index.json maar is nog niet gemeten. Haal het id uit editions/index.json: "
                       "GitHub zet de editie zelf live na de meting, als de trendregel klopt (REDACTIE.md stap 10).")
        if str(ed.get("date", "")) >= "2026-11-07":
            core = sum((SOURCES.get(r.get("source") or "") or {}).get("tier") == "core" for r in ed.get("recipes", []))
            if core < 3:
                warn(where, f"maar {core} van de recepten komen van een kernbron (doel: minstens 3, veld 'source')")
            trend_rule(ed, where, eid == concept)
        for i, wt in enumerate(ed.get("watch") or []):
            ww = f"{where} watch {i + 1}"
            need(wt, ["term", "source"], ww)
            check_signals(wt.get("signals"), ww)
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
    extra = f" (plus concept {concept}, nog niet live)" if concept else ""
    print(f"{len(ids)} editie(s) gecontroleerd{extra}: {len(errors)} fout(en), {len(warnings)} waarschuwing(en).")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
