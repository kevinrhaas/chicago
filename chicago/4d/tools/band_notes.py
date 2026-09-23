#!/usr/bin/env python3
"""Which invented values may cite the family band, and what the rest must say instead.

ROADMAP K33, opened by K25(a). Every invented form value on every reconstructed
building carries the same closing sentence — *"Type-level choice within the D3 band in
the reconstruction specification"* — and that sentence is the entire defence for the
invention: the building is made up, but it is made up inside what the specification
allows. K25(a) measured the values the crosswalk **does** bound and found 98 outside
their band. This module is the other half, and it is worse in kind: **for 623 values
there is no band to be inside at all.** `paint` carries the sentence on 227 records and
220 of those families never mention paint; `board_gap_m` carries it on 99 against a
specification that names no board gap anywhere; and 42 `roof_pitch_deg` values cite a
band on six families whose roof line is "gable or shed" — a form with no pitch in it.

A note citing a band that does not speak to the value is not an imprecise note. It is a
provenance claim with nothing behind it, and it is the same wrong sentence on values the
specification genuinely bounds and values it has never heard of, so a reader cannot tell
the two apart. That is what this module fixes: it decides, from the committed crosswalk
and nothing else, which of the two a given (family, field) is.

## Why a shared module rather than the test living in the measuring tool

`tools/family_bands.py` exists because "the same arithmetic was in two files and only one
of them ran it" — the North parcel retyped a band into Python and shipped sixty identical
buildings. The identical trap is here: the generators author the note and
`tools/measure_band_claims.py` audits it, and if the two disagree about what "the family
authors a band for this" means, the gate is measuring a different question from the one
the data answers. So the predicate is defined once, here, and both import it.

## The three states, and why the middle one keeps its citation

- **band** — the crosswalk authors a value this project can test the invention against:
  the footprint band, the eave band, the levels string, the roof form, the rise:run
  pitch. The citation is true and stays.
- **prose** — the crosswalk speaks to the thing without bounding it: `construction` is
  "hewn or round logs with chinking", `variants` is "2/3 bays; external chimney". The
  specification really is the source of the choice even though no gate can check it, so
  the citation stays. K25(a) took this position when it separated `PROSE_FIELDS` from the
  banded ones, and K33 does not reopen it.
- **silent** — the crosswalk says nothing whatever. There is no band, no prose, nothing
  for the note to be citing. These are the 623.

The instrument for **prose** is a keyword over the family's authored geometry strings and
it is deliberately generous: a hit means the specification *mentions* the thing, not that
it bounds it. Generous in this direction is the safe direction — it keeps a citation the
project might defend and only strips the ones nothing can defend, so the count of repairs
is a floor rather than an estimate.

## What replaces the citation

Not a lower confidence grade. These values are already at the bottom tier, and the
confidence floats are hashed into `generators/mesh_inputs.py`'s staleness recipe, so
regrading them would stale 249 committed GLBs and need a Blender bake this project's
improve runner does not have. Prose is not hashed. So the repair is the sentence itself:

    The A3 family's key geometry parameters do not speak to paint or finish, so this
    value cites no specification: it is the reconstruction generator's type default;
    it is not evidence for this anonymous instance.

It says what the value is (a generator default), what it is not (a reading of the
specification), and it keeps the parcel's own closing clause. It also deliberately does
not contain the word "band", so `measure_band_claims.CITES_BAND_RE` cannot read it as a
citation and the assertion below is not fooled by its own repair.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CROSSWALK_PATH = ROOT / "data" / "reconstruction" / "1835_family_archetype_crosswalk.json"

FOOTPRINT_RE = re.compile(r"^\s*(\d+)x(\d+)\s*-\s*(\d+)x(\d+)")
RANGE_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*$")
PITCH_RE = re.compile(r"(\d+):12\s*-\s*(\d+):12")

BAND = "band"
PROSE = "prose"
SILENT = "silent"

# The fields the crosswalk authors something testable for, and the test. Each takes the
# family's `key_geometry_parameters` and answers one question: is there a band here for
# a note to be citing? `roof_type` is banded because the roof line enumerates the forms
# on offer and `measure_band_claims` checks membership in it; `roof_pitch_deg` is banded
# only where that same line carries a rise:run, which six families' do not.
BANDED_FIELDS = {
    "footprint": lambda g: bool(FOOTPRINT_RE.match(str(g.get("footprint_ft") or ""))),
    "wall_height_m": lambda g: bool(RANGE_RE.match(str(g.get("eave_ft") or ""))),
    "roof_pitch_deg": lambda g: bool(PITCH_RE.search(str(g.get("roof") or ""))),
    "roof_type": lambda g: bool(str(g.get("roof") or "").strip()),
    "stories": lambda g: bool(str(g.get("levels") or "").strip()),
    "loft": lambda g: bool(str(g.get("levels") or "").strip()),
}

# The fields no band can be authored for, looked for as a keyword anywhere in the
# family's authored geometry. Generous on purpose — see the module docstring.
PROSE_KEYWORDS = {
    "construction": ("log", "frame", "plank", "board", "brick", "clapboard", "timber"),
    "bays": ("bay",),
    "chimneys": ("chimney", "stovepipe", "flue"),
    "plan": ("plan", "hall", "pen", "room", "passage"),
    "porch": ("porch", "stoop", "gallery", "veranda"),
    "gallery": ("gallery", "porch", "veranda"),
    "gable_front": ("gable",),
    "cladding": ("clapboard", "board", "plank", "log", "batten", "shingle"),
    "shopfront": ("shop", "display", "pane", "front"),
    "goods_door": ("door",),
    "goods_door_side": ("door",),
    "door": ("door",),
    "door_side": ("door",),
    "paint": ("paint", "whitewash", "unpainted"),
    "board_gap_m": ("gap", "batten", "chink"),
}

# How each field is named in the sentence a visitor reads. A field with no entry here is
# a field nothing has classified, which `classify` reports rather than guessing at.
FIELD_LABEL = {
    "footprint": "a footprint band",
    "wall_height_m": "an eave height",
    "roof_pitch_deg": "a roof pitch",
    "roof_type": "a roof form",
    "stories": "a storey count",
    "loft": "a loft",
    "construction": "construction",
    "bays": "a bay count",
    "chimneys": "chimneys",
    "plan": "an interior plan",
    "porch": "a porch",
    "gallery": "a gallery",
    "gable_front": "gable orientation",
    "cladding": "cladding",
    "shopfront": "a shopfront",
    "goods_door": "a goods door",
    "goods_door_side": "a goods-door side",
    "door": "a door type",
    "door_side": "a door side",
    "paint": "paint or finish",
    "board_gap_m": "a board gap",
}

CLASSIFIED = frozenset(BANDED_FIELDS) | frozenset(PROSE_KEYWORDS)


def geometry() -> dict[str, dict]:
    """Per family, the `key_geometry_parameters` block exactly as the crosswalk authors it."""
    return {fam["id"]: (fam.get("key_geometry_parameters") or {})
            for fam in json.loads(CROSSWALK_PATH.read_text(encoding="utf-8"))["families"]}


def classify(geom: dict, field: str) -> str | None:
    """`band`, `prose`, `silent` — or None for a field nothing has classified.

    None is not "fine": it means a form value is being authored that neither the banded
    table nor the prose table has heard of, so no one has decided whether its note may
    cite the specification. `measure_band_claims --gate` fails on it rather than letting
    a new field arrive citing a band by default.
    """
    test = BANDED_FIELDS.get(field)
    if test is not None:
        if test(geom):
            return BAND
        # A banded field whose family authors no band still gets the prose question
        # asked of it, because "gable or shed" does speak to the roof even where it
        # carries no pitch. Only a family silent on both ends is SILENT.
        return PROSE if _prose_hit(geom, field) else SILENT
    if field in PROSE_KEYWORDS:
        return PROSE if _prose_hit(geom, field) else SILENT
    return None


def _prose_hit(geom: dict, field: str) -> bool:
    words = PROSE_KEYWORDS.get(field)
    if not words:
        return False
    blob = json.dumps(geom).lower()
    return any(w in blob for w in words)


def may_cite_band(geom: dict, field: str) -> bool:
    """The assertion, in one call: may this value's note cite the family band?"""
    return classify(geom, field) in (BAND, PROSE)


def unbounded_note(family: str, field: str, why: str) -> str:
    """The sentence that replaces the citation, keeping the parcel's own closing clause.

    `why` is the generator's band-citing note, whose tail after the first `; ` is the
    clause that says whose instance this is ("it is not evidence for this anonymous North
    Division instance"). That clause is the parcel's and is preserved verbatim; only the
    claim in front of it changes.

    It opens by negating the lede rather than merely omitting a citation. Every one of
    these notes is prefixed by a generator-level paragraph that says, in as many words,
    *"the spec is cited because the invention is bounded by it"* — which is the exact
    claim K33 found to be untrue here. Leaving that paragraph standing and quietly
    dropping the citation behind it would leave the reader with the same false
    impression, so the replacement contradicts it in the first four words.
    """
    label = FIELD_LABEL.get(field, field)
    tail = why.split("; ", 1)[1].rstrip() if "; " in why else ""
    head = (f"NOT BOUNDED BY THE SPECIFICATION, and the sentence above about the "
            f"invention being bounded does not hold for this value: the {family} "
            f"family's key geometry parameters do not speak to {label}, so there is "
            f"nothing here for a citation to point at. The value is the reconstruction "
            f"generator's type default")
    return f"{head}; {tail}" if tail else f"{head}."


def split_notes(form: dict, family: str, why: str, geom: dict | None = None) -> dict:
    """Rewrite the note on every form value whose family authors nothing to cite.

    Matched on the note's TAIL, because every generator here writes `lede + why`: a
    paragraph explaining what an invented value is, followed by the family citation.
    Only the citation is this parcel's to rewrite, and only where it points at nothing.

    Values the specification bands or speaks to are left byte-identical, so the diff is
    exactly the repair. Returns the same dict, mutated, for use inline at a call site.
    """
    if geom is None:
        geom = geometry().get(family, {})
    for field, value in form.items():
        if not isinstance(value, dict) or not isinstance(value.get("note"), str):
            continue
        note = value["note"]
        if not note.endswith(why):
            # A field whose note was authored specially — a documented override, a
            # placement reason — is not this parcel's to rewrite.
            continue
        if classify(geom, field) == SILENT:
            value["note"] = note[:-len(why)] + unbounded_note(family, field, why)
    return form
