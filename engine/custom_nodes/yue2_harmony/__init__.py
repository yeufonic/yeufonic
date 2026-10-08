"""Yeufonic: a harmony control for YuE2 score plans.

YuE2's planner tends to write one four-chord loop and use it for every section.
The stock repetition penalty cannot fix that: it pushes against every recent token,
bar lines and section names included, and breaks the score long before the chords
change.  This node pushes against recently used chords only.

While the planner writes a chord symbol ("Cmaj7"), candidate tokens that would
spell a recently used chord lose logits in proportion to that chord's share of
recent chord changes.  Holding the current chord is free up to a limit, so the
model keeps its own harmonic rhythm; past the limit, staying on the same root costs
more with every bar, so the song cannot settle on one chord.  Two ways to name "the
same chord":

  spelling  exact symbols.  Cmaj7 and C are different, so the model is free to
            recolour a chord; the result stays in the key.
  root      root pitch class.  C, Cmaj7 and C/E are one chord, so the model has
            to move somewhere new, and borrowed chords appear.

A section penalty keeps a new section from opening the way the one before it did: the
n-th chord a section moves to may not be the n-th chord the previous section moved to,
for its first few chords.  Nothing is forbidden outright and no chord is chosen: it only
costs the planner logits to copy the opening, so a chorus has to find its own way in.

A structure can be followed exactly.  Given the section names the lyrics asked for, in order, the
node steers only the name the planner writes after a "%" comment: the first section must be the first
name, the second the second, and once the list is used no further "%" comment may start, and the plan may not
end until every section has begun and the last has some chords.  It does not write the sections for
the planner or decide when one begins.

An optional bonus favours roots outside the key from the score's K: line, only on
a change of chord and only while few recent chords are already outside, so the
song cannot settle on an out-of-key chord.

The node wraps comfy.text_encoders.yue2.distribution for the length of one
generation and restores it afterwards.  With strength 0 and no bonus, its output is
identical to the stock YuE2 Generate ABC node.
"""
import collections
import contextlib
import re

import comfy.text_encoders.yue2 as yue2

NOTE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
HEADER = re.compile(r"^[A-Za-z]:")
FOLLOW_LAST_CHORDS = 4  # chord symbols the last section needs before the plan may end
FOLLOW_BOOST = 50.0     # logits added to the tokens that spell the section the structure asks for next
SECTION_LINE = re.compile(r"^%\s*([A-Za-z][\w -]*?)\s*$")
KEY_LINE = re.compile(r"^K:\s*([A-G][#b]?)(m?)", re.M)
MAJOR_STEPS = {0, 2, 4, 5, 7, 9, 11}
MINOR_STEPS = {0, 2, 3, 5, 7, 8, 10}
_VOCAB = {}


def root_of(text):
    """Pitch class of a chord's root, or None.  A lone letter counts as the natural."""
    if not text or text[0] not in NOTE:
        return None
    pc = NOTE[text[0]]
    if text[1:2] == "#":
        pc += 1
    elif text[1:2] == "b":
        pc -= 1
    return pc % 12


def vocabulary(clip):
    """Decoded text of every ABC-phase token, computed once per tokenizer."""
    raw = clip.tokenizer.tokenizer
    if id(raw) not in _VOCAB:
        _VOCAB.clear()
        _VOCAB[id(raw)] = raw.decode_batch([[i] for i in range(yue2.EOD)], skip_special_tokens=False)
    return _VOCAB[id(raw)]


def walk(text, line, partial):
    """Advance the chord-symbol state over text.  Quotes on header lines (V: name="...")
    are not chords.  Returns (line, partial, completed symbols)."""
    done = []
    for ch in text:
        if ch == "\n":
            line, partial = "", None
            continue
        if partial is None:
            if ch == '"' and not HEADER.match(line):
                partial = ""
        elif ch == '"':
            done.append(partial)
            partial = None
        else:
            partial += ch
        line += ch
    return line, partial, done


class HarmonyTracker:
    def __init__(self, vocab, mode="root", strength=0.0, window=16, hold_limit=8,
                 outside_bonus=0.0, outside_limit=0.25, candidates=64, section_strength=0.0, section_open=4,
                 sections=None):
        self.vocab = vocab
        self.mode = mode
        self.strength = strength
        self.hold_limit = hold_limit
        self.outside_bonus = outside_bonus if mode == "root" else 0.0
        self.outside_limit = outside_limit
        self.candidates = candidates
        self.section_strength = section_strength
        self.section_open = section_open
        self.wanted = [name.strip().lower() for name in (sections or []) if name and name.strip()]
        self.section_count = 0   # "% name" comment lines the planner has finished
        self.section_chords = 0  # chord symbols written since the last one
        self._allowed = {}
        self.opening = []        # the roots this section has moved through so far, up to section_open of them
        self.previous = []       # the same for the section before
        self.seen = 0
        self.line = ""
        self.partial = None
        self.changes = collections.deque(maxlen=window)
        self.held = 0            # consecutive chord symbols on the same root, in either mode
        self.last_root = None
        self.head = ""
        self.scale = None
        self.chord_starts = [i for i, t in enumerate(vocab) if t.startswith('"') and t[1:2] in NOTE]

    @property
    def chord_active(self):
        return self.strength > 0 or self.outside_bonus > 0 or self.section_strength > 0

    @property
    def active(self):
        return self.chord_active or bool(self.wanted)

    # ------------------------------------------------------------- following
    def identity(self, symbol):
        return root_of(symbol) if self.mode == "root" else symbol

    def feed(self, history):
        for token in history[self.seen:]:
            text = self.vocab[token] if token < len(self.vocab) else ""
            if self.scale is None and self.mode == "root":
                self.head += text
                key = KEY_LINE.search(self.head)
                if key and "\n" in self.head[key.end():]:
                    steps = MINOR_STEPS if key.group(2) else MAJOR_STEPS
                    self.scale = {(root_of(key.group(1)) + s) % 12 for s in steps}
            self.follow_sections(text)
            self.line, self.partial, done = walk(text, self.line, self.partial)
            for symbol in done:
                root = root_of(symbol)
                if root is None:
                    continue
                self.section_chords += 1
                if len(self.opening) < self.section_open and (not self.opening or self.opening[-1] != root):
                    self.opening.append(root)
                # Holding is counted by root, so respelling a chord (E5, Em, Em7)
                # does not reset the count.
                if root == self.last_root:
                    self.held += 1
                else:
                    self.last_root = root
                    self.held = 1
                ident = self.identity(symbol)
                if not self.changes or self.changes[-1] != ident:
                    self.changes.append(ident)
        self.seen = len(history)

    def follow_sections(self, text):
        """A comment line such as '% chorus' starts a section: what the last one opened with
        becomes what this one must not copy."""
        line = self.line
        for ch in text:
            if ch != "\n":
                line += ch
                continue
            if SECTION_LINE.match(line):
                self.previous, self.opening = self.opening, []
                self.section_count += 1
                self.section_chords = 0
            line = ""

    def section_penalty(self, root):
        """Cost of choosing this root, if it would repeat the previous section's opening at the same place."""
        if not self.section_strength or not self.previous:
            return 0.0
        place = len(self.opening)
        if self.opening and root == self.opening[-1]:
            return 0.0                        # holding the chord already chosen
        if place < len(self.previous) and place < self.section_open and root == self.previous[place]:
            return self.section_strength
        return 0.0

    def outside_share(self):
        if not self.scale or not self.changes:
            return 0.0
        return sum(1 for r in self.changes if r not in self.scale) / len(self.changes)

    # --------------------------------------------------------------- scoring
    def spelling_penalty(self, completed, partial):
        current = self.changes[-1]
        counts = collections.Counter(self.changes)
        total = len(self.changes)
        score = 0.0
        for symbol in completed:
            if root_of(symbol) is not None and symbol != current:
                score += counts[symbol] / total
        if partial and root_of(partial) is not None and not current.startswith(partial):
            score += sum(n for c, n in counts.items() if c.startswith(partial) and c != current) / total
        return self.strength * score

    def hold_penalty(self, root):
        if self.hold_limit and root == self.last_root and self.held >= self.hold_limit:
            return self.strength * (1 + self.held - self.hold_limit) / 4
        return 0.0

    def root_penalty(self, root):
        current = self.changes[-1]
        value = 0.0
        if root == current:
            return self.hold_penalty(root)
        value += self.strength * collections.Counter(self.changes)[root] / len(self.changes)
        if (self.outside_bonus and self.scale is not None and root not in self.scale
                and self.outside_share() < self.outside_limit):
            value -= self.outside_bonus
        return value

    def bias(self, logits):
        """Logit adjustments for this step, as (ids, values): the chords' and the structure's together."""
        chords = self.chord_bias(logits) if self.chord_active else None
        follow = self.follow_bias(logits) if self.wanted else None
        if not follow:
            return chords
        if not chords:
            return follow
        merged = dict(zip(*chords))
        for token, value in zip(*follow):
            merged[token] = merged.get(token, 0.0) + value
        return list(merged), list(merged.values())

    def tokens_spelling(self, remaining):
        """Every token that could be the next piece of the text `remaining`, computed once for each."""
        if remaining not in self._allowed:
            self._allowed[remaining] = [i for i, text in enumerate(self.vocab) if text and remaining.startswith(text)]
        return self._allowed[remaining]

    def follow_bias(self, logits):
        """Hold the planner to the structure: after a "%" it may write only the next section's name, and
        once every section has been written it may not start another."""
        found = self.follow_line(logits)
        # The plan may not end with sections still to write, or before the last has some chords.
        end = getattr(yue2, "ABC_END", None)
        if end is not None and (self.section_count < len(self.wanted) or self.section_chords < FOLLOW_LAST_CHORDS):
            ids, values = (list(found[0]), list(found[1])) if found else ([], [])
            if end not in ids:
                ids.append(end)
                values.append(FOLLOW_BOOST)
            return ids, values
        return found

    def follow_line(self, logits):
        line = self.line
        if line.startswith("%%"):
            return None
        if line == "":
            if self.section_count < len(self.wanted):
                return None
            top = logits[0, :yue2.EOD].topk(self.candidates).indices.tolist()
            banned = [t for t in top if self.vocab[t].startswith("%")]
            return (banned, [FOLLOW_BOOST] * len(banned)) if banned else None
        if not line.startswith("%") or self.section_count >= len(self.wanted):
            return None
        target = " " + self.wanted[self.section_count]
        content = line[1:]
        if not target.startswith(content):
            return None                       # off the structure already (a comment that is not a section name)
        allowed = self.tokens_spelling(target[len(content):] + "\n")
        return (allowed, [-FOLLOW_BOOST] * len(allowed)) if allowed else None

    def chord_bias(self, logits):
        """Logit adjustments for the chords.  Only the top candidates
        are scored: a penalty only lowers a token, so one outside them could not be
        sampled either way.  A bonus can raise one, so chord openings are added."""
        if not self.chord_active or not self.changes:
            return None
        top = logits[0, :yue2.EOD].topk(self.candidates).indices.tolist()
        if self.outside_bonus and self.partial is None and any('"' in self.vocab[t] for t in top):
            top = list(dict.fromkeys(top + self.chord_starts))
        before = self.partial or ""
        out_ids, values = [], []
        for token in top:
            text = self.vocab[token]
            if self.partial is None and '"' not in text:
                continue
            _, partial, done = walk(text, self.line, self.partial)
            if self.mode == "spelling":
                if not done and not partial:
                    continue
                value = self.spelling_penalty(done, partial)
                symbol = done[0] if done else partial
                if len(before) <= 1 and root_of(symbol) is not None:
                    value += self.hold_penalty(root_of(symbol)) + self.section_penalty(root_of(symbol))
            else:
                symbol = done[0] if done else partial
                # The root is decided at its letter, and at the step after it, where
                # an accidental or anything else settles sharp, flat or natural.
                if not symbol or root_of(symbol) is None or len(before) >= 2:
                    continue
                value = self.root_penalty(root_of(symbol)) + self.section_penalty(root_of(symbol))
            if value:
                out_ids.append(token)
                values.append(value)
        return (out_ids, values) if out_ids else None


@contextlib.contextmanager
def steering(tracker):
    import torch

    original = yue2.distribution

    def distribution(logits, history, step, phase, *args, **kwargs):
        if phase == "abc":
            tracker.feed(history)
            adjust = tracker.bias(logits)
            if adjust:
                logits = logits.clone()
                ids = torch.tensor(adjust[0], device=logits.device, dtype=torch.long)
                logits[..., ids] -= torch.tensor(adjust[1], device=logits.device, dtype=logits.dtype)
        return original(logits, history, step, phase, *args, **kwargs)

    yue2.distribution = distribution
    try:
        yield
    finally:
        yue2.distribution = original


class YuE2GenerateABCHarmony:
    CATEGORY = "model/conditioning/yue2"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("abc",)
    FUNCTION = "execute"
    DESCRIPTION = "YuE2 Generate ABC with control over how predictable the chord progression is."

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "clip": ("CLIP",),
            "style": ("STRING", {"multiline": True}),
            "lyrics": ("STRING", {"multiline": True}),
            "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
            "mode": (["full", "melody"],),
            "max_abc_tokens": ("INT", {"default": 8192, "min": 1, "max": 20000}),
            "temperature": ("FLOAT", {"default": 0.7, "min": 0.0, "max": 5.0, "step": 0.05}),
            "top_p": ("FLOAT", {"default": 0.9, "min": 0.01, "max": 1.0, "step": 0.01}),
            "top_k": ("INT", {"default": 30, "min": 1, "max": 32768}),
            "repetition_penalty": ("FLOAT", {"default": 1.005, "min": 0.01, "max": 10.0, "step": 0.005}),
            "penalty_window": ("INT", {"default": 100, "min": 1, "max": 20000}),
            "chord_identity": (["root", "spelling"], {"tooltip": "root: C, Cmaj7 and C/E count as one chord. spelling: exact symbols."}),
            "chord_strength": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 64.0, "step": 0.5,
                                         "tooltip": "Logits taken from a chord for its share of recent chord changes. 0 is off."}),
            "chord_window": ("INT", {"default": 16, "min": 1, "max": 512, "tooltip": "Recent chord changes remembered."}),
            "hold_limit": ("INT", {"default": 8, "min": 0, "max": 64, "tooltip": "Bars one root may hold before staying on it costs. 0 is no limit."}),
            "outside_bonus": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 20.0, "step": 0.5,
                                        "tooltip": "Root mode: logits added to a change to a root outside the key."}),
            "outside_limit": ("FLOAT", {"default": 0.25, "min": 0.0, "max": 1.0, "step": 0.05,
                                        "tooltip": "The bonus stops while this share of recent chords is already outside the key."}),
        }, "optional": {
            "section_strength": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 64.0, "step": 0.5,
                                           "tooltip": "Logits taken from a chord that would repeat how the previous section opened. 0 is off."}),
            "section_open": ("INT", {"default": 4, "min": 1, "max": 16,
                                     "tooltip": "How many of a section's first chords are compared with the previous section's."}),
            "follow_sections": ("STRING", {"default": "", "tooltip": "Section names in order, separated by commas. The plan may write only these, in this order. Empty is off."}),
        }}

    def execute(self, clip, style, lyrics, seed, mode, max_abc_tokens, temperature, top_p, top_k, repetition_penalty,
                penalty_window, chord_identity, chord_strength, chord_window, hold_limit, outside_bonus, outside_limit,
                section_strength=0.0, section_open=4, follow_sections=""):
        tokens = clip.tokenize(style, lyrics=lyrics, cot=mode, seed=seed, max_tokens=max_abc_tokens, penalty_window=penalty_window)
        tracker = HarmonyTracker(vocabulary(clip), chord_identity, chord_strength, chord_window, hold_limit,
                                 outside_bonus, outside_limit, candidates=max(64, top_k),
                                 section_strength=section_strength, section_open=section_open,
                                 sections=[part for part in str(follow_sections or "").split(",") if part.strip()])
        generate = lambda: clip.generate(tokens, max_length=max_abc_tokens, temperature=temperature, top_p=top_p,
                                         top_k=top_k, repetition_penalty=repetition_penalty, seed=seed)
        if tracker.active:
            with steering(tracker):
                ids = generate()
        else:
            ids = generate()
        return (clip.decode(ids),)


class Yue2PeakGuard:
    """Keeps a render from clipping when it is saved.

    The decoder can overshoot full scale, and the save then turns the floating point audio
    into 16-bit, which flattens every peak past it.  Here the audio is still floating point,
    so a limiter turns it down around the peaks that would clip, and only there; anything
    that stays under the ceiling passes through untouched.  The second output says what the
    peak was."""

    CATEGORY = "audio"
    RETURN_TYPES = ("AUDIO", "STRING")
    RETURN_NAMES = ("audio", "info")
    FUNCTION = "execute"

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "audio": ("AUDIO",),
            "ceiling_db": ("FLOAT", {"default": -0.5, "min": -12.0, "max": 0.0, "step": 0.1,
                                     "tooltip": "The highest a peak may reach, in dB below full scale."}),
            "window_ms": ("FLOAT", {"default": 8.0, "min": 1.0, "max": 50.0, "step": 1.0,
                                    "tooltip": "How far either side of a peak the gain dips."}),
        }}

    def execute(self, audio, ceiling_db, window_ms=8.0):
        import math

        from . import peak as limiter

        wave = audio["waveform"]
        top = float(wave.abs().max()) if wave.numel() else 0.0
        ceiling = 10 ** (ceiling_db / 20)
        seen = f"peak {20 * math.log10(top):.2f} dBFS" if top > 0 else "silent"
        if top <= ceiling:
            return (audio, seen)
        window = int(audio["sample_rate"] * window_ms / 1000)
        limited = limiter.limit(wave, ceiling, window)
        return ({**audio, "waveform": limited},
                f"{seen}, limited to {ceiling_db:.1f} dBFS ({window_ms:g} ms window)")


# What the engine tells the app about itself: see watch.py. Never at the cost of the node.
try:
    from . import watch
    watch.install()
except Exception:  # noqa: BLE001
    pass

NODE_CLASS_MAPPINGS = {"YuE2GenerateABCHarmony": YuE2GenerateABCHarmony, "Yue2PeakGuard": Yue2PeakGuard}
NODE_DISPLAY_NAME_MAPPINGS = {"YuE2GenerateABCHarmony": "YuE2 Generate ABC (harmony)",
                              "Yue2PeakGuard": "Yeufonic peak guard"}

# Stem separation needs demucs, which an engine built before it was added does not have: the node
# is simply not there then, and the app uses its own CPU separation.
try:
    import demucs  # noqa: F401

    from .separate import Yue2Separate

    NODE_CLASS_MAPPINGS["Yue2Separate"] = Yue2Separate
    NODE_DISPLAY_NAME_MAPPINGS["Yue2Separate"] = "Yeufonic stem separation (Demucs)"
except Exception:  # noqa: BLE001
    pass

# Hearing a vocal's words on the GPU needs faster-whisper and CTranslate2 with a CUDA device; without them the node
# is not there and the app's own CPU Whisper does it.
try:
    from . import hear as _hear

    if _hear.usable():
        NODE_CLASS_MAPPINGS["Yue2Hear"] = _hear.Yue2Hear
        NODE_DISPLAY_NAME_MAPPINGS["Yue2Hear"] = "Yeufonic lyric hearing (Whisper)"
except Exception:  # noqa: BLE001
    pass
