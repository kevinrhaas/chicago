"""The K14 condition kit: age, surface variation and ground contact, evaluated from data.

TICKET T-2324 (piece 1 of T-1856, K14). Every number is data in
`data/components/prairie_1904/k14_condition.json`; this module is the one shared evaluator
any generator calls, so a wall, a roof, a joint, a painted board and a yard all weather by
the same rules:

  wall       ground damp at the foot, eave soot under the soffit and water trails below sills
             and outlets, multiplied, scaled by the fabric's response and held at the floor.
             `wall_tone` returns the multiplier the renderer's `_TONE` vertex channel takes
             (buildings.js applyPieceTone); `wall_mask` evaluates the same function on a grid,
             for a baked mask. `wall_breaks` gives the heights a wall needs a vertex row at.
  roof       the chimney plume on the covering leeward of a stack (`roof_tone`).
  joint      a geometry joint's extra recess and its tone, per K03 mortar (`mortar`).
  paint      painted timber weathers only since its last repaint (`paint_tone`).
  ground     the bare strip where a lawn meets a wall (`grass_bare`) and the wear across a
             walk or drive (`path_wear`): weights in [0, 1], not tones.

Everything is a function of the building's years standing on the target date (1904-07-01),
so a new Georgian front and a house of the 1860s beside it differ by data, not by hand, and of
the property's own seed (sha256 of its stable structure id), so a property weathers the same
on every build and independently of its neighbours. No layer removes or adds fabric.

WHY A VERTEX MULTIPLIER FIRST: the renderer already multiplies `_TONE` into colour, so a
generator that writes it costs no texture, no draw and no shader change; a grey multiplier
keeps every fabric's own hue. A baked mask is the same function sampled, for a surface whose
vertices are too sparse to carry a streak.

    python3 generators/archetypes/k14_condition.py            print the comparison table
    python3 generators/archetypes/k14_condition.py --study    write the study and its costs
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
import zlib
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DATA = ROOT / "data" / "components" / "prairie_1904" / "k14_condition.json"
STUDY_DIR = ROOT / "docs" / "RESEARCH" / "k14-condition-kit"


def load(path: Path = DATA) -> dict:
    return json.loads(Path(path).read_text())


def property_seed(structure_id: str) -> int:
    """The data's seed rule: the first 8 hex digits of sha256('k14|' + id)."""
    return int(hashlib.sha256(f"k14|{structure_id}".encode()).hexdigest()[:8], 16)


def _salt(name: str) -> int:
    return zlib.crc32(name.encode()) & 0xFFFFFFFF


def _lattice(seed: int, i) -> np.ndarray:
    """A deterministic value in [-1, 1] per integer lattice point (a 32-bit integer hash)."""
    m = np.uint64(0xFFFFFFFF)
    h = (np.asarray(i, dtype=np.int64).astype(np.uint64) * np.uint64(0x9E3779B1)
         + np.uint64(seed & 0xFFFFFFFF) * np.uint64(0x85EBCA77)) & m
    h ^= h >> np.uint64(15)
    h = (h * np.uint64(0x2C1B3C6D)) & m
    h ^= h >> np.uint64(12)
    h = (h * np.uint64(0x297A2D39)) & m
    h ^= h >> np.uint64(15)
    return h.astype(np.float64) / 4294967295.0 * 2.0 - 1.0


def noise(seed: int, t, wavelength: float) -> np.ndarray:
    """Smooth 1-D value noise in [-1, 1] along t metres, one lattice point per wavelength."""
    u = np.asarray(t, dtype=np.float64) / wavelength
    i = np.floor(u)
    f = u - i
    s = f * f * (3.0 - 2.0 * f)
    a, b = _lattice(seed, i), _lattice(seed, i + 1)
    return a + (b - a) * s


def _out(v, scalar: bool):
    return float(np.asarray(v).reshape(-1)[0]) if scalar else v


def _lerp(spec: dict, a: float) -> float:
    new = spec.get("new", 0.0)
    return new + (spec["full"] - new) * a


class Condition:
    """The kit's data, read once, and every layer as a function of it."""

    def __init__(self, data: dict | None = None):
        self.data = data if data is not None else load()
        d = self.data
        self.layers = d["layers"]
        self.floor = d["floor"]["min_tone"]
        self.full_years = d["age"]["full_years"]
        self.target = d["target_date"]
        y, m, day = (int(p) for p in self.target.split("-"))
        self.target_year = y + (m - 1) / 12.0 + (day - 1) / 365.0

    # -- age and response -------------------------------------------------------------------
    def years(self, built: float) -> float:
        """Years standing on the target date; `built` is a completion year (mid-year)."""
        return max(0.0, self.target_year - (float(built) + 0.5))

    def factor(self, built: float) -> float:
        return min(max(self.years(built) / self.full_years, 0.0), 1.0)

    def response(self, fabric: str | None) -> float:
        if fabric is None:
            return 1.0
        return self.data["fabric_response"][fabric]

    def _hold(self, tone, scalar):
        return _out(np.maximum(tone, self.floor), scalar)

    # -- wall layers, each a darkening in [0, 1) --------------------------------------------
    def damp_top(self, a: float) -> float:
        return _lerp(self.layers["ground_damp"]["top_m"], a)

    def soot_depth(self, a: float) -> float:
        return _lerp(self.layers["eave_soot"]["depth_m"], a)

    def ground_damp(self, x, y, a: float, seed: int) -> np.ndarray:
        L = self.layers["ground_damp"]
        x, y = np.asarray(x, dtype=np.float64), np.asarray(y, dtype=np.float64)
        top = self.damp_top(a) + L["wobble_m"] * a * noise(seed ^ _salt("ground_damp"), x,
                                                           L["wobble_wavelength_m"])
        top = np.maximum(top, 1e-6)
        t = np.clip(y / top, 0.0, 1.0)
        return np.where(y < top, (1.0 - L["tone"]["full"]) * a * (1.0 - t), 0.0)

    def eave_soot(self, y, soffit_m: float, a: float) -> np.ndarray:
        L = self.layers["eave_soot"]
        y = np.asarray(y, dtype=np.float64)
        depth = max(self.soot_depth(a), 1e-6)
        top = soffit_m - depth
        t = np.clip((y - top) / depth, 0.0, 1.0)
        return np.where(y > top, (1.0 - L["tone"]["full"]) * a * t, 0.0)

    def trail_length(self, source: dict, index: int, a: float, seed: int) -> float:
        L = self.layers["water_trails"]
        spec = L["sources"][source["kind"]]
        j = float(_lattice(seed ^ _salt("water_trails"), index))
        return _lerp(spec["length_m"], a) * (1.0 + L["jitter"] * j)

    def water_trail(self, x, y, source: dict, index: int, a: float, seed: int) -> np.ndarray:
        """A streak below `source` ({kind, x0, x1, y}: its horizontal extent and its foot)."""
        L = self.layers["water_trails"]
        spec = L["sources"][source["kind"]]
        x, y = np.asarray(x, dtype=np.float64), np.asarray(y, dtype=np.float64)
        length = max(self.trail_length(source, index, a, seed), 1e-6)
        below = source["y"] - y
        t = np.clip(below / length, 0.0, 1.0)
        c = (source["x0"] + source["x1"]) / 2.0
        half = (source["x1"] - source["x0"]) / 2.0 * (1.0 - (1.0 - spec["taper"]) * t)
        outside = np.abs(x - c) - half
        edge = np.clip(1.0 - outside / L["edge_soft_m"], 0.0, 1.0)
        inside = (below >= 0.0) & (below <= length)
        # run-off leaves the source in rivulets, not a sheet: the streak's strength varies
        # across it by the seed, between 1 - streaks and 1 of its full value
        rill = 1.0 - L["streaks"] * 0.5 * (1.0 + noise(seed ^ _salt("rills") ^ index, x,
                                                       L["streak_wavelength_m"]))
        dark = (1.0 - spec["tone"]["full"]) * a * (1.0 - t) * edge * rill
        return np.where(inside, dark, 0.0)

    def wall_tone(self, y, soffit_m: float, *, built: float, fabric: str, seed: int,
                  x=0.0, sources: tuple = ()):
        """The `_TONE` multiplier of a wall point (x along the wall, y above grade, metres)."""
        scalar = np.ndim(y) == 0 and np.ndim(x) == 0
        a, k = self.factor(built), self.response(fabric)
        x = np.asarray(x, dtype=np.float64)
        y = np.asarray(y, dtype=np.float64)
        tone = (1.0 - k * self.ground_damp(x, y, a, seed)) * (1.0 - k * self.eave_soot(y, soffit_m, a))
        for n, src in enumerate(sources):
            tone = tone * (1.0 - k * self.water_trail(x, y, src, n, a, seed))
        if fabric == "painted_timber":
            tone = tone * self.paint_tone(built, seed)
        return self._hold(tone, scalar)

    def wall_mask(self, width_m: float, height_m: float, px_per_m: float, soffit_m: float, *,
                  built: float, fabric: str, seed: int, sources: tuple = ()) -> np.ndarray:
        """`wall_tone` on a grid, row 0 at the top (soffit side), for a baked mask."""
        w, h = int(round(width_m * px_per_m)), int(round(height_m * px_per_m))
        xs = (np.arange(w) + 0.5) / px_per_m
        ys = height_m - (np.arange(h) + 0.5) / px_per_m
        X, Y = np.meshgrid(xs, ys)
        return self.wall_tone(Y, soffit_m, built=built, fabric=fabric, seed=seed, x=X,
                              sources=sources)

    def wall_breaks(self, soffit_m: float, *, built: float, sources: tuple = (),
                    seed: int = 0) -> list:
        """Heights a wall needs a vertex row at so `_TONE` can carry its layers."""
        a = self.factor(built)
        if a <= 0.0:
            return []
        L = self.layers["ground_damp"]
        rows = {round(self.damp_top(a) - L["wobble_m"] * a, 4),
                round(self.damp_top(a) + L["wobble_m"] * a, 4),
                round(soffit_m - self.soot_depth(a), 4)}
        for n, src in enumerate(sources):
            rows.add(round(src["y"], 4))
            rows.add(round(src["y"] - self.trail_length(src, n, a, seed), 4))
        return sorted(r for r in rows if 0.0 < r < soffit_m)

    # -- roof, joint, paint ------------------------------------------------------------------
    def roof_tone(self, dx, dz, *, built: float, fabric: str | None = None):
        """The chimney plume on the covering at (dx east, dz north) metres from a stack."""
        scalar = np.ndim(dx) == 0 and np.ndim(dz) == 0
        L = self.layers["chimney_soot"]
        a, k = self.factor(built), self.response(fabric)
        dx, dz = np.asarray(dx, dtype=np.float64), np.asarray(dz, dtype=np.float64)
        r = np.hypot(dx, dz)
        bearing = np.degrees(np.arctan2(dx, dz)) % 360.0
        off = np.abs((bearing - L["lee_bearing_deg"] + 180.0) % 360.0 - 180.0)
        length = max(_lerp(L["length_m"], a), 1e-6)
        inside = (off <= L["half_angle_deg"]) & (r <= length)
        spread = np.cos(np.clip(off / L["half_angle_deg"], 0.0, 1.0) * math.pi / 2.0)
        dark = np.where(inside, (1.0 - L["tone"]["full"]) * a * (1.0 - r / length) * spread, 0.0)
        return self._hold(1.0 - k * dark, scalar)

    def mortar(self, mortar_id: str, *, built: float) -> dict:
        spec = self.layers["mortar"]["by_mortar"][mortar_id]
        a = self.factor(built)
        return {"tone": round(max(1.0 - (1.0 - spec["tone"]["full"]) * a, self.floor), 4),
                "recess_extra_mm": round(spec["recess_extra_mm"]["full"] * a, 3)}

    def paint_age(self, built: float, seed: int) -> float:
        cycle = self.layers["paint"]["cycle_years"]
        years = self.years(built)
        offset = (seed ^ _salt("paint")) % cycle
        return min(years, (years + offset) % cycle)

    def paint_tone(self, built: float, seed: int) -> float:
        L = self.layers["paint"]
        frac = self.paint_age(built, seed) / L["cycle_years"]
        return max(1.0 - (1.0 - L["tone"]["full"]) * frac, self.floor)

    # -- ground -----------------------------------------------------------------------------
    def grass_bare(self, d, along, *, built: float, seed: int):
        """Weight of bare earth d metres out from a wall foot, `along` metres along it."""
        scalar = np.ndim(d) == 0 and np.ndim(along) == 0
        L = self.layers["grass_edge"]
        a = self.factor(built)
        d = np.asarray(d, dtype=np.float64)
        width = _lerp(L["width_m"], a) + L["wobble_m"] * a * noise(
            seed ^ _salt("grass_edge"), along, L["wobble_wavelength_m"])
        width = np.maximum(width, 1e-6)
        return _out(np.clip(1.0 - d / width, 0.0, 1.0) * (d >= 0.0), scalar)

    def path_wear(self, offset, along, *, use: str, built: float, seed: int):
        """Weight of wear `offset` metres across a walk or drive's centre line."""
        scalar = np.ndim(offset) == 0 and np.ndim(along) == 0
        spec = self.layers["path_wear"]["uses"][use]
        a = self.factor(built)
        off = np.asarray(offset, dtype=np.float64)
        dist = np.min(np.stack([np.abs(off - c) for c in spec["lines_m"]]), axis=0)
        core = np.where(dist <= spec["core_half_m"], 1.0,
                        np.clip(1.0 - (dist - spec["core_half_m"]) / spec["falloff_m"], 0.0, 1.0))
        breakup = 1.0 + 0.15 * noise(seed ^ _salt("path_wear"), along, 0.8)
        return _out(np.clip(core * spec["strength"] * a * breakup, 0.0, 1.0), scalar)


# -- the study ------------------------------------------------------------------------------
TEX = ROOT / "assets" / "textures"
#: (label, fabric id for the response, basecolor, tile in metres)
STUDY_FABRICS = (
    ("pressed red brick (K03)", "pressed_red",
     TEX / "prairie_1904_brick/panel/pressed_red_running/pressed_red_running_basecolor.png"),
    ("common buff brick (K03)", "common_buff",
     TEX / "prairie_1904_brick/panel/common_buff_common_6/common_buff_common_6_basecolor.png"),
    ("Bedford limestone (K02)", "limestone_bedford",
     TEX / "prairie_1904_stone/limestone_bedford/limestone_bedford_basecolor.png"),
    ("brown sandstone (K02)", "sandstone_brown",
     TEX / "prairie_1904_stone/sandstone_brown/sandstone_brown_basecolor.png"),
)
SILL_TEX = TEX / "prairie_1904_stone/dressed_trim/dressed_trim_basecolor.png"
PPM = 80                       # study pixels per metre
WALL_W, WALL_H = 3.0, 4.5      # the elevation: grade to soffit
GROUND_D = 1.2                 # the plan strip in front of the wall
WINDOW = (0.5, 1.5, 1.2, 3.0)  # x0, x1, y0, y1
SILL = {"kind": "sill", "x0": 0.4, "x1": 1.6, "y": 1.12}
OUTLET = {"kind": "outlet", "x0": 2.25, "x1": 2.4, "y": 3.9}
PIPE = (2.6, 2.7)
WALK = (1.75, 2.85)            # a service walk running out from the wall, plan x range
STUDY_ID = "k14-study"         # the study's property id, so its seed is a fixed one


def _to_linear(c):
    c = np.asarray(c, dtype=np.float64) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def _to_srgb(c):
    c = np.clip(c, 0.0, 1.0)
    return np.round(255.0 * np.where(c <= 0.0031308, c * 12.92,
                                     1.055 * c ** (1 / 2.4) - 0.055)).astype(np.uint8)


def _fabric_field(path: Path, w: int, h: int) -> np.ndarray:
    """The fabric's basecolor tiled at its own metric tile, linear RGB, h x w."""
    from PIL import Image
    tile_m = json.loads((path.parent / "material.json").read_text())["tile_m"]
    img = Image.open(path).convert("RGB")
    tw, th = max(1, round(tile_m[0] * PPM)), max(1, round(tile_m[1] * PPM))
    tile = _to_linear(np.asarray(img.resize((tw, th), Image.LANCZOS)))
    reps = (h // th + 2, w // tw + 2, 1)
    return np.tile(tile, reps)[:h, :w]


def study_tile(cond: Condition, fabric: str, tex: Path, built: float, seed: int):
    """One elevation and its plan strip, linear RGB, plus the wall's tone field."""
    w, h, g = round(WALL_W * PPM), round(WALL_H * PPM), round(GROUND_D * PPM)
    body = _fabric_field(tex, w, h)
    xs = (np.arange(w) + 0.5) / PPM
    ys = WALL_H - (np.arange(h) + 0.5) / PPM
    X, Y = np.meshgrid(xs, ys)
    tone = cond.wall_tone(Y, WALL_H, built=built, fabric=fabric, seed=seed, x=X,
                          sources=(SILL, OUTLET))
    sill_tone = cond.wall_tone(Y, WALL_H, built=built, fabric="dressed_trim", seed=seed, x=X)
    wall = body * tone[..., None]
    sill = _fabric_field(SILL_TEX, w, h) * sill_tone[..., None]
    in_win = (X >= WINDOW[0]) & (X <= WINDOW[1]) & (Y >= WINDOW[2]) & (Y <= WINDOW[3])
    in_sill = (X >= SILL["x0"]) & (X <= SILL["x1"]) & (Y >= SILL["y"]) & (Y < WINDOW[2])
    in_spout = (X >= OUTLET["x0"]) & (X <= OUTLET["x1"]) & (Y >= OUTLET["y"]) & (Y <= OUTLET["y"] + 0.1)
    in_pipe = (X >= PIPE[0]) & (X <= PIPE[1])
    wall = np.where(in_sill[..., None], sill, wall)
    wall = np.where(in_win[..., None], _to_linear((38, 44, 50)), wall)
    wall = np.where((in_spout | in_pipe)[..., None], _to_linear((52, 54, 52)), wall)
    # the plan strip: row 0 at the wall foot, d metres out
    gx = (np.arange(w) + 0.5) / PPM
    gd = (np.arange(g) + 0.5) / PPM
    GX, GD = np.meshgrid(gx, gd)
    bare = cond.grass_bare(GD, GX, built=built, seed=seed)
    lawn, earth = _to_linear((74, 98, 52)), _to_linear((104, 90, 70))
    ground = lawn * (1 - bare[..., None]) + earth * bare[..., None]
    c = (WALK[0] + WALK[1]) / 2.0
    on_walk = np.abs(GX - c) <= (WALK[1] - WALK[0]) / 2.0
    wear = cond.path_wear(GX - c, GD, use="service_walk", built=built, seed=seed)
    cinder = _to_linear((132, 124, 112)) * (1.0 - 0.22 * wear[..., None])
    ground = np.where(on_walk[..., None], cinder, ground)
    open_wall = ~(in_win | in_sill | in_spout | in_pipe)
    return wall, ground, tone, body, open_wall


def _lum(rgb):
    return rgb[..., 0] * 0.2126 + rgb[..., 1] * 0.7152 + rgb[..., 2] * 0.0722


def study(write: bool = True) -> dict:
    """Render the comparison (rows: fabrics; columns: new, 20 and 38 years) and measure it."""
    from PIL import Image, ImageDraw, ImageFont
    cond = Condition()
    seed = property_seed(STUDY_ID)
    ages = cond.data["age"]["comparison"]
    cols = [ages["new"], ages["middle"], ages["old"]]
    w, h, g = round(WALL_W * PPM), round(WALL_H * PPM), round(GROUND_D * PPM)
    pad, left, head = 12, 190, 44
    W = left + len(cols) * (w + pad) + pad
    H = head + len(STUDY_FABRICS) * (h + g + 6 + pad) + pad
    canvas = Image.new("RGB", (W, H), (236, 234, 228))
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default(size=15)
    for ci, col in enumerate(cols):
        years = cond.years(col["built"])
        draw.text((left + ci * (w + pad), 12),
                  f"built {col['built']}: {years:.0f} years in 1904", fill=(30, 30, 30), font=font)
    measured = []
    for ri, (label, fabric, tex) in enumerate(STUDY_FABRICS):
        y0 = head + ri * (h + g + 6 + pad)
        draw.text((pad, y0 + h // 2 - 8), label, fill=(30, 30, 30), font=font)
        for ci, col in enumerate(cols):
            wall, ground, tone, body, open_wall = study_tile(cond, fabric, tex, col["built"], seed)
            x0 = left + ci * (w + pad)
            canvas.paste(Image.fromarray(_to_srgb(wall)), (x0, y0))
            canvas.paste(Image.fromarray(_to_srgb(ground)), (x0, y0 + h + 6))
            ratio = float(_lum(wall)[open_wall].mean() / _lum(body)[open_wall].mean())
            measured.append({"fabric": fabric, "built": col["built"],
                             "years": round(cond.years(col["built"]), 2),
                             "mean_luminance_ratio": round(ratio, 4),
                             "min_tone": round(float(tone.min()), 4)})
    # costs: what a generator pays to carry the kit
    sample = np.linspace(0.0, WALL_H, 10)
    rows = cond.wall_breaks(WALL_H, built=1866, sources=(SILL, OUTLET), seed=seed)
    mask = cond.wall_mask(10.0, 12.0, 32, 12.0, built=1866, fabric="common_buff", seed=seed,
                          sources=(SILL, OUTLET))
    import io
    buf = io.BytesIO()
    Image.fromarray(np.round(mask * 255).astype(np.uint8), "L").save(buf, "PNG", optimize=True)
    costs = {
        "ticket": "T-2324",
        "study": {"image": "study.jpg", "px_per_m": PPM, "seed": seed,
                  "light": "identical neutral diffuse: linear albedo x tone, no shading"},
        "measured": measured,
        "vertex_channel": {
            "channel": "_TONE (SCALAR float32, 4 bytes a vertex)",
            "textures": 0, "draws": 0,
            "extra_rows_on_a_38_year_wall_with_a_sill_and_an_outlet": len(rows),
            "rows_m": rows,
        },
        "baked_mask": {"wall_m": [10.0, 12.0], "px_per_m": 32, "pixels": int(mask.size),
                       "png_bytes": len(buf.getvalue())},
        "sample_column_tone_38y_common_buff": [
            round(float(cond.wall_tone(float(v), WALL_H, built=1866, fabric="common_buff",
                                       seed=seed)), 4) for v in sample],
    }
    if write:
        STUDY_DIR.mkdir(parents=True, exist_ok=True)
        canvas.save(STUDY_DIR / "study.jpg", quality=86, optimize=True)
        costs["study"]["image_bytes"] = (STUDY_DIR / "study.jpg").stat().st_size
        (STUDY_DIR / "costs.json").write_text(json.dumps(costs, indent=2) + "\n")
    return costs


def main(argv: list) -> int:
    if "--study" in argv:
        costs = study(write=True)
        print(f"wrote {STUDY_DIR.relative_to(ROOT)}/study.jpg and costs.json")
        for m in costs["measured"]:
            print(f"  {m['fabric']:18} {m['built']}  {m['years']:5.1f} y  "
                  f"luminance x{m['mean_luminance_ratio']:.3f}  min tone {m['min_tone']:.3f}")
        return 0
    cond = Condition()
    for col in cond.data["age"]["comparison"].values():
        a = cond.factor(col["built"])
        print(f"{col['built']} ({col['label']}): a = {a:.3f}, damp top {cond.damp_top(a):.2f} m, "
              f"soot depth {cond.soot_depth(a):.2f} m")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
