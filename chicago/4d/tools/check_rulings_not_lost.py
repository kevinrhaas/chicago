#!/usr/bin/env python3
"""T-1124 — a judgement that is simply GONE, which no derivation can see.

On 10 September 2026 the merge lap pushed onto #1055 and
`data/research/land_sales/resident_rulings.json` conflicted. The file is
`hand_authored`; the lap's regex resolution took the branch's whole block for the
second conflict, and that branch had been cut before T-0850 and T-0990 cohort A
ruled. Forty entries left the file on one line, and twelve resident cards silently
got back a federal land purchase each had been ruled it could not have. #1073
restored them. This is the reason nobody was told.

`check.sh` was green on #1055 and on every commit after it, and it was RIGHT to be.
`read_land_sales.py --check` asks whether a ruling is WELL FORMED — that it names a
spelling the register holds, and a person the proposal named — and every surviving
ruling was. The eight that were left re-derived perfectly into a crosswalk perfectly
consistent with them. **A smaller rulings file is a legal rulings file**, and that is
the general shape: every gate this repository has re-derives DOWNSTREAM of its
hand-authored evidence, and a derivation cannot see a shrinking input. It just
derives less.

So this asks the one question a derivation cannot: is every judgement that was here
before still here? Two readings of "still here", both required:

  * BY IDENTITY — every (purchaser_as_read, resident_id) pair adjudicated at the
    merge base is adjudicated at HEAD. This is the strong one: it catches a swap,
    where one judgement leaves and another arrives and the total never moves.
  * BY COUNT — the adjudicated total may not fall. Redundant while the keys are
    unique, and kept because it is the number a person reads, and because it is what
    the incident is remembered by: 49 -> 9.

`ruled[]` and `retired[]` are counted TOGETHER, so retiring a ruling is a MOVE and
not a loss.

THE COMPARISON IS AGAINST THE MERGE BASE, never against a number committed beside the
file. A branch that dropped forty entries and also edited a total downwards would
satisfy any self-consistent check; it cannot satisfy this one, because the figure it
is held to lives in git and not in the tree it is editing.

**A DELIBERATE REMOVAL IS STILL POSSIBLE AND MUST STATE ITSELF.** A judgement that
should never have been made does not get deleted — it moves to `withdrawn[]`, which
this counts alongside `ruled[]` and `retired[]` and which requires a `reason` and the
`ticket` that decided it, exactly the way `retired[]` already carries its reason. The
total therefore never falls, and the record of what left says why. That is the same
trade the liberty ledger and the refusal lists make everywhere else in this project.

    tools/check_rulings_not_lost.py              the gate (base defaults to origin/dev)
    tools/check_rulings_not_lost.py --base REF   hold it to a different base
    tools/check_rulings_not_lost.py --self-test  prove the refusal fires

TWO STATES, deliberately different — T-1083's lesson, that a gate may not count a
skip as a pass:

  * `C4D_GATE_REQUIRE_BASE=1` (the workflow sets it) — a base ref that will not
    resolve is RED. In CI it always resolves; `actions/checkout` is pinned to
    `fetch-depth: 0`, which fetches every branch.
  * unset (an agent sandbox, a laptop, a shallow clone) — the same absence is a
    WARNING that names what went unasked, and the gate goes on.

REGISTRY, below: one entry per guarded file. The mechanism is already general; what
each new file needs is a READING of which of its stores hold a judgement and which
hold a transcription. T-1124 shipped the mechanism with land sales alone in it and
left that reading to T-1125.

T-1125 DID THE READING, on the nine files `grep -rl 'hand_authored|do not hand-edit'
data/research/` found on dev, and on one file that grep could not have found. Five are
guarded and five are REFUSED — refusals are in `REFUSED` below with the reason each was
turned away, because a file left silently out of a registry reads exactly like a file
nobody has looked at yet. The refusals are not a backlog: four of the five are DERIVED,
and guarding a derivation against shrinking is the gate that cries wolf the moment its
generator legitimately derives less.

The one file the grep could not find: `card_merge_crosswalk.json` carries the
`hand_authored` marks, but `consolidate_town_cards.py` WRITES it from
`data/residents/card_merge_rulings.json`, and that — outside data/research/ entirely —
is where the owner's 64 written merge rulings actually live. So the crosswalk is refused
and the store behind it is guarded. A registry that had taken the crosswalk at its word
would have guarded a mirror and left the original open.

THREE STORE SHAPES, because the evidence files have three and a guard that only reads
lists would have had to skip the largest hand-authored correction file in the tree:

    "added_rows"            a list of objects — the common case
    "lots"                  a MAPPING keyed by what it rules on (fergus's 113 lot
                            corrections); the key is offered to `identity` as `_key`
    "clusters[].rulings"    a list nested one level in (the 64 merge rulings sit inside
                            50 clusters); a row reaches its parent's fields with `^`

IDENTITY IS A UNION ACROSS A FILE'S STORES, never per-store: the key of a judgement has
to mean the same thing in every array it could sit in, or moving one from `ruled` to
`withdrawn` would read as a loss and an arrival. So `identity` names every field that
identifies a judgement ANYWHERE in the file and each entry fills the ones it carries.
The self-test asserts the result is still unique per file — a collision would let a loss
hide behind a duplicate, so the union is checked and not assumed.
"""
import argparse
import json
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
REPO = ROOT.parent.parent  # chicago/4d -> the monorepo root, which git speaks in

# path (repo-relative) -> what a judgement is in that file.
#   arrays  : the lists that hold one. Counted together; a move between them is not a loss.
#   identity: the fields that name one, in order. Their tuple is the key.
#   stated  : the array a deliberate withdrawal moves INTO, counted with the rest.
#   requires: the fields a `stated` entry must carry for the removal to have stated itself.
REGISTRY = {
    # T-1124. 49 adjudications of who bought federal land; #1055 lost forty of them.
    "chicago/4d/data/research/land_sales/resident_rulings.json": {
        "arrays": ["ruled", "retired", "withdrawn"],
        "identity": ["purchaser_as_read", "resident_id"],
        "stated": "withdrawn",
        "requires": ["reason", "ticket"],
        "reading": "T-1124. `ruled` and `retired` are the judgement; a retirement is a "
                   "move between them and not a loss.",
    },
    # T-1125, file 1 of 5. `hand_authored: true`, and its five judgement stores say
    # what the December 1835 trade census counted and who in the town answers to it.
    # LEFT OUT: `occupation_classes` maps the residents vocabulary onto a census word
    # and is a transcription of that vocabulary; `open_questions` is the opposite of a
    # judgement — it is what this pass declined to decide, and it SHOULD be able to
    # shrink, because a question leaves by being answered.
    "chicago/4d/data/research/books/trade_census_1835_spend_rulings.json": {
        "arrays": ["classes_ruled", "practitioners", "institutions",
                   "documented_absences", "register_records_not_assigned", "withdrawn"],
        "identity": ["class", "key", "id", "business_id"],
        "stated": "withdrawn",
        "requires": ["reason", "ticket"],
        "reading": "T-1125. A class ruled, a practitioner placed under it, an "
                   "institution present, an absence documented and a register record "
                   "deliberately not assigned are five ways of saying the same thing: "
                   "somebody decided. `occupation_classes` and `open_questions` are not.",
    },
    # T-1125, file 2 of 5. `generated_by: hand-authored (T-1006)`. 145 trade rulings and
    # four per-business overrides — the census class of every business in the register.
    # LEFT OUT: `vocabulary` transcribes the eighteen printed count-lines and its
    # `compared` flag is recomputed by `trade_census_1835.py --check`; `register_cautions`
    # is prose about the register, not a ruling on it; `boundaries` is the rule text the
    # rulings cite, and a rule is not one of the things it rules on.
    "chicago/4d/data/research/newspapers/trade_class_rulings.json": {
        "arrays": ["trade_rulings", "business_overrides", "withdrawn"],
        "identity": ["trade", "scope", "business_id"],
        "stated": "withdrawn",
        "requires": ["reason", "ticket"],
        "reading": "T-1125. `scope` is part of the identity because the same trade is "
                   "ruled twice, once inside the town and once outside it.",
    },
    # T-1125, file 3 of 5. `generated_by: hand-authored rulings (T-1048)`. 128 places the
    # newspapers name, each resolved inside or outside the committed town.
    # LEFT OUT: `counts` is recomputed field by field by `resolve_place_vocabulary.py
    # --check` from the gazetteer and these rulings, and the file says so itself; the
    # `derived` block inside each place is rewritten by the same tool, which is why the
    # identity is the `place` and not anything under it.
    "chicago/4d/data/research/newspapers/place_vocabulary.json": {
        "arrays": ["places", "withdrawn"],
        "identity": ["place"],
        "stated": "withdrawn",
        "requires": ["reason", "ticket"],
        "reading": "T-1125. A place resolved is a judgement; the counts over them are "
                   "arithmetic and are gated by recomputation already.",
    },
    # T-1125, file 4 of 5. "HAND-AUTHORED, and the only hand-authored file in this
    # reading" — 113 lot corrections keyed by lot id, a row the OCR gathered no ink for
    # at all, and six population figures read off the page image.
    # LEFT OUT: `what_the_image_could_not_settle` is a list of plain strings — a written
    # refusal to decide, with no entry to identify — and `read_off`, `grade_note` and
    # `bidder_note` are prose about the reading. The `lots` MAPPING is the reason this
    # guard grew a mapping shape: 113 of this file's 120 judgements sit in it, and a
    # list-only registry would have guarded the seven and called the file covered.
    "chicago/4d/data/research/directories/fergus_1839_lots_corrections.json": {
        "arrays": ["lots", "added_rows", "population", "withdrawn"],
        "identity": ["_key", "leaf", "half", "y", "column_first_year"],
        "stated": "withdrawn",
        "requires": ["reason", "ticket"],
        "reading": "T-1125. A correction is identified by the lot it corrects, or — for "
                   "a row and a population figure the printed page carries no id for — "
                   "by where on the leaf it was read.",
    },
    # T-1125, file 5 of 5, and NOT under data/research/. The owner's 64 written rulings
    # on which town cards are one person, nested one level inside the 50 clusters a
    # surname test proposed. `card_merge_crosswalk.json` is the landed mirror of this and
    # is refused below; this is the original. Losing one re-splits a resident.
    # LEFT OUT: `rules` is the rule text C0..C22 the rulings cite; `clusters[].
    # derived_candidate` and `why_not_derived` describe how the cluster was proposed; and
    # `also_ruled_on` is a LOG OF PASSES — a date, a ticket and a sentence about what that
    # pass decided — whose decisions are themselves in `clusters[].rulings`. Counting it
    # would be counting the same judgement twice under a key that is a date.
    "chicago/4d/data/residents/card_merge_rulings.json": {
        "arrays": ["clusters[].rulings", "deferred", "withdrawn"],
        "identity": ["^id", "rule"],
        "stated": "withdrawn",
        "requires": ["reason", "ticket"],
        "reading": "T-1125. A ruling is (the cluster it is about, the rule it applied). "
                   "`^id` reaches the parent cluster, because eleven clusters carry more "
                   "than one ruling and a cluster-level count would not see one leave.",
    },
}

# Refused entry, with the reason. A file left silently out of a registry reads like a
# file nobody has looked at; these have been looked at. T-1125's acceptance: "a file
# whose arrays are legitimately re-derivable is REFUSED entry to the registry with that
# stated, rather than added for completeness".
REFUSED = {
    "chicago/4d/data/research/residents/card_merge_crosswalk.json":
        "DERIVED. `consolidate_town_cards.py --apply` writes it from "
        "data/residents/card_merge_rulings.json, which IS in the registry above. "
        "Guarding the mirror as well would fire every time the generator legitimately "
        "lands fewer merges than the last run, and would still not protect the rulings.",
    "chicago/4d/data/research/residents/town_card_candidates.json":
        "DERIVED, and deliberately shrinking. The same tool writes it, and its `clusters` "
        "list is a WORKLIST that the tool's own docstring says is never a merge list — it "
        "gets SMALLER as clusters are ruled on, so a floor under its count would be a "
        "gate against the work getting done.",
    "chicago/4d/data/research/residents/scene_window_trade_audit.json":
        "DERIVED, and shrinking is the goal. `audit_scene_window_trades.py` rebuilds it, "
        "and every row is a person whose trade is cited by nothing yet; six rows today, "
        "and the ticket that owns it wants zero.",
    "chicago/4d/data/research/church/st_marys_baptisms_crosswalk.json":
        "DERIVED. `read_st_marys_baptisms.py --build` rebuilds all four of its "
        "judgement-shaped stores from the page readings. It HAD drifted off what that "
        "tool rebuilds; T-1110 closed that by rebuilding and gating `--check` in "
        "tools/check.sh, so the drift is now caught at its source rather than by a "
        "count frozen here. Its second input — data/residents/ — moves, and a count "
        "under it would fire on the town gaining a resident.",
    "chicago/4d/data/research/land_sales/school_section_sale_1833.json":
        "NOT A RULING FILE, and it says so: `the_ruling_is_not_here` points at "
        "land_sales/resident_rulings.json, which is registry entry one. "
        "`school_section_sale.py --build` recomputes every figure in it from the tract "
        "register; it is arithmetic over a source, and arithmetic has no judgements to lose.",
}


class Absent(Exception):
    """the file did not exist at that ref — a first commit, not a loss."""


def git(*args, ok=(0,)):
    r = subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True)
    if r.returncode not in ok:
        return None
    return r.stdout


def resolve_base(explicit=None):
    """the first ref that exists, in the order a run actually has one."""
    candidates = []
    if explicit:
        candidates.append(explicit)
    elif os.environ.get("C4D_RULINGS_BASE"):
        candidates.append(os.environ["C4D_RULINGS_BASE"])
    else:
        if os.environ.get("GITHUB_BASE_REF"):
            candidates.append("origin/" + os.environ["GITHUB_BASE_REF"])
        candidates += ["origin/dev", "dev", "origin/main"]
    for ref in candidates:
        if git("rev-parse", "--verify", "--quiet", ref + "^{commit}") is not None:
            return ref, candidates
    return None, candidates


def at_ref(path, ref):
    """the file's JSON at `ref`, or Absent if the ref did not carry it."""
    out = git("show", f"{ref}:{path}")
    if out is None:
        raise Absent(path)
    return json.loads(out)


def in_tree(path):
    p = REPO / path
    if not p.exists():
        raise Absent(path)
    return json.loads(p.read_text(encoding="utf-8"))


def rows(doc, name):
    """every judgement-bearing object in the store `name` names.

    Three shapes, because the evidence files have three (T-1125):
      * `added_rows`         — a list of objects, the common case;
      * `lots`               — a MAPPING keyed by the thing it rules on, whose key is the
                               identity and is offered to `identity` as `_key`;
      * `clusters[].rulings` — a list nested one level inside another, whose rows carry
                               their parent under `_parent` so `^field` can reach it.
    A store the file does not carry yields nothing: `withdrawn` is absent until the first
    stated removal, and a registry entry may name an array a future commit adds.
    """
    if "[]." in name:
        outer, inner = name.split("[].", 1)
        for parent in doc.get(outer) or []:
            if not isinstance(parent, dict):
                continue
            for child in parent.get(inner) or []:
                if isinstance(child, dict):
                    yield dict(child, _parent=parent)
        return
    store = doc.get(name)
    if isinstance(store, dict):
        for key, value in store.items():
            yield dict(value if isinstance(value, dict) else {}, _key=key)
        return
    for entry in store or []:
        if isinstance(entry, dict):
            yield entry


def field(entry, name):
    """one identity field. `^x` reads x from the row's parent, `_key` from its map key."""
    if name.startswith("^"):
        parent = entry.get("_parent")
        if isinstance(parent, dict) and name[1:] in parent:
            return str(parent[name[1:]])
        # No parent: a withdrawal leaving a nested store lands in a FLAT array, and has
        # to be able to state the identity it had. It does so by carrying the field
        # itself, and the key it produces is the same one.
        return str(entry.get(name[1:], ""))
    return str(entry.get(name, ""))


def adjudications(doc, spec):
    """every judgement in `doc`, as key -> the store it sits in.

    The identity is a UNION across the file's stores and never per-store, so that a
    judgement moving between them — ruled to retired, ruled to withdrawn — keeps the
    same key and reads as a move rather than a loss and an arrival.
    """
    found = {}
    for name in spec["arrays"]:
        for entry in rows(doc, name):
            key = tuple(field(entry, f) for f in spec["identity"])
            found.setdefault(key, name)
    return found


def malformed_withdrawals(doc, spec):
    """a withdrawal that does not say why is not a stated removal."""
    out = []
    for entry in rows(doc, spec["stated"]):
        key = " / ".join(field(entry, f) or "?" for f in spec["identity"])
        missing = [f for f in spec["requires"] if not field(entry, f).strip()]
        if missing:
            out.append(f"{key} — no {', '.join(missing)}")
    return out


def compare(path, spec, base_doc, head_doc):
    """the whole judgement, as (failures, note). base_doc None = nothing to compare."""
    fails = []
    for bad in malformed_withdrawals(head_doc, spec):
        fails.append(f"{path}: a withdrawal that states no reason is a deletion: {bad}")

    head = adjudications(head_doc, spec)
    if base_doc is None:
        return fails, f"{path}: {len(head)} adjudication(s); no base copy to compare"

    base = adjudications(base_doc, spec)
    gone = sorted(k for k in base if k not in head)
    if gone:
        fails.append(
            f"{path}: {len(gone)} judgement(s) adjudicated at the base are GONE — "
            "a ruling leaves by moving into "
            f"{spec['stated']}[] with a reason, never by being deleted:")
        for k in gone[:12]:
            fails.append(f"        · {' / '.join(k)}  (was in {base[k]}[])")
        if len(gone) > 12:
            fails.append(f"        · …and {len(gone) - 12} more")
    if len(head) < len(base):
        fails.append(
            f"{path}: the adjudicated total FELL, {len(base)} -> {len(head)}, "
            f"counting {' + '.join(spec['arrays'])} together")
    return fails, f"{path}: {len(base)} -> {len(head)} adjudication(s), none lost"


def run(base_ref, registry=REGISTRY, quiet=False):
    """0 green, 1 red. base_ref None means there was nothing to compare against."""
    fails = []
    for path, spec in registry.items():
        try:
            head_doc = in_tree(path)
        except Absent:
            fails.append(f"{path}: the registry names a file this tree does not carry")
            continue
        base_doc = None
        if base_ref:
            try:
                base_doc = at_ref(path, base_ref)
            except Absent:
                pass
        f, note = compare(path, spec, base_doc, head_doc)
        fails += f
        if quiet:
            continue
        # A file says ONE thing — its clean note, or its failures. Never both: a
        # transcript that opens "none lost" and then lists what was lost is the kind
        # of line three tickets have been filed against (T-0763).
        if f:
            for line in f:
                print(line if line.startswith("      ") else f"   FAIL  {line}")
        else:
            print(f"   ok    {note}")
    return 1 if fails else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", help="the ref to hold this tree to (default: origin/dev)")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()

    ref, tried = resolve_base(args.base)
    if ref is None:
        required = bool(os.environ.get("C4D_GATE_REQUIRE_BASE"))
        print(f"   {'FAIL ' if required else 'WARN '} no base ref resolved "
              f"(tried {', '.join(tried)}), so nothing can say whether a judgement left")
        for path in REGISTRY:
            print(f"            · {path} went unasked")
        print("   " + ("FAIL  a GATE may not count a skip as a pass — fetch the base ref"
                       if required else
                       "WARN  this is a sandbox or a shallow clone, so the gate goes on. "
                       "CI sets C4D_GATE_REQUIRE_BASE=1 and would be red here."))
        return 1 if required else 0

    merge_base = (git("merge-base", ref, "HEAD") or "").strip()
    if not merge_base:
        # A detached or unrelated HEAD: the ref resolves but shares no history. Hold to
        # the ref itself rather than to nothing — stricter, and never wrong.
        merge_base = ref
    print(f"   ok    base {ref} at {merge_base[:9]}")
    return run(merge_base)


# ---------------------------------------------------------------------------
# the self-test — the check.sh convention (T-0763): prove the refusal FIRES.

INCIDENT = {
    "before": "07a6a1b04",   # 49 ruled, 0 retired
    "after": "02ce7d97a",    # 8 ruled, 1 retired — forty judgements gone
    "restored": "2e5aa8a02",  # 47 ruled, 2 retired — the same 49, two of them moved
}
LAND_SALES = "chicago/4d/data/research/land_sales/resident_rulings.json"


def drop_one(doc, spec):
    """the same tree with exactly ONE judgement taken out, whatever shape holds it.

    Returns (tree, the store it came out of), or (None, None) if the file carries no
    judgement at all — which is itself a failure, and the caller says so.
    """
    cut = json.loads(json.dumps(doc))
    for name in spec["arrays"]:
        if "[]." in name:
            outer, inner = name.split("[].", 1)
            for parent in cut.get(outer) or []:
                if isinstance(parent, dict) and parent.get(inner):
                    parent[inner] = parent[inner][1:]
                    return cut, name
        elif isinstance(cut.get(name), dict) and cut[name]:
            del cut[name][next(iter(cut[name]))]
            return cut, name
        elif cut.get(name):
            cut[name] = cut[name][1:]
            return cut, name
    return None, None


def _pair(base_ref, head_ref):
    spec = REGISTRY[LAND_SALES]
    return compare(LAND_SALES, spec, at_ref(LAND_SALES, base_ref), at_ref(LAND_SALES, head_ref))[0]


def self_test():
    ok = True
    spec = REGISTRY[LAND_SALES]

    def check(cond, bad):
        nonlocal ok
        if not cond:
            print(f"   FAIL self-test {bad}")
            ok = False

    have_history = all(git("rev-parse", "--verify", "--quiet", c + "^{commit}")
                       for c in INCIDENT.values())
    if have_history:
        print("   fires: the #1055 incident itself — 49 adjudications down to 9")
        broke = _pair(INCIDENT["before"], INCIDENT["after"])
        check(broke, "the commits that lost forty rulings passed the check")
        check(any("GONE" in f for f in broke), "the incident failed for some other reason")
        print("   passes: #1073's restoration against the same base — 47 + 2 is the same 49")
        check(not _pair(INCIDENT["before"], INCIDENT["restored"]),
              "the restored tree was called a loss")
        print("   passes: a tree against itself")
        check(not _pair(INCIDENT["restored"], INCIDENT["restored"]),
              "a tree was called a loss against itself")
    else:
        print("   WARN  the #1055 commits are not in this clone (shallow?) — "
              "the fixture pair went unasked")

    # The synthetic half, which needs no history and so always runs.
    base = in_tree(LAND_SALES)
    print("   fires: one entry removed from the tree under test")
    cut = json.loads(json.dumps(base))
    cut["ruled"] = cut["ruled"][1:]
    check(compare(LAND_SALES, spec, base, cut)[0], "a removed ruling was not a failure")

    print("   fires: a swap — one judgement out, one in, and the total never moves")
    swap = json.loads(json.dumps(base))
    swap["ruled"] = swap["ruled"][1:] + [dict(swap["ruled"][0], purchaser_as_read="A STRANGER")]
    check(len(adjudications(swap, spec)) == len(adjudications(base, spec)),
          "the swap fixture moved the total, so it is not testing identity")
    check(compare(LAND_SALES, spec, base, swap)[0], "a swapped judgement passed on count alone")

    print("   passes: the same ruling RETIRED — a move between the counted arrays")
    moved = json.loads(json.dumps(base))
    moved["retired"] = moved["retired"] + [moved["ruled"][0]]
    moved["ruled"] = moved["ruled"][1:]
    check(not compare(LAND_SALES, spec, base, moved)[0], "retiring a ruling was called a loss")

    print("   passes: a ruling WITHDRAWN with a reason and the ticket that decided it")
    withdrawn = json.loads(json.dumps(base))
    # APPEND, exactly as the `retired` fixture above does. Assigning the list
    # outright was fine only while the tree's own `withdrawn[]` was empty, and the
    # moment a real judgement was withdrawn — T-1132, the land register's
    # PEARSON HIRAM — the fixture deleted it and this assertion failed for a
    # withdrawal the tool had in fact accepted. A fixture must move ONE judgement,
    # never clear an array it does not own.
    withdrawn["withdrawn"] = withdrawn.get("withdrawn", []) + [
        dict(withdrawn["ruled"][0],
             reason="the register row was a second hand's marginal",
             ticket="T-1124")]
    withdrawn["ruled"] = withdrawn["ruled"][1:]
    check(not compare(LAND_SALES, spec, base, withdrawn)[0],
          "a stated withdrawal was refused")

    print("   fires: the same withdrawal with no reason written")
    silent = json.loads(json.dumps(withdrawn))
    silent["withdrawn"] = [{k: v for k, v in silent["withdrawn"][0].items() if k != "reason"}]
    check(compare(LAND_SALES, spec, base, silent)[0],
          "a withdrawal that states nothing was accepted as a stated removal")

    # EVERY REGISTERED FILE, on its own tree (T-1125). The land-sales fixtures above are
    # the #1055 incident itself and cannot be written for a file that has not had one; so
    # each entry earns its place by the same four demonstrations against the committed
    # tree — a removal fires, a stated withdrawal of the SAME judgement does not, the same
    # withdrawal with nothing written does, and the identity is unique so a loss cannot
    # hide behind a duplicate.
    for path, s in REGISTRY.items():
        print(f"   — {path.split('/')[-1]}")
        doc = in_tree(path)
        found = adjudications(doc, s)
        total = sum(1 for a in s["arrays"] for _ in rows(doc, a))
        check(total > 0, f"{path} carries none of the stores the registry names")
        check(s["stated"] in s["arrays"],
              f"{path}: the stated-withdrawal array is not one of the counted ones")
        # The trap this registry fell into while it was being written: `ticket` named
        # both the ruling and the withdrawal, so writing the withdrawal's own ticket
        # CHANGED the identity and a stated removal read as a loss. A field cannot be
        # both what a judgement is and what its removal has to say.
        check(not (set(f.lstrip("^") for f in s["identity"]) & set(s["requires"])),
              f"{path}: an identity field is also a required withdrawal field, so a "
              f"stated removal cannot keep the identity it had")
        check(len(found) == total,
              f"{path}: two judgements share an identity key, so a loss could hide "
              f"behind a duplicate ({len(found)} keys over {total} rows)")

        cut, store = drop_one(doc, s)
        check(cut is not None, f"{path}: no store to take a judgement out of")
        if cut is None:
            continue
        print(f"     fires: one judgement out of {store}[]  "
              f"({total} adjudication(s) registered)")
        check(compare(path, s, doc, cut)[0],
              f"{path}: a removed judgement was not a failure")

        left = sorted(set(found) - set(adjudications(cut, s)))
        check(len(left) == 1, f"{path}: dropping one row moved {len(left)} keys")
        if len(left) != 1:
            continue
        stated = {f.lstrip("^"): v for f, v in zip(s["identity"], left[0])}
        stated.update(reason="the self-test's own withdrawal", ticket="T-1125")
        spoken = json.loads(json.dumps(cut))
        spoken[s["stated"]] = list(spoken.get(s["stated"]) or []) + [stated]
        print(f"     passes: the same judgement withdrawn into {s['stated']}[] with a reason")
        check(not compare(path, s, doc, spoken)[0],
              f"{path}: a stated withdrawal could not reproduce the identity it had")
        print("     fires: the same withdrawal with nothing written")
        silent = json.loads(json.dumps(spoken))
        silent[s["stated"]][-1] = {k: v for k, v in stated.items() if k != "reason"}
        check(compare(path, s, doc, silent)[0],
              f"{path}: a withdrawal that states nothing was accepted")

    # A REFUSAL ROTS TOO. A file turned away for being derived may stop being derived, or
    # may simply be renamed, and either way the reason on record stops being about
    # anything. T-1125's acceptance asks for the reason to be written down; this asks for
    # it to still be attached to something.
    print("   ok: every refused file is still in the tree, and refused for one reason")
    for path, why in REFUSED.items():
        check((REPO / path).exists(),
              f"{path} is REFUSED entry to the registry but is no longer in the tree")
        check(path not in REGISTRY, f"{path} is both registered and refused")
        check(len(why) > 60, f"{path}: the refusal does not say why")

    # THE WORKFLOW IS HALF OF THIS CHECK, so it is asserted rather than assumed —
    # check_gate_readers.py's rule, for the same reason. The comparison needs a base
    # ref in the clone, which is `fetch-depth: 0`, and it needs the absence of one to
    # be RED in CI, which is C4D_GATE_REQUIRE_BASE. Either one quietly removed turns
    # this step into a skip that counts as a pass.
    wf = REPO / ".github/workflows/chicago-4d-check.yml"
    if wf.exists():
        src = wf.read_text(encoding="utf-8")
        print("   ok: the gate workflow still fetches a base ref and requires one")
        check("fetch-depth: 0" in src,
              "the gate workflow no longer fetches history, so no base ref will resolve")
        check("C4D_GATE_REQUIRE_BASE" in src,
              "the gate workflow no longer requires a base ref, so CI counts the skip as a pass")
    else:
        print("   WARN  the gate workflow is not in this checkout — its half went unasked")

    print("   self-test: a lost judgement fails, a moved or stated one does not"
          if ok else "   self-test: FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
