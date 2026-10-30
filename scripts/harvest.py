#!/usr/bin/env python3
"""Haalt de feeds van alle werkende bronnen op (data/sources.csv), bewaart de berichten in data/posts.csv
en schrijft data/buzz.json: welke gerechten nu bij meerdere koks tegelijk opduiken.

Buzz: per woordcombinatie (2–3 woorden uit de titels) tellen we hoeveel verschillende bronnen er de
afgelopen 30 dagen over publiceerden, tegenover de 60 dagen daarvoor. Eén bron telt één keer, hoe vaak
die ook post. Draait elke vrijdagnacht als GitHub Action; de routine leest op zaterdag alleen buzz.json.

Gebruik: python3 scripts/harvest.py              (alleen feeds)
         python3 scripts/harvest.py --google 15   (plus Google Trends-label voor de 15 grootste stijgers)
"""
import concurrent.futures as cf
import csv
import datetime as dt
import json
import pathlib
import re
import sys

import feeds

ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCES = ROOT / "data" / "sources.csv"
POSTS = ROOT / "data" / "posts.csv"
BUZZ = ROOT / "data" / "buzz.json"
COLS = ["source", "name", "tier", "kind", "published", "title", "url", "views", "first_seen"]
KEEP_DAYS = 400
WINDOW, BASE = 30, 60

STOP = set("""
a an and the with for of to in on at by from or my our your his her their this that these those it its is are be best easy
quick simple healthy homemade ultimate perfect favorite favourite new ways way how make making made recipe recipes minute
minutes hour hours day days week weekly night dinner dinners lunch breakfast idea ideas guide tips video episode ep part
i me we you us top review get got just really very more most all any every one two three five ten vs plus without into out up
like tastes taste style inspired version copycat edition finds roundup things heres whats what why need know should probably missing told chef
de het een en van met voor in op aan bij uit zo je jouw mijn onze deze dit dat die wat hoe maak maken recept recepten
lekker lekkere makkelijk makkelijke snel snelle simpel simpele gezond gezonde heerlijk heerlijke week weekend dag avond
""".split())


def load_sources():
    with SOURCES.open(newline="") as f:
        return [r for r in csv.DictReader(f) if r["status"] in ("ok", "stil")]


def load_posts():
    if not POSTS.exists():
        return {}
    with POSTS.open(newline="") as f:
        return {r["url"]: r for r in csv.DictReader(f)}


def fetch(src):
    out = []
    targets = [("site", src["feed"])] if src["feed"] else []
    if src["youtube"].startswith("UC"):
        targets.append(("youtube", feeds.youtube_feed(src["youtube"])))
    for kind, url in targets:
        try:
            for p in feeds.read(url):
                out.append((src, kind, p))
        except Exception as e:  # noqa: BLE001
            print(f"FOUT  {src['name']}: {type(e).__name__}: {e}"[:110], file=sys.stderr)
    return out


def words(title):
    t = re.sub(r"&[a-z]+;|&#\d+;", " ", title.lower())
    t = re.sub(r"['’]", "", t)  # here's -> heres, niet 'here s'
    return re.findall(r"[a-zà-ÿ]+(?:-[a-zà-ÿ]+)*", t)


def phrases(title):
    w = words(title)
    out = set()
    for n in (2, 3):
        for i in range(len(w) - n + 1):
            g = w[i:i + n]
            if g[0] in STOP or g[-1] in STOP or any(len(x) < 3 for x in (g[0], g[-1])):
                continue
            out.add(" ".join(g))
    return out


def day(s):
    return dt.date.fromisoformat(s[:10]) if s else None


def buzz(posts, today):
    cur, base, examples = {}, {}, {}
    for p in posts.values():
        d = day(p["published"])
        if not d:
            continue
        age = (today - d).days
        if age < 0 or age > WINDOW + BASE:
            continue
        bucket = cur if age <= WINDOW else base
        for ph in phrases(p["title"]):
            bucket.setdefault(ph, set()).add(p["source"])
            if age <= WINDOW:
                examples.setdefault(ph, []).append(p)
    rows = []
    for ph, srcs in cur.items():
        n, b = len(srcs), len(base.get(ph, ())) * WINDOW / BASE
        if n < 3:
            continue
        ex = sorted(examples[ph], key=lambda p: p["published"], reverse=True)
        seen, posts_out = set(), []
        for p in ex:
            if p["source"] in seen:
                continue
            seen.add(p["source"])
            posts_out.append({"name": p["name"], "title": p["title"], "url": p["url"], "date": p["published"][:10], "tier": p["tier"]})
        rows.append({"phrase": ph, "sources": n, "before": round(b, 1), "rise": round(n - b, 1),
                     "core": sum(p["tier"] == "core" for p in posts_out), "posts": posts_out[:6]})
    # langere combinatie wint als die door (bijna) dezelfde bronnen komt
    rows.sort(key=lambda r: (-r["rise"], -r["sources"], -len(r["phrase"])))
    kept = []
    for r in rows:
        if any(r["phrase"] in k["phrase"] and k["sources"] >= r["sources"] - 1 for k in kept):
            continue
        kept.append(r)
    return kept[:60]


def network_for(terms, posts, today, days=WINDOW):
    """Hoeveel verschillende bronnen publiceerden de afgelopen `days` dagen iets met een van deze termen in de titel."""
    pats = [re.compile(r"\b" + re.escape(t.lower()) + r"\b") for t in terms]
    hits = {}
    for p in posts.values():
        d = day(p["published"])
        if not d or not 0 <= (today - d).days <= days:
            continue
        t = p["title"].lower()
        if any(x.search(t) for x in pats):
            if p["source"] not in hits or p["published"] > hits[p["source"]]["published"]:
                hits[p["source"]] = p
    best = sorted(hits.values(), key=lambda p: p["published"], reverse=True)
    best.sort(key=lambda p: p["tier"] != "core")  # kernbronnen eerst, daarbinnen nieuwste eerst
    return {"sources": len(hits), "days": days, "terms": list(terms),
            "posts": [{"name": p["name"], "title": p["title"], "url": p["url"], "date": p["published"][:10]} for p in best[:6]]}


def add_google(rising, n):
    """Zet per stijger het label van de site erbij (trend_check.py), zodat de routine meteen ziet wat ook gezocht wordt."""
    import trend_check
    try:
        g = trend_check.Trends()
    except Exception as e:  # noqa: BLE001
        print(f"Google Trends niet bereikbaar ({e}); stijgers zonder label.")
        return
    for r in rising[:n]:
        try:
            s = trend_check.check(g, r["phrase"])
            r["google"] = {"label": s["label"], "text": s["text"], "geo": s["geo"], "yoy": s["yoy"], "weeks": s["weeks"]} if s else None
        except Exception as e:  # noqa: BLE001
            print(f"FOUT  {r['phrase']}: {type(e).__name__}"[:100])


def main():
    today = dt.date.today()
    sources = load_sources()
    posts = load_posts()
    n0 = len(posts)
    with cf.ThreadPoolExecutor(16) as pool:
        results = [x for batch in pool.map(fetch, sources) for x in batch]
    for src, kind, p in results:
        if not p["published"]:
            continue
        old = posts.get(p["url"])
        posts[p["url"]] = {"source": src["id"], "name": src["name"], "tier": src["tier"], "kind": kind,
                           "published": p["published"].date().isoformat(), "title": " ".join(p["title"].split()),
                           "url": p["url"], "views": p["views"], "first_seen": old["first_seen"] if old else today.isoformat()}
    cutoff = today - dt.timedelta(days=KEEP_DAYS)
    posts = {u: p for u, p in posts.items() if day(p["published"]) >= cutoff}
    with POSTS.open("w", newline="") as f:
        w = csv.DictWriter(f, COLS)
        w.writeheader()
        w.writerows(sorted(posts.values(), key=lambda p: (p["published"], p["source"]), reverse=True))
    b = buzz(posts, today)
    if "--google" in sys.argv:
        add_google(b, int(sys.argv[sys.argv.index("--google") + 1]))
    recent = [p for p in posts.values() if 0 <= (today - day(p["published"])).days <= WINDOW]
    BUZZ.write_text(json.dumps({"generated": today.isoformat(), "sources": len(sources), "window": WINDOW, "base": BASE,
                                "core": sum(s["tier"] == "core" for s in sources), "posts": len(recent),
                                "posters": len({p["source"] for p in recent}), "rising": b},
                               ensure_ascii=False, indent=1) + "\n")
    print(f"{len(sources)} bronnen gelezen, {len(posts)} berichten bewaard ({len(posts) - n0:+d}).")
    print("Stijgt in het netwerk:", ", ".join(f"{r['phrase']} ({r['sources']})" for r in b[:12]))


if __name__ == "__main__":
    main()
