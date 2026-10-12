#!/usr/bin/env python3
"""The K04 roof library's study sheet: every fabric on a metric panel, in raking and diffuse light.

    python3 assets/textures/prairie_1904_roofs/tools/study_prairie_1904_roofs.py

Writes docs/RESEARCH/k04-roof-library/study.jpg and costs.json. Each fabric is laid on
a 2.6 x 1.8 m panel of roof, mapped the way a K01 roof maps it (u, v in surface
metres over tile_m, so the panel repeats the tile and a seam would show), and shaded
twice from its own web maps — the files the renderer would bind:

  * RAKING: one sun 12 degrees above the roof plane, from up-slope and to the left, the
    light that finds a butt step, a seam rib, an oversized slate or a baked highlight;
  * DIFFUSE: an overcast sky, which is what most of the town is seen under.

A 1 m bar sits in each panel's corner. This is a study of the maps, not a render of
the scene: a plain Lambert + GGX shader on the CPU, so it answers what the map
carries, not what three.js's lights will do to it.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

LIB = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "docs" / "RESEARCH" / "k04-roof-library"
PANEL_M = (2.6, 1.8)
PX_PER_M = 140
LABEL = 20


def load(path, mode="RGB"):
    return np.asarray(Image.open(path).convert(mode), dtype=np.float32) / 255.


def sample(img, u, v):
    """Bilinear, wrapping; u, v in tile units with v up (image row 0 is v = 1)."""
    h, w = img.shape[:2]
    x = np.mod(u, 1.) * w - .5
    y = np.mod(1. - np.mod(v, 1.), 1.) * h - .5
    x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
    fx, fy = (x - x0)[..., None], (y - y0)[..., None]
    x0, y0 = np.mod(x0, w), np.mod(y0, h)
    x1, y1 = np.mod(x0 + 1, w), np.mod(y0 + 1, h)
    a = img[y0, x0] * (1 - fx) + img[y0, x1] * fx
    b = img[y1, x0] * (1 - fx) + img[y1, x1] * fx
    return a * (1 - fy) + b * fy


def shade(alb, n, rough, metal, ao, lights, ambient):
    lin = alb ** 2.2
    view = np.array([0., 0., 1.])
    f0 = .04 * (1 - metal) + lin * metal
    out = ambient * lin * (1 - metal) * ao * (.55 + .45 * n[..., 2:3])
    out = out + ambient * .25 * f0 * ao
    a2 = np.clip(rough, .05, 1) ** 4
    for ldir, intensity in lights:
        ldir = np.asarray(ldir) / np.linalg.norm(ldir)
        ndl = np.clip((n * ldir).sum(-1, keepdims=True), 0, None)
        hv = (ldir + view) / np.linalg.norm(ldir + view)
        ndh = np.clip((n * hv).sum(-1, keepdims=True), 0, None)
        d = a2 / (np.pi * (ndh ** 2 * (a2 - 1) + 1) ** 2)
        ndv = np.clip(n[..., 2:3], 1e-3, None)
        k = (np.sqrt(a2) + 1) ** 2 / 8
        g = (ndl / (ndl * (1 - k) + k)) * (ndv / (ndv * (1 - k) + k))
        vdh = float(np.dot(view, hv))
        f = f0 + (1 - f0) * (1 - vdh) ** 5
        spec = d * g * f / np.clip(4 * ndl * ndv, 1e-3, None)
        diff = lin * (1 - metal) / np.pi
        out = out + intensity * ndl * (diff + spec)
    out = out / (1 + out)                      # Reinhard, then display gamma
    return np.clip(out ** (1 / 2.2), 0, 1)


def panel(mat, folder):
    w, h = int(PANEL_M[0] * PX_PER_M), int(PANEL_M[1] * PX_PER_M)
    xs = (np.arange(w) + .5) / PX_PER_M
    ys = (np.arange(h)[::-1] + .5) / PX_PER_M          # top row of the panel is uphill
    um, vm = np.meshgrid(xs, ys)
    tu, tv = mat["tile_m"]
    u, v = um / tu, vm / tv
    web = mat["web"]
    alb = sample(load(folder / web["basecolor"]), u, v)
    n = sample(load(folder / web["normal_gl"]), u, v) * 2 - 1
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    orm = sample(load(folder / web["orm"]), u, v)
    ao, rough, metal = orm[..., :1], orm[..., 1:2], orm[..., 2:3]
    sun = (np.cos(np.radians(12)) * -.6, np.cos(np.radians(12)) * .8, np.sin(np.radians(12)))
    raking = shade(alb, n, rough, metal, ao, [(sun, 9.)], .25)
    diffuse = shade(alb, n, rough, metal, ao, [((0., .35, 1.), 1.6)], 1.4)
    out = []
    for img in (raking, diffuse):
        im = Image.fromarray((img * 255 + .5).astype(np.uint8), "RGB")
        d = ImageDraw.Draw(im)
        y = h - 10
        d.rectangle([8, y - 4, 8 + PX_PER_M, y], fill=(250, 250, 245), outline=(20, 20, 20))
        d.text((12 + PX_PER_M, y - 12), "1 m", fill=(250, 250, 245))
        out.append(im)
    return out


def main() -> int:
    manifest = json.loads((LIB / "manifest.json").read_text(encoding="utf-8"))
    mats = [json.loads((LIB / m["material"]).read_text(encoding="utf-8")) for m in manifest["materials"]]
    pw, ph = int(PANEL_M[0] * PX_PER_M), int(PANEL_M[1] * PX_PER_M)
    cell_w, cell_h, gap = 2 * pw + 6, ph + LABEL, 14
    per_row = 2
    rows = (len(mats) + per_row - 1) // per_row
    sheet = Image.new("RGB", (per_row * cell_w + (per_row + 1) * gap,
                              rows * cell_h + (rows + 1) * gap + 24), (246, 244, 240))
    d = ImageDraw.Draw(sheet)
    d.text((gap, 8), "K04 roof library (T-2292) - each fabric on a 2.6 x 1.8 m roof panel: "
                     "left raking sun 12 deg, right overcast. Reconstructed appearance (L-k04-roof-library-2292).",
           fill=(30, 30, 30))
    costs = []
    for i, mat in enumerate(mats):
        folder = LIB / mat["id"]
        rak, dif = panel(mat, folder)
        x = gap + (i % per_row) * (cell_w + gap)
        y = 24 + gap + (i // per_row) * (cell_h + gap)
        tu, tv = mat["tile_m"]
        d.text((x, y + 3), f"{mat['id']}  ({mat['slot']}, tile {tu:.3f} x {tv:.3f} m)", fill=(30, 30, 30))
        sheet.paste(rak, (x, y + LABEL))
        sheet.paste(dif, (x + pw + 6, y + LABEL))
        files = sorted(p for p in folder.iterdir() if p.is_file())
        web = [folder / f for f in mat["web"].values()]
        costs.append({
            "id": mat["id"],
            "resolution_px": mat["resolution_px"],
            "px_per_m": mat["px_per_m"],
            "master_bytes": sum(p.stat().st_size for p in files if p not in web),
            "web_bytes": sum(p.stat().st_size for p in web),
            # Three RGBA8 textures with a full mip chain, as a renderer uploads them.
            "gpu_bytes_estimate": int(3 * mat["resolution_px"] ** 2 * 4 * 4 / 3),
        })
    OUT.mkdir(parents=True, exist_ok=True)
    sheet.save(OUT / "study.jpg", quality=86, optimize=True)
    total = {k: sum(c[k] for c in costs) for k in ("master_bytes", "web_bytes", "gpu_bytes_estimate")}
    (OUT / "costs.json").write_text(json.dumps({"fabrics": costs, "total": total}, indent=2) + "\n",
                                    encoding="utf-8")
    print(f"  study.jpg {sheet.size[0]} x {sheet.size[1]}; web {total['web_bytes']} B, "
          f"masters {total['master_bytes']} B, GPU ~{total['gpu_bytes_estimate']} B")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
