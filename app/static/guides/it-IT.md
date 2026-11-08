# Yeufonic — la guida

Questa guida riguarda l'**uso** dell'app. L'installazione, e tutto ciò che serve prima che funzioni, è nel
[README](https://github.com/yeufonic/yeufonic#readme).

L'app crea canzoni con YuE2, un modello che lavora in due passi: prima scrive un **piano della partitura** —
la melodia, gli accordi e le sezioni, come testo — e poi **renderizza** quel piano in audio.
Quasi tutto ciò che segue deriva da questa divisione. Un piano costa secondi e si può leggere, modificare e
scartare; un render costa minuti. Per questo l'app ti fa vedere prima il piano.

---

## La tua prima canzone {#your-first-song}

1. Premi **+ Canzone** in cima al pannello di sinistra. Si apre la finestra dell'editor.
2. **Scrivi uno stile.** Una frase, non un elenco di tag: *“warm indie rock, expressive female lead, jangly
   guitars, 96 BPM”*. È ciò che conta di più per il risultato.
3. **Aggiungi un testo**, oppure premi **Scrivi testo** e lascia che Gemma lo abbozzi da una descrizione.
4. Premi **Scrivi il piano della partitura**. La finestra si chiude e il take compare nel pannello di sinistra. Con
   **Renderizza appena il piano è pronto** spuntato accanto al pulsante, come all'inizio, il piano
   passa direttamente al render.

Per leggere il piano prima che venga renderizzato qualcosa, togli prima la spunta a **Renderizza appena il piano è pronto**. Il
take si ferma allora al suo piano: aprilo, e nella sua pagina **Partitura**, **Scrivi un nuovo piano** ritira i dadi per una melodia che non
ti piace al prezzo di qualche secondo, e **Renderizza questa partitura** la renderizza. Un take che non ha ancora audio
viene completato; uno che ha già audio viene renderizzato come nuovo take accanto, così un render non
sovrascrive mai uno che vuoi tenere.

Il take compare nella libreria a destra e suona nella barra in basso.

### Il pannello del take e l'editor {#the-take-panel-and-the-editor}

Il **pannello di sinistra** mostra l'ultimo take su cui hai cliccato, in sola lettura: il suo stile, le impostazioni del suono, le
prime righe del testo, e la partitura come tonalità, tempo, durata e gli accordi di ogni sezione.
**+ Canzone**, **+ Cover** e **+ Strumentale** in alto avviano qualcosa di nuovo; quello del tipo
del take è evidenziato. La freccia accanto al pannello lo richiude, così i take hanno la larghezza,
e lo riapre. Singoli tasti agiscono sul take mostrato dal pannello (M per il rack di mastering, E per
l'editor e altri): vedi [Scorciatoie da tastiera](#hot-keys).

Creare e cambiare un take avviene nella **finestra dell'editor**. Il suo pulsante principale nel pannello dice cosa
fa al caso: *Modifica e renderizza di nuovo*, oppure *Rivedi il piano e renderizza* quando c'è un piano in attesa. Anche i pulsanti
**Partitura** e **Ancora** di una scheda la aprono, come un doppio clic su una scheda. Ha tre
colonne (la canzone, il testo e il suono), tutte in vista, con la partitura in una scheda propria.

Chiudere la finestra, con **Chiudi**, la crocetta o Esc, conserva ciò che hai scritto.

Il pulsante dopo **Chiudi**, in alto a destra, fa occupare alla finestra tutta la finestra del browser, e
un secondo clic la riporta alla dimensione abituale. La finestra si apre come l'hai lasciata l'ultima volta. A tutta finestra,
la colonna del testo prende tutta l'altezza: il riquadro del testo (quando ha già parole) e la struttura crescono nello
spazio, e il lettore resta in fondo alla colonna.

La riga in alto della finestra ha, più grandi, i pulsantini della scheda del take: Canta di nuovo, Variazioni,
Prova ancora, Dentro, Estrai, Normalizza e Sposta, ciascuno dove lo mostrerebbe la scheda. Normalizza è verde
finché il take è normalizzato, e un clic lo riporta allora al livello con cui è stato renderizzato; Dentro
si accende finché il take ne contiene altri, e chiude la finestra per mostrarli sotto il take.

### Una voce registrata {#a-recorded-voice}

Un take può essere cantato con una voce addestrata su una **registrazione** di qualcuno che canta: la tua, o quella di un
corpus. Sceglila nel campo *Voce registrata* dell’editor, oppure addestrane una con **Crea una voce…** da un file audio di canto. Bastano pochi
minuti; una registrazione con accompagnamento viene prima separata. Anche ogni scheda di corpus ha un pulsante **Crea una voce…**,
che addestra una voce sulle canzoni del corpus. Il campo compare solo se il servizio voce opzionale è in funzione
("Recorded voices" nel README).

L’addestramento attende il suo turno sulla GPU e può richiedere un’ora; l’elenco ne mostra l’avanzamento. Un take con una
voce viene renderizzato come al solito, poi la sua voce viene separata, ricantata con la voce e rimixata sul resto, prima
che ne venga misurato il livello.

**Ottava** sposta una voce in su o in giù di un’ottava intera. Una voce cantata lontano dalla sua estensione suona male, e
solo un’ottava intera mantiene il canto nella tonalità dell’accompagnamento. Il valore resta salvato sulla voce.
**Rigenera** addestra di nuovo la voce: una voce da corpus sulle canzoni del corpus come sono ora.

Il risultato è un canto convertito su un accompagnamento separato, quindi meno uniforme di un canto che il modello ha
cantato da sé. Registrazioni più pulite, senza perdita invece che MP3, danno una voce più pulita. La ricetta di un take
nomina la sua voce, e importandola si usa la voce con quel nome su questa installazione, se c’è.

**Scarica voce** salva una voce addestrata in uno zip da dare a qualcuno, e **Importa una voce…** ne aggiunge una: quello zip, o un modello RVC preso altrove (un .pth, o uno zip con il suo indice). Quanto canto usa l’addestramento si imposta nelle Impostazioni, *Voce registrata: minuti di canto*: viene diviso in parti uguali tra le canzoni di un corpus, e una decina di minuti basta.

### Impostazioni avanzate {#advanced-settings}

Il pulsante **Avanzate** nell'intestazione dell'editor apre impostazioni solo per questo take. La maggior parte delle canzoni
non ne ha mai bisogno. Si salvano con il take, così *Modifica e renderizza di nuovo* le ritrova come le hai lasciate.
Il pulsante si accende quando un'impostazione differisce dal suo valore predefinito, e **Ripristina predefiniti** le riporta
tutte indietro.

Alcune agiscono sul piano, altre sul render e sul file finale:

- **Passi di diffusione** (16–64, predefinito 32): quanti passi compie il decodificatore audio. Più passi richiedono
  più tempo di render.
- **Segui lo stile** (0–100, predefinito 1.0): con quanta fermezza la musica segue lo stile e il testo, la guida
  della fase che trasforma la partitura in suono (CFG). Sopra 1.0 si avvicina a loro; sotto, se ne allontana. La
  differenza è sottile con valori piccoli, e un render richiede un po' di più. Si può inserire qualsiasi valore accettato dal motore:
  una guida molto alta tende a suonare aspra più che fedele. Compare quando il motore lo ha: yue2.cpp, o il motore ComfyUI
  nella versione più recente (ricostruisci un vecchio motore Docker per averlo).
- **Evita:** parole da cui allontanarsi, come “drums” o “rap vocals”. Si aggiungono allo stile
  come “avoid: …”. È un suggerimento per il pianificatore, non una garanzia: il renderer non ha un prompt negativo.
- **Blocca tonalità:** il piano viene spostato in questa tonalità dopo che il pianificatore l'ha scritto. Il pianificatore ignora
  una tonalità nominata nello stile, quindi questo si fa sulla partitura stessa: ogni nota e ogni accordo si sposta dello
  stesso intervallo e l'armatura viene riscritta. Un piano minore resta minore, e si sposta solo
  la tonica. Un piano che l'app non riesce a leggere con certezza, come uno in un modo o con un cambio di tonalità
  a metà, resta nella tonalità del pianificatore e il log lo dice.
- **Blocca tempo** (BPM): il piano viene fissato a questo tempo, che sostituisce qualsiasi tempo dello stile o della
  partitura stessa del pianificatore, e il render lo segue.
- **Limite di token della partitura** (predefinito 8192): il massimo che il pianificatore può scrivere. Un limite più basso impedisce al piano di una canzone breve
  di allungarsi.
- **Limite di accordo tenuto** (battute, predefinito 8): il massimo di battute che il pianificatore resta su una stessa fondamentale prima
  di dover cambiare.
- **Bonus di armonia fuori tonalità** (0–10, predefinito 0): con quanta forza il pianificatore viene spinto verso accordi
  presi in prestito e fondamentali fuori dalla tonalità principale. Questi due agiscono sulle scelte del pianificatore, quindi si vedono come
  una differenza negli accordi del piano più che come una differenza netta all'ascolto. Confronta nella finestra
  Partitura.
- **Le voci seguono le indicazioni** (una casella sotto il riquadro del testo, che compare quando il testo ha un'indicazione di voce come
  `[male voice]`; attiva per un take nuovo): la melodia di ogni riga indicata si sposta di ottave fin dove canta la voce che
  la sua indicazione nomina. Vedi [Il testo](#the-words).
- **Segui esattamente questa struttura** (una casella sotto il riquadro del testo, non in Avanzate; canzoni; disattivata per impostazione predefinita): il piano scrive esattamente le sezioni che il testo nomina, in
  ordine, e nessun'altra. Disattivata, il pianificatore dà forma alla canzone da sé e spesso aggiunge un'intro, un outro o un
  interludio, o tralascia una sezione. Un piano può comunque finire prima dell'elenco.
- **Le sezioni iniziano diversamente** (Segui l'armonia, Sempre, Mai): se una sezione può iniziare con gli stessi
  accordi della precedente. *Segui l'armonia* lo attiva da Colorata in su e lo lascia spento sotto; *Sempre* e
  *Mai* decidono per questo take a qualsiasi livello, per confrontare due piani con e senza.
- **Volume di destinazione:** il livello a cui un take viene normalizzato. Vale solo quando la normalizzazione è attiva.
- **Dissolvenza finale** (secondi, predefinito 3): la durata della dissolvenza quando un take viene tagliato al limite di
  durata.

### Cosa mettere nel riquadro Stile {#what-to-put-in-the-style-box}

YuE2 lo legge come la descrizione di una registrazione, quindi descrivi una registrazione. Lingua, genere, voce,
strumenti, atmosfera, tempo e produzione, più o meno in quest'ordine, tutto in una frase. Gli elenchi di tag sciolti
funzionano peggio, e i marcatori di sezione come `[Verse]` vanno nel testo, non qui.

I chip **Voce** qui sotto scrivono nello stile per te: femminile, maschile o duetto, e un carattere
come soffiata o graffiante. Sono una scorciatoia di scrittura, e puoi modificare il risultato a mano.

### Abbozzare il testo {#drafting-the-lyrics}

**La struttura.** Sopra il riquadro del testo, finché non ha parole, una canzone ha una **struttura** da costruire, come
uno strumentale: un elenco di sezioni che puoi riordinare, togliere e ampliare (intro, strofa, pre-ritornello, ritornello, ponte,
interludio, outro). **Parti da…** lo riempie con una forma comune, e la descrizione a comparsa di ogni forma dice a cosa serve. Un
**interludio** è un passaggio strumentale: l'autore mette il suo tag su una riga a sé, e il pianificatore lo suona con
la voce strumentale. **Metti le sezioni nel riquadro del testo** inserisce i tag come sezioni vuote sotto cui scrivere a mano.
Appena il riquadro ha parole, viene cantato il testo e la struttura si fa da parte.

**Scrivi testo**, accanto al riquadro del testo, chiede di cosa parla la canzone e scrive parole per le sezioni che hai costruito.
**Versi per strofa o ritornello** stabilisce quanto è lunga ciascuna: più righe in una sezione danno una canzone più lunga, perché il
pianificatore scrive più o meno tanta musica quante sono le parole. Lo stile qui sopra dà l'atmosfera. Gemma scrive la bozza nello stesso
motore, e arriva nel riquadro con un titolo se non ne avevi dato uno; un [LLM esterno](#external-llm) può scriverla al suo posto, impostato in Impostazioni. La finestra si chiude appena la bozza inizia, e l'avanzamento compare accanto al riquadro del testo.
I pulsanti dell'editor del testo aggiungono anche una qualsiasi di queste sezioni, oltre alle indicazioni di voce (+ Uomo, + Donna, + Entrambe).

**Come suonano i versi** stabilisce il ritmo e la rima che l'autore cerca. *Naturale* (predefinito) mescola righe brevi e lunghe
con qualche rima. *Rima regolare* è la forma tradizionale di righe uguali che rimano a coppie, che è ciò che
l'autore produceva prima che questa opzione esistesse. *Ritmo parlato* è colloquiale, come il parlato o il rap; *Rima
libera* fa rimare solo alcune righe; *Breve e incisivo* e *Lungo e fluido* fissano la lunghezza delle righe.

È una prima bozza. Le righe hanno ritmo e rimano, ma un modello ricorre a immagini note, e nulla
controlla se una riga è già di qualcun altro. Leggila e falla tua prima di pianificare.

---

## Scrivere una canzone da un prompt: tutte le opzioni {#writing-a-song-from-a-prompt-every-option}

**+ Canzone** ha ormai molte opzioni. Nessuna è obbligatoria: uno stile e un po' di testo bastano, come in
[La tua prima canzone](#your-first-song). Questo capitolo le passa tutte nell'ordine in cui le mostra l'editor,
nelle sue tre colonne (la canzone, il testo e il suono), e poi cosa fare dopo il piano. Finisce con una
tabella dei desideri comuni, come una canzone più lunga o un ritornello che suoni diverso dalla strofa.

### La canzone {#the-song}

- **Titolo.** Facoltativo. Se resta vuoto, si usa la prima riga del testo.
- **Stile.** L'elenco **Scegli uno stile…** ha 200 punti di partenza, dall'afrobeats allo zydeco, in ordine alfabetico.
  Sceglierne uno riempie il riquadro Stile con una descrizione completa, che puoi poi modificare. I chip qui sotto sono dieci
  avvii rapidi per una canzone: warm indie rock, soulful jazz-pop, synthwave, acoustic ballad, heavy rock, modern pop,
  country, hip hop, smooth R&B e dance pop. Vedi [Cosa mettere nel riquadro Stile](#what-to-put-in-the-style-box).
- **Salvare uno stile tuo.** **Salva**, accanto all'elenco, salva ciò che c'è nel riquadro Stile con un nome che
  scegli tu. La prima voce dell'elenco, **Stili salvati**, apre quelli che hai salvato; il cestino accanto a uno lo elimina, e la
  ricerca dell'elenco li trova insieme ai 200. Salvare con un nome già usato sostituisce quello stile. La parola chiave di una
  LoRA di stile non viene salvata, e viene rimessa per la LoRA scelta quando usi lo stile.
- **Un tempo nello stile è solo un suggerimento.** Il pianificatore di solito sceglie il suo. Per fissare il tempo, usa **Blocca tempo** in
  Avanzate.
- **Voce.** I chip scrivono una voce (femminile, maschile, duetto e un carattere) nello stile per te.
- **LoRA di stile.** In fondo alla colonna del suono. Vedi [LoRA di stile](#style-loras).

### Il testo {#the-words}

**La struttura.** Sopra il riquadro del testo, finché non ha parole, c'è un elenco di sezioni: l'ordine che
la canzone seguirà. Ogni riga si può cambiare in un'altra sezione, spostare su o giù (o trascinare), o togliere, e i
chip sotto l'elenco aggiungono una sezione. Le sezioni sono intro, strofa, pre-ritornello, ritornello, ponte, interludio e outro.
Un **interludio** è un passaggio strumentale: non ha parole, e il pianificatore lo suona con la voce strumentale.
(`solo` non è una sezione che il pianificatore conosca; l'interludio è il modo di chiederne uno.)

**Parti da…** riempie l'elenco con una forma comune. Passa il mouse su un'opzione per vedere a cosa si adatta:

| Forma | Sezioni | Adatta a |
|---|---|---|
| Strofa, ritornello, ponte | strofa, ritornello, strofa, ritornello, ponte, ritornello | la canzone classica: pop, rock, country |
| Breve | strofa, ritornello, strofa, ritornello | folk, punk, primo rock and roll |
| Intro e outro | intro, strofa, ritornello, strofa, ritornello, outro | ballate, soft rock, cantautori |
| Storia | strofa, strofa, ritornello, strofa, ritornello, outro | canzoni narrative, folk, country |
| Pop con pre-ritornello | strofa, pre-ritornello, ritornello, strofa, pre-ritornello, ritornello, ponte, ritornello | pop moderno, dance-pop, pop rock |
| Prima il gancio | ritornello, strofa, ritornello, strofa, ritornello, ponte, ritornello | pop dell'era dello streaming, indie pop |
| Breve e semplice | strofa, ritornello, strofa, ritornello, ritornello | punk, garage rock, rockabilly |
| Hip-hop | intro, strofa, ritornello, strofa, ritornello, strofa, outro | rap, hip-hop, trap, R&B |
| Doppio ponte | strofa, ritornello, strofa, ritornello, ponte, ponte, ritornello, ritornello | power ballad, rock progressivo e sinfonico |
| Interludio | strofa, ritornello, interludio, strofa, ritornello, ponte, ritornello | rock, pop rock, indie |
| Tutte le parti | intro, strofa, pre-ritornello, ritornello, interludio, strofa, pre-ritornello, ritornello, outro | pop, dance-pop |

**Quante sezioni.** Il pianificatore di solito scrive da 8 a 10 sezioni qualunque cosa chieda il testo, quindi un elenco di più
di 10 viene condensato e le parole delle sezioni che scarta non vengono cantate. Il costruttore lo segnala quando l'elenco è
così lungo. Una canzone non si allunga aggiungendo sezioni; ognuna diventa solo più breve. Vedi
[Allungare la canzone](#making-the-song-longer).

**Metti le sezioni nel riquadro del testo** inserisce le sezioni come tag vuoti, pronti per scriverci sotto a mano. Appena il riquadro ha
parole, viene cantato il testo, e il costruttore si fa da parte.

**Scrivi testo.** Descrivi di cosa parla la canzone e un modello scrive parole per le sezioni che hai costruito. Chiede
tre cose:

- **Versi per strofa o ritornello** (4, 6 o 8; 6 per impostazione predefinita). Più righe in una sezione danno una canzone più lunga,
  perché il pianificatore scrive più o meno tanta musica quante sono le parole. Un'intro, un ponte o un outro restano su 2–4 righe,
  e un interludio non ne ha.
- **Come suonano i versi.** L'elenco mostra le sillabe che ogni riga cerca. Il vecchio autore produceva quasi sempre le stesse
  righe rimate di otto sillabe, e questo lo cambia:

| Opzione | Cerca | Cosa ottieni |
|---|---|---|
| Naturale (predefinito) | 3-13 sillabe | Un misto di righe brevi e lunghe, qualche rima, nessuna pulsazione fissa |
| Rima regolare | 6-10 sillabe | Righe uguali che rimano a coppie: la forma tradizionale, e ciò che faceva prima l'autore |
| Ritmo parlato | 5-14 sillabe | Colloquiale e ritmico, come il parlato o il rap, con rime interne |
| Rima libera | 4-13 sillabe | Alcune rime, alcune assonanze, alcune nessuna, e righe di lunghezza diversa |
| Breve e incisivo | 3-6 sillabe | Righe brevi e frasi ripetute |
| Lungo e fluido | 10-14 sillabe | Righe lunghe che scorrono come un pensiero |

  L'ultima scelta viene ricordata. Sono obiettivi, non garanzie: un modello linguistico li segue da vicino agli
  estremi (breve e incisivo, lungo e fluido) e più liberamente nelle sfumature.
- **La richiesta** stessa, con parole tue, e lo stile qui sopra, che dà l'atmosfera. La richiesta si salva con il take,
  così aprire un take e premere **Scrivi testo** mostra di cosa si chiedeva che parlasse, pronta da cambiare e riscrivere.

La bozza arriva nel riquadro del testo, e la finestra si chiude appena inizia. È una prima bozza: leggila e falla
tua.

**Segui esattamente questa struttura** (la casella sotto il riquadro del testo, disattivata per impostazione predefinita). Il pianificatore prende i tag
di sezione del testo come orientamento, e da sé scrive una forma propria: spesso aggiunge un'intro e un outro,
scambia un ponte con un interludio e una strofa, o condensa un elenco lungo. Con questa attiva, il piano scrive esattamente le
sezioni che il testo nomina, in quell'ordine, e nessun'altra. Non può aggiungere un'intro o un outro che tu non
abbia messo. Il pianificatore decide comunque com'è la musica e quando inizia ogni sezione. Vale solo per le canzoni.

**Chi canta ogni riga: indicazioni di voce.** Una riga da sola tra parentesi quadre che nomina una voce dice chi canta le
righe seguenti, fino alla prossima indicazione o alla prossima sezione:

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

Scrivi un'indicazione come `[male voice]`, `[female voice]` o `[both voices]`, ciascuna su una riga propria tra parentesi quadre.
L'editor del testo ingrandito ha i pulsanti **+ Uomo**, **+ Donna** e **+ Entrambe** nell'intestazione per inserirle al cursore.
Queste sono le forme con cui la funzione è stata provata, più `vocal` al posto di `voice` (`[female vocal]`) e
`[male and female voices]` per entrambe. Puoi aggiungere parole tue dopo una virgola, come in
`[female voice, soft and close]`; non cambiano chi canta. Una sezione senza indicazione è lasciata al pianificatore.

Si leggono anche altre grafie, così un testo scritto altrove non viene ignorato: `[man]`, `[woman]`, `[duet]`, un'indicazione
dentro il tag di una sezione come `[Verse 2 - female vocal]`, e un'indicazione tra parentesi tonde, `(female voice)`. Le parentesi quadre
sono l'abitudine più sicura: le parole tra parentesi tonde sono spesso cori, e possono essere cantate.

Un'indicazione da sola non decide la voce. Chi canta dipende soprattutto da quanto è alta la melodia scritta: la stessa
riga un'ottava sopra la canta una donna, e al pianificatore piace scrivere una strofa su due ottave, cambiando ogni quattro
righe circa, qualunque sia l'indicazione. **Le voci seguono le indicazioni** (una casella sotto il riquadro del testo, che compare quando il testo ha
un'indicazione; attiva per un take nuovo) rispetta le indicazioni: quando il piano viene scritto, ogni tratto indicato della melodia si sposta di
ottave intere fin dove canta quella voce, in basso per un uomo e in alto per una donna. Nient'altro cambia nel piano. Viene
rifatto prima di ogni render, così segue un cambiamento nel testo o nella partitura. Nella pagina Partitura,
**Voci secondo le indicazioni** fa lo stesso una volta sulla partitura del riquadro, per un take fatto senza la casella; salva la partitura
e renderizzala.

Tre cose da sapere:

- **Chi canta una riga è ancora in parte fortuna.** Con la melodia al suo posto, la maggior parte delle righe va alla voce
  indicata, ma un render può comunque darne una all'altra voce. Renderizza di nuovo con un altro seed, o usa
  **Prova ancora**.
- **Entrambe** mette la riga dove canta una donna e lascia la seconda voce al render, che spesso ne aggiunge una
  in un ritornello. Chiede un duetto più che crearlo: quanto senti della seconda voce cambia da un
  render all'altro. Non c'è ancora modo di scrivere due cantanti su una riga senza che il testo ne soffra.
- Un take fatto prima che esistesse questa casella mantiene la partitura com'è; spuntala, o usa **Voci secondo le indicazioni**, per sistemarla.

**Scrivere a mano.** Il pulsante Espandi apre un editor a tutta grandezza con pulsanti per intro, strofa, pre-ritornello,
ritornello, ponte, interludio, outro e strumentale. Una sezione è una riga come `[Verse]` seguita dalle sue righe; un
tag senza righe sotto, come `[Interlude]`, è un passaggio strumentale.

### Il suono {#the-sound}

- **Armonia** (il cursore): quanto sono audaci gli accordi. Una canzone nuova parte da **Varia**, con l'interpretazione
  su **Ampia**: nelle nostre prove questa coppia ha dato le versioni musicalmente più interessanti, quindi è un buon punto di partenza. Sposta
  l'uno o l'altra come preferisci. I take esistenti mantengono ciò con cui sono stati fatti. Da solo, il pianificatore tende a scrivere un loop di
  quattro accordi e usarlo in ogni sezione, e ogni livello lo allontana un po' di più da questo. I livelli si sommano
  l'uno all'altro:

  | Livello | Cosa fa agli accordi | Sceglilo quando |
  |---|---|---|
  | Familiare | Niente: gli accordi di YuE2, spesso un solo loop per tutta la canzone | Ti piace la prima idea del pianificatore, o vuoi l'accompagnamento più semplice |
  | Varia | Scoraggia la ripetizione esatta degli accordi appena usati, quindi li ricolora (un F, poi un Fmaj7) ma resta nella tonalità | Il loop suona troppo uguale e vuoi che la canzone resti convenzionale |
  | Colorata | Lo stesso, più forte: strofa e ritornello si separano, con accordi più ricchi. Una sezione inoltre non può iniziare con gli stessi accordi della precedente, così un ritornello non inizia più come la sua strofa | Vuoi che il ritornello sia uno slancio, non una ripetizione. Un buon primo passo |
  | Avventurosa | Scoraggia le *fondamentali* usate di recente, non solo le grafie, quindi l'armonia deve viaggiare, e prende in prestito accordi fuori dalla tonalità | Vuoi movimento e sorpresa, e starai attento a un accordo che suona strano |
  | Fuori tonalità | Audace, con un'attrazione per accordi fuori dalla tonalità | Esperimenti. Mettiti in conto di scartare qualche piano |

  Da Colorata in su, le scelte degli accordi escono più diverse da una sezione all'altra: più accordi diversi in una
  canzone, più schemi di quattro battute che non si ripetono, e meno ritornelli che copiano l'inizio della strofa. Il piano resta
  una canzone normale, quindi vale la pena provare uno o due livelli più su prima di ricorrere a una Varietà del piano più sfrenata.
  In **Avanzate**, **Le sezioni iniziano diversamente** si può mettere su *Sempre* o *Mai* per provare un piano con e senza
  la regola del ritornello; il predefinito, *Segui l'armonia*, è attivo da Colorata in su. Uno stile come la trap o l'ambient è spesso
  basato sui loop per natura, quindi aspettati un cambiamento minore che nel pop o nel rock. Vedi [Armonia](#harmony) per le misure.
- **Varietà del piano.** Con quanta libertà il pianificatore scrive tutto il resto. Vedi [Varietà del piano](#plan-variety).
- **Interpretazione.** Come vengono suonate le note nel render. Vedi [Interpretazione](#interpretation).
- **Durata massima.** Il momento più tardi in cui la canzone può finire. Vedi [Durata](#length).
- **Modalità.** *Completo* mantiene gli accordi del piano; *melodia* lascia libero l'accompagnamento. *Senza partitura*, per le canzoni, non scrive
  alcun piano: vedi [Una canzone senza partitura](#a-song-with-no-score).
- **Seed**, e **mantieni questo seed**. Vedi [Il seed, e riprodurre un take](#seed-and-reproducing-a-take).
- **Rifinitura di produzione** e **Normalizza il volume.** Vedi [Rifinitura della produzione](#production-polish).
- **Renderizza appena il piano è pronto**, accanto al pulsante in fondo alla finestra, fa il piano e il render
  senza fermarsi in mezzo. All'inizio è spuntato, e l'editor ricorda la tua scelta. Togli la spunta per leggere prima il
  piano.
- **Avanzate** (il pulsante dell'intestazione): passi di diffusione, Segui lo stile, Evita, Blocca tonalità, Blocca tempo, la partitura più lunga,
  limite di permanenza su un accordo, bonus di armonia esterna, Sezioni che iniziano diversamente, loudness obiettivo e la dissolvenza finale. Vedi
  [Impostazioni avanzate](#advanced-settings).
- **Mastering** (il pulsante alla sua sinistra, quando il take ha un suono) apre il rack di mastering sopra l'editor per
  il take che contiene. Il rack è, in ordine, un equalizzatore stile 1073, un equalizzatore parametrico, un compressore, un allargatore stereo e
  un limiter. Nel grafico dell'equalizzatore parametrico, ciascuna delle sette bande è un punto: trascinalo di lato per la frequenza
  e su o giù per il guadagno, gira la rotellina sopra di esso per l'ampiezza, fai doppio clic per azzerarlo. La striscia sotto
  il grafico imposta il tipo della banda scelta (taglio dei bassi, shelf dei bassi, campana, notch, shelf degli acuti, taglio degli acuti) e la attiva
  o disattiva, **Piatto** riporta ogni banda a 0 dB, e il pulsante nell'angolo del grafico cambia quanti decibel mostra il
  grafico. Il pulsante è verde finché il rack cambia il suono del take. Con il rack aperto, la barra spaziatrice riproduce
  e mette in pausa il take e le frecce si muovono al suo interno e regolano il volume, come nella pagina principale. Esc chiude
  il rack, e di nuovo chiude l'editor.

### Allungare la canzone {#making-the-song-longer}

La durata di una canzone la stabilisce il suo piano, e il render segue la durata del piano. Ecco cosa la sposta:

| Per ottenere… | Fai così |
|---|---|
| Una canzone più lunga | Dai più righe a ogni sezione (**Versi per strofa o ritornello**: 6 o 8) |
| Una canzone più lenta e più lunga | Imposta un **Blocca tempo** in Avanzate. Lo stesso piano a meno BPM dura di più |
| Una canzone più lunga aggiungendo sezioni | Non funziona: un piano ha circa 8–10 sezioni, quindi di più si accorciano o vengono condensate |
| Più di quanto il piano consenta | Scrivi un piano nuovo; le durate variano molto tra esecuzioni con lo stesso testo |
| Una canzone che finisca alla fine del suo testo | Alza il limite di durata solo se viene tagliata; il limite è un tetto, non un obiettivo |

### Dopo il piano {#after-the-plan}

- **Renderizza questa partitura** crea un take nuovo ogni volta che il take aperto ha già audio, così un render non sovrascrive mai uno
  che vuoi confrontare. Un take che non ha ancora audio viene completato.
- **Mantieni questa melodia** (dopo aver cambiato il testo di un take): canta la partitura del take con il nuovo testo, come take nuovo. La
  melodia non può guadagnare sezioni né note, quindi se il tuo testo ha più sezioni della melodia, o molte più o molte meno
  sillabe di quante note abbia (righe lunghe su una melodia fatta per righe brevi, o brevi su una fatta per righe lunghe), la
  casella si deseleziona da sola e viene scritto un piano nuovo, con una riga che dice perché. Vedi [Stessa melodia, nuovo testo](#same-tune-new-words).
- **Filtrare la libreria.** I pulsanti **Canzone**, **Cover** e **Strumentale** accanto ai filtri mostrano solo quei
  tipi nello spazio aperto; scegline più d'uno, o nessuno per tutti i tipi.

---

## Leggere e correggere il piano {#reading-and-fixing-the-plan}

Il piano è scritto in **notazione ABC**: musica come testo semplice, lettere al posto dei puntini su un pentagramma.
Chris Walshaw la ideò all'inizio degli anni Novanta per spedire melodie folk via e-mail, ed è rimasta.

Non devi saperla leggere. L'app mostra lo stesso piano come **sigle degli accordi** e come vera **notazione
su pentagramma** sotto l'editor, e **Espandi** apre il tutto a piena grandezza. Ma il testo è ciò che YuE2
ha scritto e da cui renderizza, quindi vale la pena sapercisi muovere.

### Leggere un piano {#reading-a-plan}

Un piano inizia con un'intestazione, una lettera e due punti per riga:

```
X:1
M:4/4
L:1/32
Q:1/4=120
V: Vocal clef=treble name="Vocal Melody"
V: Ins   clef=treble name="Ins Melody"
K:D#m
```

| Riga | Significa |
|---|---|
| `X:1` | il numero della melodia. Ogni file ABC ne inizia con uno |
| `M:4/4` | il metro — quattro movimenti per battuta |
| `L:1/32` | la durata unitaria: una lettera da sola dura una biscroma |
| `Q:1/4=120` | il tempo — una semiminima a 120 battiti al minuto |
| `V:` | dichiara una voce. YuE2 ne scrive due, una linea vocale e una strumentale |
| `K:D#m` | la tonalità, re diesis minore. `K:` va sempre alla fine dell'intestazione |

Poi la musica vera e propria:

```
% intro
V: Vocal
z24z4"D#m"z4|"D#m"z32|
V: Ins
Z|d16a16-|a16g8a8|
```

- **Le note sono lettere.** `d16` è un re che dura 16 unità. Le minuscole suonano un'ottava sopra le maiuscole,
  e `'` o `,` le spostano ancora.
- **`-` lega** una nota alla successiva, così suonano come una sola.
- **`z` è una pausa**, con una durata come una nota. Una `Z` maiuscola è una pausa di battuta intera.
- **Gli accordi stanno tra virgolette doppie**, come `"D#m"`, e vanno davanti alla nota su cui iniziano. È questo
  che modifica **trova e sostituisci**.
- **`|` è una stanghetta**, e **`%` apre un commento** — così si segnano le sezioni:
  `% intro`, `% verse`, `% chorus`.

Quindi quel frammento dice: re diesis minore, quattro quarti, 120 battiti al minuto, e durante l'intro la
voce tace portando l'accordo, mentre lo strumento suona un re e un la legati, poi sol e la.

Due conseguenze pratiche. **Modificare gli accordi è sicuro** anche se le note sembrano oscure — sono solo
le parti tra virgolette, e tutto il resto può restare com'è. E **se modifichi il piano, il render
usa ciò che hai modificato**, quindi correggerne uno è spesso più veloce che ritirare finché ne esce uno buono.

### Ascoltarlo {#hearing-it}

La scheda **Notazione** ha un lettore sopra i pentagrammi. Premi **Riproduci** per sentire il piano così come è nel
riquadro, modifiche comprese, per giudicare a orecchio una melodia di cui dubiti prima di spenderci un
render. Le note che suona si evidenziano man mano, e il suo controllo del tempo cambia solo l'anteprima,
non la partitura. Avviarlo ferma ciò che stava suonando la barra del lettore, perché due cose insieme non
servono a nessuno, e chiudere la finestra — o passare a Accordi o Testo — lo ferma pure, così nulla resta
a suonare senza un comando a portata di mano.

**Strumenti** suona ogni voce con uno strumento nominato dallo stile, invece di un pianoforte
per tutto: uno stile che dice *electric guitar, drums* si sente con una chitarra, i suoi accordi suonati da
un'altra, e un basso sotto; una linea cantata la sostituisce una voce, e la melodia di uno strumentale
no. Uno stile che nomina la batteria riceve anche una parte di batteria, scritta nel metro della partitura
stessa — un backbeat per il rock, il four-on-the-floor per la dance, un ride per il jazz, qualcosa di più scarno per una
ballata — e suona dall'inizio alla fine, perché la partitura non ha sezioni in cui tacere. La
riga accanto al lettore dice cosa ha scelto, e togliendo la spunta si torna al pianoforte che sentiresti
altrimenti. È una lettura dello stile, non del render: YuE2 decide la
vera interpretazione e aggiunge parti che la partitura non ha mai avuto, quindi prendilo come il piano suonato con i colori
giusti più che come suonerà il take.

**Scarica MIDI** salva la partitura per una DAW. Ogni parte è una traccia a sé, sul proprio canale,
con lo strumento usato dall'anteprima assegnato a quel canale: la linea vocale, la linea strumentale e,
a meno che tu non tolga la spunta a **Accordi**, le sigle degli accordi come una parte di accordi con il suo basso accanto (l'unico
punto in cui l'armonia è scritta in note), e la batteria sul canale 10 quando lo stile la chiede. Gli
strumenti sono numeri di programma General MIDI, così la tua DAW li suona con i propri suoni, e
tempo e metro sono nel file. Un piano che cambia metro a metà viene scritto nel metro con cui
inizia — solo quello viene registrato — mentre le note mantengono le proprie durate. Cliccare su una nota nei
pentagrammi porta il cursore all'ABC che l'ha scritta.

Una partitura con una nota sopra quanto questi strumenti possono suonare, o sotto, viene suonata spostata di ottave
intere finché ci sta, e la riga accanto al lettore dice di quanto; i pentagrammi, il file MIDI e
la partitura stessa non cambiano. Gli strumenti non hanno tutti la stessa estensione — un basso sta molto sotto
un pianoforte — per questo la riga compare quando una partitura viene spostata. Una partitura che non ha ancora note
non ha nulla da suonare e lo dice.

Il lettore ha bisogno dei suoi campioni di note, che non fanno parte dell'app: ogni strumento pesa circa 7 MB,
viene scaricato dalla sua origine la prima volta che un'anteprima lo usa e conservato nella libreria, così
poi funziona offline. **Riproduci** scarica ciò che serve alla partitura attuale e poi parte, e
**Scarica i suoni** scarica lo stesso senza suonare, per chi preferisce averlo pronto
prima.

### Il piano roll {#the-piano-roll}

Clicca **Piano roll** nella finestra della partitura per aprire l'editor MIDI visuale. Invece di modificare lettere ABC grezze, vedi e modelli la melodia direttamente su una griglia interattiva di altezza e tempo.

L'editor mostra le due voci della partitura insieme — **Vocal** (la melodia cantata principale in azzurro cielo) e **Ins** (l'accompagnamento strumentale in ambra calda). Le due voci sono sempre pienamente attive, visibili, selezionabili e modificabili. I pulsanti **Disegna** in alto a sinistra scelgono a quale voce vengono assegnate le nuove note quando clicchi per aggiungerle.

#### Modificare le note {#editing-notes}

- **Aggiungere una nota:** clicca su una cella vuota della griglia per creare una nota a quell'altezza e in quel momento. La nota suona subito così ne senti il tono.
- **Selezionare le note:** clicca su una nota per selezionarla. Tieni premuto <kbd>Shift</kbd> o <kbd>Ctrl</kbd>/<kbd>Cmd</kbd> mentre clicchi per selezionare più note nelle parti vocale e strumentale. Clicca e trascina un **riquadro di selezione** su un'area vuota per selezionare una frase o un passaggio in tutte le voci. Premi <kbd>Ctrl</kbd>+<kbd>A</kbd> (<kbd>Cmd</kbd>+<kbd>A</kbd> su macOS) o clicca **Seleziona tutto** per selezionare tutte le note della partitura. Per selezionare tutte le note dal cursore di riproduzione alla fine della canzone, premi <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>A</kbd> o <kbd>Alt</kbd>+<kbd>A</kbd> (o clicca **Dal cursore ▶** nella barra degli strumenti).
- **Spostare le note:** trascina una nota selezionata per anticiparla o posticiparla, o in verticale per trasporne l'altezza. Quando sono selezionate più note — vocali, strumentali o di entrambe — si spostano tutte insieme, mantenendo il tempo relativo, le melodie e il testo.
- **Durata:** trascina il bordo destro di una nota per allungarla o accorciarla. Il selettore **Aggancio** (1/16, 1/8 o 1/4 di nota) vincola spostamenti e ridimensionamenti a suddivisioni musicali pulite.
- **Eliminare le note:** fai doppio clic su una nota per eliminarla, o selezionane una o più e premi <kbd>Delete</kbd> o <kbd>Backspace</kbd>.
- **Annulla e ripeti:** ogni modifica, spostamento, ridimensionamento, aggiunta ed eliminazione di una nota finisce nella cronologia. Premi <kbd>Ctrl</kbd>+<kbd>Z</kbd> (<kbd>Cmd</kbd>+<kbd>Z</kbd>) per annullare, e <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>Z</kbd> o <kbd>Ctrl</kbd>+<kbd>Y</kbd> per ripetere.
- **Ascoltare i tasti:** clicca un tasto della tastiera di pianoforte a sinistra per sentirne l'altezza.
- **Massimizzare:** clicca **Massimizza** nella barra in alto per allargare il piano roll a tutta la larghezza della finestra del browser.

#### Linea del tempo, sezioni e accordi {#timeline-sections-and-chords}

Lungo il righello in alto, la linea del tempo mostra i numeri di battuta e i confini delle sezioni:
- **Rinominare le sezioni:** clicca un indicatore di sezione (`intro`, `verse`, `chorus` ecc.) per modificarne il nome o riassegnarla.
- **Modificare gli accordi:** subito sotto il righello delle battute, la traccia degli accordi mostra la progressione armonica della canzone. Clicca un accordo esistente per rinominarlo (per esempio cambiare `C` in `Am7` o `G/B`), o una battuta vuota per mettere un accordo nuovo.
- **Armonizzare le battute vuote (Riempi i vuoti):** clicca **Riempi i vuoti** nella barra degli strumenti per riempire le battute vuote dell'accompagnamento strumentale con note generate dalla progressione di accordi.
- **Togliere le battute vuote (Compatta i vuoti):** clicca **Compatta i vuoti** per togliere le battute vuote e silenziose in entrambe le voci, spostando a sinistra le note e gli accordi successivi per eliminare buchi indesiderati nell'arrangiamento.

#### Testo e karaoke {#lyrics-and-karaoke-tracking}

Nella parte bassa del piano roll, una traccia del testo dedicata allinea ogni sillaba alla melodia vocale:
- **Adattamento per frasi:** clicca **Abbina testo** per distribuire il testo sulla melodia vocale. L'allineamento rileva i respiri naturali e le pause tra le frasi melodiche, e assegna ogni riga di testo alla sua frase senza far scivolare parole oltre le pause nelle battute seguenti. Le parole di più sillabe vengono divise in modo pulito tra le note.
- **Modificare le sillabe:** clicca un'etichetta del testo (o seleziona una nota vocale e premi <kbd>L</kbd>) per modificarne il testo. Se scrivi sillabe separate da spazi o trattini (per esempio `Hel- lo world`), vengono distribuite automaticamente sulle note vocali consecutive.
- **Evidenziazione al passaggio del mouse:** passare il mouse su un'etichetta del testo evidenzia la nota corrispondente nella griglia, e passarlo su una nota vocale evidenzia la sua etichetta sotto.
- **Pallina del karaoke:** durante la riproduzione, una pallina animata salta su ogni nota mentre viene cantata, e la sillaba attiva e la nota della griglia si illuminano in tempo reale.

#### Riproduzione e accompagnamento armonico {#playback-and-harmony-accompaniment}

Premi <kbd>Space</kbd> o clicca **▶ Riproduci** per iniziare a riprodurre dal cursore. La linea di riproduzione scorre sulla griglia, aggiornando battuta, movimento e contatore del tempo trascorso.

- **Clic udibile (metronomo):** la riproduzione include per impostazione predefinita un clic udibile, con un colpo di woodblock accentato sul primo movimento di ogni battuta e clic più morbidi sugli altri. Premi <kbd>C</kbd> o <kbd>M</kbd> (o clicca **Clic** nella barra di trasporto) per attivare o disattivare il metronomo in qualsiasi momento.
- **Accompagnamento armonico degli accordi:** la riproduzione sintetizza caldi pad di accordi polifonici direttamente dalla progressione di accordi della partitura. Anche quando le tracce vocale o strumentale tacciono, lo spazio armonico resta musicale e caldo invece di cadere in un silenzio morto. Premi <kbd>H</kbd> (o clicca **Accordi** nella barra di trasporto) per attivare o disattivare l'accompagnamento degli accordi.
- **Spostarsi per battute:** premi <kbd>Freccia sinistra</kbd> e <kbd>Freccia destra</kbd> per tornare indietro e andare avanti di una battuta, o <kbd>Home</kbd> per tornare direttamente all'inizio.

#### Scorciatoie da tastiera {#keyboard-shortcuts}

| Tasto | Azione |
|---|---|
| <kbd>Space</kbd> | Riproduci / pausa |
| <kbd>Freccia sinistra</kbd> | Indietro di una battuta |
| <kbd>Freccia destra</kbd> | Avanti di una battuta |
| <kbd>Home</kbd> | Torna all'inizio (battuta 1) |
| <kbd>C</kbd> o <kbd>M</kbd> | Attiva / disattiva il clic udibile (metronomo) |
| <kbd>H</kbd> | Attiva / disattiva l'accompagnamento degli accordi |
| <kbd>Delete</kbd> / <kbd>Backspace</kbd> | Elimina le note selezionate |
| <kbd>Ctrl</kbd>+<kbd>Z</kbd> / <kbd>Cmd</kbd>+<kbd>Z</kbd> | Annulla l'ultima modifica |
| <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>Z</kbd> / <kbd>Ctrl</kbd>+<kbd>Y</kbd> | Ripeti |
| <kbd>Ctrl</kbd>+<kbd>A</kbd> / <kbd>Cmd</kbd>+<kbd>A</kbd> | Seleziona tutte le note di entrambe le voci |
| <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>A</kbd> / <kbd>Alt</kbd>+<kbd>A</kbd> | Seleziona tutte le note dal cursore alla fine in entrambe le voci |
| <kbd>+</kbd> o <kbd>=</kbd> | Aumenta la scala orizzontale |
| <kbd>-</kbd> o <kbd>_</kbd> | Riduci la scala orizzontale |
| <kbd>0</kbd> | Scorri fino alle note (adatta la vista) |
| <kbd>L</kbd> | Modifica il testo della nota vocale selezionata |
| <kbd>Escape</kbd> | Annulla la selezione, o chiudi la finestra della partitura |

### Armonia {#harmony}

Da solo, YuE2 tende a scrivere un loop di quattro accordi e restarci. Il cursore **Armonia** lo allontana
dagli accordi appena usati, senza rompere la struttura della canzone.

| Livello | Cosa ottieni |
|---|---|
| Familiare | Gli accordi di YuE2. Spesso un solo loop per tutta la canzone |
| Varia | Evita di ripetere gli stessi accordi. Resta nella tonalità |
| Colorata | Strofa e ritornello ricevono progressioni diverse, con accordi più ricchi. Una sezione non può iniziare come la precedente |
| Avventurosa | Tiene l'armonia in movimento e prende in prestito accordi fuori dalla tonalità |
| Fuori tonalità | Audace, e si allontana di più dalla tonalità |

**Scrivi un nuovo piano** usa la posizione attuale del cursore, così puoi ritirare con lo stesso testo e accordi più
audaci e confrontare.

Questo è stato misurato, non supposto — un solo testo, due stili, tre seed ciascuno:

| | Familiare | Varia | Colorata | Avventurosa | Fuori tonalità |
|---|---|---|---|---|---|
| Accordi diversi in una canzone | 4.7 | 6.3 | 8.7 | 9.0 | 10.3 |
| Battute con un accordo fuori tonalità | 0% | 0% | 0% | 13% | 24% |
| Schemi di quattro battute che non si ripetono | 29% | 38% | 50% | 63% | 64% |

Ogni piano, a ogni livello, ha mantenuto sezioni e accordi validi. Chiedere un'armonia audace nel
testo dello stile invece — “jazz harmony”, “borrowed chords” — non ha avuto alcun effetto misurabile.

### Varietà del piano {#plan-variety}

In *Avanzate*, **Varietà del piano** stabilisce con quanta libertà scrive il pianificatore. Dove l'Armonia agisce sugli
accordi, questa agisce su tutto: melodia, struttura e durata.

- **Tranquilla:** la più stabile. Pochi accordi, e una melodia che non si allontana.
- **Normale:** il valore predefinito.
- **Vivace:** qualche accordo e qualche svolta in più.
- **Audace:** un'armonia più ricca, circa tre volte il vocabolario di accordi normale, mentre la melodia resta
  riconoscibilmente dello stesso tipo.
- **Bizzarra:** irrequieta. Gli accordi cambiano di continuo, e la melodia salta tra registri da una
  sezione all'altra. Per canzoni strane e stravaganti.
- **Sfrenata:** la più irrequieta di tutte, e può cambiare tonalità a metà.

### Una canzone senza partitura {#a-song-with-no-score}

**Senza partitura**, la terza scelta di **Modalità**, canta il testo senza alcun piano: YuE2 scrive la melodia e
gli accordi mentre canta, come faceva lo YuE originale, e la canzone viene renderizzata subito con **Canta senza partitura**.
Spesso suona piuttosto diversa da una canzone pianificata.

Ciò che orienta un piano qui non ha su cosa agire, quindi **Armonia**, **Varietà del piano**, **Mantieni questa melodia** e **Segui esattamente questa struttura**
si attenuano mentre è scelta, e non c'è partitura da leggere o modificare. YuE2 decide
la durata, fino al limite. Blocca tonalità e Blocca tempo gli arrivano solo come parole nello stile. Canta di nuovo,
Variazioni, Prova ancora e il nuovo testo funzionano tutti, ognuno cantato di nuovo senza partitura. **Scrivi un nuovo piano** dà al take una
partitura, e Modalità torna su *completo*. È solo per canzoni da un prompt: una cover è la partitura della sua registrazione, e uno
strumentale ne ha bisogno per tenere fuori la voce. Entrambi i motori possono farlo.

---

## Renderizzare {#rendering}

### Interpretazione {#interpretation}

La partitura stabilisce le note. L'**interpretazione** stabilisce come vengono suonate.

| Interpretazione | Cosa senti |
|---|---|
| Standard | La lettura abituale di YuE2 |
| Serrata | più controllata e rifinita |
| Sciolta | più grezza e spontanea |
| Posata | libera di ripetere una figura e restare su un groove |
| Irrequieta | tiene le parti in movimento, evita di ripetersi |
| Ampia | cerca suoni meno ovvi |

### Variazioni {#variations}

Il pulsante a scintilla di una scheda renderizza **la stessa partitura e lo stesso seed** nelle altre
interpretazioni. Poiché cambia solo l'interpretazione, ciò che senti tra loro è
l'interpretazione — non un altro tiro di dadi. Ognuna è un take a sé, intitolato
*Night drive · Loose* e salvato dentro il take da cui è nato (vedi **Take dentro un take**,
in La libreria). La finestra ha un proprio limite di durata, che parte da quello dell'editor e vale solo
per questi take.

### Prova ancora {#try-more}

Il pulsante del dado di una scheda renderizza **la stessa partitura e lo stesso testo di nuovo come diversi take nuovi**, da
ascoltare insieme. Variazioni cambia solo l'interpretazione e mantiene il seed; questo cambia il
tiro:

- **Nuovi seed:** un seed nuovo per ciascuno, tutto il resto uguale.
- **Intensità del Pianificatore:** per un take con una LoRA di stile che ha una metà pianificatore, lo stesso seed con
  altre intensità del Pianificatore (la sua è esclusa). Il pianificatore cambia l'esecuzione stessa, non solo
  la voce, quindi funziona come un altro seed.

I take nuovi sono intitolati *Night drive · try 1* o *Night drive · planner 0.60* e salvati dentro
il take da cui sono nati, il cui pannello si apre per mostrarli man mano che finiscono. Per sentirli l'uno contro
l'altro, premi **Seleziona tutto** mentre il pannello è aperto e poi **Confronta**. La finestra ha un proprio
limite di durata, che parte da quello del take.

### Il seed, e riprodurre un take {#seed-and-reproducing-a-take}

Ogni take registra il suo seed e ogni impostazione che gli ha dato forma. La scheda li nomina, cliccare una scheda
li mostra nel pannello del take, e aprirla nell'editor ricarica tutto. **Ancora** apre
l'editor esattamente con questo, seed compreso, per riprodurre un take che ti è piaciuto, e cambiare un'impostazione alla volta su uno che ti è quasi
piaciuto.

Nei menu dell'editor, passare il mouse su un'interpretazione mostra cosa fa.

Spunta **mantieni questo seed** per mantenere lo stesso seed tra un render e l'altro; senza spunta, ogni render ne estrae uno
nuovo.

Un render usa ciò che mostra l'editor: lo stile, la LoRA di stile e le sue intensità, il limite di durata, la modalità,
l'interpretazione e il seed, anche quando si renderizza di nuovo la partitura stessa di un take.

### Stessa melodia, nuovo testo {#same-tune-new-words}

Il pianificatore legge tutto il testo prima di scrivere una nota, quindi lo stesso seed dà lo stesso piano solo
con lo stesso testo. Cambia una riga e il piano successivo è una melodia nuova: un'altra melodia, spesso un'altra
tonalità e un altro tempo, e la voce cambia con loro.

Per tenere una melodia che ti piace, apri il take e cambiane il testo. **Mantieni questa melodia** compare sotto il
testo, spuntato, e il pulsante principale diventa **Canta con il nuovo testo**. Cambia prima tutto il resto che
vuoi: lo stile, la LoRA e le sue intensità, il limite di durata, l'interpretazione. La partitura del take viene
allora cantata con il nuovo testo, come take nuovo accanto all'originale, che resta com'è. Lascia il seed
spuntato per mantenere la voce il più simile possibile. Togli la spunta a **Mantieni questa melodia** per scrivere invece un piano nuovo, e una
melodia nuova, per il testo. Un testo nuovo che mantiene il numero di sillabe delle vecchie righe si adatta meglio
alla melodia. Quando non lo fa, perché ci sono più sezioni o molte più sillabe di quante note abbia la melodia (righe lunghe su una melodia
fatta per righe brevi: le righe escono ripetute o si perdono), o molte meno (righe brevi su una melodia fatta per righe lunghe:
il cantante riempie le note in più con parole sue), **Mantieni questa melodia** si deseleziona da solo con una riga che dice perché, e
viene scritto un piano nuovo per il testo. Rimetti la spunta per cantare comunque la melodia.

### Rifinitura della produzione {#production-polish}

**Rifinitura di produzione** applica la LoRA del decodificatore Realaudio di Mothersuperior. YuE2 così com'è suona spesso inscatolato
nei medi; questa separa più nettamente strumenti e voci. Attiva per impostazione predefinita.

### Durata {#length}

Il limite di durata è un tetto rigido, non un obiettivo. YuE2 decide quando finisce una canzone, e di solito finisce
da sola; il limite ferma quella che non lo fa. Parte da 360 secondi, o da ciò che dice **Durata massima di un nuovo take**
in Impostazioni. Poi fa spazio alla musica, così una canzone lunga non viene tagliata:

- A una **canzone o strumentale da un prompt** il limite viene alzato quando si scrive il piano, se il piano
  è più lungo: alla durata del piano con circa dieci secondi di margine. Non viene mai abbassato.
- Con una **registrazione** scelta, per una cover o uno strumentale, il limite segue la partitura della registrazione,
  arrotondato per eccesso allo stesso modo.

Un limite che scrivi tu resta come l'hai messo, e la pagina Partitura avvisa allora quando un piano è più lungo
di esso. Un piano molto più lungo del suo limite (più di un terzo oltre, e di più di otto minuti) non viene preso
per una canzone affatto, e viene riscritto. Ogni tanto
un render non si ferma alla fine della sua partitura e prosegue fino al limite; quel take sfuma
negli ultimi secondi invece di essere tagliato, e la sua scheda dice che ha raggiunto il limite. Più raramente ancora, un
render finisce prima che inizi l'ultima sezione della sua partitura. L'app lo renderizza allora di nuovo con un
seed nuovo prima di considerarlo finito, e se anche quello risulta corto, la scheda dice che si è fermato prima
dell'ultima sezione: **Renderizza** di nuovo per un altro tentativo.

---

## Fare una cover di una registrazione {#covering-a-recording}

1. Trascina un file audio, fino a 2 GB. Viene salvato una volta e ne viene calcolato l'hash, così lo stesso file non viene mai
   salvato due volte. Va bene anche un file video (MP4, MOV, MKV, WebM e simili): se ne conserva solo il suono, come FLAC.
2. Premi **Trascrivi**. SheetSage2 scrive la melodia e gli accordi nel riquadro della partitura. Questo viene
   messo in cache per registrazione, così fare un'altra cover della stessa canzone lo salta.
3. Correggi ciò che ha sentito male.
4. Aggiungi un testo, scegli uno stile, premi **Crea cover**.

Una cover segue la melodia e gli accordi dell'originale mentre lo stile decide tutto il resto, ed è
ciò che la rende una cover e non una copia.

### Registrare una melodia tua {#recording-a-tune-of-your-own}

> [!NOTE]
> Quanto bene viene rilevata una melodia dipende dalla registrazione, e un piano costruito attorno a essa può comunque sbagliare o
> divagare: scrivi un piano nuovo, o registra di nuovo la melodia.

In modalità **Cover**, **Registra melodia** apre il registratore. Scegli cosa stai registrando in **Ingresso**:

- **Voce:** canta o canticchia in un microfono. **Autotune** può agganciare la registrazione a una tonalità e una scala; il
  pulsante di una registrazione alterna tra la versione intonata e l'originale così senti cosa ha fatto.
- **Strumento:** suona la melodia su uno strumento, per esempio una chitarra collegata a un'interfaccia audio.
  Suonala **nota per nota**: la linea che suoni diventa la melodia che viene cantata, e gli accordi
  strimpellati non danno una melodia da cantare. Scegli l'interfaccia in **Dispositivo**, e in **Canale** il lato
  a cui è collegato il tuo strumento (l'ingresso 1 di un'interfaccia è di solito **Sinistro**). Alza **Guadagno d'ingresso**
  per uno strumento debole, tenendo il misuratore fuori dal CLIP. L'autotune non è offerto: uno strumento è già
  intonato. Yeufonic ricorda queste scelte in questo browser.

Il metronomo, il conto alla rovescia e l'ascolto in cuffia funzionano allo stesso modo per entrambi. **Usa per la cover** salva la
registrazione come registrazione, marcata **MIC** o **INST** nell'elenco. Trascrivila come qualsiasi registrazione; una
melodia registrata viene trascritta solo come melodia, perché accordi indovinati da una melodia isolata resterebbero in
ogni ritornello di una canzone fatta con essa (una registrazione trascritta prima di questo mantiene i suoi accordi finché non
viene trascritta di nuovo). Da dieci a trenta secondi di melodia sono più che sufficienti.
**Estrai il testo** non è offerto per una registrazione di strumento, perché non ci sono parole da sentire: usa
**Scrivi testo**.

**Ti senti in ritardo?** Il browser aggiunge un piccolo ritardo tra ciò che canti o suoni e ciò che
senti in cuffia. Se la tua interfaccia audio ha il monitoraggio diretto (a latenza zero), usalo
e spegni il **Monitor** del registratore, così ti senti direttamente dall'interfaccia, e una volta
sola. Usa cuffie con il filo: il Bluetooth aggiunge un ritardo suo.

#### Espandere a canzone completa {#expand-to-full-song}

Una melodia registrata dura di solito solo qualche battuta. **Sviluppa in canzone completa** fa pianificare a YuE2 un'intera canzone
con la tua melodia dentro: il piano è nella tonalità, nel metro e nel tempo della tua melodia, ogni ritornello (o ogni strofa,
se lo scegli) contiene la tua melodia, e il resto della canzone viene scritto attorno. Poi viene renderizzata
come cover della tua registrazione.

- **Cantata da:** un uomo o una donna. La tua melodia si sposta di ottave intere fin dove canta quella voce,
  perché l'ottava in cui è scritta la melodia decide chi la canta. Se lo stile non nomina alcun cantante,
  la voce gli viene aggiunta.
- **Accordi:** una melodia da sola torna spesso dal trascrittore senza accordi. Yeufonic le dà allora
  accordi a partire dalle sue stesse note, così il pianificatore ha un'armonia da seguire. Gli accordi che scrivi nella
  partitura della registrazione vengono mantenuti.
- **La tua melodia** è sempre la partitura della registrazione, anche se l'editor mostra un take fatto a partire
  da essa.
- **Struttura della canzone:** usata quando il riquadro del testo è vuoto. Con parole nel riquadro, le loro sezioni sono
  la struttura, e serve un **[Chorus]** (o un **[Verse]**) in cui mettere la tua melodia.
- **Testo:** un canticchiare si può pianificare senza testo. Una melodia suonata su uno strumento ha bisogno di un testo per
  essere cantata, quindi scrivilo prima: **Scrivi testo** lo abbozza per te.

### File MIDI e cover {#midi-files-and-covers}

> [!NOTE]
> I file MIDI servono a generare take diversi, spesso stravaganti, di melodie originali.

Oltre ai file audio registrati, puoi trascinare o caricare file MIDI standard (`.mid`, `.midi`) direttamente in modalità **Cover**.

Quando si carica un file MIDI:
- **Trascrizione automatica della partitura:** Yeufonic analizza tracce e canali per individuare la melodia vocale principale, l'accompagnamento e la progressione di accordi, li trascrive in notazione ABC e li carica direttamente nel piano roll. Lead di sintetizzatore o melodie vocali sequenziate in registri più gravi vengono trasposti automaticamente in un'ottava naturale da cantare.
- **Testo incorporato:** gli eventi di testo o di lyrics incorporati nella sequenza MIDI vengono estratti e allineati alle sillabe della melodia.
- **Dove cadono le battute:** un file MIDI non ha stanghette proprie, e alcuni iniziano con la prima parola sul movimento *prima* del battere. Yeufonic legge batteria e basso per trovare la vera stanghetta e, quando il file inizia con quell'anacrusi, mette le prime parole in una battuta breve a sé così gli accordi e i segni di battuta cadono dove cadono quelli della canzone. Un file senza uno schema chiaro di batteria e basso viene lasciato com'è.
- **Testo incollato:** le parole che incolli vengono adattate a tutta la melodia in una volta, una sillaba per nota, e le note in più restano sulla sillaba precedente. Le righe finiscono dove la melodia tace e iniziano dove inizia una frase, così una sezione più lunga o più breve dei titoli del testo non sposta più il resto. Se le parole sono più lunghe di quanto la melodia possa portare, le ultime righe vengono lasciate fuori.
- **Ascolto completo con SoundFont:** il lettore sintetizza l'arrangiamento MIDI in audio ad alta fedeltà con **FluidSynth** e SoundFont General MIDI (`.sf2`). L'uscita viene normalizzata sul picco così registrazioni MIDI multitraccia deboli suonano presenti e chiare senza distorsione.
- **Scegliere i SoundFont:** in **Impostazioni** puoi scegliere il tuo banco SoundFont `.sf2` attivo preferito (come *Arachno SoundFont 1.0* o *JNS-GM 2.0*). Altri file `.sf2` messi in `data/models/soundfonts/sf2/` vengono rilevati automaticamente.
- **Ritocchi nel piano roll:** apri il **Piano roll** per rivedere o modificare le note, scegliere quale traccia fa da melodia vocale principale, armonizzare i buchi dell'accompagnamento con **Riempi i vuoti**, o allineare un testo appena incollato con **Abbina testo**.

### Fare una cover di una canzone di un corpus {#covering-a-song-from-a-corpus}

L'analisi di un corpus ha già fatto ciò che serve a una cover: la partitura, le parole sentite nella canzone e
la voce separata. Così, sotto le tue registrazioni, l'elenco offre **Dai tuoi corpus**, raggruppato per
corpus, con la tonalità e il tempo di ogni canzone, e un filtro per uno grande. Scegli una canzone e diventa subito una
delle tue registrazioni, con la sua partitura e il suo testo, e nulla viene eseguito di nuovo. Le parole vengono messe
sotto le sezioni della partitura, come le mette **Estrai il testo**, a meno che tu non le abbia riviste nel corpus,
nel qual caso arrivano come le hai lasciate. Vanno nel riquadro del testo, sostituendo parole venute da
un'altra registrazione; le parole che hai scritto o modificato lì vengono sostituite solo se lo dici. Il riquadro Stile prende lo
stile con cui la canzone è stata imparata nel corpus, lo stesso del suo chip sotto una LoRA addestrata con esso.

Il file viene collegato invece che copiato quando il disco lo consente, quindi non occupa altro spazio, e resta
se il corpus viene eliminato. Alcune canzoni sono marcate *score: melody only* o *score: first 4 min*: la loro
trascrizione completa è fallita durante l'analisi, il che basta per l'addestramento. Premi **Trascrivi** per la
partitura completa con i suoi accordi.

**Con una LoRA.** È qui che le canzoni di un corpus servono di più: una canzone e una LoRA fatte dallo stesso
repertorio, o da repertori diversi.
1. In modalità **Cover**, apri l'elenco delle registrazioni e scegli la canzone sotto **Dai tuoi corpus**. La sua
   partitura fissa la melodia e gli accordi, e il suo testo è nel riquadro.
2. Scegli una **LoRA di stile**. La LoRA del corpus stesso fa reinterpretare al suo cantante la propria canzone, il più vicino possibile
   all'originale. La LoRA di un altro corpus la reinterpreta in quell'altro stile e con quell'altra voce.
3. Regola le intensità come per qualsiasi cover: la registrazione fissa già la melodia, quindi tieni **Suono**
   vicino a **0.50**, e alzalo per avere più voce e suono della LoRA.
4. Il riquadro Stile contiene già lo stile della canzone, e scegliere una LoRA mette davanti la sua parola
   chiave. Questo mantiene il genere e l'atmosfera della canzone; un altro chip, o i tag del filtro, la portano
   altrove. Tempo e tonalità vengono dalla partitura, qualunque cosa dica lo stile.
5. Premi **Crea cover**. **Variazioni** la renderizza poi nelle altre interpretazioni, e
   **Canta di nuovo** dà un'altra voce sulla stessa partitura, come per qualsiasi take.

### Estrarre il testo {#extracting-the-lyrics}

**Estrai il testo**, accanto a *Trascrivi*, scrive ciò che la registrazione canta: separa la
voce, la ascolta e mette le righe sotto le sezioni della partitura. Va richiesto invece di
avvenire a ogni trascrizione, perché richiede un paio di minuti mentre trascrivere una partitura
richiede secondi. La voce viene separata, e le sue parole sentite, sulla GPU quando il motore ha Demucs e Whisper, e sulla CPU
altrimenti (Impostazioni, **Usa la GPU per stem e testi**), e la barra dice in quale delle due fasi si trova. Whisper sulla GPU
e sulla CPU non scrivono sempre le stesse parole per la stessa voce, perché nessuno dei due è esatto: una voce difficile, come cori
sopra una voce principale, può differire di un quinto delle parole in un senso o nell'altro. La voce separata viene conservata, così estrarre di nuovo la stessa registrazione passa
direttamente all'ascolto, risparmiando gran parte dell'attesa.

Le parole vengono salvate con la registrazione. Premi di nuovo **Estrai il testo** e tornano direttamente nel
riquadro, e ti viene chiesto se estrarle di nuovo, cosa che vale la pena dopo aver cambiato il
metodo in Impostazioni. Scegliere un'altra registrazione prende le sue parole allo stesso modo, e una registrazione
senza parole cancella quelle della precedente. Le parole che hai scritto o modificato restano a meno che tu non accetti di sostituirle.

Aspettati una buona bozza più che una trascrizione. Misurato sul testo reale di due canzoni, Whisper
ha sbagliato **l'1,5% delle parole** in una e **il 25%** nell'altra, dove voce principale e cori si sovrappongono
nell'ultimo ritornello. Ascolta tutta la voce: prima saltava ciò che il suo rilevatore di voce
prendeva per silenzio, che nelle voci cantate era la maggior parte della canzone. Leggi la bozza e correggi ciò che
ha sentito male, soprattutto dove le voci si sovrappongono.

**Far ascoltare un LLM esterno.** Se un [LLM esterno](#external-llm) è il tuo fornitore, Impostazioni offre una scelta in
*Testo da una registrazione*. Impostala su **LLM esterno** e la voce separata viene inviata al modello per
sentirne le parole, mentre Whisper continua a calcolare quando viene cantata ogni riga. Sulle stesse due canzoni, Gemini
ha ottenuto **1,5% e 23%**, quindi sono vicini; prova entrambi su una canzone con cui Whisper fatica. Serve un
modello che accetti audio, come Gemini. Quando la risposta del modello sembra un testo, si usano le sue parole,
anche dove differiscono parecchio da quelle di Whisper: una voce sepolta in un mix è dove Whisper
soffre di più, e il modello no. Se il modello rifiuta l'audio, si trattiene (accorciando righe,
o rimandandoti a un sito di testi, come può fare un modello con una canzone che riconosce) o restituisce
quasi nulla, ottieni invece la versione di Whisper. Il messaggio alla fine dice quale
ha sentito le parole. La voce lascia il tuo computer per questo; Whisper la tiene qui.

Per una canzone di un corpus, **entrambe le versioni vengono conservate**. Quando esistono entrambe, il pannello di revisione della canzone mostra
**Parole da** con ogni versione e il suo numero di parole, quella del modello esterno in uso per impostazione predefinita. Scegli
l'altra e le sue parole vanno nel riquadro. La prima volta che si sceglie una versione le sue parole vengono abbozzate, il che
ne segna le sezioni con il modello esterno; poi ogni versione mantiene le proprie parole, modifiche e
casella **controllato**, così passare dall'una all'altra è istantaneo e non fa alcuna chiamata al modello. Nelle righe di Whisper, qualsiasi parola
ripetuta più di otto volte di fila, come un “la” tenuto che ha scritto centinaia di volte, viene ridotta
a otto.

---

## Strumentali {#instrumentals}

La terza modalità scrive un brano senza voce. Invece di un testo, prende una **struttura**:

| Struttura | Cosa riceve YuE2 | Chi decide |
|---|---|---|
| Lascia decidere a YuE2 | `[instrumental]` | YuE2 sceglie le sezioni e la loro durata |
| Sezioni | `[intro] [verse] [chorus] …` | tu scegli le sezioni, YuE2 la loro durata |
| Sezioni a tempo | `[intro 0:00-0:15] …` | tu scegli entrambe |

Aggiungi sezioni con i chip **+**, riordinale con le frecce, e dai a ciascuna una durata in modalità con tempi.
**Inviato a YuE2:** mostra esattamente cosa riceve il modello. La struttura è un orientamento: YuE2 può rinominare una
sezione, aggiungere un interludio, o superare i tempi che hai dato, quindi il limite di durata è il tetto rigido.

### Uno strumentale da una registrazione {#an-instrumental-from-a-recording}

**Da una registrazione (facoltativo)** in cima all'editor prende una delle tue registrazioni, come una cover. La sua
trascrizione è la partitura, quindi non c'è un piano da scrivere, e il render suona la sua melodia e i suoi
accordi con la LoRA strumentale.

Anche le sezioni vengono dalla partitura: una per ogni sezione della partitura, con i nomi che la LoRA conosce. Un
*interludio* diventa un ponte. Un render abbina ogni sezione della struttura a una della partitura,
per questo il costruttore cede loro il posto. Per riordinare la canzone, trascina una sezione altrove o spostala con le frecce, aggiungi una
**copia** subito dopo, o toglila con la **✕**: ogni modifica riscrive la partitura (la finestra Partitura
lo mostra), e **Ripristina le sezioni originali** la riporta indietro finché non si carica un'altra partitura.
Mentre il take suona nell'editor, la sezione in cui si trova si illumina, e un doppio clic su una sezione salta lì. I tempi vengono dalle battute e dal tempo della partitura, che il render segue da vicino all'inizio di un take e in uno renderizzato per intero. Un render che finisce ben prima della sua partitura ha suonato meno musica di quanta ne contenga la partitura, quindi l'elenco può slittare rispetto all'audio man mano che la canzone procede; una riga sotto l'elenco lo segnala e dice di quanto. Una cover mostra lo stesso elenco sotto il suo testo, e il testo viene abbinato alle sezioni in ordine, quindi
adattalo: l'elenco dice cosa gli serve dopo aver aggiunto, tolto o riordinato sezioni. Mostra anche il totale rispetto al
limite di durata, e propone di alzare il limite quando una canzone più lunga verrebbe tagliata. Premi **Crea strumentale** per renderizzare.

Anche uno strumentale scritto da una struttura ha una partitura, e una volta pianificato le sue sezioni vengono elencate allo stesso modo. Il
costruttore di struttura è la richiesta di un piano non ancora scritto, quindi cede il posto all'elenco. Riordina le sezioni e premi
**Renderizza questa partitura**: i tag di sezione del render seguono la partitura modificata. Un take che ha già audio viene renderizzato come
take nuovo accanto, qualunque cosa cambi, così l'originale mantiene il suo. **Scrivi un nuovo piano** (sotto la partitura) continua a chiedere
una melodia diversa dalla struttura con cui il take è stato scritto.

**Funziona anche una canzone cantata.** La sua partitura ha la melodia cantata nella parte vocale, che uscirebbe
cantata, quindi la melodia viene data a uno strumento: dove nessuno strumento suona, le note cantate
passano a uno, e la parte vocale resta solo con i suoi accordi. L'editor lo segnala sotto la registrazione. Per una canzone
è spesso la scelta migliore: senza la voce, il trascrittore tende a perdere la
differenza tra strofa e ritornello, e sente tutta la canzone come un solo loop di accordi. La LoRA
la arrangia come strumentale, quindi aspettati parti sue, come chitarra in più.

Scegli **Nessuna registrazione: scrivi un piano della partitura** nell'elenco per tornare a scrivere un piano.

### Quando uno strumentale canta {#when-an-instrumental-sings}

Ogni tanto il modello infila una voce in uno strumentale. È un difetto del modello, non un'impostazione
che hai sbagliato. Prima del render, se il piano mette note nella voce vocale, una finestra di dialogo offre un piano
nuovo, un seed nuovo, o di renderizzare comunque. Un take finito non viene controllato: ascoltalo.

### Uno strumentale dalla partitura di una canzone {#an-instrumental-from-a-song-s-score}

**Fai uno strumentale**, sotto la partitura di una canzone o di una cover nella pagina Partitura dell'editor (accanto a **Renderizza questa partitura**
in una canzone), fa della
stessa partitura uno strumentale, in un take nuovo: l'originale resta com'era. La melodia cantata passa
a uno strumento, al modello vengono inviati solo i tag di sezione della partitura invece del testo, viene
usata la LoRA strumentale, e lo stile perde i tag che descrivono una voce (“soft male vocal”).
È il modo per ottenere “questa melodia, senza voce”. Svuotare a mano la parte Vocal della partitura di una canzone non
basta: il render di una canzone continua a cantare le parole che riceve.

---

## Voci {#voices}

I chip **Voce** fissano il sesso e il carattere del cantante scrivendo nello stile, per tutta la canzone.

Per un duetto, o un cantante per le strofe e un altro per il ritornello, metti indicazioni di voce nel testo e spunta
**Le voci seguono le indicazioni**: vedi [Il testo](#the-words) in “Scrivere una canzone da un prompt”. Funziona anche per il testo
di una cover.

## Corpus e addestrare una LoRA {#corpora-and-training-a-lora}

Un **corpus** è una cartella di canzoni, preparata come set di addestramento per una LoRA di stile: di solito un
artista, un genere o qualche artista simile.
Apri **Corpus** dal menu. È attivo per impostazione predefinita; `TRAINING_ENABLED=0` per l'app, o un
motore costruito con `WITH_TRAINER=0`, lo toglie.

L'addestramento è la cosa più impegnativa che l'app fa: con il modello a piena qualità (BF16) consigliato,
una scheda grafica da 16 GB e 32 GB di RAM di sistema (su WSL2, `memory=32GB` in `.wslconfig`) sono il minimo pratico.
Una scheda da 8 GB può bastare per addestrare usando il modello a bassa memoria (INT8).

1. **Nuovo corpus.** Dagli un nome e una **parola chiave**, di' se la voce è maschile o femminile
   (**nessuna** per canzoni senza voce: vedi sotto), descrivi il suono che tutte le canzoni condividono, e apri la cartella che le contiene. Conferma di
   avere il diritto di addestrare su di esse, e premi **Esamina la cartella**. La cartella viene solo letta.
   **Un corpus senza voce.** Scegli **nessuna** in **Voce** quando le canzoni sono strumentali, come
   la musica dance ed elettronica. L'app allora non separa alcuna voce né ascolta parole, così nulla
   inventa testi sopra i sintetizzatori. Il testo di ogni canzone sono i tag di sezione nella sua partitura (o
   `[instrumental]` se non ne ha), la descrizione tralascia la parte vocale, e non c'è revisione del
   testo: il riquadro **Sezioni** si può modificare, e la modifica viene salvata. Il suono di ogni canzone è descritto
   dal modello locale quando è installato, perché quello esterno avrebbe solo un titolo su cui basarsi.
   Una LoRA addestrata così può scrivere note nella parte Vocal di un piano, il che fa cantare o canticchiare un render;
   l'avviso “potrebbe cantare” di un piano lo mostra. Cambiare la Voce di un corpus già analizzato cambia di conseguenza il suo
   testo.
2. **Scegli le canzoni.** Togli la spunta a quelle da lasciare fuori. Quando una canzone viene preparata, l'app salva una propria copia della registrazione completa nella memoria interna dei corpus, così un corpus resta intatto anche se la sua cartella d'origine viene svuotata o spostata più tardi. Una registrazione di più di 25 minuti viene lasciata fuori, perché con ogni probabilità è un album intero o un concerto in un solo file. Se accanto c'è un foglio `.cue`, **Dividi in tracce** la taglia nelle sue canzoni, che prendono il suo posto nel corpus. Le tracce vanno nella cartella propria dell'app; la tua non cambia. (Le canzoni più lunghe del limite GPU dell'addestratore, come tracce di 15 minuti, vengono tagliate in sicurezza e sfumate su un confine di sezione musicale all'esportazione.)
3. **Analizza.** La voce di ogni canzone viene separata, ne vengono trovati tonalità, tempo e sezioni, e il testo viene abbozzato, marcato per sezioni. Con un LLM esterno impostato, le sezioni vengono marcate dalle parole sentite: i ritornelli perché le loro parole ritornano, le sezioni nuove dalle pause. Vengono inviate solo le righe e i loro tempi, e le parole e il loro ordine non vengono mai cambiati. Senza di esso, o se la sua risposta non contiene tutte le righe, i tag vengono dall'analisi musicale. **Riabbozza**, accanto a Salva nella revisione di una canzone, rimarca le sezioni allo stesso modo senza riascoltare la canzone, per una canzone abbozzata prima, e sostituisce ciò che c'è nel riquadro. Una riga sotto i pulsanti dice cosa è in esecuzione, e l'analisi in corso compare nella scheda dei lavori e nella coda della schermata principale. **Ferma** la ferma. I passi completati vengono mantenuti, così **Analizza** riprende da dove si era fermata.

   **Rianalizzare.** Quando tutte le canzoni sono analizzate, il pulsante mostra **Analizzato ✓**. Cliccandolo chiede se vuoi rianalizzare i suggerimenti di stile di tutte le canzoni con i prompt e le impostazioni LLM più recenti (utile dopo aver rinominato un corpus o cambiato fornitore). Maiusc+clic su **Analizzato ✓** offre una nuova analisi completa da zero (separazione, tonalità, tempo, trascrizione e stili di nuovo). Ogni canzone si può anche ristilizzare con **Rianalizza** nella sua revisione.
4. **Rivedi** Apri una canzone per rivederne il testo e spuntare **controllato**, e per descriverne il suono
   dove differisce dal resto. La descrizione di stile mostra ciò che leggerà l'addestratore.
5. **Esporta il set di addestramento.** Scrive l'audio, il testo e la descrizione di ogni canzone. Una riga sotto i
   pulsanti mostra a che punto è. L'addestratore prende solo una parte di ogni canzone, che l'app calcola
   dalla memoria libera della tua scheda grafica (circa 5½ minuti su una scheda da 16 GB; la finestra Log
   dice cosa ha scelto). Una canzone più lunga viene tagliata alla fine della sua ultima sezione entro quel margine, sfumata,
   e mantiene solo le parole ancora cantate. La sua riga dice “first 3:12 trained”. Se l'addestramento
   esaurisce la memoria, imposta la variabile d'ambiente `TRAIN_MAX_MINUTES` a un numero più basso, come
   3.5: vedi il README.
6. **Addestra un LoRA.** Richiede molto tempo, e la GPU non è disponibile per l'app finché non
   termina. L'avanzamento si vede sotto i pulsanti e nella schermata principale, dove puoi fermarlo,
   e il badge del corpus in cima alla pagina pulsa mentre addestra. Riaddestrare mantiene
   la LoRA dell'esecuzione precedente con un nome datato, in **Esecuzioni precedenti**, o la elimina, come
   scegli tu.
   Addestrare con il modello a piena qualità (BF16) consigliato richiede almeno circa 12,5 GB di memoria GPU
   (con un taglio di 3½ minuti; un taglio più lungo ne richiede di più), per lo più mentre prepara le canzoni, quindi una scheda da 16 GB
   è il minimo pratico, insieme a 32 GB di RAM di sistema (ComfyUI tiene i pesi completi di YuE2
   e le cache del dataset nella memoria dell'host; su WSL2, imposta `memory=32GB` in `.wslconfig`). Una scheda da 8 GB può
   addestrare usando il modello a bassa memoria (INT8). Le schede che non possono addestrare possono comunque usare LoRA addestrate
   altrove (**Installa un LoRA**). La finestra Addestra avvisa quando è disponibile meno memoria GPU o di sistema,
   quindi chiudi prima tutto il resto che usa la GPU.

### Un'esecuzione che finisce prima del tempo {#a-run-that-ends-early}

Un'esecuzione può finire prima del suo ultimo passo: **Ferma**, un crash, o la GPU che esaurisce la memoria. La riga
sotto i pulsanti dice allora quando e perché, e dopo quale passo. Lungo la strada, l'addestratore salva un
checkpoint ogni 50 passi, e conserva una copia del migliore fino a quel momento secondo la sua perdita del pianificatore, quindi la maggior parte del
lavoro di solito c'è ancora. **Termina con ciò che ha salvato** fa ciò che fa un'esecuzione completata, a partire
da quei file: la copia migliore, o altrimenti l'ultimo checkpoint, diventa la LoRA con il
nome del corpus, con la sua parola chiave, e i checkpoint si raggruppano sotto di essa nell'elenco delle LoRA di stile. Richiede
secondi e nessun tempo di GPU. Gli ultimi passi di un'esecuzione sono quelli che cambiano meno la LoRA, quindi una finita in questo
modo è di solito vicina a un'esecuzione completa; **Checkpoint** renderizza una canzone una volta per ogni passo se vuoi
confrontare a orecchio. Per riaddestrare l'intera esecuzione, premi **Addestra un LoRA**.

### Esegui tutto {#run-all}

**Esegui tutto**, accanto ai tre, fa Analizza, Esporta e Addestra uno dopo l'altro, per un corpus per cui
preferisci non aspettare: uno grande richiede ore di analisi. Prima chiede cosa fare di una
LoRA precedente, poi prosegue con la pagina chiusa. Analizza solo ciò che ne ha ancora bisogno, e una
canzone la cui analisi fallisce viene lasciata fuori dal set di addestramento e nominata sotto i pulsanti. I testi
che nessuno ha rivisto vengono usati come sono stati abbozzati. **Ferma** lo ferma dove si trova, mantenendo ciò che è finito;
fermato durante l'esportazione, termina prima il set di addestramento. Aspetta tutto ciò che sta già usando
il motore prima di addestrare. Riavviare l'app lo ferma, e **Esegui tutto** di nuovo lo riprende.

### Quando la memoria della GPU finisce {#running-out-of-gpu-memory}

Un lavoro che esaurisce la memoria della GPU lo dice, con cosa provare: chiudi altri programmi che usano la GPU,
abbassa il limite di durata, o, per l'addestramento, lascia fuori le canzoni più lunghe. Se il motore si blocca e
si riavvia, il lavoro che stava eseguendo va perso, e anche questo viene detto.

### La LoRA addestrata {#the-trained-lora}

Quando l'addestramento finisce, la LoRA compare nell'elenco **LoRA di stile** con la sua parola chiave. Sceglierla
mostra un chip per ogni canzone da cui ha imparato, sotto il riquadro Stile, e cliccarne uno mette lo stile di quella canzone nel
riquadro.
Da una dozzina di canzoni in su, un riquadro di filtro e una riga dei tag ricorrenti nel corpus (i suoi generi,
atmosfere e strumenti) le restringono; clicca due tag per trovare canzoni con entrambi. L'elenco mostra la
prima dozzina fino a **Mostra tutto**. Vedi **Bilanciare Pianificatore e Suono** più avanti per le intensità iniziali. Per condividerla, premi **Scarica LoRA** nella pagina del corpus, o **Scarica** sotto
il selettore; vedi **Condividere una LoRA** più avanti.

Per aggiungere una LoRA che qualcuno ha condiviso, premi **Importa LoRA** accanto a **Nuovo corpus** e scegli il suo zip. Per usare una
LoRA addestrata altrove dal set esportato, premi **Installa un LoRA** e scegli il
file. Viene aggiunta all'elenco delle LoRA di stile con la parola chiave di questo corpus.

**Eliminare un corpus** toglie le copie delle sue canzoni fatte dall'app, le voci separate, i testi e
le partiture. La cartella che gli hai indicato, e qualsiasi LoRA fatta con esso, non vengono toccate.

---

## Diritto d'autore e consenso {#copyright-and-consent}

Con cosa addestri, e cosa fai del risultato, è una tua responsabilità secondo la legge del luogo in cui
vivi. L'app ti chiede di dichiararlo e non lo verifica: creare un corpus richiede che confermi
di avere il diritto di addestrare su quelle registrazioni.

Due cose da sapere:

- I pesi di YuE2 sono sotto **CC BY-NC 4.0** — uso non commerciale, qualunque cosa tu addestri a partire da essi.
- Addestrare in privato su un corpus e pubblicare la LoRA o ciò che produce sono atti diversi. Il secondo
  è quello che di solito richiede un permesso: da chi detiene i diritti sulle registrazioni, e per
  una voce riconoscibile, dal cantante.

Le LoRA che non hai addestrato tu hanno le proprie licenze: leggile sulla pagina da cui proviene ciascuna
(vedi **Dove trovare LoRA di stile** in LoRA di stile).

## LoRA di stile {#style-loras}

Una LoRA è un piccolo file che inclina il modello verso un suono. Mettine una in `models/loras/` e premi
**Ricarica** sotto il selettore, o usa **Installa**, e compare nell'elenco **LoRA di stile**.

Una LoRA di stile può avere due metà, e il selettore mostra quali ha un file:

- **Pianificatore** dà forma a ciò che viene suonato — il piano della partitura (forma, armonia, fraseggio), e poi la musica
  che il render scrive da quella partitura. Agisce in entrambi i passi.
- **Suono** dà forma all'audio — timbro e produzione.

Un'intensità che il file non può usare appare attenuata, e un file che questo motore non riesce affatto a caricare viene segnalato
come tale invece di fallire in silenzio dentro un render.

### Dove trovare LoRA di stile {#where-to-find-style-loras}

Il modo più rapido è all'installazione: spunta **LoRA di stile** nella pagina dei componenti dell'installer (o, con Docker, esegui
`sh scripts/fetch-models.sh --loras`). Questo scarica 39 LoRA di stile dai loro autori, 3,8 GB in tutto, ciascuna con una
descrizione che dà la sua parola chiave e le intensità suggerite: i set qui sotto, due di atomtanstudio (dream pop
e hip-hop old school), e sedici slider concettuali di ntc-ai, che danno forma solo alla partitura (Suono non fa nulla,
e non serve una parola chiave). Sono raccolte, senza modifiche, in
[pshields/yue2-style-loras](https://huggingface.co/pshields/yue2-style-loras), il cui README dà credito a ogni autore
e rimanda alla pagina d'origine. Una LoRA già presente nella tua cartella con lo stesso nome viene lasciata com'è.

Su Hugging Face ce ne sono altre. Questi sono i set raccolti lì, ciascuno sulla pagina del suo autore:

- [Militant reggae](https://huggingface.co/becausereasons/yue2-mltnt-militant-reggae)
- [Chanson française](https://huggingface.co/becausereasons/yue2-chnsn-chanson-francaise)
- [Canzone italiana](https://huggingface.co/becausereasons/yue2-cnzn-canzone-italiana)
- [Bulgarian voices](https://huggingface.co/becausereasons/yue2-blgr-bulgarian-voices)
- [Qawwali, sufi and tabla](https://huggingface.co/becausereasons/yue2-qwwl-qawwali-sufi-tabla)
- [J-pop](https://huggingface.co/storagejuju/yue2-jpop-t4-lora), una singola LoRA con la sola metà Suono

Per aggiungerne una, scarica il suo file `.safetensors` dalla scheda **Files** del repository, mettilo in `models/loras/`
e premi **Ricarica**, oppure premi **Installa** e scegli il file. La pagina del repository dà la
parola chiave e le intensità suggerite di ogni LoRA: scrivile in un `.txt` accanto al file (vedi **Descrizioni** più avanti) e
il selettore le mostra, e mette la parola chiave all'inizio dello Stile per te. Una LoRA presa altrove
può essere salvata in un formato che questo motore non sa caricare: il selettore la segnala come tale, e non fa alcun danno.

Ogni LoRA porta la licenza del suo autore, che questi set indicano come CC BY-NC 4.0: uso personale e non
commerciale, come i pesi stessi di YuE2. Leggi la licenza sulla pagina di una LoRA prima di usarla, o di condividere ciò che
produce.

### Bilanciare Pianificatore e Suono {#balancing-planner-and-sound}

- **Corpus coesi:** una LoRA addestrata su un solo album o su un suono acustico unitario (per esempio il folk rock degli anni Sessanta) regge intensità più alte, di solito intorno a **Pianificatore ~0.85 / Suono ~0.80**.
- **Corpus eterogenei:** se il corpus di addestramento abbraccia più generi, stili di produzione o epoche (per esempio folk acustico, rock e synth-pop), pesi alti del Suono possono causare scontri acustici. Fino a circa **Pianificatore 0.70 / Suono 0.70** l'audio resta pulito conservando il fraseggio melodico e il carattere vocale dell'artista.
- **Cover:** la tua registrazione fissa la melodia, quindi la LoRA ha meno da modellare e la metà Suono viene spinta di più. Tieni Suono vicino a **0.50**.
- **Varietà del piano:** con una LoRA addestrata da un corpus, **Tranquilla** o **Normale** danno il risultato più riconoscibile. **Tranquilla** può andare in loop con una LoRA di stile e uno stile breve, e il piano dura allora
  minuti con lunghe intro ripetute, o senza nulla di cantato. Descrivi lo stile più nel dettaglio (genere, strumenti e sensazione), o usa **Normale**. Un piano così, o uno molto più lungo di una canzone, viene riscritto una volta
  con un seed nuovo, e il take fallisce con un consiglio se anche il secondo esce uguale.
- **Trovare un buon take:** il carattere della LoRA dipende dal tiro tanto quanto dalle intensità.
  Tra circa 0.3 e 0.6, **Suono** cambia poco la voce, quindi non serve alzarlo.
  **Pianificatore** cambia l'esecuzione stessa, non solo la voce, quindi un valore che va bene per una canzone
  può essere il più debole per un'altra. Trattalo come il seed: provane alcuni (per esempio 0.6, 0.8 e 1.0) e alcuni
  seed con **Canta di nuovo**, e tieni il take che ti piace.
- **Salva intensità:** quando trovi la coppia giusta per una LoRA, premi **Salva intensità** sotto il
  selettore. Scegliere quella LoRA partirà allora da esse, e viaggiano con lei quando la condividi.

### Parole chiave {#trigger-words}

La maggior parte delle LoRA di stile viene addestrata su descrizioni che **iniziano** con una parola chiave, e fa ben poco
senza di essa. L'app se ne occupa: scegliere una LoRA mette la sua parola chiave all'inizio dello Stile,
passare a un'altra la sostituisce, scegliere Nessuna la toglie, e un render la rimette se è stata
cancellata. Vedrai la parola comparire nel riquadro Stile — puoi modificarla o spostarla.

### Descrizioni {#descriptions}

L'elenco è raggruppato per set. Clicca un titolo per aprirlo o richiuderlo; il selettore ricorda quali
hai lasciato aperti, e il gruppo con la tua scelta attuale si apre sempre con esso.

Passa il mouse su una voce per leggere cos'è, con le parole del suo autore, e le sue intensità suggerite. Quelle
descrizioni vengono da un file di testo accanto alla LoRA:

```
CHNSN Rive Gauche
Trigger: chnsn
Step 200, the decoder-loss minimum. The more supple of the two: acoustic
narrative, yé-yé, female leads, waltz meters.
```

La prima riga le dà il nome, una riga `Trigger:` diventa la parola chiave, e il resto è la
descrizione. Una LoRA tua ne ha una se scrivi un `.txt` accanto. `families.txt` nella stessa
cartella dà ai gruppi i loro titoli, un `prefix = label` per riga.

### LoRA addestrate da un corpus {#loras-trained-from-a-corpus}

Una LoRA addestrata da uno dei tuoi corpus è una normale LoRA di stile: compare in questo elenco con le
altre, con la sua parola chiave accanto, e valgono le stesse due intensità.

### Provare i checkpoint {#trying-the-checkpoints}

Un'esecuzione di addestramento salva un checkpoint ogni 50 passi, e li conserva sotto la sua LoRA nel selettore:
**▸ 9 passi** accanto al nome della LoRA li apre (Impostazioni può invece eliminarli, per risparmiare
spazio). Un checkpoint la cui LoRA è stata eliminata resta in **Checkpoint di addestramento**. Per
toglierne alcuni, premi **Modifica** sul corpus: **Checkpoint di addestramento** lì elenca quelli di ogni esecuzione, questa
e le precedenti, con le loro dimensioni. Spunta quelli da togliere e premi **Elimina**. La LoRA
finita non compare; ha il suo **Elimina LoRA**. Ognuno è la LoRA com'era in
quel punto dell'addestramento. Suonano più o meno ugualmente bene, ma ognuno pesa a modo suo
ciò che ha imparato, quindi ognuno ha un suo gusto senza perdere lo stile e il suono caratteristico su cui la LoRA
è stata addestrata.

Per sentirli fianco a fianco, scegli la LoRA, prepara l'editor come per un singolo take, e premi
**Checkpoint** accanto a **Elimina LoRA**. È attenuato per una LoRA senza checkpoint. Spunta i
passi che vuoi, imposta se vuoi un limite di durata per questi take, e premi **Renderizza**. L'azione
propria dell'editor viene eseguita una volta su ogni checkpoint, tutte con un unico seed, e ogni take prende il nome del suo passo:
*Night drive · step 250*, *Night drive · full*. Vengono salvati dentro il take aperto nell'editor,
o, per una canzone nuova, dentro l'ultimo di essi (vedi **Take dentro un take**, in La libreria). L'editor si chiude, così torni alla libreria
dove i take vengono fatti. Una canzone o uno strumentale scrive il suo piano e passa direttamente al
render.

In una canzone o uno strumentale, la LoRA scrive la melodia oltre a dare forma al suono, quindi lo stesso
seed non dà la stessa canzone: ogni checkpoint scrive la propria melodia e struttura. Il seed
sceglie tra ciò che il modello ritiene probabile, e ogni checkpoint pensa un po' diversamente fin dalla
prima nota, quindi i piani si separano in poche battute. Ciò che resta è il suono. Per confrontare solo il
suono, carica un piano con **Partitura** e premi **Renderizza questa partitura** con ogni checkpoint a turno.

I file nuovi compaiono quando il motore ha riguardato `models/loras/`, cosa che fa quando le opzioni
vengono ricaricate.

### Condividere una LoRA {#sharing-a-lora}

Scegli una LoRA e premi **Scarica** sotto il selettore: ottieni uno zip con la LoRA e la sua nota.
Per una LoRA addestrata da un corpus, la nota porta i suoi stili appresi, così i chip vanno con lei.

Per aggiungerne una che ti hanno mandato, premi **Installa** e scegli il suo zip, o un file `.safetensors`
sciolto. Va in `models/loras` sotto il titolo **Installate**, con il suo nome, la parola chiave e i suoi
chip. **Elimina LoRA** toglie la LoRA scelta, la sua nota e la sua riga di gruppo; **Ricarica** rilegge la cartella
dopo che hai aggiunto un file a mano.

---

## Stem {#stems}

Premi **Stem** su qualsiasi take. Scegli un modello, spunta le parti che vuoi — voce, batteria, basso, altro,
e chitarra e pianoforte in alcuni modelli — ed esegui.

La separazione avviene sulla **GPU** quando il motore ha Demucs, come un lavoro nella coda del motore: aspetta un
render in corso, poi va veloce, e un render in coda dietro di essa aspetta a sua volta. Un motore costruito prima di
questo, una LoRA in addestramento (che occupa la GPU), **Usa la GPU per stem e testi** su No in Impostazioni, o `STEMS_ON_GPU=0` la lascia sulla **CPU**, che è più lenta
e non ritarda mai un render. *Raffinato* esegue quattro modelli di fila per una separazione migliore e richiede circa quattro volte
il tempo.

Per una base, scegli **Voce e strumenti**. Divide la canzone in due: la voce, e
gli **strumenti**, tutto il resto come un solo stem. Togli la spunta a **voce** per tenere solo gli strumenti. È
la stessa separazione dei quattro stem, risommati, quindi richiede lo stesso tempo e suona altrettanto pulita.
La versione *raffinata* è quella che lascia meno voce dietro di sé.

Gli stem vanno in `data/stems/<title>-<id>/`, si ascoltano dai chip della scheda, e si scaricano uno per uno o in uno
zip. Restano finché non li elimini.

---

## Fermare, eliminare e ricominciare {#stopping-deleting-and-starting-again}

Su cosa sta lavorando il motore si vede nella barra in alto, accanto al nome: una pillola con il lavoro, il suo tempo, una riga
alla base che mostra a che punto è, e quanti lavori aspettano dietro. Nient'altro nella pagina cambia quando un
lavoro inizia o finisce. Cliccala per la scheda del lavoro: la fase, **ferma**, e **Prossimi**, i lavori in attesa, ciascuno con
**annulla**.

Un take in coda o in corso mostra **Annulla** sulla sua scheda, e **ferma** sulla scheda del lavoro ferma ciò su cui
il motore sta lavorando. Il titolo di un take sulla scheda del lavoro, nel suo elenco **Prossimi**, o nel lettore in
fondo alla pagina ti porta al take: al suo spazio, togliendo qualsiasi ricerca o filtro che lo nasconda. Eliminare un take ferma il suo lavoro e toglie i suoi stem. **Elimina** accanto a una
registrazione toglie il file e i suoi stem; le cover fatte da essa mantengono il loro audio e la partitura, ma non possono essere
renderizzate di nuovo.

**+ Canzone**, **+ Cover** e **+ Strumentale** nel pannello del take, o **Nuova canzone** accanto al
titolo dell'editor, ricominciano a partire dal take mostrato. Cancellano il titolo, il testo e la partitura,
e ripartono dai valori predefiniti: uno stile vuoto (con la parola chiave di una LoRA scelta), il limite di durata
abituale, Armonia Varia, varietà del piano normale, interpretazione Ampia, rifinitura della produzione attiva,
normalizzazione disattivata, e un seed nuovo non bloccato. Una LoRA scelta e una registrazione scelta restano scelte.
Il take mostrato lascia l'editor, così Renderizza non può agire su di esso per errore.

Le parole che avevi scritto ma non usato non vengono buttate: una barra propone di ripristinarle.

## La libreria {#the-library}

### Spazi {#spaces}

I take vivono negli **spazi**: uno spazio per canzone, per album, o per gli abbozzi. Il nome dello spazio sopra i take
è quello mostrato, e tutto ciò che fai va lì. Cliccalo per l'elenco degli spazi: scrivi per trovarne uno per
nome, o sceglilo con le frecce e Invio. I cinque usati più di recente vengono per primi, poi tutti gli spazi, ciascuno con
quanti take contiene. **Nuovo spazio**, **Rinomina questo spazio**, **Importa take…** e **Elimina questo spazio** sono in
fondo all'elenco. Eliminare uno spazio non elimina mai i take —
passano in Default. Le registrazioni sono condivise da tutti gli spazi, così una stessa registrazione può diventare cover in
diversi.

Il pulsante cartella di una scheda sposta quel take in un altro spazio, con i take che contiene.

### Take dentro un take {#takes-inside-a-take}

**Variazioni**, **Prova ancora** e **Checkpoint** fanno ciascuno diversi take di una canzone. Vengono salvati
**dentro** il take da cui sono nati, così lo spazio elenca le tue canzoni e non ogni render di ciascuna.
Checkpoints si preme nell'editor: con un take aperto lì, i suoi take vanno dentro quel take; per
una canzone nuova, che non ha ancora un take, il take dell'ultimo checkpoint spuntato (la LoRA finita, quando
è tra questi) contiene gli altri.

- **Il pulsante Dentro** compare tra i pulsantini in cima a una scheda quando il suo take contiene
  take, finiti o ancora in lavorazione, ed è **acceso in arancione**. Passaci sopra il mouse per leggere quanti sono
  pronti e quanti mancano. La scheda stessa è nettamente più chiara delle altre (nel
  tema chiaro, una tinta calda), così un take con take dentro spicca in un elenco. (Il pulsante del rack di mastering accanto si accende in verde allo
  stesso modo quando il take è masterizzato.)
- **Cliccalo** e si apre un pannello sotto la scheda con i take che contiene, ciascuno sulla propria scheda. Un
  take compare lì quando è finito; mentre viene fatto, si vede solo il take a cui appartiene.
  Clicca di nuovo il pulsante, o **Chiudi**, per chiuderlo.
- **Un take dentro un altro è un take come gli altri.** Ascoltalo, mettigli la stella, salvalo, separalo in
  stem, rinominalo, e fai doppio clic per aprirne la canzone e la partitura.
- **Un solo livello.** Un take dentro un altro non ne contiene, quindi la sua scheda non ha Variazioni né Prova
  ancora, e **Checkpoint** nell'editor è attenuato finché è il take aperto lì. **Tira fuori** (la freccia che esce da una scatola) lo rende un take a sé nell'elenco dello spazio, e allora può.
- **Gli strumenti dell'elenco seguono il pannello.** Mentre ce n'è uno aperto, **Seleziona tutto**, **Preferiti**, i pulsanti
  dei tipi, **Confronta**, **Elimina** e precedente e successivo del lettore agiscono sui take del
  pannello. Il take il cui pannello è aperto resta sulla pagina qualunque cosa dicano i filtri.
- **Ciò che suona dentro si vede fuori.** Se chiudi il pannello mentre suona uno dei suoi take,
  il pulsante Riproduci del take che lo contiene brilla d'oro, così vedi da dove viene il
  suono. Il verde indica ancora che è proprio quel take a suonare.
- **La ricerca li trova** come qualsiasi altro take, ovunque si trovino. Durante una ricerca, ciò che
  trova viene mostrato come schede semplici, e un take che è dentro un altro dice in quale.
- **Eliminare un take elimina i take che contiene.** L'avviso dice quanti. Estrai prima quelli che vuoi
  tenere.

I take fatti prima che esistesse questo restano dove sono, uno accanto all'altro nell'elenco.

### Schede {#cards}

Ogni scheda nomina le impostazioni che le hanno dato forma — Armonia, Interpretazione, Varietà del piano, la LoRA e
le sue intensità, il seed, il motore che l'ha renderizzata e da quanto tempo — così una scheda si legge come la ricetta che l'ha fatta.

**Salva** chiede in che formato scaricare il take, FLAC, WAV o MP3. Parte da ciò che hai salvato l'ultima
volta, e senza nulla scelto la prima volta. Un take con un'immagine si può salvare anche come **Video**: un MP4 della
canzone che mostra l'immagine della sua scheda (video H.264, audio AAC a 192 kbps). App di messaggistica come
WhatsApp lo inviano e riproducono come video, dove un file audio viaggia come documento. Con il rack di mastering attivo, il
video ha il suono masterizzato, come gli altri formati. **Take**, accanto, salva anche la ricetta del take: un piccolo file
(`<title>.yeufonic.json`) con il testo, lo stile e la partitura, i seed e le impostazioni, le LoRA per nome e
le impostazioni del rack di mastering, ma non l'audio. Con anche un formato scelto, entrambi vanno in uno zip; premi di nuovo il
formato scelto per salvare solo la ricetta. Il file non contiene nulla della tua installazione (né percorsi, né id, né chiavi),
quindi si può conservare, o condividere con un altro utente di Yeufonic.

**Importa take…**, nell'elenco degli spazi, crea da un file così un take nuovo nello spazio mostrato; trascinare il file
sulla libreria fa lo stesso. Il take contiene il piano, pronto da renderizzare, così puoi rivederlo o cambiarlo prima.
Entrambi i motori possono renderizzarlo: la stessa partitura e lo stesso seed sullo stesso motore danno un take molto simile, sull'altro
motore uno diverso. Una LoRA che nomina e che qui non è installata viene segnalata all'importazione, così puoi
installarla o sceglierne un'altra prima del render. La registrazione di una cover non è nel file, quindi una cover condivisa arriva
come una canzone con la partitura e il testo della cover, lasciando indietro le impostazioni che appartenevano alla sua registrazione (il
tempo bloccato, l'Armonia, le indicazioni di voce e il limite di durata): un piano nuovo a partire da essa inizia come una canzone da un prompt.

**Cerca take** trova i take in cui tutte le parole che scrivi compaiono da qualche parte nel titolo, nello stile, nel testo o nel
nome della LoRA, senza distinguere maiuscole e minuscole. Cerca nello spazio mostrato; **Tutti gli spazi**, accanto non appena scrivi,
cerca in tutti gli spazi, e una scheda di un altro spazio dice da quale. × o Esc la cancella. Il
riquadro parte vuoto ogni volta che si apre la pagina, e offre le tue ultime ricerche che hanno trovato qualcosa:
cliccane una, o sceglila con le frecce e Invio.

**Canzone**, **Cover** e **Strumentale** mostrano take di quei tipi: accendine uno o più, o nessuno per tutti i tipi.
**Preferiti** mostra solo i take con la stella; clicca di nuovo per mostrarli tutti. Le icone accanto stabiliscono come sono disposti
i take, quelle in uso accese in verde: schede **comode** più larghe con più del prompt o **compatte** più strette,
**larghezza piena** della finestra o una colonna centrata, e ogni take **richiuso** sulla riga del titolo. Passa il mouse su
un'icona per leggere cosa fa un clic.

Spunta dei take e la riga offre ciò che si può fare con essi, al posto dei tipi e della disposizione: quanti sono
scelti, **Confronta**, **Elimina** e **Fatto**, che toglie la spunta. **Seleziona tutto**, in fondo alla riga, spunta
ogni take mostrato. Un titolo resta sempre su una riga, terminato da … se è lungo. Passa il mouse sul titolo, sulle impostazioni o sullo stile di una scheda per leggerlo per intero.

### Un'immagine per ogni take {#a-picture-for-each-take}

Ogni take nuovo riceve un'immagine della canzone, vista tenue dietro la sua scheda, in cima al pannello del take quando lo scegli, e dietro l'editor quando il take è aperto
lì. Disegnata su questo PC, aspetta che non si stia facendo alcuna canzone, così non ritarda mai un piano o un render, e
compare poco dopo che la canzone è finita; disegnata da un LLM esterno, viene fatta mentre il take si renderizza.
Si fa in due passi: il titolo, lo stile e le prime parole del take diventano una **descrizione** di
un'immagine, poi un modello di immagini la **disegna** su bianco, e il bianco viene tolto, lasciando l'immagine
su uno sfondo trasparente. Un take fatto dentro un altro (Prova ancora, Variazioni, Checkpoints) mostra
l'immagine del take in cui si trova invece di averne una propria.

Un modello di immagini non disegna un gruppo o una persona reali, quindi la descrizione tralascia i nomi; e le
scritte nell'immagine stessa vengono tenute discrete, così non competono con quelle della scheda.

#### Due modi di disegnare: FLUX.2 klein su questo PC, o un LLM esterno {#two-ways-to-draw-flux-2-klein-on-this-pc-or-an-external-llm}

Le immagini hanno bisogno di qualcosa che sappia disegnare. Ce ne sono due, e puoi averne uno, entrambi o nessuno.

| | FLUX.2 klein, su questo PC | Il modello di immagini del tuo LLM esterno |
|---|---|---|
| Cos'è | un piccolo modello di immagini che gira nel motore, accanto a YuE2 | il modello di immagini del fornitore stesso, come quello di Gemini |
| Quanto costa | nulla; circa 8 GB di disco | ogni immagine è una richiesta al fornitore, che può essere a pagamento |
| Cosa lascia il PC | nulla: la descrizione la scrive Gemma su questo PC, o viene fatta dal take stesso | il titolo, lo stile e le prime parole del take, e la descrizione |
| Quando gira | sulla GPU quando non si sta facendo alcuna canzone: dopo la tua canzone, mai sulla sua strada | accanto ai render, mentre girano |
| Cosa imposti | un'opzione di installazione | l'LLM esterno in Impostazioni, con un fornitore che offra un modello di immagini |

**Per disegnare su questo PC, installa FLUX.2 klein.**

- **Windows:** spunta **FLUX.2 [klein]** nella pagina dei componenti dell'installer. Non è spuntato
  a meno che tu non lo scelga. Un'app installata riceve la stessa pagina all'aggiornamento, oppure esegui di nuovo l'installer
  dalla pagina della release: la casella viene ricordata dopo, e un aggiornamento non lo scarica mai due volte. Sono
  tre file, circa 8 GB in tutto.
- **Docker:** esegui `sh scripts/fetch-models.sh --pictures`, che mette i tre file in `models/`
  (`diffusion_models`, `text_encoders` e `vae`) e verifica ciascuno, poi riavvia l'app con
  `docker compose restart app` perché li trovi.

**FLUX.2 klein 9B, se hai la scheda grafica per farlo.** klein ha una taglia più grande, un modello di qualità superiore
che disegna più dettagli e mani e volti migliori, pensato solo per schede grafiche con più memoria
video. Yeufonic non lo scarica mai, perché i suoi file hanno accesso limitato su Hugging Face e sono sotto la **licenza non commerciale**
di Black Forest Labs, ma mettili al loro posto e vengono usati.

- **Disco:** circa 18 GB per la coppia abituale, il modello FP8 e il suo codificatore di testo FP8 (16 GB con il codificatore
  FP4), accanto ai file del 4B. Gli serve il VAE del 4B (`flux2-vae.safetensors`), quindi installa prima il 4B.
- **Memoria video:** gira su una scheda da 16 GB, ma la occupa quasi tutta mentre disegna, con la memoria libera
  vicina a zero. Le immagini aspettano che non si stia facendo alcuna canzone, quindi non rallenta le tue canzoni, ma altri
  programmi che usano la scheda grafica nello stesso momento possono avere problemi. Con meno memoria funziona ancora, più
  lentamente, mentre il motore carica e scarica il modello; lì il 4B è la scelta migliore.

1. **Il modello.** Accedi a Hugging Face, accetta la licenza su
   [black-forest-labs/FLUX.2-klein-9b-fp8](https://huggingface.co/black-forest-labs/FLUX.2-klein-9b-fp8)
   e scarica `flux-2-klein-9b-fp8.safetensors` (9,4 GB). Oppure prendi quello a piena precisione
   `flux-2-klein-9b.safetensors` da [black-forest-labs/FLUX.2-klein-9B](https://huggingface.co/black-forest-labs/FLUX.2-klein-9B),
   quello per Mac, grande circa il doppio e che richiede il doppio della memoria.
   Va nella cartella `diffusion_models`.
2. **Il suo codificatore di testo.** Da [Comfy-Org/Flux-2-Klein-9B](https://huggingface.co/Comfy-Org/Flux-2-Klein-9B/tree/main/split_files/text_encoders),
   che non richiede l'accesso, scarica uno di questi e mettilo nella cartella `text_encoders`:
   `qwen_3_8b_fp8mixed.safetensors` (8,7 GB, la scelta abituale su una scheda NVIDIA), `qwen_3_8b_fp4mixed.safetensors`
   (6,8 GB, il più piccolo) o `qwen_3_8b.safetensors` (16,4 GB, piena precisione, per un Mac).
   **Con il motore yue2.cpp** il server delle immagini non sa leggere quei codificatori: prendi invece `Qwen3-8B-Q4_K_M.gguf`
   (5,0 GB) da [unsloth/Qwen3-8B-GGUF](https://huggingface.co/unsloth/Qwen3-8B-GGUF)
   (funziona anche `-Q8_0.gguf`, 8,7 GB), e mettilo nella stessa cartella.
3. **Dove sono le cartelle:** sotto `models/` nella cartella di Yeufonic per **Docker**; sotto
   `engine\ComfyUI\models` nella cartella di installazione su **Windows**; sotto `engine/ComfyUI/models/` nella
   cartella di installazione su un **Mac**.
4. **Fai in modo che l'app li veda, e sceglilo.** Riavvia Yeufonic (con Docker, `docker compose restart app`),
   poi imposta **Immagini dei take: modello** in Impostazioni su *FLUX.2 klein 9B*. Il 4B disegna finché non lo fai, e
   Impostazioni lo segnala quando il 9B è scelto ma qui non può disegnare. Scegli
   *4B* per tornare indietro senza togliere nulla. La nota dell'immagine nell'editor dice quale l'ha disegnata
   (*drawn by FLUX.2 klein 9B on this PC*).

Il modello e il suo codificatore vengono trovati solo con questi nomi, quindi mantieni i nomi dei file come vengono scaricati.

**FLUX 3 klein, per le scritte e una scheda da 12 GB o più.** FLUX 3 Image Klein di Black Forest Labs disegna da una
descrizione completa della scena, che è proprio ciò che sono i prompt di immagine scritti da Gemma o dall'LLM esterno, e
scrive bene, il che si sposa con **Immagini dei take: titolo della canzone sull'immagine**. Come il 9B, Yeufonic non lo scarica mai: i suoi file hanno
accesso limitato su Hugging Face e sono sotto la **FLUX Kommunity License** (uso non commerciale, e uso commerciale di ciò che
disegna per chi sta sotto la soglia di ricavi della licenza; leggila prima di accettarla). Metti i suoi file al loro posto e
diventa selezionabile.

- **Disco:** circa 11 GB per la coppia int8, accanto ai file del 4B. Usa il VAE del 4B (`flux2-vae.safetensors`),
  quindi installa prima il 4B.
- **Memoria video:** circa 11 GB mentre disegna. Fa parecchi più passi dei FLUX.2 klein, quindi ogni
  immagine richiede più tempo.
- **Motore:** solo il motore ComfyUI, per ora; con il motore yue2.cpp non è offerto.

1. **Accedi a Hugging Face** e accetta la licenza su
   [black-forest-labs/flux-3-image-klein-comfy](https://huggingface.co/black-forest-labs/flux-3-image-klein-comfy).
2. **Il modello,** nella cartella `diffusion_models`: `flux3-image-klein-int8-convrot.safetensors` (5,8 GB, la scelta
   abituale su una scheda NVIDIA), `flux3-image-klein-nvfp4.safetensors` (5,3 GB, per una scheda RTX 50) o
   `flux3-image-klein-bf16.safetensors` (11,1 GB, piena precisione, per un Mac).
3. **Il suo codificatore di testo,** nella cartella `text_encoders`: `qwen3vl_4b_int8_convrot.safetensors` (4,9 GB) o
   `qwen3vl_4b_bf16.safetensors` (8,9 GB, per un Mac).
4. **Fai in modo che l'app li veda, e sceglilo:** riavvia Yeufonic (con Docker, `docker compose restart app`), poi imposta
   **Immagini dei take: modello** in Impostazioni su *FLUX 3 klein*. La nota dell'immagine nell'editor dice *drawn by
   FLUX 3 klein on this PC*.

Le cartelle sono le stesse del 9B, e i file vengono trovati solo con questi nomi.

**FIBO 2.0, per l’aspetto di una fotografia e una scheda da 16 GB.** FIBO 2.0 di Bria disegna il più vicino a una vera
fotografia delle copertine a cui si ispirano le immagini: dettagli più nitidi, una profondità di campo naturale, i colori
della pellicola e più di ciò che chiede la descrizione. Neanche FIBO viene mai scaricato da Yeufonic. **La sua licenza è
CC BY-NC 4.0: solo uso non commerciale.** La licenza di FLUX 3 permette a chi sta sotto il suo limite di fatturato di usare
commercialmente ciò che disegna; con FIBO, qualsiasi uso commerciale, compresa la copertina di una canzone che vendi,
richiede un accordo con Bria. Leggi la licenza prima di usarlo.

- **Disco:** circa 10,4 GB, il modello e il suo componente turbo. Legge l’encoder di testo di FLUX 3 e il VAE del 4B,
  quindi con FLUX 3 installato non serve altro.
- **Memoria video:** circa 12,5 GB mentre disegna, quindi una scheda da 16 GB. Una scheda più piccola ne sposta una parte
  altrove, il che è molto più lento.
- **Tempo:** con il componente turbo, più o meno quanto FLUX 3. Senza, FIBO disegna con le sue impostazioni, circa otto
  volte tanto.
- **La copertina:** disegnata da FIBO, la cornice attorno alla fotografia non ha la sottile linea scura, che FIBO
  disegnava come barre spesse e un riquadro attorno al titolo.
- **Motore:** solo il motore ComfyUI.

1. **Il modello,** da [Comfy-Org/Fibo-2.0](https://huggingface.co/Comfy-Org/Fibo-2.0), senza accesso, nella cartella
   `diffusion_models`: `fibo2_dev_int8_convrot.safetensors` (8,4 GB, la scelta abituale su una scheda NVIDIA) o
   `fibo2_dev_bf16.safetensors` (16,5 GB, piena precisione, per un Mac).
2. **Il suo componente turbo,** dalla stessa pagina, nella cartella `loras`:
   `fibo_2.0_turbo_lora_avg_rank_270_bf16.safetensors` (2 GB). Non è un LoRA di stile e non viene proposto come tale.
3. **Il suo encoder di testo,** se FLUX 3 non è installato: `qwen3vl_4b_int8_convrot.safetensors` (4,9 GB) o
   `qwen3vl_4b_bf16.safetensors` (8,9 GB, per un Mac), dalla stessa pagina, nella cartella `text_encoders`.
4. **Lascia che l’app li veda, e sceglilo:** riavvia Yeufonic (con Docker, `docker compose restart app`), poi imposta
   **Immagini dei take: modello** nelle Impostazioni su *FIBO 2.0*. La nota dell’immagine nell’editor dice *drawn by
   FIBO 2.0 on this PC*.

**Per disegnare con un LLM esterno,** apri Impostazioni e imposta **LLM per scrivere testi e tag di stile** sull'[LLM esterno](#external-llm),
con il suo **URL dell'API**, la sua **chiave API** e il suo **modello**, come per i testi. Il fornitore deve avere un modello
di immagini: Gemini ce l'ha (si usa `gemini-3.1-flash-image` a meno che tu non ne nomini un altro), e a un fornitore compatibile con OpenAI
si chiede `gpt-image-1`. L'app chiede al fornitore il suo elenco di modelli, in background,
all'avvio, quando queste impostazioni cambiano e ogni poche ore, e disegna lì solo quando l'elenco
ha il modello di immagini.

Senza nessuno dei due, **Immagini dei take** in Impostazioni dice **Nessuna immagine: lo sfondo predefinito**, con una riga su come
averle, e la scelta di farle non è selezionabile.
Imposta l'uno o l'altro e si attivano: da lì in poi vengono fatte immagini per i take che crei.

#### Gestire le immagini in Impostazioni {#managing-pictures-in-settings}

| Impostazione | Cosa fa |
|---|---|
| **Immagini dei take** | *Fanne una per ogni take nuovo* (predefinito quando qualcosa può disegnare), o *Solo su richiesta*, dove un take mantiene lo sfondo predefinito finché non ne fai una dal suo quadrato o dal pulsante Immagine dell'editor. Le impostazioni qui sotto danno forma a un'immagine fatta in entrambi i modi. È *Nessuna immagine* finché nulla qui può disegnare. |
| **Immagini dei take: disegnate da** | *Questo PC se klein è installato, altrimenti l'LLM esterno* (predefinito), *Questo PC (il modello qui sotto)* o *Il modello di immagini dell'LLM esterno*. Quale klein disegna su questo PC (FLUX.2 klein 4B o 9B, o FLUX 3 klein) si sceglie in **modello**. Anche FIBO 2.0 si sceglie lì. |
| **Immagini dei take: modello** | *FLUX.2 klein 4B* (predefinito), *FLUX.2 klein 9B*, *FLUX 3 klein*, o *9B dove i suoi file sono installati, altrimenti 4B*. Solo per immagini disegnate su questo PC. Il 9B e FLUX 3 non vengono mai installati per te: vedi [FLUX.2 klein 9B e FLUX 3 klein](#two-ways-to-draw-flux-2-klein-on-this-pc-or-an-external-llm) più sopra. Se quello chiesto non c'è, ne disegna un altro, e Impostazioni dice quale. Anche *FIBO 2.0* si aggiunge a mano ed è solo per uso non commerciale: vedi sopra. |
| **Immagini dei take: descritte da** | chi scrive il prompt di immagine, dal titolo del take, dallo stile artistico qui sotto, dal suo stile e dal suo testo (fino a 50 righe). *Gemma locale se installato, altrimenti il take stesso* (predefinito), chiunque disegni. *Gemma locale*: scritto su questo PC; richiede l'opzione Bozze dei testi. *Dal take stesso*: nessun LLM; una descrizione fatta con il titolo, lo stile e le prime parole del take, la più rapida, e non viene inviato nulla. Oppure l'*LLM esterno*, una richiesta per immagine; quando non è disponibile, o passi agli LLM locali per la sessione, Gemma le scrive al suo posto se è installato. |
| **Immagini dei take: stile artistico** | come deve apparire l'immagine, dato all'LLM che scrive il prompt di immagine (attenuato quando il take si descrive da sé). Per impostazione predefinita un design astratto e surreale nello stile delle copertine degli anni Settanta e Ottanta, senza testo né persone. Svuotato, torna a quello. |
| **Immagini dei take: il tuo prompt** | parole con cui inizia il prompt di ogni immagine, come *salt marsh, overcast*, fino a 512 caratteri; il prompt scritto dall'LLM viene dopo. Vuoto (predefinito): nessuna. Solo quando un LLM scrive il prompt di immagine (attenuato quando il take si descrive da sé). |
| **Immagini dei take: titolo della canzone sull'immagine** | *No* (predefinito) o *Sì*: il titolo della canzone viene scritto in grassetto sulla copertina, in maiuscole o minuscole, come l'hai scritto, anche quando è il nome di un artista (l'immagine stessa viene comunque descritta senza di esso). Quasi sempre l'immagine è incorniciata da una sottile linea scura dentro un bordo bianco spezzato, come in molte copertine degli anni Settanta, con il titolo centrato in una fascia più larga in alto o in basso. Circa una su cinque non ha bordo: il titolo sta sull'immagine, in un angolo o centrato in alto o in basso, in un colore smorzato preso dall'immagine, e all'LLM si chiede di lasciargli libera quella parte dell'immagine. Tutto ciò viene scelto a caso per ogni immagine. FLUX.2 klein può scriverlo con qualche refuso. Solo quando un LLM scrive il prompt di immagine. |
| **Immagini dei take: modello di immagini** | quale dei modelli del fornitore disegna. Solo per immagini disegnate dall'LLM esterno (sceglilo in **Disegnato da**; altrimenti attenuato), e vuoto per quello abituale del fornitore, che è quasi sempre quello che vuoi. |

Quindi con FLUX.2 klein installato e le impostazioni come vengono, le immagini si fanno interamente su questo PC, anche
quando l'LLM esterno scrive i tuoi testi: Gemma scrive ogni prompt di immagine dove sono installate le Bozze dei testi, e
senza di esso la descrizione viene fatta dal take stesso, senza LLM, il che non richiede tempo. Scegli *Il modello di immagini
dell'LLM esterno* perché le disegni il fornitore, o imposta **descritto da** su *Dal take stesso* per le
immagini più rapide, o su *LLM esterno* (una richiesta per immagine).

#### L'immagine di un take nell'editor {#a-take-s-picture-in-the-editor}

L'icona **Immagine** nella riga in alto della finestra dell'editor, accanto agli altri pulsanti del take, mostra l'immagine
con due scelte: **Fai una nuova immagine**, che la rifà in background, e **Usa lo sfondo predefinito**, che la toglie per sempre: per quel take non si fa più alcuna immagine a meno che tu non ne chieda una.
Clicca l'immagine per vederla intera, grande quanto la finestra consente; un clic ovunque o Esc
la toglie e lascia l'editor com'era. L'immagine intera ha le stesse due scelte sotto. Scegli
lì **Fai una nuova immagine** e l'immagine resta in vista mentre si fa quella nuova, con ciò che sta succedendo mostrato
tra i pulsanti, poi passa a quella nuova quando è pronta.

Sulla scheda di un take, il quadrato in alto a sinistra mostra l'immagine quando ci passi sopra il mouse. Un take senza
immagine offre lì invece **Fai una nuova immagine**, dove questo PC può fare immagini.

### Confrontare i take {#comparing-takes}

Spunta da due a sei take e premi **Confronta** (compare accanto a Seleziona tutto quando ne sono spuntati due, e
aspetta i take ancora in render). I take si impilano in una finestra su una posizione condivisa: premi da **1** a
**6** o cliccane uno per passare, e prosegui dallo stesso momento della canzone, in riproduzione o
in pausa. **Spazio** riproduce e mette in pausa, le frecce si spostano di 5 secondi, e la stella segna quello
che preferisci. **Uniforma il volume** abbassa i take più forti al livello del più debole, perché un take più forte tende
a sembrare migliore; **Nascondi i nomi** mescola i take e li chiama Take A, B, C per un ascolto alla cieca.

### Il lettore {#the-player}

Clicca o trascina sulla forma d'onda per spostarti. Precedente e successivo scorrono le schede nell'ordine mostrato.

| Tasto | Cosa fa |
|---|---|
| Spazio | riproduci o pausa |
| Sinistra, Destra | indietro o avanti di cinque secondi |
| Maiusc+Sinistra, Maiusc+Destra | il take precedente o successivo; nella vista Playlist, la canzone precedente o successiva della playlist |
| Su, Giù | volume |

Funzionano anche i tasti multimediali del sistema. I tasti propri del take sono in [Scorciatoie da tastiera](#hot-keys).

### Il visualizzatore audio e il testo sincronizzato {#the-audio-visualizer-and-synced-lyrics}

Premi **Visualizzatore** nella barra di trasporto (o **V** mentre suona una traccia) per aprire il palco del visualizzatore a schermo intero.

Il palco mostra visualizzazioni audio in tempo reale sincronizzate con la riproduzione:

- **Modalità del visualizzatore:** scegli tra dieci visualizzatori nella barra in alto:
  - *Yeufonic:* il logo stesso, che respira — la piastrella brilla con i bassi e si espande con il battito, ogni braccio del diapason è un misuratore con la sua metà dello spettro, e il punto verde si accende con il battito.
  - *Nastro d'onda:* due nastri armonici fluttuanti che reagiscono al suono.
  - *Aurora boreale:* tende ondeggianti di aurora eterea che reagiscono a medi e acuti.
  - *Nebulosa cosmica:* un campo stellare e una nebulosa di particelle interstellari che ruota e pulsa a ritmo.
  - *Caleidoscopio:* simmetrie geometriche radiali che pulsano con il tempo.
  - *Griglia al neon:* un piano wireframe synthwave retrofuturista in prospettiva che ondeggia con le linee di basso.
  - *Distorsione liquida:* una superficie fluida deformata da onde armoniche.
  - *Sciame di particelle:* ammassi di particelle gravitazionali che si disperdono sui colpi di percussione.
  - *Barre di spettro hi-fi:* un analizzatore di spettro multibanda con picchi fluttuanti che ricadono.
  - *Copertina:* l'immagine del take, grande, con il suo titolo sotto, su una copia sfocata di sé che si muove con la musica. Un take senza immagine mostra la scena Yeufonic finché non ne viene fatta una.
- **Dietro le scene:** le scene Copertina, Yeufonic, Mandala, Griglia, Liquido e Barre suonano sopra l'immagine del take, che si muove dolcemente con la musica, quando il take ne ha una. Sopra può muoversi anche qualcosa, nei colori dell'immagine: *Respiro* (solo l'immagine), *Raggi di luce* che ruotano dal centro, *Increspature* lanciate dal battito, *Colore alla deriva*, *Profondità* (altre copie dell'immagine che ruotano l'una contro l'altra) o un *Alone spettrale*. Ogni scena parte dal suo (colore alla deriva dietro Copertina, l'alone dietro Mandala, i raggi dietro Griglia, le increspature dietro Liquido, solo l'immagine dietro Yeufonic e Barre); premi **B** per scorrerli, e la scena ricorda la tua scelta.
- **La forma d'onda:** sotto le scene Yeufonic e Copertina, la forma d'onda del take mostra quanto della canzone ha suonato; cliccala per saltare lì.
- **Copertina e dinamica del vinile:** mostra la copertina del take in stile Hipgnosis in una busta 3D interattiva che si inclina e ruota con il puntatore. Un disco in vinile realistico gira a 33⅓ giri e scivola fuori dalla busta sui colpi di basso, con un bagliore olografico e anelli d'onda d'urto che reagiscono al ritmo. Cambia modalità con il pulsante **Copertina**: *Busta*, *Aura* (sfondo sfocato) o *Spento*.
- **Un'immagine nuova:** il pulsante immagine in alto a destra, in ogni scena, fa un'immagine nuova per il take in riproduzione, dove questo PC può fare immagini. Pulsa mentre l'immagine viene fatta, e quella nuova subentra quando è pronta.
- **Testo sullo schermo:** premi **L** o clicca **Testo** per mostrare o nascondere il pannello del testo indipendente e scorrevole. Trascinalo per la barra in alto per spostarlo; resta dove lo metti, e un doppio clic sulla barra lo rimette a posto.
- **Nastro del mini-lettore:** mentre il visualizzatore completo è chiuso, un mini-visualizzatore reattivo a doppia onda suona dentro la barra di trasporto in basso. Si attiva o disattiva in **Impostazioni → Aspetto**.

### Playlist e preferiti {#playlists-liked-songs}

Clicca **Playlist** nella barra in alto per passare alla vista Playlist.

- **Disposizione a due colonne:** la colonna di sinistra elenca le tue playlist insieme alla playlist di sistema fissata **Mi piace**, con il numero totale di canzoni. La colonna principale mostra l'intestazione della playlist attiva (copertina ad alta risoluzione, titolo, descrizione, totale delle canzoni e durata) e la tabella delle tracce.
- **Sincronizzazione automatica dei preferiti:** qualsiasi take con la stella nella libreria, in qualsiasi spazio, compare automaticamente nella playlist dei preferiti. Togliere la stella lo toglie da essa.
- **Aggiungere a una playlist:** premi **P** o clicca l'icona **Playlist** su qualsiasi scheda per aprire il selettore delle playlist, spuntare o togliere l'appartenenza alle playlist, o crearne una nuova. **Esc** chiude il selettore.
- **Ordinamento e ricerca interattivi:** clicca un'intestazione di colonna (**Titolo**, **Durata** o **Aggiunto**) per ordinare con indicatore di direzione e invertire l'ordine con un clic, e filtra le tracce con il riquadro di ricerca.
- **Andare allo spazio nella libreria:** clicca il titolo di una canzone nella tabella delle tracce per passare subito alla vista Libreria, aprire lo spazio dove vive quel take e evidenziarne la scheda.
- **Scorciatoie nelle playlist:** le scorciatoie proprie dei take vengono ignorate nella vista Playlist per evitare modifiche involontarie, tranne **M** (rack di mastering), che agisce sulla traccia in riproduzione o caricata, oltre ai normali controlli di trasporto (**Spazio**, frecce, **?** e **L**).
- **Riproduzione continua e casuale:** clicca **Riproduci** nell'intestazione della playlist per ascoltare dalla traccia 1, o **Casuale** per un ordine casuale. La riproduzione passa automaticamente alla traccia successiva della playlist quando finisce ogni canzone.

### Scorciatoie da tastiera {#hot-keys}

Nella pagina principale, i singoli tasti agiscono sul **take scelto**: quello del pannello di sinistra. Clicca la sua scheda per
sceglierlo. Ogni tasto fa ciò che fa il suo pulsante, quindi un tasto che eliminerebbe chiede prima, e un take
che non può fare ciò che un tasto chiede (Variazioni su un take senza partitura, per esempio) lascia una riga nella barra
di stato che dice perché.

| Tasto | Cosa fa |
|---|---|
| Spazio | riproduci o pausa |
| Sinistra, Destra | indietro o avanti di cinque secondi |
| Maiusc+Sinistra, Maiusc+Destra | il take precedente o successivo; nella vista Playlist, la canzone precedente o successiva della playlist |
| Su, Giù | volume |
| M | apri il rack di mastering del take; di nuovo per chiuderlo |
| E | apri il take nell'editor |
| I | i dettagli del take: tutto ciò con cui è stato fatto, a parole, con **Copia** |
| N | normalizza il take, o annulla se è normalizzato |
| V | apri o chiudi il visualizzatore durante la riproduzione, o Variazioni da fermo |
| T | Prova ancora |
| S | metti o togli la stella al take |
| P | aggiungi il take a una playlist |
| D | elimina il take, dopo aver chiesto, come il suo cestino |
| L | i log; oppure mostra il testo con il visualizzatore aperto |
| B | nel visualizzatore, ciò che si muove dietro una scena sopra l'immagine del take |
| F | schermo intero |
| ? | mostra o nascondi le scorciatoie; di nuovo per chiudere |
| Escape | chiudi la finestra in primo piano: il visualizzatore, i log, il rack di mastering sopra l'editor, poi l'editor o qualsiasi altra finestra |

I tasti con lettere non fanno nulla mentre scrivi in un riquadro, mentre c'è una finestra aperta davanti, o con Ctrl,
Alt o il tasto Windows o Comando premuto, così le scorciatoie del browser (Ctrl+L, Ctrl+S e le altre)
continuano a funzionare. Il suggerimento di un pulsante nomina il suo tasto, come in **Variazioni (V)**. Premi **?** in qualsiasi momento per vedere l'elenco delle scorciatoie.

Nella finestra dell'editor, Spazio e le frecce comandano il lettore della finestra, per il take aperto lì, ogni volta che il suo lettore
è visibile: in ogni passo, e con il rack di mastering aperto sopra. Non agiscono mai mentre scrivi in un riquadro,
e i tasti con lettere sono solo della pagina principale. Il piano roll ha i suoi tasti: vedi [Il piano roll](#the-piano-roll).

---

## Impostazioni {#settings}

Premi **Yeufonic** in alto a sinistra. Le impostazioni vengono salvate sul server, così ti seguono in qualsiasi
browser e sopravvivono a una ricostruzione: il formato audio di uscita per gli stem e per salvare un take, il
modello di separazione, dove vengono scritti gli stem, se si conservano i checkpoint di addestramento, e come si
verifica che gli strumentali non cantino.

### Archiviazione {#storage}

**Impostazioni → Spazio su disco** mostra dove va lo spazio su disco di Yeufonic e ti permette di recuperarne una parte. Addestrare un
corpus lascia molti file che non servono più: copie fatte per il motore mentre le canzoni venivano analizzate,
il set di addestramento (ogni canzone riscritta come FLAC senza perdita, più grande dell'originale), e i checkpoint
salvati lungo la strada. La finestra elenca ciascuno con la sua dimensione, **cos'è** e **cosa costa
toglierlo**, e toglie solo ciò che spunti, dopo un'ultima conferma. **Spunta quelle che non costano nulla** spunta
le copie che vengono semplicemente rifatte quando servono.

Le canzoni analizzate d'ora in poi conservano la voce separata come FLAC, lo stesso audio in circa metà dello spazio. La
finestra può **convertire le voci WAV che hai già**: ognuna viene convertita, verificata per decodificarsi esattamente nello stesso
audio, e solo allora il WAV viene tolto. Gira in background e si può fermare.

I checkpoint di addestramento meritano una seconda occhiata prima di andarsene: ognuno è una voce dell'elenco delle LoRA di stile che
puoi scegliere per take nuovi, quindi togliere i checkpoint di un corpus toglie quelle voci dall'elenco per sempre. La sua
LoRA finita resta e continua a funzionare. Il set di addestramento di un corpus è diverso: toglierlo lascia la LoRA e i suoi
checkpoint nell'elenco, e ne ha bisogno solo un nuovo addestramento di quel corpus.

I tuoi take, le canzoni, le LoRA finite e i modelli non compaiono mai tra le cose da togliere. Tutto ciò che appartiene a un corpus che viene
addestrato, esportato o analizzato appare attenuato e non si può toccare finché non ha finito.

Sotto, **Riordina automaticamente** sceglie cosa Yeufonic toglie per te: le copie di lavoro di ogni canzone
quando la sua analisi finisce (attivo per impostazione predefinita), il set di addestramento quando una LoRA è stata addestrata (disattivo per impostazione predefinita; il corpus
ha poi bisogno di un altro **Esporta** prima di poter riaddestrare), e i checkpoint di addestramento (conservati per impostazione predefinita).

Le immagini e la cache di build di Docker stanno fuori da Yeufonic e non sono coperte qui; `docker system df` le mostra.

### Il modello YuE2 {#the-yue2-model}

YuE2 esiste in due taglie, e un'installazione ne ha una: **piena qualità**, che consigliamo, o **bassa
memoria**, una copia più piccola per schede grafiche con poca memoria video. **Informazioni**, nello stesso menu,
dice quale hai. Si sceglie quando installi Yeufonic, non qui:

- **Su Windows**, esegui di nuovo l'installer. La sua pagina dei componenti offre le due taglie e spunta quelle
  già scaricate. Cambiare scarica l'altro la prima volta e li tiene entrambi, quindi tornare indietro
  non scarica nulla.
- **Con Docker**, `sh scripts/fetch-models.sh` scarica la piena qualità e
  `sh scripts/fetch-models.sh --int8` quello a bassa memoria. Con entrambi i file in `models/checkpoints`,
  l'app usa la piena qualità a meno che `YUE2_CHECKPOINT=int8` non sia in `.env`.

Prova quello a bassa memoria se i render sono molto lenti o il motore esaurisce la memoria GPU. Addestrare una LoRA funziona
con entrambe le taglie del modello. L'impostazione **Addestramento con il modello a bassa memoria (int8)** sceglie quale: disattivata, l'addestramento usa
il modello a piena qualità; attivata, usa il modello con cui l'app renderizza. Parte attivata quando è installato solo il modello a bassa
memoria. Il README su GitHub ha una sezione, *Choosing a model size*, con cosa aspettarsi da ciascuno.

Yeufonic può anche usare il motore **yue2.cpp** al posto di ComfyUI, per schede grafiche con meno memoria,
scelto all'installazione: nella pagina dei componenti dell'installer di Windows, o con Docker tramite
`sh scripts/fetch-models.sh --cpp`. **Informazioni** dice quale motore è in esecuzione, e la scheda di un take quale motore l'ha renderizzato. Fa canzoni, cover e
strumentali e trascrive registrazioni, con le tue LoRA di stile; Gemma può abbozzare testi e descrivere immagini
accanto a esso (con Docker, `--gemma`), e FLUX.2 klein disegnarle (`--pictures`). L'addestramento richiede il motore
ComfyUI: con yue2.cpp corpus e addestramento non sono offerti. La pagina
[Choosing an engine](https://github.com/yeufonic/yeufonic/blob/main/docs/ENGINES.md) su GitHub ha
l'elenco completo, e come cambiare.

**Cerca una nuova versione** è l'unica cosa qui che usa internet di sua iniziativa: ogni
quattro ore l'app chiede a yeufonic.com se è uscita una versione successiva, e lo segnala con una pillola accanto alla
versione in alto a destra. Quella pillola ti dà l'installer, o, per una copia Docker, i due comandi
che la aggiornano. È una richiesta e nient'altro lascia il computer; **Non controllare** la
disattiva. **Cerca aggiornamenti** nel menu chiede subito, che questo sia attivo o no, e risponde nel
menu: quale versione hai, e se è l'ultima.

Quando ce n'è una più recente, il menu offre **Ottieni x.y.z**, che scarica l'installer su un'installazione Windows o mette i due comandi negli appunti per una copia Docker.

**Tema** stabilisce l'aspetto dell'app: **Scuro**, **Chiaro**, **Come il computer (scuro o chiaro)**, che segue il chiaro o scuro del tuo
sistema e cambia con esso, **Studio**, uno scuro caldo con l'ambra, o **Alto contrasto**, bianco e nero
con contorni netti. Cambia all'istante, e ogni browser lo ricorda
così la pagina si apre in quel modo. La finestra dei log resta scura in tutti i temi, come un terminale. Anche il rack di mastering segue il tema: nel tema chiaro i suoi pannelli sono in argento spazzolato, mentre manopole,
finestre dei misuratori e display mantengono l'aspetto scuro dell'hardware.

**Colore dello sfondo**, sotto Tema, colora la pagina dietro i take con un colore a tua scelta: spunta **Tinta**, poi
sposta **Tonalità di colore** lungo la ruota dei colori e **Intensità** da un velo leggero a un colore pieno. La pagina cambia mentre
trascini, e la scelta viene salvata quando rilasci. Le schede dei take, i pannelli e le finestre mantengono i propri
colori, e il tema ad alto contrasto resta nero.

### LLM esterno {#external-llm}

Yeufonic può scrivere bozze di testi, trascrivere registrazioni, marcare le sezioni delle canzoni e analizzare gli stili dei corpus con un LLM esterno invece del modello Gemma locale.

Usare un LLM esterno ha due vantaggi chiari:
- **Risparmia memoria GPU:** evita di caricare il modello Gemma 4 nella VRAM della GPU (risparmiando circa 8 GB di memoria video), lasciando la tua scheda grafica completamente libera per la pianificazione e il render audio di YuE2.
- **Bozze e analisi più ricche:** i grandi modelli nel cloud spesso abbozzano testi più sfumati e producono tag di stile dettagliati per i tuoi corpus.

**Fornitore consigliato:** consigliamo di scegliere un fornitore di LLM esterno la cui API non preveda fatturazione, se ne hai uno a disposizione — **Google Gemini** è un buon esempio. L'API di Gemini (tramite Google AI Studio) offre un generoso livello gratuito senza fatturazione, supporta gli endpoint standard compatibili con OpenAI (`https://generativelanguage.googleapis.com/v1beta/openai/`) e accetta direttamente l'audio per trascrivere le registrazioni.

Se usi un'API a consumo o a pagamento per token (come i livelli a pagamento di OpenAI o Anthropic), analizzare un intero corpus con decine di canzoni o generare descrizioni per molti take può consumare in fretta crediti API o far scattare limiti di spesa. Se un'API esterna restituisce un errore di quota o di limite di frequenza (HTTP 429), Yeufonic mostra un avviso e ti permette di passare ai modelli locali per il resto della sessione, così gli altri lavori proseguono senza interruzioni. Un fornitore senza fatturazione evita costi imprevisti.

**Configurarlo:**
1. Apri **Yeufonic → Impostazioni → LLM esterno e testi**.
2. Imposta **LLM per scrivere testi e tag di stile** su **LLM esterno (API compatibile con OpenAI)**.
3. Inserisci l'**URL dell'API**, la **chiave API** e il **modello** del tuo fornitore (per esempio, il modello `gemini-2.5-flash` o `gemini-1.5-flash` con l'URL di base compatibile con OpenAI di Google Gemini `https://generativelanguage.googleapis.com/v1beta/openai/`).
4. Clicca **Prova la connessione all'LLM** per verificare le tue credenziali.
5. Se il modello scelto accetta l'audio in ingresso (come Gemini), puoi anche impostare **Testo da una registrazione** su **LLM esterno** perché ascolti le voci separate.

---

## Usare Yeufonic da un agente di IA (MCP) {#using-yeufonic-from-an-ai-agent-mcp}

Yeufonic può fare da **server MCP**. Questo permette a un agente di IA sullo stesso computer, come Claude Code o Cursor, di usarlo per te:
chiedere una canzone, una cover o uno strumentale, aspettarlo, riprodurlo, provarlo in un altro modo, dargli un'immagine, metterlo in una playlist e
riordinare la libreria, tutto con parole tue (“fai uno strumentale EDM di un minuto nello spazio EDM e riproducilo”). L'agente fa ciò che fa la pagina, per le stesse vie, quindi un take che avvia è un
normale take della tua libreria.

### Configurarlo {#setting-it-up}

1. **Attivalo.** Apri Impostazioni e imposta **Server MCP** su **Acceso**. È disattivato per impostazione predefinita, perché una richiesta può avviare lavoro sulla GPU.
2. **Collega il tuo agente** all'indirizzo dell'app con `/mcp` in fondo: l'indirizzo in cui apri Yeufonic, per esempio
   `http://localhost:8090/mcp`. In Claude Code:

   ```
   claude mcp add --transport http yeufonic http://localhost:8090/mcp
   ```

   Altri client prendono lo stesso indirizzo come server HTTP. Quelli che leggono un file di configurazione vogliono di solito qualcosa come
   `{"mcpServers": {"yeufonic": {"url": "http://localhost:8090/mcp"}}}`. Non servono accesso né chiave.
3. **Chiedi.** Avvia il tuo agente da qualsiasi cartella e descrivi ciò che vuoi.

**Quale indirizzo?** È l'indirizzo in cui apri Yeufonic, con `/mcp` in fondo.
- **Docker:** `http://localhost:8090/mcp`.
- **L'installazione Windows:** la porta dell'app è in `settings.ini` (`app_port`, 8090 a meno che tu non l'abbia cambiata, per esempio per girare accanto a
  una copia Docker). Con `app_port = 8091` è `http://localhost:8091/mcp`.
- **Agente in WSL, app su Windows:** così non si collega. L'app Windows ascolta solo sull'indirizzo di loopback di Windows, che WSL non può
  raggiungere (Docker dentro WSL va bene, perché è anch'esso in WSL). Esegui l'agente da Windows (PowerShell o la versione Windows del
  tuo agente), o attiva la rete in mirroring di WSL (`networkingMode=mirrored` sotto `[wsl2]` in `.wslconfig`, poi `wsl --shutdown`),
  che rende `localhost` uguale da entrambe le parti.

Se il tuo agente dice che il server **richiede l'autenticazione**, quasi sempre è perché l'impostazione è ancora disattivata: attivala, poi
ricollega l'agente (in Claude Code, `/mcp`). Ricollegalo anche dopo aver riavviato Yeufonic, perché un riavvio interrompe la connessione.

### Cosa puoi chiedere {#what-you-can-ask-for}

| Chiedi | Cosa succede |
|---|---|
| “Elenca i miei ultimi take”, “mostra i take nello spazio EDM” | Elenca i take, i più recenti prima, con un id breve, quando è stato fatto ciascuno, la durata e lo stile |
| “Fai uno strumentale di un minuto in stile synthwave” | Pianifica e renderizza uno strumentale. Si possono nominare una durata, uno spazio e una [LoRA di stile](#style-loras) |
| “Fai una canzone in stile folk con questo testo” | Lo stesso per una canzone, dal testo che dai |
| “…con armonia avventurosa, interpretazione controllata, in fa diesis, a 100 BPM” | Qualsiasi impostazione di un take nuovo con i nomi usati dalla pagina: [Armonia](#harmony), [Varietà del piano](#plan-variety), l'[interpretazione](#interpretation), blocco di tonalità e tempo, e per una canzone **Segui esattamente questa struttura** e **Le voci seguono le indicazioni**. Se non si dice nulla, un take nuovo parte da dove parte quello della pagina: Varia e Ampia |
| “Scrivi un testo su un treno notturno, in tono parlato” | Il **Scrivi testo** dell'app stessa, con le sue forme di canzone, righe per sezione e toni. L'agente può anche scrivere il testo da sé |
| “Fai una cover di *la registrazione* in stile jazz” | Fa una cover da una registrazione già nella tua libreria. Serve una partitura (trascrivila prima nell'app). Senza un testo tuo, usa le parole sentite nella registrazione |
| “Riproducilo” | Apre il take nel tuo browser, dove suona |
| “Metti la stella a quello”, “chiamalo Sunrise”, “spostalo nello spazio Folk” | Mette la stella, rinomina o sposta un take |
| “Renderizzalo di nuovo con un seed nuovo”, “ferma quello” | Renderizza di nuovo un take, o ne annulla uno in corso |
| “Dammene qualcun altro così” | Renderizza di nuovo il take con seed nuovi, come diversi take nuovi da ascoltare insieme |
| “Cantalo di nuovo”, “provalo in ogni interpretazione” | **Canta di nuovo** (una voce nuova per la stessa partitura) o **Variazioni** (la stessa partitura e lo stesso seed, suonati in ogni modo). Le variazioni vengono salvate dentro il take, come Prova ancora |
| “Canta quella melodia con questo testo” | **Nuovo testo**: la stessa melodia, tonalità e tempo con un altro testo, come take nuovo |
| “Fanne uno strumentale” | La stessa partitura con la melodia su uno strumento e senza canto, come take nuovo |
| “Scrivigli un piano nuovo, più vivace” | Un piano nuovo per un take che non ha ancora audio (pianificato senza render, o il cui piano è fallito). Un take con audio non viene toccato: chiedi invece un take nuovo |
| “Tira fuori quello libero” | **Tira fuori**: un take salvato dentro un altro diventa un take a sé |
| “Dagli un'immagine” | Fa un'immagine nuova per il take, come il pulsante **Immagine** dell'editor, e dà un link che la apre. Un'immagine disegnata su questo computer aspetta che non si stia facendo alcuna canzone |
| “Metti i tre migliori in una playlist chiamata Road trip” | Crea playlist, mostra cosa contengono, e aggiunge o toglie take. Mettere un take in **Mi piace** gli mette la stella |
| “Trovami uno stile synthwave”, “salva quello stile come Night drive” | Cerca tra i tuoi stili salvati e quelli integrati, e salva uno stile con un nome per il menu degli stili |
| “Crea uno spazio chiamato Drafts” | Crea uno spazio nuovo in cui tenere take |
| “Trascrivi *la registrazione*” | Trascrive una registrazione in partitura, così se ne può fare una cover. Lascia stare una registrazione che ha già una partitura a meno che non venga chiesto |
| “Separa quello in voce e strumenti” | Separa un take finito nelle sue parti (quattro, sei, o solo voce e strumenti) e ti dà un link a ogni file e uno all'intero set in uno zip |
| “Salva la ricetta di quel take”, “…e il take insieme, come zip MP3” | Dà la ricetta del take (ciò che l’ha fatto, non il suo audio) da mostrare, modificare o tenere come file, con link per scaricarla da sola o con l’audio in un unico zip |
| “Importa *Night Ferry.yeufonic.json* in Drafts e fanne il render” | Un nuovo take da un file di take, con il piano, renderizzato quando lo chiedi. Dice quali LoRA nominati nel file non sono installati, e quando una cover è arrivata come canzone |
| “Importalo di nuovo in stile dream pop, stessa partitura e seed” | Modifica la ricetta prima di importarla, così cambia solo ciò che nomini |
| “Quale motore ha fatto quel take?”, “quale motore è in uso?” | Dice quale motore ha renderizzato un take, e quale usa ora Yeufonic (ComfyUI o yue2.cpp) |
| “Yeufonic è occupato?” | Dice se il motore è pronto, cosa sta girando e con quale avanzamento, cosa aspetta, e se si sta addestrando una LoRA |
| “Elimina quel take” | Mostra cosa se ne andrebbe e ti chiede prima; vedi sotto |

Fare un take richiede minuti. L'agente lo avvia e aspetta, riportando l'avanzamento, così intanto puoi chiedere la cosa successiva.

### Come può andare: un esempio {#how-it-can-work-an-example}

Una conversazione, da un'idea a una playlist. Tu parli; l'agente sceglie gli strumenti (la colonna centrale è lì solo per mostrare cosa
succede) e ti dice cosa è tornato.

| Tu dici | L'agente | Cosa ottieni |
|---|---|---|
| “Scrivi un testo sull'ultima notte di un guardiano del faro, stile folk, forma narrativa. Poi fanne una canzone in un nuovo spazio chiamato Coast.” | `write_lyrics`, `create_space`, `make_song`, poi `wait_for_take` finché non è finito | Il testo, intitolato *The Last Light*, che ti viene mostrato; uno spazio chiamato Coast; una canzone pianificata e renderizzata lì, con l'avanzamento strada facendo |
| “Riproducila.” | `get_take`, poi apre il suo `listen_url` | Suona nel tuo browser |
| “Bella melodia. Provala più libera e irrequieta, e dammene una senza canto.” | `make_variations` con libera e irrequieta, `instrumental_from_take` | Due take dentro la canzone, e uno strumentale accanto |
| “Fammi vedere cosa abbiamo.” | `list_takes` in Coast, e con `inside` per la canzone | Un elenco con un id breve per ciascuno, così puoi dire “3f9a” invece di un titolo |
| “Tira fuori 3f9a, mettigli la stella e dagli un'immagine.” | `take_out`, `star_take`, `make_picture` | Quello libero come take a sé, con la stella (quindi anche nei preferiti), con un link alla sua immagine |
| “Metti quello e lo strumentale in una playlist chiamata Coast demos.” | `create_playlist`, `add_to_playlist` | Una playlist con i due |
| “Salva lo stile come Coastal folk.” | `save_style` | **Coastal folk** nel menu degli stili dell'app, pronto per la prossima volta |
| “Ora un duetto: questo testo, con indicazioni [male voice] e [female voice], ogni sezione come è scritta.” | `make_song` con `follow_structure` (un piano nuovo, perché le sezioni cambiano) | Una canzone nuova che pianifica esattamente le tue sezioni, in ordine, con ogni riga indicata spostata dove canta quella voce |

Tutto ciò che ha fatto è nella libreria come se l'avessi fatto sulla pagina: apri qualsiasi take nell'editor, masterizzalo, o prosegui da lì.
Quando un passo non si può fare, l'agente riceve il motivo dall'app stessa (“this take is an instrumental already”, “nothing here can draw a
picture”) e lo riferisce, così senti la stessa risposta che darebbe la pagina.

### Tutto ciò che può fare {#everything-it-can-do}

Non ti servono questi nomi: chiedi con parole tue e l'agente sceglie. Sono qui perché tu veda cosa esiste, e possa
dire al tuo agente quale vuoi.

| Strumento | Cosa fa |
|---|---|
| `list_takes` | Elenca i take, i più recenti prima, facoltativamente solo quelli che corrispondono ad alcune parole, in uno spazio nominato, o con la stella. Mostra un id breve |
| `get_take` | Un take completo: come è stato fatto, il suo stato, eventuali errori e, quando ha audio, un link che lo riproduce. Può includere la partitura |
| `wait_for_take` | Aspetta (fino a circa un minuto alla volta) un take in lavorazione, e dice se è finito |
| `make_instrumental` | Pianifica e renderizza uno strumentale da uno stile, con una durata, uno spazio e una LoRA di stile se li nomini, e sezioni se le dai |
| `make_song` | Lo stesso per una canzone, da un testo |
| `make_cover` | Una cover da una registrazione della libreria, con la sua partitura e, a meno che tu non ne dia altre, le sue parole |
| `try_more` | Diversi take in più da uno esistente, con seed nuovi |
| `sing_again` | La stessa partitura cantata di nuovo con un seed nuovo: una voce nuova, come take nuovo |
| `make_variations` | La stessa partitura e lo stesso seed in ogni interpretazione nominata (o in tutte), salvati dentro il take |
| `new_words` | La stessa partitura cantata con un altro testo, come take nuovo |
| `instrumental_from_take` | La stessa partitura come strumentale, come take nuovo |
| `replan_take` | Un piano nuovo per un take senza audio, facoltativamente con un'altra Armonia, Varietà del piano, tonalità o tempo |
| `take_out` | Trasforma un take salvato dentro un altro in un take a sé |
| `write_lyrics` | Un testo da una richiesta, con una forma e un tono di canzone, scritto come lo fa Scrivi il testo sulla pagina |
| `render_take` | Renderizza un take pianificato, o renderizza di nuovo uno finito (con un seed nuovo se richiesto) |
| `cancel_take` | Ferma un take in coda o in corso |
| `make_stems`, `get_stems` | Separa un take in parti, poi elenca le parti con un link a ciascuna e all'intero set in uno zip |
| `list_recordings`, `transcribe_recording` | Mostra le registrazioni della libreria e se ciascuna ha una partitura; trascrive quella che non ce l'ha |
| `list_style_loras` | Le LoRA di stile installate, con le loro parole chiave e le intensità salvate con esse |
| `list_spaces`, `move_take`, `create_space` | Gli spazi e cosa contiene ciascuno; sposta un take in un altro; crea uno spazio nuovo |
| `list_playlists`, `create_playlist`, `add_to_playlist`, `remove_from_playlist` | Le playlist e i take di una; ne crea una; mette o toglie take |
| `make_picture` | Un'immagine nuova per un take, con un link che la apre. Anche `get_take` dà il link all'immagine di un take |
| `list_styles`, `save_style` | I tuoi stili salvati e quelli integrati, cercati per parole; salva uno stile con un nome |
| `star_take`, `rename_take` | Mette o toglie la stella a un take; ne cambia il titolo |
| `delete_take` | Elimina un take per sempre, dopo avertelo mostrato e ricevuto il tuo via libera |
| `save_take_recipe` | La ricetta di un take, con link per scaricarla da sola o con l’audio in un unico zip, nel formato chiesto |
| `import_take` | Un nuovo take da una ricetta, in uno spazio se nominato, pronto per il render; dice quali LoRA non sono installati e quando una cover è arrivata come canzone |
| `status` | Se il motore è pronto, cosa gira e cosa aspetta, e se si sta addestrando una LoRA; nomina il motore in uso (ComfyUI o yue2.cpp) |

### Idee d'uso {#ideas-for-using-it}

- **Un lotto di idee, poi scegliere.** “Fai cinque strumentali EDM di un minuto in stili diversi, nello spazio EDM.” Li avvia uno dopo
  l'altro e ti avvisa man mano che ciascuno finisce. Ascolti, poi dici “metti la stella al secondo e al quarto ed elimina il resto”.
- **Iterare su un'idea.** “Fai uno strumentale in uno stile di synth sognante e riproducilo”, poi “ora lo stesso con più batteria”, e
  “dammene altri quattro come il secondo”. L'agente tiene traccia di quale take è quale, così puoi parlarne per posizione o
  per ciò che ne hai detto.
- **Cover senza cliccare in giro.** “Trascrivi *il demo*, poi fanne tre cover: folk, synthwave e jazz.” Trascrive
  prima la registrazione se non ha una partitura, poi fa le cover nello spazio che nomini.
- **Lavorare con una LoRA.** “Elenca le mie LoRA di stile, poi fai uno strumentale con quella jazz.” La parola chiave e le intensità salvate
  sono gestite per te, cosa facile da sbagliare a mano.
- **Testo dell'agente, o dell'app.** L'agente può scrivere il testo da sé: “Scrivi un testo su un treno notturno e fanne una canzone
  in stile folk.” Yeufonic vede solo il testo finito. Oppure chiedi quello dell'app: “usa l'autore di testi di Yeufonic, forma hip-hop,
  tono parlato”, che lo scrive come fa **Scrivi testo** sulla pagina e lo restituisce per una canzone.
- **Stessa melodia, altro testo.** “Cantalo di nuovo con questo testo per la seconda strofa”: `new_words` mantiene la melodia, la tonalità e il tempo,
  dove una canzone nuova dal testo scriverebbe una melodia nuova.
- **Confrontare impostazioni.** “Fai la stessa canzone due volte, una con armonia Familiare e una con Avventurosa, con lo stesso seed”, poi
  “ora dai alla migliore ogni interpretazione”. Le impostazioni si chiedono per nome, così puoi impostare un piccolo test in una frase.
- **Playlist dall'ascolto.** “Metti tutti i take con la stella di questa settimana in una playlist chiamata Week 43”, o “togli gli strumentali da
  Road trip”. I preferiti sono i take con la stella, quindi la stella e i preferiti sono sempre lo stesso elenco.
- **Stem per un intero lotto.** “Separa i miei cinque take più recenti in voce e strumenti e dammi i link.” Vanno in coda uno dietro
  l'altro, e dietro qualsiasi render che la GPU stia eseguendo.
- **Ordine nella libreria.** “Trova i take con lo stesso titolo, dimmi qual è il più recente, ed elimina quelli più vecchi”, o “sposta tutto
  ciò che ho fatto oggi in uno spazio chiamato Drafts”. Lavora per id e chiede prima di eliminare.
- **Controllare prima di un lavoro lungo.** “Yeufonic è occupato?” prima di mettere in coda un render lungo o un lotto, per non restare dietro un addestramento.
- **Parte di un compito più grande.** Poiché è uno strumento che l'agente può chiamare, può far parte di qualcosa di più grande: fare una traccia per un video e
  scrivere la nota che la accompagna, o costruire un lotto grande quanto una playlist e nominare i take da un elenco.

L'agente non può sentire un take, quindi non può giudicare come suona: tu ascolti, e lui fa il lavoro pesante. Non è nemmeno una
scorciatoia per aggirare il motore: la GPU fa comunque un lavoro alla volta, quindi un lotto grande è una coda lunga.
- **Condividere un take.** “Salva il mio take con la stella con la sua ricetta come zip FLAC” dà un file che un altro può ascoltare e rifare:
  chiede al suo agente di “importare questo file di take e farne il render”. Oppure “importalo di nuovo con il LoRA jazz, stessa partitura
  e seed”, per sentire lo stesso piano in un altro modo.

### Da sapere {#things-to-know}

- **I take possono avere lo stesso titolo,** quindi l'agente lavora con l'**id** di un take e ne mostra uno breve (la colonna `short_id`) quando elenca i take.
  Puoi nominare un take con l'inizio del suo id, quattro caratteri o più, purché un solo take inizi così. Se sono due, te lo dice
  e chiede di più.
- **Eliminare chiede due volte.** L'agente ti mostra prima cosa eliminerebbe, compreso ogni altro take con lo stesso titolo, ed elimina solo
  quando dici di sì. Un take con la stella richiede che tu lo dica esplicitamente. Un take eliminato, con il suo audio, non si può recuperare.
- **Spazi e LoRA di stile si nominano,** non si numerano: “nello spazio EDM”, “con la LoRA jazz”. Un nome che non corrisponde a nulla riceve l'elenco
  di ciò che c'è, e non viene creato nulla. La parola chiave di una LoRA viene aggiunta allo stile per te, perché una LoRA fa ben poco senza.
- **Un take nuovo parte da dove parte quello della pagina:** Armonia su Varia e interpretazione Ampia, a meno che tu non ne nomini altre. Su un motore
  senza il nodo dell'armonia parte da Familiare, perché lì l'Armonia non può salire oltre.
- **Immagini e testi aspettano il loro turno.** Un'immagine disegnata o descritta su questo computer aspetta che non si stia facendo alcuna canzone, e i testi
  scritti su questo computer si mettono in coda con il resto del lavoro GPU, così l'agente può dire “è ancora in lavorazione” e ricontrollare più tardi.
- **Uno strumentale viene sempre pianificato con una struttura con tempi,** calcolata dalla durata che chiedi (circa due minuti e mezzo
  se non dici nulla). Senza tempi, il pianificatore scrive piani troppo lunghi per essere usati. Nomina le tue sezioni e vengono usate così come sono.
- **Solo su questo computer.** Valgono gli stessi controlli di nome host e di origine della pagina, e non c'è accesso, quindi disattiva l'impostazione
  quando non la usi, e non esporre la porta a una rete di cui non ti fidi.

## Log di sistema {#system-logs}

L'app scrive un log consolidato in tempo reale di ogni azione importante — pianificazione della partitura, render, trascrizione audio, separazione degli stem e addestramento delle LoRA — con i prefissi `INFO`, `WARN` ed `ERROR`.

- **Console nel browser:** clicca il pulsante **Log** nella barra in alto (o premi **L**) per aprire una console flottante, che si può trascinare e ridimensionare. Resta aperta senza bloccare la pagina, così puoi mettere in coda take e seguire la generazione in tempo reale.
- **Finestra separata:** clicca **↗ Stacca** nell'intestazione della console (o vai direttamente a `/logs`) per aprire una finestra dedicata ai log.
- **Nel terminale:** i log ruotano automaticamente in `data/logs/yeufonic.log` sull'host, dove puoi seguirli in diretta:
  ```bash
  tail -f data/logs/yeufonic.log
  ```

## La pagina del motore {#the-engine-s-own-page}

Il motore è ComfyUI (a meno che questa installazione non usi yue2.cpp, la cui pagina è un semplice banco di prova), e la sua interfaccia è raggiungibile: <http://localhost:8189> con Docker, o
<http://localhost:8188> con l'installazione Windows (l'`engine_port` in `settings.ini`). Risponde solo
su questa macchina, senza accesso.

- **È lo stesso motore e la stessa GPU dell'app.** Un lavoro eseguito lì compare nella coda dell'app come proveniente
  dall'esterno, e i lavori dell'app lo aspettano.
- **La sua cronologia mostra ogni grafo che l'app ha inviato**: il piano, il render e le trascrizioni, con
  ogni impostazione così come l'ha ricevuta il motore. È un buon posto per vedere esattamente da cosa è stato fatto un
  take.

---

## Quando qualcosa non va {#when-something-is-wrong}

**L'intestazione dice che il motore manca.** L'app funziona senza e lo dice. I render aspettano.
Controlla che il container del motore sia in esecuzione.

**Una canzone non finisce.** Di solito troppa intensità del pianificatore. Abbassa il Pianificatore della LoRA a 0.5. Il
limite di durata la fermerà comunque.

**Una LoRA sembra non fare nulla.** Controlla che la parola chiave sia nello Stile, e che l'intensità che
hai alzato sia una che il file ha davvero — il selettore attenua l'altra.

**Un take dice *Render debole*.** È uscito molto più basso del normale dall'inizio alla fine. Alcuni take
così sono solo bassi; altri suonano sottili o distorti. Clicca l'avviso per normalizzarlo, il che
lo porta al volume abituale e lo marca *Normalizzato*. Se suona ancora male, prova un altro
seed, e tieni il Suono di quella LoRA a 0.5 o meno. Succede soprattutto con le cover attraverso una LoRA di stile
addestrata qui.

**Normalizza il volume.** Spuntalo nell'editor e ogni take fatto mentre è spuntato viene portato al
volume abituale quando finisce, e marcato *Normalizzato*. Un take fatto senza si può normalizzare
dopo con il pulsante dell'altoparlante in cima alla sua scheda. Il file così come è stato renderizzato viene conservato accanto, e
cliccare *Normalizzato* torna a esso. Quanto forte diventa si imposta in Impostazioni, in *Normalizza a*.
Senza spunta, un take mantiene il livello con cui è stato renderizzato.

**Uno strumentale ha cantato.** Vedi *Quando uno strumentale canta* più sopra. È un difetto del modello; un seed nuovo
di solito lo risolve.

**Un take non si renderizza di nuovo.** Forse la sua registrazione è stata eliminata. Le cover mantengono il loro audio e la
partitura, ma non si possono renderizzare di nuovo da una registrazione che non esiste più.

**Non suona nulla, ma la forma d'onda si muove.** Controlla il controllo del volume e che non sia selezionato uno stem —
il lettore segue l'ultima cosa cliccata.
