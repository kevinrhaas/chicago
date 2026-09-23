"""Every stack measured against ITS OWN roof, one stack at a time.

**T-0333's other half.** `tools/measure_stack_ordinance.py` is the gate on the Trustees'
ordinance of 5 August 1835 section 18 (`chicago_democrat_1835_08_19` c005) — every stove
pipe or chimney passing through a roof carried at least eighteen inches above it — and it
reads the committed masters' glTF accessor bounds, which is the right instrument for a
pass/fail on the by-law and is deliberately conservative. **This is not a second gate and
it is not wired into `tools/check.sh`.** The by-law has one gate and that one is it.

What this is, is the measurement that gate names as an assumption rather than a reading:

    A building carrying stacks on two roofs (a `frame_dwelling` ell, a `log_dwelling`
    frame addition) reports its TALLEST stack. That the lower one clears its own ridge
    by the same margin is the archetype's guarantee, not this measurement's.

A glTF POSITION accessor carries ONE bound per primitive, so an ell's low stack and the
main block's high one collapse into a single number and "the roof" collapses to the
tallest ridge on the building. That is fine for a floor and cannot answer a question about
a particular stack, and two questions here are about particular stacks: whether the lower
stack on a two-roof building really does clear its own ridge, and which wall each stack
actually stands against.

## How it reads a stack the bounds cannot

It runs the archetypes themselves, outside Blender: `common/mesh.MeshBuilder` accumulates
plain vertex and face lists and only needs bpy at `to_object`, which is stubbed here along
with `simple_material`. Nothing about the committed bytes is assumed and nothing is
re-baked.

**Finding the stacks is archetype-blind, on the same principle the fabric gate argues —
ask the geometry, not the generator.** Every archetype gates its stacks on the record's
`chimneys` count and draws them in the ROOF material when it is zero, so each building is
built TWICE — once as the record states it, once with the count forced to zero — and the
boxes that appear only in the first, or that appear in both but change material, ARE the
stacks. No archetype's private helper is called and no material name is trusted.

**The roof under a stack** is then sampled off the chimneyless build: every face drawn in
the `roof` material, projected to plan, and the highest roof surface standing over the
stack's own footprint. A stack that stands wholly OUTSIDE the roof's plan takes the highest
roof just beyond its footprint instead, and the table's `how` column says which answered.

## What it found on the tree of 2026-08-30

- **234 stacks on 213 buildings, per stack rather than per building.** The gate's floor
  holds stack by stack, not only building by building: the minimum is the eleven frame
  taverns' 0.550 m (21.7 in) and nothing else is within eight inches of eighteen.
- **`miller_house` is the case the bounds cannot see.** Its second stack stands on the
  frame addition and its head is 2.271 m BELOW the log core's ridge — exactly as
  `log_dwelling._chimneys` argues it should be, and exactly what a bounds reading would
  have to call a stack sunk into its roof.
- **30 of `log_dwelling`'s 47 stacks stand against an EAVE wall, not a gable end** —
  T-0435, which is what this instrument was worth building for. The split is clean: the
  17 gable stacks all clear 0.720 m and the 30 eave stacks clear 2.344 to 3.197 m, because
  an eave stack runs up past a roof that is at eave height beside it and keeps going.
- **One reading it cannot make:** one fort stack's building draws no horizontal ridge edge
  in the roof material, so `--walls` reports `unfound` for it rather than guessing. Its
  clearance is measured like every other.

    python3 tools/measure_stack_projection.py            # the whole town
    python3 tools/measure_stack_projection.py --short    # only stacks under the floor
    python3 tools/measure_stack_projection.py --walls    # gable end or eave, per stack
"""
from __future__ import annotations

import argparse
import importlib
import json
import pathlib
import sys
import types

ROOT = pathlib.Path(__file__).resolve().parents[1]

#: The ordinance's own figure. Eighteen inches, in metres, exactly.
FLOOR_M = 18 * 0.0254

#: Andreas's retrospective ceiling — "not a single steeple nor a chimney four feet
#: above any roof". REPORTED, never gated: it is one memoirist's impression of a
#: skyline fifty years later, not a rule anybody enforced, and this file does not
#: promote it into one.
ANDREAS_CEILING_M = 4 * 0.3048


# --------------------------------------------------------------- headless build

def _install_stubs():
    """Make `generators/` importable without Blender, and make MeshBuilder observable.

    `simple_material` is rebound on the module BEFORE the archetypes are imported,
    because they do `from common.mesh import simple_material` and that copies the
    binding. `to_object` and `add_box` are patched on the class, which resolves at
    call time, so their order does not matter.
    """
    sys.path.insert(0, str(ROOT / "generators"))
    sys.modules.setdefault("bpy", types.ModuleType("bpy"))
    import common.mesh as mesh

    mesh.simple_material = lambda name, rgba=(0.8, 0.8, 0.8, 1.0), roughness=0.75: \
        types.SimpleNamespace(name=name)

    original_add_box = mesh.MeshBuilder.add_box

    def add_box(self, x0, y0, z0, x1, y1, z1, confidence, mat=0, skip=()):
        first = len(self.faces)
        out = original_add_box(self, x0, y0, z0, x1, y1, z1, confidence, mat, skip)
        self.boxes.append({
            "geom": (min(x0, x1), min(y0, y1), min(z0, z1),
                     max(x0, x1), max(y0, y1), max(z0, z1)),
            "mat": mat,
            "faces": range(first, len(self.faces)),
        })
        return out

    original_init = mesh.MeshBuilder.__init__

    def init(self, name):
        original_init(self, name)
        self.boxes = []

    mesh.MeshBuilder.__init__ = init
    mesh.MeshBuilder.add_box = add_box
    mesh.MeshBuilder.to_object = lambda self, materials=None: (self, materials)
    return mesh


def chimney_count(phase) -> int:
    v = (phase.get("form") or {}).get("chimneys")
    if isinstance(v, dict):
        v = v.get("value")
    return v if isinstance(v, int) else 0


def build(archetype: str, phase: dict, name: str, chimneys: int | None = None):
    """(MeshBuilder, [material]) for one phase, optionally with the count overridden."""
    params_mod = importlib.import_module(f"archetypes.{archetype}_params")
    build_mod = importlib.import_module(f"archetypes.{archetype}")
    params = params_mod.from_phase(phase)
    if chimneys is not None:
        # Set on the constructed object rather than in the record, and with the
        # archetype's own validator shadowed for this build alone: the dataclass
        # enforces cross-attribute rules a zero count trips on purpose
        # (frame_tavern's `gable_ends` demands exactly 2), and the real build a few
        # lines above has already run every one of them against the record as
        # committed. This second pass is a measuring rig, not a build.
        object.__setattr__(params, "chimneys", chimneys)
        object.__setattr__(params, "validate", lambda: None)
    return build_mod.build(params, name)


# --------------------------------------------------------------------- geometry

def stacks_of(with_stacks, without) -> tuple[list[dict], set[int]]:
    """(the stacks, the faces of the chimneyless build that are really stack).

    A stack is a box the chimneyless build does not have — or, in one archetype, a
    box it has in the ROOF material. Every archetype paints its stacks with `M_ROOF`
    when the count is zero, which is why `measure_stack_fabric` exists at all, and
    `frame_tavern`'s `gable_ends` branch also draws its two boxes unconditionally
    (its validator refuses `gable_ends` with any count but 2, so no committed record
    reaches that state; this rig does, because it shadows the validator). Either way
    the second returned value names the faces the roof sampler must not read, or a
    stack would be measured against a copy of itself and clear its roof by zero.

    Boxes are grouped into stacks by overlap in plan: a shaft and the corbelled head
    that sits on it always overlap, and no two stacks in any archetype here stand
    close enough to (the fort's six are 0.92 m apart at their nearest faces).
    """
    pool: dict[tuple, list[dict]] = {}
    for b in without.boxes:
        pool.setdefault(b["geom"], []).append(b)

    extra, shadowed = [], set()
    for b in with_stacks.boxes:
        twins = pool.get(b["geom"])
        same = next((t for t in twins if t["mat"] == b["mat"]), None) if twins else None
        if same is not None:
            twins.remove(same)
            continue
        if twins:
            # Same volume, different material: the chimneyless build drew this stack
            # in the roof's own paint. It is a stack, and its faces are not roof.
            shadowed.update(twins.pop()["faces"])
        extra.append(b["geom"])

    groups: list[list[tuple]] = []
    for g in extra:
        hit = [grp for grp in groups if any(_overlaps_xy(g, o) for o in grp)]
        if not hit:
            groups.append([g])
            continue
        first = hit[0]
        first.append(g)
        for other in hit[1:]:
            first.extend(other)
            groups.remove(other)

    out = []
    for grp in groups:
        out.append({
            "x0": min(g[0] for g in grp), "y0": min(g[1] for g in grp),
            "x1": max(g[3] for g in grp), "y1": max(g[4] for g in grp),
            "top": max(g[5] for g in grp), "boxes": len(grp),
        })
    out.sort(key=lambda s: (round(s["x0"], 3), round(s["y0"], 3)))
    return out, shadowed


def _overlaps_xy(a, b) -> bool:
    """Two box geometries share ground in plan."""
    return not (a[3] <= b[0] or b[3] <= a[0] or a[4] <= b[1] or b[4] <= a[1])


def roof_faces(builder, materials, skip: set[int] | None = None) -> list[list[tuple]]:
    """Every face drawn in the `roof` material that has area in plan.

    Vertical faces — a gable end triangle is one, and so is every side of a box —
    project to a line and can carry no point, so they are dropped here rather than
    guarded against in the sampler.
    """
    idx = [i for i, m in enumerate(materials or []) if getattr(m, "name", None) == "roof"]
    if not idx:
        return []
    want = set(idx)
    skip = skip or set()
    out = []
    for n, (face, mat) in enumerate(zip(builder.faces, builder.mat_index)):
        if mat not in want or n in skip:
            continue
        pts = [builder.verts[i] for i in face]
        if _plan_area(pts) < 1e-6:
            continue
        out.append(pts)
    return out


def _plan_area(pts) -> float:
    a = 0.0
    for i in range(len(pts)):
        x0, y0 = pts[i][0], pts[i][1]
        x1, y1 = pts[(i + 1) % len(pts)][0], pts[(i + 1) % len(pts)][1]
        a += x0 * y1 - x1 * y0
    return abs(a) / 2.0


def _inside(pts, x, y, pad=0.0) -> bool:
    """Point in polygon, in plan, with an optional outward tolerance.

    `pad` is applied by testing the point against the polygon grown about its own
    plan centroid, which is exact for the convex quads and triangles every roof
    builder here emits and never used for anything else.
    """
    if pad:
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        scale = 1.0 + pad
        pts = [(cx + (p[0] - cx) * scale, cy + (p[1] - cy) * scale, p[2]) for p in pts]
    inside = False
    n = len(pts)
    for i in range(n):
        x0, y0 = pts[i][0], pts[i][1]
        x1, y1 = pts[(i + 1) % n][0], pts[(i + 1) % n][1]
        if (y0 > y) != (y1 > y):
            xi = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
            if x <= xi:
                inside = not inside
    return inside


def _plane_z(pts, x, y):
    """z on the face's plane. Every roof face here is planar by construction."""
    (ax, ay, az), (bx, by, bz), (cx, cy, cz) = pts[0], pts[1], pts[2]
    ux, uy, uz = bx - ax, by - ay, bz - az
    vx, vy, vz = cx - ax, cy - ay, cz - az
    nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
    if abs(nz) < 1e-9:
        return None
    return az - (nx * (x - ax) + ny * (y - ay)) / nz


def roof_under(faces, stack, samples: int = 9, reach: float = 0.0):
    """The highest roof surface over a stack's own plan footprint.

    Sampled on a grid rather than solved, because a stack can straddle a ridge and
    two roof planes, and the highest point of the roof it passes through is the one
    the ordinance is about — a flue clearing the ridge by eighteen inches clears the
    slope beside it by more.
    """
    best = None
    for i in range(samples):
        for j in range(samples):
            x = stack["x0"] + (stack["x1"] - stack["x0"]) * i / (samples - 1)
            y = stack["y0"] + (stack["y1"] - stack["y0"]) * j / (samples - 1)
            for pts in faces:
                if not _inside(pts, x, y, pad=reach):
                    continue
                z = _plane_z(pts, x, y)
                if z is not None and (best is None or z > best):
                    best = z
    return best


def wall_of(faces, stack):
    """Which wall a stack stands against: `gable`, `eave`, or `interior`.

    Archetype-blind, and the rule is stated rather than tuned. The roof's own RIDGE
    gives the frame: the horizontal edge at the roof's highest z fixes an along-ridge
    direction and an across-ridge one. A stack's offset from the roof's plan centroid is
    resolved in that frame and divided by the roof's own half-extent on each axis, so
    both numbers are 1.0 at the roof's edge whatever the building's size.

    Past 0.9 on the along-ridge axis the stack is at a gable END; past 0.9 across it, it
    is against an EAVE; short of both it stands inside the roof's plan and breaks it
    somewhere between, which is `interior`. Ties go to the larger of the two.

    The 0.9 is the one number here that is a choice rather than a measurement. It is
    loose on purpose: every stack in the town scores either under 0.55 or over 0.98 on
    its deciding axis, so no reading in the census sits near it.
    """
    if not faces:
        return "unfound"
    top = max(p[2] for f in faces for p in f)
    ridge = None
    for f in faces:
        n = len(f)
        for i in range(n):
            a, b = f[i], f[(i + 1) % n]
            if abs(a[2] - top) < 1e-6 and abs(b[2] - top) < 1e-6:
                dx, dy = b[0] - a[0], b[1] - a[1]
                if dx * dx + dy * dy > 1e-6:
                    ridge = (dx, dy)
                    break
        if ridge:
            break
    if ridge is None:
        return "unfound"
    length = (ridge[0] ** 2 + ridge[1] ** 2) ** 0.5
    ux, uy = ridge[0] / length, ridge[1] / length

    pts = [p for f in faces for p in f]
    along = [p[0] * ux + p[1] * uy for p in pts]
    across = [-p[0] * uy + p[1] * ux for p in pts]
    ca, cc = (min(along) + max(along)) / 2, (min(across) + max(across)) / 2
    ha, hc = (max(along) - min(along)) / 2, (max(across) - min(across)) / 2

    sx, sy = (stack["x0"] + stack["x1"]) / 2, (stack["y0"] + stack["y1"]) / 2
    a = abs((sx * ux + sy * uy) - ca) / ha if ha > 1e-9 else 0.0
    c = abs((-sx * uy + sy * ux) - cc) / hc if hc > 1e-9 else 0.0
    if max(a, c) < 0.9:
        return "interior"
    return "gable" if a >= c else "eave"


# ---------------------------------------------------------------------- reading

def readings(limit=None) -> list[dict]:
    mesh = _install_stubs()  # noqa: F841  (import side effect is the point)
    manifest = json.loads((ROOT / "assets" / "manifest.json").read_text())["assets"]
    arch_of = {(a["structure_id"], a.get("phase_id")): a.get("archetype")
               for a in manifest.values() if "structure_id" in a}

    rows = []
    for path in sorted((ROOT / "data" / "structures").glob("*.json")):
        rec = json.loads(path.read_text())
        if limit and rec["id"] not in limit:
            continue
        for phase in rec.get("phases", []):
            n = chimney_count(phase)
            if n <= 0:
                continue
            key = (rec["id"], phase.get("id"))
            arch = arch_of.get(key)
            if arch is None:
                continue
            built, mats = build(arch, phase, rec["id"])
            bare, _ = build(arch, phase, rec["id"], chimneys=0)
            found, shadowed = stacks_of(built, bare)
            faces = roof_faces(bare, mats, skip=shadowed)
            # The building's own skyline: the highest roof surface it draws anywhere.
            # This is what Andreas's four feet is about — a stack seen against the sky
            # from the street — and it is NOT the ordinance's measure, which is local
            # to the roof the flue comes through.
            ridge = max((p[2] for f in faces for p in f), default=None)
            for k, st in enumerate(found):
                z = roof_under(faces, st)
                how = "through"
                if z is None:
                    # An exterior gable stack stands beside the roof, not under it.
                    # 0.35 grows each face about its own centroid, which reaches the
                    # 0.72 m `log_dwelling` builds proud of the gable.
                    z = roof_under(faces, st, reach=0.35)
                    how = "beside"
                rows.append({
                    "id": rec["id"], "phase": phase.get("id"), "archetype": arch,
                    "stack": k + 1, "counted": n, "top": st["top"],
                    "roof": z, "how": how if z is not None else "unfound",
                    "clear": None if z is None else st["top"] - z,
                    "ridge": ridge, "wall": wall_of(faces, st),
                    "over_ridge": None if ridge is None else st["top"] - ridge,
                })
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--short", action="store_true",
                    help="only stacks under the ordinance's eighteen inches")
    ap.add_argument("--walls", action="store_true",
                    help="which wall each stack stands against, summarised")
    ap.add_argument("--only", nargs="+", help="structure ids")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    rows = readings(limit=set(args.only) if args.only else None)
    short = [r for r in rows if r["clear"] is None or r["clear"] < FLOOR_M - 1e-6]

    if args.json:
        print(json.dumps({"floor_m": FLOOR_M, "stacks": rows}, indent=1))
    elif args.walls:
        import collections
        by = collections.Counter((r["archetype"], r["wall"]) for r in rows)
        print(f"{'archetype':<18} {'wall':<10} {'stacks':>6}   clearance above its own roof")
        for (arch, wall) in sorted(by):
            cl = [r["clear"] for r in rows
                  if r["archetype"] == arch and r["wall"] == wall and r["clear"] is not None]
            span = f"{min(cl):.3f} – {max(cl):.3f} m" if cl else "—"
            print(f"{arch:<18} {wall:<10} {by[(arch, wall)]:>6}   {span}")
        print()
    else:
        shown = short if args.short else rows
        width = max((len(r["id"]) for r in shown), default=10)
        print(f"{'structure':<{width}}  {'archetype':<16} {'#':>2}  {'top':>7}  "
              f"{'roof':>7}  {'clear':>7}  {'in':>6}  how")
        for r in shown:
            clear = "  none " if r["clear"] is None else f"{r['clear']:7.3f}"
            inches = "     ?" if r["clear"] is None else f"{r['clear'] / 0.0254:6.1f}"
            roof = "  none " if r["roof"] is None else f"{r['roof']:7.3f}"
            flag = "" if (r["clear"] or 0) >= FLOOR_M - 1e-6 else "   <- UNDER THE ORDINANCE"
            print(f"{r['id']:<{width}}  {r['archetype']:<16} {r['stack']:>2}  "
                  f"{r['top']:7.3f}  {roof}  {clear}  {inches}  {r['how']}{flag}")
        print()

    ok = [r for r in rows if r["clear"] is not None]
    if not args.walls and ok:
        lo = min(ok, key=lambda r: r["clear"])
        hi = max(ok, key=lambda r: r["clear"])
        sky = [r for r in ok if r["over_ridge"] is not None]
        over = [r for r in sky if r["over_ridge"] > ANDREAS_CEILING_M]
        print(f"{len(rows)} stacks on "
              f"{len({(r['id'], r['phase']) for r in rows})} buildings.")
        print(f"  lowest   {lo['clear']:.3f} m ({lo['clear'] / 0.0254:.1f} in)  {lo['id']}")
        print(f"  highest  {hi['clear']:.3f} m ({hi['clear'] / 0.0254:.1f} in)  {hi['id']}")
        print(f"  the ordinance's floor is {FLOOR_M:.4f} m (18 in); "
              f"{len(short)} stack(s) stand under it")
        tallest = max(sky, key=lambda r: r["over_ridge"], default=None)
        print(f"  Andreas's retrospective ceiling is {ANDREAS_CEILING_M:.4f} m (4 ft) "
              f"over the building's OWN highest roof; {len(over)} stand over it — "
              f"reported, not gated")
        if tallest is not None:
            print(f"    tallest against the sky: {tallest['over_ridge']:.3f} m "
                  f"({tallest['over_ridge'] / 0.0254:.1f} in)  {tallest['id']}")

    if short:
        names = ", ".join(sorted({r["id"] for r in short}))
        print(f"FAIL: {len(short)} stack(s) stand less than eighteen inches above the "
              f"roof they pass through, against the Trustees' ordinance of 5 August "
              f"1835 section 18 (chicago_democrat_1835_08_19 c005), T-0333: {names}")
        return 1
    print(f"OK: all {len(rows)} stacks carry at least eighteen inches above their own "
          f"roof, as the ordinance of 5 August 1835 requires.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
