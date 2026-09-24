#!/usr/bin/env python3
"""CARRY THE ANONYMOUS-ROOF ADJUDICATION OUT IN THE RECIPES. T-1451.

    tools/execute_roof_redeal.py --apply       execute what can be executed, write the report
    tools/execute_roof_redeal.py --check       re-derive and refuse drift
    tools/execute_roof_redeal.py --self-test   the guards, fired on fixtures

T-1445 adjudicated the town's 285 anonymous roofs against the re-derived
programme and wrote `data/reconstruction/1835_roof_redeal.json`: 253 keep, 32
refamily, 0 retire. That file MOVES NO ROOF. This tool is the other half --- it
carries the verdicts back into the authored recipes, so the generators re-derive
the records rather than anybody hand-editing 32 of them.

THE SPLIT THIS TOOL MAKES, AND WHY IT IS NOT A CONVENIENCE. A verdict is
executable here only if carrying it out leaves the RECORD ID alone:

  * `generate_west_infill.py` reads a placement's id from the recipe
    (`west_rec_008` -> `recon_1835_west_008`) and its family from a separate
    field. Refamilying is a one-field edit and nothing downstream is renamed.

  * The other three generators BUILD THE ID OUT OF THE FAMILY ---
    `recon_1835_south_{family}_{seq:03d}`, `recon_1835_north_{suffix}`,
    `recon_1835_blk_{block}_{family}_{seq:02d}`. Refamilying `..._c1_003` makes
    it `..._d1_003`, and that id is not private to its record: it is named by
    `data/sidecars/1835/`, `data/enclosures/`, `data/liberties.json`,
    `data/signage/`, `data/yard/`, `data/frontage/`, the lodger and seating
    files and the business layer. Those 26 verdicts are an ID MIGRATION across
    the derived layer, not an edit. T-1452 was split once the surface was
    measured: `tools/measure_roof_id_migration.py` classifies every reference
    they stand on, and T-1481 (south), T-1482 (the platted blocks) and T-1484
    (north) carry them out.

So the tool executes the six West Division verdicts, RECORDS the other 26 as
outstanding with the files that name each one, and refuses to pretend the
difference away. An executor that quietly renamed 26 ids and left ten files
pointing at roofs that no longer exist would pass its own check and break the
town.

WHAT IT WILL NOT DO, each refusal recorded rather than worked round:

  * A CONFIDENCE IS NEVER UPGRADED. These roofs are `inferred_anonymous` before
    and after. Refamilying changes what an invented building is, never how well
    attested it is.

  * NO VERDICT IS INVENTED HERE. Every family this tool writes is the
    `to_family` T-1445 reached, and the reason written beside it is T-1445's own
    reason, quoted. This tool adjudicates nothing.

  * A FOOTPRINT ONLY MOVES WHEN THE BAND REFUSES THE OLD ONE. 28 of the 32
    refamilied roofs land in a band their committed footprint already fits, and
    those keep every dimension they had. Where the band does refuse, the tool
    takes the band CORNER NEAREST THE STANDING AREA --- the smallest change the
    new family allows --- and never a size chosen to look right.

  * A RETIREMENT IS A SUBSTITUTION, NOT A DEMOLITION. Retire verdicts leave the
    standing count through `data/exclusions.json` under a `retired_reconstruction`
    guard that carries the bucket the roof left and the liberty tokens it
    resolved. The adjudication retires NONE today, so the guard stands empty ---
    which is a measurement, not an omission, and `--check` says the number.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RECON = DATA / "reconstruction"
LEDGER = RECON / "1835_roof_redeal.json"
WEST_RECIPE = RECON / "1835_phase2_west_wolf_point_approaches.json"
CROSSWALK = RECON / "1835_family_archetype_crosswalk.json"
EXCLUSIONS = DATA / "exclusions.json"
REPORT = ROOT / "docs" / "RESEARCH" / "1835_roof_redeal_execution.md"

sys.path.insert(0, str(ROOT / "tools"))
# The same letter-to-group mapping the adjudication and the 665 ledger use,
# imported rather than retyped: a group total computed under a second opinion
# about which letter is a workshop would not be the town's.
from reconcile_665 import group_of  # noqa: E402
# The one list of names a roof-id sweep may not move (T-1499).
import roof_id_pins  # noqa: E402

TICKET = "T-1451"
ARCHETYPE_OF = {f["id"]: f["current_placeholder_archetype"]
                for f in json.loads(
                    (RECON / "1835_family_archetype_crosswalk.json")
                    .read_text(encoding="utf-8"))["families"]}
WEST_PREFIX = "recon_1835_west_"

# The directories and files that name a roof by id. A refamily that moves the id
# has to move every one of these with it, which is what makes the other 26
# verdicts a migration. Measured on 2026-09-20 over the committed tree.
REFERENCE_ROOTS = ("data/sidecars", "data/enclosures", "data/liberties.json",
                   "data/signage", "data/yard", "data/frontage",
                   "data/residents", "data/businesses", "data/reconstruction",
                   "data/research")


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------
# which verdicts this tool may carry out
# --------------------------------------------------------------------------

def id_moves(roof_id: str, family: str) -> bool:
    """True when the record id encodes the family, so refamilying renames it."""
    return not roof_id.startswith(WEST_PREFIX)


def partition(ledger: dict) -> tuple[list[dict], list[dict], list[dict]]:
    refamily = [v for v in ledger["verdicts"] if v["verdict"] == "refamily"]
    retire = [v for v in ledger["verdicts"] if v["verdict"] == "retire"]
    here = [v for v in refamily if not id_moves(v["id"], v["family"])]
    outstanding = [v for v in refamily if id_moves(v["id"], v["family"])]
    return here, outstanding, retire


# --------------------------------------------------------------------------
# the footprint, when the band refuses the standing one
# --------------------------------------------------------------------------

def band_corner_nearest(area_ft2: float, band: list[float]) -> list[int]:
    """The band corner whose area is nearest the standing one.

    `to_band_ft` is [w_min, d_min, w_max, d_max] --- the crosswalk's own
    `16x20-20x26` read as four numbers. A refamilied roof takes the SMALLEST
    change its new family permits, so a privy raised into a shanty band takes the
    band's floor and a boarding house cut into a merchant house takes its ceiling.
    Nothing in between is offered, because an interpolated size would be a
    dimension this project invented twice.
    """
    lo, hi = [int(band[0]), int(band[1])], [int(band[2]), int(band[3])]
    return lo if abs(lo[0] * lo[1] - area_ft2) <= abs(hi[0] * hi[1] - area_ft2) else hi


# The eaves-front rule, and why this tool has to know it. `frame_dwelling_params`
# refuses a range deeper than 1.5x its own front: the eaves-front house is the
# 1835 form and the gable-front house is a Greek Revival habit that arrives here
# in 1836. A WORKSHOP is allowed to be long and narrow --- a smithy is --- so a
# 20x32 ft shop whose numbers sit inside the D5 dwelling band is `band_already_fits`
# to the adjudication and still a building `frame_dwelling` will not build. T-1445
# tested the band's four numbers and could not test the archetype's proportion;
# two of this parcel's six roofs fall in that gap. This tool closes it by taking
# the nearest footprint that is BOTH inside the new band and buildable, which is
# the same "smallest change the new family allows" rule the band corner follows.
#
# THE RATIO IS NAMED HERE AND OWNED THERE. If the archetype ever moves it, the
# generator's own `--check` fails on these records rather than passing quietly:
# `generate_west_infill.validate` imports each record's archetype module and
# resolves it, so this constant cannot drift out of sight.
EAVES_FRONT_MAX_DEPTH_RATIO = 1.5
PROPORTIONED_ARCHETYPES = ("frame_dwelling",)


def buildable_in_band(w: int, d: int, band: list[float]) -> list[int]:
    """The nearest footprint inside `band` that the eaves-front rule accepts.

    Two candidates only, and both are minimal moves of one dimension: widen the
    front until it carries the standing depth, or shorten the depth until the
    standing front carries it. The smaller change in area wins; a tie goes to the
    narrower building, which is the more modest claim about an invented roof.
    """
    if d <= w * EAVES_FRONT_MAX_DEPTH_RATIO:
        return [w, d]
    w_min, d_min, w_max, d_max = (int(x) for x in band)
    options = []
    wider = -(-d // EAVES_FRONT_MAX_DEPTH_RATIO)          # ceil
    wider = int(wider) if wider == int(wider) else int(wider) + 1
    if w_min <= wider <= w_max:
        options.append([wider, d])
    shorter = int(w * EAVES_FRONT_MAX_DEPTH_RATIO)        # floor
    if d_min <= shorter <= d_max:
        options.append([w, shorter])
    if not options:
        raise SystemExit(
            f"a {w}x{d} ft roof cannot be made eaves-front inside the "
            f"{w_min}x{d_min}-{w_max}x{d_max} band. The adjudication has put this "
            f"roof in a family it cannot be built as; that is a verdict to revisit, "
            f"not a dimension to invent")
    options.sort(key=lambda o: (abs(o[0] * o[1] - w * d), o[0] * o[1]))
    return options[0]


# --------------------------------------------------------------------------
# apply
# --------------------------------------------------------------------------

def plan_west(recipe: dict, here: list[dict]) -> list[dict]:
    """What each executable verdict does to the west recipe, before doing it.

    THE LEDGER MOVES UNDER THIS TOOL, BY DESIGN. `1835_roof_redeal.json` is a
    DERIVED adjudication over the town as it stands, re-derived by the gate on
    every commit. Carry a verdict out and the roof conforms, so the next
    re-derivation returns `keep` for it and the verdict is simply gone --- which
    is the adjudication working, not drift. The permanent record of what was
    carried out is therefore the recipe's own `redealt` block, written here and
    committed beside the placements it moved; `--check` reads THAT and then asks
    the live ledger the harder question, which is whether each re-dealt roof now
    conforms.
    """
    by_id = {}
    for p in recipe["placements"]:
        by_id["recon_1835_" + p["id"].replace("west_rec_", "west_")] = p
    plan = []
    for v in here:
        p = by_id.get(v["id"])
        if p is None:
            raise SystemExit(f"{v['id']}: refamilied by the adjudication but no "
                             f"placement in {WEST_RECIPE.name} carries it")
        fp = [int(x) for x in p["footprint_ft"]]
        to_fp = fp if v["band_already_fits"] else band_corner_nearest(
            float(v["footprint_ft2"]), v["to_band_ft"])
        if ARCHETYPE_OF[v["to_family"]] in PROPORTIONED_ARCHETYPES:
            to_fp = buildable_in_band(int(to_fp[0]), int(to_fp[1]), v["to_band_ft"])
        plan.append({
            "id": v["id"], "slot": p["id"],
            "from_family": v["family"], "to_family": v["to_family"],
            "from_group": v["group"], "to_group": v["to_group"],
            "from_footprint_ft": fp, "to_footprint_ft": [int(x) for x in to_fp],
            "band_already_fits": bool(v["band_already_fits"]),
            "inventory_class": p["inventory_class"],
            "why": v["reason"],
        })
    plan.sort(key=lambda e: e["id"])
    return plan


def totals_after(recipe: dict, plan: list[dict]) -> tuple[dict, dict]:
    """The recipe's own two aggregate claims, recomputed over every placement.

    Both count all 55 placements --- the 20 built and the 35 the terrain gate
    holds --- because that is what the file has always claimed and a redeal does
    not release a held slot.
    """
    moved = {e["slot"]: e["to_family"] for e in plan}
    fams: dict[str, int] = {}
    groups: dict[str, int] = {}
    for p in recipe["placements"]:
        fam = moved.get(p["id"], p["family"])
        fams[fam] = fams.get(fam, 0) + 1
        g = group_of(fam)
        groups[g] = groups.get(g, 0) + 1
    fam_out = {k: fams[k] for k in sorted(fams)}
    group_out = {k: groups.get(k, 0) for k in recipe["inventory_group_totals"]}
    for k in sorted(groups):
        group_out.setdefault(k, groups[k])
    return fam_out, group_out


WHY_REDEALT = (
    "THE ROOF COUNT DOES NOT MOVE AND SIX FAMILIES DO. T-1445 audited the town's "
    "285 anonymous roofs against the re-derived programme and the placement "
    "policy and returned 32 refamily verdicts and no retirements: the programme "
    "wants 668 roofs and 371 stand, so a standing roof is almost nowhere surplus "
    "to what the order book can occupy. Six of the 32 are this parcel's, and this "
    "parcel is where the verdicts could be carried out first because "
    "`generate_west_infill` reads a placement's id from the recipe rather than "
    "building it out of the family - so a refamily here renames nothing. The other "
    "26 ids DO carry their family (`recon_1835_south_c1_003` becomes `..._d1_003`) "
    "and are named by the sidecars, the enclosures, the liberties, the signage, "
    "the yard, the frontage, the lodger and seating files and the business layer; "
    "that is an id migration across the derived layer and it is T-1452's unit of "
    "work, not this one's. NOTHING IS ADJUDICATED HERE: every family below is the "
    "`to_family` T-1445 reached and every reason beside it is T-1445's own, "
    "quoted. The parcel still builds the same 20 roofs out of the same 55 "
    "placements, at the same coordinates and rotations and in the same inventory "
    "classes, against the same terrain gate holding the same 35 slots west of "
    "E -300 m. What moves is which family stands where, and ONE footprint - "
    "`recon_1835_west_011`, a 5x6 ft yard privy the policy refuses where it "
    "stands, raised to the 12x16 ft floor of the D2 rough-plank band it joins, "
    "which is the smallest change that family allows. FOUR WORKSHOP ROOFS LEAVE "
    "THE WEST DIVISION'S WORKSHOP ROW and the row falls from 8 standing to 4 "
    "against a target of 8. That shortfall is the adjudication's finding and not "
    "a side effect of this execution: a trade shop that stands off its street "
    "line is refused by the placement policy wherever the town would like a trade "
    "shop to be, and the roofs the west still wants are counted in the order book "
    "for the seating tickets to put back on the line. Everything here is still "
    "conjectural exactly as it was - that any building stood on this ground, "
    "which building it was, and every dimension of it. Recorded in "
    "docs/LIBERTIES.md."
)


def _render(value, indent: int) -> str:
    """json.dumps at the file's own nesting, so a surgical edit reads like the
    hand-kept lines around it rather than like a re-dump of the whole recipe."""
    pad = " " * indent
    body = json.dumps(value, indent=2, ensure_ascii=False)
    return body.replace("\n", "\n" + pad)


def _replace_key(text: str, key: str, value, indent: int = 2) -> str:
    """Replace one top-level key's value in place, touching nothing else.

    The west recipe keeps its 55 placements ONE PER LINE with blank lines between
    clusters - a hand-kept layout that a json.load/json.dump round trip silently
    destroys, turning a six-field edit into a 1,100-line diff nobody can read.
    So every write in this tool is a span replacement over the committed text.
    """
    needle = f'{" " * indent}"{key}":'
    at = text.index(needle)
    start = text.index(":", at) + 1
    while text[start] in " \t":
        start += 1
    opener = text[start]
    closer = {"{": "}", "[": "]"}[opener]
    depth, i, in_str, esc = 0, start, False, False
    while i < len(text):
        c = text[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c == opener:
            depth += 1
        elif c == closer:
            depth -= 1
            if depth == 0:
                break
        i += 1
    return text[:start] + _render(value, indent) + text[i + 1:]


def apply_west(text: str, recipe: dict, plan: list[dict]) -> str:
    for e in plan:
        line_at = text.index(f'"id":"{e["slot"]}"')
        eol = text.index("\n", line_at)
        line = text[line_at:eol]
        was = line
        if f'"family":"{e["to_family"]}"' in line and e["from_family"] != e["to_family"]:
            continue                      # already carried out by an earlier run
        line = line.replace(f'"family":"{e["from_family"]}"',
                            f'"family":"{e["to_family"]}"', 1)
        if line == was:
            raise SystemExit(f"{e['id']}: the placement does not stand as "
                             f"{e['from_family']}, so the adjudication is not "
                             f"describing the committed recipe")
        if e["from_footprint_ft"] != e["to_footprint_ft"]:
            old = f'"footprint_ft":[{e["from_footprint_ft"][0]},{e["from_footprint_ft"][1]}]'
            new = f'"footprint_ft":[{e["to_footprint_ft"][0]},{e["to_footprint_ft"][1]}]'
            if old not in line:
                raise SystemExit(f"{e['id']}: footprint {old} not on its own line")
            line = line.replace(old, new, 1)
        text = text[:line_at] + line + text[eol:]

    fam_out, group_out = totals_after(recipe, plan)
    # Both totals keep the FILE's key order - the schedule's, not the alphabet's -
    # and a family the redeal empties drops out rather than standing at zero.
    fam_ordered = {k: fam_out[k] for k in recipe["family_totals"] if fam_out.get(k)}
    for k in sorted(fam_out):
        fam_ordered.setdefault(k, fam_out[k])
    group_ordered = {k: group_out.get(k, 0) for k in recipe["inventory_group_totals"]}
    for k in sorted(group_out):
        group_ordered.setdefault(k, group_out[k])

    text = _replace_key(text, "family_totals", fam_ordered)
    text = _replace_key(text, "inventory_group_totals", group_ordered)

    redealt = {
        "on": "2026-09-20",
        "ticket": TICKET,
        "adjudicated_by": "T-1445",
        "ledger": "data/reconstruction/1835_roof_redeal.json",
        "why": WHY_REDEALT,
        "roofs": [
            {
                "id": e["id"], "slot": e["slot"],
                "was": e["from_family"], "now": e["to_family"],
                "was_group": e["from_group"], "now_group": e["to_group"],
                "was_footprint_ft": e["from_footprint_ft"],
                "footprint_ft": e["to_footprint_ft"],
                "footprint_moved": e["from_footprint_ft"] != e["to_footprint_ft"],
                "why": e["why"],
            }
            for e in plan
        ],
    }
    if '\n  "redealt":' in text:
        return _replace_key(text, "redealt", redealt)
    anchor = text.index('\n  "reservation_policy":')
    return (text[:anchor] + '\n  "redealt": ' + _render(redealt, 2) + ","
            + text[anchor:])


def apply_retirements(retire: list[dict]) -> dict:
    """Retire verdicts leave the standing count through the exclusions file.

    A retired reconstruction is NOT the same finding as an excluded building: the
    excluded list holds buildings the research deliberately left out of 1835, and
    a retired one is a roof this project itself invented and the order book no
    longer wants. Both must stay out of a scene, so they share the validator's
    guard and are told apart by `guard`.
    """
    ex = load(EXCLUSIONS)
    ex.setdefault("retired_reconstruction_doc", (
        "Reconstructed roofs the order book no longer has an occupant for, "
        "retired by an adjudication over the committed programme (T-1197/T-1445) "
        "and carried out by tools/execute_roof_redeal.py. An entry here is a "
        "SUBSTITUTION and not a demolition: it names the bucket the roof left and "
        "the liberty tokens it resolved, so the count it vacated can be seen. The "
        "validator refuses anything named here that still resolves into a scene, "
        "exactly as it refuses an excluded building. THE LIST IS EMPTY TODAY and "
        "that is a measurement: the programme wants 668 roofs and 371 stand, so "
        "there is almost nowhere a standing roof is surplus to what the town can "
        "occupy, and T-1445 returned 0 retirements out of 285 roofs audited."))
    ex["retired_reconstruction"] = [
        {
            "id": v["id"],
            "guard": "retired_reconstruction",
            "reason": v["reason"],
            "left_bucket": v["bucket"],
            "ticket": TICKET,
            "adjudicated_by": "T-1445",
        }
        for v in sorted(retire, key=lambda v: v["id"])
    ]
    ex["retired_reconstruction_count"] = len(retire)
    return ex


# --------------------------------------------------------------------------
# the id migration --- T-1480, the North Division parcel
# --------------------------------------------------------------------------
#
# WHY THIS IS A SECOND MODE AND NOT A SECOND TOOL. Everything above carries a
# verdict out where the record id does not move. `generate_north_infill` builds
# the id out of the family and the sequence (`recon_1835_north_c1_020` ->
# `..._d3_020`), so carrying the same verdict out here RENAMES a record that
# twenty-odd other committed files name. The rules that decide the new family
# and the new footprint are the ones above, imported rather than restated: a
# migration that adjudicated anything of its own would be a second opinion about
# a town this tool does not adjudicate.
#
# WHAT THE MIGRATION OWNS, AND WHAT IT REFUSES:
#
#   * THE ARCHETYPE IS ASKED OF THE GENERATOR THAT BUILDS THE PARCEL, not of the
#     crosswalk. They disagree about H2 --- the crosswalk's placeholder is
#     `frame_dwelling` and `generate_north_infill.archetype_for` returns
#     `frame_tavern` --- and it is the generator's answer that decides whether
#     `frame_dwelling_params`' eaves-front refusal applies to a roof. Asking the
#     crosswalk here would have cut two boarding houses to a proportion nothing
#     was going to enforce on them.
#
#   * THE INVENTORY CLASS FOLLOWS THE GROUP. `recon_1835_north_c1_047` is moved
#     from a store to a stable, and a stable is not a principal functional roof.
#     The north recipe authors the class per placement and gates its own 45/15
#     mix, so the class moves with the family and the mix is recounted --- it is
#     not a number chosen to keep the old total. This is the same principal /
#     ancillary line T-1482 has to re-deal for the platted blocks; here it is one
#     roof and the recipe's own counter is the whole of the arithmetic.
#
#   * A YARD GROUP NAMED AFTER A MIGRATED ROOF MOVES WITH IT. Three ancillary
#     placements sit in `nw_w2_005_yard`, `wk_w1_018_yard` and `re_c1_047_yard`
#     --- yards named for the roof they stand behind. Leaving those strings
#     behind would leave three yards named for buildings that no longer exist,
#     which is the rot this ticket is about.
#
#   * A RECEIPT IS NOT A REFERENCE. `renderers/unreal/receipts/` pins a signed
#     build to a `scene_source_commit`, `docs/unreal/prototype/` holds the import
#     report that build produced, and `tickets/` records what was found on a day.
#     All three name these roofs by the id they had then, and all three are
#     TRUE as written. Rewriting a dated measurement so it agrees with today is
#     falsifying it, so they are pinned and `--check-migration` counts them as
#     pinned rather than stale --- and names them, so the exemption is visible
#     rather than silent.
#
#   * THE DERIVED FILES ARE RE-DERIVED, NEVER REWRITTEN. The adjudication ledger
#     and its two reports name every migrated roof, and they are the measurement
#     of whether the migration worked: a rewritten ledger would agree with the
#     migration by construction. They are excluded from the substitution and
#     regenerated, which is how `--check` can ask the live adjudication whether
#     each migrated roof now returns `keep`.

NORTH_RECIPE = RECON / "1835_north_division_initial_parcel.json"
NORTH_PREFIX = "recon_1835_north_"
MIGRATION_TICKET = "T-1480"

# Derived from the roofs themselves, so they cannot be rewritten into agreement.
# A DIFFERENT IDEA FROM A PIN, and the shared list's gate refuses any overlap: a pin
# says "keep the old name", a re-derivation says "regenerate until it holds the new".
MIGRATION_REDERIVED = roof_id_pins.REDERIVED

# Where a record's id is part of a FILE NAME. Each is renamed beside the
# substitution, because a file called after a roof that no longer exists is the
# same dangling reference as a line of JSON that names one.
MIGRATION_FILENAMES = (
    ("data/structures", "{id}.json"),
    ("data/sidecars/1835", "{id}.json"),
    ("data/residents/lodgers", "hh_lodging_{id}.json"),
    ("assets/gltf", "{id}__inferred_1835.glb"),
    ("assets/web", "{id}__inferred_1835.glb"),
)

# TRUE AS WRITTEN ON THE DAY THEY WERE WRITTEN, and the list of them is no longer
# kept here. It was, and `tools/migrate_roof_ids.py` kept its own beside it, with
# overlapping contents, the same reasoning written out twice and nothing holding
# the two in agreement but somebody remembering to edit both — which twice nobody
# did. T-1499 made it one list: `tools/roof_id_pins.py`, every pin carrying its own
# reason and the kind of name it is, read by both sweeps, with a gate step that
# asserts the two of them answer alike for every file in the tree.
#
# The North recipe's own `migrated` block was NOT in either list: it was skipped
# inline, two branches below the list, with its reason in a trailing comment. It is
# a pin. It is written down as one now, which also means `--check-migration` NAMES
# it among the pinned rather than passing it over in silence.


def keeps_the_old_name(rel: str) -> bool:
    """This sweep's verdict, and it is the shared list's — asked through this tool's
    own name so that `roof_id_pins --check` is putting the question to the SWEEP.
    A run that re-introduces a private list here diverges from the other sweep and
    fails that step rather than quietly disagreeing with it."""
    return roof_id_pins.is_pinned(rel)

ANCILLARY_GROUPS = ("barns_stables", "small_outbuildings")


def north_archetype(family: str) -> str:
    """The archetype the parcel's own generator deals this family.

    Imported, never retyped: which roofs `frame_dwelling_params` will refuse for
    depth is decided by the generator that writes the records, and this tool has
    to predict the same answer or it computes a footprint nothing enforces.
    """
    sys.path.insert(0, str(ROOT / "tools"))
    import generate_north_infill  # noqa: PLC0415
    return generate_north_infill.archetype_for(family)


def plan_north(recipe: dict, outstanding: list[dict]) -> list[dict]:
    fields = recipe["placement_fields"]
    rows = {dict(zip(fields, row))["id_suffix"]: dict(zip(fields, row))
            for row in recipe["placements"]}
    plan = []
    for v in sorted(outstanding, key=lambda v: v["id"]):
        if not v["id"].startswith(NORTH_PREFIX):
            continue
        suffix = v["id"][len(NORTH_PREFIX):]
        row = rows.get(suffix)
        if row is None:
            raise SystemExit(f"{v['id']}: refamilied by the adjudication but no "
                             f"placement in {NORTH_RECIPE.name} carries it")
        if row["family"] != v["family"]:
            raise SystemExit(f"{v['id']}: the placement stands as {row['family']}, "
                             f"not the {v['family']} the adjudication describes")
        fp = [int(row["width_ft"]), int(row["depth_ft"])]
        to_fp = fp if v["band_already_fits"] else band_corner_nearest(
            float(v["footprint_ft2"]), v["to_band_ft"])
        if north_archetype(v["to_family"]) in PROPORTIONED_ARCHETYPES:
            to_fp = buildable_in_band(int(to_fp[0]), int(to_fp[1]), v["to_band_ft"])
        new_suffix = f"{v['to_family'].lower()}_{int(row['sequence']):03d}"
        to_class = ("ancillary" if v["to_group"] in ANCILLARY_GROUPS
                    else "principal_functional")
        plan.append({
            "id": v["id"], "new_id": NORTH_PREFIX + new_suffix,
            "sequence": int(row["sequence"]),
            "suffix": suffix, "new_suffix": new_suffix,
            "from_family": v["family"], "to_family": v["to_family"],
            "from_group": v["group"], "to_group": v["to_group"],
            "from_footprint_ft": fp, "to_footprint_ft": [int(x) for x in to_fp],
            "from_inventory_class": row["inventory_class"],
            "to_inventory_class": to_class,
            "band_already_fits": bool(v["band_already_fits"]),
            "why": v["reason"],
        })
    seen = [e["new_id"] for e in plan]
    if len(set(seen)) != len(seen):
        raise SystemExit("two migrated roofs would take the same id; the "
                         "sequence no longer makes the id unique")
    return plan


WHY_MIGRATED = (
    "THE SAME 60 ROOFS STAND AND NINE OF THEM ARE CALLED SOMETHING ELSE. T-1445 "
    "adjudicated the town's 285 anonymous roofs and returned 32 refamily "
    "verdicts; T-1451 carried out the six whose ids do not move. These nine are "
    "the North Division's, and `generate_north_infill` builds a record's id out "
    "of its family and sequence, so refamilying one RENAMES it and every "
    "committed file that names it --- the sidecars, the liberties, the signage "
    "and trade goods, the lodging model and the lodgers seated under two of "
    "these roofs, the reconstructed seating, the business layer and the "
    "boarding house authored over `..._h3_045`, the hay limits, the Newberry "
    "leads, the land-sale ground index, the asset manifests and the two GLBs "
    "per roof. NOTHING IS ADJUDICATED HERE: every family below is the "
    "`to_family` T-1445 reached and every reason beside it is T-1445's own, "
    "quoted. The parcel still builds 60 roofs at the same coordinates, "
    "rotations and clusters. What moves is which family stands where, THREE "
    "FOOTPRINTS that the family they join cannot carry at the depth they had "
    "--- `..._c2_027` 20x32 to 20x30 ft, `..._w1_018` 18x28 to 18x27 ft, and "
    "`..._h3_045` 32x48 to the 30x42 ft ceiling of the H2 band --- and ONE "
    "INVENTORY CLASS: `..._c1_047` is moved from a store to a stable and a "
    "stable is ancillary, so the parcel's mix is recounted from 45/15 to 44/16 "
    "rather than the class being held to keep an old total. Three yards named "
    "after a migrated roof are renamed with it. Everything here is still "
    "conjectural exactly as it was --- that any building stood on this ground, "
    "which building it was, and every dimension of it. Recorded in "
    "docs/LIBERTIES.md."
)


def migrate_recipe(recipe: dict, plan: list[dict]) -> dict:
    """The recipe, re-dealt. Loaded and dumped whole: this file is already
    one-value-per-line at indent 2 and a round trip reproduces it byte for byte,
    so the surgical span editing the west recipe needs buys nothing here."""
    fields = recipe["placement_fields"]
    by_suffix = {e["suffix"]: e for e in plan}
    renamed_yards = {f"{tag}_{e['suffix']}_yard": f"{tag}_{e['new_suffix']}_yard"
                     for e in plan for tag in ("nw", "wk", "re", "km", "ke", "rf")}
    for row in recipe["placements"]:
        r = dict(zip(fields, row))
        e = by_suffix.get(r["id_suffix"])
        if e is not None:
            r["id_suffix"] = e["new_suffix"]
            r["family"] = e["to_family"]
            r["width_ft"], r["depth_ft"] = e["to_footprint_ft"]
            r["inventory_class"] = e["to_inventory_class"]
        if r["yard_group"] in renamed_yards:
            r["yard_group"] = renamed_yards[r["yard_group"]]
        row[:] = [r[f] for f in fields]

    fams: dict[str, int] = {}
    groups: dict[str, int] = {}
    classes: dict[str, int] = {}
    for row in recipe["placements"]:
        r = dict(zip(fields, row))
        fams[r["family"]] = fams.get(r["family"], 0) + 1
        g = group_of(r["family"])
        groups[g] = groups.get(g, 0) + 1
        classes[r["inventory_class"]] = classes.get(r["inventory_class"], 0) + 1

    inv = recipe["inventory"]
    inv["principal_functional"] = classes.get("principal_functional", 0)
    inv["ancillary"] = classes.get("ancillary", 0)
    # Both totals keep the FILE's key order --- the schedule's, not the alphabet's ---
    # and a family the redeal empties drops out rather than standing at zero.
    inv["group_totals"] = ({k: groups[k] for k in inv["group_totals"] if groups.get(k)}
                           | {k: groups[k] for k in sorted(groups)
                              if k not in inv["group_totals"]})
    inv["family_totals"] = ({k: fams[k] for k in inv["family_totals"] if fams.get(k)}
                            | {k: fams[k] for k in sorted(fams)
                               if k not in inv["family_totals"]})

    recipe["migrated"] = {
        "on": "2026-09-20",
        "ticket": MIGRATION_TICKET,
        "adjudicated_by": "T-1445",
        "executed_under": TICKET,
        "ledger": "data/reconstruction/1835_roof_redeal.json",
        "why": WHY_MIGRATED,
        "yard_groups_renamed": dict(sorted(
            (k, v) for k, v in renamed_yards.items()
            if any(k == dict(zip(fields, row))["yard_group"] or
                   v == dict(zip(fields, row))["yard_group"]
                   for row in recipe["placements"]))),
        "roofs": [
            {
                "was_id": e["id"], "id": e["new_id"], "sequence": e["sequence"],
                "was": e["from_family"], "now": e["to_family"],
                "was_group": e["from_group"], "now_group": e["to_group"],
                "was_footprint_ft": e["from_footprint_ft"],
                "footprint_ft": e["to_footprint_ft"],
                "footprint_moved": e["from_footprint_ft"] != e["to_footprint_ft"],
                "was_inventory_class": e["from_inventory_class"],
                "inventory_class": e["to_inventory_class"],
                "why": e["why"],
            }
            for e in plan
        ],
    }
    return recipe


def migrate_tree(plan: list[dict]) -> tuple[list[str], list[str]]:
    """Carry every committed reference across, and rename every file called
    after a migrated roof. Returns (files rewritten, files renamed)."""
    moves = {e["id"]: e["new_id"] for e in plan}
    yards = {}
    for e in plan:
        for tag in ("nw", "wk", "re", "km", "ke", "rf"):
            yards[f"{tag}_{e['suffix']}_yard"] = f"{tag}_{e['new_suffix']}_yard"

    # A MANIFEST ENTRY IS THE RECORD OF A BAKE, and a bake whose output has been
    # renamed leaves one pointing at a file that is not there. The substitution
    # below carries the key across with everything else; the entry then holds the
    # OLD mesh's hash under the new name, which `validate.py --stale` reads as
    # "re-bake me" — exactly right, because that is what has to happen next.
    # Dropping the entry instead would let an unbaked roof through the staleness
    # gate by having nothing to compare against.
    renamed = []
    for folder, pattern in MIGRATION_FILENAMES:
        for e in plan:
            old = ROOT / folder / pattern.format(id=e["id"])
            if old.exists():
                new = ROOT / folder / pattern.format(id=e["new_id"])
                old.rename(new)
                renamed.append(str(new.relative_to(ROOT)))

    skip = {ROOT / rel for rel in MIGRATION_REDERIVED}
    rewritten = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or path in skip:
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel.startswith(roof_id_pins.NOT_THE_SOURCE_TREE) or keeps_the_old_name(rel):
            continue
        if path.suffix.lower() not in (".json", ".md", ".py", ".js", ".mjs",
                                       ".html", ".css", ".txt", ".sh", ".csv"):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="strict")
        except UnicodeDecodeError:
            continue     # not text after all; --check-migration sweeps for misses
        out = text
        for old, new in moves.items():
            # The lookahead refuses a LONGER id, not a longer string. Every id in
            # this parcel ends `_<3 digits>`, so only a digit can extend one —
            # and `_` must be allowed through, because both manifests key their
            # entries `<id>__inferred_1835.glb` and an underscore-excluding
            # lookahead walked straight past all 18 of them (measured, T-1480).
            out = re.sub(rf"{old}(?![0-9A-Za-z])", new, out)
        for old, new in yards.items():
            out = out.replace(old, new)
        if out != text:
            path.write_text(out, encoding="utf-8")
            rewritten.append(rel)
    return sorted(rewritten), sorted(renamed)


def check_migration() -> int:
    """Did the migration work, and is anything still pointing at a roof that
    no longer exists?"""
    recipe = load(NORTH_RECIPE)
    block = recipe.get("migrated")
    if not block:
        print(f"DRIFT: no migration recorded in {NORTH_RECIPE.name} — run --migrate")
        return 1
    fields = recipe["placement_fields"]
    rows = {dict(zip(fields, row))["id_suffix"]: dict(zip(fields, row))
            for row in recipe["placements"]}
    verdict = {v["id"]: v for v in load(LEDGER)["verdicts"]}

    for r in block["roofs"]:
        suffix = r["id"][len(NORTH_PREFIX):]
        row = rows.get(suffix)
        if row is None:
            print(f"DRIFT: {r['id']} was migrated but no placement carries it")
            return 1
        if row["family"] != r["now"]:
            print(f"DRIFT: {r['id']} was migrated to {r['now']} and stands as "
                  f"{row['family']}")
            return 1
        if [int(row["width_ft"]), int(row["depth_ft"])] != [int(x) for x in r["footprint_ft"]]:
            print(f"DRIFT: {r['id']} was migrated at {r['footprint_ft']} ft and "
                  f"stands at {[row['width_ft'], row['depth_ft']]}")
            return 1
        if row["inventory_class"] != r["inventory_class"]:
            print(f"DRIFT: {r['id']} was migrated as {r['inventory_class']} and "
                  f"stands as {row['inventory_class']}")
            return 1
        # THE EXECUTION HAS TO HAVE WORKED --- the same question --check asks of
        # the west parcel. A migrated roof the live adjudication still wants to
        # refamily was moved into a family refused where it stands.
        v = verdict.get(r["id"])
        if v is None:
            print(f"DRIFT: the adjudication no longer audits {r['id']}")
            return 1
        if v["verdict"] != "keep":
            print(f"FAIL: {r['id']} was migrated {r['was']} -> {r['now']} and the "
                  f"adjudication still says {v['verdict']} — the migration did "
                  f"not settle it")
            return 1
        if verdict.get(r["was_id"]) is not None:
            print(f"DRIFT: {r['was_id']} is still audited, so the old record "
                  f"still stands")
            return 1

    # NOTHING MAY STILL NAME A ROOF THAT NO LONGER EXISTS. This is the check the
    # ticket is for: the migration is not "the recipe says D4", it is "no
    # committed file is left pointing at `recon_1835_north_w2_005`".
    stale, pinned = [], []
    old_ids = [r["was_id"] for r in block["roofs"]]
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel.startswith(roof_id_pins.NOT_THE_SOURCE_TREE):
            continue
        if keeps_the_old_name(rel):
            text = path.read_text(encoding="utf-8", errors="ignore")
            if any(re.search(rf"{old}(?![0-9A-Za-z])", text) for old in old_ids):
                pinned.append(rel)
            continue
        if path.suffix.lower() in (".glb", ".png", ".jpg", ".jpeg", ".pdf",
                                   ".webp", ".tif", ".tiff", ".zip", ".xlsx"):
            if any(path.name.startswith(old) for old in old_ids):
                stale.append(rel)
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for old in old_ids:
            if re.search(rf"{old}(?![0-9A-Za-z])", text):
                stale.append(f"{rel} names {old}")
                break
    if stale:
        print("MIGRATION INCOMPLETE — these still name a migrated roof:")
        for s in stale[:40]:
            print(f"  - {s}")
        return 1

    classes: dict[str, int] = {}
    fams: dict[str, int] = {}
    for row in recipe["placements"]:
        r = dict(zip(fields, row))
        classes[r["inventory_class"]] = classes.get(r["inventory_class"], 0) + 1
        fams[r["family"]] = fams.get(r["family"], 0) + 1
    inv = recipe["inventory"]
    if (inv["principal_functional"] != classes.get("principal_functional", 0)
            or inv["ancillary"] != classes.get("ancillary", 0)):
        print("DRIFT: the recipe's inventory-class mix does not count its own "
              "placements")
        return 1
    if inv["family_totals"] != {k: v for k, v in fams.items()
                                if k in inv["family_totals"]} or \
            sum(inv["family_totals"].values()) != len(recipe["placements"]):
        print("DRIFT: family_totals does not count the placements it claims")
        return 1

    print(f"verified {len(block['roofs'])} migrated roof(s), every one now `keep`, "
          f"and no live reference names an id they left behind")
    for rel in pinned:
        print(f"  pinned, true as written on its own date: {rel}")
    return 0


# --------------------------------------------------------------------------
# the report
# --------------------------------------------------------------------------

def references(roof_id: str) -> list[str]:
    hits = []
    for root in REFERENCE_ROOTS:
        base = ROOT / root
        paths = [base] if base.is_file() else sorted(base.rglob("*.json"))
        for p in paths:
            if p.name == f"{roof_id}.json":
                continue
            try:
                if roof_id in p.read_text(encoding="utf-8"):
                    hits.append(str(p.relative_to(ROOT)))
            except (OSError, UnicodeDecodeError):
                continue
    return hits


def write_report(plan: list[dict], outstanding: list[dict], retire: list[dict]) -> str:
    out = []
    out.append("# The anonymous-roof redeal, carried out — July 1835\n")
    out.append(f"DERIVED — regenerate with `tools/execute_roof_redeal.py --apply`. {TICKET}.\n")
    out.append(
        "T-1445 adjudicated 285 anonymous roofs and moved none of them. This is the "
        "execution: the verdicts carried back into the authored recipes so the "
        "generators re-derive the records. It adjudicates nothing — every family "
        "below is the `to_family` T-1445 reached.\n")
    out.append(f"- refamily verdicts standing: **{len(plan) + len(outstanding)}**")
    out.append(f"- carried out here: **{len(plan)}** (the West Division parcel)")
    out.append(f"- outstanding, and why: **{len(outstanding)}** — the record id carries "
               f"the family, so executing them renames a roof other files name "
               f"(T-1481/T-1482/T-1484, over the surface "
               f"`tools/measure_roof_id_migration.py` measures)")
    out.append(f"- retired: **{len(retire)}** — the guard stands empty and that is a "
               f"measurement, not an omission\n")
    out.append("## Carried out\n")
    out.append("| roof | was | now | group | footprint ft | why |")
    out.append("| --- | --- | --- | --- | --- | --- |")
    for e in plan:
        fp = f"{e['to_footprint_ft'][0]}x{e['to_footprint_ft'][1]}"
        if e["from_footprint_ft"] != e["to_footprint_ft"]:
            fp += f" (was {e['from_footprint_ft'][0]}x{e['from_footprint_ft'][1]})"
        out.append(f"| `{e['id']}` | {e['from_family']} | {e['to_family']} | "
                   f"{e['from_group']} → {e['to_group']} | {fp} | {e['why']} |")
    out.append("")
    out.append("## Outstanding — the id migration T-1481, T-1482 and T-1484 own\n")
    out.append(
        "Each of these becomes a new id when its family moves, and the id is not "
        "private to its record. The files below name it today and would point at a "
        "roof that no longer exists. Counted over the committed tree; a record's own "
        "`data/structures/<id>.json` is not listed.\n")
    out.append("| roof | becomes | files that name it |")
    out.append("| --- | --- | ---: |")
    for v in sorted(outstanding, key=lambda v: v["id"]):
        if v["id"].startswith("recon_1835_blk_"):
            new = v["id"].rsplit("_", 2)[0] + f"_{v['to_family'].lower()}_" + v["id"].rsplit("_", 1)[1]
        else:
            head, _fam, seq = v["id"].rsplit("_", 2)
            new = f"{head}_{v['to_family'].lower()}_{seq}"
        refs = references(v["id"])
        out.append(f"| `{v['id']}` | `{new}` | {len(refs)} |")
    out.append("")
    blk = sorted({v["id"].removeprefix("recon_1835_").rsplit("_", 2)[0]
                  for v in outstanding if v["id"].startswith("recon_1835_blk_")})
    n_blk = sum(1 for v in outstanding if v["id"].startswith("recon_1835_blk_"))
    out.append(
        f"The {n_blk} platted-block roofs among them, across {len(blk)} block(s) "
        f"({', '.join('`' + b + '`' for b in blk)}), carry a second difficulty "
        "the West parcel does not. Their slots are `ancillary` — yard buildings off "
        "the block alley — and the family each is moved into is a dwelling. "
        "`generate_block_infill` gates a block's principal/ancillary split against "
        "the schedule the recipe claims, and refuses a second principal roof on a "
        "lot that already has one, so whether a rear cottage counts as the one or "
        "the other is a re-deal of the block and its claimed mix, not a field "
        "edit.\n")
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------------
# self-test
# --------------------------------------------------------------------------

def self_test() -> int:
    ok = True

    def want(cond, msg):
        nonlocal ok
        if not cond:
            ok = False
            print(f"  FAIL {msg}")

    want(band_corner_nearest(30.0, [12, 16, 18, 24]) == [12, 16],
         "a 30 ft2 privy raised into the D2 band takes the band floor, not its ceiling")
    want(band_corner_nearest(1513.9, [24, 32, 30, 42]) == [30, 42],
         "a 1514 ft2 boarding house cut into the H2 band takes the band ceiling")
    want(id_moves("recon_1835_south_c1_003", "C1"),
         "a south id carries its family and therefore moves")
    want(id_moves("recon_1835_blk_randolph_market_a1_07", "A1"),
         "a platted-block id carries its family and therefore moves")
    want(not id_moves("recon_1835_west_008", "W1"),
         "a west id does not carry its family and therefore does not move")

    want(buildable_in_band(20, 32, [18, 28, 24, 34]) == [20, 30],
         "a 20x32 shop made a D5 cottage loses two feet of depth, the smaller move")
    want(buildable_in_band(22, 34, [20, 26, 24, 34]) == [22, 33],
         "a 22x34 shop made a D6 cottage loses one foot of depth")
    want(buildable_in_band(18, 24, [16, 20, 18, 24]) == [18, 24],
         "a footprint the eaves-front rule already accepts is left alone")
    try:
        buildable_in_band(10, 40, [10, 40, 10, 40])
        want(False, "a roof that cannot be made eaves-front inside its band is refused")
    except SystemExit:
        pass

    # A verdict this parcel does not carry is a refusal, not a silent skip.
    try:
        plan_west({"placements": []}, [{"id": "recon_1835_west_404", "family": "W1",
                                        "to_family": "D4", "group": "workshops",
                                        "to_group": "ordinary_dwellings",
                                        "band_already_fits": True, "footprint_ft2": 100.0,
                                        "to_band_ft": [18, 24, 22, 30], "reason": "x"}])
        want(False, "a verdict with no placement to land on is refused")
    except SystemExit:
        pass

    # The totals are recomputed over every placement, held and built alike.
    recipe = {"placements": [{"id": "a", "family": "W1"}, {"id": "b", "family": "D3"}],
              "inventory_group_totals": {"workshops": 1, "ordinary_dwellings": 1}}
    fams, groups = totals_after(recipe, [{"slot": "a", "to_family": "D3"}])
    want(fams == {"D3": 2}, "a refamilied slot leaves its old family total")
    want(groups["workshops"] == 0 and groups["ordinary_dwellings"] == 2,
         "a refamilied slot leaves its old group total")

    print("  self-test:", "ok" if ok else "FAILED")
    return 0 if ok else 1


# --------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--migrate", action="store_true",
                    help="carry the North Division's nine id-moving verdicts out")
    ap.add_argument("--check-migration", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return self_test()
    if args.check_migration:
        return check_migration()

    ledger = load(LEDGER)
    here, outstanding, retire = partition(ledger)
    recipe = load(WEST_RECIPE)

    if args.migrate:
        north = load(NORTH_RECIPE)
        plan = plan_north(north, outstanding)
        if not plan:
            print("no North Division verdict is outstanding; nothing to migrate")
            return 0
        rewritten, renamed = migrate_tree(plan)
        dump(NORTH_RECIPE, migrate_recipe(north, plan))
        print(f"{len(plan)} North Division roof(s) migrated; "
              f"{len(renamed)} file(s) renamed, {len(rewritten)} rewritten")
        for rel in rewritten:
            print(f"  ~ {rel}")
        return 0

    if args.apply:
        plan = plan_west(recipe, here)
        # Verdicts a previous run already carried out are gone from the ledger and
        # stand in the recipe. Merge them so the report and the totals describe the
        # whole execution rather than only today's remainder.
        done = {e["id"] for e in plan}
        for r in recipe.get("redealt", {}).get("roofs", []):
            if r["id"] in done:
                continue
            plan.append({
                "id": r["id"], "slot": r["slot"],
                "from_family": r["was"], "to_family": r["now"],
                "from_group": r["was_group"], "to_group": r["now_group"],
                "from_footprint_ft": list(r.get("was_footprint_ft", r["footprint_ft"])),
                "to_footprint_ft": list(r["footprint_ft"]),
                "band_already_fits": not r["footprint_moved"],
                "inventory_class": None, "why": r["why"],
            })
        plan.sort(key=lambda e: e["id"])
        text = WEST_RECIPE.read_text(encoding="utf-8")
        WEST_RECIPE.write_text(apply_west(text, recipe, plan), encoding="utf-8")
        dump(EXCLUSIONS, apply_retirements(retire))
        REPORT.write_text(write_report(plan, outstanding, retire), encoding="utf-8")
        print(f"{len(plan)} West Division verdict(s) carried out; "
              f"{len(outstanding)} outstanding as an id migration; "
              f"{len(retire)} retired")
        return 0

    # --check. Two questions, and the second is the one worth asking.
    fresh = load(WEST_RECIPE)
    executed = fresh.get("redealt", {}).get("roofs", [])
    if not executed:
        print("DRIFT: no execution recorded in "
              f"{WEST_RECIPE.name} — run --apply")
        return 1
    by_slot = {p["id"]: p for p in fresh["placements"]}
    verdict = {v["id"]: v for v in ledger["verdicts"]}

    # 1. the recipe says what was carried out, and the placements say the same thing
    for r in executed:
        p = by_slot.get(r["slot"])
        if p is None:
            print(f"DRIFT: {r['id']} was re-dealt but {r['slot']} is not a placement")
            return 1
        if p["family"] != r["now"]:
            print(f"DRIFT: {r['id']} was re-dealt to {r['now']} and stands as "
                  f"{p['family']}")
            return 1
        if [int(x) for x in p["footprint_ft"]] != [int(x) for x in r["footprint_ft"]]:
            print(f"DRIFT: {r['id']} was re-dealt at "
                  f"{r['footprint_ft']} ft and stands at {p['footprint_ft']}")
            return 1

    # 2. THE EXECUTION HAS TO HAVE WORKED. A refamily is for one thing: the roof
    #    stops breaching the placement policy. So ask the live adjudication what it
    #    now says about each roof this tool moved, and require `keep`. A re-dealt
    #    roof still returning `refamily` means the family it was moved into is
    #    refused where it stands too, and carrying the verdict out achieved nothing.
    for r in executed:
        v = verdict.get(r["id"])
        if v is None:
            print(f"DRIFT: the adjudication no longer audits {r['id']}")
            return 1
        if v["verdict"] != "keep":
            print(f"FAIL: {r['id']} was re-dealt {r['was']} -> {r['now']} and the "
                  f"adjudication still says {v['verdict']} — the execution did not "
                  f"settle it")
            return 1

    # 3. the totals still count the placements the recipe holds
    fam_out, group_out = totals_after(fresh, [])
    if fresh["family_totals"] != {k: v for k, v in fam_out.items() if v}:
        print("DRIFT: family_totals does not count the placements it claims")
        return 1
    if dict(fresh["inventory_group_totals"]) != group_out:
        print("DRIFT: inventory_group_totals does not count the placements it claims")
        return 1

    # 4. everything still outstanding moves an id, which is why it is still outstanding
    for v in outstanding:
        if not id_moves(v["id"], v["family"]):
            print(f"DRIFT: {v['id']} is outstanding but its id does not move — "
                  f"this tool should have carried it out")
            return 1

    ex = load(EXCLUSIONS)
    if ex.get("retired_reconstruction_count") != len(retire):
        print(f"DRIFT: the retired_reconstruction guard counts "
              f"{ex.get('retired_reconstruction_count')}, the adjudication retires "
              f"{len(retire)}")
        return 1
    if len(ex.get("retired_reconstruction", [])) != len(retire):
        print("DRIFT: the retired_reconstruction guard does not hold its own count")
        return 1

    print(f"verified {len(executed)} carried-out verdict(s), every one now `keep`; "
          f"{len(outstanding)} outstanding as an id migration; "
          f"{len(retire)} retired roof(s) under the guard")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
