#!/usr/bin/env python3
"""A store placed by counting doors off a corner claims a POSITION and never a lot.

T-0384, and the gate the owner's ruling of 2026-08-30 is owed. `docs/CORNER-ORDINAL.md`
is the policy in prose; this is the part of it a later run cannot quietly undo.

The ruling has two halves and only one of them is a reading. *"One door from Dearborn
street"* is an ordinal off the corner rather than a reach of the street — that half lives
in `tools/compile_register.resolve_anchor`, which turns the phrase into a `corner_ordinal`
anchor and an action that places. The other half is a LIMIT: **an ordinal is still not a
lot.** It fixes a position in a sequence along a face; it names no platted lot and may not
claim one. A limit written only in prose is a limit that expires the first time somebody
reads the prose quickly, so the record states it in a field — a `lot_claim` block —
`tools/plat_occupancy.py` reads that field, and this file proves the whole chain holds.

Four assertions, and each one is a way the limit could stop being true:

**1. The declaration and the reading name the same records.** Every structure carrying
`lot_claim` is one the register places by an ordinal, and every ordinal-placed record
standing in the town carries the declaration. Both directions, because either alone
permits the drift: a declaration on a record nothing places is a field that has stopped
meaning anything, and an ordinal placement with no declaration is the limit simply
missing. An ordinal business that is not built yet is REPORTED, not failed — the register
reads the papers and the town is built from it slowly, and a business waiting for a run is
the normal state.

**2. The declaration says what it must say.** `claims_lot: false`, `lot: null`, a
`placement_rule` in the vocabulary, a note that gives a reason — and no OTHER field
anywhere in the record naming a lot. That last test is the street-face adoptions' own
(`tools/adopt_street_faces.py`), for the same reason: the failure to guard against is not
a lot field with a value in it, it is a lot field with a different NAME.

**3. The declaration bars nothing.** Computed rather than trusted: the map of lots barred
to a new roof (`plat_occupancy.exclusive_lots`) is derived twice, once with the declaring
records in the town and once with them out of it, and the two must agree. A lot that is
barred WITH them and free without them is the transparency broken — which is exactly the
failure PR #514 hit, where standing Holbrook beside the Chicago American's office switched
off the business-front clause and the block generator was refused a roof it had been
dealt. The one permitted difference is a lot whose ONLY holders are declaring records:
that lot reads as taken, which is the conservative direction the policy chose on purpose
and says so.

**4. The metres are admitted.** How far one door is from a corner is this project's
arithmetic, not the paper's, and the ruling says so in terms. So a declaring record's
position may never be graded `attested`, and some liberty must cover the record — the
project's standing way of saying *we made this up*. L215 is that liberty today and owns
the door-gap rule (a neighbouring front stands 3.048 m clear of the wall it neighbours).

    tools/measure_corner_ordinals.py            the report, and the corpus sweep
    tools/measure_corner_ordinals.py --gate     the four assertions
    tools/measure_corner_ordinals.py --self-test
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import plat_occupancy                                       # noqa: E402
import compile_register                                     # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
STRUCTURES = ROOT / "data" / "structures"
REGISTER = ROOT / "data" / "research" / "newspapers" / "register_1835.json"
EXTRACTED = ROOT / "data" / "research" / "newspapers" / "extracted"
LIBERTIES = ROOT / "data" / "liberties.json"
LOTS = ROOT / "data" / "traces" / "vectors" / "thompson_lots.json"
DATUM = ROOT / "data" / "datum.json"

PLACEMENT_RULES = ("corner_ordinal",)
# A field whose NAME says lot, anywhere in a declaring record, other than the declaration's
# own `lot: null`. The adoptions' gate guards the same way and for the same reason.
LOT_NAMED = re.compile(r"lot", re.I)


# ---------------------------------------------------------------- reading the tree

def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def records() -> dict[str, dict]:
    return {p.stem: load(p) for p in sorted(STRUCTURES.glob("*.json"))}


def declaring(recs: dict[str, dict]) -> dict[str, dict]:
    """{structure_id: its lot_claim block} for every record that carries one."""
    return {rid: r["lot_claim"] for rid, r in recs.items() if r.get("lot_claim")}


def ordinal_businesses(register: dict) -> list[dict]:
    return [b for b in register["businesses"]
            if b["anchor"]["kind"] == "corner_ordinal"]


# ---------------------------------------------------------------- the four assertions

def linkage_faults(ordinals: list[dict], declared: set[str],
                   known: set[str]) -> tuple[list[str], list[str]]:
    """Assertion 1 — the reading and the declaration name the same records.

    Returns (faults, waiting). A `corner_ordinal` business resolved to a committed
    structure must have declared; one that is not built yet is `waiting` and is reported.
    """
    faults, waiting, placed = [], [], set()
    for b in ordinals:
        target = b["action_target"] if b["action"] == "enrich_existing" else None
        if target and target in known:
            placed.add(target)
            if target not in declared:
                faults.append(
                    "%s is placed by an ordinal off a corner and stands as %s, and that "
                    "record declares no `lot_claim` — an ordinal names no lot and the "
                    "record has to say so (docs/CORNER-ORDINAL.md)" % (b["id"], target))
        else:
            waiting.append("%s reads as an ordinal off a corner and is not built yet "
                           "(action %s)" % (b["id"], b["action"]))
    for rid in sorted(declared - placed):
        faults.append(
            "%s declares `lot_claim` and no register business places it by an ordinal off "
            "a corner — the declaration has stopped meaning anything" % rid)
    return faults, waiting


def shape_faults(rid: str, record: dict) -> list[str]:
    """Assertion 2 — the declaration says what it must, and grows no lot field."""
    claim = record.get("lot_claim") or {}
    out = []
    if claim.get("claims_lot") is not False:
        out.append("%s: `claims_lot` is %r and the only value this block may carry is "
                   "false" % (rid, claim.get("claims_lot")))
    if claim.get("lot") is not None:
        out.append("%s: the declared lot is %r — a record that claims no lot may not name "
                   "one" % (rid, claim.get("lot")))
    if claim.get("placement_rule") not in PLACEMENT_RULES:
        out.append("%s: placement rule %r is not one of %s"
                   % (rid, claim.get("placement_rule"), "/".join(PLACEMENT_RULES)))
    if not (claim.get("note") or "").strip():
        out.append("%s: the declaration gives no reason" % rid)

    def walk(node, path):
        if isinstance(node, dict):
            for key, value in node.items():
                if LOT_NAMED.search(key) and path != ("lot_claim",):
                    out.append("%s: the record has grown a lot-named field at %s — a "
                               "record that claims no lot may not carry one under another "
                               "name" % (rid, ".".join(path + (key,))))
                walk(value, path + (key,))
        elif isinstance(node, list):
            for i, value in enumerate(node):
                walk(value, path + ("%d" % i,))

    walk({k: v for k, v in record.items() if k != "lot_claim"}, ())
    return out


def transparency(declared: set[str]) -> dict:
    """Assertion 3 — derive the barred-lot map with the declaring records and without."""
    grid, datum = load(LOTS), load(DATUM)
    with_them = plat_occupancy.exclusive_lots(grid, datum)
    without = plat_occupancy.exclusive_lots(grid, datum, exclude=frozenset(declared))
    held = plat_occupancy.lot_holders(grid, datum)
    return {"with": with_them, "without": without, "held": held}


def transparency_faults(measured: dict, declared: set[str]) -> tuple[list[str], list[str]]:
    """(faults, conceded) — a barred lot the declaration created, and the one exception."""
    def barred(m):
        return {(block, index) for block, lots in m.items() for index in lots}

    faults, conceded = [], []
    with_them, without = barred(measured["with"]), barred(measured["without"])
    for block, index in sorted(without - with_them):
        faults.append(
            "%s lot %d is barred to a new roof only when the no-lot-claim records are "
            "TAKEN OUT of the town — a declaration may never free a lot, and this one "
            "does" % (block, index))
    for block, index in sorted(with_them - without):
        holders = measured["held"].get(block, {}).get(index, [])
        if set(holders) <= declared:
            conceded.append(
                "%s lot %d is held only by no-lot-claim record(s) (%s) and reads as taken "
                "— the conservative half of the policy, and it costs nothing today"
                % (block, index, ", ".join(sorted(holders))))
        else:
            faults.append(
                "%s lot %d is barred to a new roof BECAUSE a no-lot-claim record stands "
                "on it (holders: %s) — the declaration is meant to bar nothing"
                % (block, index, ", ".join(sorted(holders))))
    return faults, conceded


def admission_faults(declared: set[str], recs: dict[str, dict],
                     liberties: dict) -> list[str]:
    """Assertion 4 — the metres are this project's, and a liberty says so."""
    # `covers` is compiled to a token dict per claim (domain/structure/phase/aspect);
    # only the structure it names is wanted here.
    covered = set()
    for entry in liberties.get("liberties", []):
        for token in entry.get("covers") or []:
            covered.add(token.get("structure") if isinstance(token, dict)
                        else str(token).split(".")[0])
    covered.discard(None)
    out = []
    for rid in sorted(declared):
        for phase in recs[rid]["phases"]:
            grade = (phase.get("position") or {}).get("confidence")
            if grade == "attested":
                out.append(
                    "%s/%s: the position is graded `attested`, and how far one door is "
                    "from a corner is this project's arithmetic and never the paper's"
                    % (rid, phase["id"]))
        if rid not in covered:
            out.append("%s: no liberty covers this record, so the metres between its door "
                       "and the corner are admitted nowhere a visitor can read them" % rid)
    return out


# ---------------------------------------------------------------- the corpus sweep

# T-0771 asked TWO things of this sweep, and both are counted rather than assumed.
#
# THE SPLIT. An ordinal counts doors from a CROSSING, so the reader needs two streets;
# and where a claim carries them, one is usually in the `anchor` and the other in the
# placement's own `street` field. Clark, Filer & Co. read "the corner of Randolph st."
# in the anchor and "South Water Street" in `street`, and the question T-0771 opened was
# whether an anchor naming one street of a crossing may take the second from there.
# It may, it always has, and `compile_register.ordinal_off_a_corner`'s third test IS
# that pairing — the doubt was about the code and not about the corpus. So this counts
# the shape: how many `n doors` claims are split that way, and how many instead carry
# both streets in the anchor.
#
# THE SUPPLY. The other half of T-0771, and the fault that actually held Clark, Filer &
# Co. off the ground for a week. A square bracket is the reading pass saying it could
# not see the word, and this project does not spend a supply — so a phrase whose count
# or cross street falls inside brackets is refused, correctly. What is worth COUNTING is
# how often that happens, because a refusal nobody can see is a refusal nobody fixes.
# Eleven claims across the corpus print an `n doors` phrase the reader cannot reach for
# this reason. It is not a licence to unbracket any of them: where another printing of
# the SAME reading sets the sentence whole, `compile_gazetteer.absorb_reading` keeps
# that printing, and where none does the phrase stays refused.
BRACKETED = re.compile(r"\[[^\]]*\]")


def opened(text: str) -> str:
    """A transcription with its bracketed supplies opened — for COUNTING only."""
    return BRACKETED.sub(lambda m: m.group(0)[1:-1], text)


def sweep() -> dict:
    """Every `n doors from` phrase the corpus prints, and what the reading does with it.

    The ticket asked how many other claims are now readable. The answer is derived here
    rather than counted by hand, so a later reading pass that adds one moves the number.
    """
    town = compile_register.read_town()
    rows, hidden = [], []
    for path in sorted(EXTRACTED.glob("*.json")):
        for claim in load(path)["claims"]:
            placement = ((claim.get("business") or {}).get("placement") or {})
            match, field = None, None
            for field in ("offset_normalized", "offset_text"):
                match = compile_register.ORDINAL_DOOR.search(
                    str(placement.get(field) or ""))
                if match:
                    break
            if not match:
                # A phrase a SUPPLY hides: no `n doors` reading today, and one the
                # moment the brackets are opened. Counted, never opened for real.
                normalised = str(placement.get("offset_normalized") or "")
                if BRACKETED.search(normalised) and \
                        compile_register.ORDINAL_DOOR.search(opened(normalised)):
                    hidden.append({
                        "issue": path.stem, "claim": claim["id"],
                        "business": (claim.get("business") or {}).get("name"),
                        "phrase": " ".join(normalised.split())[:70]})
                continue
            reference = compile_register.streets_in(town, match.group(3), True)
            along = compile_register.streets_in(town, placement.get("street"), False)
            corner = bool(compile_register.CORNER.search(str(placement.get(field) or "")))
            pair = (len(reference) == 1 and len(along) == 1
                    and reference[0] != along[0] and not corner)
            # A pair of streets is not a corner until the plat says they meet (T-0771).
            crosses = pair and compile_register.streets_cross(town, along[0],
                                                              reference[0])
            readable = pair and crosses
            # The crossing's two streets, split between the anchor and `street` — the
            # shape T-0771 asked to have counted. Measured on every row, readable or
            # not, because the question is about the CORPUS and not about what resolves.
            in_anchor = compile_register.streets_in(town, placement.get("anchor"), True)
            split = (len(reference) == 1 and len(along) == 1 and reference[0] != along[0]
                     and in_anchor == reference and along[0] not in in_anchor)
            rows.append({
                "issue": path.stem, "claim": claim["id"],
                "business": (claim.get("business") or {}).get("name"),
                "phrase": " ".join(match.group(0).split())[:70],
                "reference": reference, "along": along,
                "reads_as_a_corner_first": corner,
                "readable_as_an_ordinal": readable,
                "streets_split_across_anchor_and_street": split,
                "named_streets_do_not_cross": bool(pair and not crosses),
            })
    return {"claims": rows,
            "total": len(rows),
            "readable": sum(1 for r in rows if r["readable_as_an_ordinal"]),
            "corner_first": sum(1 for r in rows if r["reads_as_a_corner_first"]),
            "split": sum(1 for r in rows
                         if r["streets_split_across_anchor_and_street"]),
            "parallel": sum(1 for r in rows if r["named_streets_do_not_cross"]),
            "hidden_by_a_supply": hidden,
            "landmark_or_unresolved": sum(
                1 for r in rows
                if not r["readable_as_an_ordinal"] and not r["reads_as_a_corner_first"])}


# ---------------------------------------------------------------- report and gate

def gate(quiet: bool = False) -> int:
    recs = records()
    register = load(REGISTER)
    declared = set(declaring(recs))
    ordinals = ordinal_businesses(register)

    faults, waiting = linkage_faults(ordinals, declared, set(recs))
    for rid in sorted(declared):
        faults += shape_faults(rid, recs[rid])
    measured = transparency(declared)
    t_faults, conceded = transparency_faults(measured, declared)
    faults += t_faults
    faults += admission_faults(declared, recs, load(LIBERTIES))

    if not quiet or faults:
        print("   %d business(es) read as an ordinal off a corner; %d record(s) declare "
              "`lot_claim`" % (len(ordinals), len(declared)))
        for line in waiting + conceded:
            print("   note: %s" % line)
    for line in faults:
        print("   %s" % line)
    if not faults:
        print("   4 assertions fire: the reading and the declaration agree, the "
              "declaration is well formed, it bars no lot, and the metres are admitted")
    return 1 if faults else 0


def report() -> str:
    recs = records()
    register = load(REGISTER)
    declared = set(declaring(recs))
    lines = ["ORDINALS OFF A CORNER — docs/CORNER-ORDINAL.md, the owner's ruling of "
             "2026-08-30", ""]
    for b in ordinal_businesses(register):
        o = b["anchor"]["ordinal"]
        lines.append("  %-34s %d door%s %s of/from %s, along %s -> %s %s"
                     % (b["id"], o["count"], "" if o["count"] == 1 else "s",
                        o["direction"] or "", o["from_street"], o["along"],
                        b["action"], b["action_target"] or ""))
        lines.append("      %r" % o["phrase"])
    lines += ["", "  declaring `lot_claim`: %s" % (", ".join(sorted(declared)) or "none"),
              ""]
    s = sweep()
    lines += ["THE CORPUS SWEEP — every `n doors` phrase in %d extraction file(s)"
              % len(list(EXTRACTED.glob("*.json"))), "",
              "  %-58s %d" % ("claims carrying an `n doors` phrase", s["total"]),
              "  %-58s %d" % ("— read as a corner of two streets first", s["corner_first"]),
              "  %-58s %d" % ("— a landmark hop, or naming no platted street",
                              s["landmark_or_unresolved"]),
              "  %-58s %d" % ("— readable as an ordinal off a corner", s["readable"]),
              "  %-58s %d" % ("— the crossing split anchor/`street` (T-0771)",
                              s["split"]),
              "  %-58s %d" % ("— refused: the two streets named never meet (T-0771)",
                              s["parallel"]), ""]
    for row in s["claims"]:
        if row["readable_as_an_ordinal"]:
            lines.append("    %s#%s  %s — %r"
                         % (row["issue"], row["claim"], row["business"], row["phrase"]))
    for row in s["claims"]:
        if row["named_streets_do_not_cross"]:
            lines.append("    %s#%s  %s — %r"
                         % (row["issue"], row["claim"], row["business"], row["phrase"]))
            lines.append("        %s and %s are parallel: the plat holds no such corner."
                         % (row["along"][0], row["reference"][0]))
    lines += ["",
              "  %-58s %d" % ("phrases a bracketed supply hides from the reader",
                              len(s["hidden_by_a_supply"])), ""]
    for row in s["hidden_by_a_supply"]:
        lines.append("    %s#%s  %s — %r"
                     % (row["issue"], row["claim"], row["business"], row["phrase"]))
    return "\n".join(lines)


# ---------------------------------------------------------------- self-test

def self_test() -> int:
    """Each assertion, fed the break it exists to catch."""
    failures = []

    def fires(label, got):
        if not got:
            failures.append(label)
        print("  %s: %s" % ("fires" if got else "SILENT", label))

    good = {"claims_lot": False, "lot": None, "placement_rule": "corner_ordinal",
            "note": "an ordinal is not a lot"}
    base = {"id": "x", "phases": [{"id": "p", "position": {"confidence": "inferred"}}],
            "lot_claim": dict(good)}

    fires("a declaration that has stopped saying `claims_lot: false`",
          shape_faults("x", dict(base, lot_claim=dict(good, claims_lot=True))))
    fires("a declaration that has filled the lot it declares",
          shape_faults("x", dict(base, lot_claim=dict(good, lot="blk_x:0"))))
    fires("a placement rule outside the vocabulary",
          shape_faults("x", dict(base, lot_claim=dict(good, placement_rule="vibes"))))
    fires("a declaration with no reason on it",
          shape_faults("x", dict(base, lot_claim=dict(good, note="  "))))
    fires("a record that has grown a lot field under another name",
          shape_faults("x", dict(base, phases=[{"id": "p", "plat_lot": 3}])))
    fires("…and the well-formed record is silent",
          not shape_faults("x", base))

    fires("an ordinal placement whose record declares nothing",
          linkage_faults([{"id": "b", "action": "enrich_existing",
                           "action_target": "x"}], set(), {"x"})[0])
    fires("a declaration no ordinal reading places",
          linkage_faults([], {"orphan"}, {"orphan"})[0])
    unbuilt = linkage_faults([{"id": "b", "action": "new_building",
                               "action_target": "a+b"}], set(), {"x"})
    fires("…and a business not built yet is reported, not failed",
          unbuilt[0] == [] and len(unbuilt[1]) == 1)

    measured = {"with": {"blk": {0: "x"}}, "without": {},
                "held": {"blk": {0: ["x", "other"]}}}
    fires("a lot barred BECAUSE a no-lot-claim record stands on it",
          transparency_faults(measured, {"x"})[0])
    conceded_only = transparency_faults({"with": {"blk": {0: "x"}}, "without": {},
                                         "held": {"blk": {0: ["x"]}}}, {"x"})
    fires("…and a lot held only by declaring records is conceded, not failed",
          conceded_only[0] == [] and len(conceded_only[1]) == 1)
    fires("a declaration that FREES a lot the town bars without it",
          transparency_faults({"with": {}, "without": {"blk": {0: "y"}},
                               "held": {}}, {"x"})[0])

    liberties = {"liberties": [{"covers": [
        {"domain": "structure", "structure": "x", "phase": "p", "aspect": "footprint"}]}]}
    fires("an ordinal placement graded `attested`",
          admission_faults({"x"}, {"x": {"phases": [
              {"id": "p", "position": {"confidence": "attested"}}]}}, liberties))
    fires("an ordinal placement no liberty admits",
          admission_faults({"x"}, {"x": {"phases": [
              {"id": "p", "position": {"confidence": "inferred"}}]}},
              {"liberties": []}))
    fires("…and the admitted, inferred record is silent",
          not admission_faults({"x"}, {"x": base}, liberties))

    for line in failures:
        print("   SILENT: %s" % line)
    print("SELF-TEST %s — %d case(s)"
          % ("FAIL" if failures else "PASS", 16))
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gate", action="store_true")
    parser.add_argument("--self-test", action="store_true", dest="self_test")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if args.gate:
        return gate(quiet=args.quiet)
    print(report())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
