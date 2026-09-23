#!/usr/bin/env python3
"""Keep another resident pass's findings when a mint rebuilds its own card (T-1137).

    python3 tools/resident_mint_carry.py --self-test

THE BOUNDARY IS A WRITER-OWNED MARKER, not the mint's entire derived note.  Every pass
that appends prose to ``persons[].note`` already writes a stable ``MARKER`` so its own
once-each gate can find the paragraph.  That same marker is the honest boundary for a
mint: everything from the first foreign marker onward is appended evidence, even when
the prose the mint derives before it has changed.

The old prefix test survives only as a compatibility path for an unchanged derived
note carrying an older, unmarked suffix.  If both the derived prose and an unmarked
suffix change, there is no safe boundary to infer and this module refuses to guess.
New appenders are discovered from the same source shape as ``spend_write_once.py``;
the two old-settler markers predate the ``spend_`` convention and are included by name.

The note is only one co-owned field.  Consolidation passes also add household blocks,
person evidence, citations, a ladder rule, and ``occupation.later_occupation``.  This
module carries those in the same fixed slots the four mints already use, while callers
name optional fields they themselves own so an old derivation cannot resurrect one.
"""
from __future__ import annotations

import ast
from functools import lru_cache
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"

# ``old_settlers.py`` is an evidence writer rather than a ``spend_*.py`` pass.  Its
# marker function chooses between these two literals, and its own --check holds them.
OLD_SETTLER_MARKERS = ("OLD SETTLERS, 1882", "OLD SETTLERS, 1879")
MINTS = (
    "mint_civic_residents.py",
    "mint_documented_residents.py",
    "mint_letter_list_residents.py",
    "mint_placed_residents.py",
)


def _literal(path: pathlib.Path, name: str):
    """One module-level literal assignment, without importing a writer as code."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        value = None
        targets = []
        if isinstance(node, ast.Assign):
            value, targets = node.value, node.targets
        elif isinstance(node, ast.AnnAssign):
            value, targets = node.value, [node.target]
        for target in targets:
            if isinstance(target, ast.Name) and target.id == name:
                try:
                    return ast.literal_eval(value)
                except (TypeError, ValueError):
                    return None
    return None


@lru_cache(maxsize=1)
def note_markers() -> tuple[str, ...]:
    """Every current append-only resident-note marker, discovered from its writer."""
    found = []
    for path in sorted(TOOLS.glob("spend_*.py")):
        if path.name == "spend_write_once.py":
            continue
        source = path.read_text(encoding="utf-8")
        if "MARKER not in note" not in source:
            continue
        marker = _literal(path, "MARKER")
        if isinstance(marker, str):
            found.append(marker)
    found.extend(OLD_SETTLER_MARKERS)
    # A tuple is deterministic, and dict order removes a duplicated literal without
    # making the order depend on a set's hash seed.  Boundary choice itself is by the
    # marker's position in the note, never by this inventory order.
    return tuple(dict.fromkeys(found))


def carry_note(derived: str, prior: str,
               markers: tuple[str, ...] | None = None) -> str:
    """Put a foreign suffix after freshly derived prose, using its first marker."""
    derived = derived or ""
    prior = prior or ""
    if prior.startswith(derived):
        # The byte-identical path, including the spacing an older writer chose.
        return prior
    boundaries = [prior.index(marker) for marker in (markers or note_markers())
                  if marker in prior and marker not in derived]
    if not boundaries:
        return derived
    tail = prior[min(boundaries):].strip()
    return " ".join(part for part in (derived.strip(), tail) if part)


def _insert_after(row: dict, key: str, value, after: str) -> None:
    """Insert one carried field in the residents layer's stable conventional slot."""
    rebuilt = {}
    for old_key, old_value in row.items():
        rebuilt[old_key] = old_value
        if old_key == after:
            rebuilt[key] = value
    if key not in rebuilt:
        rebuilt[key] = value
    row.clear()
    row.update(rebuilt)


def carry_resident_mint(doc: dict, prior: dict | None, *,
                        owned_person_keys: tuple[str, ...] = (),
                        retracted_sources: set | None = None) -> dict:
    """Carry foreign findings from ``prior`` onto one freshly minted household.

    A caller's ordinary keys win because they are its new derivation.  Missing keys are
    foreign unless the caller names them in ``owned_person_keys``; those named absences
    are answers and are never resurrected.  Sources remain additive, except for a source
    the caller explicitly retracted from its own evidence.
    """
    if not prior:
        return doc
    owned = set(owned_person_keys)
    retracted = set(retracted_sources or ())

    for key, value in prior.items():
        if key not in doc:
            doc[key] = value

    # Kinship has one conventional household slot: immediately before persons.
    if "kin" in doc:
        kin = doc.pop("kin")
        _insert_after(doc, "kin", kin, "present_on_scene_date")

    by_id = {person.get("id"): person for person in prior.get("persons") or []}
    for person in doc.get("persons") or []:
        old = by_id.get(person.get("id")) or {}

        # A rung belongs beside the grade it explains, rather than at the arbitrary end
        # of whichever mint happened to rebuild this person.
        rung = old.get("ladder_rule")
        if rung is not None and "ladder_rule" not in person \
                and "ladder_rule" not in owned:
            _insert_after(person, "ladder_rule", rung, "grade")

        for key, value in old.items():
            if key == "ladder_rule":
                continue
            if key not in person and key not in owned:
                person[key] = value

        # A later trade is another pass's pointer inside an object the mints own.
        pointer = (old.get("occupation") or {}).get("later_occupation")
        if pointer is not None and isinstance(person.get("occupation"), dict):
            _insert_after(person["occupation"], "later_occupation", pointer, "confidence")

        # T-1229: AND THE 1835 FIELD IS NOW A VIEW OF `roles[]`, DERIVED AFTER THE MINT.
        # `roles` itself is an ordinary foreign person key and the loop above already
        # carries it; these three live INSIDE `occupation`, which the mints rebuild whole,
        # so they are lost the same way `later_occupation` was before T-1137. They are
        # appended in the order tools/derive_resident_roles.py writes them, which is what
        # keeps a mint's --check a byte comparison rather than a semantic one.
        derived = old.get("occupation") or {}
        if isinstance(person.get("occupation"), dict):
            for key in ("withdrawn_from_scene_date", "derived_from",
                        "roles_at_scene_date"):
                if key in derived and key not in person["occupation"] \
                        and key not in owned:
                    person["occupation"][key] = derived[key]

        derived_sources = set(person.get("sources") or [])
        prior_sources = set(old.get("sources") or [])
        person["sources"] = sorted(
            derived_sources | (prior_sources - (retracted - derived_sources)))
        person["note"] = carry_note(person.get("note") or "", old.get("note") or "")
    return doc


def self_test() -> int:
    failures = []

    def want(label, condition):
        if not condition:
            failures.append(label)

    markers = note_markers()
    want("all six spend writers and both old-settler boundaries are discovered",
         len(markers) >= 8 and set(OLD_SETTLER_MARKERS) <= set(markers))

    marker = "A FOREIGN WRITER'S MARKER."
    old_derived = "This mint derived one sentence."
    foreign = marker + " Another pass's finding survives."
    changed = "This mint derived a changed sentence."
    want("a derived-prose change keeps the marker-bounded foreign suffix",
         carry_note(changed, old_derived + " " + foreign, (marker,))
         == changed + " " + foreign)
    want("an unchanged derivation stays byte-identical",
         carry_note(old_derived, old_derived + "  " + foreign, (marker,))
         == old_derived + "  " + foreign)
    want("an unmarked suffix is not guessed after the derivation changes",
         carry_note(changed, old_derived + " an unmarked suffix", (marker,)) == changed)

    fresh = {
        "id": "hh_x", "present_on_scene_date": {},
        "persons": [{
            "id": "p_x", "grade": "attested",
            "occupation": {"value": "none_recorded", "confidence": "reconstructed"},
            "sources": ["source_this_mint_derives"], "note": changed,
        }],
    }
    prior = {
        "id": "hh_x", "present_on_scene_date": {},
        "kin": [{"person": "p_x", "relation": "head"}],
        "persons": [{
            "id": "p_x", "grade": "attested", "ladder_rule": "G1b",
            "occupation": {
                "value": "none_recorded", "confidence": "reconstructed",
                "later_occupation": {"value": "clerk", "describes_date": 1839},
                "withdrawn_from_scene_date": {"value": "grocer", "verdict": "pre_scene"},
                "derived_from": "roles", "roles_at_scene_date": [],
            },
            "roles": [{"role": None, "as_printed": "clerk", "from": "1839"}],
            "sources": ["source_this_mint_derives", "source_another_pass_added"],
            "note": old_derived + " " + OLD_SETTLER_MARKERS[0] + " — finding",
            "resident_research": {"ticket": "T-0509"},
            "press_evidence": [{"record_id": "old-derived-row"}],
        }],
        "directories": {"people": [{"person_id": "p_x"}]},
    }
    kept = carry_resident_mint(fresh, prior, owned_person_keys=("press_evidence",))
    person = kept["persons"][0]
    want("a foreign household block survives", kept.get("directories") == prior["directories"])
    want("kinship returns immediately before persons",
         list(kept).index("kin") == list(kept).index("persons") - 1)
    want("a foreign person block survives",
         person.get("resident_research") == {"ticket": "T-0509"})
    want("a missing field this mint owns is not resurrected", "press_evidence" not in person)
    want("the rung returns immediately after grade",
         list(person).index("ladder_rule") == list(person).index("grade") + 1)
    want("a later occupation survives inside the newly derived occupation",
         person["occupation"].get("later_occupation", {}).get("describes_date") == 1839)
    # T-1229. `roles[]` is an ordinary foreign person key; the three view keys live
    # inside `occupation`, which a mint rebuilds whole, so they need naming.
    want("the dated roles survive", person.get("roles") == prior["persons"][0]["roles"])
    want("the scene-date view survives inside the newly derived occupation",
         person["occupation"].get("derived_from") == "roles"
         and person["occupation"].get("roles_at_scene_date") == [])
    want("a withdrawn trade is not resurrected as a live one",
         person["occupation"]["value"] == "none_recorded"
         and person["occupation"]["withdrawn_from_scene_date"]["value"] == "grocer")
    want("the view keys keep the order the generator writes them in",
         [k for k in person["occupation"]
          if k in ("withdrawn_from_scene_date", "derived_from", "roles_at_scene_date")]
         == ["withdrawn_from_scene_date", "derived_from", "roles_at_scene_date"])
    want("another pass's citation survives",
         "source_another_pass_added" in person["sources"])
    want("the marker-bounded finding survives the changed note",
         OLD_SETTLER_MARKERS[0] in person["note"])

    # A shared helper no generator calls is the same defect with a function beside it.
    for name in MINTS:
        source = (TOOLS / name).read_text(encoding="utf-8")
        want(f"{name} uses the shared preservation contract",
             "carry_resident_mint(" in source)

    for failure in failures:
        print(f"   FAIL: {failure}")
    if failures:
        print(f"   {len(failures)} assertion(s) failed")
        return 1
    print(f"   OK: changed prose preserves foreign findings at {len(markers)} writer "
          "boundaries, and all four resident mints use the contract")
    return 0


def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()
    print(__doc__.strip().splitlines()[0])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
