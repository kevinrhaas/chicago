#!/usr/bin/env python3
"""T-2374: the explicit compound aperture set — bounded, opt-in, and off everywhere else.

The Wau-Bun panorama of 1831 draws the Agency House's front gable with TWO upright
dark marks standing on the ground and ONE small mark above them. The log_dwelling
compound path states one opening per room, so that front was not sayable at all, and
nothing short of splitting the centre room — which would change the roof and the walls
the rest of the record states — could say it in data alone. `compound_apertures` is the
opt-in that lets ONE room state its own set instead.

An opt-in is only as good as what refuses it, so this holds four things, none of them
needing Blender:

  1. the params module's gable geometry tracks the BUILDER'S own overhang — the gable a
     compound room closes stands `COMPOUND_ROOF_OVERHANG_M` outboard of its roof
     rectangle because `log_dwelling._compound` passes no overhang to
     `MeshBuilder.add_gable_roof`, so the default is read out of mesh.py's source (it
     imports bpy) and compared. An aperture measured against the wrong triangle is
     buried in the roof or hanging off the rake, and nothing else here would notice;
  2. Cobweb Castle resolves to the three stated apertures, its centre room's own
     `front_opening` is OVERRIDDEN rather than drawn as well — no phantom centre door —
     and exactly one of the three is a grounded way in, so the entrance reader still
     finds one door on that front;
  3. the front WALL reading and the builder's rectangles are the same rectangles, and
     the gable one is NOT on the front wall (it stands above the wall head, outboard of
     it, where no signboard, apron or doorway reads);
  4. every malformed set is refused, one case per rule, and every other log_dwelling
     record in the tree resolves with an empty set and the front rects the legacy rule
     has always given it.

Run `--self-test` for the refusals alone; with no argument it runs the lot.
"""

from __future__ import annotations

import argparse
import ast
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generators"))

from archetypes import facade_openings  # noqa: E402
from archetypes import log_dwelling_params as ldp  # noqa: E402

FAILS: list[str] = []


def check(ok: bool, what: str) -> None:
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        FAILS.append(what)


def gable_roof_default_overhang() -> float | None:
    """`MeshBuilder.add_gable_roof`'s default overhang, read from mesh.py's source."""
    tree = ast.parse((ROOT / "generators" / "common" / "mesh.py").read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "add_gable_roof":
            args = node.args.args[1:]
            pad = len(args) - len(node.args.defaults)
            for arg, default in zip(args[pad:], node.args.defaults):
                if arg.arg == "overhang" and isinstance(default, ast.Constant):
                    return default.value
    return None


def record(structure_id: str) -> dict:
    return json.loads((ROOT / "data" / "structures" / f"{structure_id}.json")
                      .read_text(encoding="utf-8"))


def resolve(rec: dict):
    return ldp.from_phase(rec["phases"][0], rec)


def refuses(rec: dict, apertures, why: str) -> None:
    """A record whose stated set is `apertures` must not resolve."""
    bad = copy.deepcopy(rec)
    form = bad["phases"][0]["form"]
    form["compound_apertures"] = {"value": apertures, "confidence": "reconstructed"}
    try:
        resolve(bad)
    except ldp.ParamError as exc:
        check(True, f"refused: {why} ({exc})")
    except Exception as exc:  # noqa: BLE001
        check(False, f"refused: {why} — but with {type(exc).__name__}: {exc}")
    else:
        check(False, f"NOT refused: {why}")


def ap(**kw) -> dict:
    out = {"room": 0, "face": "+y", "zone": "wall", "kind": "aperture",
           "u0": 4.26, "u1": 5.16, "z0": 0.02, "z1": 1.95}
    out.update(kw)
    return out


def run_refusals(rec: dict) -> None:
    good = ap()
    refuses(rec, [ap(room=9)], "a room the record does not state")
    refuses(rec, [ap(room=True)], "a boolean room index")
    refuses(rec, [ap(room=1)], "a room whose +y wall is not an outward face")
    refuses(rec, [ap(face="-y")], "an unsupported face")
    refuses(rec, [ap(zone="roof")], "an unsupported zone")
    refuses(rec, [ap(kind="window")], "an unsupported kind")
    refuses(rec, [ap(u0=float("inf"))], "a non-finite coordinate")
    refuses(rec, [ap(z0=True)], "a boolean coordinate")
    refuses(rec, [ap(u0=5.16, u1=4.26)], "a negative width")
    refuses(rec, [ap(z0=1.95, z1=0.02)], "a negative height")
    refuses(rec, [ap(u0=3.9, u1=4.9)], "a wall aperture past its room's corner")
    refuses(rec, [ap(u0=8.2, u1=8.95)], "a wall aperture inside the corner margin")
    refuses(rec, [ap(z1=2.55)], "a wall aperture into the wall head")
    refuses(rec, [ap(zone="gable", z0=2.2, z1=2.9)], "a gable aperture reaching below the eave")
    refuses(rec, [ap(zone="gable", u0=5.57, u1=6.27, z0=3.9, z1=4.5)],
            "a gable aperture standing through its own rake")
    refuses(rec, [ap(zone="gable", u0=3.8, u1=4.5, z0=2.7, z1=3.3)],
            "a gable aperture off the end of the rake")
    refuses(rec, [ap(kind="door", z0=0.9, z1=2.1)], "a way in that does not reach the ground")
    refuses(rec, [ap(kind="door", zone="gable", u0=5.57, u1=6.27, z0=2.74, z1=3.54)],
            "a way in up in the gable")
    refuses(rec, [ap(kind="door"), ap(kind="door", u0=6.22, u1=7.12)], "two ways in")
    refuses(rec, [good, ap(u0=5.2, u1=6.1)], "two apertures with no wall between them")
    refuses(rec, [good, ap(u0=4.8, u1=5.6)], "two apertures that overlap")
    refuses(rec, [], "an empty stated set")
    refuses(rec, [ap() for _ in range(7)], "more apertures than the bound allows")
    refuses(rec, [{"room": 0, "zone": "wall", "kind": "aperture",
                   "u0": 4.26, "u1": 5.16, "z0": 0.02, "z1": 1.95}],
            "an aperture missing a key")

    # ...and the two shapes of record that may not carry a set at all.
    elbow = record("wolf_point_tavern")
    elbow["phases"][0]["form"]["compound_apertures"] = {
        "value": [ap()], "confidence": "reconstructed"}
    try:
        resolve(elbow)
    except ldp.ParamError as exc:
        check(True, f"refused: a set on the bounded elbow ({exc})")
    else:
        check(False, "NOT refused: a set on the bounded elbow")

    plain = record("walker_meeting_house")
    plain["phases"][0]["form"]["compound_apertures"] = {
        "value": [ap()], "confidence": "reconstructed"}
    try:
        resolve(plain)
    except ldp.ParamError as exc:
        check(True, f"refused: a set on a house with no stated rooms ({exc})")
    else:
        check(False, "NOT refused: a set on a house with no stated rooms")


def run_reading(rec: dict) -> None:
    oh = gable_roof_default_overhang()
    check(oh == ldp.COMPOUND_ROOF_OVERHANG_M,
          f"COMPOUND_ROOF_OVERHANG_M {ldp.COMPOUND_ROOF_OVERHANG_M} is "
          f"add_gable_roof's own default overhang {oh}")

    p = resolve(rec)
    check(len(p.compound_apertures) == 3,
          f"Cobweb Castle states three apertures ({len(p.compound_apertures)})")
    plane, g0, g1, apex, eave, ridge = ldp.compound_gable_face(p, 0)
    wall = p.compound_parts[0][0]
    check(abs(plane - (wall[3] + ldp.COMPOUND_ROOF_OVERHANG_M)) < 1e-9,
          f"its centre gable stands at y {plane} — the wall at {wall[3]} plus the overhang")
    check(abs(eave - p.wall_height_m) < 1e-9 and ridge > eave,
          f"that gable runs from the eave {eave} up to the ridge {ridge:.3f}")

    rects = ldp.compound_front_rects(p)
    centre = [r for r in rects if r[0] == wall[3]]
    check(len(centre) == 2,
          f"the centre room's front carries the two stated wall apertures ({len(centre)})")
    old_u = (wall[0] + wall[2]) / 2.0
    check(not any(abs((r[2] + r[3]) / 2.0 - old_u) < 1e-9 and r[1] == "door" for r in centre),
          "the room's own front_opening is overridden, not drawn as well — no phantom centre door")
    check(sorted(r[1] for r in centre) == ["aperture", "door"],
          "...and what stands there is one neutral aperture and one stated way in")

    wings = [r for r in rects if r[0] != wall[3]]
    check(len(wings) == 2 and all(r[1] == "window" for r in wings),
          f"both wings keep their own single window ({[r[1] for r in wings]})")

    w = ldp.front_wall(p)
    kinds = sorted(o["kind"] for o in w["openings"])
    check(kinds == ["aperture", "door"],
          f"the front wall reads exactly those two rectangles ({kinds})")
    check(all(o["z1"] <= w["wall_height_m"] + 1e-9 for o in w["openings"]),
          "nothing on the front WALL reading stands above the wall head")
    doors = [o for o in w["openings"] if o["kind"] == "door" and o["z0"] < 0.30]
    check(len(doors) == 1,
          f"the entrance reader finds exactly one grounded way in ({len(doors)})")
    check("aperture" in facade_openings.HOLE_KINDS and
          "aperture" not in ("door", "shop_door", "open_bay"),
          "an aperture is a hole a board must clear, and not an entrance kind")

    stated = ldp.compound_aperture_rects(p)
    walls = {(pl, k, a, c, z0, z1) for pl, zone, k, a, c, z0, z1 in stated if zone == "wall"}
    check(walls <= set(rects),
          "the builder's wall apertures are the SAME rectangles the facade reader gives")
    gables = [s for s in stated if s[1] == "gable"]
    check(len(gables) == 1 and abs(gables[0][0] - plane) < 1e-9,
          "the one gable aperture is reported on the gable plane, not on the wall")
    check(not any(abs(r[0] - plane) < 1e-9 for r in rects),
          "...and never reaches the front-wall reading")


def run_default_off() -> None:
    """Every other log_dwelling record states no set and keeps its legacy front."""
    changed, seen = [], 0
    for path in sorted((ROOT / "data" / "structures").glob("*.json")):
        rec = json.loads(path.read_text(encoding="utf-8"))
        if rec.get("archetype") != "log_dwelling" or rec["id"] == "cobweb_castle":
            continue
        for phase in rec.get("phases", []):
            if not phase.get("form"):
                continue
            p = ldp.from_phase(phase, rec)
            seen += 1
            if p.compound_apertures:
                changed.append(f"{rec['id']}/{phase.get('id')}")
            if p.compound_parts and p.compound_joint is None:
                legacy = [r for r in ldp.compound_front_rects(p)]
                if any(r[1] not in ("door", "window") for r in legacy):
                    changed.append(f"{rec['id']}/{phase.get('id')} front kinds")
    check(not changed and seen > 0,
          f"{seen} other log_dwelling phases resolve with no stated set and their legacy "
          f"fronts ({', '.join(changed) if changed else 'none changed'})")


def main() -> int:
    ap_ = argparse.ArgumentParser()
    ap_.add_argument("--self-test", action="store_true",
                     help="only the refusals — the gates proved by breaking them")
    args = ap_.parse_args()
    rec = record("cobweb_castle")
    if args.self_test:
        run_refusals(rec)
    else:
        run_reading(rec)
        run_default_off()
        run_refusals(rec)
    if FAILS:
        print(f"\n{len(FAILS)} failure(s)")
        return 1
    print("\nall checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
