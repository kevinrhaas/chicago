#!/usr/bin/env python3
"""Hold the e1830_natural terrain spec: an overlay on 1834 that accounts for every block (T-2002).

    python3 tools/check_terrain_e1830.py --check      # check (also the default)
    python3 tools/check_terrain_e1830.py --resolve    # print the effective 1812 zone table
    python3 tools/check_terrain_e1830.py --self-test

`data/terrain/epochs/e1830_natural/terrain_spec.json` is not a copy of the 1834 zone table.
Almost all of the natural ground is the same ground, so the 1812 spec names every top-level
block of `e1834_harbor_cut/terrain_spec.json` in `inherits.blocks` and says what 1812 does
with it -- carry, carry_except, replace, drop or own -- and authors only what differs: the
lake stage, the spit, the isthmus L240 left as a hole, the live outlet channel, the shore
north of the spit root, and the ruling on the old channel's west bank T-1286 asked for.

What this refuses:

* a block of the 1834 spec that the overlay does not account for, or accounts for twice
  -- a key added to 1834 later must be decided for 1812 before either gate is green;
* a `replace`, `carry_except` or `rename_runs` that names something that is not there;
* an authored elevation that cites no dossier zone, or a zone the dossier table lacks,
  or a value outside the range that zone gives;
* an authored elevation better than `reconstructed`, a reconstructed block with no note,
  or a source id that does not resolve;
* an isthmus left undecided, or surfaced at a height that is not the spit's (a lower neck
  is a breach, which is the 1834 storm's landform);
* the west-bank ruling left `undecided` without grading the band conjectural, or with a
  band that does not run from Harrison's old mouth to the adopted outlet station;
* an authored block that shadows an 1834 block the overlay carries (resolve() would
  quietly keep the 1834 one), or a graded authored block that does not reach the Evidence
  panel -- since T-2003 every one is a `compile_scene.GROUND_GROUPS` group with an entry in
  `terrain_inputs.CONSUMED`, the generator's own statement of what it reads;
* a west-bank band whose width is not T-1286's measured worst separation for that bank
  (`data/terrain/1812_harrison_cross_check.json`);
* an effective table (`resolve()`) that still carries a harbour work.

`resolve()` is the function `generators/terrain_gen_e1830.py` (T-2003) imports. Standard
library only; `generators/terrain_inputs.py` is read for CONSUMED, and it is too.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EPOCHS = ROOT / "data" / "terrain" / "epochs"
SPEC_PATH = EPOCHS / "e1830_natural" / "terrain_spec.json"
SHORE_PATH = EPOCHS / "e1830_natural" / "shoreline.geojson"
EPOCHS_JSON = ROOT / "data" / "terrain" / "epochs.json"
DOSSIER = ROOT / "docs" / "research" / "01-terrain-hydrology.md"
COMPILE_SCENE = ROOT / "tools" / "compile_scene.py"
CROSS_CHECK = ROOT / "data" / "terrain" / "1812_harrison_cross_check.json"
SOURCES = ROOT / "data" / "sources"

TAKES = ("carry", "carry_except", "replace", "drop", "own")
AUTHORED = ("lake_stage_1812", "water_bodies_1812", "shore_runs_1812", "north_lake_shore_1812",
            "spit_1812", "isthmus_1812", "outlet_channel_1812", "channel_west_bank_ruling",
            "not_modelled_1812")
# The harbour works and the 1835 town, by the block or item that models them. None may
# survive into the effective 1812 table.
WORKS = {"approaches", "approaches_note", "street_sections", "islands", "water"}
WORK_ITEMS = {("reaches", "harbour_cut_1834"), ("reaches", "old_south_channel"),
              ("surface_materials", "sand_bar_1834")}
HARRISON_OLD_MOUTH_N = -69.0      # T-1286: 'Old Mouth of River very shallow', local N
ELEVATION_KEY = re.compile(r"_ft$")


def load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def dossier_zones() -> dict[int, str]:
    """zone number -> its row, from the TERRAIN MODEL RECOMMENDATIONS table."""
    out = {}
    for line in DOSSIER.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\|\s*(\d+)\s*\|(.*)$", line)
        if m:
            out[int(m.group(1))] = m.group(2)
    return out


def ground_groups() -> set[str]:
    """The block names compile_scene puts on the Evidence panel, read from its source."""
    src = COMPILE_SCENE.read_text(encoding="utf-8")
    m = re.search(r"^GROUND_GROUPS = \[(.*?)^\]", src, re.S | re.M)
    return set(re.findall(r'^\s*\("([a-z0-9_]+)",', m.group(1), re.M)) if m else set()


def consumed_groups() -> set[str]:
    """The groups `generators/terrain_inputs.CONSUMED` declares reads for."""
    sys.path.insert(0, str(ROOT / "generators"))
    import terrain_inputs  # noqa: PLC0415
    return set(terrain_inputs.CONSUMED)


def item_id(x: dict):
    return x.get("id") or x.get("zone") or x.get("feature")


def resolve(spec: dict, base: dict) -> dict:
    """The effective 1812 zone table: the 1834 blocks the overlay carries, less what it
    excepts, plus every block this spec authors. Raises KeyError on a dangling name."""
    out: dict = {}
    for key, rule in spec["inherits"]["blocks"].items():
        take = rule["take"]
        if take == "carry":
            out[key] = copy.deepcopy(base[key])
        elif take == "carry_except":
            block = copy.deepcopy(base[key])
            gone = set(rule.get("drop", [])) | set(rule.get("replace", {}))
            if isinstance(block, list):
                ids = {item_id(x) for x in block}
                missing = gone - ids
                if missing:
                    raise KeyError(f"{key}: no item {sorted(missing)} in the 1834 block")
                block = [x for x in block if item_id(x) not in gone]
                for iid, keys in rule.get("drop_keys", {}).items():
                    hit = [x for x in block if item_id(x) == iid]
                    if not hit:
                        raise KeyError(f"{key}: no item '{iid}' to drop keys from")
                    for k in keys:
                        if k not in hit[0]:
                            raise KeyError(f"{key}.{iid}: no key '{k}' to drop")
                        del hit[0][k]
            out[key] = block
        elif take in ("replace", "own"):
            continue
        elif take == "drop":
            continue
    for key in spec:
        if key not in ("inherits",) and key not in out:
            out[key] = copy.deepcopy(spec[key])
    return out


def authored_blocks(spec: dict):
    for key in AUTHORED:
        if isinstance(spec.get(key), dict):
            yield key, spec[key]


def elevations(block: dict):
    """(key, value) for every numeric elevation an authored block states at its top level."""
    for k, v in block.items():
        if ELEVATION_KEY.search(k) and k != "range_ft" and isinstance(v, (int, float)):
            yield k, float(v)


def validate(spec: dict, base: dict, shore: dict, epochs: dict,
             groups: set[str] | None = None, consumed: set[str] | None = None) -> list[str]:
    bad: list[str] = []
    zones = dossier_zones()
    sources = {p.stem for p in SOURCES.glob("*.json")}
    feats = {f.get("id") for f in shore.get("features", [])}
    inh = spec.get("inherits") or {}
    blocks = inh.get("blocks") or {}

    if spec.get("epoch") != "e1830_natural":
        bad.append(f"epoch is {spec.get('epoch')!r}, not e1830_natural")
    if inh.get("from") != base.get("epoch"):
        bad.append(f"inherits.from {inh.get('from')!r} is not the base spec's epoch {base.get('epoch')!r}")

    # 1. Every 1834 block accounted for, once, with a reason.
    for key in base:
        if key not in blocks:
            bad.append(f"the 1834 block '{key}' is not accounted for in inherits.blocks -- decide what it "
                       f"means for 1812 (carry, carry_except, replace, drop or own) and say why")
    for key, rule in blocks.items():
        if key not in base:
            bad.append(f"inherits.blocks names '{key}', which the 1834 spec does not have")
        if rule.get("take") not in TAKES:
            bad.append(f"inherits.blocks.{key}: take {rule.get('take')!r} is not one of {TAKES}")
        if not str(rule.get("why", "")).strip():
            bad.append(f"inherits.blocks.{key}: no `why` -- a disposition with no reason is a default")
        if rule.get("take") == "replace" and rule.get("by") not in spec:
            bad.append(f"inherits.blocks.{key}: replaced by '{rule.get('by')}', which this spec does not author")
        if rule.get("take") == "own" and key not in spec:
            bad.append(f"inherits.blocks.{key}: marked own, and this spec does not write it")
        for iid, by in (rule.get("replace") or {}).items():
            if by not in spec:
                bad.append(f"inherits.blocks.{key}: item '{iid}' replaced by '{by}', which this spec does not author")

    # 2. Runs renamed onto runs that exist.
    base_runs = {r.get("id") for r in base.get("shore_runs", [])}
    authored_runs = set(AUTHORED)
    for old, new in (inh.get("rename_runs") or {}).items():
        if old.startswith("_"):
            continue
        if old not in base_runs:
            bad.append(f"rename_runs: '{old}' is not a shore run of the 1834 spec")
        for r in new:
            if r not in feats and r not in authored_runs:
                bad.append(f"rename_runs: '{r}' is neither a feature of e1830_natural/shoreline.geojson "
                           f"nor a block this spec authors")
    runs = spec.get("shore_runs_1812") or {}
    for r in runs.get("carried", []):
        if r not in base_runs:
            bad.append(f"shore_runs_1812 carries '{r}', which is not an 1834 shore run")
    for r in runs.get("from_shoreline_1812", []):
        if r not in feats:
            bad.append(f"shore_runs_1812 reads '{r}' from the 1812 shoreline, which does not have it")
    for r in runs.get("authored", []):
        if r not in spec:
            bad.append(f"shore_runs_1812 names '{r}' as authored, and this spec does not author it")

    # 3. The authored blocks: zones, grades, reasons, sources.
    groups = ground_groups() if groups is None else groups
    consumed = consumed_groups() if consumed is None else consumed
    if not groups:
        bad.append("cannot read GROUND_GROUPS from tools/compile_scene.py")
    for key in sorted(set(spec) & set(base)):
        if blocks.get(key, {}).get("take") not in ("own", "replace", "drop"):
            bad.append(f"'{key}' is authored here and is also the 1834 block the overlay takes as "
                       f"{blocks.get(key, {}).get('take')!r}; resolve() keeps the 1834 one, so the 1812 "
                       f"one would be silently ignored")
    for key, block in authored_blocks(spec):
        if "confidence" not in block:
            continue
        if key not in groups:
            bad.append(f"'{key}' grades itself and is not a compile_scene.GROUND_GROUPS group, so the "
                       f"Evidence panel never shows it (T-2003 wired every one)")
        elif key not in consumed:
            bad.append(f"'{key}' reaches the Evidence panel with no terrain_inputs.CONSUMED entry, so "
                       f"nothing says which of its figures the 1812 ground is built from")
    for key, block in authored_blocks(spec):
        conf = block.get("confidence")
        if conf in ("attested", "documented"):
            bad.append(f"{key}: graded {conf} -- nothing in an 1812 spec is better than inferred")
        if conf == "reconstructed" and not str(block.get("note", "")).strip():
            bad.append(f"{key}: reconstructed with no note -- a reconstruction says what bounds it")
        for s in block.get("sources", []) or []:
            if s not in sources:
                bad.append(f"{key}: source '{s}' does not resolve in data/sources/")
        elev = list(elevations(block))
        if elev:
            z = block.get("dossier_zone")
            if z not in zones:
                bad.append(f"{key}: states {', '.join(k for k, _ in elev)} and cites dossier zone {z!r}, "
                           f"which the terrain dossier's table does not have")
            if conf != "reconstructed":
                bad.append(f"{key}: authors an 1812 elevation graded {conf!r}; no 1812 height is read, so "
                           f"every one is reconstructed")
            rng = block.get("range_ft")
            for k, v in elev:
                if k in ("crest_ft", "bed_ft", "surface_ft") and rng and not (min(rng) <= v <= max(rng)):
                    bad.append(f"{key}: {k} {v} is outside its own zone range {rng}")

    # 4. The decisions the ticket asked for.
    spit, isth = spec.get("spit_1812") or {}, spec.get("isthmus_1812") or {}
    if spit.get("feature") not in feats:
        bad.append(f"spit_1812 surfaces '{spit.get('feature')}', which the 1812 shoreline does not have")
    if spit and not (4.0 <= spit.get("crest_ft", -99) <= 8.0):
        bad.append(f"spit_1812 crest {spit.get('crest_ft')} ft is outside zone 7's +4 to +8")
    if isth.get("decision") not in ("surfaced", "absent"):
        bad.append("isthmus_1812 is undecided -- L240 asks for a surface and a height, or 'absent' with a reason")
    elif isth.get("feature") != "spit_attachment_gap_1812" or "spit_attachment_gap_1812" not in feats:
        bad.append("isthmus_1812 must decide L240's own feature, spit_attachment_gap_1812")
    if isth.get("decision") == "surfaced":
        if isth.get("crest_ft") != spit.get("crest_ft"):
            bad.append(f"isthmus_1812 crest {isth.get('crest_ft')} is not the spit's {spit.get('crest_ft')}: a "
                       f"lower neck is a breach (1834's landform) and a higher one is the zone 3 ridge")
        if not (100.0 <= isth.get("width_ft", -1) <= 300.0):
            bad.append(f"isthmus_1812 width {isth.get('width_ft')} ft is outside zone 7's 100-300 ft")
    out = spec.get("outlet_channel_1812") or {}
    if out and not (-4.0 <= out.get("bed_ft", 99) <= -1.0):
        bad.append(f"outlet_channel_1812 bed {out.get('bed_ft')} ft is outside zone 26's -1 to -4")
    stage = spec.get("lake_stage_1812") or {}
    if stage.get("confidence") in ("attested", "documented", "inferred"):
        bad.append("lake_stage_1812 is graded as if a stage of 1812 were recorded; none is (zone 2)")

    rule = spec.get("channel_west_bank_ruling") or {}
    verdict = rule.get("verdict")
    if verdict not in ("a", "b", "c", "undecided"):
        bad.append(f"channel_west_bank_ruling verdict {verdict!r} is not a, b, c or undecided")
    if rule.get("bank_run") not in feats:
        bad.append("channel_west_bank_ruling must name the 1812 bank it rules on")
    if set((rule.get("readings") or {})) != {"a", "b", "c"}:
        bad.append("channel_west_bank_ruling must weigh all three readings T-1286 named")
    worst = (((load(CROSS_CHECK).get("by_nearest_derived_feature") or {})
              .get(rule.get("bank_run")) or {}).get("max_m"))
    if worst is None or abs(float(rule.get("west_band_m", -1)) - float(worst)) > 0.05:
        bad.append(f"channel_west_bank_ruling west_band_m {rule.get('west_band_m')} is not T-1286's "
                   f"worst separation for {rule.get('bank_run')} ({worst} m, "
                   f"1812_harrison_cross_check.json)")
    if verdict == "undecided":
        if rule.get("ground_confidence") != "conjectural":
            bad.append("an undecided west bank leaves its ground at the grade T-1286 asked for: conjectural")
        bank = next((f for f in shore.get("features", []) if f.get("id") == rule.get("bank_run")), None)
        outlet_n = None
        if bank:
            st = bank["properties"].get("outlet_station_local")
            st = json.loads(st) if isinstance(st, str) else st
            outlet_n = float(st[1]) if st else None
        band = sorted(rule.get("band_n_m") or [])
        if outlet_n is None or len(band) != 2 or abs(band[0] - outlet_n) > 0.01 \
                or abs(band[1] - HARRISON_OLD_MOUTH_N) > 0.01:
            bad.append(f"channel_west_bank_ruling band {band} must run from the adopted outlet "
                       f"(N {outlet_n}) to Harrison's old mouth (N {HARRISON_OLD_MOUTH_N})")

    # 5. The effective table is the 1812 ground and nothing built.
    try:
        eff = resolve(spec, base)
    except KeyError as e:
        bad.append(f"resolve() fails: {e}")
        eff = {}
    for key in WORKS & set(eff):
        bad.append(f"the effective 1812 table still carries '{key}', a work or a state of after 1830")
    for key, iid in WORK_ITEMS:
        if any(item_id(x) == iid for x in eff.get(key, []) if isinstance(x, dict)):
            bad.append(f"the effective 1812 table still carries {key}.{iid}")
    for x in eff.get("dunes", []):
        if x.get("keep_clear"):
            bad.append(f"dunes.{item_id(x)} keeps clear of a building that stood in 1835, not 1812")

    # 6. The epoch register points at this file.
    ep = next((e for e in epochs.get("epochs", []) if e.get("id") == "e1830_natural"), {})
    if (ep.get("layers") or {}).get("terrain_spec") != "e1830_natural/terrain_spec.json":
        bad.append("data/terrain/epochs.json does not register e1830_natural's terrain_spec layer")
    return bad


def self_test(spec, base, shore, epochs) -> int:
    cases = []

    def breaks(label, mutate, on="spec"):
        s, b = copy.deepcopy(spec), copy.deepcopy(base)
        mutate(s if on == "spec" else b)
        cases.append((label, bool(validate(s, b, shore, epochs))))

    cases.append(("the committed spec passes", not validate(spec, base, shore, epochs)))
    breaks("a block added to the 1834 spec and not decided for 1812 fails",
           lambda b: b.__setitem__("ferry_landings", []), on="base")
    breaks("a disposition with no reason fails",
           lambda s: s["inherits"]["blocks"]["grid"].__setitem__("why", ""))
    breaks("carrying the bridge approaches into 1812 fails",
           lambda s: s["inherits"]["blocks"]["approaches"].__setitem__("take", "carry"))
    breaks("carrying the 1834 cut's reach into 1812 fails",
           lambda s: s["inherits"]["blocks"]["reaches"].__setitem__("drop", []))
    breaks("replacing with a block nobody wrote fails",
           lambda s: s["inherits"]["blocks"]["water"].__setitem__("by", "lake_1812"))
    breaks("an authored height citing a zone the dossier lacks fails",
           lambda s: s["spit_1812"].__setitem__("dossier_zone", 99))
    breaks("an authored height graded inferred fails",
           lambda s: s["outlet_channel_1812"].__setitem__("confidence", "inferred"))
    breaks("a source that does not resolve fails",
           lambda s: s["isthmus_1812"]["sources"].append("no_such_source"))
    breaks("an undecided isthmus fails",
           lambda s: s["isthmus_1812"].__setitem__("decision", "later"))
    breaks("an isthmus lower than the spit (a breach) fails",
           lambda s: s["isthmus_1812"].__setitem__("crest_ft", 2.0))
    breaks("an isthmus wider than zone 7 allows fails",
           lambda s: s["isthmus_1812"].__setitem__("width_ft", 400.0))
    breaks("an outlet as deep as the main stem fails",
           lambda s: s["outlet_channel_1812"].__setitem__("bed_ft", -12.0))
    breaks("an undecided west bank left at inferred fails",
           lambda s: s["channel_west_bank_ruling"].__setitem__("ground_confidence", "inferred"))
    breaks("a west-bank band that stops short of the outlet fails",
           lambda s: s["channel_west_bank_ruling"].__setitem__("band_n_m", [-300.0, -69.0]))
    breaks("a ruling that weighs only two readings fails",
           lambda s: s["channel_west_bank_ruling"]["readings"].pop("c"))
    breaks("a run renamed onto nothing fails",
           lambda s: s["inherits"]["rename_runs"]["south_shore_harbor_reach"].append("ghost_run"))
    breaks("an 1812 block that shadows a carried 1834 block fails",
           lambda s: s.__setitem__("reaches", s["outlet_channel_1812"]))
    groups = ground_groups()
    cases.append(("a graded 1812 block the Evidence panel does not list fails",
                  bool(validate(spec, base, shore, epochs, groups=groups - {"spit_1812"}))))
    cases.append(("a graded 1812 block with no CONSUMED entry fails",
                  bool(validate(spec, base, shore, epochs, consumed=consumed_groups() - {"isthmus_1812"}))))
    breaks("a west band narrower than Harrison's worst separation fails",
           lambda s: s["channel_west_bank_ruling"].__setitem__("west_band_m", 100.0))
    breaks("keeping the 1835 boarding house's keep-clear fails",
           lambda s: s["inherits"]["blocks"]["dunes"].__setitem__("drop_keys", {}))
    for label, ok in cases:
        print(("   ok   " if ok else "   FAIL ") + label)
    return 0 if all(ok for _, ok in cases) else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="validate (the default; named so the gate says what it asks)")
    ap.add_argument("--resolve", action="store_true", help="print the effective 1812 zone table")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    spec, base = load(SPEC_PATH), load(EPOCHS / "e1834_harbor_cut" / "terrain_spec.json")
    shore, epochs = load(SHORE_PATH), load(EPOCHS_JSON)
    if a.self_test:
        return self_test(spec, base, shore, epochs)
    if a.resolve:
        json.dump(resolve(spec, base), sys.stdout, indent=1, ensure_ascii=False)
        print()
        return 0
    bad = validate(spec, base, shore, epochs)
    for b in bad:
        print("FAIL", b)
    if not bad:
        takes = {}
        for rule in spec["inherits"]["blocks"].values():
            takes[rule["take"]] = takes.get(rule["take"], 0) + 1
        eff = resolve(spec, base)
        print(f"OK e1830_natural accounts for all {len(base)} blocks of the 1834 spec "
              f"({', '.join(f'{v} {k}' for k, v in sorted(takes.items()))}); the effective 1812 table has "
              f"{len(eff)} blocks and no harbour work; spit and isthmus at +{spec['spit_1812']['crest_ft']} ft "
              f"(zone 7), outlet bed {spec['outlet_channel_1812']['bed_ft']} ft (zone 26), west bank "
              f"{spec['channel_west_bank_ruling']['verdict']} and graded "
              f"{spec['channel_west_bank_ruling']['ground_confidence']} from N "
              f"{spec['channel_west_bank_ruling']['band_n_m'][0]} to {spec['channel_west_bank_ruling']['band_n_m'][1]}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
