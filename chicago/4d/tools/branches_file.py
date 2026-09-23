#!/usr/bin/env python3
"""`data/terrain/epochs/e1834_harbor_cut/branches.geojson` — the one file that
more than one trace writes, and the rules that keep it deterministic.

`tools/trace_river.py` owns the forks window and writes `river.geojson` alone.
Every reach OUTSIDE that window is a separate window with its own declared
splice row, its own hue argument and its own tool, and they all land here:

    tools/trace_north_branch.py   north_branch_*   splices at BPL master row 1252
    tools/trace_south_branch.py   south_branch_*   splices at BPL master row 2372

Two tools, one file, and that needs three things said out loud or the second
tool silently deletes the first one's work:

* **Each tool owns its feature ids and nothing else.** Writing is a merge: the
  committed features whose ids the writer does not own are carried through
  untouched, byte for byte, and only the writer's own are replaced.
* **The order is declared here, not by who ran last.** `ORDER` fixes it, so the
  file's bytes do not depend on which trace was re-run — which is what lets each
  tool keep an exact `--check` against a re-trace of the scan.
* **The collection's own fields — `name`, `crs`, `_doc` — live here**, because
  they describe all the reaches and no single tool can state them correctly.

An id this module has never heard of is refused rather than appended: a new
reach declares itself in `ORDER` in the same commit as its tool, and until it
does, nothing can write the file.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PATH = ROOT / "data" / "terrain" / "epochs" / "e1834_harbor_cut" / "branches.geojson"

NAME = "e1834_harbor_cut branches"
CRS = {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::26916"}}
DOC = ("Water polygons and bank lines for the Chicago River's branches OUTSIDE the forks "
       "window traced by tools/trace_river.py: the North Branch from that window's north "
       "edge to the north line of Wright's survey (tools/trace_north_branch.py) and the "
       "South Branch from its south edge to the School Section's south line "
       "(tools/trace_south_branch.py). Coordinates are EPSG:26916 metres (UTM 16N, NAD83); "
       "local ENU metres used by the scene are these minus data/datum.json origin_utm_e / "
       "origin_utm_n. Written by those tools through tools/branches_file.py — do not "
       "hand-edit.")

# Downstream to upstream on each side of the forks, which is also north to south
# on the sheet. Adding a reach means adding its ids here.
ORDER = (
    "north_branch_wabansia",
    "north_branch_west_bank",
    "north_branch_east_bank",
    "south_branch_school_section",
    "south_branch_west_bank",
    "south_branch_east_bank",
)


def committed() -> dict:
    """The file as committed, or an empty collection if it is not there yet."""
    if not PATH.exists():
        return {"type": "FeatureCollection", "features": []}
    return json.loads(PATH.read_text())


def render(own_ids, own_features) -> str:
    """The full file text this writer would commit: its own features, plus every
    committed feature it does not own, in `ORDER`."""
    own_ids = tuple(own_ids)
    carried = [f for f in committed().get("features", []) if f.get("id") not in own_ids]
    feats = carried + list(own_features)
    unknown = sorted({f.get("id") for f in feats} - set(ORDER))
    if unknown:
        raise SystemExit(f"branches.geojson: feature id(s) {unknown} are not declared in "
                         "tools/branches_file.py ORDER — declare the reach before writing it")
    feats.sort(key=lambda f: ORDER.index(f["id"]))
    fc = {"type": "FeatureCollection", "name": NAME, "crs": CRS, "_doc": DOC,
          "features": feats}
    return json.dumps(fc, indent=1) + "\n"


def check_collection(doc: dict, own_ids, eq, bad: list) -> None:
    """Hold the collection's shared fields and its feature order to this module.

    `eq(label, got, want)` is the caller's own comparator, so a failure is
    reported in the voice of whichever `--check-properties` ran.
    """
    eq("name", doc.get("name"), NAME)
    eq("_doc", doc.get("_doc"), DOC)
    eq("crs", doc.get("crs"), CRS)
    ids = [f.get("id") for f in doc.get("features", [])]
    missing = [i for i in own_ids if i not in ids]
    if missing:
        bad.append(f"feature ids: {missing} are not in the committed collection")
    unknown = [i for i in ids if i not in ORDER]
    if unknown:
        bad.append(f"feature ids: {unknown} are not declared in tools/branches_file.py ORDER")
    ranked = [ORDER.index(i) for i in ids if i in ORDER]
    if ranked != sorted(ranked):
        bad.append(f"feature order {ids} is not the ORDER declared in tools/branches_file.py")
