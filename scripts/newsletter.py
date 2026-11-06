#!/usr/bin/env python3
"""Maakt de nieuwsbrief van een editie: mail/<id>/mail.html (voor Laposta), index.html (webversie op de site)
en een sparkline-PNG per recept.

Mail-HTML is geen gewone webpagina: alleen tabellen en inline stijlen, geen SVG (Gmail haalt dat weg) en geen
JavaScript. De sparklines worden daarom PNG's (Pillow), net als het logo (mail/proef-logo.png). Alles wordt
geladen vanaf de site, dus de map mail/ moet live staan voordat Laposta de mail verstuurt.

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
import sys

from PIL import Image, ImageDraw

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = "https://edial.github.io/proef/"

INK, MUTED, RULE, BOARD, SHEET, CREAM, HANKO = "#1F1D1A", "#7A7366", "#DDD6C8", "#E8E4DB", "#F8F5EE", "#F8F5EE", "#C4372C"
# tint van het recept: achtergrond, tekst, lijnkleur (zelfde als de tegels op de site)
TINTS = {
    "sage": ("#BFD3C7", INK, "#2E4A6B"), "sky": ("#A9C4DE", INK, "#2E4A6B"), "blush": ("#EBC9BA", INK, "#7E3A2C"),
    "persimmon": ("#D8693E", CREAM, CREAM), "mustard": ("#F0B23B", INK, "#5B3D10"),
}
ARROW = {"Nieuw": "✦", "Seizoen": "↻", "Piek": "▲", "Stijgt": "↗", "Stabiel": "→", "Dalend": "↘"}
GOOD = {"Nieuw", "Seizoen", "Piek", "Stijgt"}
MONTHS = "januari februari maart april mei juni juli augustus september oktober november december".split()

SERIF = "Georgia, 'Times New Roman', serif"
SANS = "Helvetica, Arial, sans-serif"
MONO = "'IBM Plex Mono', Menlo, Consolas, 'Courier New', monospace"


def esc(s):
    return html.escape(str(s or ""), quote=True)


def spark_png(weeks, color, path, w=120, h=28):
    """Lijn van 12 maanden met een rode stip op de laatste week, 2× zo scherp voor retina-schermen."""
    s = 8  # eerst groot tekenen, dan verkleinen: gladde lijnen
    W, H, pad = w * s, h * s, 4 * s
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    top = max(1, max(weeks))
    xs = [pad + i * (W - 2 * pad) / (len(weeks) - 1) for i in range(len(weeks))]
    ys = [H - pad - v / top * (H - 2 * pad) for v in weeks]
    d.line(list(zip(xs, ys)), fill=color, width=int(1.6 * s), joint="curve")
    r = 3 * s
    d.ellipse([xs[-1] - r, ys[-1] - r, xs[-1] + r, ys[-1] + r], fill=HANKO)
    img.resize((w * 2, h * 2), Image.LANCZOS).save(path, optimize=True)


def nice_date(iso):
    y, m, d = iso.split("-")
    return f"{int(d)} {MONTHS[int(m) - 1]} {y}"


def recipe_block(r, base, mail_url):
    bg, fg, line = TINTS.get(r.get("tint"), (SHEET, INK, INK))
    soft = "rgba(248,245,238,.85)" if fg == CREAM else "rgba(31,29,26,.72)"
    url = f"{base}recept/{r['slug']}/"
    credit = (r.get("photoCredit") or {}).get("label")
    photo = ""
    if r.get("photo"):
        photo = (f'<tr><td style="padding:0;background:{bg};"><a href="{esc(url)}"><img src="{esc(r["photo"])}" width="600" alt="Foto van {esc(r["title"])}" '
                 f'style="display:block;width:100%;max-width:600px;height:auto;border:0;"></a></td></tr>')
    sp = r.get("spark") or {}
    trend = ""
    if sp.get("weeks"):
        label = sp.get("label", "")
        lc = (HANKO if fg == INK else CREAM) if label in GOOD else soft
        trend = (f'<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin:16px 0 0;border-top:1px solid {soft};width:100%;"><tr>'
                 f'<td width="1%" style="padding:10px 12px 0 0;white-space:nowrap;font-family:{MONO};font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:{lc};vertical-align:middle;">'
                 f'{ARROW.get(label, "•")}&nbsp;{esc(label)}</td>'
                 f'<td style="padding:10px 0 0;vertical-align:middle;width:120px;"><img src="{esc(mail_url)}{esc(r["slug"])}.png" width="120" height="28" alt="" style="display:block;border:0;"></td>'
                 f'<td width="100%" style="padding:10px 0 0;">&nbsp;</td></tr>'
                 f'<tr><td colspan="3" style="padding:4px 0 0;font-family:{SERIF};font-style:italic;font-size:15px;line-height:1.4;color:{soft};">{esc(sp.get("text"))}</td></tr></table>')
    meta = " · ".join(x for x in [r.get("category", ""), f'{r["minutes"]} min' if r.get("minutes") else ""] if x)
    return f"""
<tr><td style="padding:0 0 28px;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:{bg};">
    {photo}
    <tr><td style="padding:22px 24px 24px;background:{bg};color:{fg};">
      <div style="font-family:{MONO};font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:{soft};">{esc(meta)}</div>
      <h2 style="margin:8px 0 0;font-family:{SERIF};font-weight:normal;font-size:26px;line-height:1.15;letter-spacing:-.01em;color:{fg};">
        <a href="{esc(url)}" style="color:{fg};text-decoration:none;">{esc(r["title"])}</a></h2>
      <p style="margin:10px 0 0;font-family:{SERIF};font-size:16px;line-height:1.5;color:{fg};">{esc(r.get("dek"))}</p>
      {trend}
      <p style="margin:18px 0 0;font-family:{MONO};font-size:12px;letter-spacing:.1em;text-transform:uppercase;">
        <a href="{esc(url)}" style="color:{fg};text-decoration:underline;text-underline-offset:3px;">Naar het recept →</a></p>
      {f'<p style="margin:10px 0 0;font-family:{SANS};font-size:11.5px;color:{soft};">Naar een recept van {esc(credit)}</p>' if credit else ""}
    </td></tr>
  </table>
</td></tr>"""


def build(ed, base, subject=None, preview=None):
    out = ROOT / "mail" / ed["id"]
    out.mkdir(parents=True, exist_ok=True)
    mail_url = f"{base}mail/{ed['id']}/"
    for r in ed["recipes"]:
        sp = r.get("spark") or {}
        if sp.get("weeks"):
            spark_png(sp["weeks"], TINTS.get(r.get("tint"), (0, 0, INK))[2], out / f"{r['slug']}.png")
    f = ed.get("ferment")
    ferment = ""
    if f:
        ferment = f"""
<tr><td style="padding:0 0 28px;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:{INK};">
    <tr><td style="padding:26px 24px;color:{CREAM};">
      <div style="font-family:{MONO};font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:#E8A07A;">Fermentatie van de week</div>
      <h2 style="margin:8px 0 0;font-family:{SERIF};font-weight:normal;font-size:26px;line-height:1.15;color:{CREAM};">{esc(f["title"])}</h2>
      <p style="margin:10px 0 0;font-family:{SERIF};font-size:16px;line-height:1.5;color:{CREAM};">{esc(f.get("teaser") or f.get("lede"))}</p>
      <p style="margin:18px 0 0;font-family:{MONO};font-size:12px;letter-spacing:.1em;text-transform:uppercase;">
        <a href="{esc(base)}#fermentatie-{esc(ed["id"])}" style="color:{CREAM};text-decoration:underline;text-underline-offset:3px;">Zo maak je het →</a></p>
    </td></tr>
  </table>
</td></tr>"""
    m = ed.get("mail") or {}
    pre = preview or m.get("preview") or ed["intro"].split(". ")[0].rstrip(".") + "."
    subject = subject or m.get("subject") or f"Proef Nº {ed['number']:02d}: {ed['recipes'][0]['title']} en nog vier recepten"
    page = f"""<!doctype html>
<html lang="nl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light">
<meta name="supported-color-schemes" content="light">
<title>{esc(subject)}</title>
</head>
<body style="margin:0;padding:0;background:{BOARD};">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;">{esc(pre)}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:{BOARD};">
<tr><td align="center" style="padding:24px 12px;">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" style="width:100%;max-width:600px;">
  <tr><td style="padding:4px 0 18px;border-bottom:1px solid {INK};">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
      <td style="vertical-align:bottom;"><a href="{esc(base)}"><img src="{esc(base)}mail/proef-logo.png" width="118" height="40" alt="Proef" style="display:block;border:0;"></a></td>
      <td align="right" style="vertical-align:bottom;font-family:{MONO};font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:{MUTED};">Nº {ed['number']:02d} · week {ed['week']}<br>{esc(nice_date(ed['date']))}</td>
    </tr></table>
  </td></tr>
  <tr><td style="padding:26px 0 28px;">
    <div style="font-family:{MONO};font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:{HANKO};">Deze week</div>
    <p style="margin:10px 0 0;font-family:{SERIF};font-size:21px;line-height:1.45;color:{INK};">{esc(ed["intro"])}</p>
  </td></tr>
  {"".join(recipe_block(r, base, mail_url) for r in ed["recipes"])}
  {ferment}
  <tr><td style="padding:6px 0 0;border-top:1px solid {INK};font-family:{SANS};font-size:12.5px;line-height:1.6;color:{MUTED};">
    @@FOOTER@@
  </td></tr>
</table>
</td></tr>
</table>
</body>
</html>
"""
    small = f'font-family:{MONO};font-size:11px;letter-spacing:.08em;text-transform:uppercase;'
    privacy = f'<a href="{esc(base)}#privacy" style="color:{INK};">Privacy</a>'
    # mail (Laposta): /tag/unsubscribe en /tag/web zet Laposta bij het versturen om in de afmeld- en webversielink
    mail_footer = (f'<p style="margin:14px 0 0;">Je krijgt deze mail omdat je je hebt aangemeld op <a href="{esc(base)}" style="color:{MUTED};">edial.github.io/proef</a>. '
                   f'Elke zaterdag vijf trending recepten, gemeten met Google Trends en wat koks nu maken.</p>'
                   f'<p style="margin:10px 0 0;{small}"><a href="/tag/unsubscribe" style="color:{INK};">Afmelden</a> &nbsp;·&nbsp; '
                   f'<a href="/tag/web" style="color:{INK};">Bekijk in je browser</a> &nbsp;·&nbsp; {privacy}</p>')
    # web (de site): geen afmeldlink, wel aanmelden
    web_footer = (f'<p style="margin:14px 0 0;">Dit is de nieuwsbrief van Proef, elke zaterdag met vijf trending recepten. Wil je hem ook krijgen?</p>'
                  f'<p style="margin:10px 0 0;{small}"><a href="{esc(base)}#nieuwsbrief" style="color:{INK};">Aanmelden</a> &nbsp;·&nbsp; {privacy}</p>')
    (out / "mail.html").write_text(page.replace("@@FOOTER@@", mail_footer))
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
