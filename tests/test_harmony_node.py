"""The engine's yue2_harmony node: chord tracking and scoring, without ComfyUI."""
import importlib.util
import sys
import types
from pathlib import Path

import pytest

NODE = Path(__file__).resolve().parents[1] / "engine" / "custom_nodes" / "yue2_harmony" / "__init__.py"


@pytest.fixture(scope="module")
def harmony():
    stub = types.ModuleType("comfy.text_encoders.yue2")
    stub.EOD = 1000
    stub.ABC_END = 1001
    stub.distribution = lambda *a, **k: None
    saved = {k: sys.modules.get(k) for k in ("comfy", "comfy.text_encoders", "comfy.text_encoders.yue2")}
    sys.modules.update({"comfy": types.ModuleType("comfy"), "comfy.text_encoders": types.ModuleType("comfy.text_encoders"),
                        "comfy.text_encoders.yue2": stub})
    spec = importlib.util.spec_from_file_location("yue2_harmony_under_test", NODE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    yield module
    for key, value in saved.items():
        if value is None:
            sys.modules.pop(key, None)
        else:
            sys.modules[key] = value


VOCAB = ['K:D\n', 'V: Vocal name="Vocal"\n', '"D"', 'z16|', '"Gmaj7"', '"A"', '"Bm"', '"G"', '"Gsus2"',
         '"Bb"', '"C"', '"F', '#m"', '"D', '"', '\n', '"Dsus2"']
IDS = {text: i for i, text in enumerate(VOCAB)}


def feed(harmony, mode, symbols, **kw):
    """A tracker that has read the key line, a header with a quoted name, then symbols."""
    t = harmony.HarmonyTracker(VOCAB, mode, kw.pop("strength", 8.0), **kw)
    history = [IDS['K:D\n'], IDS['V: Vocal name="Vocal"\n']]
    for symbol in symbols:
        history += [IDS[symbol], IDS['z16|']]
    t.feed(history)
    return t


def value(harmony, t, text):
    """What choosing text next would cost (negative: a bonus)."""
    _, partial, done = harmony.walk(text, t.line, t.partial)
    if t.mode == "spelling":
        symbol = done[0] if done else partial
        return t.spelling_penalty(done, partial) + t.hold_penalty(harmony.root_of(symbol))
    return t.root_penalty(harmony.root_of(done[0] if done else partial))


LOOP = ['"D"', '"Gmaj7"', '"A"', '"D"']


def test_header_quotes_are_not_chords(harmony):
    assert list(feed(harmony, "spelling", LOOP).changes) == ["D", "Gmaj7", "A", "D"]


def test_spelling_mode_lets_a_chord_be_respelled(harmony):
    t = feed(harmony, "spelling", LOOP)
    assert value(harmony, t, '"Gmaj7"') == 8.0 * 1 / 4
    assert value(harmony, t, '"Gsus2"') == 0        # a new spelling counts as a new chord
    assert value(harmony, t, '"D"') == 0            # holding the current chord is free


def test_root_mode_treats_spellings_as_one_chord(harmony):
    t = feed(harmony, "root", LOOP)
    assert value(harmony, t, '"Gsus2"') == value(harmony, t, '"Gmaj7"') == 8.0 * 1 / 4
    assert value(harmony, t, '"Bm"') == 0


def test_root_mode_limits_holding(harmony):
    t = feed(harmony, "root", ['"A"', '"D"', '"D"', '"D"'], hold_limit=2)
    assert t.held == 3
    assert value(harmony, t, '"D"') == 8.0 * (1 + 3 - 2) / 4


def test_spelling_mode_limits_holding_by_root(harmony):
    t = feed(harmony, "spelling", ['"A"', '"D"', '"D"', '"D"'], hold_limit=2)
    assert t.held == 3
    assert value(harmony, t, '"D"') == 8.0 * (1 + 3 - 2) / 4
    # A respelling of the same root does not escape the limit: it keeps the count.
    respelled = feed(harmony, "spelling", ['"A"', '"D"', '"D"', '"Dsus2"'], hold_limit=2)
    assert respelled.held == 3


def test_outside_bonus_only_on_a_change_and_below_the_limit(harmony):
    t = feed(harmony, "root", LOOP, outside_bonus=3.0, outside_limit=0.25)
    assert t.scale == {1, 2, 4, 6, 7, 9, 11}        # D major
    assert value(harmony, t, '"Bb"') == -3.0        # a change to a root outside the key
    held = feed(harmony, "root", ['"D"', '"C"'], outside_bonus=3.0)
    assert value(harmony, held, '"C"') == 0         # holding an outside chord earns nothing
    busy = feed(harmony, "root", ['"D"', '"C"', '"D"'], outside_bonus=3.0, outside_limit=0.25)
    assert value(harmony, busy, '"Bb"') == 0        # a third of recent chords are already outside


def test_an_accidental_after_the_letter_decides_the_root(harmony):
    t = harmony.HarmonyTracker(VOCAB, "root", 8.0, outside_bonus=3.0)
    t.feed([IDS['K:D\n'], IDS['"D"'], IDS['z16|'], IDS['"F']])   # the planner has written "F
    assert t.partial == "F"
    assert value(harmony, t, '#m"') == 0      # F#m: F# is in D major, so no bonus
    assert value(harmony, t, '"') == -3.0     # F natural is outside it


def test_off_is_inactive(harmony):
    assert not harmony.HarmonyTracker(VOCAB, "root", 0.0).active
    assert not harmony.HarmonyTracker(VOCAB, "spelling", 0.0, outside_bonus=5.0).active   # the bonus is root mode only


SECTION_VOCAB = VOCAB + ['% verse\n', '% chorus\n', '"Em"']
SECTION_IDS = {text: i for i, text in enumerate(SECTION_VOCAB)}


def follow(harmony, parts, **kw):
    t = harmony.HarmonyTracker(SECTION_VOCAB, "root", kw.pop("strength", 0.0), section_strength=kw.pop("section_strength", 6.0), **kw)
    t.feed([SECTION_IDS[p] for p in parts])
    return t


VERSE = ['K:D\n', '% verse\n', 'V: Vocal name="Vocal"\n', '"D"', 'z16|', '"Gmaj7"', 'z16|', '"A"', 'z16|', '"Bm"', 'z16|', '\n']


def test_a_section_may_not_open_the_way_the_last_one_did(harmony):
    t = follow(harmony, VERSE + ['% chorus\n', 'V: Vocal name="Vocal"\n'])
    assert t.previous == [2, 7, 9, 11]                  # D, G, A, B
    assert t.section_penalty(harmony.root_of("D")) == 6.0      # the first chord, as before
    assert t.section_penalty(harmony.root_of("G")) == 0.0      # a chord from the verse, at a different place
    t = follow(harmony, VERSE + ['% chorus\n', 'V: Vocal name="Vocal"\n', '"G"', 'z16|'])
    assert t.opening == [7]
    assert t.section_penalty(harmony.root_of("G")) == 0.0      # holding what it chose
    assert t.section_penalty(harmony.root_of("G") + 0) == 0.0
    assert t.section_penalty(harmony.root_of("A")) == 0.0      # the verse's third chord, at the second place
    t = follow(harmony, VERSE + ['% chorus\n', 'V: Vocal name="Vocal"\n', '"A"', 'z16|'])
    assert t.section_penalty(harmony.root_of("G")) == 6.0      # the verse's second chord, at the second place


def test_the_penalty_ends_after_the_chords_compared(harmony):
    t = follow(harmony, VERSE + ['% chorus\n', 'V: Vocal name="Vocal"\n', '"A"', 'z16|', '"Em"', 'z16|'], section_open=2)
    assert t.opening == [9, 4]
    assert t.section_penalty(harmony.root_of("A")) == 0.0      # past the two compared, nothing is penalised


def test_the_first_section_has_nothing_to_copy_and_off_is_off(harmony):
    t = follow(harmony, ['K:D\n', '% verse\n', 'V: Vocal name="Vocal"\n', '"D"', 'z16|'])
    assert t.previous == [] and t.section_penalty(harmony.root_of("D")) == 0.0
    t = follow(harmony, VERSE + ['% chorus\n', 'V: Vocal name="Vocal"\n'], section_strength=0.0)
    assert not t.active and t.section_penalty(harmony.root_of("D")) == 0.0


FOLLOW_VOCAB = ['\n', '%', ' verse', ' chorus', ' bridge', ' ver', 'se', '|\n', 'z16|', '"D"', ' pre', '-', 'chorus', '%%', 'V', ': Vocal']
FOLLOW_IDS = {text: i for i, text in enumerate(FOLLOW_VOCAB)}


class Logits:
    """Just enough of a tensor: topk over a row of scores."""
    def __init__(self, n):
        self.n = n

    def __getitem__(self, key):
        return self

    def topk(self, k):
        import types
        return types.SimpleNamespace(indices=types.SimpleNamespace(tolist=lambda: list(range(min(k, self.n)))))


def follower(harmony, parts, sections):
    t = harmony.HarmonyTracker(FOLLOW_VOCAB, "root", 0.0, sections=sections)
    t.feed([FOLLOW_IDS[p] for p in parts])
    return t


def test_after_a_percent_only_the_next_sections_name_is_allowed(harmony):
    t = follower(harmony, ['%'], ["verse", "chorus"])
    ids, values = t.follow_line(Logits(len(FOLLOW_VOCAB)))
    assert {FOLLOW_VOCAB[i] for i in ids} == {' ver', ' verse'} or {FOLLOW_VOCAB[i] for i in ids} >= {' verse'}
    assert FOLLOW_IDS[' chorus'] not in ids and FOLLOW_IDS[' bridge'] not in ids
    assert all(v < 0 for v in values)                   # a bonus: logits go up
    t = follower(harmony, ['%', ' verse', '\n', 'z16|', '|\n', '%'], ["verse", "chorus"])
    ids, _ = t.follow_line(Logits(len(FOLLOW_VOCAB)))
    assert FOLLOW_IDS[' chorus'] in ids and FOLLOW_IDS[' verse'] not in ids      # the second section is the chorus


def test_a_name_is_finished_with_a_newline_and_a_longer_name_is_spelt_out(harmony):
    t = follower(harmony, ['%', ' verse'], ["verse"])
    ids, _ = t.follow_line(Logits(len(FOLLOW_VOCAB)))
    assert [FOLLOW_VOCAB[i] for i in ids] == ['\n']                                # the name is whole: only the line's end
    t = follower(harmony, ['%', ' pre'], ["pre-chorus"])
    ids, _ = t.follow_line(Logits(len(FOLLOW_VOCAB)))
    assert FOLLOW_IDS['-'] in ids and FOLLOW_IDS['chorus'] not in ids               # a hyphen first


def test_once_the_structure_is_used_no_more_sections_may_start(harmony):
    t = follower(harmony, ['%', ' verse', '\n', 'z16|', '|\n'], ["verse"])
    ids, values = t.follow_line(Logits(len(FOLLOW_VOCAB)))
    assert {FOLLOW_VOCAB[i] for i in ids} == {'%', '%%'} and all(v > 0 for v in values)     # a penalty on every comment opener
    t = follower(harmony, ['%', ' verse', '\n', 'z16|', '|\n'], ["verse", "chorus"])
    assert t.follow_line(Logits(len(FOLLOW_VOCAB))) is None                         # more to come: the planner decides when


def test_a_line_that_is_not_a_section_comment_is_left_alone(harmony):
    t = follower(harmony, ['V', ': Vocal'], ["verse"])
    assert t.follow_line(Logits(len(FOLLOW_VOCAB))) is None
    t = follower(harmony, ['%%'], ["verse"])
    assert t.follow_line(Logits(len(FOLLOW_VOCAB))) is None
    assert follower(harmony, [], []).active is False and follower(harmony, [], ["verse"]).active is True


def test_the_plan_may_not_end_before_the_structure_is_written(harmony):
    t = follower(harmony, ['%', ' verse', '\n', 'z16|', '"D"', 'z16|'], ["verse", "chorus"])
    ids, values = t.follow_bias(Logits(len(FOLLOW_VOCAB)))
    assert 1001 in ids and values[ids.index(1001)] > 0                         # the end of the plan is penalised: a chorus is still to come
    t = follower(harmony, ['%', ' verse', '\n', '%', ' chorus', '\n'], ["verse", "chorus"])
    ids, values = t.follow_bias(Logits(len(FOLLOW_VOCAB)))
    assert 1001 in ids                                                            # every section has begun, but the last has no chords yet
    t = follower(harmony, ['%', ' verse', '\n', '%', ' chorus', '\n'] + ['"D"', 'z16|'] * 4, ["verse", "chorus"])
    got = t.follow_bias(Logits(len(FOLLOW_VOCAB)))
    assert got is None or 1001 not in got[0]                                     # all written, the last has chords: it may end
