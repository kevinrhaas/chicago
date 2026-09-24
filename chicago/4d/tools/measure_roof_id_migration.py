#!/usr/bin/env python3
"""THE GROUND THE 26 MOVING IDS STAND ON, MEASURED BEFORE ANYTHING MOVES. T-1483.

    tools/measure_roof_id_migration.py --build      measure, write the report
    tools/measure_roof_id_migration.py --check      re-measure and refuse drift
    tools/measure_roof_id_migration.py --self-test  the classifier, on fixtures

T-1445 adjudicated the town's 285 anonymous roofs and returned 32 refamily
verdicts. T-1451 carried out the six whose record id does not encode its family.
The other 26 do encode it --- `recon_1835_south_c1_003` becomes `..._d1_003` ---
and the id is not private to the record: some seventy files name these roofs.

THIS TOOL MOVES NOTHING. It answers the question the carry-out tickets
(T-1481/T-1482/T-1484) each have to answer before they may touch a recipe: for
every file that names a moving roof, is the right migration a RENAME, a
RE-DERIVATION, a REFUSAL to touch it, or an ADJUDICATION that a rename would
falsify? Four answers, and only the last costs judgement. Measuring them here,
once, is what makes those three tickets mechanical instead of each rediscovering
the same surface --- and it is what stopped T-1452 being taken as one run.

THE FOURTH ANSWER IS THE POINT, AND IT IS WHY A SCRIPTED RENAME WOULD BE WRONG.
A reference is not always a pointer. `1835_inferred_household_programme.json`
says a household `works_at` a roof; move that roof out of the groups a town can
work in and into a dwelling, and renaming the pointer leaves a cooper employed at
a cottage. The signage and yard files each hold a `refused` row whose REASON
names the trade the roof carried; rename it and the file refuses a signboard to a
dwelling for a reason about a store. Those are the rows a carry-out has to
resolve, and a bare `sed` over the tree would pass every gate and print them
wrong.

THE CLASSIFIER IS MEASURED, NOT LISTED. A file is DERIVED because it says so ---
its own `_doc`/`$schema_note` declares a generator, or it is one of the two
generated trees named below with the reason each is not self-declaring. A
reference is an ADJUDICATION because its own JSON path lands on a key that
asserts something about the roof's FUNCTION, and because the verdict moves the
roof across the group boundary that assertion needs. Everything else is a plain
pointer and renames. The only hand-written list is FROZEN, and every entry
carries why it may not be rewritten.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
LEDGER = DATA / "reconstruction" / "1835_roof_redeal.json"
REPORT = ROOT / "docs" / "RESEARCH" / "1835_roof_id_migration.md"

sys.path.insert(0, str(ROOT / "tools"))
from reconcile_665 import group_of  # noqa: E402

TICKET = "T-1483"
WEST_PREFIX = "recon_1835_west_"

# --------------------------------------------------------------------------
# what a group can carry
# --------------------------------------------------------------------------
#
# Stated once, here, because both adjudication rules below turn on it and a
# second opinion about which group is a workplace would not be the town's. These
# are the nine groups `reconcile_665.group_of` returns.

# A town works in these. A cooper's shop, a store, a warehouse, a tavern, a
# schoolhouse and a boarding house all have somebody employed in them; a cottage,
# a stable and a privy do not.
WORKPLACE_GROUPS = frozenset({
    "stores_mixed_use", "workshops", "warehouses_freight", "inns_taverns",
    "institutional_public", "larger_boarding_houses",
})
# A town sleeps in these. A store-residence and a tavern lodge people; a stable
# and a workshop do not.
HOUSING_GROUPS = frozenset({
    "ordinary_dwellings", "larger_boarding_houses", "inns_taverns",
    "stores_mixed_use",
})

# The keys whose value is not a pointer but an ASSERTION about the roof. Each
# names the group set the assertion needs to stay true.
FUNCTION_KEYS = {
    "works_at": WORKPLACE_GROUPS,
    "workplace": WORKPLACE_GROUPS,
    "employs_at": WORKPLACE_GROUPS,
    "lives_at": HOUSING_GROUPS,
    "lodges_at": HOUSING_GROUPS,
    "seated_at": HOUSING_GROUPS,
}

# --------------------------------------------------------------------------
# the four answers
# --------------------------------------------------------------------------

RENAMED, REDERIVED, FROZEN, ADJUDICATED = "renamed", "re-derived", "frozen", "adjudicated"

# Files that ARE generated and do not say so in a machine-readable way, with the
# reason each is not self-declaring. This is the only place derivedness is
# asserted rather than read, and it is short on purpose.
GENERATED_TREES = {
    "data/sidecars/": "compiled from the structure records by tools/compile_scene.py --all",
    "assets/manifest.json": "written by the bake; one entry per built mesh",
    "assets/manifest.web.json": "written by tools/web_derivatives.sh from the masters",
    "data/liberties.json": "compiled from docs/LIBERTIES.md by tools/compile_liberties.py",
}

# Records of something that ALREADY HAPPENED. A migration may not rewrite these:
# the id they name was the id at the time, and editing it would make a receipt
# claim to have seen a building that did not yet exist under that name.
FROZEN_FILES = {
    "data/research/residents/synthesis_full_gate_after_fixes.log":
        "a log of a gate run on a dated tree — it recorded what it saw",
    "docs/unreal/prototype/import_report.json.txt":
        "an import report from a dated Unreal prototype run",
    "docs/LIBERTIES.md":
        "append-only by its own rule; a liberty already taken is not rewritten, "
        "and the migration appends a new entry instead",
}
FROZEN_TREES = {
    "renderers/unreal/receipts/":
        "per-machine import receipts — each records one dated run on one tree",
}

# Where a reference can live. Read once and searched in memory: the sweep asks
# ~70 files about 26 ids and doing that with one grep per id per root is how the
# earlier measurement cost a minute.
SEARCH_ROOTS = ("data", "tools", "docs", "renderers", "generators")
SEARCH_SUFFIXES = (".json", ".md", ".py", ".mjs", ".js", ".txt", ".log", ".sh")


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def new_id(roof_id: str, to_family: str) -> str:
    """The id the roof takes when its family moves.

    Every moving id is `<head>_<family>_<seq>`: the three generators that build
    an id out of the family all put the family second from the end. The West
    parcel's ids do not carry a family at all and never reach here.
    """
    head, _family, seq = roof_id.rsplit("_", 2)
    return f"{head}_{to_family.lower()}_{seq}"


def moving(ledger: dict) -> list[dict]:
    return sorted((v for v in ledger["verdicts"]
                   if v["verdict"] == "refamily" and not v["id"].startswith(WEST_PREFIX)),
                  key=lambda v: v["id"])


# --------------------------------------------------------------------------
# the classifier
# --------------------------------------------------------------------------

def declares_a_generator(text: str, doc: dict | None) -> str | None:
    """The file's own claim to be derived, quoted back, or None.

    Read from the file rather than asserted about it: a derived file in this
    project says so in `_doc` or `$schema_note`, because `check.sh` re-derives it
    and somebody had to be told not to hand-edit it.
    """
    if doc is not None:
        for key in ("$schema_note", "_doc", "doc", "schema_note"):
            claim = doc.get(key)
            if isinstance(claim, str) and re.search(
                    r"\bDERIVED\b|\bGENERATED\b|regenerate with|Do not hand-edit|"
                    r"NEVER AUTHORED", claim, re.IGNORECASE):
                return claim.strip().split(".")[0][:180]
        for key in ("generated_by", "written_by", "tool"):
            if isinstance(doc.get(key), str):
                return f"generated_by {doc[key]}"
    head = "\n".join(text.splitlines()[:6])
    m = re.search(r"DERIVED\s*[—-]\s*regenerate with[^\n.]*", head)
    return m.group(0) if m else None


def json_paths_of(node, wanted: set[str], path: str = "", key: str | None = None):
    """Every (path, key, id) at which one of `wanted` appears in a JSON tree."""
    if isinstance(node, dict):
        for k, v in node.items():
            yield from json_paths_of(v, wanted, f"{path}.{k}", k)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from json_paths_of(v, wanted, f"{path}[{i}]", key)
    elif isinstance(node, str) and node in wanted:
        yield path, key, node


def adjudications_in(doc, verdict_of: dict) -> list[dict]:
    """The references in one JSON file that a rename would falsify.

    A reference is an adjudication when BOTH hold: its key asserts a function
    (`works_at`, `lives_at`, ...) and the verdict carries the roof out of the
    group that assertion needs. A `works_at` pointing at a store that becomes a
    cottage is one; a `works_at` pointing at a workshop that becomes a store is
    not, because the household still works somewhere.
    """
    out = []
    for path, key, roof in json_paths_of(doc, set(verdict_of)):
        needed = FUNCTION_KEYS.get(key or "")
        if needed is None:
            continue
        v = verdict_of[roof]
        if v["to_group"] in needed:
            continue
        out.append({
            "path": path, "key": key, "id": roof,
            "was_group": v["group"], "now_group": v["to_group"],
            "why": f"`{key}` needs a {'/'.join(sorted(needed))[:0] or ''}"
                   f"{'workplace' if needed is WORKPLACE_GROUPS else 'dwelling'}"
                   f" and {v['to_group']} is not one",
        })
    return out


def leaving_tokens(roof_id: str, verdict: dict) -> set[str]:
    """The words a refusal would have to use to be ABOUT the family that leaves.

    Taken from the roof's own committed record rather than guessed: its family
    code, its group, its archetype and the function it was assigned. A refusal
    reason that uses none of them is a refusal about the SLOT — "an anonymous
    slot, and this project never invents a business for one" — and that sentence
    is exactly as true after the roof becomes a cottage. One that says "is a
    blacksmith_shop" is not.
    """
    tokens = {verdict["family"].lower(), verdict["group"].lower(),
              verdict["group"].replace("_", " ").lower()}
    record = DATA / "structures" / f"{roof_id}.json"
    if record.exists():
        st = load(record)
        for value in (st.get("archetype"), (st.get("function") or {}).get("value")):
            if isinstance(value, str):
                tokens.add(value.lower())
                tokens.add(value.replace("_", " ").lower())
    return {t for t in tokens if len(t) > 2}


def refusal_rows_in(doc, verdict_of: dict) -> list[dict]:
    """`refused` rows whose stated reason is about the family that is leaving.

    The signage, yard and frontage files each carry a `refused` list: roofs
    deliberately given no signboard, no goods and no hitching post, each with a
    reason. Some of those reasons are about the SLOT and survive the move
    untouched; some are about the TRADE — "the trade at ... is reconstructed",
    "is a blacksmith_shop" — and renaming those leaves the file refusing a
    cottage a signboard for a reason about a smithy. Only the second kind is an
    adjudication, and which kind a row is, is read from the row against the
    roof's own record rather than assumed from the file it sits in.
    """
    out = []
    for path, key, roof in json_paths_of(doc, set(verdict_of)):
        if ".refused[" not in path:
            continue
        row = doc
        for part in re.findall(r"\.([^.\[\]]+)|\[(\d+)\]", path.rsplit(".", 1)[0]):
            row = row[part[0]] if part[0] else row[int(part[1])]
        if not isinstance(row, dict):
            continue
        reason = " ".join(str(v) for k, v in row.items()
                          if k in ("reason", "why", "note") and isinstance(v, str))
        v = verdict_of[roof]
        named = sorted(t for t in leaving_tokens(roof, v) if t in reason.lower())
        if not named:
            continue
        out.append({
            "path": path, "key": key, "id": roof,
            "was_group": v["group"], "now_group": v["to_group"],
            "names": named, "reason": reason[:200],
        })
    return out


def classify(rel: str, text: str, doc, verdict_of: dict) -> dict:
    for name, why in FROZEN_FILES.items():
        if rel == name:
            return {"answer": FROZEN, "why": why}
    for tree, why in FROZEN_TREES.items():
        if rel.startswith(tree):
            return {"answer": FROZEN, "why": why}

    adjudications = refusal_rows_in(doc, verdict_of) if doc is not None else []
    adjudications += adjudications_in(doc, verdict_of) if doc is not None else []
    if adjudications:
        return {"answer": ADJUDICATED, "why": "a reference here asserts what the "
                "roof is, and the verdict moves it out of that",
                "rows": adjudications}

    for tree, why in GENERATED_TREES.items():
        if rel.startswith(tree):
            return {"answer": REDERIVED, "why": why}
    claim = declares_a_generator(text, doc if isinstance(doc, dict) else None)
    if claim:
        return {"answer": REDERIVED, "why": claim}

    return {"answer": RENAMED, "why": "a plain pointer at the record"}


# --------------------------------------------------------------------------
# the sweep
# --------------------------------------------------------------------------

def sweep(verdicts: list[dict]) -> tuple[list[dict], dict]:
    verdict_of = {v["id"]: v for v in verdicts}
    ids = set(verdict_of)
    own = {f"data/structures/{i}.json" for i in ids}
    files = []
    for root in SEARCH_ROOTS:
        for path in sorted((ROOT / root).rglob("*")):
            if not path.is_file() or path.suffix not in SEARCH_SUFFIXES:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            named = sorted(i for i in ids if i in text)
            if not named:
                continue
            rel = str(path.relative_to(ROOT))
            # The report is the output of this sweep and names every moving id by
            # definition; counting it would make the measurement grow by one each
            # time it was taken.
            if rel in own or path == REPORT:
                continue
            doc = None
            if path.suffix == ".json":
                try:
                    doc = json.loads(text)
                except json.JSONDecodeError:
                    doc = None
            entry = {"file": rel, "names": named}
            entry.update(classify(rel, text, doc, verdict_of))
            files.append(entry)
    files.sort(key=lambda f: (f["answer"], f["file"]))
    counts = {a: sum(1 for f in files if f["answer"] == a)
              for a in (ADJUDICATED, RENAMED, REDERIVED, FROZEN)}
    return files, counts


# --------------------------------------------------------------------------
# the report
# --------------------------------------------------------------------------

def render(verdicts: list[dict], files: list[dict], counts: dict) -> str:
    out = ["# The ground the 26 moving roof ids stand on — July 1835\n",
           f"DERIVED — regenerate with `tools/measure_roof_id_migration.py --build`. {TICKET}.\n",
           "T-1445 returned 32 refamily verdicts; T-1451 carried out the 6 whose record id "
           "does not encode its family. These are the other 26. Each becomes a new id the "
           "moment its family moves, and the id is named across the tree. NOTHING IS MOVED "
           "HERE: this is the measurement the three carry-out tickets "
           "(T-1481 south, T-1482 the platted blocks, T-1484 north) each stand on.\n"]
    out.append(f"- roofs whose id moves: **{len(verdicts)}**")
    out.append(f"- files that name one: **{len(files)}**")
    out.append(f"- of those, **{counts[ADJUDICATED]}** hold a reference a rename would "
               f"falsify, **{counts[RENAMED]}** rename, **{counts[REDERIVED]}** are "
               f"re-derived by their own tool, **{counts[FROZEN]}** are frozen records "
               f"of a past run\n")

    out.append("## The rows that cost judgement\n")
    out.append("A reference is not always a pointer. These assert what the roof IS, and the "
               "verdict moves it out of that — so a carry-out has to resolve them, not "
               "rename them. This is the list a scripted rename would have passed over.\n")
    out.append("| file | where | roof | group | becomes | why it is not a rename |")
    out.append("| --- | --- | --- | --- | --- | --- |")
    rows = 0
    for f in files:
        for r in f.get("rows", []):
            rows += 1
            why = r.get("why") or (
                f"the refusal's own reason says “{', '.join(r['names'])}” — it is about "
                f"the {r['was_group']} that leaves: “{r['reason']}”")
            out.append(f"| `{f['file']}` | `{r['path']}` | `{r['id']}` | {r['was_group']} "
                       f"| {r['now_group']} | {why} |")
    out.append(f"\n**{rows}** reference(s), across {counts[ADJUDICATED]} file(s).\n")

    out.append("## Every moving roof, and what names it\n")
    out.append("| roof | becomes | renamed | re-derived | frozen | adjudicated |")
    out.append("| --- | --- | ---: | ---: | ---: | ---: |")
    for v in verdicts:
        per = {a: 0 for a in (RENAMED, REDERIVED, FROZEN, ADJUDICATED)}
        for f in files:
            if v["id"] in f["names"]:
                per[f["answer"]] += 1
        out.append(f"| `{v['id']}` | `{new_id(v['id'], v['to_family'])}` | "
                   f"{per[RENAMED]} | {per[REDERIVED]} | {per[FROZEN]} | {per[ADJUDICATED]} |")
    out.append("")

    for answer, title, blurb in (
        (RENAMED, "Renamed", "A plain pointer at the record. The migration rewrites the "
                             "string and nothing else is owed."),
        (REDERIVED, "Re-derived", "Written by a tool, which `check.sh` re-runs. The "
                                  "migration must NOT hand-edit these; it re-runs the tool "
                                  "and commits what comes out."),
        (FROZEN, "Frozen", "A record of something that already happened. The id it names "
                           "was the id at the time; rewriting it would make a receipt claim "
                           "to have seen a building that did not exist under that name."),
        (ADJUDICATED, "Adjudicated", "Listed above with the reference that has to be "
                                     "resolved."),
    ):
        out.append(f"## {title} — {counts[answer]} file(s)\n")
        out.append(blurb + "\n")
        out.append("| file | roofs | why |")
        out.append("| --- | ---: | --- |")
        for f in files:
            if f["answer"] == answer:
                out.append(f"| `{f['file']}` | {len(f['names'])} | {f['why']} |")
        out.append("")
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------------

def self_test() -> int:
    ok = True

    def want(cond, msg):
        nonlocal ok
        if not cond:
            ok = False
            print(f"  FAIL {msg}")

    want(new_id("recon_1835_south_c1_003", "D1") == "recon_1835_south_d1_003",
         "a south id takes its new family in place")
    want(new_id("recon_1835_blk_randolph_market_a1_07", "D4")
         == "recon_1835_blk_randolph_market_d4_07",
         "a platted-block id keeps its block and its slot number")
    want(new_id("recon_1835_north_c1_020", "D3") == "recon_1835_north_d3_020",
         "a north id keeps its sequence")

    store_to_cottage = {"recon_1835_x_c1_001": {
        "id": "recon_1835_x_c1_001", "family": "C1", "group": "stores_mixed_use",
        "to_group": "ordinary_dwellings"}}
    shop_to_store = {"recon_1835_x_w1_002": {
        "id": "recon_1835_x_w1_002", "family": "W1", "group": "workshops",
        "to_group": "stores_mixed_use"}}

    want(len(adjudications_in({"households": [{"works_at": "recon_1835_x_c1_001"}]},
                              store_to_cottage)) == 1,
         "a household working at a store that becomes a cottage is an adjudication")
    want(adjudications_in({"households": [{"works_at": "recon_1835_x_w1_002"}]},
                          shop_to_store) == [],
         "a household working at a shop that becomes a store still works somewhere")
    want(adjudications_in({"households": [{"near": "recon_1835_x_c1_001"}]},
                          store_to_cottage) == [],
         "a pointer that asserts nothing about function is a rename")
    want(len(adjudications_in({"h": [{"lives_at": "recon_1835_x_c1_001"}]},
                              {"recon_1835_x_c1_001": {
                                  "id": "recon_1835_x_c1_001", "family": "C1",
                                  "group": "stores_mixed_use",
                                  "to_group": "barns_stables"}})) == 1,
         "somebody living in a store that becomes a stable is an adjudication")

    want(len(refusal_rows_in(
        {"refused": [{"structure_id": "recon_1835_x_c1_001",
                      "reason": "no board: this is a stores_mixed_use with no named firm"}]},
        store_to_cottage)) == 1,
         "a refusal row whose reason names the leaving group is an adjudication")
    want(refusal_rows_in(
        {"refused": [{"structure_id": "recon_1835_x_c1_001",
                      "reason": "an anonymous slot, and this project invents no business "
                                "for one"}]},
        store_to_cottage) == [],
         "a refusal about the SLOT is as true after the move, and renames")

    want(declares_a_generator("", {"$schema_note": "DERIVED. Written by tools/x.py"}),
         "a file that says it is derived is read as derived")
    want(declares_a_generator("", {"id": "x"}) is None,
         "a file that claims nothing is not assumed to be derived")
    want(classify("renderers/unreal/receipts/mac-1.json", "", None, {})["answer"] == FROZEN,
         "an import receipt is frozen")

    print("  self-test:", "ok" if ok else "FAILED")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()

    verdicts = moving(load(LEDGER))
    files, counts = sweep(verdicts)
    text = render(verdicts, files, counts)

    if args.build:
        REPORT.write_text(text, encoding="utf-8")
        print(f"{len(verdicts)} moving id(s) across {len(files)} file(s): "
              + ", ".join(f"{n} {a}" for a, n in counts.items()))
        return 0

    if not REPORT.exists():
        print(f"DRIFT: {REPORT.relative_to(ROOT)} has not been measured — run --build")
        return 1
    if REPORT.read_text(encoding="utf-8") != text:
        print(f"DRIFT: {REPORT.relative_to(ROOT)} is not what a re-measurement "
              f"produces — run --build and commit the result")
        return 1
    print(f"the migration surface holds: {len(verdicts)} moving id(s), {len(files)} file(s), "
          f"{counts[ADJUDICATED]} of them carrying a reference a rename would falsify")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
