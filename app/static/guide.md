# Yeufonic — the guide

This is about **using** the app. Installing it, and everything you need before it runs, is in the
[README](https://github.com/yeufonic/yeufonic#readme).

The app writes songs with YuE2, a model that works in two steps: first it writes a **score plan** —
the melody, the chords and the sections, as text — and then it **renders** that plan into audio.
Almost everything here follows from that split. A plan costs seconds and can be read, edited and
thrown away; a render costs minutes. So the app lets you look at the plan first.

---

## Your first song

1. Press **+ Song** at the top of the left panel. The editor window opens.
2. **Type a style.** A sentence, not a tag list: *"warm indie rock, expressive female lead, jangly
   guitars, 96 BPM"*. This is the single biggest influence on what comes out.
3. **Add lyrics**, or press **Write lyrics** and let Gemma draft them from a description.
4. Press **Write score plan**. Nothing is rendered yet: the window turns to its **Score** page.
5. **Read the plan** when it lands. If the melody is wrong, **Write a new plan** rerolls it for the
   cost of a few seconds.
6. Press **Render this score**. The window closes. A take with no audio yet is filled in; one that already has
   audio is rendered as a new take beside it, so a render never overwrites one you may want to keep.

Tick *render as soon as the plan is ready* to run both steps without stopping in between.

The take appears in the library on the right, and plays in the bar at the bottom.

### The take panel and the editor

The **left panel** shows the take you last clicked, read-only: its style, its sound settings, the
first lines of its words, and its score as a key, a tempo, a length and each section's chords.
**+ Song**, **+ Cover** and **+ Instrumental** at the top start something new; the one for the
take's own kind stands out. The chevron beside the panel folds it away, so the takes have the width,
and brings it back.

Making and changing a take happens in the **editor window**. Its main button on the panel says what
fits: *Edit and render again*, or *Review the plan and render* when a plan is waiting. A card's
**Score** and **Again** buttons open it too, and so does double-clicking a card. It has three
columns (the song, the words and the sound) with the score on a tab of its own. **Settings → Editor
layout** offers steps instead, one part at a time, with a summary of what will be sent at the end.

Closing the window, with **Close**, the cross or Escape, keeps what you typed.

### Advanced settings

The **Advanced** button in the editor's header opens settings for this one take. Most songs never
need them. They are saved with the take, so *Edit and render again* finds them as you left them.
The button lights up when any setting differs from its default, and **Reset to defaults** puts
them all back.

Some of these act on the plan, and some on the render and the finished file:

- **Diffusion steps** (16–64, default 32): how many steps the audio decoder takes. More steps take
  longer to render.
- **Avoid:** words to steer away from, such as "drums" or "rap vocals". They are added to the style
  as "avoid: …". It is a hint to the planner, not a guarantee: the renderer has no negative prompt.
- **Key lock:** the plan is moved to this key once the planner has written it. The planner ignores
  a key named in the style, so this is done to the score itself: every note and chord shifts by the
  same interval and the key signature is rewritten. A minor plan stays minor, and only the tonic
  moves. A plan the app cannot read with certainty, such as one in a modal key or with a key change
  part way, is left in the planner's key and the log says so.
- **Tempo lock** (BPM): the plan is set to this tempo, replacing any tempo in the style or in the
  planner's own score, and the render follows it.
- **Score token cap** (default 8192): the most the planner may write. A lower cap stops a short
  song's plan running on.
- **Chord hold limit** (bars, default 8): the most bars the planner stays on one chord root before
  it must change.
- **Outside harmony bonus** (0–10, default 0): how strongly the planner is pushed toward borrowed
  chords and roots outside the home key. These two act on the planner's choices, so they show as a
  difference in the chords of the plan rather than as a clear difference by ear. Compare the Score
  window.
- **Follow this structure exactly** (a tick under the lyrics box, not in Advanced; songs; off by default): the plan writes exactly the sections the lyrics name, in
  order, and no others. Left off, the planner shapes the song itself and often adds an intro, an outro or an
  interlude, or leaves a section out. A plan can still end before the list does; Details shows what was asked for and
  what the plan wrote.
- **Sections open differently** (Follow Harmony, Always, Never): whether a section may open on the same
  chords as the one before it. *Follow Harmony* turns it on from Colourful up and leaves it off below; *Always* and
  *Never* decide for this take at any step, so two plans can be compared with and without it.
- **Target loudness:** the level a take is normalised to. It applies only when normalising is on.
- **Outro fade** (seconds, default 3): the length of the fade when a take is cut off at the length
  cap.

### What to put in the Style box

YuE2 reads this as a description of a recording, so describe a recording. Language, genre, voice,
instruments, mood, tempo and production, roughly in that order, all in one sentence. Bare tag lists
work less well, and section markers such as `[Verse]` belong in the lyrics, not here.

The **Vocal** chips below write into the style for you: female, male or duet, and a character such
as breathy or raspy. They are a shortcut for typing, and you can edit the result by hand.

### Drafting the lyrics

**The structure.** Above the lyrics box, while it holds no words, a song has a **structure** to build, as an
instrumental has: a list of sections you can reorder, remove and add to (intro, verse, pre-chorus, chorus, bridge,
interlude, outro). **Start from** fills it with a common shape, and each shape's tooltip says what it suits. An
**interlude** is an instrumental passage: the writer puts its tag on a line of its own, and the planner plays it with
the instrument voice. **Put sections in the lyrics box** drops the tags in as empty sections to write under by hand.
Once the box has words, the lyrics are what is sung and the structure steps aside.

**Write lyrics**, beside the lyrics box, asks what the song is about and writes words for the sections you built.
**Lines in a verse or chorus** sets how long each is: more lines in a section make a longer song, because the
planner writes about as much music as there are words. The Style above sets the mood. Gemma writes the draft on the same
engine, and it lands in the box with a title if you had not given one. The window closes as soon as the draft starts, and the progress shows beside the lyrics box.
The lyrics editor's buttons add any of these sections too.

It is a first draft. The lines scan and rhyme, but a model reaches for familiar images, and nothing
checks whether a line is already someone else's. Read it and make it yours before you plan.

---

## Reading and fixing the plan

The plan is written in **ABC notation**: music as plain text, letters instead of dots on a stave.
Chris Walshaw devised it in the early 1990s for sending folk tunes by email, and it stuck.

You do not need to read it. The app renders the same plan as a **chord chart** and as real **staff
notation** below the editor, and **Expand** opens all of it full size. But the text is what YuE2
wrote and what it renders from, so it is worth being able to find your way around.

### Reading a plan

A plan begins with a header, one letter and a colon per line:

```
X:1
M:4/4
L:1/32
Q:1/4=120
V: Vocal clef=treble name="Vocal Melody"
V: Ins   clef=treble name="Ins Melody"
K:D#m
```

| Line | Means |
|---|---|
| `X:1` | the tune's number. Every ABC file starts with one |
| `M:4/4` | the metre — four beats in a bar |
| `L:1/32` | the unit length: a bare letter lasts a thirty-second note |
| `Q:1/4=120` | the tempo — a quarter note at 120 beats per minute |
| `V:` | declares a voice. YuE2 writes two, a vocal and an instrumental line |
| `K:D#m` | the key, D sharp minor. `K:` always comes last in the header |

Then the music itself:

```
% intro
V: Vocal
z24z4"D#m"z4|"D#m"z32|
V: Ins
Z|d16a16-|a16g8a8|
```

- **Notes are letters.** `d16` is a D lasting 16 units. Lowercase sits an octave above uppercase,
  and `'` or `,` shift it further.
- **`-` ties** a note into the next one, so they sound as one.
- **`z` is a rest**, with a length like a note. A capital `Z` rests for a whole bar.
- **Chords live in double quotes**, like `"D#m"`, and sit in front of the note they start on. These
  are what **find and replace** edits.
- **`|` is a bar line**, and **`%` starts a comment** — which is how the sections are marked:
  `% intro`, `% verse`, `% chorus`.

So that fragment says: D sharp minor, four four, 120 beats per minute, and through the intro the
vocal rests while carrying the chord, while the instrument plays a tied D and A, then G and A.

Two practical consequences. **Editing chords is safe** even if the notes look opaque — they are only
the parts in quotes, and everything else can be left alone. And **if you edit the plan, the render
uses what you edited**, so repairing one is usually faster than rerolling until a good one appears.

### Hearing it

The **Notation** tab has a player above the staves. Press **Play** to hear the plan as the box has
it, edits and all, so a melody you are unsure of can be judged by ear before a render is spent on
it. The notes it is playing are picked out as it goes, and its tempo control changes the preview
only, not the score. Playing it stops whatever the player bar had, since two things at once is no
use to anyone, and closing the window — or moving to Chart or Lyrics — stops it too, so nothing is
left playing with no control in reach.

**Instruments** plays each voice with an instrument the Style names, rather than a piano
throughout: a style that says *electric guitar, drums* is heard with a guitar, its chords played by
another, and a bass under them; a sung line is stood in for by a voice, and an instrumental's
melody is not. A style that names drums gets a drum part too, written against the score's own
metre — a backbeat for rock, four to the floor for dance, a ride for jazz, something sparser for a
ballad — and it plays all the way through, since the score has no sections for it to sit out. The
line beside the player says what it chose, and unticking it goes back to the piano you would
otherwise hear. This is a reading of the style, not of the render: YuE2 decides the
real performance and adds parts the score never had, so treat it as the plan played in the right
colours rather than as what the take will sound like.

**Download MIDI** saves the score for a DAW. Each part is a track of its own, on its own channel,
with the instrument the preview used set on that channel: the vocal line, the instrument line and,
unless you untick **Chords**, the chord symbols as a chord part with its bass beside it (the only
place the harmony is written as notes), and drums on channel 10 when the style asks for them. The
instruments are General MIDI program numbers, so your DAW plays them with its own sounds, and the
tempo and metre are in the file. A plan that changes its metre part way is written in the metre it
starts in — only that one is recorded — while the notes keep their own lengths. Clicking a note in
the staves puts the cursor on the ABC that wrote it.

A score with a note above what these instruments can play, or below it, is played shifted by whole
octaves until it fits, and the line beside the player says how far; the staves, the MIDI file and
the score itself are unchanged. The instruments are not all the same size — a bass stops well below
a piano — which is why the line is there when a score is shifted. A score with no notes in it yet
has nothing to play and says so.

The player needs its note samples, which are not part of the app: each instrument is about 7 MB,
fetched from its upstream home the first time a preview plays with it and kept in the library, so
it works offline afterwards. **Play** fetches whatever the current score needs and then starts, and
**Get the sounds** fetches the same without playing, for anyone who would rather have it ready
first.

### The Piano Roll

Click **Piano Roll** in the score window to open the visual MIDI editor. Rather than editing raw ABC letters, you can see and shape the melody directly on an interactive pitch and time grid.

The editor displays both score voices simultaneously — **Vocal** (the lead singing melody in sky blue) and **Ins** (the instrumental accompaniment in warm amber). Both voices are always fully active, visible, selectable, and editable. The **Draw** buttons at the top left choose which voice new notes will be assigned to when you click to add notes.

#### Editing notes

- **Add a note:** Click any empty cell on the grid to create a note at that pitch and time. The note auditions immediately so you can hear its tone.
- **Select notes:** Click a note to select it. Hold <kbd>Shift</kbd> or <kbd>Ctrl</kbd>/<kbd>Cmd</kbd> while clicking to select multiple notes across both vocal and instrumental parts. Click and drag a **marquee selection box** over empty grid space to select any phrase or passage across all voices. Press <kbd>Ctrl</kbd>+<kbd>A</kbd> (<kbd>Cmd</kbd>+<kbd>A</kbd> on macOS) or click **Select All** to select all notes across the entire score. To select all notes from the playhead cursor to the end of the song, press <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>A</kbd> or <kbd>Alt</kbd>+<kbd>A</kbd> (or click **From Cursor ▶** in the toolbar).
- **Move notes:** Drag any selected note to shift its timing earlier or later, or drag vertically to transpose its pitch. When multiple notes are selected — whether vocal, instrumental, or a combination of both — they all move together in lockstep, preserving their relative timing, melodies, and lyrics.
- **Resize and duration:** Drag the right-hand edge of a note to lengthen or shorten its duration. The **Snap** selector (1/16, 1/8, or 1/4 note) constrains movement and resizing to clean musical divisions.
- **Delete notes:** Double-click any note to delete it, or select one or more notes and press <kbd>Delete</kbd> or <kbd>Backspace</kbd>.
- **Undo and redo:** Every note edit, move, resize, addition, and deletion is recorded in the history stack. Press <kbd>Ctrl</kbd>+<kbd>Z</kbd> (<kbd>Cmd</kbd>+<kbd>Z</kbd>) to undo, and <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>Z</kbd> or <kbd>Ctrl</kbd>+<kbd>Y</kbd> to redo.
- **Audition keys:** Click any key on the left-hand piano keyboard to hear its pitch.
- **Maximize:** Click **Maximize** in the top toolbar to expand the piano roll to the full width of your browser window.

#### Timeline, sections, and chords

Along the top ruler, the timeline displays measure numbers and section boundaries:
- **Rename sections:** Click any section marker badge (`intro`, `verse`, `chorus`, etc.) to edit its name or reassign it.
- **Edit chords:** Directly below the bar ruler, the chord track displays the song's harmonic progression. Click an existing chord badge to rename it (for example, change `C` to `Am7` or `G/B`), or click an empty bar slot to place a new chord.
- **Harmonize empty bars (Fill Gaps):** Click **Fill Gaps** in the toolbar to populate empty bars in the instrumental accompaniment track with musical notes generated from the chord progression.
- **Remove empty bars (Compact Gaps):** Click **Compact Gaps** to remove silent empty bars across both voices, shifting subsequent notes and chords left to eliminate unwanted gaps in the arrangement.

#### Lyrics and karaoke tracking

At the bottom of the piano roll, a dedicated lyrics track aligns each syllable with the vocal melody:
- **Phrase-aware matching:** Click **Match Lyrics** to distribute lyrics across the vocal melody. The alignment detects natural musical breath pauses and rest gaps between melodic phrases, assigning each lyric line to its intended phrase without spilling words across rests into subsequent measures. Multi-syllable words split cleanly across notes.
- **Editing syllables:** Click any lyric tag (or select a vocal note and press <kbd>L</kbd>) to edit its text. If you enter space- or hyphen-separated syllables (for instance, `Hel- lo world`), they automatically flow across consecutive vocal notes.
- **Hover highlighting:** Hovering over a lyric tag highlights the corresponding note on the piano roll grid, and hovering a vocal note highlights its lyric tag below.
- **Karaoke dancing ball:** During playback, an animated dancing ball arcs across each note as it is sung, and the active syllable and grid note illuminate with a real-time glow.

#### Playback and harmony accompaniment

Press <kbd>Space</kbd> or click **▶ Play** to start playback from the playhead cursor. The playhead line sweeps across the grid, updating the current bar, beat, and elapsed time counter.

- **Audible click track (metronome):** Playback includes an audible click track by default, with an accented woodblock click on beat 1 of each bar and softer clicks on inner beats. Press <kbd>C</kbd> or <kbd>M</kbd> (or click **Click** in the transport bar) to toggle the metronome on or off at any moment.
- **Harmonic chord accompaniment:** Playback synthesizes warm polyphonic chord accompaniment pads directly from the score's chord progression. Even when the vocal or instrumental tracks rest, the harmonic space remains musical and warm rather than dropping out into dead silence. Press <kbd>H</kbd> (or click **Chords** in the transport bar) to toggle chord accompaniment on or off.
- **Stepping measures:** Press <kbd>Left Arrow</kbd> and <kbd>Right Arrow</kbd> to step backward and forward bar by bar, or press <kbd>Home</kbd> to jump straight back to the beginning.

#### Keyboard shortcuts

| Key | Action |
|---|---|
| <kbd>Space</kbd> | Play / Pause playback |
| <kbd>Left Arrow</kbd> | Step back one bar |
| <kbd>Right Arrow</kbd> | Step forward one bar |
| <kbd>Home</kbd> | Return playhead to start (bar 1) |
| <kbd>C</kbd> or <kbd>M</kbd> | Toggle audible click track (metronome) on / off |
| <kbd>H</kbd> | Toggle chord harmony accompaniment on / off |
| <kbd>Delete</kbd> / <kbd>Backspace</kbd> | Delete selected note(s) |
| <kbd>Ctrl</kbd>+<kbd>Z</kbd> / <kbd>Cmd</kbd>+<kbd>Z</kbd> | Undo last edit |
| <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>Z</kbd> / <kbd>Ctrl</kbd>+<kbd>Y</kbd> | Redo edit |
| <kbd>Ctrl</kbd>+<kbd>A</kbd> / <kbd>Cmd</kbd>+<kbd>A</kbd> | Select all notes across both voices |
| <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>A</kbd> / <kbd>Alt</kbd>+<kbd>A</kbd> | Select all notes from playhead cursor to end across both voices |
| <kbd>+</kbd> or <kbd>=</kbd> | Zoom in timeline horizontal scale |
| <kbd>-</kbd> or <kbd>_</kbd> | Zoom out timeline horizontal scale |
| <kbd>F</kbd> or <kbd>0</kbd> | Scroll to notes (Fit view) |
| <kbd>L</kbd> | Edit lyric for selected vocal note |
| <kbd>Escape</kbd> | Clear note selection, or close score window |

### Harmony

YuE2 left alone tends to write one four-chord loop and stay there. The **Harmony** slider pushes it
away from chords it has just used, without breaking the song's structure.

| Step | What you get |
|---|---|
| Familiar | YuE2's own chords. Often one loop for the whole song |
| Varied | Avoids repeating the same chords. Stays in the key |
| Colourful | Verse and chorus get different progressions, with richer chords. A section may not open the way the one before it did |
| Adventurous | Keeps the harmony moving, and borrows chords from outside the key |
| Outside | Adventurous, and reaches further outside the key |

**Write a new plan** uses the slider's current position, so you can reroll the same words with more
adventurous chords and compare.

This was measured rather than guessed — one set of lyrics, two styles, three seeds each:

| | Familiar | Varied | Colourful | Adventurous | Outside |
|---|---|---|---|---|---|
| Different chords in a song | 4.7 | 6.3 | 8.7 | 9.0 | 10.3 |
| Bars using a chord from outside the key | 0% | 0% | 0% | 13% | 24% |
| Four-bar patterns that are not repeats | 29% | 38% | 50% | 63% | 64% |

Every plan at every step kept its sections and valid chords. Asking for adventurous harmony in the
style text instead — "jazz harmony", "borrowed chords" — had no measurable effect at all.

### Plan variety

Under *Advanced*, **Plan variety** sets how freely the planner writes. Where Harmony acts on the
chords, this acts on everything: melody, structure and length.

- **Calm:** the steadiest. Few chords, and a melody that stays close to home.
- **Normal:** the default.
- **Lively:** a few more chords and turns.
- **Bold:** richer harmony, about three times normal's chord vocabulary, while the tune stays
  recognisably the same kind of tune.
- **Quirky:** restless. Chords keep changing, and the melody leaps between registers from one
  section to the next. For odd, off-the-wall songs.
- **Wild:** the most restless of all, and it may change key partway through.

---

## Rendering

### Interpretation

The score fixes the notes. The **interpretation** sets how they are performed.

| Interpretation | What you hear |
|---|---|
| Standard | YuE2's usual reading |
| Tight | more controlled and polished |
| Loose | rougher and more spontaneous |
| Settled | free to repeat a figure and sit in a groove |
| Restless | keeps the parts moving, avoids repeating itself |
| Wide | reaches for less obvious sounds |

### Variations

The sparkle button on a card renders **the same score and the same seed** in the other
interpretations. Because only the interpretation changes, what you hear between them is the
interpretation — not a different roll of the dice. Each lands as its own take, titled
*Night drive · Loose*. The window has its own length cap, which starts at the editor's and applies
only to these takes.

### Try more

The dice button on a card renders **the same score and words again as several new takes**, to
listen to together. Variations changes only the interpretation and keeps the seed; this changes the
roll:

- **New seeds:** a fresh seed for each, everything else kept.
- **Planner strengths:** for a take with a style LoRA that has a planner half, the same seed at
  other Planner strengths (its own is left out). Planner changes the performance itself, not only
  the voice, so it works like another seed.

The new takes are titled *Night drive · try 1* or *Night drive · planner 0.60*, and are ticked
with the original, so **Compare** opens as soon as they have finished. The window has its own
length cap, which starts at the take's own.

### Seed, and reproducing a take

Every take records its seed and every setting that shaped it. The card names them, clicking a card
shows them in the take panel, and opening it in the editor loads all of it back. **Again** opens the
editor with exactly that, seed included, so a take you liked can be reproduced, and a take you nearly
liked can be nudged one setting at a time.

The **Details** button (the circled *i*, among the small icons at the card's top right) opens a window listing everything the
take was made with in words: its model, mode, seed, interpretation, production polish, whether the volume was normalised, its
style LoRA and strengths, the length cap and the Advanced settings. **Copy** puts it on the clipboard as text, to compare two
takes or to describe one to someone else. In the editor's menus, hovering an interpretation shows what it does.

Tick **keep this seed** to keep the same seed across renders; leave it off and each render rolls a
new one.

A render uses what the editor shows: its style, style LoRA and strengths, length cap, mode,
interpretation and seed, even when rendering a take's own score again.

### Same tune, new words

The planner reads all the lyrics before it writes a note, so the same seed gives the same plan only
for the same words. Change one line and the next plan is a new tune: another melody, often another
key and tempo, and the voice moves with them.

To keep a tune you like, open the take and change its words. **Keep this tune** appears under the
lyrics, ticked, and the main button becomes **Sing with new words**. Change anything else you want
first: the style, the LoRA and its strengths, the length cap, the interpretation. The take's score is
then sung with the new words, as a new take beside the original, which stays as it is. Keep the seed
ticked to keep the voice as close as it can be. Untick **Keep this tune** to write a new plan, and a
new tune, for the words instead. New words that keep the old lines' syllable counts fit the melody
best.

### Production polish

**Production polish** applies Mothersuperior's Realaudio decoder LoRA. Stock YuE2 often sounds boxy
in the mid-range; this separates instruments and vocals more cleanly. On by default.

### Length

The length cap is a firm limit, not a target. YuE2 decides when a song ends, and usually ends by
itself; the cap stops one that will not. It starts at 360 seconds. With a recording chosen, for a
cover or an instrumental, it follows the recording's score instead, rounded up with about ten seconds
to spare, so a long song is not cut short. A cap you type yourself stays as you set it. Now and then
a render doesn't stop at the end of its score and plays on until the cap; such a take is faded out
over its last few seconds rather than cut off, and its card says it ran to the cap. Rarer still, a
render ends before the last section of its score begins. The app then renders it once more with a new
seed before calling it finished, and if that one stops short too, the card says it stopped before the
last section: **Render** again for another try.

---

## Covering a recording

1. Drop in an audio file, up to 300 MB. It is stored once and hashed, so the same file is never
   held twice.
2. Press **Transcribe**. SheetSage2 writes the melody and the chords into the score box. This is
   cached per recording, so covering the same song again skips it.
3. Fix anything it misheard.
4. Add lyrics, choose a style, press **Create cover**.

A cover follows the original's melody and chords while the style decides everything else, which is
what makes it a cover rather than a copy.

### MIDI files and covers (Experimental)

> [!NOTE]
> **Experimental:** Using MIDI files is designed for generating different, often off-the-wall takes of original tunes.

In addition to recorded audio files, you can drop or upload Standard MIDI files (`.mid`, `.midi`) directly into **Cover** mode.

When a MIDI file is uploaded:
- **Automatic score transcription:** Yeufonic analyses tracks and channels to identify the lead vocal melody, accompaniment, and harmonic chord progression, transcribing them into ABC notation and loading them directly into the Piano Roll. Synth leads or vocal melodies sequenced in lower registers are automatically transposed to a natural singing octave.
- **Embedded lyrics:** Any lyric or text events embedded within the MIDI sequence are extracted and aligned to the melody syllables.
- **Where the bars fall:** a MIDI file has no bar lines of its own, and some start with the first word on the beat *before* the downbeat. Yeufonic reads the drums and bass to find the real bar line and, when the file starts with such a lead-in, puts the first words in a short bar of their own so the chords and bar markers land where the song's do. A file with no clear drum and bass pattern is left as it is.
- **Pasted lyrics:** words you paste are fitted to the whole melody at once, a syllable to a note, with the notes left over held on the syllable before. Lines end where the melody rests and begin where a phrase begins, so a section that is longer or shorter than the lyrics' headings no longer pulls the rest out of step. If the words are longer than the melody can carry, the last lines are left out.
- **Full audio audition with SoundFonts:** The audition player synthesizes the MIDI arrangement into high-fidelity audio using **FluidSynth** and General MIDI SoundFonts (`.sf2`). The output is peak-normalised so that quiet multi-track MIDI recordings audition with full presence and clarity without distortion.
- **Select SoundFonts:** In **Settings**, you can choose your preferred active `.sf2` SoundFont bank (such as *Arachno SoundFont 1.0* or *JNS-GM 2.0*). Additional `.sf2` files placed in `data/models/soundfonts/sf2/` are picked up automatically.
- **Piano Roll refinement:** Open the **Piano Roll** to inspect or modify notes, choose which track acts as the lead vocal melody, harmonize accompaniment gaps with **Fill Gaps**, or align newly pasted lyrics with **Match Lyrics**.

### Covering a song from a corpus

A corpus's analysis has already done what a cover needs: the score, the words heard in the song, and
its separated vocal. So below your recordings, the list offers **From your corpora**, folded by
corpus, with each song's key and tempo, and a filter for a big one. Pick a song and it becomes one
of your recordings at once, with its score and its words, and nothing runs again. The words are laid
under the score's sections, as **Extract lyrics** lays them, unless you checked them in the corpus,
when they come as you left them. They go into the Lyrics box, replacing words that came from
another recording; words you typed or edited there are replaced only if you say so. The Style box takes the
style the song was learned with in the corpus, the same as its chip under a LoRA trained from it.

The file is linked rather than copied where the disk allows, so it takes no more space, and it stays
if the corpus is deleted. A few songs are marked *score: melody only* or *score: first 4 min*: their
full transcription failed during the analysis, which does for training. Press **Transcribe** for the
whole score with its chords.

**With a LoRA.** This is where corpus songs are most use: a song and a LoRA made from the same
work, or from different ones.
1. In **Cover** mode, open the recording list and pick the song under **From your corpora**. Its
   score sets the melody and chords, and its words are in the box.
2. Choose a **Style LoRA**. The corpus's own LoRA has its singer cover their own song, closest to
   the original. Another corpus's LoRA covers it in that other style and voice.
3. Set the strengths as for any cover: the recording already sets the melody, so keep **Sound**
   near **0.50**, and raise it for more of the LoRA's voice and sound.
4. The Style box already holds the song's own style, and choosing a LoRA puts its trigger word in
   front. That keeps the song's genre and mood; another chip, or the filter's tags, moves it
   somewhere else. The tempo and key come from the score, whatever the style says.
5. Press **Create cover**. **Variations** then renders it in the other interpretations, and
   **Sing again** gives another voice over the same score, as with any take.

### Extracting the lyrics

**Extract lyrics**, beside *Transcribe*, writes down what the recording sings: it separates the
vocal, listens to it, and lays the lines under the sections of the score. It is asked for rather
than done with every transcription, because it takes a couple of minutes where transcribing a score
takes seconds. The vocal is separated, and its words heard, on the GPU when the engine has Demucs and Whisper and on the CPU
otherwise (Settings, **Use the GPU for stems and lyrics**), and the bar says which of the two stages it is on. Whisper on the GPU
and on the CPU do not always write the same words for the same vocal, as neither is exact: a hard vocal, such as backing singers
over a lead, can differ by a fifth of its words either way. The separated vocal is kept, so extracting the same recording again skips
straight to the listening, which is most of the wait saved.

The words are kept with the recording. Press **Extract lyrics** again and they go straight back in
the box, and you're asked whether to extract them again, which is worth doing after changing the
method in Settings. Choosing another recording takes its words in the same way, and a recording
with none clears the last one's. Words you typed or edited stay unless you agree to replace them.

Expect a good draft rather than a transcript. Measured against the real words of two songs, Whisper
got **1.5% of words wrong** on one and **25%** on the other, where lead and backing vocals sing over
each other in the last chorus. It listens to the whole vocal: it used to skip whatever its voice
detector took for silence, which on sung vocals was most of the song. Read the draft and fix what it
misheard, especially where voices overlap.

**Letting an external LLM listen.** If an external LLM is your provider, Settings has a choice under
*Lyrics from a recording*. Set it to **External LLM** and the separated vocal is sent to the model to
hear the words, while Whisper still works out when each line is sung. On the same two songs Gemini
got **1.5% and 23%**, so the two are close; try both on a song Whisper struggles with. It needs a
model that accepts audio, such as Gemini. When the model's reply looks like lyrics, its words are
used, even where they differ a good deal from Whisper's: a vocal buried in a mix is where Whisper
struggles most, and the model does not. If the model refuses the audio, holds back (cutting lines
short, or pointing you at a lyrics site, as a model may with a song it recognises) or sends back
almost nothing, you get Whisper's version instead. The message when it finishes names which one
heard the words. The vocal leaves your machine for this; Whisper keeps it here.

For a corpus song, **both versions are kept**. When both exist, the song's Review panel shows
**Words from** with each version and its word count, the external model's in use by default. Pick
the other and its words go in the box. The first time a version is chosen its words are drafted, which
marks their sections with the external model; after that each version keeps its own words, edits and
**checked** tick, so switching between them is instant and makes no call to the model. Whisper's own lines have any word
it repeated more than eight times in a row, such as a held "la" it wrote hundreds of times, cut
back to eight.

---

## Instrumentals

The third mode writes a piece with no vocal. In place of lyrics it takes a **structure**:

| Structure | What YuE2 gets | Who decides |
|---|---|---|
| Let YuE2 decide | `[instrumental]` | YuE2 chooses the sections and their lengths |
| Sections | `[intro] [verse] [chorus] …` | you choose the sections, YuE2 their length |
| Timed sections | `[intro 0:00-0:15] …` | you choose both |

Add sections with the **+** chips, reorder them with the arrows, and give each a length when timed.
**Sent to YuE2** shows exactly what the model receives. The structure is guidance: YuE2 may rename a
section, add an interlude, or run past the times you gave, so the length cap is the firm limit.

### An instrumental from a recording

**From a recording** at the top of the editor takes one of your recordings, as a cover does. Its
transcription is the score, so there is no plan to write, and the render plays its melody and
chords with the instrumental LoRA.

The sections come from the score too: one per section of the score, in the names the LoRA knows. An
*interlude* becomes a bridge. A render pairs each section of the structure with one of the score,
which is why the builder gives way to them. To rearrange the song, drag a section to a new place or move it with the arrows, add a
**copy** of it after itself, or take it out with the **✕**: each change rewrites the score (the Score
window shows it), and **Restore the original sections** puts it back until another score is loaded.
While the take plays in the editor, the section it is at is lit, and double-clicking a section jumps to it. A cover shows the same list under its words, and its words are matched to the sections in order, so
change them to suit: the list says what they need after you add, remove or rearrange sections. It also shows the total against the
length cap, and offers to raise the cap when a longer song would be cut short. Press **Create instrumental** to render.

An instrumental you wrote from a structure has a score too, and once it is planned its sections are listed in the same way. The
structure builder is the brief for a plan not yet written, so it gives way to the list. Rearrange the sections and press
**Render this score**: the render's section tags follow the edited score. A take that already has audio is rendered as a
new take beside it, whatever you changed, so the original keeps its own. **Write a new plan** (under the score) still asks
for a different melody from the structure the take was written with.

**A song with vocals works too.** Its score has the sung melody in the vocal part, which would come
out sung, so the tune is given to an instrument: wherever no instrument is playing, the sung notes
move to one, and the vocal part keeps only its chords. The editor says so under the recording. It
is usually the better choice for a song: without its voice, the transcriber tends to miss the
difference between verse and chorus, and hears the whole song as one loop of chords. The LoRA
arranges it as an instrumental, so expect parts of its own, such as extra guitar.

Choose **No recording** in the list to go back to writing a plan.

### When an instrumental sings

Occasionally the model puts a voice into an instrumental. This is a model failure, not a setting
you got wrong. Before rendering, if the plan puts notes in the vocal voice, a dialog offers a new
plan, a new seed, or rendering anyway. A finished take is not checked for singing: listen to it.

### An instrumental from a song's score

**Make an instrumental**, under a song's or cover's score on the editor's Score page (beside **Render this score**
for a song), makes the
same score as an instrumental, in a new take: the original is left as it was. The sung melody moves
to an instrument, only the score's section tags are sent to the model in place of the words, the
instrumental LoRA is used, and the style loses the tags that describe a voice ("soft male vocal").
It is the way to get "this tune, no vocals". Emptying the Vocal part of a song's score by hand is
not enough: a song's render still sings the words it is given.

---

## Voices

The **Vocal** chips set the singer's sex and character by writing into the style.

## Corpora and training a LoRA

A **corpus** is a folder of songs, prepared as a training set for a style LoRA: typically one
artist, one genre, or a few similar artists.
Open **Corpora** from the menu. It is on by default; `TRAINING_ENABLED=0` for the app, or an
engine built with `WITH_TRAINER=0`, takes it out.

Training is the most demanding thing the app does: a 16 GB card is the practical minimum.

1. **New corpus.** Give it a name and a **trigger word**, say whether the voice is male or female
   (**none** for songs without vocals: see below), describe the sound shared by every song, and open the folder that holds the songs. Confirm you
   have the right to train on them, then press **Scan the folder**. The folder is only read.
   **A corpus without vocals.** Choose **none** for **Voice** when the songs are instrumental, such as
   dance and electronic music. The app then does not separate a vocal or listen for words, so nothing
   invents words over synths. Each song's lyrics are the section tags found in its score (or
   `[instrumental]` when it has none), the caption leaves out the vocal clause, and there is no lyrics
   review: the **Sections** box can be edited, and an edit is kept. The sound of each song is described
   by the local model when it is installed, since the external one would only have a title to go on.
   A LoRA trained this way may write notes in the Vocal part of a plan, which makes a render sing or hum;
   a plan's "may sing" warning shows it. Changing the Voice of a corpus already analysed changes its
   lyrics to match.
2. **Choose the songs.** Untick any you want left out. A recording longer than 10 minutes is
   left out, since it is most likely a whole album in one file. If a `.cue` sheet sits beside it,
   **Split into tracks** cuts it into its songs, which take its place in the corpus. The tracks go
   in the app's own folder; yours is not changed.
3. **Analyse.** Each song's vocal is separated, its key, tempo and sections are found, and its
   lyrics are drafted, tagged by section. With an external LLM set in Settings, the sections are
   marked from the words as heard: choruses by their words coming back, new sections by the
   pauses. Only the lines and their timings are sent, and the words and their order are never
   changed. Without one, or if its answer does not hold every line, the tags come from the music
   analysis. **Redraft**, beside Save in a song's review, marks the sections again the same way
   without hearing the song again, for a song drafted before, and replaces what is in the box. A line under the buttons says what is running, and
   **Stop** ends it. Finished steps are kept, so **Analyse** carries on from where it stopped.
4. **Review.** Open a song to check its lyrics and tick **checked**, and to describe its sound
   where it differs from the rest. The style caption shows what the trainer will read.
5. **Export training set.** Writes the audio, lyrics and caption for each song. A line under the
   buttons shows how far it has got. The trainer takes only so much of a song, which the app works
   out from your graphics card's free memory (about 5½ minutes on a 16 GB card; the Logs window
   says what it chose). A longer song is cut at the end of its last section within that, faded
   out, and keeps only the words still sung. Its row says "first 3:12 trained". If training
   runs out of memory, set the `TRAIN_MAX_MINUTES` environment setting to a lower number, such
   as 3.5: see the README.
6. **Train a LoRA.** This takes a long time, and the GPU is not available to the app until it
   finishes. Progress shows under the buttons and on the main screen, where you can stop it,
   and the corpus's badge at the top of the page pulses while it trains. Training again keeps
   the LoRA from the last run under a dated name, in **Previous runs**, or deletes it, as you
   choose.
   Training needs at least about 12.5 GB of GPU memory (at a 3½ minute cut; a longer cut takes
   more), most of it while it prepares the songs, so a 16 GB card is the practical minimum; a smaller one, such as 8 GB, can't train, though it can
   still use LoRAs trained elsewhere (**Install a LoRA**). The Train window warns when less than
   that is free, so close anything else using the GPU first.

### A run that ends early

A run can end before its last step: **Stop**, a crash, or the GPU running out of memory. The line
under the buttons then says when and why, and after which step. Along the way the trainer saves a
checkpoint every 50 steps, and keeps a copy of the best one so far by its planner loss, so most of
the work is usually still there. **Finish with what it saved** does what a finished run does, from
those files: the best copy, or failing that the last checkpoint, becomes the LoRA under the
corpus's name, with its trigger word, and the checkpoints fold under it in the Style LoRA list. It
takes seconds and no GPU time. The last steps of a run change the LoRA least, so one finished this
way is usually close to a full run; **Checkpoints** renders a song once on each step if you want to
compare by ear. To train the whole run again instead, press **Train a LoRA**.

### Run all

**Run all**, beside the three, does Analyse, Export and Train one after the other, for a corpus you
would rather not wait on: a big one takes hours to analyse. It asks first what to do with an
earlier LoRA, then carries on with the page closed. It analyses only what still needs it, and a
song whose analysis fails is left out of the training set and named under the buttons. Lyrics
nobody has checked are used as drafted. **Stop** ends it where it is, keeping what is finished;
stopped while it exports, it finishes the training set first. It waits for anything already using
the engine before it trains. An app restart ends it, and **Run all** again carries on.

### Running out of GPU memory

A job that runs out of GPU memory says so, with what to try: close other programs using the GPU,
lower the length cap, or, for training, leave the longest songs out. If the engine crashes and
restarts, the job it was running is lost, and it says that too.

### The trained LoRA

When training finishes, the LoRA appears in the **Style LoRA** list with its trigger word. Choosing
it shows a chip for each song it learned from, and clicking one puts that song's style in the box.
Past a dozen songs, a filter box and a row of the tags that recur across the corpus (its genres,
moods and instruments) narrow them; click two tags to find songs with both. The list shows its
first dozen until **Show all**. See **Balancing Planner and Sound** below for starting strengths. To share it, press **Download LoRA** on the corpus's page, or **Download** under
the picker; see **Sharing a LoRA** below.

To add a LoRA someone shared, press **Import LoRA** beside **New corpus** and choose their zip. To use a
LoRA trained elsewhere from the exported set, press **Install a LoRA** and choose the
file. It is added to the Style LoRA list with this corpus's trigger word.

**Deleting a corpus** removes the app's copies of its songs, the separated vocals, the lyrics and
the scores. The folder you pointed it at, and any LoRA made from it, are not touched.

---

## Copyright and consent

What you train on, and what you do with the result, is your responsibility under the law where you
live. The app asks you to declare it and does not check it: creating a corpus requires you to confirm
that you have the right to train on those recordings.

Two facts are worth knowing:

- The YuE2 weights are **CC BY-NC 4.0** — non-commercial use, whatever you train from them.
- Training privately on a corpus and publishing the LoRA or its output are different acts. The second
  is the one that usually needs permission: from whoever holds the rights in the recordings, and for
  a recognisable voice, from the singer.

LoRAs you did not train yourself carry their own licences: read them on the page each one comes from
(see **Where to find style LoRAs** under Style LoRAs).

## Style LoRAs

A LoRA is a small file that leans the model towards a sound. Put one in `models/loras/` and press
**Rescan** under the picker, or use **Install**, and it appears in the **Style LoRA** list.

A style LoRA can hold two halves, and the picker shows which ones a file holds:

- **Planner** shapes what is played — the score plan (form, harmony, phrasing), and then the music
  the render writes from that score. It applies at both steps.
- **Sound** shapes the audio — timbre and production.

A strength the file cannot use is greyed out, and a file this engine cannot load at all is named as
such rather than failing quietly inside a render.

### Where to find style LoRAs

There are free Style LoRAs available, mostly found on Hugging Face. Here are a few examples of LoRAs that
Yeufonic can import and use with your own creations:

- [Militant reggae](https://huggingface.co/becausereasons/yue2-mltnt-militant-reggae)
- [Chanson française](https://huggingface.co/becausereasons/yue2-chnsn-chanson-francaise)
- [Canzone italiana](https://huggingface.co/becausereasons/yue2-cnzn-canzone-italiana)
- [Bulgarian voices](https://huggingface.co/becausereasons/yue2-blgr-bulgarian-voices)
- [Qawwali, sufi and tabla](https://huggingface.co/becausereasons/yue2-qwwl-qawwali-sufi-tabla)
- [J-pop](https://huggingface.co/storagejuju/yue2-jpop-t4-lora), a single LoRA with a Sound half only

To add one, download its `.safetensors` file from the repository's **Files** tab, put it in `models/loras/`
and press **Rescan**, or press **Install** and choose the file. The repository's page gives each LoRA's
trigger word and suggested strengths: write them in a `.txt` beside the file (see **Descriptions** below) and
the picker shows them, and puts the trigger word at the front of the Style for you. A LoRA from elsewhere
may be saved in a layout this engine cannot load: the picker names it as such, and it does no harm.

Each LoRA carries its author's licence, which these sets give as CC BY-NC 4.0: personal and non-commercial
use, the same as YuE2's own weights. Read the licence on a LoRA's page before using it, or sharing what it
makes.

### Balancing Planner and Sound

- **Cohesive corpora:** A LoRA trained on a single album or unified acoustic sound (e.g. 1960s folk rock) can run higher strengths, typically around **Planner ~0.85 / Sound ~0.80**.
- **Diverse corpora:** If the training corpus spans multiple genres, production styles, or eras (e.g. acoustic folk, rock, and synth-pop), high Sound weights can cause acoustic clashing. Up to about **Planner 0.70 / Sound 0.70** keeps the audio clean while retaining the artist's melodic phrasing and vocal character.
- **Covers:** your recording sets the melody, so there is less for the LoRA to shape and the Sound half is pushed harder. Keep Sound near **0.50**.
- **Plan variety:** with a LoRA trained from a corpus, **Calm** or **Normal** gives the most recognisable result. **Calm** can loop with a style LoRA and a short style, and the plan then runs for
  minutes with long repeated intros, or with nothing sung. Describe the style in more detail (genre, instruments and feel), or use **Normal**. A plan like that, or one far longer than a song, is written once more
  with a new seed, and the take fails with advice if the second comes out the same.
- **Finding a good take:** the LoRA's character depends on the roll as much as on the strengths.
  Between about 0.3 and 0.6, **Sound** changes the voice little, so there is no need to push it.
  **Planner** changes the performance itself, not only the voice, so a value that suits one song
  can be the weakest for another. Treat it like the seed: try a few (say 0.6, 0.8 and 1.0) and a
  few seeds with **Sing again**, and keep the take you like.
- **Save strengths:** when you find the right pair for a LoRA, press **Save strengths** under the
  picker. Choosing that LoRA then starts at them, and they travel with it when you share it.

### Trigger words

Most style LoRAs are trained on captions that **begin** with a trigger word, and do very little
without it. The app handles this: choosing a LoRA puts its trigger at the front of the Style,
changing to another swaps it, choosing None removes it, and a render puts it back if it was
deleted. You will see the word appear in the Style box — it is yours to edit or move.

### Descriptions

The list is grouped by set. Click a heading to open or fold it; the picker remembers which you
left open, and the group holding your current choice always opens with it.

Hover any entry to read what it is, in its author's words, with their suggested strengths. Those
descriptions come from a text file beside the LoRA:

```
CHNSN Rive Gauche
Trigger: chnsn
Step 200, the decoder-loss minimum. The more supple of the two: acoustic
narrative, yé-yé, female leads, waltz meters.
```

The first line names it, a `Trigger:` line becomes the trigger word, and the rest is the
description. A LoRA of your own gets one by writing a `.txt` beside it. `families.txt` in the same
folder gives the groups their headings, one `prefix = label` per line.

### LoRAs trained from a corpus

A LoRA trained from one of your corpora is an ordinary style LoRA: it appears in this list with the
rest, its trigger word beside it, and the same two strengths apply.

### Trying the checkpoints

A training run saves a checkpoint every 50 steps, and keeps them under its LoRA in the picker:
**▸ 9 steps** beside the LoRA's name opens them (Settings can delete them instead, to save the
space). A checkpoint whose LoRA has been deleted stays under **Training checkpoints**. To clear
some out, press **Edit** on the corpus: **Training checkpoints** there lists each run's, this run's
and any previous run's, with their sizes. Tick the ones to go and press **Delete**. The finished
LoRA is not listed; it has **Delete LoRA** of its own. Each is the LoRA as it stood at
that point in training. They sound about as good as each other, but each has its own weighting of
what it learned, so each has its own taste while keeping the style and signature sound the LoRA
was trained on.

To hear them side by side, choose the LoRA, set up the editor as you would for one take, and press
**Checkpoints** beside **Delete LoRA**. It is greyed out for a LoRA without checkpoints. Tick the
steps you want, set a length cap for these takes if you like, and press **Render**. The editor's
own action runs once on each checkpoint, all with one seed, and each take is named after its step:
*Night drive · step 250*, *Night drive · full*. A song or an instrumental writes its plan and goes
straight on to render.

In a song or an instrumental the LoRA writes the tune as well as shaping the sound, so the same
seed does not give the same song: each checkpoint writes its own melody and structure. The seed
picks from what the model thinks likely, and each checkpoint thinks slightly differently from the
first note, so the plans part ways within a few bars. What stays is the sound. To compare only the
sound, load one plan with **Score** and press **Render this score** with each checkpoint in turn.

New files appear once the engine has looked at `models/loras/` again, which it does when the
options are reloaded.

### Sharing a LoRA

Choose a LoRA and press **Download** under the picker: you get one zip with the LoRA and its note.
For a LoRA trained from a corpus, the note carries its learned styles, so the chips come with it.

To add one someone sent you, press **Install** and choose their zip, or a bare `.safetensors`
file. It goes into `models/loras` under the heading **Installed**, with its name, trigger word and
chips. **Delete LoRA** removes the chosen LoRA, its note and its group line; **Rescan** reads the folder
again after you add a file by hand.

---

## Stems

Press **Stems** on any take. Choose a model, tick the parts you want — vocals, drums, bass, other,
and guitar and piano on some models — and run.

Separation runs on the **GPU** when the engine has Demucs, as a job in the engine's queue: it waits for a
render that is running, then goes quickly, and a render queued behind it waits in turn. An engine built before
this, a LoRA being trained (which holds the GPU), **Use the GPU for stems and lyrics** set to Off in Settings, or `STEMS_ON_GPU=0` leaves it on the **CPU**, which is slower
and never holds up a render. *Fine tuned* runs four models in turn for a better split and takes about four times
as long.

For a backing track, choose **Vocals and instruments**. It splits the song in two: the vocal, and
**instruments**, everything else as one stem. Untick **vocals** to keep only the instruments. It is
the same separation as the four stems, added back together, so it takes as long and sounds as clean.
The *fine tuned* one leaves the least of the voice behind.

Stems land in `data/stems/<title>-<id>/`, play from the chips on the card, and download singly or as
a zip. They stay until you delete them.

---

## Stopping, deleting and starting again

A queued or running take shows **Cancel** on its card, and **stop** on the job card stops whatever
the engine is working on. Deleting a take stops its job and removes its stems. **Delete** beside a
recording removes the file and its stems; covers made from it keep their audio and score, but cannot
be rendered again.

**+ Song**, **+ Cover** and **+ Instrumental** on the take panel, or **New song** beside the
editor's heading, start again from the take on show. They clear the title, the lyrics and the score,
and start from the defaults: an empty style (with a chosen LoRA's trigger word), the usual length
cap, Harmony Familiar, plan variety normal, interpretation Standard, production polish on,
normalising off, and a new seed that is not held. A chosen LoRA and a chosen recording stay chosen.
The take being shown lets go of the editor, so Render cannot act on it by mistake.

Words you had typed but not used are not thrown away: a bar offers to restore them.

## The library

### Spaces

Takes live in **spaces**: a space per song, per album, or for sketches. The menu above the takes
chooses which is on show, and anything you make lands there. Deleting a space never deletes takes —
they move to Default. Recordings are shared by every space, so one recording can be covered in
several.

The folder button on a card moves that take to another space.

### Cards

Each card names the settings that shaped it — Harmony, Interpretation, Plan variety, the LoRA and
its strengths, the seed and its age — so a card reads as the recipe that made it.

**Save** asks which format to download the take in, FLAC, WAV or MP3, starting with the output
audio format set in Settings.

**Search takes** finds the takes with every word you type somewhere in the title, style, lyrics or
LoRA name, in any case. It looks through the space on show; **All spaces**, beside it once you type,
looks through every space, and a card from another space says which one. × or Escape clears it. The
box starts empty each time the page opens, and offers your last few searches that found something:
click one, or pick it with the arrow keys and Enter.

**Starred** shows only starred takes. **Compact** switches between three narrow cards across and
wider ones with more of the prompt. A title always stays on one line, ending in … when it is long. Hover over a card's title, settings or style to read all of it.

### Comparing takes

Tick two to six takes and press **Compare** (it appears beside Select all once two are ticked, and
waits for takes still rendering). The takes stack in one window on a shared position: press **1** to
**6** or click one to switch, and it carries on from the same moment in the song, playing or
paused. **Space** plays and pauses, the arrows move 5 seconds, and the star marks the one you
prefer. **Match loudness** turns the louder takes down to the quietest, since a louder take tends
to sound better; **Hide names** shuffles the takes and calls them Take A, B, C for a blind listen.

### The player

Click or drag the waveform to seek. Previous and next step through the cards in the order shown.

| Key | Does |
|---|---|
| Space | play or pause |
| Left, Right | back or forward five seconds |
| Up, Down | volume |

The keys do nothing while you are typing, or while a window is open in front. The system media keys
work too.

---

## Settings

Press **Yeufonic** in the top left. Settings live on the server, so they follow you to any
browser and survive a rebuild: the output audio format for stems and a take's Save, the
separation model, where stems are written, whether training checkpoints are kept, and how
instrumentals are checked for singing.

### Storage

**Settings → Storage** shows where Yeufonic's disk space is going and lets you give some back. Training a
corpus leaves a lot of files that are not needed again: copies made for the engine while songs were analysed,
the training set (each song written again as lossless FLAC, larger than the original), and the checkpoints
saved along the way. The window lists each of these with its size, **what it is** and **what removing it
costs**, and removes only what you tick, after a last confirmation. **Tick the ones that cost nothing** ticks
the copies that are simply made again when needed.

Songs analysed from now on keep their separated vocal as FLAC, the same audio in about half the room. The
window can **convert the WAV vocals you already have**: each is converted, checked to decode to exactly the same
audio, and only then is the WAV removed. It runs in the background and can be stopped.

Training checkpoints deserve a second look before they go: each is an entry in the Style LoRA list that you
can pick for new takes, so removing a corpus's checkpoints takes those entries out of the list for good. Its
finished LoRA stays and keeps working. A corpus's training set is different: removing it leaves the LoRA and its
checkpoints in the list, and only training that corpus again needs it.

Your takes, songs, finished LoRAs and models are never listed for removal. Anything belonging to a corpus that is
training, being exported or being analysed is shown greyed and cannot be touched until it has finished.

Below that, **Tidy up automatically** chooses what Yeufonic removes for you: the working copies of each song
once its analysis ends (on by default), the training set once a LoRA has trained (off by default; the corpus
then needs **Export** again before it can train again), and the training checkpoints (kept by default).

Docker's own images and build cache are outside Yeufonic and not covered here; `docker system df` shows them.

### The YuE2 model

YuE2 comes in two sizes, and an install has one: **full quality**, which we recommend, or **low
memory**, a smaller copy for graphics cards with little video memory. **About**, in the same menu,
says which you have. It is chosen when Yeufonic is installed, not here:

- **On Windows**, run the installer again. Its components page offers both sizes, shows the one you
  have, and switching downloads the other and removes the first.
- **With Docker**, `sh scripts/fetch-models.sh` fetches full quality and
  `sh scripts/fetch-models.sh --int8` the low-memory one. With both files in `models/checkpoints`, the
  app uses full quality unless `YUE2_CHECKPOINT=int8` is set in `.env`.

Try low memory if renders are very slow or the engine runs out of GPU memory. Training a LoRA uses
the full-quality model and says so if only the small one is installed. The README on GitHub has
a section, *Choosing a model size*, with what to expect from each.

**Check for a new version** is the one thing here that uses the internet on its own account: every
four hours the app asks yeufonic.com whether a later release is out, and says so with a pill beside the
version in the top right. That pill hands you the installer, or, for a Docker copy, the two commands
that update it. It is one request and nothing else leaves the computer; **Do not check** turns it
off. The menu's **Check for updates** asks then and there whether this is on or off, and answers in
the menu: which version you are on, and whether it is the latest.

When there is a newer one, the menu offers **Get x.y.z**, which downloads the installer on a Windows install or puts the two commands on the clipboard for a Docker copy.


**Theme** sets how the app looks: **Dark**, **Light**, **Match the computer**, which follows your
system's light or dark and changes with it, **Studio**, a warm dark with amber, or **High
contrast**, black and white with strong outlines. It changes at once, and each browser remembers it
so the page opens in it. The log window stays dark in every theme, like a terminal.

---

## Using Yeufonic from an AI agent (MCP)

Yeufonic can act as an **MCP server**. That lets an AI agent on the same computer, such as Claude Code or Cursor, use it for you:
ask for a song, a cover or an instrumental, wait for it, play it, and tidy the library, all in your own words ("make a one-minute
EDM instrumental in the EDM space and play it"). The agent does what the page does, through the same routes, so a take it starts is an
ordinary take in your library.

### Setting it up

1. **Turn it on.** Open Settings and set **MCP server** to **On**. It is off by default, because a request can start work on the GPU.
2. **Connect your agent** to the app's address with `/mcp` on the end: the address you open Yeufonic at, for example
   `http://localhost:8090/mcp`. In Claude Code:

   ```
   claude mcp add --transport http yeufonic http://localhost:8090/mcp
   ```

   Other clients take the same address as an HTTP server. Those that read a settings file usually want something like
   `{"mcpServers": {"yeufonic": {"url": "http://localhost:8090/mcp"}}}`. No login or key is needed.
3. **Ask.** Start your agent from any folder and describe what you want.

**Which address?** It is the address you open Yeufonic at, with `/mcp` on the end.
- **Docker:** `http://localhost:8090/mcp`.
- **The Windows install:** the app's port is in `settings.ini` (`app_port`, 8090 unless you changed it, for instance to run beside
  a Docker copy). With `app_port = 8091` it is `http://localhost:8091/mcp`.
- **Agent in WSL, app on Windows:** this does not connect. The Windows app listens only on Windows' own loopback address, which WSL cannot
  reach (Docker running inside WSL is fine, as it is in WSL too). Run the agent from Windows (PowerShell or the Windows version of
  your agent), or turn on WSL's mirrored networking (`networkingMode=mirrored` under `[wsl2]` in `.wslconfig`, then `wsl --shutdown`),
  which makes `localhost` the same on both sides.

If your agent says the server **needs authentication**, it is almost always because the setting is still Off: turn it on, then
reconnect the agent (in Claude Code, `/mcp`). Reconnect after restarting Yeufonic too, because a restart ends the connection.

### What you can ask for

| Ask for | What happens |
|---|---|
| "List my latest takes", "show the takes in the EDM space" | Lists takes, newest first, with a short id, when each was made, its length and style |
| "Make a one-minute instrumental in a synthwave style" | Plans and renders an instrumental. A length, a space and a [style LoRA](#style-loras) can be named |
| "Make a song in a folk style with these words" | The same for a song, from the lyrics you give |
| "Make a cover of *the recording* in a jazz style" | Makes a cover from a recording already in your library. It needs a score (transcribe it in the app first). Without words of your own it uses the words heard in the recording |
| "Play it" | Opens the take in your browser, where it plays |
| "Star that one", "call it Sunrise", "move it to the Folk space" | Stars, renames or moves a take |
| "Render it again with a new seed", "stop that" | Renders a take again, or cancels one in progress |
| "Give me a few more like that one" | Renders the take again with new seeds, as several new takes to listen to together |
| "Transcribe *the recording*" | Transcribes a recording into a score, so a cover can be made from it. It leaves a recording that already has a score alone unless asked |
| "Split that into vocals and instruments" | Separates a finished take into its parts (four, six, or just vocals and instruments) and gives you a link to each file and one to the whole set as a zip |
| "Is Yeufonic busy?" | Says whether the engine is ready, what is running and with what progress, what is waiting, and whether a LoRA is training |
| "Delete that take" | Shows what would go and asks you first; see below |

Making a take takes minutes. The agent starts it and waits, reporting progress, so you can ask for the next thing meanwhile.

### Everything it can do

You do not need these names: you ask in your own words and the agent picks. They are here so you can see what exists, and so you can
tell your agent which one you mean.

| Tool | What it does |
|---|---|
| `list_takes` | Lists takes, newest first, optionally only those matching words, in a named space, or starred. Shows a short id |
| `get_take` | One take in full: how it was made, its status, any error and, once it has audio, a link that plays it. Can include the score |
| `wait_for_take` | Waits (up to about a minute at a time) for a take that is being made, and says whether it has finished |
| `make_instrumental` | Plans and renders an instrumental from a style, with a length, a space and a style LoRA if you name them, and sections if you give them |
| `make_song` | The same for a song, from lyrics |
| `make_cover` | A cover from a recording in the library, using its score and, unless you give others, its words |
| `try_more` | Several more takes from an existing one, with new seeds |
| `render_take` | Renders a planned take, or renders a finished one again (with a new seed if asked) |
| `cancel_take` | Stops a take that is queued or running |
| `make_stems`, `get_stems` | Splits a take into parts, then lists the parts with a link to each and to the whole set as a zip |
| `list_recordings`, `transcribe_recording` | Shows the recordings in the library and whether each has a score; transcribes one that has none |
| `list_style_loras` | The style LoRAs installed, with their trigger words and the strengths saved with them |
| `list_spaces`, `move_take` | The spaces and what each holds; moves a take to another |
| `star_take`, `rename_take` | Stars or unstars a take; changes its title |
| `delete_take` | Deletes a take for good, after showing it to you and being told to go ahead |
| `status` | Whether the engine is ready, what is running and waiting, and whether a LoRA is training |

### Ideas for using it

- **A batch of ideas, then pick.** "Make five one-minute EDM instrumentals in different styles, in the EDM space." It starts them one after
  another and tells you as each finishes. You listen, then say "star the second and fourth and delete the rest."
- **Iterating on one idea.** "Make an instrumental in a dreamy synth style and play it", then "now the same with more drums", and
  "give me four more like the second one." The agent keeps track of which take is which, so you can talk about them by position or
  by what you said about them.
- **Covers without clicking through.** "Transcribe *the demo*, then make three covers of it: folk, synthwave and jazz." It transcribes
  the recording first if it has no score, then makes the covers in the space you name.
- **Working a LoRA.** "List my style LoRAs, then make an instrumental with the jazz one." The trigger word and the saved strengths are
  handled for you, which is easy to get wrong by hand.
- **Words from the agent.** The agent can write the lyrics itself: "Write lyrics about a night train and make a song of them in a folk
  style." Yeufonic only sees the finished words.
- **Stems for a whole set.** "Split my five newest takes into vocals and instruments and give me the links." They queue behind
  one another, and behind any render the GPU is running.
- **Library housekeeping.** "Find the takes with the same title, show me which is newest, and delete the older ones", or "move everything
  I made today into a space called Drafts." It works from ids and asks before deleting.
- **Checking before a long job.** "Is Yeufonic busy?" before you queue a long render or a batch, so you do not queue behind a training run.
- **Part of a bigger task.** Because it is a tool the agent can call, it can sit inside something larger: make a track for a video and
  write the note that goes with it, or build a playlist-sized batch and name the takes to match a list.

The agent cannot hear a take, so it cannot judge how it sounds: you do the listening, and it does the legwork. It is also not a
shortcut round the engine: the GPU still does one job at a time, so a large batch is a long queue.

### Things to know

- **Takes can share a title,** so the agent works from a take's **id** and shows a short one (the `short_id` column) when it lists takes.
  You can name a take by the start of its id, four characters or more, as long as only one take begins that way. If two do, it tells you
  and asks for more.
- **Deleting asks twice.** The agent first shows you what it would delete, including any other take with the same title, and deletes
  only after you say yes. A starred take needs you to say so explicitly. A deleted take, with its audio, cannot be got back.
- **Spaces and style LoRAs are named,** not numbered: "in the EDM space", "using the jazz LoRA". A name that matches nothing gets the list of
  what there is, and nothing is created. A LoRA's trigger word is added to the style for you, since a LoRA does very little without it.
- **An instrumental is always planned with a structure that has times,** worked out from the length you ask for (about two and a half
  minutes when you do not say). Without times the planner writes plans too long to use. Name your own sections and they are used as given.
- **Only on this computer.** The same host-name and cross-site checks apply as for the page, and there is no login, so turn the setting
  off when you are not using it, and do not expose the port to a network you do not trust.

## System Logs

The app writes a consolidated, real-time log of every major action — score planning, rendering, audio transcription, stem separation, and LoRA training — tagged with `INFO`, `WARN`, and `ERROR` prefixes.

- **In-Browser Console:** Click the **Logs** button in the topbar (or select *Logs* from the brand menu) to open a floating, draggable, and resizable console. It stays open without blocking the page, allowing you to queue takes and monitor generation in real time.
- **Standalone Window:** Click **↗ Pop out** in the console header (or navigate directly to `/logs`) to open a dedicated log viewer window.
- **Terminal Tail:** Logs rotate automatically to `data/logs/yeufonic.log` on the host, where you can follow them live:
  ```bash
  tail -f data/logs/yeufonic.log
  ```

## The engine's own page

The engine is ComfyUI, and its own interface is reachable: <http://localhost:8189> with Docker, or
<http://localhost:8188> with the Windows install (the `engine_port` in `settings.ini`). It answers
on this machine only, with no login.

- **It is the same engine and GPU as the app.** A job run there shows in the app's queue as coming
  from outside, and the app's own jobs wait for it.
- **Its History shows every graph the app sent**: the plan, the render and the transcriptions, with
  every setting as the engine received it. It's a useful place to see exactly what a take was made
  from.

---

## When something is wrong

**The header says the engine is missing.** The app runs without it and will say so. Renders wait.
Check the engine container is up.

**A song will not end.** Usually too much planner strength. Drop the LoRA's Planner to 0.5. The
length cap will stop it regardless.

**A LoRA seems to do nothing.** Check the trigger word is in the Style, and that the strength you
raised is one the file actually holds — the picker greys out the other.

**A take says *Weak render*.** It came out far quieter than usual all the way through. Some takes
like that are only quiet; others sound thin or distorted. Click the warning to normalise it, which
brings it up to the usual loudness and marks it *Normalised*. If it still sounds wrong, try another
seed, and keep that LoRA's Sound at 0.5 or below. It happens most in covers through a style LoRA
trained here.

**Normalise volume.** Tick it in the editor and each take made while it is ticked is brought to the
usual loudness when it finishes, and marked *Normalised*. A take made without it can be normalised
later with the speaker button at the top of its card. The file as rendered is kept beside it, and
clicking *Normalised* goes back to it. How loud it is made is set in Settings, under *Normalise to*.
Unticked, a take keeps the level it was rendered at.

**An instrumental sang.** See *When an instrumental sings* above. It is a model failure; a new seed
usually fixes it.

**A take will not render again.** Its recording may have been deleted. Covers keep their audio and
score, but cannot be re-rendered from a recording that is gone.

**Nothing plays, but the waveform moves.** Check the volume slider and that a stem is not selected —
the player follows whatever was last clicked.
