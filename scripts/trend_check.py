#!/usr/bin/env python3
"""Snelle check vóór je kiest: is een gerecht volgens Google Trends nu echt in trek?

Geeft per zoekterm hetzelfde label als de site (Nieuw, Seizoen, Piek, Stijgt, Stabiel, Dalend), met de zin.
Ongeveer 5 seconden per term. Kies minstens 3 recepten met Nieuw, Seizoen, Piek of Stijgt.

Gebruik: python3 scripts/trend_check.py "zuppa toscana" "marry me cabbage" "kimchi fried rice"
"""
import datetime as dt
import sys

import trends_spark
from trends_collect import Trends

GOOD = {"Nieuw", "Seizoen", "Piek", "Stijgt"}


def check(g, term):
    """Label voor één zoekterm (eerst NL, anders wereldwijd), of None als er te weinig data is."""
    series, end, today = {}, None, dt.date.today()
    for geo in ("NL", "world"):
        points, _ = g.fetch(term, "NL" if geo == "NL" else "", "today 5-y", related=False)
        full = {dt.date.fromisoformat(p): v for p, v in points if dt.date.fromisoformat(p) + dt.timedelta(days=7) <= today}
        if full:
            series[(term, geo)] = full
            end = max(end or max(full), max(full))
    if not end:
        return None
    return trends_spark.spark_for({"trendTerms": [term], "title": term}, series, end)


def main():
    terms = sys.argv[1:]
    if not terms:
        print(__doc__)
        return 2
    g = Trends()
    for t in terms:
        try:
            s = check(g, t)
        except Exception as e:  # noqa: BLE001
            print(f"{t:32} FOUT {type(e).__name__}: {e}"[:110])
            continue
        if not s:
            print(f"{t:32} te weinig zoekdata")
            continue
        mark = "✓" if s["label"] in GOOD else "·"
        print(f"{mark} {t:30} {s['label']:8} [{s['geo']}] {s['text']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
