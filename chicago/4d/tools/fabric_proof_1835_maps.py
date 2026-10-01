#!/usr/bin/env python3
"""Pack the T-1801 proof's relief maps the way strategy A would ship them.

Strategy A (docs/RESEARCH/1835_photographic_fabric_preparation.md section 5) binds ONE
shared relief pair per substrate and keeps colour on the vertex. Its first patch needs the
basecolor's variation without a colour texture, so it is packed into the `orm` B channel,
which is metallic and therefore always 0 on a non-metal substrate:

    orl.R = AO            (the library's own)
    orl.G = roughness     (the library's own)
    orl.B = 0.5 * L / mean(L), clamped    L = linear luminance of the basecolor

and the renderer reads `colour = vertexColour * 2 * orl.B`, whose mean is 1. So the
household's finish stays the mean and the wood's grain is the variation around it.

Writes, for every substrate, `normal_gl.png` + `orl.png` at the library's 1024 px (Full,
Balanced) and a 512 px pair (Light), plus `material.json` carrying the span and the mean
roughness the second patch divides by. Nothing here is committed: the proof driver
(tools/fabric_proof_1835.sh) runs it into its work directory and the review reads bytes
from there, so the sizes it reports are the sizes this recipe produces.

    python3 tools/fabric_proof_1835_maps.py --out /tmp/fabric-proof-1835/maps
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
LIB = ROOT / "assets" / "textures" / "chicago_1835_pbr"

# substrate -> (library material, span override or None). The chinking reuses the
# chimney daub and is resampled to 2.04 m at 512 px -- 251 px/m, the log row's density
# (preparation map section 3, the one real texel defect).
SUBSTRATES = {
    "clapboard": ("walls/clapboard_board_face", None),
    "log": ("walls/hewn_log_face", None),
    "chinking": ("masonry/cat_and_clay_chimney", 512),
    "sign": ("props/signboard_weathered", None),
    "deck": ("waterfront/plank_walk_weathered", None),
    # the course-bearing maps the preparation map refused, kept to SHOW why
    "clapboard_courses": ("walls/clapboard_weathered_oak", None),
    "log_courses": ("walls/hewn_log_oak_chinked", None),
}


def srgb_to_linear(a):
    return np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)


def pack(src: Path, size: int, dst: Path) -> dict:
    sheet = json.loads((src / "material.json").read_text())
    mid = sheet["id"]
    base = np.asarray(Image.open(src / f"{mid}_basecolor.png").convert("RGB").resize(
        (size, size), Image.Resampling.LANCZOS), dtype=np.float32) / 255.0
    lin = srgb_to_linear(base)
    lum = 0.2126 * lin[..., 0] + 0.7152 * lin[..., 1] + 0.0722 * lin[..., 2]
    ratio = np.clip(0.5 * lum / max(float(lum.mean()), 1e-6), 0.0, 1.0)
    orm = np.asarray(Image.open(src / f"{mid}_orm.png").convert("RGB").resize(
        (size, size), Image.Resampling.LANCZOS), dtype=np.uint8).copy()
    orm[..., 2] = np.clip(ratio * 255 + 0.5, 0, 255).astype(np.uint8)
    nrm = Image.open(src / f"{mid}_normal_gl.png").convert("RGB").resize(
        (size, size), Image.Resampling.LANCZOS)
    dst.mkdir(parents=True, exist_ok=True)
    nrm.save(dst / "normal_gl.png", optimize=True)
    Image.fromarray(orm).save(dst / "orl.png", optimize=True)
    return {"library_id": mid, "span_m": sheet["span_m"],
            "mean_roughness": float(orm[..., 1].mean()) / 255.0,
            "albedo_ratio_spread": [round(float(np.percentile(2 * ratio, q)), 3) for q in (5, 50, 95)],
            "px": size, "px_per_m": round(size / sheet["span_m"], 1),
            "bytes": (dst / "normal_gl.png").stat().st_size + (dst / "orl.png").stat().st_size}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    out = {}
    for key, (rel, override) in SUBSTRATES.items():
        src = LIB / rel
        full = override or 1024
        rec = {"full": pack(src, full, a.out / key / "1024"),
               "light": pack(src, max(full // 2, 256), a.out / key / "512")}
        if override:
            rec["span_m_override"] = round(override / 251.0, 2)
            for t in ("full", "light"):
                rec[t]["span_m"] = rec["span_m_override"]
                rec[t]["px_per_m"] = round(rec[t]["px"] / rec["span_m_override"], 1)
        out[key] = rec
    (a.out / "maps.json").write_text(json.dumps(out, indent=2) + "\n")
    for k, r in out.items():
        print(f"{k:18s} {r['full']['library_id']:30s} span {r['full']['span_m']} m "
              f"{r['full']['px_per_m']} px/m  {r['full']['bytes']/1e6:.2f} MB full, "
              f"{r['light']['bytes']/1e6:.2f} MB light  ratio p5/50/95 {r['full']['albedo_ratio_spread']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
