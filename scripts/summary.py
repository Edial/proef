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
    recent = [e["ferment"]["title"] for e in eds[:4] if e.get("ferment")]
    print("\nFERMENTS LAATSTE 4 EDITIES (niet herhalen):", ", ".join(recent) or "-")
    print("Kies het ferment uit de bibliotheek in FERMENTATIE.md §9.")

    if "--example" in sys.argv and eds:
        e = eds[0]
        r = dict(e["recipes"][0])
        r["ingredients"] = r["ingredients"][:3] + ["…"]
        r["steps"] = r["steps"][:2] + ["…"]
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
