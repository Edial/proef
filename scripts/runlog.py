#!/usr/bin/env python3
"""Logboek van alles wat automatisch draait, zodat we later kunnen terugkijken wat er gebeurde en wat beter kan.

- logs/runs/<datum>-<run-id>.json: één bestand per run (welke Action, gepland, te laat, duur, uitkomst, details).
- LOGBOEK.md: leesbaar overzicht per week, nieuwste eerst, gemaakt uit logs/runs/.

Zo werkt het:
1. Een Action (harvest, Instagram dagelijks, meten, nieuwsbrief) zet RUNLOG_FILE=/tmp/runlog.json. Scripts schrijven
   daar hun kerncijfers in met runlog.metric(...) (buiten een Action doet dat niets). Aan het eind uploadt de Action
   dat bestand als artifact "runlog".
2. De Action "Logboek" draait als een van die Actions klaar is (workflow_run), haalt de tijden en de uitkomst uit
   GitHub en de cijfers uit het artifact, schrijft logs/runs/… en LOGBOEK.md en commit die. Eén voor één, dus
   nooit twee tegelijk aan LOGBOEK.md. Controle wordt alleen gelogd als hij faalt.
3. De wekelijkse routine (Claude) draait buiten GitHub: haar tijd zien we aan de push van het concept (meten logt
   wanneer dat binnenkwam, tegenover 07:00).

Gebruik: python3 scripts/runlog.py metric sleutel=waarde …        cijfers toevoegen (in een Action)
         python3 scripts/runlog.py editie editions/2026-46.json --trendregel ok|niet|toch
         python3 scripts/runlog.py add <event.json> [runlog.json]  (Action Logboek)
         python3 scripts/runlog.py render                          LOGBOEK.md opnieuw maken
         python3 scripts/runlog.py backfill <runs.json>            eerdere runs (gh api …/actions/runs) zonder cijfers
"""
import datetime as dt
import json
import os
import pathlib
import re
import subprocess
import sys
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parent.parent
RUNS = ROOT / "logs" / "runs"
BOOK = ROOT / "LOGBOEK.md"
NL = ZoneInfo("Europe/Amsterdam")
LOGGED = {"Bronnen ophalen", "Instagram dagelijks", "Trends en foto's meten", "Nieuwsbrief", "Controle"}
ONLY_FAILURES = {"Controle"}
WEEKS = 12
DAYS_NL = "ma di wo do vr za zo".split()
MONTHS = "januari februari maart april mei juni juli augustus september oktober november december".split()


# ---------- in een Action: cijfers verzamelen ----------
def metric(**kw):
    """Voegt cijfers toe aan $RUNLOG_FILE (doet niets als dat niet gezet is, bijvoorbeeld lokaal)."""
    f = os.environ.get("RUNLOG_FILE")
    if not f:
        return
    p = pathlib.Path(f)
    try:
        d = json.loads(p.read_text()) if p.exists() else {}
    except ValueError:
        d = {}
    d.update({k: v for k, v in kw.items() if v is not None})
    p.write_text(json.dumps(d, ensure_ascii=False))


def edition_metrics(path, gate):
    """Wat de meting van een editie opleverde: in trek per bron, live of niet, en wanneer de routine pushte."""
    import instagram_trend
    ed = json.loads(pathlib.Path(path).read_text())
    hot = {"Nieuw", "Seizoen", "Piek", "Stijgt"}
    rs = ed.get("recipes", [])
    google = sum((r.get("spark") or {}).get("label") in hot for r in rs)
    insta = sum(instagram_trend.counts(r.get("igTrend")) for r in rs)
    either = sum((r.get("spark") or {}).get("label") in hot or instagram_trend.counts(r.get("igTrend")) for r in rs)
    labels = ", ".join(f"{(r.get('spark') or {}).get('label', '–')}{'+IG' if instagram_trend.counts(r.get('igTrend')) else ''}" for r in rs)
    # de commit die het bestand toevoegde = de push van de routine (niet de latere commit van de meting)
    pushed = (subprocess.run(["git", "log", "--diff-filter=A", "--format=%cI", "--", path], capture_output=True, text=True, cwd=ROOT).stdout.strip().splitlines() or [""])[-1]
    metric(editie=f"Nº {ed.get('number', 0):02d} ({ed.get('id')})", in_trek=f"{either} van {len(rs)}", google=google,
           instagram=insta, labels=labels, trendregel=gate, live=gate in ("ok", "toch"), concept_gepusht=pushed or None)


# ---------- Action Logboek: een run vastleggen ----------
def ts(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None


def _field(spec, lo, hi):
    out = set()
    for part in spec.split(","):
        step = 1
        if "/" in part:
            part, step = part.split("/")
            step = int(step)
        a, b = (lo, hi) if part == "*" else (map(int, part.split("-")) if "-" in part else (int(part), int(part)))
        out.update(range(a, b + 1, step))
    return out


def cron_prev(expr, before):
    """Het laatste moment vóór `before` (UTC) waarop deze cron had moeten afgaan."""
    m, h, dom, mon, dow = expr.split()[:5]
    M, H, D, MO = _field(m, 0, 59), _field(h, 0, 23), _field(dom, 1, 31), _field(mon, 1, 12)
    W = {x % 7 for x in _field(dow, 0, 7)}  # cron: 0 en 7 zijn zondag
    t = before.replace(second=0, microsecond=0)
    for _ in range(60 * 24 * 9):
        if t.minute in M and t.hour in H and t.day in D and t.month in MO and (t.isoweekday() % 7) in W:
            return t
        t -= dt.timedelta(minutes=1)
    return None


def entry_from_run(run, details=None):
    name, start, end = run["name"], ts(run.get("run_started_at") or run.get("created_at")), ts(run.get("updated_at"))
    scheduled = None
    if run.get("event") == "schedule" and run.get("path"):
        wf = ROOT / run["path"]
        cron = re.search(r'cron:\s*"([^"]+)"', wf.read_text()) if wf.exists() else None
        scheduled = cron_prev(cron.group(1), start + dt.timedelta(minutes=1)) if cron and start else None
    return {
        "workflow": name, "uitkomst": run.get("conclusion") or run.get("status"), "aanleiding": run.get("event"),
        "start": start.isoformat() if start else None, "eind": end.isoformat() if end else None,
        "duur_s": round((end - start).total_seconds()) if start and end else None,
        "gepland": scheduled.isoformat() if scheduled else None,
        "te_laat_min": round((start - scheduled).total_seconds() / 60) if scheduled and start else None,
        "run": run.get("html_url"), "run_id": run.get("id"), "details": details or {},
    }


def save(entry):
    RUNS.mkdir(parents=True, exist_ok=True)
    start = ts(entry["start"]) or dt.datetime.now(dt.timezone.utc)
    p = RUNS / f"{start:%Y-%m-%d_%H%M}-{entry['run_id']}.json"
    p.write_text(json.dumps(entry, ensure_ascii=False, indent=1) + "\n")
    return p


def add(event_path, details_path=None):
    run = json.loads(pathlib.Path(event_path).read_text())["workflow_run"]
    if run["name"] not in LOGGED:
        return print(f"{run['name']}: niet gelogd")
    if run["name"] in ONLY_FAILURES and run.get("conclusion") == "success":
        return print(f"{run['name']} geslaagd: niet gelogd (alleen als het misgaat)")
    details = {}
    if details_path and pathlib.Path(details_path).exists():
        try:
            details = json.loads(pathlib.Path(details_path).read_text())
        except ValueError:
            details = {}
    print("gelogd:", save(entry_from_run(run, details)).name)


def backfill(path):
    runs = json.loads(pathlib.Path(path).read_text())
    runs = runs.get("workflow_runs", runs)
    n = 0
    for run in runs:
        if run.get("name") in LOGGED and run.get("status") == "completed" \
                and not (run["name"] in ONLY_FAILURES and run.get("conclusion") == "success"):
            e = entry_from_run(run, {"let_op": "achteraf toegevoegd, zonder cijfers"})
            if not list(RUNS.glob(f"*-{e['run_id']}.json")):
                save(e)
                n += 1
    print(f"{n} eerdere runs toegevoegd")


# ---------- LOGBOEK.md ----------
def nl(t, fmt="%H:%M"):
    return ts(t).astimezone(NL).strftime(fmt) if t else "–"


def dur(s):
    if s is None:
        return "–"
    return f"{s // 3600} u {s % 3600 // 60:02d}" if s >= 3600 else f"{s // 60} min" if s >= 60 else f"{s} s"


def late(m):
    if m is None:
        return ""
    return "op tijd" if m < 10 else f"{m // 60} u {m % 60:02d}" if m >= 60 else f"{m} min"


SHOW = [  # (sleutel, label) in de kolom Details, in deze volgorde
    ("editie", ""), ("in_trek", "in trek"), ("google", "Google"), ("instagram", "Instagram"), ("labels", "labels"), ("trendregel", "trendregel"),
    ("live", "live"), ("concept_gepusht", "concept binnen"), ("nieuwsbrief", "nieuwsbrief"), ("onderwerp", "onderwerp"),
    ("instagram_accounts", "Instagram-accounts"), ("berichten_nieuw", "nieuwe berichten"), ("bronnen", "bronnen"),
    ("stijgers", "stijgers"), ("google_labels", "met Google-label"), ("trending", "trending op Instagram"),
    ("groeit", "waarvan groeit"), ("top", "top"), ("fout", "fout"), ("let_op", "let op"),
]


def details(d):
    out = []
    for k, label in SHOW:
        if k not in d:
            continue
        v = d[k]
        if k == "concept_gepusht":
            v = nl(v)
        if isinstance(v, bool):
            v = "ja" if v else "nee"
        out.append(f"{label}: {v}" if label else str(v))
    return " · ".join(out).replace("|", "/")


def summary(entries):
    """Eén regel per week: wat er met de editie gebeurde en wat opviel."""
    bits = []
    meten = [e for e in entries if e["workflow"] == "Trends en foto's meten" and e["details"].get("editie")]
    for e in meten:
        d = e["details"]
        bits.append(f"{d['editie']}: {'live om ' + nl(e['eind']) if d.get('live') else 'niet live (trendregel)'}"
                    f", in trek {d.get('in_trek', '?')} (Instagram {d.get('instagram', 0)})")
    mail = [e for e in entries if e["workflow"] == "Nieuwsbrief" and e["details"].get("nieuwsbrief")]
    for e in mail:
        t = ts(e["eind"]).astimezone(NL)
        bits.append(f"nieuwsbrief: {e['details']['nieuwsbrief']} ({DAYS_NL[t.weekday()]} {t:%H:%M})")
    failed = [e for e in entries if e["uitkomst"] not in ("success", "skipped", None)]
    if failed:
        bits.append(f"**{len(failed)} mislukt**")
    lates = [e["te_laat_min"] for e in entries if e.get("te_laat_min") is not None]
    if lates:
        bits.append(f"{sum(m >= 10 for m in lates)} van {len(lates)} geplande runs te laat (max {late(max(lates)) or 'op tijd'})")
    return " · ".join(bits) or "geen bijzonderheden"


def render():
    entries = []
    for p in sorted(RUNS.glob("*.json")):
        try:
            entries.append(json.loads(p.read_text()))
        except ValueError:
            continue
    entries.sort(key=lambda e: e.get("start") or "", reverse=True)
    weeks = {}
    for e in entries:
        t = ts(e["start"]).astimezone(NL)
        y, w, _ = t.isocalendar()
        weeks.setdefault((y, w), []).append(e)
    lines = ["# Logboek", "",
             "Alles wat automatisch draait, per week, nieuwste eerst. Wordt na elke run bijgewerkt door de Action *Logboek* "
             "(`scripts/runlog.py`); de losse runs staan in `logs/runs/`. Tijden in Nederlandse tijd. "
             "*Te laat* = hoeveel later dan gepland GitHub de run startte. De controle staat er alleen in als hij faalde.", ""]
    for (y, w), es in sorted(weeks.items(), reverse=True)[:WEEKS]:
        sat = dt.date.fromisocalendar(y, w, 6)
        lines += [f"## Week {w} · zaterdag {sat.day} {MONTHS[sat.month - 1]} {y}", "", f"**Samenvatting:** {summary(es)}", "",
                  "| Wanneer | Wat | Te laat | Duur | Uitkomst | Details |", "|---|---|---|---|---|---|"]
        for e in es:
            t = ts(e["start"]).astimezone(NL)
            ok = {"success": "✓ gelukt", "failure": "✗ mislukt", "cancelled": "afgebroken", "skipped": "overgeslagen"}.get(e["uitkomst"], e["uitkomst"] or "?")
            when = f"{DAYS_NL[t.weekday()]} {t:%d-%m %H:%M}"
            what = f"[{e['workflow']}]({e['run']})" if e.get("run") else e["workflow"]
            lines.append(f"| {when} | {what} | {late(e.get('te_laat_min'))} | {dur(e.get('duur_s'))} | {ok} | {details(e.get('details') or {})} |")
        lines.append("")
    BOOK.write_text("\n".join(lines))
    print(f"LOGBOEK.md: {len(entries)} runs, {min(len(weeks), WEEKS)} weken")


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "metric":
        kv = dict(a.split("=", 1) for a in args if "=" in a)
        metric(**{k: (int(v) if v.isdigit() else v) for k, v in kv.items()})
    elif cmd == "editie":
        gate = args[args.index("--trendregel") + 1] if "--trendregel" in args else "?"
        edition_metrics(args[0], gate)
    elif cmd == "add":
        add(args[0], args[1] if len(args) > 1 else None)
        render()
    elif cmd == "backfill":
        backfill(args[0])
        render()
    elif cmd == "render":
        render()
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
