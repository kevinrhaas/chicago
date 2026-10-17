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
    (self_test if "--self-test" in sys.argv else check)()
    if fails:
        print(f"FAIL: {len(fails)} problem(s)")
        sys.exit(1)
    print("OK" + (": every planted fault was refused by name" if "--self-test" in sys.argv
                  else ": the 1904 directory is its own, and the drawer still offers no People section"))
