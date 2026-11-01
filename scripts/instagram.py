#!/usr/bin/env python3
"""Leest de recente Instagram-posts van de koks in data/sources.csv (kolom `instagram`) via de Instagram API
met Facebook Login, endpoint Business Discovery. Alleen standaardbibliotheek.

Business Discovery werkt met je eigen Instagram professioneel account (gekoppeld aan een Facebook-pagina) en
leest publieke posts van andere zakelijke en creator-accounts. Voor je eigen account is Standard Access genoeg:
geen App Review nodig.

Nodig (als omgevingsvariabelen of GitHub-secrets):
  IG_TOKEN     toegangstoken met instagram_basic en pages_read_engagement (bij voorkeur van een systeemgebruiker)
  IG_USER_ID   het id van JOUW Instagram professioneel account (niet de gebruikersnaam)

Gebruik:
  python3 scripts/instagram.py check                  controleert token en account
  python3 scripts/instagram.py thewoksoflife          toont de laatste posts van één account
harvest.py gebruikt read() en zet de posts in data/posts.csv met kind=instagram.
"""
import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

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
        raise RuntimeError(f"HTTP {e.code}: {msg}"[:200]) from None


def title_from(caption):
    """Eerste regel van het onderschrift, zonder hashtags en mentions: meestal de naam van het gerecht."""
    first = next((line for line in (caption or "").splitlines() if line.strip()), "")
    words = [w for w in first.split() if not w.startswith(("#", "@"))]
    return " ".join(words)[:140]


def read(handle, limit=25):
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


def main():
    if not enabled():
        sys.exit("Zet eerst IG_TOKEN en IG_USER_ID (zie de uitleg bovenin dit bestand).")
    arg = sys.argv[1] if len(sys.argv) > 1 else "check"
    if arg == "check":
        me = _get(os.environ["IG_USER_ID"], {"fields": "username,followers_count,media_count"})
        print(f"OK: verbonden als @{me['username']} ({me.get('followers_count')} volgers, {me.get('media_count')} posts).")
        return
    for p in read(arg.lstrip("@"), 10):
        print(f"{p['published']:%Y-%m-%d}  {p['views'] or '–':>7}  {p['title'][:70]}")
        time.sleep(0.2)


if __name__ == "__main__":
    main()
