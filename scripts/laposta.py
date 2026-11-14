#!/usr/bin/env python3
"""Zet de nieuwsbrief van een editie klaar in Laposta en stuurt een testmail of verstuurt hem echt.

Eerst `python3 scripts/newsletter.py <id>`: dat maakt mail/<id>/mail.html en mail.json (onderwerp, preview).
Plaatjes (logo, sparklines) komen van de site, dus mail/ moet live staan voordat iemand de mail opent.

Nodig (omgevingsvariabelen of GitHub-secrets; adressen staan bewust niet in deze openbare repo):
  LAPOSTA_API_KEY      API-sleutel (Basic auth, sleutel als gebruikersnaam)
  LAPOSTA_FROM_EMAIL   afzendadres, goedgekeurd in Laposta (Instellingen → Afzendadressen)
  LAPOSTA_FROM_NAME    afzendernaam (standaard: Proef)
  LAPOSTA_LIST         lijst-id (standaard: ug5tljseab, de lijst Proef)

Gebruik: python3 scripts/laposta.py prepare 2026-45 [naam@example.net]  echte campagne klaarzetten (+ testmail), niet versturen
         python3 scripts/laposta.py send 2026-45                         echt versturen naar de lijst
         python3 scripts/laposta.py test 2026-45 naam@example.net        losse testcampagne "(test)" met testmail
Dezelfde editie hergebruikt dezelfde, nog niet verzonden campagne. Een editie wordt nooit twee keer verstuurd:
is "Proef <id>" al verstuurd, dan stoppen prepare en send zonder iets te doen.
"""
import base64
import json
import os
import pathlib
import sys
import urllib.error
import urllib.parse
import urllib.request

import runlog

ROOT = pathlib.Path(__file__).resolve().parent.parent
API = "https://api.laposta.nl/v2"


def call(method, path, data=None):
    key = os.environ.get("LAPOSTA_API_KEY", "")
    body = urllib.parse.urlencode(data, doseq=True).encode() if data else None
    req = urllib.request.Request(f"{API}/{path}", data=body, method=method, headers={
        "Authorization": "Basic " + base64.b64encode(f"{key}:".encode()).decode(),
        "User-Agent": "Proef nieuwsbrief (+https://edial.github.io/proef/)"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        try:
            msg = json.load(e).get("error", {})
        except Exception:  # noqa: BLE001
            msg = {}
        sys.exit(f"Laposta {method} {path}: HTTP {e.code} {msg.get('message', '')} {msg.get('parameter', '')}".strip())


def campaign_for(eid, meta, test):
    """Hergebruik de onverzonden campagne van deze editie, of maak er een. Stopt als de editie al verstuurd is."""
    name = f"Proef {eid}" + (" (test)" if test else "")
    campaigns = [x["campaign"] for x in call("GET", "campaign").get("data", [])]
    sent = [c for c in campaigns if c.get("name") == f"Proef {eid}" and (c.get("delivery_started") or c.get("delivery_requested"))]
    if sent and not test:
        print(f"Editie {eid} is al verstuurd of ingepland ({sent[0].get('delivery_started') or sent[0].get('delivery_requested')}). Niets gedaan.")
        runlog.metric(nieuwsbrief="al eerder verstuurd, niets gedaan")
        sys.exit(0)
    for c in campaigns:
        if c.get("name") == name and not c.get("delivery_started") and not c.get("delivery_requested"):
            return c["campaign_id"], False
    sender = os.environ.get("LAPOSTA_FROM_EMAIL")
    if not sender:
        sys.exit("Zet LAPOSTA_FROM_EMAIL (een in Laposta goedgekeurd afzendadres).")
    c = call("POST", "campaign", [
        ("type", "regular"), ("name", name), ("subject", meta["subject"]), ("previewtext", meta["previewtext"][:120]),
        ("from[name]", os.environ.get("LAPOSTA_FROM_NAME", "Proef")), ("from[email]", sender), ("reply_to", sender),
        ("list_ids[]", os.environ.get("LAPOSTA_LIST", "ug5tljseab"))])["campaign"]
    return c["campaign_id"], True


def main():
    if len(sys.argv) < 3 or sys.argv[1] not in ("test", "prepare", "send") or (sys.argv[1] == "test" and len(sys.argv) < 4):
        sys.exit(__doc__)
    mode, eid = sys.argv[1], sys.argv[2]
    folder = ROOT / "mail" / eid
    if not (folder / "mail.html").exists():
        sys.exit(f"Eerst: python3 scripts/newsletter.py {eid}")
    meta = json.loads((folder / "mail.json").read_text())
    cid, new = campaign_for(eid, meta, mode == "test")
    if not new:  # onderwerp kan sinds de vorige keer veranderd zijn
        call("POST", f"campaign/{cid}", [("subject", meta["subject"]), ("previewtext", meta["previewtext"][:120])])
    res = call("POST", f"campaign/{cid}/content", [("html", (folder / "mail.html").read_text())])
    report = (res.get("campaign") or {}).get("report") or res.get("report")
    print(f"campagne {cid} ({'nieuw' if new else 'bijgewerkt'}): {meta['subject']}")
    runlog.metric(onderwerp=meta["subject"])
    if report:
        print("Laposta meldt bij het importeren:", json.dumps(report, ensure_ascii=False))
    if mode in ("test", "prepare"):
        if len(sys.argv) > 3 and sys.argv[3]:
            call("POST", f"campaign/{cid}/action/testmail", [("email", sys.argv[3])])
            print("testmail verstuurd")
        print("klaargezet in Laposta, nog niet verstuurd naar de lijst" if mode == "prepare" else "testcampagne bijgewerkt")
        runlog.metric(nieuwsbrief="klaargezet met testmail, nog niet verstuurd" if mode == "prepare" else "testcampagne")
    else:
        call("POST", f"campaign/{cid}/action/send")
        print("verstuurd naar de lijst")
        runlog.metric(nieuwsbrief="verstuurd naar de lijst")


if __name__ == "__main__":
    main()
