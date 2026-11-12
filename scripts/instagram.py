#!/usr/bin/env python3
"""Leest de recente Instagram-posts van de koks in data/sources.csv (kolom `instagram`) via de Instagram API
met Facebook Login, endpoint Business Discovery. Alleen standaardbibliotheek.

Business Discovery werkt met je eigen Instagram professioneel account (gekoppeld aan een Facebook-pagina) en
leest publieke posts van andere zakelijke en creator-accounts. Voor je eigen account is Standard Access genoeg:
geen App Review nodig.

Nodig (als omgevingsvariabelen of GitHub-secrets):
  IG_TOKEN     toegangstoken met instagram_basic, instagram_manage_insights en pages_read_engagement
               (en ads_read als je paginarol via Business Manager loopt)
  IG_USER_ID   het id van JOUW Instagram professioneel account (niet de gebruikersnaam)

Gebruik:
  python3 scripts/instagram.py check                  controleert token en account
  python3 scripts/instagram.py thewoksoflife          toont de laatste posts van één account
  python3 scripts/instagram.py bronnen                controleert alle handles in data/sources.csv
  python3 scripts/instagram.py profiel a b c          naam, website en bereik van nieuwe accounts (om toe te voegen)
  python3 scripts/instagram.py noemt food52           welke accounts food52 het vaakst noemt (de koks erachter)
harvest.py gebruikt read() en zet de posts in data/posts.csv met kind=instagram.

Limiet: Business Discovery telt mee in de Platform Rate Limit van Meta (200 calls per uur per gebruiker).
Eén call per handle per week blijft daar ruim onder.
"""
import csv
import datetime as dt
import json
import os
import pathlib
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
API = "https://graph.facebook.com/v26.0"
MEDIA = "caption,like_count,comments_count,timestamp,permalink,media_type"


def enabled():
    return bool(os.environ.get("IG_TOKEN") and os.environ.get("IG_USER_ID"))


def _get(path, params):
    q = urllib.parse.urlencode({**params, "access_token": os.environ["IG_TOKEN"]})
    req = urllib.request.Request(f"{API}/{path}?{q}", headers={"User-Agent": "Proef (+https://edial.github.io/proef/)"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        try:
            msg = json.load(e).get("error", {}).get("message", "")
        except Exception:  # noqa: BLE001
            msg = ""
        err = RateLimited if "limit" in msg.lower() else RuntimeError
        raise err(f"HTTP {e.code}: {msg}"[:200]) from None


class RateLimited(RuntimeError):
    """Meta zegt: te veel verzoeken. Dan stoppen we voor deze run, de rest van de harvest gaat door."""


def title_from(caption):
    """Eerste zin van het onderschrift, zonder hashtags en mentions: meestal de naam van het gerecht.
    Alleen de eerste zin, zodat lange onderschriften de woordcombinaties in buzz.json niet vervuilen."""
    first = next((line for line in (caption or "").splitlines() if line.strip()), "")
    first = re.split(r"(?<=[.!?])\s", first.strip(), maxsplit=1)[0]
    words = [w for w in first.split() if not w.startswith(("#", "@"))]
    return " ".join(words)[:140]


def handles():
    """[(bron-id, naam, tier, handle)] voor elke bron in data/sources.csv met een `instagram`-handle."""
    with (ROOT / "data" / "sources.csv").open(newline="") as f:
        return [(r["id"], r["name"], r["tier"], r["instagram"].strip().lstrip("@"))
                for r in csv.DictReader(f) if r.get("instagram", "").strip()]


def read(handle, limit=50):
    # 50 i.p.v. 25: drukke accounts (Food & Wine: 49 posts in een week) vallen anders deels buiten beeld
    """Geeft [{title, url, published (datetime), views, likes, comments}] terug, net als feeds.read()."""
    fields = f"business_discovery.username({handle}){{followers_count,media.limit({limit}){{{MEDIA}}}}}"
    data = _get(os.environ["IG_USER_ID"], {"fields": fields})["business_discovery"]
    out = []
    for m in data.get("media", {}).get("data", []):
        likes, comments = m.get("like_count"), m.get("comments_count") or 0
        out.append({"title": title_from(m.get("caption")), "url": m["permalink"],
                    "published": dt.datetime.strptime(m["timestamp"], "%Y-%m-%dT%H:%M:%S%z"),
                    # like_count ontbreekt als het account likes verbergt; dan telt alleen het aantal reacties
                    "views": "" if likes is None else str(likes + comments),
                    "likes": likes, "comments": comments, "followers": data.get("followers_count")})
    return [p for p in out if p["title"]]


def profile(handle, limit=12):
    """Naam, website, volgers en gemiddelde reacties: genoeg om te beslissen of een account erbij moet."""
    f = (f"business_discovery.username({handle}){{username,name,website,biography,followers_count,media_count,"
         f"media.limit({limit}){{like_count,comments_count,timestamp}}}}")
    d = _get(os.environ["IG_USER_ID"], {"fields": f})["business_discovery"]
    m = d.get("media", {}).get("data", [])
    eng = [(x.get("like_count") or 0) + (x.get("comments_count") or 0) for x in m]
    return {"username": d["username"], "name": d.get("name", ""), "website": d.get("website", ""),
            "bio": " ".join((d.get("biography") or "").split())[:90], "followers": d.get("followers_count"),
            "last": m[0]["timestamp"][:10] if m else "", "avg": round(sum(eng) / len(eng)) if eng else 0}


def mentions(handle, limit=50):
    """Telt de @namen in de laatste onderschriften van een account, bijvoorbeeld de koks achter een magazine."""
    f = f"business_discovery.username({handle}){{media.limit({limit}){{caption}}}}"
    caps = [x.get("caption") or "" for x in _get(os.environ["IG_USER_ID"], {"fields": f})["business_discovery"]["media"]["data"]]
    # De API laat het @-teken weg ("where noahtanen cooks it"). Daarom: woorden in kleine letters die als
    # bezitsvorm staan (noahtanen's) of na by/from/where/with/chef/and, en woorden met een punt, _ of cijfer.
    pat = re.compile(r"(?:\b(?:by|from|where|with|chef|and|via|of|to|on)\s+([a-z][a-z0-9._]{3,29})\b)"
                     r"|(?:\b([a-z][a-z0-9._]{3,29})['’]s\b)|(?:@?\b([a-z][a-z0-9]*[._][a-z0-9._]+|[a-z]+\d+[a-z0-9]*)\b)")
    common = set("""about after again also amazing another around baking because before best better bread brown butter cake
        cheese chicken chocolate classic coffee cook cooking cream crispy dinner each easy every everyone fall favorite flavor
        food fresh friends from garlic good great have home into just kitchen like little make making more most much night
        only other over perfect recipe recipes right salad sauce season simple some soup spicy sugar sweet test that their
        them then these they thing things this those time today together tomato turkey very week what when where which while
        with your yours pumpkin apple apples potato potatoes pasta rice thanksgiving holiday holidays cookies pie pies""".split())
    count = {}
    for c in caps:
        for m in set(pat.findall(c)):
            h = next(x for x in m if x).rstrip(".").lower()
            if h not in common and not h.endswith(("ing", "ed", "ly")):
                count[h] = count.get(h, 0) + 1
    return len(caps), sorted(count.items(), key=lambda x: -x[1])


def main():
    if not enabled():
        sys.exit("Zet eerst IG_TOKEN en IG_USER_ID (zie de uitleg bovenin dit bestand).")
    arg = sys.argv[1] if len(sys.argv) > 1 else "check"
    if arg == "check":
        me = _get(os.environ["IG_USER_ID"], {"fields": "username,followers_count,media_count"})
        print(f"OK: verbonden als @{me['username']} ({me.get('followers_count')} volgers, {me.get('media_count')} posts).")
        return
    if arg == "profiel":
        for h in sys.argv[2:]:
            try:
                p = profile(h.lstrip("@"))
                print(f"OK    @{p['username']:22} {p['followers']:>9} volgers  gem. {p['avg']:>6} reacties  laatste {p['last']}  "
                      f"{p['name'][:30]} | {p['website'] or '-'} | {p['bio']}")
            except Exception as e:  # noqa: BLE001
                print(f"FOUT  @{h.lstrip('@'):22} {e}"[:160])
            time.sleep(0.3)
        return
    if arg == "noemt":
        for h in sys.argv[2:]:
            n, top = mentions(h.lstrip("@"))
            print(f"@{h.lstrip('@')} noemt in {n} posts:", ", ".join(f"@{k} ({v})" for k, v in top[:30]))
        return
    if arg == "diepte":  # hoeveel dagen beslaan de posts die we per keer ophalen? (diepte 100 a b c: met 100 posts)
        n = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 50
        for h in [x for x in sys.argv[2:] if not x.isdigit()]:
            posts = read(h.lstrip("@"), n)
            if posts:
                print(f"OK    @{h.lstrip('@'):22} {len(posts)} posts, van {posts[-1]['published']:%Y-%m-%d} tot {posts[0]['published']:%Y-%m-%d}")
            time.sleep(0.3)
        return
    if arg == "bronnen":
        ok = 0
        for sid, name, tier, h in handles():
            try:
                posts = read(h, 5)
                last = max((p["published"] for p in posts), default=None)
                print(f"OK    @{h:28} {tier:7} {posts[0]['followers'] if posts else '-':>9} volgers  laatste {last:%Y-%m-%d}" if last
                      else f"LEEG  @{h:28} {tier:7} geen posts met onderschrift")
                ok += 1
            except RateLimited as e:
                print(f"LIMIET bereikt bij @{h}: {e}")
                break
            except Exception as e:  # noqa: BLE001
                print(f"FOUT  @{h:28} {tier:7} {sid}: {e}"[:160])
            time.sleep(0.3)
        print(f"{ok} van {len(handles())} handles werken.")
        return
    for p in read(arg.lstrip("@"), 10):
        print(f"{p['published']:%Y-%m-%d}  {p['views'] or '–':>7}  {p['title'][:70]}")
        time.sleep(0.2)


if __name__ == "__main__":
    main()
