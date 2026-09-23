#!/usr/bin/env python3
"""Audit every graded value in the dataset against what the three levels MEAN.

The three levels are not a scale of how sure we feel. They name three different
acts, and each one implies things that can be checked:

  attested       A source STATES this value.
                 -> It must cite at least one source.
                 -> Its own note must not say the sources are silent on it.

  inferred       Reasoned from evidence about THIS PARTICULAR THING — a described
                 location, a measured lot, a neighbouring record.
                 -> There must be reasoning: a note saying what was reasoned from.
                 -> It cannot sit on a structure that is itself an invention,
                    because then there is no "this particular thing" to reason about.

  reconstructed  Invented to fill a demonstrable need; no source speaks to it.
                 -> It MAY cite sources: an invention bounded by a source is
                    defensible rather than arbitrary, and the bound is worth
                    showing. So a citation here is not an error.
                 -> But if a source flatly states the value, the grade is too low.

The rule that matters most, and the one this was written for: EVERY VALUE ON AN
INVENTED STRUCTURE IS RECONSTRUCTED. A typology — what a shoemaker's shop of the
period was ordinarily like — is evidence about a KIND, not about a building, and
the building is not there. Grading those as `inferred` made 158 structures that
never existed render solid in the confidence view while the Exchange Coffee
House, a real tavern with a name and a keeper, rendered as a dithered ghost
because its wall height is honestly unknown. The view told the visitor the exact
opposite of the truth.

Run bare to report; `--strict` exits non-zero on any error, which is how
tools/check.sh consumes it.
"""
import argparse
import json
import pathlib
import re
import sys
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[1]

# The vocabulary, weakest claim last.
ATTESTED, INFERRED, RECONSTRUCTED = "attested", "inferred", "reconstructed"
LEVELS = (ATTESTED, INFERRED, RECONSTRUCTED)
RANK = {ATTESTED: 0, INFERRED: 1, RECONSTRUCTED: 2}

# Phrases that mean "no source says this". A value carrying one of these cannot
# be attested, whatever its chip says — the note is the record contradicting
# itself in its own words.
SILENCE = re.compile(
    r"no source|not stated|nothing (?:in|states)|does not (?:state|say|give)|"
    r"unrecorded|no record|nobody (?:states|recorded)|is not recorded|"
    r"invented|hypothesi[sz]ed|conjectur|assumed|typical of|ordinarily",
    re.I)

# An invented structure. These prefixes are the programme's own naming, and the
# programme is the thing that invents buildings.
INVENTED_ID = re.compile(r"^(recon_|inf_)")


def load_sidecars():
    out = []
    for p in sorted((ROOT / "data" / "sidecars").rglob("*.json")):
        try:
            out.append((p, json.loads(p.read_text())))
        except json.JSONDecodeError as e:
            out.append((p, {"__unparseable__": str(e)}))
    return out


def graded_blocks(doc):
    """Yield (path, block) for every dict carrying a `confidence`."""
    def walk(node, path):
        if isinstance(node, dict):
            if isinstance(node.get("confidence"), str):
                yield path, node
            for k, v in node.items():
                yield from walk(v, f"{path}.{k}" if path else k)
        elif isinstance(node, list):
            for i, v in enumerate(node):
                yield from walk(v, f"{path}[{i}]")
    yield from walk(doc, "")


def audit():
    errors, warnings, counts = [], [], Counter()
    for path, doc in load_sidecars():
        rel = path.relative_to(ROOT)
        if "__unparseable__" in doc:
            errors.append(f"{rel}: will not parse — {doc['__unparseable__']}")
            continue
        sid = doc.get("id") or doc.get("structure_id") or rel.stem
        invented = bool(INVENTED_ID.match(sid))

        for where, block in graded_blocks(doc):
            conf = block["confidence"]
            counts[conf] += 1
            note = block.get("note") or ""
            sources = block.get("sources") or []

            if conf not in LEVELS:
                errors.append(f"{sid} {where}: '{conf}' is not one of {LEVELS}")
                continue

            # THE RULE. Nothing on an invented structure can outrank the invention
            # that put it there.
            if invented and RANK[conf] < RANK[RECONSTRUCTED]:
                errors.append(
                    f"{sid} {where}: graded '{conf}' on an INVENTED structure. "
                    f"A typology is evidence about a kind, not about this building — "
                    f"and this building is not there.")
                continue

            if conf == ATTESTED:
                if not sources:
                    errors.append(f"{sid} {where}: attested with no source. "
                                  f"Attested means a source states it; name the source "
                                  f"or drop the grade.")
                # ADVISORY, not an error, and the distinction was earned. This
                # fired on 25 values and every one was a false positive, because
                # the notes in this dataset are long and careful: Peck's store
                # says its loft is "THE SINGLE MOST VIVID DOCUMENTED FACT ABOUT
                # THIS BUILDING" and then declines to claim what the loft was
                # floored with. A phrase saying some ADJACENT detail is unrecorded
                # is exactly the honesty this project is for, and no regex can
                # tell which attribute a clause 200 words into a note refers to.
                # So it prompts a human to look; it does not return a verdict.
                m = SILENCE.search(note)
                if m:
                    warnings.append(f"{sid} {where}: attested, and its note contains "
                                    f"'{m.group(0)}' — worth checking that the phrase is "
                                    f"about some other detail and not about this value.")

            # Reasoning lives under `note` on a structure attribute and under
            # `notes` (a list) on a terrain claim. Checking only the first
            # reported all twelve reasoned river reaches as unreasoned.
            reasoning = note.strip() or " ".join(
                str(n) for n in (block.get("notes") or []) if n).strip()
            if conf == INFERRED and not reasoning:
                # An inference with no stated reasoning is indistinguishable from
                # an invention, and this project's whole claim is that it can tell
                # the difference.
                errors.append(f"{sid} {where}: inferred with no reasoning recorded. "
                              f"Say what it was reasoned from, or grade it "
                              f"reconstructed.")

            if conf == RECONSTRUCTED and re.search(
                    r"\bthe source states\b|\bAndreas states\b|\bexplicitly states\b", note, re.I):
                warnings.append(f"{sid} {where}: reconstructed, but the note says a source "
                                f"states it — this may be graded too low.")
    return errors, warnings, counts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true",
                    help="exit non-zero on any error (how check.sh runs it)")
    args = ap.parse_args()

    errors, warnings, counts = audit()
    total = sum(counts.values())
    print(f"   {total} graded value(s): "
          + ", ".join(f"{counts.get(k, 0)} {k}" for k in LEVELS))
    for w in warnings[:20]:
        print(f"   warn: {w}")
    if len(warnings) > 20:
        print(f"   ... and {len(warnings) - 20} more warning(s)")
    for e in errors[:40]:
        print(f"   ERROR: {e}")
    if len(errors) > 40:
        print(f"   ... and {len(errors) - 40} more error(s)")
    if errors:
        print(f"   {len(errors)} error(s)")
        return 1 if args.strict else 0
    print("   every graded value is consistent with what its level means")
    return 0


if __name__ == "__main__":
    sys.exit(main())
