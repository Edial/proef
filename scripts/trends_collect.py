#!/usr/bin/env python3
"""Verzamelt trenddata van een editie in data/trends.csv (één regel per meetpunt), voor een later dashboard.

Wat erin komt:
  1. de cijfers die de redactie vond (`signals` per recept, `watch` op editieniveau), zoals ze in de editie staan;
  2. Google Trends voor de zoektermen van deze editie (`trendTerms` per recept, `watch[].term`):
     interesse per week over 5 jaar (NL en wereldwijd) en de snelst stijgende verwante zoekopdrachten;
  3. een korte update (3 maanden) voor de zoektermen van de vorige 4 edities, zodat hun lijn doorloopt;
  4. daarna zet het per recept een trendlabel, zin en sparkline (`spark`) in de editie, via trends_spark.py.

Google Trends schaalt elke reeks naar 0–100 binnen die zoekterm, dat land en dat tijdvenster (kolom `window`);
vergelijk dus alleen waarden met dezelfde term, geo en window. Bestaande meetpunten worden bijgewerkt, niet verdubbeld.
De weekpunten (metric `interest`) hebben geen url: die volgt uit term, geo en window (zie de `rising-query`-regels).

Gebruik: python3 scripts/trends_collect.py editions/2026-44.json   (alleen standaardbibliotheek)
         --no-google   alleen de cijfers uit de editie overnemen
"""
import csv
import datetime as dt
import http.cookiejar
import json
import pathlib
import sys
import time
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
CSV = ROOT / "data" / "trends.csv"
COLS = ["collected", "edition", "recipe", "source", "term", "geo", "metric", "window", "period", "value", "unit", "url", "note"]
KEY = ("source", "term", "geo", "metric", "window", "period", "note")
GEOS = ["NL", ""]  # "" = wereldwijd
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 Chrome/126 Safari/537.36"


class Trends:
    def __init__(self):
        self.op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        self.op.addheaders = [("User-Agent", UA), ("Accept-Language", "nl-NL")]
        self.op.open("https://trends.google.com/trends/?geo=NL", timeout=20).read()  # zet de NID-cookie

    def _get(self, path, params):
        for attempt in range(3):
            try:
                raw = self.op.open(f"https://trends.google.com/trends/api/{path}?" + urllib.parse.urlencode(params), timeout=30).read().decode()
                time.sleep(1.5)  # rustig aan, anders volgt een 429
                return json.loads(raw[raw.index("{"):])
            except urllib.error.HTTPError as e:
                if e.code != 429 or attempt == 2:
                    raise
                time.sleep(20 * (attempt + 1))

    def fetch(self, term, geo, window, related=True):
        req = {"comparisonItem": [{"keyword": term, "geo": geo, "time": window}], "category": 0, "property": ""}
        widgets = {w["id"]: w for w in self._get("explore", {"hl": "nl-NL", "tz": "-60", "req": json.dumps(req)})["widgets"]}
        base = {"hl": "nl-NL", "tz": "-60"}
        ts = self._get("widgetdata/multiline", {**base, "req": json.dumps(widgets["TIMESERIES"]["request"]), "token": widgets["TIMESERIES"]["token"]})
        points = [(dt.datetime.fromtimestamp(int(p["time"]), dt.timezone.utc).date().isoformat(), p["value"][0])
                  for p in ts["default"]["timelineData"] if p.get("hasData", [True])[0]]
        rising = []
        if related and "RELATED_QUERIES" in widgets:
            rq = self._get("widgetdata/relatedsearches", {**base, "req": json.dumps(widgets["RELATED_QUERIES"]["request"]), "token": widgets["RELATED_QUERIES"]["token"]})
            lists = rq["default"]["rankedList"]
            if len(lists) > 1:
                rising = [(k["query"], k.get("formattedValue", ""), k.get("value")) for k in lists[1]["rankedKeyword"][:10]]
        return points, rising


def load():
    if not CSV.exists():
        return {}
    with CSV.open(newline="") as f:
        return {tuple(r[k] for k in KEY): r for r in csv.DictReader(f)}


def save(rows):
    CSV.parent.mkdir(exist_ok=True)
    with CSV.open("w", newline="") as f:
        w = csv.DictWriter(f, COLS)
        w.writeheader()
        w.writerows(sorted(rows.values(), key=lambda r: (r["source"], r["term"], r["geo"], r["metric"], r["window"], r["period"], r["note"])))


def terms_of(ed):
    out = []
    for r in ed.get("recipes", []):
        for t in r.get("trendTerms") or [r["title"].lower()]:
            out.append((t, r["slug"]))
    for w in ed.get("watch", []):
        if w.get("term"):
            out.append((w["term"], ""))
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 1:
        print(__doc__)
        return 2
    path = pathlib.Path(args[0])
    ed = json.load(path.open())
    today = dt.date.today().isoformat()
    rows = load()
    n0 = len(rows)

    def put(**kw):
        row = {c: "" for c in COLS} | {"collected": today, "edition": ed["id"]} | {k: ("" if v is None else str(v)) for k, v in kw.items()}
        rows[tuple(row[k] for k in KEY)] = row

    # 1. cijfers uit de editie
    for r in ed.get("recipes", []):
        for s in r.get("signals", []):
            put(recipe=r["slug"], **s)
    for w in ed.get("watch", []):
        for s in w.get("signals", []):
            put(term=w.get("term", ""), **s)
        if not w.get("signals"):
            put(term=w.get("term", ""), source=w.get("source", ""), metric="mentioned", period=today, url=w.get("url", ""), note=w.get("note", ""))

    # 2 en 3. Google Trends
    if "--no-google" not in sys.argv:
        others = sorted(p for p in (ROOT / "editions").glob("*-*.json") if p.name < path.name)[-4:]
        jobs = [(t, slug, "today 5-y") for t, slug in terms_of(ed)]
        mine = {t for t, _, _ in jobs}
        for p in others:
            jobs += [(t, slug, "today 3-m") for t, slug in terms_of(json.load(p.open())) if t not in mine]
        try:
            g = Trends()
        except Exception as e:  # noqa: BLE001
            print(f"Google Trends niet bereikbaar ({e}); alleen de cijfers uit de editie opgeslagen.")
            g = None
        fails = 0
        for term, slug, window in jobs if g else []:
            for geo in GEOS:
                try:
                    points, rising = g.fetch(term, geo, window)
                except Exception as e:  # noqa: BLE001
                    fails += 1
                    print(f"FOUT  {term} [{geo or 'wereld'}]: {type(e).__name__}: {e}"[:120])
                    continue
                url = "https://trends.google.com/trends/explore?" + urllib.parse.urlencode({"q": term, "geo": geo, "date": window})
                for period, value in points:
                    put(recipe=slug, source="Google Trends", term=term, geo=geo or "world", metric="interest", window=window, period=period, value=value, unit="0-100")
                for query, label, value in rising:
                    put(recipe=slug, source="Google Trends", term=term, geo=geo or "world", metric="rising-query", window=window, period=today, value=value, unit="%" if label != "Breakout" else "breakout", url=url, note=query)
                print(f"{term:32} {geo or 'wereld':6} {window:10} {len(points):4} weken, {len(rising)} stijgers")
        if fails:
            print(f"{fails} Google Trends-verzoek(en) mislukt; de rest is opgeslagen. Niet blokkerend voor de editie.")

    save(rows)
    print(f"{CSV.relative_to(ROOT)}: {len(rows)} regels ({len(rows) - n0:+d}).")

    # 4. trendlabel en sparkline per recept in de editie (zie trends_spark.py)
    import trends_spark
    print("\n".join(trends_spark.apply(ed)))
    with path.open("w") as f:
        json.dump(ed, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
