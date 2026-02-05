# Experiment: Few-Shot Prompting

**Datum:** Februari 2026
**Status:** Afgerond - niet geïmplementeerd
**Conclusie:** Standard methode geeft uitgebreidere feedback, few-shot is consistenter maar vereist veel handwerk per eis.

---

## Wat is Few-Shot Prompting?

Few-shot prompting is een techniek waarbij je de AI voorbeeldconversaties geeft in plaats van voorbeelden in de system prompt. Het idee is dat de AI het patroon van de voorbeelden imiteert.

### Verschil met Standard

**Standard (huidige methode):**
```
System prompt: [basis instructies + eis info + voorbeelden]
User: "Geef feedback op onze invulling"
```

**Few-shot:**
```
System prompt: [basis instructies + eis info] (ZONDER voorbeelden)
User: "Geef feedback op [zwakke voorbeeldinvulling]"
Assistant: "[kritische feedback]"
User: "Geef feedback op [goede voorbeeldinvulling]"
Assistant: "[positieve feedback]"
User: "Geef feedback op [echte invulling]"  ← echte vraag
```

---

## Wat we hebben getest

### Test 1: Generieke few-shot responses

We testten eerst met generieke voorbeeldresponses die voor alle eisen hetzelfde waren.

**Resultaat:** De AI volgde het format goed, maar miste eis-specifieke kennis. Bijvoorbeeld:
- Voor OP 4.4 (Verzuimbeleid) noemde de standard methode "16 uur in 4 weken" en "VSV", de few-shot niet.
- De few-shot gaf soms een te mild oordeel ("Voldoende" in plaats van "Onvoldoende").

### Test 2: Eis-specifieke few-shot responses

We voegden voor OP 2.1 eis-specifieke voorbeeldresponses toe met termen als:
- Warme overdracht
- Leerlingvolgsysteem
- Sociaal-emotionele ontwikkeling
- DIA-toetsen, SAQI

**Resultaat:** Veel beter! De feedback was nu eis-specifiek en het oordeel was consistent.

---

## Testresultaten

### OP 4.4 - Verzuimbeleid (generieke few-shot)

**Invulling (zwak):**
```
Ambitie: We willen dat leerlingen naar school komen en verzuim beperken.
Beoogd resultaat: Leerlingen zijn aanwezig op school. Ongeoorloofd verzuim wordt aangepakt.
Concrete acties: Docenten registreren aanwezigheid in Magister. Bij veel verzuim wordt de mentor ingeschakeld. We melden bij leerplicht als het moet.
Wijze van meten: We kijken naar de verzuimcijfers als er problemen zijn.
```

**Standard response:**
```
Oordeel: Onvoldoende

Sterke punten:
- Jullie geven aan dat docenten aanwezigheid registreren, wat een basisstap is.
- Jullie benoemen dat de mentor wordt ingeschakeld bij veel verzuim.

Verbeterpunten:
- De ambitie is te vaag. "Leerlingen naar school komen" is niet specifiek genoeg en zegt niets over het waarom (bijvoorbeeld het behalen van onderwijstijd of diploma's).
- Het beoogd resultaat is te simpel. "Leerlingen zijn aanwezig" is niet meetbaar en zegt niets over de mate van aanwezigheid.
- De concrete acties zijn onvoldoende uitgewerkt. Er ontbreekt een duidelijk protocol met stappen en tijdslijnen. Wanneer precies wordt de mentor ingeschakeld? Wat gebeurt er na de inschakeling van de mentor? Wanneer wordt er gemeld bij de leerplicht?
- De wijze van meten is reactief en niet proactief. "We kijken naar de verzuimcijfers als er problemen zijn" is te laat. Jullie moeten verzuim actief monitoren en analyseren.
- Jullie missen een preventief beleid. Er staat niets over hoe jullie verzuim voorkomen.
- Jullie vermelden de wettelijke meldplicht bij de leerplichtambtenaar, maar geven geen details over wanneer dit moet (na 16 uren in 4 weken).
- Jullie benoemen het VSV (voortijdig schoolverlaten) niet, terwijl dit onderdeel is van deze deugdelijkheidseis.
- Jullie missen een beschrijving van verantwoordelijkheden (wie doet wat?).

Vervolgstappen:
- Formuleer een ambitie die gericht is op het behalen van onderwijstijd en diploma's.
- Stel meetbare doelen voor het beoogd resultaat (bijvoorbeeld een maximaal percentage ongeoorloofd verzuim).
- Werk een concreet verzuimprotocol uit met stappen, tijdslijnen en verantwoordelijkheden.
- Beschrijf preventieve maatregelen om verzuim te voorkomen.
- Benoem de wettelijke meldplicht bij de leerplichtambtenaar (na 16 uur in 4 weken).
- Neem VSV op in jullie beleid en beschrijf hoe jullie dit aanpakken.
- Zorg voor systematische registratie van aanwezigheid en analyse van verzuimcijfers.
- Evalueer jaarlijks het beleid en pas het aan waar nodig.
```

**Few-shot response (generiek):**
```
Oordeel: Voldoende

Sterke punten:
- Er is een basisinvulling van de vier PDCA-onderdelen
- Er wordt geregistreerd en er is een koppeling naar de leerplicht

Verbeterpunten:
- De ambitie is te algemeen en mist concrete streefpunten.
- Het beoogde resultaat is te vaag. Wat betekent 'aangepakt'?
- De concrete acties zijn onvoldoende specifiek. Wat houdt 'veel verzuim' in? Hoe ziet de inschakeling van de mentor eruit?
- De wijze van meten is reactief en niet proactief. Er wordt alleen gekeken als er al problemen zijn.

Vervolgstappen:
- Formuleer een ambitie met een concreet streefcijfer voor verzuim.
- Beschrijf in het beoogde resultaat hoe je het verzuim wilt verminderen (bijvoorbeeld een percentage).
- Maak de concrete acties specifieker:
  - Definieer 'veel verzuim' (bijvoorbeeld 5 uur per maand).
  - Beschrijf de taken van de mentor (bijvoorbeeld een gesprek met leerling en ouders).
  - Benoem de criteria voor het melden bij de leerplicht.
- Stel een systematische manier van meten op:
  - Rapporteer verzuimcijfers periodiek (bijvoorbeeld maandelijks).
  - Analyseer de cijfers en identificeer trends.
  - Evalueer het beleid en pas het aan waar nodig.
```

**Analyse:**
- Standard: Oordeel "Onvoldoende", noemt specifiek "16 uur in 4 weken", "VSV"
- Few-shot: Oordeel "Voldoende" (te mild!), mist eis-specifieke termen

---

### OP 2.1 - Verzamelen van (toets)informatie

#### Met generieke few-shot

**Invulling (zwak):**
```
Ambitie: We houden leerlingen in de gaten.
Beoogd resultaat: We weten hoe het gaat met leerlingen.
Concrete acties: Docenten voeren cijfers in. Als er problemen zijn horen we dat wel.
Wijze van meten: We merken het als er iets aan de hand is.
```

**Standard response:**
```
Oordeel: Onvoldoende

Sterke punten:
- Jullie geven aan dat er cijfers worden ingevoerd door docenten. Dit is een begin van het vastleggen van cognitieve ontwikkeling.

Verbeterpunten:
- De ambitie en het beoogd resultaat zijn extreem vaag. "Leerlingen in de gaten houden" en "weten hoe het gaat" zijn niet concreet genoeg om te beoordelen of jullie dit daadwerkelijk bereiken.
- Jullie beschrijven alleen dat docenten cijfers invoeren, maar niet hoe systematisch dit gebeurt. Is er een leerlingvolgsysteem? Welke toetsen worden gebruikt?
- Er wordt geen melding gemaakt van informatieverzameling bij binnenkomst (warme overdracht, onderwijskundig rapport, intake).
- De focus ligt volledig op reactief handelen ("Als er problemen zijn horen we dat wel") in plaats van systematisch verzamelen van informatie. Dit voldoet niet aan de eis.
- De wijze van meten is onbruikbaar. "We merken het als er iets aan de hand is" is subjectief en niet controleerbaar.
- Jullie missen volledig de aspecten van sociaal-emotionele ontwikkeling.

Vervolgstappen:
- Formuleer een concrete ambitie en een meetbaar beoogd resultaat. Denk aan het doel van 'zicht op de leerling' en hoe je dat concreet maakt.
- Beschrijf de complete cyclus van informatieverzameling: bij binnenkomst, gedurende het schooljaar en bij overgangen.
- Benoem de instrumenten die jullie gebruiken voor zowel cognitieve (toetsen, leerlingvolgsysteem) als sociaal-emotionele ontwikkeling (mentor, observaties).
- Maak concreet hoe vaak informatie wordt verzameld en vastgelegd.
- Bedenk een objectieve manier om te meten of jullie het beoogde resultaat bereiken (bijvoorbeeld door leerlingdossiers te controleren op volledigheid).
```

**Few-shot response (generiek):**
```
Oordeel: Onvoldoende

Sterke punten:
- Er is een begin gemaakt met het beschrijven van de aanpak.

Verbeterpunten:
- De ambitie is te vaag en niet concreet genoeg - beschrijf specifieker wat jullie willen bereiken
- Er zijn geen meetbare doelen geformuleerd in het beoogde resultaat
- De concrete acties zijn te algemeen - beschrijf specifiek welke stappen jullie nemen
- De wijze van meten ontbreekt grotendeels of is onduidelijk - hoe weten jullie of het werkt?
- De PDCA-cyclus is niet compleet: er mist een duidelijke koppeling tussen acties en evaluatie

Vervolgstappen:
- Formuleer een concrete, meetbare ambitie met streefpercentages of aantallen
- Beschrijf per actie: wie, wat, wanneer en hoe vaak
- Voeg een systematische evaluatiemethode toe (bijv. jaarlijkse enquête, registratiesysteem)
- Zorg dat alle vier PDCA-onderdelen volledig zijn ingevuld
```

**Analyse:**
- Standard: Noemt "warme overdracht", "leerlingvolgsysteem", "sociaal-emotionele ontwikkeling"
- Few-shot (generiek): Alleen generieke feedback, mist eis-specifieke termen

---

#### Met eis-specifieke few-shot (OP 2.1)

**Dezelfde invulling (zwak):**
```
Ambitie: We houden leerlingen in de gaten.
Beoogd resultaat: We weten hoe het gaat met leerlingen.
Concrete acties: Docenten voeren cijfers in. Als er problemen zijn horen we dat wel.
Wijze van meten: We merken het als er iets aan de hand is.
```

**Standard response:**
```
Oordeel: Onvoldoende

Sterke punten:
- Jullie geven aan dat er cijfers worden ingevoerd, wat een basis vorm van informatieverzameling is.

Verbeterpunten:
- De ambitie en het beoogd resultaat zijn extreem vaag. "Leerlingen in de gaten houden" en "weten hoe het gaat" zijn niet concreet en niet meetbaar. Het geeft geen richting aan wat jullie willen bereiken.
- Jullie beschrijven alleen dat cijfers worden ingevoerd, maar niet hoe systematisch dit gebeurt. Is er een leerlingvolgsysteem? Welke toetsen worden gebruikt? Hoe vaak worden cijfers ingevoerd?
- De concrete acties zijn beperkt en vooral reactief ("Als er problemen zijn horen we dat wel"). Er ontbreekt een proactieve aanpak van systematische informatieverzameling.
- Jullie missen volledig de informatieverzameling bij binnenkomst (warme overdracht, onderwijskundig rapport, intake).
- Er is geen aandacht voor sociaal-emotionele ontwikkeling. Alleen cognitieve prestaties (cijfers) worden genoemd.
- De wijze van meten is subjectief en onbruikbaar ("We merken het als er iets aan de hand is"). Er is geen sprake van objectieve criteria of meetbare indicatoren.
- Jullie focussen op signaleren van problemen, terwijl deze eis gaat om het verzamelen van informatie, ook als er geen problemen zijn.

Vervolgstappen:
- Formuleer een concrete ambitie en een meetbaar beoogd resultaat. Denk aan het doel: leerlingen goed in beeld hebben.
- Beschrijf een systematische aanpak van informatieverzameling, inclusief:
  - Wat bij binnenkomst gebeurt (warme overdracht, intake)
  - Welke toetsen worden gebruikt voor cognitieve ontwikkeling
  - Hoe sociaal-emotionele ontwikkeling wordt gevolgd (mentor, observaties)
  - Welk leerlingvolgsysteem jullie gebruiken en hoe dit wordt ingezet
- Maak de concrete acties specifieker en beschrijf hoe informatie wordt verzameld.
- Bepaal concrete meetmethoden om te controleren of jullie het beoogde resultaat bereiken (bijvoorbeeld evaluatie van het leerlingvolgsysteem, steekproefsgewijze controle van dossiers).

Jullie invulling mist de basisvereisten van deze deugdelijkheidseis. Het is belangrijk om een systematische en complete aanpak van informatieverzameling te beschrijven, waarbij zowel cognitieve als sociaal-emotionele ontwikkeling worden gevolgd, vanaf het moment dat een leerling bij jullie op school komt.
```

**Few-shot response (eis-specifiek):**
```
Oordeel: Onvoldoende

Sterke punten:
- Er is een begin gemaakt met het benoemen van informatieverzameling.

Verbeterpunten:
- De ambitie is te vaag. "Leerlingen in de gaten houden" is niet concreet en geeft geen richting aan de systematische aanpak die de Onderwijsinspectie verwacht.
- Het beoogd resultaat is eveneens te vaag. "We weten hoe het gaat met leerlingen" is subjectief en niet meetbaar.
- De concrete acties zijn onvoldoende gedetailleerd. Alleen "cijfers invoeren" is niet systematisch en dekt niet alle relevante informatie. Wat voor soort informatie wordt verzameld naast cijfers? Hoe vaak gebeurt dit?
- De wijze van meten is reactief en onvoldoende betrouwbaar. "We merken het als er iets aan de hand is" is geen systematische controle op de volledigheid en actualiteit van de informatie.
- Er ontbreekt informatie over de informatieverzameling bij binnenkomst van leerlingen (warme overdracht vanuit het primair onderwijs).
- Er ontbreekt informatie over hoe sociaal-emotionele ontwikkeling wordt gemonitord.

Vervolgstappen:
- Formuleer een concrete ambitie die de systematische verzameling van zowel cognitieve als sociaal-emotionele informatie benoemt.
- Beschrijf een meetbaar beoogd resultaat, bijvoorbeeld dat voor elke leerling actuele informatie beschikbaar is in een leerlingvolgsysteem.
- Specificeer de concrete acties: welke toetsen worden afgenomen, hoe vaak, en door wie? Welke rol heeft de mentor in het verzamelen van informatie?
- Beschrijf hoe de volledigheid en actualiteit van de informatie wordt gecontroleerd (bijvoorbeeld door steekproefsgewijze controle van leerlingdossiers).
- Benoem de procedures voor de warme overdracht vanuit het primair onderwijs.
- Beschrijf hoe de sociaal-emotionele ontwikkeling van leerlingen wordt gemonitord.
```

**Analyse:**
- Beide geven nu "Onvoldoende" (consistent!)
- Beide noemen de eis-specifieke termen
- Standard is langer en heeft afsluitende paragraaf
- Few-shot is korter en strakker gestructureerd

---

## Conclusie

| Aspect | Standard | Few-Shot (generiek) | Few-Shot (eis-specifiek) |
|--------|----------|---------------------|--------------------------|
| Eis-specifieke kennis | ✅ Ja | ❌ Nee | ✅ Ja |
| Oordeel accuraat | ✅ Ja | ⚠️ Soms te mild | ✅ Ja |
| Format consistentie | ⚠️ Wisselend | ✅ Consistent | ✅ Consistent |
| Uitgebreidheid | ✅ Uitgebreid | ❌ Beperkt | ⚠️ Gemiddeld |
| Implementatie-effort | ✅ Geen extra werk | ✅ Geen extra werk | ❌ Per eis responses schrijven |

### Besluit

We kiezen voor de **standard methode** omdat:
1. De feedback uitgebreider en specifieker is
2. De eis-specifieke kennis automatisch meekomt via de database
3. Few-shot met eis-specifieke responses vereist veel handmatig werk (voor elke eis aparte responses schrijven)

### Wanneer few-shot overwegen

Few-shot kan interessant zijn als:
- Je zeer strikte format-consistentie nodig hebt
- Je bereid bent om voor elke eis gedetailleerde voorbeeldresponses te schrijven
- Je een model gebruikt dat moeite heeft met lange system prompts

---

## Bestanden

- `few_shot.py` - De volledige implementatie van few-shot prompting
- `EXPERIMENT.md` - Dit document

De code in `few_shot.py` is volledig werkend en kan later opnieuw geïntegreerd worden indien gewenst.
