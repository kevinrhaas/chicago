#!/usr/bin/env python3
"""Build the 1904 lakefront railway PBR library (T-2478).

    python3 generate_prairie_1904_rail.py --out ..      # rebuild the library in place

The Illinois Central's right-of-way east of Prairie Avenue: the cinder bed the tracks
lie in, the trodden cinders between and beside them, the weedy verge along the edges,
the timber of a crosstie, and the alpha card the verge's grass tufts are drawn with.
It is the street-surface library's sibling (../prairie_1904_pbr/) and borrows its noise
and its map writer, so the two read as one place: 512 px, seamless, deterministic,
three web JPEG derivatives per material that publish.sh ships and nothing else.

One difference, for the repository's weight: the masters kept here are the colour,
the OpenGL normal, the 16-bit height and the packed ORM, not the full eight. The
DirectX normal and the loose AO / roughness / metallic are one line of numpy from
those, and nobody binds them.

WHAT THESE ARE EVIDENCE OF: NOTHING. George Glessner's photographs at 18th Street show
the bed as dark, fine and filled to the ties' tops, and that is all a picture here
borrows from a source; the grain, the colour, the clinker, the weeds and the grain of
the timber are ours (docs/LIBERTIES.md L-ic-tracks-2478). Which ground carries which
material is data/railway/1904_spec.json's to say. No photograph is sampled.

Orientation: image x runs ALONG the track (the renderer's u), image y ACROSS it (v).
"""

from __future__ import annotations

import argparse
import io
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "prairie_1904_pbr" / "tools"))
import generate_prairie_1904_pbr as base  # noqa: E402  (the sibling's noise and writers)

SIZE = base.SIZE
clamp01, blur, noise, fbm, stamps, palette, voronoi = (
    base.clamp01, base.blur, base.noise, base.fbm, base.stamps, base.palette, base.voronoi)

MATERIALS = [
    dict(id="cinder_ballast", group="ballast", span_m=2.0, span_across_m=2.0,
         kind="ballast", mean_roughness=0.96, colors=((74, 70, 66), (22, 21, 21)),
         note="Locomotive cinders as track ballast, filled up round the ties: coarse "
              "clinker in a fine black-grey ash, a few rust-brown and glassy lumps and pale "
              "ash where the sun has dried it. The darkness and fineness are what both "
              "Glessner photographs at 18th Street show; grain and colour are "
              "reconstructed (L-ic-tracks-2478)."),
    dict(id="trodden_cinders", group="ground", span_m=4.0, span_across_m=4.0,
         kind="trodden", mean_roughness=0.93, colors=((92, 87, 81), (36, 34, 33)),
         note="The same cinders trodden and rolled flat between and beside the tracks: "
              "finer, dustier, a faint path worn along the track, oil drips and a little "
              "moss and grass in the low places. Reconstructed (L-ic-tracks-2478)."),
    dict(id="weedy_verge", group="verge", span_m=3.0, span_across_m=3.0,
         kind="verge", mean_roughness=0.95, colors=((104, 116, 62), (56, 66, 36)),
         note="A railway verge in July: patchy grass and weeds over cinder ground, bare "
              "ash showing through, dry straw-coloured stalks. The grass tufts drawn over "
              "it are the alpha card grass_tuft. Reconstructed (L-ic-tracks-2478)."),
    dict(id="tie_timber", group="timber", span_m=2.44, span_across_m=0.229,
         kind="timber", mean_roughness=0.88, colors=((104, 94, 80), (52, 46, 40)),
         note="The top of an untreated hewn-oak crosstie a few seasons in the track, "
              "weathered silver-brown: grain along its length, end and season checks, "
              "cinder dust packed into the grain and a darker band where each rail sits. "
              "Untreated because creosoting was still unusual on Midwestern lines before "
              "about 1910; that, the wood and its colour are reconstructed (L-ic-tracks-2478)."),
]

TUFT = dict(id="grass_tuft", group="foliage", width_px=256, height_px=512, height_m=0.55,
            note="An alpha card of grass and weed blades with a few seed heads, drawn "
                 "upright; the renderer stands two crossed at each tuft. Species, height "
                 "and colour are reconstructed (L-ic-tracks-2478).")

WEB_SUFFIXES = ("basecolor", "normal_gl", "orm")


# ------------------------------------------------------------------------ surfaces

def ballast(spec, rng):
    # two sizes of clinker lump (~3-5 cm and ~1-2 cm at 256 px/m), half buried in ash
    ids, dist, edge = voronoi(rng, 900)
    ids2, dist2, edge2 = voronoi(rng, 4200)
    n1, n2 = ids.max() + 1, ids2.max() + 1
    tone = rng.random(n1).astype(np.float32)[ids]
    tone2 = rng.random(n2).astype(np.float32)[ids2]
    rust = (rng.random(n1) < 0.03).astype(np.float32)[ids]
    glass = (rng.random(n2) < 0.05).astype(np.float32)[ids2]
    big = clamp01(1 - dist / 7.0) ** 0.6
    small = clamp01(1 - dist2 / 3.2) ** 0.8
    ash = fbm(rng, (30, 10, 3), (0.5, 0.3, 0.2))          # fine ash settling between lumps
    fill = clamp01((ash - 0.40) * 2.0)                    # where ash buries the lumps
    showbig = clamp01((noise(rng, 5.0) - 0.45) * 3) * (1 - fill)
    lump = np.maximum(big * showbig, small * (1 - 0.6 * fill))
    crack = np.maximum(blur(edge, 0.8) * showbig, 0.6 * blur(edge2, 0.6) * (1 - fill))
    fine = noise(rng, 0.6)
    pale = clamp01((noise(rng, 1.1) - 0.74) * 4)          # sun-dried ash specks
    t = 0.42 + 0.30 * (np.where(showbig > 0.5, tone, tone2) - 0.5) * (1 - 0.5 * fill)
    t = t + 0.22 * (fine - 0.5) + 0.18 * (ash - 0.5) - 0.20 * crack + 0.30 * pale + 0.08 * lump
    color = palette(t, *spec["colors"])
    rust = rust * showbig
    color = color * (1 - 0.45 * rust[..., None]) + np.array((92, 64, 48), np.float32) * 0.45 * rust[..., None]
    color = color * (1 - 0.35 * glass[..., None]) + np.array((26, 28, 32), np.float32) * 0.35 * glass[..., None]
    h = 0.42 + 0.38 * lump + 0.10 * (fine - 0.5) - 0.12 * crack
    rough = spec["mean_roughness"] - 0.35 * glass * small + 0.03 * (fine - 0.5)
    return clamp01(h), color, clamp01(rough), 4.5


def trodden(spec, rng):
    base_f = fbm(rng, (60, 20, 6), (0.45, 0.35, 0.20))
    grit = noise(rng, 0.55)
    specks = clamp01((noise(rng, 0.7) - 0.64) * 6)        # embedded clinker
    pale = clamp01((noise(rng, 1.0) - 0.70) * 5)
    path = 0.5 + 0.5 * np.cos(np.linspace(0, 2 * math.pi, SIZE, endpoint=False))[:, None]
    path = blur(np.broadcast_to(path ** 6, (SIZE, SIZE)).copy() * noise(rng, (3.0, 60.0)), (6.0, 30.0))
    oil = stamps(rng, 5, 9.0, elongate=1.6) * noise(rng, 2.5)
    moss = clamp01((fbm(rng, (40, 12), (0.6, 0.4)) - 0.66) * 4) * (1 - path)
    t = 0.52 + 0.28 * (base_f - 0.5) + 0.14 * (grit - 0.5) - 0.30 * specks + 0.22 * pale + 0.10 * path
    color = palette(t, *spec["colors"])
    color = color * (1 - 0.55 * oil[..., None]) + np.array((22, 20, 19), np.float32) * 0.55 * oil[..., None]
    color = color * (1 - 0.6 * moss[..., None]) + np.array((70, 82, 44), np.float32) * 0.6 * moss[..., None]
    h = 0.5 + 0.14 * (base_f - 0.5) + 0.12 * (grit - 0.5) + 0.10 * specks - 0.08 * path + 0.06 * moss
    rough = spec["mean_roughness"] - 0.20 * oil - 0.06 * path + 0.03 * (grit - 0.5)
    return clamp01(h), color, clamp01(rough), 3.4


def verge(spec, rng):
    cover = fbm(rng, (55, 22, 8), (0.5, 0.3, 0.2))        # where the weeds have taken
    blades = noise(rng, (1.2, 0.45))                      # fine blade grain along x
    grassy = clamp01((cover + 0.30 * (noise(rng, 1.5) - 0.5) - 0.36) * 4.5)
    clumps = fbm(rng, (6, 2.5, 1.0), (0.45, 0.35, 0.2))
    straw = clamp01((noise(rng, (2.0, 0.6)) - 0.66) * 4) * grassy
    flowers = clamp01((noise(rng, 0.9) - 0.83) * 9) * grassy  # a few yellow and white heads
    which = noise(rng, 6.0) > 0.5
    ground = palette(0.45 + 0.25 * (noise(rng, 0.7) - 0.5) + 0.2 * (cover - 0.5), (104, 98, 90), (44, 42, 40))
    t = 0.50 + 0.55 * (blades - 0.5) + 0.35 * (clumps - 0.5)
    leaf = palette(t, *spec["colors"])
    leaf = leaf * (1 - 0.6 * straw[..., None]) + np.array((150, 134, 88), np.float32) * 0.6 * straw[..., None]
    color = ground * (1 - grassy[..., None]) + leaf * grassy[..., None]
    fcol = np.where(which[..., None], np.array((206, 176, 60), np.float32), np.array((214, 210, 196), np.float32))
    color = color * (1 - flowers[..., None]) + fcol * flowers[..., None]
    h = 0.40 + 0.30 * grassy * (0.6 + 0.4 * clumps) + 0.15 * (blades - 0.5) * grassy
    rough = spec["mean_roughness"] + 0.02 * (blades - 0.5)
    return clamp01(h), color, clamp01(rough), 3.0


def timber(spec, rng):
    yy, xx = np.indices((SIZE, SIZE)).astype(np.float32)
    # the tile is 2.44 m along x and one tie's width across y: grain runs along x,
    # so every field is stretched hard along x
    rings = noise(rng, (0.9, 40.0))
    wav = blur(rng.random((SIZE, SIZE), dtype=np.float32), (6.0, 60.0))
    grain = 0.5 + 0.5 * np.sin((yy / SIZE) * 2 * math.pi * 26 + 18 * (base.standard(wav) - 0.5))
    checks = np.zeros((SIZE, SIZE), np.float32)
    for _ in range(9):                                    # season checks: long thin splits
        y0, x0 = rng.random() * SIZE, rng.random() * SIZE
        ln = SIZE * (0.15 + 0.4 * rng.random())
        dy = np.minimum(np.abs(yy - y0), SIZE - np.abs(yy - y0))
        dx = (xx - x0) % SIZE
        along = clamp01(1 - np.abs(dx - ln / 2) / (ln / 2))
        checks = np.maximum(checks, clamp01(1 - dy / (0.6 + 1.6 * along)) * (along > 0))
    # rail seats: the 85-lb rail's base, 0.13 m wide, at gauge each side of centre
    seat_c = np.array((0.5 - 0.7175 / 2.44 - 0.0335 / 2.44, 0.5 + 0.7175 / 2.44 + 0.0335 / 2.44)) * SIZE
    seat = np.zeros((SIZE, SIZE), np.float32)
    for c in seat_c:
        seat = np.maximum(seat, clamp01(1 - np.abs(xx - c) / (0.075 / 2.44 * SIZE)))
    dust = clamp01(blur(checks, 2.0) * 1.5) + 0.5 * fbm(rng, (30, 8), (0.6, 0.4))
    ends = clamp01(1 - np.minimum(xx, SIZE - 1 - xx) / (0.12 * SIZE))
    t = 0.55 + 0.20 * (rings - 0.5) + 0.12 * (grain - 0.5) - 0.25 * dust - 0.20 * ends - 0.30 * seat
    color = palette(t, *spec["colors"])
    color *= (1 - 0.55 * checks)[..., None]
    color = color * (1 - 0.35 * seat[..., None]) + np.array((70, 46, 34), np.float32) * 0.35 * seat[..., None]
    h = 0.6 + 0.10 * (grain - 0.5) + 0.06 * (rings - 0.5) - 0.45 * checks - 0.06 * seat
    rough = spec["mean_roughness"] + 0.05 * (rings - 0.5) - 0.12 * seat
    return clamp01(h), color, clamp01(rough), 3.0


SURFACES = {"ballast": ballast, "trodden": trodden, "verge": verge, "timber": timber}


# ---------------------------------------------------------------------------- tuft

def grass_tuft(rng, w, h):
    """RGBA: blades rising from the bottom edge, drawn at 4x and reduced for clean alpha."""
    k = 4
    W, H = w * k, h * k
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    greens = [(92, 116, 50), (112, 132, 58), (78, 100, 44), (132, 142, 70), (150, 140, 88)]

    def blade(x0, height, lean, width, col, curl):
        steps = 18
        pts_l, pts_r = [], []
        for i in range(steps + 1):
            s = i / steps
            x = x0 + lean * s * height + curl * (s ** 2) * height
            y = H - s * height
            half = width * (1 - s) ** 0.8 / 2 + 0.5
            pts_l.append((x - half, y))
            pts_r.append((x + half, y))
        shade = 0.75 + 0.35 * rng.random()
        c = tuple(int(min(255, v * shade)) for v in col)
        d.polygon(pts_l + pts_r[::-1], fill=c + (255,))

    order = sorted(range(70), key=lambda _: rng.random())
    for _ in order:
        x0 = W * (0.30 + 0.40 * rng.random())
        height = H * (0.35 + 0.6 * rng.random() ** 0.7)
        lean = (rng.random() - 0.5) * 0.7
        curl = (rng.random() - 0.5) * 0.5
        col = greens[int(rng.integers(len(greens)))]
        blade(x0, height, lean, W * (0.012 + 0.014 * rng.random()), col, curl)
    for _ in range(3):                                    # seed stalks with a head (timothy, foxtail)
        x0 = W * (0.38 + 0.24 * rng.random())
        height = H * (0.80 + 0.18 * rng.random())
        lean = (rng.random() - 0.5) * 0.25
        blade(x0, height, lean, W * 0.008, (120, 118, 70), 0.0)
        tx = x0 + lean * height
        hl = H * 0.06
        for j in range(26):
            yy = H - height + j * hl / 26
            r = W * 0.008 * (1 - abs(j / 26 - 0.45))
            c = (int(150 + 30 * rng.random()), int(140 + 20 * rng.random()), 90)
            d.ellipse((tx - r, yy - r, tx + r, yy + r), fill=c + (255,))
    # Reduce with the colour weighted by its own alpha: a plain resize mixes the
    # transparent black around every blade into its edge, and a blade two pixels wide
    # is all edge, so the weeds drew black.
    big = np.asarray(img).astype(np.float32) / 255.0
    al = big[..., 3:4]
    prem = (big[..., :3] * al).reshape(h, k, w, k, 3).mean(axis=(1, 3))
    alpha = al.reshape(h, k, w, k, 1).mean(axis=(1, 3))
    rgb = prem / np.maximum(alpha, 1e-4)
    # and give the transparent texels the colour of the blades near them, so the
    # mip levels a far tuft is drawn from do not darken toward black either
    from scipy import ndimage
    wsum = ndimage.gaussian_filter(alpha[..., 0], 6.0)
    fill = np.stack([ndimage.gaussian_filter(prem[..., c], 6.0) for c in range(3)], -1) / np.maximum(wsum, 1e-4)[..., None]
    empty = alpha < 0.02
    rgb = np.where(empty, fill, rgb)
    # darken toward the base: the tuft's own shade
    shade = np.linspace(0.72, 1.0, h, dtype=np.float32)[::-1][:, None, None]
    a = np.concatenate([np.clip(rgb * shade, 0, 1), alpha], -1) * 255.0
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


# ---------------------------------------------------------------------------- build

def build(out: Path) -> list[dict]:
    manifest = []
    for i, spec in enumerate(MATERIALS):
        seed = 19040714 + i * 101
        rng = np.random.default_rng(seed)
        h, color, rough, strength = SURFACES[spec["kind"]](spec, rng)
        ngl, _ndx, ao = base.maps_from_height(h, strength)
        metal = np.zeros_like(h)
        orm = np.stack((ao, rough, metal), axis=-1)
        d = out / spec["group"] / spec["id"]
        d.mkdir(parents=True, exist_ok=True)
        stem = spec["id"]
        base.save_png8(d / f"{stem}_basecolor.png", color / 255.0)
        base.save_png8(d / f"{stem}_normal_gl.png", ngl)
        base.save_png16(d / f"{stem}_height16.png", h)
        base.save_png8(d / f"{stem}_orm.png", orm)
        base.save_jpg(d / f"{stem}_basecolor_web.jpg", color / 255.0, 86)
        base.save_jpg(d / f"{stem}_normal_gl_web.jpg", ngl, 92)
        base.save_jpg(d / f"{stem}_orm_web.jpg", orm, 90)
        data = {
            **{k: v for k, v in spec.items()},
            "span_along_m": spec["span_m"],
            "resolution_px": SIZE,
            "px_per_m": round(SIZE / spec["span_m"], 2),
            "confidence": "reconstructed appearance; which ground carries it is data/railway/1904_spec.json's to say",
            "orientation": "image x = along the track (renderer u); image y = across it (v)",
            "color_space": {"basecolor": "sRGB", "normal_gl": "linear", "height16": "linear 16-bit",
                            "orm": "linear; R=AO G=Roughness B=Metallic"},
            "web": {s: f"{stem}_{s}_web.jpg" for s in WEB_SUFFIXES},
            "seamless": True,
            "generator_seed": seed,
            "generation_method": "deterministic procedural synthesis (tools/generate_prairie_1904_rail.py); no photograph sampled",
        }
        (d / "material.json").write_text(json.dumps(data, indent=2) + "\n")
        manifest.append(data)

    seed = 19040714 + len(MATERIALS) * 101
    rng = np.random.default_rng(seed)
    d = out / TUFT["group"] / TUFT["id"]
    d.mkdir(parents=True, exist_ok=True)
    tuft = grass_tuft(rng, TUFT["width_px"], TUFT["height_px"])
    buf = io.BytesIO()
    tuft.save(buf, format="PNG", optimize=True)
    (d / "grass_tuft_web.png").write_bytes(buf.getvalue())
    tdata = {**TUFT, "width_m": round(TUFT["height_m"] * TUFT["width_px"] / TUFT["height_px"], 3),
             "web": {"basecolor_alpha": "grass_tuft_web.png"},
             "color_space": {"basecolor_alpha": "sRGB colour, linear alpha"},
             "confidence": "reconstructed appearance",
             "generator_seed": seed,
             "generation_method": "deterministic procedural drawing (tools/generate_prairie_1904_rail.py); no photograph sampled"}
    (d / "material.json").write_text(json.dumps(tdata, indent=2) + "\n")
    manifest.append(tdata)

    (out / "manifest.json").write_text(json.dumps(
        {"library": "Prairie Avenue 1904 lakefront railway PBR materials", "version": "1.0.0",
         "ticket": "T-2478", "materials": manifest}, indent=2) + "\n")
    contact_sheet(out, manifest)
    return manifest


def contact_sheet(out: Path, manifest: list[dict]):
    thumb, label, cols = 200, 46, len(manifest)
    sheet = Image.new("RGB", (cols * thumb, thumb + label), (26, 27, 25))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for i, m in enumerate(manifest):
        folder = out / m["group"] / m["id"]
        if "kind" in m:
            im = Image.open(folder / f'{m["id"]}_basecolor.png').convert("RGB")
            if m["span_across_m"] < 0.5:        # the tie: show it at its own proportion
                im = im.resize((thumb, max(8, int(thumb * m["span_across_m"] / m["span_m"]))))
                bg = Image.new("RGB", (thumb, thumb), (60, 58, 55))
                bg.paste(im, (0, thumb // 2 - im.height // 2))
                im = bg
            else:
                im = im.resize((thumb, thumb), Image.Resampling.LANCZOS)
            span = f'{m["span_m"]:.2f} x {m["span_across_m"]:.2f} m'
        else:
            t = Image.open(folder / "grass_tuft_web.png").convert("RGBA")
            t = t.resize((thumb // 2, thumb), Image.Resampling.LANCZOS)
            im = Image.new("RGBA", (thumb, thumb), (150, 170, 190, 255))
            im.alpha_composite(t, (thumb // 4, 0))
            im = im.convert("RGB")
            span = f'{m["width_m"]:.2f} x {m["height_m"]:.2f} m card'
        x = i * thumb
        sheet.paste(im, (x, 0))
        draw.text((x + 6, thumb + 6), m["id"].replace("_", " "), font=font, fill=(235, 232, 220))
        draw.text((x + 6, thumb + 22), span, font=font, fill=(166, 169, 157))
    buf = io.BytesIO()
    sheet.save(buf, format="JPEG", quality=88, optimize=True)
    (out / "contact_sheet.jpg").write_bytes(buf.getvalue())


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", type=Path, default=HERE.parent)
    a = ap.parse_args()
    for m in build(a.out):
        print(f'{m["group"]}/{m["id"]}')


if __name__ == "__main__":
    main()
