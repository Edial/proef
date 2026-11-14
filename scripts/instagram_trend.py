#!/usr/bin/env python3
"""Wat is er nu echt trending op Instagram bij de koks en magazines die we volgen? Rekent alleen met data/posts.csv
(de dagelijkse meting), zonder internet. Gebruikt door summary.py (de lijst voor de routine), check_edition.py
(de trendregel) en de Action "Trends en foto's meten" (die zet `igTrend` in de editie).

De logica, in gewone woorden:
1. Betrokkenheid = likes + reacties, maar reacties tellen hooguit mee tot een kwart van de likes. Zo tellen posts als
   "reageer met SOEP en ik stuur je het recept" of winacties niet dubbel. (Oudere posts in posts.csv hebben alleen de
   som; daar rekenen we met de som.)
2. Normaal = de mediaan van die betrokkenheid over de posts van hetzelfde account die bij het meten minstens 3 dagen
   oud waren (minstens 8 posts). Zo wegen een klein account en Bon Appétit even zwaar: we kijken hoe een post het doet
   ten opzichte van wat dat account gewend is. Posts met bijna niets (minder dan 5% van het 75e percentiel van dat
   account, bijvoorbeeld proef-reels die alleen niet-volgers zien) tellen niet mee voor normaal: bij Kalejunkie was
   de helft van de posts zo'n post, waardoor normaal op 64 likes uitkwam en alles een uitschieter leek.
   Jonge posts groeien nog. Gemeten op 7 november 2026 (175 posts): een post van 1 dag oud had gemiddeld 40% van wat
   normaal is, van 2 dagen 80%, vanaf 3 dagen 100%. Een post van 1 of 2 dagen vergelijken we daarom met dat deel van
   normaal; een post van dezelfde dag telt nog niet mee (de dagelijkse meting pakt hem morgen op).
3. Een post is trending op een van twee manieren (altijd minstens 1.000 likes en reacties, anders is één toevallige
   uitschieter bij een klein account al genoeg):
   - Uitschieter: verscheen in de afgelopen 4 weken en scoort minstens 5× zo goed als normaal. Op 12 november waren
     dat er 118 (65 als we alleen de laatste 2 weken namen).
   - Groeit nu: een post van 1 tot 6 weken oud die er de afgelopen week minstens 2× zoveel likes en reacties bij kreeg
     als een gewone post van dat account in totaal haalt. Een oudere post die ineens weer rondgaat, dus. Hiervoor
     bewaart de dagelijkse meting per post een meetpunt van 7 tot 13 dagen terug (harvest.py, cp1_). De drempel 2× is
     een startwaarde: eind november is er genoeg meetdata om hem te ijken.
4. De volgorde van de lijst: hoeveel extra likes en reacties een post kreeg (bij een uitschieter boven normaal, bij een
   groeier in de afgelopen week). Zo staan de grote trends bovenaan, niet de kleine accounts met een hoge verhouding.

Gebruik: python3 scripts/instagram_trend.py [--top 20]         lijst van wat nu trending is
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
DAYS, MIN_RATIO, MIN_ENGAGEMENT, MIN_POSTS, COMMENT_SHARE = 28, 5.0, 1000, 8, 0.25
GROW_MIN_AGE, GROW_MAX_AGE, GROW_RATIO = 7, 42, 2.0   # groeit nu: post van 1 tot 6 weken, week-groei ≥ 2× normaal
SHARE_AT_AGE = {1: 0.4, 2: 0.8}   # deel van de uiteindelijke likes en reacties dat een post na 1 of 2 dagen heeft
MATURE = 3                        # vanaf zoveel dagen oud is een post uitgegroeid
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
    def measured_age(p):  # leeftijd van de post op het moment dat de likes zijn geteld
        on = p.get("measured") or p.get("first_seen") or today.isoformat()
        return (dt.date.fromisoformat(on) - dt.date.fromisoformat(p["published"])).days

    per = {}
    for p in rows:
        e = engagement(p)
        if e is not None and measured_age(p) >= MATURE:
            per.setdefault(p["source"], []).append(e)
    def robust(v):
        v = sorted(v)
        floor = 0.05 * v[int(len(v) * 0.75)]
        return [x for x in v if x >= floor]
    per = {s: robust(v) for s, v in per.items() if len(v) >= MIN_POSTS}
    normal = {s: statistics.median(v) for s, v in per.items() if len(v) >= MIN_POSTS}
    out = {}
    for p in rows:
        e, n, c, at = engagement(p), normal.get(p["source"]), code(p["url"]), measured_age(p)
        share = 1.0 if at >= MATURE else SHARE_AT_AGE.get(at)
        if e is None or not n or not c or not share:
            continue
        age = (today - dt.date.fromisoformat(p["published"])).days
        s = {"source": p["source"], "name": p["name"], "url": p["url"], "date": p["published"], "title": p["title"],
             "engagement": e, "likes": int(p["likes"]) if (p.get("likes") or "").isdigit() else None,
             "normal": round(n * share), "ratio": round(e / (n * share), 1), "age": age, "measuredAge": at,
             "kind": "uitschieter", "extra": e - round(n * share)}
        # groeit nu: likes en reacties erbij sinds het meetpunt van 7 tot 13 dagen terug, omgerekend naar een week
        before = engagement({"likes": p.get("cp1_likes") or "", "comments": p.get("cp1_comments") or ""})
        if before is not None and p.get("cp1_on") and p.get("measured"):
            days = (dt.date.fromisoformat(p["measured"]) - dt.date.fromisoformat(p["cp1_on"])).days
            if days >= 7:
                s["growth"] = round((e - before) * 7 / days)
                s["growthRatio"] = round(s["growth"] / n, 1)   # t.o.v. wat een gewone post in totaal haalt
                if grows(s) and not is_outlier(s):   # een uitschieter blijft een uitschieter
                    s.update(kind="groeit", extra=s["growth"])
        out[c] = s
    return out


def is_outlier(s):
    return s["ratio"] >= MIN_RATIO and s["engagement"] >= MIN_ENGAGEMENT and 0 <= s["age"] <= DAYS


def grows(s):
    return s.get("growthRatio", 0) >= GROW_RATIO and s.get("growth", 0) >= MIN_ENGAGEMENT \
        and GROW_MIN_AGE <= s["age"] <= GROW_MAX_AGE


def is_trending(s):
    return bool(s) and (is_outlier(s) or grows(s)) and not NOT_A_POST.search(s["title"])


def trending(today=None):
    """Wat nu trending is, met de meeste extra aandacht (boven normaal, of erbij in de afgelopen week) eerst."""
    return sorted((s for s in scored(today).values() if is_trending(s)), key=lambda s: -s["extra"])


def counts(trend):
    """Telt een gemeten igTrend mee voor de trendregel?"""
    if not trend:
        return False
    if trend.get("kind") == "groeit":
        return grows(trend)
    return trend.get("ratio", 0) >= MIN_RATIO and trend.get("engagement", 0) >= MIN_ENGAGEMENT and trend.get("age", 0) <= DAYS


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
        r["igTrend"] = {k: s[k] for k in ("name", "url", "date", "title", "engagement", "normal", "ratio", "age", "kind",
                                           "growth", "growthRatio") if k in s}
        how = (f"{s['growth']} erbij in een week ({s['growthRatio']}× een gewone post)" if s["kind"] == "groeit"
               else f"{s['engagement']} likes en reacties, {s['ratio']}× normaal")
        print(f"{r['slug'][:34]:34} {s['name']}: {how}"
              f"{'' if counts(r['igTrend']) else ' (telt niet mee: geen uitschieter en groeit niet genoeg)'}")
    pathlib.Path(path).write_text(json.dumps(ed, ensure_ascii=False, indent=2) + "\n")


def main():
    if len(sys.argv) > 1 and sys.argv[1] != "--top":
        return measure(sys.argv[1])
    top = int(sys.argv[2]) if len(sys.argv) > 2 else None
    hits = trending()
    import runlog
    runlog.metric(trending=len(hits), groeit=sum(h["kind"] == "groeit" for h in hits),
                  top="; ".join(f"{h['name']}: {h['title'][:40]}" for h in hits[:3]))
    for s in hits[:top]:
        how = f"+{s['growth']}/week" if s["kind"] == "groeit" else f"{s['ratio']:.1f}×"
        print(f"{how:>12} {s['engagement']:>7} {s['name'][:24]:24} {s['date']} {s['title'][:70]} {s['url']}")


if __name__ == "__main__":
    main()
