#!/usr/bin/env python3
"""Gate the K14 condition kit (T-2324): the data, the shared evaluator and the study.

    python3 tools/check_condition_kit.py --check       every rule, on the committed kit
    python3 tools/check_condition_kit.py --self-test   break each rule in memory; each must refuse

The kit (data/components/prairie_1904/k14_condition.json, evaluated by
generators/archetypes/k14_condition.py) is the condition of each building on 1904-07-01. The
rules below are what keeps it that, and not a modern ruin or a clean model with a label on it:

  provenance  every layer and the floor carry a confidence from the validator's vocabulary and
              a note saying what the number rests on.
  range       every wall and roof tone, over every fabric, every age and every height, lies in
              [floor, 1]; every ground weight in [0, 1]; the floor itself in [0.55, 0.80], and
              no layer declared darker than it (a floor may hold a sum, never hide a ruin).
  age         an older building is never cleaner than a newer one, at any point, in any layer
              but paint (which renews on its cycle); the layers stop growing at full_years.
  1904        new work (built 1900 or later) reads clean: a study wall darkens under 2 per cent
              on average and nowhere under 0.96. A 38-year wall is visibly older but keeps its
              material: between 3 and 15 per cent darker on average.
  K03         the full-age damp and soot are the K03 1808 service wall's constants
              (generators/archetypes/k03_brick.py), so the shipped mask and the kit agree.
  fabrics     every K02 stone and K03 brick fabric and every K03 mortar has a response.
  trails      a trail is zero above its source and past its length, darkest under it, and no
              wider at its foot than its source.
  plume       the chimney plume lies leeward (the lee bearing is the east half, downwind of
              Chicago's westerlies) and never windward.
  paint       painted timber is never older than its repaint cycle (4 to 10 years), and the
              seed spreads the repaint years.
  seed        a property's seed is stable, and two properties' wobble differs.
  never       the `never` list names the ruin conditions, and no layer is one of them.
  study       docs/RESEARCH/k14-condition-kit/costs.json re-derives from the kit, and the image
              is committed.

It writes nothing: the study is written by the generator run with --study, which no gate runs.
"""

from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "generators" / "archetypes"))
import k14_condition as K  # noqa: E402

CONFIDENCE = {"attested", "inferred", "reconstructed"}
STONE = ROOT / "assets" / "textures" / "prairie_1904_stone"
BRICK = ROOT / "assets" / "textures" / "prairie_1904_brick" / "profiles.json"
K03 = ROOT / "generators" / "archetypes" / "k03_brick.py"
RUIN_WORDS = ("spall", "crack", "vegetation", "moss", "ivy", "lichen", "broken", "boarded",
              "graffiti", "peel", "missing", "rot")
AGES = (1904, 1902, 1900, 1894, 1884, 1874, 1866, 1860, 1840)
FABRICS_STUDY = [f for _, f, _ in K.STUDY_FABRICS]


def _ids():
    stone = sorted(p.parent.name for p in STONE.glob("*/material.json"))
    prof = json.loads(BRICK.read_text())
    brick = list(prof["fabrics"]) if isinstance(prof["fabrics"], dict) else [f["id"] for f in prof["fabrics"]]
    mortars = list(prof["mortars"]) if isinstance(prof["mortars"], dict) else [m["id"] for m in prof["mortars"]]
    return stone, brick, mortars


def _k03_constants() -> dict:
    src = K03.read_text()
    out = {}
    for a, b in (("DAMP_TOP_M", "DAMP_TONE"), ("SOOT_DEPTH_M", "SOOT_TONE")):
        m = re.search(rf"^{a}, {b} = ([0-9.]+), ([0-9.]+)", src, re.M)
        out[a], out[b] = (float(m.group(1)), float(m.group(2))) if m else (None, None)
    return out


def rules(data: dict) -> list:
    """(label, ok, detail) for every rule except the study's."""
    import numpy as np
    res = []

    def rule(label, ok, detail):
        res.append((label, bool(ok), detail))

    # provenance
    missing = [n for n, L in data["layers"].items()
               if L.get("confidence") not in CONFIDENCE or not str(L.get("note", "")).strip()]
    for part in ("floor", "age", "seed", "fabric_response"):
        if data[part].get("confidence") not in CONFIDENCE or not str(data[part].get("note", "")).strip():
            missing.append(part)
    rule("provenance", not missing, f"no confidence or note: {missing}" if missing else
         f"{len(data['layers'])} layers and 4 parts carry a confidence and a note")

    floor = data["floor"]["min_tone"]
    fulls = {n: L["tone"]["full"] for n, L in data["layers"].items() if "tone" in L}
    fulls.update({f"{n} {k}": v["tone"]["full"] for n in ("water_trails", "mortar")
                  for k, v in data["layers"][n].get("sources", data["layers"][n].get("by_mortar", {})).items()})
    under = [n for n, v in fulls.items() if v < floor]
    rule("floor", 0.55 <= floor <= 0.80 and not under,
         f"min_tone {floor} (0.55 to 0.80)" + (f"; layers declared darker than it: {under}" if under else
                                               f"; no layer's full tone is under it ({len(fulls)} tones)"))

    try:
        cond = K.Condition(data)
    except Exception as e:  # a broken file is a refusal, not a crash
        rule("evaluator", False, f"{type(e).__name__}: {e}")
        return res

    stone, brick, mortars = _ids()
    need = stone + brick + ["painted_timber"]
    lack = [f for f in need if f not in data["fabric_response"]]
    lack += [m for m in mortars if m not in data["layers"]["mortar"]["by_mortar"]]
    rule("fabrics", not lack, f"no response for {lack}" if lack else
         f"{len(stone)} K02 stones, {len(brick)} K03 bricks, painted timber, {len(mortars)} mortars")
    if lack:
        return res

    # range and age, on a grid of heights and sources
    seed = K.property_seed("k14-check")
    y = np.linspace(0.0, 12.0, 241)
    x = np.linspace(0.0, 6.0, 241)
    src = ({"kind": "sill", "x0": 1.0, "x1": 2.2, "y": 4.0},
           {"kind": "outlet", "x0": 3.0, "x1": 3.15, "y": 10.5})
    lo, hi, worse = 1.0, 0.0, []
    for fabric in need:
        prev = None
        for built in AGES:
            t = cond.wall_tone(y, 12.0, built=built, fabric=fabric, seed=seed, x=x, sources=src)
            lo, hi = min(lo, float(t.min())), max(hi, float(t.max()))
            if fabric == "painted_timber":   # paint renews on its cycle; every other layer ages
                t = t / cond.paint_tone(built, seed)
            if prev is not None and np.any(t > prev + 1e-9):
                worse.append(f"{fabric} {built}")
            prev = t
    dx, dz = np.meshgrid(np.linspace(-5, 5, 41), np.linspace(-5, 5, 41))
    prev = None
    for built in AGES:
        t = cond.roof_tone(dx, dz, built=built)
        lo, hi = min(lo, float(t.min())), max(hi, float(t.max()))
        if prev is not None and np.any(t > prev + 1e-9):
            worse.append(f"roof {built}")
        prev = t
    for m in mortars:
        seq = [cond.mortar(m, built=b) for b in AGES]
        lo = min(lo, *(s["tone"] for s in seq))
        hi = max(hi, *(s["tone"] for s in seq))
        if any(b["tone"] > a["tone"] + 1e-9 or b["recess_extra_mm"] < a["recess_extra_mm"] - 1e-9
               for a, b in zip(seq, seq[1:])):
            worse.append(f"mortar {m}")
    g_lo, g_hi = 1.0, 0.0
    d = np.linspace(0.0, 1.0, 101)
    along = np.linspace(0.0, 6.0, 101)
    for use in data["layers"]["path_wear"]["uses"]:
        prev = None
        for built in AGES:
            wgt = cond.path_wear(d - 0.5, along, use=use, built=built, seed=seed)
            g_lo, g_hi = min(g_lo, float(wgt.min())), max(g_hi, float(wgt.max()))
            if prev is not None and np.any(wgt < prev - 1e-9):
                worse.append(f"path {use} {built}")
            prev = wgt
    prev = None
    for built in AGES:
        wgt = cond.grass_bare(d, along, built=built, seed=seed)
        g_lo, g_hi = min(g_lo, float(wgt.min())), max(g_hi, float(wgt.max()))
        if prev is not None and np.any(wgt < prev - 1e-9):
            worse.append(f"grass {built}")
        prev = wgt
    rule("range", floor - 1e-9 <= lo and hi <= 1.0 + 1e-9 and 0.0 <= g_lo and g_hi <= 1.0,
         f"tones {lo:.3f} to {hi:.3f}, ground weights {g_lo:.3f} to {g_hi:.3f}")
    rule("age", not worse, f"older reads cleaner at {worse[:4]}" if worse else
         f"no point cleaner with age over {len(AGES)} ages, every layer")
    full = cond.full_years
    late = int(cond.target_year - full - 1)
    sat = all(np.allclose(cond.wall_tone(y, 12.0, built=late, fabric=f, seed=seed, x=x, sources=src),
                          cond.wall_tone(y, 12.0, built=late - 25, fabric=f, seed=seed, x=x, sources=src))
              for f in FABRICS_STUDY)
    rule("saturation", 20 <= full <= 60 and sat, f"full_years {full}; {late} and {late - 25} identical: {sat}")

    # 1904: new work clean, old work visible, on the study's own tiles
    new_bad, old_bad, stats = [], [], []
    for label, fabric, tex in K.STUDY_FABRICS:
        for built in (1900, 1902):
            wall, _, tone, body, open_wall = K.study_tile(cond, fabric, tex, built, K.property_seed(K.STUDY_ID))
            ratio = float(K._lum(wall)[open_wall].mean() / K._lum(body)[open_wall].mean())
            if ratio < 0.98 or float(tone.min()) < 0.96:
                new_bad.append(f"{fabric} {built}: x{ratio:.3f}, min {tone.min():.3f}")
        wall, _, tone, body, open_wall = K.study_tile(cond, fabric, tex, 1866, K.property_seed(K.STUDY_ID))
        ratio = float(K._lum(wall)[open_wall].mean() / K._lum(body)[open_wall].mean())
        stats.append(f"{fabric} x{ratio:.3f}")
        if not 0.85 <= ratio <= 0.97:
            old_bad.append(f"{fabric} x{ratio:.3f}")
    rule("new work clean", not new_bad, "; ".join(new_bad) if new_bad else
         "1900 and 1902 walls under 2 per cent darker, nowhere under 0.96")
    rule("old work visible, not ruined", not old_bad,
         f"38-year walls outside 0.85 to 0.97: {old_bad}" if old_bad else "38-year walls " + ", ".join(stats))

    # K03 agreement
    k3 = _k03_constants()
    L = data["layers"]
    pairs = [(k3["DAMP_TOP_M"], L["ground_damp"]["top_m"]["full"]), (k3["DAMP_TONE"], L["ground_damp"]["tone"]["full"]),
             (k3["SOOT_DEPTH_M"], L["eave_soot"]["depth_m"]["full"]), (k3["SOOT_TONE"], L["eave_soot"]["tone"]["full"])]
    rule("K03", all(a is not None and abs(a - b) < 1e-9 for a, b in pairs),
         f"k03_brick.py {[a for a, _ in pairs]} against the kit's full age {[b for _, b in pairs]}")

    # trails
    a = cond.factor(1866)
    tbad = []
    for n, s in enumerate(src):
        cx = (s["x0"] + s["x1"]) / 2.0
        length = cond.trail_length(s, n, a, seed)
        top = float(cond.water_trail(cx, s["y"] - 0.01, s, n, a, seed))
        if float(cond.water_trail(cx, s["y"] + 0.05, s, n, a, seed)) != 0.0:
            tbad.append(f"{s['kind']} above its source")
        if float(cond.water_trail(cx, s["y"] - length - 0.05, s, n, a, seed)) != 0.0:
            tbad.append(f"{s['kind']} past its length")
        col = cond.water_trail(np.full(50, cx), s["y"] - np.linspace(0.01, length, 50), s, n, a, seed)
        if top <= 0 or float(col.max()) > top + 1e-9 and not np.isclose(float(col.max()), top):
            tbad.append(f"{s['kind']} not darkest under its source")
        taper = L["water_trails"]["sources"][s["kind"]]["taper"]
        if not 0.0 < taper <= 1.0:
            tbad.append(f"{s['kind']} taper {taper} widens at its foot")
    rule("trails", not tbad, "; ".join(tbad) if tbad else "zero above and past, darkest under, narrowing")

    # plume
    lee = L["chimney_soot"]["lee_bearing_deg"]
    import math
    r = 1.0
    lee_pt = (r * math.sin(math.radians(lee)), r * math.cos(math.radians(lee)))
    wind_pt = (-lee_pt[0], -lee_pt[1])
    t_lee = cond.roof_tone(*lee_pt, built=1866)
    t_wind = cond.roof_tone(*wind_pt, built=1866)
    rule("plume", 0.0 < lee < 180.0 and t_lee < 1.0 and t_wind == 1.0,
         f"lee {lee} deg: {t_lee:.3f} leeward, {t_wind:.3f} windward")

    # paint
    cyc = L["paint"]["cycle_years"]
    ages_ok = all(cond.paint_age(b, K.property_seed(f"p{i}")) <= min(cyc, cond.years(b)) + 1e-9
                  for b in AGES for i in range(12))
    spread = len({round(cond.paint_age(1866, K.property_seed(f"p{i}")), 3) for i in range(12)})
    rule("paint", 4 <= cyc <= 10 and ages_ok and spread > 1,
         f"cycle {cyc} years; paint never older than its cycle: {ages_ok}; {spread} repaint phases in 12 houses")

    # seed
    s1, s2 = K.property_seed("pa-1808"), K.property_seed("pa-1808")
    w1 = cond.grass_bare(0.1, along, built=1866, seed=K.property_seed("pa-1808"))
    w2 = cond.grass_bare(0.1, along, built=1866, seed=K.property_seed("pa-1812"))
    rule("seed", s1 == s2 and not np.allclose(w1, w2), "stable per property, independent between two")

    # never
    nev = " ".join(data.get("never", [])).lower()
    named = [w for w in ("spall", "glass", "vegetation", "bare wood", "black") if w not in nev]
    ruin = [n for n in L if any(w in n.lower() for w in RUIN_WORDS)]
    rule("never", not named and not ruin,
         (f"never omits {named}" if named else "") + (f" ruin layers {ruin}" if ruin else "") or
         f"{len(data['never'])} ruin conditions named; no layer is one")
    return res


def study_rules() -> list:
    res = []
    costs_p = K.STUDY_DIR / "costs.json"
    img = K.STUDY_DIR / "study.jpg"
    if not costs_p.exists() or not img.exists():
        return [("study", False, "docs/RESEARCH/k14-condition-kit/study.jpg or costs.json is missing")]
    committed = json.loads(costs_p.read_text())
    fresh = K.study(write=False)
    drift = []
    for a, b in zip(committed["measured"], fresh["measured"]):
        if (a["fabric"], a["built"]) != (b["fabric"], b["built"]) or \
                abs(a["mean_luminance_ratio"] - b["mean_luminance_ratio"]) > 0.003 or \
                abs(a["min_tone"] - b["min_tone"]) > 0.003:
            drift.append(f"{a['fabric']} {a['built']}")
    if len(committed["measured"]) != len(fresh["measured"]):
        drift.append("row count")
    if committed["vertex_channel"] != fresh["vertex_channel"]:
        drift.append("vertex_channel")
    if committed["sample_column_tone_38y_common_buff"] != fresh["sample_column_tone_38y_common_buff"]:
        drift.append("sample column")
    res.append(("study", not drift, f"costs.json is stale ({drift}): run the generator with --study"
                if drift else f"costs.json re-derives; study.jpg {img.stat().st_size:,} B"))
    return res


def check() -> int:
    res = rules(K.load()) + study_rules()
    bad = [r for r in res if not r[1]]
    for label, ok, detail in res:
        print(f"{'ok  ' if ok else 'FAIL'} {label}: {detail}")
    print(f"{'ok  ' if not bad else 'FAIL'} K14 condition kit: {len(res) - len(bad)}/{len(res)} rules hold")
    return 1 if bad else 0


def _set(path: str, value):
    def f(d):
        node = d
        keys = path.split(".")
        for k in keys[:-1]:
            node = node[k]
        if value is _DELETE:
            del node[keys[-1]]
        else:
            node[keys[-1]] = value
    return f


_DELETE = object()

CASES = (
    ("a floor of 0.30", "floor", _set("floor.min_tone", 0.30)),
    ("a soot band that lightens the wall", "range", _set("layers.eave_soot.tone.full", 1.25)),
    ("full age at 400 years, so a 38-year wall reads new", "old work visible, not ruined", _set("age.full_years", 400)),
    ("soot at 0.30, a black facade the floor would only hide", "floor", _set("layers.eave_soot.tone.full", 0.30)),
    ("every layer at half strength, a black facade", "old work visible, not ruined",
     lambda d: [d["layers"][n]["tone"].__setitem__("full", 0.63) for n in ("ground_damp", "eave_soot")]
     and d["layers"]["eave_soot"]["depth_m"].__setitem__("full", 4.4)),
    ("a damp layer with no note", "provenance", _set("layers.ground_damp.note", "")),
    ("a moss layer", "never", lambda d: d["layers"].__setitem__("moss_growth", {
        "applies_to": "wall", "confidence": "reconstructed", "note": "x"})),
    ("a 40-year repaint cycle", "paint", _set("layers.paint.cycle_years", 40)),
    ("damp 0.70 m, off the K03 wall", "K03", _set("layers.ground_damp.top_m.full", 0.70)),
    ("no response for Bedford limestone", "fabrics", _set("fabric_response.limestone_bedford", _DELETE)),
    ("a sill trail that widens to its foot", "trails", _set("layers.water_trails.sources.sill.taper", 2.5)),
    ("a plume blown west, into the wind", "plume", _set("layers.chimney_soot.lee_bearing_deg", 250)),
    ("a damp band that shrinks with age", "age", _set("layers.ground_damp.top_m.new", 2.5)),
    ("full age at 4 years, so new work arrives sooted", "new work clean", _set("age.full_years", 4)),
)


def self_test() -> int:
    base = K.load()
    failed = 0
    clean = [r for r in rules(copy.deepcopy(base)) if not r[1]]
    for name, label, breaker in CASES:
        data = copy.deepcopy(base)
        breaker(data)
        res = rules(data)
        hit = [r for r in res if r[0] == label and not r[1]]
        if hit:
            print(f"   self-test | ok   {name}: refused by '{label}'")
        else:
            failed += 1
            print(f"   self-test | FAIL {name}: the '{label}' rule let it through")
    if clean:
        failed += 1
        print(f"   self-test | FAIL the unbroken kit fails {len(clean)} rule(s): {clean[0][0]}: {clean[0][2]}")
    else:
        print("   self-test | ok   the unbroken kit holds every rule")
    print(f"{'ok  ' if not failed else 'FAIL'} K14 condition kit self-test: {len(CASES) + 1 - failed}/{len(CASES) + 1}")
    return 1 if failed else 0


def main(argv) -> int:
    if "--check" in argv:
        return check()
    if "--self-test" in argv:
        return self_test()
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
