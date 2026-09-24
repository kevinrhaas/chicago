#!/usr/bin/env python3
"""What the letter-list mint would do to the town if it ran today, counted (T-1334).

`tools/mint_letter_list_residents.py` re-derives 798 files differently from the ones
committed. That number has been carried in prose since T-0662 and it says nothing: 798
could be one harmless prefix repeated 798 times, or it could be the town gaining a
hundred people nobody read. T-1334's first acceptance is that the drift is MEASURED AND
NAMED, so this tool reads the mint's output against the committed tree and says, per
class and per key, what a re-run would actually change.

WHAT THIS IS NOT. It is not the gate. T-1222 owns the check `tools/check.sh` should run
at the mint's own place in the pipeline, and that is a different instrument: it has to
compare what the mint OWNS and ignore what a later pass owns, which means ruling on
ownership key by key and defending each ruling. This tool rules on nothing. It sorts the
difference into classes a reader can check by hand and prints the counts, and where it
cannot attribute a key it says so loudly rather than folding it into a bucket. Run it,
read it, and take the argument to T-1222.

THE FOUR CLASSES, in the order they matter to the town:

  people the town would GAIN     a household the mint derives that is on no committed
                                 card, whose head's name matches no person in the layer
  people the town would RENAME   a household the mint derives under an id the layer does
                                 not hold, whose head's name IS already in the layer
                                 under another id — a re-mint, not a new person
  people the town would LOSE     a committed letter-list household the mint no longer
                                 derives at all
  cards that would be REWRITTEN  a household both sides hold, differing in fields

Only the last class is the one the prose has been describing. The first three are people.

USAGE
  python3 tools/letter_list_mint_drift.py            the report
  python3 tools/letter_list_mint_drift.py --json     the same numbers as JSON
"""
from __future__ import annotations

import argparse
import collections
import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MINT = ROOT / "tools" / "mint_letter_list_residents.py"

# WHO OWNS EACH KEY THE TWO TREES DISAGREE ABOUT. A key is listed here only where the
# project has already written down which pass fills it; the `note` on each row is the
# evidence a reader checks the attribution against. Anything not listed comes out under
# UNATTRIBUTED, which is a finding and not a default.
#
# `mint` means the mint derives the value itself, so a difference is the mint's own
# derivation having MOVED — the register's letter-list readings were re-read under
# T-1115, T-1138 and T-1155 and the mint has not been run since.
# Every other owner is a pass that runs AFTER the mint and writes over it, so a
# difference is work a re-run would REVERT.
OWNERS: list[tuple[str, str, str]] = [
    ("name", "mint",
     "the household label the mint builds out of the read name"),
    ("persons[].name", "mint",
     "the person name as the register prints it, which is the mint's to read"),
    ("persons[].letter_list_only", "mint",
     "the mint's own cohort flag"),
    ("persons[].letter_list_returns", "mint",
     "the dated returns of uncalled-for letters the mint counts the name in"),
    ("arrival", "mint",
     "the bound the mint derives from the earliest return, and nothing else writes"),
    ("present_on_scene_date", "mint",
     "the mint states the corpus's last dated appearance here; it moves with the returns"),
    ("persons[].grade", "synthesize_resident_research.py / spend_ladder_rungs.py",
     "the PROJECTED RESIDENT downgrade and the ratified ladder's rungs, both after the mint"),
    ("persons[].note", "synthesize_resident_research.py / spend_ladder_rungs.py",
     "the same two passes prepend their prose to the note the mint wrote"),
    ("persons[].sources", "the resident-research passes",
     "a corroborating source appended to the card after the mint set the list"),
    ("persons[].occupation", "the resident-research passes",
     "the mint writes none_recorded; a later reading fills the trade it found"),
    ("origin", "the arrival and origin fill stage (T-1169)",
     "written_by_stage: attribute_fill_arrival; the mint writes Not attested."),
    ("reason_for_coming", "the arrival and origin fill stage (T-1169)",
     "written_by_stage: attribute_fill_arrival"),
]


def load_mint():
    spec = importlib.util.spec_from_file_location("mint_letter_list_residents", MINT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def normalise(path: str) -> str:
    """A leaf path with list indices flattened: persons.[0].note becomes persons[].note."""
    return re.sub(r"\.?\[\d+\]", "[]", path)


def owner_of(key: str) -> tuple[str, str]:
    for prefix, owner, why in OWNERS:
        if key == prefix or key.startswith(prefix + ".") or key.startswith(prefix + "["):
            return owner, why
    return "UNATTRIBUTED", "no pass in this tool's table claims this key"


def leaves(a, b, prefix: str = "") -> list[str]:
    """Every leaf path at which two committed documents differ."""
    out: list[str] = []
    if isinstance(a, dict) and isinstance(b, dict):
        for key in sorted(set(a) | set(b)):
            if key not in a or key not in b:
                out.append(prefix + key)
            elif a[key] != b[key]:
                out += leaves(a[key], b[key], prefix + key + ".")
        return out
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for index, (x, y) in enumerate(zip(a, b)):
            if x != y:
                out += leaves(x, y, f"{prefix}[{index}].")
        return out
    return [prefix.rstrip(".")]


def person_names(module) -> dict[str, list[str]]:
    """Every person name standing in the committed layer, folded for comparison."""
    index: dict[str, list[str]] = collections.defaultdict(list)
    for path in sorted(module.HOUSEHOLDS.glob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        for person in doc.get("persons", []):
            index[fold(person.get("name"))].append(path.stem)
    return index


def fold(name) -> str:
    """A name reduced to its bare word set, so 'Joseph Pothier' and 'Pothier, Joseph' meet."""
    words = re.sub(r"[^a-z ]", " ", str(name or "").lower()).split()
    return " ".join(sorted(w for w in words if len(w) > 1))


def measure() -> dict:
    module = load_mint()
    files, accepted, refusals, mine = module.build()
    index_path = module.INDEX
    committed = person_names(module)

    gained, renamed, rewritten = [], [], []
    keys: collections.Counter = collections.Counter()
    files_by_owner: collections.Counter = collections.Counter()
    for path, text in files.items():
        if path == index_path:
            continue
        if not path.exists():
            head = json.loads(text)["persons"][0]
            row = {"id": path.stem, "name": head.get("name")}
            folded = fold(head.get("name"))
            if folded in committed:
                row["already_in_the_layer_as"] = sorted(committed[folded])
                renamed.append(row)
            else:
                gained.append(row)
            continue
        old = json.loads(path.read_text(encoding="utf-8"))
        new = json.loads(text)
        if old == new:
            continue
        differing = sorted({normalise(k) for k in leaves(old, new)})
        for key in differing:
            keys[key] += 1
        for owner in sorted({owner_of(k)[0] for k in differing}):
            files_by_owner[owner] += 1
        rewritten.append({"id": path.stem, "keys": differing,
                          "owners": sorted({owner_of(k)[0] for k in differing})})

    lost = sorted(p.stem for p in mine if p not in files)
    return {
        "mint_would_hold": len(accepted),
        "mint_would_refuse": len(refusals),
        "committed_under_this_pass": len(mine),
        "drifting_files": len(rewritten) + len(gained) + len(renamed) + len(lost)
                          + (1 if index_path in files and (
                              not index_path.exists()
                              or index_path.read_text(encoding="utf-8") != files[index_path])
                             else 0),
        "gained": sorted(gained, key=lambda r: r["id"]),
        "renamed": sorted(renamed, key=lambda r: r["id"]),
        "lost": lost,
        "rewritten": sorted(rewritten, key=lambda r: r["id"]),
        "keys": dict(keys.most_common()),
        "files_touching_each_owner": dict(files_by_owner.most_common()),
        "files_by_exact_owner_set": {
            " + ".join(owners): count for owners, count in
            collections.Counter(tuple(row["owners"]) for row in rewritten).most_common()},
    }


def report(found: dict) -> None:
    print("THE LETTER-LIST MINT, RE-RUN AGAINST THE COMMITTED TREE")
    print(f"  the mint holds            {found['mint_would_hold']:5d} household(s)")
    print(f"  the mint refuses          {found['mint_would_refuse']:5d} candidate(s)")
    print(f"  the layer carries         {found['committed_under_this_pass']:5d} "
          "household(s) under this pass's mark")
    print(f"  files that differ         {found['drifting_files']:5d}\n")

    print("WHAT A RE-RUN WOULD DO TO THE TOWN'S PEOPLE")
    print(f"  people GAINED             {len(found['gained']):5d} "
          "household(s) on no committed card, under a name the layer holds nowhere")
    print(f"  households RENAMED        {len(found['renamed']):5d} "
          "re-mint(s) of a name the layer already holds under another id")
    print(f"  people LOST               {len(found['lost']):5d} "
          "committed letter-list household(s) the mint no longer derives")
    print(f"  cards REWRITTEN           {len(found['rewritten']):5d}\n")

    print("THE REWRITTEN CARDS, BY WHO OWNS THE KEY THAT MOVED")
    for owner, count in found["files_touching_each_owner"].items():
        print(f"  {count:5d} file(s)  {owner}")
    print("\n  …and by the EXACT set of owners each card's difference touches, which is "
          "the cut that\n  says how much of the 798 is one prefix repeated and how much "
          "is somebody's work:")
    for owners, count in found["files_by_exact_owner_set"].items():
        print(f"  {count:5d} file(s)  {owners}")
    print()
    print("EVERY KEY THAT MOVED, AND WHO OWNS IT")
    for key, count in found["keys"].items():
        owner, why = owner_of(key)
        print(f"  {count:5d}  {key:42s} {owner}")
        print(f"         {why}")
    unattributed = [k for k in found["keys"] if owner_of(k)[0] == "UNATTRIBUTED"]
    if unattributed:
        print("\nUNATTRIBUTED KEYS — no pass in this tool's table claims these, and a key "
              "nobody owns\nis the finding this report exists to surface:")
        for key in unattributed:
            print(f"  {key}")
    print("\nThe people this re-run would ADD, in full — every one of them is a person "
          "the town\ndoes not hold and nobody has read:")
    for row in found["gained"]:
        print(f"  {row['id']:30s} {row['name']}")
    print("\nThe households it would LOSE:")
    for hid in found["lost"]:
        print(f"  {hid}")
    print("\nThe re-mints, and the card each one already stands on:")
    for row in found["renamed"]:
        print(f"  {row['id']:30s} {row['name']:26s} "
              f"-> {', '.join(row['already_in_the_layer_as'])}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", action="store_true",
                        help="the report (the default)")
    parser.add_argument("--json", action="store_true",
                        help="the same numbers as JSON, for a reader that is a program")
    args = parser.parse_args()
    found = measure()
    if args.json:
        print(json.dumps(found, indent=2, ensure_ascii=False))
        return 0
    report(found)
    return 0


if __name__ == "__main__":
    sys.exit(main())
