"""How much of each song a LoRA trains on, worked out from the card."""
from app import trainsize

GB = trainsize.GB
LONG = [120.0, 250.0, 330.0, 420.0]      # seconds; the longest is seven minutes


def card(free_gb, held_gb=0.0):
    return {"vram_free": free_gb * GB, "engine_vram": held_gb * GB}


def test_a_context_is_the_codes_and_the_prefix_in_whole_steps():
    assert trainsize.tokens_for(210) == 7168             # 5,250 codes + 1,536, up to a multiple of 512
    assert trainsize.tokens_for(330) == 10240
    assert trainsize.clock(5.5) == "5:30" and trainsize.clock(3.5) == "3:30"


def test_a_16_gb_card_takes_more_than_the_default_and_a_busier_one_less():
    roomy = trainsize.choose(card(14.7), LONG)
    assert roomy["minutes"] == 5.5 and roomy["tokens"] == 10240 and not roomy["tight"]
    assert roomy["whole"] == 3 and roomy["songs"] == 4       # three songs fit whole; the seven-minute one is cut
    busy = trainsize.choose(card(13.9), LONG)                # a browser or a game holds some
    assert busy["minutes"] == 4.5 and busy["tokens"] == trainsize.tokens_for(270)


def test_what_the_engine_holds_counts_as_available():
    """It lets go of its models before training starts."""
    assert trainsize.choose(card(6.0, 8.7), LONG)["minutes"] == trainsize.choose(card(14.7), LONG)["minutes"]


def test_on_a_mac_only_the_free_memory_counts():
    """Metal reports the whole of the computer's memory as the engine's own; adding it to the free
    memory said 43 GB on a 24 GB Mac."""
    mac = {"name": "mps", "vram_free": 19.3 * GB, "engine_vram": 24.0 * GB}
    assert round(trainsize.available_gb(mac), 1) == 19.3
    assert round(trainsize.available_gb({**mac, "name": "cuda:0 NVIDIA GeForce RTX 4070"}), 1) == 43.3


def test_a_small_card_never_does_worse_than_the_default_and_says_so():
    small = trainsize.choose(card(10.9), LONG)
    assert small["minutes"] == trainsize.FLOOR_MINUTES and small["tight"]
    assert small["tokens"] >= trainsize.MIN_TOKENS


def test_a_big_card_stops_at_what_the_builder_can_encode_whole():
    assert trainsize.choose(card(40.0), LONG)["minutes"] == trainsize.CEILING_MINUTES


def test_it_asks_for_no_more_than_the_songs_have():
    short = trainsize.choose(card(40.0), [90.0, 200.0])      # the longest is 3:20
    assert short["minutes"] == 3.5 and short["tokens"] == trainsize.MIN_TOKENS and short["whole"] == 2
    some = trainsize.choose(card(40.0), [90.0, 280.0])       # 4:40 rounds up to 5:00
    assert some["minutes"] == 5.0 and some["tokens"] == trainsize.tokens_for(280)


def test_a_card_that_cannot_be_read_gets_the_default():
    unknown = trainsize.choose(None, LONG)
    assert unknown["minutes"] == trainsize.FLOOR_MINUTES and not unknown["tight"]
    assert "could not be read" in unknown["reason"]
    assert trainsize.choose(card(14.7), [])["minutes"] == trainsize.FLOOR_MINUTES     # a corpus with no songs yet


def test_the_settings_win_over_the_card(monkeypatch):
    from app import config
    monkeypatch.setattr(config, "TRAIN_MINUTES_AUTO", True)
    monkeypatch.setattr(config, "TRAIN_TOKENS_AUTO", True)
    auto = trainsize.for_corpus(LONG, card(14.7))
    assert auto["minutes"] == 5.5 and auto["tokens"] == 10240 and "14.7 GB available" in auto["reason"]
    # A card that runs out is given less by setting a number.
    monkeypatch.setattr(config, "TRAIN_MINUTES_AUTO", False)
    monkeypatch.setattr(config, "TRAIN_MAX_MINUTES", 3.0)
    smaller = trainsize.for_corpus(LONG, card(14.7))
    assert smaller["minutes"] == 3.0 and "TRAIN_MAX_MINUTES" in smaller["reason"]
    assert smaller["tokens"] == trainsize.tokens_for(180) or smaller["tokens"] == trainsize.MIN_TOKENS
    monkeypatch.setattr(config, "TRAIN_TOKENS_AUTO", False)
    monkeypatch.setattr(config, "TRAIN_MAX_TOKENS", 12288)
    assert trainsize.for_corpus(LONG, card(14.7))["tokens"] == 12288
    # Unreadable card, and auto: the default.
    monkeypatch.setattr(config, "TRAIN_MINUTES_AUTO", True)
    assert trainsize.for_corpus(LONG, None)["minutes"] == trainsize.FLOOR_MINUTES


def test_system_ram_is_checked_against_the_32_gb_recommendation():
    low_ram = {**card(14.7), "ram_total": 24 * GB}
    plenty_ram = {**card(14.7), "ram_total": 31 * GB}
    assert trainsize.choose(low_ram, LONG)["ram_tight"] is True
    assert trainsize.choose(low_ram, LONG)["ram_gb"] == 24.0
    assert trainsize.choose(plenty_ram, LONG)["ram_tight"] is False
    assert trainsize.for_corpus(LONG, low_ram)["ram_tight"] is True
    assert trainsize.for_corpus(LONG, plenty_ram)["ram_tight"] is False

