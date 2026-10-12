"""Yeufonic as an MCP server: an agent can ask the app for songs, instrumentals and takes.

Only the part of the Model Context Protocol this needs: JSON-RPC 2.0 over one POST address (the
"streamable HTTP" transport, without sessions or server-sent streams), with the three requests a client makes
to use tools (`initialize`, `tools/list`, `tools/call`) and `ping`. A tool does what the page does, by
calling the app's own routes, so it has the same checks and the same effect, and a job it starts is an
ordinary take in the library.

It is off until `mcp.enabled` is switched on in Settings: a tool call can queue GPU work, and a client on
the same network could otherwise start it. The Host and cross-site checks the app applies to everything
apply to it too."""
from __future__ import annotations

import asyncio
import datetime
import json
import time
from typing import Any, Awaitable, Callable

PROTOCOL_VERSIONS = ("2025-06-18", "2025-03-26", "2024-11-05")
Api = Callable[..., Awaitable[Any]]      # api(method, path, json=None, params=None) -> the route's JSON

LIMIT = 100                              # most takes one call returns
MOST_WAIT = 55                           # seconds one wait_for_take may hold a call: short of a client's timeout
POLL = 2.0                               # how often it looks while waiting

TOOLS: list[dict] = [
    {
        "name": "list_takes",
        "description": "List takes in the library, newest first: id, title, kind (song, cover or instrumental), "
                       "status, length, style and when it was made. Titles are NOT unique: several takes can share one, "
                       "and `same_title_count` says so. When you show takes to a person, ALWAYS include the `short_id` as a "
                       "column, so they can name one exactly (every tool accepts it). Act on a take by its id; when more than "
                       "one matches what the person said, show the choices (short_id, made, length, style) and ask which. "
                       "Takes made from a take by try_more (or Variations and Checkpoints in the app) are kept INSIDE it and "
                       "are not in this list: a take that holds some says how many in `takes_inside` (and `being_made` for "
                       "those not finished), and `inside` with its id lists them. A query finds takes wherever they are, and "
                       "one found inside another says which in `inside_of`. Use get_take for one in full.",
        "inputSchema": {"type": "object", "properties": {
            "query": {"type": "string", "description": "Words that must appear in the title, style or lyrics."},
            "space": {"type": "string", "description": "Only the takes in this space, by name (see list_spaces)."},
            "favourites": {"type": "boolean", "description": "Only starred takes."},
            "inside": {"type": "string", "description": "The id of a take: list the finished takes kept inside it."},
            "limit": {"type": "integer", "description": f"How many, at most {LIMIT}. Default 20."},
        }},
    },
    {
        "name": "get_take",
        "description": "One take in full: how it was made, its status, any error, its lyrics or structure, and "
                       "once it has audio a `listen_url`. You cannot play sound yourself: to let the person hear the take, "
                       "open listen_url in their default browser (for example `xdg-open URL`, `wslview URL` or "
                       "`explorer.exe URL` in WSL, `open URL` on a Mac, `start URL` on Windows). Do not download the file.",
        "inputSchema": {"type": "object", "required": ["take_id"], "properties": {
            "take_id": {"type": "string"},
            "include_score": {"type": "boolean", "description": "Also return the score (ABC text). Default false: it is long."},
        }},
    },
    {
        "name": "wait_for_take",
        "description": "Wait for a take that is being made, for up to about a minute, and return as soon as it is done or "
                       "has failed (or, for a take that is not rendering, as soon as its plan is ready). Returns the same "
                       "as get_take plus `finished`: if it is false the take is still going, so call this again. Use this "
                       "after make_song, make_instrumental or render_take rather than asking the person to check back.",
        "inputSchema": {"type": "object", "required": ["take_id"], "properties": {
            "take_id": {"type": "string"},
            "seconds": {"type": "integer", "description": f"How long to wait, at most {MOST_WAIT}. Default 45."},
        }},
    },
    {
        "name": "list_spaces",
        "description": "The spaces takes are kept in, with how many each holds.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "make_instrumental",
        "description": "Make an instrumental from a style (and optionally a structure such as "
                       "'[intro]\\n[verse]\\n[chorus]\\n[outro]'). It plans the score and, unless render is false, "
                       "renders it. Takes minutes: check progress with get_take. Returns the new take.",
        "inputSchema": {"type": "object", "required": ["style"], "properties": {
            "style": {"type": "string", "description": "Comma-separated tags: genre, mood, instruments, tempo."},
            "structure": {"type": "string", "description": "One section tag per line, each with its time, such as "
                                                           "'[intro 0:00-0:10]\\n[verse 0:10-0:30]'. Omit and one is made for "
                                                           "max_duration (default about 2.5 minutes): leave it out unless the person "
                                                           "named the sections."},
            "max_duration": {"type": "integer", "description": "The most seconds the take may run, 10 to 900. Left out, the app's own setting (360 unless changed), raised to fit a longer plan. "
                                                                 "Ask for the length wanted: 60 for a minute."},
            "title": {"type": "string"},
            "seed": {"type": "integer"},
            "space": {"type": "string", "description": "The space to make it in, by name, such as \"EDM\" (see list_spaces). "
                                                      "Omit for the default space."},
            "style_lora": {"type": "string", "description": "A style LoRA to use, by name or title (see list_style_loras). Its "
                                                           "trigger word is added to the style for you."},
            "lora_planner": {"type": "number", "description": "How strongly it shapes the plan, 0 to 3. Default: the strength saved with it."},
            "lora_sound": {"type": "number", "description": "How strongly it shapes the sound, 0 to 3. Default: the strength saved with it."},
            "render": {"type": "boolean", "description": "Render as well as plan. Default true."},
        }},
    },
    {
        "name": "make_song",
        "description": "Make a song from a style and lyrics (section tags like [Verse] and [Chorus] in the lyrics). "
                       "It plans the score and, unless render is false, renders it. Takes minutes: check progress "
                       "with get_take. Returns the new take.",
        "inputSchema": {"type": "object", "required": ["style", "lyrics"], "properties": {
            "style": {"type": "string"},
            "lyrics": {"type": "string"},
            "max_duration": {"type": "integer", "description": "The most seconds the take may run, 10 to 900. Left out, the app's own setting (360 unless changed), raised to fit a longer plan. "
                                                                 "Ask for the length wanted: 60 for a minute."},
            "title": {"type": "string"},
            "seed": {"type": "integer"},
            "space": {"type": "string", "description": "The space to make it in, by name, such as \"EDM\" (see list_spaces). "
                                                      "Omit for the default space."},
            "style_lora": {"type": "string", "description": "A style LoRA to use, by name or title (see list_style_loras). Its "
                                                           "trigger word is added to the style for you."},
            "lora_planner": {"type": "number", "description": "How strongly it shapes the plan, 0 to 3. Default: the strength saved with it."},
            "lora_sound": {"type": "number", "description": "How strongly it shapes the sound, 0 to 3. Default: the strength saved with it."},
            "render": {"type": "boolean", "description": "Render as well as plan. Default true."},
        }},
    },
    {
        "name": "list_recordings",
        "description": "The recordings in the library that a cover can be made from: id, title, length, whether it has a score "
                       "(a cover needs one) and whether its words are known. Recordings can share a title: use the id.",
        "inputSchema": {"type": "object", "properties": {
            "query": {"type": "string", "description": "Words that must appear in the title."},
        }},
    },
    {
        "name": "make_cover",
        "description": "Make a cover of a recording from the library: the same song and melody, sung and played in a new style. "
                       "Needs the recording's id from list_recordings and a score for it. If no lyrics are given, the words heard "
                       "in the recording (or last used for a cover of it) are used. It renders straight away and takes minutes: "
                       "follow it with wait_for_take.",
        "inputSchema": {"type": "object", "required": ["recording_id", "style"], "properties": {
            "recording_id": {"type": "string"},
            "style": {"type": "string", "description": "Comma-separated tags: genre, mood, instruments, voice."},
            "lyrics": {"type": "string", "description": "Words with section tags like [Verse]. Omit to use the recording's own."},
            "title": {"type": "string"},
            "seed": {"type": "integer"},
            "max_duration": {"type": "integer", "description": "The most seconds it may run, 10 to 900. Default: the recording's length plus a margin."},
            "space": {"type": "string", "description": "The space to make it in, by name. Omit for the default space."},
            "style_lora": {"type": "string", "description": "A style LoRA to use, by name or title (see list_style_loras). Its "
                                                           "trigger word is added to the style for you."},
            "lora_planner": {"type": "number", "description": "How strongly it shapes the plan, 0 to 3. Default: the strength saved with it."},
            "lora_sound": {"type": "number", "description": "How strongly it shapes the sound, 0 to 3. Default: the strength saved with it."},
        }},
    },
    {
        "name": "list_style_loras",
        "description": "The style LoRAs installed: ones trained on a corpus of songs, which carry a sound (and sometimes a voice). "
                       "Gives each one's name, title, trigger word, saved strengths and the styles it learned.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "try_more",
        "description": "Make more takes from an existing one: the same score and words rendered again with new seeds, as several "
                       "new takes to listen to together (the Try more button). Each is queued; follow them with wait_for_take. "
                       "They are kept inside the take they were made from (see list_takes), and a take that is itself inside "
                       "another cannot have more made from it.",
        "inputSchema": {"type": "object", "required": ["take_id"], "properties": {
            "take_id": {"type": "string"},
            "count": {"type": "integer", "description": "How many, 1 to 8. Default 4."},
        }},
    },
    {
        "name": "status",
        "description": "How busy Yeufonic is: whether the engine is online, what is running now and with what progress, what is waiting, "
                       "and whether a LoRA is being trained (which holds the GPU). Check this before queuing something long.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "transcribe_recording",
        "description": "Transcribe a recording in the library into a score, which a cover is made from. Takes a minute or two on the GPU. "
                       "Waits up to `wait_seconds` and returns the state; call again (or list_recordings) while it is still running. "
                       "Recordings can share a title: use the id from list_recordings.",
        "inputSchema": {"type": "object", "required": ["recording_id"], "properties": {
            "recording_id": {"type": "string"},
            "wait_seconds": {"type": "integer", "description": f"How long to wait for it, at most {MOST_WAIT}. Default 45."},
            "again": {"type": "boolean", "description": "Transcribe even though it has a score: this replaces the score, edits and all."},
        }},
    },
    {
        "name": "make_stems",
        "description": "Split a finished take into its parts. `kind` is 'four' (vocals, drums, bass and the rest, the default), "
                       "'vocals_and_instruments' (two parts, the usual choice for a backing track or an acapella), or 'six' (adds guitar "
                       "and piano). Runs on the CPU for minutes, beside other work. Follow it with get_stems.",
        "inputSchema": {"type": "object", "required": ["take_id"], "properties": {
            "take_id": {"type": "string"},
            "kind": {"type": "string", "enum": ["four", "vocals_and_instruments", "six"]},
            "only": {"type": "array", "items": {"type": "string"},
                     "description": "Keep only these parts, such as [\"vocals\"] (the others are still separated, not saved)."},
            "format": {"type": "string", "enum": ["wav", "flac", "mp3"], "description": "Default: the format set in Settings."},
        }},
    },
    {
        "name": "get_stems",
        "description": "The stems made from a take: each set's state, progress and, once done, its files with a link to open or save each "
                       "and one for the whole set as a zip. Waits up to `wait_seconds` for one that is still being made.",
        "inputSchema": {"type": "object", "required": ["take_id"], "properties": {
            "take_id": {"type": "string"},
            "wait_seconds": {"type": "integer", "description": f"How long to wait for a running set, at most {MOST_WAIT}. Default 0: just look."},
        }},
    },
    {
        "name": "star_take",
        "description": "Star a take (or, with starred false, unstar it). Use the take's id: titles are not unique.",
        "inputSchema": {"type": "object", "required": ["take_id"], "properties": {
            "take_id": {"type": "string"},
            "starred": {"type": "boolean", "description": "Default true."},
        }},
    },
    {
        "name": "rename_take",
        "description": "Change a take's title. Use the take's id: titles are not unique.",
        "inputSchema": {"type": "object", "required": ["take_id", "title"], "properties": {
            "take_id": {"type": "string"},
            "title": {"type": "string"},
        }},
    },
    {
        "name": "move_take",
        "description": "Move a take to another space, by the space's name. Reversible: move it back. Take the id from "
                       "list_takes; never act on a title, since several takes can share one.",
        "inputSchema": {"type": "object", "required": ["take_id", "space"], "properties": {
            "take_id": {"type": "string"},
            "space": {"type": "string", "description": "The space to move it to, by name (see list_spaces)."},
        }},
    },
    {
        "name": "delete_take",
        "description": "Delete a take for good: its audio and its record cannot be got back. Two steps. Called with just "
                       "take_id it deletes NOTHING and returns what it would delete, with any other takes that share the "
                       "title. Show the person that, ask whether to go ahead, and only if they say yes call again with "
                       "confirm true. A starred take also needs even_if_starred true, and the person must have said so. "
                       "Take the id from list_takes; never act on a title.",
        "inputSchema": {"type": "object", "required": ["take_id"], "properties": {
            "take_id": {"type": "string"},
            "confirm": {"type": "boolean", "description": "True only after the person has agreed to this deletion."},
            "even_if_starred": {"type": "boolean", "description": "Needed as well when the take is starred."},
        }},
    },
    {
        "name": "render_take",
        "description": "Render a planned take, or render a finished one again (with new_seed for a different result).",
        "inputSchema": {"type": "object", "required": ["take_id"], "properties": {
            "take_id": {"type": "string"},
            "new_seed": {"type": "boolean"},
        }},
    },
    {
        "name": "cancel_take",
        "description": "Stop a take that is queued or running.",
        "inputSchema": {"type": "object", "required": ["take_id"], "properties": {"take_id": {"type": "string"}}},
    },
]

# Without times the planner writes plans of ten minutes and more for an instrumental, which the app rejects as
# unreadable, so an instrumental an agent asks for always gets a structure with times, sized to the length asked.
_SHAPES = (                       # (longest song this shape is for, in seconds; sections with their weights)
    (100, (("intro", 1), ("verse", 3), ("chorus", 3), ("outro", 1))),
    (190, (("intro", 1), ("verse", 3), ("chorus", 3), ("verse", 3), ("chorus", 3), ("outro", 1))),
    (900, (("intro", 1), ("verse", 3), ("chorus", 3), ("verse", 3), ("chorus", 3), ("bridge", 2), ("chorus", 3), ("outro", 1))),
)
DEFAULT_SECONDS = 150


def _mmss(seconds: int) -> str:
    return f"{seconds // 60}:{seconds % 60:02d}"


def timed_structure(total: int) -> str:
    """Sections with times that add up to `total` seconds, in the form the instrumental LoRA reads."""
    total = max(30, min(900, int(total)))                  # four sections of five seconds or more need about this
    sections = next(shape for limit, shape in _SHAPES if total <= limit)
    weight = sum(w for _, w in sections)
    lengths = [max(5, round(total * w / weight)) for _, w in sections]
    lengths[-1] += total - sum(lengths)                    # rounding goes to the last section
    if lengths[-1] < 5:                                    # a very short song: take it from the longest
        longest = lengths.index(max(lengths[:-1]))
        lengths[longest] -= 5 - lengths[-1]
        lengths[-1] = 5
    out, clock = [], 0
    for (name, _), length in zip(sections, lengths):
        out.append(f"[{name} {_mmss(clock)}-{_mmss(clock + length)}]")
        clock += length
    return "\n".join(out)


TAKE_TOOLS = ("try_more", "make_stems", "get_stems", "get_take", "wait_for_take", "move_take", "delete_take", "render_take", "cancel_take", "star_take", "rename_take")
_BRIEF = ("id", "title", "kind", "status", "duration", "style", "favourite", "error")


def _when(stamp: Any) -> str | None:
    """A time a person can tell takes apart by."""
    try:
        return datetime.datetime.fromtimestamp(float(stamp)).strftime("%Y-%m-%d %H:%M")
    except (TypeError, ValueError, OSError):
        return None


def _brief(take: dict, spaces: dict | None = None) -> dict:
    out = {key: take.get(key) for key in _BRIEF if take.get(key) not in (None, "")}
    out["has_audio"] = bool(take.get("has_audio"))
    out["short_id"] = str(take.get("id") or "")[:6]
    out["made"] = _when(take.get("created_at"))
    if spaces and take.get("space_id") in spaces:
        out["space"] = spaces[take["space_id"]]           # the name, which an agent can say to a person
    if take.get("children"):
        out["takes_inside"] = take["children"]            # list them with list_takes and `inside`
    if take.get("children_pending"):
        out["being_made"] = take["children_pending"]
    if take.get("parent_id"):
        out["inside_of"] = {"id": take["parent_id"], "title": take.get("parent_title")}
    return out


async def _space_names(api: Api) -> dict:
    return {space["id"]: space["name"] for space in await api("GET", "/api/spaces")}


def _full(take: dict, include_score: bool, spaces: dict | None = None, base: str = "") -> dict:
    out = {key: value for key, value in take.items()
           if value is not None and key not in ("abc", "audio_path", "prompt_id", "live", "weak_dismissed")}
    if spaces and take.get("space_id") in spaces:
        out["space"] = spaces[take["space_id"]]
    if take.get("live"):
        out["progress"] = take["live"]
    if include_score:
        out["score"] = take.get("abc")
    if take.get("has_audio"):
        out["audio_url"] = f"/api/takes/{take['id']}/audio"
        # A link a person's browser plays. The agent cannot play sound itself: to let them hear it, open this.
        out["listen_url"] = f"{base}/api/takes/{take['id']}/audio"
    return out


def _settled(take: dict) -> bool:
    """Whether there is nothing more to wait for: done, failed, stopped, or a plan that is not going on to render."""
    status = take.get("status")
    if status in ("done", "failed", "cancelled", "stopped"):
        return True
    return status == "planned" and not take.get("auto_render")


MIN_PREFIX = 4


async def _take_id(api: Api, asked: Any) -> str:
    """The full id of the take a person or agent named: the whole id, or the start of it (as many characters as shown in
    the short_id column), when only one take begins that way. A title is never taken for an id."""
    ident = str(asked or "").strip().lower()
    if not ident:
        raise ApiRefused("which take? Give its id (the short_id column of list_takes will do).")
    try:
        await api("GET", f"/api/takes/{ident}")
        return ident
    except ApiRefused:
        pass
    if len(ident) < MIN_PREFIX or not all(ch in "0123456789abcdef" for ch in ident):
        raise ApiRefused(f"no such take: '{asked}'. Use a take's id, or the start of it from the short_id column (at least {MIN_PREFIX} characters).")
    found = [take for take in await api("GET", "/api/takes", params={"limit": 5000}) if take["id"].startswith(ident)]
    if not found:
        raise ApiRefused(f"no such take: '{asked}'")
    if len(found) > 1:
        raise ApiRefused(f"'{asked}' starts {len(found)} takes (" + ", ".join(f"{take['id']} {take.get('title')!r}" for take in found[:6]) +
                         "). Use more of the id.")
    return found[0]["id"]


async def _space_of(api: Api, asked: Any) -> str | None:
    """The id of the space an agent named, by name (any case, with or without the word "space") or by id.
    None when it named none. A name that matches nothing is an error that lists the spaces there are."""
    name = str(asked or "").strip()
    if not name:
        return None
    spaces = await api("GET", "/api/spaces")
    for space in spaces:
        if space["id"] == name:
            return space["id"]
    wanted = {name.lower()}
    if name.lower().endswith(" space"):
        wanted.add(name[:-6].strip().lower())
    found = [space for space in spaces if space["name"].strip().lower() in wanted]
    if len(found) == 1:
        return found[0]["id"]
    names = ", ".join(space["name"] for space in spaces)
    raise ApiRefused(f"{'More than one space is' if found else 'No space is'} called '{name}'. The spaces are: {names}.")


_LORA_KINDS = ("planner", "decoder", "both", "unknown")


async def _style_loras(api: Api) -> list[dict]:
    """The style LoRAs the app offers: not the ones it applies for its own reasons."""
    state = await api("GET", "/api/state")
    return [item for item in (state.get("options") or {}).get("loras") or []
            if not item.get("reserved") and item.get("kind") in _LORA_KINDS]


def _lora_brief(item: dict) -> dict:
    strengths = item.get("strengths") or {}
    styles = [style.get("title") for style in (item.get("styles") or []) if style.get("title")][:12]
    out = {"name": item["name"], "title": item.get("title"), "trigger": item.get("trigger"), "kind": item.get("kind"),
           "saved_planner": strengths.get("planner"), "saved_sound": strengths.get("sound"),
           "note": (item.get("note") or "")[:300] or None, "learned_styles": styles or None}
    return {key: value for key, value in out.items() if value is not None}


def _has_tag(style: str, word: str) -> bool:
    return word.strip().lower() in [tag.strip().lower() for tag in style.split(",")]


async def _with_lora(api: Api, args: dict, body: dict) -> None:
    """Add the style LoRA an agent asked for to a create request: resolved by name or title, its trigger word put first
    in the style (a LoRA does very little without it), and its strengths the ones asked for, else the ones saved with it."""
    asked = str(args.get("style_lora") or "").strip()
    if not asked:
        return
    loras = await _style_loras(api)
    want = asked.lower()
    found = [item for item in loras if want in (item["name"].lower(), item["name"].lower().removesuffix(".safetensors"),
                                                 str(item.get("title") or "").strip().lower())]
    if len(found) != 1:
        names = ", ".join(f"{item.get('title') or item['name']}" for item in loras) or "none are installed"
        raise ApiRefused(f"{'More than one style LoRA is' if found else 'No style LoRA is'} called '{asked}'. They are: {names}.")
    item = found[0]
    strengths = item.get("strengths") or {}
    body["style_lora"] = item["name"]
    body["style_lora_clip"] = float(args["lora_planner"]) if args.get("lora_planner") is not None else float(strengths.get("planner", 1.0))
    body["style_lora_model"] = float(args["lora_sound"]) if args.get("lora_sound") is not None else float(strengths.get("sound", 1.0))
    trigger = (item.get("trigger") or "").strip()
    if trigger and not _has_tag(body.get("style", ""), trigger):
        body["style"] = trigger + (", " + body["style"] if body.get("style") else "")


def _text(value: Any, error: bool = False) -> dict:
    return {"content": [{"type": "text", "text": value if isinstance(value, str) else json.dumps(value, indent=2, default=str)}],
            "isError": error}


_KINDS = {"four": "htdemucs", "vocals_and_instruments": "htdemucs_2s", "six": "htdemucs_6s"}
_TRANSCRIBING = ("queued", "running")


def _stem_set(item: dict, base: str) -> dict:
    out = {"id": item["id"], "status": item.get("status"), "model": item.get("model"), "parts": item.get("wanted"),
           "format": item.get("fmt"), "progress": item.get("progress"), "stage": item.get("stage"), "error": item.get("error")}
    if item.get("files"):
        out["files"] = [{"name": f["name"], "url": f"{base}/api/stem-sets/{item['id']}/{f['file']}"} for f in item["files"]]
        out["zip_url"] = f"{base}/api/stem-sets/{item['id']}/zip"
    return {key: value for key, value in out.items() if value not in (None, "")}


async def call_tool(name: str, args: dict, api: Api, base: str = "") -> dict:
    """Run one tool. A refusal from the app comes back as an error result the agent can read."""
    args = dict(args or {})
    try:
        if name in TAKE_TOOLS:
            args["take_id"] = await _take_id(api, args.get("take_id"))
        if name == "list_takes":
            limit = max(1, min(LIMIT, int(args.get("limit") or 20)))
            params = {"limit": limit, "q": args.get("query") or "", "favourite": bool(args.get("favourites"))}
            space = await _space_of(api, args.get("space") or args.get("space_id"))
            if space:
                params["space_id"] = space
            if args.get("inside"):
                params["inside"] = await _take_id(api, args["inside"])
            spaces = await _space_names(api)
            found = [_brief(take, spaces) for take in await api("GET", "/api/takes", params=params)]
            same = {}
            for item in found:
                same[item.get("title")] = same.get(item.get("title"), 0) + 1
            for item in found:
                if same[item.get("title")] > 1:
                    item["same_title_count"] = same[item.get("title")]       # so an agent knows the title is not enough
            return _text(found)
        if name == "get_take":
            take = await api("GET", f"/api/takes/{args['take_id']}")
            return _text(_full(take, bool(args.get("include_score")), await _space_names(api), base))
        if name == "wait_for_take":
            wait = max(1, min(MOST_WAIT, int(args.get("seconds") or 45)))
            deadline, started = time.monotonic() + wait, time.monotonic()
            while True:
                take = await api("GET", f"/api/takes/{args['take_id']}")
                if _settled(take) or time.monotonic() >= deadline:
                    break
                await asyncio.sleep(min(POLL, max(0.05, deadline - time.monotonic())))
            result = _full(take, False, await _space_names(api), base)
            result["finished"] = _settled(take)
            result["waited_seconds"] = round(time.monotonic() - started, 1)
            return _text(result)
        if name == "list_spaces":
            return _text(await api("GET", "/api/spaces"))
        if name in ("make_instrumental", "make_song"):
            body = {"style": args["style"], "auto_render": args.get("render") is not False}
            space = await _space_of(api, args.get("space") or args.get("space_id"))
            if space:
                body["space_id"] = space
            for key in ("title", "seed", "max_duration"):
                if args.get(key) not in (None, ""):
                    body[key] = args[key]
            await _with_lora(api, args, body)
            if name == "make_instrumental":
                # What the person asked for, or a timed structure for the length: never bare, which fails.
                body["structure"] = str(args.get("structure") or "").strip() or timed_structure(
                    int(args.get("max_duration") or DEFAULT_SECONDS))
                if not args.get("max_duration") and not args.get("structure"):
                    body["max_duration"] = DEFAULT_SECONDS + 30
                    body["cap_typed"] = False
                made = await api("POST", "/api/instrumentals", json=body)
            else:
                body["lyrics"] = args["lyrics"]
                made = await api("POST", "/api/songs", json=body)
            return _text(_brief(made, await _space_names(api)) if isinstance(made, dict) and "id" in made else made)
        if name == "list_recordings":
            query = str(args.get("query") or "").strip().lower()
            found = [{"id": r["id"], "title": r["title"], "length": r.get("duration"), "has_score": bool(r.get("has_score")),
                      "transcription": r.get("transcribe_state"), "words_known": bool(r.get("has_lyrics")),
                      "covers_made": r.get("take_count")}
                     for r in await api("GET", "/api/sources") if not query or query in (r.get("title") or "").lower()]
            return _text(found[:LIMIT])
        if name == "list_style_loras":
            return _text([_lora_brief(item) for item in await _style_loras(api)])
        if name == "make_cover":
            source = await api("GET", f"/api/sources/{args['recording_id']}")
            if not (source.get("abc") or "").strip():
                return _text(f"'{source.get('title')}' has no score yet, and a cover is made from its score. Transcribe it in the "
                             "app first (the Transcribe button beside the recording).", True)
            lyrics = str(args.get("lyrics") or "").strip()
            if not lyrics:
                heard = await api("GET", f"/api/sources/{args['recording_id']}/lyrics")
                lyrics = (heard.get("lyrics") or heard.get("last_used") or "").strip()
            sources = {r["id"]: r for r in await api("GET", "/api/sources")}
            seconds = (sources.get(source["id"]) or {}).get("score_seconds")
            body = {"source_id": source["id"], "style": args["style"], "lyrics": lyrics,
                    "max_duration": float(args["max_duration"]) if args.get("max_duration") else min(900.0, float(int(seconds or 350) + 10))}
            for key in ("title", "seed"):
                if args.get(key) not in (None, ""):
                    body[key] = args[key]
            space = await _space_of(api, args.get("space"))
            if space:
                body["space_id"] = space
            await _with_lora(api, args, body)
            made = await api("POST", "/api/takes", json=body)
            if isinstance(made, dict) and "id" in made:
                return _text({"kind": "cover", **_brief(made, await _space_names(api))})     # the route's reply does not say
            return _text(made)
        if name == "try_more":
            count = max(1, min(8, int(args.get("count") or 4)))
            made = await api("POST", f"/api/takes/{args['take_id']}/tries", json={"mode": "seeds", "count": count})
            return _text({"queued": [{"id": t["id"], "short_id": t["id"][:6], "title": t["title"], "seed": t["seed"]}
                                     for t in made.get("created", [])],
                          "next": "Each is rendering. Use wait_for_take on any of them, or list_takes to see them all."})
        if name == "status":
            state = await api("GET", "/api/state")
            engine, current = state.get("engine") or {}, state.get("current")
            training = state.get("training")
            out = {"version": state.get("version"), "engine_online": bool(engine.get("online")),
                   "engine_starting": bool(engine.get("starting")), "engine_error": engine.get("error"),
                   "running_now": ({"id": current.get("id"), "kind": current.get("kind"), "label": current.get("label"),
                                    "seconds": current.get("elapsed"), "progress": current.get("progress")} if current else None),
                   "waiting": [{"kind": q.get("kind"), "title": q.get("title"), "state": q.get("state")} for q in state.get("queue") or []
                               if q.get("state") != "running"],
                   "training": ({"lora": training.get("lora_name"), "progress": training.get("progress"), "stage": training.get("stage")}
                                if training else None),
                   "gpu": engine.get("gpu")}
            if not out["engine_online"]:
                out["advice"] = "The engine is not online, so nothing can be planned or rendered yet."
            return _text({key: value for key, value in out.items() if value not in (None, [], "")})
        if name == "transcribe_recording":
            ident = args["recording_id"]
            before = await api("GET", f"/api/sources/{ident}")
            if (before.get("abc") or "").strip() and before.get("transcribe_state") == "done" and not args.get("again"):
                return _text({"recording_id": ident, "title": before.get("title"), "transcription": "done", "has_score": True,
                              "next": "It already has a score, so nothing was run. Pass again true to transcribe it again (it replaces the score)."})
            try:
                await api("POST", f"/api/sources/{ident}/transcribe")
            except ApiRefused as refused:
                if "already being transcribed" not in str(refused):
                    raise
            wait = max(0, min(MOST_WAIT, int(args.get("wait_seconds") if args.get("wait_seconds") is not None else 45)))
            deadline = time.monotonic() + wait
            while True:
                source = await api("GET", f"/api/sources/{ident}")
                if source.get("transcribe_state") not in _TRANSCRIBING or time.monotonic() >= deadline:
                    break
                await asyncio.sleep(min(POLL, max(0.05, deadline - time.monotonic())))
            state = source.get("transcribe_state")
            out = {"recording_id": ident, "title": source.get("title"), "transcription": state,
                   "has_score": bool((source.get("abc") or "").strip())}
            if state == "failed":
                out["error"] = source.get("transcribe_error")
            elif state in _TRANSCRIBING:
                out["next"] = "Still transcribing: call again to wait longer."
            return _text({key: value for key, value in out.items() if value not in (None, "")})
        if name == "make_stems":
            kind = str(args.get("kind") or "four")
            if kind not in _KINDS:
                return _text(f"kind must be one of: {', '.join(_KINDS)}", True)
            body = {"model": _KINDS[kind], "stems": list(args.get("only") or [])}
            if args.get("format"):
                body["format"] = args["format"]
            made = await api("POST", f"/api/takes/{args['take_id']}/stems", json=body)
            return _text({"stem_set": made.get("id"), "parts": made.get("stems"), "format": made.get("format"), "status": made.get("status"),
                          "next": "Separating on the CPU takes minutes. Call get_stems with this take's id, with wait_seconds to wait."})
        if name == "get_stems":
            wait = max(0, min(MOST_WAIT, int(args.get("wait_seconds") or 0)))
            deadline = time.monotonic() + wait
            while True:
                sets = await api("GET", "/api/stem-sets", params={"take_id": args["take_id"]})
                running = [item for item in sets if item.get("status") in ("queued", "running")]
                if not running or time.monotonic() >= deadline:
                    break
                await asyncio.sleep(min(POLL, max(0.05, deadline - time.monotonic())))
            if not sets:
                return _text({"take_id": args["take_id"], "stem_sets": [], "message": "No stems have been made for this take. Use make_stems."})
            return _text({"take_id": args["take_id"], "stem_sets": [_stem_set(item, base) for item in sets], "any_running": bool(running)})
        if name == "star_take":
            starred = args.get("starred") is not False
            await api("POST", f"/api/takes/{args['take_id']}/favourite", params={"value": starred})
            return _text({"take_id": args["take_id"], "starred": starred})
        if name == "rename_take":
            return _text(await api("POST", f"/api/takes/{args['take_id']}/rename", json={"title": str(args.get("title") or "")}))
        if name == "move_take":
            space = await _space_of(api, args.get("space"))
            if not space:
                return _text("say which space to move it to", True)
            await api("POST", f"/api/takes/{args['take_id']}/move", json={"space_id": space})
            return _text(_brief(await api("GET", f"/api/takes/{args['take_id']}"), await _space_names(api)))
        if name == "delete_take":
            take = await api("GET", f"/api/takes/{args['take_id']}")
            if take.get("favourite") and not args.get("even_if_starred"):
                return _text(f"'{take.get('title')}' ({take['id']}) is starred, so it was not deleted. If the person really wants it "
                             "gone, ask them, then call again with confirm and even_if_starred both true.", True)
            inside = (take.get("children") or 0) + (take.get("children_pending") or 0)
            if not args.get("confirm"):
                spaces = await _space_names(api)
                same = [t for t in await api("GET", "/api/takes", params={"q": take.get("title") or "", "limit": LIMIT})
                        if t["id"] != take["id"] and t.get("title") == take.get("title")]
                return _text({
                    "deleted": False,
                    "message": "NOTHING WAS DELETED. This is the take that would be. Show the person its details, ask whether to "
                               "delete it for good, and if they agree call delete_take again with confirm true."
                               + (f" It holds {inside} other take{'' if inside == 1 else 's'} made from it, which would be "
                                  "deleted with it: say so." if inside else ""),
                    "would_delete": _brief(take, spaces) | ({"running": "it is being made and would be stopped"}
                                                           if take.get("status") in ("queued", "running") else {}),
                    "other_takes_with_this_title": [_brief(t, spaces) for t in same],
                })
            await api("DELETE", f"/api/takes/{args['take_id']}")
            return _text({"deleted": True, "take": {"id": take["id"], "title": take.get("title"), "made": _when(take.get("created_at"))}})
        if name == "render_take":
            made = await api("POST", f"/api/takes/{args['take_id']}/render", json={"reseed": bool(args.get("new_seed"))})
            return _text(made)
        if name == "cancel_take":
            return _text(await api("POST", f"/api/takes/{args['take_id']}/cancel"))
    except KeyError as missing:
        return _text(f"missing argument: {missing}", True)
    except ApiRefused as refused:
        return _text(str(refused), True)
    return _text(f"unknown tool: {name}", True)


class ApiRefused(Exception):
    """The app turned a request down, with its own reason."""


def error_reply(request_id: Any, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


async def handle(message: Any, api: Api, version: str, base: str = "") -> dict | None:
    """One JSON-RPC message in, its reply out; None for a notification, which has none."""
    if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
        return error_reply(None, -32600, "not a JSON-RPC 2.0 request")
    request_id, method, params = message.get("id"), message.get("method"), message.get("params") or {}
    if "id" not in message:
        return None                                  # notifications/initialized, notifications/cancelled
    if method == "initialize":
        asked = params.get("protocolVersion")
        return {"jsonrpc": "2.0", "id": request_id, "result": {
            "protocolVersion": asked if asked in PROTOCOL_VERSIONS else PROTOCOL_VERSIONS[0],
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "yeufonic", "version": version},
            "instructions": "Yeufonic makes songs, covers and instrumentals with YuE2. Making one takes minutes: start it, then "
                            "call wait_for_take with its id, and again while `finished` is false. Do not poll with shell commands or "
                            "the app's web API: use these tools. To let the person hear a take, open its listen_url in their "
                            "browser. Several takes can share a title, so act on a take by its id, and whenever you list takes show "
                            "each one's short_id (any tool accepts it) so the person can name one exactly.",
        }}
    if method == "ping":
        return {"jsonrpc": "2.0", "id": request_id, "result": {}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        if not isinstance(params.get("name"), str):
            return error_reply(request_id, -32602, "a tool name is needed")
        return {"jsonrpc": "2.0", "id": request_id, "result": await call_tool(params["name"], params.get("arguments"), api, base)}
    return error_reply(request_id, -32601, f"method not found: {method}")
