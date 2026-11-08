#!/usr/bin/env python3
"""Wat is er nu echt trending op Instagram bij de koks en magazines die we volgen? Rekent alleen met data/posts.csv
(de wekelijkse harvest), zonder internet. Gebruikt door summary.py (de lijst voor de routine), check_edition.py
(de trendregel) en de Action "Trends en foto's meten" (die zet `igTrend` in de editie).

De logica, in gewone woorden:
1. Betrokkenheid = likes + reacties, maar reacties tellen hooguit mee tot een kwart van de likes. Zo tellen posts als
   "reageer met SOEP en ik stuur je het recept" of winacties niet dubbel. (Oudere posts in posts.csv hebben alleen de
   som; daar rekenen we met de som.)
2. Normaal = de mediaan van die betrokkenheid over de posts van hetzelfde account (minstens 8 posts). Zo wegen een
   klein account en Bon Appétit even zwaar: we kijken hoe een post het doet ten opzichte van wat dat account gewend is.
3. Een post is trending als hij in de afgelopen 14 dagen verscheen, minstens 5× zo goed scoort als normaal en minstens
   1.000 likes en reacties heeft (anders is één toevallige uitschieter bij een klein account al genoeg).
   Ter vergelijking: in oktober en begin november haalden 11 tot 16 posts per week dat.

Gebruik: python3 scripts/instagram_trend.py                    lijst van wat nu trending is
         python3 scripts/instagram_trend.py editions/2026-46.json  zet per recept met `instagram` (url van de post) het
                                                                gemeten `igTrend` in de editie (niet met de hand invullen)
"""
import csv
import datetime as dt
import json
import pathlib
import re
import statistics
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
POSTS = ROOT / "data" / "posts.csv"
DAYS, MIN_RATIO, MIN_ENGAGEMENT, MIN_POSTS, COMMENT_SHARE = 14, 5.0, 1000, 8, 0.25
NOT_A_POST = re.compile(r"\b(giveaway|winactie|win a|winnen)\b", re.I)


def code(url):
    """De vaste code van een post (…/p/DfYFxdgF4H2/ of …/reel/DfYFxdgF4H2/ → DfYFxdgF4H2)."""
    m = re.search(r"instagram\.com/(?:[^/]+/)?(?:p|reel|reels|tv)/([A-Za-z0-9_-]+)", url or "")
    return m.group(1) if m else None


def engagement(p):
    likes, comments = p.get("likes") or "", p.get("comments") or ""
    if likes.isdigit():
        c = int(comments) if comments.isdigit() else 0
        return int(likes) + min(c, int(int(likes) * COMMENT_SHARE))
    return int(p["views"]) if (p.get("views") or "").isdigit() else None


def scored(today=None):
    """Alle Instagram-posts met betrokkenheid, normaal en verhouding: {code: {...}}."""
    today = today or dt.date.today()
    if not POSTS.exists():
        return {}
    with POSTS.open(newline="") as f:
        rows = [p for p in csv.DictReader(f) if p["kind"] == "instagram"]
    per = {}
    for p in rows:
        e = engagement(p)
        if e is not None:
            per.setdefault(p["source"], []).append(e)
    normal = {s: statistics.median(v) for s, v in per.items() if len(v) >= MIN_POSTS}
    out = {}
    for p in rows:
        e, n, c = engagement(p), normal.get(p["source"]), code(p["url"])
        if e is None or not n or not c:
            continue
        age = (today - dt.date.fromisoformat(p["published"])).days
        out[c] = {"source": p["source"], "name": p["name"], "url": p["url"], "date": p["published"], "title": p["title"],
                  "engagement": e, "likes": int(p["likes"]) if (p.get("likes") or "").isdigit() else None,
                  "normal": round(n), "ratio": round(e / n, 1), "age": age}
    return out


def is_trending(s):
    return bool(s) and s["ratio"] >= MIN_RATIO and s["engagement"] >= MIN_ENGAGEMENT and 0 <= s["age"] <= DAYS \
        and not NOT_A_POST.search(s["title"])


def trending(today=None):
    """Wat nu trending is, beste eerst."""
    return sorted((s for s in scored(today).values() if is_trending(s)), key=lambda s: -s["ratio"])


def counts(trend):
    """Telt een gemeten igTrend mee voor de trendregel?"""
    return bool(trend) and trend.get("ratio", 0) >= MIN_RATIO and trend.get("engagement", 0) >= MIN_ENGAGEMENT \
        and trend.get("age", 0) <= DAYS


def measure(path):
    ed = json.loads(pathlib.Path(path).read_text())
    today = dt.date.fromisoformat(ed["date"]) if ed.get("date") else dt.date.today()
    all_ = scored(today)
    for r in ed.get("recipes", []):
        s = all_.get(code(r.get("instagram")))
        if not r.get("instagram"):
            r.pop("igTrend", None)
            continue
        if not s:
            r.pop("igTrend", None)
            print(f"{r['slug'][:34]:34} Instagram-post niet in data/posts.csv (account niet gevolgd of te oud)")
            continue
        r["igTrend"] = {k: s[k] for k in ("name", "url", "date", "title", "engagement", "normal", "ratio", "age")}
        print(f"{r['slug'][:34]:34} {s['name']}: {s['engagement']} likes en reacties, {s['ratio']}× normaal"
              f"{'' if counts(r['igTrend']) else ' (telt niet mee: minder dan 5× normaal of 1.000)'}")
    pathlib.Path(path).write_text(json.dumps(ed, ensure_ascii=False, indent=2) + "\n")


def main():
    if len(sys.argv) > 1:
        return measure(sys.argv[1])
    for s in trending():
        print(f"{s['ratio']:5.1f}× {s['engagement']:>7} {s['name'][:24]:24} {s['date']} {s['title'][:70]} {s['url']}")


if __name__ == "__main__":
    main()
