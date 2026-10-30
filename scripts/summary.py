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
        "bestaat al": any(e["id"] == eid for e in eds),
    }


def buzz_and_core():
    """Wat er in het netwerk stijgt (data/buzz.json) en de nieuwste recepten van de kernbronnen (data/posts.csv)."""
    import csv
    bz = ROOT / "data" / "buzz.json"
    if bz.exists():
        b = json.loads(bz.read_text())
        print(f"\nSTIJGT IN HET NETWERK ({b['sources']} bronnen, opgehaald {b['generated']}; aantal koks laatste {b['window']} dagen, (ervoor)):")
        for r in b["rising"][:25]:
            ex = "; ".join(f"{p['name']}: {p['title']} {p['url']}" for p in r["posts"][:2])
            g = r.get("google")
            gl = f" google={g['label']}[{g['geo']}]" if g else (" google=te weinig data" if "google" in r else "")
            print(f"- {r['phrase']} {r['sources']} ({r['before']}) kern={r['core']}{gl} | {ex}")
    posts = ROOT / "data" / "posts.csv"
    if posts.exists():
        since = (dt.date.today() - dt.timedelta(days=21)).isoformat()
        with posts.open(newline="") as f:
            core = [p for p in csv.DictReader(f) if p["tier"] == "core" and p["published"] >= since]
        print(f"\nNIEUW BIJ DE KERNBRONNEN (laatste 21 dagen, {len(core)} berichten; kies hier minstens 3 recepten uit):")
        for p in core[:60]:
            print(f"- {p['published']} {p['name']}: {p['title']} {p['url']}")


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
