#!/usr/bin/env python3
"""What the three inferred-household passes still own — one implementation (T-1228).

    python3 tools/inferred_household_ownership.py            print the settlement
    python3 tools/inferred_household_ownership.py --self-test  the assertions still fire

WHY A FIELD-LEVEL CONTRACT AND NOT BYTE-IDENTITY.

The three passes — `generate_inferred_households.py`, `generate_inferred_names.py`,
`replace_invented_residents.py` — are one pipeline, and on 2026-09-02 the owner's
T-0489 ruling retired the reconstructed resident population it exists to produce,
keeping the geometry as anonymous stock. Nothing told the generators. They went on
deriving the whole retired layer, so every `--check` went red against a tree that
is no longer their derivation: 96 households missing, 31 roofs stripped of their
occupant, four more records carrying later tickets' edits, and the five survivors
absorbed into the resident research layer.

Byte-identity is therefore the WRONG CONTRACT for these passes, for exactly the
reason T-0662 already found for the letter-list mint: they are not the last writer
of the files they derive. Re-running them in write mode is a REVERSAL of an owner
ruling, and a `--check` that demands the whole file back is asking for that
reversal once per commit.

So the contract is field-level, and it has two halves, both of them checked:

  A. OWNED-FIELD EXACTNESS — for every field a pass is still the last writer of,
     the tree must equal what the pass derives. Non-circular: the expectation
     comes from the authored programme, not from the tree.

  B. WITHDRAWAL INTACTNESS — for every field some ruling or later pass took off
     it, the tree must still satisfy that ruling's own shape. Also non-circular:
     the expectation is a stated rule, checked against the tree. This is what
     stops a withdrawal from being a hole in the gate — a retired household that
     reappears, or an `occupants` block that stops saying "anonymous stock", goes
     red here rather than passing unnoticed because nobody compares it.

The settlement itself — which records, which paths, and the ticket that took each
withdrawn one — is authored data, not code:
`data/reconstruction/1835_inferred_household_pass_ownership.json`.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
RECORD = ROOT / "data" / "reconstruction" / "1835_inferred_household_pass_ownership.json"
STRUCTURES = ROOT / "data" / "structures"
HOUSEHOLDS = ROOT / "data" / "residents" / "households"
# The programme that reopened invented naming under an auditable stage (T-1167).
PROGRAMME_1167 = ROOT / "data" / "reconstruction" / "1835_resident_reconstruction_programme.json"

MISSING = object()          # distinct from a committed null


def settlement() -> dict:
    return json.loads(RECORD.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------
# paths — "a.b[].c" walks every element of the list at b
# --------------------------------------------------------------------------

def _steps(path: str) -> list:
    out = []
    for part in path.split("."):
        head, *idx = re.split(r"\[(\d*)\]", part)
        if head:
            out.append(head)
        for token in idx:
            if token == "":
                continue
            out.append("[]" if token == "" else int(token) if token.isdigit() else "[]")
        # a bare "[]" between the split tokens means "every element"
        if "[]" in part:
            out.append("[]")
    return out


def reach(doc, path: str) -> list:
    """Every value the path selects, as (label, value) pairs. MISSING where absent."""
    frontier = [(path.split(".")[0] if False else "", doc)]
    for step in _steps(path):
        nxt = []
        for label, node in frontier:
            if step == "[]":
                if isinstance(node, list):
                    nxt += [(f"{label}[{i}]", v) for i, v in enumerate(node)]
                else:
                    nxt.append((label, MISSING))
            elif isinstance(node, dict):
                nxt.append((f"{label}.{step}".lstrip("."), node.get(step, MISSING)))
            else:
                nxt.append((f"{label}.{step}".lstrip("."), MISSING))
        frontier = nxt
    return frontier


def prune(doc, paths: list[str]):
    """A copy of doc with every listed path removed, so what is left is the owned part."""
    out = json.loads(json.dumps(doc))

    def drop(node, steps):
        if not steps or node is None:
            return
        step, rest = steps[0], steps[1:]
        if step == "[]":
            if isinstance(node, list):
                for v in node:
                    drop(v, rest)
            return
        if not isinstance(node, dict):
            return
        if not rest:
            node.pop(step, None)
            return
        drop(node.get(step), rest)

    for path in paths:
        if path == "*":
            return {}
        drop(out, _steps(path))
    return out


def graft(derived, tree, paths: list[str]):
    """`derived`, with every listed path taken from `tree` instead.

    The other half of `prune`, and the reason it exists is T-1191. A pass that OWNS a
    record but may not write it has no way to land a correction: the households pass
    refuses `--write` outright, because writing regenerates the whole record and that
    reverses the owner's T-0489 retirement of the resident population. So for as long
    as that refusal has stood, the only way to move a roof the pass owns has been to
    hand-edit the file the pass derives — which is the exact fault T-1227 was written
    to stop, and it produced a programme and a record that disagreed for a fortnight.

    This is the operation the refusal was missing: keep the derivation for the fields
    the pass still owns, and keep the TREE for the withheld ones, so a correction can
    land without a ruling being undone. A withheld path absent from the tree is removed
    from the result rather than defaulted, because absence there is itself the ruling.
    """
    out = json.loads(json.dumps(derived))

    def carry(dst, src, steps):
        step, rest = steps[0], steps[1:]
        if step == "[]":
            if isinstance(dst, list) and isinstance(src, list):
                for d, s_ in zip(dst, src):
                    carry(d, s_, rest)
            return
        if not isinstance(dst, dict):
            return
        if not rest:
            if isinstance(src, dict) and step in src:
                dst[step] = json.loads(json.dumps(src[step]))
            else:
                dst.pop(step, None)
            return
        carry(dst.get(step), src.get(step) if isinstance(src, dict) else None, rest)

    for path in paths:
        if path == "*":
            return json.loads(json.dumps(tree))
        carry(out, tree, _steps(path))
    return out


def withheld_paths(pass_id: str) -> dict[str, list[str]]:
    """Per structure id, the paths the settlement withholds from `pass_id`."""
    spec = settlement()["passes"][pass_id]
    out: dict[str, list[str]] = {}
    for block in spec["withdrawn"]:
        for sid in block.get("applies_to", []):
            out.setdefault(sid, []).extend(block["paths"])
    for block in spec["reassigned"]:
        out.setdefault(block["structure"], []).extend(block["paths"])
    return out


def differences(disk, derived, where: str) -> list[str]:
    """Every leaf that differs, named by its path. Order-preserving, deduped by path."""
    out = []

    def walk(a, b, path):
        if isinstance(a, dict) and isinstance(b, dict):
            for k in sorted(set(a) | set(b)):
                if k not in a:
                    out.append(f"{where}: {path}.{k} is derived and not in the tree")
                elif k not in b:
                    out.append(f"{where}: {path}.{k} is in the tree and not derived")
                else:
                    walk(a[k], b[k], f"{path}.{k}")
        elif isinstance(a, list) and isinstance(b, list):
            if len(a) != len(b):
                out.append(f"{where}: {path} has {len(a)} item(s) in the tree, "
                           f"{len(b)} derived")
            else:
                for i, (x, y) in enumerate(zip(a, b)):
                    walk(x, y, f"{path}[{i}]")
        elif a != b:
            out.append(f"{where}: {path} is {_short(a)} in the tree, {_short(b)} derived")

    walk(disk, derived, "")
    return out


def _short(v) -> str:
    text = json.dumps(v, ensure_ascii=False)
    return text if len(text) <= 70 else text[:67] + "..."


# --------------------------------------------------------------------------
# half B — the withdrawals are still standing
# --------------------------------------------------------------------------

def assert_shape(doc, rules: dict, where: str) -> list[str]:
    """Each rule is `path: expected`, or `path~: substring` for a note."""
    out = []
    for key, expected in rules.items():
        contains = key.endswith("~")
        path = key[:-1] if contains else key
        for label, value in reach(doc, path):
            if value is MISSING:
                out.append(f"{where}: {path} is gone — the withdrawal it recorded "
                           f"is no longer stated in the record")
            elif contains:
                if not isinstance(value, str) or expected not in value:
                    out.append(f"{where}: {path} no longer cites {expected!r}, so the "
                               f"record no longer says which ruling withdrew it")
            elif value != expected:
                out.append(f"{where}: {path} is {_short(value)}, but the ruling "
                           f"leaves it {_short(expected)}")
    return out


def absent(paths: list[pathlib.Path], why: str) -> list[str]:
    return [f"{p.relative_to(ROOT)} is back on disk — {why}" for p in paths if p.exists()]


# --------------------------------------------------------------------------
# the three passes' checks
# --------------------------------------------------------------------------

def check_households_pass(derived: dict[pathlib.Path, str]) -> list[str]:
    """`generate_inferred_households.py --check`: the 38 structure records it owns."""
    spec = settlement()["passes"]["tools/generate_inferred_households.py"]
    owned = spec["still_owns"]["data/structures"]
    withheld = withheld_paths("tools/generate_inferred_households.py")

    drift: list[str] = []
    for sid in owned["ids"]:
        path = STRUCTURES / f"{sid}.json"
        text = derived.get(path)
        if text is None:
            drift.append(f"{sid} is in the settlement but this pass no longer derives it")
            continue
        if not path.exists():
            drift.append(f"data/structures/{sid}.json is missing")
            continue
        skip = withheld.get(sid, [])
        drift += differences(prune(json.loads(path.read_text(encoding="utf-8")), skip),
                             prune(json.loads(text), skip), sid)

    # half B: the ruling is still standing on the roofs it emptied, and the 96
    # households it removed have not come back.
    for block in spec["withdrawn"]:
        rules = block.get("assert_instead")
        if rules:
            for sid in block.get("applies_to", []):
                doc = json.loads((STRUCTURES / f"{sid}.json").read_text(encoding="utf-8"))
                drift += assert_shape(doc, rules, sid)
        drift += absent([HOUSEHOLDS / f"{h}.json"
                         for h in block.get("applies_to_households", [])],
                        f"{block['by']} retired it and nothing may put it back")
    return drift


def check_names_pass(derived: dict[pathlib.Path, dict],
                     rederived: dict[pathlib.Path, dict]) -> list[str]:
    """`generate_inferred_names.py --check`: a pass that owns no committed file."""
    drift: list[str] = []
    if not derived:
        drift.append("the naming pass dealt no names at all, so nothing below is a "
                     "test — its input is the household programme, not the tree")
    changed = sorted(p.name for p in derived if derived[p] != rederived.get(p))
    if changed:
        drift.append(f"the allocation is not deterministic: {len(changed)} household(s) "
                     f"got different names on a second derivation "
                     f"({', '.join(changed[:5])})")
    # Only the people this pass NAMES are its own: the household programme's
    # output also carries the documented households it links, whose heads are real
    # people with sourced names and no name_basis to give.
    invented = 0
    for path, doc in sorted(derived.items()):
        for person in doc.get("persons", []):
            if person.get("grade") != "reconstructed":
                continue
            invented += 1
            basis = person.get("name_basis")
            if basis is None:
                drift.append(f"{path.stem}: {person.get('id')} was dealt a name with no "
                             f"name_basis, so nothing says the name was invented")
            elif basis.get("confidence") != "reconstructed":
                drift.append(f"{path.stem}: {person.get('id')} carries a name_basis graded "
                             f"{basis.get('confidence')!r} — an invented name may claim "
                             f"nothing better than reconstructed")
    if derived and not invented:
        drift.append("not one person in the naming pass's input is graded "
                     "reconstructed, so no invented name was dealt and nothing below "
                     "is a test")
    # half B: not one of THIS PASS's names stands in the tree, because T-0489 retired
    # every person it ever named.
    #
    # T-1314 narrowed what "this pass's" means. The test used to be "no person in the
    # tree carries a name_basis at all", which was the same sentence for as long as this
    # pass was the only thing that had ever dealt an invented name. Since T-1167 the
    # reconstruction programme deals them too, under a stage that re-derives the person
    # and a record contract `tools/reconstruct_residents_1835.py --check` holds. Those
    # are not this pass's people coming back, and reading them as such would make the
    # programme the owner asked for unlandable. A name_basis on anyone the programme does
    # NOT claim is still exactly the return T-0489 forbade, and still fails here.
    try:
        prog = json.loads(PROGRAMME_1167.read_text(encoding="utf-8"))
        stage_keys = {row.get("key") for row in prog.get("stages") or []}
    except (OSError, ValueError):
        stage_keys = set()

    def unclaimed(person):
        return (isinstance(person, dict) and person.get("name_basis")
                and (person.get("reconstruction") or {}).get("stage") not in stage_keys)

    standing = sorted(p.name for p in HOUSEHOLDS.glob("*.json")
                      if any(unclaimed(person) for person in json.loads(
                          p.read_text(encoding="utf-8")).get("persons", [])))
    drift += [f"data/residents/households/{name} carries an invented name_basis that no "
              f"reconstruction stage claims — T-0489 retired the reconstructed resident "
              f"population and nothing may put an invented resident back outside the "
              f"programme" for name in standing]
    return drift


def check_replace_pass(seated: dict[str, dict]) -> list[str]:
    """`replace_invented_residents.py --check`: the heads the register deal seats.

    `seated` maps household id -> the person record this pass deals that roof.
    """
    spec = settlement()["passes"]["tools/replace_invented_residents.py"]
    owned = spec["still_owns"]["data/residents/households"]
    drift: list[str] = []

    expected = {row["household"]: row for row in owned["seats"]}
    if sorted(seated) != sorted(expected):
        gained = sorted(set(seated) - set(expected))
        lost = sorted(set(expected) - set(seated))
        for hid in gained:
            drift.append(f"{hid} is seated by the deal and is not in the settlement — "
                         f"the register has changed under these roofs")
        for hid in lost:
            drift.append(f"{hid} is in the settlement and the deal no longer seats it")

    for hid, row in sorted(expected.items()):
        path = HOUSEHOLDS / f"{hid}.json"
        if not path.exists():
            drift.append(f"data/residents/households/{hid}.json is missing — the roof this "
                         f"deal seated a documented man on is gone")
            continue
        doc = json.loads(path.read_text(encoding="utf-8"))
        head = next((p for p in doc.get("persons", [])
                     if p.get("relationship") == "head"), {})
        person = seated.get(hid, {})
        for field in ("id", "name"):
            if person and person.get(field) != row[f"person_{field}"]:
                drift.append(f"{hid}: the deal now seats {field} "
                             f"{person.get(field)!r}, settled as {row[f'person_{field}']!r}")
            if head.get(field) != row[f"person_{field}"]:
                drift.append(f"{hid}: the tree's head has {field} {head.get(field)!r}, "
                             f"but this pass seats {row[f'person_{field}']!r}")
        # half B: the ruling left him unplaced.
        for block in spec["withdrawn"]:
            drift += assert_shape(doc, block.get("assert_instead", {}), hid)
    drift += check_refused_and_standing(seated, spec)
    return drift


def check_refused_and_standing(seated: dict[str, dict], spec: dict) -> list[str]:
    """A roof this deal ONCE seated, refused today, and standing in the tree anyway.

    T-1294. The deal seats four and once seated five. The fifth — J. W. Reed's
    hh_inf_joiner_north_02 — is refused under refusal 5, `already named in the
    town`, because six committed cards outside the hh_inf_ layer now speak that
    surname, all of them written after the roof was. The household did not go
    away with the deal that made it: the man's evidence is the poll books' and
    the press's, not this pass's, so the record stands and is the resident
    layer's. It read as OWNERLESS until this settled it, which is the whole of
    T-1294.

    Three things are asserted, because all three are ways the finding could
    silently stop being true: the household is still there with that head; the
    deal still does NOT reach it (if a refusal stops firing, the deal would seat
    it and this settlement would be describing the wrong tree); and the cards
    that fire the refusal have not all left. This gate does not assert the
    head's grade or its placement — those are the synthesizer's, which is the
    point of naming it the owner.
    """
    drift: list[str] = []
    for row in spec.get("refused_and_standing", []):
        hid = row["household"]
        if hid in seated:
            drift.append(f"{hid}: the deal seats it again — it is settled as refused "
                         f"({row['refusal']}), so the settlement is out of date")
        path = HOUSEHOLDS / f"{hid}.json"
        if not path.exists():
            drift.append(f"data/residents/households/{hid}.json is missing — a refused "
                         f"roof this deal once seated may not be dropped to tidy a pass")
            continue
        doc = json.loads(path.read_text(encoding="utf-8"))
        head = next((p for p in doc.get("persons", [])
                     if p.get("relationship") == "head"), {})
        for field in ("id", "name"):
            if head.get(field) != row[f"person_{field}"]:
                drift.append(f"{hid}: the tree's head has {field} {head.get(field)!r}, "
                             f"settled as {row[f'person_{field}']!r}")
        speakers = [c for c in row.get("named_by", [])
                    if (HOUSEHOLDS / f"{c}.json").exists()
                    and re.search(rf"\b{re.escape(row['surname'])}\b",
                                  (HOUSEHOLDS / f"{c}.json").read_text(encoding="utf-8"),
                                  re.I)]
        if not speakers:
            drift.append(f"{hid}: no card named in the settlement still says "
                         f"{row['surname']!r} — the refusal that took this roof out of "
                         f"the deal may no longer stand, so the reading needs re-taking")
    return drift


# --------------------------------------------------------------------------

def summary() -> str:
    doc = settlement()
    lines = [f"THE SETTLEMENT — {doc['ticket']}, measured {doc['measured']}"]
    for name, spec in doc["passes"].items():
        owns = spec.get("still_owns") or {}
        if not owns:
            lines.append(f"  {name}\n      owns NOTHING in the tree")
        for where, block in owns.items():
            held = len(block.get("ids") or block.get("seats") or [])
            lines.append(f"  {name}\n      owns {held} record(s) under {where}")
        for block in spec.get("withdrawn", []):
            n = len(block.get("applies_to", [])) + len(block.get("applies_to_households", []))
            lines.append(f"      {block['by']} withdrew {', '.join(block['paths'])}"
                         + (f" on {n} record(s)" if n else ""))
        for block in spec.get("reassigned", []):
            lines.append(f"      {block['to']} took {len(block['paths'])} path(s) "
                         f"on {block['structure']}")
        for block in spec.get("no_longer_owns", []):
            lines.append(f"      no longer owns {block['what']} (now {block['to']})")
        for block in spec.get("refused_and_standing", []):
            lines.append(f"      {block['household']} is refused ({block['refusal']}) "
                         f"and stands — owned by {block['owner']} ({block['settled_by']})")
    return "\n".join(lines)


def self_test() -> int:
    """Both halves must fire when broken, or neither is a gate."""
    failures = []

    def case(name, got):
        if not got:
            failures.append(name)

    case("a changed owned field is reported",
         differences({"a": {"b": 1}}, {"a": {"b": 2}}, "x"))
    case("a field only in the tree is reported",
         differences({"a": 1, "b": 2}, {"a": 1}, "x"))
    case("a field only in the derivation is reported",
         differences({"a": 1}, {"a": 1, "b": 2}, "x"))
    case("an identical record is silent",
         not differences({"a": [1, {"b": "c"}]}, {"a": [1, {"b": "c"}]}, "x"))
    case("prune removes a withdrawn path",
         prune({"a": 1, "b": 2}, ["b"]) == {"a": 1})
    case("prune walks a list with []",
         prune({"p": [{"q": 1, "r": 2}]}, ["p[].q"]) == {"p": [{"r": 2}]})
    case("a withdrawn path that vanishes is reported",
         assert_shape({}, {"occupants.value": None}, "x"))
    case("a withdrawn path whose value moved is reported",
         assert_shape({"reconstruction": {"status": "occupied"}},
                      {"reconstruction.status": "inferred_anonymous"}, "x"))
    case("a note that stops citing its ruling is reported",
         assert_shape({"resident_assignment": {"note": "no ticket here"}},
                      {"resident_assignment.note~": "T-0489"}, "x"))
    case("a withdrawal that still stands is silent",
         not assert_shape({"resident_assignment": {"note": "T-0489 owner ruling"}},
                          {"resident_assignment.note~": "T-0489"}, "x"))
    case("a retired household that reappears is reported",
         absent([RECORD], "it was retired"))
    case("a retired household that stays retired is silent",
         not absent([HOUSEHOLDS / "hh_inf_carpenter_south_01.json"], "it was retired"))

    # T-1294: the refused roof that stands anyway. Five ways it could quietly
    # stop being true, and the gate has to speak for every one of them.
    spec = settlement()["passes"]["tools/replace_invented_residents.py"]
    row = spec["refused_and_standing"][0]
    case("a refused roof that stands as settled is silent",
         not check_refused_and_standing({}, spec))
    case("a refused roof the deal seats again is reported",
         check_refused_and_standing({row["household"]: {}}, spec))
    case("a refused roof whose head has changed is reported",
         check_refused_and_standing({}, {"refused_and_standing": [
             dict(row, person_name="Somebody Else")]}))
    case("a refused roof that has left the tree is reported",
         check_refused_and_standing({}, {"refused_and_standing": [
             dict(row, household="hh_inf_not_a_household")]}))
    case("a refusal no card fires any more is reported",
         check_refused_and_standing({}, {"refused_and_standing": [
             dict(row, named_by=["hh_no_such_card"])]}))

    doc = settlement()
    case("the settlement names all three passes", len(doc["passes"]) == 3)
    case("the settlement leaves no record ownerless",
         not any("nobody" in block["to"]
                 for spec_ in doc["passes"].values()
                 for block in spec_.get("no_longer_owns", [])))
    case("the settlement cites the ruling behind it",
         any(r["ticket"] == "T-0489" for r in doc["rulings"]))

    for name in failures:
        print(f"   FAIL: {name}")
    if failures:
        print(f"   {len(failures)} assertion(s) do not fire")
        return 1
    print("   OK: the ownership contract's assertions fire on both halves")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true",
                    help="the contract's own assertions still fire when broken")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    print(summary())
    return 0


if __name__ == "__main__":
    sys.exit(main())
