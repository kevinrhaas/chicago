#!/usr/bin/env python3
"""The 1904 people directory, and the gate a later scene's household cards pass (T-2702).

    python3 tools/test_people_scene.py              the committed directory is honest
    python3 tools/test_people_scene.py --self-test  each planted fault is refused by name

A scene other than 1835 keeps its own households in data/residents_<scene>/households/,
and tools/compile_scene.py compiles them into data/sidecars/<scene>/people.json with the
same generator as 1835 (`compile_people`). This holds what that must mean:

  - the 1904 directory carries exactly the people its own cards hold, and none of
    1835's — the fault T-1739 fixed, when 1904 carried 3,308 people of 1835;
  - every row is attested or carries the card's reasoning, and lives in a structure that
    stands in the scene;
  - the Glessner summary record's residents are the directory's people, by id;
  - and T-1740 STAYS TRUE: the 1904 scene does not list the `residents` layer, so the
    drawer offers no People section. That layer is the drawer's People, City, Population
    and Order book, which read the 1835 town's files; a two-person 1904 directory is read
    by the summary records and, later, the Navigator's People app, not by them.

--self-test plants each fault in a scratch copy of a card and requires
`scene_people_manifest` to refuse it.
"""
import copy
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import compile_scene as cs  # noqa: E402

DATA = ROOT / "data"
fails = []


def fail(msg):
    fails.append(msg)
    print(f"  FAIL  {msg}")


def ok(msg):
    print(f"  ok    {msg}")


def check_how_known():
    """Only the explicit invented trade-head category loses the source-named fallback."""
    rows = json.loads((DATA / "sidecars/1835/people.json").read_text())["people"]
    by_id = {row["id"]: row for row in rows}
    def raw(ident):
        card = json.loads((DATA / "residents" / by_id[ident]["file"]).read_text())
        return next(p for p in card["persons"] if p["id"] == ident)
    person = raw("rc_bardwell_otis")
    before = copy.deepcopy(person)
    cases = [("actual invented Bardwell", person, False, "reconstructed"),
             ("attested source-named", {"grade": "attested"}, False, "documented"),
             ("inferred source-named", {"grade": "inferred"}, False, "documented"),
             ("grade-reconstructed projected source name", {"grade": "reconstructed", "resident_subtype": "projected_resident"}, False, "projected"),
             ("grade-reconstructed post-office name", {"grade": "reconstructed", "letter_list_only": True}, False, "letter_list"),
             ("grade-reconstructed civic name", {"grade": "reconstructed", "civic_mint": True}, False, "civic_mint"),
             ("visitor category retained", person, True, "transient"),
             ("trade category with civic evidence", {**person, "civic_mint": True}, False, "civic_mint"),
             ("trade category with letter evidence", {**person, "letter_list_only": True}, False, "letter_list"),
             ("grade alone proves no invented name", {"grade": "reconstructed"}, False, "documented")]
    for ident in ("stephen_r_beggs", "susan_anderson", "pay_co_je_bai", "nau_con_ne_bec", "maub_biss"):
        source_named = raw(ident)
        if not source_named.get("name_as_read"):
            fail(f"{ident}: source-read negative control lost its actual name provenance")
        cases.append((f"actual source-read {ident}", source_named, False, "documented"))
    for label, row, transient, expected in cases:
        got = cs.how_known(row, transient=transient)
        if got != expected:
            fail(f"{label}: how_known {got!r}, expected {expected!r}")
        else:
            ok(f"{label}: {expected}")
    trade_rows = [row for row in rows if row.get("resident_subtype") == "reconstructed_trade_head"]
    for row in trade_rows:
        minted = raw(row["id"])
        basis = (minted.get("name_basis") or {}).get("basis") or {}
        if (minted.get("name_as_read") or basis.get("id") != "1835_invented_name_pools"
                or (minted.get("reconstruction") or {}).get("stage") != "trade_households"
                or cs.how_known(minted) != "reconstructed"):
            fail(f"{row['id']}: trade-head category no longer proves a model-minted identity")
    if not trade_rows:
        fail("actual reconstructed trade-head provenance control is empty")
    else:
        ok(f"all {len(trade_rows)} actual trade heads retain explicit invented-name provenance")
    if person != before:
        fail("how_known changed the person's existing identity/grade/source record")


def check_known_tallies(directory=None):
    """The card/filter identity categories and declared counts agree; source-flag overlaps remain."""
    directory = directory or json.loads((DATA / "sidecars/1835/people.json").read_text())
    rows = directory["people"]
    counts = directory["counts"]
    residents = [r for r in rows if r["how_known"] != "transient"]
    trade_ids = {r["id"] for r in rows if r.get("resident_subtype") == "reconstructed_trade_head"}
    model_ids = {r["id"] for r in rows if r["how_known"] == "reconstructed"}
    expected = {"documented": sum(r["how_known"] == "documented" for r in residents),
                "reconstructed_identities": len(model_ids),
                "letter_list_only": sum(bool(r["letter_list_only"]) for r in residents),
                "civic_mint": sum(bool(r["civic_mint"]) for r in residents),
                "projected_residents": sum(r["resident_subtype"] == "projected_resident" for r in residents)}
    for key, value in expected.items():
        if counts.get(key) != value:
            fail(f"people counts.{key} is {counts.get(key)!r}, but actual card/filter rows count {value}")
    if not trade_ids or model_ids != trade_ids:
        fail("reconstructed identity card category is not exactly the explicitly minted trade-head set")
    else:
        ok(f"{len(trade_ids)} actual trade-head identity cards agree with the reconstructed tally; source counts preserved")


def check():
    root = cs.residents_root("1904")
    cards = sorted((root / "households").glob("*.json"))
    held = {p["id"] for c in cards for p in json.loads(c.read_text())["persons"]}
    directory = json.loads((DATA / "sidecars" / "1904" / "people.json").read_text())
    rows = {r["id"]: r for r in directory["people"]}
    if set(rows) == held and held:
        ok(f"the 1904 directory holds exactly its own cards' {len(held)} people")
    else:
        fail(f"1904 directory {sorted(rows)} is not its cards' people {sorted(held)}")
    legacy = json.loads((DATA / "sidecars" / "1835" / "people.json").read_text())
    stray = set(rows) & {r["id"] for r in legacy["people"]}
    if stray:
        fail(f"1835 people in the 1904 directory: {sorted(stray)[:5]}")
    else:
        ok("no 1835 person is in the 1904 directory")
    if directory.get("residents_root") == "data/residents_1904":
        ok("its rows point into data/residents_1904/")
    else:
        fail(f"residents_root is {directory.get('residents_root')!r}")
    standing = {p.stem for p in (DATA / "sidecars" / "1904").glob("*.json")}
    for r in rows.values():
        if r["grade"] not in ("attested", "inferred", "reconstructed"):
            fail(f"{r['id']}: grade {r['grade']!r}")
        if r["lives_at"] and r["lives_at"] not in standing:
            fail(f"{r['id']}: lives at {r['lives_at']}, which does not stand in 1904")
    ok("every row is graded and lives in a 1904 structure")
    summary = json.loads((DATA / "summaries" / "glessner_house.json").read_text())
    named = [r["person"] for r in summary["residents"]]
    if named and all(n in rows and rows[n]["lives_at"] == "glessner_house" for n in named):
        ok(f"the Glessner record's residents ({', '.join(named)}) live at glessner_house in the directory")
    else:
        fail(f"the Glessner record's residents {named} are not the directory's people at glessner_house")
    layers = json.loads((DATA / "scenes" / "1904.json").read_text()).get("layers", [])
    if "residents" not in layers:
        ok("T-1740 holds: 1904 does not list `residents`, so the drawer offers no People section")
    else:
        fail("1904 lists `residents`: the drawer would mount the 1835 town's People, City, "
             "Population and Order book over a two-person directory")


def self_test():
    src = cs.residents_root("1904") / "households" / "hh_glessner_john_j.json"
    good = json.loads(src.read_text())

    def planted(name, mutate, expect):
        card = copy.deepcopy(good)
        mutate(card)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "households").mkdir()
            (root / "households" / f"{card.get('id', 'x')}.json").write_text(json.dumps(card))
            try:
                cs.scene_people_manifest("1904", root)
            except SystemExit as e:
                if expect in str(e):
                    ok(f"refused: {name}")
                    return
                fail(f"{name}: refused, but not for `{expect}`: {e}")
                return
            fail(f"{name}: accepted")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "households").mkdir()
        (root / "households" / src.name).write_text(json.dumps(good))
        try:
            cs.scene_people_manifest("1904", root)
            ok("the committed card passes")
        except SystemExit as e:
            fail(f"the committed card is refused: {e}")

    def p0(c):
        return c["persons"][0]
    planted("an attested person with no source", lambda c: p0(c).pop("sources"), "cites no source")
    planted("a person with no grade", lambda c: p0(c).pop("grade"), "has grade `None`")
    planted("an inferred person with no note", lambda c: p0(c).update(grade="inferred"), "with no note")
    planted("a source that does not resolve", lambda c: p0(c).update(sources=["no_such_source"]), "does not resolve")
    planted("a home that does not stand in the scene",
            lambda c: c["associated_with"][0].update(place_or_structure_id="no_such_house"), "does not stand")
    planted("an arrival after the scene date", lambda c: c["arrival"].update(value="1905-01-01"), "after the scene date")
    planted("a household of nobody", lambda c: c.update(persons=[]), "nobody in it")
    planted("a card for another scene", lambda c: c.update(scene="1835"), "is not 1904")


if __name__ == "__main__":
    check_how_known()
    check_known_tallies()
    (self_test if "--self-test" in sys.argv else check)()
    if fails:
        print(f"FAIL: {len(fails)} problem(s)")
        sys.exit(1)
    print("OK" + (": every planted fault was refused by name" if "--self-test" in sys.argv
                  else ": the 1904 directory is its own, and the drawer still offers no People section"))
