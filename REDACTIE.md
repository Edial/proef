# Redactie: zo maak je een editie

Elke zaterdag verschijnt een nieuwe editie van Proef. Dit document is de vaste werkwijze, voor mensen én voor de wekelijkse Claude-routine. De site laadt vanzelf alles wat in `editions/index.json` staat. Een editie is pas live als dat bestand is bijgewerkt en naar `main` is gepusht.

## Wat Proef is

Vijf recepten die deze week trending zijn, plus één Fermentatie van de week. Weinig werk, veel Aziatisch, groente van het seizoen en goed te maken met kinderen. Alles in grammen, milliliters en °C. De recepten zijn in eigen woorden in het Nederlands herschreven. Foto's worden getoond vanaf de bron, met naam en link, en niet gekopieerd.

## Stappen

1. **Bepaal de editie.** `id` is `<jaar>-<ISO-week>` van de zaterdag van verschijnen (bijv. `2026-44`), `date` is die zaterdag, en `number` is het vorige nummer + 1. Bestaat het bestand al, stop dan: niets dubbel publiceren.
2. **Zoek de trends van deze week** (Pinterest, Google Trends, TikTok, foodmedia). Kies 5 recepten:
   - minstens 2 Aziatisch (Japans, Koreaans, Chinees, Zuidoost-Aziatisch);
   - minstens 3 met groente van het seizoen in Nederland;
   - allemaal goed te doen met kinderen, met een `tip` voor de kinderversie;
   - niet meer dan 60 minuten, tenzij de oven het werk doet;
   - verschillende categorieën: niet vijf hoofdgerechten;
   - geen gerecht dat al in een eerdere editie stond (de validator controleert slugs, controleer ook de gerechten zelf).
3. **Per recept:** zoek een bronrecept met een foto (`photo` = directe https-link naar de afbeelding, `photoCredit` = naam en link). Herschrijf het in eigen woorden, reken alles om naar g/ml/°C en controleer of de hoeveelheden kloppen voor het aantal personen.
4. **Vormgeving per recept:**
   - `tint`: gebruik elke kleur één keer (`sage`, `sky`, `blush`, `persimmon`, `mustard`). Kies de kleur die bij het gerecht past.
   - `glyph`: één Japans of Koreaans teken dat het gerecht samenvat (bijv. 汁 soep, 밥 rijst, 麺 noedels, 菜 groente, 卵 ei).
   - `native` + `roman`: de naam in het Japans of Koreaans met uitspraak. Alleen als je het zeker weet; anders leeg laten.
   - `trend`: `source` (bijv. TikTok, Pinterest; op de site staat "Gezien op …") + één rustige zin van **hooguit 10 woorden** waarom het nu gemaakt wordt. Schrijf als een vaststelling, niet als reclame: geen superlatieven of hypewoorden ("hét", "grootste", "viral", "is in", "must"). **Geen kale percentages**: schrijf "veel meer gezocht", niet "+110%". Goed: "Wordt nu veel gemaakt, nu het kouder wordt."
   - `signal.text` + `links`: de langere uitleg en de bronnen voor "Waarom deze week".
5. **Fermentatie van de week:** kies uit de bibliotheek in **[FERMENTATIE.md](FERMENTATIE.md) §9** en vink de checklist in §8 helemaal af. Herhaal geen ferment uit de laatste 4 edities. Koppel het ferment met `usedIn` aan een recept van deze editie als dat kan. Zet de geraadpleegde bronnen in `sources`.
6. **Omslag:** `cover.color` is anders dan vorige week (`navy`, `ink`, `kaki`, `moss`). `cover.glyph` is één teken voor het thema van de week (standaard 旬, "in het seizoen").
7. **Controleer:** `python3 scripts/check_photos.py editions/<id>.json` (alle foto's moeten werken), daarna `python3 scripts/photo_light.py editions/<id>.json` (zet `photoGamma`, zodat alle foto's even licht zijn; vereist `pip install pillow`) en `python3 scripts/check_edition.py` (0 fouten).
8. **Publiceer:** voeg het id vooraan toe in `editions/index.json`, commit als `Proef: editie NN (week WW)` en push naar `main`. GitHub Pages zet het binnen een paar minuten live.

## Wekelijkse run (Claude-routine): zuinig werken

De routine draait elke zaterdag om 06:00. Elke stap kost tokens, en alles wat je inleest wordt bij elke volgende stap opnieuw meegestuurd. Daarom:

1. **Begin met `python3 scripts/summary.py --example`.** Dat geeft de volgende id, datum en nummer, alle eerdere recepten en ferments, en een ingekort voorbeeld. Lees **niet** de volledige edities, `index.html` of de broncode van de scripts.
2. **Lees alleen** deze REDACTIE.md en van FERMENTATIE.md §1, §6, §8 en §9.
3. **Zoeken:** gebruik WebSearch in `standard`-modus (niet `extended`), **maximaal 8 zoekopdrachten** in totaal. Stuur ze tegelijk in één beurt.
4. **Pagina's openen:** maximaal 10 keer WebFetch, alleen voor pagina's die je echt gebruikt (bronrecept, trendbron). Vraag in de prompt alleen wat je nodig hebt.
5. **Ferment:** kies uit de bibliotheek in FERMENTATIE.md §9, geen nieuw onderzoek. Schrijf het ferment met de cijfers uit de tabel. De bronlinks controleert `check_photos.py`.
6. **Schrijf de editie in één keer** met Write. Draai daarna `python3 scripts/check_photos.py editions/<id>.json`, `python3 scripts/photo_light.py editions/<id>.json` en `python3 scripts/check_edition.py`. Herstel alleen wat de scripts melden.
7. **Publiceer** zoals in stap 8 hierboven en sluit af met een verslag van hooguit 15 regels.

## Velden van een editie

```jsonc
{
  "id": "2026-44", "number": 2, "year": 2026, "week": 44, "date": "2026-10-31",
  "intro": "Twee, drie zinnen over deze week.",
  "cover": { "color": "ink", "glyph": "旬" },
  "recipes": [
    {
      "slug": "uniek-over-alle-edities",       // wordt de link: /#slug
      "title": "…", "dek": "…", "category": "Hoofdgerecht",
      "minutes": 30, "servings": 4,             // optioneel: "servingsLabel": "stuks"
      "tags": ["Aziatisch", "Kindvriendelijk", "Weinig werk", "Seizoen"],
      "tint": "sage", "glyph": "菜", "native": "キャベツ", "roman": "kyabetsu",
      "trend": { "source": "Pinterest", "text": "…" },
      "signal": { "source": "…", "text": "…" },
      "links": [{ "label": "…", "url": "https://…" }],
      "photo": "https://…jpg", "photoCredit": { "label": "…", "url": "https://…" },
      "photoGamma": 0.62,  // door scripts/photo_light.py, niet zelf invullen
      "ingredients": [{ "qty": 200, "unit": "g", "item": "…", "group": "Saus (optioneel)" }],
      "steps": ["…"], "tip": "…"
    }
  ],
  "ferment": {
    "number": 2, "slug": "uniek", "title": "…", "glyph": "酵", "native": "…", "roman": "…",
    "lede": "…", "teaser": "…", "yield": "1 pot van 1 liter",
    "facts": [{ "label": "Aanrecht", "value": "1–2 dagen, 18–22 °C" }],
    "usedIn": "slug-van-een-recept",
    "science": ["…"], "timeline": [{ "when": "Dag 0", "title": "…", "text": "…", "now": false }],
    "ingredients": [{ "qty": 20, "unit": "g", "item": "zeezout zonder jodium …" }],
    "steps": ["…"], "ok": "…", "bad": "…", "kids": "…",
    "sources": [{ "label": "…", "url": "https://…" }]
  }
}
```

Eenheden: alleen `g`, `ml` of leeg (stuks). Geen kopjes, ounces of °F.
