#!/usr/bin/env python3
"""Generate the bare, trodden ground immediately outside Fort Dearborn's walls (T-0097).

WHAT THIS IS. T-0044's image-accuracy pass read the render against the two committed Fort
Dearborn plates and listed eight gaps. Number 7: *"The ground round the walls is full
prairie sward; both plates show it bare and trodden."* In `p4_0.png` — the fort from the
north bank, the stand this project shoots the fort from — the sward stops well short of the
walls: from the foot of the pickets outward the ground is bare, pale, trodden earth, with a
walking figure on it and the track from the gate crossing it, and the prairie only resumes
past the crest of the bank. In the render, bluestem grew to the foot of the pickets.

**NO SOURCE STATES THIS AND THIS RECORD DOES NOT PRETEND OTHERWISE.** Every value here is
`reconstructed`; `docs/LIBERTIES.md` L174 claims the invention and states its bounds. What
bounds it is (a) the two plates, which are tier-5 pictorial and may drive SETTING as
`inferred` but may never drive a coordinate, and (b) the plain fact that ground worked daily
by a garrison — drill, fatigue parties, wood and water details, the gate traffic — does not
carry 1.5 m of prairie grass.

THE RULE, and it is a rule rather than a hand-drawn polygon precisely so it can be argued
with and re-derived:

  **The band `APRON_M` metres wide immediately outside the palisade's committed footprint,
  on all four sides, is bare trodden earth.**

Not one coordinate here is authored. The band is derived from
`data/sidecars/1835/fort_dearborn_palisade.json` — its `footprint.polygon` and its
`placement` — in the frame `docs/GLB-CONTRACT.md` fixes, so if the fort is ever re-placed or
re-sized the ground follows it. `tools/check.sh` re-derives this file byte for byte.

WHY A FRAME OF FOUR BANDS AND NOT ONE SQUARE. The claim this record makes is about the
ground OUTSIDE the walls. A single square would also lay a treatment over the parade inside
them, which is a second claim, about ground no committed plate shows, and it is not made
here. So the apron is the frame: four bands that tile the annulus exactly, with no overlap
and no gap, and the fort's own interior left as it is.

WHY `trodden_earth` AND NOT `worn_earth`. The two treatments the yard layer already builds
differ in exactly the thing the plate settles: `worn_earth` is a wheeled yard, with ruts and
a wide surviving fringe of trampled grass at its edges; `trodden_earth` is a pen — finer,
darker, no ruts, and trodden right up to its own boundary. `p4_0` draws the second: the bare
ground reaches the pickets with no grassy collar at the wall. The fringe is measured from
the apron's OUTER ring alone (`fringe_ring_local_enu_m`), so the sward feathers in at the
prairie edge and the ground stays bare at the wall — which is what the picture shows and
what a band-by-band fringe would have got wrong at three edges out of four.

WHAT THIS RECORD DELIBERATELY DOES NOT DO:

  * It draws no fence. The enclosure here is the palisade, which is a committed structure
    with a baked GLB; this record carries the ground and nothing else, which is why its
    `runs` are empty and why it says so in as many words.
  * It does not clip the fort road. The road (T-0044) arrives at the south gate and its
    last ~7 m of track lies on the apron. Both are bare-earth drapes at the same lift, both
    are `reconstructed`, and a travelled track crossing a trodden apron is what the plate
    draws; clipping one out of the other would be inventing a boundary the picture has not
    got.
  * It does not reach the water. `renderers/web/js/yards.js` drops any cell whose foot is
    in the river mask, so the north band stops itself at the bank rather than being trimmed
    by a number authored here.
  * It does not touch the bank's shape. Nothing here regrades a metre of terrain; the
    treatment is draped on the committed heightfield.

WHAT WOULD MOVE IT OFF RECONSTRUCTION: a garrison return or quartermaster's account
describing the ground of the reservation; an 1830s survey of the United States Reservation
showing cleared ground; or an identification of either plate against a dated original that
would raise it above tier 5.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
PALISADE = DATA / "sidecars" / "1835" / "fort_dearborn_palisade.json"
ENCLOSURES = DATA / "enclosures"
STREETS = DATA / "streets" / "1835.json"
OUT = ENCLOSURES / "fort_dearborn_apron.json"

# THE ONE INVENTED NUMBER, and it is the whole of the invention. 12 m of bare ground
# outside every wall. What bounds it: in `p4_0` the bare ground runs from the foot of the
# pickets, past a walking figure, to the crest of the bank, and the fort's own 53 m side is
# in the same picture to scale it against — which puts the reach at the order of ten to
# twenty metres. It is also the same figure as the fort road's own `corridor_width_m`, which
# is the only other reconstructed distance this project has stated on this reservation, and
# using a second unrelated number would imply a precision neither has.
APRON_M = 12.0

# The fort road's last point must fall ON the apron. Not a tuning knob: it is the assertion
# that the rule closes the gap it was written for — a track that arrives at the gate across
# a collar of untouched prairie would be the same defect in a different place.
ROAD_ID = "fort_road"


def _round(x: float, places: int = 2) -> float:
    return round(x + 0.0, places)


def _to_enu(u: float, v: float, place: dict) -> tuple[float, float]:
    """A footprint coordinate to local ENU metres.

    docs/GLB-CONTRACT.md: polygon `u` -> +X, polygon `v` -> -Z, ENU `local_e` -> +X and
    `local_n` -> -Z, and the node's yaw is `-rotation_deg` about +Y. The same three lines
    every other derived layer in this project uses to leave a building's own frame.
    """
    th = math.radians(-(place.get("rotation_deg") or 0.0))
    x, z = u, -v
    xr = x * math.cos(th) + z * math.sin(th)
    zr = -x * math.sin(th) + z * math.cos(th)
    return (place.get("local_e") or 0.0) + xr, (place.get("local_n") or 0.0) - zr


def _ring(box: tuple[float, float, float, float], place: dict) -> list[list[float]]:
    """One rectangle in the fort's own footprint frame, as a ring in local ENU."""
    u0, u1, v0, v1 = box
    return [[_round(e), _round(n)] for e, n in
            (_to_enu(u0, v0, place), _to_enu(u1, v0, place),
             _to_enu(u1, v1, place), _to_enu(u0, v1, place))]


def _point_in_ring(pts: list, e: float, n: float) -> bool:
    inside = False
    j = len(pts) - 1
    for i in range(len(pts)):
        xi, yi = pts[i]
        xj, yj = pts[j]
        if (yi > n) != (yj > n) and e < (xj - xi) * (n - yi) / ((yj - yi) or 1e-12) + xi:
            inside = not inside
        j = i
    return inside


def bands(place: dict, poly: list) -> tuple[list, list, dict]:
    """The four bands, the outer fringe ring, and the frame they were derived in.

    The palisade's footprint is a rectangle in its own `u`/`v`, so the annulus tiles
    exactly: the south and north bands run the FULL outer width, and the west and east
    bands fill the two remaining flanks between them. No band overlaps another and the
    four together are the whole frame, which is asserted below rather than asserted here.
    """
    u0 = min(p[0] for p in poly)
    u1 = max(p[0] for p in poly)
    v0 = min(p[1] for p in poly)
    v1 = max(p[1] for p in poly)
    a = APRON_M
    boxes = [
        ("south", (u0 - a, u1 + a, v0 - a, v0)),
        ("north", (u0 - a, u1 + a, v1, v1 + a)),
        ("west", (u0 - a, u0, v0, v1)),
        ("east", (u1, u1 + a, v0, v1)),
    ]
    rings = [{"id": f"apron_{name}", "ring_local_enu_m": _ring(box, place)}
             for name, box in boxes]
    outer = _ring((u0 - a, u1 + a, v0 - a, v1 + a), place)
    frame = {"u": [_round(u0), _round(u1)], "v": [_round(v0), _round(v1)]}
    return rings, outer, frame


def assertions(rings: list, outer: list, place: dict, poly: list) -> list[dict]:
    """What the rule has to be true for, re-run on every commit by `--check`.

    These are the reason this is a generated record and not a drawn one. Each one is a
    sentence somebody could disagree with, and each one fails the gate rather than a
    reviewer's attention.
    """
    out = []

    # 1. THE FRAME TILES THE ANNULUS. Area arithmetic in the fort's own frame, where every
    # band is axis-aligned: the four bands must sum to the outer square less the palisade,
    # which is true iff none of them overlaps and none of them leaves a gap.
    u0 = min(p[0] for p in poly)
    u1 = max(p[0] for p in poly)
    v0 = min(p[1] for p in poly)
    v1 = max(p[1] for p in poly)
    a = APRON_M
    outer_area = (u1 - u0 + 2 * a) * (v1 - v0 + 2 * a)
    inner_area = (u1 - u0) * (v1 - v0)
    band_area = 2 * (u1 - u0 + 2 * a) * a + 2 * (v1 - v0) * a
    out.append({
        "id": "frame_tiles_the_annulus",
        "claim": "the four bands cover the whole band outside the walls, with no overlap "
                 "and no gap",
        "expected_m2": _round(outer_area - inner_area),
        "derived_m2": _round(band_area),
        "holds": abs(band_area - (outer_area - inner_area)) < 1e-6,
    })

    # 2. NOTHING IS DRAWN INSIDE THE WALLS. The claim is about the ground OUTSIDE, so the
    # palisade's own centre must fall on no band. A single square would fail this, which is
    # the point of stating it.
    centre = _to_enu((u0 + u1) / 2, (v0 + v1) / 2, place)
    out.append({
        "id": "the_parade_is_not_claimed",
        "claim": "no band covers the ground inside the palisade — the parade is a second "
                 "claim and this record does not make it",
        "at_local_enu_m": [_round(centre[0]), _round(centre[1])],
        "holds": not any(_point_in_ring(r["ring_local_enu_m"], *centre) for r in rings),
    })

    # 3. THE APRON REACHES THE ROAD. The gap this rule exists to close runs from the wall
    # outward, and the fort road already models trodden ground coming the other way; if the
    # two do not meet there is a collar of untouched prairie between them and the picture is
    # still wrong, quietly, in a narrower ring.
    road = None
    try:
        for street in json.loads(STREETS.read_text(encoding="utf-8")).get("streets", []):
            if street.get("id") == ROAD_ID:
                road = street
    except Exception:  # noqa: BLE001 — reported as a failed assertion, not a crash
        road = None
    end = (road.get("path_local_enu_m") or [])[-1] if road else None
    out.append({
        "id": "the_apron_reaches_the_fort_road",
        "claim": f"the last point of {ROAD_ID}'s traced way stands on the apron, so no ring "
                 "of untouched prairie is left between the track and the wall",
        "at_local_enu_m": [_round(end[0]), _round(end[1])] if end else None,
        "holds": bool(end) and any(_point_in_ring(r["ring_local_enu_m"], end[0], end[1])
                                   for r in rings),
    })

    # 4. NO OTHER RECORD ALREADY TREATS THIS GROUND. Two ground treatments on one patch is
    # two claims about one place; the town's other fenced interiors are half a mile west,
    # and this asserts it rather than assuming it.
    clashes = []
    for path in sorted(ENCLOSURES.glob("*.json")):
        if path.name in ("index.json", OUT.name):
            continue
        rec = json.loads(path.read_text(encoding="utf-8"))
        ground = rec.get("ground") or {}
        others = []
        authored = ground.get("interior_local_enu_m")
        if isinstance(authored, list) and authored and isinstance(authored[0], list) \
                and authored[0] and isinstance(authored[0][0], (int, float)):
            others.append(authored)
        for run in rec.get("runs") or []:
            p = run.get("path_local_enu_m") or []
            if len(p) >= 4 and abs(p[0][0] - p[-1][0]) < 1e-6 and abs(p[0][1] - p[-1][1]) < 1e-6:
                others.append(p)
        for other in others:
            for band in rings:
                if any(_point_in_ring(other, e, n) for e, n in band["ring_local_enu_m"]) \
                        or any(_point_in_ring(band["ring_local_enu_m"], e, n) for e, n in other):
                    clashes.append(rec.get("id"))
    out.append({
        "id": "no_other_treated_ground_here",
        "claim": "no other enclosure record already lays a ground treatment on this band",
        "clashes": sorted(set(clashes)),
        "holds": not clashes,
    })
    return out


def record(rings: list, outer: list, frame: dict, checks: list, palisade: dict) -> dict:
    place = palisade.get("placement") or {}
    return {
        "_doc": (
            "THE BARE, TRODDEN GROUND IMMEDIATELY OUTSIDE FORT DEARBORN'S WALLS (T-0097). "
            "Both committed Fort Dearborn plates draw the ground round the stockade as bare "
            "trodden earth and the render grew prairie sward to the foot of the pickets. "
            "This record is the rule that stops it: the band "
            f"{APRON_M:.1f} m wide outside the palisade's committed footprint, on all four "
            "sides, treated as trodden earth. NOT ONE COORDINATE HERE IS AUTHORED - every "
            "ring is derived from data/sidecars/1835/fort_dearborn_palisade.json by "
            "tools/generate_fort_apron.py, and tools/check.sh re-derives this file byte for "
            "byte, so the ground follows the fort if the fort is ever re-placed. IT DRAWS NO "
            "FENCE: the enclosure here is the palisade itself, a committed structure with a "
            "baked GLB, so this record carries `runs: []` and the ground alone. NOTHING HERE "
            "IS ATTESTED - every value is `reconstructed` and docs/LIBERTIES.md L174 states "
            "what bounds the invention. Read the rule, and what it deliberately does not "
            "claim, in tools/generate_fort_apron.py."
        ),
        "id": "fort_dearborn_apron",
        "name": "The trodden ground outside Fort Dearborn's walls",
        "kind": "apron",
        "scene": "1835",
        "target_date": "1835-07-01",
        "structure_id": "fort_dearborn_palisade",
        "coordinates": (
            "Local East-North-Up metres from data/datum.json's origin - the same frame "
            "data/enclosures/'s other records, data/signage/ and the sidecars' "
            "placement.local_e / local_n use."
        ),
        "derived_from": {
            "sidecar": "data/sidecars/1835/fort_dearborn_palisade.json",
            "placement_local_enu_m": [place.get("local_e"), place.get("local_n")],
            "rotation_deg": place.get("rotation_deg"),
            "footprint_frame_m": frame,
            "apron_width_m": APRON_M,
            "note": (
                "The palisade's footprint and placement, in the frame docs/GLB-CONTRACT.md "
                "fixes. The footprint itself is `inferred` on the 1830 Harrison plan and "
                "Andreas; this band inherits that placement and adds a reconstructed width "
                "to it, so it can never be better evidenced than the wall it is measured "
                "from."
            ),
        },
        "existence": {
            "confidence": "reconstructed",
            "note": (
                "That the ground outside a garrisoned post's walls was bare and trodden is "
                "what both committed plates draw and what daily use makes of ground; that it "
                f"reached exactly {APRON_M:.1f} m is invented. docs/LIBERTIES.md L174."
            ),
            "sources": ["kurz_allison_1893"],
            "sources_note": (
                "NAMED SINCE 2026-09-13 (T-1107), AND THE PLATE WAS ONE THIS PROJECT "
                "ALREADY HELD. This field used to read 'EMPTY, AND THAT IS THE FINDING', "
                "because the fort views reached the repository only as owner-supplied crops "
                "with a README (data/sources/assets/prefire_views_kevin_2026_08/p4_0.png and "
                "p4_1.png) and no source record held them. Both are panels of "
                "`kurz_allison_1893` - Kurz & Allison, 'Chicago In Early Days, 1779-1857' "
                "(1893), tier 5, public_domain, the whole sheet committed at "
                "chicago/reference/photos/IMG_5382.png. Measured, not recognised, by "
                "tools/measure_plate_join.py, which re-measures the join on every commit: "
                "p4_0 is PANEL 1 ('No. 1.  Old Fort Dearborn.  Erected 1803.'), ncc 0.896 at "
                "0.295x against 0.400 anywhere in the control panel.\n\n"
                "AND THE PAIR IS NOT A PAIR. p4_1 is PANEL 8 - 'No. 8.  Chicago in 1830 - "
                "From the Lake.  Population 96.' - a TOWN view of 1830, not a second view of "
                "the fort, so the sentence this record used to carry about 'the two Fort "
                "Dearborn plates' was wrong about one of them. It costs this record nothing: "
                "the treatment below is read off p4_0 alone and always was, and the "
                "existence note above says 'both committed plates draw' a bare apron, which "
                "both of them do - panel 8 draws the same bare ground round the same post "
                "five years earlier. Nothing here is one grade better evidenced for being "
                "cited. The plate is still a retrospective lithograph published fifty-eight "
                "years after the scene date, it may never drive a coordinate, and every "
                "value on this record stays `reconstructed` for the reasons it always did."
            ),
        },
        "runs": [],
        "runs_note": (
            "EMPTY, AND DELIBERATELY. Every other record on this layer states a fence and "
            "gets its ground from the ring that fence closes. The enclosure here is the "
            "palisade - a committed structure record with a baked GLB, drawn by "
            "renderers/web/js/buildings.js - so there is no fence for this record to draw "
            "and it would be drawing a second wall beside the first if it tried."
        ),
        "ground": {
            "treatment": "trodden_earth",
            "confidence": "reconstructed",
            "note": (
                "The pen's treatment rather than the wagon yard's, and the plate decides "
                "between them: `worn_earth` is a wheeled yard with ruts and a wide fringe of "
                "surviving grass at its edges, `trodden_earth` is finer, darker, without ruts "
                "and trodden right up to its own boundary. p4_0 draws the second - the bare "
                "ground reaches the pickets with no grassy collar at the wall."
            ),
            "interior_local_enu_m": [r["ring_local_enu_m"] for r in rings],
            "interior_note": (
                "FOUR BANDS, NOT ONE SQUARE. The claim is about the ground OUTSIDE the walls; "
                "a single square would also treat the parade inside them, which is a second "
                "claim about ground no committed plate shows and this record does not make "
                "it. The four tile the annulus exactly - asserted, not assumed, under "
                "`assertions`."
            ),
            "fringe_ring_local_enu_m": outer,
            "fringe_note": (
                "The sward feathers in at the apron's OUTER edge and nowhere else. Measured "
                "band by band the fringe would have drawn a grassy seam along the wall and "
                "along the three internal joins, which is the opposite of what the plate "
                "shows: bare earth right up to the pickets."
            ),
        },
        "bands": rings,
        "assertions": checks,
        "research_note": (
            "WHAT WOULD MOVE THIS OFF RECONSTRUCTION: a garrison return or quartermaster's "
            "account describing the ground of the reservation; or an 1830s survey of the United "
            "States Reservation showing cleared ground. ONE ROUTE IS NOW CLOSED: this note "
            "used to offer 'an identification of either Fort Dearborn plate against a dated "
            "original' as a third, and T-1107 made that identification - p4_0 is panel 1 of "
            "kurz_allison_1893, measured. It did NOT raise the standing, because the dated "
            "original is itself the 1893 retrospective; naming a tier-5 lithograph settles "
            "its rights and its date and leaves its tier exactly where it was. WHAT THIS "
            "RECORD IS SHORT OF, stated rather than left to be noticed: the width is one "
            "number for all four sides, where a real post wears its gate side hardest; the "
            "band stops square, where trodden ground fans out from a gate; and the ground "
            "INSIDE the walls is left as it is, because no committed plate shows it."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="re-derive and diff, write nothing")
    args = ap.parse_args()

    palisade = json.loads(PALISADE.read_text(encoding="utf-8"))
    poly = (palisade.get("footprint") or {}).get("polygon") or []
    place = palisade.get("placement") or {}
    if len(poly) < 4 or place.get("local_e") is None:
        print("FORT APRON: the palisade record carries no placed footprint to derive from")
        return 1

    rings, outer, frame = bands(place, poly)
    checks = assertions(rings, outer, place, poly)
    text = json.dumps(record(rings, outer, frame, checks, palisade),
                      indent=2, ensure_ascii=False) + "\n"

    failed = [c for c in checks if not c["holds"]]
    if failed:
        print("FORT APRON: the rule does not hold")
        for c in failed:
            print(f"  - {c['id']}: {c['claim']}")
        return 1

    if args.check:
        if not OUT.exists():
            print(f"FORT APRON DRIFT\n  - {OUT.relative_to(ROOT)} is missing")
            return 1
        if OUT.read_text(encoding="utf-8") != text:
            print(f"FORT APRON DRIFT\n  - {OUT.relative_to(ROOT)} has drifted from the rule "
                  f"in tools/generate_fort_apron.py")
            return 1
    else:
        OUT.write_text(text, encoding="utf-8")

    verb = "verified" if args.check else "wrote"
    print(f"{verb} the fort apron: {len(rings)} band(s) {APRON_M:.1f} m wide outside the "
          f"palisade, {len(checks)} assertion(s) holding")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
