#!/usr/bin/env python3
"""Re-fetch the modern street control from OpenStreetMap and compare it to what is committed.

`data/sources/osm_streets_2026.json` promises that *node ids are recorded per
control point so every coordinate is re-fetchable*. A promise about re-fetching
that nothing ever re-fetches is a sentence, not a property of the dataset, and it
had already failed twice: two of the four control points in
`data/traces/street_control.json` were read off OpenStreetMap in August 2026 for
placements and their node ids were never written down, so the coordinate five
buildings stand on could not be re-derived from the source it names.

This tool is the other half of that promise. It is deliberately **not** part of
`tools/check.sh`: it needs the network, and a commit gate that needs the network
is a gate that fails on aeroplanes and in offline sandboxes for reasons that have
nothing to do with the commit. Run it when the control changes, when a placement
is added, or when you want to know whether the modern city moved under the
dataset.

## The two modes, and why both exist

**Verify** (the default) answers *is the committed coordinate still the mean of
its recorded nodes?* It fetches each control point's `osm_node_ids` by id — no
name matching, no bounding box, no heuristics — averages them in EPSG:26916 and
reports the drift. This is the mode that keeps the promise: it is reproducible
years from now by anyone with the file, and it catches the two ways a control
point silently rots. A node can be *moved* by a mapper, which shifts the control
under placements that were computed from it; and a node can be *deleted* in a
retagging, which means the coordinate can no longer be re-derived at all. Both
are findings to record, not failures to paper over — the tool reports each node's
OSM version and edit timestamp so the answer to "when did this change?" is in the
output rather than in a follow-up investigation.

**Discover** answers the prior question — *which nodes are this junction?* — and
exists because that is the step whose absence created the gap. It reads the
control point's `osm_ways` (the modern street names the junction is made of),
fetches a small map extract around the committed coordinate, and reports every
node the named ways share. That set, averaged, is the control point, and the rule
is the georeference's own: `data/traces/gcp/hathaway_1834_gcps.json` records
"multi-node crossings averaged", because a modern junction of two dual
carriageways is several nodes and its centre is their mean.

Only surface roadways count. Chicago hands this tool the case that makes the rule
necessary: Market Street's modern successor is Wacker Drive, which at Lake Street
is three separate streets stacked on each other — North Upper Wacker Drive at the
surface, North Lower Wacker Drive beneath it, and a service drive beneath that.
They are separate ways with separate names, and only the surface one is the 1830
plat's street. Bikeways and footways are excluded for a subtler reason: they are
mapped as their own paths a few metres off the roadway centreline, so a junction
"centre" that averages them in is pulled off centre by however many of them a
modern reconstruction happens to have drawn.

**Refusals are entries too.** A junction the rule has been asked for and cannot make is
recorded in `refused_control` in the same file, with the `osm_ways` and the search centre
the reading used, so `--discover` re-runs it and the refusal stays checkable rather than
becoming an absence somebody re-investigates. Those entries carry no coordinate, and the
run reports the mean against nothing rather than against a number nobody committed.

**And --discover now refuses a set it recognises.** Two named surface roadways share nodes
without crossing wherever one changes name into the other at a bend, which is what Wacker
Drive does at Lake Street; the shared set then looks exactly like a junction and is the
NEIGHBOURING one. Whenever the discovered set is identical to a control point already in
the file under another name, the run says so and exits 1. See `node_rule`.

## What it cannot tell you

That the control is *right*. It compares the dataset to OpenStreetMap, which is a
2026 street map, and every coordinate derived from it still carries the
georeference's ±20 m onto the 1834 sheets. What it can tell you is whether the
number in the file is the number the named source gives today, which is a smaller
claim and was previously not checkable at all.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTROL = ROOT / "data" / "traces" / "street_control.json"
API = "https://api.openstreetmap.org/api/0.6"
UA = "chicago-4d control re-fetch (kevinrhaas/custom)"

# Surface roadways only. `construction` and `proposed` are excluded because a way
# that is not a street yet is not the street the plat laid out; `cycleway`,
# `footway` and `path` because they are mapped beside the roadway rather than on
# it. See the module docstring.
ROAD_HIGHWAYS = {
    "motorway", "trunk", "primary", "secondary", "tertiary",
    "unclassified", "residential", "living_street",
    "motorway_link", "trunk_link", "primary_link", "secondary_link", "tertiary_link",
}


class Offline(RuntimeError):
    """The OSM API could not be reached, which is not a dataset finding."""


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        if e.code in (404, 410):
            return b""
        raise Offline(f"{url} -> HTTP {e.code}") from e
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise Offline(f"{url} -> {e}") from e


def _to_utm():
    try:
        from pyproj import Transformer  # noqa: PLC0415
    except ImportError as e:  # pragma: no cover - environment, not logic
        raise SystemExit("pyproj is required: pip install pyproj") from e
    t = Transformer.from_crs("EPSG:4326", "EPSG:26916", always_xy=True)
    return lambda lat, lon: t.transform(lon, lat)


def _to_wgs():
    from pyproj import Transformer  # noqa: PLC0415
    t = Transformer.from_crs("EPSG:26916", "EPSG:4326", always_xy=True)
    return lambda e, n: tuple(reversed(t.transform(e, n)))


def fetch_nodes(ids: list[int]) -> dict[int, dict]:
    """Every node by id, in one call. Missing ids come back missing, on purpose."""
    if not ids:
        return {}
    raw = _get(f"{API}/nodes.json?nodes=" + ",".join(str(i) for i in ids))
    if not raw:
        # The API refuses the whole batch if any single id is gone, so fall back
        # to one call each: the interesting output is *which* node vanished.
        out = {}
        for i in ids:
            r = _get(f"{API}/node/{i}.json")
            if r:
                out[i] = json.loads(r)["elements"][0]
        return out
    return {el["id"]: el for el in json.loads(raw)["elements"]}


def verify(doc: dict, tol: float) -> int:
    to_utm = _to_utm()
    control = doc.get("control") or {}
    bad = 0
    for cid, c in sorted(control.items()):
        ids = c.get("osm_node_ids") or []
        if not ids:
            print(f"{cid:16} SKIP — no node ids recorded"
                  f"{' (gap declared)' if (c.get('gap') or '').strip() else ''}")
            continue
        els = fetch_nodes([int(i) for i in ids])
        missing = [i for i in ids if int(i) not in els]
        if missing:
            print(f"{cid:16} FAIL — node(s) {missing} no longer exist in OpenStreetMap; "
                  f"this control point can no longer be re-derived from its stated source")
            bad = 1
            continue
        pts = [to_utm(els[int(i)]["lat"], els[int(i)]["lon"]) for i in ids]
        me = sum(p[0] for p in pts) / len(pts)
        mn = sum(p[1] for p in pts) / len(pts)
        ce, cn = c.get("utm_e"), c.get("utm_n")
        drift = math.hypot(me - ce, mn - cn)
        ok = drift <= tol
        bad = bad or (0 if ok else 1)
        print(f"{cid:16} {'ok  ' if ok else 'DRIFT'} {len(ids)} node(s), mean E {me:.2f} "
              f"N {mn:.2f}, committed E {ce:.2f} N {cn:.2f}, drift {drift:.2f} m "
              f"(tolerance {tol:.2f})")
        for i in ids:
            el = els[int(i)]
            e, n = to_utm(el["lat"], el["lon"])
            print(f"    {i:>12}  v{el['version']}  {el['timestamp']}  E {e:.2f} N {n:.2f}")
    return bad


def discover(doc: dict, cid: str, radius_m: float) -> int:
    control = (doc.get("control") or {}).get(cid)
    refused = control is None
    if refused:
        control = (doc.get("refused_control") or {}).get(cid)
    if not control:
        print(f"no control point '{cid}' in {CONTROL.relative_to(ROOT)}")
        return 1
    names = control.get("osm_ways") or []
    if len(names) != 2:
        print(f"control '{cid}' does not record exactly two `osm_ways` names, so the junction "
              f"cannot be re-derived; add them (the modern street names) first")
        return 1
    to_utm, to_wgs = _to_utm(), _to_wgs()
    lat, lon = control.get("lat"), control.get("lon")
    if lat is None or lon is None:
        lat, lon = control.get("search_lat"), control.get("search_lon")
    if lat is None or lon is None:
        lat, lon = to_wgs(control["utm_e"], control["utm_n"])
    radius_m = control.get("search_radius_m", radius_m) if refused else radius_m
    d = radius_m / 111_320.0
    raw = _get(f"{API}/map?bbox={lon - d / math.cos(math.radians(lat))},{lat - d},"
               f"{lon + d / math.cos(math.radians(lat))},{lat + d}")
    if not raw:
        print("the map extract came back empty")
        return 1

    import xml.etree.ElementTree as ET  # noqa: PLC0415
    root = ET.fromstring(raw)
    nodes = {n.get("id"): (float(n.get("lat")), float(n.get("lon"))) for n in root.findall("node")}
    sets: dict[str, set] = {n: set() for n in names}
    for w in root.findall("way"):
        tags = {t.get("k"): t.get("v") for t in w.findall("tag")}
        if tags.get("highway") not in ROAD_HIGHWAYS:
            continue
        if tags.get("name") in sets:
            sets[tags["name"]].update(nd.get("ref") for nd in w.findall("nd"))
    shared = sorted(set.intersection(*sets.values()), key=int)
    print(f"{cid}: {names[0]} x {names[1]} -> {len(shared)} shared node(s)")
    if not shared:
        print("    none — the names may not match OpenStreetMap's, or the junction is beyond "
              "the search radius")
        return 1
    pts = []
    for nid in shared:
        lat_, lon_ = nodes[nid]
        e, n = to_utm(lat_, lon_)
        pts.append((e, n))
        print(f"    {nid:>12}  {lat_:.7f} {lon_:.7f}  E {e:.2f} N {n:.2f}")
    me = sum(p[0] for p in pts) / len(pts)
    mn = sum(p[1] for p in pts) / len(pts)
    spread = max(math.hypot(a[0] - b[0], a[1] - b[1]) for a in pts for b in pts) if pts else 0.0
    ce, cn = control.get("utm_e"), control.get("utm_n")
    if ce is None or cn is None:
        print(f"    mean E {me:.2f} N {mn:.2f}  (spread {spread:.2f} m)  "
              f"nothing committed to compare it to")
    else:
        print(f"    mean E {me:.2f} N {mn:.2f}  (spread {spread:.2f} m)  "
              f"committed E {ce:.2f} N {cn:.2f}  drift {math.hypot(me - ce, mn - cn):.2f} m")

    # A shared set is not on its own a junction. Two named roadways also share nodes where
    # one CHANGES NAME INTO the other at a bend, and that reads identically here — right
    # count, plausible spread, clean mean. The tell is that the set is a junction this file
    # has already committed under another name: at market_south_water the rule returns
    # lake_market's own two nodes, 110 m from the corner it was asked for. See `node_rule`.
    mine = {str(i) for i in shared}
    for other, c in sorted((doc.get("control") or {}).items()):
        if other == cid:
            continue
        if mine and mine == {str(i) for i in (c.get("osm_node_ids") or [])}:
            print(f"    REFUSED — this is exactly the node set already committed as "
                  f"'{other}', so the two named ways do not cross here: they meet at that "
                  f"junction and one changes name into the other. A control point made from "
                  f"it would name '{cid}' and stand at '{other}'.")
            return 1
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--discover", metavar="CONTROL_ID",
                    help="re-derive a junction's node set from its `osm_ways` names")
    ap.add_argument("--radius", type=float, default=130.0,
                    help="search half-size in metres for --discover (default 130)")
    ap.add_argument("--tol", type=float, default=1.0,
                    help="drift tolerance in metres for the verify pass (default 1.0)")
    args = ap.parse_args()

    doc = json.loads(CONTROL.read_text())
    try:
        if args.discover:
            return discover(doc, args.discover, args.radius)
        return verify(doc, args.tol)
    except Offline as e:
        print(f"OpenStreetMap could not be reached: {e}\n"
              f"This tool is on-demand and is not part of tools/check.sh, so this is a network "
              f"result, not a dataset result. Try again when you have one.")
        return 2


if __name__ == "__main__":
    sys.exit(main())
