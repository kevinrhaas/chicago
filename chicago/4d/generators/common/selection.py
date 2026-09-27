"""Which structures a `--only` selection names, and what a name nobody answers to costs.

TICKET T-1652 (filed twice the same day — T-1650 is the same finding, from a run
that had just been bitten by it). `tools/bake.sh` documents three forms in its own
usage, and has since the comma form was written into it:

    tools/bake.sh --only <id>     build one structure
    tools/bake.sh --only a,b,c    build several, in one Blender start-up

`bake.sh` passes `"$@"` straight through, so the second line is a promise made
about `generators/build.py`. What build.py did with it was

    if args.only and st["id"] != args.only:
        continue

— one string compared for EQUALITY against 422 ids, none of which is
`"a,b,c"`. So the documented form matched nothing, skipped every record, printed
`0 asset(s) built` and exited 1. Nothing said the selection was the problem; the
run that filed this ticket read that as a build failure, and the transcript of a
re-family lap on 2026-09-26 shows ten separate one-id Blender start-ups where one
would have done.

Two silences, not one. `--only ""` was FALSY, so an empty selection — a shell
variable that did not expand — fell through the `if` and baked the whole town:
twenty minutes for a command whose author had asked for one building.

So the rule is here, in one bpy-free place, with a self-test that fires on each
of its assertions. It is in `common/` for the reason `phases.py` gives: that is
where a rule more than one caller reads belongs, and nothing else hangs on it.
`generators/build.py` is the caller that matters; `tools/check_only_selection.py`
is the gate that holds this against bake.sh's usage, so the documented form and
the implemented form cannot drift apart again.

THE SHAPE OF THE ANSWER: a selection either names structures that exist, or it
is REFUSED IN WRITING before a single mesh is generated. A selection is not a
filter — a filter that matches nothing is empty, which is a fine answer to a
question about data, and a terrible one to an instruction. `--only` is an
instruction, and an instruction naming something that does not exist is a
mistake to be reported, not a set to be intersected.
"""

from __future__ import annotations

import argparse
import difflib

# The exit status a refused selection earns. 2, not 1: `1` is build.py's
# "nothing was built", which is a fact about the data (every named record's
# phase is out of the scene window, say) and can be a correct answer. A refusal
# is a fact about the COMMAND, and the caller reading the status should be able
# to tell those apart. It is the status the datum refusal already uses.
REFUSED = 2


def parse_only(raw: str | None) -> list[str] | None:
    """The ids a `--only` value names: in the order written, without duplicates.

    `None` means no selection was made at all (build everything the scene
    resolves). An empty LIST means a selection was made and named nothing,
    which is a refusal — see `refusal()`. Those two are different things and
    the caller must not conflate them, which is exactly what `if args.only`
    did.
    """
    if raw is None:
        return None
    ids: list[str] = []
    for part in raw.split(","):
        one = part.strip()
        if one and one not in ids:
            ids.append(one)
    return ids


def refusal(requested: list[str] | None, available: list[str]) -> str | None:
    """The message refusing this selection, or None if every id names a record.

    `available` is every structure id on disk. The hint is a courtesy and is
    load-bearing for nothing: the refusal stands whether or not a near miss is
    found.
    """
    if requested is None:
        return None
    if not requested:
        return ("--only was given no id. An empty selection is not 'build "
                "everything' — drop the flag for that, or name the structures "
                "to build (a comma list is allowed: --only a,b,c).")
    known = set(available)
    missing = [one for one in requested if one not in known]
    if not missing:
        return None
    lines = [f"--only names {len(missing)} id(s) that no structure record answers to:"]
    for one in missing:
        near = difflib.get_close_matches(one, available, n=3, cutoff=0.6)
        hint = f"  did you mean: {', '.join(near)}" if near else ""
        lines.append(f"  {one}{hint}")
    lines.append(f"{len(available)} records live in data/structures/. "
                 "Nothing was built; no manifest was written.")
    return "\n".join(lines)


def selects(requested: list[str] | None, structure_id: str) -> bool:
    """Is this record in the selection? No selection selects everything."""
    return requested is None or structure_id in requested


# ----------------------------------------------------------------------- self-test

def self_test() -> int:
    fails: list[str] = []

    def ok(label: str) -> None:
        print(f"  ok    {label}")

    def want(label: str, got, expected) -> None:
        if got == expected:
            ok(label)
        else:
            fails.append(f"{label}: got {got!r}, wanted {expected!r}")

    town = ["beaubien_barn", "brickyard_north_side", "green_tree_tavern", "west_046"]

    print("\n  -- the value the flag was given")
    want("no flag is no selection", parse_only(None), None)
    want("one id is a selection of one", parse_only("west_046"), ["west_046"])
    want("the documented comma form names each id",
         parse_only("beaubien_barn,brickyard_north_side,west_046"),
         ["beaubien_barn", "brickyard_north_side", "west_046"])
    want("spaces around a comma are the shell's, not an id's",
         parse_only(" beaubien_barn , west_046 "), ["beaubien_barn", "west_046"])
    want("a trailing or doubled comma names nothing extra",
         parse_only("west_046,,"), ["west_046"])
    want("an id written twice is built once",
         parse_only("west_046,west_046"), ["west_046"])
    want("an empty value is an empty selection, NOT absence of one",
         parse_only(""), [])
    want("…and that is the distinction `if args.only` could not make",
         parse_only("") is None, False)

    print("\n  -- what a selection nobody answers to costs")
    want("a selection of real ids is not refused",
         refusal(["west_046", "beaubien_barn"], town), None)
    want("no selection is not refused", refusal(None, town), None)

    empty = refusal([], town)
    if empty and "not 'build everything'" in empty:
        ok("an empty selection is refused, and says it is not 'build everything'")
    else:
        fails.append(f"empty selection: not refused ({empty!r})")

    # THE BUG ITSELF, as the ticket describes it: the whole comma string arrived
    # as one id. It must now be refused by name rather than silently matching
    # nothing — and it is the one case that cannot be allowed to regress.
    whole = refusal(["beaubien_barn,brickyard_north_side"], town)
    if whole and "beaubien_barn,brickyard_north_side" in whole:
        ok("an unsplit comma string is refused BY NAME (the T-1652 failure)")
    else:
        fails.append(f"unsplit comma string: not refused ({whole!r})")

    typo = refusal(["beaubien_bran"], town)
    if typo and "did you mean" in typo and "beaubien_barn" in typo:
        ok("a near miss is named in the refusal")
    else:
        fails.append(f"near miss: no hint offered ({typo!r})")

    far = refusal(["zzzzzzzz"], town)
    if far and "zzzzzzzz" in far and "did you mean" not in far:
        ok("…and an id near nothing is refused without a guess")
    else:
        fails.append(f"far miss: guessed anyway ({far!r})")

    mixed = refusal(["west_046", "not_a_roof"], town)
    if mixed and "not_a_roof" in mixed and "west_046" not in mixed:
        ok("a part-real selection is refused whole, naming only the missing")
    else:
        fails.append(f"part-real selection: {mixed!r}")

    print("\n  -- which records the selection then builds")
    want("no selection builds every record", selects(None, "west_046"), True)
    want("a named record is built", selects(["west_046"], "west_046"), True)
    want("an unnamed record is skipped", selects(["west_046"], "beaubien_barn"), False)
    want("every id of a comma list is built",
         [selects(parse_only("beaubien_barn,west_046"), one) for one in town],
         [True, False, False, True])
    # The equality comparison build.py used, stated as what it did: the comma
    # form selected NO record at all. If this ever passes, the bug is back.
    want("…where the equality comparison selected none of them",
         any(one == "beaubien_barn,west_046" for one in town), False)

    print()
    for f in fails:
        print(f"  FAIL  {f}")
    print("ONLY-SELECTION SELF-TEST " + ("PASS" if not fails else "FAIL"))
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--self-test", action="store_true",
                    help="break each assertion in memory and prove it fires")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
