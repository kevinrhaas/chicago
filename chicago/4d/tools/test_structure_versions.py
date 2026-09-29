#!/usr/bin/env python3
"""The structure-version gates fire (T-1727).

    python3 tools/test_structure_versions.py [--self-test]   (the flag is accepted; every run is one)
    python3 tools/test_structure_versions.py --liberties-only (no meshes required)
    python3 tools/test_structure_versions.py --isolated-only (coverage and hash fixtures)

`tools/validate.py` holds every structure VERSION (data/structures/versions/<id>/<label>.json)
to the structure rules, and `--stale` holds its mesh. The ticket's acceptance names the reds
it must produce — a version with no mesh, a version with a stale mesh — and the label rule
must refuse a model identifier. A gate nobody has seen fire is a gate nobody has, so each
refusal is provoked here on a sandbox copy of the committed fixture, and the committed tree
is checked clean first so a red below is the mutation's and not the tree's.

Every line of this transcript is tagged `self-test |`, like the other self-tests in check.sh:
the FAILs it provokes on purpose are the point, and only the verdict line counts.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "generators"))
import validate  # noqa: E402
from common import versions as V  # noqa: E402

REAL = validate.ROOT
FAILURES: list[str] = []


def say(line: str) -> None:
    print(f"   self-test | {line}")


def check(name: str, cond: bool, detail: str = "") -> None:
    say(f"{'ok  ' if cond else 'FAIL'} {name}" + ("" if cond or not detail else f" — {detail}"))
    if not cond:
        FAILURES.append(name)


# ---- the label rule ------------------------------------------------------------------
for good in ("v1", "v2", "b", "hall-plan", "fixture", "pre-v2", "a1-b2"):
    check(f"label '{good}' is accepted", V.label_problem(good) is None, str(V.label_problem(good)))
for bad, why in (("", "empty"), ("V1", "upper case"), ("hall_plan", "underscore"),
                 ("-v1", "leading hyphen"), ("v1-", "trailing hyphen"), ("a" * 25, "too long"),
                 ("default", "reserved")):
    check(f"label {bad!r} is refused ({why})", V.label_problem(bad) is not None)
# The refused names are held as digests (generators/common/versions.py), so the test builds
# a label containing one from the digest set rather than writing the name down.
check("the vendor/model-name refusal is armed (18 digests)", len(V._REFUSED_DIGESTS) == 18)


def _three_letter_refused() -> str | None:
    import hashlib  # noqa: PLC0415
    import itertools  # noqa: PLC0415
    for t in itertools.product("abcdefghijklmnopqrstuvwxyz", repeat=3):
        s = "".join(t)
        if hashlib.sha256(s.encode()).hexdigest()[:16] in V._REFUSED_DIGESTS:
            return s
    return None


_name = _three_letter_refused()
check("a label with a refused name inside it is refused, wherever the name sits",
      _name is not None and all(V.label_problem(lab) for lab in
                                (_name, f"{_name}4", f"v2-{_name}", f"my{_name}plan")),
      "no three-letter digest found" if _name is None else "")


# ---- truthful admissions can belong only to a version (T-1730) ------------------------
# These cases use independent records, not the committed meshes: they exercise the
# whole-town forward AND reverse pass that used to reject v4-only form attributes.
def liberties_case(*, phase="existing", confidence="reconstructed", claim=True,
                   claimed_phase=None, claimed_aspect="form.detail_profile",
                   omitted=False, ground_gap=False) -> list[str]:
    canonical = {"house.json": {"id": "house", "archetype": "test",
                               "phases": [{"id": "existing", "form": {}}]}}
    attribute = {"value": "detailed", "confidence": confidence}
    if omitted:
        attribute["geometry"] = "simplified"
    alternate = {"house/v4.json": {"id": "house", "archetype": "test",
                                  "version": {"label": "v4"},
                                  "phases": [{"id": phase,
                                              "form": {"detail_profile": attribute}}]}}
    covers = [{"structure": "house", "phase": claimed_phase or phase,
               "aspect": claimed_aspect}] if claim else []
    # An entry with no covers keeps the register nonempty while testing an
    # unclaimed actual value, rather than the separate empty-register refusal.
    register = {"liberties": [{"id": "L-test", "subjects": ["house"],
                                "section": "active", "covers": covers}]}
    consumed = {"test": frozenset() if omitted else frozenset({"detail_profile"})}
    unlanded = [("house", phase, "ground_contact", f"version house/v4/{phase}", 0.5)] \
        if ground_gap else []
    rep = validate.Report()
    validate.check_liberties_coverage(canonical, register, rep, consumed, unlanded,
                                     versions=alternate)
    return rep.errors


errs = liberties_case()
check("a claimed version-only form attribute is admitted without changing the default",
      not errs, "; ".join(errs))
errs = liberties_case(phase="alternate_phase")
check("reverse coverage finds a phase belonging only to the version, not the first default",
      not errs, "; ".join(errs))
errs = liberties_case(phase="alternate_phase", claimed_phase="missing_phase")
check("a phase absent from both default and version is still refused",
      any("has no phase 'missing_phase'" in e for e in errs), str(errs))
errs = liberties_case(claimed_aspect="form.nonexistent")
check("an invented admission with no value in any record is still refused",
      any("form.nonexistent" in e and "neither inferred" in e for e in errs), str(errs))
errs = liberties_case(claim=False)
check("a version-only invention without an admission is still refused",
      any("form.detail_profile is inferred but no liberty" in e for e in errs), str(errs))
errs = liberties_case(confidence="attested")
check("a version-only attested built value does not excuse an invented-value over-claim",
      any("neither inferred" in e for e in errs), str(errs))
errs = liberties_case(phase="alternate_phase", confidence="attested", omitted=True)
check("a declared omission belonging only to a version honours its admission",
      not errs, "; ".join(errs))
errs = liberties_case(phase="alternate_phase", confidence="attested", ground_gap=True,
                      claimed_aspect="ground_contact")
check("a measured ground-contact gap belonging only to a version honours its admission",
      not errs, "; ".join(errs))

if "--liberties-only" in sys.argv:
    say(f"{len(FAILURES)} failure(s)")
    sys.exit(1 if FAILURES else 0)


# ---- a version's exclusive dependencies cannot stale the default (T-1730) -------------
def test_detail_dependency_isolation() -> None:
    from dataclasses import dataclass  # noqa: PLC0415
    from unittest.mock import patch  # noqa: PLC0415
    import mesh_inputs  # noqa: PLC0415

    @dataclass
    class Params:
        detail_profile: str = ""

    with tempfile.TemporaryDirectory(prefix="version-inputs-") as tmp:
        root = Path(tmp)
        files = {
            "generators/blender.pin": "4.3.2",
            "generators/emit.py": "# shared export\n",
            "generators/archetypes/masonry_house.py": "# shared builder\n",
            "generators/common/mesh.py": "# shared geometry\n",
            "generators/archetypes/masonry_house_v4.py": "# v4 detail\n",
            "generators/archetypes/masonry_house_v4_materials.py": "# v4 materials\n",
            "assets/textures/glessner-v4/stone.png": "png fixture",
            "assets/textures/glessner-v4/stone_normal.jpg": "jpeg fixture",
            "assets/textures/glessner-v4/generate.py": "# texture recipe\n",
        }
        for rel, content in files.items():
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content)

        structure = {"id": "glessner_house", "archetype": "masonry_house"}
        default_phase = {"id": "built", "profile": ""}
        detail_phase = {"id": "built", "profile": "glessner_v4"}
        with patch.object(mesh_inputs, "ROOT", root), \
                patch.object(mesh_inputs.code_inputs, "geometry_modules", return_value=[
                    root / "generators/common/mesh.py"]), \
                patch.object(mesh_inputs, "resolve_params", side_effect=
                             lambda arch, phase, record: Params(phase["profile"])):
            baseline = mesh_inputs.structure_inputs_sha(structure, default_phase)
            detailed = mesh_inputs.structure_inputs_sha(structure, detail_phase)
            default_doc = mesh_inputs.structure_inputs_doc(structure, default_phase)
            check("the default has no v4 detail or texture dependency",
                  "textures" not in default_doc and not any(
                      "masonry_house_v4" in name for name in default_doc["code"]))

            # Change one input at a time and restore it, so each refusal is
            # independently caused by the named dependency. No real map is touched.
            for rel, label in (
                ("generators/archetypes/masonry_house_v4.py", "v4 detail module"),
                ("generators/archetypes/masonry_house_v4_materials.py", "v4 material module"),
                ("assets/textures/glessner-v4/stone.png", "v4 PNG map"),
                ("assets/textures/glessner-v4/stone_normal.jpg", "v4 JPEG map"),
                ("assets/textures/glessner-v4/generate.py", "v4 texture recipe"),
            ):
                p = root / rel
                p.write_text(files[rel] + " changed")
                check(f"changing the {label} stales v4",
                      mesh_inputs.structure_inputs_sha(structure, detail_phase) != detailed)
                check(f"changing the {label} leaves the default fresh",
                      mesh_inputs.structure_inputs_sha(structure, default_phase) == baseline)
                p.write_text(files[rel])


test_detail_dependency_isolation()

if "--isolated-only" in sys.argv:
    say(f"{len(FAILURES)} failure(s)")
    sys.exit(1 if FAILURES else 0)


# ---- the validator, on a sandbox ------------------------------------------------------
def load_world():
    rep = validate.Report()
    structures = validate.load_dir(REAL / "data" / "structures", rep)
    scenes = validate.load_dir(REAL / "data" / "scenes", rep)
    sources = validate.load_dir(REAL / "data" / "sources", rep)
    liberties = validate.load_json(REAL / "data" / "liberties.json", rep) or {}
    consumed = validate.archetype_consumed(rep)
    return structures, scenes, sources, liberties, consumed


STRUCTURES, SCENES, SOURCES, LIBERTIES, CONSUMED = load_world()
SOURCE_IDS = {s.get("id") for s in SOURCES.values() if isinstance(s, dict)}


def sandbox() -> Path:
    root = Path(tempfile.mkdtemp(prefix="versions-"))
    for rel in ("data/structures/versions", "assets/gltf/versions", "assets/web/versions"):
        src = REAL / rel
        if src.exists():
            shutil.copytree(src, root / rel)
    shutil.copyfile(REAL / "assets" / "manifest.versions.json",
                    root / "assets" / "manifest.versions.json")
    return root


def run(root: Path) -> list[str]:
    validate.ROOT = root
    rep = validate.Report()
    try:
        versions = validate.check_versions(STRUCTURES, SCENES, SOURCES, SOURCE_IDS, LIBERTIES,
                                           CONSUMED, rep)
        validate.run_version_stale_check(versions, SCENES, rep)
    finally:
        validate.ROOT = REAL
    return rep.errors


FIX = "data/structures/versions/bates_auction_room/fixture.json"
KEY = "versions/bates_auction_room/fixture/bates_auction_room__frame_1834.glb"


def mutate(name: str, edit, expect: str) -> None:
    root = sandbox()
    try:
        edit(root)
        errs = run(root)
        hit = [e for e in errs if expect in e]
        check(name, bool(hit), f"expected an error containing {expect!r}; got {errs[:3]}")
    finally:
        shutil.rmtree(root, ignore_errors=True)


root = sandbox()
clean = run(root)
shutil.rmtree(root, ignore_errors=True)
check("the committed versions validate clean (so every red below is its mutation's)",
      not clean, "; ".join(clean[:3]))


def edit_json(rel, fn):
    def go(root: Path):
        p = root / rel
        doc = json.loads(p.read_text())
        fn(doc)
        p.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    return go


def no_mesh(root: Path):
    (root / "assets" / "gltf" / KEY).unlink()
    (root / "assets" / "web" / KEY).unlink()
    doc = json.loads((root / "assets" / "manifest.versions.json").read_text())
    del doc["assets"][KEY]
    (root / "assets" / "manifest.versions.json").write_text(json.dumps(doc))


def taller(doc):
    doc["phases"][0]["form"]["wall_height_m"]["value"] = 4.2


def stray(root: Path):
    (root / "data" / "structures" / "versions" / "loose.json").write_text("{}")


def bad_label(root: Path):
    d = root / "data" / "structures" / "versions" / "bates_auction_room"
    doc = json.loads((d / "fixture.json").read_text())
    doc["version"]["label"] = "Hall_Plan"
    (d / "Hall_Plan.json").write_text(json.dumps(doc))


def orphan_version(root: Path):
    d = root / "data" / "structures" / "versions"
    shutil.copytree(d / "bates_auction_room", d / "no_such_structure")


def derivative_drift(root: Path):
    (root / "assets" / "web" / KEY).write_bytes(b"not the derivative of that master")
    doc = json.loads((root / "assets" / "manifest.versions.json").read_text())
    doc["assets"][KEY]["web_master_sha256"] = "0" * 64
    (root / "assets" / "manifest.versions.json").write_text(json.dumps(doc))


def stray_mesh(root: Path):
    p = root / "assets" / "gltf" / "versions" / "bates_auction_room" / "ghost" / "x.glb"
    p.parent.mkdir(parents=True)
    p.write_bytes(b"glTF")


mutate("a version with NO MESH is red", no_mesh, "has NO MESH")
mutate("a version whose record changed under its mesh is STALE and red",
       edit_json(FIX, taller), "is STALE")
mutate("a version whose derivative is not of its master is red", derivative_drift,
       "not recorded as made from the committed master")
mutate("a mesh with no version record behind it is red", stray_mesh, "no manifest entry")
mutate("a file that is not versions/<id>/<label>.json is red", stray, "is not a structure version")
mutate("a label outside the rule is red", bad_label, "label refused")
mutate("a version of a structure that does not exist is red", orphan_version,
       "no canonical record")
mutate("a version carrying another structure's id is red",
       edit_json(FIX, lambda d: d.__setitem__("id", "sauganash_hotel")), "carries its structure's id")
mutate("a version block naming another label is red",
       edit_json(FIX, lambda d: d["version"].__setitem__("label", "v9")), "version.label")
mutate("a version with an empty summary is red",
       edit_json(FIX, lambda d: d["version"].__setitem__("summary", " ")), "summary")
mutate("a version citing a source that does not exist is red (the provenance pass reaches it)",
       edit_json(FIX, lambda d: d["phases"][0]["documented_range"]["sources"].append(
           "no_such_source_t1727")), "no_such_source_t1727")
mutate("a version no scene resolves is red",
       edit_json(FIX, lambda d: d["phases"][0]["documented_range"].update(
           {"from": "1900-01-01", "to": "1901-01-01"})), "no scene resolves")

say(f"{len(FAILURES)} failure(s)")
sys.exit(1 if FAILURES else 0)
