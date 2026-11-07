#!/usr/bin/env python3
"""Maakt de nieuwsbrief van een editie: mail/<id>/mail.html (voor Laposta), index.html (webversie op de site)
en een sparkline-PNG per recept.

Opbouw: twee kolommen op desktop (5 recepten + de fermentatie, 2×3 vakken), op een telefoon onder elkaar.
Elk beeld is even hoog: de foto staat als achtergrond in een vak van vaste hoogte (cover), met daarover een
doorzichtige afbeelding (mail/blank.png) die het vak zijn maat en alt-tekst geeft. De foto komt van de bron.

Mail-HTML is geen gewone webpagina: alleen tabellen en inline stijlen, geen SVG (Gmail haalt dat weg) en geen
JavaScript. Sparklines en logo zijn daarom PNG's, geladen vanaf de site: de map mail/ moet live
staan voordat Laposta de mail verstuurt.

Laposta zet de links /tag/unsubscribe en /tag/web in mail.html om in de afmeld- en webversielink
(de <lp-…>-tags werken alleen in sjablonen, niet in campagne-inhoud via de API).

Onderwerp en previewtekst staan in de editie: "mail": {"subject": "…", "preview": "…"} (zie REDACTIE.md).

Gebruik: python3 scripts/newsletter.py                     (nieuwste editie uit editions/index.json)
         python3 scripts/newsletter.py 2026-44 --subject "…" --preview "…"
         python3 scripts/newsletter.py 2026-44 --base http://localhost:8000/proef/   (voorbeeld lokaal)
"""
import html
import json
import pathlib
import re
import sys

from PIL import Image, ImageDraw

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = "https://edial.github.io/proef/"

INK, MUTED, RULE, SHEET, CREAM, HANKO = "#1F1D1A", "#7A7366", "#DDD6C8", "#F8F5EE", "#F8F5EE", "#C4372C"
# logo en sparklines zonder randje: kleuren die op licht én op een donkere achtergrond leesbaar zijn. Gmail kan in
# donkere modus niet wisselen naar de donkere plaatjes, dus de standaardversie moet in beide goed staan.
SPARK = "#8C8478"
# donkere modus (Apple Mail, iPhone, Outlook): zelfde kleuren als de site in het donker
D_BG, D_INK, D_MUTED, D_RULE, D_CARD = "#161412", "#EEE9DF", "#A39B8E", "#4A443B", "#2B2620"
# licht en donker van elke tint, zoals --hi en --lo op de site
TINTS = {
    "sage": ("#BFD3C7", "#2E4A6B"), "sky": ("#A9C4DE", "#2E4A6B"), "blush": ("#F3DACE", "#7E3A2C"),
    "persimmon": ("#FAD2B4", "#9C3F1F"), "mustard": ("#F7D27E", "#5B3D10"),
}
ARROW = {"Nieuw": "✦", "Seizoen": "↻", "Piek": "▲", "Stijgt": "↗", "Stabiel": "→", "Dalend": "↘"}
GOOD = {"Nieuw", "Seizoen", "Piek", "Stijgt"}
MONTHS = "januari februari maart april mei juni juli augustus september oktober november december".split()

SERIF = "Georgia, 'Times New Roman', serif"
SANS = "Helvetica, Arial, sans-serif"
MONO = "'IBM Plex Mono', Menlo, Consolas, 'Courier New', monospace"
CJK = "'Hiragino Mincho ProN', 'Yu Mincho', 'Noto Serif JP', 'Noto Serif CJK JP', 'MS Mincho', serif"
COL, PIC = 280, 200  # breedte van een vak en hoogte van elk beeld (px)


def esc(s):
    return html.escape(str(s or ""), quote=True)


def rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def spark_png(weeks, path, dark_path, w=84, h=18):
    """Lijn van 12 maanden met een rode stip op de laatste week, 2× zo scherp voor retina-schermen.
    Twee versies, allebei zonder randje: standaard warmgrijs (leesbaar op licht én als Gmail de mail donker maakt)
    en lichter warmgrijs voor mailprogramma's met een echte donkere modus."""
    s = 8  # eerst groot tekenen, dan verkleinen: gladde lijnen
    W, H, pad = w * s, h * s, 3 * s
    top = max(1, max(weeks))
    xs = [pad + i * (W - 2 * pad) / (len(weeks) - 1) for i in range(len(weeks))]
    ys = [H - pad - v / top * (H - 2 * pad) for v in weeks]
    pts, r = list(zip(xs, ys)), int(2.6 * s)
    for out, line in ((path, SPARK), (dark_path, D_MUTED)):
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.line(pts, fill=line, width=int(1.4 * s), joint="curve")
        d.ellipse([xs[-1] - r, ys[-1] - r, xs[-1] + r, ys[-1] + r], fill=HANKO)
        img.resize((w * 2, h * 2), Image.LANCZOS).save(out, optimize=True)


def logo_pngs():
    """Logo voor de mail, zonder randje: mail/proef-logo.png (hanko-rood, leesbaar op licht én in de donkere modus
    van Gmail) en mail/proef-logo-dark.png (crème, voor mailprogramma's die zelf wisselen).
    Gemaakt uit mail/proef-logo-src.png (inkt op transparant)."""
    src = ROOT / "mail" / "proef-logo-src.png"
    if not src.exists():
        return
    a = Image.open(src).convert("RGBA").split()[3]
    for name, color in (("proef-logo.png", HANKO), ("proef-logo-dark.png", D_INK)):
        img = Image.new("RGBA", a.size, rgb(color) + (0,))
        img.putalpha(a)
        img.save(ROOT / "mail" / name, optimize=True)


def pair(light, dark, w, h, alt, extra=""):
    """Twee afbeeldingen: de lichte standaard, de donkere alleen zichtbaar in donkere modus (CSS .lt/.dk)."""
    return (f'<img class="lt" src="{esc(light)}" width="{w}" height="{h}" alt="{esc(alt)}" style="display:block;border:0;{extra}">'
            f'<!--[if !mso]><!--><img class="dk" src="{esc(dark)}" width="{w}" height="{h}" alt="{esc(alt)}" '
            f'style="display:none;max-height:0;overflow:hidden;border:0;{extra}"><!--<![endif]-->')


def blank_png(path):
    """Doorzichtige pixel: houdt het fotovak op maat en draagt de alt-tekst."""
    Image.new("RGBA", (1, 1), (0, 0, 0, 0)).save(path)


def nice_date(iso):
    y, m, d = iso.split("-")
    return f"{int(d)} {MONTHS[int(m) - 1]} {y}"


def card(pic, meta, title, url, extra=""):
    """Eén vak: beeld van vaste hoogte, daaronder soort en tijd, titel en wat er verder bij hoort."""
    return f"""<div class="col" style="display:inline-block;width:100%;max-width:{COL + 20}px;vertical-align:top;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr><td style="padding:0 10px 34px;text-align:left;">
  <a href="{esc(url)}" style="display:block;text-decoration:none;">{pic}</a>
  <div class="mu" style="margin:12px 0 0;font-family:{MONO};font-size:10.5px;letter-spacing:.1em;text-transform:uppercase;color:{MUTED};">{esc(meta)}</div>
  <div style="margin:5px 0 0;font-family:{SERIF};font-size:19px;line-height:1.25;"><a class="ik" href="{esc(url)}" style="color:{INK};text-decoration:none;">{esc(title)}</a></div>
  {extra}
</td></tr></table>
</div>"""


def recipe_card(r, base, mail_url):
    url = f"{base}recept/{r['slug']}/"
    tint = r.get("tint") if r.get("tint") in TINTS else "sage"
    alt = esc(f"Foto van {r['title']}")
    if r.get("photo"):
        sizes = [x for x in r.get("photoSet") or [] if x.get("w", 0) >= 2 * COL]
        ph = esc(min(sizes, key=lambda x: x["w"])["url"] if sizes else r["photo"])  # kleinste maat die scherp genoeg is
        pic = (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>'
               f'<td class="pic" height="{PIC}" background="{ph}" style="height:{PIC}px;background-color:{TINTS[tint][0]};'
               f'background-image:url(\'{ph}\');background-size:cover;background-position:center;">'
               f'<img src="{esc(base)}mail/blank.png" width="{COL}" height="{PIC}" alt="{alt}" '
               f'style="display:block;width:100%;height:{PIC}px;border:0;"></td></tr></table>')
    else:
        pic = (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>'
               f'<td height="{PIC}" align="center" style="height:{PIC}px;background:{TINTS[tint][0]};color:{TINTS[tint][1]};'
               f'font-family:{CJK};font-size:72px;line-height:1;">{esc(r.get("glyph") or "食")}</td></tr></table>')
    sp = r.get("spark") or {}
    trend = ""
    if sp.get("weeks"):
        slug = r["slug"]
        spark_img = pair(f"{mail_url}{slug}.png", f"{mail_url}{slug}-dark.png", 84, 18, "")
        label = sp.get("label", "")
        lc = HANKO if label in GOOD else MUTED
        trend = (f'<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin:10px 0 0;"><tr>'
                 f'<td style="padding:0 10px 0 0;white-space:nowrap;font-family:{MONO};font-size:10.5px;letter-spacing:.08em;'
                 f'text-transform:uppercase;color:{lc};vertical-align:middle;">{ARROW.get(label, "•")}&nbsp;{esc(label)}</td>'
                 f'<td style="vertical-align:middle;">{spark_img}</td>'
                 f'</tr></table>'
                 f'<div class="mu" style="margin:4px 0 0;font-family:{SERIF};font-style:italic;font-size:14px;line-height:1.4;color:{MUTED};">{esc(sp.get("text"))}</div>')
    pc = r.get("photoCredit") or {}
    credit = (f'<div class="mu" style="margin:8px 0 0;font-family:{SANS};font-size:11px;color:{MUTED};">Foto: '
              f'<a class="mu" href="{esc(pc.get("url") or url)}" style="color:{MUTED};">{esc(pc["label"])}</a></div>') if pc.get("label") else ""
    meta = " · ".join(x for x in [r.get("category", ""), f'{r["minutes"]} min' if r.get("minutes") else ""] if x)
    return card(pic, meta, r["title"], url, trend + credit)


def ferment_card(f, ed, base):
    url = f"{base}#fermentatie-{ed['id']}"
    pic = (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>'
           f'<td class="fm" height="{PIC}" align="center" style="height:{PIC}px;background:{INK};color:{CREAM};'
           f'font-family:{CJK};font-size:76px;line-height:1;">{esc(f.get("glyph") or "酵")}</td></tr></table>')
    extra = f'<div class="mu" style="margin:8px 0 0;font-family:{SERIF};font-style:italic;font-size:14px;line-height:1.4;color:{MUTED};">{esc(f.get("teaser") or f.get("lede"))}</div>'
    return card(pic, "Fermentatie van de week", f["title"], url, extra)


def grid(cards):
    """Twee vakken per rij; in Outlook voor Windows (mso) met een tabel eromheen, elders inline-block."""
    rows = []
    for i in range(0, len(cards), 2):
        pair = cards[i:i + 2]
        inner = f'<!--[if mso]></td><td width="{COL + 20}" valign="top"><![endif]-->'.join(pair)
        rows.append(f'<tr><td style="padding:0;font-size:0;text-align:left;">'
                    f'<!--[if mso]><table role="presentation" width="{2 * (COL + 20)}" cellpadding="0" cellspacing="0" border="0"><tr><td width="{COL + 20}" valign="top"><![endif]-->'
                    f'{inner}<!--[if mso]></td></tr></table><![endif]--></td></tr>')
    return "\n".join(rows)


def tag_links(page, eid):
    """Links naar de site in de mail krijgen utm_medium=email: zo weet de site dat de lezer al abonnee is
    (geen aanmeld-pop-up) en zie je in statistieken wat de mail oplevert. De site haalt ze daarna uit de url."""
    utm = f"utm_source=nieuwsbrief&utm_medium=email&utm_campaign={eid}"
    def one(m):
        url, frag = m.group(1), m.group(2) or ""
        return f'href="{url}{"&" if "?" in url else "?"}{utm}{frag}"'
    return re.sub(r'href="(' + re.escape(SITE) + r'[^"#]*)(#[^"]*)?"', one, page)


def build(ed, base, subject=None, preview=None):
    out = ROOT / "mail" / ed["id"]
    out.mkdir(parents=True, exist_ok=True)
    if not (ROOT / "mail" / "blank.png").exists():
        blank_png(ROOT / "mail" / "blank.png")
    mail_url = f"{base}mail/{ed['id']}/"
    logo_pngs()
    for r in ed["recipes"]:
        if (r.get("spark") or {}).get("weeks"):
            spark_png(r["spark"]["weeks"], out / f"{r['slug']}.png", out / f"{r['slug']}-dark.png")
    cards = [recipe_card(r, base, mail_url) for r in ed["recipes"]]
    if ed.get("ferment"):
        cards.append(ferment_card(ed["ferment"], ed, base))
    m = ed.get("mail") or {}
    pre = preview or m.get("preview") or ed["intro"].split(". ")[0].rstrip(".") + "."
    subject = subject or m.get("subject") or f"Proef Nº {ed['number']:02d}: {ed['recipes'][0]['title']} en nog vier recepten"
    small = f"font-family:{MONO};font-size:10.5px;letter-spacing:.1em;text-transform:uppercase;"
    page = f"""<!doctype html>
<html lang="nl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<meta name="supported-color-schemes" content="light dark">
<title>{esc(subject)}</title>
<style>
  :root {{ color-scheme: light dark; supported-color-schemes: light dark; }}
  @media (max-width: 620px) {{ .col {{ max-width: 100% !important; }} }}
  /* donkere modus (Apple Mail, iPhone, Outlook): donkere achtergrond, lichte tekst, lichte afbeeldingen */
  @media (prefers-color-scheme: dark) {{
    .bg {{ background: {D_BG} !important; }}
    .ik {{ color: {D_INK} !important; }}
    .mu {{ color: {D_MUTED} !important; }}
    .bd {{ border-color: {D_RULE} !important; }}
    .fm {{ background: {D_CARD} !important; }}
    .lt {{ display: none !important; }}
    .dk {{ display: block !important; max-height: none !important; overflow: visible !important; }}
  }}
  /* Outlook.com en Outlook-apps in donkere modus */
  [data-ogsb] .bg {{ background: {D_BG} !important; }}
  [data-ogsc] .ik {{ color: {D_INK} !important; }}
  [data-ogsc] .mu {{ color: {D_MUTED} !important; }}
  [data-ogsc] .lt {{ display: none !important; }}
  [data-ogsc] .dk {{ display: block !important; max-height: none !important; overflow: visible !important; }}
</style>
</head>
<body class="bg" style="margin:0;padding:0;background:{SHEET};">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;">{esc(pre)}</div>
<table class="bg" role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:{SHEET};">
<tr><td class="bg" align="center" style="padding:28px 8px 32px;">
<table role="presentation" width="{2 * (COL + 20)}" cellpadding="0" cellspacing="0" border="0" style="width:100%;max-width:{2 * (COL + 20)}px;">
  <tr><td style="padding:0 10px;">
    <table class="bd" role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border-bottom:1px solid {INK};"><tr>
      <td style="padding:0 0 14px;vertical-align:bottom;"><a href="{esc(base)}">{pair(f"{base}mail/proef-logo.png", f"{base}mail/proef-logo-dark.png", 94, 32, "Proef")}</a></td>
      <td class="mu" align="right" style="padding:0 0 14px;vertical-align:bottom;{small}color:{MUTED};">Nº {ed['number']:02d} · {esc(nice_date(ed['date']))}</td>
    </tr></table>
  </td></tr>
  <tr><td class="ik" style="padding:22px 10px 30px;font-family:{SERIF};font-size:17px;line-height:1.55;color:{INK};">{esc(ed["intro"])}</td></tr>
  {grid(cards)}
  <tr><td style="padding:0 10px;">
    <div class="bd mu" style="border-top:1px solid {INK};padding:14px 0 0;font-family:{SANS};font-size:12px;line-height:1.6;color:{MUTED};">@@FOOTER@@</div>
  </td></tr>
</table>
</td></tr>
</table>
</body>
</html>
"""
    privacy = f'<a class="ik" href="{esc(base)}#privacy" style="color:{INK};">Privacy</a>'
    # mail (Laposta): /tag/unsubscribe en /tag/web zet Laposta bij het versturen om in de afmeld- en webversielink
    mail_footer = (f'Je krijgt deze mail omdat je je hebt aangemeld op <a class="mu" href="{esc(base)}" style="color:{MUTED};">edial.github.io/proef</a>.'
                   f'<div style="margin:8px 0 0;{small}"><a class="ik" href="/tag/unsubscribe" style="color:{INK};">Afmelden</a> &nbsp;·&nbsp; '
                   f'<a class="ik" href="/tag/web" style="color:{INK};">Bekijk in je browser</a> &nbsp;·&nbsp; {privacy}</div>')
    # web (de site): geen afmeldlink, wel aanmelden
    web_footer = (f'Dit is de nieuwsbrief van Proef: elke zaterdag vijf trending recepten van het seizoen (de kinderen eten mee) en een fermentatie.'
                  f'<div style="margin:8px 0 0;{small}"><a class="ik" href="{esc(base)}#nieuwsbrief" style="color:{INK};">Aanmelden</a> &nbsp;·&nbsp; {privacy}</div>')
    (out / "mail.html").write_text(tag_links(page.replace("@@FOOTER@@", mail_footer), ed["id"]))
    (out / "index.html").write_text(page.replace("@@FOOTER@@", web_footer))
    meta = {"subject": subject, "previewtext": pre[:120], "url": f"{SITE}mail/{ed['id']}/"}
    (out / "mail.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n")
    return out, meta, len(page.encode())


def opt(name):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else None


def main():
    flags = {"--base", "--subject", "--preview"}
    args, skip = [], False
    for a in sys.argv[1:]:
        if skip:
            skip = False
        elif a in flags:
            skip = True
        else:
            args.append(a)
    eid = args[0] if args else json.loads((ROOT / "editions" / "index.json").read_text())["editions"][0]
    ed = json.loads((ROOT / "editions" / f"{eid}.json").read_text())
    out, meta, size = build(ed, opt("--base") or SITE, opt("--subject"), opt("--preview"))
    print(f"{out.relative_to(ROOT)}/index.html ({size / 1024:.0f} KB; Gmail knipt af boven 102 KB)")
    print(f"onderwerp: {meta['subject']}\npreview:   {meta['previewtext']}")


if __name__ == "__main__":
    main()
