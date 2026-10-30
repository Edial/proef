#!/usr/bin/env python3
"""Controleert data/sources.csv: zoekt per bron de feed (site en YouTube), leest hem en zet de status.

Status: ok (feed werkt, laatste bericht binnen 120 dagen) · stil (feed werkt, al lang niets) ·
        geen-feed (site werkt, geen feed gevonden) · onbereikbaar (site werkt niet).
Alleen bronnen met status ok of stil tellen mee in harvest.py.

Gebruik: python3 scripts/check_sources.py            (alleen bronnen die nog niet gecontroleerd zijn)
         python3 scripts/check_sources.py --all      (alles opnieuw, bijvoorbeeld elk kwartaal)
"""
import concurrent.futures as cf
import csv
import datetime as dt
import pathlib
import sys

import feeds

ROOT = pathlib.Path(__file__).resolve().parent.parent
CSV = ROOT / "data" / "sources.csv"


def check(row):
    now = dt.datetime.now(dt.timezone.utc)
    row = dict(row)
    feed = row["feed"] or feeds.discover(row["site"])
    yt = feeds.youtube_feed(row["youtube"]) if row["youtube"] else ""
    posts = []
    for url in (feed, yt):
        if not url:
            continue
        try:
            posts += feeds.read(url)
        except Exception:  # noqa: BLE001
            if url == feed:
                feed = ""
    row["feed"] = feed
    if yt:
        row["youtube"] = yt.rsplit("=", 1)[-1]  # handle -> kanaal-id, dan hoeft het maar één keer
    dates = [p["published"] for p in posts if p["published"]]
    last = max(dates) if dates else None
    if posts:
        row["status"] = "ok" if last and (now - last).days <= 120 else "stil"
    else:
        try:
            feeds.get(row["site"])
            row["status"] = "geen-feed"
        except Exception:  # noqa: BLE001
            row["status"] = "onbereikbaar"
    row["last_post"] = last.date().isoformat() if last else ""
    row["items"] = str(len(posts))
    row["checked"] = now.date().isoformat()
    return row


def main():
    with CSV.open(newline="") as f:
        rows = list(csv.DictReader(f))
    todo = [i for i, r in enumerate(rows) if "--all" in sys.argv or not r["checked"]]
    with cf.ThreadPoolExecutor(16) as pool:
        for i, row in zip(todo, pool.map(check, [rows[i] for i in todo])):
            rows[i] = row
    with CSV.open("w", newline="") as f:
        w = csv.DictWriter(f, rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    count = lambda tier, st: sum(r["tier"] == tier and r["status"] == st for r in rows)
    for tier in ("core", "network"):
        print(f"{tier:8} ok {count(tier, 'ok'):3}  stil {count(tier, 'stil'):3}  geen-feed {count(tier, 'geen-feed'):3}  onbereikbaar {count(tier, 'onbereikbaar'):3}")
    print(f"{len(todo)} bron(nen) gecontroleerd, {len(rows)} in totaal.")


if __name__ == "__main__":
    main()
