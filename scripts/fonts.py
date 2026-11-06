#!/usr/bin/env python3
"""Zet de lettertypen in de site zelf (assets/fonts/), zodat bezoekers niets bij Google Fonts ophalen.

- Fraunces, Inter en IBM Plex Mono: alleen de Latijnse delen (latin en latin-ext). De browser laadt latin-ext
  alleen als een pagina zulke tekens heeft.
- Noto Serif JP en KR: alleen de tekens die op de site staan (index.html en alle edities). Google maakt die
  uitsnede met `text=`; zonder dat zijn het honderden kilobytes. Gewicht 900 (grote tekens) krijgt alle tekens,
  gewicht 700 alleen wat in de kleine namen (veld native) en het zegeltje staat; zo blijft dat bestand klein. Komen er in een nieuwe editie nieuwe tekens bij,
  dan draait dit script opnieuw (meten.yml). Een teken dat nog ontbreekt, toont de browser in een systeemletter.

Schrijft assets/fonts/fonts.css plus de woff2-bestanden. Gebruik: python3 scripts/fonts.py
"""
import hashlib
import json
import pathlib
import re
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "fonts"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
LATIN = "https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,500;1,9..144,400&family=IBM+Plex+Mono:wght@400;500&family=Inter:wght@400;500;600&display=swap"
KEEP = {"latin", "latin-ext"}
JP_RANGE = "U+3000-30FF, U+3400-4DBF, U+4E00-9FFF, U+F900-FAFF, U+FF00-FFEF"
KR_RANGE = "U+1100-11FF, U+3130-318F, U+AC00-D7AF"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def save(url, name):
    data = get(url)
    (OUT / name).write_bytes(data)
    return name, len(data)


def used_chars():
    """Alle CJK-tekens die de site kan tonen: in index.html (microseizoenen, tekens) en in de edities."""
    text = (ROOT / "index.html").read_text()
    for f in sorted((ROOT / "editions").glob("*.json")):
        text += f.read_text()
    for f in (ROOT / "data").glob("*.json"):
        text += f.read_text()
    text = json.loads(json.dumps(text))  # \\uXXXX in JSON blijven gewoon tekens
    jp = sorted({c for c in text if re.match(r"[　-ヿ㐀-䶿一-鿿豈-﫿＀-￯]", c)})
    kr = sorted({c for c in text if re.match(r"[ᄀ-ᇿ㄰-㆏가-힯]", c)})
    return "".join(jp), "".join(kr)


def native_chars():
    """Tekens in gewicht 700: de kleine Japanse/Koreaanse namen (native) en het seizoenszegeltje."""
    text = "春夏秋冬探"
    for f in sorted((ROOT / "editions").glob("*.json")):
        ed = json.loads(f.read_text())
        text += "".join(r.get("native") or "" for r in ed.get("recipes", []))
        text += (ed.get("ferment") or {}).get("native") or ""
    return text


def code_points(chars):
    return ", ".join(f"U+{ord(c):04X}" for c in chars)


def faces(css):
    """[(subset, blok)] uit de css van Google; het subset staat als commentaar boven elk blok."""
    return re.findall(r"/\*\s*([\w-]+)\s*\*/\s*(@font-face\s*{[^}]*})", css)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.woff2"):
        old.unlink()
    out_css, total, files = [], 0, {}
    # Latijnse lettertypen
    for subset, block in faces(get(LATIN).decode()):
        if subset not in KEEP:
            continue
        fam = re.search(r"font-family:\s*'([^']+)'", block).group(1)
        url = re.search(r"url\((https://[^)]+\.woff2)\)", block).group(1)
        if url not in files:
            style = re.search(r"font-style:\s*(\w+)", block).group(1)
            name = f"{fam.lower().replace(' ', '-')}-{style}-{subset}-{hashlib.sha1(url.encode()).hexdigest()[:6]}.woff2"
            files[url] = save(url, name)
            total += files[url][1]
        out_css.append(f"/* {fam} {subset} */\n" + block.replace(url, files[url][0]))
    # Japans en Koreaans: alleen de gebruikte tekens
    jp, kr = used_chars()
    small = native_chars()
    for fam, chars, rng in (("Noto Serif JP", jp, JP_RANGE), ("Noto Serif KR", kr, KR_RANGE)):
        for weight in ("900", "700"):
            sub = chars if weight == "900" else "".join(c for c in chars if c in small)
            if not sub:
                continue
            url = "https://fonts.googleapis.com/css2?" + urllib.parse.urlencode({"family": f"{fam}:wght@{weight}", "text": sub, "display": "swap"})
            for block in re.findall(r"@font-face\s*{[^}]*}", get(url).decode()):
                src = re.search(r"url\((https://[^)]+)\)", block).group(1)
                name = f"{fam.lower().replace(' ', '-')}-{weight}-{hashlib.sha1(sub.encode()).hexdigest()[:6]}.woff2"
                files[src] = save(src, name)
                total += files[src][1]
                block = re.sub(r"src:[^;]+;", f"src: url({name}) format('woff2');", block)
                # 900: het hele blok; 700: precies deze tekens (andere tekens in 700 tonen dan in 900)
                block = block.replace("}", f"  unicode-range: {rng if weight == '900' else code_points(sub)};\n}}")
                out_css.append(f"/* {fam} {weight}: {len(sub)} tekens */\n" + block)
    (OUT / "fonts.css").write_text("/* Gemaakt door scripts/fonts.py: lettertypen van de site zelf, niet van Google. */\n" + "\n".join(out_css) + "\n")
    # in index.html: de stylesheet, en de twee letters die elke pagina meteen nodig heeft vooraf laden
    names = {n for n, _ in files.values()}
    pre = [n for n in sorted(names) if n.startswith(("fraunces-normal-latin-", "inter-normal-latin-")) and "-ext-" not in n]
    head = "<!-- fonts:start (gemaakt door scripts/fonts.py) -->\n" + "".join(
        f'<link rel="preload" href="assets/fonts/{n}" as="font" type="font/woff2" crossorigin>\n' for n in pre) + \
        '<link rel="stylesheet" href="assets/fonts/fonts.css">\n<!-- fonts:end -->'
    page = (ROOT / "index.html").read_text()
    page = re.sub(r"<!-- fonts:start.*?<!-- fonts:end -->", lambda _: head, page, flags=re.S)
    (ROOT / "index.html").write_text(page)
    print(f"{len(files)} bestanden, {total / 1024:.0f} KB samen; {len(jp)} Japanse en {len(kr)} Koreaanse tekens")


if __name__ == "__main__":
    main()
