#!/usr/bin/env python3
"""The grade of a STRUCTURE, as the owner defined it on 2026-10-16 (T-2686, AGENTS.md rule 12).

    "for a structure if there is an image of it that is reasonable, not just like a corner or
    side, but even the robert [law] house we did earlier, that is attested, something inferred
    would be like we only have the sanborn map level description, or some text description of
    it, but nothing to visually depict its size or scope or appearance, and then reconstructed
    will be where we made a determined choice that there should have been, based on model of
    town or other guiding research that there could have or would have been a structure of
    that type and form and appearance there"

Every ATTRIBUTE keeps its own grade (docs/PROVENANCE.md, "Confidence is per attribute"). This is
the one word for the building as a whole, and it answers a different question from
`documented_range.confidence` ("did a source say it stood here?"): do we know what it LOOKED
like? A Sanborn footprint says a house stood on its lot and how big its plan was; it does not
say what the house looked like. So:

  attested       a reasonable picture of it exists (DEPICTED below)
  inferred       not pictured, and a map or a text records that it stood here
  reconstructed  not pictured, and its existence is itself reconstructed — our model of the
                 town, or other guiding research, placed it

WHAT COUNTS AS A REASONABLE PICTURE. The pictures are the ones the card's Images tab shows
(tools/compile_pictures.py joins them: the Prairie library's image records for 1904, the
photograph and illustration records in data/sources/ a structure cites, and the picture of
every image-gate camera). Of those, a picture DEPICTS the structure when

  1. it is a library record whose view shows the building whole — a front elevation, an
     oblique front, a side elevation or a rear view (VIEWS_THAT_SHOW_IT); or
  2. an image-gate camera has been solved on it for this structure
     (data/reference_views/<id>/<view>.json): fitting a camera to a building is the proof the
     building is in the picture well enough to be matched; or
  3. data/structure_grades.json rules it in, with the reason.

and data/structure_grades.json can rule a picture OUT, with the reason (a front elevation that
turns out to show another house, say). A detail, an interior, a plan or section, or a street
view, aerial or bird's-eye view the building merely stands in does not count by itself: the
owner's "not just like a corner or side". A street view that does show the house well is ruled
in by name, or gets its camera solved.

THE 1835 STREETS. A street's form is its line and its width, and a plat or survey that draws it
is a picture of exactly that. So a street whose own record cites one of the maps
data/structure_grades.json lists for its scene is attested; any other street keeps the grade
of its line (`geometry_confidence`), which is the claim its ribbon has always stood on.

    python3 tools/grade_structures.py              the table: every structure's grade, by scene
    python3 tools/grade_structures.py --check      validate the rulings; print the counts
    python3 tools/grade_structures.py --self-test  break each branch of the rule on fixtures

compile_scene.py calls `grader()` and writes the grade into every sidecar (and every 1835
street), so `compile_scene.py --check` is what holds the committed grades to this rule: adding a
picture to the library, or solving a camera, moves the grade, and the sidecar must be compiled
again in the same change.
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RULINGS = ROOT / "data" / "structure_grades.json"
LEVELS = ("attested", "inferred", "reconstructed")

#: Library views that show a building whole. Everything else in the library's vocabulary is a
#: part of it (detail, entrance/roof/courtyard detail, interior, plan, section, courtyard) or a
#: picture of something larger that it stands in (street view, aerial, map, site plan).
VIEWS_THAT_SHOW_IT = {"front elevation", "oblique front", "side elevation", "rear"}

#: The programme's own prefixes for an invented roof (tools/audit_confidence.py INVENTED_ID).
#: Nothing invented can have a picture of itself, so a ruling that says one does is refused.
INVENTED_ID = re.compile(r"^(recon_|inf_)")

#: What the card says, in a visitor's words. One line each; the Images tab carries the pictures.
WHY = {
    "attested": "Pictured: {n} of the pictures on the Images tab show it.",
    "attested_one": "Pictured: a picture on the Images tab shows it.",
    "inferred": "Known from maps or written records; no picture of it has been found.",
    "reconstructed": "Placed by our reconstruction of the town; no source pictures or records it here.",
}
STREET_WHY = {
    "attested": "Drawn on the {maps}.",
    "inferred": "Reasoned from the surveys; no map of the time draws this line.",
    "reconstructed": "Placed by our reconstruction of the town; no map of the time draws it.",
}


def load_rulings(path=RULINGS):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}


def depicting(sid, pictures, cameras, rulings, scene):
    """-> sorted ids of the pictures that depict structure `sid` (see the header)."""
    out = set()
    for p in pictures or []:
        if p.get("library") and p.get("view") in VIEWS_THAT_SHOW_IT:
            out.add(p["id"])
    for cam in cameras or []:
        pic = cam.get("library_image") or cam.get("source_id")
        if pic:
            out.add(pic)
    for r in rulings.get("pictured", []):
        if r.get("structure") == sid and r.get("scene") == scene:
            out.add(r["picture"])
    for r in rulings.get("not_pictured", []):
        if r.get("structure") == sid and r.get("scene") == scene:
            out.discard(r["picture"])
    return sorted(out)


def grade_structure(sid, existence, pictures, cameras, rulings, scene):
    """-> the sidecar's `grade` block: {value, why, pictures}."""
    shown = depicting(sid, pictures, cameras, rulings, scene)
    if shown:
        value = "attested"
        why = WHY["attested_one"] if len(shown) == 1 else WHY["attested"].format(n=len(shown))
    elif existence == "reconstructed" or existence not in LEVELS:
        value, why = "reconstructed", WHY["reconstructed"]
    else:
        value, why = "inferred", WHY["inferred"]
    return {"value": value, "why": why, "pictures": shown}


def grade_street(raw, scene, rulings, sources):
    """-> a street's `grade` block: {value, why}."""
    maps = (rulings.get("street_maps", {}).get(scene) or {}).get("maps", [])
    drawn = [m for m in maps if m in (raw.get("sources") or [])]
    if drawn:
        names = []
        for m in drawn:
            names.append(MAP_NAMES.get(m) or m)
        names = list(dict.fromkeys(names))
        text = names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]
        return {"value": "attested", "why": STREET_WHY["attested"].format(maps=text)}
    line = raw.get("geometry_confidence", "reconstructed")
    if line == "attested":
        return {"value": "attested", "why": "Its line is attested by a source."}
    value = line if line in LEVELS else "reconstructed"
    return {"value": value, "why": STREET_WHY[value]}


#: The maps' names as a visitor reads them on the street's card.
MAP_NAMES = {
    "thompson_plat_1830": "1830 town plat",
    "wright_1834": "1834 survey",
    "wright_1834_nara_hup": "1834 survey",
    "hathaway_1834": "1834 survey",
}


def grader(scene_ids=None):
    """-> (grade(scene, sid, existence) -> block, rulings) for compile_scene.

    The picture join is computed once, from the tree as it stands."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import compile_pictures as cp
    images, tsv, sources, texts, _listed, cams = cp.read_tree()
    # Every structure record against every scene, not the sidecars already on disk: the
    # compiler is writing those, and a grade read off them would need two compiles to settle
    # on a new building.
    sids = sorted((ROOT / "data" / "structures").glob("*.json"))
    scenes = {p.stem: [s.stem for s in sids] for p in sorted((ROOT / "data" / "scenes").glob("*.json"))}
    pics = cp.derive(images, tsv, sources, texts, scenes, cams)
    rulings = load_rulings()

    def grade(scene, sid, existence):
        pictures = (pics.get(scene) or {}).get("by_structure", {}).get(sid, [])
        return grade_structure(sid, existence, pictures, cams.get(sid, []), rulings, scene)

    return grade, rulings


def check_rulings(rulings, structures_by_scene, sources):
    """Every ruling names a structure in its scene, a picture, and why. -> list of faults."""
    faults = []
    for key in ("pictured", "not_pictured"):
        for i, r in enumerate(rulings.get(key, [])):
            where = f"{key}[{i}]"
            sid, scene, pic = r.get("structure"), r.get("scene"), r.get("picture")
            if not (sid and scene and pic):
                faults.append(f"{where}: needs structure, scene and picture")
                continue
            if sid not in structures_by_scene.get(scene, set()):
                faults.append(f"{where}: {sid} is not a structure of the {scene} scene")
            if not str(r.get("why") or "").strip():
                faults.append(f"{where}: says nothing about why — a ruling owes its reason")
            if key == "pictured" and INVENTED_ID.match(sid):
                faults.append(f"{where}: {sid} is an invented roof; nothing pictures an invention")
    for scene, rule in (rulings.get("street_maps") or {}).items():
        if not str(rule.get("why") or "").strip():
            faults.append(f"street_maps.{scene}: says nothing about why")
        for m in rule.get("maps", []):
            if m not in sources:
                faults.append(f"street_maps.{scene}: {m} is not a source in data/sources/")
            elif sources[m].get("type") != "map":
                faults.append(f"street_maps.{scene}: {m} is a {sources[m].get('type')}, not a map")
            if m not in MAP_NAMES:
                faults.append(f"street_maps.{scene}: {m} has no name a visitor can read (MAP_NAMES)")
    return faults


def read_scenes():
    out = {}
    for d in sorted(p for p in (ROOT / "data" / "sidecars").iterdir() if p.is_dir() and re.fullmatch(r"\d{4}", p.name)):
        index = json.loads((d / "index.json").read_text(encoding="utf-8"))
        out[d.name] = {e["id"] for e in index.get("structures", [])}
    return out


def table():
    grade, rulings = grader()
    rows, counts = [], {}
    for scene, sids in read_scenes().items():
        c = Counter()
        for sid in sorted(sids):
            sc = json.loads((ROOT / "data" / "sidecars" / scene / f"{sid}.json").read_text(encoding="utf-8"))
            existence = (sc.get("documented_range") or {}).get("confidence", "reconstructed")
            g = grade(scene, sid, existence)
            c[g["value"]] += 1
            rows.append((scene, sid, existence, g))
        counts[scene] = c
    return rows, counts, rulings


def self_test():
    fails = []

    def expect(cond, what):
        if not cond:
            fails.append(what)

    front = {"id": "front", "library": True, "view": "front elevation"}
    street = {"id": "street", "library": True, "view": "street view"}
    detail = {"id": "detail", "library": True, "view": "detail"}
    plate = {"id": "plate", "library": False, "view": None}
    none = {}
    g = lambda pics, ex="inferred", cams=(), rul=none, sid="h": grade_structure(sid, ex, pics, list(cams), rul, "1904")["value"]
    expect(g([front]) == "attested", "a front elevation makes the building attested")
    expect(g([front], ex="reconstructed") == "attested", "a picture outranks a reconstructed existence")
    expect(g([street]) == "inferred", "a street view it stands in does not attest it by itself")
    expect(g([detail]) == "inferred", "a detail is not the building")
    expect(g([plate]) == "inferred", "a cited source picture needs a camera or a ruling")
    expect(g([street], cams=[{"library_image": "street"}]) == "attested", "a solved camera attests whatever the view tag")
    expect(g([plate], cams=[{"source_id": "plate"}]) == "attested", "a camera on a source picture attests it")
    expect(g([]) == "inferred", "a mapped or written-up building with no picture is inferred")
    expect(g([], ex="attested") == "inferred", "a Sanborn-attested footprint alone is inferred, not attested")
    expect(g([], ex="reconstructed") == "reconstructed", "an unpictured invention is reconstructed")
    expect(g([], ex="") == "reconstructed", "an ungraded existence is reconstructed, never promoted by omission")
    rin = {"pictured": [{"structure": "h", "scene": "1904", "picture": "street", "why": "w"}]}
    expect(g([street], rul=rin) == "attested", "a ruling brings a street view in")
    rin_other = {"pictured": [{"structure": "h", "scene": "1835", "picture": "street", "why": "w"}]}
    expect(g([street], rul=rin_other) == "inferred", "a ruling binds only its own scene")
    rout = {"not_pictured": [{"structure": "h", "scene": "1904", "picture": "front", "why": "w"}]}
    expect(g([front], rul=rout) == "inferred", "a ruling takes a mis-tagged front out")
    one = grade_structure("h", "inferred", [front], [], none, "1904")
    expect(one["pictures"] == ["front"] and "a picture" in one["why"], f"the block names its picture ({one})")
    faults = check_rulings({"pictured": [{"structure": "recon_x", "scene": "1835", "picture": "p"},
                                          {"structure": "ghost", "scene": "1904", "picture": "p", "why": "w"}],
                            "street_maps": {"1835": {"maps": ["a_book"], "why": "w"}}},
                           {"1835": {"recon_x"}, "1904": set()}, {"a_book": {"type": "book"}})
    expect(any("why" in f for f in faults), "a ruling with no reason is refused")
    expect(any("invented roof" in f for f in faults), "a ruling that pictures an invention is refused")
    expect(any("not a structure of the 1904" in f for f in faults), "a ruling on an unknown structure is refused")
    expect(any("not a map" in f for f in faults), "a street ruling citing a non-map is refused")
    rul = {"street_maps": {"1835": {"maps": ["thompson_plat_1830", "wright_1834"], "why": "w"}}}
    s = lambda **kw: grade_street(kw, "1835", rul, {})["value"]
    expect(s(sources=["wright_1834"], geometry_confidence="inferred") == "attested", "a street the survey draws is attested")
    expect(s(sources=["wright_1834"], geometry_confidence="reconstructed") == "attested",
           "a platted street is attested even where its line is derived")
    expect(s(sources=["a_book"], geometry_confidence="reconstructed") == "reconstructed", "a road no map draws keeps its line's grade")
    expect(s(sources=[], geometry_confidence="inferred") == "inferred", "an undrawn inferred line stays inferred")
    expect(s(sources=[]) == "reconstructed", "an ungraded undrawn street is reconstructed")
    why = grade_street({"sources": ["thompson_plat_1830", "wright_1834"]}, "1835", rul, {})["why"]
    expect(why == "Drawn on the 1830 town plat and 1834 survey.", f"the street's reason names its maps ({why})")
    for f in fails:
        print(f"FAIL: {f}")
    if fails:
        return 1
    print("OK: pictures, cameras, rulings, existence and the street maps each decide what they should")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    sources = {}
    for f in sorted((ROOT / "data" / "sources").glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        if isinstance(d, dict) and d.get("id"):
            sources[d["id"]] = d
    rows, counts, rulings = table()
    faults = check_rulings(rulings, read_scenes(), sources)
    for scene, c in counts.items():
        print(f"   {scene}: " + ", ".join(f"{c[l]} {l}" for l in LEVELS))
    if faults:
        for f in faults:
            print(f"FAIL: {f}")
        return 1
    if a.check:
        print("OK: every ruling names its structure, its picture and why")
        return 0
    for scene, sid, existence, g in rows:
        print(f"{scene}  {g['value']:<13} stood:{existence:<13} {sid}  {', '.join(g['pictures'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
