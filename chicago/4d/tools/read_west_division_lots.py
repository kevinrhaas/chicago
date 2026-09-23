#!/usr/bin/env python3
"""Hold the West Division's lot figures to the sheet they were read off.

T-0689. T-0444's acceptance point 1 asked for the West Division's lot dimensions
and block lot-counts to be READ off the Thompson plat and committed as data,
explicitly not inferred from the South Division. PR #681 answered the rest of
T-0444, said in its own words that point 1 was still owed, and T-0444 was closed
without it. `data/traces/thompson_west_division_lots.json` is that reading; this
file is its gate.

WHAT IT CHECKS, AND WHY EACH CHECK IS WORTH RUNNING EVERY COMMIT.

  the sheet          Every figure in the trace cites a pixel region of
                     chicago/pre_fire_v1/maps/images/1830_thompson_plat.png. A
                     region is a citation and a citation must survive its source,
                     so the sheet's sha256 is committed beside the reading. Swap
                     the scan and all 22 blocks' citations point at coordinates
                     nobody checked — this goes red instead.
  the regions        Inside the sheet, positive extent. A region that runs off
                     the paper is a region nobody can re-open.
  the numerals       A block's lot numerals must be a permutation of 1..n with no
                     repeats and no gaps. That is not decoration: the West
                     Division run is a boustrophedon written 2|1, 3|4, 6|5, 7|8,
                     10|9 down the block, and a misread numeral almost always
                     lands as a duplicate or a hole.
  THE CLOSURE        The one assertion that makes this a reading and not a
                     transcription. The block's east-west width comes from three
                     PRINTED figures — 180 at a block face, the legend's 18 ft
                     alley, 180 again — and sums to 378. Its north-south height
                     comes from a DIFFERENT printed figure in a DIFFERENT margin,
                     75 3/5, times the numerals counted in the block, and sums to
                     378 as well. The two share no input. They meet to the foot,
                     the five-row West Division block is square, and the 458 ft
                     module docs/RESEARCH/west_division_module.md derived from two
                     inferences on 2026-09-03 comes back unchanged from figures.
  not eighty         The South Division's lot fronts 80 ft and that is the number
                     an inference carries west. The sheet prints 75 3/5. This
                     check refuses any West Division frontage of 80 outright, so
                     the inference cannot creep back in as a tidy-up.
  the refusals       Every block that does not carry a dimension must SAY why, and
                     every block that does must cite where it was read and grade
                     itself `documented`. T-0689 acceptance point 2: a gap stated
                     is worth more than a number carried across.

WHAT IT DOES NOT CHECK, because the trace does not claim it: any position. A lot
dimension is a length. Where the West Division grid sits is T-0445's.

  tools/read_west_division_lots.py            print the reading
  tools/read_west_division_lots.py --check    the gate
  tools/read_west_division_lots.py --self-test
"""
import argparse
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
TRACE = ROOT / "data" / "traces" / "thompson_west_division_lots.json"
SHEET = ROOT.parent / "pre_fire_v1" / "maps" / "images" / "1830_thompson_plat.png"

FT_PER_M = 0.3048
# The figure docs/RESEARCH/west_division_module.md derived on 2026-09-03, before the
# sheet was read. The reading has to come back to it or one of the two is wrong.
MODULE_M_IN_THE_MEMO = 139.598


def load():
    return json.loads(TRACE.read_text())


def regions(doc):
    """Every 'x,y,w,h' string anywhere in the document, with the key it sat under."""
    out = []

    def walk(node, path):
        if isinstance(node, dict):
            for k, v in node.items():
                walk(v, f"{path}.{k}" if path else k)
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{path}[{i}]")
        elif isinstance(node, str) and path.endswith(("region", "_region")):
            out.append((path, node))
    walk(doc, "")
    return out


def check(doc):
    problems = []
    sheet = doc["sheet"]
    w_px, h_px = sheet["pixels"]

    if SHEET.exists():
        digest = hashlib.sha256(SHEET.read_bytes()).hexdigest()
        if digest != sheet["sha256"]:
            problems.append(
                f"the sheet has changed under the reading: {SHEET.name} hashes {digest[:16]}… "
                f"where the trace was read on {sheet['sha256'][:16]}…. Every pixel region "
                f"below cites coordinates on the old scan and none of them has been re-checked")
    else:
        problems.append(f"the sheet the reading cites is not in the tree: {SHEET}")

    for path, region in regions(doc):
        try:
            x, y, w, h = (int(p) for p in region.split(","))
        except ValueError:
            problems.append(f"{path}: '{region}' is not an x,y,w,h region")
            continue
        if w <= 0 or h <= 0:
            problems.append(f"{path}: region {region} has no extent")
        if x < 0 or y < 0 or x + w > w_px or y + h > h_px:
            problems.append(
                f"{path}: region {region} runs off a {w_px}x{h_px} sheet, so nobody can re-open it")

    blocks = doc["blocks"]
    by_number = {}
    for b in blocks:
        n = b["plat_block_number"]
        if n in by_number:
            problems.append(f"block {n} is in the trace twice")
        by_number[n] = b

        numerals = [v for row in b["lot_numerals_north_to_south"] for v in row]
        if len(numerals) != b["lot_count"]:
            problems.append(
                f"block {n}: {len(numerals)} numerals read but lot_count says {b['lot_count']}")
        if len(set(numerals)) != len(numerals):
            problems.append(f"block {n}: a lot numeral is read twice — {sorted(numerals)}")
        if b.get("irregular"):
            if not set(numerals) <= set(range(1, 11)):
                problems.append(f"block {n} is irregular but its numerals leave 1..10")
        elif sorted(numerals) != list(range(1, len(numerals) + 1)):
            problems.append(
                f"block {n}: the numerals are not a run 1..{len(numerals)} — {sorted(numerals)}")

        dims = [b.get("lot_depth_ft"), b.get("lot_frontage_ft")]
        carries = [d for d in dims if d is not None] or b.get("depth_figures_read") \
            or b.get("frontage_figures_read") or b.get("figures_read")
        if carries:
            if b.get("confidence") != "documented":
                problems.append(
                    f"block {n} carries a figure off a tier-1 sheet but is not graded documented")
            if not any(k.endswith("region") for k in b):
                problems.append(f"block {n} carries a figure and cites no region for it")
        if any(d is None for d in dims) and not b.get("refused"):
            problems.append(
                f"block {n} is missing a dimension and does not say what was illegible")
        if b.get("lot_frontage_ft") == 80:
            problems.append(
                f"block {n} reads a West Division frontage of 80 ft — that is the South "
                f"Division's figure, and carrying it west is exactly what T-0689 forbids")

    blk = doc["the_west_division_block"]
    depth, alley, frontage = blk["lot_depth_ft"], blk["alley_width_ft"], blk["lot_frontage_ft"]
    east_west = 2 * depth + alley
    if east_west != blk["block_east_west_ft"]:
        problems.append(
            f"the block's east-west width does not rebuild from its printed parts: "
            f"2 x {depth} + {alley} = {east_west}, trace says {blk['block_east_west_ft']}")

    five_row = [b for b in blocks if len(b["lot_numerals_north_to_south"]) == 5
                and not b.get("irregular")]
    if not five_row:
        problems.append("no five-row block in the trace to close the frontage against")
    rows = 5
    north_south = round(rows * frontage, 6)
    if north_south != float(blk["block_north_south_ft_five_row_tiers"]):
        problems.append(
            f"{rows} x {frontage} = {north_south}, not the "
            f"{blk['block_north_south_ft_five_row_tiers']} the trace records")
    if north_south != float(east_west):
        problems.append(
            f"THE CLOSURE IS BROKEN: the face figures give {east_west} ft east-west and the "
            f"margin figure gives {north_south} ft north-south. The five-row West Division "
            f"block is square or this reading is wrong")

    module = east_west + doc["legend"]["street_width_ft"]
    if module != blk["north_south_street_module_ft"]:
        problems.append(
            f"the street module does not rebuild: {east_west} + "
            f"{doc['legend']['street_width_ft']} = {module}, trace says "
            f"{blk['north_south_street_module_ft']}")
    module_m = round(module * FT_PER_M, 3)
    if abs(module_m - MODULE_M_IN_THE_MEMO) > 0.001:
        problems.append(
            f"the read module is {module_m} m where west_division_module.md derived "
            f"{MODULE_M_IN_THE_MEMO} m from two inferences — one of them is wrong, and the "
            f"memo must be re-read against the sheet before either stands")

    for tier in doc["tiers"]:
        want = tier["blocks"]
        got = [b["plat_block_number"] for b in blocks if b["tier"] == tier["tier"]]
        if got != want:
            problems.append(f"tier {tier['tier']}: lists {want}, blocks say {got}")
        for n in want:
            b = by_number.get(n)
            if b is None:
                problems.append(f"tier {tier['tier']} names block {n}, which is not in the trace")
                continue
            if b.get("irregular"):
                continue
            if len(b["lot_numerals_north_to_south"]) != tier["rows"]:
                problems.append(
                    f"block {n} reads {len(b['lot_numerals_north_to_south'])} rows where its "
                    f"tier reads {tier['rows']}")

    counts = doc["counts"]
    actual = {
        "blocks_read": len(blocks),
        "lots_read": sum(b["lot_count"] for b in blocks),
        "blocks_with_a_depth_figure": sum(1 for b in blocks if b.get("depth_figures_read")),
        "blocks_with_a_frontage_figure": sum(1 for b in blocks if b.get("frontage_figures_read")),
        "blocks_refusing_a_dimension": sum(1 for b in blocks if b.get("refused")),
    }
    for k, v in actual.items():
        if counts.get(k) != v:
            problems.append(f"counts.{k} says {counts.get(k)}, the blocks say {v}")

    return problems


def report(doc):
    blk = doc["the_west_division_block"]
    print(f"the sheet: {doc['sheet']['asset']}  {doc['sheet']['pixels'][0]}x"
          f"{doc['sheet']['pixels'][1]} px, read {doc['sheet']['read_on']}")
    print(f"the legend: streets {doc['legend']['street_width_ft']} ft, alleys "
          f"{doc['legend']['alley_width_ft']} ft, scale "
          f"{doc['legend']['scale_ft_per_inch']} ft to an inch")
    print(f"the block:  {blk['lot_depth_ft']} ft deep x {blk['lot_frontage_as_printed']} ft "
          f"of frontage, two columns of five across an {blk['alley_width_ft']} ft alley")
    print(f"  east-west   2 x {blk['lot_depth_ft']} + {blk['alley_width_ft']} = "
          f"{blk['block_east_west_ft']} ft")
    print(f"  north-south 5 x {blk['lot_frontage_ft']}          = "
          f"{5 * blk['lot_frontage_ft']:.0f} ft")
    print(f"  module      {blk['block_east_west_ft']} + {doc['legend']['street_width_ft']} = "
          f"{blk['north_south_street_module_ft']} ft = "
          f"{blk['north_south_street_module_ft'] * FT_PER_M:.3f} m")
    for tier in doc["tiers"]:
        blocks = " ".join(str(n) for n in tier["blocks"])
        print(f"  {tier['tier']:30s} {tier['rows']} rows   blocks {blocks}")
    c = doc["counts"]
    print(f"  {c['blocks_read']} blocks, {c['lots_read']} lots; "
          f"{c['blocks_with_a_depth_figure']} carry a depth figure, "
          f"{c['blocks_with_a_frontage_figure']} a frontage figure, "
          f"{c['blocks_refusing_a_dimension']} refuse one")


def self_test():
    failures = []

    def must_fire(mutate, what):
        doc = load()
        mutate(doc)
        if not check(doc):
            failures.append(what)

    def set_sha(d):
        d["sheet"]["sha256"] = "0" * 64

    def off_paper(d):
        d["blocks"][0]["region"] = "2700,1900,400,400"

    def dup_numeral(d):
        d["blocks"][1]["lot_numerals_north_to_south"][0][0] = \
            d["blocks"][1]["lot_numerals_north_to_south"][1][0]

    def eighty(d):
        for b in d["blocks"]:
            if b.get("lot_frontage_ft"):
                b["lot_frontage_ft"] = 80
                break

    def break_closure(d):
        d["the_west_division_block"]["lot_frontage_ft"] = 80.0
        d["the_west_division_block"]["block_north_south_ft_five_row_tiers"] = 400

    def silent_gap(d):
        for b in d["blocks"]:
            if b.get("refused"):
                del b["refused"]
                break

    def ungraded(d):
        for b in d["blocks"]:
            if b.get("depth_figures_read"):
                b["confidence"] = "inferred"
                break

    def wrong_rows(d):
        d["tiers"][2]["rows"] = 5

    must_fire(set_sha, "a sheet whose hash no longer matches the reading did not break the gate")
    must_fire(off_paper, "a region running off the paper did not break the gate")
    must_fire(dup_numeral, "a lot numeral read twice in one block did not break the gate")
    must_fire(eighty, "a West Division frontage of 80 ft — the South Division's figure carried "
                      "west, which is the thing T-0689 exists to refuse — did not break the gate")
    must_fire(break_closure, "an 80 ft frontage in the summary, which stops the margin figure "
                             "closing against the face figures, did not break the gate")
    must_fire(silent_gap, "a block missing a dimension without saying what was illegible did "
                          "not break the gate")
    must_fire(ungraded, "a figure read off a tier-1 sheet and graded below documented did not "
                        "break the gate")
    must_fire(wrong_rows, "a tier whose row count disagrees with its blocks' numerals did not "
                          "break the gate")

    for f in failures:
        print(f"SELF-TEST FAILED: {f}")
    if failures:
        return 1
    print("self-test: a changed scan, a region off the paper, a duplicated numeral, an 80 ft "
          "West Division frontage, a broken east-west/north-south closure, a silent refusal, "
          "an under-graded figure and a tier at odds with its blocks all break the gate, as "
          "they must")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    doc = load()
    problems = check(doc)
    if args.check:
        for p in problems:
            print(f"  {p}")
        if problems:
            print(f"{len(problems)} problem(s) in the West Division lot reading")
            return 1
        print("the West Division's 22 blocks, 203 lots and every printed figure still answer "
              "for the sheet they were read on; 378 ft closes both ways and the module is 458 ft")
        return 0

    report(doc)
    if problems:
        print("DRIFTED:")
        for p in problems:
            print(f"  {p}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
