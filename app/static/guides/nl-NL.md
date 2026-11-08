# Yeufonic — de handleiding

Deze handleiding gaat over het **gebruik** van de app. De installatie, en alles wat je nodig hebt voordat hij werkt, staat in de
[README](https://github.com/yeufonic/yeufonic#readme).

De app maakt nummers met YuE2, een model dat in twee stappen werkt: eerst schrijft het een **partituurplan** —
de melodie, de akkoorden en de secties, als tekst — en daarna **rendert** het dat plan naar audio.
Bijna alles hieronder volgt uit die tweedeling. Een plan kost seconden en kun je lezen, bewerken en
weggooien; een render kost minuten. Daarom laat de app je eerst het plan zien.

---

## Je eerste nummer {#your-first-song}

1. Klik op **+ Nummer** bovenaan het linkerpaneel. Het editorvenster gaat open.
2. **Schrijf een stijl.** Een zin, geen lijst met tags: *“warm indie rock, expressive female lead, jangly
   guitars, 96 BPM”*. Dit bepaalt het meest hoe het resultaat klinkt.
3. **Voeg een songtekst toe**, of klik op **Songtekst schrijven** en laat Gemma er een opzetten op basis van een beschrijving.
4. Klik op **Partituurplan schrijven**. Het venster sluit en de take verschijnt in het linkerpaneel. Met
   **Renderen zodra het plan klaar is** aangevinkt naast de knop, zoals het begint, gaat het plan
   meteen door naar de render.

Om het plan te lezen voordat er iets gerenderd wordt, vink je eerst **Renderen zodra het plan klaar is** uit. De
take stopt dan bij zijn plan: open hem, en op zijn pagina **Partituur** gooit **Een nieuw plan schrijven** opnieuw voor een melodie die je
niet bevalt, voor de prijs van een paar seconden, en **Deze partituur renderen** rendert hem. Een take die nog geen audio heeft
wordt aangevuld; een take die al audio heeft wordt gerenderd als een nieuwe take ernaast, dus een render
overschrijft nooit een take die je wilt houden.

De take verschijnt in de bibliotheek rechts en speelt in de balk onderaan.

### Het takepaneel en de editor {#the-take-panel-and-the-editor}

Het **linkerpaneel** toont de laatste take waarop je klikte, alleen om te lezen: de stijl, de klankinstellingen, de
eerste regels van de tekst, en de partituur als toonsoort, tempo, lengte en de akkoorden van elke sectie.
**+ Nummer**, **+ Cover** en **+ Instrumentaal** bovenaan beginnen iets nieuws; die van het soort
take is gemarkeerd. Het pijltje naast het paneel klapt het in, zodat de takes de breedte krijgen,
en weer uit. Losse toetsen werken op de take die het paneel toont (M voor het masteringrack, E voor
de editor en meer): zie [Sneltoetsen](#hot-keys).

Een take maken en veranderen gebeurt in het **editorvenster**. De hoofdknop in het paneel zegt wat
past: *Bewerken en opnieuw renderen*, of *Het plan nakijken en renderen* als er een plan klaarstaat. De knoppen
**Partituur** en **Nog eens** op een kaart openen het ook, net als dubbelklikken op een kaart. Het heeft drie
kolommen (het nummer, de tekst en de klank), alles in beeld, met de partituur op een eigen tabblad.

Het venster sluiten, met **Sluiten**, het kruisje of Escape, bewaart wat je hebt geschreven.

De knop na **Sluiten**, rechtsboven, laat het venster het hele browservenster vullen, en
een tweede klik zet het terug op de gewone grootte. Het venster opent zoals je het de vorige keer achterliet. Schermvullend
neemt de tekstkolom de hele hoogte: het tekstvak (als het al woorden heeft) en de structuur groeien mee in
de ruimte, en de speler blijft onderaan de kolom.

De bovenste rij van het venster heeft, groter, de knopjes van de takekaart: Opnieuw zingen, Variaties,
Meer proberen, Binnenin, Eruit halen, Normaliseren en Verplaatsen, elk waar de kaart het zou tonen. Normaliseren is groen
zolang de take genormaliseerd is, en een klik zet hem dan terug op het niveau waarop hij werd gerenderd; Binnenin
licht op zolang de take andere takes bevat, en sluit het venster om ze onder de take te tonen.

### Een opgenomen stem {#a-recorded-voice}

Een take kan gezongen worden met een stem die getraind is op opnamen van iemand die zingt: jijzelf, of de zanger van
een corpus. Stemmen maak en beheer je op de pagina **Stemmen**, in het menu, en je kiest er een in het veld *Opgenomen stem*
van de editor als je een take maakt. Een take met een stem wordt gewoon gerenderd; daarna wordt de zang gescheiden, opnieuw
gezongen in de stem en weer over de rest gemixt, voordat het niveau wordt gemeten. Daarvoor is de optionele stemservice nodig
("Recorded voices" in de README); zonder die is het veld verborgen.

**Nieuwe stem** maakt een stem van je eigen opnamen of een die getraind wordt op de nummers van een corpus. Een stem van
opnamen begint leeg, en zijn pagina verzamelt ze: **Opnemen…** opent de recorder, en elke take die je bewaart gaat naar de stem
zoals hij gezongen is, nooit met autotune; **Uploaden…** neemt audiobestanden; **Uit de bibliotheek…** voegt opnamen toe die je al
hebt, zoals een zangpartij die je voor een cover opnam, met een speler bij elke om hem eerst te beluisteren. Een opname uit de
bibliotheek wordt aangewezen, niet gekopieerd. De pagina telt de zang af tegen de minuten waarop een stem traint: ongeveer tien
minuten over je hele bereik is genoeg, en een korte opname geeft al een herkenbare stem. Elke opname zegt of hij alleen een stem
is (**alleen zang**, aangevinkt bij wat je hier opnam) of een nummer, dat eerst gescheiden wordt. Druk dan op **Trainen**.

Het trainen wacht zijn beurt af op de GPU en toont de voortgang in de taakpil en het logboek. **Opnieuw trainen** traint opnieuw
op de opnamen zoals ze nu zijn, of op de nummers van het corpus. Een opname die inmiddels uit de bibliotheek is verwijderd, wordt
overgeslagen. De pagina bewaart **Waarvan hij leerde**, de gescheiden zang van elk nummer en de getrainde fragmenten, om te
beluisteren.

**Octaaf** zet de stem een heel octaaf hoger of lager, voor een zanger wiens bereik ver van dat van de take ligt. **Zangniveau**
en **Instrumentniveau** bepalen de balans van de nieuwe mix, en **Gelijkenis** hoe dicht de stem bij de eigen klank van de zanger
blijft: hoger klinkt meer als die zanger, en kan bewerkter klinken. Dit zijn de standaardwaarden van de stem; de editor toont ze
onder de stem, om voor één take aan te passen, en de take houdt ze. Instellingen → *Stemtraining* bepaalt van hoeveel zang een
stem leert en hoeveel rondes.

Het resultaat is omgezette zang over een gescheiden begeleiding, dus minder naadloos dan zang die het model zelf zong. Schone,
droge opnamen geven de schoonste stem. **Stem downloaden** slaat een getrainde stem op als zip om aan iemand te geven, en **Stem
importeren…** voegt er een toe: die zip, of een RVC-model van elders (een .pth, of een zip met zijn index). Het recept van een
take noemt zijn stem en de instellingen van de take ervoor, en bij het importeren wordt de stem met die naam op deze installatie
gebruikt, als die er is.

### Geavanceerde instellingen {#advanced-settings}

De knop **Geavanceerd** in de kop van de editor opent instellingen alleen voor deze take. De meeste nummers
hebben ze nooit nodig. Ze worden met de take bewaard, dus *Bewerken en opnieuw renderen* vindt ze zoals je ze achterliet.
De knop licht op als een instelling afwijkt van de standaard, en **Standaardwaarden herstellen** zet ze
allemaal terug.

Sommige werken op het plan, andere op de render en het uiteindelijke bestand:

- **Diffusiestappen** (16–64, standaard 32): hoeveel stappen de audiodecoder zet. Meer stappen duren
  langer om te renderen.
- **De stijl volgen** (0–100, standaard 1.0): hoe strak de muziek de stijl en de tekst volgt, de sturing
  van de fase die de partituur in klank omzet (CFG). Boven 1.0 komt hij er dichter bij; eronder dwaalt hij af. Het
  verschil is subtiel bij kleine waarden, en een render duurt iets langer. Elke waarde die de engine aanneemt kan worden ingevoerd:
  een heel hoge sturing klinkt eerder ruw dan trouwer. Zichtbaar als de engine het heeft: yue2.cpp, of de ComfyUI-engine
  in de nieuwste versie (bouw een oude Docker-engine opnieuw om het te krijgen).
- **Vermijden:** woorden om van weg te sturen, zoals “drums” of “rap vocals”. Ze worden aan de stijl
  toegevoegd als “avoid: …”. Het is een hint voor de planner, geen garantie: de renderer heeft geen negatieve prompt.
- **Toonsoort vastzetten:** het plan wordt naar deze toonsoort verplaatst nadat de planner het heeft geschreven. De planner negeert
  een toonsoort die in de stijl wordt genoemd, dus dit gebeurt op de partituur zelf: elke noot en elk akkoord schuift
  hetzelfde interval op en de voortekening wordt herschreven. Een mineurplan blijft mineur, en alleen
  de grondtoon verschuift. Een plan dat de app niet zeker kan lezen, zoals een in een modus of met een toonsoortwissel
  halverwege, blijft in de toonsoort van de planner en het log zegt dat.
- **Tempo vastzetten** (BPM): het plan wordt op dit tempo vastgezet, dat elk tempo in de stijl of in de
  eigen partituur van de planner vervangt, en de render volgt het.
- **Tokenlimiet van de partituur** (standaard 8192): het meeste dat de planner mag schrijven. Een lagere grens voorkomt dat het plan van een kort nummer
  uitdijt.
- **Limiet voor aangehouden akkoord** (maten, standaard 8): het maximale aantal maten dat de planner op één grondtoon blijft voordat
  hij moet wisselen.
- **Bonus voor toonsoortvreemde harmonie** (0–10, standaard 0): hoe sterk de planner naar geleende akkoorden
  en grondtonen buiten de hoofdtoonsoort wordt geduwd. Deze twee werken op de keuzes van de planner, dus ze tonen zich als
  een verschil in de akkoorden van het plan, meer dan als een duidelijk hoorbaar verschil. Vergelijk in het venster
  Partituur.
- **Stemmen volgen de aanwijzingen** (een vinkje onder het tekstvak, dat verschijnt als de tekst een stemaanwijzing heeft zoals
  `[male voice]`; aan voor een nieuwe take): de melodie van elke aangewezen regel schuift per octaaf naar waar de stem zingt die
  de aanwijzing noemt. Zie [De tekst](#the-words).
- **Deze structuur precies volgen** (een vinkje onder het tekstvak, niet in Geavanceerd; nummers; standaard uit): het plan schrijft precies de secties die de tekst noemt, in
  volgorde, en geen andere. Uit geeft de planner het nummer zelf vorm en voegt vaak een intro, outro of
  interlude toe, of laat een sectie weg. Een plan kan nog steeds eindigen voordat de lijst op is.
- **Delen beginnen anders** (Harmonie volgen, Altijd, Nooit): of een sectie mag beginnen met dezelfde
  akkoorden als de vorige. *Harmonie volgen* zet het aan vanaf Kleurrijk en laat het daaronder uit; *Altijd* en
  *Nooit* beslissen voor deze take op elk niveau, om twee plannen met en zonder te vergelijken.
- **Doelluidheid:** het niveau waarop een take wordt genormaliseerd. Geldt alleen als normaliseren aan staat.
- **Eindfade** (seconden, standaard 3): de lengte van de fade als een take bij de lengtegrens wordt
  afgekapt.

### Wat je in het vak Stijl zet {#what-to-put-in-the-style-box}

YuE2 leest dit als de beschrijving van een opname, dus beschrijf een opname. Taal, genre, stem,
instrumenten, sfeer, tempo en productie, ongeveer in die volgorde, alles in één zin. Losse lijsten met tags
werken slechter, en sectiemarkeringen zoals `[Verse]` horen in de tekst, niet hier.

De chips **Zang** eronder schrijven voor je in de stijl: vrouwelijk, mannelijk of duet, en een karakter
zoals ademend of rauw. Ze zijn een typsnelkoppeling, en je kunt het resultaat met de hand aanpassen.

### De tekst opzetten {#drafting-the-lyrics}

**De structuur.** Boven het tekstvak heeft een nummer, zolang het geen woorden heeft, een **structuur** om op te bouwen, net als
een instrumentaal: een lijst met secties die je kunt herschikken, verwijderen en uitbreiden (intro, couplet, pre-refrein, refrein, bridge,
interlude, outro). **Beginnen met…** vult hem met een gangbare vorm, en de tooltip van elke vorm zegt waarvoor die dient. Een
**interlude** is een instrumentale passage: de schrijver zet de tag op een eigen regel, en de planner speelt hem met
de instrumentale stem. **Delen in het tekstvak zetten** plaatst de tags als lege secties om er met de hand onder te schrijven.
Zodra het vak woorden heeft, wordt de tekst gezongen en gaat de structuur opzij.

**Songtekst schrijven**, naast het tekstvak, vraagt waar het nummer over gaat en schrijft woorden voor de secties die je hebt opgebouwd.
**Regels in een couplet of refrein** bepaalt hoe lang elke sectie is: meer regels in een sectie geven een langer nummer, omdat de
planner ongeveer zoveel muziek schrijft als er woorden zijn. De stijl hierboven zet de sfeer. Gemma schrijft het concept in dezelfde
engine, en het komt in het vak aan met een titel als je er nog geen had gegeven; een [externe LLM](#external-llm) kan het in plaats daarvan schrijven, ingesteld in Instellingen. Het venster sluit zodra het concept begint, en de voortgang verschijnt naast het tekstvak.
De knoppen van de teksteditor voegen ook elk van deze secties toe, plus stemaanwijzingen (+ Man, + Vrouw, + Beide).

**Hoe de regels klinken** bepaalt het ritme en het rijm waar de schrijver op mikt. *Natuurlijk* (standaard) mengt korte en lange regels
met wat rijm. *Regelmatig rijm* is de traditionele vorm van gelijke regels die per twee rijmen, wat de
schrijver maakte voordat deze keuze bestond. *Gesproken ritme* is spreektalig, als spreken of rap; *Los
rijm* laat maar sommige regels rijmen; *Kort en krachtig* en *Lang en vloeiend* bepalen de lengte van de regels.

Het is een eerste concept. De regels hebben ritme en rijmen, maar een model grijpt naar bekende beelden, en niets
controleert of een regel al van iemand anders is. Lees het en maak het je eigen voordat je plant.

---

## Een nummer schrijven vanuit een prompt: alle opties {#writing-a-song-from-a-prompt-every-option}

**+ Nummer** heeft inmiddels veel opties. Geen ervan is verplicht: een stijl en wat tekst zijn genoeg, zoals in
[Je eerste nummer](#your-first-song). Dit hoofdstuk loopt ze allemaal langs in de volgorde waarin de editor ze toont,
in zijn drie kolommen (het nummer, de tekst en de klank), en daarna wat je na het plan doet. Het eindigt met een
tabel van veelvoorkomende wensen, zoals een langer nummer of een refrein dat anders klinkt dan het couplet.

### Het nummer {#the-song}

- **Titel.** Optioneel. Leeg gelaten wordt de eerste regel van de tekst gebruikt.
- **Stijl.** De lijst **Een stijl kiezen…** heeft 200 vertrekpunten, van afrobeats tot zydeco, op alfabet.
  Een keuze vult het vak Stijl met een volledige beschrijving, die je daarna kunt bewerken. De chips eronder zijn tien
  snelle starts voor een nummer: warm indie rock, soulful jazz-pop, synthwave, acoustic ballad, heavy rock, modern pop,
  country, hip hop, smooth R&B en dance pop. Zie [Wat je in het vak Stijl zet](#what-to-put-in-the-style-box).
- **Een eigen stijl bewaren.** **Opslaan**, naast de lijst, bewaart wat er in het vak Stijl staat onder een naam die je
  kiest. Het eerste item van de lijst, **Opgeslagen stijlen**, opent de stijlen die je bewaarde; het prullenbakje ernaast verwijdert er een, en de
  zoekfunctie van de lijst vindt ze samen met de 200. Bewaren onder een naam die al bestaat vervangt die stijl. Het triggerwoord van een
  stijl-LoRA wordt niet bewaard, en wordt opnieuw ingevuld voor de LoRA die gekozen is als je de stijl gebruikt.
- **Een tempo in de stijl is maar een hint.** De planner kiest meestal zijn eigen. Om het tempo vast te zetten, gebruik **Tempo vastzetten** in
  Geavanceerd.
- **Zang.** De chips schrijven een stem (vrouwelijk, mannelijk, duet en een karakter) voor je in de stijl.
- **Stijl-LoRA.** Onderaan de klankkolom. Zie [Stijl-LoRA's](#style-loras).

### De tekst {#the-words}

**De structuur.** Boven het tekstvak staat, zolang het geen woorden heeft, een lijst met secties: de volgorde die
het nummer zal volgen. Elke rij kan in een andere sectie veranderen, omhoog of omlaag (of gesleept) worden, of verwijderd, en de
chips onder de lijst voegen een sectie toe. De secties zijn intro, couplet, pre-refrein, refrein, bridge, interlude en outro.
Een **interlude** is een instrumentale passage: hij heeft geen woorden, en de planner speelt hem met de instrumentale stem.
(`solo` is geen sectie die de planner kent; de interlude is de manier om er een te vragen.)

**Beginnen met…** vult de lijst met een gangbare vorm. Beweeg de muis over een keuze om te zien waar die bij past:

| Vorm | Secties | Past bij |
|---|---|---|
| Couplet, refrein, bridge | couplet, refrein, couplet, refrein, bridge, refrein | het klassieke nummer: pop, rock, country |
| Kort | couplet, refrein, couplet, refrein | folk, punk, vroege rock-'n-roll |
| Intro en outro | intro, couplet, refrein, couplet, refrein, outro | ballades, softrock, singer-songwriters |
| Verhaal | couplet, couplet, refrein, couplet, refrein, outro | verhalende nummers, folk, country |
| Pop met pre-refrein | couplet, pre-refrein, refrein, couplet, pre-refrein, refrein, bridge, refrein | moderne pop, dance-pop, poprock |
| Hook eerst | refrein, couplet, refrein, couplet, refrein, bridge, refrein | pop uit het streamingtijdperk, indiepop |
| Kort en simpel | couplet, refrein, couplet, refrein, refrein | punk, garagerock, rockabilly |
| Hiphop | intro, couplet, refrein, couplet, refrein, couplet, outro | rap, hiphop, trap, R&B |
| Dubbele bridge | couplet, refrein, couplet, refrein, bridge, bridge, refrein, refrein | powerballads, progressieve en symfonische rock |
| Interlude | couplet, refrein, interlude, couplet, refrein, bridge, refrein | rock, poprock, indie |
| Alle delen | intro, couplet, pre-refrein, refrein, interlude, couplet, pre-refrein, refrein, outro | pop, dance-pop |

**Hoeveel secties.** De planner schrijft meestal 8 tot 10 secties, wat de tekst ook vraagt, dus een lijst van meer
dan 10 wordt samengeperst en de woorden van de secties die hij laat vallen worden niet gezongen. De bouwer waarschuwt als de lijst
zo lang is. Een nummer wordt niet langer door meer secties; elke sectie wordt gewoon korter. Zie
[Het nummer langer maken](#making-the-song-longer).

**Delen in het tekstvak zetten** plaatst de secties als lege tags, klaar om er met de hand onder te schrijven. Zodra het vak
woorden heeft, wordt de tekst gezongen, en gaat de bouwer opzij.

**Songtekst schrijven.** Beschrijf waar het nummer over gaat en een model schrijft woorden voor de secties die je hebt opgebouwd. Het vraagt
drie dingen:

- **Regels in een couplet of refrein** (4, 6 of 8; standaard 6). Meer regels in een sectie geven een langer nummer,
  omdat de planner ongeveer zoveel muziek schrijft als er woorden zijn. Een intro, bridge of outro blijft op 2 tot 4 regels,
  en een interlude heeft er geen.
- **Hoe de regels klinken.** De lijst toont de lettergrepen waar elke regel op mikt. De oude schrijver maakte bijna altijd dezelfde
  rijmende regels van acht lettergrepen, en dit verandert dat:

| Keuze | Mikt op | Wat je krijgt |
|---|---|---|
| Natuurlijk (standaard) | 3-13 lettergrepen | Een mix van korte en lange regels, wat rijm, geen vaste maat |
| Regelmatig rijm | 6-10 lettergrepen | Gelijke regels die per twee rijmen: de traditionele vorm, en wat de schrijver vroeger deed |
| Gesproken ritme | 5-14 lettergrepen | Spreektalig en ritmisch, als spreken of rap, met binnenrijm |
| Los rijm | 4-13 lettergrepen | Sommige regels rijmen, sommige half, sommige niet, met wisselende lengtes |
| Kort en krachtig | 3-6 lettergrepen | Korte regels en herhaalde zinnen |
| Lang en vloeiend | 10-14 lettergrepen | Lange regels die stromen als een gedachte |

  De laatste keuze wordt onthouden. Het zijn doelen, geen garanties: een taalmodel volgt ze nauw aan de
  uitersten (kort en krachtig, lang en vloeiend) en losser in de tussengebieden.
- **De opdracht** zelf, in je eigen woorden, en de stijl hierboven, die de sfeer zet. De opdracht wordt met de take bewaard,
  dus een take openen en op **Songtekst schrijven** klikken toont waar het over moest gaan, klaar om te veranderen en opnieuw te schrijven.

Het concept komt in het tekstvak, en het venster sluit zodra het begint. Het is een eerste concept: lees het en maak het
je eigen.

**Deze structuur precies volgen** (het vinkje onder het tekstvak, standaard uit). De planner neemt de sectietags
van de tekst als leidraad, en schrijft uit zichzelf een eigen vorm: hij voegt vaak een intro en outro toe,
ruilt een bridge voor een interlude en een couplet, of perst een lange lijst samen. Met dit aan schrijft het plan precies de
secties die de tekst noemt, in die volgorde, en geen andere. Het kan geen intro of outro toevoegen die jij
niet hebt gezet. De planner beslist nog steeds hoe de muziek gaat en wanneer elke sectie begint. Geldt alleen voor nummers.

**Wie zingt welke regel: stemaanwijzingen.** Een losse regel tussen vierkante haken die een stem noemt, zegt wie de
volgende regels zingt, tot de volgende aanwijzing of de volgende sectie:

```
[Verse 1]
[male voice]
The ferry leaves at half past nine
I watch the harbour lights go by
[female voice]
I wait beside the ticket line

[Chorus]
[both voices]
Carry me over, carry me home
```

Schrijf een aanwijzing als `[male voice]`, `[female voice]` of `[both voices]`, elk op een eigen regel tussen vierkante haken.
De vergrote teksteditor heeft de knoppen **+ Man**, **+ Vrouw** en **+ Beide** in de kop om ze bij de cursor in te voegen.
Dit zijn de vormen waarmee de functie is getest, plus `vocal` in plaats van `voice` (`[female vocal]`) en
`[male and female voices]` voor beide. Je kunt eigen woorden toevoegen na een komma, zoals
`[female voice, soft and close]`; die veranderen niet wie zingt. Een sectie zonder aanwijzing wordt aan de planner overgelaten.

Andere schrijfwijzen worden ook gelezen, zodat elders geschreven teksten niet worden genegeerd: `[man]`, `[woman]`, `[duet]`, een aanwijzing
in de tag van een sectie zoals `[Verse 2 - female vocal]`, en een aanwijzing tussen ronde haken, `(female voice)`. Vierkante haken
zijn de veiligste gewoonte: woorden tussen ronde haken zijn vaak achtergrondzang, en kunnen gezongen worden.

Een aanwijzing alleen beslist de stem niet. Wie zingt hangt vooral af van hoe hoog de melodie is geschreven: dezelfde
regel een octaaf hoger wordt door een vrouw gezongen, en de planner schrijft een couplet graag over twee octaven, wisselend om de vier
regels of zo, wat er ook is aangewezen. **Stemmen volgen de aanwijzingen** (een vinkje onder het tekstvak, dat verschijnt als de tekst
een aanwijzing heeft; aan voor een nieuwe take) houdt zich aan de aanwijzingen: als het plan wordt geschreven, schuift elk aangewezen stuk melodie per
heel octaaf naar waar die stem zingt, laag voor een man en hoog voor een vrouw. Verder verandert er niets aan het plan. Het wordt
voor elke render opnieuw gedaan, dus het volgt een wijziging in de tekst of de partituur. Op de pagina Partituur doet
**Stemmen naar aanwijzingen** hetzelfde één keer met de partituur in het vak, voor een take gemaakt zonder het vinkje; bewaar de partituur
en render hem.

Drie dingen om te weten:

- **Wie een regel zingt is nog deels toeval.** Met de melodie op zijn plek gaan de meeste regels naar de aangewezen
  stem, maar een render kan er toch een aan de andere stem geven. Render opnieuw met een andere seed, of gebruik
  **Meer proberen**.
- **Beide** legt de regel waar een vrouw zingt en laat de tweede stem aan de render, die er vaak een
  in een refrein zet. Het vraagt om een duet meer dan dat het er een maakt: hoeveel je van de tweede stem hoort verschilt per
  render. Er is nog geen manier om twee zangers op één regel te schrijven zonder dat de tekst eronder lijdt.
- Een take gemaakt voordat dit vinkje bestond houdt zijn partituur zoals die is; vink het aan, of gebruik **Stemmen naar aanwijzingen**, om hem bij te werken.

**Met de hand schrijven.** De knop Uitvouwen opent een editor op volle grootte met knoppen voor intro, couplet, pre-refrein,
refrein, bridge, interlude, outro en instrumentaal. Een sectie is een regel zoals `[Verse]` gevolgd door zijn regels; een
tag zonder regels eronder, zoals `[Interlude]`, is een instrumentale passage.

### De klank {#the-sound}

- **Harmonie** (de schuif): hoe gedurfd de akkoorden zijn. Een nieuw nummer begint op **Gevarieerd**, met de interpretatie
  op **Breed**: in onze eigen tests gaf dat paar de muzikaal interessantste versies, dus het is een goed vertrekpunt. Verschuif
  een van beide naar smaak. Bestaande takes houden waarmee ze gemaakt zijn. Uit zichzelf schrijft de planner graag een lus van
  vier akkoorden en gebruikt die in elke sectie, en elk niveau trekt hem daar wat verder vandaan. De niveaus bouwen
  op elkaar voort:

  | Niveau | Wat het met de akkoorden doet | Kies het als |
  |---|---|---|
  | Vertrouwd | Niets: de akkoorden van YuE2, vaak één lus voor het hele nummer | Je de eerste ingeving van de planner mooi vindt, of de eenvoudigste begeleiding wilt |
  | Gevarieerd | Ontmoedigt het precies herhalen van akkoorden die het net gebruikte, dus kleurt ze anders (een F, dan een Fmaj7) maar blijft in de toonsoort | De lus te gelijk klinkt en je wilt dat het nummer conventioneel blijft |
  | Kleurrijk | Hetzelfde, sterker: couplet en refrein gaan uit elkaar, met rijkere akkoorden. Een sectie mag ook niet met dezelfde akkoorden beginnen als de vorige, dus een refrein begint niet meer als zijn couplet | Je wilt dat het refrein een opstuwing is, geen herhaling. Een goede eerste stap |
  | Avontuurlijk | Ontmoedigt kort geleden gebruikte *grondtonen*, niet alleen schrijfwijzen, dus de harmonie moet reizen, en leent akkoorden van buiten de toonsoort | Je wilt beweging en verrassing, en let op een akkoord dat vreemd klinkt |
  | Daarbuiten | Gedurfd, met een trek naar akkoorden buiten de toonsoort | Experimenten. Reken erop dat je wat plannen weggooit |

  Vanaf Kleurrijk komen de akkoordkeuzes per sectie meer verschillend uit: meer verschillende akkoorden in een
  nummer, meer patronen van vier maten die niet herhalen, en minder refreinen die het begin van het couplet kopiëren. Het plan blijft
  een gewoon nummer, dus het loont om een of twee niveaus hoger te proberen voordat je naar een wildere Variatie van het plan grijpt.
  In **Geavanceerd** kan **Delen beginnen anders** op *Altijd* of *Nooit* worden gezet om een plan met en zonder
  de refreinregel te testen; de standaard, *Harmonie volgen*, staat aan vanaf Kleurrijk. Een stijl als trap of ambient is vaak
  van nature op lussen gebouwd, dus verwacht daar een kleinere verandering dan in pop of rock. Zie [Harmonie](#harmony) voor de metingen.
- **Variatie van het plan.** Hoe vrij de planner al het andere schrijft. Zie [Variatie van het plan](#plan-variety).
- **Interpretatie.** Hoe de noten worden gespeeld bij het renderen. Zie [Interpretatie](#interpretation).
- **Lengtegrens.** Het laatste moment waarop het nummer mag eindigen. Zie [Lengte](#length).
- **Modus.** *Volledig* houdt de akkoorden van het plan; *melodie* laat de begeleiding vrij. *Geen partituur*, voor nummers, schrijft
  helemaal geen plan: zie [Een nummer zonder partituur](#a-song-with-no-score).
- **Seed**, en **deze seed houden**. Zie [De seed, en een take reproduceren](#seed-and-reproducing-a-take).
- **Productieafwerking** en **Volume normaliseren.** Zie [Productieafwerking](#production-polish).
- **Renderen zodra het plan klaar is**, naast de knop onderaan het venster, maakt het plan en de render
  zonder tussendoor te stoppen. Het staat in het begin aangevinkt, en de editor onthoudt je keuze. Vink het uit om eerst het
  plan te lezen.
- **Geavanceerd** (de knop in de kop): diffusiestappen, De stijl volgen, Vermijden, Toonsoort vastzetten, Tempo vastzetten, de langste partituur,
  akkoordduur, bonus voor harmonie van buiten, Secties die anders openen, doelluidheid en de eindfade. Zie
  [Geavanceerde instellingen](#advanced-settings).
- **Mastering** (de knop links ervan, als de take klank heeft) opent het masteringrack boven de editor voor
  de take die erin staat. Het rack is, op volgorde, een eq in 1073-stijl, een parametrische eq, een compressor, een stereoverbreder en
  een limiter. In de grafiek van de parametrische eq is elk van de zeven banden een punt: sleep het opzij voor de frequentie
  en omhoog of omlaag voor de versterking, draai het scrollwiel erboven voor de breedte, dubbelklik om het terug te zetten. De strook onder
  de grafiek stelt het type van de gekozen band in (laag afsnijden, laag shelf, klok, notch, hoog shelf, hoog afsnijden) en zet hem aan
  of uit, **Vlak** zet elke band terug op 0 dB, en de knop in de hoek van de grafiek verandert hoeveel decibel de
  grafiek toont. De knop is groen zolang het rack verandert hoe de take klinkt. Met het rack open speelt de spatiebalk
  de take af en pauzeert hem, en bewegen de pijltjes erdoorheen en regelen het volume, zoals op de hoofdpagina. Escape sluit
  het rack, en nog eens sluit de editor.

### Het nummer langer maken {#making-the-song-longer}

De lengte van een nummer wordt bepaald door zijn plan, en de render volgt de lengte van het plan. Dit is wat hem verschuift:

| Om te krijgen… | Doe dit |
|---|---|
| Een langer nummer | Geef elke sectie meer regels (**Regels in een couplet of refrein**: 6 of 8) |
| Een trager, langer nummer | Zet een **Tempo vastzetten** in Geavanceerd. Hetzelfde plan duurt langer bij minder BPM |
| Een langer nummer door secties toe te voegen | Werkt niet: een plan heeft zo'n 8 tot 10 secties, dus meer worden alleen korter of samengeperst |
| Meer dan het plan toelaat | Schrijf een nieuw plan; lengtes variëren sterk tussen runs met dezelfde tekst |
| Een nummer dat eindigt aan het eind van zijn tekst | Verhoog de lengtegrens alleen als hij wordt afgekapt; de grens is een plafond, geen doel |

### Na het plan {#after-the-plan}

- **Deze partituur renderen** maakt een nieuwe take zodra de geopende take al audio heeft, dus een render overschrijft nooit een
  take die je wilt vergelijken. Een take die nog geen audio heeft wordt aangevuld.
- **Deze melodie houden** (nadat je de tekst van een take hebt veranderd): zingt de partituur van de take met de nieuwe tekst, als nieuwe take. De
  melodie kan geen secties of noten bijkrijgen, dus als je tekst meer secties heeft dan de melodie, of veel meer of veel minder
  lettergrepen dan hij noten heeft (lange regels op een melodie gemaakt voor korte, of korte op een gemaakt voor lange), vinkt
  het vakje zichzelf uit en wordt er een nieuw plan geschreven, met een regel die zegt waarom. Zie [Zelfde melodie, nieuwe tekst](#same-tune-new-words).
- **De bibliotheek filteren.** De knoppen **Nummer**, **Cover** en **Instrumentaal** naast de filters tonen alleen die
  soorten in de geopende ruimte; kies er meer dan één, of geen voor alle soorten.

---

## Het plan lezen en verbeteren {#reading-and-fixing-the-plan}

Het plan is geschreven in **ABC-notatie**: muziek als platte tekst, letters in plaats van stippen op een notenbalk.
Chris Walshaw bedacht het begin jaren negentig om folkmelodieën per e-mail te versturen, en het bleef.

Je hoeft het niet te kunnen lezen. De app toont hetzelfde plan als **akkoordenschema** en als echte **notatie
op notenbalken** onder de editor, en **Uitvouwen** opent het geheel op volle grootte. Maar de tekst is wat YuE2
schreef en waaruit het rendert, dus het loont om je erin te kunnen redden.

### Een plan lezen {#reading-a-plan}

Een plan begint met een kop, één letter en een dubbele punt per regel:

```
X:1
M:4/4
L:1/32
Q:1/4=120
V: Vocal clef=treble name="Vocal Melody"
V: Ins   clef=treble name="Ins Melody"
K:D#m
```

| Regel | Betekent |
|---|---|
| `X:1` | het nummer van de melodie. Elk ABC-bestand begint met een |
| `M:4/4` | de maatsoort — vier tellen per maat |
| `L:1/32` | de eenheidslengte: een losse letter duurt een tweeëndertigste noot |
| `Q:1/4=120` | het tempo — een kwartnoot op 120 tellen per minuut |
| `V:` | declareert een stem. YuE2 schrijft er twee, een zanglijn en een instrumentale lijn |
| `K:D#m` | de toonsoort, dis mineur. `K:` staat altijd aan het eind van de kop |

Daarna de muziek zelf:

```
% intro
V: Vocal
z24z4"D#m"z4|"D#m"z32|
V: Ins
Z|d16a16-|a16g8a8|
```

- **Noten zijn letters.** `d16` is een D die 16 eenheden duurt. Kleine letters klinken een octaaf hoger dan hoofdletters,
  en `'` of `,` verschuiven ze verder.
- **`-` bindt** een noot aan de volgende, zodat ze als één klinken.
- **`z` is een rust**, met een lengte zoals een noot. Een hoofdletter `Z` is een rust van een hele maat.
- **Akkoorden staan tussen dubbele aanhalingstekens**, zoals `"D#m"`, en staan voor de noot waarop ze beginnen. Dit
  is wat **zoeken en vervangen** bewerkt.
- **`|` is een maatstreep**, en **`%` begint een opmerking** — zo worden secties gemarkeerd:
  `% intro`, `% verse`, `% chorus`.

Dat fragment zegt dus: dis mineur, vier vierde, 120 tellen per minuut, en tijdens de intro zwijgt de
stem terwijl ze het akkoord draagt, terwijl het instrument een gebonden D en A speelt, daarna G en A.

Twee praktische gevolgen. **De akkoorden bewerken is veilig**, ook als de noten ondoorgrondelijk lijken — het zijn alleen
de stukken tussen aanhalingstekens, en al het andere kan blijven zoals het is. En **als je het plan bewerkt, gebruikt de render
wat je bewerkte**, dus er een verbeteren is vaak sneller dan opnieuw gooien tot er een goede uitkomt.

### Ernaar luisteren {#hearing-it}

Het tabblad **Notatie** heeft een speler boven de notenbalken. Klik op **Afspelen** om het plan te horen zoals het in het
vak staat, bewerkingen en al, om een melodie waar je aan twijfelt op het gehoor te beoordelen voordat je er een render aan
besteedt. De noten die hij speelt lichten mee op, en zijn tempoknop verandert alleen de voorbeeldweergave,
niet de partituur. Afspelen stopt wat de spelerbalk speelde, omdat twee dingen tegelijk niemand
helpen, en het venster sluiten — of naar Akkoorden of Tekst gaan — stopt het ook, zodat niets blijft
spelen zonder een knop binnen handbereik.

**Instrumenten** speelt elke stem op een instrument dat de stijl noemt, in plaats van een piano
voor alles: een stijl die *electric guitar, drums* zegt klinkt met een gitaar, de akkoorden gespeeld door
een tweede, en een bas eronder; een gezongen lijn wordt door een stem vervangen, en de melodie van een instrumentaal
niet. Een stijl die drums noemt krijgt ook een drumpartij, geschreven in de maatsoort van de partituur
zelf — een backbeat voor rock, four-on-the-floor voor dance, een ride voor jazz, iets karigers voor een
ballade — en die speelt van begin tot eind, omdat de partituur geen secties heeft om in te zwijgen. De
regel naast de speler zegt wat hij koos, en uitvinken gaat terug naar de piano die je anders
zou horen. Het is een lezing van de stijl, niet van de render: YuE2 beslist de
echte uitvoering en voegt partijen toe die de partituur nooit had, dus zie het als het plan gespeeld in de juiste
kleuren, meer dan als hoe de take zal klinken.

**MIDI downloaden** bewaart de partituur voor een DAW. Elke partij is een eigen spoor, op een eigen kanaal,
met het instrument dat het voorbeeld gebruikte aan dat kanaal toegewezen: de zanglijn, de instrumentale lijn en,
tenzij je **Akkoorden** uitvinkt, de akkoordsymbolen als akkoordpartij met de bas ernaast (de enige
plek waar de harmonie in noten is uitgeschreven), en de drums op kanaal 10 als de stijl erom vraagt. De
instrumenten zijn General MIDI-programmanummers, dus je DAW speelt ze met zijn eigen klanken, en het
tempo en de maatsoort staan in het bestand. Een plan dat halverwege van maatsoort wisselt wordt geschreven in de maatsoort waarmee het
begint — alleen die wordt vastgelegd — terwijl de noten hun eigen lengtes houden. Op een noot in de
notenbalken klikken zet de cursor op de ABC die hem schreef.

Een partituur met een noot boven wat deze instrumenten kunnen spelen, of eronder, wordt per hele octaaf verschoven gespeeld
tot hij past, en de regel naast de speler zegt hoeveel; de notenbalken, het MIDI-bestand en
de partituur zelf veranderen niet. Instrumenten hebben niet allemaal hetzelfde bereik — een bas ligt ver onder
een piano — daarom verschijnt de regel als een partituur wordt verschoven. Een partituur die nog geen noten heeft
heeft niets om te spelen en zegt dat.

De speler heeft zijn nootsamples nodig, die geen deel van de app zijn: elk instrument is zo'n 7 MB,
wordt de eerste keer dat een voorbeeld het gebruikt bij de bron gedownload en in de bibliotheek bewaard, dus
daarna werkt het offline. **Afspelen** downloadt wat de huidige partituur nodig heeft en begint dan, en
**Klanken ophalen** downloadt hetzelfde zonder te spelen, voor wie het liever van tevoren
klaar heeft.

### De pianorol {#the-piano-roll}

Klik op **Pianoroll** in het partituurvenster om de visuele MIDI-editor te openen. In plaats van ruwe ABC-letters te bewerken, zie en vorm je de melodie rechtstreeks op een interactief raster van toonhoogte en tijd.

De editor toont beide stemmen van de partituur tegelijk — **Vocal** (de hoofdzangmelodie in hemelsblauw) en **Ins** (de instrumentale begeleiding in warm amber). Beide stemmen zijn altijd volledig actief, zichtbaar, selecteerbaar en bewerkbaar. De knoppen **Tekenen** linksboven kiezen aan welke stem nieuwe noten worden toegewezen als je klikt om ze toe te voegen.

#### Noten bewerken {#editing-notes}

- **Een noot toevoegen:** klik op een lege cel in het raster om een noot op die toonhoogte en dat moment te maken. De noot klinkt meteen zodat je de toon hoort.
- **Noten selecteren:** klik op een noot om hem te selecteren. Houd <kbd>Shift</kbd> of <kbd>Ctrl</kbd>/<kbd>Cmd</kbd> ingedrukt tijdens het klikken om meerdere noten in de zang- en instrumentale partijen te selecteren. Klik en sleep een **selectiekader** over een leeg gebied om een frase of passage in alle stemmen te selecteren. Druk op <kbd>Ctrl</kbd>+<kbd>A</kbd> (<kbd>Cmd</kbd>+<kbd>A</kbd> op macOS) of klik op **Alles selecteren** om alle noten van de partituur te selecteren. Om alle noten van de afspeelcursor tot het eind van het nummer te selecteren, druk op <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>A</kbd> of <kbd>Alt</kbd>+<kbd>A</kbd> (of klik op **Vanaf cursor ▶** in de werkbalk).
- **Noten verplaatsen:** sleep een geselecteerde noot naar voren of naar achteren in de tijd, of verticaal om de toonhoogte te transponeren. Als er meerdere noten geselecteerd zijn — zang, instrumentaal of beide — bewegen ze allemaal samen, met behoud van hun onderlinge timing, melodieën en tekst.
- **Lengte:** sleep de rechterrand van een noot om hem langer of korter te maken. De keuzelijst **Uitlijnen** (1/16, 1/8 of 1/4 noot) beperkt verplaatsen en van grootte veranderen tot nette muzikale onderverdelingen.
- **Noten verwijderen:** dubbelklik op een noot om hem te verwijderen, of selecteer er een of meer en druk op <kbd>Delete</kbd> of <kbd>Backspace</kbd>.
- **Ongedaan maken en opnieuw:** elke bewerking, verplaatsing, lengteverandering, toevoeging en verwijdering van een noot komt in de geschiedenis. Druk op <kbd>Ctrl</kbd>+<kbd>Z</kbd> (<kbd>Cmd</kbd>+<kbd>Z</kbd>) om ongedaan te maken, en <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>Z</kbd> of <kbd>Ctrl</kbd>+<kbd>Y</kbd> om opnieuw te doen.
- **Toetsen beluisteren:** klik op een toets van het pianoklavier links om de toonhoogte te horen.
- **Maximaliseren:** klik op **Maximaliseren** in de bovenbalk om de pianorol over de volle breedte van het browservenster uit te rekken.

#### Tijdlijn, secties en akkoorden {#timeline-sections-and-chords}

Langs de bovenste liniaal toont de tijdlijn de maatnummers en de sectiegrenzen:
- **Secties hernoemen:** klik op een sectiemarkering (`intro`, `verse`, `chorus` enz.) om de naam te bewerken of hem opnieuw toe te wijzen.
- **Akkoorden bewerken:** net onder de maatliniaal toont het akkoordspoor de harmonische progressie van het nummer. Klik op een bestaand akkoord om het te hernoemen (bijvoorbeeld `C` in `Am7` of `G/B` veranderen), of op een lege maat om een nieuw akkoord te plaatsen.
- **Lege maten harmoniseren (Gaten vullen):** klik op **Gaten vullen** in de werkbalk om lege maten in de instrumentale begeleiding te vullen met noten gemaakt uit de akkoordprogressie.
- **Lege maten weghalen (Gaten dichten):** klik op **Gaten dichten** om lege, stille maten in beide stemmen weg te halen, waarbij de noten en akkoorden erna naar links schuiven om ongewenste gaten in het arrangement te dichten.

#### Tekst en karaoke {#lyrics-and-karaoke-tracking}

Onderaan de pianorol zet een eigen tekstspoor elke lettergreep op de zangmelodie:
- **Passen per frase:** klik op **Tekst koppelen** om de tekst over de zangmelodie te verdelen. De uitlijning herkent natuurlijke ademhalingen en rusten tussen melodische frasen, en wijst elke tekstregel toe aan zijn frase zonder woorden over rusten heen naar volgende maten te laten lopen. Woorden van meerdere lettergrepen worden netjes over noten verdeeld.
- **Lettergrepen bewerken:** klik op een tekstlabel (of selecteer een zangnoot en druk op <kbd>L</kbd>) om de tekst te bewerken. Als je lettergrepen typt gescheiden door spaties of streepjes (bijvoorbeeld `Hel- lo world`), worden ze automatisch over opeenvolgende zangnoten verdeeld.
- **Markering bij aanwijzen:** de muis over een tekstlabel bewegen markeert de bijbehorende noot in het raster, en over een zangnoot bewegen markeert het label eronder.
- **Karaokebal:** tijdens het afspelen stuitert een geanimeerde bal over elke noot terwijl die gezongen wordt, en lichten de actieve lettergreep en de rasternoot in realtime op.

#### Afspelen en harmonische begeleiding {#playback-and-harmony-accompaniment}

Druk op <kbd>Space</kbd> of klik op **▶ Afspelen** om vanaf de cursor af te spelen. De afspeellijn veegt over het raster en werkt maat, tel en verstreken tijd bij.

- **Hoorbare klik (metronoom):** afspelen heeft standaard een hoorbare klik, met een geaccentueerde woodblocktik op de eerste tel van elke maat en zachtere klikken op de andere. Druk op <kbd>C</kbd> of <kbd>M</kbd> (of klik op **Klik** in de transportbalk) om de metronoom op elk moment aan of uit te zetten.
- **Harmonische akkoordbegeleiding:** afspelen synthetiseert warme, polyfone akkoordpads rechtstreeks uit de akkoordprogressie van de partituur. Ook als de zang- of instrumentale sporen zwijgen, blijft de harmonische ruimte muzikaal en warm in plaats van in dode stilte te vallen. Druk op <kbd>H</kbd> (of klik op **Akkoorden** in de transportbalk) om de akkoordbegeleiding aan of uit te zetten.
- **Per maat navigeren:** druk op <kbd>Pijl links</kbd> en <kbd>Pijl rechts</kbd> om maat voor maat terug en vooruit te gaan, of <kbd>Home</kbd> om meteen naar het begin te gaan.

#### Sneltoetsen {#keyboard-shortcuts}

| Toets | Actie |
|---|---|
| <kbd>Space</kbd> | Afspelen / pauzeren |
| <kbd>Pijl links</kbd> | Eén maat terug |
| <kbd>Pijl rechts</kbd> | Eén maat vooruit |
| <kbd>Home</kbd> | Terug naar het begin (maat 1) |
| <kbd>C</kbd> of <kbd>M</kbd> | Hoorbare klik (metronoom) aan / uit |
| <kbd>H</kbd> | Akkoordbegeleiding aan / uit |
| <kbd>Delete</kbd> / <kbd>Backspace</kbd> | Geselecteerde noten verwijderen |
| <kbd>Ctrl</kbd>+<kbd>Z</kbd> / <kbd>Cmd</kbd>+<kbd>Z</kbd> | Laatste bewerking ongedaan maken |
| <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>Z</kbd> / <kbd>Ctrl</kbd>+<kbd>Y</kbd> | Opnieuw |
| <kbd>Ctrl</kbd>+<kbd>A</kbd> / <kbd>Cmd</kbd>+<kbd>A</kbd> | Alle noten in beide stemmen selecteren |
| <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>A</kbd> / <kbd>Alt</kbd>+<kbd>A</kbd> | Alle noten van de cursor tot het eind in beide stemmen selecteren |
| <kbd>+</kbd> of <kbd>=</kbd> | Horizontaal inzoomen |
| <kbd>-</kbd> of <kbd>_</kbd> | Horizontaal uitzoomen |
| <kbd>0</kbd> | Naar de noten scrollen (passend maken) |
| <kbd>L</kbd> | De tekst van de geselecteerde zangnoot bewerken |
| <kbd>Escape</kbd> | Selectie wissen, of het partituurvenster sluiten |

### Harmonie {#harmony}

Uit zichzelf schrijft YuE2 graag een lus van vier akkoorden en blijft daar. De schuif **Harmonie** trekt het weg
van akkoorden die het net gebruikte, zonder de structuur van het nummer te breken.

| Niveau | Wat je krijgt |
|---|---|
| Vertrouwd | De akkoorden van YuE2. Vaak één lus voor het hele nummer |
| Gevarieerd | Vermijdt het herhalen van dezelfde akkoorden. Blijft in de toonsoort |
| Kleurrijk | Couplet en refrein krijgen verschillende progressies, met rijkere akkoorden. Een sectie mag niet beginnen zoals de vorige |
| Avontuurlijk | Houdt de harmonie in beweging en leent akkoorden van buiten de toonsoort |
| Daarbuiten | Gedurfd, en gaat verder buiten de toonsoort |

**Een nieuw plan schrijven** gebruikt de huidige stand van de schuif, dus je kunt opnieuw gooien met dezelfde tekst en gedurfdere
akkoorden en vergelijken.

Dit is gemeten in plaats van aangenomen — één tekst, twee stijlen, elk drie seeds:

| | Vertrouwd | Gevarieerd | Kleurrijk | Avontuurlijk | Daarbuiten |
|---|---|---|---|---|---|
| Verschillende akkoorden in een nummer | 4.7 | 6.3 | 8.7 | 9.0 | 10.3 |
| Maten met een akkoord buiten de toonsoort | 0% | 0% | 0% | 13% | 24% |
| Patronen van vier maten die niet herhalen | 29% | 38% | 50% | 63% | 64% |

Elk plan, op elk niveau, hield geldige secties en akkoorden. In plaats daarvan om gedurfde harmonie vragen in de
stijltekst — “jazz harmony”, “borrowed chords” — had geen meetbaar effect.

### Variatie van het plan {#plan-variety}

In *Geavanceerd* bepaalt **Variatie van het plan** hoe vrij de planner schrijft. Waar Harmonie op de
akkoorden werkt, werkt dit op alles: melodie, structuur en lengte.

- **Rustig:** het stabielst. Weinig akkoorden, en een melodie die niet afdwaalt.
- **Normaal:** de standaard.
- **Levendig:** wat meer akkoorden en wendingen.
- **Gedurfd:** rijkere harmonie, zo'n drie keer de normale akkoordenschat, terwijl de melodie
  herkenbaar van hetzelfde soort blijft.
- **Eigenzinnig:** rusteloos. De akkoorden blijven veranderen, en de melodie springt van register van de ene
  sectie naar de volgende. Voor vreemde, grillige nummers.
- **Wild:** het rusteloost van allemaal, en kan halverwege van toonsoort veranderen.

### Een nummer zonder partituur {#a-song-with-no-score}

**Geen partituur**, de derde keuze van **Modus**, zingt de tekst zonder enig plan: YuE2 schrijft de melodie en
de akkoorden terwijl het zingt, zoals de oorspronkelijke YuE deed, en het nummer wordt meteen gerenderd met **Zingen zonder partituur**.
Het klinkt vaak heel anders dan een gepland nummer.

Wat een plan stuurt heeft hier niets om op te werken, dus **Harmonie**, **Variatie van het plan**, **Deze melodie houden** en **Deze structuur precies volgen**
worden gedimd zolang dit gekozen is, en er is geen partituur om te lezen of te bewerken. YuE2 bepaalt
de lengte, tot aan de grens. Toonsoort vastzetten en Tempo vastzetten bereiken het alleen als woorden in de stijl. Opnieuw zingen,
Variaties, Meer proberen en de nieuwe tekst werken allemaal, elk opnieuw gezongen zonder partituur. **Een nieuw plan schrijven** geeft de take een
partituur, en Modus gaat terug naar *volledig*. Het is alleen voor nummers vanuit een prompt: een cover is de partituur van zijn opname, en een
instrumentaal heeft er een nodig om de stem buiten te houden. Beide engines kunnen het.

---

## Renderen {#rendering}

### Interpretatie {#interpretation}

De partituur bepaalt de noten. De **interpretatie** bepaalt hoe ze gespeeld worden.

| Interpretatie | Wat je hoort |
|---|---|
| Standaard | De gewone lezing van YuE2 |
| Strak | strakker en gepolijster |
| Los | rauwer en spontaner |
| Rustig | vrij om een figuur te herhalen en in een groove te blijven |
| Onrustig | houdt de partijen in beweging, vermijdt herhaling |
| Breed | zoekt minder voor de hand liggende klanken |

### Variaties {#variations}

De fonkelknop op een kaart rendert **dezelfde partituur en dezelfde seed** in de andere
interpretaties. Omdat alleen de interpretatie verandert, is wat je ertussen hoort de
interpretatie — geen nieuwe worp van de dobbelstenen. Elk is een eigen take, getiteld
*Night drive · Loose* en bewaard in de take waaruit hij kwam (zie **Takes in een take**,
onder De bibliotheek). Het venster heeft een eigen lengtegrens, die begint bij die van de editor en alleen geldt
voor deze takes.

### Meer proberen {#try-more}

De dobbelsteenknop op een kaart rendert **dezelfde partituur en tekst opnieuw als meerdere nieuwe takes**, om
naast elkaar te beluisteren. Variaties verandert alleen de interpretatie en houdt de seed; dit verandert de
worp:

- **Nieuwe seeds:** een nieuwe seed voor elke take, al het andere gelijk.
- **Planner-sterktes:** voor een take met een stijl-LoRA die een plannerhelft heeft, dezelfde seed met
  andere Planner-sterktes (die van hemzelf wordt overgeslagen). De planner verandert de uitvoering zelf, niet alleen
  de stem, dus dit werkt als een andere seed.

De nieuwe takes heten *Night drive · try 1* of *Night drive · planner 0.60* en worden bewaard in
de take waaruit ze kwamen, waarvan het paneel opengaat om ze te tonen zodra ze klaar zijn. Om ze tegen elkaar
te horen, klik op **Alles selecteren** terwijl het paneel open is en dan op **Vergelijken**. Het venster heeft een eigen
lengtegrens, die begint bij die van de take.

### De seed, en een take reproduceren {#seed-and-reproducing-a-take}

Elke take legt zijn seed vast en elke instelling die hem vorm gaf. De kaart noemt ze, op een kaart klikken
toont ze in het takepaneel, en hem in de editor openen laadt alles opnieuw. **Nog eens** opent de
editor met precies dat, seed inbegrepen, om een take te reproduceren die je beviel, en één instelling tegelijk te veranderen bij een die je bijna
beviel.

In de menu's van de editor toont de muis over een interpretatie bewegen wat die doet.

Vink **deze seed houden** aan om dezelfde seed tussen renders te houden; uitgevinkt trekt elke render een
nieuwe.

Een render gebruikt wat de editor toont: de stijl, de stijl-LoRA en zijn sterktes, de lengtegrens, de modus,
de interpretatie en de seed, ook als je de eigen partituur van een take opnieuw rendert.

### Zelfde melodie, nieuwe tekst {#same-tune-new-words}

De planner leest de hele tekst voordat hij een noot schrijft, dus dezelfde seed geeft alleen hetzelfde plan
met dezelfde tekst. Verander één regel en het volgende plan is een nieuwe melodie: een andere melodie, vaak een andere
toonsoort en een ander tempo, en de stem verandert mee.

Om een melodie te houden die je bevalt, open je de take en verander je zijn tekst. **Deze melodie houden** verschijnt onder de
tekst, aangevinkt, en de hoofdknop wordt **Zingen met nieuwe woorden**. Verander eerst al het andere dat je
wilt: de stijl, de LoRA en zijn sterktes, de lengtegrens, de interpretatie. De partituur van de take wordt
dan met de nieuwe tekst gezongen, als nieuwe take naast het origineel, dat blijft zoals het is. Laat de seed
aangevinkt om de stem zo gelijk mogelijk te houden. Vink **Deze melodie houden** uit om in plaats daarvan een nieuw plan, en een
nieuwe melodie, voor de tekst te schrijven. Een nieuwe tekst die het aantal lettergrepen van de oude regels houdt past het best
op de melodie. Als dat niet zo is, omdat er meer secties zijn of veel meer lettergrepen dan de melodie noten heeft (lange regels op een melodie
gemaakt voor korte: regels komen herhaald uit of vallen weg), of veel minder (korte regels op een melodie gemaakt voor lange:
de zanger vult de overgebleven noten met eigen woorden), vinkt **Deze melodie houden** zichzelf uit met een regel die zegt waarom, en
wordt er een nieuw plan voor de tekst geschreven. Vink het weer aan om de melodie toch te zingen.

### Productieafwerking {#production-polish}

**Productieafwerking** past de Realaudio-decoder-LoRA van Mothersuperior toe. YuE2 zoals het is klinkt vaak dof
in het middengebied; dit scheidt instrumenten en stemmen schoner. Standaard aan.

### Lengte {#length}

De lengtegrens is een hard plafond, geen doel. YuE2 beslist wanneer een nummer eindigt, en meestal eindigt het
vanzelf; de grens stopt het nummer dat dat niet doet. Hij begint op 360 seconden, of wat **Maximale lengte voor een nieuwe take**
in Instellingen zegt. Daarna maakt hij plaats voor de muziek, zodat een lang nummer niet wordt afgekapt:

- Een **nummer of instrumentaal vanuit een prompt** krijgt een hogere grens als zijn plan wordt geschreven, als het plan
  langer is: tot de lengte van het plan met zo'n tien seconden speling. Hij wordt nooit verlaagd.
- Met een **opname** gekozen, voor een cover of een instrumentaal, volgt de grens de partituur van de opname,
  op dezelfde manier naar boven afgerond.

Een grens die je zelf typt blijft zoals je hem zette, en de pagina Partituur waarschuwt dan als een plan langer is
dan die grens. Een plan dat veel langer is dan zijn grens (meer dan een derde erboven, en langer dan acht minuten) wordt helemaal niet
voor een nummer aangezien, en wordt opnieuw geschreven. Af en toe
stopt een render niet aan het eind van zijn partituur en loopt door tot de grens; die take fadet
in zijn laatste seconden in plaats van af te kappen, en zijn kaart zegt dat hij de grens bereikte. Nog zeldzamer eindigt een
render voordat de laatste sectie van zijn partituur begint. De app rendert hem dan opnieuw met een
nieuwe seed voordat hij hem klaar noemt, en als die ook te kort uitvalt, zegt de kaart dat hij stopte voor de
laatste sectie: **Renderen** nog eens voor een nieuwe poging.

---

## Een cover van een opname maken {#covering-a-recording}

1. Sleep een audiobestand erin, tot 2 GB. Het wordt één keer opgeslagen en gehasht, dus hetzelfde bestand wordt nooit
   twee keer opgeslagen. Een videobestand (MP4, MOV, MKV, WebM en dergelijke) kan ook: alleen het geluid wordt bewaard, als FLAC.
2. Klik op **Transcriberen**. SheetSage2 schrijft de melodie en de akkoorden in het partituurvak. Dit wordt
   per opname gecachet, dus een volgende cover van hetzelfde nummer slaat het over.
3. Verbeter wat het verkeerd hoorde.
4. Voeg een tekst toe, kies een stijl, klik op **Cover maken**.

Een cover volgt de melodie en de akkoorden van het origineel terwijl de stijl al het andere bepaalt, en dat
maakt het een cover en geen kopie.

### Een eigen melodie opnemen {#recording-a-tune-of-your-own}

> [!NOTE]
> Hoe goed een melodie wordt herkend hangt af van de opname, en een plan dat eromheen is gebouwd kan nog steeds missen of
> afdwalen: schrijf een nieuw plan, of neem de melodie opnieuw op.

In de modus **Cover** opent **Melodie opnemen** de recorder. Kies wat je opneemt bij **Ingang**:

- **Stem:** zing of neurie in een microfoon. **Autotune** kan de opname op een toonsoort en toonladder trekken; de
  knop van een opname wisselt tussen de gestemde versie en het origineel zodat je hoort wat het deed.
- **Instrument:** speel de melodie op een instrument, bijvoorbeeld een gitaar aangesloten op een audio-interface.
  Speel hem **noot voor noot**: de lijn die je speelt wordt de melodie die gezongen wordt, en aangeslagen
  akkoorden geven geen melodie om te zingen. Kies de interface bij **Apparaat**, en bij **Kanaal** de kant
  waarop je instrument is aangesloten (ingang 1 van een interface is meestal **Links**). Zet **Ingangsversterking** hoger
  voor een zacht instrument, en houd de meter uit CLIP. Autotune wordt niet aangeboden: een instrument is al
  gestemd. Yeufonic onthoudt deze keuzes in deze browser.

De metronoom, het aftellen en meeluisteren via de koptelefoon werken voor beide hetzelfde. **Als cover gebruiken** bewaart de
opname als opname, gemarkeerd **MIC** of **INST** in de lijst. Transcribeer hem zoals elke opname; een
opgenomen melodie wordt alleen als melodie getranscribeerd, omdat akkoorden die uit een losse melodie geraden zijn in
elk refrein van een nummer ermee zouden blijven hangen (een opname die eerder is getranscribeerd houdt zijn akkoorden tot hij
opnieuw wordt getranscribeerd). Tien tot dertig seconden melodie is ruim genoeg.
**Songtekst eruit halen** wordt niet aangeboden voor een instrumentopname, omdat er geen woorden te horen zijn: gebruik
**Songtekst schrijven**.

**Hoor je jezelf met vertraging?** De browser voegt een kleine vertraging toe tussen wat je zingt of speelt en wat
je in de koptelefoon hoort. Als je audio-interface direct monitoren (zonder latentie) heeft, gebruik dat
en zet de **Monitor** van de recorder uit, zodat je jezelf rechtstreeks via de interface hoort, en maar
één keer. Gebruik een bedrade koptelefoon: Bluetooth voegt zijn eigen vertraging toe.

#### Uitbreiden tot een volledig nummer {#expand-to-full-song}

Een opgenomen melodie is meestal maar een paar maten lang. **Uitwerken tot volledig nummer** laat YuE2 een heel nummer plannen
met jouw melodie erin: het plan staat in de toonsoort, maatsoort en het tempo van je melodie, elk refrein (of elk couplet,
als je dat kiest) bevat je melodie, en de rest van het nummer wordt eromheen geschreven. Daarna wordt het gerenderd
als cover van je opname.

- **Gezongen door:** een man of een vrouw. Je melodie schuift per heel octaaf naar waar die stem zingt,
  omdat het octaaf waarin de melodie is geschreven bepaalt wie hem zingt. Als de stijl geen zanger noemt,
  wordt de stem eraan toegevoegd.
- **Akkoorden:** een melodie alleen komt vaak zonder akkoorden terug van de transcriber. Yeufonic geeft hem dan
  akkoorden uit zijn eigen noten, zodat de planner een harmonie heeft om te volgen. Akkoorden die je in
  de partituur van de opname schrijft blijven behouden.
- **Je melodie** is altijd de partituur van de opname, ook als de editor een take toont die ervan is
  gemaakt.
- **Structuur van het nummer:** gebruikt als het tekstvak leeg is. Met woorden in het vak zijn hun secties
  de structuur, en ze hebben een **[Chorus]** (of een **[Verse]**) nodig om je melodie in te zetten.
- **Woorden:** een geneurie kan zonder tekst worden gepland. Een melodie gespeeld op een instrument heeft een tekst nodig om
  gezongen te worden, dus schrijf die eerst: **Songtekst schrijven** zet hem voor je op.

### MIDI-bestanden en covers {#midi-files-and-covers}

> [!NOTE]
> MIDI-bestanden zijn bedoeld om verschillende, vaak grillige takes van originele melodieën te maken.

Naast opgenomen audiobestanden kun je standaard MIDI-bestanden (`.mid`, `.midi`) rechtstreeks in de modus **Cover** slepen of uploaden.

Als je een MIDI-bestand uploadt:
- **Automatische partituurtranscriptie:** Yeufonic analyseert sporen en kanalen om de hoofdzangmelodie, de begeleiding en de akkoordprogressie te vinden, transcribeert ze naar ABC-notatie en laadt ze rechtstreeks in de pianorol. Synthleads of gesequencete zangmelodieën in lagere registers worden automatisch naar een natuurlijk zingbaar octaaf getransponeerd.
- **Ingebedde tekst:** tekst- of lyricsgebeurtenissen die in de MIDI-sequentie zijn ingebed worden eruit gehaald en op de lettergrepen van de melodie gezet.
- **Waar de maten vallen:** een MIDI-bestand heeft geen eigen maatstrepen, en sommige beginnen met het eerste woord op de tel *voor* de eerste tel. Yeufonic leest de drums en de bas om de echte maatstreep te vinden en zet, als het bestand met zo'n opmaat begint, de eerste woorden in een eigen korte maat zodat de akkoorden en maatmarkeringen vallen waar die van het nummer vallen. Een bestand zonder duidelijk patroon van drums en bas blijft zoals het is.
- **Geplakte tekst:** woorden die je plakt worden in één keer over de hele melodie verdeeld, één lettergreep per noot, en overgebleven noten blijven op de vorige lettergreep. Regels eindigen waar de melodie rust en beginnen waar een frase begint, dus een sectie die langer of korter is dan de koppen van de tekst verschuift de rest niet meer. Als de woorden langer zijn dan de melodie kan dragen, vallen de laatste regels weg.
- **Volledig beluisteren met SoundFonts:** de speler synthetiseert het MIDI-arrangement naar hifi-audio met **FluidSynth** en General MIDI-SoundFonts (`.sf2`). De uitvoer wordt op piek genormaliseerd zodat zachte meersporige MIDI-opnames aanwezig en helder klinken zonder vervorming.
- **SoundFonts kiezen:** in **Instellingen** kun je je favoriete actieve `.sf2`-SoundFontbank kiezen (zoals *Arachno SoundFont 1.0* of *JNS-GM 2.0*). Extra `.sf2`-bestanden in `data/models/soundfonts/sf2/` worden automatisch gevonden.
- **Bijwerken in de pianorol:** open de **Pianoroll** om noten na te kijken of aan te passen, te kiezen welk spoor de hoofdzangmelodie is, gaten in de begeleiding te harmoniseren met **Gaten vullen**, of een net geplakte tekst uit te lijnen met **Tekst koppelen**.

### Een cover maken van een nummer uit een corpus {#covering-a-song-from-a-corpus}

De analyse van een corpus heeft al gedaan wat een cover nodig heeft: de partituur, de woorden die in het nummer gehoord zijn, en
de afgescheiden stem. Dus onder je opnames biedt de lijst **Uit je corpora**, ingeklapt per
corpus, met de toonsoort en het tempo van elk nummer, en een filter voor een groot corpus. Kies een nummer en het wordt meteen een
van je opnames, met zijn partituur en tekst, en er wordt niets opnieuw uitgevoerd. De woorden worden
onder de secties van de partituur gezet, zoals **Songtekst eruit halen** ze zet, tenzij je ze in het corpus hebt nagekeken,
dan komen ze zoals je ze achterliet. Ze gaan in het tekstvak en vervangen woorden die van
een andere opname kwamen; woorden die je daar zelf typte of bewerkte worden alleen vervangen als je dat zegt. Het vak Stijl krijgt de
stijl waarmee het nummer in het corpus is aangeleerd, dezelfde als zijn chip onder een LoRA die erop getraind is.

Het bestand wordt gelinkt in plaats van gekopieerd als de schijf dat toelaat, dus het neemt geen extra ruimte in, en het blijft
als het corpus wordt verwijderd. Sommige nummers zijn gemarkeerd *score: melody only* of *score: first 4 min*: hun
volledige transcriptie mislukte tijdens de analyse, wat voor training genoeg is. Klik op **Transcriberen** voor de
volledige partituur met akkoorden.

**Met een LoRA.** Hier zijn de nummers van een corpus het nuttigst: een nummer en een LoRA uit hetzelfde
werk, of uit verschillend werk.
1. Open in de modus **Cover** de lijst met opnames en kies het nummer onder **Uit je corpora**. Zijn
   partituur legt de melodie en de akkoorden vast, en zijn tekst staat in het vak.
2. Kies een **Stijl-LoRA**. De LoRA van het corpus zelf laat zijn zanger het eigen nummer coveren, zo dicht mogelijk bij het
   origineel. De LoRA van een ander corpus covert het in die andere stijl en stem.
3. Stel de sterktes in zoals voor elke cover: de opname legt de melodie al vast, dus houd **Klank**
   rond **0.50**, en zet hem hoger voor meer van de stem en klank van de LoRA.
4. Het vak Stijl bevat al de eigen stijl van het nummer, en een LoRA kiezen zet zijn triggerwoord
   ervoor. Dat houdt het genre en de sfeer van het nummer; een andere chip, of de tags van het filter, sturen het
   ergens anders heen. Tempo en toonsoort komen uit de partituur, wat de stijl ook zegt.
5. Klik op **Cover maken**. **Variaties** rendert hem daarna in de andere interpretaties, en
   **Opnieuw zingen** geeft een andere stem op dezelfde partituur, zoals bij elke take.

### De tekst eruit halen {#extracting-the-lyrics}

**Songtekst eruit halen**, naast *Transcriberen*, schrijft op wat de opname zingt: het scheidt de
stem af, luistert ernaar en zet de regels onder de secties van de partituur. Je vraagt erom in plaats van dat het
bij elke transcriptie gebeurt, omdat het een paar minuten duurt waar een partituur transcriberen
seconden duurt. De stem wordt afgescheiden, en de woorden gehoord, op de GPU als de engine Demucs en Whisper heeft, en anders op de CPU
(Instellingen, **De GPU gebruiken voor stems en songteksten**), en de balk zegt in welke van de twee stappen hij is. Whisper op de GPU
en op de CPU schrijven niet altijd dezelfde woorden voor dezelfde stem, omdat geen van beide exact is: een lastige stem, zoals achtergrondzang
over een leadstem, kan een vijfde van zijn woorden de ene of de andere kant op verschillen. De afgescheiden stem wordt bewaard, dus dezelfde opname opnieuw uitlezen gaat
meteen naar het luisteren, wat het grootste deel van het wachten scheelt.

De woorden worden met de opname bewaard. Klik nog eens op **Songtekst eruit halen** en ze komen meteen terug in het
vak, en je wordt gevraagd of je ze opnieuw wilt uitlezen, wat de moeite waard is na het veranderen van de
methode in Instellingen. Een andere opname kiezen haalt op dezelfde manier haar woorden op, en een opname
zonder woorden wist die van de vorige. Woorden die je zelf typte of bewerkte blijven, tenzij je instemt ze te vervangen.

Verwacht eerder een goed concept dan een transcriptie. Gemeten tegen de echte tekst van twee nummers zat Whisper
bij **1,5% van de woorden** ernaast in het ene en bij **25%** in het andere, waar leadstem en achtergrondzang elkaar overlappen
in het laatste refrein. Het luistert naar de hele stem: vroeger sloeg het over wat zijn stemdetector
voor stilte hield, wat bij gezongen stemmen het grootste deel van het nummer was. Lees het concept en verbeter wat
het verkeerd hoorde, vooral waar stemmen overlappen.

**Een externe LLM laten luisteren.** Als een [externe LLM](#external-llm) je provider is, biedt Instellingen een keuze bij
*Songtekst uit een opname*. Zet die op **Externe LLM** en de afgescheiden stem wordt naar het model gestuurd om
de woorden te horen, terwijl Whisper blijft uitrekenen wanneer elke regel wordt gezongen. Op dezelfde twee nummers haalde Gemini
**1,5% en 23%**, dus ze liggen dicht bij elkaar; probeer beide op een nummer waar Whisper moeite mee heeft. Het heeft een
model nodig dat audio aanneemt, zoals Gemini. Als het antwoord van het model op een tekst lijkt, worden zijn woorden gebruikt,
ook waar ze flink van die van Whisper verschillen: een stem die diep in een mix zit is waar Whisper
het meest worstelt, en het model niet. Als het model de audio weigert, zich inhoudt (regels inkort,
of je naar een tekstensite verwijst, zoals een model kan doen met een nummer dat het herkent) of
bijna niets teruggeeft, krijg je in plaats daarvan de versie van Whisper. De melding aan het eind zegt welke
de woorden hoorde. De stem verlaat hiervoor je computer; Whisper houdt hem hier.

Voor een corpusnummer **worden beide versies bewaard**. Als ze allebei bestaan, toont het reviewpaneel van het nummer
**Woorden van** met elke versie en het aantal woorden, standaard die van het externe model. Kies
de andere en haar woorden gaan in het vak. De eerste keer dat een versie gekozen wordt, worden haar woorden opgezet, wat
haar secties markeert met het externe model; daarna houdt elke versie haar eigen woorden, bewerkingen en
vinkje **gecontroleerd**, dus wisselen tussen beide gaat direct en doet geen enkele aanroep naar het model. In de regels van Whisper wordt elk woord
dat het meer dan acht keer achter elkaar herhaalde, zoals een aangehouden “la” dat het honderden keren schreef, ingekort
tot acht.

---

## Instrumentaal {#instrumentals}

De derde modus schrijft een stuk zonder stem. In plaats van een tekst neemt hij een **structuur**:

| Structuur | Wat YuE2 krijgt | Wie beslist |
|---|---|---|
| YuE2 laten beslissen | `[instrumental]` | YuE2 kiest de secties en hun lengte |
| Delen | `[intro] [verse] [chorus] …` | jij kiest de secties, YuE2 hun lengte |
| Getimede delen | `[intro 0:00-0:15] …` | jij kiest beide |

Voeg secties toe met de chips **+**, herschik ze met de pijltjes, en geef elke sectie een lengte in de getimede modus.
**Naar YuE2 gestuurd:** toont precies wat het model krijgt. De structuur is een leidraad: YuE2 kan een
sectie hernoemen, een interlude toevoegen, of over de tijden heen gaan die je gaf, dus de lengtegrens is het harde plafond.

### Een instrumentaal uit een opname {#an-instrumental-from-a-recording}

**Vanuit een opname (optioneel)** bovenaan de editor neemt een van je opnames, zoals een cover. Zijn
transcriptie is de partituur, dus er is geen plan te schrijven, en de render speelt zijn melodie en
akkoorden met de instrumentale LoRA.

De secties komen ook uit de partituur: één per sectie van de partituur, met de namen die de LoRA kent. Een
*interlude* wordt een bridge. Een render koppelt elke sectie van de structuur aan een van de partituur,
daarom wijkt de bouwer voor ze. Om het nummer te herschikken, sleep je een sectie naar een andere plek of verplaats je hem met de pijltjes, voeg je er direct na een
**kopie** van toe, of haal je hem weg met de **✕**: elke wijziging herschrijft de partituur (het venster Partituur
toont het), en **De oorspronkelijke secties herstellen** zet hem terug tot er een andere partituur wordt geladen.
Terwijl de take in de editor speelt, licht de sectie op waarin hij is, en dubbelklikken op een sectie springt erheen. De tijden komen uit de maten en het tempo van de partituur, die de render nauw volgt aan het begin van een take en in een take die helemaal wordt gerenderd. Een render die flink voor zijn partituur eindigt heeft minder muziek gespeeld dan de partituur bevat, dus de lijst kan naarmate het nummer vordert van de audio afdrijven; een regel onder de lijst zegt dat en hoeveel. Een cover toont dezelfde lijst onder zijn tekst, en zijn tekst wordt op volgorde aan de secties gekoppeld, dus
pas hem aan: de lijst zegt wat hij nodig heeft na het toevoegen, weghalen of herschikken van secties. Hij toont ook het totaal tegen de
lengtegrens, en biedt aan de grens te verhogen als een langer nummer zou worden afgekapt. Klik op **Instrumentaal maken** om te renderen.

Een instrumentaal geschreven vanuit een structuur heeft ook een partituur, en na het plannen worden zijn secties op dezelfde manier getoond. De
structuurbouwer is de opdracht voor een plan dat nog niet geschreven is, dus hij wijkt voor de lijst. Herschik de secties en klik op
**Deze partituur renderen**: de sectietags van de render volgen de bewerkte partituur. Een take die al audio heeft wordt gerenderd als een
nieuwe take ernaast, wat je ook verandert, dus het origineel houdt het zijne. **Een nieuw plan schrijven** (onder de partituur) vraagt nog steeds
om een andere melodie uit de structuur waarmee de take werd geschreven.

**Een gezongen nummer werkt ook.** Zijn partituur heeft de gezongen melodie in de zangpartij, die
gezongen zou uitkomen, dus de melodie wordt aan een instrument gegeven: waar geen instrument speelt, gaan de gezongen noten
naar een instrument, en houdt de zangpartij alleen zijn akkoorden. De editor zegt dat onder de opname. Voor een nummer
is dit vaak de betere keuze: zonder de stem verliest de transcriber vaak het
verschil tussen couplet en refrein, en hoort het hele nummer als één akkoordlus. De LoRA
arrangeert het als instrumentaal, dus verwacht eigen partijen, zoals extra gitaar.

Kies **Geen opname: schrijf een partituurplan** in de lijst om weer een plan te schrijven.

### Als een instrumentaal zingt {#when-an-instrumental-sings}

Af en toe smokkelt het model een stem in een instrumentaal. Het is een fout van het model, geen instelling
die je verkeerd zette. Als het plan vóór het renderen noten in de zangstem zet, biedt een dialoog een nieuw
plan, een nieuwe seed, of toch renderen. Een klare take wordt niet gecontroleerd: luister ernaar.

### Een instrumentaal uit de partituur van een nummer {#an-instrumental-from-a-song-s-score}

**Een instrumentaal maken**, onder de partituur van een nummer of een cover op de pagina Partituur van de editor (naast **Deze partituur renderen**
bij een nummer), maakt van dezelfde
partituur een instrumentaal, in een nieuwe take: het origineel blijft zoals het was. De gezongen melodie gaat
naar een instrument, alleen de sectietags van de partituur worden naar het model gestuurd in plaats van de tekst, de
instrumentale LoRA wordt gebruikt, en de stijl verliest de tags die een stem beschrijven (“soft male vocal”).
Zo krijg je “deze melodie, zonder stem”. De Vocal-partij van de partituur van een nummer met de hand leegmaken is niet
genoeg: de render van een nummer zingt nog steeds de woorden die hij krijgt.

---

## Stemmen {#voices}

De chips **Zang** bepalen het geslacht en het karakter van de zanger door in de stijl te schrijven, voor het hele nummer.

Voor een duet, of de ene zanger voor de coupletten en een andere voor het refrein, zet je stemaanwijzingen in de tekst en vink je
**Stemmen volgen de aanwijzingen** aan: zie [De tekst](#the-words) onder “Een nummer schrijven vanuit een prompt”. Het werkt ook voor de tekst
van een cover.

## Corpora en een LoRA trainen {#corpora-and-training-a-lora}

Een **corpus** is een map met nummers, voorbereid als trainingsset voor een stijl-LoRA: meestal één
artiest, één genre of een paar vergelijkbare artiesten.
Open **Corpora** vanuit het menu. Het staat standaard aan; `TRAINING_ENABLED=0` voor de app, of een
engine gebouwd met `WITH_TRAINER=0`, haalt het weg.

Trainen is het zwaarste wat de app doet: met het aanbevolen model van volle kwaliteit (BF16) zijn
een grafische kaart van 16 GB en 32 GB systeem-RAM (onder WSL2, `memory=32GB` in `.wslconfig`) het praktische minimum.
Een kaart van 8 GB kan volstaan om te trainen met het model voor weinig geheugen (INT8).

1. **Nieuw corpus.** Geef het een naam en een **triggerwoord**, zeg of de stem mannelijk of vrouwelijk is
   (**geen** voor nummers zonder stem: zie hieronder), beschrijf de klank die alle nummers delen, en open de map waarin ze staan. Bevestig dat
   je het recht hebt erop te trainen, en klik op **De map scannen**. De map wordt alleen gelezen.
   **Een corpus zonder stem.** Kies **geen** bij **Stem** als de nummers instrumentaal zijn, zoals
   dance en elektronische muziek. De app scheidt dan geen stem af en luistert niet naar woorden, dus niets
   verzint teksten over synthesizers. De tekst van elk nummer zijn de sectietags in zijn partituur (of
   `[instrumental]` als er geen zijn), de beschrijving laat de zangpartij weg, en er is geen review van
   de tekst: het vak **Delen** is te bewerken, en de bewerking wordt bewaard. De klank van elk nummer wordt beschreven
   door het lokale model als dat geïnstalleerd is, omdat het externe alleen een titel zou hebben om op te bouwen.
   Een LoRA die zo getraind is kan noten in de Vocal-partij van een plan schrijven, waardoor een render gaat zingen of neuriën;
   de waarschuwing “kan zingen” van een plan laat dat zien. De Stem van een al geanalyseerd corpus veranderen past zijn
   tekst navenant aan.
2. **Kies de nummers.** Vink uit wat je wilt weglaten. Als een nummer wordt voorbereid, bewaart de app een eigen kopie van de volledige opname in de interne corpusopslag, dus een corpus blijft intact ook als de bronmap later wordt leeggemaakt of verplaatst. Een opname van meer dan 25 minuten wordt weggelaten, omdat het waarschijnlijk een heel album of een concert in één bestand is. Als er een `.cue`-blad naast staat, knipt **Splitsen in tracks** hem in zijn nummers, die zijn plaats in het corpus innemen. De tracks gaan naar de eigen map van de app; die van jou verandert niet. (Nummers langer dan de GPU-grens van de trainer, zoals tracks van 15 minuten, worden bij het exporteren veilig ingekort en uitgefadet op een muzikale sectiegrens.)
3. **Analyseren.** De stem van elk nummer wordt afgescheiden, de toonsoort, het tempo en de secties worden gevonden, en de tekst wordt opgezet, gemarkeerd per sectie. Met een externe LLM ingesteld worden de secties gemarkeerd uit de gehoorde woorden: refreinen omdat hun woorden terugkomen, nieuwe secties aan de pauzes. Alleen de regels en hun tijden worden verstuurd, en de woorden en hun volgorde worden nooit veranderd. Zonder externe LLM, of als zijn antwoord niet alle regels bevat, komen de tags uit de muzikale analyse. **Opnieuw opstellen**, naast Bewaren in de review van een nummer, markeert de secties opnieuw op dezelfde manier zonder het nummer opnieuw te beluisteren, voor een nummer dat eerder is opgezet, en vervangt wat er in het vak staat. Een regel onder de knoppen zegt wat er loopt, en de lopende analyse verschijnt in de takenkaart en de wachtrij op het hoofdscherm. **Stop** stopt hem. Afgeronde stappen blijven bewaard, dus **Analyseren** gaat verder waar hij was.

   **Opnieuw analyseren.** Als alle nummers geanalyseerd zijn, toont de knop **Geanalyseerd ✓**. Erop klikken vraagt of je de stijlsuggesties van alle nummers opnieuw wilt analyseren met de nieuwste LLM-prompts en -instellingen (handig na het hernoemen van een corpus of het wisselen van provider). Shift+klik op **Geanalyseerd ✓** biedt een volledige nieuwe analyse vanaf nul (scheiding, toonsoort, tempo, transcriptie en stijlen opnieuw). Elk nummer kan ook een nieuwe stijl krijgen met **Opnieuw analyseren** in zijn review.
4. **Nakijken** Open een nummer om de tekst na te kijken en **gecontroleerd** aan te vinken, en om de klank te beschrijven
   waar die van de rest verschilt. De stijlbeschrijving toont wat de trainer zal lezen.
5. **Trainingsset exporteren.** Schrijft de audio, tekst en beschrijving van elk nummer. Een regel onder de
   knoppen toont hoe ver hij is. De trainer neemt maar een deel van elk nummer, dat de app berekent
   uit het vrije geheugen van je grafische kaart (zo'n 5½ minuut op een kaart van 16 GB; het venster Logs
   zegt wat hij koos). Een langer nummer wordt afgeknipt aan het eind van zijn laatste sectie binnen die marge, uitgefadet,
   en houdt alleen de woorden die nog gezongen worden. Zijn rij zegt “first 3:12 trained”. Als het trainen
   te weinig geheugen heeft, zet de omgevingsvariabele `TRAIN_MAX_MINUTES` op een lager getal, zoals
   3.5: zie de README.
6. **Een LoRA trainen.** Dit duurt lang, en de GPU is niet beschikbaar voor de app tot het
   klaar is. De voortgang staat onder de knoppen en op het hoofdscherm, waar je het kunt stoppen,
   en de corpusbadge bovenaan de pagina pulseert tijdens het trainen. Opnieuw trainen houdt
   de LoRA van de vorige run onder een gedateerde naam, onder **Vorige runs**, of verwijdert hem, zoals
   je kiest.
   Trainen met het aanbevolen model van volle kwaliteit (BF16) heeft minstens zo'n 12,5 GB GPU-geheugen nodig
   (bij een knip van 3½ minuut; een langere knip heeft meer nodig), vooral tijdens het voorbereiden van de nummers, dus een kaart van 16 GB
   is het praktische minimum, samen met 32 GB systeem-RAM (ComfyUI houdt de volledige gewichten van YuE2
   en de datasetcaches in het hostgeheugen; onder WSL2, zet `memory=32GB` in `.wslconfig`). Een kaart van 8 GB kan
   trainen met het model voor weinig geheugen (INT8). Kaarten die niet kunnen trainen kunnen nog steeds LoRA's gebruiken die
   elders getraind zijn (**Een LoRA installeren**). Het venster Trainen waarschuwt als er minder GPU- of systeemgeheugen vrij is,
   dus sluit eerst al het andere dat de GPU gebruikt.

### Een run die vroeg eindigt {#a-run-that-ends-early}

Een run kan eindigen voor zijn laatste stap: **Stop**, een crash, of de GPU die zonder geheugen raakt. De regel
onder de knoppen zegt dan wanneer en waarom, en na welke stap. Onderweg bewaart de trainer elke 50 stappen een
checkpoint, en houdt hij een kopie van de beste tot dan toe volgens zijn plannerverlies, dus het meeste
werk is meestal nog aanwezig. **Afronden met wat er is opgeslagen** doet wat een afgeronde run doet, vanuit
die bestanden: de beste kopie, of anders het laatste checkpoint, wordt de LoRA met de
naam van het corpus, met zijn triggerwoord, en de checkpoints klappen eronder in in de lijst met stijl-LoRA's. Het duurt
seconden en kost geen GPU-tijd. De laatste stappen van een run veranderen de LoRA het minst, dus een die zo
is afgerond ligt meestal dicht bij een volledige run; **Checkpoints** rendert een nummer één keer bij elke stap als je
op het gehoor wilt vergelijken. Om de hele run opnieuw te trainen, klik op **Een LoRA trainen**.

### Alles uitvoeren {#run-all}

**Alles uitvoeren**, naast de drie, doet Analyseren, Exporteren en Trainen na elkaar, voor een corpus waar je
liever niet op wacht: een groot corpus analyseren duurt uren. Het vraagt eerst wat er met een
vorige LoRA moet gebeuren, en gaat dan door met de pagina dicht. Het analyseert alleen wat dat nog nodig heeft, en een
nummer waarvan de analyse mislukt wordt uit de trainingsset gelaten en onder de knoppen genoemd. Teksten
die niemand heeft nagekeken worden gebruikt zoals ze zijn opgezet. **Stop** stopt het waar het is, en houdt wat klaar is;
gestopt tijdens het exporteren maakt het eerst de trainingsset af. Het wacht op alles wat de engine al
gebruikt voordat het traint. De app herstarten stopt het, en **Alles uitvoeren** opnieuw gaat verder.

### Als het GPU-geheugen op is {#running-out-of-gpu-memory}

Een taak die zonder GPU-geheugen raakt zegt dat, met wat je kunt proberen: sluit andere programma's die de GPU gebruiken,
verlaag de lengtegrens, of laat voor het trainen de langste nummers weg. Als de engine crasht en
herstart, gaat de taak die liep verloren, en dat wordt ook gezegd.

### De getrainde LoRA {#the-trained-lora}

Als het trainen klaar is, verschijnt de LoRA in de lijst **Stijl-LoRA** met zijn triggerwoord. Hem kiezen
toont een chip voor elk nummer waarvan hij leerde, onder het vak Stijl, en op een chip klikken zet de stijl van dat nummer in
het vak.
Vanaf een dozijn nummers maken een filtervak en een rij met de tags die in het corpus terugkomen (zijn genres,
sferen en instrumenten) de keuze kleiner; klik op twee tags om nummers met beide te vinden. De lijst toont zijn
eerste dozijn tot **Alles tonen**. Zie **Planner en Klank in balans** hieronder voor de beginsterktes. Om hem te delen, klik op **LoRA downloaden** op de corpuspagina, of op **Downloaden** onder
de kiezer; zie **Een LoRA delen** hieronder.

Om een LoRA toe te voegen die iemand deelde, klik op **LoRA importeren** naast **Nieuw corpus** en kies zijn zip. Om een
LoRA te gebruiken die elders uit de geëxporteerde set is getraind, klik op **Een LoRA installeren** en kies het
bestand. Hij wordt aan de lijst met stijl-LoRA's toegevoegd met het triggerwoord van dit corpus.

**Een corpus verwijderen** haalt de kopieën van zijn nummers weg die de app maakte, de afgescheiden stemmen, de teksten en
de partituren. De map die je opgaf, en elke LoRA die ervan is gemaakt, blijven onaangeroerd.

---

## Auteursrecht en toestemming {#copyright-and-consent}

Waarop je traint, en wat je met het resultaat doet, is jouw verantwoordelijkheid onder de wet van waar je
woont. De app vraagt je het te verklaren en controleert het niet: een corpus aanmaken vraagt je te bevestigen
dat je het recht hebt op die opnames te trainen.

Twee dingen om te weten:

- De gewichten van YuE2 vallen onder **CC BY-NC 4.0** — niet-commercieel gebruik, wat je er ook op traint.
- Privé op een corpus trainen en de LoRA of wat hij maakt publiceren zijn verschillende handelingen. Het tweede
  is wat meestal toestemming vraagt: van wie de rechten op de opnames heeft, en voor
  een herkenbare stem, van de zanger.

LoRA's die je niet zelf trainde hebben hun eigen licenties: lees ze op de pagina waar elke LoRA vandaan komt
(zie **Waar je stijl-LoRA's vindt** onder Stijl-LoRA's).

## Stijl-LoRA's {#style-loras}

Een LoRA is een klein bestand dat het model naar een klank laat overhellen. Zet er een in `models/loras/` en klik op
**Opnieuw inlezen** onder de kiezer, of gebruik **Installeren**, en hij verschijnt in de lijst **Stijl-LoRA**.

Een stijl-LoRA kan twee helften hebben, en de kiezer laat zien welke een bestand heeft:

- **Planner** vormt wat er gespeeld wordt — het partituurplan (vorm, harmonie, frasering), en daarna de muziek
  die de render uit die partituur schrijft. Het werkt in beide stappen.
- **Klank** vormt de audio — klankkleur en productie.

Een sterkte die het bestand niet kan gebruiken wordt gedimd, en een bestand dat deze engine helemaal niet kan laden wordt
als zodanig gemarkeerd in plaats van stil te falen in een render.

### Waar je stijl-LoRA's vindt {#where-to-find-style-loras}

Het snelst is bij de installatie: vink **Stijl-LoRA's** aan op de componentenpagina van het installatieprogramma (of, met Docker, voer
`sh scripts/fetch-models.sh --loras` uit). Dat downloadt 39 stijl-LoRA's van hun makers, 3,8 GB in totaal, elk met een
beschrijving die het triggerwoord en de voorgestelde sterktes geeft: de sets hieronder, twee van atomtanstudio (dream pop
en oldschool hiphop), en zestien conceptschuiven van ntc-ai, die alleen de partituur vormen (Klank doet niets,
en ze hebben geen triggerwoord nodig). Ze zijn, ongewijzigd, verzameld in
[pshields/yue2-style-loras](https://huggingface.co/pshields/yue2-style-loras), waarvan de README elke maker vermeldt
en naar de bronpagina linkt. Een LoRA die al met dezelfde naam in je map staat blijft zoals hij is.

Er zijn er meer op Hugging Face. Dit zijn de sets die daar verzameld zijn, elk op de pagina van de maker:

- [Militant reggae](https://huggingface.co/becausereasons/yue2-mltnt-militant-reggae)
- [Chanson française](https://huggingface.co/becausereasons/yue2-chnsn-chanson-francaise)
- [Canzone italiana](https://huggingface.co/becausereasons/yue2-cnzn-canzone-italiana)
- [Bulgarian voices](https://huggingface.co/becausereasons/yue2-blgr-bulgarian-voices)
- [Qawwali, sufi and tabla](https://huggingface.co/becausereasons/yue2-qwwl-qawwali-sufi-tabla)
- [J-pop](https://huggingface.co/storagejuju/yue2-jpop-t4-lora), één LoRA met alleen de Klank-helft

Om er een toe te voegen, download je zijn `.safetensors`-bestand van het tabblad **Files** van de repository, zet je het in `models/loras/`
en klik je op **Opnieuw inlezen**, of klik je op **Installeren** en kies je het bestand. De pagina van de repository geeft het
triggerwoord en de voorgestelde sterktes van elke LoRA: schrijf ze in een `.txt` naast het bestand (zie **Beschrijvingen** hieronder) en
de kiezer toont ze, en zet het triggerwoord voor je aan het begin van de Stijl. Een LoRA van elders
kan zijn opgeslagen in een formaat dat deze engine niet kan laden: de kiezer markeert hem als zodanig, en hij kan geen kwaad.

Elke LoRA heeft de licentie van zijn maker, die deze sets opgeven als CC BY-NC 4.0: persoonlijk, niet-
commercieel gebruik, net als de gewichten van YuE2 zelf. Lees de licentie op de pagina van een LoRA voordat je hem gebruikt, of deelt wat
hij maakt.

### Planner en Klank in balans {#balancing-planner-and-sound}

- **Samenhangende corpora:** een LoRA getraind op één album of een eenduidige akoestische klank (bijv. folkrock uit de jaren zestig) kan hogere sterktes aan, meestal rond **Planner ~0.85 / Klank ~0.80**.
- **Gevarieerde corpora:** als het trainingscorpus meerdere genres, productiestijlen of tijdperken beslaat (bijv. akoestische folk, rock en synthpop), kunnen hoge Klank-gewichten akoestische botsingen geven. Tot ongeveer **Planner 0.70 / Klank 0.70** blijft de audio schoon terwijl de melodische frasering en het stemkarakter van de artiest behouden blijven.
- **Covers:** je opname legt de melodie vast, dus de LoRA heeft minder te vormen en de Klank-helft wordt harder aangezet. Houd Klank rond **0.50**.
- **Variatie van het plan:** met een LoRA getraind uit een corpus geven **Rustig** of **Normaal** het herkenbaarste resultaat. **Rustig** kan gaan rondzingen met een stijl-LoRA en een korte stijl, en het plan loopt dan
  minuten door met lange herhaalde intro's, of zonder iets gezongen. Beschrijf de stijl uitgebreider (genre, instrumenten en gevoel), of gebruik **Normaal**. Zo'n plan, of een dat veel langer is dan een nummer, wordt één keer opnieuw geschreven
  met een nieuwe seed, en de take mislukt met een tip als de tweede net zo uitvalt.
- **Een goede take vinden:** het karakter van de LoRA hangt evenveel af van de worp als van de sterktes.
  Tussen ongeveer 0.3 en 0.6 verandert **Klank** de stem weinig, dus hem hoger zetten hoeft niet.
  **Planner** verandert de uitvoering zelf, niet alleen de stem, dus een waarde die bij het ene nummer past
  kan bij een ander de zwakste zijn. Behandel hem als de seed: probeer er een paar (bijvoorbeeld 0.6, 0.8 en 1.0) en een paar
  seeds met **Opnieuw zingen**, en houd de take die je bevalt.
- **Sterktes bewaren:** als je het juiste paar voor een LoRA hebt gevonden, klik op **Sterktes bewaren** onder de
  kiezer. Die LoRA kiezen begint dan op die sterktes, en ze reizen met hem mee als je hem deelt.

### Triggerwoorden {#trigger-words}

De meeste stijl-LoRA's worden getraind op beschrijvingen die **beginnen** met een triggerwoord, en doen weinig
zonder. De app regelt het: een LoRA kiezen zet zijn trigger aan het begin van de Stijl,
naar een andere wisselen vervangt hem, Geen kiezen haalt hem weg, en een render zet hem terug als hij
was gewist. Je ziet het woord in het vak Stijl verschijnen — je kunt het bewerken of verplaatsen.

### Beschrijvingen {#descriptions}

De lijst is gegroepeerd per set. Klik op een kop om hem open of dicht te klappen; de kiezer onthoudt welke
je open liet, en de groep met je huidige keuze gaat er altijd mee open.

Beweeg de muis over een item om te lezen wat het is, in de woorden van de maker, en zijn voorgestelde sterktes. Die
beschrijvingen komen uit een tekstbestand naast de LoRA:

```
CHNSN Rive Gauche
Trigger: chnsn
Step 200, the decoder-loss minimum. The more supple of the two: acoustic
narrative, yé-yé, female leads, waltz meters.
```

De eerste regel geeft de naam, een regel `Trigger:` wordt het triggerwoord, en de rest is de
beschrijving. Een eigen LoRA krijgt er een als je er een `.txt` naast schrijft. `families.txt` in dezelfde
map geeft de groepen hun koppen, één `prefix = label` per regel.

### LoRA's getraind uit een corpus {#loras-trained-from-a-corpus}

Een LoRA getraind uit een van je corpora is een gewone stijl-LoRA: hij verschijnt in deze lijst met de
andere, met zijn triggerwoord ernaast, en dezelfde twee sterktes gelden.

### De checkpoints uitproberen {#trying-the-checkpoints}

Een trainingsrun bewaart elke 50 stappen een checkpoint, en houdt ze onder zijn LoRA in de kiezer:
**▸ 9 stappen** naast de naam van de LoRA klapt ze open (Instellingen kan ze in plaats daarvan verwijderen, om
ruimte te sparen). Een checkpoint waarvan de LoRA is verwijderd blijft onder **Trainingscheckpoints**. Om
er een paar weg te halen, klik op **Bewerken** bij het corpus: **Trainingscheckpoints** daar toont die van elke run, deze
en eerdere, met hun grootte. Vink aan wat weg moet en klik op **Verwijderen**. De afgeronde
LoRA wordt niet getoond; die heeft zijn eigen **LoRA verwijderen**. Elk checkpoint is de LoRA zoals hij was op
dat punt in de training. Ze klinken ongeveer even goed, maar elk weegt op zijn eigen manier
wat het leerde, dus elk heeft zijn eigen smaak zonder de stijl en de kenmerkende klank te verliezen waarop de LoRA
getraind is.

Om ze naast elkaar te horen, kies je de LoRA, stel je de editor in zoals voor één take, en klik je op
**Checkpoints** naast **LoRA verwijderen**. Het is gedimd voor een LoRA zonder checkpoints. Vink de
stappen aan die je wilt, stel als je wilt een lengtegrens voor deze takes in, en klik op **Renderen**. De eigen
actie van de editor draait één keer op elk checkpoint, allemaal met één seed, en elke take krijgt de naam van zijn stap:
*Night drive · step 250*, *Night drive · full*. Ze worden bewaard in de take die in de editor open is,
of, voor een nieuw nummer, in de laatste ervan (zie **Takes in een take**, onder De bibliotheek). De editor sluit, dus je komt terug in de bibliotheek
waar de takes worden gemaakt. Een nummer of instrumentaal schrijft zijn plan en gaat meteen door naar
renderen.

Bij een nummer of instrumentaal schrijft de LoRA ook de melodie, naast het vormen van de klank, dus dezelfde
seed geeft niet hetzelfde nummer: elk checkpoint schrijft zijn eigen melodie en structuur. De seed
kiest uit wat het model waarschijnlijk acht, en elk checkpoint denkt vanaf de eerste noot een beetje
anders, dus de plannen lopen binnen een paar maten uiteen. Wat overblijft is de klank. Om alleen de
klank te vergelijken, laad je een plan met **Partituur** en klik je op **Deze partituur renderen** met elk checkpoint om de beurt.

Nieuwe bestanden verschijnen als de engine `models/loras/` opnieuw heeft bekeken, wat hij doet als de
opties opnieuw worden geladen.

### Een LoRA delen {#sharing-a-lora}

Kies een LoRA en klik op **Downloaden** onder de kiezer: je krijgt een zip met de LoRA en zijn notitie.
Voor een LoRA getraind uit een corpus bevat de notitie zijn aangeleerde stijlen, dus de chips gaan mee.

Om er een toe te voegen die je is gestuurd, klik op **Installeren** en kies zijn zip, of een los
`.safetensors`-bestand. Hij gaat naar `models/loras` onder de kop **Geïnstalleerd**, met zijn naam, triggerwoord en
chips. **LoRA verwijderen** haalt de gekozen LoRA weg, met zijn notitie en zijn groepsregel; **Opnieuw inlezen** leest de map opnieuw
nadat je met de hand een bestand hebt toegevoegd.

---

## Stems {#stems}

Klik op **Stems** bij een take. Kies een model, vink de partijen aan die je wilt — zang, drums, bas, overig,
en gitaar en piano bij sommige modellen — en start.

Het scheiden gebeurt op de **GPU** als de engine Demucs heeft, als taak in de wachtrij van de engine: het wacht op een
lopende render, gaat dan snel, en een render die erachter in de wachtrij staat wacht op zijn beurt. Een engine gebouwd van voor
dit, een LoRA die traint (die de GPU bezet), **De GPU gebruiken voor stems en songteksten** op Nee in Instellingen, of `STEMS_ON_GPU=0` houdt het op de **CPU**, die langzamer is
en een render nooit ophoudt. *Verfijnd* draait vier modellen achter elkaar voor een betere scheiding en duurt ongeveer vier keer
zo lang.

Voor een begeleidingstrack kies je **Zang en instrumenten**. Het splitst het nummer in tweeën: de zang, en
de **instrumenten**, al het andere als één stem. Vink **zang** uit om alleen de instrumenten te houden. Het is
dezelfde scheiding als de vier stems, weer bij elkaar opgeteld, dus het duurt even lang en klinkt even schoon.
De *verfijnde* versie laat de minste zang achter.

Stems gaan naar `data/stems/<title>-<id>/`, spelen af vanaf de chips op de kaart, en worden los of als
zip gedownload. Ze blijven tot je ze verwijdert.

---

## Stoppen, verwijderen en opnieuw beginnen {#stopping-deleting-and-starting-again}

Waar de engine mee bezig is staat in de bovenbalk, naast de naam: een pil met de taak, de tijd, een lijn
langs de onderkant die laat zien hoe ver hij is, en hoeveel taken erachter wachten. Verder verandert er niets op de pagina als een
taak begint of eindigt. Klik erop voor de takenkaart: de fase, **stop**, en **Hierna**, de wachtende taken, elk met
**annuleren**.

Een take in de wachtrij of in uitvoering toont **Annuleren** op zijn kaart, en **stop** op de takenkaart stopt waar
de engine mee bezig is. De titel van een take op de takenkaart, in zijn lijst **Hierna**, of in de speler
onderaan de pagina brengt je naar de take: naar zijn ruimte, waarbij elke zoekopdracht of filter die hem verbergt wordt gewist. Een take verwijderen stopt zijn taak en haalt zijn stems weg. **Verwijderen** naast een
opname haalt het bestand en zijn stems weg; covers die ervan gemaakt zijn houden hun audio en partituur, maar kunnen niet
opnieuw worden gerenderd.

**+ Nummer**, **+ Cover** en **+ Instrumentaal** in het takepaneel, of **Nieuw nummer** naast de
titel van de editor, beginnen opnieuw vanaf de getoonde take. Ze wissen de titel, tekst en partituur,
en beginnen bij de standaarden: een lege stijl (met het triggerwoord van een gekozen LoRA), de gewone
lengtegrens, Harmonie Gevarieerd, gewone planvariatie, interpretatie Breed, productieafwerking aan,
normaliseren uit, en een nieuwe, niet vastgezette seed. Een gekozen LoRA en een gekozen opname blijven gekozen.
De getoonde take laat de editor los, zodat Renderen er niet per ongeluk op kan werken.

Woorden die je had getypt maar niet gebruikte worden niet weggegooid: een balk biedt aan ze terug te zetten.

## De bibliotheek {#the-library}

### Ruimtes {#spaces}

Takes wonen in **ruimtes**: een ruimte per nummer, per album, of voor schetsen. De naam van de ruimte boven de takes
is degene die getoond wordt, en alles wat je doet komt daar terecht. Klik erop voor de lijst met ruimtes: typ om er een op
naam te vinden, of kies hem met de pijltjes en Enter. De vijf die je het laatst gebruikte komen eerst, daarna alle ruimtes, elk met
hoeveel takes erin zitten. **Nieuwe ruimte**, **Deze ruimte hernoemen**, **Take importeren…** en **Deze ruimte verwijderen** staan
onderaan de lijst. Een ruimte verwijderen verwijdert nooit takes —
ze gaan naar Default. Opnames worden door alle ruimtes gedeeld, dus één opname kan in
meerdere worden gecoverd.

De mapknop op een kaart verplaatst die take naar een andere ruimte, met de takes die erin zitten.

### Takes in een take {#takes-inside-a-take}

**Variaties**, **Meer proberen** en **Checkpoints** maken elk meerdere takes van één nummer. Ze worden bewaard
**in** de take waaruit ze kwamen, zodat de ruimte je nummers toont en niet elke render van elk nummer.
Op Checkpoints wordt in de editor geklikt: met een take daar open gaan zijn takes in die take; voor
een nieuw nummer, dat nog geen take heeft, bevat de take van het laatst aangevinkte checkpoint (de afgeronde LoRA, als
die erbij zit) de andere.

- **De knop Binnenin** verschijnt tussen de knopjes bovenaan een kaart als zijn take
  takes bevat, klaar of nog bezig, en is **oranje verlicht**. Beweeg de muis erover om te lezen hoeveel er
  klaar zijn en hoeveel nog komen. De kaart zelf is duidelijk lichter dan de andere (in het
  lichte thema een warme tint), zodat een take met takes erin opvalt in een lijst. (De knop van het masteringrack ernaast licht op
  dezelfde manier groen op als de take gemasterd is.)
- **Klik erop** en er gaat een paneel open onder de kaart met de takes die hij bevat, elk op een eigen kaart. Een
  take verschijnt daar als hij klaar is; zolang hij gemaakt wordt, wordt alleen de take getoond waar hij bij hoort.
  Klik nog eens op de knop, of op **Sluiten**, om het te sluiten.
- **Een take in een take is een take als elke andere.** Speel hem af, geef hem een ster, bewaar hem, splits hem in
  stems, hernoem hem, en dubbelklik om zijn nummer en partituur te openen.
- **Eén niveau.** Een take in een take bevat er geen, dus zijn kaart heeft geen Variaties of Meer
  proberen, en **Checkpoints** in de editor is gedimd zolang hij daar de geopende take is. **Eruit halen** (het pijltje dat uit een doos komt) maakt er een eigen take van in de lijst van de ruimte, en dan kan het wel.
- **De gereedschappen van de lijst volgen het paneel.** Zolang er een open is, werken **Alles selecteren**, **Met ster**, de
  soortknoppen, **Vergelijken**, **Verwijderen** en vorige en volgende van de speler op de takes van het
  paneel. De take waarvan het paneel open is blijft op de pagina, wat de filters ook zeggen.
- **Wat binnen speelt, zie je buiten.** Als je het paneel sluit terwijl een van zijn takes speelt,
  gloeit de afspeelknop van de bevattende take goud, zodat je ziet waar het
  geluid vandaan komt. Groen betekent nog steeds dat die take zelf speelt.
- **Zoeken vindt ze** zoals elke andere take, waar ze ook zitten. Tijdens een zoekopdracht wordt wat
  gevonden wordt als eenvoudige kaarten getoond, en een take die in een andere take zit zegt in welke.
- **Een take verwijderen verwijdert de takes die hij bevat.** De waarschuwing zegt hoeveel. Haal eerst de takes eruit die je wilt
  houden.

Takes die gemaakt zijn voordat dit bestond blijven waar ze zijn, naast elkaar in de lijst.

### Kaarten {#cards}

Elke kaart noemt de instellingen die hem vormden — Harmonie, Interpretatie, Variatie van het plan, de LoRA en
zijn sterktes, de seed, de engine die hem renderde en hoe oud hij is — zodat een kaart leest als het recept waarmee hij werd gemaakt.

**Opslaan** vraagt in welk formaat je de take wilt downloaden, FLAC, WAV of MP3. Het begint bij wat je de vorige
keer bewaarde, en de eerste keer met niets gekozen. Een take met een afbeelding kan ook als **Video** worden bewaard: een MP4 van
het nummer met de afbeelding van zijn kaart (H.264-video, AAC-audio op 192 kbps). Berichtenapps zoals
WhatsApp versturen en spelen dat af als video, waar een audiobestand als document gaat. Met het masteringrack aan heeft de
video de gemasterde klank, zoals de andere formaten. **Take**, ernaast, bewaart ook het recept van de take: een klein bestand
(`<title>.yeufonic.json`) met zijn tekst, stijl en partituur, zijn seeds en instellingen, zijn LoRA's op naam en
de instellingen van het masteringrack, maar niet zijn audio. Met ook een formaat gekozen gaan beide in een zip; klik nog eens op het
gekozen formaat om alleen het recept te bewaren. Het bestand bevat niets van je installatie (geen paden, id's of sleutels),
dus het kan bewaard worden, of gedeeld met een andere Yeufonic-gebruiker.

**Take importeren…**, in de lijst met ruimtes, maakt van zo'n bestand een nieuwe take in de getoonde ruimte; het bestand
op de bibliotheek slepen doet hetzelfde. De take bevat het plan, klaar om te renderen, zodat je het eerst kunt nakijken of veranderen.
Beide engines kunnen hem renderen: dezelfde partituur en seed op dezelfde engine geven een heel vergelijkbare take, op de andere
engine een andere. Een LoRA die hij noemt en die hier niet geïnstalleerd is wordt bij het importeren gemeld, zodat je
hem kunt installeren of een andere kunt kiezen voor het renderen. De opname van een cover zit niet in het bestand, dus een gedeelde cover komt binnen
als een nummer met de partituur en tekst van de cover, zonder de instellingen die bij zijn opname hoorden (het
vastgezette tempo, Harmonie, stemaanwijzingen en de lengtegrens): een nieuw plan ervan begint als een nummer vanuit een prompt.

**Takes zoeken** vindt de takes waarin alle woorden die je typt ergens voorkomen in de titel, stijl, tekst of
LoRA-naam, ongeacht hoofdletters. Het zoekt in de getoonde ruimte; **Alle ruimtes**, ernaast zodra je typt,
zoekt in elke ruimte, en een kaart uit een andere ruimte zegt uit welke. × of Escape wist het. Het
vak is leeg elke keer dat de pagina opent, en biedt je laatste zoekopdrachten die iets vonden:
klik op een, of kies hem met de pijltjes en Enter.

**Nummer**, **Cover** en **Instrumentaal** tonen takes van die soorten: zet er een of meer aan, of geen voor alle soorten.
**Met ster** toont alleen takes met een ster; klik nog eens om alles te tonen. De pictogrammen ernaast bepalen hoe
de takes worden opgemaakt, de gebruikte groen verlicht: bredere **ruime** kaarten met meer van de prompt of smallere **compacte**,
de **volle breedte** van het venster of een gecentreerde kolom, en elke take **ingeklapt** tot zijn titelregel. Beweeg de muis over
een pictogram om te lezen wat een klik doet.

Vink takes aan en de rij biedt wat je ermee kunt doen, in plaats van de soorten en de opmaak: hoeveel er
gekozen zijn, **Vergelijken**, **Verwijderen** en **Klaar**, dat ze weer uitvinkt. **Alles selecteren**, aan het eind van de rij, vinkt
elke getoonde take aan. Een titel blijft altijd op één regel, eindigend op … als hij lang is. Beweeg de muis over de titel, instellingen of stijl van een kaart om hem helemaal te lezen.

### Een afbeelding voor elke take {#a-picture-for-each-take}

Elke nieuwe take krijgt een afbeelding van het nummer, vaag te zien achter zijn kaart, bovenaan het takepaneel als je hem kiest, en achter de editor als de take daar
open is. Getekend op deze pc wacht hij tot er geen nummer wordt gemaakt, dus hij houdt nooit een plan of render op, en
verschijnt kort nadat het nummer klaar is; getekend door een externe LLM wordt hij gemaakt terwijl de take rendert.
Hij wordt in twee stappen gemaakt: de titel, stijl en eerste woorden van de take worden een **beschrijving** van
een afbeelding, dan **tekent** een afbeeldingsmodel die op wit, en het wit wordt weggehaald, waardoor de afbeelding
op een transparante achtergrond overblijft. Een take die in een andere is gemaakt (Meer proberen, Variaties, Checkpoints) toont de
afbeelding van de take waarin hij zit in plaats van een eigen.

Een afbeeldingsmodel tekent geen echte band of persoon, dus de beschrijving laat namen weg; en de eigen
letters van de afbeelding worden zacht gehouden, zodat ze niet concurreren met die van de kaart.

#### Twee manieren van tekenen: FLUX.2 klein op deze pc, of een externe LLM {#two-ways-to-draw-flux-2-klein-on-this-pc-or-an-external-llm}

Afbeeldingen hebben iets nodig dat kan tekenen. Er zijn er twee, en je kunt er een, beide of geen hebben.

| | FLUX.2 klein, op deze pc | Het afbeeldingsmodel van je externe LLM |
|---|---|---|
| Wat het is | een klein afbeeldingsmodel dat in de engine draait, naast YuE2 | het eigen afbeeldingsmodel van de provider, zoals dat van Gemini |
| Wat het kost | niets; zo'n 8 GB schijfruimte | elke afbeelding is een verzoek aan de provider, dat kan worden gefactureerd |
| Wat de pc verlaat | niets: de beschrijving wordt geschreven door Gemma op deze pc, of gemaakt uit de take zelf | de titel, stijl en eerste woorden van de take, en de beschrijving |
| Wanneer het draait | op de GPU als er geen nummer wordt gemaakt: na je nummer, nooit ervoor in de weg | naast renders, terwijl die lopen |
| Wat je instelt | een installatieoptie | de externe LLM in Instellingen, met een provider die een afbeeldingsmodel biedt |

**Om op deze pc te tekenen, installeer je FLUX.2 klein.**

- **Windows:** vink **FLUX.2 [klein]** aan op de componentenpagina van het installatieprogramma. Het staat niet aangevinkt
  tenzij je het kiest. Een geïnstalleerde app krijgt dezelfde pagina bij het bijwerken, of voer het installatieprogramma opnieuw uit
  vanaf de releasepagina: het vinkje wordt daarna onthouden, en een update downloadt het nooit twee keer. Het zijn
  drie bestanden, zo'n 8 GB in totaal.
- **Docker:** voer `sh scripts/fetch-models.sh --pictures` uit, dat de drie bestanden in `models/` zet
  (`diffusion_models`, `text_encoders` en `vae`) en elk controleert, en herstart dan de app met
  `docker compose restart app` zodat hij ze vindt.

**FLUX.2 klein 9B, als je de grafische kaart ervoor hebt.** klein heeft een grotere maat, een model van hogere kwaliteit
dat meer detail en betere handen en gezichten tekent, alleen bedoeld voor grafische kaarten met meer videogeheugen.
Yeufonic downloadt het nooit, omdat de bestanden op Hugging Face afgeschermd zijn en onder de **niet-commerciële licentie**
van Black Forest Labs vallen, maar zet ze op hun plek en ze worden gebruikt.

- **Schijf:** zo'n 18 GB voor het gebruikelijke paar, het FP8-model en zijn FP8-tekstencoder (16 GB met de FP4-
  encoder), naast de bestanden van de 4B. Hij heeft de VAE van de 4B nodig (`flux2-vae.safetensors`), dus installeer eerst de 4B.
- **Videogeheugen:** draait op een kaart van 16 GB, maar neemt er tijdens het tekenen bijna alles van in, met het vrije geheugen
  bijna op nul. Afbeeldingen wachten tot er geen nummer wordt gemaakt, dus het vertraagt je nummers niet, maar andere
  programma's die de grafische kaart tegelijk gebruiken kunnen het moeilijk krijgen. Met minder geheugen werkt het nog, maar
  trager, terwijl de engine het model in en uit laadt; daar is de 4B de betere keuze.

1. **Het model.** Log in bij Hugging Face, accepteer de licentie op
   [black-forest-labs/FLUX.2-klein-9b-fp8](https://huggingface.co/black-forest-labs/FLUX.2-klein-9b-fp8)
   en download `flux-2-klein-9b-fp8.safetensors` (9,4 GB). Of neem de versie met volle precisie
   `flux-2-klein-9b.safetensors` van [black-forest-labs/FLUX.2-klein-9B](https://huggingface.co/black-forest-labs/FLUX.2-klein-9B),
   die voor de Mac, die ongeveer twee keer zo groot is en twee keer zoveel geheugen nodig heeft.
   Hij gaat in de map `diffusion_models`.
2. **Zijn tekstencoder.** Download van [Comfy-Org/Flux-2-Klein-9B](https://huggingface.co/Comfy-Org/Flux-2-Klein-9B/tree/main/split_files/text_encoders),
   waarvoor je niet hoeft in te loggen, een van deze en zet hem in de map `text_encoders`:
   `qwen_3_8b_fp8mixed.safetensors` (8,7 GB, de gewone keuze op een NVIDIA-kaart), `qwen_3_8b_fp4mixed.safetensors`
   (6,8 GB, de kleinste) of `qwen_3_8b.safetensors` (16,4 GB, volle precisie, voor een Mac).
   **Met de yue2.cpp-engine** kan de afbeeldingsserver die encoders niet lezen: neem in plaats daarvan `Qwen3-8B-Q4_K_M.gguf`
   (5,0 GB) van [unsloth/Qwen3-8B-GGUF](https://huggingface.co/unsloth/Qwen3-8B-GGUF)
   (`-Q8_0.gguf`, 8,7 GB, werkt ook), en zet hem in dezelfde map.
3. **Waar de mappen zijn:** onder `models/` in de Yeufonic-map voor **Docker**; onder
   `engine\ComfyUI\models` in de installatiemap op **Windows**; onder `engine/ComfyUI/models/` in de
   installatiemap op een **Mac**.
4. **Laat de app ze zien, en kies hem.** Herstart Yeufonic (met Docker, `docker compose restart app`),
   en zet dan **Take-afbeeldingen: model** in Instellingen op *FLUX.2 klein 9B*. De 4B tekent tot je dat doet, en
   Instellingen zegt het als de 9B gekozen is maar hier niet kan tekenen. Kies
   *4B* om terug te gaan zonder iets weg te halen. De notitie bij de afbeelding in de editor zegt welke hem tekende
   (*drawn by FLUX.2 klein 9B on this PC*).

Het model en zijn encoder worden alleen onder deze namen gevonden, dus houd de bestandsnamen zoals ze gedownload worden.

**FLUX 3 klein, voor belettering en een kaart van 12 GB of meer.** FLUX 3 Image Klein van Black Forest Labs tekent vanuit een
volledige scènebeschrijving, en dat is precies wat de afbeeldingsprompts zijn die Gemma of de externe LLM schrijven, en
het lettert goed, wat past bij **Take-afbeeldingen: songtitel op de afbeelding**. Net als de 9B downloadt Yeufonic het nooit: de bestanden zijn
op Hugging Face afgeschermd en vallen onder de **FLUX Kommunity License** (niet-commercieel gebruik, en commercieel gebruik van wat
het tekent voor wie onder de omzetgrens van de licentie zit; lees hem voordat je hem accepteert). Zet de bestanden op hun plek en het
wordt kiesbaar.

- **Schijf:** zo'n 11 GB voor het int8-paar, naast de bestanden van de 4B. Het gebruikt de VAE van de 4B (`flux2-vae.safetensors`),
  dus installeer eerst de 4B.
- **Videogeheugen:** zo'n 11 GB tijdens het tekenen. Het zet een aantal keer meer stappen dan de FLUX.2 klein, dus elke
  afbeelding duurt langer.
- **Engine:** voorlopig alleen de ComfyUI-engine; met de yue2.cpp-engine wordt het niet aangeboden.

1. **Log in bij Hugging Face** en accepteer de licentie op
   [black-forest-labs/flux-3-image-klein-comfy](https://huggingface.co/black-forest-labs/flux-3-image-klein-comfy).
2. **Het model,** in de map `diffusion_models`: `flux3-image-klein-int8-convrot.safetensors` (5,8 GB, de gewone
   keuze op een NVIDIA-kaart), `flux3-image-klein-nvfp4.safetensors` (5,3 GB, voor een RTX 50-kaart) of
   `flux3-image-klein-bf16.safetensors` (11,1 GB, volle precisie, voor een Mac).
3. **Zijn tekstencoder,** in de map `text_encoders`: `qwen3vl_4b_int8_convrot.safetensors` (4,9 GB) of
   `qwen3vl_4b_bf16.safetensors` (8,9 GB, voor een Mac).
4. **Laat de app ze zien, en kies het:** herstart Yeufonic (met Docker, `docker compose restart app`), en zet dan
   **Take-afbeeldingen: model** in Instellingen op *FLUX 3 klein*. De notitie bij de afbeelding in de editor zegt *drawn by
   FLUX 3 klein on this PC*.

De mappen zijn dezelfde als voor de 9B, en de bestanden worden alleen onder deze namen gevonden.

**FIBO 2.0, voor de uitstraling van een foto en een kaart van 16 GB.** Bria's FIBO 2.0 tekent het dichtst bij een echte
foto van de hoezen waarop de afbeeldingen zijn gebaseerd: scherpere details, een natuurlijke scherptediepte, de kleuren
van film en meer van wat de beschrijving vraagt. Ook FIBO downloadt Yeufonic nooit. **De licentie is CC BY-NC 4.0:
alleen niet-commercieel gebruik.** De licentie van FLUX 3 laat iemand onder de omzetgrens wat het tekent commercieel
gebruiken; bij FIBO heeft elk commercieel gebruik, ook een hoes voor een nummer dat je verkoopt, een overeenkomst met
Bria nodig. Lees de licentie voordat je het gebruikt.

- **Schijf:** ongeveer 10,4 GB, het model en zijn turbo-toevoeging. Het leest de tekstencoder van FLUX 3 en de VAE van
  de 4B, dus met FLUX 3 geïnstalleerd is er verder niets nodig.
- **Videogeheugen:** ongeveer 12,5 GB tijdens het tekenen, dus een kaart van 16 GB. Een kleinere kaart lagert een deel
  uit, wat veel trager is.
- **Tijd:** met de turbo-toevoeging ongeveer even lang als FLUX 3. Zonder tekent FIBO met zijn eigen instellingen,
  ongeveer acht keer zo lang.
- **De hoes:** getekend door FIBO heeft de rand om de foto geen dunne donkere lijn; FIBO tekende die als dikke balken
  en een kader om de titel.
- **Engine:** alleen de ComfyUI-engine.

1. **Het model,** van [Comfy-Org/Fibo-2.0](https://huggingface.co/Comfy-Org/Fibo-2.0), zonder aanmelden, in de map
   `diffusion_models`: `fibo2_dev_int8_convrot.safetensors` (8,4 GB, de gebruikelijke keuze op een NVIDIA-kaart) of
   `fibo2_dev_bf16.safetensors` (16,5 GB, volle precisie, voor een Mac).
2. **De turbo-toevoeging,** van dezelfde pagina, in de map `loras`:
   `fibo_2.0_turbo_lora_avg_rank_270_bf16.safetensors` (2 GB). Het is geen stijl-LoRA en wordt niet als zodanig aangeboden.
3. **De tekstencoder,** als FLUX 3 niet geïnstalleerd is: `qwen3vl_4b_int8_convrot.safetensors` (4,9 GB) of
   `qwen3vl_4b_bf16.safetensors` (8,9 GB, voor een Mac), van dezelfde pagina, in de map `text_encoders`.
4. **Laat de app ze zien, en kies het:** start Yeufonic opnieuw (met Docker `docker compose restart app`) en zet dan
   **Take-afbeeldingen: model** in de Instellingen op *FIBO 2.0*. De notitie bij de afbeelding in de editor zegt
   *drawn by FIBO 2.0 on this PC*.

**Om met een externe LLM te tekenen,** open je Instellingen en zet je **LLM voor het schrijven van songteksten & stijltags** op de
[externe LLM](#external-llm), met zijn **API-URL**, **API-sleutel** en **model**, zoals voor teksten. De provider moet een
afbeeldingsmodel hebben: Gemini heeft er een (`gemini-3.1-flash-image` wordt gebruikt tenzij je een ander noemt), en aan een OpenAI-compatibele provider
wordt `gpt-image-1` gevraagd. De app vraagt de provider op de achtergrond om zijn lijst met modellen,
bij het opstarten, als deze instellingen veranderen en om de paar uur, en tekent daar alleen als de lijst
het afbeeldingsmodel heeft.

Zonder een van beide zegt **Take-afbeeldingen** in Instellingen **Geen afbeeldingen: de standaardachtergrond**, met een regel over hoe je ze
krijgt, en de keuze om ze te maken is niet te kiezen.
Stel een van beide in en ze gaan aan: vanaf dan worden er afbeeldingen gemaakt voor de takes die je maakt.

#### De afbeeldingen beheren in Instellingen {#managing-pictures-in-settings}

| Instelling | Doet |
|---|---|
| **Take-afbeeldingen** | *Maak er een voor elke nieuwe take* (de standaard als iets kan tekenen), of *Alleen op verzoek*, waarbij een take de standaardachtergrond houdt tot je er een maakt via zijn vierkantje of de knop Afbeelding in de editor. De instellingen hieronder vormen een afbeelding die op een van beide manieren is gemaakt. Staat op *Geen afbeeldingen* zolang niets hier kan tekenen. |
| **Take-afbeeldingen: getekend door** | *Deze pc als klein geïnstalleerd is, anders de externe LLM* (standaard), *Deze pc (het model hieronder)* of *Het afbeeldingsmodel van de externe LLM*. Welke klein op deze pc tekent (FLUX.2 klein 4B of 9B, of FLUX 3 klein) kies je bij **model**. FIBO 2.0 wordt daar ook gekozen. |
| **Take-afbeeldingen: model** | *FLUX.2 klein 4B* (standaard), *FLUX.2 klein 9B*, *FLUX 3 klein*, of *9B waar zijn bestanden geïnstalleerd zijn, anders 4B*. Alleen voor afbeeldingen getekend op deze pc. De 9B en FLUX 3 worden nooit voor je geïnstalleerd: zie [FLUX.2 klein 9B en FLUX 3 klein](#two-ways-to-draw-flux-2-klein-on-this-pc-or-an-external-llm) hierboven. Als de gevraagde er niet is, tekent een andere, en Instellingen zegt welke. *FIBO 2.0* wordt ook met de hand toegevoegd en is alleen voor niet-commercieel gebruik: zie hierboven. |
| **Take-afbeeldingen: beschreven door** | wie de afbeeldingsprompt schrijft, uit de titel van de take, de kunststijl hieronder, zijn stijl en zijn tekst (tot 50 regels). *Lokale Gemma als die geïnstalleerd is, anders de take zelf* (standaard), wie er ook tekent. *Lokale Gemma*: geschreven op deze pc; heeft de optie Tekstconcepten nodig. *Uit de take zelf*: geen LLM; een beschrijving gemaakt uit de titel, stijl en eerste woorden van de take, de snelste, en er wordt niets verstuurd. Of de *externe LLM*, één verzoek per afbeelding; als die niet beschikbaar is, of je voor de sessie naar lokale LLM's overschakelt, schrijft Gemma ze in plaats daarvan als die geïnstalleerd is. |
| **Take-afbeeldingen: kunststijl** | hoe de afbeelding eruit moet zien, gegeven aan de LLM die de afbeeldingsprompt schrijft (gedimd als de take zichzelf beschrijft). Standaard een abstract, surrealistisch ontwerp in de stijl van hoezen uit de jaren zeventig en tachtig, zonder tekst of mensen. Leeggemaakt gaat het daarnaar terug. |
| **Take-afbeeldingen: je eigen prompt** | woorden waarmee de afbeeldingsprompt van elke afbeelding begint, zoals *salt marsh, overcast*, tot 512 tekens; de prompt die de LLM schrijft volgt erna. Leeg (standaard): geen. Alleen als een LLM de afbeeldingsprompt schrijft (gedimd als de take zichzelf beschrijft). |
| **Take-afbeeldingen: songtitel op de afbeelding** | *Nee* (standaard) of *Ja*: de titel van het nummer wordt vet op de hoes gezet, in hoofd- of kleine letters, zoals je hem typte, ook als het de naam van een artiest is (de afbeelding zelf wordt nog steeds zonder beschreven). Meestal wordt de afbeelding omlijst door een dunne donkere lijn binnen een gebroken witte rand, zoals op veel hoezen uit de jaren zeventig, met de titel gecentreerd in een bredere band boven of onder. Ongeveer één op de vijf heeft geen rand: de titel staat op de afbeelding, in een hoek of gecentreerd boven of onder, in een gedempte kleur uit de afbeelding, en de LLM wordt gevraagd dat deel van de afbeelding er vrij voor te houden. Dit wordt allemaal per afbeelding willekeurig gekozen. FLUX.2 klein kan hem met een tikfout schrijven. Alleen als een LLM de afbeeldingsprompt schrijft. |
| **Take-afbeeldingen: beeldmodel** | welk van de modellen van de provider tekent. Alleen voor afbeeldingen getekend door de externe LLM (kies die bij **Getekend door**; anders gedimd), en leeg voor het gewone model van de provider, wat bijna altijd is wat je wilt. |

Dus met FLUX.2 klein geïnstalleerd en de instellingen zoals ze komen, worden afbeeldingen helemaal op deze pc gemaakt, ook
als de externe LLM je teksten schrijft: Gemma schrijft elke afbeeldingsprompt waar de Tekstconcepten geïnstalleerd zijn, en
zonder wordt de beschrijving uit de take zelf gemaakt, zonder LLM, wat geen tijd kost. Kies *Het afbeeldingsmodel van de
externe LLM* om de provider ze te laten tekenen, of zet **beschreven door** op *Uit de take zelf* voor de
snelste afbeeldingen, of op *Externe LLM* (één verzoek per afbeelding).

#### De afbeelding van een take in de editor {#a-take-s-picture-in-the-editor}

Het pictogram **Afbeelding** in de bovenste rij van het editorvenster, naast de andere knoppen van de take, toont de afbeelding
met twee keuzes: **Een nieuwe afbeelding maken**, die hem op de achtergrond opnieuw maakt, en **De standaardachtergrond gebruiken**, die hem voorgoed weghaalt: er wordt geen afbeelding meer gemaakt voor die take tenzij je erom vraagt.
Klik op de afbeelding om hem helemaal te zien, zo groot als het venster toelaat; een klik ergens of Escape
haalt hem weg en laat de editor zoals hij was. De volledige afbeelding heeft dezelfde twee keuzes eronder. Kies
daar **Een nieuwe afbeelding maken** en de afbeelding blijft in beeld terwijl de nieuwe wordt gemaakt, met wat er gebeurt getoond
tussen de knoppen, en wisselt naar de nieuwe als die klaar is.

Op de kaart van een take toont het vierkantje linksboven de afbeelding als je de muis erover beweegt. Een take zonder
afbeelding biedt daar in plaats daarvan **Een nieuwe afbeelding maken**, waar deze pc afbeeldingen kan maken.

### Takes vergelijken {#comparing-takes}

Vink twee tot zes takes aan en klik op **Vergelijken** (het verschijnt naast Alles selecteren als er twee zijn aangevinkt, en
wacht op takes die nog renderen). De takes worden in een venster gestapeld op een gedeelde positie: druk op **1** tot
**6** of klik op een om te wisselen, en speel verder vanaf hetzelfde moment in het nummer, spelend of
gepauzeerd. **Spatie** speelt en pauzeert, de pijltjes springen 5 seconden, en de ster markeert de take die
je verkiest. **Luidheid gelijktrekken** brengt luidere takes omlaag naar de zachtste, omdat een luidere take vaak
beter klinkt; **Namen verbergen** schudt de takes en noemt ze Take A, B, C voor een blinde luistertest.

### De speler {#the-player}

Klik of sleep in de golfvorm om te zoeken. Vorige en volgende lopen door de kaarten in de getoonde volgorde.

| Toets | Doet |
|---|---|
| Spatie | afspelen of pauzeren |
| Links, Rechts | vijf seconden terug of vooruit |
| Shift+Links, Shift+Rechts | de vorige of volgende take; in de weergave Afspeellijsten, het vorige of volgende nummer van de lijst |
| Omhoog, Omlaag | volume |

Mediatoetsen van het systeem werken ook. De eigen toetsen van de take staan bij [Sneltoetsen](#hot-keys).

### De audiovisualizer en de gesynchroniseerde tekst {#the-audio-visualizer-and-synced-lyrics}

Klik op **Visualizer** in de transportbalk (of **V** terwijl er een track speelt) om het visualizerpodium schermvullend te openen.

Het podium toont realtime audiovisualisaties die met het afspelen zijn gesynchroniseerd:

- **Visualizermodi:** kies uit tien visualizers in de bovenbalk:
  - *Yeufonic:* het logo zelf, ademend — de tegel gloeit met de bas en zwelt aan met de beat, elke arm van de stemvork is een meter met zijn helft van het spectrum, en de groene stip licht op met de beat.
  - *Golflint:* twee zwevende harmonische linten die op het geluid reageren.
  - *Noorderlicht:* golvende gordijnen van etherisch poollicht die op midden en hoog reageren.
  - *Kosmische nevel:* een sterrenveld en een nevel van interstellaire deeltjes die draait en meepulseert op de maat.
  - *Caleidoscoop:* radiale geometrische symmetrieën die met het tempo pulseren.
  - *Neonraster:* een retrofuturistisch synthwave-draadmodelvlak in perspectief dat golft met de baslijnen.
  - *Vloeibare vervorming:* een vloeibaar oppervlak dat door harmonische golven wordt vervormd.
  - *Deeltjeszwerm:* zwaartekrachtige deeltjeswolken die uiteenspatten op slagwerkaccenten.
  - *Hifi-spectrumbalken:* een spectrumanalyzer met meerdere banden en zwevende, vallende pieken.
  - *Hoes:* de afbeelding van de take, groot, met de titel eronder, op een vervaagde kopie van zichzelf die met de muziek meebeweegt. Een take zonder afbeelding toont de Yeufonic-scène tot er een is gemaakt.
- **Achter de scènes:** de scènes Hoes, Yeufonic, Mandala, Raster, Vloeibaar en Balken spelen over de afbeelding van de take, die zachtjes met de muziek meebeweegt, als de take er een heeft. Erbovenop kan ook iets bewegen, in de kleuren van de afbeelding: *Ademen* (alleen de afbeelding), *Lichtstralen* die vanuit het midden draaien, *Rimpelingen* die met de beat worden uitgezonden, *Kleurdrift*, *Diepte* (meer kopieën van de afbeelding die tegen elkaar in draaien) of een *Spectrale halo*. Elke scène begint met zijn eigen (kleurdrift achter Hoes, de halo achter Mandala, stralen achter Raster, rimpelingen achter Vloeibaar, alleen de afbeelding achter Yeufonic en Balken); druk op **B** om ze door te lopen, en de scène onthoudt je keuze.
- **De golfvorm:** onder de scènes Yeufonic en Hoes laat de golfvorm van de take zien hoeveel van het nummer al gespeeld is; klik erop om erheen te springen.
- **Hoes en vinyldynamiek:** toont de hoes van de take in Hipgnosis-stijl in een interactieve 3D-hoes die kantelt en draait met de aanwijzer. Een realistische vinylplaat draait op 33⅓ toeren en schuift uit de hoes op basslagen, met een holografische glans en schokgolfringen die op het ritme reageren. Wissel van modus met de knop **Hoes**: *Hoes*, *Aura* (vervaagde achtergrond) of *Uit*.
- **Een nieuwe afbeelding:** de afbeeldingsknop rechtsboven, in elke scène, maakt een nieuwe afbeelding voor de spelende take, waar deze pc afbeeldingen kan maken. Hij pulseert terwijl de afbeelding wordt gemaakt, en de nieuwe neemt het over als hij klaar is.
- **Tekst op het scherm:** druk op **L** of klik op **Tekst** om het losse, scrollbare tekstpaneel te tonen of te verbergen. Sleep het aan de balk bovenaan uit de weg; het blijft waar je het neerzet, en dubbelklikken op de balk zet het terug.
- **Lint van de minispeler:** zolang de volledige visualizer dicht is, speelt een reactieve minivisualizer met dubbele golf in de onderste transportbalk. Zet hem aan of uit in **Instellingen → Weergave**.

### Afspeellijsten en favorieten {#playlists-liked-songs}

Klik op **Afspeellijsten** in de bovenbalk om naar de weergave Afspeellijsten te gaan.

- **Opmaak in twee kolommen:** de linkerkolom toont je afspeellijsten naast de vastgezette systeemlijst **Leuk gevonden**, met het totale aantal nummers. De hoofdkolom toont de kop van de actieve lijst (hoes in hoge resolutie, titel, beschrijving, totaal aantal nummers en duur) en de tabel met tracks.
- **Favorieten automatisch bijhouden:** elke take met een ster in de bibliotheek, in welke ruimte ook, verschijnt automatisch in de favorietenlijst. De ster weghalen haalt hem eruit.
- **Toevoegen aan een afspeellijst:** druk op **P** of klik op het pictogram **Afspeellijst** op een kaart om de lijstkiezer te openen, lidmaatschap van lijsten aan of uit te vinken, of een nieuwe te maken. **Escape** sluit de kiezer.
- **Interactief sorteren en zoeken:** klik op een kolomkop (**Titel**, **Duur** of **Toegevoegd**) om te sorteren met een richtingsaanduiding en de volgorde met één klik om te keren, en filter tracks met het zoekvak.
- **Naar de ruimte in de bibliotheek:** klik op de titel van een nummer in de tracktabel om meteen naar de weergave Bibliotheek te gaan, de ruimte te openen waar die take woont en zijn kaart te markeren.
- **Sneltoetsen in afspeellijsten:** de eigen sneltoetsen van takes worden in de weergave Afspeellijsten genegeerd om onbedoelde wijzigingen te voorkomen, behalve **M** (masteringrack), dat werkt op de spelende of geladen track, naast de gewone transportknoppen (**Spatie**, pijltjes, **?** en **L**).
- **Doorlopend en willekeurig afspelen:** klik op **Afspelen** in de kop van de lijst om vanaf track 1 te luisteren, of op **Willekeurig** voor een willekeurige volgorde. Het afspelen gaat automatisch door naar de volgende track van de lijst als elk nummer afloopt.

### Sneltoetsen {#hot-keys}

Op de hoofdpagina werken losse toetsen op de **gekozen take**: die in het linkerpaneel. Klik op zijn kaart om
hem te kiezen. Elke toets doet wat zijn knop doet, dus een toets die zou verwijderen vraagt eerst, en een take
die niet kan wat een toets vraagt (Variaties bij een take zonder partituur, bijvoorbeeld) laat een regel achter in de
statusbalk die zegt waarom.

| Toets | Doet |
|---|---|
| Spatie | afspelen of pauzeren |
| Links, Rechts | vijf seconden terug of vooruit |
| Shift+Links, Shift+Rechts | de vorige of volgende take; in de weergave Afspeellijsten, het vorige of volgende nummer van de lijst |
| Omhoog, Omlaag | volume |
| M | het masteringrack van de take openen; nog eens om het te sluiten |
| E | de take in de editor openen |
| I | de details van de take: alles waarmee hij gemaakt is, in woorden, met **Kopiëren** |
| N | de take normaliseren, of dat ongedaan maken als hij genormaliseerd is |
| V | de visualizer openen of sluiten tijdens het afspelen, of Variaties als er niets speelt |
| T | Meer proberen |
| S | de take een ster geven of die weghalen |
| P | de take aan een afspeellijst toevoegen |
| D | de take verwijderen, na een vraag, zoals zijn prullenbak |
| L | de logs; of de tekst tonen als de visualizer open is |
| B | in de visualizer, wat er achter een scène beweegt over de afbeelding van de take |
| F | schermvullend |
| ? | de sneltoetsen tonen of verbergen; nog eens om te sluiten |
| Escape | het voorste venster sluiten: de visualizer, de logs, het masteringrack boven de editor, daarna de editor of een ander venster |

Lettertoetsen doen niets terwijl je in een vak typt, terwijl er een venster voor open is, of met Ctrl,
Alt of de Windows- of Command-toets ingedrukt, zodat de eigen sneltoetsen van de browser (Ctrl+L, Ctrl+S en de rest)
blijven werken. De tooltip van een knop noemt zijn toets, zoals bij **Variaties (V)**. Druk op elk moment op **?** om de lijst met sneltoetsen te zien.

In het editorvenster bedienen Spatie en de pijltjes de speler van het venster, voor de take die daar open is, zolang zijn speler
zichtbaar is: in elke stap, en met het masteringrack erboven open. Ze werken nooit terwijl je in een vak typt,
en de lettertoetsen zijn alleen voor de hoofdpagina. De pianorol heeft zijn eigen toetsen: zie [De pianorol](#the-piano-roll).

---

## Instellingen {#settings}

Klik op **Yeufonic** linksboven. Instellingen worden op de server bewaard, dus ze volgen je naar elke
browser en overleven een herbouw: het audioformaat voor stems en voor het bewaren van een take, het
scheidingsmodel, waar stems worden geschreven, of trainingscheckpoints worden bewaard, en hoe wordt
gecontroleerd dat instrumentale nummers niet zingen.

### Opslag {#storage}

**Instellingen → Opslag** laat zien waar de schijfruimte van Yeufonic heen gaat en laat je een deel terugwinnen. Een corpus
trainen laat veel bestanden achter die niet meer nodig zijn: kopieën gemaakt voor de engine terwijl de nummers werden geanalyseerd,
de trainingsset (elk nummer herschreven als verliesvrije FLAC, groter dan het origineel), en de checkpoints
die onderweg zijn bewaard. Het venster toont elk met zijn grootte, **wat het is** en **wat het kost om
het weg te halen**, en haalt alleen weg wat je aanvinkt, na een laatste bevestiging. **Die aanvinken die niets kosten** vinkt
de kopieën aan die gewoon opnieuw worden gemaakt als ze nodig zijn.

Nummers die vanaf nu worden geanalyseerd bewaren hun afgescheiden stem als FLAC, dezelfde audio in ongeveer de helft van de ruimte. Het
venster kan **de WAV-stemmen die je al hebt omzetten**: elk wordt omgezet, gecontroleerd op een decodering naar precies dezelfde
audio, en pas dan wordt de WAV weggehaald. Het draait op de achtergrond en kan worden gestopt.

Trainingscheckpoints verdienen een tweede blik voordat ze weggaan: elk is een item in de lijst met stijl-LoRA's dat je
kunt kiezen voor nieuwe takes, dus de checkpoints van een corpus weghalen haalt die items voorgoed uit de lijst. Zijn
afgeronde LoRA blijft en blijft werken. De trainingsset van een corpus is anders: die weghalen laat de LoRA en zijn
checkpoints in de lijst staan, en alleen dat corpus opnieuw trainen heeft hem nodig.

Je takes, nummers, afgeronde LoRA's en modellen verschijnen nooit om weg te halen. Alles wat bij een corpus hoort dat
wordt getraind, geëxporteerd of geanalyseerd wordt gedimd getoond en kan niet worden aangeraakt tot het klaar is.

Daaronder kiest **Automatisch opruimen** wat Yeufonic voor je weghaalt: de werkkopieën van elk nummer
als zijn analyse klaar is (standaard aan), de trainingsset als een LoRA is getraind (standaard uit; het corpus
heeft dan nog een **Exporteren** nodig voordat het opnieuw kan trainen), en de trainingscheckpoints (standaard bewaard).

De images en de buildcache van Docker staan buiten Yeufonic en worden hier niet behandeld; `docker system df` toont ze.

### Het YuE2-model {#the-yue2-model}

YuE2 komt in twee maten, en een installatie heeft er een: **volle kwaliteit**, die we aanraden, of **weinig
geheugen**, een kleinere kopie voor grafische kaarten met weinig videogeheugen. **Over**, in hetzelfde menu,
zegt welke je hebt. Je kiest hem bij het installeren van Yeufonic, niet hier:

- **Op Windows** voer je het installatieprogramma opnieuw uit. Zijn componentenpagina biedt beide maten en vinkt
  de al gedownloade aan. Wisselen downloadt de andere de eerste keer en houdt beide, dus teruggaan
  downloadt niets.
- **Met Docker** downloadt `sh scripts/fetch-models.sh` volle kwaliteit en
  `sh scripts/fetch-models.sh --int8` de versie voor weinig geheugen. Met beide bestanden in `models/checkpoints` gebruikt de
  app volle kwaliteit, tenzij `YUE2_CHECKPOINT=int8` in `.env` staat.

Probeer de versie voor weinig geheugen als renders erg traag zijn of de engine zonder GPU-geheugen raakt. Een LoRA trainen werkt
met beide modelmaten. De instelling **Training met het model voor weinig geheugen (int8)** kiest welke: uit traint met
het model van volle kwaliteit; aan gebruikt het model waarmee de app rendert. Hij staat aan als alleen het model voor weinig
geheugen geïnstalleerd is. De README op GitHub heeft een sectie, *Choosing a model size*, met wat je van elk kunt verwachten.

Yeufonic kan ook de engine **yue2.cpp** gebruiken in plaats van ComfyUI, voor grafische kaarten met minder geheugen,
gekozen bij het instellen: op de componentenpagina van het Windows-installatieprogramma, of met Docker via
`sh scripts/fetch-models.sh --cpp`. **Over** zegt welke engine draait, en de kaart van een take welke engine hem renderde. Hij maakt nummers, covers en
instrumentale nummers en transcribeert opnames, met je stijl-LoRA's; Gemma kan teksten opzetten en afbeeldingen beschrijven
ernaast (met Docker, `--gemma`), en FLUX.2 klein ze tekenen (`--pictures`). Trainen heeft de ComfyUI-
engine nodig: met yue2.cpp worden corpora en trainen niet aangeboden. De pagina
[Choosing an engine](https://github.com/yeufonic/yeufonic/blob/main/docs/ENGINES.md) op GitHub heeft de
volledige lijst, en hoe je wisselt.

**Zoeken naar een nieuwe versie** is het enige hier dat uit zichzelf internet gebruikt: elke
vier uur vraagt de app aan yeufonic.com of er een nieuwere versie uit is, en zegt het met een pil naast het
versienummer rechtsboven. Die pil geeft je het installatieprogramma, of, voor een Docker-kopie, de twee opdrachten
die hem bijwerken. Het is één verzoek en verder verlaat niets de computer; **Niet controleren** zet het
uit. **Zoeken naar updates** in het menu vraagt het meteen, of dit nu aan staat of niet, en antwoordt in
het menu: welke versie je hebt, en of het de nieuwste is.

Als er een nieuwere is, biedt het menu **x.y.z ophalen**, dat het installatieprogramma downloadt op een Windows-installatie of de twee opdrachten op het klembord zet voor een Docker-kopie.

**Thema** bepaalt hoe de app eruitziet: **Donker**, **Licht**, **Zoals de computer (donker of licht)**, dat het licht of donker van je
systeem volgt en ermee meewisselt, **Studio**, een warm donker met amber, of **Hoog contrast**, zwart en wit
met duidelijke randen. Het verandert meteen, en elke browser onthoudt het
zodat de pagina zo opent. Het logvenster blijft in elk thema donker, zoals een terminal. Het masteringrack volgt ook het thema: in het lichte thema zijn zijn panelen geborsteld zilver, terwijl zijn knoppen,
meterschermpjes en displays de donkere hardwarelook houden.

**Achtergrondkleur**, onder Thema, kleurt de pagina achter de takes met een kleur die je kiest: vink **Tint** aan, en
beweeg dan **Kleurtoon** rond het kleurenwiel en **Sterkte** van een lichte waas naar een volle kleur. De pagina verandert terwijl
je sleept, en de keuze wordt bewaard als je loslaat. Takekaarten, panelen en vensters houden hun eigen
kleuren, en het thema met hoog contrast blijft zwart.

### Externe LLM {#external-llm}

Yeufonic kan tekstconcepten schrijven, opnames transcriberen, de secties van nummers markeren en de stijlen van corpora analyseren met een externe LLM in plaats van het lokale Gemma-model.

Een externe LLM gebruiken heeft twee duidelijke voordelen:
- **Bespaart GPU-geheugen:** voorkomt dat het Gemma 4-model in het VRAM van de GPU wordt geladen (wat zo'n 8 GB videogeheugen bespaart), zodat je grafische kaart helemaal vrij is voor het plannen en audiorenderen van YuE2.
- **Rijkere concepten en analyses:** grote cloudmodellen zetten vaak genuanceerdere teksten op en geven gedetailleerde stijltags voor je corpora.

**Aanbevolen provider:** we raden aan een externe LLM-provider te kiezen waarvan de API geen facturering heeft, als je die beschikbaar hebt — **Google Gemini** is een goed voorbeeld. De Gemini-API (via Google AI Studio) biedt een royale gratis laag zonder facturering, ondersteunt de standaard OpenAI-compatibele endpoints (`https://generativelanguage.googleapis.com/v1beta/openai/`) en neemt audio rechtstreeks aan voor het transcriberen van opnames.

Als je een API gebruikt die per verbruik of per token betaald wordt (zoals de betaalde lagen van OpenAI of Anthropic), kan het analyseren van een heel corpus met tientallen nummers of het maken van beschrijvingen voor veel takes snel API-tegoed opmaken of bestedingslimieten raken. Als een externe API een quota- of ratelimietfout geeft (HTTP 429), toont Yeufonic een waarschuwing en laat je voor de rest van de sessie naar lokale modellen overschakelen, zodat andere taken zonder onderbreking doorgaan. Een provider zonder facturering voorkomt onverwachte kosten.

**Instellen:**
1. Open **Yeufonic → Instellingen → Externe LLM & songteksten**.
2. Zet **LLM voor het schrijven van songteksten & stijltags** op **Externe LLM (OpenAI-compatibele API)**.
3. Vul de **API-URL**, **API-sleutel** en het **model** van je provider in (bijvoorbeeld het model `gemini-2.5-flash` of `gemini-1.5-flash` met de OpenAI-compatibele basis-URL van Google Gemini `https://generativelanguage.googleapis.com/v1beta/openai/`).
4. Klik op **LLM-verbinding testen** om je gegevens te controleren.
5. Als het gekozen model audio-invoer aanneemt (zoals Gemini), kun je ook **Songtekst uit een opname** op **Externe LLM** zetten zodat het naar afgescheiden stemmen luistert.

---

## Yeufonic gebruiken vanuit een AI-agent (MCP) {#using-yeufonic-from-an-ai-agent-mcp}

Yeufonic kan als **MCP-server** werken. Daarmee kan een AI-agent op dezelfde computer, zoals Claude Code of Cursor, het voor je gebruiken:
een nummer, cover of instrumentaal vragen, erop wachten, het afspelen, het anders proberen, het een afbeelding geven, het in een afspeellijst zetten en
de bibliotheek opruimen, allemaal in je eigen woorden (“maak een EDM-instrumentaal van een minuut in de ruimte EDM en speel het af”). De agent doet wat de pagina doet, via dezelfde wegen, dus een take die hij begint is een
gewone take in je bibliotheek.

### Instellen {#setting-it-up}

1. **Zet het aan.** Open Instellingen en zet **MCP-server** op **Aan**. Het staat standaard uit, omdat een verzoek GPU-werk kan starten.
2. **Verbind je agent** met het adres van de app met `/mcp` erachter: het adres waarop je Yeufonic opent, bijvoorbeeld
   `http://localhost:8090/mcp`. In Claude Code:

   ```
   claude mcp add --transport http yeufonic http://localhost:8090/mcp
   ```

   Andere clients nemen hetzelfde adres als HTTP-server. Clients die een configuratiebestand lezen willen meestal iets als
   `{"mcpServers": {"yeufonic": {"url": "http://localhost:8090/mcp"}}}`. Er is geen inlog of sleutel nodig.
3. **Vraag.** Start je agent vanuit elke map en beschrijf wat je wilt.

**Welk adres?** Het is het adres waarop je Yeufonic opent, met `/mcp` erachter.
- **Docker:** `http://localhost:8090/mcp`.
- **De Windows-installatie:** de poort van de app staat in `settings.ini` (`app_port`, 8090 tenzij je hem veranderde, bijvoorbeeld om naast
  een Docker-kopie te draaien). Met `app_port = 8091` is het `http://localhost:8091/mcp`.
- **Agent in WSL, app op Windows:** dit verbindt niet. De Windows-app luistert alleen op het eigen loopbackadres van Windows, dat WSL niet
  kan bereiken (Docker binnen WSL is prima, omdat dat ook in WSL zit). Draai de agent vanuit Windows (PowerShell of de Windows-versie van
  je agent), of zet het gespiegelde netwerk van WSL aan (`networkingMode=mirrored` onder `[wsl2]` in `.wslconfig`, daarna `wsl --shutdown`),
  waardoor `localhost` aan beide kanten hetzelfde is.

Als je agent zegt dat de server **authenticatie nodig heeft**, komt dat bijna altijd doordat de instelling nog uit staat: zet hem aan, en
verbind de agent daarna opnieuw (in Claude Code, `/mcp`). Verbind ook opnieuw na het herstarten van Yeufonic, want een herstart verbreekt de verbinding.

### Wat je kunt vragen {#what-you-can-ask-for}

| Vraag | Wat er gebeurt |
|---|---|
| “Toon mijn laatste takes”, “toon de takes in de ruimte EDM” | Toont takes, nieuwste eerst, met een kort id, wanneer elk is gemaakt, de lengte en de stijl |
| “Maak een instrumentaal van een minuut in synthwave-stijl” | Plant en rendert een instrumentaal. Een lengte, een ruimte en een [stijl-LoRA](#style-loras) kunnen worden genoemd |
| “Maak een folknummer met deze tekst” | Hetzelfde voor een nummer, vanuit de tekst die je geeft |
| “…met avontuurlijke harmonie, strakke interpretatie, in Fis, op 100 BPM” | Elke instelling van een nieuwe take met de namen die de pagina gebruikt: [Harmonie](#harmony), [Variatie van het plan](#plan-variety), de [interpretatie](#interpretation), toonsoort en tempo vastzetten, en voor een nummer **Deze structuur precies volgen** en **Stemmen volgen de aanwijzingen**. Als niets gezegd wordt, begint een nieuwe take waar die van de pagina begint: Gevarieerd en Breed |
| “Schrijf een tekst over een nachttrein, in spreektoon” | De eigen **Songtekst schrijven** van de app, met zijn nummervormen, regels per sectie en tonen. De agent kan de tekst ook zelf schrijven |
| “Maak een cover van *de opname* in jazzstijl” | Maakt een cover van een opname die al in je bibliotheek staat. Heeft een partituur nodig (transcribeer hem eerst in de app). Zonder eigen tekst gebruikt hij de woorden die in de opname gehoord zijn |
| “Speel het af” | Opent de take in je browser, waar hij speelt |
| “Geef die een ster”, “noem hem Sunrise”, “verplaats hem naar de ruimte Folk” | Geeft een ster, hernoemt of verplaatst een take |
| “Render hem opnieuw met een nieuwe seed”, “stop daarmee” | Rendert een take opnieuw, of annuleert een lopende |
| “Geef me er nog een paar zoals die” | Rendert de take opnieuw met nieuwe seeds, als meerdere nieuwe takes om naast elkaar te beluisteren |
| “Zing hem opnieuw”, “probeer hem in elke interpretatie” | **Opnieuw zingen** (een nieuwe stem voor dezelfde partituur) of **Variaties** (dezelfde partituur en seed, op elke manier gespeeld). Variaties worden in de take bewaard, zoals Meer proberen |
| “Zing die melodie met deze tekst” | **Nieuwe tekst**: dezelfde melodie, toonsoort en tempo met een andere tekst, als nieuwe take |
| “Maak er een instrumentaal van” | Dezelfde partituur met de melodie op een instrument en zonder zang, als nieuwe take |
| “Schrijf er een nieuw plan voor, levendiger” | Een nieuw plan voor een take die nog geen audio heeft (gepland zonder render, of waarvan het plan mislukte). Een take met audio wordt niet aangeraakt: vraag in plaats daarvan een nieuwe take |
| “Haal de losse eruit” | **Eruit halen**: een take die in een andere bewaard is wordt een eigen take |
| “Geef hem een afbeelding” | Maakt een nieuwe afbeelding voor de take, zoals de knop **Afbeelding** van de editor, en geeft een link die hem opent. Een afbeelding getekend op deze computer wacht tot er geen nummer wordt gemaakt |
| “Zet de beste drie in een afspeellijst met de naam Road trip” | Maakt afspeellijsten, toont wat erin staat, en voegt takes toe of haalt ze weg. Een take in **Leuk gevonden** zetten geeft hem een ster |
| “Zoek een synthwave-stijl voor me”, “bewaar die stijl als Night drive” | Zoekt in je bewaarde en de ingebouwde stijlen, en bewaart een stijl onder een naam voor het stijlmenu |
| “Maak een ruimte met de naam Drafts” | Maakt een nieuwe ruimte om takes in te bewaren |
| “Transcribeer *de opname*” | Transcribeert een opname naar een partituur, zodat er een cover van kan worden gemaakt. Laat een opname die al een partituur heeft met rust tenzij erom gevraagd wordt |
| “Splits die in zang en instrumenten” | Splitst een klare take in partijen (vier, zes, of alleen zang en instrumenten) en geeft je een link naar elk bestand en een naar de hele set als zip |
| “Bewaar het recept van die take”, “…en de take erbij als MP3-zip” | Geeft het recept van de take (wat hem maakte, niet zijn audio) om te tonen, te wijzigen of als bestand te bewaren, met links om het alleen of met de audio als één zip te downloaden |
| “Importeer *Night Ferry.yeufonic.json* in Drafts en render het” | Een nieuwe take uit een takebestand, met het plan, gerenderd wanneer je het vraagt. Hij zegt welke LoRA's in het bestand niet geïnstalleerd zijn, en wanneer een cover als nummer binnenkwam |
| “Importeer het opnieuw in een dreampopstijl, zelfde partituur en seed” | Wijzigt het recept voor het importeren, zodat alleen anders is wat je noemt |
| “Welke engine maakte die take?”, “welke engine draait er?” | Zegt welke engine een take renderde, en welke Yeufonic nu gebruikt (ComfyUI of yue2.cpp) |
| “Is Yeufonic bezig?” | Zegt of de engine klaar is, wat er loopt en met welke voortgang, wat er wacht, en of er een LoRA wordt getraind |
| “Verwijder die take” | Toont wat er weg zou gaan en vraagt het je eerst; zie hieronder |

Een take maken duurt minuten. De agent begint hem en wacht, met voortgangsberichten, dus je kunt ondertussen om het volgende vragen.

### Hoe het kan gaan: een voorbeeld {#how-it-can-work-an-example}

Eén gesprek, van een idee tot een afspeellijst. Jij praat; de agent kiest de gereedschappen (de middelste kolom staat er alleen om te laten zien wat
er gebeurt) en vertelt je wat er terugkwam.

| Jij zegt | De agent | Wat je krijgt |
|---|---|---|
| “Schrijf een tekst over de laatste nacht van een vuurtorenwachter, folkstijl, verhaalvorm. Maak er dan een nummer van in een nieuwe ruimte met de naam Coast.” | `write_lyrics`, `create_space`, `make_song`, dan `wait_for_take` tot hij klaar is | De tekst, getiteld *The Last Light*, die je te zien krijgt; een ruimte met de naam Coast; een nummer daar gepland en gerenderd, met voortgang onderweg |
| “Speel het af.” | `get_take`, opent dan zijn `listen_url` | Het speelt in je browser |
| “Mooie melodie. Probeer hem losser en rustelozer, en geef me er een zonder zang.” | `make_variations` met los en rusteloos, `instrumental_from_take` | Twee takes in het nummer, en een instrumentaal ernaast |
| “Laat zien wat we hebben.” | `list_takes` in Coast, en met `inside` voor het nummer | Een lijst met een kort id voor elk, zodat je “3f9a” kunt zeggen in plaats van een titel |
| “Haal 3f9a eruit, geef hem een ster en een afbeelding.” | `take_out`, `star_take`, `make_picture` | De losse als eigen take, met een ster (dus ook in favorieten), met een link naar zijn afbeelding |
| “Zet die en de instrumentaal in een afspeellijst met de naam Coast demos.” | `create_playlist`, `add_to_playlist` | Een afspeellijst met de twee |
| “Bewaar de stijl als Coastal folk.” | `save_style` | **Coastal folk** in het stijlmenu van de app, klaar voor de volgende keer |
| “Nu een duet: deze tekst, met aanwijzingen [male voice] en [female voice], elke sectie zoals geschreven.” | `make_song` met `follow_structure` (een nieuw plan, omdat de secties veranderen) | Een nieuw nummer dat precies je secties plant, op volgorde, met elke aangewezen regel verplaatst naar waar die stem zingt |

Alles wat hij deed staat in de bibliotheek alsof je het op de pagina had gedaan: open elke take in de editor, master hem, of ga daar verder.
Als een stap niet kan, krijgt de agent de reden van de app zelf (“this take is an instrumental already”, “nothing here can draw a
picture”) en geeft die door, dus je hoort hetzelfde antwoord als de pagina zou geven.

### Alles wat hij kan {#everything-it-can-do}

Je hebt deze namen niet nodig: je vraagt in je eigen woorden en de agent kiest. Ze staan hier zodat je kunt zien wat er bestaat, en je
agent kunt zeggen welke je wilt.

| Gereedschap | Wat het doet |
|---|---|
| `list_takes` | Toont takes, nieuwste eerst, eventueel alleen die bij een paar woorden passen, in een genoemde ruimte, of met een ster. Toont een kort id |
| `get_take` | Eén take volledig: hoe hij is gemaakt, zijn status, eventuele fouten en, als hij audio heeft, een link die hem afspeelt. Kan de partituur bevatten |
| `wait_for_take` | Wacht (tot ongeveer een minuut per keer) op een take die gemaakt wordt, en zegt of hij klaar is |
| `make_instrumental` | Plant en rendert een instrumentaal vanuit een stijl, met een lengte, ruimte en stijl-LoRA als je ze noemt, en secties als je ze geeft |
| `make_song` | Hetzelfde voor een nummer, vanuit een tekst |
| `make_cover` | Een cover van een opname in de bibliotheek, met zijn partituur en, tenzij je andere geeft, zijn woorden |
| `try_more` | Meerdere extra takes van een bestaande, met nieuwe seeds |
| `sing_again` | Dezelfde partituur opnieuw gezongen met een nieuwe seed: een nieuwe stem, als nieuwe take |
| `make_variations` | Dezelfde partituur en seed in elke genoemde interpretatie (of alle), bewaard in de take |
| `new_words` | Dezelfde partituur gezongen met een andere tekst, als nieuwe take |
| `instrumental_from_take` | Dezelfde partituur als instrumentaal, als nieuwe take |
| `replan_take` | Een nieuw plan voor een take zonder audio, eventueel met andere Harmonie, Variatie van het plan, toonsoort of tempo |
| `take_out` | Maakt van een take die in een andere bewaard is een eigen take |
| `write_lyrics` | Een tekst vanuit een opdracht, met een nummervorm en toon, geschreven zoals Songtekst schrijven op de pagina het doet |
| `render_take` | Rendert een geplande take, of rendert een klare opnieuw (met een nieuwe seed als gevraagd) |
| `cancel_take` | Stopt een take in de wachtrij of in uitvoering |
| `make_stems`, `get_stems` | Splitst een take in partijen, en toont dan de partijen met een link naar elk en naar de hele set als zip |
| `list_recordings`, `transcribe_recording` | Toont de opnames in de bibliotheek en of elk een partituur heeft; transcribeert er een die er geen heeft |
| `list_style_loras` | De geïnstalleerde stijl-LoRA's, met hun triggerwoorden en de sterktes die ermee bewaard zijn |
| `list_spaces`, `move_take`, `create_space` | De ruimtes en wat erin zit; verplaatst een take naar een andere; maakt een nieuwe ruimte |
| `list_playlists`, `create_playlist`, `add_to_playlist`, `remove_from_playlist` | Afspeellijsten en de takes in een lijst; maakt er een; zet takes erin of haalt ze eruit |
| `make_picture` | Een nieuwe afbeelding voor een take, met een link die hem opent. `get_take` geeft ook de link naar de afbeelding van een take |
| `list_styles`, `save_style` | Je bewaarde en de ingebouwde stijlen, doorzocht op woorden; bewaart een stijl onder een naam |
| `star_take`, `rename_take` | Geeft een take een ster of haalt die weg; verandert zijn titel |
| `delete_take` | Verwijdert een take voorgoed, nadat hij hem je heeft getoond en je akkoord heeft gekregen |
| `save_take_recipe` | Het recept van een take, met links om het alleen of met de audio als één zip te downloaden, in het gevraagde formaat |
| `import_take` | Een nieuwe take uit een recept, in een ruimte als die genoemd is, klaar om te renderen; zegt welke LoRA's niet geïnstalleerd zijn en wanneer een cover als nummer binnenkwam |
| `status` | Of de engine klaar is, wat er loopt en wat er wacht, en of er een LoRA wordt getraind; noemt de engine die draait (ComfyUI of yue2.cpp) |

### Ideeën om het te gebruiken {#ideas-for-using-it}

- **Een reeks ideeën, en dan kiezen.** “Maak vijf EDM-instrumentals van een minuut in verschillende stijlen, in de ruimte EDM.” Hij start ze na
  elkaar en meldt het als elk klaar is. Jij luistert, en zegt dan “geef de tweede en vierde een ster en verwijder de rest”.
- **Doorwerken op één idee.** “Maak een instrumentaal in een dromerige synthstijl en speel het af”, dan “nu hetzelfde met meer drums”, en
  “geef me er nog vier zoals de tweede”. De agent houdt bij welke take welke is, dus je kunt erover praten op positie of
  op wat je erover zei.
- **Covers zonder klikken.** “Transcribeer *de demo*, en maak er dan drie covers van: folk, synthwave en jazz.” Hij transcribeert
  eerst de opname als die geen partituur heeft, en maakt dan de covers in de ruimte die je noemt.
- **Werken met een LoRA.** “Toon mijn stijl-LoRA's, en maak dan een instrumentaal met de jazz-LoRA.” Het triggerwoord en de bewaarde sterktes worden
  voor je geregeld, wat met de hand makkelijk misgaat.
- **Tekst van de agent, of van de app.** De agent kan de tekst zelf schrijven: “Schrijf een tekst over een nachttrein en maak er
  een folknummer van.” Yeufonic ziet alleen de klare tekst. Of vraag die van de app: “gebruik de tekstschrijver van Yeufonic, hiphopvorm,
  spreektoon”, die hem schrijft zoals **Songtekst schrijven** op de pagina doet en hem teruggeeft voor een nummer.
- **Zelfde melodie, andere tekst.** “Zing die nog eens met deze tekst voor het tweede couplet”: `new_words` houdt de melodie, toonsoort en tempo,
  waar een nieuw nummer vanuit de tekst een nieuwe melodie zou schrijven.
- **Instellingen vergelijken.** “Maak hetzelfde nummer twee keer, een keer met Vertrouwde en een keer met Avontuurlijke harmonie, met dezelfde seed”, dan
  “geef de betere nu elke interpretatie”. Instellingen worden bij naam gevraagd, dus je kunt een kleine test in één zin opzetten.
- **Afspeellijsten vanuit het luisteren.** “Zet alle takes met een ster van deze week in een afspeellijst met de naam Week 43”, of “haal de instrumentals uit
  Road trip”. Favorieten zijn de takes met een ster, dus de ster en de favorieten zijn altijd dezelfde lijst.
- **Stems voor een hele reeks.** “Splits mijn vijf nieuwste takes in zang en instrumenten en geef me de links.” Ze staan in de wachtrij achter
  elkaar, en achter elke render die de GPU draait.
- **De bibliotheek opruimen.** “Zoek de takes met dezelfde titel, zeg welke de nieuwste is, en verwijder de oudere”, of “verplaats alles
  wat ik vandaag maakte naar een ruimte met de naam Drafts”. Hij werkt op id en vraagt voor hij verwijdert.
- **Even checken voor een lange klus.** “Is Yeufonic bezig?” voordat je een lange render of reeks in de wachtrij zet, zodat je niet achter een training terechtkomt.
- **Deel van een grotere taak.** Omdat het een gereedschap is dat de agent kan aanroepen, kan het deel zijn van iets groters: een track voor een video maken en
  de notitie erbij schrijven, of een reeks zo groot als een afspeellijst opbouwen en de takes uit een lijst benoemen.

De agent kan een take niet horen, dus hij kan niet beoordelen hoe hij klinkt: jij luistert, en hij doet het zware werk. Het is ook geen
manier om de engine over te slaan: de GPU doet nog steeds één taak tegelijk, dus een grote reeks is een lange wachtrij.
- **Een take delen.** “Bewaar mijn take met ster met zijn recept als FLAC-zip” geeft een bestand dat een ander kan horen en opnieuw maken: die vraagt
  zijn agent om “dit takebestand te importeren en te renderen”. Of “importeer het opnieuw met de jazz-LoRA, zelfde partituur en seed”, om
  hetzelfde plan anders te horen.

### Goed om te weten {#things-to-know}

- **Takes kunnen dezelfde titel hebben,** dus de agent werkt met het **id** van een take en toont een kort id (de kolom `short_id`) als hij takes toont.
  Je kunt een take noemen met het begin van zijn id, vier tekens of meer, zolang maar één take zo begint. Als het er twee zijn, zegt hij dat
  en vraagt hij om meer.
- **Verwijderen vraagt twee keer.** De agent toont je eerst wat hij zou verwijderen, inclusief elke andere take met dezelfde titel, en verwijdert pas
  als je ja zegt. Een take met een ster heeft nodig dat je het uitdrukkelijk zegt. Een verwijderde take, met zijn audio, kan niet worden teruggehaald.
- **Ruimtes en stijl-LoRA's worden bij naam genoemd,** niet genummerd: “in de ruimte EDM”, “met de jazz-LoRA”. Een naam die nergens bij past krijgt de lijst
  van wat er is, en er wordt niets aangemaakt. Het triggerwoord van een LoRA wordt voor je aan de stijl toegevoegd, omdat een LoRA zonder weinig doet.
- **Een nieuwe take begint waar die van de pagina begint:** Harmonie op Gevarieerd en de interpretatie Breed, tenzij je andere noemt. Op een engine
  zonder de harmonienode begint hij op Vertrouwd, omdat Harmonie daar niet hoger kan.
- **Afbeeldingen en teksten wachten op hun beurt.** Een afbeelding die op deze computer wordt getekend of beschreven wacht tot er geen nummer wordt gemaakt, en teksten
  die op deze computer worden geschreven staan in de wachtrij met de rest van het GPU-werk, dus de agent kan zeggen “wordt nog gemaakt” en later nog eens kijken.
- **Een instrumentaal wordt altijd gepland met een getimede structuur,** berekend uit de lengte die je vraagt (zo'n tweeënhalve minuut
  als je niets zegt). Zonder tijden schrijft de planner plannen die te lang zijn om te gebruiken. Noem je eigen secties en ze worden zo gebruikt.
- **Alleen op deze computer.** Dezelfde controles op hostnaam en herkomst als op de pagina gelden, en er is geen inlog, dus zet de instelling
  uit als je hem niet gebruikt, en stel de poort niet bloot aan een netwerk dat je niet vertrouwt.

## Systeemlogs {#system-logs}

De app schrijft een samengevoegd, realtime log van elke belangrijke handeling — partituurplanning, renderen, audiotranscriptie, stems scheiden en LoRA-training — met de voorvoegsels `INFO`, `WARN` en `ERROR`.

- **Console in de browser:** klik op de knop **Logs** in de bovenbalk (of druk op **L**) om een zwevende console te openen, die je kunt verslepen en van grootte veranderen. Hij blijft open zonder de pagina te blokkeren, zodat je takes in de wachtrij kunt zetten en het genereren live kunt volgen.
- **Apart venster:** klik op **↗ Losmaken** in de kop van de console (of ga direct naar `/logs`) om een eigen logvenster te openen.
- **In de terminal:** logs roteren automatisch in `data/logs/yeufonic.log` op de host, waar je ze live kunt volgen:
  ```bash
  tail -f data/logs/yeufonic.log
  ```

## De eigen pagina van de engine {#the-engine-s-own-page}

De engine is ComfyUI (tenzij deze installatie yue2.cpp gebruikt, waarvan de pagina een eenvoudige testomgeving is), en zijn eigen interface is bereikbaar: <http://localhost:8189> met Docker, of
<http://localhost:8188> met de Windows-installatie (de `engine_port` in `settings.ini`). Hij antwoordt alleen
op deze machine, zonder inlog.

- **Het is dezelfde engine en GPU als de app.** Een taak die daar wordt gedraaid verschijnt in de wachtrij van de app als
  afkomstig van buiten, en de eigen taken van de app wachten erop.
- **Zijn geschiedenis toont elke graph die de app stuurde**: het plan, de render en de transcripties, met
  elke instelling zoals de engine hem ontving. Het is een goede plek om precies te zien waaruit een
  take is gemaakt.

---

## Als er iets misgaat {#when-something-is-wrong}

**De kop zegt dat de engine ontbreekt.** De app werkt zonder en zegt dat. Renders wachten.
Controleer of de enginecontainer draait.

**Een nummer houdt niet op.** Meestal te veel plannersterkte. Zet de Planner van de LoRA terug naar 0.5. De
lengtegrens stopt het toch wel.

**Een LoRA lijkt niets te doen.** Controleer of het triggerwoord in de Stijl staat, en of de sterkte die
je hoger zette er een is die het bestand echt heeft — de kiezer dimt de andere.

**Een take zegt *Zwakke render*.** Hij kwam van begin tot eind veel zachter uit dan normaal. Sommige takes
als deze zijn alleen zacht; andere klinken dun of vervormd. Klik op de melding om hem te normaliseren, wat
hem naar de gewone luidheid brengt en hem *Genormaliseerd* markeert. Als hij nog steeds slecht klinkt, probeer een andere
seed, en houd de Klank van die LoRA op 0.5 of lager. Het gebeurt vooral bij covers via een stijl-LoRA
die hier getraind is.

**Volume normaliseren.** Vink het aan in de editor en elke take die gemaakt wordt terwijl het aan staat wordt bij het afronden naar de
gewone luidheid gebracht, en gemarkeerd *Genormaliseerd*. Een take die zonder is gemaakt kan later worden genormaliseerd
met de luidsprekerknop bovenaan zijn kaart. Het bestand zoals gerenderd wordt ernaast bewaard, en
op *Genormaliseerd* klikken gaat ernaar terug. Hoe luid hij wordt stel je in Instellingen in, bij *Normaliseren naar*.
Uitgevinkt houdt een take het niveau waarop hij werd gerenderd.

**Een instrumentaal zong.** Zie *Als een instrumentaal zingt* hierboven. Het is een fout van het model; een nieuwe seed
lost het meestal op.

**Een take rendert niet opnieuw.** Misschien is zijn opname verwijderd. Covers houden hun audio en
partituur, maar kunnen niet opnieuw worden gerenderd vanuit een opname die er niet meer is.

**Er speelt niets, maar de golfvorm beweegt.** Controleer de volumeregelaar en of er geen stem geselecteerd is —
de speler volgt wat het laatst werd aangeklikt.
