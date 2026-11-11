# Yeufonic — das Handbuch

Hier geht es um die **Bedienung** der App. Die Installation und alles, was du brauchst, bevor sie läuft, steht in der
[README](https://github.com/yeufonic/yeufonic#readme).

Die App schreibt Songs mit YuE2, einem Modell, das in zwei Schritten arbeitet: Zuerst schreibt es einen **Partiturplan** —
Melodie, Akkorde und Abschnitte, als Text — und dann **rendert** es diesen Plan zu Audio.
Fast alles hier folgt aus dieser Aufteilung. Ein Plan kostet Sekunden und kann gelesen, bearbeitet und
verworfen werden; ein Rendering kostet Minuten. Deshalb lässt dich die App zuerst den Plan ansehen.

---

## Dein erster Song {#your-first-song}

1. Drücke **+ Song** oben im linken Bereich. Das Editorfenster öffnet sich.
2. **Gib einen Stil ein.** Einen Satz, keine Tag-Liste: *„warm indie rock, expressive female lead, jangly
   guitars, 96 BPM“*. Das ist der größte einzelne Einfluss auf das Ergebnis.
3. **Füge einen Songtext hinzu**, oder drücke **Songtext schreiben** und lass Gemma ihn aus einer Beschreibung entwerfen.
4. Drücke **Partiturplan schreiben**. Das Fenster schließt sich und der Take erscheint im linken Bereich. Ist
   **Rendern, sobald der Plan fertig ist** neben der Schaltfläche angehakt, wie zu Beginn, geht der Plan
   direkt weiter zum Rendering.

Um den Plan zu lesen, bevor etwas gerendert wird, entferne zuerst den Haken bei **Rendern, sobald der Plan fertig ist**. Der
Take hält dann bei seinem Plan an: Öffne ihn, und auf seiner Seite **Partitur** würfelt **Einen neuen Plan schreiben** eine Melodie, die dir
nicht gefällt, für ein paar Sekunden neu, und **Diese Partitur rendern** rendert sie. Ein Take ohne Audio wird
gefüllt; einer, der schon Audio hat, wird als neuer Take daneben gerendert, sodass ein Rendering nie etwas
überschreibt, das du vielleicht behalten willst.

Der Take erscheint rechts in der Bibliothek und spielt in der Leiste unten.

### Der Take-Bereich und der Editor {#the-take-panel-and-the-editor}

Der **linke Bereich** zeigt den zuletzt angeklickten Take, nur zum Lesen: seinen Stil, seine Klangeinstellungen, die
ersten Zeilen seines Textes und seine Partitur als Tonart, Tempo, Länge und die Akkorde jedes Abschnitts.
**+ Song**, **+ Cover** und **+ Instrumental** oben beginnen etwas Neues; die Schaltfläche für die
Art des Takes ist hervorgehoben. Der Pfeil neben dem Bereich klappt ihn weg, damit die Takes die Breite haben,
und holt ihn zurück. Einzelne Tasten wirken auf den Take, den der Bereich zeigt (M für das Mastering-Rack, E für
den Editor und mehr): siehe [Tastenkürzel](#hot-keys).

Einen Take erstellen und ändern geschieht im **Editorfenster**. Seine Hauptschaltfläche im Bereich sagt, was
passt: *Bearbeiten und erneut rendern*, oder *Plan prüfen und rendern*, wenn ein Plan wartet. Die Schaltflächen
**Partitur** und **Nochmal** einer Karte öffnen ihn auch, ebenso ein Doppelklick auf eine Karte. Er hat drei
Spalten (der Song, der Text und der Klang), alles im Blick, mit der Partitur auf einem eigenen Reiter.

Das Fenster mit **Schließen**, dem Kreuz oder Escape zu schließen, behält, was du getippt hast.

Die Schaltfläche nach **Schließen**, oben rechts, lässt das Fenster das ganze Browserfenster füllen, und
ein zweiter Klick bringt es auf die übliche Größe zurück. Das Fenster öffnet sich so, wie du es zuletzt verlassen hast. Füllt es das Fenster,
nimmt die Textspalte ihre ganze Höhe ein: Das Textfeld (sobald Wörter darin stehen) und die Struktur wachsen in
den Platz, und der Player bleibt am Fuß der Spalte.

Die obere Zeile des Fensters hat die kleinen Schaltflächen des Takes von seiner Karte, größer: Erneut singen, Variationen,
Mehr ausprobieren, Inhalt, Herausnehmen, Normalisieren und Verschieben, jede dort, wo die Karte sie zeigen würde. Normalisieren ist grün,
solange der Take normalisiert ist, und ein Klick bringt ihn dann auf den Pegel zurück, mit dem er gerendert wurde; Inhalt
leuchtet, solange der Take andere enthält, und schließt das Fenster, um sie unter dem Take zu zeigen.

### Eine aufgenommene Stimme {#a-recorded-voice}

Ein Take kann mit einer Stimme gesungen werden, die aus Aufnahmen eines Menschen trainiert wurde: deiner eigenen
oder der des Sängers eines Korpus. Stimmen legst du auf der Seite **Stimmen** im Menü an und verwaltest sie dort; im Feld
*Aufgenommene Stimme* des Editors wählst du eine, wenn du einen Take machst. Ein Take mit Stimme wird wie gewohnt gerendert;
dann wird sein Gesang getrennt, mit der Stimme neu gesungen und wieder über den Rest gemischt, bevor sein Pegel gemessen wird.
Dafür braucht es den optionalen Stimmendienst („Recorded voices“ in der README); ohne ihn ist das Feld ausgeblendet.

**Neue Stimme** legt entweder eine Stimme aus deinen eigenen Aufnahmen an oder eine, die mit den Songs eines Korpus
trainiert wird. Eine Stimme aus Aufnahmen beginnt leer, und ihre Seite sammelt sie: **Aufnehmen…** öffnet den Recorder, und
jeder Take, den du behältst, kommt so zur Stimme, wie er gesungen wurde, nie mit Autotune; **Hochladen…** nimmt Audiodateien;
**Aus der Bibliothek…** fügt Aufnahmen hinzu, die du schon hast, etwa einen Gesang, den du für ein Cover aufgenommen hast, mit
einem Player an jeder, um sie vorher anzuhören. Eine Aufnahme aus der Bibliothek wird verknüpft, nicht kopiert. Die Seite zählt
den Gesang gegen die Minuten, mit denen eine Stimme trainiert: etwa zehn Minuten über deinen ganzen Umfang reichen, und schon
eine kurze Aufnahme ergibt eine erkennbare Stimme. Jede Aufnahme sagt, ob sie reiner Gesang ist (**nur Gesang**, angehakt bei
dem, was du hier aufgenommen hast) oder ein Song, der zuerst getrennt wird. Dann drückst du **Trainieren**.

Das Training wartet auf der GPU, bis es an der Reihe ist, und zeigt seinen Fortschritt in der Job-Pille und im Protokoll.
**Erneut trainieren** trainiert mit den Aufnahmen, wie sie jetzt sind, oder mit den Songs des Korpus. Eine inzwischen aus der
Bibliothek gelöschte Aufnahme bleibt außen vor. Die Seite bewahrt **Woraus sie gelernt hat** auf, den getrennten Gesang jedes
Songs und die trainierten Ausschnitte, zum Anhören.

**Oktave** verschiebt die Stimme um eine ganze Oktave nach oben oder unten, für einen Sänger, dessen Umfang weit von dem des
Takes entfernt ist. **Gesangspegel** und **Instrumentenpegel** stellen das Verhältnis im neuen Mix ein, und **Ähnlichkeit**, wie
eng die Stimme beim eigenen Klang des Sängers bleibt: höher klingt ihm ähnlicher und kann bearbeiteter klingen. Bei 100 % kann die Stimme die Wörter verlieren: Sie behält nur die gelernten Laute, sodass Wörter, die der Sänger nie gesungen hat, verstümmelt herauskommen können; der Editor weist darauf hin. **Raum** legt
einen kurzen Raum unter den umgewandelten Gesang (*Trocken*, *Dezent* oder *Mehr*), damit er im Mix sitzt, und **Brillanz** auf
*Auto* hebt seine Höhen auf die des gerenderten Gesangs an; *Aus* lässt sie wie umgewandelt. **Atem und Konsonanten** legt fest,
wie weit diese die Laute des gerenderten Gesangs behalten: *Bewahrt* bleibt klar, trägt aber eine Spur davon, *Umgewandelt* kann
reißen. **Dynamik** legt fest, wessen Lautstärke der Gesang von Phrase zu Phrase folgt: der des Takes, wie gerendert, oder den
eigenen Schwellungen der Stimme. **Formant** ändert die Größe der Stimme bei gleicher Tonhöhe: *Tiefer* klingt größer, *Heller* kleiner. **Mischung** legt fest, wie viel des Gesangs die Stimme singt; der Rest ist der gerenderte Gesang, aus dem sie entstand. Das sind die Voreinstellungen der Stimme. Im Editor wählst du die Stimme unter **Aufgenommene Stimme**; **Einstellungen** daneben öffnet diese Einstellungen, um sie für einen Take zu ändern, und zeigt an, wenn der Take eigene hat. **Anhören** spielt dort die Stimme, die eine kurze Schleife singt, einen Mann oder eine Frau, mit den Einstellungen, wie sie sind, immer wieder, während du sie änderst, und **Als neue Stimme speichern…** behält, was du hörst, als eigene Stimme mit demselben Modell. Eigene Schleifen kommen dazu: Lege eine kurze Aufnahme einer einzelnen Stimme, trocken gesungen, 15 bis 30 Sekunden, in den Ordner *voice-loops* der Bibliothek (`data/voice-loops` mit Docker); sie erscheint mit ihrem Dateinamen, wenn **Einstellungen** das nächste Mal geöffnet wird. Gelesen werden FLAC, WAV, MP3, M4A, OGG und Opus. Einstellungen → *Stimmentraining* legt fest, aus wie viel Gesang eine Stimme lernt und mit wie vielen
Durchläufen.

Das Ergebnis ist ein umgewandelter Gesang über einer getrennten Begleitung, also weniger nahtlos als ein Gesang, den das Modell
selbst gesungen hat. Saubere, trockene Aufnahmen ergeben die sauberste Stimme. **Stimme herunterladen** speichert eine
trainierte Stimme als ZIP, um sie weiterzugeben, und **Stimme importieren…** fügt eine hinzu: diese ZIP oder ein RVC-Modell von
anderswo (seine ZIP oder seine .pth und .index zusammen ausgewählt). Eine ohne Index importierte Stimme bekommt ihn später mit **Index hinzufügen…**: Ähnlichkeit greift darauf zurück. Fertige Stimmen, von anderen trainierte RVC-Modelle, gibt es auf Seiten wie [voice-models.com](https://voice-models.com/): **Stimme importieren…** nimmt die ZIP so, wie sie heruntergeladen wurde. Das Rezept eines Takes nennt seine Stimme und die Einstellungen des Takes
dafür, und beim Import wird die Stimme dieses Namens auf dieser Installation verwendet, falls es sie gibt.

Eine Stimme lernt den Hall und die Produktion der Aufnahme mit dem Sänger zusammen, daher ergibt sauberer Gesang mit klarem Leadgesang eine sauberere Stimme als ein Korpus gemischter Lieder. Ein einzelnes Lied oder eine kurze Aufnahme ergibt eine erkennbare Stimme, die aber Wörter verwischen kann, die sie nie gesungen gehört hat. Eine Stimme, die auf viel mehr Gesang und mit viel mehr Durchgängen trainiert wurde, wie es fertige Stimmen oft sind, behält die Wörter auch bei hoher Ähnlichkeit.

### Erweiterte Einstellungen {#advanced-settings}

Die Schaltfläche **Erweitert** in der Kopfzeile des Editors öffnet Einstellungen nur für diesen Take. Die meisten Songs
brauchen sie nie. Sie werden mit dem Take gespeichert, sodass *Bearbeiten und erneut rendern* sie so vorfindet, wie du sie verlassen hast.
Die Schaltfläche leuchtet, wenn eine Einstellung von ihrem Standard abweicht, und **Auf Standard zurücksetzen** setzt
alle zurück.

Manche wirken auf den Plan, manche auf das Rendering und die fertige Datei:

- **Diffusionsschritte** (16–64, Standard 32): wie viele Schritte der Audio-Decoder macht. Mehr Schritte rendern
  länger.
- **Dem Stil folgen** (0–100, Standard 1.0): wie eng die Musik dem Stil und dem Text folgt, die Führung
  der Stufe, die die Partitur in Klang verwandelt (CFG). Über 1.0 neigt sie sich stärker zu ihnen hin; darunter weg davon. Der
  Unterschied ist bei kleinen Werten subtil, und ein Rendering dauert etwas länger. Jeder Wert, den die Engine annimmt, kann
  eingegeben werden: Sehr hohe Führung klingt eher harsch als näher. Es wird gezeigt, wenn die Engine es hat: yue2.cpp oder die ComfyUI-Engine
  in ihrer neueren Version (baue eine ältere Docker-Engine neu, um es zu bekommen).
- **Vermeiden:** Wörter, von denen weggesteuert werden soll, etwa „drums“ oder „rap vocals“. Sie werden dem Stil
  als „avoid: …“ hinzugefügt. Es ist ein Hinweis an den Planner, keine Garantie: Der Renderer hat keinen Negativ-Prompt.
- **Tonart festlegen:** Der Plan wird in diese Tonart verschoben, sobald der Planner ihn geschrieben hat. Der Planner ignoriert
  eine im Stil genannte Tonart, deshalb geschieht dies an der Partitur selbst: Jede Note und jeder Akkord verschiebt sich um
  dasselbe Intervall und die Vorzeichnung wird neu geschrieben. Ein Moll-Plan bleibt Moll, und nur der Grundton
  wandert. Ein Plan, den die App nicht sicher lesen kann, etwa einer in einer modalen Tonart oder mit einem Tonartwechsel
  mittendrin, bleibt in der Tonart des Planners, und das Log sagt es.
- **Tempo festlegen** (BPM): Der Plan wird auf dieses Tempo gesetzt, das jedes Tempo im Stil oder in der
  eigenen Partitur des Planners ersetzt, und das Rendering folgt ihm.
- **Token-Grenze der Partitur** (Standard 8192): das Meiste, was der Planner schreiben darf. Eine niedrigere Grenze verhindert, dass der Plan eines kurzen
  Songs weiterläuft.
- **Grenze für gehaltene Akkorde** (Takte, Standard 8): die meisten Takte, die der Planner auf einem Akkordgrundton bleibt, bevor
  er wechseln muss.
- **Bonus für tonartfremde Harmonik** (0–10, Standard 0): wie stark der Planner zu geborgten
  Akkorden und Grundtönen außerhalb der Grundtonart gedrängt wird. Diese beiden wirken auf die Entscheidungen des Planners, also zeigen sie sich als
  Unterschied in den Akkorden des Plans statt als klarer hörbarer Unterschied. Vergleiche das Fenster
  Partitur.
- **Stimmen folgen den Hinweisen** (ein Haken unter dem Textfeld, gezeigt, sobald der Text eine Stimmanweisung wie
  `[male voice]` hat; für einen neuen Take an): Die Melodie jeder angewiesenen Zeile wird um Oktaven dorthin verschoben, wo die Stimme, die ihre
  Anweisung nennt, gesungen wird. Siehe [Der Text](#the-words).
- **Dieser Struktur genau folgen** (ein Haken unter dem Textfeld, nicht in Erweitert; Songs; standardmäßig aus): Der Plan schreibt genau die Abschnitte, die der Text nennt, in
  dieser Reihenfolge, und keine anderen. Ausgeschaltet formt der Planner den Song selbst und fügt oft ein Intro, ein Outro oder ein
  Zwischenspiel hinzu oder lässt einen Abschnitt weg. Ein Plan kann trotzdem enden, bevor die Liste es tut.
- **Teile beginnen unterschiedlich** (Harmonie folgen, Immer, Nie): ob ein Abschnitt mit denselben
  Akkorden beginnen darf wie der davor. *Harmonie folgen* schaltet es ab Farbenreich ein und darunter aus; *Immer* und
  *Nie* entscheiden für diesen Take auf jeder Stufe, sodass zwei Pläne mit und ohne verglichen werden können.
- **Ziellautheit:** der Pegel, auf den ein Take normalisiert wird. Er gilt nur, wenn Normalisieren an ist.
- **Ausblenden am Ende** (Sekunden, Standard 3): die Länge der Ausblendung, wenn ein Take an der Längengrenze
  abgeschnitten wird.

### Was ins Stilfeld gehört {#what-to-put-in-the-style-box}

YuE2 liest dies als Beschreibung einer Aufnahme, also beschreibe eine Aufnahme. Sprache, Genre, Stimme,
Instrumente, Stimmung, Tempo und Produktion, ungefähr in dieser Reihenfolge, alles in einem Satz. Reine Tag-Listen
funktionieren schlechter, und Abschnittsmarken wie `[Verse]` gehören in den Text, nicht hierher.

Die Chips **Gesang** darunter schreiben für dich in den Stil: weiblich, männlich oder Duett, und einen Charakter
wie hauchig oder rau. Sie sind eine Abkürzung zum Tippen, und du kannst das Ergebnis von Hand bearbeiten.

### Den Songtext entwerfen {#drafting-the-lyrics}

**Die Struktur.** Über dem Textfeld hat ein Song, solange es keine Wörter enthält, eine **Struktur** zum Bauen, wie
ein Instrumental: eine Liste von Abschnitten, die du umsortieren, entfernen und ergänzen kannst (Intro, Strophe, Pre-Chorus, Refrain, Bridge,
Zwischenspiel, Outro). **Beginnen mit…** füllt sie mit einer gängigen Form, und der Tooltip jeder Form sagt, wozu sie passt. Ein
**Zwischenspiel** ist eine instrumentale Passage: Der Schreiber setzt seinen Tag auf eine eigene Zeile, und der Planner spielt es mit
der Instrumentenstimme. **Teile ins Songtextfeld setzen** setzt die Tags als leere Abschnitte ein, unter die du von Hand schreibst.
Sobald das Feld Wörter hat, wird der Text gesungen und die Struktur tritt zurück.

**Songtext schreiben** neben dem Textfeld fragt, worum es im Song geht, und schreibt Wörter für die Abschnitte, die du gebaut hast.
**Zeilen in einer Strophe oder einem Refrain** legt fest, wie lang jeder ist: Mehr Zeilen in einem Abschnitt ergeben einen längeren Song, weil der
Planner ungefähr so viel Musik schreibt, wie es Wörter gibt. Der Stil darüber bestimmt die Stimmung. Gemma schreibt den Entwurf auf derselben
Engine, und er landet im Feld, mit einem Titel, falls du keinen angegeben hattest; eine [externe LLM](#external-llm) kann ihn stattdessen schreiben, eingerichtet in den Einstellungen. Das Fenster schließt sich, sobald der Entwurf beginnt, und der Fortschritt erscheint neben dem Textfeld.
Die Schaltflächen des Texteditors fügen diese Abschnitte ebenfalls ein, dazu Stimmanweisungen (+ Männlich, + Weiblich, + Beide).

**Wie die Zeilen klingen** legt Rhythmus und Reim fest, die der Schreiber anstrebt. *Natürlich* (der Standard) mischt kurze und lange
Zeilen mit einigen Reimen. *Regelmäßiger Reim* ist die traditionelle Form gleichmäßiger Zeilen, die sich paarweise reimen, also das,
was der Schreiber vor dieser Wahl erzeugt hat. *Gesprochener Rhythmus* ist gesprächig, wie Sprache oder Rap; *Lockerer
Reim* reimt nur einige Zeilen; *Kurz und prägnant* und *Lang und fließend* bestimmen die Zeilenlänge.

Es ist ein erster Entwurf. Die Zeilen haben Metrum und Reim, aber ein Modell greift zu vertrauten Bildern, und nichts
prüft, ob eine Zeile schon jemand anderem gehört. Lies ihn und mach ihn zu deinem, bevor du planst.

---

## Einen Song aus einem Prompt schreiben: alle Optionen {#writing-a-song-from-a-prompt-every-option}

**+ Song** hat inzwischen viele Wahlmöglichkeiten. Keine davon ist nötig: Ein Stil und etwas Text genügen, wie in
[Dein erster Song](#your-first-song). Dieses Kapitel geht alle in der Reihenfolge durch, in der der Editor sie zeigt,
seine drei Spalten (der Song, der Text und der Klang), und dann, was nach dem Plan zu tun ist. Es endet mit einer
Tabelle für die häufigen Wünsche, etwa einen längeren Song oder einen Refrain, der anders klingt als die Strophe.

### Der Song {#the-song}

- **Titel.** Optional. Leer gelassen wird die erste Zeile des Textes verwendet.
- **Stil.** Die Liste **Einen Stil wählen…** enthält 200 Ausgangspunkte, von Afrobeats bis Zydeco, alphabetisch.
  Wählst du einen, füllt er das Stilfeld mit einer vollständigen Beschreibung, die du dann bearbeiten kannst. Die Chips darunter sind zehn schnelle
  Starts für einen Song: warm indie rock, soulful jazz-pop, synthwave, acoustic ballad, heavy rock, modern pop,
  country, hip hop, smooth R&B und dance pop. Siehe [Was ins Stilfeld gehört](#what-to-put-in-the-style-box).
- **Einen eigenen Stil speichern.** **Speichern** neben der Liste behält, was im Stilfeld steht, unter einem Namen, den du ihm
  gibst. Der erste Eintrag der Liste, **Gespeicherte Stile**, öffnet die gespeicherten; der Papierkorb daneben löscht einen, und die
  Suche der Liste findet sie zusammen mit den 200. Unter einem schon benutzten Namen zu speichern ersetzt diesen Stil. Das Triggerwort
  einer Stil-LoRA wird beim Speichern weggelassen und für die jeweils gewählte LoRA wieder eingesetzt, wenn du den Stil benutzt.
- **Ein Tempo im Stil ist nur ein Hinweis.** Der Planner wählt oft sein eigenes. Um das Tempo festzulegen, nutze **Tempo festlegen** in
  Erweitert.
- **Gesang.** Die Chips schreiben eine Stimme (weiblich, männlich, Duett und einen Charakter) für dich in den Stil.
- **Stil-LoRA.** Unter der Klangspalte. Siehe [Stil-LoRAs](#style-loras).

### Der Text {#the-words}

**Die Struktur.** Über dem Textfeld steht, solange es keine Wörter enthält, eine Liste von Abschnitten: die Reihenfolge, in der
der Song verlaufen wird. Jede Zeile kann in einen anderen Abschnitt geändert, nach oben oder unten verschoben (oder gezogen) oder entfernt werden, und die
Chips unter der Liste fügen einen Abschnitt hinzu. Die Abschnitte sind Intro, Strophe, Pre-Chorus, Refrain, Bridge, Zwischenspiel und Outro.
Ein **Zwischenspiel** ist eine instrumentale Passage: Es hat keine Wörter, und der Planner spielt es mit der Instrumentenstimme.
(`solo` ist kein Abschnitt, den der Planner kennt; Zwischenspiel ist der Weg, eines zu verlangen.)

**Beginnen mit…** füllt die Liste mit einer gängigen Form. Fahre über eine Option, um zu sehen, wozu sie passt:

| Form | Abschnitte | Passt zu |
|---|---|---|
| Strophe, Refrain, Bridge | Strophe, Refrain, Strophe, Refrain, Bridge, Refrain | der klassische Song: Pop, Rock, Country |
| Kurz | Strophe, Refrain, Strophe, Refrain | Folk, Punk, früher Rock 'n' Roll |
| Intro und Outro | Intro, Strophe, Refrain, Strophe, Refrain, Outro | Balladen, Soft Rock, Singer-Songwriter |
| Geschichte | Strophe, Strophe, Refrain, Strophe, Refrain, Outro | Erzähllieder, Folk, Country |
| Pop mit Pre-Chorus | Strophe, Pre-Chorus, Refrain, Strophe, Pre-Chorus, Refrain, Bridge, Refrain | moderner Pop, Dance-Pop, Pop-Rock |
| Hook zuerst | Refrain, Strophe, Refrain, Strophe, Refrain, Bridge, Refrain | Pop der Streaming-Ära, Indie-Pop |
| Kurz und einfach | Strophe, Refrain, Strophe, Refrain, Refrain | Punk, Garage Rock, Rockabilly |
| Hip-Hop | Intro, Strophe, Refrain, Strophe, Refrain, Strophe, Outro | Rap, Hip-Hop, Trap, R&B |
| Doppelte Bridge | Strophe, Refrain, Strophe, Refrain, Bridge, Bridge, Refrain, Refrain | Power-Balladen, Progressive und Symphonic Rock |
| Zwischenspiel | Strophe, Refrain, Zwischenspiel, Strophe, Refrain, Bridge, Refrain | Rock, Pop-Rock, Indie |
| Alle Teile | Intro, Strophe, Pre-Chorus, Refrain, Zwischenspiel, Strophe, Pre-Chorus, Refrain, Outro | Pop, Dance-Pop |

**Wie viele Abschnitte.** Der Planner schreibt meist 8 bis 10 Abschnitte, egal was der Text verlangt, also wird eine Liste, die länger
als 10 ist, verdichtet, und die Wörter der weggelassenen Abschnitte werden nicht gesungen. Der Baukasten sagt es, wenn die Liste
so lang ist. Ein Song wird durch mehr Abschnitte nicht länger; jeder wird nur kürzer. Siehe
[Den Song länger machen](#making-the-song-longer).

**Teile ins Songtextfeld setzen** setzt die Abschnitte als leere Tags ein, bereit, darunter von Hand zu schreiben. Sobald das Feld
Wörter hat, wird der Text gesungen, und der Baukasten tritt zurück.

**Songtext schreiben.** Beschreibe, worum es im Song geht, und ein Modell schreibt Wörter für die Abschnitte, die du gebaut hast. Es fragt nach
drei Dingen:

- **Zeilen in einer Strophe oder einem Refrain** (4, 6 oder 8; 6 ist der Standard). Mehr Zeilen in einem Abschnitt ergeben einen längeren Song,
  weil der Planner ungefähr so viel Musik schreibt, wie es Wörter gibt. Ein Intro, eine Bridge oder ein Outro bleibt bei 2 bis 4 Zeilen,
  und ein Zwischenspiel hat keine.
- **Wie die Zeilen klingen.** Die Liste zeigt die Silben, die jede Zeile anstrebt. Der alte Schreiber erzeugte fast jedes Mal dieselben
  achtsilbigen gereimten Zeilen, das hier ändert das:

| Wahl | Strebt an | Was du bekommst |
|---|---|---|
| Natürlich (der Standard) | 3-13 Silben | Eine Mischung aus kurzen und langen Zeilen, einige Reime, kein gleichmäßiger Takt |
| Regelmäßiger Reim | 6-10 Silben | Gleichmäßige Zeilen, die sich paarweise reimen: die traditionelle Form und das, was der Schreiber früher tat |
| Gesprochener Rhythmus | 5-14 Silben | Gesprächig und rhythmisch, wie Sprache oder Rap, mit Binnenreimen |
| Lockerer Reim | 4-13 Silben | Einige Reime, einige unreine Reime, einige keine, und Zeilen unterschiedlicher Länge |
| Kurz und prägnant | 3-6 Silben | Kurze Zeilen und wiederholte Phrasen |
| Lang und fließend | 10-14 Silben | Lange Zeilen, die wie ein Gedanke weiterlaufen |

  Die letzte Wahl wird gemerkt. Das sind Ziele, keine Garantien: Ein Sprachmodell folgt ihnen eng bei den
  Extremen (kurz und prägnant, lang und fließend) und lockerer bei den feinen.
- **Die Aufgabe** selbst, in deinen eigenen Worten, und der Stil darüber, der die Stimmung bestimmt. Die Aufgabe wird mit dem Take gespeichert,
  sodass das Öffnen eines Takes und Drücken von **Songtext schreiben** zeigt, worum es gehen sollte, bereit zum Ändern und erneuten Schreiben.

Der Entwurf landet im Textfeld, und das Fenster schließt sich, sobald er beginnt. Es ist ein erster Entwurf: Lies ihn und mach ihn zu
deinem.

**Dieser Struktur genau folgen** (der Haken unter dem Textfeld, standardmäßig aus). Der Planner behandelt die Abschnitts-
Tags im Text als Orientierung, und sich selbst überlassen schreibt er seine eigene Form: Er fügt oft ein Intro und ein Outro hinzu,
tauscht eine Bridge gegen ein Zwischenspiel und eine Strophe oder verdichtet eine lange Liste. Ist dies an, schreibt der Plan genau die
Abschnitte, die der Text nennt, in dieser Reihenfolge, und keine anderen. Er kann kein Intro oder Outro hinzufügen, das du nicht
aufgeführt hast. Der Planner entscheidet weiterhin, was die Musik ist und wann jeder Abschnitt beginnt. Es gilt nur für Songs.

**Wer singt welche Zeile: Stimmanweisungen.** Eine Zeile für sich in eckigen Klammern, die eine Stimme nennt, sagt, wer die
Zeilen darunter singt, bis zur nächsten Anweisung oder zum nächsten Abschnitt:

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

Schreibe eine Anweisung als `[male voice]`, `[female voice]` oder `[both voices]`, jede auf einer eigenen Zeile in eckigen Klammern.
Der erweiterte Texteditor hat die Schaltflächen **+ Männlich**, **+ Weiblich** und **+ Beide** in seiner Kopfzeile, um sie am Cursor einzufügen.
Das sind die Formen, mit denen die Funktion erprobt wurde, dazu `vocal` für `voice` (`[female vocal]`) und
`[male and female voices]` für beide. Du kannst nach einem Komma eigene Wörter anfügen, wie in
`[female voice, soft and close]`; sie ändern nicht, wer singt. Ein Abschnitt ohne Anweisung bleibt dem Planner überlassen.

Andere Schreibweisen werden ebenfalls gelesen, damit anderswo geschriebene Texte nicht ignoriert werden: `[man]`, `[woman]`, `[duet]`, eine Anweisung
im Tag eines Abschnitts wie `[Verse 2 - female vocal]` und eine Anweisung in runden Klammern, `(female voice)`. Eckige
Klammern sind die sicherere Gewohnheit: Wörter in runden Klammern sind meist Backgroundgesang und werden womöglich gesungen.

Eine Anweisung allein bestimmt die Stimme nicht. Wer singt, ergibt sich vor allem daraus, wie hoch die Melodie geschrieben ist: Dieselbe
Zeile eine Oktave höher singt eine Frau, und der Planner schreibt eine Strophe gern in zwei Oktaven, mit Wechsel etwa alle vier
Zeilen, egal wer angewiesen wurde. **Stimmen folgen den Hinweisen** (ein Haken unter dem Textfeld, gezeigt, sobald der Text
eine Anweisung hat; für einen neuen Take an) hält die Anweisungen ein: Wenn der Plan geschrieben wird, wird jede angewiesene Strecke der Melodie um
ganze Oktaven dorthin verschoben, wo diese Stimme singt, tief für einen Mann und hoch für eine Frau. Sonst ändert sich nichts am Plan. Es
geschieht vor jedem Rendering erneut, folgt also einer Änderung am Text oder an der Partitur. Auf der Seite Partitur
tut **Stimmen nach Hinweisen** dasselbe einmal an der Partitur im Feld, für einen Take, der ohne den Haken gemacht wurde; speichere die Partitur
und rendere sie.

Drei Dinge, die man wissen sollte:

- **Wer eine Zeile singt, ist immer noch teils Zufall.** Mit der Melodie an der richtigen Stelle gehen die meisten Zeilen an die angewiesene
  Stimme, aber ein Rendering kann trotzdem eine an die andere Stimme geben. Rendere erneut mit einem anderen Seed, oder nutze
  **Mehr versuchen**.
- **Beide** setzt die Zeile dorthin, wo eine Frau singt, und überlässt die zweite Stimme dem Rendering, das oft eine
  im Refrain einbringt. Es bittet um ein Duett, statt eines zu machen: Wie viel von der zweiten Stimme du hörst, ändert sich von
  Rendering zu Rendering. Es gibt noch keinen Weg, zwei Sänger auf einer Zeile zu schreiben, ohne dass der Text leidet.
- Ein Take, der gemacht wurde, bevor es diesen Haken gab, behält seine Partitur, wie sie war; setze den Haken oder nutze **Stimmen nach Hinweisen**, um ihn anzupassen.

**Von Hand schreiben.** Die Schaltfläche Aufklappen öffnet einen Editor in voller Größe mit Schaltflächen für Intro, Strophe, Pre-Chorus,
Refrain, Bridge, Zwischenspiel, Outro und Instrumental. Ein Abschnitt ist eine Zeile wie `[Verse]`, gefolgt von seinen Zeilen; ein
Tag ohne Zeilen darunter, wie `[Interlude]`, ist eine instrumentale Passage.

### Der Klang {#the-sound}

- **Harmonie** (der Schieberegler): wie abenteuerlich die Akkorde sind. Ein neuer Song beginnt bei **Abwechslungsreich**, mit der Interpretation
  auf **Weit**: In unseren eigenen Tests ergab dieses Paar die musikalisch interessantesten Versionen, also ist es ein guter Anfang. Verstelle
  beides nach Geschmack. Bestehende Takes behalten, womit sie gemacht wurden. Sich selbst überlassen schreibt der Planner gern eine Vier-Akkord-
  Schleife und nutzt sie für jeden Abschnitt, und jede Stufe schiebt ihn ein Stück weiter davon weg. Die Stufen bauen aufeinander
  auf:

  | Stufe | Was sie mit den Akkorden macht | Greif dazu, wenn |
  |---|---|---|
  | Vertraut | Nichts: die eigenen Akkorde von YuE2, oft eine Schleife für den ganzen Song | Dir die erste Idee des Planners gefällt oder du die schlichteste Begleitung willst |
  | Abwechslungsreich | Hält davon ab, genau die gerade benutzten Akkorde zu wiederholen, färbt sie also um (ein F, dann ein Fmaj7), bleibt aber in der Tonart | Die Schleife sich zu gleichförmig anfühlt und der Song konventionell bleiben soll |
  | Farbig | Dasselbe, stärker: Strophe und Refrain gehen getrennte Wege, mit reicheren Akkorden. Ein Abschnitt darf außerdem nicht mit denselben Akkorden beginnen wie der davor, also beginnt ein Refrain nicht mehr so wie seine Strophe | Der Refrain sich wie ein Aufschwung anfühlen soll, nicht wie eine Wiederholung. Ein guter erster Schritt nach oben |
  | Abenteuerlich | Hält von kürzlich benutzten *Grundtönen* ab, nicht nur Schreibweisen, sodass die Harmonie wandern muss, und sie borgt Akkorde von außerhalb der Tonart | Du Bewegung und Überraschung willst und auf einen Akkord achtest, der seltsam klingt |
  | Außerhalb | Abenteuerlich, mit einem Zug zu Akkorden außerhalb der Tonart | Experimente. Rechne damit, manche Pläne zu verwerfen |

  Ab Farbenreich fallen die Akkordwahlen von Abschnitt zu Abschnitt deutlicher verschieden aus: mehr verschiedene Akkorde in einem
  Song, mehr Vier-Takt-Muster, die keine Wiederholungen sind, und weniger Refrain, der den Anfang der Strophe kopiert. Der Plan ist
  immer noch ein normaler Song, also lohnt es sich, eine oder zwei Stufen höher zu probieren, bevor man zu einer wilderen Planvielfalt greift.
  Unter **Erweitert** kann **Teile beginnen unterschiedlich** auf *Immer* oder *Nie* gesetzt werden, um einen Plan mit und ohne
  die Refrain-Regel zu probieren; der Standard, *Harmonie folgen*, ist ab Farbenreich an. Ein Stil wie Trap oder Ambient ist oft
  von Natur aus schleifenbasiert, also erwarte dort eine kleinere Änderung als bei Pop oder Rock. Siehe [Harmonie](#harmony) für die Messungen.
- **Planvielfalt.** Wie frei der Planner alles andere schreibt. Siehe [Planvielfalt](#plan-variety).
- **Interpretation.** Wie die Noten beim Rendern gespielt werden. Siehe [Interpretation](#interpretation).
- **Längenbegrenzung.** Das späteste Ende des Songs. Siehe [Länge](#length).
- **Modus.** *Voll* behält die Akkorde des Plans; *Melodie* lässt die Begleitung frei. *Keine Partitur*, für Songs, schreibt
  überhaupt keinen Plan: siehe [Ein Song ohne Partitur](#a-song-with-no-score).
- **Seed** und **diesen Seed behalten**. Siehe [Seed, und einen Take reproduzieren](#seed-and-reproducing-a-take).
- **Produktionsschliff** und **Lautstärke normalisieren.** Siehe [Produktionsschliff](#production-polish).
- **Rendern, sobald der Plan fertig ist**, neben der Schaltfläche am Fuß des Fensters, führt Plan und Rendering
  ohne Halt dazwischen aus. Es ist zu Beginn angehakt, und der Editor merkt sich deine Wahl. Entferne den Haken, um den
  Plan zuerst zu lesen.
- **Erweitert** (die Schaltfläche in der Kopfzeile): Diffusionsschritte, Dem Stil folgen, Vermeiden, Tonart fixieren, Tempo fixieren, die längste Partitur,
  Akkord-Haltegrenze, Bonus für Harmonie außerhalb, Abschnitte beginnen unterschiedlich, Ziellautheit und die Ausblendung am Ende. Siehe
  [Erweiterte Einstellungen](#advanced-settings).
- **Mastering** (die Schaltfläche links davon, wenn der Take Klang hat) öffnet das Mastering-Rack über dem Editor für
  den Take darin. Das Rack ist, in dieser Reihenfolge, ein EQ im Stil des 1073, ein parametrischer Equalizer, ein Kompressor, ein Stereo-Imager und
  ein Limiter. Im Diagramm des parametrischen Equalizers ist jedes der sieben Bänder ein Punkt: Zieh ihn seitlich für seine Frequenz
  und hoch oder runter für seine Verstärkung, dreh das Mausrad darüber für seine Breite, doppelklicke, um ihn zurückzusetzen. Die Leiste unter
  dem Diagramm legt die Art des gewählten Bands fest (Low Cut, Low Shelf, Glocke, Notch, High Shelf, High Cut) und schaltet es ein
  oder aus, **Flach** setzt jedes Band auf 0 dB zurück, und die Schaltfläche in der Ecke des Diagramms ändert, wie viele Dezibel das
  Diagramm zeigt. Die Schaltfläche ist grün, solange das Rack den Klang des Takes verändert. Bei offenem Rack spielt die Leertaste
  den Take und pausiert ihn, und die Pfeiltasten bewegen sich darin und stellen die Lautstärke ein, wie auf der Hauptseite. Escape schließt
  das Rack, und erneut den Editor.
- **3D-Raum**, ein Modul des Racks zwischen Imager und Limiter, setzt den Take für Kopfhörer um dich herum. Aus dem **Mix**: zwei virtuelle Lautsprecher vorn (**Width**) und zwei hinten (**Rear**); **Surround** bestimmt, wie viel von der Breite und dem Raumanteil des Mixes aus den hinteren kommt; die Lautsprecher lassen sich auch auf dem Kreis ziehen. **Height** hebt sie alle an, **Room** fügt einen kurzen Raum hinzu. Aus **Stems**: Jeder Stem des Takes wird für sich platziert; wähle einen unter dem Kreis, ziehe dann rund um den Kreis, um ihn zu platzieren, und das Mausrad fächert ihn auf (**Stems erstellen** öffnet das Stems-Fenster, wenn der Take keine hat). **Front**, **Wide** und **Around** stellen alles auf einmal ein. Was du hörst, ist für Kopfhörer und nie Teil der eigenen Datei des Takes: **Herunterladen** unter Kopfhörer speichert es als WAV, und **FLAC** und **AC-3** unter 5.1-Lautsprecher speichern den Take für Surround-Lautsprecher (aus Stems geht jeder an die Lautsprecher beiderseits seiner Position). Das Speichern-Fenster des Takes bietet dieselben Downloads, solange sein Raum an ist. Jedes Modul lässt sich mit dem Pfeil links in seiner Leiste einklappen, und der Take merkt sich, welche eingeklappt sind.

### Den Song länger machen {#making-the-song-longer}

Die Länge eines Songs bestimmt sein Plan, und das Rendering folgt der Länge des Plans. Diese Dinge verändern sie:

| Um zu bekommen… | Tu dies |
|---|---|
| Einen längeren Song | Gib jedem Abschnitt mehr Zeilen (**Zeilen in einer Strophe oder einem Refrain**: 6 oder 8) |
| Einen langsameren, längeren Song | Setze **Tempo festlegen** in Erweitert. Derselbe Plan bei niedrigerem BPM läuft länger |
| Einen längeren Song durch mehr Abschnitte | Das funktioniert nicht: Ein Plan hat etwa 8 bis 10 Abschnitte, also werden mehr nur kürzer oder verdichtet |
| Mehr, als der Plan erlaubt | Schreibe einen neuen Plan; die Längen schwanken zwischen Durchläufen mit demselben Text stark |
| Einen Song, der am Ende seines Textes aufhört | Erhöhe die Längengrenze nur, wenn er abgeschnitten wird; die Grenze ist ein Limit, kein Ziel |

### Nach dem Plan {#after-the-plan}

- **Diese Partitur rendern** macht einen neuen Take, sobald der offene Take schon Audio hat, sodass ein Rendering nie einen überschreibt,
  den du vielleicht vergleichen willst. Ein Take ohne Audio wird gefüllt.
- **Diese Melodie behalten** (nachdem du den Text eines Takes geändert hast): singt die Partitur des Takes mit dem neuen Text, als neuen Take. Die
  Melodie kann keine Abschnitte oder Noten dazugewinnen, also wenn dein Text mehr Abschnitte hat als die Melodie, oder viel mehr oder viel weniger
  Silben als sie Noten hat (lange Zeilen auf einer Melodie für kurze oder kurze Zeilen auf einer für lange), entfernt sich der
  Haken selbst und ein neuer Plan wird geschrieben, mit einer Zeile, die sagt warum. Siehe [Dieselbe Melodie, neuer Text](#same-tune-new-words).
- **Die Bibliothek filtern.** Die Schalter **Song**, **Cover** und **Instrumental** neben den Filtern zeigen nur diese
  Arten im offenen Bereich; wähle mehrere oder keinen für alle Arten.

---

## Den Plan lesen und reparieren {#reading-and-fixing-the-plan}

Der Plan ist in **ABC-Notation** geschrieben: Musik als reiner Text, Buchstaben statt Punkten auf Notenlinien.
Chris Walshaw hat sie Anfang der 1990er erfunden, um Folk-Melodien per E-Mail zu verschicken, und sie hat sich gehalten.

Du musst sie nicht lesen können. Die App zeigt denselben Plan als **Akkordtabelle** und als echte **Noten**
unter dem Editor, und **Vergrößern** öffnet alles in voller Größe. Aber der Text ist das, was YuE2
geschrieben hat und woraus es rendert, also lohnt es sich, sich darin zurechtzufinden.

### Einen Plan lesen {#reading-a-plan}

Ein Plan beginnt mit einem Kopf, ein Buchstabe und ein Doppelpunkt pro Zeile:

```
X:1
M:4/4
L:1/32
Q:1/4=120
V: Vocal clef=treble name="Vocal Melody"
V: Ins   clef=treble name="Ins Melody"
K:D#m
```

| Zeile | Bedeutet |
|---|---|
| `X:1` | die Nummer der Melodie. Jede ABC-Datei beginnt mit einer |
| `M:4/4` | das Metrum — vier Schläge pro Takt |
| `L:1/32` | die Grundlänge: ein bloßer Buchstabe dauert eine Zweiunddreißigstelnote |
| `Q:1/4=120` | das Tempo — eine Viertelnote bei 120 Schlägen pro Minute |
| `V:` | deklariert eine Stimme. YuE2 schreibt zwei, eine Gesangs- und eine Instrumentallinie |
| `K:D#m` | die Tonart, dis-Moll. `K:` steht immer zuletzt im Kopf |

Dann die Musik selbst:

```
% intro
V: Vocal
z24z4"D#m"z4|"D#m"z32|
V: Ins
Z|d16a16-|a16g8a8|
```

- **Noten sind Buchstaben.** `d16` ist ein D, das 16 Einheiten dauert. Kleinbuchstaben liegen eine Oktave über Großbuchstaben,
  und `'` oder `,` verschieben sie weiter.
- **`-` bindet** eine Note an die nächste, sodass sie wie eine klingen.
- **`z` ist eine Pause**, mit einer Länge wie eine Note. Ein großes `Z` pausiert einen ganzen Takt.
- **Akkorde stehen in doppelten Anführungszeichen**, wie `"D#m"`, und stehen vor der Note, auf der sie beginnen. Diese
  bearbeitet **Suchen und Ersetzen**.
- **`|` ist ein Taktstrich**, und **`%` beginnt einen Kommentar** — so werden die Abschnitte markiert:
  `% intro`, `% verse`, `% chorus`.

Dieses Fragment sagt also: dis-Moll, Viervierteltakt, 120 Schläge pro Minute, und durch das Intro pausiert der
Gesang und trägt dabei den Akkord, während das Instrument ein gebundenes D und A spielt, dann G und A.

Zwei praktische Folgen. **Akkorde zu bearbeiten ist sicher**, auch wenn die Noten undurchsichtig wirken — es sind nur
die Teile in Anführungszeichen, und alles andere kann bleiben, wie es ist. Und **wenn du den Plan bearbeitest, nutzt das Rendering,
was du bearbeitet hast**, also ist das Reparieren eines Plans meist schneller, als neu zu würfeln, bis ein guter erscheint.

### Ihn hören {#hearing-it}

Der Reiter **Notation** hat einen Player über den Notenzeilen. Drücke **Abspielen**, um den Plan so zu hören, wie das Feld
ihn hat, samt Änderungen, sodass eine Melodie, bei der du unsicher bist, nach Gehör beurteilt werden kann, bevor ein Rendering
für sie verbraucht wird. Die Noten, die er spielt, werden dabei hervorgehoben, und sein Temporegler ändert nur die Vorschau,
nicht die Partitur. Das Abspielen stoppt, was die Player-Leiste hatte, da zwei Dinge gleichzeitig niemandem
nützen, und das Schließen des Fensters — oder der Wechsel zu Akkorde oder Text — stoppt ihn auch, damit nichts
weiterspielt, ohne dass ein Regler erreichbar ist.

**Instrumente** spielt jede Stimme mit einem Instrument, das der Stil nennt, statt durchgehend mit einem Klavier:
Ein Stil, der *electric guitar, drums* sagt, wird mit einer Gitarre gehört, ihre Akkorde von
einer anderen gespielt und ein Bass darunter; eine gesungene Linie wird durch eine Stimme vertreten, die Melodie eines Instrumentals
nicht. Ein Stil, der Schlagzeug nennt, bekommt auch eine Schlagzeugspur, geschrieben im eigenen Metrum der Partitur
— ein Backbeat für Rock, Four-on-the-floor für Dance, ein Ride für Jazz, etwas Spärlicheres für eine
Ballade — und sie spielt durchgehend, da die Partitur keine Abschnitte hat, in denen sie aussetzen könnte. Die
Zeile neben dem Player sagt, was er gewählt hat, und das Entfernen des Hakens kehrt zu dem Klavier zurück, das du
sonst hören würdest. Das ist eine Lesart des Stils, nicht des Renderings: YuE2 entscheidet die
echte Darbietung und fügt Stimmen hinzu, die die Partitur nie hatte, also betrachte es als den Plan in den richtigen
Farben gespielt, nicht als das, wie der Take klingen wird.

**MIDI herunterladen** speichert die Partitur für eine DAW. Jede Stimme ist eine eigene Spur, auf ihrem eigenen Kanal,
mit dem Instrument, das die Vorschau benutzt hat, auf diesem Kanal eingestellt: die Gesangslinie, die Instrumentallinie und,
sofern du den Haken bei **Akkorde** nicht entfernst, die Akkordsymbole als Akkordstimme mit ihrem Bass daneben (die einzige
Stelle, an der die Harmonie als Noten geschrieben ist), und Schlagzeug auf Kanal 10, wenn der Stil danach fragt. Die
Instrumente sind General-MIDI-Programmnummern, also spielt deine DAW sie mit ihren eigenen Klängen, und
Tempo und Metrum stehen in der Datei. Ein Plan, der sein Metrum mittendrin ändert, wird im Metrum geschrieben, mit dem er
beginnt — nur dieses wird festgehalten —, während die Noten ihre eigenen Längen behalten. Ein Klick auf eine Note in
den Notenzeilen setzt den Cursor auf das ABC, das sie geschrieben hat.

Eine Partitur mit einer Note über dem, was diese Instrumente spielen können, oder darunter, wird um ganze
Oktaven verschoben gespielt, bis sie passt, und die Zeile neben dem Player sagt, wie weit; die Notenzeilen, die MIDI-Datei und
die Partitur selbst bleiben unverändert. Die Instrumente sind nicht alle gleich groß — ein Bass endet weit unter
einem Klavier —, deshalb gibt es die Zeile, wenn eine Partitur verschoben wird. Eine Partitur, die noch keine Noten hat,
hat nichts zu spielen und sagt es.

Der Player braucht seine Notensamples, die nicht Teil der App sind: Jedes Instrument hat etwa 7 MB,
wird beim ersten Abspielen einer Vorschau damit von seiner ursprünglichen Quelle geholt und in der Bibliothek behalten, sodass
es danach offline funktioniert. **Abspielen** holt, was die aktuelle Partitur braucht, und startet dann, und
**Klänge laden** holt dasselbe, ohne abzuspielen, für alle, die es lieber vorher bereit
haben.

### Die Pianorolle {#the-piano-roll}

Klicke im Partiturfenster auf **Piano Roll**, um den visuellen MIDI-Editor zu öffnen. Statt rohe ABC-Buchstaben zu bearbeiten, siehst und formst du die Melodie direkt auf einem interaktiven Raster aus Tonhöhe und Zeit.

Der Editor zeigt beide Partiturstimmen gleichzeitig — **Vocal** (die gesungene Hauptmelodie in Himmelblau) und **Ins** (die instrumentale Begleitung in warmem Bernstein). Beide Stimmen sind immer voll aktiv, sichtbar, auswählbar und bearbeitbar. Die Schaltflächen **Zeichnen** oben links wählen, welcher Stimme neue Noten zugeordnet werden, wenn du klickst, um Noten hinzuzufügen.

#### Noten bearbeiten {#editing-notes}

- **Eine Note hinzufügen:** Klicke auf eine leere Zelle im Raster, um eine Note bei dieser Tonhöhe und Zeit zu erzeugen. Die Note erklingt sofort, sodass du ihren Ton hörst.
- **Noten auswählen:** Klicke auf eine Note, um sie auszuwählen. Halte <kbd>Shift</kbd> oder <kbd>Ctrl</kbd>/<kbd>Cmd</kbd> beim Klicken, um mehrere Noten in Gesangs- und Instrumentalstimme auszuwählen. Klicke und ziehe einen **Auswahlrahmen** über leeren Rasterbereich, um eine Phrase oder Passage über alle Stimmen hinweg auszuwählen. Drücke <kbd>Ctrl</kbd>+<kbd>A</kbd> (<kbd>Cmd</kbd>+<kbd>A</kbd> unter macOS) oder klicke **Alle auswählen**, um alle Noten der ganzen Partitur auszuwählen. Um alle Noten vom Abspielcursor bis zum Ende des Songs auszuwählen, drücke <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>A</kbd> oder <kbd>Alt</kbd>+<kbd>A</kbd> (oder klicke **Ab Cursor ▶** in der Werkzeugleiste).
- **Noten verschieben:** Ziehe eine ausgewählte Note, um ihr Timing früher oder später zu legen, oder ziehe senkrecht, um ihre Tonhöhe zu transponieren. Wenn mehrere Noten ausgewählt sind — Gesang, Instrument oder beides —, bewegen sie sich alle gemeinsam im Gleichschritt und behalten ihr relatives Timing, ihre Melodien und ihren Text.
- **Länge ändern:** Ziehe den rechten Rand einer Note, um ihre Dauer zu verlängern oder zu verkürzen. Die Auswahl **Raster** (1/16, 1/8 oder 1/4 Note) beschränkt Verschieben und Längenänderung auf saubere musikalische Einteilungen.
- **Noten löschen:** Doppelklicke eine Note, um sie zu löschen, oder wähle eine oder mehrere Noten aus und drücke <kbd>Delete</kbd> oder <kbd>Backspace</kbd>.
- **Rückgängig und Wiederholen:** Jede Bearbeitung, Verschiebung, Längenänderung, Hinzufügung und Löschung einer Note wird im Verlauf festgehalten. Drücke <kbd>Ctrl</kbd>+<kbd>Z</kbd> (<kbd>Cmd</kbd>+<kbd>Z</kbd>) zum Rückgängigmachen und <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>Z</kbd> oder <kbd>Ctrl</kbd>+<kbd>Y</kbd> zum Wiederholen.
- **Tasten anhören:** Klicke auf eine Taste der Klaviertastatur links, um ihre Tonhöhe zu hören.
- **Maximieren:** Klicke **Maximieren** in der oberen Werkzeugleiste, um die Pianorolle auf die volle Breite deines Browserfensters zu erweitern.

#### Zeitleiste, Abschnitte und Akkorde {#timeline-sections-and-chords}

Entlang des oberen Lineals zeigt die Zeitleiste Taktnummern und Abschnittsgrenzen:
- **Abschnitte umbenennen:** Klicke auf eine Abschnittsmarke (`intro`, `verse`, `chorus` usw.), um ihren Namen zu bearbeiten oder sie neu zuzuordnen.
- **Akkorde bearbeiten:** Direkt unter dem Taktlineal zeigt die Akkordspur die harmonische Folge des Songs. Klicke auf eine vorhandene Akkordmarke, um sie umzubenennen (zum Beispiel `C` in `Am7` oder `G/B`), oder klicke auf einen leeren Takt, um einen neuen Akkord zu setzen.
- **Leere Takte harmonisieren (Lücken füllen):** Klicke **Lücken füllen** in der Werkzeugleiste, um leere Takte der instrumentalen Begleitspur mit Noten zu füllen, die aus der Akkordfolge erzeugt werden.
- **Leere Takte entfernen (Lücken schließen):** Klicke **Lücken schließen**, um stille leere Takte in beiden Stimmen zu entfernen und nachfolgende Noten und Akkorde nach links zu schieben, damit keine ungewollten Lücken im Arrangement bleiben.

#### Text und Karaoke-Verfolgung {#lyrics-and-karaoke-tracking}

Unten in der Pianorolle richtet eine eigene Textspur jede Silbe an der Gesangsmelodie aus:
- **Phrasenbewusste Zuordnung:** Klicke **Text zuordnen**, um den Text über die Gesangsmelodie zu verteilen. Die Ausrichtung erkennt natürliche Atempausen und Pausenlücken zwischen melodischen Phrasen und ordnet jede Textzeile ihrer vorgesehenen Phrase zu, ohne Wörter über Pausen hinweg in nachfolgende Takte zu verschütten. Mehrsilbige Wörter teilen sich sauber auf Noten auf.
- **Silben bearbeiten:** Klicke auf eine Textmarke (oder wähle eine Gesangsnote und drücke <kbd>L</kbd>), um ihren Text zu bearbeiten. Gibst du durch Leerzeichen oder Bindestriche getrennte Silben ein (zum Beispiel `Hel- lo world`), verteilen sie sich automatisch auf aufeinanderfolgende Gesangsnoten.
- **Hervorhebung beim Überfahren:** Das Überfahren einer Textmarke hebt die zugehörige Note im Raster hervor, und das Überfahren einer Gesangsnote hebt ihre Textmarke darunter hervor.
- **Karaoke-Ball:** Beim Abspielen hüpft ein animierter Ball über jede Note, während sie gesungen wird, und die aktive Silbe und die Rasternote leuchten in Echtzeit auf.

#### Abspielen und Harmoniebegleitung {#playback-and-harmony-accompaniment}

Drücke <kbd>Space</kbd> oder klicke **▶ Abspielen**, um ab dem Abspielcursor abzuspielen. Die Abspiellinie wandert über das Raster und aktualisiert den aktuellen Takt, Schlag und die verstrichene Zeit.

- **Hörbarer Klick (Metronom):** Das Abspielen enthält standardmäßig einen hörbaren Klick, mit einem betonten Woodblock-Klick auf Schlag 1 jedes Takts und leiseren Klicks auf den inneren Schlägen. Drücke <kbd>C</kbd> oder <kbd>M</kbd> (oder klicke **Klick** in der Transportleiste), um das Metronom jederzeit ein- oder auszuschalten.
- **Harmonische Akkordbegleitung:** Das Abspielen erzeugt warme mehrstimmige Akkordflächen direkt aus der Akkordfolge der Partitur. Selbst wenn Gesangs- oder Instrumentalspur pausieren, bleibt der harmonische Raum musikalisch und warm, statt in tote Stille abzufallen. Drücke <kbd>H</kbd> (oder klicke **Akkorde** in der Transportleiste), um die Akkordbegleitung ein- oder auszuschalten.
- **Taktweise springen:** Drücke <kbd>Pfeil links</kbd> und <kbd>Pfeil rechts</kbd>, um Takt für Takt zurück und vor zu springen, oder <kbd>Home</kbd>, um direkt zum Anfang zu springen.

#### Tastenkürzel {#keyboard-shortcuts}

| Taste | Aktion |
|---|---|
| <kbd>Space</kbd> | Abspielen / Pause |
| <kbd>Pfeil links</kbd> | Einen Takt zurück |
| <kbd>Pfeil rechts</kbd> | Einen Takt vor |
| <kbd>Home</kbd> | Abspielposition zum Anfang (Takt 1) |
| <kbd>C</kbd> oder <kbd>M</kbd> | Hörbaren Klick (Metronom) ein / aus |
| <kbd>H</kbd> | Akkordbegleitung ein / aus |
| <kbd>Delete</kbd> / <kbd>Backspace</kbd> | Ausgewählte Note(n) löschen |
| <kbd>Ctrl</kbd>+<kbd>Z</kbd> / <kbd>Cmd</kbd>+<kbd>Z</kbd> | Letzte Bearbeitung rückgängig |
| <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>Z</kbd> / <kbd>Ctrl</kbd>+<kbd>Y</kbd> | Bearbeitung wiederholen |
| <kbd>Ctrl</kbd>+<kbd>A</kbd> / <kbd>Cmd</kbd>+<kbd>A</kbd> | Alle Noten in beiden Stimmen auswählen |
| <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>A</kbd> / <kbd>Alt</kbd>+<kbd>A</kbd> | Alle Noten vom Abspielcursor bis zum Ende in beiden Stimmen auswählen |
| <kbd>+</kbd> oder <kbd>=</kbd> | Zeitleiste horizontal vergrößern |
| <kbd>-</kbd> oder <kbd>_</kbd> | Zeitleiste horizontal verkleinern |
| <kbd>0</kbd> | Zu den Noten scrollen (Ansicht einpassen) |
| <kbd>L</kbd> | Text der ausgewählten Gesangsnote bearbeiten |
| <kbd>Escape</kbd> | Notenauswahl aufheben oder Partiturfenster schließen |

### Harmonie {#harmony}

Sich selbst überlassen schreibt YuE2 gern eine Vier-Akkord-Schleife und bleibt dabei. Der Schieberegler **Harmonie** drängt es
weg von Akkorden, die es gerade benutzt hat, ohne die Struktur des Songs zu zerbrechen.

| Stufe | Was du bekommst |
|---|---|
| Vertraut | Die eigenen Akkorde von YuE2. Oft eine Schleife für den ganzen Song |
| Abwechslungsreich | Vermeidet, dieselben Akkorde zu wiederholen. Bleibt in der Tonart |
| Farbig | Strophe und Refrain bekommen verschiedene Folgen, mit reicheren Akkorden. Ein Abschnitt darf nicht so beginnen wie der davor |
| Abenteuerlich | Hält die Harmonie in Bewegung und borgt Akkorde von außerhalb der Tonart |
| Außerhalb | Abenteuerlich, und reicht weiter aus der Tonart hinaus |

**Einen neuen Plan schreiben** nutzt die aktuelle Stellung des Reglers, sodass du denselben Text mit abenteuerlicheren
Akkorden neu würfeln und vergleichen kannst.

Das wurde gemessen statt geraten — ein Songtext, zwei Stile, je drei Seeds:

| | Vertraut | Abwechslungsreich | Farbig | Abenteuerlich | Außerhalb |
|---|---|---|---|---|---|
| Verschiedene Akkorde in einem Song | 4.7 | 6.3 | 8.7 | 9.0 | 10.3 |
| Takte mit einem Akkord außerhalb der Tonart | 0% | 0% | 0% | 13% | 24% |
| Vier-Takt-Muster, die keine Wiederholungen sind | 29% | 38% | 50% | 63% | 64% |

Jeder Plan auf jeder Stufe behielt seine Abschnitte und gültige Akkorde. Abenteuerliche Harmonie stattdessen im
Stiltext zu verlangen — „jazz harmony“, „borrowed chords“ — hatte überhaupt keine messbare Wirkung.

### Planvielfalt {#plan-variety}

Unter *Erweitert* legt **Planvielfalt** fest, wie frei der Planner schreibt. Wo Harmonie auf die
Akkorde wirkt, wirkt dies auf alles: Melodie, Struktur und Länge.

- **Ruhig:** das Beständigste. Wenige Akkorde und eine Melodie, die nah bei sich bleibt.
- **Normal:** der Standard.
- **Lebhaft:** ein paar Akkorde und Wendungen mehr.
- **Kühn:** reichere Harmonie, etwa das Dreifache des normalen Akkordvokabulars, während die Melodie
  erkennbar dieselbe Art Melodie bleibt.
- **Schräg:** unruhig. Die Akkorde wechseln ständig, und die Melodie springt von einem
  Abschnitt zum nächsten zwischen Lagen. Für eigenwillige, ausgefallene Songs.
- **Wild:** das Unruhigste von allen, und es kann mittendrin die Tonart wechseln.

### Ein Song ohne Partitur {#a-song-with-no-score}

**Keine Partitur**, die dritte Wahl unter **Modus**, singt den Text ganz ohne Plan: YuE2 schreibt Melodie und
Akkorde beim Singen, wie das ursprüngliche YuE es tat, und der Song wird sofort mit **Ohne Partitur singen** gerendert.
Er klingt oft ganz anders als ein geplanter Song.

Was einen Plan steuert, hat nichts, worauf es wirken könnte, also sind **Harmonie**, **Planvielfalt**, **Diese Melodie behalten** und **Dieser Struktur genau folgen**
ausgegraut, solange es gewählt ist, und es gibt keine Partitur zum Lesen oder Bearbeiten. YuE2 entscheidet
die Länge, bis zur Längengrenze. Tonart fixieren und Tempo fixieren erreichen es nur als Wörter im Stil. Erneut singen,
Variationen, Mehr ausprobieren und neuer Text funktionieren alle, jeweils wieder ohne Partitur gesungen. **Einen neuen Plan schreiben** gibt dem Take eine
Partitur, und Modus geht zurück auf *voll*. Es ist nur für Songs aus einem Prompt: Ein Cover ist die Partitur seiner Aufnahme, und ein
Instrumental braucht eine, um seine Stimme draußen zu halten. Beide Engines können es.

---

## Rendern {#rendering}

### Interpretation {#interpretation}

Die Partitur legt die Noten fest. Die **Interpretation** bestimmt, wie sie gespielt werden.

| Interpretation | Was du hörst |
|---|---|
| Standard | Die übliche Lesart von YuE2 |
| Straff | kontrollierter und geschliffener |
| Locker | rauer und spontaner |
| Gelassen | darf eine Figur wiederholen und in einem Groove bleiben |
| Unruhig | hält die Stimmen in Bewegung, vermeidet Wiederholungen |
| Weit | greift zu weniger naheliegenden Klängen |

### Variationen {#variations}

Die Funkel-Schaltfläche auf einer Karte rendert **dieselbe Partitur und denselben Seed** in den anderen
Interpretationen. Weil sich nur die Interpretation ändert, ist das, was du zwischen ihnen hörst, die
Interpretation — kein anderer Wurf der Würfel. Jede ist ein eigener Take mit dem Titel
*Night drive · Loose* und wird in dem Take aufbewahrt, aus dem sie gemacht wurde (siehe **Takes in einem Take**
unter Die Bibliothek). Das Fenster hat seine eigene Längengrenze, die bei der des Editors beginnt und nur
für diese Takes gilt.

### Mehr ausprobieren {#try-more}

Die Würfel-Schaltfläche auf einer Karte rendert **dieselbe Partitur und denselben Text erneut als mehrere neue Takes**, um
sie zusammen anzuhören. Variationen ändert nur die Interpretation und behält den Seed; dies ändert den
Wurf:

- **Neue Seeds:** ein frischer Seed für jeden, alles andere bleibt.
- **Planer-Stärken:** für einen Take mit einer Stil-LoRA, die eine Planner-Hälfte hat, derselbe Seed bei
  anderen Planner-Stärken (seine eigene wird ausgelassen). Planner ändert die Darbietung selbst, nicht nur
  die Stimme, also wirkt es wie ein anderer Seed.

Die neuen Takes heißen *Night drive · try 1* oder *Night drive · planner 0.60* und werden in
dem Take aufbewahrt, aus dem sie gemacht wurden, dessen Bereich sich öffnet, um sie zu zeigen, sobald sie fertig sind. Um sie gegen-
einander zu hören, drücke **Alle auswählen**, solange der Bereich offen ist, und dann **Vergleichen**. Das Fenster hat seine
eigene Längengrenze, die bei der des Takes beginnt.

### Seed, und einen Take reproduzieren {#seed-and-reproducing-a-take}

Jeder Take hält seinen Seed und jede Einstellung fest, die ihn geformt hat. Die Karte nennt sie, ein Klick auf eine Karte
zeigt sie im Take-Bereich, und das Öffnen im Editor lädt alles zurück. **Nochmal** öffnet den
Editor mit genau dem, Seed eingeschlossen, sodass ein Take, der dir gefallen hat, reproduziert werden kann und einer, der dir fast
gefallen hat, eine Einstellung nach der anderen angepasst werden kann.

In den Menüs des Editors zeigt das Überfahren einer Interpretation, was sie tut.

Setze den Haken bei **diesen Seed behalten**, um denselben Seed über Renderings hinweg zu behalten; lässt du ihn weg, würfelt jedes Rendering einen
neuen.

Ein Rendering nutzt, was der Editor zeigt: seinen Stil, die Stil-LoRA und ihre Stärken, Längengrenze, Modus,
Interpretation und Seed, selbst wenn die eigene Partitur eines Takes erneut gerendert wird.

### Dieselbe Melodie, neuer Text {#same-tune-new-words}

Der Planner liest den ganzen Text, bevor er eine Note schreibt, also ergibt derselbe Seed nur
für denselben Text denselben Plan. Ändere eine Zeile, und der nächste Plan ist eine neue Melodie: eine andere Melodie, oft eine andere
Tonart und ein anderes Tempo, und die Stimme wandert mit.

Um eine Melodie zu behalten, die dir gefällt, öffne den Take und ändere seinen Text. **Diese Melodie behalten** erscheint unter dem
Text, angehakt, und die Hauptschaltfläche wird zu **Mit neuem Text singen**. Ändere zuerst alles andere, was du
willst: den Stil, die LoRA und ihre Stärken, die Längengrenze, die Interpretation. Die Partitur des Takes wird
dann mit dem neuen Text gesungen, als neuer Take neben dem Original, das bleibt, wie es ist. Lass den Seed
angehakt, um die Stimme so nah wie möglich zu halten. Entferne den Haken bei **Diese Melodie behalten**, um stattdessen einen neuen Plan und eine
neue Melodie für den Text zu schreiben. Neuer Text, der die Silbenzahlen der alten Zeilen beibehält, passt am besten
zur Melodie. Wenn nicht, weil es mehr Abschnitte gibt oder viel mehr Silben, als die Melodie Noten hat (lange Zeilen auf einer Melodie
für kurze: die Zeilen werden wiederholt oder fallen weg), oder viel weniger (kurze Zeilen auf einer Melodie für lange:
der Sänger füllt die übrigen Noten mit eigenen Wörtern), entfernt sich der Haken bei **Diese Melodie behalten** selbst mit einer Zeile, die sagt warum, und
ein neuer Plan wird für den Text geschrieben. Setze ihn wieder, um die Melodie trotzdem zu singen.

### Produktionsschliff {#production-polish}

**Produktionsschliff** wendet die Realaudio-Decoder-LoRA von Mothersuperior an. Standard-YuE2 klingt in den Mitten oft
dumpf; dies trennt Instrumente und Gesang sauberer. Standardmäßig an.

### Länge {#length}

Die Längengrenze ist ein festes Limit, kein Ziel. YuE2 entscheidet, wann ein Song endet, und endet meist von
selbst; die Grenze stoppt einen, der es nicht tut. Sie beginnt bei 360 Sekunden oder bei dem, was **Längenbegrenzung für einen neuen Take**
in den Einstellungen sagt. Dann macht sie Platz für die Musik, damit ein langer Song nicht abgeschnitten wird:

- Bei einem **Song oder Instrumental aus einem Prompt** wird die Grenze angehoben, wenn sein Plan geschrieben wird, falls der Plan
  länger ist: auf die Länge des Plans mit etwa zehn Sekunden Reserve. Sie wird nie gesenkt.
- Mit einer gewählten **Aufnahme**, für ein Cover oder ein Instrumental, folgt die Grenze der Partitur der Aufnahme,
  auf dieselbe Weise aufgerundet.

Eine Grenze, die du selbst eintippst, bleibt, wie du sie gesetzt hast, und die Seite Partitur sagt dann, wenn ein Plan länger ist als
sie. Ein Plan, der viel länger ist als seine Grenze (mehr als ein Drittel darüber und über acht Minuten), wird gar nicht
als Song angenommen und neu geschrieben. Hin und wieder
hört ein Rendering nicht am Ende seiner Partitur auf und spielt bis zur Grenze weiter; ein solcher Take wird über
seine letzten Sekunden ausgeblendet statt abgeschnitten, und seine Karte sagt, dass er bis zur Grenze lief. Noch seltener endet ein
Rendering, bevor der letzte Abschnitt seiner Partitur beginnt. Die App rendert es dann noch einmal mit einem neuen
Seed, bevor sie es für fertig erklärt, und wenn auch das zu früh aufhört, sagt die Karte, dass es vor dem
letzten Abschnitt aufgehört hat: **Rendern** erneut für einen weiteren Versuch.

---

## Eine Aufnahme covern {#covering-a-recording}

1. Zieh eine Audiodatei hinein, bis 2 GB. Sie wird einmal gespeichert und gehasht, sodass dieselbe Datei nie
   doppelt gehalten wird. Eine Videodatei (MP4, MOV, MKV, WebM und ähnliche) geht auch: Nur ihr Ton wird behalten, als FLAC.
2. Drücke **Transkribieren**. SheetSage2 schreibt Melodie und Akkorde in das Partiturfeld. Das wird
   pro Aufnahme zwischengespeichert, sodass ein erneutes Covern desselben Songs es überspringt.
3. Korrigiere, was es falsch gehört hat.
4. Füge Text hinzu, wähle einen Stil, drücke **Cover erstellen**.

Ein Cover folgt Melodie und Akkorden des Originals, während der Stil alles andere entscheidet, und genau
das macht es zu einem Cover statt einer Kopie.

### Eine eigene Melodie aufnehmen {#recording-a-tune-of-your-own}

> [!NOTE]
> Wie gut eine Melodie erkannt wird, hängt von der Aufnahme ab, und ein Plan um sie herum kann trotzdem scheitern oder
> abschweifen: Schreibe einen neuen Plan oder nimm die Melodie erneut auf.

Im Modus **Cover** öffnet **Melodie aufnehmen** den Rekorder. Wähle unter **Eingang**, was du aufnimmst:

- **Stimme:** Singe oder summe in ein Mikrofon. **Autotune** kann den Take auf eine Tonart und Tonleiter ziehen; die
  Schaltfläche an einem Take wechselt zwischen gestimmter und roher Version, damit du hörst, was es getan hat.
- **Instrument:** Spiel die Melodie auf einem Instrument, zum Beispiel einer Gitarre über ein Audio-Interface.
  Spiele sie **Note für Note**: Die Linie, die du spielst, wird die gesungene Melodie, und angeschlagene
  Akkorde geben keine Melodie zum Singen. Wähle das Interface unter **Gerät** und unter **Kanal** die Seite,
  an der dein Instrument steckt (Eingang 1 eines Interfaces ist meist **Links**). Erhöhe **Eingangsverstärkung**
  für ein leises Instrument und halte die Anzeige aus CLIP heraus. Autotune wird nicht angeboten: Ein Instrument ist
  schon gestimmt. Yeufonic merkt sich diese Wahl in diesem Browser.

Metronom, Einzähler und Kopfhörer-Monitoring funktionieren für beide gleich. **Als Cover verwenden** behält den
Take als Aufnahme, in der Liste als **MIC** oder **INST** markiert. Transkribiere sie wie jede Aufnahme; eine
aufgenommene Melodie wird nur als Melodie transkribiert, da aus einer einzelnen Melodie geratene Akkorde in
jedem Refrain eines daraus gemachten Songs gehalten würden (eine Aufnahme, die vorher transkribiert wurde, behält ihre Akkorde, bis sie
erneut transkribiert wird). Zehn bis dreißig Sekunden Melodie sind reichlich.
**Songtext extrahieren** wird für einen Instrument-Take nicht angeboten, da er keine Wörter zum Hören hat: Nutze
**Songtext schreiben**.

**Hörst du dich verzögert?** Der Browser fügt eine kurze Verzögerung zwischen dem ein, was du singst oder spielst, und dem, was
du im Kopfhörer hörst. Hat dein Audio-Interface direktes (latenzfreies) Monitoring, nutze es
und schalte **Monitor** im Rekorder aus, sodass du dich direkt aus dem Interface hörst, und nur
einmal. Nutze kabelgebundene Kopfhörer: Bluetooth fügt eine eigene Verzögerung hinzu.

#### Zum ganzen Song erweitern {#expand-to-full-song}

Eine aufgenommene Melodie ist oft nur ein paar Takte lang. **Zum ganzen Song erweitern** lässt YuE2 einen ganzen Song
mit deiner Melodie darin planen: Der Plan steht in Tonart, Metrum und Tempo deiner Melodie, jeder Refrain (oder jede Strophe,
wenn du willst) enthält deine Melodie, und der Rest des Songs wird um sie herum geschrieben. Dann wird er
als Cover deiner Aufnahme gerendert.

- **Gesungen von:** ein Mann oder eine Frau. Deine Melodie wird um ganze Oktaven dorthin verschoben, wo diese Stimme singt,
  da die Oktave, in der die Melodie geschrieben ist, bestimmt, wer sie singt. Nennt der Stil keinen Sänger,
  wird die Stimme hinzugefügt.
- **Akkorde:** Eine Melodie allein kommt vom Transkribierer oft ohne Akkorde zurück. Yeufonic gibt ihr dann
  Akkorde aus ihren eigenen Noten, damit der Planner eine Harmonie hat, der er folgen kann. Akkorde, die du in
  die Partitur der Aufnahme schreibst, bleiben erhalten.
- **Deine Melodie** ist immer die Partitur der Aufnahme, auch wenn der Editor einen daraus gemachten Take
  zeigt.
- **Songstruktur:** wird benutzt, wenn das Textfeld leer ist. Mit Wörtern im Feld sind deren Abschnitte
  die Struktur, und sie brauchen einen **[Chorus]** (oder **[Verse]**), in dem deine Melodie stehen kann.
- **Text:** Ein Summen kann ohne Wörter geplant werden. Eine auf einem Instrument gespielte Melodie braucht Wörter zum
  Singen, also schreibe sie zuerst: **Songtext schreiben** entwirft sie für dich.

### MIDI-Dateien und Cover {#midi-files-and-covers}

> [!NOTE]
> MIDI-Dateien sind dafür gedacht, unterschiedliche, oft ausgefallene Takes ursprünglicher Melodien zu erzeugen.

Neben aufgenommenen Audiodateien kannst du Standard-MIDI-Dateien (`.mid`, `.midi`) direkt in den Modus **Cover** ziehen oder hochladen.

Wenn eine MIDI-Datei hochgeladen wird:
- **Automatische Partiturtranskription:** Yeufonic analysiert Spuren und Kanäle, um die Hauptgesangsmelodie, die Begleitung und die harmonische Akkordfolge zu erkennen, transkribiert sie in ABC-Notation und lädt sie direkt in die Pianorolle. Synth-Leads oder Gesangsmelodien, die in tieferen Lagen programmiert sind, werden automatisch in eine natürliche Gesangsoktave transponiert.
- **Eingebetteter Text:** Text- oder Lyrics-Ereignisse in der MIDI-Sequenz werden ausgelesen und an den Silben der Melodie ausgerichtet.
- **Wo die Takte liegen:** Eine MIDI-Datei hat keine eigenen Taktstriche, und manche beginnen mit dem ersten Wort auf dem Schlag *vor* der Eins. Yeufonic liest Schlagzeug und Bass, um den echten Taktstrich zu finden, und setzt, wenn die Datei mit einem solchen Auftakt beginnt, die ersten Wörter in einen eigenen kurzen Takt, damit Akkorde und Taktmarken dort liegen, wo die des Songs liegen. Eine Datei ohne klares Muster aus Schlagzeug und Bass bleibt, wie sie ist.
- **Eingefügter Text:** Wörter, die du einfügst, werden auf einmal an die ganze Melodie angepasst, eine Silbe pro Note, wobei übrige Noten auf der Silbe davor gehalten werden. Zeilen enden, wo die Melodie pausiert, und beginnen, wo eine Phrase beginnt, sodass ein Abschnitt, der länger oder kürzer ist als die Überschriften im Text, den Rest nicht mehr aus dem Takt bringt. Sind die Wörter länger, als die Melodie tragen kann, werden die letzten Zeilen weggelassen.
- **Volles Probehören mit SoundFonts:** Der Player synthetisiert das MIDI-Arrangement mit **FluidSynth** und General-MIDI-SoundFonts (`.sf2`) zu hochwertigem Audio. Die Ausgabe wird auf Spitzenpegel normalisiert, damit leise mehrspurige MIDI-Aufnahmen mit voller Präsenz und Klarheit ohne Verzerrung klingen.
- **SoundFonts wählen:** In den **Einstellungen** kannst du deine bevorzugte aktive `.sf2`-SoundFont-Bank wählen (etwa *Arachno SoundFont 1.0* oder *JNS-GM 2.0*). Weitere `.sf2`-Dateien in `data/models/soundfonts/sf2/` werden automatisch erkannt.
- **Feinschliff in der Pianorolle:** Öffne die **Piano Roll**, um Noten zu prüfen oder zu ändern, zu wählen, welche Spur als Hauptgesangsmelodie dient, Lücken der Begleitung mit **Lücken füllen** zu harmonisieren oder neu eingefügten Text mit **Text zuordnen** auszurichten.

### Einen Song aus einem Korpus covern {#covering-a-song-from-a-corpus}

Die Analyse eines Korpus hat schon erledigt, was ein Cover braucht: die Partitur, die im Song gehörten Wörter und
seinen getrennten Gesang. Deshalb bietet die Liste unter deinen Aufnahmen **Aus deinen Korpora** an, nach
Korpus gefaltet, mit Tonart und Tempo jedes Songs und einem Filter für einen großen. Wähle einen Song, und er wird sofort eine
deiner Aufnahmen, mit seiner Partitur und seinem Text, und nichts läuft erneut. Die Wörter werden
unter die Abschnitte der Partitur gelegt, wie **Songtext extrahieren** sie legt, es sei denn, du hast sie im Korpus geprüft,
dann kommen sie so, wie du sie hinterlassen hast. Sie kommen ins Textfeld und ersetzen Wörter, die von
einer anderen Aufnahme stammten; Wörter, die du dort getippt oder bearbeitet hast, werden nur ersetzt, wenn du es sagst. Das Stilfeld übernimmt den
Stil, mit dem der Song im Korpus gelernt wurde, wie sein Chip unter einer daraus trainierten LoRA.

Die Datei wird verknüpft statt kopiert, wo die Festplatte es erlaubt, nimmt also keinen weiteren Platz ein, und sie bleibt,
wenn der Korpus gelöscht wird. Einige Songs sind mit *score: melody only* oder *score: first 4 min* markiert: Ihre
volle Transkription ist bei der Analyse fehlgeschlagen, was fürs Training reicht. Drücke **Transkribieren** für die
ganze Partitur mit ihren Akkorden.

**Mit einer LoRA.** Hier sind Korpus-Songs am nützlichsten: ein Song und eine LoRA aus demselben
Werk oder aus verschiedenen.
1. Öffne im Modus **Cover** die Aufnahmeliste und wähle den Song unter **Aus deinen Korpora**. Seine
   Partitur legt Melodie und Akkorde fest, und sein Text steht im Feld.
2. Wähle eine **Stil-LoRA**. Die eigene LoRA des Korpus lässt den Sänger seinen eigenen Song covern, am nächsten am
   Original. Die LoRA eines anderen Korpus covert ihn in jenem anderen Stil und mit jener Stimme.
3. Stelle die Stärken ein wie für jedes Cover: Die Aufnahme legt die Melodie schon fest, also halte **Klang**
   nahe **0.50** und erhöhe es für mehr von der Stimme und dem Klang der LoRA.
4. Das Stilfeld enthält schon den eigenen Stil des Songs, und eine LoRA zu wählen setzt ihr Triggerwort
   davor. Das behält Genre und Stimmung des Songs; ein anderer Chip oder die Tags des Filters führen ihn
   woandershin. Tempo und Tonart kommen aus der Partitur, egal was der Stil sagt.
5. Drücke **Cover erstellen**. **Variationen** rendert es dann in den anderen Interpretationen, und
   **Erneut singen** gibt eine andere Stimme über dieselbe Partitur, wie bei jedem Take.

### Den Text extrahieren {#extracting-the-lyrics}

**Songtext extrahieren**, neben *Transkribieren*, schreibt auf, was die Aufnahme singt: Es trennt den
Gesang, hört ihn an und legt die Zeilen unter die Abschnitte der Partitur. Man fordert es an,
statt dass es bei jeder Transkription passiert, weil es ein paar Minuten dauert, während das Transkribieren einer Partitur
Sekunden braucht. Der Gesang wird auf der GPU getrennt und seine Wörter gehört, wenn die Engine Demucs und Whisper hat, sonst auf der CPU
(Einstellungen, **Die GPU für Stems und Songtexte nutzen**), und die Leiste sagt, in welcher der beiden Stufen es ist. Whisper auf der GPU
und auf der CPU schreiben für denselben Gesang nicht immer dieselben Wörter, da keines exakt ist: Ein schwieriger Gesang, etwa Backgroundsänger
über einer Hauptstimme, kann sich um ein Fünftel seiner Wörter in die eine oder andere Richtung unterscheiden. Der getrennte Gesang wird behalten, sodass eine erneute Extraktion derselben Aufnahme
direkt zum Hören springt, womit der größte Teil der Wartezeit gespart ist.

Die Wörter werden mit der Aufnahme behalten. Drücke **Songtext extrahieren** erneut, und sie kommen direkt zurück ins
Feld, und du wirst gefragt, ob sie erneut extrahiert werden sollen, was sich nach einer Änderung der
Methode in den Einstellungen lohnt. Eine andere Aufnahme zu wählen übernimmt deren Wörter auf dieselbe Weise, und eine Aufnahme
ohne Wörter leert die der vorigen. Wörter, die du getippt oder bearbeitet hast, bleiben, es sei denn, du stimmst zu, sie zu ersetzen.

Erwarte einen guten Entwurf statt einer Abschrift. Gemessen am echten Text zweier Songs hatte Whisper
bei einem **1,5 % der Wörter falsch** und beim anderen **25 %**, wo Haupt- und Backgroundgesang sich im
letzten Refrain überlagern. Es hört den ganzen Gesang: Früher übersprang es, was sein Stimmdetektor
für Stille hielt, was bei gesungenem Gesang den größten Teil des Songs ausmachte. Lies den Entwurf und korrigiere, was es
falsch gehört hat, besonders wo Stimmen sich überlagern.

**Eine externe LLM hören lassen.** Ist eine [externe LLM](#external-llm) dein Anbieter, haben die Einstellungen eine Wahl unter
*Songtext aus einer Aufnahme*. Stell sie auf **Externes LLM**, und der getrennte Gesang wird an das Modell geschickt, um
die Wörter zu hören, während Whisper weiterhin ermittelt, wann jede Zeile gesungen wird. Bei denselben zwei Songs hatte Gemini
**1,5 % und 23 %**, die beiden liegen also nah beieinander; probiere beide bei einem Song, mit dem Whisper kämpft. Es braucht ein
Modell, das Audio annimmt, wie Gemini. Sieht die Antwort des Modells wie ein Songtext aus, werden seine Wörter
benutzt, selbst wo sie sich deutlich von denen von Whisper unterscheiden: Ein im Mix vergrabener Gesang ist, wo Whisper
am meisten kämpft, und das Modell nicht. Lehnt das Modell das Audio ab, hält es sich zurück (kürzt Zeilen
oder verweist dich auf eine Lyrics-Seite, wie es ein Modell bei einem erkannten Song tun kann) oder schickt
fast nichts zurück, bekommst du stattdessen die Version von Whisper. Die Meldung am Ende nennt, wer
die Wörter gehört hat. Der Gesang verlässt dafür deinen Rechner; Whisper behält ihn hier.

Für einen Korpus-Song werden **beide Versionen behalten**. Gibt es beide, zeigt der Prüfbereich des Songs
**Wörter von** mit jeder Version und ihrer Wortzahl, standardmäßig die des externen Modells. Wähle
die andere, und ihre Wörter kommen ins Feld. Beim ersten Wählen einer Version werden ihre Wörter entworfen, was
ihre Abschnitte mit dem externen Modell markiert; danach behält jede Version ihre eigenen Wörter, Änderungen und
den Haken **geprüft**, sodass das Wechseln sofort geht und keinen Aufruf des Modells braucht. In den eigenen Zeilen von Whisper wird jedes Wort,
das es mehr als achtmal hintereinander wiederholt hat, etwa ein gehaltenes „la“, das es hunderte Male schrieb, auf acht
gekürzt.

---

## Instrumentals {#instrumentals}

Der dritte Modus schreibt ein Stück ohne Gesang. Statt eines Textes nimmt er eine **Struktur**:

| Struktur | Was YuE2 bekommt | Wer entscheidet |
|---|---|---|
| YuE2 entscheiden lassen | `[instrumental]` | YuE2 wählt die Abschnitte und ihre Längen |
| Teile | `[intro] [verse] [chorus] …` | du wählst die Abschnitte, YuE2 ihre Länge |
| Zeitlich festgelegte Teile | `[intro 0:00-0:15] …` | du wählst beides |

Füge Abschnitte mit den **+**-Chips hinzu, sortiere sie mit den Pfeilen um und gib jedem eine Länge, wenn zeitlich festgelegt.
**An YuE2 gesendet:** zeigt genau, was das Modell bekommt. Die Struktur ist eine Orientierung: YuE2 kann einen
Abschnitt umbenennen, ein Zwischenspiel hinzufügen oder über die angegebenen Zeiten hinauslaufen, also ist die Längengrenze das feste Limit.

### Ein Instrumental aus einer Aufnahme {#an-instrumental-from-a-recording}

**Aus einer Aufnahme (optional)** oben im Editor nimmt eine deiner Aufnahmen, wie ein Cover. Ihre
Transkription ist die Partitur, also gibt es keinen Plan zu schreiben, und das Rendering spielt ihre Melodie und
Akkorde mit der Instrumental-LoRA.

Auch die Abschnitte kommen aus der Partitur: einer pro Abschnitt der Partitur, mit den Namen, die die LoRA kennt. Ein
*Zwischenspiel* wird zu einer Bridge. Ein Rendering paart jeden Abschnitt der Struktur mit einem der Partitur,
deshalb weicht der Baukasten ihnen. Um den Song umzustellen, zieh einen Abschnitt an eine neue Stelle oder verschiebe ihn mit den Pfeilen, füge eine
**Kopie** davon hinter ihm ein oder nimm ihn mit dem **✕** heraus: Jede Änderung schreibt die Partitur neu (das Partitur-
fenster zeigt es), und **Ursprüngliche Teile wiederherstellen** stellt sie wieder her, bis eine andere Partitur geladen wird.
Während der Take im Editor spielt, leuchtet der Abschnitt, bei dem er ist, und ein Doppelklick auf einen Abschnitt springt dorthin. Die Zeiten kommen aus den Takten und dem Tempo der Partitur, denen das Rendering im ersten Teil eines Takes und bei einem vollständig gerenderten eng folgt. Ein Rendering, das deutlich vor seiner Partitur endet, hat weniger Musik gespielt, als die Partitur enthält, also kann die Liste im Lauf des Songs aus dem Takt mit dem Audio geraten; eine Zeile unter der Liste sagt es und um wie viel. Ein Cover zeigt dieselbe Liste unter seinem Text, und sein Text wird den Abschnitten in Reihenfolge zugeordnet, also
passe ihn an: Die Liste sagt, was er braucht, nachdem du Abschnitte hinzugefügt, entfernt oder umgestellt hast. Sie zeigt auch die Gesamtlänge gegenüber der
Längengrenze und bietet an, die Grenze zu erhöhen, wenn ein längerer Song abgeschnitten würde. Drücke **Instrumental erstellen**, um zu rendern.

Ein Instrumental, das du aus einer Struktur geschrieben hast, hat auch eine Partitur, und sobald es geplant ist, werden seine Abschnitte genauso aufgelistet. Der
Struktur-Baukasten ist die Vorgabe für einen noch nicht geschriebenen Plan, also weicht er der Liste. Stelle die Abschnitte um und drücke
**Diese Partitur rendern**: Die Abschnitts-Tags des Renderings folgen der bearbeiteten Partitur. Ein Take, der schon Audio hat, wird als
neuer Take daneben gerendert, egal was du geändert hast, sodass das Original sein eigenes behält. **Einen neuen Plan schreiben** (unter der Partitur) verlangt weiterhin
eine andere Melodie aus der Struktur, mit der der Take geschrieben wurde.

**Ein Song mit Gesang geht auch.** Seine Partitur hat die gesungene Melodie in der Gesangsstimme, die
gesungen herauskäme, also wird die Melodie einem Instrument gegeben: Wo kein Instrument spielt, wandern die gesungenen Noten
zu einem, und die Gesangsstimme behält nur ihre Akkorde. Der Editor sagt es unter der Aufnahme. Für einen Song
ist das meist die bessere Wahl: Ohne seine Stimme übersieht der Transkribierer oft den
Unterschied zwischen Strophe und Refrain und hört den ganzen Song als eine Akkordschleife. Die LoRA
arrangiert ihn als Instrumental, also rechne mit eigenen Stimmen, etwa zusätzlicher Gitarre.

Wähle **Keine Aufnahme: einen Partiturplan schreiben** in der Liste, um zum Schreiben eines Plans zurückzukehren.

### Wenn ein Instrumental singt {#when-an-instrumental-sings}

Gelegentlich setzt das Modell eine Stimme in ein Instrumental. Das ist ein Fehler des Modells, keine Einstellung,
die du falsch gemacht hast. Setzt der Plan vor dem Rendern Noten in die Gesangsstimme, bietet ein Dialog einen neuen
Plan, einen neuen Seed oder trotzdem zu rendern an. Ein fertiger Take wird nicht auf Gesang geprüft: Hör ihn dir an.

### Ein Instrumental aus der Partitur eines Songs {#an-instrumental-from-a-song-s-score}

**Ein Instrumental machen**, unter der Partitur eines Songs oder Covers auf der Partitur-Seite des Editors (neben **Diese Partitur rendern**
bei einem Song), macht dieselbe
Partitur als Instrumental, in einem neuen Take: Das Original bleibt, wie es war. Die gesungene Melodie wandert
zu einem Instrument, statt der Wörter werden nur die Abschnitts-Tags der Partitur an das Modell geschickt, die
Instrumental-LoRA wird benutzt, und der Stil verliert die Tags, die eine Stimme beschreiben („soft male vocal“).
So bekommt man „diese Melodie, ohne Gesang“. Die Gesangsstimme der Partitur eines Songs von Hand zu leeren
reicht nicht: Das Rendering eines Songs singt trotzdem die Wörter, die es bekommt.

---

## Stimmen {#voices}

Die Chips **Gesang** legen Geschlecht und Charakter des Sängers fest, indem sie in den Stil schreiben, für den ganzen Song.

Für ein Duett, oder einen Sänger für die Strophen und einen anderen für den Refrain, setze Stimmanweisungen in den Text und hake
**Stimmen folgen den Hinweisen** an: siehe [Der Text](#the-words) unter „Einen Song aus einem Prompt schreiben“. Es funktioniert auch für den Text
eines Covers.

## Korpora und eine LoRA trainieren {#corpora-and-training-a-lora}

Ein **Korpus** ist ein Ordner mit Songs, vorbereitet als Trainingsset für eine Stil-LoRA: typischerweise ein
Künstler, ein Genre oder einige ähnliche Künstler.
Öffne **Korpora** im Menü. Es ist standardmäßig an; `TRAINING_ENABLED=0` für die App oder eine
Engine, die mit `WITH_TRAINER=0` gebaut wurde, nimmt es heraus.

Training ist das Anspruchsvollste, was die App tut: Mit dem empfohlenen Modell in voller Qualität (BF16)
sind eine Grafikkarte mit 16 GB und 32 GB Arbeitsspeicher (unter WSL2 `memory=32GB` in `.wslconfig`) das praktische Minimum.
Eine Karte mit 8 GB kann zum Training benutzt werden, wenn das Modell mit wenig Speicher (INT8) verwendet wird.

1. **Neues Korpus.** Gib ihm einen Namen und ein **Triggerwort**, sag, ob die Stimme männlich oder weiblich ist
   (**keine** für Songs ohne Gesang: siehe unten), beschreibe den Klang, den alle Songs teilen, und öffne den Ordner mit den Songs. Bestätige, dass du
   das Recht hast, mit ihnen zu trainieren, und drücke dann **Ordner einlesen**. Der Ordner wird nur gelesen.
   **Ein Korpus ohne Gesang.** Wähle **keine** für **Stimme**, wenn die Songs instrumental sind, etwa
   Dance und elektronische Musik. Die App trennt dann keinen Gesang und hört nicht nach Wörtern, sodass nichts
   Wörter über Synths erfindet. Der Text jedes Songs sind die Abschnitts-Tags aus seiner Partitur (oder
   `[instrumental]`, wenn sie keine hat), die Beschreibung lässt den Gesangsteil weg, und es gibt keine Text-
   prüfung: Das Feld **Teile** kann bearbeitet werden, und eine Änderung bleibt. Der Klang jedes Songs wird
   vom lokalen Modell beschrieben, wenn es installiert ist, da das externe nur einen Titel hätte.
   Eine so trainierte LoRA kann Noten in die Gesangsstimme eines Plans schreiben, was ein Rendering singen oder summen lässt;
   die Warnung „kann singen“ eines Plans zeigt es. Die Stimme eines schon analysierten Korpus zu ändern passt seinen
   Text entsprechend an.
2. **Die Songs wählen.** Entferne den Haken bei allen, die draußen bleiben sollen. Wenn ein Song vorbereitet wird, behält die App eine eigene Kopie der vollen Aufnahme im internen Korpus-Speicher, sodass ein Korpus intakt bleibt, auch wenn sein Quellordner später geleert oder verschoben wird. Eine Aufnahme über 25 Minuten wird weggelassen, da sie höchstwahrscheinlich ein ganzes Album oder Konzert in einer Datei ist. Liegt ein `.cue`-Sheet daneben, schneidet **In Tracks teilen** sie in ihre Songs, die ihren Platz im Korpus einnehmen. Die Tracks kommen in den eigenen Ordner der App; deiner bleibt unverändert. (Songs, die länger sind als das GPU-Limit des Trainers, etwa 15-minütige Tracks, werden beim Export sicher an einer musikalischen Abschnittsgrenze gekürzt und ausgeblendet.)
3. **Analysieren.** Der Gesang jedes Songs wird getrennt, Tonart, Tempo und Abschnitte werden gefunden, und sein Text wird entworfen, nach Abschnitten markiert. Mit einer externen LLM in den Einstellungen werden die Abschnitte aus den gehörten Wörtern markiert: Refrains daran, dass ihre Wörter wiederkehren, neue Abschnitte an den Pausen. Nur die Zeilen und ihre Zeiten werden geschickt, und die Wörter und ihre Reihenfolge werden nie geändert. Ohne eine, oder wenn ihre Antwort nicht jede Zeile enthält, kommen die Tags aus der Musikanalyse. **Neu entwerfen**, neben Speichern in der Prüfung eines Songs, markiert die Abschnitte erneut auf dieselbe Weise, ohne den Song erneut zu hören, für einen früher entworfenen Song, und ersetzt, was im Feld steht. Eine Zeile unter den Schaltflächen sagt, was läuft, und eine laufende Analyse erscheint in der Auftragskarte und Warteschlange des Hauptbildschirms. **Stopp** beendet sie. Fertige Schritte bleiben, also macht **Analysieren** dort weiter, wo es aufgehört hat.

   **Erneut analysieren.** Sobald jeder Song analysiert ist, zeigt die Schaltfläche **Analysiert ✓**. Ein Klick darauf fragt, ob du die Stilvorschläge aller Songs mit den neuesten Prompts und LLM-Einstellungen erneut analysieren willst (praktisch nach dem Umbenennen eines Korpus oder einem Anbieterwechsel). Ein Shift-Klick auf **Analysiert ✓** bietet eine vollständige Neuanalyse von Grund auf an (Stem-Trennung, Tonart, Tempo, Transkription und Stile laufen erneut). Einzelne Songs können auch mit **Neu analysieren** in ihrer Prüfung neu beschrieben werden.
4. **Prüfen** Öffne einen Song, um seinen Text zu prüfen und **geprüft** anzuhaken, und um seinen Klang zu beschreiben,
   wo er sich vom Rest unterscheidet. Die Stilbeschreibung zeigt, was der Trainer lesen wird.
5. **Trainingsset exportieren.** Schreibt Audio, Text und Beschreibung für jeden Song. Eine Zeile unter den
   Schaltflächen zeigt, wie weit es ist. Der Trainer nimmt nur so viel von einem Song, wie die App
   aus dem freien Speicher deiner Grafikkarte errechnet (etwa 5½ Minuten bei einer 16-GB-Karte; das Fenster Logs
   sagt, was es gewählt hat). Ein längerer Song wird am Ende seines letzten Abschnitts innerhalb davon gekürzt, ausgeblendet,
   und behält nur die Wörter, die noch gesungen werden. Seine Zeile sagt „first 3:12 trained“. Läuft dem Training
   der Speicher aus, setze die Umgebungsvariable `TRAIN_MAX_MINUTES` auf eine kleinere Zahl, etwa
   3.5: siehe die README.
6. **Ein LoRA trainieren.** Das dauert lange, und die GPU steht der App nicht zur Verfügung, bis es
   fertig ist. Der Fortschritt erscheint unter den Schaltflächen und auf dem Hauptbildschirm, wo du es stoppen kannst,
   und das Abzeichen des Korpus oben auf der Seite pulsiert, während es trainiert. Erneutes Training behält
   die LoRA des letzten Laufs unter einem datierten Namen, in **Frühere Läufe**, oder löscht sie, wie du
   wählst.
   Training mit dem empfohlenen Modell in voller Qualität (BF16) braucht mindestens etwa 12,5 GB GPU-Speicher
   (bei einem Schnitt von 3½ Minuten; ein längerer Schnitt braucht mehr), das meiste davon, während es die Songs vorbereitet, also ist eine 16-GB-
   Karte das praktische Minimum, zusammen mit 32 GB Arbeitsspeicher (ComfyUI legt die vollen YuE2-Gewichte
   und Dataset-Caches im Hauptspeicher ab; unter WSL2 setze `memory=32GB` in `.wslconfig`). Eine 8-GB-Karte kann
   trainieren, wenn das Modell mit wenig Speicher (INT8) verwendet wird. Karten, die nicht trainieren können, können trotzdem anderswo trainierte LoRAs
   benutzen (**Ein LoRA installieren**). Das Fenster Trainieren warnt, wenn weniger GPU- oder Arbeitsspeicher verfügbar ist,
   also schließe vorher alles andere, das die GPU benutzt.

### Ein Lauf, der früh endet {#a-run-that-ends-early}

Ein Lauf kann vor seinem letzten Schritt enden: **Stopp**, ein Absturz oder die GPU, der der Speicher ausgeht. Die Zeile
unter den Schaltflächen sagt dann, wann und warum und nach welchem Schritt. Unterwegs speichert der Trainer alle 50 Schritte einen
Checkpoint und behält eine Kopie des bisher besten nach seinem Planner-Verlust, sodass meist der größte Teil
der Arbeit noch da ist. **Mit dem Gespeicherten abschließen** tut, was ein fertiger Lauf tut, aus
diesen Dateien: Die beste Kopie, oder ersatzweise der letzte Checkpoint, wird zur LoRA unter dem
Namen des Korpus, mit seinem Triggerwort, und die Checkpoints falten sich darunter in der Liste der Stil-LoRAs. Es
dauert Sekunden und keine GPU-Zeit. Die letzten Schritte eines Laufs ändern die LoRA am wenigsten, also ist eine so fertiggestellte
meist nah an einem vollen Lauf; **Checkpoints** rendert einen Song einmal auf jedem Schritt, wenn du nach Gehör
vergleichen willst. Um stattdessen den ganzen Lauf neu zu trainieren, drücke **Ein LoRA trainieren**.

### Alles ausführen {#run-all}

**Alles ausführen**, neben den dreien, führt Analysieren, Exportieren und Trainieren nacheinander aus, für einen Korpus, auf den du
lieber nicht wartest: Ein großer braucht Stunden zum Analysieren. Es fragt zuerst, was mit einer
früheren LoRA geschehen soll, und läuft dann bei geschlossener Seite weiter. Es analysiert nur, was es noch braucht, und ein
Song, dessen Analyse scheitert, wird aus dem Trainingsset herausgelassen und unter den Schaltflächen genannt. Texte,
die niemand geprüft hat, werden wie entworfen benutzt. **Stopp** beendet es, wo es ist, und behält, was fertig ist;
während des Exports gestoppt, stellt es zuerst das Trainingsset fertig. Es wartet auf alles, was die
Engine schon benutzt, bevor es trainiert. Ein Neustart der App beendet es, und **Alles ausführen** erneut macht weiter.

### Wenn der GPU-Speicher ausgeht {#running-out-of-gpu-memory}

Ein Auftrag, dem der GPU-Speicher ausgeht, sagt es, mit Vorschlägen: Schließe andere Programme, die die GPU benutzen,
senke die Längengrenze oder lass beim Training die längsten Songs weg. Stürzt die Engine ab und
startet neu, ist der Auftrag, den sie ausführte, verloren, und das sagt er auch.

### Die trainierte LoRA {#the-trained-lora}

Wenn das Training fertig ist, erscheint die LoRA mit ihrem Triggerwort in der Liste **Stil-LoRA**. Wählst du
sie, zeigt sie unter dem Stilfeld einen Chip für jeden Song, aus dem sie gelernt hat, und ein Klick setzt den Stil dieses Songs in
das Feld.
Ab einem Dutzend Songs grenzen ein Filterfeld und eine Reihe von Tags, die im Korpus wiederkehren (seine Genres,
Stimmungen und Instrumente), sie ein; klicke zwei Tags, um Songs mit beiden zu finden. Die Liste zeigt ihr
erstes Dutzend bis **Alle anzeigen**. Siehe **Planner und Klang ausbalancieren** unten für Startstärken. Um sie zu teilen, drücke **LoRA herunterladen** auf der Seite des Korpus oder **Herunterladen** unter
der Auswahl; siehe **Eine LoRA teilen** unten.

Um eine LoRA hinzuzufügen, die jemand geteilt hat, drücke **LoRA importieren** neben **Neues Korpus** und wähle dessen Zip. Um eine
anderswo aus dem exportierten Set trainierte LoRA zu benutzen, drücke **Ein LoRA installieren** und wähle die
Datei. Sie wird mit dem Triggerwort dieses Korpus zur Liste der Stil-LoRAs hinzugefügt.

**Einen Korpus löschen** entfernt die Kopien der App von seinen Songs, die getrennten Gesänge, die Texte und
die Partituren. Der Ordner, auf den du ihn gerichtet hast, und jede daraus gemachte LoRA bleiben unberührt.

---

## Urheberrecht und Einwilligung {#copyright-and-consent}

Womit du trainierst und was du mit dem Ergebnis machst, liegt in deiner Verantwortung nach dem Recht deines
Wohnorts. Die App bittet dich, es zu erklären, und prüft es nicht: Einen Korpus anzulegen verlangt, dass du bestätigst,
das Recht zu haben, mit diesen Aufnahmen zu trainieren.

Zwei Tatsachen sind gut zu wissen:

- Die YuE2-Gewichte stehen unter **CC BY-NC 4.0** — nicht kommerzielle Nutzung, egal was du daraus trainierst.
- Privat mit einem Korpus zu trainieren und die LoRA oder ihre Ausgabe zu veröffentlichen sind verschiedene Handlungen. Die zweite
  ist die, die meist eine Erlaubnis braucht: von dem, der die Rechte an den Aufnahmen hält, und bei
  einer erkennbaren Stimme vom Sänger.

LoRAs, die du nicht selbst trainiert hast, haben ihre eigenen Lizenzen: Lies sie auf der Seite, von der jede stammt
(siehe **Wo man Stil-LoRAs findet** unter Stil-LoRAs).

## Stil-LoRAs {#style-loras}

Eine LoRA ist eine kleine Datei, die das Modell zu einem Klang hinneigen lässt. Leg eine in `models/loras/` und drücke
**Neu einlesen** unter der Auswahl, oder nutze **Installieren**, und sie erscheint in der Liste **Stil-LoRA**.

Eine Stil-LoRA kann zwei Hälften enthalten, und die Auswahl zeigt, welche eine Datei enthält:

- **Planer** formt, was gespielt wird — den Partiturplan (Form, Harmonie, Phrasierung) und dann die Musik,
  die das Rendering aus dieser Partitur schreibt. Er wirkt in beiden Schritten.
- **Klang** formt das Audio — Klangfarbe und Produktion.

Eine Stärke, die die Datei nicht nutzen kann, ist ausgegraut, und eine Datei, die diese Engine gar nicht laden kann, wird als
solche benannt, statt still in einem Rendering zu scheitern.

### Wo man Stil-LoRAs findet {#where-to-find-style-loras}

Am schnellsten bei der Installation: Hake **Stil-LoRAs** auf der Komponentenseite des Installers an (oder führe mit Docker
`sh scripts/fetch-models.sh --loras` aus). Das holt 39 Stil-LoRAs ihrer Autoren, 3,8 GB insgesamt, jede mit einer
Beschreibung, die ihr Triggerwort und empfohlene Stärken nennt: die Sets unten, zwei von atomtanstudio (Dream Pop
und Old-School-Hip-Hop) und sechzehn Konzept-Regler von ntc-ai, die nur die Partitur formen (Klang tut nichts,
und sie brauchen kein Triggerwort). Sie sind unverändert gesammelt in
[pshields/yue2-style-loras](https://huggingface.co/pshields/yue2-style-loras), dessen README jeden Autor nennt
und auf die Seite verlinkt, von der die LoRA stammt. Eine LoRA, die schon unter demselben Namen in deinem Ordner liegt, bleibt, wie sie ist.

Auf Hugging Face gibt es mehr. Dies sind die dort gesammelten Sets, jedes auf der eigenen Seite seines Autors:

- [Militant reggae](https://huggingface.co/becausereasons/yue2-mltnt-militant-reggae)
- [Chanson française](https://huggingface.co/becausereasons/yue2-chnsn-chanson-francaise)
- [Canzone italiana](https://huggingface.co/becausereasons/yue2-cnzn-canzone-italiana)
- [Bulgarian voices](https://huggingface.co/becausereasons/yue2-blgr-bulgarian-voices)
- [Qawwali, sufi and tabla](https://huggingface.co/becausereasons/yue2-qwwl-qawwali-sufi-tabla)
- [J-pop](https://huggingface.co/storagejuju/yue2-jpop-t4-lora), eine einzelne LoRA nur mit einer Klang-Hälfte

Um eine hinzuzufügen, lade ihre `.safetensors`-Datei vom Reiter **Files** des Repositorys herunter, leg sie in `models/loras/`
und drücke **Neu einlesen**, oder drücke **Installieren** und wähle die Datei. Die Seite des Repositorys nennt das
Triggerwort und die empfohlenen Stärken jeder LoRA: Schreib sie in eine `.txt` neben die Datei (siehe **Beschreibungen** unten), und
die Auswahl zeigt sie und setzt das Triggerwort für dich an den Anfang des Stils. Eine LoRA von anderswo
ist womöglich in einem Format gespeichert, das diese Engine nicht laden kann: Die Auswahl benennt sie als solche, und sie richtet keinen Schaden an.

Jede LoRA trägt die Lizenz ihres Autors, die diese Sets als CC BY-NC 4.0 angeben: persönliche und nicht kommerzielle
Nutzung, wie die eigenen Gewichte von YuE2. Lies die Lizenz auf der Seite einer LoRA, bevor du sie benutzt oder teilst, was sie
erzeugt.

### Planner und Klang ausbalancieren {#balancing-planner-and-sound}

- **Einheitliche Korpora:** Eine LoRA, die auf einem einzigen Album oder einem einheitlichen akustischen Klang trainiert wurde (z. B. Folk-Rock der 1960er), verträgt höhere Stärken, typischerweise um **Planner ~0.85 / Klang ~0.80**.
- **Vielfältige Korpora:** Umfasst der Trainingskorpus mehrere Genres, Produktionsstile oder Epochen (z. B. akustischer Folk, Rock und Synth-Pop), können hohe Klang-Gewichte akustische Konflikte erzeugen. Bis etwa **Planner 0.70 / Klang 0.70** bleibt das Audio sauber, während die melodische Phrasierung und der Gesangscharakter des Künstlers erhalten bleiben.
- **Cover:** Deine Aufnahme legt die Melodie fest, also hat die LoRA weniger zu formen und die Klang-Hälfte wird stärker gefordert. Halte Klang nahe **0.50**.
- **Planvielfalt:** Mit einer aus einem Korpus trainierten LoRA ergibt **Ruhig** oder **Normal** das erkennbarste Ergebnis. **Ruhig** kann sich mit einer Stil-LoRA und einem kurzen Stil in Schleifen verfangen, und der Plan läuft dann
  minutenlang mit langen wiederholten Intros oder ohne Gesang. Beschreibe den Stil genauer (Genre, Instrumente und Gefühl) oder nutze **Normal**. Ein solcher Plan, oder einer, der viel länger ist als ein Song, wird noch einmal
  mit einem neuen Seed geschrieben, und der Take scheitert mit einem Rat, wenn der zweite genauso ausfällt.
- **Einen guten Take finden:** Der Charakter der LoRA hängt so sehr vom Wurf ab wie von den Stärken.
  Zwischen etwa 0.3 und 0.6 verändert **Klang** die Stimme wenig, also muss man es nicht hochdrehen.
  **Planer** verändert die Darbietung selbst, nicht nur die Stimme, also kann ein Wert, der zu einem Song passt,
  für einen anderen der schwächste sein. Behandle ihn wie den Seed: Probiere ein paar (etwa 0.6, 0.8 und 1.0) und ein
  paar Seeds mit **Erneut singen**, und behalte den Take, der dir gefällt.
- **Stärken speichern:** Wenn du das richtige Paar für eine LoRA gefunden hast, drücke **Stärken speichern** unter der
  Auswahl. Diese LoRA zu wählen beginnt dann bei ihnen, und sie reisen mit, wenn du sie teilst.

### Triggerwörter {#trigger-words}

Die meisten Stil-LoRAs sind auf Beschreibungen trainiert, die mit einem Triggerwort **beginnen**, und tun ohne es sehr wenig.
Die App kümmert sich darum: Eine LoRA zu wählen setzt ihren Trigger an den Anfang des Stils,
der Wechsel zu einer anderen tauscht ihn, Keine zu wählen entfernt ihn, und ein Rendering setzt ihn zurück, falls er
gelöscht wurde. Du wirst das Wort im Stilfeld erscheinen sehen — du kannst es bearbeiten oder verschieben.

### Beschreibungen {#descriptions}

Die Liste ist nach Sets gruppiert. Klicke eine Überschrift, um sie zu öffnen oder einzuklappen; die Auswahl merkt sich, welche du
offen gelassen hast, und die Gruppe mit deiner aktuellen Wahl öffnet sich immer mit.

Fahre über einen Eintrag, um zu lesen, was er ist, in den Worten seines Autors, mit dessen empfohlenen Stärken. Diese
Beschreibungen kommen aus einer Textdatei neben der LoRA:

```
CHNSN Rive Gauche
Trigger: chnsn
Step 200, the decoder-loss minimum. The more supple of the two: acoustic
narrative, yé-yé, female leads, waltz meters.
```

Die erste Zeile benennt sie, eine Zeile `Trigger:` wird zum Triggerwort, und der Rest ist die
Beschreibung. Eine eigene LoRA bekommt eine, indem du eine `.txt` daneben schreibst. `families.txt` im selben
Ordner gibt den Gruppen ihre Überschriften, ein `prefix = label` pro Zeile.

### Aus einem Korpus trainierte LoRAs {#loras-trained-from-a-corpus}

Eine aus einem deiner Korpora trainierte LoRA ist eine gewöhnliche Stil-LoRA: Sie erscheint in dieser Liste mit den
übrigen, ihr Triggerwort daneben, und es gelten dieselben zwei Stärken.

### Die Checkpoints ausprobieren {#trying-the-checkpoints}

Ein Trainingslauf speichert alle 50 Schritte einen Checkpoint und behält sie unter seiner LoRA in der Auswahl:
**▸ 9 Schritte** neben dem Namen der LoRA öffnet sie (die Einstellungen können sie stattdessen löschen, um
Platz zu sparen). Ein Checkpoint, dessen LoRA gelöscht wurde, bleibt unter **Trainings-Checkpoints**. Um
einige zu entfernen, drücke **Bearbeiten** beim Korpus: **Trainings-Checkpoints** dort listet die jedes Laufs, dieses Laufs
und früherer Läufe, mit ihren Größen. Hake die zu entfernenden an und drücke **Löschen**. Die fertige
LoRA wird nicht aufgeführt; sie hat ihr eigenes **LoRA löschen**. Jeder ist die LoRA so, wie sie an
diesem Punkt des Trainings stand. Sie klingen etwa gleich gut, aber jeder gewichtet das Gelernte auf seine Weise,
sodass jeder seinen eigenen Geschmack hat und dabei den Stil und den charakteristischen Klang behält, auf die die LoRA
trainiert wurde.

Um sie nebeneinander zu hören, wähle die LoRA, richte den Editor ein wie für einen Take und drücke
**Checkpoints** neben **LoRA löschen**. Bei einer LoRA ohne Checkpoints ist es ausgegraut. Hake die
gewünschten Schritte an, setze bei Bedarf eine Längengrenze für diese Takes und drücke **Rendern**. Die eigene
Aktion des Editors läuft einmal auf jedem Checkpoint, alle mit einem Seed, und jeder Take ist nach seinem Schritt benannt:
*Night drive · step 250*, *Night drive · full*. Sie werden in dem Take aufbewahrt, der im Editor offen ist,
oder, bei einem neuen Song, im letzten von ihnen (siehe **Takes in einem Take** unter Die Bibliothek). Der Editor schließt sich, sodass du wieder bei der Bibliothek bist,
wo die Takes entstehen. Ein Song oder ein Instrumental schreibt seinen Plan und geht direkt weiter zum
Rendern.

Bei einem Song oder Instrumental schreibt die LoRA die Melodie und formt den Klang, also ergibt derselbe
Seed nicht denselben Song: Jeder Checkpoint schreibt seine eigene Melodie und Struktur. Der Seed
wählt aus dem, was das Modell für wahrscheinlich hält, und jeder Checkpoint denkt ab der ersten Note ein wenig anders,
sodass die Pläne sich nach ein paar Takten trennen. Was bleibt, ist der Klang. Um nur den
Klang zu vergleichen, lade einen Plan mit **Partitur** und drücke **Diese Partitur rendern** nacheinander mit jedem Checkpoint.

Neue Dateien erscheinen, sobald die Engine `models/loras/` erneut angesehen hat, was sie tut, wenn die
Optionen neu geladen werden.

### Eine LoRA teilen {#sharing-a-lora}

Wähle eine LoRA und drücke **Herunterladen** unter der Auswahl: Du bekommst ein Zip mit der LoRA und ihrer Notiz.
Bei einer aus einem Korpus trainierten LoRA trägt die Notiz ihre gelernten Stile, also kommen die Chips mit.

Um eine hinzuzufügen, die dir jemand geschickt hat, drücke **Installieren** und wähle dessen Zip oder eine bloße `.safetensors`-
Datei. Sie kommt in `models/loras` unter der Überschrift **Installiert**, mit ihrem Namen, Triggerwort und
Chips. **LoRA löschen** entfernt die gewählte LoRA, ihre Notiz und ihre Gruppenzeile; **Neu einlesen** liest den Ordner
erneut, nachdem du von Hand eine Datei hinzugefügt hast.

---

## Stems {#stems}

Drücke **Stems** an einem Take. Wähle ein Modell, hake die gewünschten Teile an — Gesang, Schlagzeug, Bass, Sonstiges,
und bei manchen Modellen Gitarre und Klavier — und starte.

Die Trennung läuft auf der **GPU**, wenn die Engine Demucs hat, als Auftrag in der Warteschlange der Engine: Sie wartet auf ein
laufendes Rendering, geht dann schnell, und ein dahinter wartendes Rendering wartet seinerseits. Eine Engine, die vor
dieser Funktion gebaut wurde, eine trainierende LoRA (die die GPU hält), **Die GPU für Stems und Songtexte nutzen** in den Einstellungen auf Aus oder `STEMS_ON_GPU=0` lässt sie auf der **CPU**, was langsamer ist
und nie ein Rendering aufhält. *Feinabgestimmt* lässt vier Modelle nacheinander laufen für eine bessere Trennung und braucht etwa viermal
so lange.

Für eine Begleitspur wähle **Gesang und Instrumente**. Es teilt den Song in zwei: den Gesang und
**Instrumente**, alles andere als ein Stem. Entferne den Haken bei **Gesang**, um nur die Instrumente zu behalten. Es ist
dieselbe Trennung wie bei den vier Stems, wieder zusammengefügt, also dauert sie genauso lange und klingt genauso sauber.
Die *feinabgestimmte* lässt am wenigsten von der Stimme zurück.

Stems landen in `data/stems/<title>-<id>/`, spielen über die Chips auf der Karte und lassen sich einzeln oder als
Zip herunterladen. Sie bleiben, bis du sie löschst.

---

## Stoppen, Löschen und neu anfangen {#stopping-deleting-and-starting-again}

Woran die Engine arbeitet, zeigt sich in der oberen Leiste neben dem Namen: eine Pille mit dem Auftrag, seiner Zeit, einer Linie
an ihrem Fuß dafür, wie weit er ist, und wie viele Aufträge danach warten. Sie ändert sonst nichts auf der Seite, wenn ein
Auftrag beginnt oder endet. Klicke darauf für die Auftragskarte: die Stufe, **stopp** und **Als Nächstes**, die wartenden Aufträge, jeder mit
**abbrechen**.

Ein wartender oder laufender Take zeigt **Abbrechen** auf seiner Karte, und **stopp** auf der Auftragskarte stoppt, woran
die Engine gerade arbeitet. Der Titel eines Takes auf der Auftragskarte, in ihrer Liste **Als Nächstes** oder im Player am
Fuß der Seite führt dich zum Take: in seinen Bereich, wobei eine Suche oder ein Filter, der ihn verbirgt, aufgehoben wird. Einen Take zu löschen stoppt seinen Auftrag und entfernt seine Stems. **Löschen** neben einer
Aufnahme entfernt die Datei und ihre Stems; daraus gemachte Cover behalten ihr Audio und ihre Partitur, können aber nicht
erneut gerendert werden.

**+ Song**, **+ Cover** und **+ Instrumental** im Take-Bereich, oder **Neuer Song** neben der
Überschrift des Editors, beginnen neu ausgehend vom gezeigten Take. Sie leeren Titel, Text und Partitur
und beginnen mit den Standards: ein leerer Stil (mit dem Triggerwort einer gewählten LoRA), die übliche Längen-
grenze, Harmonie Abwechslungsreich, Planvielfalt normal, Interpretation Weit, Produktionsschliff an,
Normalisieren aus und ein neuer Seed, der nicht festgehalten wird. Eine gewählte LoRA und eine gewählte Aufnahme bleiben gewählt.
Der gezeigte Take löst sich vom Editor, sodass Rendern nicht versehentlich auf ihn wirken kann.

Wörter, die du getippt, aber nicht benutzt hast, werden nicht weggeworfen: Eine Leiste bietet an, sie wiederherzustellen.

## Die Bibliothek {#the-library}

### Bereiche {#spaces}

Takes leben in **Bereichen**: ein Bereich pro Song, pro Album oder für Skizzen. Der Name des Bereichs über den Takes
ist der gezeigte, und alles, was du machst, landet dort. Klicke darauf für die Liste der Bereiche: Tippe, um einen nach
Namen zu finden, oder wähle ihn mit den Pfeiltasten und Enter. Die fünf zuletzt benutzten kommen zuerst, dann jeder Bereich, jeder mit
der Zahl seiner Takes. **Neuer Bereich**, **Diesen Bereich umbenennen**, **Take importieren…** und **Diesen Bereich löschen** stehen am
Fuß der Liste. Einen Bereich zu löschen löscht nie Takes —
sie wandern nach Default. Aufnahmen teilen sich alle Bereiche, sodass eine Aufnahme in
mehreren gecovert werden kann.

Die Ordner-Schaltfläche auf einer Karte verschiebt diesen Take in einen anderen Bereich, mit den Takes darin.

### Takes in einem Take {#takes-inside-a-take}

**Variationen**, **Mehr versuchen** und **Checkpoints** machen jeweils mehrere Takes eines Songs. Sie werden
**in** dem Take aufbewahrt, aus dem sie gemacht wurden, sodass der Bereich deine Songs auflistet und nicht jedes Rendering davon.
Checkpoints wird im Editor gedrückt: Mit einem dort offenen Take kommen seine Takes in diesen Take; bei
einem neuen Song, der noch keinen Take hat, enthält der Take des zuletzt angehakten Checkpoints (die fertige LoRA, wenn
sie dabei ist) die anderen.

- **Die Schaltfläche Inhalt** erscheint unter den kleinen Schaltflächen oben auf einer Karte, sobald ihr Take
  Takes enthält, fertige oder noch entstehende, und sie **leuchtet orange**. Fahre darüber, um zu lesen, wie viele
  fertig sind und wie viele noch kommen. Die Karte selbst ist deutlich heller als die anderen (im
  hellen Design ein warmer Ton), sodass ein Take mit Takes darin in einer Liste auffällt. (Die Schaltfläche des Mastering-Racks daneben leuchtet auf
  dieselbe Weise grün, wenn der Take gemastert ist.)
- **Klicke darauf**, und unter der Karte öffnet sich ein Bereich mit den Takes darin, jeder eine eigene Karte. Ein
  Take erscheint dort, wenn er fertig ist; solange er entsteht, erscheint nur der Take, zu dem er gehört.
  Klicke die Schaltfläche erneut oder **Schließen**, um ihn zu schließen.
- **Ein Take in einem anderen ist ein Take wie jeder andere.** Spiel ihn ab, gib ihm einen Stern, speichere ihn, teile ihn in
  Stems, benenne ihn um und doppelklicke ihn, um seinen Song und seine Partitur zu öffnen.
- **Eine Ebene.** Ein Take in einem anderen enthält selbst keine, also hat seine Karte keine Variationen oder Mehr
  ausprobieren, und **Checkpoints** im Editor ist ausgegraut, solange er dort der offene Take ist. **Herausnehmen** (der Pfeil, der eine Box verlässt) macht ihn zu einem eigenen Take in der Liste des Bereichs, und dann geht es.
- **Die Werkzeuge der Liste folgen dem Bereich.** Solange einer offen ist, wirken **Alle auswählen**, **Markiert**, die Art-
  Schalter, **Vergleichen**, **Löschen** und Zurück und Weiter des Players auf die Takes im
  Bereich. Der Take, dessen Bereich offen ist, bleibt auf der Seite, egal was die Filter sagen.
- **Was drinnen spielt, wird draußen gezeigt.** Schließt du den Bereich, während ein Take darin
  spielt, leuchtet die Abspiel-Schaltfläche des Takes, der ihn enthält, golden, sodass du siehst, woher der Klang
  kommt. Grün heißt weiterhin, dass dieser Take selbst spielt.
- **Die Suche findet sie** wie jeden anderen Take, wo immer sie sind. Solange eine Suche läuft, wird das Gefundene
  als einfache Karten gezeigt, und ein Take in einem anderen sagt, in welchem.
- **Einen Take zu löschen löscht die Takes darin.** Die Warnung sagt, wie viele. Nimm vorher heraus, was du
  behalten willst.

Takes, die vor dieser Funktion gemacht wurden, bleiben, wo sie sind, nebeneinander in der Liste.

### Karten {#cards}

Jede Karte nennt die Einstellungen, die den Take geformt haben — Harmonie, Interpretation, Planvielfalt, die LoRA und
ihre Stärken, den Seed, die Engine, die ihn gerendert hat, und sein Alter —, sodass eine Karte sich wie das Rezept liest, das ihn gemacht hat.

**Speichern** fragt, in welchem Format der Take heruntergeladen werden soll, FLAC, WAV oder MP3. Es beginnt mit dem, was du zuletzt gespeichert
hast, und beim ersten Mal ist nichts gewählt. Ein Take mit Bild kann auch als **Video** gespeichert werden: ein MP4 des
Songs, das das Bild zeigt, das seine Karte zeigt (H.264-Video, AAC-Audio mit 192 kbps). Messenger-Apps wie
WhatsApp senden und spielen es als Video, wo eine Audiodatei als Dokument geht. Mit eingeschaltetem Mastering-Rack hat das
Video den gemasterten Klang, wie die anderen Formate. **Take** daneben speichert zusätzlich das Rezept des Takes: eine kleine Datei
(`<title>.yeufonic.json`) mit seinem Text, Stil und seiner Partitur, seinen Seeds und Einstellungen, seinen LoRAs nach Namen und
den Einstellungen des Mastering-Racks, aber nicht seinem Audio. Ist auch ein Format gewählt, kommt beides in einem Zip; drücke das
gewählte Format erneut, um nur das Rezept zu speichern. Die Datei enthält nichts von deiner Installation (keine Pfade, IDs oder Schlüssel),
also kann sie behalten oder mit einem anderen Yeufonic-Nutzer geteilt werden.

**Take importieren…** in der Liste der Bereiche macht aus einer solchen Datei einen neuen Take im gezeigten Bereich; die Datei
auf die Bibliothek zu ziehen tut dasselbe. Der Take enthält den Plan, bereit zum Rendern, sodass er vorher geprüft oder geändert werden kann.
Beide Engines können ihn rendern: Dieselbe Partitur und derselbe Seed auf derselben Engine ergeben einen sehr ähnlichen Take, auf der anderen
Engine einen anderen. Eine genannte LoRA, die hier nicht installiert ist, wird beim Import genannt, sodass du
sie installieren oder vor dem Rendern eine andere wählen kannst. Die Aufnahme eines Covers ist nicht in der Datei, also kommt ein geteiltes Cover
als Song mit der Partitur und dem Text des Covers herein und lässt die Einstellungen zurück, die zu seiner Aufnahme gehörten (die
Tempo-Fixierung, Harmonie, Stimmanweisungen und die Längengrenze): Ein neuer Plan daraus beginnt wie ein Song aus einem Prompt.

**Takes durchsuchen** findet die Takes, bei denen jedes eingetippte Wort irgendwo im Titel, Stil, Text oder
LoRA-Namen steht, unabhängig von Groß- und Kleinschreibung. Sie durchsucht den gezeigten Bereich; **Alle Bereiche**, daneben, sobald du tippst,
durchsucht jeden Bereich, und eine Karte aus einem anderen Bereich sagt, aus welchem. × oder Escape leert sie. Das
Feld beginnt bei jedem Öffnen der Seite leer und bietet deine letzten Suchen an, die etwas gefunden haben:
Klicke eine an oder wähle sie mit den Pfeiltasten und Enter.

**Song**, **Cover** und **Instrumental** zeigen Takes dieser Arten: Lass einen oder mehrere leuchten, oder keinen für alle Arten.
**Markiert** zeigt nur Takes mit Stern; klicke erneut, um alle zu zeigen. Die Symbole daneben legen fest, wie die Takes
angeordnet sind, die benutzten grün leuchtend: breitere **komfortable** Karten mit mehr vom Prompt oder schmalere **kompakte**,
die **ganze Breite** des Fensters oder eine zentrierte Spalte, und jeder Take auf seine Kopfzeile **eingeklappt**. Fahre über
ein Symbol, um zu lesen, was ein Klick tut.

Hake Takes an, und die Zeile bietet statt der Arten und der Anordnung an, was mit ihnen getan werden kann: wie viele
gewählt sind, **Vergleichen**, **Löschen** und **Fertig**, das die Haken entfernt. **Alle auswählen** am Ende der Zeile hakt
jeden gezeigten Take an. Ein Titel bleibt immer auf einer Zeile und endet mit …, wenn er lang ist. Fahre über Titel, Einstellungen oder Stil einer Karte, um alles zu lesen.

### Ein Bild für jeden Take {#a-picture-for-each-take}

Jeder neue Take bekommt ein Bild des Songs, blass hinter der Karte des Takes gezeigt, oben im Take-Bereich, wenn du ihn wählst, und hinter dem Editor, wenn der Take dort
offen ist. Auf diesem PC gezeichnet, wartet es, bis kein Song entsteht, hält also nie einen Plan oder ein Rendering auf, und
erscheint kurz nachdem der Song fertig ist; von einer externen LLM gezeichnet, entsteht es, während der Take rendert.
Es entsteht in zwei Schritten: Titel, Stil und erste Worte des Takes werden zu einer **Beschreibung**
eines Bildes, dann **zeichnet** ein Bildmodell es auf Weiß, und das Weiß wird herausgenommen, sodass das Bild
einen transparenten Hintergrund hat. Ein Take, der in einem anderen entstand (Mehr ausprobieren, Variationen, Checkpoints), zeigt das
Bild des Takes, in dem er steckt, statt ein eigenes zu haben.

Ein Bildmodell zeichnet keine echte Band oder Person, also lässt die Beschreibung Namen weg; und die
eigene Schrift des Bildes bleibt weich, damit sie nicht mit der der Karte kämpft.

#### Zwei Wege zu zeichnen: FLUX.2 klein auf diesem PC oder eine externe LLM {#two-ways-to-draw-flux-2-klein-on-this-pc-or-an-external-llm}

Bilder brauchen etwas, das zeichnen kann. Es gibt zwei, und du kannst eines, beide oder keines haben.

| | FLUX.2 klein, auf diesem PC | Das Bildmodell deiner externen LLM |
|---|---|---|
| Was es ist | ein kleines Bildmodell, das auf der Engine läuft, neben YuE2 | das eigene Bildmodell des Anbieters, etwa das von Gemini |
| Was es kostet | nichts; etwa 8 GB Festplatte | jedes Bild ist eine Anfrage an den Anbieter, die kostenpflichtig sein kann |
| Was den PC verlässt | nichts: Die Beschreibung schreibt Gemma auf diesem PC, oder sie entsteht aus dem Take selbst | Titel, Stil und erste Worte des Takes und die Beschreibung |
| Wann es läuft | auf der GPU, sobald kein Song entsteht: nach deinem Song, nie ihm im Weg | neben den Renderings, während sie laufen |
| Was du einrichtest | eine Installationsoption | die externe LLM in den Einstellungen, mit einem Anbieter, der ein Bildmodell anbietet |

**Um auf diesem PC zu zeichnen, installiere FLUX.2 klein.**

- **Windows:** Hake **FLUX.2 [klein]** auf der Komponentenseite des Installers an. Es ist nicht angehakt,
  wenn du es nicht wählst. Eine installierte App bekommt dieselbe Seite bei einem Update, oder führe den Installer erneut
  von der Release-Seite aus: Der Haken wird danach gemerkt, und ein Update lädt es nie zweimal herunter. Es
  sind drei Dateien, etwa 8 GB insgesamt.
- **Docker:** Führe `sh scripts/fetch-models.sh --pictures` aus, das die drei Dateien in `models/`
  (`diffusion_models`, `text_encoders` und `vae`) legt und jede prüft, und starte dann die App mit
  `docker compose restart app` neu, damit sie sie findet.

**FLUX.2 klein 9B, wenn du die Grafikkarte dafür hast.** klein gibt es in einer größeren Ausführung, einem Modell höherer
Qualität, das mehr Details und bessere Hände und Gesichter zeichnet, nur für Grafikkarten mit mehr Video-
speicher gedacht. Yeufonic lädt es nie herunter, weil seine Dateien auf Hugging Face zugangsbeschränkt sind und unter der **nicht kommerziellen Lizenz**
von Black Forest Labs stehen, aber leg sie an ihren Platz, und sie werden benutzt.

- **Festplatte:** etwa 18 GB für das übliche Paar, das FP8-Modell und seinen FP8-Textencoder (16 GB mit dem FP4-
  Encoder), neben den Dateien des 4B. Es braucht das VAE des 4B (`flux2-vae.safetensors`), also installiere zuerst den 4B.
- **Videospeicher:** Es läuft auf einer 16-GB-Karte, belegt beim Zeichnen aber fast alles, mit freiem Speicher
  nahe null. Bilder warten, bis kein Song entsteht, also bremst das deine Songs nicht, aber andere
  Programme, die gleichzeitig die Grafikkarte nutzen, können Mühe haben. Mit weniger Speicher läuft es trotzdem, langsamer,
  während die Engine das Modell ein- und auslagert; dort ist der 4B die bessere Wahl.

1. **Das Modell.** Melde dich bei Hugging Face an, akzeptiere die Lizenz auf
   [black-forest-labs/FLUX.2-klein-9b-fp8](https://huggingface.co/black-forest-labs/FLUX.2-klein-9b-fp8)
   und lade `flux-2-klein-9b-fp8.safetensors` (9,4 GB) herunter. Oder nimm das volle
   `flux-2-klein-9b.safetensors` von [black-forest-labs/FLUX.2-klein-9B](https://huggingface.co/black-forest-labs/FLUX.2-klein-9B),
   das für einen Mac, das etwa doppelt so groß ist und doppelt so viel Speicher braucht.
   Es kommt in den Ordner `diffusion_models`.
2. **Sein Textencoder.** Lade von [Comfy-Org/Flux-2-Klein-9B](https://huggingface.co/Comfy-Org/Flux-2-Klein-9B/tree/main/split_files/text_encoders),
   wofür keine Anmeldung nötig ist, einen dieser herunter und leg ihn in den Ordner `text_encoders`:
   `qwen_3_8b_fp8mixed.safetensors` (8,7 GB, die übliche Wahl bei einer NVIDIA-Karte), `qwen_3_8b_fp4mixed.safetensors`
   (6,8 GB, der kleinste) oder `qwen_3_8b.safetensors` (16,4 GB, volle Genauigkeit, für einen Mac).
   **Mit der yue2.cpp-Engine** kann der Bildserver diese Encoder nicht lesen: Nimm stattdessen `Qwen3-8B-Q4_K_M.gguf`
   (5,0 GB) von [unsloth/Qwen3-8B-GGUF](https://huggingface.co/unsloth/Qwen3-8B-GGUF)
   (`-Q8_0.gguf`, 8,7 GB, geht auch) und leg es in denselben Ordner.
3. **Wo die Ordner sind:** unter `models/` im Yeufonic-Ordner bei **Docker**; unter
   `engine\ComfyUI\models` im Installationsordner unter **Windows**; unter `engine/ComfyUI/models/` im
   Installationsordner auf einem **Mac**.
4. **Lass die App sie sehen, und wähle es.** Starte Yeufonic neu (mit Docker `docker compose restart app`)
   und setze dann **Take-Bilder: Modell** in den Einstellungen auf *FLUX.2 klein 9B*. Bis dahin zeichnet der 4B, und
   die Einstellungen sagen es, wenn der 9B gewählt ist, hier aber nicht zeichnen kann. Wähle
   *4B*, um zurückzugehen, ohne etwas zu entfernen. Die Notiz zum Bild im Editor sagt, wer es gezeichnet hat
   (*drawn by FLUX.2 klein 9B on this PC*).

Das Modell und sein Encoder werden nur unter diesen Namen gefunden, also behalte die Dateinamen so, wie sie heruntergeladen werden.

**FLUX 3 klein, für Schrift und eine Karte ab 12 GB.** FLUX 3 Image Klein von Black Forest Labs zeichnet aus einer
vollständigen Beschreibung der Szene, und genau das sind die von Gemma oder der externen LLM geschriebenen Bild-Prompts, und es
setzt Schrift gut, was zu **Take-Bilder: Songtitel auf dem Bild** passt. Wie den 9B lädt Yeufonic es nie herunter: Seine Dateien sind
auf Hugging Face zugangsbeschränkt und stehen unter der **FLUX Kommunity License** (nicht kommerzielle Nutzung, und kommerzielle Nutzung dessen, was es
zeichnet, für alle unter der Umsatzgrenze der Lizenz; lies sie, bevor du sie akzeptierst). Leg seine Dateien an ihren Platz, und es
kann gewählt werden.

- **Festplatte:** etwa 11 GB für das int8-Paar, neben den Dateien des 4B. Es nutzt das VAE des 4B (`flux2-vae.safetensors`),
  also installiere zuerst den 4B.
- **Videospeicher:** etwa 11 GB beim Zeichnen. Es braucht ein Mehrfaches der Schritte der FLUX.2-kleins, also dauert jedes
  Bild länger.
- **Engine:** vorerst nur die ComfyUI-Engine; mit der yue2.cpp-Engine wird es nicht angeboten.

1. **Melde dich bei Hugging Face an** und akzeptiere die Lizenz auf
   [black-forest-labs/flux-3-image-klein-comfy](https://huggingface.co/black-forest-labs/flux-3-image-klein-comfy).
2. **Das Modell,** in den Ordner `diffusion_models`: `flux3-image-klein-int8-convrot.safetensors` (5,8 GB, die übliche
   Wahl bei einer NVIDIA-Karte), `flux3-image-klein-nvfp4.safetensors` (5,3 GB, für eine RTX-50-Karte) oder
   `flux3-image-klein-bf16.safetensors` (11,1 GB, volle Genauigkeit, für einen Mac).
3. **Sein Textencoder,** in den Ordner `text_encoders`: `qwen3vl_4b_int8_convrot.safetensors` (4,9 GB) oder
   `qwen3vl_4b_bf16.safetensors` (8,9 GB, für einen Mac).
4. **Lass die App sie sehen, und wähle es:** Starte Yeufonic neu (mit Docker `docker compose restart app`) und setze dann
   **Take-Bilder: Modell** in den Einstellungen auf *FLUX 3 klein*. Die Notiz zum Bild im Editor sagt *drawn by
   FLUX 3 klein on this PC*.

Die Ordner sind dieselben wie beim 9B, und die Dateien werden nur unter diesen Namen gefunden.

**FIBO 2.0, für den Look einer Fotografie und eine 16-GB-Karte.** Brias FIBO 2.0 zeichnet am nächsten an einer echten
Fotografie der Plattenhüllen, nach denen die Bilder gestaltet sind: schärfere Details, eine natürliche Schärfentiefe,
die Farben eines Films und mehr von dem, was die Beschreibung verlangt. Auch FIBO lädt Yeufonic nie herunter. **Seine
Lizenz ist CC BY-NC 4.0: nur nichtkommerzielle Nutzung.** Die Lizenz von FLUX 3 erlaubt jemandem unter ihrer
Umsatzgrenze, das Gezeichnete kommerziell zu nutzen; bei FIBO braucht jede kommerzielle Nutzung, auch ein Cover für einen
Song, den du verkaufst, eine Vereinbarung mit Bria. Lies die Lizenz, bevor du es nutzt.

- **Festplatte:** etwa 10,4 GB, das Modell und sein Turbo-Zusatz. Es liest den Textencoder von FLUX 3 und das VAE des
  4B; mit installiertem FLUX 3 wird also nichts weiter gebraucht.
- **Videospeicher:** etwa 12,5 GB beim Zeichnen, also eine 16-GB-Karte. Eine kleinere Karte lagert einen Teil aus, was
  viel langsamer ist.
- **Zeit:** mit dem Turbo-Zusatz etwa so lange wie FLUX 3. Ohne ihn zeichnet FIBO mit seinen eigenen Einstellungen,
  etwa achtmal so lange.
- **Die Hülle:** von FIBO gezeichnet hat der Rand um die Fotografie keine dünne dunkle Linie; FIBO zeichnete sie als
  dicke Balken und einen Kasten um den Titel.
- **Engine:** nur die ComfyUI-Engine.

1. **Das Modell,** von [Comfy-Org/Fibo-2.0](https://huggingface.co/Comfy-Org/Fibo-2.0), ohne Anmeldung, in den Ordner
   `diffusion_models`: `fibo2_dev_int8_convrot.safetensors` (8,4 GB, die übliche Wahl bei einer NVIDIA-Karte) oder
   `fibo2_dev_bf16.safetensors` (16,5 GB, volle Genauigkeit, für einen Mac).
2. **Sein Turbo-Zusatz,** von derselben Seite, in den Ordner `loras`:
   `fibo_2.0_turbo_lora_avg_rank_270_bf16.safetensors` (2 GB). Er ist kein Stil-LoRA und wird nicht als solches angeboten.
3. **Sein Textencoder,** falls FLUX 3 nicht installiert ist: `qwen3vl_4b_int8_convrot.safetensors` (4,9 GB) oder
   `qwen3vl_4b_bf16.safetensors` (8,9 GB, für einen Mac), von derselben Seite, in den Ordner `text_encoders`.
4. **Lass die App sie sehen, und wähle es:** Starte Yeufonic neu (mit Docker `docker compose restart app`) und setze dann
   **Take-Bilder: Modell** in den Einstellungen auf *FIBO 2.0*. Die Notiz zum Bild im Editor sagt *drawn by FIBO 2.0
   on this PC*.

**Um mit einer externen LLM zu zeichnen,** öffne die Einstellungen und setze **LLM für Songtexte & Stil-Tags** auf die
[externe LLM](#external-llm), mit ihrer **API-URL**, ihrem **API-Schlüssel** und ihrem **Modell**, wie für Songtexte. Der Anbieter muss ein Bild-
modell haben: Gemini hat eines (`gemini-3.1-flash-image` wird benutzt, wenn du kein anderes nennst), und ein OpenAI-kompatibler
Anbieter wird nach `gpt-image-1` gefragt. Die App fragt den Anbieter im Hintergrund nach seiner Modellliste,
wenn die App startet, wenn sich diese Einstellungen ändern und alle paar Stunden, und zeichnet dort erst, wenn die Liste
das Bildmodell enthält.

Mit keinem von beiden sagt **Take-Bilder** in den Einstellungen **Keine Bilder: der Standardhintergrund**, mit einer Zeile, wie man sie
bekommt, und die Wahl, welche zu machen, kann nicht getroffen werden.
Richte eines ein, und sie gehen an: Bilder werden dann für die Takes gemacht, die du ab da machst.

#### Bilder in den Einstellungen verwalten {#managing-pictures-in-settings}

| Einstellung | Bewirkt |
|---|---|
| **Take-Bilder** | *Für jeden neuen Take eins machen* (der Standard, wo etwas zeichnen kann) oder *Nur auf Anfrage*, wo ein Take den Standardhintergrund behält, bis du eins über sein Quadrat oder die Schaltfläche Bild im Editor machst. Die Einstellungen darunter formen ein Bild in beiden Fällen. Es heißt *Keine Bilder*, solange hier nichts zeichnen kann. |
| **Take-Bilder: gezeichnet von** | *Dieser PC, wenn klein installiert ist, sonst die externe LLM* (der Standard), *Dieser PC (das Modell unten)* oder *Das Bildmodell der externen LLM*. Welches klein auf diesem PC zeichnet (FLUX.2 klein 4B oder 9B oder FLUX 3 klein), wird unter **Modell** gewählt. FIBO 2.0 wird ebenfalls dort gewählt. |
| **Take-Bilder: Modell** | *FLUX.2 klein 4B* (der Standard), *FLUX.2 klein 9B*, *FLUX 3 klein* oder *9B, wo seine Dateien installiert sind, sonst 4B*. Nur für auf diesem PC gezeichnete Bilder. Der 9B und FLUX 3 werden nie für dich installiert: siehe [FLUX.2 klein 9B und FLUX 3 klein](#two-ways-to-draw-flux-2-klein-on-this-pc-or-an-external-llm) oben. Wird eines verlangt, ist aber nicht da, zeichnet ein anderes, und die Einstellungen sagen, welches. *FIBO 2.0* wird ebenfalls von Hand hinzugefügt und ist nur für nichtkommerzielle Nutzung: siehe oben. |
| **Take-Bilder: beschrieben von** | wer den Bild-Prompt schreibt, aus dem Titel des Takes, dem Kunststil unten, seinem Stil und seinem Text (bis zu 50 Zeilen). *Lokales Gemma, wenn installiert, sonst der Take selbst* (der Standard), egal wer zeichnet. *Lokales Gemma*: auf diesem PC geschrieben; braucht die Option Songtext-Entwürfe. *Aus dem Take selbst*: keine LLM; eine Beschreibung aus Titel, Stil und ersten Worten des Takes, am schnellsten, und nichts wird dafür verschickt. Oder die *Externe LLM*, eine Anfrage pro Bild; ist sie nicht erreichbar oder wechselst du für die Sitzung zu lokalen LLMs, schreibt Gemma sie stattdessen, wenn es installiert ist. |
| **Take-Bilder: Kunststil** | wie das Bild aussehen soll, an die LLM gegeben, die den Bild-Prompt schreibt (ausgegraut, wenn der Take sich selbst beschreibt). Standardmäßig ein abstraktes, surrealistisches Design im Stil von Albumcovern der 1970er und 1980er, ohne Text oder Menschen. Geleert geht es dorthin zurück. |
| **Take-Bilder: dein eigener Prompt** | Wörter, mit denen der Bild-Prompt jedes Bildes beginnt, etwa *salt marsh, overcast*, bis zu 512 Zeichen; der Prompt, den die LLM schreibt, folgt darauf. Leer (der Standard): keine. Nur, wenn eine LLM den Bild-Prompt schreibt (ausgegraut, wenn der Take sich selbst beschreibt). |
| **Take-Bilder: Songtitel auf dem Bild** | *Aus* (der Standard) oder *An*: Der Titel des Songs wird fett auf das Cover geschrieben, in Groß- oder Kleinbuchstaben, wie du ihn geschrieben hast, selbst wenn er der Name eines Künstlers ist (das Bild selbst wird trotzdem ohne ihn beschrieben). Meist wird das Bild von einer dünnen dunklen Linie in einem gebrochen weißen Rand gerahmt, wie auf vielen Hüllen der 1970er, mit dem Titel zentriert in einem tieferen Band oben oder unten. Etwa eines von fünf hat keinen Rand: Der Titel steht über dem Bild, in einer Ecke oder zentriert oben oder unten, in einer gedämpften Farbe aus dem Bild, und die LLM wird gebeten, diesen Teil des Bildes dafür frei zu halten. All das wird für jedes Bild zufällig gewählt. FLUX.2 klein schreibt ihn womöglich nicht ganz richtig. Nur, wenn eine LLM den Bild-Prompt schreibt. |
| **Take-Bilder: Bildmodell** | welches Modell des Anbieters zeichnet. Nur für von der externen LLM gezeichnete Bilder (wähle es unter **Gezeichnet von**; sonst ausgegraut), und leer für das übliche des Anbieters, was fast immer das ist, was du willst. |

Mit installiertem FLUX.2 klein und den Einstellungen, wie sie kommen, entstehen Bilder also vollständig auf diesem PC, selbst
wenn die externe LLM deine Songtexte schreibt: Gemma schreibt jeden Bild-Prompt, wo Songtext-Entwürfe installiert sind, und
ohne es entsteht die Beschreibung aus dem Take selbst, ohne LLM, was keine Zeit kostet. Wähle *Das Bildmodell der externen
LLM*, damit stattdessen der Anbieter sie zeichnet, oder setze **beschrieben von** auf *Aus dem Take selbst* für die
schnellsten Bilder oder auf *Externe LLM* (eine Anfrage pro Bild).

#### Das Bild eines Takes im Editor {#a-take-s-picture-in-the-editor}

Das Symbol **Bild** in der oberen Zeile des Editorfensters, neben den anderen Schaltflächen des Takes, zeigt das Bild
mit zwei Möglichkeiten: **Ein neues Bild machen**, das es im Hintergrund neu macht, und **Den Standardhintergrund verwenden**, das es endgültig entfernt: Für diesen Take wird kein Bild mehr gemacht, es sei denn, du bittest darum.
Klicke dort auf das Bild, um es ganz zu sehen, so groß, wie das Fenster erlaubt; ein Klick irgendwo oder Escape
legt es weg und lässt den Editor, wie er war. Das ganze Bild hat dieselben zwei Möglichkeiten darunter. Wähle
dort **Ein neues Bild machen**, und das Bild bleibt stehen, während das neue entsteht, mit dem, was gerade passiert, zwischen
den Schaltflächen angezeigt, und wechselt dann zum neuen, wenn es fertig ist.

Auf der Karte eines Takes zeigt das Quadrat oben links das Bild, wenn du darauf zeigst. Ein Take ohne
Bild bietet dort stattdessen **Ein neues Bild machen** an, wo dieser PC Bilder machen kann.

### Takes vergleichen {#comparing-takes}

Hake zwei bis sechs Takes an und drücke **Vergleichen** (es erscheint neben Alle auswählen, sobald zwei angehakt sind, und
wartet auf Takes, die noch rendern). Die Takes stapeln sich in einem Fenster auf einer gemeinsamen Position: Drücke **1** bis
**6** oder klicke einen an, um zu wechseln, und er macht vom selben Moment im Song aus weiter, spielend oder
pausiert. **Leertaste** spielt und pausiert, die Pfeile springen 5 Sekunden, und der Stern markiert den, der dir
lieber ist. **Lautheit angleichen** dreht die lauteren Takes auf den leisesten herunter, da ein lauterer Take dazu neigt,
besser zu klingen; **Namen verbergen** mischt die Takes und nennt sie Take A, B, C für einen Blindtest.

### Der Player {#the-player}

Klicke oder ziehe auf der Wellenform, um zu springen. Zurück und Weiter gehen die Karten in der angezeigten Reihenfolge durch.

| Taste | Bewirkt |
|---|---|
| Leertaste | abspielen oder pausieren |
| Links, Rechts | fünf Sekunden zurück oder vor |
| Shift+Links, Shift+Rechts | der vorige oder nächste Take; in der Ansicht Playlists der vorige oder nächste Song der Playlist |
| Hoch, Runter | Lautstärke |

Die Medientasten des Systems funktionieren auch. Die eigenen Tasten des Takes stehen unter [Tastenkürzel](#hot-keys).

### Der Audio-Visualizer und synchronisierter Text {#the-audio-visualizer-and-synced-lyrics}

Drücke **Visualizer** in der Transportleiste (oder **V**, während ein Track spielt), um die Vollbild-Bühne des Visualizers zu öffnen.

Die Bühne zeigt Audio-Visualisierungen in Echtzeit, synchron zum Abspielen:

- **Visualizer-Modi:** Wähle in der oberen Leiste aus elf verschiedenen Visualizern:
  - *Yeufonic:* Das Logo selbst, atmend — die Kachel glüht mit dem Bass und weitet sich auf dem Schlag, jeder Gabelarm ist eine Anzeige mit seiner eigenen Hälfte des Spektrums, und der grüne Punkt flammt auf dem Schlag auf.
  - *Wellenband:* Schwebende harmonische Doppelbänder als reaktive Wellen.
  - *Polarlicht:* Wogende Vorhänge ätherischen Nordlichts, die auf mittlere und hohe Frequenzen reagieren.
  - *Kosmischer Nebel:* Sternenfeld und wirbelnder interstellarer Partikelnebel, im Takt pulsierend.
  - *Kaleidoskop:* Radiale geometrische Symmetrien, die mit dem musikalischen Tempo pulsieren.
  - *Neon-Gitter:* Retro-futuristische Synthwave-Drahtgitterfläche in Perspektive, die zu Basslinien wogt.
  - *Flüssige Verzerrung:* Fließende harmonische Wellenverschiebung einer Oberfläche.
  - *Partikelschwarm:* Gravitative Partikelhaufen, die bei Schlagzeugtreffern zerstreuen.
  - *Hi-Fi-Spektrumbalken:* Mehrband-Spektrumanalysator mit physikalisch schwebenden, abklingenden Spitzenkappen.
  - *Artwork:* Das Bild des Takes, groß, mit seinem Titel darunter, über einer weichen Kopie seiner selbst, die sich mit der Musik bewegt. Ein Take ohne Bild zeigt die Yeufonic-Szene, bis eins gemacht ist.
  - *Keins:* Nur das Bild des Takes, unbewegt, auf dunklem Grund, oder das Yeufonic-Zeichen, wenn er keins hat. Nichts bewegt sich: für einen Computer, dem die anderen Szenen zu viel sind.
- **Hinter den Szenen:** Die Szenen Artwork, Yeufonic, Mandala, Gitter, Flüssig und Balken spielen über dem Bild des Takes, sanft mit der Musik bewegt, wo der Take eines hat. Darüber kann sich auch etwas bewegen, in den eigenen Farben des Bildes: *Atem* (das Bild allein), *Lichtstrahlen*, die sich aus der Mitte drehen, *Wellen*, die auf dem Schlag ausgesandt werden, *Treibende Farbe*, *Tiefe* (weitere Kopien des Bildes, die sich gegeneinander drehen) oder ein *Spektrum-Halo*. Jede Szene beginnt mit ihrem eigenen (treibende Farbe hinter Artwork, der Halo hinter Mandala, Strahlen hinter Gitter, Wellen hinter Flüssig, das Bild allein hinter Yeufonic und Balken); drücke **B**, um sie durchzugehen, und die Szene merkt sich deine Wahl.
- **Die Wellenform:** Unter den Szenen Yeufonic und Artwork zeigt die Wellenform des Takes, wie weit der Song gespielt hat; klicke darauf, um dorthin zu springen.
- **Albumcover und Vinyl-Dynamik:** Zeigt das Albumcover des Takes im Stil von Hipgnosis in einer interaktiven 3D-Hülle, die sich mit der Zeigerbewegung neigt und kreist. Eine realistische Vinylplatte dreht sich mit 33⅓ U/min und gleitet bei Basstreffern aus der Hülle, begleitet von holografischem Schimmer und schlagreaktiven Schockwellenringen. Wechsle die Modi mit der Schaltfläche **Artwork**: *Hülle*, *Aura* (verschwommener Hintergrund) oder *Aus*.
- **Ein neues Bild:** Die Bild-Schaltfläche oben rechts macht in jeder Szene ein neues Bild für den spielenden Take, wo dieser PC Bilder machen kann. Sie pulsiert, während das Bild entsteht, und das neue übernimmt, wenn es fertig ist.
- **Textanzeige:** Drücke **L** oder klicke **Text**, um das eigenständige, scrollbare Textfeld ein- und auszublenden. Zieh es an der Leiste oben aus dem Weg; es bleibt, wo du es hinlegst, und ein Doppelklick auf die Leiste legt es zurück.
- **Mini-Player-Band:** Während der volle Visualizer geschlossen ist, spielt ein reaktives Mini-Doppelwellen-Band in der unteren Transportleiste. Es lässt sich in **Einstellungen → Darstellung** umschalten.

### Playlists und Lieblingssongs {#playlists-liked-songs}

Klicke **Playlists** in der oberen Leiste, um zur Ansicht Playlists zu wechseln.

- **Zweispaltiges Layout:** Die linke Spalte listet deine Playlists neben der angehefteten System-Playlist **Gefällt mir** mit der Gesamtzahl der Songs. Die Hauptspalte zeigt den Kopf der aktiven Playlist (hochaufgelöstes Artwork, Titel, Beschreibung, Gesamtzahl der Songs und Dauer) und die Trackliste.
- **Automatische Synchronisierung der Favoriten:** Jeder Take, der in der Bibliothek in einem beliebigen Bereich einen Stern bekommt, erscheint automatisch in der Playlist Favoriten. Den Stern zu entfernen nimmt ihn aus der Playlist Favoriten.
- **Zur Playlist hinzufügen:** Drücke **P** oder klicke das Symbol **Playlist** auf einer Take-Karte, um die Playlist-Auswahl zu öffnen, die Zugehörigkeit zu Playlists umzuschalten oder eine neue Playlist anzulegen. **Escape** schließt die Auswahl.
- **Interaktives Sortieren und Suchen:** Klicke einen Spaltenkopf (**Titel**, **Dauer** oder **Hinzugefügt**), um mit Richtungsanzeige zu sortieren und die Reihenfolge per Klick umzukehren, und filtere Tracks mit dem Suchfeld.
- **Zum Bereich in der Bibliothek springen:** Klicke den Titel eines Songs in der Trackliste der Playlist, um sofort zur Bibliotheksansicht zu wechseln, den Bereich zu öffnen, in dem dieser Take lebt, und seine Karte hervorzuheben.
- **Tastenkürzel in Playlists:** Take-spezifische Tasten werden in der Ansicht Playlists ignoriert, um ungewollte Änderungen zu vermeiden, außer **M** (Mastering-Rack), das auf den gerade spielenden oder geladenen Track wirkt, neben den üblichen Transporttasten (**Leertaste**, Pfeile, **?** und **L**).
- **Durchgehendes Abspielen und Zufall:** Klicke **Abspielen** im Kopf der Playlist, um ab Track 1 zu hören, oder **Zufallswiedergabe** für zufällige Reihenfolge. Das Abspielen geht automatisch zum nächsten Track der Playlist weiter, wenn ein Song endet.

### Tastenkürzel {#hot-keys}

Auf der Hauptseite wirken einzelne Tasten auf den **gewählten Take**: den im linken Bereich. Klicke seine Karte, um
ihn zu wählen. Jede Taste tut, was ihre Schaltfläche tut, also fragt eine Taste, die löschen würde, zuerst, und ein Take,
der nicht tun kann, was eine Taste verlangt (etwa Variationen bei einem Take ohne Partitur), hinterlässt eine Zeile in der Status-
leiste, die sagt, warum.

| Taste | Bewirkt |
|---|---|
| Leertaste | abspielen oder pausieren |
| Links, Rechts | fünf Sekunden zurück oder vor |
| Shift+Links, Shift+Rechts | der vorige oder nächste Take; in der Ansicht Playlists der vorige oder nächste Song der Playlist |
| Hoch, Runter | Lautstärke |
| M | das Mastering-Rack für den Take öffnen; erneut, um es zu schließen |
| E | den Take im Editor öffnen |
| I | die Details des Takes: alles, womit er gemacht wurde, in Worten, mit **Kopieren** |
| N | den Take normalisieren oder es rückgängig machen, wenn er normalisiert ist |
| V | den Visualizer beim Abspielen öffnen oder schließen, oder Variationen im Ruhezustand |
| T | Mehr ausprobieren |
| S | dem Take einen Stern geben oder ihn entfernen |
| P | den Take zu einer Playlist hinzufügen |
| D | den Take löschen, nach Rückfrage, wie sein Papierkorb |
| L | die Logs; oder den Text ein- und ausblenden, während der Visualizer offen ist |
| B | im Visualizer, was sich hinter einer Szene über dem Bild des Takes bewegt |
| F | Vollbild umschalten |
| ? | die Tastenkürzel zeigen oder verbergen; erneut, um zu schließen |
| Escape | das vordere Fenster schließen: den Visualizer, die Logs, das Mastering-Rack über dem Editor, dann den Editor oder jedes andere Fenster |

Die Buchstabentasten tun nichts, während du in einem Feld tippst, während ein Fenster vorne offen ist, oder wenn Ctrl,
Alt oder die Windows- oder Befehlstaste gedrückt ist, sodass die eigenen Kürzel des Browsers (Ctrl+L, Ctrl+S und die übrigen)
weiter funktionieren. Der Tipp einer Schaltfläche nennt ihre Taste, wie in **Variationen (V)**. Drücke jederzeit **?**, um die Liste der Tastenkürzel anzuzeigen.

Im Editorfenster bedienen Leertaste und Pfeile den Player des Fensters, für den dort offenen Take, wann immer sein Player
erscheint: auf jedem Schritt und mit dem Mastering-Rack darüber. Sie wirken nie, während du in einem Feld tippst,
und die Buchstabentasten gehören nur der Hauptseite. Die Pianorolle hat eigene Tasten: siehe [Die Pianorolle](#the-piano-roll).

---

## Einstellungen {#settings}

Drücke **Yeufonic** oben links. Einstellungen liegen auf dem Server, sie folgen dir also in jeden
Browser und überstehen einen Neubau: das Ausgabe-Audioformat für Stems und das Speichern eines Takes, das
Trennungsmodell, wo Stems geschrieben werden, ob Trainings-Checkpoints behalten werden und wie
Instrumentals auf Gesang geprüft werden.

### Speicher {#storage}

**Einstellungen → Speicher** zeigt, wohin der Festplattenplatz von Yeufonic geht, und lässt dich etwas zurückgeben. Das Training eines
Korpus hinterlässt viele Dateien, die nicht wieder gebraucht werden: Kopien für die Engine, die beim Analysieren der Songs entstanden,
das Trainingsset (jeder Song erneut als verlustfreies FLAC geschrieben, größer als das Original) und die Checkpoints,
die unterwegs gespeichert wurden. Das Fenster listet jedes davon mit seiner Größe, **was es ist** und **was das Entfernen
kostet**, und entfernt nur, was du anhakst, nach einer letzten Bestätigung. **Die anhaken, die nichts kosten** hakt
die Kopien an, die bei Bedarf einfach neu gemacht werden.

Ab jetzt analysierte Songs behalten ihren getrennten Gesang als FLAC, dasselbe Audio in etwa halbem Platz. Das
Fenster kann **die vorhandenen WAV-Gesänge umwandeln**: Jeder wird umgewandelt, darauf geprüft, dass er zu genau demselben
Audio dekodiert, und erst dann wird die WAV entfernt. Es läuft im Hintergrund und kann gestoppt werden.

Trainings-Checkpoints verdienen einen zweiten Blick, bevor sie gehen: Jeder ist ein Eintrag in der Liste der Stil-LoRAs, den du
für neue Takes wählen kannst, also nimmt das Entfernen der Checkpoints eines Korpus diese Einträge endgültig aus der Liste. Seine
fertige LoRA bleibt und funktioniert weiter. Das Trainingsset eines Korpus ist anders: Es zu entfernen lässt die LoRA und ihre
Checkpoints in der Liste, und nur ein erneutes Training dieses Korpus braucht es.

Deine Takes, Songs, fertigen LoRAs und Modelle werden nie zum Entfernen aufgeführt. Alles, was zu einem Korpus gehört, der
trainiert, exportiert oder analysiert wird, wird ausgegraut gezeigt und kann nicht angefasst werden, bis es fertig ist.

Darunter wählt **Automatisch aufräumen**, was Yeufonic für dich entfernt: die Arbeitskopien jedes Songs,
sobald seine Analyse endet (standardmäßig an), das Trainingsset, sobald eine LoRA trainiert hat (standardmäßig aus; der Korpus
braucht dann wieder **Exportieren**, bevor er erneut trainieren kann), und die Trainings-Checkpoints (standardmäßig behalten).

Die eigenen Images und der Build-Cache von Docker liegen außerhalb von Yeufonic und sind hier nicht erfasst; `docker system df` zeigt sie.

### Das YuE2-Modell {#the-yue2-model}

YuE2 gibt es in zwei Größen, und eine Installation hat eine: **volle Qualität**, die wir empfehlen, oder **wenig
Speicher**, eine kleinere Kopie für Grafikkarten mit wenig Videospeicher. **Über** im selben Menü
sagt, welche du hast. Sie wird bei der Installation von Yeufonic gewählt, nicht hier:

- **Unter Windows** führe den Installer erneut aus. Seine Komponentenseite bietet beide Größen an und markiert die
  schon heruntergeladenen. Ein Wechsel lädt beim ersten Mal die andere herunter und behält beide, sodass das Zurückwechseln
  nichts herunterlädt.
- **Mit Docker** holt `sh scripts/fetch-models.sh` die volle Qualität und
  `sh scripts/fetch-models.sh --int8` die mit wenig Speicher. Mit beiden Dateien in `models/checkpoints` nutzt die
  App die volle Qualität, außer `YUE2_CHECKPOINT=int8` ist in `.env` gesetzt.

Probiere wenig Speicher, wenn Renderings sehr langsam sind oder der Engine der GPU-Speicher ausgeht. Das Training einer LoRA funktioniert
mit beiden Modellgrößen. Die Einstellung **Training mit dem Low-Memory-Modell (int8)** wählt, welche: aus, nutzt das Training
das Modell in voller Qualität; an, nutzt es das Modell, mit dem die App rendert. Sie ist an, wenn nur das Modell mit wenig Speicher
installiert ist. Die README auf GitHub hat einen Abschnitt, *Choosing a model size*, mit dem, was von jedem zu erwarten ist.

Yeufonic kann statt ComfyUI auch die **yue2.cpp**-Engine nutzen, für Grafikkarten mit weniger Speicher,
gewählt bei der Einrichtung: auf der Komponentenseite des Windows-Installers oder mit Docker über
`sh scripts/fetch-models.sh --cpp`. **Über** sagt, welche Engine läuft, und die Karte eines Takes, welche Engine ihn gerendert hat. Sie macht Songs, Cover und
Instrumentals und transkribiert Aufnahmen, mit deinen Stil-LoRAs; Gemma kann daneben Songtexte entwerfen und Bilder beschreiben
(mit Docker `--gemma`), und FLUX.2 klein sie zeichnen (`--pictures`). Training braucht die ComfyUI-
Engine: Mit yue2.cpp werden Korpora und Training nicht angeboten. Die Seite
[Choosing an engine](https://github.com/yeufonic/yeufonic/blob/main/docs/ENGINES.md) auf GitHub hat die
ganze Liste und wie man wechselt.

**Nach einer neuen Version suchen** ist das Einzige hier, das von sich aus das Internet nutzt: Alle
vier Stunden fragt die App yeufonic.com, ob eine neuere Version erschienen ist, und sagt es mit einer Pille neben der
Version oben rechts. Diese Pille reicht dir den Installer, oder, für eine Docker-Kopie, die zwei Befehle,
die sie aktualisieren. Es ist eine Anfrage, und sonst verlässt nichts den Computer; **Nicht suchen** schaltet es
ab. **Nach Updates suchen** im Menü fragt sofort, ob dies an oder aus ist, und antwortet im
Menü: welche Version du hast und ob es die neueste ist.

Gibt es eine neuere, bietet das Menü **x.y.z holen** an, was bei einer Windows-Installation den Installer herunterlädt oder bei einer Docker-Kopie die zwei Befehle in die Zwischenablage legt.

**Design** legt fest, wie die App aussieht: **Dunkel**, **Hell**, **Wie der Computer (dunkel oder hell)**, das dem Hell oder Dunkel deines
Systems folgt und mit ihm wechselt, **Studio**, ein warmes Dunkel mit Bernstein, oder **Hoher Kontrast**, Schwarz und Weiß
mit kräftigen Umrissen. Es wechselt sofort, und jeder Browser merkt es sich,
damit die Seite darin öffnet. Das Log-Fenster bleibt in jedem Design dunkel, wie ein Terminal. Auch das Mastering-Rack folgt dem Design: Im hellen Design sind seine Paneele gebürstetes Silber, während seine Knöpfe,
Anzeigefenster und Displays den dunklen Look der Hardware behalten.

**Hintergrundfarbe**, unter Design, tönt die Seite hinter den Takes mit einer Farbe deiner Wahl: Hake **Tönung** an, dann
bewege **Farbton** um den Farbkreis und **Stärke** von einem zarten Hauch bis zu einer satten Farbe. Die Seite ändert sich, während du
ziehst, und die Wahl wird behalten, wenn du loslässt. Die Take-Karten, die Bereiche und die Fenster behalten ihre eigenen
Farben, und das Design mit hohem Kontrast bleibt schwarz.

### Externe LLM {#external-llm}

Yeufonic kann Songtext-Entwürfe schreiben, Aufnahmen transkribieren, Songabschnitte markieren und Korpus-Stile mit einer externen LLM statt des lokalen Gemma-Modells analysieren.

Eine externe LLM zu nutzen hat zwei klare Vorteile:
- **Spart GPU-Speicher:** Das Gemma-4-Modell muss nicht in den GPU-VRAM geladen werden (spart etwa 8 GB Videospeicher), sodass deine Grafikkarte ganz für das Planen und Rendern mit YuE2 frei bleibt.
- **Reichere Entwürfe und Analysen:** Größere Cloud-Modelle entwerfen oft nuanciertere Songtexte und erzeugen detaillierte Stil-Tags für deine Korpora.

**Empfohlener Anbieter:** Wir empfehlen, einen externen LLM-Anbieter zu wählen, bei dem für die API keine Abrechnung anfällt, wenn dir das möglich ist — **Google Gemini** ist ein gutes Beispiel. Die API von Gemini (über Google AI Studio) bietet eine großzügige kostenlose Stufe ohne Abrechnung, unterstützt die üblichen OpenAI-kompatiblen Endpunkte (`https://generativelanguage.googleapis.com/v1beta/openai/`) und nimmt Audio direkt für die Transkription von Aufnahmen an.

Nutzt du eine gemessene oder pro Token abgerechnete API (etwa bezahlte Stufen von OpenAI oder Anthropic), kann das Analysieren eines ganzen Korpus mit Dutzenden Songs oder das Erzeugen von Beschreibungen für viele Takes schnell API-Guthaben verbrauchen oder Ausgabenlimits auslösen. Gibt eine externe API einen Kontingent- oder Ratenlimit-Fehler zurück (HTTP 429), zeigt Yeufonic eine Warnung und lässt dich für den Rest der Sitzung zu lokalen Modellen wechseln, sodass andere Aufträge ungestört weiterlaufen. Ein Anbieter ohne Abrechnung vermeidet unerwartete Kosten.

**Einrichtung:**
1. Öffne **Yeufonic → Einstellungen → Externes LLM & Songtext**.
2. Setze **LLM für Songtexte & Stil-Tags** auf **Externes LLM (OpenAI-kompatible API)**.
3. Gib die **API-URL**, den **API-Schlüssel** und das **Modell** deines Anbieters ein (zum Beispiel das Modell `gemini-2.5-flash` oder `gemini-1.5-flash` mit der OpenAI-kompatiblen Basis-URL von Google Gemini `https://generativelanguage.googleapis.com/v1beta/openai/`).
4. Klicke **LLM-Verbindung testen**, um deine Zugangsdaten zu prüfen.
5. Unterstützt dein gewähltes Modell Audio-Eingabe (wie Gemini), kannst du auch **Songtext aus einer Aufnahme** auf **Externes LLM** setzen, damit es den getrennten Gesang anhört.

---

## Yeufonic von einem KI-Agenten aus nutzen (MCP) {#using-yeufonic-from-an-ai-agent-mcp}

Yeufonic kann als **MCP-Server** arbeiten. Damit kann ein KI-Agent auf demselben Computer, etwa Claude Code oder Cursor, es für dich bedienen:
um einen Song, ein Cover oder ein Instrumental bitten, darauf warten, es abspielen, es anders probieren, ihm ein Bild geben, es in eine Playlist legen und
die Bibliothek aufräumen, alles in deinen eigenen Worten („mach ein einminütiges EDM-Instrumental im Bereich EDM und spiel es ab“). Der Agent tut, was die Seite tut, über dieselben Wege, also ist ein Take, den er startet, ein
gewöhnlicher Take in deiner Bibliothek.

### Einrichtung {#setting-it-up}

1. **Schalte es ein.** Öffne die Einstellungen und setze **MCP-Server** auf **Ein**. Es ist standardmäßig aus, weil eine Anfrage Arbeit auf der GPU starten kann.
2. **Verbinde deinen Agenten** mit der Adresse der App mit `/mcp` am Ende: der Adresse, unter der du Yeufonic öffnest, zum Beispiel
   `http://localhost:8090/mcp`. In Claude Code:

   ```
   claude mcp add --transport http yeufonic http://localhost:8090/mcp
   ```

   Andere Clients nehmen dieselbe Adresse als HTTP-Server. Solche, die eine Einstellungsdatei lesen, wollen meist etwas wie
   `{"mcpServers": {"yeufonic": {"url": "http://localhost:8090/mcp"}}}`. Es braucht keine Anmeldung und keinen Schlüssel.
3. **Frag.** Starte deinen Agenten aus einem beliebigen Ordner und beschreibe, was du willst.

**Welche Adresse?** Es ist die Adresse, unter der du Yeufonic öffnest, mit `/mcp` am Ende.
- **Docker:** `http://localhost:8090/mcp`.
- **Die Windows-Installation:** Der Port der App steht in `settings.ini` (`app_port`, 8090, sofern du ihn nicht geändert hast, etwa um neben
  einer Docker-Kopie zu laufen). Mit `app_port = 8091` ist es `http://localhost:8091/mcp`.
- **Agent in WSL, App unter Windows:** Das verbindet nicht. Die Windows-App lauscht nur auf der eigenen Loopback-Adresse von Windows, die WSL nicht
  erreichen kann (Docker in WSL ist in Ordnung, da es auch in WSL läuft). Starte den Agenten unter Windows (PowerShell oder die Windows-Version
  deines Agenten), oder schalte das gespiegelte Netzwerk von WSL ein (`networkingMode=mirrored` unter `[wsl2]` in `.wslconfig`, dann `wsl --shutdown`),
  was `localhost` auf beiden Seiten gleich macht.

Sagt dein Agent, dass der Server **eine Authentifizierung braucht**, liegt es fast immer daran, dass die Einstellung noch aus ist: Schalte sie ein und
verbinde den Agenten neu (in Claude Code `/mcp`). Verbinde auch nach einem Neustart von Yeufonic neu, weil ein Neustart die Verbindung beendet.

### Worum du bitten kannst {#what-you-can-ask-for}

| Bitte um | Was passiert |
|---|---|
| „Liste meine neuesten Takes“, „zeig die Takes im Bereich EDM“ | Listet Takes, neueste zuerst, mit einer kurzen ID, wann jeder gemacht wurde, seiner Länge und seinem Stil |
| „Mach ein einminütiges Instrumental im Synthwave-Stil“ | Plant und rendert ein Instrumental. Eine Länge, ein Bereich und eine [Stil-LoRA](#style-loras) können genannt werden |
| „Mach einen Song im Folk-Stil mit diesem Text“ | Dasselbe für einen Song, aus dem Text, den du gibst |
| „…mit abenteuerlicher Harmonie, enger Interpretation, in Fis, mit 100 BPM“ | Jede Einstellung eines neuen Takes unter den Namen, die die Seite benutzt: [Harmonie](#harmony), [Planvielfalt](#plan-variety), die [Interpretation](#interpretation), die Fixierung von Tonart und Tempo und für einen Song **Dieser Struktur genau folgen** und **Stimmen folgen den Hinweisen**. Ungesagt beginnt ein neuer Take dort, wo der der Seite beginnt: Abwechslungsreich und Weit |
| „Schreib einen Text über einen Nachtzug, gesprochen“ | Das eigene **Songtext schreiben** der App, mit seinen Songformen, Zeilen pro Abschnitt und Klangarten. Der Agent kann Texte auch selbst schreiben |
| „Mach ein Cover von *der Aufnahme* im Jazz-Stil“ | Macht ein Cover aus einer Aufnahme, die schon in deiner Bibliothek ist. Es braucht eine Partitur (transkribiere sie zuerst in der App). Ohne eigenen Text nutzt es die in der Aufnahme gehörten Wörter |
| „Welche Stimmen habe ich?“, „sing es mit meiner Stimme Night Singer, etwas tiefer“ | Listet deine aufgenommenen Stimmen auf und macht einen Song oder ein Cover, gesungen in einer davon, oder rendert einen Take neu in einer, mit eigenen Einstellungen für diesen Take (Formant, Mischung, Ähnlichkeit und der Rest), wie die **Einstellungen** der Stimme im Editor |
| „Spiel es ab“ | Öffnet den Take in deinem Browser, wo er spielt |
| „Gib dem einen Stern“, „nenn es Sunrise“, „verschieb es in den Bereich Folk“ | Gibt einem Take einen Stern, benennt ihn um oder verschiebt ihn |
| „Render es neu mit einem neuen Seed“, „stopp das“ | Rendert einen Take erneut oder bricht einen laufenden ab |
| „Gib mir noch ein paar wie diesen“ | Rendert den Take erneut mit neuen Seeds, als mehrere neue Takes zum gemeinsamen Anhören |
| „Sing es noch mal“, „probier es in jeder Interpretation“ | **Erneut singen** (eine neue Stimme für dieselbe Partitur) oder **Variationen** (dieselbe Partitur und derselbe Seed, auf jede Weise gespielt). Variationen werden im Take aufbewahrt, wie Mehr ausprobieren |
| „Sing diese Melodie stattdessen mit diesem Text“ | **Neuer Text**: dieselbe Melodie, Tonart und dasselbe Tempo mit anderem Text, als neuer Take |
| „Mach ein Instrumental daraus“ | Dieselbe Partitur mit der Melodie auf einem Instrument und ohne Gesang, als neuer Take |
| „Schreib einen neuen Plan dafür, lebhafter“ | Ein neuer Plan für einen Take, der noch kein Audio hat (einer, der ohne Rendern geplant wurde, oder dessen Plan scheiterte). Ein Take mit Audio bleibt unberührt: Bitte stattdessen um einen neuen Take |
| „Behalte den lockeren für sich“ | **Herausnehmen**: Ein Take, der in einem anderen aufbewahrt wird, wird ein eigener Take |
| „Gib ihm ein Bild“ | Macht ein neues Bild für den Take, wie die Schaltfläche **Bild** des Editors, und gibt einen Link, der es öffnet. Ein auf diesem Computer gezeichnetes Bild wartet, bis kein Song entsteht |
| „Leg die besten drei in eine Playlist namens Road trip“ | Macht Playlists, listet, was darin ist, und fügt Takes hinzu oder entfernt sie. Einen Take in **Gefällt mir** zu legen gibt ihm einen Stern |
| „Finde mir einen Synthwave-Stil“, „speichere den Stil als Night drive“ | Durchsucht deine gespeicherten Stile und die eingebauten und speichert einen Stil unter einem Namen für das Stilmenü |
| „Mach einen Bereich namens Drafts“ | Macht einen neuen Bereich für Takes |
| „Transkribiere *die Aufnahme*“ | Transkribiert eine Aufnahme in eine Partitur, damit ein Cover daraus gemacht werden kann. Eine Aufnahme, die schon eine Partitur hat, lässt es in Ruhe, sofern nicht gefragt |
| „Teil das in Gesang und Instrumente“ | Trennt einen fertigen Take in seine Teile (vier, sechs oder nur Gesang und Instrumente) und gibt dir einen Link zu jeder Datei und einen zum ganzen Set als Zip |
| „Speichere das Rezept dieses Takes“, „…und den Take dazu als MP3-Zip“ | Gibt das Rezept des Takes (was ihn gemacht hat, nicht sein Audio) zum Zeigen, Ändern oder Aufbewahren als Datei, mit Links, um es allein oder mit dem Audio als ein Zip herunterzuladen |
| „Importiere *Night Ferry.yeufonic.json* in Drafts und rendere es“ | Ein neuer Take aus einer Take-Datei, mit dem Plan, gerendert, wenn du es sagst. Er sagt, welche in der Datei genannten LoRAs nicht installiert sind und wann ein Cover als Song kam |
| „Importiere es noch einmal im Dream-Pop-Stil, gleiche Partitur und Seed“ | Ändert das Rezept vor dem Import, sodass nur das anders ist, was du nennst |
| „Welche Engine hat diesen Take gemacht?“, „welche Engine läuft?“ | Sagt, welche Engine einen Take gerendert hat und welche Yeufonic gerade nutzt (ComfyUI oder yue2.cpp) |
| „Ist Yeufonic beschäftigt?“ | Sagt, ob die Engine bereit ist, was läuft und mit welchem Fortschritt, was wartet und ob eine LoRA trainiert |
| „Lösch diesen Take“ | Zeigt, was gehen würde, und fragt dich zuerst; siehe unten |

Einen Take zu machen dauert Minuten. Der Agent startet ihn und wartet, mit Fortschrittsmeldungen, sodass du inzwischen um das Nächste bitten kannst.

### Wie es laufen kann: ein Beispiel {#how-it-can-work-an-example}

Ein Gespräch, von einer Idee bis zu einer Playlist. Du sprichst; der Agent wählt die Werkzeuge (die mittlere Spalte zeigt nur, was
passiert) und sagt dir, was zurückkam.

| Du sagst | Der Agent | Was du bekommst |
|---|---|---|
| „Schreib einen Text über die letzte Nacht eines Leuchtturmwärters, Folk-Stil, als Geschichte. Dann mach einen Song daraus in einem neuen Bereich namens Coast.“ | `write_lyrics`, `create_space`, `make_song`, dann `wait_for_take`, bis er fertig ist | Der Text mit dem Titel *The Last Light*, dir gezeigt; ein Bereich namens Coast; ein dort geplanter und gerenderter Song, mit Fortschritt unterwegs |
| „Spiel ihn ab.“ | `get_take`, dann öffnet er seine `listen_url` | Er spielt in deinem Browser |
| „Gute Melodie. Probier ihn lockerer und unruhiger, und gib mir einen ohne Gesang.“ | `make_variations` mit locker und unruhig, `instrumental_from_take` | Zwei Takes im Song und ein Instrumental daneben |
| „Zeig mir, was wir haben.“ | `list_takes` in Coast und mit `inside` für den Song | Eine Liste mit einer kurzen ID für jeden, sodass du „3f9a“ statt eines Titels sagen kannst |
| „Behalte 3f9a für sich, gib ihm einen Stern und ein Bild.“ | `take_out`, `star_take`, `make_picture` | Der lockere als eigener Take, mit Stern (also auch in Favoriten), mit einem Link zu seinem Bild |
| „Leg den und das Instrumental in eine Playlist namens Coast demos.“ | `create_playlist`, `add_to_playlist` | Eine Playlist mit den beiden |
| „Speichere den Stil als Coastal folk.“ | `save_style` | **Coastal folk** im Stilmenü der App, bereit für das nächste Mal |
| „Jetzt ein Duett: dieser Text, mit [male voice]- und [female voice]-Anweisungen, jeder Abschnitt wie geschrieben.“ | `make_song` mit `follow_structure` (ein neuer Plan, weil sich die Abschnitte ändern) | Ein neuer Song, der genau deine Abschnitte plant, in Reihenfolge, mit jeder angewiesenen Zeile dorthin verschoben, wo diese Stimme singt |

Alles, was er gemacht hat, ist in der Bibliothek, als hättest du es auf der Seite gemacht: Öffne jeden Take im Editor, mastere ihn oder mach dort weiter.
Kann ein Schritt nicht ausgeführt werden, bekommt der Agent den eigenen Grund der App („dieser Take ist schon ein Instrumental“, „hier kann nichts ein
Bild zeichnen“) und gibt ihn weiter, sodass du dieselbe Antwort hörst, die die Seite geben würde.

### Alles, was er kann {#everything-it-can-do}

Du brauchst diese Namen nicht: Du fragst in deinen eigenen Worten, und der Agent wählt. Sie stehen hier, damit du siehst, was es gibt, und damit du
deinem Agenten sagen kannst, welches du meinst.

| Werkzeug | Was es tut |
|---|---|
| `list_takes` | Listet Takes, neueste zuerst, wahlweise nur die zu Wörtern passenden, in einem genannten Bereich oder mit Stern. Zeigt eine kurze ID |
| `get_take` | Ein Take vollständig: wie er gemacht wurde, sein Status, ein Fehler und, sobald er Audio hat, ein Link, der ihn abspielt. Kann die Partitur enthalten |
| `wait_for_take` | Wartet (bis etwa eine Minute am Stück) auf einen Take, der entsteht, und sagt, ob er fertig ist |
| `make_instrumental` | Plant und rendert ein Instrumental aus einem Stil, mit einer Länge, einem Bereich und einer Stil-LoRA, wenn du sie nennst, und Abschnitten, wenn du sie gibst |
| `make_song` | Dasselbe für einen Song, aus einem Text |
| `make_cover` | Ein Cover aus einer Aufnahme in der Bibliothek, mit ihrer Partitur und, sofern du keine anderen gibst, ihrem Text |
| `try_more` | Mehrere weitere Takes aus einem vorhandenen, mit neuen Seeds |
| `sing_again` | Dieselbe Partitur erneut gesungen mit einem neuen Seed: eine neue Stimme, als neuer Take |
| `make_variations` | Dieselbe Partitur und derselbe Seed in jeder genannten Interpretation (oder allen), im Take aufbewahrt |
| `new_words` | Dieselbe Partitur mit anderem Text gesungen, als neuer Take |
| `instrumental_from_take` | Dieselbe Partitur als Instrumental, als neuer Take |
| `replan_take` | Ein neuer Plan für einen Take ohne Audio, wahlweise mit anderer Harmonie, Planvielfalt, Tonart oder anderem Tempo |
| `take_out` | Macht einen in einem anderen aufbewahrten Take zu einem eigenen |
| `write_lyrics` | Ein Text aus einer Vorgabe, in einer Songform und Klangart, geschrieben wie das Songtext schreiben der Seite |
| `render_take` | Rendert einen geplanten Take oder rendert einen fertigen erneut (mit neuem Seed, wenn gewünscht) |
| `cancel_take` | Stoppt einen wartenden oder laufenden Take |
| `make_stems`, `get_stems` | Teilt einen Take in Teile und listet dann die Teile mit einem Link zu jedem und zum ganzen Set als Zip |
| `list_recordings`, `transcribe_recording` | Zeigt die Aufnahmen in der Bibliothek und ob jede eine Partitur hat; transkribiert eine ohne |
| `list_style_loras` | Die installierten Stil-LoRAs, mit ihren Triggerwörtern und den mit ihnen gespeicherten Stärken |
| `list_voices` | Deine aufgenommenen Stimmen, ob jede bereit ist, und ihre Voreinstellungen. `make_song`, `make_cover` und `render_take` nehmen eine beim Namen, mit eigenen Einstellungen für diesen Take; `get_take` sagt, welche Stimme einen Take gesungen hat |
| `list_spaces`, `move_take`, `create_space` | Die Bereiche und was jeder enthält; verschiebt einen Take in einen anderen; macht einen neuen Bereich |
| `list_playlists`, `create_playlist`, `add_to_playlist`, `remove_from_playlist` | Die Playlists und die Takes in einer; macht eine; legt Takes hinein oder nimmt sie heraus |
| `make_picture` | Ein neues Bild für einen Take, mit einem Link, der es öffnet. `get_take` gibt auch den Link zum Bild eines Takes |
| `list_styles`, `save_style` | Deine gespeicherten Stile und die eingebauten, nach Wörtern durchsucht; behält einen Stil unter einem Namen |
| `star_take`, `rename_take` | Gibt einem Take einen Stern oder nimmt ihn weg; ändert seinen Titel |
| `delete_take` | Löscht einen Take endgültig, nachdem er ihn dir gezeigt hat und du zugestimmt hast |
| `save_take_recipe` | Das Rezept eines Takes, mit Links, um es allein oder mit dem Audio als ein Zip im gewünschten Format herunterzuladen |
| `import_take` | Ein neuer Take aus einem Rezept, in einem Bereich, falls genannt, bereit zum Rendern; sagt, welche LoRAs nicht installiert sind und wann ein Cover als Song kam |
| `status` | Ob die Engine bereit ist, was läuft und wartet und ob eine LoRA trainiert; nennt die laufende Engine (ComfyUI oder yue2.cpp) |

### Ideen zur Nutzung {#ideas-for-using-it}

- **Ein Stapel Ideen, dann auswählen.** „Mach fünf einminütige EDM-Instrumentals in verschiedenen Stilen im Bereich EDM.“ Er startet sie nacheinander
  und sagt dir, wenn jeder fertig ist. Du hörst sie an und sagst dann „gib dem zweiten und vierten einen Stern und lösch den Rest.“
- **An einer Idee feilen.** „Mach ein Instrumental in einem verträumten Synth-Stil und spiel es ab“, dann „jetzt dasselbe mit mehr Schlagzeug“ und
  „gib mir vier weitere wie das zweite.“ Der Agent behält im Blick, welcher Take welcher ist, sodass du über sie nach Position oder
  nach dem, was du über sie gesagt hast, sprechen kannst.
- **Cover, ohne sich durchzuklicken.** „Transkribiere *das Demo* und mach drei Cover daraus: Folk, Synthwave und Jazz.“ Er transkribiert
  die Aufnahme zuerst, wenn sie keine Partitur hat, und macht dann die Cover in dem Bereich, den du nennst.
- **Mit einer LoRA arbeiten.** „Liste meine Stil-LoRAs und mach dann ein Instrumental mit der Jazz-LoRA.“ Das Triggerwort und die gespeicherten Stärken werden
  für dich erledigt, was von Hand leicht schiefgeht.
- **Text vom Agenten oder von der App.** Der Agent kann den Text selbst schreiben: „Schreib einen Text über einen Nachtzug und mach einen Song
  daraus im Folk-Stil.“ Yeufonic sieht nur den fertigen Text. Oder frag nach dem der App: „nutze den Songtext-Schreiber von Yeufonic, Hip-Hop-Form,
  gesprochen“, der ihn schreibt wie **Songtext schreiben** auf der Seite und ihn für einen Song zurückgibt.
- **Dieselbe Melodie, anderer Text.** „Sing den noch einmal mit diesem Text für die zweite Strophe“: `new_words` behält Melodie, Tonart und Tempo,
  wo ein neuer Song aus dem Text eine neue Melodie schreiben würde.
- **Einstellungen vergleichen.** „Mach denselben Song zweimal, einmal mit Vertraut und einmal mit Abenteuerlich als Harmonie, mit demselben Seed“, dann
  „gib dem besseren jetzt jede Interpretation.“ Einstellungen werden bei ihrem Namen genannt, sodass du einen kleinen Test in einem Satz entwerfen kannst.
- **Playlists aus dem Hören.** „Leg jeden Take mit Stern von dieser Woche in eine Playlist namens Week 43“ oder „nimm die Instrumentals aus
  Road trip.“ Favoriten sind die Takes mit Stern, also bleiben Stern und Favoriten dieselbe Liste.
- **Stems für ein ganzes Set.** „Teil meine fünf neuesten Takes in Gesang und Instrumente und gib mir die Links.“ Sie reihen sich hinter-
  einander ein und hinter jedes Rendering, das die GPU gerade ausführt.
- **Ordnung in der Bibliothek.** „Finde die Takes mit demselben Titel, zeig mir, welcher der neueste ist, und lösch die älteren“ oder „verschieb alles,
  was ich heute gemacht habe, in einen Bereich namens Drafts.“ Er arbeitet mit IDs und fragt vor dem Löschen.
- **Vor einem langen Auftrag prüfen.** „Ist Yeufonic beschäftigt?“, bevor du ein langes Rendering oder einen Stapel einreihst, damit du nicht hinter einem Trainingslauf wartest.
- **Teil einer größeren Aufgabe.** Weil es ein Werkzeug ist, das der Agent aufrufen kann, kann es in etwas Größerem stecken: einen Track für ein Video machen und
  die Notiz dazu schreiben, oder einen Stapel in Playlist-Größe bauen und die Takes passend zu einer Liste benennen.

Der Agent kann einen Take nicht hören, also kann er nicht beurteilen, wie er klingt: Du hörst zu, und er erledigt die Laufarbeit. Er ist auch keine
Abkürzung an der Engine vorbei: Die GPU macht weiterhin einen Auftrag nach dem anderen, also ist ein großer Stapel eine lange Warteschlange.
- **Einen Take teilen.** „Speichere meinen markierten Take mit seinem Rezept als FLAC-Zip“ gibt eine Datei, die jemand anderes hören und nachbauen
  kann: Er bittet seinen Agenten, „diese Take-Datei zu importieren und zu rendern“. Oder „importiere es noch einmal mit der Jazz-LoRA, gleiche
  Partitur und Seed“, um denselben Plan anders zu hören.

### Gut zu wissen {#things-to-know}

- **Takes können einen Titel teilen,** also arbeitet der Agent mit der **ID** eines Takes und zeigt eine kurze (die Spalte `short_id`), wenn er Takes listet.
  Du kannst einen Take mit dem Anfang seiner ID benennen, vier Zeichen oder mehr, solange nur ein Take so beginnt. Tun es zwei, sagt er es dir
  und bittet um mehr.
- **Löschen fragt zweimal.** Der Agent zeigt dir zuerst, was er löschen würde, einschließlich jedes anderen Takes mit demselben Titel, und löscht
  erst, nachdem du Ja gesagt hast. Ein Take mit Stern verlangt, dass du es ausdrücklich sagst. Ein gelöschter Take samt Audio kann nicht zurückgeholt werden.
- **Bereiche und Stil-LoRAs werden benannt,** nicht nummeriert: „im Bereich EDM“, „mit der Jazz-LoRA“. Ein Name, der zu nichts passt, bekommt die Liste dessen,
  was es gibt, und nichts wird angelegt. Das Triggerwort einer LoRA wird für dich zum Stil hinzugefügt, da eine LoRA ohne es sehr wenig tut.
- **Ein neuer Take beginnt dort, wo der der Seite beginnt:** Harmonie auf Abwechslungsreich und die Interpretation Weit, sofern du keine anderen nennst. Auf einer Engine
  ohne den Harmonie-Knoten beginnt er bei Vertraut, da Harmonie dort nicht höher gehen kann.
- **Bilder und Texte warten, bis sie dran sind.** Ein auf diesem Computer gezeichnetes oder beschriebenes Bild wartet, bis kein Song entsteht, und Texte,
  die auf diesem Computer geschrieben werden, reihen sich mit der übrigen GPU-Arbeit ein, also meldet der Agent vielleicht „entsteht noch“ und schaut später wieder.
- **Ein Instrumental wird immer mit einer Struktur mit Zeiten geplant,** errechnet aus der Länge, die du verlangst (etwa zweieinhalb
  Minuten, wenn du nichts sagst). Ohne Zeiten schreibt der Planner Pläne, die zu lang sind. Nenne eigene Abschnitte, und sie werden wie angegeben benutzt.
- **Nur auf diesem Computer.** Es gelten dieselben Prüfungen von Hostnamen und seitenübergreifenden Anfragen wie für die Seite, und es gibt keine Anmeldung, also schalte die Einstellung
  aus, wenn du sie nicht nutzt, und öffne den Port nicht für ein Netzwerk, dem du nicht vertraust.

## Systemprotokolle {#system-logs}

Die App schreibt ein zusammengefasstes Echtzeit-Log jeder größeren Aktion — Partiturplanung, Rendern, Audiotranskription, Stem-Trennung und LoRA-Training —, markiert mit den Präfixen `INFO`, `WARN` und `ERROR`.

- **Konsole im Browser:** Klicke die Schaltfläche **Protokolle** in der oberen Leiste (oder drücke **L**), um eine schwebende, verschiebbare und größenveränderbare Konsole zu öffnen. Sie bleibt offen, ohne die Seite zu blockieren, sodass du Takes einreihen und die Erzeugung in Echtzeit verfolgen kannst.
- **Eigenes Fenster:** Klicke **↗ Herauslösen** im Kopf der Konsole (oder gehe direkt zu `/logs`), um ein eigenes Log-Fenster zu öffnen.
- **Im Terminal verfolgen:** Logs rotieren automatisch nach `data/logs/yeufonic.log` auf dem Host, wo du sie live verfolgen kannst:
  ```bash
  tail -f data/logs/yeufonic.log
  ```

## Die eigene Seite der Engine {#the-engine-s-own-page}

Die Engine ist ComfyUI (außer diese Installation läuft mit yue2.cpp, deren Seite dort ein schlichter Prüfstand ist), und ihre eigene Oberfläche ist erreichbar: <http://localhost:8189> mit Docker oder
<http://localhost:8188> mit der Windows-Installation (der `engine_port` in `settings.ini`). Sie antwortet
nur auf diesem Rechner, ohne Anmeldung.

- **Es ist dieselbe Engine und GPU wie die der App.** Ein dort ausgeführter Auftrag erscheint in der Warteschlange der App als von
  außen kommend, und die eigenen Aufträge der App warten auf ihn.
- **Ihr Verlauf zeigt jeden Graphen, den die App geschickt hat**: den Plan, das Rendering und die Transkriptionen, mit
  jeder Einstellung so, wie die Engine sie bekommen hat. Ein nützlicher Ort, um genau zu sehen, woraus ein Take gemacht
  wurde.

---

## Wenn etwas nicht stimmt {#when-something-is-wrong}

**Der Kopf sagt, dass die Engine fehlt.** Die App läuft ohne sie und sagt es. Renderings warten.
Prüfe, ob der Engine-Container läuft.

**Ein Song endet nicht.** Meist zu viel Planner-Stärke. Senke den Planner der LoRA auf 0.5. Die
Längengrenze stoppt ihn ohnehin.

**Eine LoRA scheint nichts zu tun.** Prüfe, ob das Triggerwort im Stil steht und ob die Stärke, die du
erhöht hast, eine ist, die die Datei tatsächlich enthält — die Auswahl graut die andere aus.

**Ein Take sagt *Schwaches Rendering*.** Er kam durchgehend viel leiser heraus als üblich. Manche Takes
dieser Art sind nur leise; andere klingen dünn oder verzerrt. Klicke die Warnung, um ihn zu normalisieren, was
ihn auf die übliche Lautheit bringt und als *Normalisiert* markiert. Klingt er immer noch falsch, probiere einen anderen
Seed und halte den Klang dieser LoRA bei 0.5 oder darunter. Es passiert am häufigsten bei Covern über eine hier trainierte
Stil-LoRA.

**Lautstärke normalisieren.** Hake es im Editor an, und jeder Take, der gemacht wird, während es angehakt ist, wird bei Fertigstellung auf die
übliche Lautheit gebracht und als *Normalisiert* markiert. Ein ohne es gemachter Take kann später
mit der Lautsprecher-Schaltfläche oben auf seiner Karte normalisiert werden. Die Datei, wie sie gerendert wurde, bleibt daneben erhalten, und
ein Klick auf *Normalisiert* kehrt zu ihr zurück. Wie laut er gemacht wird, legen die Einstellungen unter *Normalisieren auf* fest.
Ohne Haken behält ein Take den Pegel, mit dem er gerendert wurde.

**Ein Instrumental hat gesungen.** Siehe *Wenn ein Instrumental singt* oben. Es ist ein Fehler des Modells; ein neuer Seed
behebt es meist.

**Ein Take rendert nicht erneut.** Seine Aufnahme wurde vielleicht gelöscht. Cover behalten ihr Audio und ihre
Partitur, können aber nicht aus einer Aufnahme neu gerendert werden, die weg ist.

**Nichts spielt, aber die Wellenform bewegt sich.** Prüfe den Lautstärkeregler und ob nicht ein Stem gewählt ist —
der Player folgt dem, was zuletzt angeklickt wurde.
