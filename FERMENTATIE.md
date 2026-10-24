# Fermentatie: veiligheidsrichtlijnen voor Proef

Elke editie heeft een **Fermentatie van de week**. Voordat er een gepubliceerd wordt, moet het recept aan deze richtlijnen voldoen. Ze zijn samengesteld uit de bronnen onderaan: Amerikaanse universiteiten (extension services) en het National Center for Home Food Preservation (NCHFP). Waar bronnen elkaar tegenspreken, kiest Proef **altijd de strengste**.

Laatst gecontroleerd: 24 oktober 2026.

## 1. Wat wel en wat niet

**Wel:** melkzuurfermentatie van groente (en fruit) met zout: zuurkool, kimchi, gefermenteerde augurken, wortel, radijs, kool, chilipasta op basis van groente. Deze worden vanzelf zuur, en zuur is wat ze veilig maakt.

**Niet in Proef:**
- Groente, knoflook of kruiden **in olie** laten staan of "fermenteren": zuurstofarm en niet zuur, de klassieke botulismeval.
- Zelf **vlees of vis** fermenteren.
- Zelf **groente wecken**. Het Voedingscentrum raadt dit af vanwege botulisme (alleen fruit is veilig om te wecken).
- Ferments met **schimmelculturen** (koji, tempeh, miso) zolang er geen geteste thuisinstructie van een betrouwbare bron bij is.
- Elk ferment waarvoor geen recept of richtlijn van een betrouwbare bron te vinden is. **Geen bron, geen publicatie.**

## 2. Zout

- **Weeg het zout.** Lepels zijn niet nauwkeurig genoeg.
- Gebruik zout **zonder jodium en zonder antiklontermiddel** (zeezout of inmaakzout). Jodium remt de fermentatie, en antiklontermiddel geeft troebel vocht en neerslag.
- **Eindconcentratie 2 tot 5 % van het gewicht van de groente.** Onder ongeveer 1,7 % wordt kool zacht of slijmerig.
- Ruwe controle: zuurkool is 3 eetlepels zout per 5 pond kool, dat is ruim **2 % op gewicht** (ca. 54 g op 2,3 kg). Kimchi wordt vaak eerst sterker gezouten en daarna afgespoeld. Het zout dat achterblijft valt dan binnen 2 tot 5 %.
- **Pekel om bij te vullen:** 20 g zout per liter water. Kook het water en laat het afkoelen.
- Gebruik **geen zoutvervanger** (kaliumchloride): dat smaakt bitter.

## 3. Temperatuur en tijd

| Temperatuur | Wat er gebeurt |
|---|---|
| onder 15 °C | fermenteert mogelijk niet |
| 18 – 22 °C | **ideaal**: de Proef-norm |
| 22 – 24 °C | gaat sneller, maar de groente wordt eerder zacht |
| boven 29 °C | niet doen: bederfbacteriën winnen het |

- Kimchi: 1 tot 2 dagen (soms tot 4) op kamertemperatuur, daarna de koelkast in.
- Zuurkool: 3 tot 4 weken bij 21 tot 24 °C, 5 tot 6 weken bij 15 tot 18 °C.
- Een goed ferment zakt **binnen 48 uur onder pH 4,6**.

## 4. Zuurgraad (pH)

- **pH 4,6 of lager** is de veiligheidsgrens. Kimchi zit op zijn best rond **pH 4,2**.
- Een recept in Proef noemt altijd de optionele controle met **pH-strips** (bij drogist of online), vooral voor beginners.
- Het ferment is pas klaar voor de koelkast als het zurig ruikt én er bubbels zijn geweest.

## 5. Gerei en hygiëne

- **Glas, rvs of voedselveilig plastic.** Gebruik **geen koper, messing, zink of ijzer**: dan het hele ferment weggooien. Gebruik ook geen vuilniszakken als verzwaring.
- Was pot, deksel en gewicht in heet zeepsop en spoel ze na met heel heet water.
- **Kopruimte:** laat minstens **5 cm** leeg tot de rand.
- **Alles onder het vocht houden**, 2,5 tot 5 cm diep. Dat doe je met een gewicht, een klein schoteltje of een zakje met pekel. Controleer dit elke dag.
- Laat het gas ontsnappen: gebruik een deksel met waterslot, of draai het deksel elke dag even open ("burpen").
- Veeg de rand schoon voordat het deksel er weer op gaat.

## 6. Goed of weggooien

| Wat je ziet | Oordeel |
|---|---|
| Bubbels, gesis bij openen, fris zure geur, troebel vocht | **Goed**: zo hoort het |
| Vlak wit, grijs of roze vliesje op het vocht (kahmgist) | **Onschuldig**: schep het eraf, check dat alles onder het vocht staat |
| Roze kleur zonder slijm | **Veilig**: gist of kleurstof uit de groente |
| Zachte groente, maar ruikt en smaakt schoon en zuur | **Veilig**, wel mindere kwaliteit |
| **Pluizige schimmel** (groen, blauw, zwart, bruin of wit pluis) | **Alles weggooien.** Niet wegscheppen: Proef volgt hier de strengste bron (UC Davis) |
| **Slijmerig** | **Weggooien** |
| **Rotte of bedorven geur** (niet zuur maar vies) | **Weggooien** |
| Gemaakt met koper, messing of zink | **Weggooien** |

## 7. Bewaren

- Bewaar het in de koelkast op **4 °C of kouder**, met de groente onder het vocht.
- **Proef-norm voor kimchi: binnen 1 maand opmaken.** Bronnen lopen uiteen: van "op zijn best binnen 1 week" (Oregon State, algemeen) tot "tot 6 maanden" bij een getest recept (ook Oregon State). Proef blijft voorzichtig.
- Zuurkool: afgedekt enkele maanden in de koelkast (NCHFP).

## 8. Checklist voor elke Fermentatie van de week

Elk punt moet "ja" zijn, anders publiceert Proef het niet. De validator (`scripts/check_edition.py`) controleert de velden. De inhoud controleer je zelf met deze lijst.

- [ ] Het type ferment staat bij **wel** (§1), en er is minstens één betrouwbare bron voor dit ferment of een vergelijkbaar getest recept. Die bron staat in `ferment.sources`.
- [ ] Zout is gewogen in grammen, zonder jodium en zonder antiklontermiddel, en valt in de 2–5 %-regel (§2).
- [ ] De temperatuur op het aanrecht staat erin, binnen 18–22 °C, met een duur (§3).
- [ ] Er staan stappen in voor schone pot, 5 cm kopruimte, onder het vocht houden en gas laten ontsnappen (§5).
- [ ] De pekel om bij te vullen staat erin als de groente niet onder staat.
- [ ] `ok`, `bad` en `kids` zijn ingevuld, en `bad` noemt schimmel, slijm en rotte geur als reden om weg te gooien (§6).
- [ ] De bewaartermijn valt binnen §7.
- [ ] De pH-controle wordt genoemd (§4).

## Bronnen

- National Center for Home Food Preservation: [Sauerkraut](https://nchfp.uga.edu/how/ferment/recipes/sauerkraut/), [Containers, covers and weights](https://nchfp.uga.edu/how/ferment/general-information-on-fermenting/suitable-containers-covers-and-weights-for-fermenting-food/), [Problems with fermented pickles](https://nchfp.uga.edu/how/ferment/general-information-on-fermenting/causes-and-possible-solutions-for-problems-with-fermented-pickles/)
- Oregon State University Extension: [Kimchi basics (SP 50-1007)](https://extension.oregonstate.edu/catalog/sp50-1007-kimchi-basics), [Sauerkraut: problems and solutions (SP 50-745)](https://extension.oregonstate.edu/food/preservation/sauerkraut-problems-solutions)
- UC Davis, Department of Food Science and Technology: [Troubleshooting fermented fruits and vegetables](https://ucfoodsafety.ucdavis.edu/sites/g/files/dgvnsk7366/files/media/documents/Troubleshooting%20fermented%20fruits%20and%20vegetables%20FINAL.pdf) (2022)
- University of Wisconsin Extension: [Preserve it fresh, preserve it safe (sept./okt. 2023)](https://winnebago.extension.wisc.edu/2023/09/01/preserve-it-fresh-preserve-it-safe-a-newsletter-for-those-who-preserve-food-at-home-september-october-2023)
- University of New Hampshire Extension: [Fermenting: safe food preservation](https://extension.unh.edu/node/22550)
- Voedingscentrum, standpunt over zelf groente wecken (via [Webwoordenboek](https://webwoordenboek.nl/kenniscentrum/kun-je-ook-vlees-wecken)). Een officiële Voedingscentrum-pagina over thuis fermenteren is niet gevonden. Controleer dit opnieuw als die verschijnt.
