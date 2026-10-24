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
- **Pekel om bij te vullen:** bij een ferment in pekel (wortel, radijs, augurk) dezelfde sterkte als de pekel van het recept. Bij droog gezouten kool (zuurkool, kimchi) 20 g zout per liter. Kook het water altijd en laat het afkoelen.
- Stukken of hele groente in pekel: **5 %** (50 g per liter). Geraspte of fijngesneden groente: **3 %** (University of Illinois Extension).
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

## 9. Bibliotheek: gecontroleerde ferments

Kies de Fermentatie van de week **uit deze lijst**. De cijfers zijn al gecontroleerd tegen de bronnen. De wekelijkse run hoeft ze niet opnieuw uit te zoeken en controleert alleen of de bronlinks nog werken. Herhaal geen ferment uit de **laatste 4 edities**: `python3 scripts/summary.py` laat zien welke dat zijn.

Een nieuw ferment toevoegen mag alleen als het onder §1 valt en je **minstens twee bronnen hebt gelezen** die de cijfers dragen. Zet het dan onderaan deze tabel met "nalopen" erachter, zodat een mens het nakijkt.

| Ferment | Zout | Aanrecht | Daarna | Bronnen |
|---|---|---|---|---|
| **Mak-kimchi** (Chinese kool) | 40 g per kg kool, 2 uur, daarna 3× afspoelen | 1–2 dagen, 18–22 °C | koelkast, binnen 1 maand op | Oregon State SP 50-1007 · UC Davis |
| **Zuurkool** (witte kool of spitskool) | 22 g per kg kool (ruim 2 %), droog door de kool kneden tot er vocht komt | 3–4 weken, 20–22 °C; bij 15–18 °C 5–6 weken | koelkast, binnen 2 maanden op | NCHFP Sauerkraut · Oregon State SP 50-745 |
| **Augurken met dille** | pekel per liter water: 75 g zout + 30 ml azijn (5 %); ca. 950 g augurkjes, 2 mm van de bloemkant eraf | 3–4 weken, 20–22 °C | koelkast, binnen 3 maanden op | NCHFP Dill Pickles · NCHFP Problems |
| **Radijs in pekel** | pekel 5 %: 50 g zout per liter water | tot het zuur ruikt, **pH-strip verplicht: 4,6 of lager** (meestal na enkele dagen) | koelkast, binnen 1 maand op | UCI SSIHI tabel · UC Inyo-Mono brine math |
| **Gefermenteerde wortel met gember** (staafjes) | pekel 5 %: 50 g zout per liter water; bijvullen met dezelfde pekel | 10–14 dagen, 20–22 °C; ruikt het na 3 weken niet zuur, dan weggooien. pH-strip: 4,6 of lager | koelkast, binnen 1 maand op | Illinois Extension · UC Davis · gebruikt in Nº 02 (test) |
| **Bloemkool of sperziebonen in pekel** | pekel 5 %: 50 g zout per liter water (Illinois: stukken 5 %; UCI noemt 2 %, Proef neemt de strengste) | tot het zuur ruikt, meestal 1–2 weken, **pH-strip verplicht: 4,6 of lager** | koelkast, binnen 1 maand op | Illinois Extension · UCI SSIHI tabel |

**Nog niet in de lijst:**
- **Gefermenteerde chilisaus.** Paprika en chili zijn weinig zuur, dus het risico op botulisme is groter. De primaire bron (University of Minnesota Extension) was niet te lezen. Eerst nalopen.
- **Kkakdugi** (radijskimchi): geen bron van een universiteit of overheid gevonden.

Bronlinks voor deze tabel staan hieronder.

## Bronnen

- National Center for Home Food Preservation: [Sauerkraut](https://nchfp.uga.edu/how/ferment/recipes/sauerkraut/), [Containers, covers and weights](https://nchfp.uga.edu/how/ferment/general-information-on-fermenting/suitable-containers-covers-and-weights-for-fermenting-food/), [Problems with fermented pickles](https://nchfp.uga.edu/how/ferment/general-information-on-fermenting/causes-and-possible-solutions-for-problems-with-fermented-pickles/)
- Oregon State University Extension: [Kimchi basics (SP 50-1007)](https://extension.oregonstate.edu/catalog/sp50-1007-kimchi-basics), [Sauerkraut: problems and solutions (SP 50-745)](https://extension.oregonstate.edu/food/preservation/sauerkraut-problems-solutions)
- UC Davis, Department of Food Science and Technology: [Troubleshooting fermented fruits and vegetables](https://ucfoodsafety.ucdavis.edu/sites/g/files/dgvnsk7366/files/media/documents/Troubleshooting%20fermented%20fruits%20and%20vegetables%20FINAL.pdf) (2022)
- University of Illinois Extension: [Fermenting](https://extension.illinois.edu/food-preservation/fermenting), [Lacto-fermentation handout](https://extension.illinois.edu/sites/default/files/fermentation_handout_2020.pdf), [Fermenting FAQ](https://extension.illinois.edu/food-preservation/fermenting-faq). Stukken in pekel 5 %, geraspt 3 %, kahmgist is onschuldig, en bij slijm of een rotte geur alles weggooien.
- National Center for Home Food Preservation: [Dill pickles (gefermenteerd)](https://nchfp.uga.edu/how/ferment/recipes/dill-pickles/)
- UC Master Food Preserver Program (Inyo-Mono): [Brine math made easy](https://ucanr.edu/sites/inyomonomfp/files/404267.pdf). Geteste recepten liggen tussen 2 en 10 % pekel, minder zout is onveilig, en zout altijd wegen.
- UC Irvine, Susan Samueli Integrative Health Institute: [How to lacto-ferment any vegetable](https://ssihi.uci.edu/files/2024/05/How-to-Lacto-Ferment-Any-Vegetable.pdf), een tabel met pekelpercentages per groente
- University of Wisconsin Extension: [Preserve it fresh, preserve it safe (sept./okt. 2023)](https://winnebago.extension.wisc.edu/2023/09/01/preserve-it-fresh-preserve-it-safe-a-newsletter-for-those-who-preserve-food-at-home-september-october-2023)
- University of New Hampshire Extension: [Fermenting: safe food preservation](https://extension.unh.edu/node/22550)
- Voedingscentrum, standpunt over zelf groente wecken (via [Webwoordenboek](https://webwoordenboek.nl/kenniscentrum/kun-je-ook-vlees-wecken)). Een officiële Voedingscentrum-pagina over thuis fermenteren is niet gevonden. Controleer dit opnieuw als die verschijnt.
