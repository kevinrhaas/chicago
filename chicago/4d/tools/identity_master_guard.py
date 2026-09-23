#!/usr/bin/env python3
"""T-0843. Ask the identity master, before a mint writes a card, whether the town
already holds this person.

    python3 tools/identity_master_guard.py --report     the population, card by card
    python3 tools/identity_master_guard.py --self-test  the resolver's own assertions

WHY THIS FILE EXISTS.

T-0839 found 39 surname clusters holding 110 town cards that were fewer people:
Gurdon Saltonstall Hubbard stood on six cards and Lieut. James Allen on four. PR #929
folded the 42 duplicates under written rulings and `tools/consolidate_town_cards.py
--check` gates that every candidate cluster carries one. That gate is RULING COVERAGE.
It says the duplicates the town holds today have been ruled on; it does not stop a
minting pass writing a new one tomorrow, and the owner's ticket is explicit that the
cause, not the symptom, is what T-0843 owns.

THE CAUSE, IN ONE SENTENCE. Three of the four minting passes test "does the town
already carry this person?" by SURNAME — `the town already names a Hubbard` — and that
test is deliberately blunt, so it is also deliberately PARTIAL: each pass skips the
households minted by itself and by every pass below it in the precedence order
(mint_documented_residents.MINTED_PASSES), and all three skip the civic pass's
households outright, because a surname proxy over 700-odd letter-list records would
retire hundreds of committed cards on a collision alone. The blind spot is the point of
the design and it is not going away. What was missing is the PRECISE instrument to look
into it: the identity master already resolves a name on surname AND forename signature
across every landed domain, and nothing was asking it.

WHAT THIS RESOLVER IS, AND WHAT IT IS NOT.

It is the master's own merge rules, applied to ONE printed name against the identities
that already stand on a committed card:

  M1  identical normalised name — same surname, same forename tokens, letter for letter
  M2  an initial-only forename attaches to the ONE full forename of that surname
      carrying that initial. Two or more rivals is a refusal to guess, never a choice
  M3  a middle initial present on one reading and absent on the other, forename and
      surname agreeing, and no rival of that surname carrying a different middle initial

It is NOT a new adjudication and it invents no rule of its own — every rule here is
quoted from `MERGE_RULES` in tools/consolidate_resident_evidence.py, whose parser
(`split_name`) is also the one used, so a name this file reads is read exactly as the
master read it. Where the master would refuse to merge (R2/R4 — two identities of one
surname; R3 — an initial with rival full forenames), this resolver hands back nothing
and the mint proceeds: two men until something says otherwise is the ratified answer,
and a guard that refused on ambiguity would quietly retire real people.

It also claims NOTHING about a card a pass is entitled not to see. `blind_to` is the
set of person ids the calling pass must not read back — its own previous answer, and
every later pass's — so consulting the master cannot make a pass unre-derivable, which
is the failure `mint_civic_residents.py`'s docstring spends a page on.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from consolidate_resident_evidence import (  # noqa: E402
    MASTER, ROOT, cluster, is_initial, split_name,
)

CANDIDATE = "__the_name_being_minted__"

HOUSEHOLDS = ROOT / "data" / "residents" / "households"


def load_master(path: Path = MASTER) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class IdentityGuard:
    """The identities that stand on a committed card, resolvable by printed name."""

    def __init__(self, master: dict):
        # EVERY identity of a surname is kept, not only the ones on a card. A rival
        # the town never wrote a card for is still what holds a merge apart (R2/R3/R4),
        # so dropping it would turn a refusal into a match.
        self.by_surname: dict[str, list[dict]] = defaultdict(list)
        self.rows: dict[str, dict] = {}
        for row in master.get("identities") or []:
            signature = tuple(t for t in (row.get("forename") or "").split() if t)
            if not signature:
                continue
            entry = {
                "id": row["id"],
                "surname": row["surname"],
                "signature": signature,
                "printed": " ".join(signature) + " " + row["surname"],
                "canonical_person_id": row.get("canonical_person_id"),
                "town_person_ids": list(row.get("town_person_ids") or []),
            }
            self.by_surname[row["surname"]].append(entry)
            self.rows[row["id"]] = entry

    @classmethod
    def load(cls, path: Path = MASTER) -> "IdentityGuard":
        return cls(load_master(path))

    def holder(self, printed_name: str, blind_to=frozenset()):
        """The card the town already holds this person on, or None.

        Returns {'identity', 'person_id', 'rule', 'as_the_card_prints_it'} on a match.
        None means either that no committed card resolves to this name, or that the
        master's own rules refuse to choose between rivals — the two cases a mint must
        treat the same way, because in both of them nothing has been demonstrated.

        THE RULES ARE NOT RE-IMPLEMENTED HERE, AND THE FIRST DRAFT OF THIS FILE IS WHY.
        Written out by hand from MERGE_RULES the resolver reported 19 committed cards as
        duplicates of each other where the master itself reports 2, because a hand copy
        of M2 cannot see the rivals that HOLD a merge apart: `C. S. Hunt` looks like the
        one Charles Hunt on a card until you notice the bucket also prints `Cha Hunt`,
        which is R3 and not a merge. So the candidate is handed to `cluster()` — the
        master's own function — inside its own surname bucket, with every identity of
        that surname standing as an anchor whether it holds a card or not. What comes
        back is the master's answer, arrived at by the master's code.
        """
        parsed = split_name(printed_name)
        if not parsed or not parsed[1]:
            return None
        surname, given = parsed
        bucket = self.by_surname.get(surname)
        if not bucket:
            return None

        entries = [self._entry(row["id"], row["printed"]) for row in bucket]
        entries.append(self._entry(CANDIDATE, printed_name))
        identities, _refusals = cluster(entries)
        group = next((i for i in identities
                      if any(m["record_id"] == CANDIDATE for m in i["members"])), None)
        if group is None:
            return None
        joined = [m["record_id"] for m in group["members"] if m["record_id"] != CANDIDATE]
        if len(joined) != 1:
            # Nothing, or a fold the master itself holds apart — either way undemonstrated.
            return None
        row = self.rows[joined[0]]
        visible = [pid for pid in row["town_person_ids"] if pid not in blind_to]
        if not visible:
            return None
        signature = tuple(given)
        if signature == row["signature"]:
            rule = "M1"
        elif is_initial(signature[0]) or (row["signature"] and is_initial(row["signature"][0])):
            rule = "M2"
        else:
            rule = "M3"
        return self._hit(row, visible[0], rule)

    @staticmethod
    def _entry(record_id: str, name: str) -> dict:
        return {"domain": "guard", "record_id": record_id, "source_id": None,
                "as_read": name, "normalized": name}

    @staticmethod
    def _hit(row: dict, person_id: str, rule: str) -> dict:
        return {
            "identity": row["id"],
            "person_id": person_id,
            "rule": rule,
            "as_the_card_prints_it": row["printed"].title(),
        }


def refusal(hit: dict) -> str:
    """The sentence a mint files when the guard stops it. One shape for all four."""
    return (f"the identity master already holds this person on a committed card "
            f"({hit['person_id']}, {hit['as_the_card_prints_it']}) — merged by "
            f"{hit['rule']} on surname and forename signature, not on surname alone")


def blind_person_ids(docs: dict, is_blind) -> set[str]:
    """The person ids on the households a calling pass must not read back.

    `is_blind(path, doc)` is the pass's own precedence test — the same
    `minted_by()` predicate its `town_family_names` already skips on — so the guard
    can never make a pass see a card its surname test is entitled not to see. That
    symmetry is what keeps every mint re-derivable beside the others.
    """
    out: set[str] = set()
    for path, doc in docs.items():
        if not is_blind(path, doc):
            continue
        for person in doc.get("persons") or []:
            if person.get("id"):
                out.add(person["id"])
    return out


# ---------------------------------------------------------------------------
# THE REPORT. What the population actually is, before anything is wired to it.


def committed_heads() -> list[tuple[str, str]]:
    """(person_id, printed name) for every person on every committed household card."""
    heads = []
    for path in sorted(HOUSEHOLDS.glob("*.json")):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for person in doc.get("persons") or []:
            if person.get("id") and person.get("name"):
                heads.append((person["id"], person["name"]))
    return heads


def cmd_report() -> int:
    master = load_master()
    guard = IdentityGuard(master)
    rows = [r for r in master["identities"] if r.get("canonical_person_id")]
    doubled = [r for r in rows if len(r.get("town_person_ids") or []) > 1]

    print("THE POPULATION THE GUARD READS")
    print(f"  {len(master['identities'])} identities in the master; "
          f"{len(rows)} of them stand on a committed town card")
    print(f"  {len(doubled)} identity/identities carry MORE THAN ONE card — the duplicates "
          "that already exist")
    for row in doubled:
        print(f"    {row['id']:32} {', '.join(row['town_person_ids'])}")

    heads = committed_heads()
    resolved = []
    for person_id, name in heads:
        hit = guard.holder(name, blind_to={person_id})
        if hit:
            resolved.append((person_id, name, hit))
    print(f"\nEVERY COMMITTED CARD, READ BACK AS IF IT WERE BEING MINTED TODAY")
    print(f"  {len(heads)} person record(s) read; {len(resolved)} resolve onto a DIFFERENT "
          "card by the master's own merge rules")
    for person_id, name, hit in resolved:
        print(f"    {person_id:30} {name:34} -> {hit['person_id']} ({hit['rule']})")
    print("\n  A pass wired to this guard refuses a candidate that lands in the second "
          "list.\n  It is a PREVENTION and its steady state is nought: the cards already "
          "there\n  were ruled on by T-0839, and what this stops is the next one.")
    return 0


# ---------------------------------------------------------------------------
# SELF-TEST. Each case asserts one rule, and one case asserts a refusal to guess.


def _master(*identities) -> dict:
    """(surname, forename, person_ids) rows. An empty person_ids is an identity the
    master holds that no town card stands on — a rival, which is a thing that refuses."""
    rows = []
    for surname, forename, person_ids in identities:
        rows.append({
            "id": "id_" + surname + "_" + "_".join(forename.split()),
            "surname": surname, "forename": forename,
            "canonical_person_id": person_ids[0] if person_ids else None,
            "town_person_ids": list(person_ids),
        })
    return {"identities": rows}


def cmd_self_test() -> int:
    failures = 0

    def case(label, got, want):
        nonlocal failures
        if got != want:
            print(f"  FAIL {label}: got {got!r}, wanted {want!r}")
            failures += 1
        else:
            print(f"  ok    {label}")

    g = IdentityGuard(_master(("hubbard", "gurdon saltonstall", ["hubbard_gurdon_s"])))
    case("M1 — the same name letter for letter is the same man",
         (g.holder("Gurdon Saltonstall Hubbard") or {}).get("rule"), "M1")
    case("M2 — 'G. S. Hubbard' attaches to the one Gurdon on a card",
         (g.holder("Hubbard, G. S.") or {}).get("person_id"), "hubbard_gurdon_s")
    case("M3 — a bare 'Gurdon Hubbard' folds onto the one middle initial",
         (g.holder("Gurdon Hubbard") or {}).get("rule"), "M3")
    case("a surname the town does not carry resolves onto nothing",
         g.holder("Gurdon Saltonstall Pettibone"), None)
    case("a name that names nobody resolves onto nothing",
         g.holder("Hamilton & Sons"), None)

    rivals = IdentityGuard(_master(("smith", "john", ["smith_john"]),
                                   ("smith", "james", ["smith_james"])))
    case("R3 — an initial with two rival full forenames is never guessed at",
         rivals.holder("J. Smith"), None)
    case("R2 — a different initial of the same surname is a different man",
         rivals.holder("Peter Smith"), None)
    case("…and the exact forename of one rival still resolves",
         (rivals.holder("John Smith") or {}).get("person_id"), "smith_john")

    # THE CASE THE HAND-WRITTEN RULES GOT WRONG, kept as the reason the resolver
    # defers to `cluster()`. 'Cha Hunt' stands on no card, so a resolver reading only
    # the identities that do would see one Charles for 'C. S. Hunt' and merge them; the
    # master sees two and refuses under R3. The rival is what makes it a refusal.
    cardless_rival = IdentityGuard(_master(
        ("hunt", "charles cotesworth pinckney", ["hunt_charles_cotesworth_pinckney"]),
        ("hunt", "cha", [])))
    case("a rival the town wrote no card for still holds the merge apart",
         cardless_rival.holder("C. S. Hunt"), None)

    middles = IdentityGuard(_master(("brown", "william h", ["brown_william_h"]),
                                    ("brown", "william j", ["brown_william_j"])))
    case("M3 refuses when a rival carries a different middle initial",
         middles.holder("William Brown"), None)

    blind = IdentityGuard(_master(("hubbard", "gurdon saltonstall", ["hubbard_gurdon_s"])))
    case("a card the pass is blind to is not a card it may be refused for",
         blind.holder("Gurdon Saltonstall Hubbard", blind_to={"hubbard_gurdon_s"}), None)

    two = IdentityGuard(_master(("norton", "nelson r", ["norton_n_r", "norton_nelson_r"])))
    case("an identity already holding two cards still answers with a visible one",
         (two.holder("Nelson R. Norton", blind_to={"norton_n_r"}) or {}).get("person_id"),
         "norton_nelson_r")

    hit = {"person_id": "hubbard_gurdon_s", "as_the_card_prints_it": "Gurdon Saltonstall Hubbard",
           "rule": "M2"}
    case("the refusal sentence names the card, the reading and the rule",
         all(part in refusal(hit) for part in ("hubbard_gurdon_s", "Gurdon", "M2")), True)
    return failures


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return cmd_self_test()
    if args.report:
        return cmd_report()
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
