#!/usr/bin/env python3
"""Run Yeufonic's features against a running app and say what worked and how long it took.

For a new platform or machine (a Mac, a smaller card): every check uses fixed inputs and seeds,
so two runs on two machines can be compared line by line.  Standard library only, so it runs
wherever Python 3.10 does, the machine under test included.

    python3 tools/live_check.py --base http://127.0.0.1:8090 \\
        [--recording song.mp3] [--midi tune.mid] [--only song,stems] [--skip lyrics] \\
        [--full] [--out results]

It drives the app through its MCP tools (turning the MCP server on for the run and back off
afterwards) and a few of its routes.  What it makes goes into a space of its own, "live-check",
to look at or delete afterwards.  On a Mac it also samples the system's free memory and swap.

Checks, in order (a check whose inputs are missing is skipped):
  state       the app answers, the engine is online and compatible, which model
  mcp         the MCP server lists its tools
  song        a short song from fixed lyrics: plan and render, the real-time factor
  instrumental  a short instrumental from a timed structure
  try_more    one more take of the song with a new seed
  variations  one other interpretation of the song
  stems       four stems of the song, then vocals-and-instruments
  cover       a recording (--recording): upload, transcribe, hear the words, render a cover
  midi        a MIDI file (--midi): upload and read its parts
  lyrics      a lyric draft by the app (slow where Gemma has no fast kernel)
  picture     a picture for the song, if anything can draw
  storage     the Storage window's scan
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import platform
import shutil
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

CHECKS = ["state", "mcp", "song", "instrumental", "try_more", "variations", "stems", "cover", "midi",
          "lyrics", "picture", "storage"]
SPACE = "live-check"
STYLE = "indie pop, warm female vocal, acoustic guitar, light drums, 100 bpm"
LYRICS = """[Verse]
Morning light across the floor
Coffee cooling by the door
[Chorus]
Hold on, hold on, the day is new
Hold on, I'm coming home to you
"""
STRUCTURE = "[intro 0:00-0:08]\n[verse 0:08-0:28]\n[chorus 0:28-0:48]\n[outro 0:48-0:56]"
SEED = 20261028


class Failed(Exception):
    pass


class App:
    def __init__(self, base: str) -> None:
        self.base = base.rstrip("/")
        self.rpc_id = 0

    def call(self, method: str, path: str, body: dict | None = None, data: bytes | None = None,
             headers: dict | None = None, timeout: float = 120) -> dict:
        if body is not None:
            data, headers = json.dumps(body).encode(), {"Content-Type": "application/json"}
        req = urllib.request.Request(self.base + path, data=data, method=method, headers=headers or {})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as reply:
                text = reply.read().decode() or "{}"
        except urllib.error.HTTPError as exc:
            raise Failed(f"{method} {path}: {exc.code} {exc.read().decode()[:300]}") from None
        except (urllib.error.URLError, TimeoutError) as exc:
            raise Failed(f"{method} {path}: {exc}") from None
        return json.loads(text)

    def get(self, path: str) -> dict:
        return self.call("GET", path)

    def tool(self, tool_name: str, /, **arguments) -> dict:
        """One MCP tool call; its JSON answer, or Failed with the tool's own words.  The tool's
        name is positional only: create_space has an argument called name of its own."""
        self.rpc_id += 1
        reply = self.call("POST", "/mcp", {"jsonrpc": "2.0", "id": self.rpc_id, "method": "tools/call",
                                           "params": {"name": tool_name, "arguments": arguments}}, timeout=200)
        if "error" in reply:
            raise Failed(f"{tool_name}: {reply['error'].get('message')}")
        result = reply.get("result") or {}
        text = "".join(part.get("text", "") for part in result.get("content", []))
        if result.get("isError"):
            raise Failed(f"{tool_name}: {text[:300]}")
        try:
            return json.loads(text)
        except ValueError:
            return {"text": text}

    def upload(self, path: Path, title: str) -> dict:
        boundary = uuid.uuid4().hex
        kind = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        parts = [f"--{boundary}\r\nContent-Disposition: form-data; name=\"title\"\r\n\r\n{title}\r\n".encode(),
                 f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{path.name}\"\r\n"
                 f"Content-Type: {kind}\r\n\r\n".encode() + path.read_bytes() + b"\r\n",
                 f"--{boundary}--\r\n".encode()]
        return self.call("POST", "/api/sources", data=b"".join(parts),
                         headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}, timeout=600)

    def wait_take(self, take_id: str, limit: float) -> dict:
        deadline = time.time() + limit
        while time.time() < deadline:
            take = self.tool("wait_for_take", take_id=take_id, seconds=45)
            if take.get("finished"):
                if take.get("status") != "done":
                    raise Failed(f"take {take_id} {take.get('status')}: {str(take.get('error'))[:300]}")
                return take
        raise Failed(f"take {take_id} not finished after {limit:.0f} s")

    def wait_source(self, source_id: str, field: str, limit: float) -> dict:
        deadline = time.time() + limit
        while time.time() < deadline:
            source = self.get(f"/api/sources/{source_id}")
            state = source.get(f"{field}_state")
            if state == "done":
                return source
            if state == "failed":
                raise Failed(f"{field}: {source.get(f'{field}_error')}")
            time.sleep(5)
        raise Failed(f"{field} not finished after {limit:.0f} s")


class Memory:
    """The lowest free memory and the most swap seen while a check ran (a Mac's numbers)."""

    def __init__(self) -> None:
        self.on = sys.platform == "darwin" and shutil.which("memory_pressure") is not None
        self.low, self.swap, self.stop = 100, 0.0, threading.Event()

    def sample(self) -> None:
        try:
            out = subprocess.run(["memory_pressure"], capture_output=True, text=True, timeout=10).stdout
            self.low = min(self.low, int(out.strip().splitlines()[-1].split(":")[-1].strip().rstrip("%")))
            swap = subprocess.run(["sysctl", "-n", "vm.swapusage"], capture_output=True, text=True, timeout=5).stdout
            self.swap = max(self.swap, float(swap.split("used = ")[1].split("M")[0]))
        except (OSError, ValueError, IndexError, subprocess.SubprocessError):
            pass

    def __enter__(self):
        self.low, self.swap = 100, 0.0
        self.stop.clear()
        if self.on:
            def loop():
                while not self.stop.wait(5):
                    self.sample()
            self.thread = threading.Thread(target=loop, daemon=True)
            self.sample()
            self.thread.start()
        return self

    def __exit__(self, *_):
        self.stop.set()
        if self.on:
            self.thread.join(6)
            self.sample()

    def said(self) -> dict:
        return {"lowest_free_memory_pct": self.low, "most_swap_mb": round(self.swap)} if self.on else {}


def seconds_of(take: dict) -> float | None:
    for key in ("duration", "seconds", "length_seconds"):
        if isinstance(take.get(key), (int, float)):
            return float(take[key])
    return None


def run(args) -> list[dict]:
    app = App(args.base)
    chosen = [c for c in CHECKS if (not args.only or c in args.only) and c not in args.skip]
    memory = Memory()
    results: list[dict] = []
    made: dict[str, str] = {}

    mcp_was = None
    try:
        settings = app.get("/api/settings")
        mcp_was = next((s.get("value") for s in settings.get("settings", []) if s.get("key") == "mcp.enabled"), None)
    except Failed:
        pass
    app.call("PUT", "/api/settings", {"key": "mcp.enabled", "value": "on"})

    def check(name: str, fn, needs: str | None = None):
        if name not in chosen:
            return
        if needs and needs not in made:
            results.append({"check": name, "result": "skipped", "why": f"needs {needs}"})
            print(f"{name:13} skipped (needs {needs})", flush=True)
            return
        started = time.time()
        print(f"{name:13} ...", end="", flush=True)
        with memory:
            try:
                detail = fn() or {}
                result = {"check": name, "result": "pass", **detail}
            except Failed as exc:
                result = {"check": name, "result": "FAIL", "why": str(exc)}
            except Exception as exc:  # noqa: BLE001 - reported, and the next check still runs
                result = {"check": name, "result": "FAIL", "why": f"{type(exc).__name__}: {exc}"}
        result["seconds"] = round(time.time() - started, 1)
        result.update(memory.said())
        results.append(result)
        print(f"\r{name:13} {result['result']:5} {result['seconds']:7.1f} s  "
              f"{result.get('why') or result.get('note') or ''}", flush=True)

    def state():
        s = app.get("/api/state")
        engine = s.get("engine") or {}
        if not engine.get("online"):
            raise Failed(f"engine offline: {engine.get('error')}")
        if not (engine.get("compat") or {}).get("ok"):
            raise Failed(f"engine not compatible: {engine.get('compat')}")
        return {"version": s.get("version"), "build": s.get("build"), "model": s.get("model"),
                "note": f"{s.get('version')} · {s.get('model')}"}

    def mcp_tools():
        app.rpc_id += 1
        reply = app.call("POST", "/mcp", {"jsonrpc": "2.0", "id": app.rpc_id, "method": "tools/list"})
        tools = [t["name"] for t in reply.get("result", {}).get("tools", [])]
        if len(tools) < 10:
            raise Failed(f"only {len(tools)} tools")
        try:
            app.tool("create_space", name=SPACE)
        except Failed:
            pass        # already there from an earlier run
        return {"tools": len(tools), "note": f"{len(tools)} tools"}

    def timed_take(take: dict, limit: float) -> dict:
        take_id = take.get("id") or take.get("take_id")
        if not take_id:
            raise Failed(f"no take id in {str(take)[:200]}")
        started = time.time()
        done = app.wait_take(take_id, limit)
        wall = time.time() - started
        audio = seconds_of(done)
        out = {"take": take_id, "wall_seconds": round(wall, 1)}
        if audio:
            out.update(audio_seconds=round(audio, 1), real_time_factor=round(audio / wall, 2),
                       note=f"{audio:.0f} s of audio, {audio / wall:.2f}x real time")
        return out

    def song():
        take = app.tool("make_song", style=STYLE, lyrics=LYRICS, title="Live check song", seed=SEED,
                        max_duration=60 if not args.full else 180, space=SPACE)
        out = timed_take(take, args.limit)
        made["song"] = out["take"]
        return out

    def instrumental():
        take = app.tool("make_instrumental", style="lo-fi hip hop, mellow piano, vinyl crackle, 80 bpm",
                        structure=STRUCTURE, title="Live check instrumental", seed=SEED, max_duration=70, space=SPACE)
        return timed_take(take, args.limit)

    def first_take(reply: dict) -> dict:
        takes = reply.get("queued") or ([reply] if reply.get("id") else [])
        if not takes:
            raise Failed(f"nothing made: {str(reply)[:200]}")
        return takes[0]

    def try_more():
        return timed_take(first_take(app.tool("try_more", take_id=made["song"], count=1)), args.limit)

    def variations():
        reply = app.tool("make_variations", take_id=made["song"], interpretations=["tight"])
        return timed_take(first_take(reply), args.limit)

    def stems():
        notes = []
        for kind in ("four", "vocals_and_instruments"):
            set_id = app.tool("make_stems", take_id=made["song"], kind=kind).get("stem_set")
            deadline = time.time() + args.limit
            started = time.time()
            while time.time() < deadline:
                sets = app.tool("get_stems", take_id=made["song"], wait_seconds=45).get("stem_sets") or []
                mine = next((s for s in sets if s.get("id") == set_id), {})
                if mine.get("status") == "failed":
                    raise Failed(f"{kind}: {mine.get('error')}")
                if mine.get("status") == "done":
                    notes.append(f"{kind} {time.time() - started:.0f} s, {len(mine.get('files') or [])} files")
                    break
            else:
                raise Failed(f"{kind} not done after {args.limit:.0f} s")
        return {"note": ", ".join(notes)}

    def cover():
        path = Path(args.recording)
        source = app.upload(path, "Live check recording")
        sid = source["id"]
        times = {}
        started = time.time()
        if source.get("transcribe_state") != "done":
            app.tool("transcribe_recording", recording_id=sid)
            app.wait_source(sid, "transcribe", args.limit)
        times["transcribe"] = round(time.time() - started, 1)
        started = time.time()
        if app.get(f"/api/sources/{sid}").get("lyrics_state") != "done":
            app.call("POST", f"/api/sources/{sid}/lyrics", {})
            app.wait_source(sid, "lyrics", args.limit)
        times["lyrics"] = round(time.time() - started, 1)
        take = app.tool("make_cover", recording_id=sid, style=STYLE, title="Live check cover", seed=SEED,
                        space=SPACE, **({} if args.full else {"max_duration": 90}))
        out = timed_take(take, args.limit)
        out.update(transcribe_seconds=times["transcribe"], lyrics_seconds=times["lyrics"])
        out["note"] = f"transcribe {times['transcribe']:.0f} s, words {times['lyrics']:.0f} s, " + out.get("note", "")
        return out

    def midi():
        source = app.upload(Path(args.midi), "Live check MIDI")
        full = app.get(f"/api/sources/{source['id']}")
        if full.get("transcribe_state") not in ("done", None) and full.get("transcribe_state") != "done":
            app.wait_source(source["id"], "transcribe", 120)
        return {"note": f"source {source['id']}"}

    def lyrics():
        reply = app.tool("write_lyrics", brief="a road trip at night with an old friend", style=STYLE,
                         lines=4, wait_seconds=45)
        deadline = time.time() + args.lyrics_limit
        while not reply.get("lyrics") and time.time() < deadline:
            if reply.get("status") == "failed" or reply.get("error"):
                raise Failed(str(reply.get("error"))[:300])
            reply = app.tool("write_lyrics", draft_id=reply.get("draft_id"), wait_seconds=45)
        if not reply.get("lyrics"):
            raise Failed(f"no words after {args.lyrics_limit:.0f} s")
        return {"note": f"{len(reply['lyrics'].splitlines())} lines"}

    def picture():
        if not app.get("/api/state").get("pictures_possible"):
            return {"result": "skipped", "note": "nothing here can draw"}
        deadline = time.time() + args.limit
        reply = app.tool("make_picture", take_id=made["song"], wait_seconds=45)
        while not reply.get("picture_url") and time.time() < deadline:
            if reply.get("error"):
                raise Failed(str(reply["error"])[:300])
            reply = app.tool("get_take", take_id=made["song"])
            time.sleep(10)
        if not reply.get("picture_url"):
            raise Failed(f"no picture after {args.limit:.0f} s")
        return {}

    def storage():
        s = app.get("/api/storage")
        return {"note": f"{len(s.get('items') or [])} items, {s.get('reclaimable', 0) / 1e9:.1f} GB to give back"}

    try:
        check("state", state)
        check("mcp", mcp_tools)
        check("song", song)
        check("instrumental", instrumental)
        check("try_more", try_more, needs="song")
        check("variations", variations, needs="song")
        check("stems", stems, needs="song")
        if args.recording:
            check("cover", cover)
        elif "cover" in chosen:
            results.append({"check": "cover", "result": "skipped", "why": "no --recording"})
        if args.midi:
            check("midi", midi)
        elif "midi" in chosen:
            results.append({"check": "midi", "result": "skipped", "why": "no --midi"})
        check("lyrics", lyrics)
        check("picture", picture, needs="song")
        check("storage", storage)
    finally:
        if mcp_was != "on":
            try:
                app.call("PUT", "/api/settings", {"key": "mcp.enabled", "value": mcp_was or "off"})
            except Failed:
                pass
    for r in results:   # a check that said it was skipped from inside
        if r.get("result") == "pass" and r.get("note") == "nothing here can draw":
            r["result"] = "skipped"
    return results


def report(results: list[dict], args) -> None:
    stamp = time.strftime("%Y%m%d-%H%M%S")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    machine = {"platform": platform.platform(), "machine": platform.machine(), "base": args.base,
               "at": time.strftime("%Y-%m-%d %H:%M:%S %Z")}
    (out / f"live-check-{stamp}.json").write_text(json.dumps({"machine": machine, "results": results}, indent=2))
    lines = [f"# Live check {machine['at']}", "", f"{machine['platform']} ({machine['machine']}), {args.base}", "",
             "| Check | Result | Seconds | Real time | Lowest free mem | Swap MB | Note |",
             "|---|---|---|---|---|---|---|"]
    for r in results:
        lines.append(f"| {r['check']} | {r['result']} | {r.get('seconds', '')} | {r.get('real_time_factor', '')} | "
                     f"{r.get('lowest_free_memory_pct', '')} | {r.get('most_swap_mb', '')} | "
                     f"{(r.get('why') or r.get('note') or '').replace('|', '/')} |")
    (out / f"live-check-{stamp}.md").write_text("\n".join(lines) + "\n")
    print(f"\nWritten {out / f'live-check-{stamp}.md'} and .json")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--base", default="http://127.0.0.1:8090")
    parser.add_argument("--recording", help="an audio file to make a cover from")
    parser.add_argument("--midi", help="a MIDI file to import")
    parser.add_argument("--only", type=lambda s: s.split(","), default=[])
    parser.add_argument("--skip", type=lambda s: s.split(","), default=[])
    parser.add_argument("--full", action="store_true", help="full-length song and cover, not the short ones")
    parser.add_argument("--limit", type=float, default=3600, help="the longest any one job may take, in seconds")
    parser.add_argument("--lyrics-limit", type=float, default=900)
    parser.add_argument("--out", default="live-check-results")
    args = parser.parse_args()
    results = run(args)
    report(results, args)
    return 1 if any(r["result"] == "FAIL" for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
