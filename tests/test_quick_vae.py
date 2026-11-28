"""The engine's quick tiled audio decode blends its tiles exactly as ComfyUI's does, without the per-sample loop."""
import importlib.util
import itertools
from pathlib import Path

import pytest

from app import jobs

torch = pytest.importorskip("torch")
SPEC = importlib.util.spec_from_file_location(
    "vae", Path(__file__).resolve().parents[1] / "engine" / "custom_nodes" / "yue2_harmony" / "vae.py")
vae = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(vae)


def comfy_tiles(samples, function, tile, overlap, upscale_amount, out_channels):
    """ComfyUI's tiled_scale_multidim for one dimension and a plain upscale, its feathering loop as it is written."""
    output = torch.empty([samples.shape[0], out_channels, round(upscale_amount * samples.shape[2])])
    for b in range(samples.shape[0]):
        s = samples[b:b + 1]
        if s.shape[2] <= tile:
            output[b:b + 1] = function(s)
            continue
        out = output[b:b + 1].zero_()
        out_div = torch.zeros([1, 1, round(upscale_amount * s.shape[2])])
        for pos in range(0, s.shape[2] - overlap, tile - overlap):
            pos = max(0, min(s.shape[2] - overlap, pos))
            length = min(tile, s.shape[2] - pos)
            ps = function(s.narrow(2, pos, length))
            mask = torch.ones([1, 1, ps.shape[2]])
            feather = round(upscale_amount * overlap)
            if feather < mask.shape[2]:
                for t in range(feather):
                    a = (t + 1) / feather
                    mask.narrow(2, t, 1).mul_(a)
                    mask.narrow(2, mask.shape[2] - 1 - t, 1).mul_(a)
            start = round(upscale_amount * pos)
            length = min(ps.shape[2], out.shape[2] - start)
            out.narrow(2, start, length).add_(ps.narrow(2, 0, length) * mask.narrow(2, 0, length))
            out_div.narrow(2, start, length).add_(mask.narrow(2, 0, length))
        out.div_(out_div)
    return output


def decoder(upscale):
    """A stand-in decoder: each latent frame becomes `upscale` samples on two channels, not all alike."""
    weights = torch.linspace(-1.0, 1.0, upscale)

    def decode(latent):
        frames = latent.mean(dim=1, keepdim=True)                       # (1, 1, frames)
        wave = (frames.unsqueeze(-1) * weights).flatten(2)             # (1, 1, frames * upscale)
        return torch.cat([wave, wave.flip(-1)], dim=1)
    return decode


@pytest.mark.parametrize("frames, tile, overlap", [(1500, 512, 64), (700, 256, 32), (300, 512, 64), (1030, 128, 0)])
def test_the_audio_is_the_same_to_the_bit(frames, tile, overlap):
    torch.manual_seed(frames)
    latent = torch.randn(1, 8, frames)
    upscale = 48
    want = comfy_tiles(latent, decoder(upscale), tile, overlap, upscale, 2)
    got = vae.tiled_scale_multidim(latent, decoder(upscale), tile=(tile,), overlap=overlap, upscale_amount=upscale,
                                   out_channels=2, output_device="cpu")
    assert torch.equal(got, want)


def test_the_ramp_is_the_loops_own():
    for feather, size in itertools.product((1, 7, 1920), (2000, 4000)):
        loop, quick = torch.ones(1, 1, size), torch.ones(1, 1, size)
        for t in range(feather):
            a = (t + 1) / feather
            loop.narrow(2, t, 1).mul_(a)
            loop.narrow(2, size - 1 - t, 1).mul_(a)
        vae._feathered(quick, 2, feather)
        assert torch.equal(loop, quick)


def test_a_render_uses_it_when_the_engine_has_it(monkeypatch):
    take = {"id": "abc", "style": "pop", "lyrics": "", "abc": "", "seed": 1, "mode": "full", "max_duration": 60}

    class Engine:
        options = {"quick_vae": True}
    monkeypatch.setattr(jobs, "ENGINE", Engine())
    assert jobs.build_render_graph(take)["15"]["class_type"] == "Yue2VAEDecodeAudioTiled"
    Engine.options = {}
    assert jobs.build_render_graph(take)["15"]["class_type"] == "VAEDecodeAudioTiled"
