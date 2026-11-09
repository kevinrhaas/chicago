#!/usr/bin/env python3
"""Where the 1835 and 1904 people's homes are entered (T-3516), as derive_doors_1812.py does for 1812.

    python3 tools/derive_doors_scene.py            write data/humans/doors_1835.json, doors_1904.json
    python3 tools/derive_doors_scene.py --check    the gate: each file is what the records say

The owner, 2026-11-08: *"They can take breaks and go in and out of houses and buildings"*, for
all years. renderers/web/js/human-days.js takes a person in by the door of the building their
day has them in, and offers Ask for them there. Which buildings: those named by a drawn
person's day (`behaviour.day[].spans[].where`) in data/humans/instances/<year>/.

  1835  the town's buildings draw their door leaves into their own models, as 1812's do, so a
        building's doors are read off its model by derive_doors_1812.py's `doors_of`.
  1904  Glessner's house is one model with no door material; its doors are read from its
        record, in its own plan frame (W feet west of the Prairie face, S feet south of the
        Eighteenth Street face, house-doors.js glessnerFrontPlan's frame):
          service_stair  the court's service entrance (openings_court_north, at the head of the
                         north court service stair, v4_detail.north_court_service_stair): one
                         answering stands STEP_M out from the foot of the flight. Since T-3524
                         the door is a passage (house-doors.js): who goes in climbs the flight
                         and the landing to it, it opens and shuts, and only then are they in.
          north_entry    the servants' entry off Eighteenth Street (v4_detail.north_entry_alcove):
                         one answering stands on the walk STEP_M out from the alcove's front
                         steps; a passage too (T-3524), up the front steps and the stair inside
                         to its side door.
          stable         the stable's carriage doorway on Eighteenth Street
                         (openings_stable_doors).
        The family's front door is house-doors.js's own (T-3442) and is not listed here.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import derive_doors_1812 as d1812  # noqa: E402

FORMAT = "c4d-doors-scene/1"
SCENES = ("1835", "1904")
FT = 0.3048
STEP_M = d1812.STEP_M


def wheres(scene: str) -> set[str]:
    out = set()
    folder = ROOT / f"data/humans/instances/{scene}"
    for f in sorted(folder.glob("hi_*.json")):
        rec = json.loads(f.read_text())
        if rec.get("display") != "shown":
            continue
        for v in (rec.get("behaviour") or {}).get("day") or []:
            for s in v.get("spans") or []:
                if s.get("indoors") and s.get("where") and not s.get("away"):
                    out.add(s["where"])
    return out


def val(sc: dict, name: str):
    v = (sc.get("attributes") or {}).get(name)
    return v["value"] if isinstance(v, dict) and "value" in v else v


def glessner_doors(sc: dict) -> list[dict]:
    frame = val(sc, "frame_ft")
    L, D = float(frame["length_ft"]), float(frame["depth_ft"])
    pl = sc["placement"]
    th = math.radians(float(pl.get("rotation_deg") or 0.0))
    c, s = math.cos(th), math.sin(th)

    def world(W: float, S: float) -> dict:
        e, n = d1812.to_world((L - W) * FT, (D - S) * FT, pl)
        return {"local_e": round(e, 2), "local_n": round(n, 2)}

    def outward(du: float, dv: float) -> float:
        de, dn = du * c + dv * s, -du * s + dv * c
        return round((math.degrees(math.atan2(de, dn)) + 360) % 360, 1)

    detail = val(sc, "v4_detail") or {}
    out = []
    stair = detail.get("north_court_service_stair")
    court = next((o for o in (val(sc, "openings_court_north") or {}).get("items", []) if o.get("kind") == "door"), None)
    if stair and court:
        W = sum(stair["flight_W"]) / 2
        foot = max(stair["flight_S"])
        out.append({"id": "glessner_house:service_stair", "leaf": world(W, foot), "step": world(W, foot + STEP_M / FT),
                    "outward_deg": outward(0, -1), "width_m": round((max(stair["flight_W"]) - min(stair["flight_W"])) * FT, 2),
                    "passage": True,
                    "reconstructed": "up the north court service stair and its landing to the door (" + court["what"]
                                     + "), which opens and shuts as they pass (house-doors.js passages, T-3524); "
                                     "the line walked is the flight's middle"})
    alcove = detail.get("north_entry_alcove")
    if alcove:
        # The front steps (masonry_house_v4_detail.py north_entry) run out over the walk on the
        # arch's west half, from its west jamb to the cheek; one answering stands out past them.
        W = (max(alcove["opening_W"]) + max(alcove["cheek_W"])) / 2
        out_S = -(float(alcove["front_run_ft"]) + STEP_M / FT)
        out.append({"id": "glessner_house:north_entry", "leaf": world(W, alcove["back_S"] / 2), "step": world(W, out_S),
                    "outward_deg": outward(0, 1), "width_m": round((max(alcove["opening_W"]) - min(alcove["opening_W"])) * FT, 2),
                    "passage": True,
                    "reconstructed": "up the alcove's front steps and the stair inside it to its side door, which opens "
                                     "and shuts as they pass (house-doors.js passages, T-3524); the line walked is the steps' middle"})
    stable = next((o for o in (val(sc, "openings_stable_doors") or {}).get("items", []) if o.get("kind") == "doors"), None)
    if stable:
        W = sum(stable["at"]) / 2
        out.append({"id": "glessner_house:stable", "leaf": world(W, 0.0), "step": world(W, -STEP_M / FT),
                    "outward_deg": outward(0, 1), "width_m": round((max(stable["at"]) - min(stable["at"])) * FT, 2)})
    return out


def derive(scene: str) -> tuple[dict, list[str]]:
    rows, problems = [], []
    for sid in sorted(wheres(scene)):
        f = ROOT / f"data/sidecars/{scene}/{sid}.json"
        if not f.exists():
            problems.append(f"{sid}: a day names it, but {scene} has no such building")
            continue
        sc = json.loads(f.read_text())
        if sid == "glessner_house":
            doors, h = glessner_doors(sc), None
        else:
            glb = ROOT / "assets" / sc["asset"]
            if not glb.exists():
                problems.append(f"{sid}: its model {sc['asset']} is not built")
                continue
            h = d1812.sha256(glb)
            doors, p = d1812.doors_of(sc, glb)
            problems += p
            doors = [{k: (round(float(v), 2) if isinstance(v, float) or type(v).__name__.startswith("float") else v)
                      for k, v in x.items()} for x in doors]
            for x in doors:
                for k in ("leaf", "step"):
                    x[k] = {a: round(float(b), 2) for a, b in x[k].items()}
        if not doors:
            problems.append(f"{sid}: no door found; who is in it cannot be asked for")
            continue
        row = {"structure": sid, "name": sc.get("name") or sid, "placement": d1812._placement(sc), "doors": doors}
        if h:
            row["asset_sha256"] = h
        rows.append(row)
    return {
        "format": FORMAT,
        "ticket": "T-3516",
        "generated_by": "tools/derive_doors_scene.py",
        "note": f"Where each {scene} building a drawn person's day goes into is entered, and where one who answers stands. Asking at a door, going in and out: renderers/web/js/human-days.js.",
        "structures": rows,
    }, problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    bad = 0
    for scene in SCENES:
        out = ROOT / f"data/humans/doors_{scene}.json"
        data, problems = derive(scene)
        for p in problems:
            print(f"doors_{scene}: {p}", file=sys.stderr)
        bad |= bool(problems)
        text = json.dumps(data, indent=1) + "\n"
        if args.check:
            if not out.exists() or out.read_text() != text:
                print(f"FAIL doors_{scene}: {out.relative_to(ROOT)} is not what the records say; run python3 tools/derive_doors_scene.py", file=sys.stderr)
                bad = 1
                continue
            n = sum(len(s["doors"]) for s in data["structures"])
            print(f"doors_{scene}: {n} doors on {len(data['structures'])} buildings")
        else:
            out.write_text(text)
            print(f"wrote {out.relative_to(ROOT)}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
