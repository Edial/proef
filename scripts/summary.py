#!/usr/bin/env python3
"""Compact overzicht voor de wekelijkse run, zodat niemand hele edities hoeft te lezen.

Gebruik: python3 scripts/summary.py            overzicht + volgende editie
         python3 scripts/summary.py --example  plus een ingekort voorbeeldrecept en -ferment
"""
import datetime as dt
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
ED = ROOT / "editions"
COVERS = ["navy", "ink", "kaki", "moss"]


def load():
    ids = json.loads((ED / "index.json").read_text())["editions"]
    return [json.loads((ED / f"{i}.json").read_text()) for i in ids if (ED / f"{i}.json").exists()]


def next_edition(eds):
    today = dt.datetime.now(dt.timezone(dt.timedelta(hours=1))).date()  # benadering van Europe/Amsterdam
    sat = today + dt.timedelta(days=(5 - today.weekday()) % 7)
    y, w, _ = sat.isocalendar()
    eid = f"{y}-{w:02d}"
    last = eds[0] if eds else {}
    used = (last.get("cover") or {}).get("color")
    color = next((c for c in COVERS[COVERS.index(used) + 1:] + COVERS if c != used), "navy") if used in COVERS else "navy"
    return {
        "id": eid, "date": sat.isoformat(), "year": y, "week": w,
        "number": max((e["number"] for e in eds), default=0) + 1,
        "cover.color (suggestie)": color,
        # ook een concept (nog niet live, wacht op de meting of haalde de trendregel niet) telt: niet opnieuw maken
        "bestaat al": any(e["id"] == eid for e in eds) or (ED / f"{eid}.json").exists(),
    }


def buzz_and_core():
    """Wat er in het netwerk stijgt (data/buzz.json) en de nieuwste recepten van de kernbronnen (data/posts.csv)."""
    import csv
    bz = ROOT / "data" / "buzz.json"
    if bz.exists():
        b = json.loads(bz.read_text())
        print(f"\nSTIJGT IN HET NETWERK ({b['sources']} bronnen, opgehaald {b['generated']}; aantal koks laatste {b['window']} dagen, (ervoor)):")
        print("  TRENDREGEL: minstens 3 recepten horen bij een stijger met google=Nieuw, Seizoen, Piek of Stijgt, met die stijger als "
              "EERSTE trendTerm (letterlijk zoals hier). Anders gaat de editie niet live.")
        for r in b["rising"][:40]:
            ex = "; ".join(f"{p['name']}: {p['title']} {p['url']}" for p in r["posts"][:2])
            g = r.get("google")
            gl = f" google={g['label']}[{g['geo']}]" if g else (" google=te weinig data" if "google" in r else "")
            print(f"- {r['phrase']} {r['sources']} ({r['before']}) kern={r['core']}{gl} | {ex}")
    posts = ROOT / "data" / "posts.csv"
    if posts.exists():
        since = (dt.date.today() - dt.timedelta(days=21)).isoformat()
        with posts.open(newline="") as f:
            rows = list(csv.DictReader(f))
        core = [p for p in rows if p["tier"] == "core" and p["published"] >= since and p["kind"] != "instagram"]
        print(f"\nNIEUW BIJ DE KERNBRONNEN (laatste 21 dagen, {len(core)} recepten van hun eigen site; kies hier minstens 3 recepten uit):")
        for p in core[:60]:
            print(f"- {p['published']} {p['name']}: {p['title']} {p['url']}")
        instagram_hits(rows)


def instagram_hits(rows, days=14, top=12):
    """Instagram-posts die het veel beter doen dan normaal voor die kok (likes + reacties t.o.v. de mediaan van
    het account). Zo tellen kleine koks even zwaar als grote. Alleen een signaal: het recept zelf komt van de eigen site."""
    import statistics
    ig = [p for p in rows if p["kind"] == "instagram" and p["views"].isdigit()]
    per = {}
    for p in ig:
        per.setdefault(p["source"], []).append(int(p["views"]))
    med = {s: statistics.median(v) for s, v in per.items() if len(v) >= 8}
    since = (dt.date.today() - dt.timedelta(days=days)).isoformat()
    hits = [(int(p["views"]) / med[p["source"]], p) for p in ig
            if p["published"] >= since and med.get(p["source"]) and int(p["views"]) >= 2 * med[p["source"]]]
    hits.sort(key=lambda x: -x[0])
    if hits:
        print(f"\nUITSCHIETERS OP INSTAGRAM (laatste {days} dagen, minstens 2× zoveel reacties als normaal voor die kok; "
              "alleen een signaal, zoek het recept op de eigen site van de maker):")
    for r, p in hits[:top]:
        print(f"- {p['published']} {p['name']} ({r:.1f}× normaal): {p['title']} {p['url']}")


def main():
    eds = load()
    print("VOLGENDE EDITIE:", json.dumps(next_edition(eds), ensure_ascii=False))
    print("\nARCHIEF (nieuwste eerst). Gebruik geen slug of gerecht opnieuw.")
    for e in eds:
        c = e.get("cover") or {}
        print(f"- {e['id']} Nº{e['number']:02d} cover={c.get('color', '-')}/{c.get('glyph', '-')}")
        for r in e["recipes"]:
            print(f"    {r['slug']} | {r['title']} | {r.get('category', '')} | {r.get('tint', '')} | {r.get('glyph', '')}")
        f = e.get("ferment")
        if f:
            print(f"    ferment: {f['title']} (slug {f['slug']}, usedIn {f.get('usedIn', '-')})")
    buzz_and_core()
    recent = [e["ferment"]["title"] for e in eds[:4] if e.get("ferment")]
    print("\nFERMENTS LAATSTE 4 EDITIES (niet herhalen):", ", ".join(recent) or "-")
    print("Kies het ferment uit de bibliotheek in FERMENTATIE.md §9.")

    if "--example" in sys.argv and eds:
        e = eds[0]
        r = dict(e["recipes"][0])
        r["ingredients"] = r["ingredients"][:3] + ["…"]
        r["steps"] = r["steps"][:2] + ["…"]
        if r.get("spark"):
            r["spark"] = "… (maakt trends_collect.py, niet zelf schrijven)"
        print("\nVOORBEELD RECEPT (ingekort):")
        print(json.dumps(r, ensure_ascii=False, indent=1))
        if e.get("ferment"):
            f = dict(e["ferment"])
            for k in ("ingredients", "steps", "timeline", "science"):
                if k in f:
                    f[k] = f[k][:2] + ["…"]
            print("\nVOORBEELD FERMENT (ingekort):")
            print(json.dumps(f, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
