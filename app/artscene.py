"""A scene for a take's picture, made from the take itself with no language model.

Given only a title and style tags, FLUX.2 [klein] draws much the same wide landscape every time: nothing in
the prompt is a thing to draw.  So this picks things out of the song's words and title (a list of nouns that
draw well; people and body parts are left out, as klein draws them badly up close), puts the chief one in a
surreal arrangement, sets it somewhere the style suggests (or a place the words name), and gives it a light,
colours, a medium and a framing.  Every choice is drawn from `rng`, so a new picture is a new scene.
"""
from __future__ import annotations

import random
import re

# Things that draw well as the subject, singular.  Words mostly sung as verbs ("watch", "match", "fall") are left out.
THINGS = """
apple anchor anvil armchair arrow axe balloon banjo basket bath bathtub bell bicycle bird birdcage boat
bone book boot bottle bowl box bucket bus butterfly cabinet cactus cage camera candle canoe car caravan
carousel cassette castle cat chair chandelier chess clock cloud coat coin compass crow crown cup curtain
deer desk diamond dice dog doll door dove dress drum eagle egg envelope feather fence fish flag flower
fork fox frame gate glass globe glove goat guitar hammer harp hat helicopter horse hourglass house ice
jar jukebox kettle key kite knife ladder lamp lantern leaf letter lighthouse lightbulb lion mask
microphone mirror moon moth motorcycle mountain nest net oar owl paintbrush parachute pear pen piano
pillow pipe plane planet pocketwatch radio raven record ribbon ring rocket rope rose sail sailboat
satellite saxophone scissors seashell ship shoe skull snake sofa spoon star statue stone suitcase sun
sunflower swan sword table taxi teacup telephone telescope television tent tiger torch tower toy tractor
train tree trumpet trunk tulip typewriter umbrella van vase violin wagon whale wheel window wine wing
wolf wreath yacht
"""

# Places the words may name: these replace the setting the style would give.
PLACES = {
    "sea": "beside a calm grey sea", "ocean": "at the edge of an open ocean", "beach": "on an empty beach",
    "shore": "on a long empty shore", "harbour": "in a quiet harbour", "harbor": "in a quiet harbour",
    "river": "beside a slow river", "lake": "on the shore of a still lake", "bay": "across a wide bay",
    "desert": "in a wide desert", "field": "in an open field", "meadow": "in a meadow",
    "forest": "in a dark forest", "wood": "in a woodland clearing", "woods": "in a woodland clearing",
    "garden": "in an overgrown garden", "city": "on a city street", "street": "on an empty street",
    "road": "on a long straight road", "highway": "on an empty highway", "motorway": "on an empty motorway",
    "bridge": "on a bridge", "station": "on a deserted railway platform", "platform": "on a deserted railway platform",
    "church": "in an empty church", "chapel": "in an empty chapel", "hotel": "in a long hotel corridor",
    "bar": "in a dim bar", "kitchen": "in a plain kitchen", "bedroom": "in a bare bedroom",
    "roof": "on a rooftop", "rooftop": "on a rooftop", "hill": "on a bare hillside", "valley": "in a valley",
    "island": "on a small island", "pool": "beside an empty swimming pool", "attic": "in a dusty attic",
    "stage": "on an empty stage", "ballroom": "in an empty ballroom", "cliff": "on a cliff edge",
    "airport": "in an empty airport lounge", "school": "in an empty classroom", "prison": "in a bare cell",
}

# Weather and elements the words may name.
WEATHER = {
    "rain": "rain falling", "raining": "rain falling", "storm": "a storm gathering", "thunder": "a storm gathering",
    "lightning": "lightning on the horizon", "snow": "snow falling", "fog": "thick fog", "mist": "low mist",
    "smoke": "drifting smoke", "fire": "small fires burning in the distance", "flame": "small fires burning in the distance",
    "flood": "flood water everywhere", "wind": "everything blown by a strong wind", "ice": "everything frosted with ice",
    "dust": "dust hanging in the air", "ash": "ash drifting down",
}

# Times the words may name, which set the light.
TIMES = {
    "night": "night, lit by a single source", "midnight": "night, lit by a single source",
    "dark": "night, lit by a single source", "moonlight": "moonlight", "dawn": "first light at dawn",
    "morning": "early morning light", "sunrise": "first light at dawn", "sunset": "low sunset light",
    "evening": "dusk light", "dusk": "dusk light", "twilight": "blue twilight", "noon": "flat midday sun",
    "winter": "pale winter light", "summer": "hot summer light", "autumn": "low autumn light",
}

IRREGULAR = {"leaves": "leaf", "wolves": "wolf", "knives": "knife", "shelves": "shelf", "geese": "goose",
             "mice": "mouse", "glasses": "glass", "boxes": "box",
             "torches": "torch", "benches": "bench", "dresses": "dress", "compasses": "compass"}

# A surreal arrangement for the subject.  {a} is the subject with its article ({A} capitalised, {n} bare), {b} a
# second thing ({bn} bare), {where} the setting.
DEVICES_ONE = [
    "{A} floating in mid-air {where}",
    "{A} repeated many times in a long row to the horizon {where}",
    "{A}, half-sunk in still water, {where}",
    "An enormous {n}, many times its real size, {where}",
    "{A} wrapped in white cloth and tied with string, {where}",
    "{A} burning with a calm flame but not consumed, {where}",
    "{A} hanging from a single thin thread {where}",
    "{A} on a white plinth, alone {where}",
    "{A} frozen inside a block of clear ice {where}",
    "{A} made entirely of glass {where}",
    "{A} caught in a single beam of light from above {where}",
    "Two halves of {a} drifting apart {where}",
    "A framed painting of {a} standing on an easel {where}, the painting continuing the view behind it",
    "{A} whose shadow points the wrong way {where}",
    "{A} tethered to the ground by a long rope like a balloon {where}",
    "A tiny figure seen from far off, carrying {a} {where}",
    "{A} sinking slowly into soft sand {where}",
    "{A} trailing a long ribbon of coloured smoke {where}",
    "{A} reflected in a puddle that shows a different sky {where}",
]
DEVICES_TWO = [
    "{A} balanced on top of {b} {where}",
    "{A} casting the shadow of {b} {where}",
    "{A} and {b} facing each other across an empty space {where}",
    "{A} with {b} growing out of it {where}",
    "A long line of {bn}s leading to {a} {where}",
]

# Families of style, by the words that name them: where they are set and their colours.
FAMILIES = [
    ("electronic", "synthwave synth electronic edm techno house trance retrowave vaporwave electro idm darkwave",
     ["in an empty multi-storey car park at night", "in a vast drained swimming pool", "on a wet city street under neon",
      "in a white gallery room", "on a salt flat under a grid of lights"],
     ["magenta and cyan", "neon magenta against deep blue", "chrome and violet"]),
    ("folk", "folk acoustic country americana bluegrass singer-songwriter celtic",
     ["in a wheat field", "on a wooden porch", "beside a railway line in open country", "in a misty woodland clearing",
      "in a farmhouse kitchen"],
     ["ochre, sage and cream", "faded autumn browns", "soft greens and straw yellow"]),
    ("jazz", "jazz blues soul lounge swing bossa gospel motown",
     ["in a smoky empty club", "on a rain-slicked street corner at night", "in a hotel corridor", "in a dim bar with one lamp"],
     ["deep blue and amber", "warm brass and shadow", "midnight blue"]),
    ("metal", "metal doom hardcore thrash sludge industrial",
     ["on a black volcanic shore", "in a ruined cathedral", "on a storm-lit plain", "inside a foundry"],
     ["black, chrome and fire orange", "cold steel grey", "deep red and charcoal"]),
    ("ambient", "ambient drone chill lofi lo-fi downtempo meditative new-age",
     ["over still water in thick fog", "in a white empty room", "on a frozen lake", "at the edge of a calm sea"],
     ["pale grey and blush", "soft white and powder blue", "muted pastels"]),
    ("hiphop", "hip-hop hip hop rap trap drill grime r&b rnb boom-bap",
     ["on a rooftop above the city", "on an empty basketball court at night", "in a tiled underpass",
      "outside a late-night launderette"],
     ["gold and black", "purple dusk", "sodium orange and teal"]),
    ("classical", "classical orchestral cinematic choral baroque symphonic opera piano",
     ["in a grand empty concert hall", "in a formal garden of clipped hedges", "in a marble hall", "on a cliff above the sea"],
     ["ivory and gold", "deep velvet red", "cool silver"]),
    ("psychedelic", "psychedelic prog progressive space krautrock shoegaze",
     ["in a vast desert under two suns", "on an endless chequerboard plain", "inside a mirrored room",
      "on a beach where the sea stands still"],
     ["swirling oranges and purples", "acid green and violet", "sunburst yellow and deep blue"]),
    ("pop", "pop disco funk dance-pop synthpop k-pop j-pop bubblegum",
     ["beside a pastel-tiled swimming pool", "on a beach at noon", "in a glittering empty ballroom",
      "on a candy-coloured suburban street"],
     ["saturated primaries", "fuchsia and turquoise", "sunny yellow and sky blue"]),
    ("tropical", "reggae latin tropical afrobeat afrobeats dancehall salsa cumbia ska",
     ["on a sunlit beach", "in a courtyard of painted walls", "in a market square at dusk"],
     ["sun-bleached turquoise and coral", "warm terracotta and green"]),
    ("rock", "rock indie punk grunge alternative garage emo britpop post-punk",
     ["in an empty car park", "in a derelict hall", "on a motel balcony", "on a suburban street at dusk",
      "in a bare rehearsal room"],
     ["washed-out reds and greys", "black and white with one red accent", "sodium orange"]),
]
GENERAL = (["in a wide open landscape", "in an empty room with tall windows", "on a long empty shore",
            "on a city rooftop", "in a quiet courtyard", "on a salt flat"],
           ["muted earth colours", "cool blues and greys", "warm faded colours"])

MOODS = [
    ("melancholic melancholy sad wistful lonely somber sombre haunting bittersweet mournful nostalgic",
     ["overcast light", "dusk light", "cold blue-hour light"]),
    ("upbeat happy joyful euphoric energetic bright uplifting playful cheerful",
     ["bright midday sun", "golden late-afternoon sunlight"]),
    ("dreamy ethereal hazy floating hypnotic", ["hazy soft light", "moonlight"]),
    ("aggressive angry intense heavy raw furious", ["harsh stormy light", "hard flash at night"]),
    ("romantic warm love tender intimate sensual", ["warm low sunset light", "candlelight"]),
    ("dark ominous brooding menacing", ["low dramatic light under heavy cloud", "night, lit by a single source"]),
]
LIGHTS = ["soft overcast light", "low raking sunlight", "clear morning light", "late-afternoon light", "blue twilight"]

MEDIA = ["infrared film photograph", "double-exposure photograph", "hand-tinted photograph",
         "cross-processed 35mm film photograph", "black-and-white photograph with a single colour picked out",
         "airbrushed painting", "photo collage with clean cut edges", "large-format colour photograph",
         "faded instant photograph", "gouache painting"]
FRAMINGS = ["wide shot, the subject small in the frame", "symmetrical, centred composition",
            "low horizon under a big sky", "seen from high above", "straight-on, still and formal"]

# Things to draw when the words and title name none, by family.
STAND_INS = {
    "electronic": ["television", "satellite", "cassette", "lightbulb"], "folk": ["chair", "lantern", "boot", "kettle"],
    "jazz": ["saxophone", "lamp", "telephone", "piano"], "metal": ["anvil", "crown", "sword", "raven"],
    "ambient": ["feather", "stone", "glass", "cloud"], "hiphop": ["crown", "microphone", "car", "record"],
    "classical": ["violin", "chandelier", "statue", "harp"], "psychedelic": ["eye-shaped mirror", "planet", "door", "egg"],
    "pop": ["balloon", "cherry-red telephone", "umbrella", "record"], "tropical": ["sun hat", "boat", "radio", "flower"],
    "rock": ["guitar", "motorcycle", "amplifier", "door"],
}
GENERAL_STAND_INS = ["chair", "door", "umbrella", "suitcase", "red ball", "piano", "ladder", "mirror"]

_THINGS = set(THINGS.split())
_WORD = re.compile(r"[a-z][a-z'\-]*")


def _a(noun: str) -> str:
    return ("an " if noun[0] in "aeiou" else "a ") + noun


def _singular(word: str) -> str:
    if word in IRREGULAR:
        return IRREGULAR[word]
    if word in _THINGS or word in PLACES or word in WEATHER or word in TIMES:
        return word
    if word.endswith("ies") and word[:-3] + "y" in _THINGS:
        return word[:-3] + "y"
    if word.endswith("es") and word[:-2] in _THINGS:
        return word[:-2]
    if word.endswith("s") and word[:-1] in _THINGS | set(PLACES):
        return word[:-1]
    return word


def _sung_lines(lyrics: str) -> list[str]:
    out = []
    for line in (lyrics or "").splitlines():
        line = line.strip()
        if line and not re.fullmatch(r"\[[^\]]*\]", line) and not line.startswith("%"):
            out.append(line)
    return out


def _scores(title: str, lyrics: str) -> dict[str, float]:
    """Each word of the title and the words, scored: more for the title, the opening lines and a repeat."""
    scores: dict[str, float] = {}
    whole_title = title.strip().lower()
    for word in _WORD.findall(title.lower()):
        word = _singular(word)
        if word != whole_title:              # a one-word title is taken out of what klein draws: not the subject
            scores[word] = scores.get(word, 0) + 3
    for i, line in enumerate(_sung_lines(lyrics)):
        weight = 2.0 if i < 4 else 1.0
        for word in _WORD.findall(line.lower()):
            word = _singular(word)
            scores[word] = scores.get(word, 0) + weight
    return scores


def _top(scores: dict[str, float], among, rng: random.Random, k: int = 3) -> list[str]:
    """The best scored words of a kind, the first picked at random among the top k, then the rest in order."""
    found = sorted((w for w in scores if w in among), key=lambda w: -scores[w])
    if not found:
        return []
    first = rng.choice(found[:k])
    return [first] + [w for w in found if w != first]


def family_of(style: str) -> str | None:
    text = " " + re.sub(r"[,/]", " ", (style or "").lower()) + " "
    best, hits = None, 0
    for name, words, _, _ in FAMILIES:
        n = sum(1 for w in words.split() if f" {w} " in text or (len(w) > 4 and w in text))
        if n > hits:
            best, hits = name, n
    return best


def take_scene(title: str, style: str, lyrics: str, rng: random.Random | None = None) -> str:
    """One scene for the picture, a few short sentences, from the take's title, style and words."""
    rng = rng or random.Random()
    scores = _scores(title or "", lyrics or "")
    family = family_of(style)
    settings, palettes = next(((s, p) for n, _, s, p in FAMILIES if n == family), GENERAL)

    things = _top(scores, _THINGS, rng)
    if not things:
        things = [rng.choice(STAND_INS.get(family, GENERAL_STAND_INS))]
    places = _top(scores, PLACES, rng, k=2)
    where = PLACES[places[0]] if places else rng.choice(settings)

    subject = things[0]
    if len(things) > 1 and rng.random() < 0.4:
        device = rng.choice(DEVICES_TWO)
        second = things[1]
    else:
        device = rng.choice(DEVICES_ONE)
        second = ""
    arranged = device.format(A=_a(subject).capitalize(), a=_a(subject), n=subject, b=_a(second) if second else "",
                             bn=second, where=where)

    lines = [arranged.rstrip(",") + "."]
    weather = _top(scores, WEATHER, rng, k=2)
    if weather:
        lines.append(WEATHER[weather[0]].capitalize() + ".")
    times = _top(scores, TIMES, rng, k=2)
    lowered = (style or "").lower()
    mood_light = next((lights for words, lights in MOODS if any(w in lowered for w in words.split())), None)
    light = TIMES[times[0]] if times else rng.choice(mood_light or LIGHTS)
    lines.append(f"{light.capitalize()}, {rng.choice(palettes)}.")
    lines.append(f"{rng.choice(MEDIA).capitalize()}, {rng.choice(FRAMINGS)}.")
    return " ".join(lines)
