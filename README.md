# Proef

Minimalistisch weekmagazine: elke zaterdag vijf trending recepten. Weinig werk, veel Aziatisch, groente van het seizoen en goed te maken voor kinderen. Alles in grammen, milliliters en °C.

- Site: https://edial.github.io/proef/
- Edities: `editions/<jaar>-<week>.json`, lijst in `editions/index.json`
- Foto's worden getoond vanaf de bron (met naam en link), niet gekopieerd.

## Per editie

- **[REDACTIE.md](REDACTIE.md)**: de vaste werkwijze voor een nieuwe editie, met alle velden. Elke zaterdag maakt een Claude-routine zo een editie.
- **[FERMENTATIE.md](FERMENTATIE.md)**: veiligheidsrichtlijnen. Elke Fermentatie van de week moet de checklist daarin doorstaan.
- `python3 scripts/check_edition.py` controleert alle edities voordat er iets live gaat.
- Op de site opent `/` de zoekfunctie. Je kunt zoeken op gerecht, ingrediënt, tag, tijd ("onder 30 min") of wat je in huis hebt ("kool, ei, rijst").
