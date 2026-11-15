# Redactie: zo maak je een editie

Elke zaterdag verschijnt een nieuwe editie van Proef. Dit document is de vaste werkwijze, voor mensen én voor de wekelijkse Claude-routine. De site laadt alles wat in `editions/index.json` staat. **Dat bestand werk je niet zelf bij.** Je pusht alleen `editions/<id>.json`: dat is een concept. De Action *Trends en foto's meten* meet het, toetst de trendregel en zet het pas daarna live (id in `index.json`, receptpagina's, sitemap). Daarna volgt de nieuwsbrief. Haalt het concept de trendregel niet, dan gaat het niet live, komt er een issue op GitHub en gaat er geen nieuwsbrief uit.

## Wat Proef is

Tagline: *Vijf trending recepten van het seizoen. De kinderen eten mee.* Vanaf Nº 05 is Proef **het beste van Instagram**: elke zaterdag vier gerechten en één baksel of zoet die bij de makers die we volgen een hit zijn, plus één Fermentatie van de week. Weinig werk, liefst wat Aziatisch en goed te maken met kinderen. Alles in grammen, milliliters en °C. De recepten zijn in eigen woorden in het Nederlands herschreven. Foto's worden getoond vanaf de bron, met naam en link, en niet gekopieerd.

## Stappen

1. **Bepaal de editie.** `id` is `<jaar>-<ISO-week>` van de zaterdag van verschijnen (bijv. `2026-44`), `date` is die zaterdag, en `number` is het vorige nummer + 1. Bestaat het bestand al, stop dan: niets dubbel publiceren.
2. **Kies uit de hits op Instagram** (vanaf Nº 05). `scripts/summary.py` toont **TRENDING OP INSTAGRAM: DE KANDIDATEN**: posts van de makers die we volgen die minstens 5× zoveel likes en reacties halen als normaal voor dat account (tot 4 weken oud), of een oudere post die deze week sterk groeit. Elke dag gemeten (`scripts/instagram_trend.py`). Bij elke kandidaat staat het begin van het onderschrift; het hele onderschrift staat in `data/ig_captions.json` onder de code tussen haken.
   - **De editie: 4 gerechten en 1 baksel of zoet** (`category` van het zoete recept: `Gebak`, `Bakken`, `Dessert`, `Zoet`, `Koekjes` of `Taart`), plus het ferment.
   - **Minstens 4 van de 5 recepten komen uit de kandidatenlijst.** Zet de url van de post in het recept als `"instagram"`. Het vijfde recept komt ook uit de lijst, of is een seizoensgerecht: dan is de eerste `trendTerm` een stijger uit de samenvatting met `google=Seizoen`.
   - **Hooguit 1 recept per maker** per editie. Geen post die al in een eerdere editie stond (die staan niet meer in de lijst).
   - **Sla over wat geen gerecht is** (techniek, nieuws, reclame, een persoonlijk bericht) en wat niet past: niet goed te maken met kinderen, meer dan 45 minuten werk (tenzij de oven het doet), of met ingrediënten die in Nederland niet te koop zijn. Geef elk recept een `tip` voor de kinderversie.
   - **Liefst minstens 2 van de 4 gerechten Aziatisch** (tag `Aziatisch`), en niet vier keer hetzelfde soort gerecht.
   - **Waar het recept vandaan komt:** (a) van de eigen site van de maker, als het daar gratis en met hoeveelheden staat: neem dan ook de foto van die site (`photo`, `photoCredit`). (b) Staat het alleen op Instagram, dan mag je het recept uit het onderschrift halen, **alleen als daar alle hoeveelheden in staan**. Laat dan `photo` weg (nooit een foto van Instagram): de site toont in plaats daarvan de post zelf, die pas laadt na een klik. `photoCredit` is dan de naam van de maker met de url van de post. Schat nooit hoeveelheden uit een video; staat het recept nergens uitgeschreven, kies een andere kandidaat. Achter een betaalmuur: niet gebruiken.
   - De volgorde hoef je niet te bepalen: na de meting zet GitHub de gerechten op grootte van de hit (Nº 01 is de grootste) en het zoete recept als laatste.
   - De lijsten **Stijgt in het netwerk** en **Nieuw bij de kernbronnen** zijn er nog als achtergrond (en voor het ene seizoensgerecht), niet meer als basis voor de keuze.
3. **Per recept:** open het bronrecept (bij voorkeur van een kernbron, en nooit achter een betaalmuur) met een foto (`photo` = directe https-link naar de afbeelding, `photoCredit` = naam en link). De foto wordt getoond vanaf die site en nooit gekopieerd. Weigert de site dat (check_photos meldt een fout), kies dan een andere foto of een ander recept, en omzeil het niet. Kwam het recept via Instagram, zoek het dan op de eigen site van de maker (blog, Substack, NYT Cooking) en gebruik de foto daarvan, nooit een foto van Instagram zelf. **Video (optioneel):** heeft de maker zelf een video van dit recept (eigen kanaal op YouTube, Instagram of TikTok), zet die in `video` met `platform`, `id` en `url`. Een video staat naast het recept, nooit in plaats ervan. Kies een recept met video alleen als er een geschreven versie is (blog, beschrijving of caption) met hoeveelheden. Schat nooit hoeveelheden uit een video. Zet `vertical: false` bij een liggende video op Instagram of TikTok; YouTube Shorts krijgen `vertical: true`. De foto blijft nodig voor de tegels; bij YouTube mag dat de thumbnail van de video zijn (`https://i.ytimg.com/vi/<id>/maxresdefault.jpg`). Herschrijf het in eigen woorden, reken alles om naar g/ml/°C en controleer of de hoeveelheden kloppen voor het aantal personen.
4. **Vormgeving per recept:**
   - `tint`: gebruik elke kleur één keer (`sage`, `sky`, `blush`, `persimmon`, `mustard`). Kies de kleur die bij het gerecht past.
   - `glyph`: één Japans of Koreaans teken dat het gerecht samenvat (bijv. 汁 soep, 밥 rijst, 麺 noedels, 菜 groente, 卵 ei).
   - `native` + `roman`: de naam in het Japans of Koreaans met uitspraak. Alleen als je het zeker weet; anders leeg laten.
   - `trend`: `source` (bijv. TikTok, Pinterest; op de site staat "Gezien op …") + één rustige zin van **hooguit 10 woorden** waarom het nu gemaakt wordt. Schrijf als een vaststelling, niet als reclame: geen superlatieven of hypewoorden ("hét", "grootste", "viral", "is in", "must"). **Geen kale percentages**: schrijf "veel meer gezocht", niet "+110%". Goed: "Wordt nu veel gemaakt, nu het kouder wordt."
   - `signal.text` + `links`: de langere uitleg en de bronnen voor "Waarom deze week".
5. **Fermentatie van de week:** kies uit de bibliotheek in **[FERMENTATIE.md](FERMENTATIE.md) §9** (drie lijnen: klassiek, snel en fris, smaakmakers; wissel ze af) en vink de checklist in §8 af. Het zout moet precies kloppen met de bibliotheek: `check_edition.py` rekent het na (`data/ferments.json`). Zonder zout (tepache): geen ingrediënt met `"salt": true` en `"saltMode": "geen"`; shio koji: `"saltMode": "koji"`. Herhaal geen ferment uit de laatste 4 edities. Koppel het ferment met `usedIn` aan een recept van deze editie als dat kan. Zet de geraadpleegde bronnen in `sources`.
6. **Trenddata bijhouden** (voor een later dashboard, kost geen extra zoekopdrachten):
   - `trendTerms` per recept: 1–3 zoektermen zoals mensen ze intypen, meestal Engels (bijv. `["zuppa toscana"]`, `["kimchi fried rice", "kimchi"]`).
   - `signals` per recept: elk **cijfer of lijstje** dat je onderweg tegenkwam, met bron en link. Verzin niets: alleen wat er letterlijk staat. Velden: `source`, `metric` (`search-growth`, `views`, `saves`, `listed`, …), `value` (getal, of weglaten), `unit` (`x`, `%`, `views`, …), `period`, `geo` (`NL` of `world`), `url`, `note`.
   - `watch` op editieniveau: de andere trending gerechten die je zag maar niet koos, met `term`, `source`, `url`, `note` (en eventueel `signals`). Zo groeit de lijst van wat er speelt, ook buiten de vijf recepten.
   - Na het schrijven: `python3 scripts/trends_collect.py editions/<id>.json`. Dat zet alles in `data/trends.csv` en haalt Google Trends op (5 jaar per week, NL en wereldwijd, plus stijgende zoekopdrachten). Mislukt Google Trends, dan blokkeert dat de editie niet.
   - Hetzelfde script zet per recept `spark` in de editie: een gemeten label (Nieuw, Seizoen, Piek, Stijgt, Stabiel of Dalend), één zin en de lijn van 12 maanden. **Schrijf `spark` nooit zelf.** De site toont het label in plaats van `trend`; `trend.text` is alleen nog de terugval als er geen zoekdata is. Voor de 3 recepten die de trendregel dragen is de eerste `trendTerm` de stijger (zie stap 2); voor de andere recepten kies je hem zo specifiek mogelijk: het gerecht zelf, niet de hoofdingrediënt.
   - Komt er bij een recept "Dalend" uit, dan mag dat: het label is eerlijk. Maar zijn er na de meting minder dan 3 recepten in trek, dan gaat de editie niet live (zie stap 10).
7. **Nieuwsbrief:** zet op editieniveau `"mail": {"subject": "…", "preview": "…"}`. De onderwerpregel is pakkend en gaat over déze editie: noem één of twee gerechten of wat het seizoen doet, met één of twee passende emoji (🎃 🍜 🥢 🍠 🔥). Hooguit 70 tekens, liefst rond de 50, want de rest valt weg in de inbox. Geen hypewoorden en geen "Proef Nº" (dat staat al in de mail). `preview` (hooguit 120 tekens) noemt de andere recepten. Goed: "🍜 Popcornkip in je noedelsoep, pompoen uit de oven 🎃".
8. **Omslag:** `cover.color` is anders dan vorige week (`navy`, `ink`, `kaki`, `moss`). Het teken op de omslag volgt vanzelf uit de datum: het microseizoen (七十二候) van die zaterdag, met de Nederlandse vertaling erbij. `cover.glyph` is niet meer nodig.
9. **Controleer:** `python3 scripts/check_photos.py editions/<id>.json` (alle foto's moeten werken), daarna `python3 scripts/photo_light.py editions/<id>.json` (zet `photoGamma`, zodat alle foto's even licht zijn; vereist `pip install pillow`) en `python3 scripts/check_edition.py` (0 fouten).
10. **Publiceer:** commit alleen `editions/<id>.json` als `Proef: editie NN (week WW)` en push naar `main`. **Zet het id niet in `editions/index.json`** en draai `build_pages.py` niet: dat doet de Action *Trends en foto's meten* na de meting, als minstens 3 recepten in trek zijn. Binnen een kwartier staat de editie dan live en gaat de nieuwsbrief uit. Haalt de editie de regel niet, dan volgt er een issue met wat er mis is; vervang dan recepten en push opnieuw, of zet hem met de hand toch live (Actions → *Trends en foto's meten* → Run workflow, vink *toch publiceren* aan).

## Wekelijkse run (Claude-routine): zuinig werken

De routine draait elke zaterdag om 06:00. Elke stap kost tokens, en alles wat je inleest wordt bij elke volgende stap opnieuw meegestuurd. Daarom:

1. **Begin met `python3 scripts/summary.py --example`.** Dat geeft de volgende id, datum en nummer, alle eerdere recepten en ferments, en een ingekort voorbeeld. Lees **niet** de volledige edities, `index.html` of de broncode van de scripts.
2. **Lees alleen** deze REDACTIE.md en van FERMENTATIE.md §1, §6, §8 en §9.
3. **Zoeken:** meestal niet nodig, de kandidaten staan in de samenvatting. Gebruik WebSearch alleen voor wat ontbreekt (bijvoorbeeld een Aziatisch recept als de kern er deze week geen heeft), in `standard`-modus, **maximaal 4 zoekopdrachten**.
4. **Pagina's openen:** maximaal 10 keer WebFetch, alleen voor pagina's die je echt gebruikt (bronrecept, trendbron). Vraag in de prompt alleen wat je nodig hebt.
5. **Ferment:** kies uit de bibliotheek in FERMENTATIE.md §9, geen nieuw onderzoek. Schrijf het ferment met de cijfers uit de tabel. De bronlinks controleert `check_photos.py`.
6. **Schrijf de editie in één keer** met Write. Draai daarna `python3 scripts/check_photos.py editions/<id>.json` en `python3 scripts/check_edition.py` tot alle foto's werken en er 0 fouten zijn (die controleert ook de trendregel: minstens 3 recepten met een stijger als eerste `trendTerm`). Meten, fotolichtheid en receptpagina's doet GitHub na de push. Herstel alleen wat de scripts melden.
7. **Publiceer** zoals in stap 10 hierboven (alleen `editions/<id>.json`, niet `index.json`) en sluit af met een verslag van hooguit 15 regels.

## Bronnen

- `data/sources.csv`: alle koks, bloggers en magazines die we volgen. `tier` is `core` (receptbron, met oud-Bon Appétit en delicious. in de kern) of `network` (alleen voor de meting). `python3 scripts/check_sources.py` zoekt nieuwe feeds en zet de status; met `--all` controleer je alles opnieuw (eens per kwartaal).
- Nieuwe bron toevoegen: een regel met `id`, `name`, `tier`, `affiliation`, `site`, `lang`, `country`, `focus` (en eventueel `youtube` met de @-naam en `instagram` met de gebruikersnaam zonder @), de rest leeg. Daarna `check_sources.py`.
- **Kaartje van de maker** (receptpagina): de naam, foto en bio komen uit `data/sources.csv`, kolommen `person` (de kok, als die anders heet dan de site), `avatar` (directe https-link naar een foto van de maker op de eigen site, nooit van Instagram) en `bio` (één Nederlandse zin, alleen feiten die op de site van de maker staan). Vul ze in voor elke bron die je voor het eerst gebruikt; zonder foto toont de site de eerste letter. Draai daarna `python3 scripts/build_pages.py` (dat maakt `data/makers.json`).
- **Instagram:** de harvest leest ook de posts van elke bron met een `instagram`-handle, ook als die bron geen werkende feed heeft. Dat werkt alleen voor zakelijke en creator-accounts. Controleren: start de Action *Instagram testen* met `bronnen` als account; een handle met FOUT haal je weg of verbeter je. Een nieuw account beoordelen: `profiel naam1 naam2` (naam, website, volgers, gemiddelde reacties). De koks achter een magazine vinden: `noemt food52` (welke accounts het vaakst genoemd worden).
- `data/posts.csv` en `data/buzz.json` maakt `scripts/harvest.py`; niet met de hand bewerken.

## Velden van een editie

```jsonc
{
  "id": "2026-44", "number": 2, "year": 2026, "week": 44, "date": "2026-10-31",
  "intro": "Twee zinnen over deze week. Herhaal niet de vaste tagline (vijf trending recepten van het seizoen, de kinderen eten mee) en niet grammen/milliliters.",
  "cover": { "color": "ink", "glyph": "旬" },
  "mail": { "subject": "🍜 Popcornkip in je noedelsoep, pompoen uit de oven 🎃", "preview": "Plus gestoomd ei met garnalen en koekjes met bruine boter." },
  "watch": [{ "term": "butter board", "source": "TikTok", "url": "https://…", "note": "gezien, niet gekozen" }],
  "recipes": [
    {
      "slug": "uniek-over-alle-edities",       // wordt de link: /#slug
      "title": "…", "dek": "…", "category": "Hoofdgerecht",
      "minutes": 30, "servings": 4,             // optioneel: "servingsLabel": "stuks"
      "tags": ["Aziatisch", "Kindvriendelijk", "Weinig werk", "Seizoen"],
      "tint": "sage", "glyph": "菜", "native": "キャベツ", "roman": "kyabetsu",
      "trend": { "source": "Pinterest", "text": "…" },
      "signal": { "source": "…", "text": "…" },
      "source": "molly-baz",                    // id uit data/sources.csv als het bronrecept van een kernbron komt
      "trendTerms": ["zuppa toscana"],          // zoektermen voor Google Trends, specifiekste eerst
      "spark": { "label": "Seizoen", "text": "…", "weeks": [/* 52 */] },  // door scripts/trends_collect.py, niet zelf invullen
      "signals": [{ "source": "Pinterest", "metric": "search-growth", "value": 2, "unit": "x", "period": "2026 vs 2025", "geo": "world", "url": "https://…", "note": "…" }],
      "links": [{ "label": "…", "url": "https://…" }],
      "instagram": "https://www.instagram.com/reel/…/",  // optioneel: de post uit TRENDING OP INSTAGRAM waar dit gerecht vandaan komt
      "igTrend": { "name": "…", "engagement": 14445, "normal": 840, "ratio": 17.2 },  // door scripts/instagram_trend.py, niet zelf invullen
      "photo": "https://…jpg", "photoCredit": { "label": "…", "url": "https://…" },
      "photos": [{ "url": "https://…jpg", "w": 1200, "h": 800, "thumb": "https://…-150x150.jpg" }],  // door scripts/photo_more.py, niet zelf invullen
      "video": { "platform": "youtube", "id": "Lf44Fk7H24s", "url": "https://www.youtube.com/watch?v=Lf44Fk7H24s" },  // optioneel, zie stap 3
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
    "saltMode": "afspoelen",                   // alleen als het zout na het zouten wordt afgespoeld (kimchi)
    "ingredients": [
      { "qty": 500, "unit": "g", "item": "winterpeen …", "base": true, "key": "wortel" },
      { "qty": 500, "unit": "ml", "item": "water …", "base": true, "key": "water" },
      { "qty": 25, "unit": "g", "item": "zeezout zonder jodium …", "salt": true, "key": "zout" }
    ],
    "steps": ["Los {zout} zout op in …"], "ok": "…", "bad": "…", "kids": "…",
    "sources": [{ "label": "…", "url": "https://…" }]
  }
}
```

Eenheden: alleen `g`, `ml` of leeg (stuks). Geen kopjes, ounces of °F.

**Ferment: Hoeveel maak je?** Op de fermentatiepagina vult de lezer het gewicht van groente + water samen in, en het zout en de rest rekenen mee. Daarom: groente en water in g/ml met `"base": true`, precies één zout met `"salt": true`, en het zout moet 2–5 % van het totaal van de base-ingrediënten zijn (behalve bij `"saltMode": "afspoelen"`). Schrijf in de stappen `{zout}` (of een andere `key`) in plaats van een vast getal, dan rekent dat ook mee. `check_edition.py` controleert dit.
