#!/usr/bin/env python3
"""No 1812 building stands in the ground: a wall on sloping ground has its sill carried (T-3492).

    python3 tools/check_sunken_sills.py               the gate, every checked scene
    python3 tools/check_sunken_sills.py --report      every building's relief, the level ones too
    python3 tools/check_sunken_sills.py --self-test   break it three ways; each must fire

WHY THIS EXISTS. The owner, 2026-11-07, with a screenshot looking west over 378 N Michigan
Avenue in 1812: *"this house looks sunken in 1812"*. The renderer stands a building on the
LOWEST ground under its walls (renderers/web/js/buildings.js `groundUnder`, T-3029), which
buries the uphill side by however far the ground rises across the walls. On nearly flat
ground that is nothing. The government factory stands on the top of the river bank, where
the committed e1830_natural ground rises 0.93 m across its walls, so its east front stood
in the ground over the foot of its door and its ground-floor sash. The validator's
ground-contact check had seen the same 0.93 m and asked for a declaration, and got one,
which is honest and still leaves a house in the ground.

THE RULE. In a checked scene, a building whose footprint stands on more relief than
RELIEF_MAX_M (the walls' highest ground less their lowest, sampled along every edge of the
sidecar polygon placed as the renderer seats it, on the scene's own committed heightfield)
must carry `placement.underpinning`, which the renderer builds as a sill clear of the
highest ground on stone down to below the lowest, with a doorstep
(renderers/web/js/underpinning.js). RELIEF_MAX_M is the photo-ticket stopping rule's bar of
about a foot (AGENTS.md rule 11): less than that, a visitor reads the bedding as a sill
settled into the yard. And the claim is checked the other way: an underpinning on ground
with less than LEVEL_M of relief is a reconstruction answering nothing, and is refused.

WHICH SCENES. 1812 (T-3492). 1835's worst is 0.45 m (the fort wash house) and its riverbank
houses are a separate question with their own declared ground contact; adding "1835" to
SCENES is how that work would start.

Reads the compiled sidecars (`tools/compile_scene.py --check` holds them to the records)
and the committed heightfield through tools/heightfield.py, the same bilinear reader the
validator uses. No browser, no Blender.
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from heightfield import Heightfield  # noqa: E402

SCENES = ("1812",)
#: The good-enough bar (AGENTS.md rule 11, T-3153): about a foot.
RELIEF_MAX_M = 0.30
#: An underpinning on less relief than this answers nothing.
LEVEL_M = 0.15
#: Archetypes that stand walls with a door on the ground. Fences, fields, camps and
#: the fort's own ground pieces are drawn on the ground, not bedded on it.
WALLED = ("log_dwelling", "outbuilding", "frame_dwelling", "frame_tavern",
          "frame_storefront", "fort_structure")
#: Sample spacing along an edge.
STEP_M = 0.5


def placed(poly: list, p: dict) -> list[tuple[float, float]]:
    """The polygon's (u, v) placed in local (E, N), turned CLOCKWISE by its bearing, as
    the renderer seats the mesh (angles.js bearingToYaw) and the validator places it."""
    th = math.radians(float(p.get("rotation_deg") or 0.0))
    c, s = math.cos(th), math.sin(th)
    e0, n0 = float(p["local_e"]), float(p["local_n"])
    return [(e0 + u * c + v * s, n0 - u * s + v * c) for u, v in poly]


def relief(field: Heightfield, poly: list, p: dict) -> tuple[float, float]:
    """(lowest, highest) ground along the placed polygon's edges and at its origin."""
    pts = placed(poly, p)
    hs = [field.height(float(p["local_e"]), float(p["local_n"]))]
    for i, (ae, an) in enumerate(pts):
        be, bn = pts[(i + 1) % len(pts)]
        k = max(1, math.ceil(math.hypot(be - ae, bn - an) / STEP_M))
        hs += [field.height(ae + (be - ae) * j / k, an + (bn - an) * j / k) for j in range(k + 1)]
    return min(hs), max(hs)


def load_scene(scene: str) -> tuple[Heightfield, list[dict]]:
    meta = json.loads((ROOT / "data" / "scenes" / f"{scene}.json").read_text(encoding="utf-8"))
    field = Heightfield.load(ROOT / "data" / "terrain" / "epochs" / meta["terrain_epoch"])
    if field is None:
        raise SystemExit(f"check_sunken_sills: no heightfield for {meta['terrain_epoch']}")
    cars = []
    for f in sorted((ROOT / "data" / "sidecars" / scene).glob("*.json")):
        if f.name == "index.json":
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        if isinstance(d, dict) and isinstance(d.get("placement"), dict):
            cars.append(d)
    return field, cars


def findings(field: Heightfield, cars: list[dict]) -> tuple[list[str], list[tuple]]:
    """(problems, rows): every refusal in words, and (id, archetype, relief, underpinned)."""
    problems, rows = [], []
    for d in cars:
        p = d["placement"]
        poly = (d.get("footprint") or {}).get("polygon") or []
        if d.get("archetype") not in WALLED or p.get("vertical_anchor") != "terrain" or len(poly) < 3:
            continue
        if not field.covers(float(p["local_e"]), float(p["local_n"])):
            continue
        lo, hi = relief(field, poly, p)
        under = p.get("underpinning")
        rows.append((d["id"], d.get("archetype"), hi - lo, bool(under)))
        if hi - lo > RELIEF_MAX_M and not under:
            problems.append(
                f"{d['id']}: its walls stand on {hi - lo:.2f} m of ground ({lo:.2f} to {hi:.2f} m), "
                f"more than the {RELIEF_MAX_M} m a visitor reads as a settled sill, so bedded at its "
                f"lowest corner its uphill side stands {hi - lo:.2f} m in the ground. Carry it on "
                f"an underpinning (phase.underpinning, data/structures.schema.json) and compile, or "
                f"move it off the slope")
        if under and hi - lo < LEVEL_M:
            problems.append(
                f"{d['id']}: states an underpinning on {hi - lo:.2f} m of relief, under the "
                f"{LEVEL_M} m at which one answers anything — drop it")
        if under and under.get("doors") == [] and d.get("archetype") == "log_dwelling":
            problems.append(f"{d['id']}: underpinned with no door to step up to — the compiler "
                            f"could not read its front wall")
    return problems, rows


def self_test() -> int:
    field, cars = load_scene("1812")
    by_id = {d["id"]: d for d in cars}
    fails = 0

    def expect(label: str, mutate, needle: str) -> None:
        nonlocal fails
        trial = copy.deepcopy(cars)
        mutate({d["id"]: d for d in trial})
        probs, _ = findings(field, trial)
        ok = any(needle in s for s in probs)
        fails += not ok
        print(f"   self-test | {'ok  ' if ok else 'FAIL'} {label}")
        for s in probs:
            print(f"   self-test |      {s[:150]}")

    if "first_fort_outer_factory" not in by_id:
        print("   self-test | FAIL the factory is not in the 1812 sidecars")
        return 1
    expect("the factory on its bank with no underpinning is refused",
           lambda m: m["first_fort_outer_factory"]["placement"].pop("underpinning", None),
           "first_fort_outer_factory: its walls stand on")
    expect("an underpinning under the level agent's house is refused",
           lambda m: m["first_fort_outer_agents_house"]["placement"].__setitem__(
               "underpinning", {"kind": "fieldstone", "sill_clear_m": 0.2, "doors": [[1, 2]]}),
           "first_fort_outer_agents_house: states an underpinning")
    expect("a house moved onto the bank's face is refused",
           lambda m: m["kinzie_bake_house_1812"]["placement"].update(
               local_e=by_id["first_fort_outer_factory"]["placement"]["local_e"] - 4,
               local_n=by_id["first_fort_outer_factory"]["placement"]["local_n"] + 4),
           "kinzie_bake_house_1812: its walls stand on")
    print(f"check_sunken_sills self-test: {'PASS' if not fails else f'{fails} FAILED'}")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    bad = 0
    for scene in SCENES:
        field, cars = load_scene(scene)
        problems, rows = findings(field, cars)
        if args.report:
            for sid, arch, r, u in sorted(rows, key=lambda x: -x[2]):
                print(f"  {scene} {r:5.2f} m  {'underpinned' if u else '           '}  {sid} ({arch})")
        for s in problems:
            print(f"FAIL {scene} {s}")
        bad += len(problems)
        worst = max(rows, key=lambda x: x[2] if not x[3] else -1, default=None)
        print(f"check_sunken_sills {scene}: {len(rows)} walled buildings, "
              f"{sum(1 for r in rows if r[3])} underpinned; worst bedded relief "
              f"{worst[2]:.2f} m ({worst[0]})" if worst else f"check_sunken_sills {scene}: none")
    print("check_sunken_sills: " + ("PASS" if not bad else f"{bad} FAIL"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
