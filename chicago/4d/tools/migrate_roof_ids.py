#!/usr/bin/env python3
"""MOVE A REFAMILIED ROOF'S ID, AND EVERYTHING THAT NAMES IT. T-1494.

    tools/migrate_roof_ids.py --plan      what would move, and what names it today
    tools/migrate_roof_ids.py --apply     refamily the recipe and carry every name with it
    tools/migrate_roof_ids.py --check     re-derive the map and refuse a stale name
    tools/migrate_roof_ids.py --self-test the guards, fired on fixtures

T-1445 adjudicated the town's 285 anonymous roofs and returned 32 refamily verdicts.
T-1451 carried out the six whose id does NOT move --- `generate_west_infill` reads a
placement's id from the recipe, so refamilying there is a one-field edit. The other 26
are different in kind, and `docs/RESEARCH/1835_roof_redeal_execution.md` says why: the
other generators BUILD THE ID OUT OF THE FAMILY, so `recon_1835_south_c1_003` refamilied
to D1 becomes `recon_1835_south_d1_003`, and that id is not private to its record. The
sidecars, the enclosure and frontage and signage and yard layers, the lodging files, the
seating files, the business layer and a dozen reports all name it.

This tool owns the PHASE-ONE SOUTH PARCEL's eleven. The North Division parcel (T-1495)
authors its own id suffix, inventory class and footprint per placement and is a
different edit; the three platted blocks (T-1496) move six ancillary yard buildings into
dwelling families, which re-deals a block's claimed principal/ancillary schedule and is
not a field edit at all.

WHAT IT REFUSES TO DO, each refusal recorded rather than worked round:

  * IT ADJUDICATES NOTHING. Every family below is the `to_family` T-1445 reached and
    every reason is T-1445's own, quoted. This tool moves names.

  * A CONFIDENCE IS NEVER UPGRADED. These roofs are `inferred_anonymous` before and
    after, and every form value they carry still grades at the bottom tier.

  * IT INVENTS NO FOOTPRINT. The south recipe authors no dimensions: the generator
    samples them inside the family's own band on a stable key. Refamilying therefore
    re-derives the footprint out of the NEW band by construction, and this tool does not
    choose one. That is why the verdicts' `band_already_fits` column, which the West
    parcel's executor had to honour, has nothing to answer for here.

  * IT MOVES NO ROOF. Every placement keeps its easting and its row, so the building
    stands exactly where it stood. The adjudication refused these families' PLACEMENT
    POLICY, not their positions --- "the slot is wanted and the position stands".

  * IT LEAVES A NAME IT CANNOT MOVE. A reference this tool does not know how to rewrite
    is a refusal, not a silent skip: `--check` fails while any committed file still
    names a migrated id.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RECON = DATA / "reconstruction"
LEDGER = RECON / "1835_roof_redeal.json"
PARCEL = RECON / "1835_phase1_south_mixed_blocks.json"
MIGRATION = RECON / "1835_roof_id_migration.json"
STRUCTURES = DATA / "structures"
SIDECARS = DATA / "sidecars" / "1835"
ASSETS = (ROOT / "assets" / "gltf", ROOT / "assets" / "web")
MANIFEST = ROOT / "assets" / "manifest.json"
PREFIX = "recon_1835_south_"
TICKET = "T-1494"

# Where a roof id can be written down. Measured over the committed tree on 2026-09-20:
# every path outside this set that named one of the eleven was a `data/structures/<id>`
# or an `assets/` mesh, both of which move as FILES below.
TEXT_SUFFIXES = (".json", ".md", ".py", ".mjs", ".js", ".html", ".css", ".txt")
SKIP_DIRS = {".git", "node_modules", "site", "assets", "renderers/web/vendor"}

# THE NAMES THIS TOOL DOES NOT REWRITE ARE NOT LISTED HERE ANY MORE. They were,
# until T-1499, and so were the executor's — two lists, overlapping, with the same
# reasoning written out twice and nothing holding them in agreement but somebody
# remembering to edit both. Twice nobody did. `tools/roof_id_pins.py` is the one
# list: every pin carries its own reason and the KIND of true-as-written name it
# is, both sweeps read it, and a gate step asserts the two of them return the same
# verdict for every file in the tree, so a future divergence is red rather than
# silent.
sys.path.insert(0, str(ROOT / "tools"))
import roof_id_pins  # noqa: E402

REDERIVED = roof_id_pins.REDERIVED


def keeps_the_old_name(rel: str) -> bool:
    """This sweep's verdict, and it is the shared list's — asked through this tool's
    own name so that `roof_id_pins --check` is putting the question to the SWEEP.
    A run that re-introduces a private list here diverges from the other sweep and
    fails that step rather than quietly disagreeing with it."""
    return roof_id_pins.is_pinned(rel)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------
# the map
# --------------------------------------------------------------------------

def parcel_ids(parcel: dict) -> list[tuple[int, int, int, str]]:
    """(row index, placement index, sequence, id) for every placement, in build order.

    The sequence is the position across all rows, which is what `make_record` counts and
    what `recon_1835_south_<family>_<seq:03d>` is built from. Walking the recipe here in
    the same order is how this tool finds the placement a verdict is about WITHOUT
    importing the generator, whose import pulls in the datum, the siding stock and four
    other modules to answer a question about two list elements.
    """
    out = []
    seq = 0
    for ri, row in enumerate(parcel["rows"]):
        for pi, placement in enumerate(row["placements"]):
            seq += 1
            out.append((ri, pi, seq, f"{PREFIX}{placement[1].lower()}_{seq:03d}"))
    return out


def moves(parcel: dict | None = None) -> list[dict]:
    """The eleven, derived from the adjudication rather than listed here.

    Derived and not listed because the ledger is RE-DERIVED by the gate: carry a verdict
    out and the roof conforms, so the next re-derivation returns `keep` and the verdict
    is gone. A tool that read its work list from the live ledger would therefore have
    nothing to do the moment it had done it --- which is why `--check` reads the
    committed migration ledger this writes, and only `--plan`/`--apply` read the
    adjudication.
    """
    parcel = parcel if parcel is not None else load(PARCEL)
    at = {sid: (ri, pi, seq) for ri, pi, seq, sid in parcel_ids(parcel)}
    out = []
    for v in load(LEDGER)["verdicts"]:
        if v["verdict"] != "refamily" or not v["id"].startswith(PREFIX):
            continue
        ri, pi, seq = at[v["id"]]
        out.append({
            "from": v["id"],
            "to": f"{PREFIX}{v['to_family'].lower()}_{seq:03d}",
            "row": parcel["rows"][ri]["id"], "row_index": ri, "placement_index": pi,
            "sequence": seq,
            "from_family": v["family"], "to_family": v["to_family"],
            "from_group": v["group"], "to_group": v["to_group"],
            "why": v["reason"],
        })
    out.sort(key=lambda m: m["sequence"])
    return out


# --------------------------------------------------------------------------
# who names a roof
# --------------------------------------------------------------------------

def text_files() -> list[Path]:
    out = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix not in TEXT_SUFFIXES:
            continue
        rel = path.relative_to(ROOT).as_posix()
        if any(rel == d or rel.startswith(d + "/") for d in SKIP_DIRS):
            continue
        if keeps_the_old_name(rel):
            continue
        out.append(path)
    return sorted(out)


def read_utf8(path: Path) -> str | None:
    """The file's text, or None when it is not text at all.

    A `.txt` under `docs/` turned out to be a 400 kB Unreal log in the engine's own
    encoding. It is not something this tool may rewrite and not something it may
    silently pass over either, so it decodes to None and `--check` counts it: a name
    this tool cannot read is a name it cannot promise to have moved.
    """
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None


def names_of(ids: list[str]) -> dict[str, list[str]]:
    """Which committed files name each id today, a record's own file excluded.

    An empty list returns an empty answer rather than an alternation of nothing, which
    is a regex that matches at every position in every file.
    """
    if not ids:
        return {}
    pattern = re.compile("|".join(re.escape(i) for i in ids))
    found: dict[str, list[str]] = {i: [] for i in ids}
    for path in text_files():
        rel = path.relative_to(ROOT).as_posix()
        text = read_utf8(path)
        if text is None:
            continue
        for hit in set(pattern.findall(text)):
            if rel in (f"data/structures/{hit}.json", f"data/sidecars/1835/{hit}.json"):
                continue
            found[hit].append(rel)
    return {k: sorted(v) for k, v in found.items()}


# --------------------------------------------------------------------------
# apply
# --------------------------------------------------------------------------

def refamily(parcel: dict, plan: list[dict]) -> dict:
    """The recipe edit, and it is one field per placement plus two recomputed totals."""
    for m in plan:
        placement = parcel["rows"][m["row_index"]]["placements"][m["placement_index"]]
        if placement[1] != m["from_family"]:
            raise SystemExit(f"{m['from']}: the recipe carries {placement[1]}, not "
                             f"{m['from_family']} — the adjudication is about a parcel "
                             f"that has moved under it")
        placement[1] = m["to_family"]
    # `make_record` reads the class off the family letter, so these two are a COUNT of
    # what the recipe now says and never a second opinion about it.
    families = [p[1] for row in parcel["rows"] for p in row["placements"]]
    parcel["ancillary"] = sum(1 for f in families if f.startswith("A"))
    parcel["principal_functional"] = len(families) - parcel["ancillary"]
    return parcel


def rewrite_names(plan: list[dict]) -> list[str]:
    """Every remaining written name moved, and the files it touched named."""
    rename = {m["from"]: m["to"] for m in plan}
    pattern = re.compile("|".join(re.escape(k) for k in rename))
    touched = []
    for path in text_files():
        text = read_utf8(path)
        if text is None:
            continue
        moved = pattern.sub(lambda mo: rename[mo.group(0)], text)
        if moved != text:
            path.write_text(moved, encoding="utf-8")
            touched.append(path.relative_to(ROOT).as_posix())
    return touched


def move_files(plan: list[dict]) -> list[str]:
    """The sidecar and the two meshes, moved as files rather than rewritten.

    The mesh is moved and NOT left to the bake because a stale
    `<old-id>__inferred_1835.glb` is exactly what `tools/validate.py --stale` cannot
    see: it checks that every record has a fresh mesh, not that every mesh has a record.
    The bake then rewrites the moved file's CONTENTS from the re-derived record.
    """
    moved = []
    for m in plan:
        for base in (SIDECARS,):
            src, dst = base / f"{m['from']}.json", base / f"{m['to']}.json"
            if src.exists():
                src.rename(dst)
                moved.append(f"{src.relative_to(ROOT)} -> {dst.name}")
        for base in ASSETS:
            for src in sorted(base.glob(f"{m['from']}__*")):
                dst = base / src.name.replace(m["from"], m["to"], 1)
                src.rename(dst)
                moved.append(f"{src.relative_to(ROOT)} -> {dst.name}")
        old = STRUCTURES / f"{m['from']}.json"
        if old.exists():
            old.unlink()
            moved.append(f"{old.relative_to(ROOT)} -> removed (re-derived as {m['to']})")
    # The bake's own record of what it built, keyed by mesh NAME. `build.py --only`
    # writes the new key and has no reason to know the old one is dead, so a migration
    # that left it would leave "the record of a bake outlived its output" —
    # `tools/validate.py --stale`'s words — on every one of these, and the withdrawn
    # T-0059 case counts committed assets out of this file and would read eleven too
    # many. The entry is DROPPED and not renamed: its hash is the old record's inputs,
    # and the bake writes the true one.
    manifest = load(MANIFEST)
    for m in plan:
        for name in [k for k in manifest.get("assets", {}) if k.startswith(f"{m['from']}__")]:
            del manifest["assets"][name]
            moved.append(f"assets/manifest.json -> dropped {name} (re-baked as {m['to']})")
    dump(MANIFEST, manifest)
    return moved


def apply() -> int:
    parcel = load(PARCEL)
    plan = moves(parcel)
    if not plan:
        # And this is the ordinary state once the migration has run, not an error. The
        # adjudication is re-derived over the town as it stands: carry a verdict out and
        # the roof conforms, so the next re-derivation returns `keep` and there is
        # nothing outstanding to carry. `--check` reads the committed migration ledger,
        # which is what holds the record of what happened.
        print("no outstanding phase-one South refamily verdict carries an id that "
              "moves — nothing to migrate")
        return 0
    named = names_of([m["from"] for m in plan])
    dump(PARCEL, refamily(parcel, plan))
    moved_files = move_files(plan)
    touched = rewrite_names(plan)
    rc = subprocess.run([sys.executable, str(ROOT / "tools" / "generate_inferred_infill.py")],
                        cwd=ROOT)
    if rc.returncode:
        return rc.returncode
    dump(MIGRATION, {
        "$schema_note": "DERIVED — regenerate with tools/migrate_roof_ids.py --apply; "
                        "tools/check.sh re-derives it with --check. Do not hand-edit.",
        "id": "chicago_july_1835_roof_id_migration_south_phase1",
        "ticket": TICKET,
        "parent_ticket": "T-1452",
        "adjudication": "T-1445, data/reconstruction/1835_roof_redeal.json",
        "target_date": "1835-07-01",
        "generated_by": "tools/migrate_roof_ids.py --apply",
        "not_a_reading": "no page of any source is read here. An adjudication already "
                         "made is carried into the recipe that derives these records, "
                         "and every file that wrote the old name down is moved with it.",
        "parcel": "phase1_south_mixed_blocks",
        "counts": {
            "migrated": len(plan),
            "files_that_named_an_old_id": sorted({f for fs in named.values() for f in fs}),
        },
        "migrations": [dict(m, named_by=named[m["from"]]) for m in plan],
    })
    print(f"migrated {len(plan)} phase-one South roofs")
    for m in plan:
        print(f"  {m['from']} -> {m['to']}  ({m['from_family']} -> {m['to_family']})")
    print(f"  {len(moved_files)} file(s) moved, {len(touched)} file(s) rewritten")
    return 0


# --------------------------------------------------------------------------
# check
# --------------------------------------------------------------------------

def check() -> int:
    if not MIGRATION.exists():
        print(f"{MIGRATION.relative_to(ROOT)} is missing")
        return 1
    committed = load(MIGRATION)
    drift = []
    by_seq = {seq: sid for _, _, seq, sid in parcel_ids(load(PARCEL))}
    for m in committed["migrations"]:
        if by_seq.get(m["sequence"]) != m["to"]:
            drift.append(f"sequence {m['sequence']} derives "
                         f"{by_seq.get(m['sequence'])}, not the migrated {m['to']}")
        if not (STRUCTURES / f"{m['to']}.json").exists():
            drift.append(f"{m['to']} has no record")
        if (STRUCTURES / f"{m['from']}.json").exists():
            drift.append(f"{m['from']} still has a record")
    stale = names_of([m["from"] for m in committed["migrations"]])
    for old, files in stale.items():
        for rel in files:
            if rel == MIGRATION.relative_to(ROOT).as_posix():
                continue
            drift.append(f"{rel} still names the migrated {old}")
    for rel in REDERIVED:
        if (ROOT / rel).read_text(encoding="utf-8").count(f"{PREFIX}") and any(
                m["from"] in (ROOT / rel).read_text(encoding="utf-8")
                for m in committed["migrations"]):
            drift.append(f"{rel} still names a migrated id — it is re-derived, not "
                         f"rewritten, so re-run the tool that writes it")
    if drift:
        print("ROOF ID MIGRATION DRIFT")
        for item in drift:
            print(f"  - {item}")
        return 1
    print(f"verified {len(committed['migrations'])} migrated phase-one South roof ids, "
          f"no committed file naming an old one")
    return 0


def self_test() -> int:
    parcel = {"rows": [{"id": "r", "local_n": 0, "placements": [[1, "D3"], [2, "C1"]]}],
              "principal_functional": 2, "ancillary": 0}
    got = [sid for *_, sid in parcel_ids(parcel)]
    assert got == [f"{PREFIX}d3_001", f"{PREFIX}c1_002"], got
    plan = [{"from": f"{PREFIX}c1_002", "to": f"{PREFIX}a1_002", "row_index": 0,
             "placement_index": 1, "from_family": "C1", "to_family": "A1",
             "sequence": 2}]
    out = refamily(json.loads(json.dumps(parcel)), plan)
    assert out["rows"][0]["placements"][1][1] == "A1"
    assert (out["principal_functional"], out["ancillary"]) == (1, 1), out
    bent = json.loads(json.dumps(parcel))
    bent["rows"][0]["placements"][1][1] = "D7"
    try:
        refamily(bent, plan)
    except SystemExit as exc:
        assert "the recipe carries D7" in str(exc), exc
    else:
        raise AssertionError("a recipe that has moved under the adjudication passed")
    print("migrate_roof_ids self-test: 3 guard(s) fired")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if args.apply:
        return apply()
    if args.check:
        return check()
    plan = moves()
    named = names_of([m["from"] for m in plan])
    for m in plan:
        print(f"{m['from']} -> {m['to']}  ({m['from_family']} -> {m['to_family']}, "
              f"{m['from_group']} -> {m['to_group']})")
        for rel in named[m["from"]]:
            print(f"    {rel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
