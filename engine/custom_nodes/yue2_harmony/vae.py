"""The audio VAE's tiled decode, with ComfyUI's tile blending built in one step rather than sample by sample.

ComfyUI's `tiled_scale_multidim` softens each tile's edges with a mask built in a Python loop, one pass for every
output sample of the overlap.  For a picture that is a few hundred passes; for YuE2's audio VAE, where one latent frame
is 1920 samples, the default overlap of 64 frames is 122,880 passes for every tile, two tensor operations each: the
mask building took longer than the decoding itself, and more the longer the song.

`tiled_scale_multidim` below is ComfyUI's own (comfy/utils.py, at the commit engine/Dockerfile pins), with that loop
replaced by two multiplications by a ramp.  The ramp's values are the loop's, (t + 1) / feather worked out in double
precision, so the mask, and the audio, are the same to the bit.  The node puts it in place of ComfyUI's only while it
decodes, and gives everything else (the memory the decode asks for, the dtype, the output) to ComfyUI unchanged.
"""
from __future__ import annotations

import contextlib
import itertools

import torch


def _feathered(mask: torch.Tensor, dim: int, feather: int) -> None:
    """The loop `for t in range(feather): a = (t + 1) / feather; mask[t] *= a; mask[-1 - t] *= a`, in two steps."""
    ramp = (torch.arange(1, feather + 1, dtype=torch.float64, device=mask.device) / feather).to(mask.dtype)
    shape = [1] * mask.ndim
    shape[dim] = feather
    ramp = ramp.reshape(shape)
    mask.narrow(dim, 0, feather).mul_(ramp)
    mask.narrow(dim, mask.shape[dim] - feather, feather).mul_(ramp.flip(dim))


def tiled_scale_multidim(samples, function, tile=(64, 64), overlap=8, upscale_amount=4, out_channels=3, output_device="cpu",
                         downscale=False, index_formulas=None, pbar=None):
    dims = len(tile)

    if not (isinstance(upscale_amount, (tuple, list))):
        upscale_amount = [upscale_amount] * dims

    if not (isinstance(overlap, (tuple, list))):
        overlap = [overlap] * dims

    if index_formulas is None:
        index_formulas = upscale_amount

    if not (isinstance(index_formulas, (tuple, list))):
        index_formulas = [index_formulas] * dims

    def get_upscale(dim, val):
        up = upscale_amount[dim]
        return up(val) if callable(up) else up * val

    def get_downscale(dim, val):
        up = upscale_amount[dim]
        return up(val) if callable(up) else val / up

    def get_upscale_pos(dim, val):
        up = index_formulas[dim]
        return up(val) if callable(up) else up * val

    def get_downscale_pos(dim, val):
        up = index_formulas[dim]
        return up(val) if callable(up) else val / up

    if downscale:
        get_scale = get_downscale
        get_pos = get_downscale_pos
    else:
        get_scale = get_upscale
        get_pos = get_upscale_pos

    def mult_list_upscale(a):
        return [round(get_scale(i, a[i])) for i in range(len(a))]

    output = torch.empty([samples.shape[0], out_channels] + mult_list_upscale(samples.shape[2:]), device=output_device)

    for b in range(samples.shape[0]):
        s = samples[b:b + 1]

        # handle entire input fitting in a single tile
        if all(s.shape[d + 2] <= tile[d] for d in range(dims)):
            output[b:b + 1] = function(s).to(output_device)
            if pbar is not None:
                pbar.update(1)
            continue

        out = output[b:b + 1].zero_()
        out_div = torch.zeros([s.shape[0], 1] + mult_list_upscale(s.shape[2:]), device=output_device)

        positions = [range(0, s.shape[d + 2] - overlap[d], tile[d] - overlap[d]) if s.shape[d + 2] > tile[d] else [0]
                     for d in range(dims)]

        for it in itertools.product(*positions):
            s_in = s
            upscaled = []

            for d in range(dims):
                pos = max(0, min(s.shape[d + 2] - overlap[d], it[d]))
                length = min(tile[d], s.shape[d + 2] - pos)
                s_in = s_in.narrow(d + 2, pos, length)
                upscaled.append(round(get_pos(d, pos)))

            ps = function(s_in).to(output_device)
            mask = torch.ones([1, 1] + list(ps.shape[2:]), device=output_device)

            for d in range(2, dims + 2):
                feather = round(get_scale(d - 2, overlap[d - 2]))
                if feather >= mask.shape[d]:
                    continue
                if feather > 0:
                    _feathered(mask, d, feather)

            o = out
            o_d = out_div
            ps_view = ps
            mask_view = mask
            for d in range(dims):
                length = min(ps_view.shape[d + 2], o.shape[d + 2] - upscaled[d])
                o = o.narrow(d + 2, upscaled[d], length)
                o_d = o_d.narrow(d + 2, upscaled[d], length)
                if length < ps_view.shape[d + 2]:
                    ps_view = ps_view.narrow(d + 2, 0, length)
                    mask_view = mask_view.narrow(d + 2, 0, length)

            o.add_(ps_view * mask_view)
            o_d.add_(mask_view)

            if pbar is not None:
                pbar.update(1)

        out.div_(out_div)
    return output


@contextlib.contextmanager
def _quick_tiles():
    """ComfyUI's tiling helper replaced by the one above while a decode runs, and put back after."""
    import comfy.utils

    original = comfy.utils.tiled_scale_multidim
    comfy.utils.tiled_scale_multidim = tiled_scale_multidim
    try:
        yield
    finally:
        comfy.utils.tiled_scale_multidim = original


class Yue2VAEDecodeAudioTiled:
    """VAE Decode Audio (Tiled), the same decode and the same audio, without the mask building loop."""

    CATEGORY = "audio"
    RETURN_TYPES = ("AUDIO",)
    FUNCTION = "execute"

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "samples": ("LATENT",),
            "vae": ("VAE",),
            "tile_size": ("INT", {"default": 512, "min": 32, "max": 8192, "step": 8}),
            "overlap": ("INT", {"default": 64, "min": 0, "max": 1024, "step": 8}),
        }}

    def execute(self, samples, vae, tile_size, overlap):
        from comfy_extras.nodes_audio import vae_decode_audio

        with _quick_tiles():
            return (vae_decode_audio(vae, samples, tile_size, overlap),)
