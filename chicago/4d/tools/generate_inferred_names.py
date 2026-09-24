#!/usr/bin/env python3
"""Give the reconstructed residents names, and say plainly that we made them up.

    python3 tools/generate_inferred_names.py           write
    python3 tools/generate_inferred_names.py --check   re-derive and diff

WHY THIS EXISTS, given that the records argued the opposite until now.

Every reconstructed person used to carry a designation — "A baker (inferred
resident, unnamed)" — and the note explained the choice: an invented surname
would make the record indistinguishable at a glance from the documented layer
beside it. That reasoning is sound about the DATA and wrong about the TOWN. A
place where a third of the households are called "an inferred cooper's
household" does not read as a reconstruction with honest gaps; it reads as a
spreadsheet. The owner asked for names, and the record says loudly enough which
layer it belongs to that a name cannot smuggle anything past a reader: the chip
says reconstructed, the note says HYPOTHESISED AND NOT A PERSON, and now a
`name_basis` block says the name itself was invented and what pool it came from.

WHAT KEEPS IT HONEST.

  1. The pools are bounded by evidence this project already holds. They are
     seeded from the 76 ATTESTED residents in data/residents/ — real people,
     named from cited sources — so an invented cooper is named the way this
     town's real coopers were named. See data/reconstruction/
     1835_invented_name_pools.json for the seeds and their citations.

  2. Assignment is DETERMINISTIC, from a hash of the person's id. Re-running
     produces the same town, `--check` proves the committed data is what this
     script derives, and nobody has to wonder whether a name drifted.

  3. The grade never moves. A person graded `reconstructed` keeps that grade,
     and `name_basis.confidence` is `reconstructed` too. validate.py refuses an
     invented name that claims anything better — which is the rule that stops
     this from becoming a way to launder inventions into the documented layer.

  4. Where the trade-to-community weighting is itself a guess, the note says so.
     Boatmen draw French colonial on evidence; labourers draw evenly BECAUSE the
     Irish labouring Chicago of popular memory arrives with the canal contracts
     of 1836, after this scene, and weighting them Irish would be importing a
     later decade into this one.
"""
import argparse
import hashlib
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from reconstructed_person import is_reconstructed  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
HOUSEHOLDS = ROOT / "data" / "residents" / "households"
POOLS = ROOT / "data" / "reconstruction" / "1835_invented_name_pools.json"
INDEX = ROOT / "data" / "residents" / "index.json"

# Trades this dataset records as held by a woman. Everything else draws male,
# mirroring the documented layer of household heads — and that is a statement
# about who the SOURCES named, not about who worked. Women's labour in this town
# is largely unrecorded rather than absent, and the reconstructed layer must not
# paper over a silence in the evidence by inventing against it.
FEMALE_TRADES = {"laundress", "domestic"}


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def dumps(doc, indent=1):
    return json.dumps(doc, indent=indent, ensure_ascii=False) + "\n"


def pick(seq, key, salt):
    """A stable choice from a list, keyed by the person's own id."""
    h = hashlib.sha256(f"{key}:{salt}".encode()).digest()
    return seq[int.from_bytes(h[:4], "big") % len(seq)]


def preference(pool, pid, salt):
    """This person's OWN ordering of a pool — their whole list of preferences.

    Not a single choice: the claim below walks this list until it finds a name
    the bucket can still afford, so a person who is outbid falls back to their
    own second choice rather than to whatever the arithmetic of their position
    hands them. Keyed on the person's id, so the ordering is a property of the
    person and moves nowhere when the town grows around them.
    """
    return sorted(pool, key=lambda n: hashlib.sha256(
        f"{pid}:{salt}:{n}".encode()).hexdigest())


def claim(pool, used, pid, salt, allowed=None):
    """The least-used name this person is willing and permitted to take.

    Least-used rather than unused, because two of the five buckets this layer
    populates are BIGGER than their pool — 73 yankee men draw on 36 surnames —
    so a surname must be reused and the only question is whether the reuse is
    even. Holding every claim to the current floor keeps the counts within one of
    each other, which is the spread the old index deal existed to produce.

    Ties inside a count are broken by the person's OWN preference order, which is
    what makes the result depend on who a person collides with rather than on how
    many people sort ahead of them.

    `allowed` rejects a candidate outright: it carries the one hard constraint,
    that no two invented residents may end up with the same full name.
    """
    order = preference(pool, pid, salt)
    for name in sorted(order, key=lambda n: used[n]):
        if allowed is None or allowed(name):
            used[name] += 1
            return name
    raise AssertionError(f"every name in a pool of {len(pool)} is refused for {pid}")


def community_for(pools, occupation, pid):
    rule = pools["trade_weights"].get(occupation) or pools["trade_weights"]["_default"]
    bag = []
    for cid, weight in rule["weights"].items():
        bag.extend([cid] * weight)
    bag.sort()
    return pick(bag, pid, "community"), rule


def overlay(files: dict) -> dict:
    """Apply the naming pass to an in-memory {path: text} map and hand it back.

    The household programme calls this so its drift check compares against the
    END of the pipeline rather than its own midpoint. Without it, every household
    reads as drifted the moment names exist, and a report that always cries wolf
    is not a report.
    """
    out = dict(files)
    named_files, _ = build(preload={p: json.loads(t) for p, t in files.items()
                                    if p.name.startswith("hh_")})
    out.update(named_files)
    return out


def build(preload: dict | None = None):
    pools = load(POOLS)
    by_id = {c["id"]: c for c in pools["communities"]}
    files = {}
    named = 0

    # TWO PASSES, because independent draws collide badly at this scale.
    #
    # Drawing each surname from a hash alone put four unrelated households under
    # "Lyman" and four more under "Gilbert" out of 92 people. That is not just
    # untidy: a shared surname reads as kinship, and this layer claims no
    # relationship whatever between its households. So the community is chosen
    # per person (pass one), and then each community's names are allocated in a
    # stable hash order (pass two) under a rule that spreads them as evenly as
    # the pool allows and repeats only when a pool genuinely runs out.
    #
    # WHAT PASS TWO USED TO DO, AND WHY IT CHANGED (ROADMAP K20). It dealt each
    # bucket round its pool BY INDEX — person i took given[i % n]. That spreads
    # perfectly and is stable across re-runs, which is what this file's own
    # docstring promised and what `--check` proved. What nobody had measured is
    # what it does when the town GROWS: an index is a function of how many people
    # sort ahead of you, so one insertion shifts everybody behind it by one and
    # renames them all. Measured with tools/measure_name_churn.py before the
    # change: a single synthetic household renamed up to 73 of the 113
    # reconstructed residents, 64.6 % of the layer, and never fewer than one.
    #
    # No name that came out of that was wrong — every name here is invented and
    # graded `reconstructed`, so all readings are equally honest. It was a REVIEW
    # defect: a block parcel adding four households shipped a diff in which its
    # four real additions could not be found, and a name that drifted because
    # something was actually wrong would have been invisible inside the noise.
    # Two parcels measured it in passing (T-A2h: 25 of 94; T-A5: 17 of 33) and
    # both read it as an oddity of their own diff rather than as a property.
    #
    # It now allocates by CLAIM instead: each person has their own deterministic
    # ordering of the pool, and walking the same stable order, each takes the
    # first name still at the floor of the use counts. The even spread survives —
    # the floor rule is what enforces it — but a person's name now depends on who
    # they actually collide with rather than on how many people precede them, so
    # an insertion costs the people it displaces and nobody else.
    people = []
    sources = preload if preload is not None else {
        path: load(path) for path in sorted(HOUSEHOLDS.glob("*.json"))}
    for path in sorted(sources):
        doc = sources[path]
        for person in doc.get("persons", []):
            if person.get("grade") != "reconstructed":
                continue
            # T-1171: …and not one T-1167's programme wrote. This allocator is the RETIRED
            # pass (T-0489); the programme that replaced it draws its own names from
            # data/reconstruction/1835_invented_name_pools.json, seeded and re-derivable,
            # and a name this one re-deals over that would overwrite a stage's own draw.
            if is_reconstructed(person):
                continue
            occ = (person.get("occupation") or {}).get("value") or ""
            cid, rule = community_for(pools, occ, person["id"])
            female = person.get("sex") == "female" or occ in FEMALE_TRADES
            people.append({"path": path, "doc": doc, "person": person, "cid": cid,
                           "rule": rule, "female": female, "occ": occ})

    # Deal within each (community, sex) bucket, ordered by a hash of the id so the
    # order is stable across runs and independent of filename or iteration order.
    buckets = {}
    for rec in people:
        buckets.setdefault((rec["cid"], rec["female"]), []).append(rec)
    for (cid, female), bucket in buckets.items():
        bucket.sort(key=lambda r: hashlib.sha256(r["person"]["id"].encode()).hexdigest())
        community = by_id[cid]
        givens = community["given_female" if female else "given_male"]
        surnames = community["surnames"]
        # THE TWO HALVES OF A NAME ARE NOT THE SAME PROBLEM, and the old deal
        # treated them as one by welding them to a shared index — everyone who
        # drew "Ezra" also drew "Kimball", so the pair repeated whole every time
        # the shorter pool wrapped.
        #
        # A repeated GIVEN name is what a real town looks like: five Johns among
        # 73 men is unremarkable in 1835 and carries no claim about anybody. So a
        # given name is simply each person's own first preference, with no ledger
        # at all, which is the most insertion-local rule there is — a new
        # neighbour cannot change what you are called.
        #
        # A repeated SURNAME is a claim, because a shared surname reads as
        # kinship and this layer asserts no relationship whatever between its
        # households. That one keeps the ledger and the floor rule.
        used_surname = {n: 0 for n in surnames}
        taken = set()
        for rec in bucket:
            pid = rec["person"]["id"]
            given = preference(givens, pid, "given")[0]
            # The one absolute: two invented residents may not be the same
            # person. Without this guard the town shipped two Alvah Hastings.
            surname = claim(surnames, used_surname, pid, "surname",
                            allowed=lambda s, g=given: (g, s) not in taken)
            taken.add((given, surname))
            rec["given"], rec["surname"] = given, surname

    docs = {}
    for rec in people:
        path, doc, person = rec["path"], rec["doc"], rec["person"]
        docs[path] = doc
        community = by_id[rec["cid"]]
        rule = rec["rule"]
        female = rec["female"]
        given, surname = rec["given"], rec["surname"]
        person["name"] = f"{given} {surname}"
        if female and not person.get("sex"):
            person["sex"] = "female"

        weighting = (
            f"The draw was weighted toward this community ON EVIDENCE: {rule['why']}"
            if rule["basis"] == "evidenced" else
            f"The community was drawn WITHOUT a weighting that any source supports. "
            f"{rule['why']}"
        )
        person["name_basis"] = {
            "value": f"invented from the {community['label']} pool",
            "confidence": "reconstructed",
            "sources": list(community["sources"]),
            "note": (
                "THE NAME IS INVENTED. No source names this resident, and this field is "
                "not a finding about anybody — it is a label so that a reconstructed "
                "household reads as a household rather than as a row in a table. "
                f"It was drawn from the {community['label']} pool in "
                "data/reconstruction/1835_invented_name_pools.json, which is seeded from "
                "the names of the 76 ATTESTED residents this project holds — real people, "
                "named from cited sources — so that an invented resident is named the way "
                "this town's documented residents were actually named rather than the way "
                "a story would name one. " + weighting + " The evidence for the pool "
                "itself: " + community["evidence"]
            ),
        }
        named += 1

    for path, doc in docs.items():
        # The household's own label follows its head. "A reconstructed baker's
        # household (south division)" is what the layer is FOR, and it is also
        # unreadable as a place where someone lived; "The Kellogg household — a
        # reconstructed baker (south division)" says both at once.
        #
        # "reconstructed", not "inferred", since K23a: the head's own `grade` is
        # `reconstructed` and the card prints that chip directly under this line,
        # so calling the household inferred claimed a tier better than its own
        # record — the middle tier means reasoned from evidence about this
        # particular person, and there is no particular person here.
        head = next((p for p in doc.get("persons", [])
                     if p.get("relationship") == "head"), None)
        if head and head.get("name"):
            trade = ((head.get("occupation") or {}).get("value") or "").replace("_", " ")
            doc["name"] = (f"The {head['name'].split()[-1]} household — a reconstructed "
                           f"{trade} ({doc.get('division', '')} division)")
        files[path] = dumps(doc)
    return files, named


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="re-derive and prove the allocation, and that none of it stands")
    args = ap.parse_args()

    files, named = build()
    if args.check:
        # THIS PASS OWNS NOTHING IN THE TREE, and that is the finding (T-1228).
        #
        # Until 2026-09-17 --check compared this pass's output against the tree at
        # the end of the build-name-replace pipeline. It did not report drift; it
        # CRASHED, with an unhandled FileNotFoundError on
        # hh_inf_carpenter_south_01.json. That file is one of the 96 households the
        # owner's T-0489 ruling of 2026-09-02 removed when it retired the
        # reconstructed resident population — and every person this pass has ever
        # named was graded `reconstructed`, so the ruling took all of them. Measured
        # the same day: not one household in data/residents/households carries a
        # name_basis block. There is nothing left of this pass on disk to diff.
        #
        # A pass that owns no committed file cannot have a drift gate over the tree,
        # so --check proves what is still true and still worth proving. The pass is
        # a live stage — the other two overlay it to derive their own comparisons —
        # and two properties of it are load-bearing: the allocation is
        # DETERMINISTIC (the promise K20's allocator and tools/measure_name_churn.py
        # exist to protect), and every name it deals carries a name_basis graded
        # `reconstructed`, which is the rule that stops an invention being laundered
        # into the documented layer. Then it asserts the retirement itself: if an
        # invented name reappears in the tree, this goes red.
        # THE TREE IS NOT THIS PASS'S INPUT and since T-0489 it is not even its
        # output, so the derivation starts where the pipeline starts: the household
        # programme's own recipe, expanded in memory. Calling build() bare here
        # would read the tree, find no reconstructed resident left in it, and deal
        # nought names — a gate that proves nothing by construction.
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
        import importlib.util  # noqa: PLC0415

        import inferred_household_ownership as ownership  # noqa: PLC0415

        spec = importlib.util.spec_from_file_location(
            "gen_households", pathlib.Path(__file__).with_name(
                "generate_inferred_households.py"))
        programme = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(programme)

        def deal():
            raw, _records, _hh = programme.build_all()
            return {q: json.loads(text) for q, text in
                    overlay({q: s for q, s in raw.items()
                             if q.name.startswith("hh_")}).items()}

        files, rederived = deal(), deal()
        named = sum(1 for doc in files.values() for person in doc.get("persons", [])
                    if person.get("grade") == "reconstructed")
        drift = ownership.check_names_pass(files, rederived)
        for item in drift:
            print(f"   DRIFT: {item}")
        if drift:
            print(f"   {len(drift)} finding(s) — see "
                  f"data/reconstruction/1835_inferred_household_pass_ownership.json")
            return 1
        print(f"   OK: {named} invented name(s) re-deal identically on a second "
              f"derivation, every one carrying a name_basis graded reconstructed, and "
              f"not one of them stands in the tree — T-0489's retirement holds")
        return 0

    for p, text in files.items():
        p.write_text(text, encoding="utf-8")

    # The manifest is deliberately NOT touched. Its `head` field carries the
    # person's ID, not their name — validate.py checks the two against each
    # other and the record is authoritative. Writing names into it replaced
    # 152 ids with display strings and failed the manifest against every
    # household in the dataset, attested ones included.

    print(f"named {named} reconstructed resident(s) across {len(files)} household(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
