#!/usr/bin/env python3
"""Eighteen inches of stack above every roof — the town's own by-law, measured.

**T-0333.** The Trustees of the Town of Chicago passed their by-laws on 5 August 1835,
and `chicago_democrat_1835_08_19#c005` prints section 18 line by line:

> *"every stove pipe or chimney passing through the roof of any building shall extend
> and be carried at least eighteen inches above the roof, and no stove pipe shall be
> passed through the side or end of any building"* — under a penalty of five dollars for
> each and every offence, with a fire warden walking every house, store and shop in his
> district once a month from September to May (section 21).

**This is the first documented DIMENSIONAL constraint this project holds on anything
above a roof line**, and it points the other way from the sentence the flagstaff work
quotes — Andreas describing a town with *"not a single steeple nor a chimney four feet
above any roof."* Four feet is a maximum a memoirist noticed; eighteen inches is a
minimum the town enforced, and together they bracket every stack in the scene.

## What it measures, and why on the bytes

`tools/measure_stack_fabric.py` (T-0137) asks what a stack is PAINTED and reads the
committed masters' accessor bounds to do it. This asks the neighbouring question — how
far a stack stands above the roof it passes through — off the same bounds and on the
same principle: **the generator is the thing under test, so ask the geometry, not the
generator.** A glTF POSITION accessor is required to carry `min`/`max`, so the highest
vertex of each material is readable from the JSON chunk with no mesh decoded.

The clearance is measured against the top of the `roof` material, which is the RIDGE.
That is the conservative reading in the two ways it can be wrong:

- A stack standing off the ridge — `frame_storefront` on a shed roof, `frame_tavern`
  across the frontage — breaks a roof plane LOWER than the ridge, so its true projection
  above its own roof is larger than the figure here.
- A building carrying stacks on two roofs (a `frame_dwelling` ell, a `log_dwelling`
  frame addition) reports its TALLEST stack. That the lower one clears its own ridge by
  the same margin is the archetype's guarantee, not this measurement's: every archetype
  builds each stack with one helper, relative to the ridge it is handed. Said plainly
  here rather than left for a reader to assume.

The declared `slope_offsets` and `far_gable` schemes are measured separately:
an offset stack or a separate belfry roof makes the global ridge an unsuitable
reference for the roof the stack passes through. Decode the actual
brick/chimney and upward roof triangles, recover every shaft and cap, and use the
highest roof point under the entire cap footprint for each stack. All stacks must
clear the same eighteen-inch floor; no generator heights or named-building
exemptions are used. Unsupported mesh layouts, missing roof coverage and a count
that disagrees with the record fail closed. Existing schemes keep the original
bounds reading. This is the project's existing dimensional ratchet, not evidence
that this undated retrospective image attests compliance in July1835.

## What the ordinance's second clause binds, which is nothing today

*"No stove pipe shall be passed through the side or end of any building."* **This model
draws no stove pipe anywhere.** Every one of the stacks below is masonry — brick on the
argument `docs/RESEARCH/chimneys.md` makes from Blodgett's yard, the brick Lake House and
the Petford watercolour — and the archetypes carry no pipe object at all. `log_dwelling`'s
stack stands OUTSIDE the gable rather than inside it, which is the frontier pattern and
not a pipe through an end wall: it is a chimney, and it is carried above the roof like
every other. So the clause is recorded and binds nothing that is drawn.

## The corporation limits, and why this gate is a ratchet rather than an enforcement

Section 18 binds *"within the limits of the Corporation"*, and until T-0436 this file
said that section 22 of the same sitting walks those limits. **IT DOES NOT.** Section 22
draws the hay-stacking boundary, which is a DIFFERENT and narrower line and is T-0334's
— committed since that ticket landed, at `data/reconstruction/1835_hay_limits.json`, and
199 acres against this boundary's 532. Reading section 22 as the corporate limits is a
mistake this docstring made and this paragraph retracts. The corporation's limits are the ones the Trustees walked on 7 November 1833
and printed three weeks later in the first number of the Chicago Democrat
(`chicago_democrat_1833_11_26#c024`, tier 1) — and since T-0436 they are committed, at
`data/reconstruction/1835_corporation_limits.json`, resolved by
`tools/measure_corporation_limits.py` from the committed streets and the committed
shoreline.

So this gate now knows which buildings the by-law reached, and says so: **twenty-four
drawn structures stand outside the limits, eight of them carrying twelve chimneys between
them, and section 18 never bound one of them.** All twenty-four are on the United States Reservation or the
harbour beyond it — ground the 1833 boundary walks around and the extension of February
1835 withheld again.

It still gates every stack in the town, and that is deliberate. Every stack already
clears eighteen inches on both sides of the line, so the ratchet costs nothing and keeps
one from dropping back under; and the twelve stacks beyond the line are held to the figure
by their archetypes rather than by the by-law. What has changed is that the reach is now REPORTED instead of
assumed, so nothing can be quietly conformed to a rule that never bound it. The day a
record legitimately stands a shorter stack outside the limits, that is the boundary to
scope on, and the failure message says which side of it the building is on.

    python3 tools/measure_stack_ordinance.py            the census
    python3 tools/measure_stack_ordinance.py --gate --quiet    check.sh's line
    python3 tools/measure_stack_ordinance.py --self-test       the assertions, fired

Exit 1 if any drawn stack stands less than eighteen inches above its roof.
"""
import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from measure_glbs import read_glb                       # noqa: E402
from measure_stack_fabric import chimney_count, material_tops, roof_top   # noqa: E402
from measure_corporation_limits import split as corporation_split   # noqa: E402

#: Eighteen inches, stated converted per data/datum.json's units rule.
MINIMUM_M = 18 * 0.0254

#: The materials an archetype builds a stack with. `roof` is excluded by construction —
#: a stack painted the colour of its own roof is T-0137's fault and its own gate.
STACK_MATERIALS = ("chimney", "brick")

#: A ridge is modelled to the centimetre, so a clearance is tested to the millimetre.
EPS_M = 0.0005


def local_stack_clearances(js, bins, expected):
    """Actual uncompressed, identity-node mesh: each stack over its own roof.

    Bounded to declared local-roof paths. Unsupported layouts fail closed;
    no generator heights, accessor bounds or structure-name exemptions are used.
    glTF is Y-up, so the horizontal footprint is X/Z. Shaft/cap mesh islands are
    welded by positions, then merged only when their XY footprints and Z ranges
    intersect (in Y-up terms, XZ and Y). Every recovered stack is measured.
    """
    import math
    import struct

    def refuse(why):
        raise ValueError("local stack measurement: " + why)

    def integer(value):
        return isinstance(value, int) and not isinstance(value, bool) and value >= 0

    if not integer(expected) or expected < 1:
        refuse("invalid expected chimney count")
    if js.get("extensionsUsed") or len(js.get("buffers", [])) != 1:
        refuse("extensions or multiple buffers unsupported")
    blob = bins.get(0)
    if not isinstance(blob, bytes) or js["buffers"][0].get("uri"):
        refuse("missing embedded buffer")
    if js["buffers"][0].get("byteLength") not in range(len(blob) - 3, len(blob) + 1):
        refuse("buffer length mismatch")
    nodes = js.get("nodes", [])
    if len(nodes) != 1 or nodes[0].get("children"):
        refuse("only one identity mesh node is supported")
    node = nodes[0]
    identity = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]
    for key, want in (("matrix", identity), ("translation", [0, 0, 0]),
                      ("rotation", [0, 0, 0, 1]), ("scale", [1, 1, 1])):
        if node.get(key, want) != want:
            refuse("nonidentity node transform unsupported")
    scenes = js.get("scenes", [])
    scene = js.get("scene", 0)
    if not integer(scene) or scene >= len(scenes) or scenes[scene].get("nodes") != [0]:
        refuse("unsafe scene roots")
    mesh_i = node.get("mesh")
    if not integer(mesh_i) or mesh_i >= len(js.get("meshes", [])):
        refuse("missing mesh")

    def accessor(index, positions=False):
        if not integer(index) or index >= len(js.get("accessors", [])):
            refuse("missing accessor")
        acc = js["accessors"][index]
        ct = acc.get("componentType")
        types = {5123: ("H", 2), 5125: ("I", 4), 5121: ("B", 1)}
        if positions:
            if ct != 5126 or acc.get("type") != "VEC3":
                refuse("POSITION must be unnormalized FLOAT VEC3")
            fmt, size, n = "f", 4, 3
        else:
            if ct not in types or acc.get("type") != "SCALAR":
                refuse("indices must be unsigned integer SCALAR")
            fmt, size = types[ct]
            n = 1
        if acc.get("normalized") or acc.get("sparse") or acc.get("extensions"):
            refuse("normalized/sparse/extension accessor unsupported")
        count, vi = acc.get("count"), acc.get("bufferView")
        if not integer(count) or count < 1 or not integer(vi) or vi >= len(js.get("bufferViews", [])):
            refuse("invalid count or buffer view")
        view = js["bufferViews"][vi]
        if view.get("buffer", 0) != 0 or view.get("extensions"):
            refuse("external/compressed view unsupported")
        vo, ao = view.get("byteOffset", 0), acc.get("byteOffset", 0)
        length, stride = view.get("byteLength"), view.get("byteStride", size * n)
        if not all(integer(x) for x in (vo, ao, length, stride)) or stride < size * n or stride % size:
            refuse("invalid view layout")
        if vo + length > len(blob) or ao + (count - 1) * stride + size * n > length:
            refuse("truncated accessor")
        values = [struct.unpack_from("<" + fmt * n, blob, vo + ao + i * stride)
                  for i in range(count)]
        if positions and not all(math.isfinite(x) for point in values for x in point):
            refuse("nonfinite POSITION")
        return values

    bricks, roofs = [], []
    for prim in js["meshes"][mesh_i].get("primitives", []):
        mi = prim.get("material")
        if not integer(mi) or mi >= len(js.get("materials", [])):
            refuse("invalid material")
        name = js["materials"][mi].get("name", "")
        target = bricks if name in STACK_MATERIALS else roofs if name == "roof" or name.startswith("roof_") else None
        if target is None:
            continue
        if prim.get("mode", 4) != 4 or prim.get("extensions") or prim.get("targets"):
            refuse("only static uncompressed triangles supported")
        points = accessor(prim.get("attributes", {}).get("POSITION"), True)
        ix = [v[0] for v in accessor(prim.get("indices"))]
        if len(ix) % 3 or any(i >= len(points) for i in ix):
            refuse("invalid triangle indices")
        for offset in range(0, len(ix), 3):
            tri = tuple(points[i] for i in ix[offset:offset + 3])
            a, b, c = tri
            cross = ((b[1]-a[1])*(c[2]-a[2])-(b[2]-a[2])*(c[1]-a[1]),
                     (b[2]-a[2])*(c[0]-a[0])-(b[0]-a[0])*(c[2]-a[2]),
                     (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))
            if sum(v*v for v in cross) <= 1e-16:
                refuse("degenerate triangle")
            if target is bricks or cross[1] > 1e-9:
                target.append(tri)
    if not bricks or not roofs:
        refuse("missing stack or upward roof triangles")

    # Exported faces split normals/UVs, so index connectivity is insufficient.
    parent = list(range(len(bricks)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def join(i, j):
        parent[find(i)] = find(j)

    seen = {}
    for i, tri in enumerate(bricks):
        for point in tri:
            key = tuple(round(x, 6) for x in point)
            if key in seen:
                join(i, seen[key])
            seen[key] = i
    islands = {}
    for i, tri in enumerate(bricks):
        islands.setdefault(find(i), []).extend(tri)
    boxes = [[list(min(p[k] for p in points) for k in range(3)),
              list(max(p[k] for p in points) for k in range(3))]
             for points in islands.values()]
    if any(any(hi[k] - lo[k] <= 1e-6 for k in range(3)) for lo, hi in boxes):
        refuse("stack island has no volume")
    # A cap touches its shaft at a different rectangle, without welded vertices.
    changed = True
    while changed:
        changed = False
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                a, b = boxes[i], boxes[j]
                horizontal = all(min(a[1][k], b[1][k]) - max(a[0][k], b[0][k]) > 1e-6 for k in (0, 2))
                vertical = min(a[1][1], b[1][1]) - max(a[0][1], b[0][1]) >= -1e-5
                if horizontal and vertical:
                    boxes[i] = [[min(a[0][k], b[0][k]) for k in range(3)],
                                [max(a[1][k], b[1][k]) for k in range(3)]]
                    boxes.pop(j)
                    changed = True
                    break
            if changed:
                break
    if len(boxes) != expected:
        refuse(f"record counts {expected} stacks; mesh recovers {len(boxes)}")

    def clip(poly, axis, edge, sign):
        out = []
        for a, b in zip(poly, poly[1:] + poly[:1]):
            da, db = sign * (a[axis] - edge), sign * (b[axis] - edge)
            if da >= 0:
                out.append(a)
            if (da < 0) != (db < 0):
                t = da / (da - db)
                out.append(tuple(a[k] + t * (b[k] - a[k]) for k in range(3)))
        return out

    def height(tri, x, z):
        a, b, c = tri
        det = (b[2]-c[2])*(a[0]-c[0]) + (c[0]-b[0])*(a[2]-c[2])
        if abs(det) < 1e-12:
            return None
        u = ((b[2]-c[2])*(x-c[0]) + (c[0]-b[0])*(z-c[2])) / det
        v = ((c[2]-a[2])*(x-c[0]) + (a[0]-c[0])*(z-c[2])) / det
        if min(u, v, 1-u-v) < -1e-6:
            return None
        return u*a[1] + v*b[1] + (1-u-v)*c[1]

    results = []
    for lo, hi in sorted(boxes, key=lambda b: (b[0][0], b[0][2])):
        samples = [(x, z) for x in (lo[0], hi[0]) for z in (lo[2], hi[2])]
        samples.append(((lo[0]+hi[0])/2, (lo[2]+hi[2])/2))
        sampled = []
        for x, z in samples:
            values = [h for tri in roofs if (h := height(tri, x, z)) is not None]
            if not values:
                refuse("roof missing under stack footprint corner/centre")
            sampled.append(max(values))
        # Clipping also catches a ridge crossing the cap away from the centre:
        # a linear triangle's maximum is at a clipped vertex, not an arbitrary sample.
        clipped, area = [], 0.0
        for tri in roofs:
            poly = list(tri)
            for axis, edge, sign in ((0, lo[0], 1), (0, hi[0], -1),
                                     (2, lo[2], 1), (2, hi[2], -1)):
                poly = clip(poly, axis, edge, sign) if poly else []
            if len(poly) < 3:
                continue
            a = abs(sum(p[0]*q[2]-q[0]*p[2] for p, q in zip(poly, poly[1:]+poly[:1]))) / 2
            if a > 1e-10:
                area += a
                clipped.extend(p[1] for p in poly)
        wanted = (hi[0]-lo[0])*(hi[2]-lo[2])
        if abs(area-wanted) > max(1e-6, wanted*1e-5) or not clipped:
            refuse("roof does not cover footprint once (hole/overlap)")
        roof = max(clipped + sampled)
        if not lo[1] < roof < hi[1]:
            refuse("stack does not penetrate measured roof")
        results.append({"bbox_min": lo, "bbox_max": hi, "top": hi[1],
                        "roof_top": roof, "above": hi[1]-roof,
                        "roof_samples": sampled})
    return results


def readings():
    """One row per phase whose record counts a chimney and whose master is committed."""
    manifest = json.loads((ROOT / "assets" / "manifest.json").read_text())["assets"]
    by_key = {(a["structure_id"], a.get("phase_id")): name
              for name, a in manifest.items() if "structure_id" in a}
    arch_of = {(a["structure_id"], a.get("phase_id")): a.get("archetype")
               for a in manifest.values() if "structure_id" in a}

    out = []
    for path in sorted((ROOT / "data" / "structures").glob("*.json")):
        rec = json.loads(path.read_text())
        for phase in rec.get("phases", []):
            n = chimney_count(phase)
            placement = (phase.get("form", {}).get("chimney_placement", {}) or {}).get("value")
            local_roof = placement in ("slope_offsets", "far_gable")
            if n <= 0 and not local_roof:
                continue
            key = (rec["id"], phase.get("id"))
            if key not in by_key:
                if local_roof:
                    raise ValueError(f"{key}: {placement} has no committed master")
                continue
            glb = read_glb(ROOT / "assets" / "gltf" / by_key[key])
            if local_roof:
                expected_archetype = {"slope_offsets": "frame_tavern", "far_gable": "frame_dwelling"}[placement]
                if arch_of[key] != expected_archetype:
                    raise ValueError(f"{key}: unsupported {placement} archetype")
                measured = local_stack_clearances(*glb, n)
                worst = min(measured, key=lambda row: row["above"])
                names = {m.get("name") for m in glb[0].get("materials", [])}
                out.append({"id": rec["id"], "archetype": arch_of[key], "stacks": n,
                            "material": "+".join(sorted(names.intersection(STACK_MATERIALS))),
                            "roof_top": worst["roof_top"], "above": worst["above"],
                            "per_stack": measured})
                continue
            tops = material_tops(glb[0])
            # The COVERING, whatever the sheet named it — `roof_top` and not
            # `tops["roof"]`, which skipped every `outbuilding` in the town until
            # T-1680 because its slot is called `roof_board`.
            _, roof = roof_top(tops)
            if roof is None:
                continue
            stack = {m: t for m, t in tops.items() if m in STACK_MATERIALS}
            if not stack:
                continue
            material, top = max(stack.items(), key=lambda kv: kv[1])
            out.append({"id": rec["id"], "archetype": arch_of[key], "stacks": n,
                        "material": material, "roof_top": roof, "above": top - roof})
    return out


def offenders(rows):
    return [r for r in rows if r["above"] < MINIMUM_M - EPS_M]


def report(rows, quiet=False):
    bad = offenders(rows)
    _inside, outside = corporation_split()
    beyond = [r for r in rows if r["id"] in set(outside)]
    if not quiet:
        width = max((len(r["id"]) for r in rows), default=10)
        print(f"{'structure':<{width}}  {'archetype':<18} {'stacks':>6} "
              f"{'material':<9} {'above its roof':>16}")
        for r in rows:
            flag = "   <- UNDER EIGHTEEN INCHES" if r in bad else ""
            print(f"{r['id']:<{width}}  {(r['archetype'] or '?'):<18} {r['stacks']:>6} "
                  f"{r['material']:<9} {r['above']:>10.3f} m "
                  f"({r['above'] / 0.0254:>4.1f} in){flag}")
        print()

        by_arch = {}
        for r in rows:
            by_arch.setdefault(r["archetype"], []).append(r["above"])
        print("by archetype — the ordinance's floor is 0.457 m (18.0 in):")
        for arch in sorted(by_arch, key=str):
            v = by_arch[arch]
            print(f"  {(arch or '?'):<18} {len(v):>4} building(s)  "
                  f"least {min(v):.3f} m ({min(v) / 0.0254:.1f} in)  "
                  f"most {max(v):.3f} m ({max(v) / 0.0254:.1f} in)")

        print(f"\nwhich of them the by-law actually reached — the limits of the "
              f"Corporation as the Trustees\nwalked them on 7 November 1833 "
              f"(chicago_democrat_1833_11_26#c024, resolved by\n"
              f"tools/measure_corporation_limits.py):")
        print(f"  inside the limits  {len(rows) - len(beyond):>4} building(s), "
              f"{sum(r['stacks'] for r in rows if r not in beyond):>4} stack(s) — "
              f"section 18 bound these")
        print(f"  outside them       {len(beyond):>4} building(s), "
              f"{sum(r['stacks'] for r in beyond):>4} stack(s) — it bound none of "
              f"these, and they are gated anyway")
        for r in beyond:
            print(f"      {r['id']:<34} {r['above']:.3f} m "
                  f"({r['above'] / 0.0254:.1f} in)")

    stacks = sum(r["stacks"] for r in rows)
    if bad:
        n = sum(r["stacks"] for r in bad)
        print(f"FAIL: {len(bad)} building(s) carrying {n} stack(s) stand less than "
              f"eighteen inches above their own roof, which the Town of Chicago's "
              f"by-law of 5 August 1835 section 18 forbids under a five-dollar penalty "
              f"(chicago_democrat_1835_08_19#c005): "
              f"{', '.join('%s %.3f m' % (r['id'], r['above']) for r in bad)}. "
              f"Raise the stack, or — if the building stands OUTSIDE the limits of the "
              f"Corporation — scope this gate on the boundary of 7 November 1833 "
              f"(data/reconstruction/1835_corporation_limits.json; "
              f"tools/measure_corporation_limits.py names the "
              f"{len(outside)} structure(s) that are outside it today) and say in the "
              f"record which side of it the building is on. Do not weaken the eighteen "
              f"inches: it is a documented figure.")
        return 1
    if not quiet:
        least = min(rows, key=lambda r: r["above"])
        print(f"\nOK: all {stacks} stack(s) on {len(rows)} building(s) are carried at "
              f"least eighteen inches above their own roof. The tightest is "
              f"{least['id']} at {least['above']:.3f} m "
              f"({least['above'] / 0.0254:.1f} in).")
    else:
        print(f"OK: all {stacks} stack(s) on {len(rows)} building(s) clear eighteen "
              f"inches above their own roof, per the by-law of 5 August 1835 § 18.")
    return 0


def local_stack_self_test():
    """Actual triangle fixtures; no generator module or height metadata."""
    import math
    import struct

    failures = []

    def fixture(rises=(0.8, 0.8, 0.8, 0.8), ridge=False, distant_roof=False):
        if ridge:
            # A ridge inside the cap but away from its centre. Five samples
            # alone miss its maximum; the clipped triangle vertices must catch it.
            roof = []
            for z0, h0, z1, h1 in ((0, 5, 3.1, 5.31), (3.1, 5.31, 8, 4.82)):
                a,b,c,d = (0,h0,z0),(0,h1,z1),(20,h1,z1),(20,h0,z0)
                roof.extend(((a,b,c),(a,c,d)))
            foot = 5.3
        else:
            a,b,c,d = (0,5,0),(0,7.4,8),(20,7.4,8),(20,5,0)
            roof, foot = [(a,b,c),(a,c,d)], 5.9
        if distant_roof:
            # A tall roof outside every stack footprint (a belfry, for example).
            # Its global maximum must neither condemn a compliant local stack
            # nor excuse a short one on the roof it actually penetrates.
            a,b,c,d = (18,20,0),(18,20,2),(20,20,2),(20,20,0)
            roof.extend(((a,b,c),(a,c,d)))
        brick = []

        def box(x0,y0,z0,x1,y1,z1):
            p = [(x,y,z) for x in (x0,x1) for y in (y0,y1) for z in (z0,z1)]
            # Five faces: no lower face, matching emitted shaft/cap boxes.
            for a,b,c,d in ((0,1,3,2),(4,6,7,5),(0,2,6,4),(2,3,7,6),(1,5,7,3)):
                brick.extend(((p[a],p[b],p[c]),(p[a],p[c],p[d])))
        for x, rise in zip((2,6,10,14), rises):
            box(x-.25,foot-.3,2.75,x+.25,foot+rise,3.25)
            box(x-.3,foot+rise,2.7,x+.3,foot+rise+.075,3.3)
        js = {"buffers": [], "bufferViews": [], "accessors": [],
              "materials": [{"name":"roof_shingle"},{"name":"brick"}],
              "meshes":[{"primitives":[]}], "nodes":[{"mesh":0}],
              "scenes":[{"nodes":[0]}], "scene":0}
        blob = bytearray()
        for material, triangles in enumerate((roof,brick)):
            vertices = [p for tri in triangles for p in tri]
            attrs = []
            for kind, ct, fmt, data in (("VEC3",5126,"fff",vertices),
                                         ("SCALAR",5125,"I",[(i,) for i in range(len(vertices))])):
                while len(blob)%4:
                    blob.append(0)
                start = len(blob)
                for value in data:
                    blob.extend(struct.pack("<"+fmt,*value))
                js["bufferViews"].append({"buffer":0,"byteOffset":start,"byteLength":len(blob)-start})
                js["accessors"].append({"bufferView":len(js["bufferViews"])-1,
                                        "componentType":ct,"type":kind,"count":len(data)})
                attrs.append(len(js["accessors"])-1)
            js["meshes"][0]["primitives"].append({"material":material,"attributes":{"POSITION":attrs[0]},"indices":attrs[1]})
        js["buffers"] = [{"byteLength":len(blob)}]
        return js,{0:bytes(blob)}

    def check(label, assertion):
        if not assertion:
            failures.append(label)
        print(f"  {'ok   ' if assertion else 'FAIL '}: {label}")

    def rejects(label, edit, expected=4):
        js, bins = fixture()
        edit(js,bins)
        try:
            local_stack_clearances(js,bins,expected)
        except (ValueError, KeyError, IndexError, TypeError, struct.error):
            check(label, True)
        else:
            check(label, False)

    js,bins = fixture()
    rows = local_stack_clearances(js,bins,4)
    check("four shafts/caps recovered from split-face triangle vertices", len(rows)==4)
    check("whole-cap highest roof gives exact conservative clearance", all(abs(r['above']-.785)<1e-5 for r in rows))
    check("all four locally compliant offset stacks pass", not offenders(rows))
    low = local_stack_clearances(*fixture((.8,.2,.8,.8)),4)
    check("one short offset stack fails while three taller stacks remain compliant",
          len(offenders(low))==1 and sum(r['above']>=MINIMUM_M for r in low)==3)
    distant = local_stack_clearances(*fixture(distant_roof=True),4)
    check("a distant higher roof does not replace each stack's actual roof",
          distant == rows)
    near_floor = local_stack_clearances(*fixture(
        (MINIMUM_M+.015-.001,.8,.8,.8), distant_roof=True),4)
    check("a stack one millimetre below the local floor still fails beside a higher roof",
          len(offenders(near_floor))==1 and abs(near_floor[0]['above']-(MINIMUM_M-.001))<1e-5)
    ridge = local_stack_clearances(*fixture(ridge=True),4)
    check("clipped triangles catch off-centre ridge missed by five point samples",
          all(abs(r['roof_top']-5.31)<1e-5 and r['roof_top']>max(r['roof_samples'])+.009 for r in ridge))
    rejects("missing roof fails closed", lambda j,b:j['meshes'][0]['primitives'].pop(0))
    rejects("missing roof coverage at a cap corner fails closed", lambda j,b:j['accessors'][1].update(count=3))
    rejects("record/mesh chimney count disagreement fails closed", lambda j,b:None,3)
    rejects("truncated binary fails closed", lambda j,b:b.update({0:b[0][:-20]}))
    rejects("out-of-range indices fail closed", lambda j,b:b.update({0:b[0][:72]+struct.pack('<I',999999)+b[0][76:]}))
    rejects("normalized POSITION fails closed", lambda j,b:j['accessors'][0].update(normalized=True))
    rejects("sparse POSITION fails closed", lambda j,b:j['accessors'][0].update(sparse={'count':1}))
    rejects("nonfinite POSITION fails closed", lambda j,b:b.update({0:struct.pack('<f',math.nan)+b[0][4:]}))
    rejects("nonidentity node transforms fail closed", lambda j,b:j['nodes'][0].update(translation=[0,1,0]))
    rejects("wrong scene roots fail closed", lambda j,b:j['scenes'][0].update(nodes=[]))
    return failures


def self_test():
    """The four ways this could pass something it should refuse, fired."""
    cases = [
        ("a stack exactly on the ordinance's floor passes",
         [{"id": "a", "archetype": "x", "stacks": 1, "material": "chimney",
           "roof_top": 4.0, "above": MINIMUM_M}], 0),
        ("a stack a millimetre under it fails",
         [{"id": "a", "archetype": "x", "stacks": 1, "material": "chimney",
           "roof_top": 4.0, "above": MINIMUM_M - 0.001}], 1),
        ("a stack level with its own roof fails",
         [{"id": "a", "archetype": "x", "stacks": 1, "material": "chimney",
           "roof_top": 4.0, "above": 0.0}], 1),
        ("one short stack among compliant ones still fails",
         [{"id": "a", "archetype": "x", "stacks": 1, "material": "chimney",
           "roof_top": 4.0, "above": 0.78},
          {"id": "b", "archetype": "x", "stacks": 2, "material": "brick",
           "roof_top": 4.0, "above": 0.30}], 1),
    ]
    failures = []
    for label, rows, want in cases:
        got = 1 if offenders(rows) else 0
        print(f"  {'fires' if want else 'ok   '}: {label}")
        if got != want:
            failures.append(label)

    # The floor is the ordinance's figure and not a rounded one.
    if abs(MINIMUM_M - 0.4572) > 1e-9:
        failures.append("MINIMUM_M is not eighteen inches")
    print(f"  ok   : the floor is eighteen inches exactly ({MINIMUM_M:.4f} m)")

    failures.extend(local_stack_self_test())

    if failures:
        print("SELF-TEST FAIL: " + "; ".join(failures))
        return 1
    print(f"SELF-TEST PASS — the ordinance gate fires when broken ({len(cases)} cases)")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate", action="store_true", help="pass/fail only")
    ap.add_argument("--quiet", action="store_true", help="suppress the per-building table")
    ap.add_argument("--self-test", action="store_true",
                    help="prove the gate refuses a short stack")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    return report(readings(), quiet=args.gate or args.quiet)


if __name__ == "__main__":
    raise SystemExit(main())
