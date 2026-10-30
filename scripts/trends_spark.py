#!/usr/bin/env python3
"""Maakt per recept een trendlabel, een zin en een sparkline uit data/trends.csv en zet die als `spark` in de editie.

Per recept nemen we de eerste zoekterm uit `trendTerms` met genoeg data, eerst in Nederland, anders wereldwijd.
Labels (in deze volgorde):
  Nieuw    het laatste jaar volop gezocht, daarvoor bijna niet
  Seizoen  komt elk jaar rond deze tijd terug en zit nu hoog
  Piek     zo vaak gezocht als in vijf jaar niet, en meer dan vorig jaar
  Stijgt   minstens 1,25 keer zo vaak als dezelfde weken vorig jaar
  Dalend   hooguit 0,8 keer zo vaak als vorig jaar
  Stabiel  de rest
Steeds vergeleken over 4 volle weken; de lopende week telt niet mee.

Gebruik: python3 scripts/trends_spark.py editions/2026-44.json   (draait ook aan het eind van trends_collect.py)
"""
import csv
import datetime as dt
import json
import pathlib
import statistics as st
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CSV = ROOT / "data" / "trends.csv"
WEEKS = 261  # 5 jaar
SEASON = {12: "winter", 1: "winter", 2: "winter", 3: "voorjaar", 4: "voorjaar", 5: "voorjaar",
          6: "zomer", 7: "zomer", 8: "zomer", 9: "najaar", 10: "najaar", 11: "najaar"}
IN_SEASON = {"winter": "in de winter", "voorjaar": "in het voorjaar", "zomer": "in de zomer", "najaar": "in het najaar"}


def day(s):
    return dt.date.fromisoformat(s)


def load(terms):
    """{(term, geo): {weekstart: waarde}} voor volle weken, plus de laatste volle week."""
    out, end = {}, None
    with CSV.open(newline="") as f:
        for r in csv.DictReader(f):
            if r["metric"] != "interest" or r["window"] != "today 5-y" or r["term"] not in terms:
                continue
            p = day(r["period"])
            if p + dt.timedelta(days=7) > day(r["collected"]):
                continue  # lopende week, nog niet compleet
            out.setdefault((r["term"], r["geo"]), {})[p] = int(r["value"])
            end = max(end or p, p)
    return out, end


def grid(points, end):
    """Volle reeks van WEEKS weken tot en met `end`; weken zonder data tellen als 0."""
    return [points.get(end - dt.timedelta(weeks=WEEKS - 1 - i), 0) for i in range(WEEKS)]


def mean(xs):
    return st.mean(xs) if xs else 0


def times(x):
    """1,9 -> 'twee keer'"""
    if x < 1.75:
        return "anderhalf keer"
    words = ["", "", "twee", "drie", "vier", "vijf", "zes", "zeven", "acht", "negen", "tien"]
    n = round(x)
    return f"{words[n]} keer" if n <= 10 else "meer dan tien keer"


def less(r):
    if r > 0.8:
        return "Iets minder gezocht dan vorig jaar."
    if r >= 0.7:
        return "Een kwart minder gezocht dan vorig jaar."
    if r >= 0.58:
        return "Een derde minder gezocht dan vorig jaar."
    if r >= 0.42:
        return "Half zo vaak gezocht als vorig jaar."
    if r >= 0.29:
        return "Nog maar een derde zo vaak gezocht als vorig jaar."
    if r >= 0.2:
        return "Nog maar een kwart zo vaak gezocht als vorig jaar."
    return "Bijna niet meer gezocht, vergeleken met vorig jaar."


def analyse(v, end):
    n = len(v)
    now = mean(v[-4:])
    last_year = mean(v[-56:-52])
    yoy = now / last_year if last_year else None
    year = v[-52:]
    roll = [mean(year[i:i + 8]) for i in range(0, 45)]
    trough_i = min(range(len(roll)), key=roll.__getitem__)
    trough = roll[trough_i] or None
    trough_month = (end - dt.timedelta(weeks=51 - (trough_i + 4))).month
    peak5 = max(mean(v[i:i + 4]) for i in range(0, n - 3))

    # seizoen: in eerdere jaren lag deze tijd van het jaar ook duidelijk boven het jaargemiddelde
    hits = tries = 0
    for k in range(1, 5):
        a = n - 52 * k
        here, around = v[a - 4:a], v[max(0, a - 26):a + 26]
        if a - 4 < 0 or mean(around) < 3:
            continue
        tries += 1
        hits += mean(here) >= 1.25 * mean(around)
    seasonal = tries >= 2 and hits >= max(2, tries - 1) and now >= 1.2 * mean(year)
    new = sum(x > 0 for x in year) >= 20 and sum(x > 0 for x in v[:-104]) <= 4 and mean(v[-104:-52]) < 0.25 * mean(year)

    if new:
        label, text = "Nieuw", "Een jaar geleden zocht nog bijna niemand hierop."
    elif seasonal and trough and now / trough >= 1.5:
        s_now, s_low = SEASON[end.month], SEASON[trough_month]
        than = IN_SEASON[s_low] if s_low != s_now else "eerder dit jaar"
        label, text = "Seizoen", f"Elk {s_now} terug: nu {times(now / trough)} zo vaak gezocht als {than}."
    elif yoy and yoy >= 1.25 and now >= 0.85 * peak5:
        label, text = "Piek", "Zo vaak gezocht als in vijf jaar niet."
    elif yoy and yoy >= 1.25:
        label, text = "Stijgt", times(yoy).capitalize() + " zo vaak gezocht als vorig jaar."
    elif yoy is not None and yoy <= 0.8:
        label, text = "Dalend", less(yoy)
    else:
        label = "Stabiel"
        text = ("Iets vaker gezocht dan vorig jaar." if yoy and yoy >= 1.1 else
                "Iets minder gezocht dan vorig jaar." if yoy and yoy <= 0.9 else "Even vaak gezocht als vorig jaar.")
    return {
        "label": label, "text": text,
        "yoy": round(yoy, 2) if yoy and not new else None,
        "vsLow": round(now / trough, 1) if trough else None,
    }


def enough(v):
    """Een vol jaar data, en ook data in dezelfde weken vorig jaar (nodig voor de vergelijking)."""
    return sum(x > 0 for x in v[-52:]) >= 40 and sum(x > 0 for x in v[-56:-52]) >= 3 and mean(v[-52:]) >= 3


def is_new(v):
    return sum(x > 0 for x in v[-52:]) >= 20 and sum(x > 0 for x in v[:-104]) <= 4


def spark_for(recipe, series, end):
    for term in recipe.get("trendTerms") or [recipe["title"].lower()]:
        for geo in ("NL", "world"):
            v = series.get((term, geo))
            if not v:
                continue
            v = grid(v, end)
            if enough(v) or is_new(v):
                a = analyse(v, end)
                return {"term": term, "geo": geo, "source": "Google Trends", "asOf": end.isoformat(),
                        "start": (end - dt.timedelta(weeks=51)).isoformat(),
                        "weeks": v[-52:], "prev": v[-104:-52], **a}
    return None


def apply(ed):
    """Zet `spark` op elk recept waarvoor genoeg data is; geeft de regels voor de uitvoer terug."""
    terms = {t for r in ed.get("recipes", []) for t in (r.get("trendTerms") or [r["title"].lower()])}
    series, end = load(terms)
    import harvest  # netwerk: hoeveel koks uit data/sources.csv publiceerden dit de afgelopen 30 dagen
    posts, today = harvest.load_posts(), dt.date.today()
    active = len(harvest.load_sources()) if posts else 0
    lines = []
    for r in ed.get("recipes", []):
        s = spark_for(r, series, end) if end else None
        if s and posts:
            s["network"] = {**harvest.network_for(r.get("trendTerms") or [r["title"].lower()], posts, today), "of": active}
        if s:
            r["spark"] = s
            net = f"  · {s['network']['sources']} koks" if "network" in s else ""
            lines.append(f"{r['slug']:30} {s['label']:8} {s['term']} [{s['geo']}]{net}  {s['text']}")
        else:
            r.pop("spark", None)
            lines.append(f"{r['slug']:30} geen trenddata, de site toont de trend-tekst")
    return lines


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    path = pathlib.Path(sys.argv[1])
    ed = json.load(path.open())
    print("\n".join(apply(ed)))
    with path.open("w") as f:
        json.dump(ed, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
