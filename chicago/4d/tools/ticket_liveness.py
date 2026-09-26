#!/usr/bin/env python3
"""THE ONE WALK, AND THE QUESTION A CLOSING PR NEVER ASKED (T-1581).

Owner, 2026-09-25, after `dev` went red three times in one afternoon with no code
wrong: *closing a leaf ticket can strand work owned by its split ancestors, and
`ticket.mjs done` and the gate must catch it before the PR merges, not after.*

THE SHAPE, WHICH WAS THE SAME ALL THREE TIMES. A work pointer — a research unit's
`ticket`, a ruling's `ticket`, a bucket's `owning_ticket` — names a ticket that has
since been `split`. A split is a grouping record, so it is live exactly while some
descendant of it is live. The last live descendant then closes SOMEWHERE ELSE, in a
PR that never reads the pointer, and the ancestor goes dead on `dev` the instant the
tickets repo settles the close. Whoever gates next inherits the red:

  1. #40 (T-1448) merged 16:13Z — last live leaf of T-1189 -> T-1434 -> T-1448.
     Twelve resident cohort units deferred to T-1189. Four gate steps red for 2.5h.
  2. #43 (T-1560) merged 17:50Z — last DIRECT piece of T-1556, while T-1564 stood
     open two levels down under the split T-1559. The order book's programme gate red.
  3. #49 (T-1523) — 272 landholding units on T-1198, held live by T-1523 alone. It
     was written onto the ticket by hand, so a person had to read a NOTE for it.

WHY THE THREE EXISTING GUARDS ALL MISS IT.

  * `ticket.mjs`'s NOTE (T-1237) looks ONE level up, at the closing ticket's own
    `parent`, and only prints. Case 1's pointer was a grandparent; case 2's was a
    grandparent through a split piece.
  * `done --pr` sets `review`, and the tickets repo's settle workflow sets `done`
    when the PR MERGES. So the state that breaks `dev` arrives after the PR's gate
    has already passed — the gate read the ticket as `review`, which is live.
  * The ledger and the order book each grew their own walk of the same relation.
    They are not the same code, so a fix to one (T-1421's fixed point) did not reach
    the other, and T-1575 had to re-derive descent in the book two months later.

WHAT THIS FILE IS. The walk, once, and the two callers that had their own:

    live_pieces_of(...)   the descent — T-1575's rule in the order book
    derived_states(...)   the ascent   — T-1237/T-1421's `split_live` in the ledger

They are one relation read in two directions, and both are built here on one
predicate. What they do NOT share is WHICH FLAT STATES COUNT AS LIVE, and that
difference is deliberate and is kept: the research ledger requires an OPEN ticket to
own an unresolved unit (a blocked ticket is not somebody working), while the order
book's work-order gate counts a blocked ticket as live because it is on the board and
unblocks. So the leaf set is a parameter, and only the walk over `split` is shared.

AND THE QUESTION ITSELF: `strands()` asks, for a set of tickets a PR is about to
close, which ancestors would be left with no live descendant at any depth. `python3
tools/ticket_liveness.py --closing T-NNNN` then scans the committed ledger, the
ruling registers and the order book for pointers at those ancestors, using those
tools' own readers rather than a grep, and exits non-zero naming each. `ticket.mjs
done` runs it before it writes, and `check.sh` runs it for the tickets the branch
carries — so the PR that would strand units goes red on its OWN diff.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# A ticket in one of these names nobody who can still act on it. `split` is in the
# list because a split parent is a grouping record and never a run — its liveness is
# not its own state but its descendants', which is the whole subject of this file.
DEAD_FLAT_STATES = ("done", "split", "withdrawn")

# `split_live` is DERIVED — `derived_states` writes it back onto the map as the answer
# this walk produces. A caller holding a derived map and asking the walk again is not a
# mistake (the ledger's fragile-pointer note does exactly that), so the walk recognises
# both spellings of the same node and descends through either. Reading `split_live` as
# an opaque unknown state instead is a silent hole: it drops the whole subtree under it,
# which is how the self-test's T-9001 -> T-9002 -> T-9003 chain first came back empty.
SPLIT_STATES = ("split", "split_live")

# The two leaf sets, named where they are used rather than folded together. See the
# module docstring: the asymmetry is a ruling, not an oversight.
LEDGER_ALIVE = frozenset({"open", "claimed", "review", "in-progress"})
ORDER_BOOK_ALIVE = None      # None = "anything not flat-dead", the book's own reading


def _alive(state: str | None, alive: frozenset[str] | None) -> bool:
    """Is a ticket in this FLAT state live, before any walk through a split?"""
    if state is None or state in SPLIT_STATES:
        return False
    if alive is None:
        return state not in DEAD_FLAT_STATES
    return state in alive


# ---------------------------------------------------------------- reading tickets

def read_tree(root: Path = ROOT,
              tickets_dir: Path | None = None) -> tuple[dict[str, str], dict[str, str]]:
    """(id -> flat state, child -> parent), off the front matter of every ticket.

    The same scan `research_spend_ledger.ticket_states` and
    `build_order_book_1835.ticket_states` have each done for themselves; both now
    call this, so a ticket that parses for one parses for the other.
    """
    states: dict[str, str] = {}
    parents: dict[str, str] = {}
    if tickets_dir is None:
        # The clone can be somewhere else — `ticket.mjs` runs against
        # `CHICAGO_TICKETS_DIR` in the tickets repo's own workflows, and a walk that
        # read a different queue from its caller's would be worse than no walk.
        env = os.environ.get("CHICAGO_TICKETS_DIR")
        # …but only for THIS checkout. `fragile_pointers`' self-test builds a fixture
        # tree in a temp directory and asks for it by root; an env var pointing at the
        # real clone would answer with the real queue and the fixture would prove
        # nothing. An explicitly named root wins over the environment.
        tickets_dir = Path(env) if env and root == ROOT else root / "tickets"
    directory = Path(tickets_dir)
    if not directory.is_dir():
        return states, parents
    for path in sorted(directory.rglob("T-*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        tid = re.search(r"(?m)^id:\s*(T-\d+)\s*$", text)
        state = re.search(r"(?m)^state:\s*([^\s#]+)", text)
        parent = re.search(r"(?m)^parent:\s*(T-\d+)\s*$", text)
        if tid and state:
            states[tid.group(1)] = state.group(1)
            if parent:
                parents[tid.group(1)] = parent.group(1)
    return states, parents


def children_of(parents: dict[str, str]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for child, parent in sorted(parents.items()):
        out.setdefault(parent, []).append(child)
    return out


# ------------------------------------------------------------------- the one walk

def live_pieces_of(ticket: str, states: dict[str, str], children: dict[str, list[str]],
                   alive: frozenset[str] | None = ORDER_BOOK_ALIVE) -> list[str]:
    """THE DESCENT (T-1575): the live runs a split ticket is still discharged by.

    A split is a grouping record AT EVERY DEPTH, so the walk goes through a split
    child to its own pieces and a closed piece ends the walk. Returns the live
    descendants themselves — never the split nodes on the way — so the caller can
    name who is actually on it.
    """
    found: list[str] = []
    seen: set[str] = set()

    def walk(tid: str) -> None:
        for kid in children.get(tid) or []:
            if kid in seen:
                continue
            seen.add(kid)
            if states.get(kid) in SPLIT_STATES:
                walk(kid)
            elif _alive(states.get(kid), alive):
                found.append(kid)

    walk(ticket)
    return sorted(found)


def is_live(ticket: str, states: dict[str, str], children: dict[str, list[str]],
            alive: frozenset[str] | None = ORDER_BOOK_ALIVE) -> bool:
    """One predicate. A flat-live ticket is live; a split is live through its pieces."""
    if states.get(ticket) in SPLIT_STATES:
        return bool(live_pieces_of(ticket, states, children, alive))
    return _alive(states.get(ticket), alive)


def derived_states(states: dict[str, str], parents: dict[str, str],
                   alive: frozenset[str] | None = ORDER_BOOK_ALIVE) -> dict[str, str]:
    """THE ASCENT (T-1237/T-1421): the same relation, written back onto the map.

    A `split` parent reports `split_live` while `is_live` says so, and plain `split`
    once every leaf of its chain has closed. This is what the ledger asks, and it is
    now the descent above read upward rather than a second fixed-point pass.
    """
    children = children_of(parents)
    out = dict(states)
    for tid, state in states.items():
        if state in SPLIT_STATES and is_live(tid, states, children, alive):
            out[tid] = "split_live"
    return out


def strands(closing: list[str], states: dict[str, str], parents: dict[str, str],
            alive: frozenset[str] | None = ORDER_BOOK_ALIVE) -> dict[str, list[str]]:
    """Ancestor -> the closing tickets that take its last live descendant.

    Asked of the WHOLE ancestor chain, not the parent: case 1 and case 2 above both
    stranded a grandparent. An ancestor that is already dead is not listed — it is
    somebody else's red, and blaming this PR for it is what T-1593 is filed about.
    """
    after = dict(states)
    for tid in closing:
        if tid in after:
            after[tid] = "done"
    children = children_of(parents)
    out: dict[str, list[str]] = {}
    for tid in closing:
        walk, seen = parents.get(tid), set()
        while walk and walk not in seen:
            seen.add(walk)
            if (is_live(walk, states, children, alive)
                    and not is_live(walk, after, children, alive)):
                out.setdefault(walk, []).append(tid)
            walk = parents.get(walk)
    return {k: sorted(set(v)) for k, v in sorted(out.items())}


# --------------------------------------------------- what rides on those ancestors

def pointers_at(tickets: set[str], root: Path = ROOT) -> list[str]:
    """Every committed work pointer naming one of `tickets`, by the gates' own readers.

    THE READERS AND NOT A GREP, because a grep over `tools/*.py` finds the owner
    tables and misses the 272 rows inside a gzipped ledger — which is exactly the
    advice `ticket.mjs` used to print. `research_spend_ledger` and
    `build_order_book_1835` are imported and asked; if either cannot be imported the
    caller is TOLD, because a check that could not run is not a check that passed.
    """
    sys.path.insert(0, str(root / "tools"))
    found: list[str] = []

    try:
        import research_spend_ledger as rl
    except Exception as exc:                                  # pragma: no cover
        found.append(f"NOT CHECKED: the research ledger could not be read ({exc})")
    else:
        doc = rl.read_ledger() or {}
        counts = Counter(str(row.get("ticket") or "")
                         for row in (doc.get("units") or [])
                         if isinstance(row, dict) and row.get("disposition") == "unresolved")
        for ticket in sorted(tickets):
            if counts.get(ticket):
                found.append(f"{counts[ticket]:,} unresolved research unit(s) in "
                             f"{rl.LEDGER.relative_to(rl.ROOT)} defer to {ticket}")
        try:
            rulings, _ = rl.read_rulings(root)
        except Exception as exc:                              # pragma: no cover
            found.append(f"NOT CHECKED: the ruling registers could not be read ({exc})")
        else:
            ruled = Counter(str(r.get("ticket") or "")
                            for r in (rulings.values() if isinstance(rulings, dict) else [])
                            if isinstance(r, dict) and r.get("disposition") == "unresolved")
            for ticket in sorted(tickets):
                if ruled.get(ticket):
                    found.append(f"{ruled[ticket]:,} unresolved ruling(s) in the spend "
                                 f"registers defer to {ticket}")
    return found


def order_book_holes(states: dict[str, str], parents: dict[str, str],
                     root: Path = ROOT) -> list[str]:
    """The work-order gate (T-1420/T-1575), asked against a hypothetical queue."""
    sys.path.insert(0, str(root / "tools"))
    try:
        import build_order_book_1835 as ob
    except Exception as exc:                                  # pragma: no cover
        return [f"NOT CHECKED: the order book could not be read ({exc})"]
    doc = ob.read_json(ob.ORDER_BOOK) if hasattr(ob, "ORDER_BOOK") else None
    if doc is None:
        path = root / "data/reconstruction/1835_reconstruction_order_book.json"
        if not path.is_file():
            return [f"NOT CHECKED: {path} is not here"]
        import json
        doc = json.loads(path.read_text(encoding="utf-8"))
    try:
        ob.every_work_order_names_a_live_ticket(doc, dict(states), children_of(parents))
    except Exception as exc:
        return [str(exc)]
    return []


# ------------------------------------------------------------------- the question

def branch_tickets(root: Path = ROOT) -> list[str]:
    """The ticket ids this branch carries, read off its name.

    The convention `ticket.mjs inflight` already reads: a steward branch is named for
    the ticket it discharges (`steward/t1581-…`). It is a DECLARATION and not a
    contract — `--closing` overrides it, and `dev`/`main` carry none, which is what
    keeps this step quiet where there is nothing being closed.
    """
    name = os.environ.get("GITHUB_HEAD_REF") or os.environ.get("GITHUB_REF_NAME") or ""
    if not name:
        try:
            name = subprocess.run(["git", "-C", str(root), "rev-parse", "--abbrev-ref", "HEAD"],
                                  capture_output=True, text=True, check=True).stdout.strip()
        except Exception:                                     # pragma: no cover
            name = ""
    if name in ("dev", "main", "HEAD", ""):
        return []
    return sorted({f"T-{m.group(1)}" for m in re.finditer(r"(?i)\bt-?(\d{4})\b", name)})


def would_strand(closing: list[str], root: Path = ROOT) -> tuple[list[str], list[str]]:
    """(faults, notes) for closing `closing` — the whole question in one call."""
    states, parents = read_tree(root)
    unknown = [t for t in closing if t not in states]
    closing = [t for t in closing if t in states]
    notes = [f"{t} is not a ticket in this clone — not evaluated" for t in unknown]
    if not closing:
        return [], notes or ["no ticket ids to evaluate"]

    faults: list[str] = []
    # THE LEDGER'S QUESTION, on the ledger's own leaf set.
    ledger_lost = strands(closing, states, parents, LEDGER_ALIVE)
    riders = pointers_at(set(ledger_lost), root)
    for line in riders:
        blame = ", ".join(sorted({c for a in ledger_lost for c in ledger_lost[a]}))
        faults.append(f"{line} — closing {blame} takes its last live descendant")

    # THE ORDER BOOK'S QUESTION, asked as the book asks it: re-run the gate against a
    # queue in which these tickets are already `done`.
    after = dict(states)
    for tid in closing:
        after[tid] = "done"
    before_holes = set(order_book_holes(states, parents, root))
    for hole in order_book_holes(after, parents, root):
        if hole not in before_holes:
            faults.append(f"{hole} — and that is new with this close")
        elif hole.startswith("NOT CHECKED"):
            faults.append(hole)

    for ancestor, by in sorted(ledger_lost.items()):
        notes.append(f"{ancestor} loses its last live descendant when "
                     f"{', '.join(by)} close(s)")
    if not faults and not notes:
        notes.append(f"closing {', '.join(closing)} strands nothing")
    return faults, notes


def fragile(root: Path = ROOT) -> list[str]:
    """Pointers ONE closure away: a split chain held live by a single leaf.

    Acceptance 5 of T-1581 — what is currently standing on one run, so the reading
    can be made before the close rather than after it.
    """
    states, parents = read_tree(root)
    derived = derived_states(states, parents, LEDGER_ALIVE)
    children = children_of(parents)
    out = []
    for ancestor, state in sorted(derived.items()):
        if state != "split_live":
            continue
        leaves = live_pieces_of(ancestor, states, children, LEDGER_ALIVE)
        if len(leaves) != 1:
            continue
        riders = pointers_at({ancestor}, root)
        for line in riders:
            out.append(f"{line} — held live by ONE leaf, {leaves[0]}")
    return out


# ------------------------------------------------------------------------ selftest

def _fixture(tree: dict[str, tuple[str, str | None]]):
    states = {tid: state for tid, (state, _) in tree.items()}
    parents = {tid: parent for tid, (_, parent) in tree.items() if parent}
    return states, parents


def self_test() -> int:
    """The three shapes that cost `dev` an afternoon, and the one that must NOT fire."""
    failures = []

    def case(label, tree, closing, want_stranded, alive=LEDGER_ALIVE):
        states, parents = _fixture(tree)
        got = sorted(strands(closing, states, parents, alive))
        if got != sorted(want_stranded):
            failures.append(f"{label}: expected {sorted(want_stranded)}, got {got}")
        else:
            print(f"  holds: {label}")

    # 1. #40's shape — a leaf closing under a split GRANDPARENT two levels up.
    case("a leaf closing strands its split grandparent",
         {"T-1189": ("split", None), "T-1434": ("split", "T-1189"),
          "T-1448": ("claimed", "T-1434")},
         ["T-1448"], ["T-1189", "T-1434"])

    # 2. #43's shape — a DIRECT piece closing while a grandchild lives. Nothing is
    #    stranded, and reading one level deep is what said otherwise.
    case("a direct piece closing while a grandchild lives strands nobody",
         {"T-1556": ("split", None), "T-1560": ("claimed", "T-1556"),
          "T-1559": ("split", "T-1556"), "T-1564": ("open", "T-1559")},
         ["T-1560"], [])

    # 3. #49's shape — a single-leaf chain, the 272 landholding units on T-1198.
    case("a single-leaf chain strands its parent",
         {"T-1198": ("split", None), "T-1523": ("claimed", "T-1198")},
         ["T-1523"], ["T-1198"])

    # 4. AND THE NEGATIVE, which is the one that keeps this usable: a split with a
    #    live descendant two levels down must NOT be refused.
    case("a split with a live descendant two levels down is not refused",
         {"T-1": ("split", None), "T-2": ("split", "T-1"), "T-3": ("done", "T-2"),
          "T-4": ("open", "T-2"), "T-5": ("claimed", "T-1")},
         ["T-5"], [])

    # 5. The leaf sets differ, and the difference is load-bearing (see the docstring).
    blocked = {"T-1": ("split", None), "T-2": ("blocked-tech", "T-1")}
    states, parents = _fixture(blocked)
    if derived_states(states, parents, ORDER_BOOK_ALIVE).get("T-1") != "split_live":
        failures.append("the order book's leaf set must count a blocked ticket as live")
    elif derived_states(states, parents, LEDGER_ALIVE).get("T-1") != "split":
        failures.append("the ledger's leaf set must not count a blocked ticket as live")
    else:
        print("  holds: a blocked leaf is live for the order book and not for the ledger")

    # 6. A cycle in `parent` must not hang the walk — the tool refuses tickets, it
    #    does not get to refuse to run.
    cyc = {"T-1": ("split", "T-2"), "T-2": ("split", "T-1"), "T-3": ("open", "T-1")}
    states, parents = _fixture(cyc)
    strands(["T-3"], states, parents, LEDGER_ALIVE)
    print("  holds: a parent cycle terminates")

    # 8. A DERIVED MAP READS THE SAME AS A FLAT ONE, and this one is not theoretical:
    #    `fragile_pointers` holds the derived map and asks the walk again, and the first
    #    version of this module read `split_live` as an unknown state and silently
    #    dropped the whole subtree under it. The ledger's own T-9001 -> T-9002 -> T-9003
    #    fixture caught it; it is held here too, where it is one line to read.
    chain = {"T-9001": ("split", None), "T-9002": ("split", "T-9001"),
             "T-9003": ("open", "T-9002")}
    states, parents = _fixture(chain)
    derived = derived_states(states, parents, LEDGER_ALIVE)
    flat_leaves = live_pieces_of("T-9001", states, children_of(parents), LEDGER_ALIVE)
    derived_leaves = live_pieces_of("T-9001", derived, children_of(parents), LEDGER_ALIVE)
    if flat_leaves != ["T-9003"] or derived_leaves != ["T-9003"]:
        failures.append(f"the walk disagrees with itself on a derived map: "
                        f"flat {flat_leaves}, derived {derived_leaves}")
    else:
        print("  holds: the walk descends `split_live` exactly as it descends `split`")

    # 7. ONE DEFINITION, ASSERTED AND NOT ASSUMED. The two callers keep their own
    #    leaf sets on purpose, and the walk is shared — so what this holds is that
    #    neither has quietly grown a second copy of the constants it reads.
    sys.path.insert(0, str(ROOT / "tools"))
    try:
        import research_spend_ledger as rl
        import build_order_book_1835 as ob
    except Exception as exc:                                  # pragma: no cover
        failures.append(f"the two callers could not be imported: {exc}")
    else:
        if frozenset(rl.LEDGER_ALIVE_SET) != LEDGER_ALIVE:
            failures.append("the ledger's leaf set has drifted from LEDGER_ALIVE")
        elif rl.OPEN_TICKET_STATES != set(LEDGER_ALIVE) | {"split_live"}:
            failures.append("the ledger's OPEN_TICKET_STATES no longer equals its leaf "
                            "set plus the derived `split_live`")
        elif tuple(ob.DEAD_TICKET_STATES) != DEAD_FLAT_STATES:
            failures.append("the order book's DEAD_TICKET_STATES has drifted from "
                            "DEAD_FLAT_STATES")
        else:
            print("  holds: the ledger and the order book read this module's constants")

    for line in failures:
        print(f"  FAIL {line}")
    print(f"ticket liveness self-test: {'FAILED' if failures else 'all cases hold'}")
    return 1 if failures else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--closing", action="append", default=[],
                    help="a ticket this branch closes (repeatable); default: read off the branch name")
    ap.add_argument("--report", action="store_true",
                    help="list the pointers currently ONE closure away and stop")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--tickets", default=None,
                    help="the ticket clone, if it is not <root>/tickets (or $CHICAGO_TICKETS_DIR)")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    if args.tickets:
        os.environ["CHICAGO_TICKETS_DIR"] = str(Path(args.tickets).resolve())

    if args.selftest:
        return self_test()

    if args.report:
        lines = fragile(root)
        for line in lines:
            print(f"  {line}")
        print(f"{len(lines)} pointer group(s) are one closure away")
        return 0

    closing = [t.upper() for t in args.closing] or branch_tickets(root)
    if not closing:
        print("no ticket id on this branch — nothing is being closed here")
        return 0
    faults, notes = would_strand(closing, root)
    for note in notes:
        print(f"  note: {note}")
    if not faults:
        print(f"closing {', '.join(closing)} strands no committed work pointer")
        return 0
    print("")
    print(f"CLOSING {', '.join(closing)} WOULD STRAND COMMITTED WORK:")
    for fault in faults:
        print(f"  - {fault}")
    print("")
    print("Repoint them at the live ticket that owns their question, or file one, in")
    print("THIS pull request — after it merges the red is dev's and is nobody's diff.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
