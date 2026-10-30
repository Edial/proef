"""Gedeelde code voor de bronnenlijst: feeds vinden, ophalen en lezen (RSS, Atom, YouTube). Alleen standaardbibliotheek."""
import datetime as dt
import email.utils
import html
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 Chrome/126 Safari/537.36 (Proef feedlezer; +https://edial.github.io/proef/)"
NS = {"atom": "http://www.w3.org/2005/Atom", "media": "http://search.yahoo.com/mrss/", "dc": "http://purl.org/dc/elements/1.1/"}


def get(url, timeout=15, limit=3_000_000):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*", "Cookie": "CONSENT=YES+1; SOCS=CAI"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.geturl(), r.read(limit).decode("utf-8", "replace")


def looks_like_feed(text):
    head = text[:2000].lower()
    return "<rss" in head or "<feed" in head or "<rdf:rdf" in head


def discover(site):
    """Zoekt de feed van een site: eerst <link rel=alternate>, dan de gebruikelijke adressen."""
    try:
        final, page = get(site)
        if looks_like_feed(page):
            return final
        for m in re.finditer(r"<link[^>]+>", page[:200_000], re.I):
            tag = m.group(0)
            if re.search(r"rel=[\"']?alternate", tag, re.I) and re.search(r"(rss|atom)\+xml", tag, re.I):
                href = re.search(r"href=[\"']([^\"']+)", tag, re.I)
                if href and "comments" not in href.group(1):
                    return urllib.parse.urljoin(final, html.unescape(href.group(1)))
    except Exception:  # noqa: BLE001
        pass
    base = site.rstrip("/")
    for path in ("/feed", "/feed/", "/rss", "/rss.xml", "/feed.xml", "/atom.xml", "/index.xml"):
        try:
            final, text = get(base + path)
            if looks_like_feed(text):
                return final
        except Exception:  # noqa: BLE001
            continue
    return ""


def youtube_feed(handle):
    """@handle -> feed-url van het kanaal (of '' als het niet lukt)."""
    if not handle:
        return ""
    if handle.startswith("UC"):
        return "https://www.youtube.com/feeds/videos.xml?channel_id=" + handle
    try:
        _, page = get("https://www.youtube.com/@" + handle.lstrip("@"))
        m = re.search(r'"(?:channelId|externalId)":"(UC[\w-]{22})"', page)
        return "https://www.youtube.com/feeds/videos.xml?channel_id=" + m.group(1) if m else ""
    except Exception:  # noqa: BLE001
        return ""


def _date(s):
    if not s:
        return None
    s = s.strip()
    try:
        d = email.utils.parsedate_to_datetime(s)
    except (TypeError, ValueError):
        try:
            d = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
        except ValueError:
            return None
    return (d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)).astimezone(dt.timezone.utc)


def _text(el, path):
    x = el.find(path, NS)
    return (x.text or "").strip() if x is not None and x.text else ""


def parse(text):
    """Geeft [{title, url, published (datetime), views}] terug."""
    text = re.sub(r"^[^<]+", "", text)  # BOM of rommel voor de xml
    root = ET.fromstring(text.encode("utf-8"))
    items = []
    for it in root.iter("item"):  # RSS
        items.append({"title": _text(it, "title"), "url": _text(it, "link"),
                      "published": _date(_text(it, "pubDate") or _text(it, "dc:date")), "views": ""})
    for e in root.iter("{http://www.w3.org/2005/Atom}entry"):  # Atom en YouTube
        link = next((l.get("href") for l in e.findall("atom:link", NS) if l.get("rel", "alternate") == "alternate"), "")
        stats = e.find("media:group/media:community/media:statistics", NS)
        items.append({"title": _text(e, "atom:title"), "url": link,
                      "published": _date(_text(e, "atom:published") or _text(e, "atom:updated")),
                      "views": stats.get("views", "") if stats is not None else ""})
    return [i for i in items if i["title"] and i["url"]]


def read(url):
    _, text = get(url)
    return parse(text)
