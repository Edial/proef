# Proef

Minimalistisch weekmagazine: elke zaterdag vijf trending recepten. Weinig werk, veel Aziatisch, groente van het seizoen en goed te maken voor kinderen. Alles in grammen, milliliters en °C.

- Site: https://edial.github.io/proef/
- Edities: `editions/<jaar>-<week>.json`, lijst in `editions/index.json`
- Foto's worden getoond vanaf de bron (met naam en link), niet gekopieerd.

## Per editie

- **[REDACTIE.md](REDACTIE.md)**: de vaste werkwijze voor een nieuwe editie, met alle velden. Elke zaterdag maakt een Claude-routine zo een editie.
- **[FERMENTATIE.md](FERMENTATIE.md)**: veiligheidsrichtlijnen. Elke Fermentatie van de week moet de checklist daarin doorstaan.
- `python3 scripts/check_edition.py` controleert alle edities voordat er iets live gaat.
- Elk recept heeft een eigen adres, `/proef/recept/<slug>/`, met deelvoorbeeld en receptgegevens voor Google. Die pagina's maakt `python3 scripts/build_pages.py`; draai het na elke wijziging aan `index.html` of een editie (de controle op GitHub faalt anders).
- `data/sources.csv`: de koks, bloggers en magazines die we volgen (kern: oud-Bon Appétit en delicious.). Elke vrijdagnacht leest een GitHub Action hun feeds (`scripts/harvest.py`) naar `data/posts.csv` en `data/buzz.json`. Lezers zien het op `#trends`.
- `data/trends.csv` bewaart elke week de trenddata (cijfers uit de bronnen en Google Trends) voor een later dashboard. Bijwerken met `python3 scripts/trends_collect.py editions/<id>.json`.
- Op de site opent `/` de zoekfunctie. Je kunt zoeken op gerecht, ingrediënt, tag, tijd ("onder 30 min") of wat je in huis hebt ("kool, ei, rijst").
- Na elke push van een editie meet de GitHub Action *Trends en foto's meten* (`.github/workflows/meten.yml`) de trendlabels, sparklines en lichtheid van de foto's, en bouwt de receptpagina's opnieuw. De wekelijkse routine kan zelf niet bij Google Trends of de receptsites.
