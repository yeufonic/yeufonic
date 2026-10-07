"""Whisper in a process of its own, for where it cannot share the engine's.

On Windows the engine's PyTorch carries the CUDA 13 cuDNN, and CTranslate2 wants the CUDA 12 one.  Both are called
cudnn64_9.dll, and a process keeps whichever it loads first, so putting the CUDA 12 libraries where CTranslate2 can find
them made the engine's own first use of cuDNN (a Demucs separation) fail with a sub-library version mismatch.  Here
CTranslate2 has the process, and its libraries, to itself.

    python hear_worker.py <audio.npy> <model folder or name> <download root> <language>

Writes "P <fraction>" as it goes and "R <json>" at the end: the segments Whisper wrote, as {"start", "end", "text"}.
"""
import json
import sys

import numpy as np
from faster_whisper import WhisperModel

audio_path, target, root, language = sys.argv[1:5]
audio = np.load(audio_path)


def load(local_only):
    return WhisperModel(target, device="cuda", compute_type="float16", download_root=root, local_files_only=local_only)


try:
    model = load(True)
except Exception:  # noqa: BLE001
    model = load(False)
segments, _ = model.transcribe(audio, language=language or None, vad_filter=False, beam_size=5,
                               condition_on_previous_text=False, word_timestamps=True,
                               hallucination_silence_threshold=2.0)
seconds = len(audio) / 16000
out = []
for seg in segments:
    out.append({"start": round(float(seg.start), 2), "end": round(float(seg.end), 2), "text": seg.text})
    print("P", min(1.0, float(seg.end) / seconds) if seconds > 0 else 1.0, flush=True)
print("R", json.dumps(out), flush=True)
