#!/usr/bin/env python3
"""Generate the town's planted poplar rows — the treatment Wau-Bun states (T-0117).

WHAT IS ATTESTED, verbatim, and it is more than this project had realised it held.
Juliette Kinzie, *Wau-Bun*, ch. XVII "Chicago in 1831" (source record
`kinzie_waubun_1856`, tier 2, describing 1831):

    "On the northern bank of the river, directly facing the fort, was the family
     mansion of my husband. It was a long, low building, with a piazza extending
     along its front, a range of four or five rooms. **A broad green space was
     inclosed between it and the river, and shaded by a ROW OF LOMBARDY
     POPLARS.** Two immense cottonwood-trees stood in the rear of the building,
     one of which still remains as an ancient landmark."

So the SPECIES, the ROW, the fenced green, which side of the house it stood on and
the round-crowned cottonwoods behind it are all stated by somebody who lived there.
That sentence is why this file exists and it is the whole of the treatment's
evidence. `data/flora/plantings/town_dooryard_plantings.json` had to leave the
poplars out — "no committed flora zone record describes the species" — and holding
the species was made its own ticket. It is held now, in
`data/flora/zones/z10_settled_town.json`, at a density of ZERO per hectare, because
nothing grows this tree here: `Populus nigra` 'Italica' is a European cultivar that
reaches Chicago as nursery stock, and every stem of it in this scene is planted by a
household and stated by this record.

WHAT THE PLATES ADD, and it was MEASURED rather than remembered. Seven committed
images draw the row — `data/sources/assets/prefire_views_kevin_2026_08/` p6_1
(plate "12"), p3_0 and p4_1, and `chicago/reference/images/chicago/`
chicago_kinzie_house_1833.png (Chicago Magazine, March 1857),
chicago_kinzie_house_fort_dearborn_1812.jpg (Lossing 1869),
chicago_kinzie_mansion_1832_and_1845_view.jpg ("The Old Kinzie Mansion in 1832") and
chicago_kinzie_house_1804.jpg (a Curt Teich postcard after a painting). Each was
opened and its skyline measured — for every column of the plate, the topmost dark
pixel; the apexes are the local minima of that curve:

    plate                                   spires   gaps (px)        gap / height
    p6_1, plate "12"                          4      27, 22, 23          0.195
    Chicago Magazine 1857                     4      53, 59, 42          0.192
    Lossing 1869                              4      33, 34, 33          0.186
    The Old Kinzie Mansion in 1832            4      25, 20, 38          0.213
    p3_0                                      4      7, 8, 6             0.190
    p4_1                                      4-5    34, 35, 25, 21      (coarse)
    Curt Teich postcard                       5      59, 28, 20, 34      (a painting)

**FIVE INDEPENDENTLY DRAWN PLATES AGREE ON FOUR TREES AND ON A SPACING OF 0.195 OF
THEIR OWN HEIGHT, sd 0.010.** That is the whole of what the plates settle, and it is
the count and the rhythm this file uses. They settle nothing else: the two loosest
images are a low-resolution far view and a painting, and a perspective lithograph
cannot be asked for a metre.

**AND HERE IS WHAT THE PLATES REFUSE.** Every one of the seven draws the row at the
SAME PLACE — the Kinzie group on the north bank of the main stem, facing the fort.
Not one committed plate shows a Lombardy poplar anywhere else in Chicago: not at the
fort (`p4_0`, plate "1", and `p3_1`, plate "5", draw the reservation and the south
bank with none), not on South Water Street, not in any town view. `docs/LIBERTIES.md`
already names the missing evidence in as many words — *"a source describing the
Lombardy poplars' spread into the town would additionally unlock the species"* — and
this run did not find it. **So the plates carry a TREATMENT and one location, and the
location is a house this project excludes** (`data/exclusions.json` → `kinzie_house`:
gone by 1835; its cottonwoods stay, the house does not). Dealing a poplar row to
every riverside house in the town would be inventing an ornamental avenue out of one
household's planting, and this file does not do it.

THE RULE, and it is a rule rather than a list so that it can be argued with and
re-derived. A committed structure gets a planted poplar row iff

  1. **it is a DWELLING** by archetype and by function — T-0052's two clauses,
     imported from `generate_dooryard_plantings` rather than copied, because two
     rules that state the same clause twice drift. A tavern yard and a store
     frontage are different ground with different uses.

  2. **the dataset can date it back far enough to have grown one.** Its own
     `documented_range.from` — the earliest date this project can evidence for the
     building — is on or before `PLANTED_BY`, five growing seasons before the
     scene date. THIS IS THE CLAUSE THAT DOES THE REFUSING: it leaves four of the
     town's 137 dwellings standing.

     **AND IT IS A CLAUSE ABOUT THE DATASET, NOT ABOUT THE HOUSES.** 131 of the
     refused carry `from: 1835-01-01` because their own records say "no evidence
     establishes that this particular building existed" — that is an admission of
     ignorance, not a claim that the house was new, and this file must not read it
     as one. What follows from ignorance is the same either way: a grown
     ornamental at a house of unknown age is an invention resting on an invention,
     and a row goes only where the dataset can say the ground has been somebody's
     long enough for one to have been planted and come up. What survives is the
     four oldest dwellings in the town, which is a fact about the evidence rather
     than a choice made here.

  3. **it has a green on the water** — Wau-Bun's own ground. The waterline lies
     between `GREEN_MIN_M` and `GREEN_MAX_M` from the footprint's near edge along
     the bearing to the nearest water, with NO other committed footprint standing
     in between. Under the minimum there is a strip and not a green; over the
     maximum the ground between house and river is the town's and not the
     household's.

  4. **the row lays clean.** `ROW_STEMS` stems on a straight line PARALLEL to the
     local waterline, `SPACING_M` apart, set `ROW_FRAC` of the way across the green
     — the river side of it, which is where every plate draws the row and where the
     fence in those plates runs. Every stem must clear every committed footprint,
     street track, fence line, neighbouring stem and the planter's own dry floor by
     the margins `generate_dooryard_plantings.py` asks of a dooryard tree, and the
     row may slide along its own line to find room. **Fewer than `ROW_STEMS` clear
     and the whole row is refused**, because a row of two is not the treatment the
     plates draw.

WHAT COMES OUT, as this is written: FOUR dwellings pass the age clause, THREE of them
carry a row, and the fourth — James Kinzie's house at Wolf Point — is refused with its
number, because 7.7 m of ground between a house and the water is a strip and not a
green. Twelve stems in all.

WHAT IS INVENTED, and `docs/LIBERTIES.md` claims it: every coordinate; the choice of
the river side of the green; the growth allowance that turns a house's age into a
height; and the extension of the treatment from the one household that is attested to
the three that meet the rule. What is NOT invented is the species, the fact of a row,
the count, the spacing rhythm and the side of the house — those are the source's and
the plates'.

WHAT WOULD CHANGE IT: any sale notice, diary, view or nurseryman's list that places a
Lombardy poplar at a second Chicago address; or T-0055's source record for the
Kinzie-view plate, which would let this file cite a plate rather than a committed
path.

    python3 tools/generate_planted_rows.py            write the record
    python3 tools/generate_planted_rows.py --check    re-derive and diff
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from heightfield import Heightfield  # noqa: E402
# The dwelling clause and the renderer's own refusals are IMPORTED, not restated.
# T-0052 wrote them, T-0074 reused them, and a third copy is a third thing to keep
# in step.
from generate_dooryard_plantings import (  # noqa: E402
    CLEAR_MARGIN_M, DRY_FLOOR_M, DWELLING_ARCHETYPES, EDGE_INSET_M,
    FENCE_MARGIN_M, FOOTPRINT_MARGIN_M, STEM_SPACING_M, TRACK_MARGIN_M,
    TRACK_SHOULDER_M, footprint_world, is_dwelling_function, path_dist,
    poly_contains, poly_edge_dist,
)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SIDECARS = DATA / "sidecars" / "1835"
STRUCTURES = DATA / "structures"
STREETS = DATA / "streets" / "1835.json"
ENCLOSURES = DATA / "enclosures"
FLORA_INDEX = DATA / "flora" / "index.json"
ZONE = DATA / "flora" / "zones" / "z10_settled_town.json"
EPOCH = DATA / "terrain" / "epochs" / "e1834_harbor_cut"
OUT = DATA / "flora" / "plantings" / "town_planted_rows.json"

SPECIES = "populus_nigra_italica"
SCENE_YEAR = 1835.5  # the scene date, 1835-07-01, as a fraction of the year

# --- what the plates settled ------------------------------------------------
# Four stems, and a gap of 0.195 of the row's own height. Both measured; see the
# table in the docstring.
ROW_STEMS = 4
GAP_OVER_HEIGHT = 0.195
# A row is planted ONCE, at the spacing it will need when it is grown, and the
# plates measure grown rows — so the spacing is taken against the species band's
# CEILING and is the same for every row, young or old. 0.195 x 18 m.
SPACING_M = 3.5

# --- the rule's own numbers, every one of them invented ---------------------
PLANTED_BY = 1830.0        # a house first evidenced after this cannot carry a row
MIN_SEASONS = 5.0          # ...which is five growing seasons before the scene date
GROWTH_M_PER_SEASON = 1.0  # the LOW end of the cultivar's ordinary rate
GREEN_MIN_M = 12.0         # under this there is a strip, not a green
GREEN_MAX_M = 95.0         # over this the ground is the town's, not the household's
ROW_FRAC = 0.60            # how far across the green the row stands, house -> water
ROW_MAX_OUT_M = 24.0       # ...but never further from the house than this
BANK_CLEAR_M = 4.0         # and never nearer the waterline than this
SLIDE_M = 14.0             # how far a row may slide along its own line to find room
TANGENT_SPAN_M = 8.0       # over what span the local waterline direction is read


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def world():
    """Everything a stem must stand clear of, read once. Mirrors the dooryard pass."""
    sidecars = {}
    for path in sorted(SIDECARS.glob("*.json")):
        sc = load(path)
        if (sc.get("placement") or {}).get("local_e") is None:
            continue
        sidecars[path.stem] = sc
    obstructions = []
    for sid, sc in sidecars.items():
        pl = sc.get("placement") or {}
        if pl.get("vertical_anchor") == "water":
            continue
        if sc.get("drawn_by"):
            continue
        fp = footprint_world(sc)
        if len(fp) >= 3:
            obstructions.append(fp)
    streets = []
    for st in load(STREETS)["streets"]:
        pts = st.get("path_local_enu_m") or []
        if len(pts) >= 2:
            streets.append((pts, float(st.get("track_width_m") or 0.0)))
    fences = []
    for path in sorted(ENCLOSURES.glob("*.json")):
        if path.name == "index.json":
            continue
        for run in load(path).get("runs") or []:
            pts = run.get("path_local_enu_m") or []
            if len(pts) >= 2:
                fences.append(pts)
    hf = Heightfield.load(EPOCH)
    if hf is None:
        raise SystemExit("no heightfield at " + str(EPOCH))
    # EVERY STEM ALREADY COMMITTED, read through the manifest exactly as the
    # renderer reads it. The rows are dealt AFTER the dooryard pass and yield to
    # it: a dooryard tree is a claim about one house's own ground and a row is a
    # claim about the green in front of it, and where the two want the same metre
    # the older record keeps it.
    taken = []
    for entry in load(FLORA_INDEX).get("plantings", []):
        path = FLORA_INDEX.parent / entry["file"]
        if path == OUT:
            continue
        for stem in load(path).get("stems", []):
            taken.append(tuple(stem["at_local_enu_m"]))
    return sidecars, obstructions, streets, fences, hf, taken


def water_at(hf, e: float, n: float) -> bool:
    return hf.height(e, n) < float(hf.meta.get("water_surface_m", 0.0)) + 0.2


def clear(p, obstructions, streets, fences, hf, taken) -> bool:
    """The renderer's own refusals, asked of a point this rule chose."""
    e, n = p
    if not (hf.origin_e + EDGE_INSET_M <= e
            <= hf.origin_e + (hf.cols - 1) * hf.cell_m - EDGE_INSET_M
            and hf.origin_n + EDGE_INSET_M <= n
            <= hf.origin_n + (hf.rows - 1) * hf.cell_m - EDGE_INSET_M):
        return False
    if hf.height(e, n) < float(hf.meta.get("water_surface_m", 0.0)) + DRY_FLOOR_M:
        return False
    for fp in obstructions:
        cx = sum(q[0] for q in fp) / len(fp)
        cy = sum(q[1] for q in fp) / len(fp)
        if abs(e - cx) > 60 or abs(n - cy) > 60:
            continue
        if poly_contains(p, fp) or poly_edge_dist(p, fp) < FOOTPRINT_MARGIN_M:
            return False
    for pts, track_w in streets:
        if path_dist(p, pts) < track_w / 2 + TRACK_SHOULDER_M + TRACK_MARGIN_M:
            return False
    for pts in fences:
        if path_dist(p, pts) < FENCE_MARGIN_M:
            return False
    return all(math.hypot(e - te, n - tn) >= STEM_SPACING_M for te, tn in taken)


def nearest_water(hf, cx: float, cy: float):
    """Distance and bearing from a point to the nearest waterline, or (None, None).

    A ray scan at one-degree steps out to GREEN_MAX_M plus the footprint's own
    reach — the same shape of scan the dooryard pass uses to find allowed ground,
    asked of the water instead.
    """
    best_r, best_b = None, None
    for k in range(360):
        b = math.radians(k)
        se, cn = math.sin(b), math.cos(b)
        r = 1.0
        while r <= GREEN_MAX_M + 40.0:
            if water_at(hf, cx + se * r, cy + cn * r):
                if best_r is None or r < best_r:
                    best_r, best_b = r, b
                break
            r += 1.0
    return best_r, best_b


def waterline_along(hf, e: float, n: float, b: float, limit: float):
    """March from (e,n) on bearing b until the water; return the last dry point."""
    se, cn = math.sin(b), math.cos(b)
    r = 0.0
    while r <= limit:
        if water_at(hf, e + se * r, n + cn * r):
            return r
        r += 0.5
    return None


def bank_tangent(hf, cx: float, cy: float, b: float, reach: float):
    """The local direction of the waterline, read over TANGENT_SPAN_M.

    Two probes are stepped sideways from the house along the perpendicular to the
    bearing to the water, and each marches to the waterline on the same bearing.
    The line through the two hits is the bank's own direction there, so the row
    this file lays is parallel to the water rather than to a compass point.
    """
    pe, pn = math.cos(b), -math.sin(b)   # perpendicular to the bearing (e, n)
    hits = []
    for side in (-1.0, 1.0):
        ox = cx + pe * TANGENT_SPAN_M * side
        oy = cy + pn * TANGENT_SPAN_M * side
        d = waterline_along(hf, ox, oy, b, reach + 30.0)
        if d is None:
            return None
        hits.append((ox + math.sin(b) * d, oy + math.cos(b) * d))
    (ax, ay), (bx, by) = hits
    length = math.hypot(bx - ax, by - ay) or 1e-6
    return ((bx - ax) / length, (by - ay) / length)


def blocked_between(cx, cy, b, reach, obstructions, mine) -> str | None:
    """Whether another committed footprint stands between the house and the water."""
    se, cn = math.sin(b), math.cos(b)
    r = 2.0
    while r < reach:
        p = (cx + se * r, cy + cn * r)
        for i, fp in enumerate(obstructions):
            if i == mine:
                continue
            fx = sum(q[0] for q in fp) / len(fp)
            fy = sum(q[1] for q in fp) / len(fp)
            if abs(p[0] - fx) > 60 or abs(p[1] - fy) > 60:
                continue
            if poly_contains(p, fp):
                return f"{p[0]:.0f},{p[1]:.0f}"
        r += 1.0
    return None


def function_of(sid: str, sc: dict):
    path = STRUCTURES / f"{sid}.json"
    st = load(path) if path.exists() else sc
    fn = (st.get("attributes") or {}).get("function") if "attributes" in st \
        else st.get("function")
    if fn is None:
        fn = (sc.get("attributes") or {}).get("function")
    return fn.get("value") if isinstance(fn, dict) else fn


def build():
    sidecars, obstructions, streets, fences, hf, taken = world()
    band = None
    for sp in load(ZONE)["species"]:
        if sp["id"] == SPECIES:
            band = sp["height_m"]
    if band is None:
        raise SystemExit(f"{ZONE.relative_to(ROOT)} describes no {SPECIES} — the "
                         f"renderer would refuse every stem in this record")

    stems, rows, refused = [], [], []
    houses = 0
    for sid in sorted(sidecars):
        sc = sidecars[sid]
        if sc.get("archetype") not in DWELLING_ARCHETYPES:
            continue
        if not is_dwelling_function(function_of(sid, sc)):
            continue
        houses += 1
        # ---- clause 2: standing long enough to have grown a row --------------
        frm = ((sc.get("documented_range") or {}).get("from") or "")[:4]
        if not frm or float(frm) > PLANTED_BY:
            continue
        seasons = SCENE_YEAR - float(frm)
        # ---- clause 3: a green on the water ---------------------------------
        fp = footprint_world(sc)
        cx = sum(q[0] for q in fp) / len(fp)
        cy = sum(q[1] for q in fp) / len(fp)
        mine = next((i for i, q in enumerate(obstructions) if q == fp), None)
        reach, bearing = nearest_water(hf, cx, cy)
        if reach is None:
            refused.append(f"{sid}: no waterline within {GREEN_MAX_M + 40:.0f} m — "
                           f"no green to shade")
            continue
        # The GREEN is the open ground between the house and the water: measured
        # from the waterline back to the nearest edge of this house's own
        # footprint, not from its centroid, so a long low building is not credited
        # with the green its own plan stands on.
        green = poly_edge_dist((cx + math.sin(bearing) * reach,
                                cy + math.cos(bearing) * reach), fp)
        if green < GREEN_MIN_M:
            refused.append(f"{sid}: {green:.1f} m of open ground to the water, under "
                           f"the {GREEN_MIN_M:.0f} m a green needs — a strip, not a green")
            continue
        if green > GREEN_MAX_M:
            refused.append(f"{sid}: {green:.1f} m to the water, over the "
                           f"{GREEN_MAX_M:.0f} m bound — that ground is the town's, "
                           f"not this household's")
            continue
        where = blocked_between(cx, cy, bearing, reach, obstructions, mine)
        if where:
            refused.append(f"{sid}: another committed footprint stands between the "
                           f"house and the water at {where}")
            continue
        tangent = bank_tangent(hf, cx, cy, bearing, reach)
        if tangent is None:
            refused.append(f"{sid}: the waterline turns inside {TANGENT_SPAN_M:.0f} m "
                           f"of this house, so no bank direction can be read to lay a "
                           f"row parallel to")
            continue
        # ---- the height: as old as the house, at the cultivar's low rate -----
        height = round(min(band[1], max(band[0],
                                        GROWTH_M_PER_SEASON * seasons)), 1)
        # ---- clause 4: lay the row ------------------------------------------
        # WHERE ACROSS THE GREEN. ROW_FRAC of the way to the water, held off the
        # bank by BANK_CLEAR_M and never more than ROW_MAX_OUT_M from the house.
        # The cap is what keeps a row a HOUSE's row: on the deepest green in this
        # dataset the fraction alone would set it fifty metres out, which is a
        # file of trees in a field rather than the thing every plate composes —
        # house behind, row in front, both in one view.
        offset = min(reach - BANK_CLEAR_M, reach * ROW_FRAC, ROW_MAX_OUT_M)
        centre = (cx + math.sin(bearing) * offset, cy + math.cos(bearing) * offset)
        laid = lay(centre, tangent, obstructions, streets, fences, hf, taken)
        if laid is None:
            refused.append(f"{sid}: a green {green:.1f} m deep, and no line across it "
                           f"carries {ROW_STEMS} stems {SPACING_M} m apart clear of "
                           f"every footprint, track and fence — the row is refused "
                           f"whole, because a row of two is not the treatment")
            continue
        compass = (math.degrees(bearing) + 360.0) % 360.0
        for i, p in enumerate(laid):
            stems.append({
                "id": f"{sid}_poplar_{i + 1}",
                "species": SPECIES,
                "at_local_enu_m": [round(p[0], 2), round(p[1], 2)],
                "height_m": height,
                "confidence": "reconstructed",
                "note": (
                    f"STEM {i + 1} OF {ROW_STEMS} IN {sid}'s ROW, dealt by the rule in "
                    f"tools/generate_planted_rows.py. The row stands "
                    f"{offset:.1f} m out from the house across a green {green:.1f} m "
                    f"deep, on the water side of it, parallel to the waterline the "
                    f"committed heightfield draws there — Wau-Bun's \"broad green "
                    f"space ... inclosed between it and the river, and shaded by a "
                    f"row of Lombardy poplars\". {SPACING_M} m between stems is the "
                    f"0.195 of a grown row's height that five committed plates agree "
                    f"on, taken against this species' 18 m ceiling because a row is "
                    f"planted once at the spacing it will need. {height} m is "
                    f"{GROWTH_M_PER_SEASON} m for each of this house's "
                    f"{seasons:.1f} growing seasons since its own documented_range "
                    f"begins, held inside the species' recorded "
                    f"{band[0]}-{band[1]} m band. The position is invented."
                ),
            })
            taken.append(p)
        rows.append({
            "at": sid,
            "stems": ROW_STEMS,
            "height_m": height,
            "seasons_standing": round(seasons, 1),
            "green_m": round(green, 1),
            "stands_out_m": round(offset, 1),
            "bearing_to_water_deg": round(compass, 1),
        })
    return stems, rows, refused, houses


def lay(centre, tangent, obstructions, streets, fences, hf, taken):
    """ROW_STEMS stems on the line through `centre` along `tangent`, or None.

    The row may slide along its own line — never off it, and never bend — because
    sliding keeps the treatment (a straight file parallel to the water) while
    bending would invent a different one. The slide is tried outward from centred,
    so a row that fits where the plates put it stays there.
    """
    tx, ty = tangent
    half = (ROW_STEMS - 1) / 2.0
    slides = [0.0]
    step = 0.5
    s = step
    while s <= SLIDE_M:
        slides.extend((s, -s))
        s += step
    for slide in slides:
        pts = []
        for i in range(ROW_STEMS):
            d = (i - half) * SPACING_M + slide
            pts.append((round(centre[0] + tx * d, 2), round(centre[1] + ty * d, 2)))
        if all(clear(p, obstructions, streets, fences, hf, taken) for p in pts):
            return pts
    return None


def record(stems, rows, refused, houses):
    return {
        "_doc": (
            "A PLANTING RECORD in the shape T-0091 established and T-0074 reused: "
            "woody stems whose position is STATED rather than dealt from the land. "
            "This one is GENERATED — tools/generate_planted_rows.py holds the rule, "
            "prints why every house got a row or did not, and re-derives this file "
            "byte for byte in tools/check.sh."
        ),
        "id": "town_planted_rows",
        "name": "The rows of Lombardy poplars planted on the town's river greens",
        "kind": "planting",
        "scene": "1835",
        "target_date": "1835-07-01",
        "generated_by": "tools/generate_planted_rows.py",
        "generated_from": [
            "data/sidecars/1835/*.json",
            "data/structures/*.json",
            "data/streets/1835.json",
            "data/enclosures/*.json",
            "data/flora/index.json",
            "data/flora/zones/z10_settled_town.json",
            "data/terrain/epochs/e1834_harbor_cut/heightfield.json",
        ],
        "belongs_to": [r["at"] for r in rows],
        "in_enclosure": None,
        "zone": "z10_settled_town",
        "existence": {
            "value": True,
            "confidence": "inferred",
            "sources": ["kinzie_waubun_1856"],
            "note": (
                "THE TREATMENT IS ATTESTED AND THESE FOUR ADDRESSES ARE NOT. "
                "Wau-Bun, ch. XVII, of the Kinzie mansion on the north bank facing "
                "the fort: \"A broad green space was inclosed between it and the "
                "river, and shaded by a row of Lombardy poplars.\" That is a "
                "near-contemporary who lived there, naming the species, the row, "
                "the enclosed green and the side of the house. Seven committed "
                "plates draw the same row and five of them agree on FOUR stems at "
                "0.195 of their own height apart (the measurement is in the "
                "generator's docstring). WHAT NO SOURCE CARRIES is a second "
                "address: every plate that draws a poplar draws it at that one "
                "house, and that house is excluded from this scene "
                "(data/exclusions.json, kinzie_house — gone by 1835). So this "
                "record does what T-0052 did with the garden pickets: it takes the "
                "TREATMENT from the source and lets a RULE say which ground gets "
                "it. The rule is in tools/generate_planted_rows.py and its "
                "load-bearing clause is AGE AS THE DATASET CAN EVIDENCE IT: a "
                "house whose own record cannot be dated back five growing seasons "
                "gets no grown ornamental, because 131 of this town's dwellings "
                "carry a 1835 date only as an admission that 'no evidence "
                "establishes that this particular building existed', and a grown "
                "poplar row at a house of unknown age is an invention resting on "
                "an invention."
            ),
        },
        "rows": rows,
        "stems": stems,
        "refused": refused,
        "research_note": (
            f"{len(rows)} PLANTED ROWS, {len(stems)} STEMS, ACROSS THE "
            f"{len(rows)} OF THIS TOWN'S {houses} DWELLINGS THAT WERE STANDING "
            "LONG ENOUGH TO HAVE GROWN ONE — every one dealt by the rule in "
            "tools/generate_planted_rows.py and re-derived on every commit. "
            "THE AGE CLAUSE IS THE DEAL. `documented_range.from` on or before "
            f"{PLANTED_BY:.0f} refuses {houses - len(rows) - len([r for r in refused])} "
            "houses silently and names the rest below; almost all of them are the "
            "1835 programme's anonymous count-units, whose own records say no "
            "evidence establishes that the building existed before this year. A "
            "grown ornamental at a house first evidenced this year would be a "
            "claim about 1835 that nothing supports, and it is the difference "
            "between this record and one that lines the whole river with poplars. "
            "WHAT IS ATTESTED: the species, the row, the fenced green between "
            "house and river, and the side of the house — Wau-Bun ch. XVII, "
            "verbatim in the existence note. WHAT THE PLATES ADD: four stems at "
            "0.195 of their own height apart, measured off five independently "
            "drawn views (sd 0.010). WHAT THE PLATES REFUSE: a second location. "
            "Not one committed plate shows a Lombardy poplar anywhere in Chicago "
            "except the Kinzie group on the north bank, and that house is excluded "
            "from this scene — so extending the treatment to these four houses is "
            "this record's own invention, graded reconstructed on every stem and "
            "claimed in docs/LIBERTIES.md. WHAT IS DELIBERATELY NOT HERE: Dr. "
            "Harmon's nursery rows south of the fort, which docs/research/"
            "02-flora.md documents as young ornamental and fruit trees 2-5 m tall "
            "\"staked, in rows\" — a different treatment at a different scale, on "
            "ground about 1.2 km east of the modelled box, and its own parcel. "
            "WHAT WOULD UPGRADE IT: any notice, diary, view or nurseryman's list "
            "that places a Lombardy poplar at a second Chicago address, or T-0055's "
            "source record for the Kinzie-view plate."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="re-derive and diff, write nothing")
    args = ap.parse_args()
    stems, rows, refused, houses = build()
    text = json.dumps(record(stems, rows, refused, houses),
                      indent=2, ensure_ascii=False) + "\n"
    if args.check:
        if not OUT.exists():
            print(f"PLANTED ROW DRIFT\n  - {OUT.relative_to(ROOT)} is missing")
            return 1
        if OUT.read_text(encoding="utf-8") != text:
            print(f"PLANTED ROW DRIFT\n  - {OUT.relative_to(ROOT)} has drifted from "
                  f"the rule in tools/generate_planted_rows.py")
            return 1
        print(f"verified {len(rows)} planted row(s), {len(stems)} stems, across "
              f"{houses} dwellings ({len(refused)} named refusal(s))")
        return 0
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} — {len(rows)} row(s), {len(stems)} stems, "
          f"across {houses} dwellings ({len(refused)} named refusal(s))")
    for r in rows:
        print(f"  row at {r['at']}: {r['stems']} stems, {r['height_m']} m, "
              f"green {r['green_m']} m, out {r['stands_out_m']} m, "
              f"bearing {r['bearing_to_water_deg']} deg")
    for r in refused:
        print(f"  refused {r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
