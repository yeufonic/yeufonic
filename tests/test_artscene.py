"""The scene for a take's picture made from the take itself, with no language model."""
import random

from app import artscene, artwork

WORDS = "[Verse]\nA lantern on the harbour wall\nThe rain comes down on every train\n\n[Chorus]\nCarry the lantern home"


def scene(title="", style="", lyrics="", seed=1):
    return artscene.take_scene(title, style, lyrics, random.Random(seed))


def test_the_subject_comes_from_the_words():
    for seed in range(20):
        text = scene("Night crossing", "folk, acoustic guitar", WORDS, seed)
        assert "lantern" in text or "train" in text
        assert "Rain falling." in text


def test_a_place_in_the_words_is_where_it_is_set():
    for seed in range(20):
        assert "in a quiet harbour" in scene("", "synthwave", WORDS, seed)


def test_with_no_place_named_the_style_sets_it():
    settings = next(s for n, _, s, _ in artscene.FAMILIES if n == "electronic")
    for seed in range(20):
        assert any(where in scene("", "synthwave, gated drums", "A lantern in the dark", seed) for where in settings)


def test_a_song_that_names_nothing_still_has_something_to_draw():
    stand_ins = artscene.STAND_INS["jazz"]
    for seed in range(20):
        text = scene("Untitled", "smoky jazz, upright bass", "", seed)
        assert any(thing in text for thing in stand_ins)


def test_people_are_never_the_subject():
    text = scene("", "pop", "The man and the woman, her eyes, his hands, my heart, the girl", 3)
    for word in ("man", "woman", "eyes", "hands", "heart", "girl"):
        assert f" {word}" not in text.lower().split(".")[0]


def test_a_one_word_title_is_not_the_subject():
    """klein's prompt has the title taken out, which would leave the scene without its subject."""
    for seed in range(20):
        assert "piano" not in scene("Piano", "rock", "", seed).lower().split(".")[0]


def test_a_new_picture_is_a_new_scene():
    assert len({scene("", "rock", WORDS, seed) for seed in range(10)}) > 5


def test_the_take_description_carries_a_scene_when_nothing_wrote_one():
    take = {"title": "Night crossing", "style": "folk", "lyrics": WORDS}
    assert 'visual scene:\n"' in artwork.take_description(take)
    assert 'visual scene:\n"A pear on a crate."' in artwork.take_description(take, scene="A pear on a crate.")


def test_klein_is_no_longer_told_to_draw_a_landscape():
    assert "landscape" not in artwork.klein_request("A chair in a quiet courtyard.")



def test_klein_is_given_the_scene_alone():
    """The style's instruments and voices made klein draw players, whose limbs it gets wrong."""
    take = {"title": "Night crossing", "style": "power pop, jangly electric guitar, punchy rock drums, male vocal",
            "lyrics": WORDS}
    drawn = artwork.klein_request(artwork.drawing_request(artwork.take_description(take, scene="A chair."), take), take)
    assert "A chair." in drawn
    assert "guitar" not in drawn and "vocal" not in drawn and "cover style" not in drawn
    # an external image model, which draws people well, keeps the whole style
    assert "male vocal" in artwork.drawing_request(artwork.take_description(take, scene="A chair."), take)
