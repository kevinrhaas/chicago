#!/usr/bin/env python3
"""The home and workplace reconciliation rows, written as `associated_with` rows (T-1273).

    python3 tools/household_associations.py             the table, on stdout
    python3 tools/household_associations.py --write     write the rows onto the household records
                                                        and data/research/residents/household_associations.json
    python3 tools/household_associations.py --check     re-derive both and refuse a drift
    python3 tools/household_associations.py --self-test the assertions of --check, broken on purpose

WHAT THIS IS FOR.

T-1237's reconciliation table (`tools/location_reconciliation.py`) holds one row
for every home and workplace claim a household makes, resolved as far as the
evidence reaches. T-1238 gave a relationship between a person and a place its
plural, dated shape, and `tools/person_associations.py` filled that shape with
the OTHER places a man was. Neither wrote the home and the workplace — the two
claims the shape was invented to widen — so a household's second address was
legible in the table and not on the card. This module is the first half of
T-1253's migration: it copies every committed home and workplace reconciliation
row onto the household it belongs to, CHANGING NO VALUE, CONFIDENCE OR SOURCE.
T-1274 moves the readers off `lives_at`/`works_at` and retires the pair.

WHAT IS COPIED, FIELD BY FIELD.

  * `kind`        `home` for a `lives_at` row, `workplace` for a `works_at` row.
  * the place     the row's `resolved_structure`, at the `structure` rung — every
                  row copied here resolved to a committed roof.
  * `tier`        the claim's own `confidence`, unchanged.
  * the sources   the claim's own `sources`, in their own order: the first is
                  `source_id`, any later ones `also_sources`. A reconstructed claim
                  cites nothing and its row cites nothing.
  * the note      the claim's own note, then the reconciliation row's limit clause,
                  then the sentence that says this module wrote it.
  * the dates     NONE, and the row says `undated: true`. The singular field states
                  where the household was on the scene date and says nothing about
                  when the relationship began or ended; the reconciliation row's
                  `date_precision: scene_date` says the same. Writing 1 July 1835 as a
                  `from` would turn the scene date into a start the source never gave,
                  which is the flattening T-1238 exists to refuse. This is also how the
                  hand-written precedent reads: St Cyr's `home` row at St Mary's.

WHAT IS NOT COPIED, AND WHY — the refusals are counted beside the rows.

  * A `home` row the table limits to a DIVISION (83 of them). Every one has a
    `lives_at` of `null`: the division is the household's seating class, not a
    claim about where it lived. `associations.py` defines the list over CLAIMS —
    "an absent relationship is an absent row" — and Bates's own hand-written row
    says it in so many words: "THERE IS NO HOME ROW because there is no home claim".
  * A home with NO CLAIM at all (`no_claim`). Same rule.
  * A LATER directory address (`later_home_address`, `later_workplace_address`).
    Those are 1839, 1843 and 1844 readings; a back-projection that "resolved" one
    placed nothing in 1835, and a row from a later year would begin after the scene.
  * A business location. A business is not a household record and this list lives
    on households and persons.
  * A claim a card ALREADY carries in its own hand — a row of the same family
    (home or work, `associations.HOME_KINDS`/`WORK_KINDS`) at the same structure,
    written by a reading. Porter's loft is a `lodging`, Bates's room is a
    `business_premises`, St Mary's is St Cyr's `church`; each of those is a finer
    word than this module would use, so the card keeps its own and nothing is added.

THE ROWS ARE THIS MODULE'S, AND IT CAN TELL WHICH ONES. Every row it writes ends
with `MARK` in its note. `--check` re-derives the rows from the committed table
and the committed cards and refuses (a) a derived row that is not on its card
byte for byte, and (b) a marked row on a card that no longer derives — the stale
row a changed `lives_at` would otherwise leave behind, which `singular_drift`
does not catch because it only asks that the singular value appear somewhere.
"""
from __future__ import annotations

import copy
import gzip
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
HOUSEHOLDS = DATA / "residents" / "households"
RECONCILIATION = DATA / "research" / "location_reconciliation.json.gz"
REPORT = DATA / "research" / "residents" / "household_associations.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from associations import HOME_KINDS, WORK_KINDS  # noqa: E402

MARK = "(T-1273)"

FIELD_FOR = {"home": "lives_at", "workplace": "works_at"}
FAMILY = {"home": HOME_KINDS, "workplace": WORK_KINDS}


def load_households() -> list:
    return [(p, json.loads(p.read_text(encoding="utf-8")))
            for p in sorted(HOUSEHOLDS.glob("*.json"))]


def reconciliation_rows() -> list:
    with gzip.open(RECONCILIATION, "rt", encoding="utf-8") as f:
        return json.load(f)["rows"]


def key(r) -> tuple:
    return (r.get("kind"), r.get("place_or_structure_id"), str(r.get("from")))


def ours(r) -> bool:
    return isinstance(r, dict) and str(r.get("note") or "").endswith(MARK)


def note_for(field: str, claim: dict, rec: dict) -> str:
    parts = []
    own = str(claim.get("note") or "").strip()
    if own:
        parts.append(own if own.endswith((".", "!", "?", "'", '"', ")")) else own + ".")
    basis = claim.get("basis") or {}
    if claim.get("confidence") == "reconstructed" and basis.get("id"):
        parts.append(f"Reconstructed on the {basis.get('kind', 'rule')} `{basis['id']}`; "
                     f"no source places this household.")
    parts.append(rec["limit_clause"])
    parts.append(f"COPIED FROM THE SINGULAR `{field}` AND ITS RECONCILIATION ROW "
                 f"`{rec['row_id']}`, changing no value, confidence or source. That field "
                 f"names the place as of 1 July 1835 and dates neither end of the "
                 f"relationship, so this row is `undated` rather than borrowing the scene "
                 f"date as a start {MARK}")
    return " ".join(parts)


def derive_row(rec: dict, claim: dict) -> dict:
    field = FIELD_FOR[rec["claim_kind"]]
    sources = list(claim.get("sources") or [])
    tier = claim.get("confidence")
    cites = tier in ("attested", "inferred")
    row = {"kind": rec["claim_kind"], "place_or_structure_id": rec["resolved_structure"],
           "resolves_to": "structure", "from": None, "to": None, "undated": True,
           "tier": tier, "source_id": sources[0] if cites and sources else None,
           "note": note_for(field, claim, rec)}
    if cites and len(sources) > 1:
        row["also_sources"] = sources[1:]
    # T-2261: the claim's own words and its next rung ride on the row, so nothing has to
    # read them off the singular once the pair retires. The row's `note` is those words
    # with this module's limit clause and mark appended, which is the card's sentence and
    # not the claim's; `basis.note` is the claim's alone. The garrison's eleven carry a
    # `replaceable_by` ("a plan of the post that assigns its quarters") a row could not
    # hold before, and the card prints it.
    basis = own_basis(claim)
    if basis:
        row["basis"] = basis
    if claim.get("replaceable_by"):
        row["replaceable_by"] = copy.deepcopy(claim["replaceable_by"])
    return row


def own_basis(claim: dict) -> dict | None:
    """The claim's `basis`, carrying the claim's own note where the basis states none."""
    basis = copy.deepcopy(claim.get("basis") or {})
    own = str(claim.get("note") or "").strip()
    if not str(basis.get("note") or "").strip() and own:
        basis["note"] = claim["note"]
    return basis or None


def derive(households=None) -> tuple:
    """(rows by household id, refusals by reason, already held by a reading)."""
    households = households if households is not None else load_households()
    cards = {h["id"]: h for _p, h in households}
    proposal: dict = {}
    refused: dict = {}
    already: list = []
    for rec in reconciliation_rows():
        kind = rec["claim_kind"]
        if kind not in FIELD_FOR:
            refused[f"{kind}: not a household's own home or workplace claim"] = \
                refused.get(f"{kind}: not a household's own home or workplace claim", 0) + 1
            continue
        if rec["disposition"] != "resolved" or not rec.get("resolved_structure"):
            why = f"{kind} {rec['disposition']}: the record makes no claim that reaches a place"
            refused[why] = refused.get(why, 0) + 1
            continue
        hid = rec["household_id"]
        card = cards.get(hid)
        claim = (card or {}).get(FIELD_FOR[kind]) or {}
        if claim.get("value") != rec["resolved_structure"]:
            raise SystemExit(f"FAIL {rec['row_id']} names {rec['resolved_structure']!r} and the "
                             f"card's {FIELD_FOR[kind]} names {claim.get('value')!r}: the "
                             f"reconciliation table is stale. Rebuild it with "
                             f"tools/location_reconciliation.py --build first.")
        row = derive_row(rec, claim)
        held = [r for r in (card.get("associated_with") or [])
                if not ours(r) and r.get("kind") in FAMILY[kind]
                and r.get("place_or_structure_id") == row["place_or_structure_id"]]
        if held:
            already.append({"household_id": hid, "claim": FIELD_FOR[kind],
                            "held_as": sorted(r["kind"] for r in held)})
            continue
        proposal.setdefault(hid, []).append(row)
    return proposal, dict(sorted(refused.items())), already


def counts(proposal, refused, already) -> dict:
    by_kind: dict = {}
    by_tier: dict = {}
    for rs in proposal.values():
        for r in rs:
            by_kind[r["kind"]] = by_kind.get(r["kind"], 0) + 1
            by_tier[r["tier"]] = by_tier.get(r["tier"], 0) + 1
    return {
        "households_carrying_rows": len(proposal),
        "rows": sum(len(v) for v in proposal.values()),
        "rows_by_kind": dict(sorted(by_kind.items())),
        "rows_by_tier": dict(sorted(by_tier.items())),
        "rows_with_a_second_source": sum(1 for rs in proposal.values() for r in rs
                                         if r.get("also_sources")),
        "already_held_by_a_reading": len(already),
        "refused": sum(refused.values()),
    }


def payload(proposal, refused, already) -> dict:
    return {
        "schema": "household_associations/1",
        "generated_by": "tools/household_associations.py",
        "_doc": ("T-1273. Every home and workplace reconciliation row that reaches a roof, "
                 "copied onto its household as an `associated_with` row with no value, "
                 "confidence or source changed; the rows a reading already wrote in finer "
                 "words; and every reconciliation row that is not copied, by the reason. "
                 "DERIVED: rebuild with --write, and --check refuses a hand-edit or a "
                 "drift between this file and the rows on the cards."),
        "compiled_from": [
            "data/research/location_reconciliation.json.gz (rows of claim_kind home and workplace)",
            "data/residents/households/*.json (lives_at, works_at, associated_with)",
        ],
        "counts": counts(proposal, refused, already),
        "rows_by_household": {hid: rs for hid, rs in sorted(proposal.items())},
        "already_held_by_a_reading": already,
        "refused_by_reason": refused,
    }


def render(p: dict) -> str:
    c = p["counts"]
    out = [f"household associations: {c['rows']} row(s) on {c['households_carrying_rows']} "
           f"household(s), {c['rows_with_a_second_source']} with a second source, "
           f"{c['already_held_by_a_reading']} already held by a reading, "
           f"{c['refused']} reconciliation row(s) not copied"]
    for k, v in c["rows_by_kind"].items():
        out.append(f"  row      {k:12} {v}")
    for k, v in c["rows_by_tier"].items():
        out.append(f"  tier     {k:12} {v}")
    for k, v in p["refused_by_reason"].items():
        out.append(f"  refused  {v:5}  {k}")
    return "\n".join(out)


# --------------------------------------------------------------------------

def place_rows(card: dict, rows: list) -> None:
    """Write `associated_with` straight after `works_at`, where the hand-written
    household rows already sit (Bates, Porter, St Cyr), keeping every other key
    exactly where it lies."""
    if "associated_with" in card:
        card["associated_with"] = rows
        return
    out = {}
    for k, v in list(card.items()):
        out[k] = v
        if k == "works_at":
            out["associated_with"] = rows
    if "associated_with" not in out:
        out["associated_with"] = rows
    card.clear()
    card.update(out)


def apply_to_cards(proposal) -> int:
    written = 0
    for path, h in load_households():
        before = json.dumps(h, indent=1, ensure_ascii=False)
        kept = [r for r in (h.get("associated_with") or []) if not ours(r)]
        want = proposal.get(h["id"], [])
        rows = kept + [r for r in want if key(r) not in {key(x) for x in kept}]
        if rows:
            place_rows(h, rows)
        elif "associated_with" in h:
            del h["associated_with"]
        after = json.dumps(h, indent=1, ensure_ascii=False)
        if after != before:
            path.write_text(after + "\n", encoding="utf-8")
            written += 1
    return written


def cards_drift(proposal, households=None) -> list:
    """Every derived row missing from its card, and every marked row that no longer derives."""
    out = []
    for _p, h in (households if households is not None else load_households()):
        on_card = [r for r in (h.get("associated_with") or []) if ours(r)]
        want = proposal.get(h["id"], [])
        for r in want:
            if r not in on_card:
                out.append(f"{h['id']}: derived row {key(r)} is not on the card as derived")
        for r in on_card:
            if r not in want:
                out.append(f"{h['id']}: row {key(r)} carries {MARK} and no longer derives")
    return out


def main(argv) -> int:
    if "--self-test" in argv:
        return self_test()
    proposal, refused, already = derive()
    p = payload(proposal, refused, already)
    if "--write" in argv:
        n = apply_to_cards(proposal)
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(p, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"wrote {n} household file(s) and {REPORT.relative_to(ROOT)}")
        print(render(p))
        return 0
    if "--check" in argv:
        if not REPORT.exists():
            print(f"FAIL {REPORT.relative_to(ROOT)} is missing", file=sys.stderr)
            return 1
        committed = json.loads(REPORT.read_text(encoding="utf-8"))
        bad = [k for k in ("counts", "rows_by_household", "already_held_by_a_reading",
                           "refused_by_reason") if committed.get(k) != p[k]]
        if bad:
            print(f"FAIL {REPORT.relative_to(ROOT)} does not re-derive: {bad} differ. "
                  f"Rebuild with --write; the file is derived and a hand-edit loses.",
                  file=sys.stderr)
            return 1
        drift = cards_drift(proposal)
        if drift:
            print(f"FAIL {len(drift)} household row(s) drift from the reconciliation table. "
                  f"First: {drift[0]}. Rebuild with --write.", file=sys.stderr)
            return 1
        print(f"ok  {render(p)}")
        return 0
    print(render(p))
    return 0


def self_test() -> int:
    """Break the assertions --check stands on; a gate that cannot fail is not a gate."""
    failed = 0

    def say(ok, label):
        nonlocal failed
        print(("ok   " if ok else "FAIL ") + label)
        failed += 0 if ok else 1

    households = load_households()
    proposal, refused, already = derive(households)
    rows = [r for rs in proposal.values() for r in rs]

    say(bool(rows), "the table yields rows to copy")
    say(bool(refused), "the refusals are not empty — the division and later-address rows are the finding")
    say(all(r["undated"] and r["from"] is None and r["to"] is None for r in rows),
        "no row borrows the scene date as a start")
    say(all((r["tier"] == "reconstructed") == (r["source_id"] is None) for r in rows),
        "a row cites a source exactly when its tier is one that cites")
    say(all(ours(r) for r in rows), "every row carries the mark that lets --check find it")

    cards = {h["id"]: h for _p, h in households}
    lost = []
    for hid, rs in proposal.items():
        for r in rs:
            claim = cards[hid][FIELD_FOR[r["kind"]]]
            cited = [r["source_id"]] + list(r.get("also_sources") or []) if r["source_id"] else []
            if (claim.get("value") != r["place_or_structure_id"]
                    or claim.get("confidence") != r["tier"]
                    or cited != list(claim.get("sources") or [])):
                lost.append(hid)
    say(not lost, "no value, confidence or source changed in the copy"
        + ("" if not lost else f" -> {lost[:3]}"))

    # The drift check fires on a row dropped from a card and on a stale marked row.
    if rows:
        hid = sorted(proposal)[0]
        dropped = [(p, copy.deepcopy(h)) for p, h in households]
        for _p, h in dropped:
            if h["id"] == hid:
                h["associated_with"] = [r for r in h.get("associated_with") or [] if not ours(r)]
        say(bool(cards_drift(proposal, dropped)), "a derived row missing from its card is refused")
        stale = [(p, copy.deepcopy(h)) for p, h in households]
        for _p, h in stale:
            if h["id"] == hid:
                h["associated_with"] = (h.get("associated_with") or []) + [
                    {**proposal[hid][0], "place_or_structure_id": "somewhere_else"}]
        say(bool(cards_drift(proposal, stale)), "a marked row that no longer derives is refused")
        altered = [(p, copy.deepcopy(h)) for p, h in households]
        for _p, h in altered:
            if h["id"] == hid:
                h["associated_with"] = [r for r in h.get("associated_with") or []
                                        if not ours(r)] + [
                    {**r, "tier": "reconstructed" if r["tier"] != "reconstructed"
                     else "inferred"} for r in proposal[hid]]
        say(bool(cards_drift(proposal, altered)), "a hand-edited tier on a copied row is refused")

    # A reading's own row at the same place is kept and nothing is added beside it.
    fake_rec = {"claim_kind": "home", "disposition": "resolved", "resolved_structure": "x",
                "household_id": "hh_t", "row_id": "hh_t#lives_at", "limit_clause": "c."}
    claim = {"value": "x", "confidence": "attested", "sources": ["a", "b"], "note": "n"}
    r = derive_row(fake_rec, claim)
    say(r["source_id"] == "a" and r["also_sources"] == ["b"],
        "a two-source claim keeps both sources, in their own order")
    r = derive_row(fake_rec, {"value": "x", "confidence": "reconstructed", "note": "n",
                              "basis": {"kind": "rule", "id": "rule_x"}})
    say(r["source_id"] is None and "also_sources" not in r and "rule_x" in r["note"],
        "a reconstructed claim cites nothing and names its rule")
    say(r["basis"] == {"kind": "rule", "id": "rule_x", "note": "n"},
        "a basis that states no note carries the claim's own (T-2261)")
    rb = {"kind": "household", "match": "a plan of the post"}
    r = derive_row(fake_rec, {"value": "x", "confidence": "reconstructed", "note": "n",
                              "basis": {"kind": "rule", "id": "rule_x", "note": "the rule's"},
                              "replaceable_by": rb})
    say(r["basis"]["note"] == "the rule's" and r["replaceable_by"] == rb
        and r["replaceable_by"] is not rb,
        "the claim's basis and replaceable_by ride on the row, copied, not shared")
    r = derive_row(fake_rec, {"value": "x", "confidence": "attested", "sources": ["a"]})
    say("basis" not in r and "replaceable_by" not in r,
        "a claim with no words and no next rung adds neither key")
    def own_words(claim):
        return (claim.get("basis") or {}).get("note") or claim.get("note")
    say(all((r.get("basis") or {}).get("note") == own_words(cards[hid][FIELD_FOR[r["kind"]]])
            for hid, rs in proposal.items() for r in rs),
        "every copied row's basis is its claim's own words")

    print(f"{failed} failure(s)")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
