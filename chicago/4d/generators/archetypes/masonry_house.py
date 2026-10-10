"""masonry_house — a load-bearing masonry house built as a composition of parts.

The parameter module (`masonry_house_params.py`) has already turned the record's form
attributes into metric parts — gabled ranges, round towers, a bow, bays, dormers, a
ridge turret, stacks, openings, bands, a gate and the courtyard ground — each carrying
the _CONFIDENCE float of the attributes behind it. This module draws them and decides
nothing about the building's form: every dimension it uses arrives in `params`.

What it DOES decide is how a part is drawn, and those choices are stated here because
they are the only thing in the mesh a record does not own:

* **Meeting ranges interpenetrate.** Where the Glessner House's north range meets the
  east wing and the stable, its roof is carried a few metres into the neighbour's
  (`roof_extend`), below the neighbour's slopes, so the valley a visitor sees is the
  real intersection of two planes rather than a seam this module had to compute.
  Walls that fall inside another mass are skipped by span (`wall_skip`).
* **Roofs are two-sided**, so an eave seen from below is not a hole in the sky.
* **Openings are surfaces, not holes** — a dark panel a few centimetres proud of the
  wall, the rule every archetype in this project follows. Voussoirs are wedges with a
  joint left between them, which is what makes a fan read at a distance.
* **Parapet gables** carry their wall a stated height above the roof with a stone
  coping along the top, which is what an 1880s masonry gable does; the height is the
  record's (`range_ends.parapet_ft`).

All colours arrive in params as LINEAR rgba from the record's tint attributes, except
glass, which is the town's sheet row (`common.materials.GLASS`).
"""

from __future__ import annotations

import math

from archetypes.masonry_house_params import MasonryHouseParams
from common import materials
from common.mesh import MeshBuilder, simple_material

# Material slots, in the order the builder indexes them.
GRANITE, BRICK, TRIM, ROOF, COPPER, GLASS, WOOD, LAWN, DRIVE = range(9)

WALL_MAT = {"granite": GRANITE, "brick": BRICK, "trim": TRIM, "wood": WOOD}
COLOUR_MAT = {"granite": GRANITE, "brick": BRICK, "trim": TRIM, "roof": ROOF,
              "copper": COPPER, "wood": WOOD}

# The drawing choices named in the module docstring, in metres.
EAVE_OVERHANG = 0.20        # a masonry eave: a moulded cornice, not a frame overhang
ROOF_THICK = 0.06           # the gap between a roof's upper and lower skins
PANEL_PROUD = 0.03          # openings stand this far off the wall plane
RING_PROUD = 0.05           # voussoir rings and tympana
WALL_T = 0.45               # a parapet's thickness, for its coping and inner face
COPING_H = 0.18             # the coping's own depth
JOINT = 0.035               # the joint left between voussoir wedges, metres of arc


# ------------------------------------------------------------------ primitives


def _normal(pts):
    """Newell's method — the face normal of a planar polygon, by its vertex order."""
    nx = ny = nz = 0.0
    n = len(pts)
    for i in range(n):
        x0, y0, z0 = pts[i]
        x1, y1, z1 = pts[(i + 1) % n]
        nx += (y0 - y1) * (z0 + z1)
        ny += (z0 - z1) * (x0 + x1)
        nz += (x0 - x1) * (y0 + y1)
    return nx, ny, nz


def _poly_facing(b: MeshBuilder, pts, conf, mat, want) -> None:
    """Add a polygon whose normal points along `want` (a 3-vector); reversed if not."""
    n = _normal(pts)
    if n[0] * want[0] + n[1] * want[1] + n[2] * want[2] < 0:
        pts = list(reversed(pts))
    b.add_poly(pts, conf, mat)


def _up(b, pts, conf, mat) -> None:
    _poly_facing(b, pts, conf, mat, (0.0, 0.0, 1.0))


def _two_sided_roof(b, pts, conf, mat) -> None:
    """A roof plane seen from above AND below, the lower skin dropped ROOF_THICK."""
    _up(b, pts, conf, mat)
    low = [(x, y, z - ROOF_THICK) for x, y, z in pts]
    _poly_facing(b, low, conf, mat, (0.0, 0.0, -1.0))


def _plane_point(pl: dict, u: float, z: float, off: float = 0.0):
    """A point on a wall plane: `u` along it, `z` up, `off` metres outward."""
    at = pl["at"] + pl["sign"] * off
    return (at, u, z) if pl["axis"] == "x" else (u, at, z)


def _plane_dir(pl: dict):
    return (pl["sign"], 0.0, 0.0) if pl["axis"] == "x" else (0.0, pl["sign"], 0.0)


def _panel(b, pl, u0, u1, z0, z1, conf, mat, off=PANEL_PROUD) -> None:
    pts = [_plane_point(pl, u0, z0, off), _plane_point(pl, u1, z0, off),
           _plane_point(pl, u1, z1, off), _plane_point(pl, u0, z1, off)]
    _poly_facing(b, pts, conf, mat, _plane_dir(pl))


def _profile_wall(b, pl, prof, spans, conf, mat) -> None:
    """A wall on plane `pl` whose top follows `prof` — a list of (u, z) breakpoints,
    u increasing — drawn only over the kept `spans` [(u0, u1), ...]."""
    def h(u):
        for (ua, za), (ub, zb) in zip(prof, prof[1:]):
            if ua - 1e-9 <= u <= ub + 1e-9:
                t = 0.0 if ub == ua else (u - ua) / (ub - ua)
                return za + t * (zb - za)
        return prof[0][1] if u < prof[0][0] else prof[-1][1]

    for a, c in spans:
        if c - a < 1e-4:
            continue
        top = [(a, h(a))] + [(u, z) for u, z in prof if a < u < c] + [(c, h(c))]
        pts = [_plane_point(pl, a, 0.0), _plane_point(pl, c, 0.0)]
        pts += [_plane_point(pl, u, z) for u, z in reversed(top)]
        # bottom edge left->right, then the top right->left: one simple polygon
        _poly_facing(b, pts, conf, mat, _plane_dir(pl))


def _kept(u0, u1, skips):
    spans = [(u0, u1)]
    for s0, s1 in skips:
        nxt = []
        for a, c in spans:
            if s1 <= a or s0 >= c:
                nxt.append((a, c))
                continue
            if s0 > a:
                nxt.append((a, s0))
            if s1 < c:
                nxt.append((s1, c))
        spans = nxt
    return spans


def _box(b, x0, y0, z0, x1, y1, z1, conf, mat, bottom=False) -> None:
    skip = () if bottom else ("bottom",)
    b.add_box(min(x0, x1), min(y0, y1), z0, max(x0, x1), max(y0, y1), z1, conf, mat,
              skip=skip)


def _cone(b, cx, cy, r, z_base, z_apex, conf, mat, seg=16, a0=0.0, a1=2 * math.pi,
          soffit=None) -> None:
    """A cone (or a sector of one) from a ring at z_base to an apex over its centre."""
    if getattr(b,'reduced_roof_details',False) and b.params.detail.get('roof_edges'):
        # Same analytic cone, coarser angular sampling in Light only. The largest
        # 2.5451m radius departs from its circle by at most 12.3mm at 32 facets.
        seg=min(seg,32)
    full = abs((a1 - a0) - 2 * math.pi) < 1e-6
    n = seg if full else max(3, int(seg * abs(a1 - a0) / (2 * math.pi)) + 1)
    angs = [a0 + (a1 - a0) * i / n for i in range(n + (0 if full else 1))]
    ring = [(cx + r * math.cos(a), cy + r * math.sin(a), z_base) for a in angs]
    pairs = list(zip(ring, ring[1:] + ([ring[0]] if full else [])))
    for p, q in pairs:
        _up(b, [p, q, (cx, cy, z_apex)], conf, mat)
    if soffit is not None:
        # the underside of the overhang, down to the drum it overhangs
        rin = soffit
        for (p, q), a, c in zip(pairs, angs, angs[1:] + ([angs[0]] if full else [])):
            pi_ = (cx + rin * math.cos(a), cy + rin * math.sin(a), z_base)
            qi = (cx + rin * math.cos(c), cy + rin * math.sin(c), z_base)
            _poly_facing(b, [p, q, qi, pi_], conf, mat, (0.0, 0.0, -1.0))


def _drum(b, cx, cy, r, z0, z1, conf, mat, seg=16, a0=0.0, a1=2 * math.pi) -> list:
    """A cylinder wall (or an arc of one), outward. Returns the facet list
    [(angle0, angle1)] so openings can be hung on it."""
    full = abs((a1 - a0) - 2 * math.pi) < 1e-6
    n = seg if full else max(2, int(seg * abs(a1 - a0) / (2 * math.pi)) + 1)
    angs = [a0 + (a1 - a0) * i / n for i in range(n + 1)]
    facets = []
    for a, c in zip(angs, angs[1:]):
        p = (cx + r * math.cos(a), cy + r * math.sin(a))
        q = (cx + r * math.cos(c), cy + r * math.sin(c))
        m = ((a + c) / 2.0)
        _poly_facing(b, [(p[0], p[1], z0), (q[0], q[1], z0), (q[0], q[1], z1),
                         (p[0], p[1], z1)], conf, mat, (math.cos(m), math.sin(m), 0.0))
        facets.append((a, c))
    return facets


def _finial(b, x, y, z, h, conf, mat) -> None:
    if getattr(b,"params",None) and b.params.detail.get("roof_edges"):
        from archetypes.masonry_house_v4_roof_edges import finial
        return finial(b,x,y,z,h,mat)
    if h <= 0:
        return
    s = 0.06
    _box(b, x - s, y - s, z - 0.05, x + s, y + s, z + h * 0.55, conf, mat)
    _cone(b, x, y, s * 2.2, z + h * 0.55, z + h, conf, mat, seg=6)


# ------------------------------------------------------------------- the parts


def _range(b, r) -> None:
    """One gabled range: its walls, its roof, its gable ends."""
    if r.get("stable_roof"):
        return _stable_reworked(b, r)
    ax = r["axis"]                          # ridge runs along this metric axis
    x0, x1, y0, y1 = r["x0"], r["x1"], r["y0"], r["y1"]
    rz, elo, ehi, ra = r["ridge_z"], r["eave_lo_z"], r["eave_hi_z"], r["ridge_at"]
    # across-ridge coordinate range, and along-ridge range
    c0, c1 = (x0, x1) if ax == "y" else (y0, y1)
    l0, l1 = (y0, y1) if ax == "y" else (x0, x1)

    def roof_z(c):
        """Height of the roof surface at across-ridge coordinate c (no overhang)."""
        if c <= ra:
            base, zb, span = c0, elo, ra - c0
            kick = r["kick"] if r["kick"] and r["kick"]["side"] in ("south", "west") \
                else None
        else:
            base, zb, span = c1, ehi, c1 - ra
            kick = r["kick"] if r["kick"] and r["kick"]["side"] in ("north", "east") \
                else None
        d = abs(c - base)
        if kick:
            run = kick["run_m"]
            zk = zb + run * math.tan(math.radians(kick["pitch_deg"]))
            if d <= run:
                return zb + d * math.tan(math.radians(kick["pitch_deg"]))
            return zk + (d - run) * (rz - zk) / max(span - run, 1e-6)
        return zb + d * (rz - zb) / max(span, 1e-6)

    # the across-ridge profile's breakpoints, eave to eave
    prof_c = [c0]
    if r["kick"]:
        side = r["kick"]["side"]
        run = r["kick"]["run_m"]
        if side in ("south", "west"):
            prof_c.append(c0 + run)
        prof_c.append(ra)
        if side in ("north", "east"):
            prof_c.append(c1 - run)
    else:
        prof_c.append(ra)
    prof_c.append(c1)
    prof = [(c, roof_z(c)) for c in prof_c]

    # ---- walls
    faces = {
        "east": ({"axis": "x", "sign": 1, "at": x1}, (y0, y1)),
        "west": ({"axis": "x", "sign": -1, "at": x0}, (y0, y1)),
        "north": ({"axis": "y", "sign": 1, "at": y1}, (x0, x1)),
        "south": ({"axis": "y", "sign": -1, "at": y0}, (x0, x1)),
    }
    for face, (pl, (u0, u1)) in faces.items():
        kind = r["walls"][face]
        if kind == "none":
            continue
        mat = WALL_MAT[kind]
        spans = _kept(u0, u1, r["wall_skip"].get(face, []))
        is_gable = (ax == "y" and face in ("north", "south")) or \
                   (ax == "x" and face in ("east", "west"))
        if is_gable:
            end = r["gable_ends"].get(face, "none")
            if end == "none":
                continue
            lift = r["parapet_m"].get(face, 0.0) if end == "parapet" else 0.0
            end_prof = prof
            cross_gable = r.get("north_cross_gable") if face == "north" else None
            if cross_gable:
                g = cross_gable
                end_prof = [(g["x0"], g["eave_z"]), (ra, rz),
                            (g["x1"], g["eave_z"])]
                # Only the projecting triangle has coping. The wall beside it
                # returns to the ordinary north-range eave, not a raised parapet.
                gprof = [(c0, g["eave_z"]), (g["x0"], g["eave_z"] + lift),
                         (ra, rz + lift), (g["x1"], g["eave_z"] + lift),
                         (c1, g["eave_z"])]
                gprof = sorted(set(gprof))
            else:
                gprof = [(c, z + lift) for c, z in prof]
            _profile_wall(b, pl, gprof, spans, r["conf_ends"][face], mat)
            if end == "parapet":
                _parapet(b, pl, end_prof, lift, r["conf_ends"][face], mat)
        else:
            z = roof_z(c1) if (face in ("east", "north")) else roof_z(c0)
            wall_prof = [(u0, z), (u1, z)]
            if (r['name']=='north_range' and face=='south' and
                    getattr(b,'params',None) and b.params.detail.get('dining_roof_junction')):
                from archetypes.masonry_house_v4_courtyard_roof import wall_profile
                wall_prof=wall_profile(b.params,u0,u1,z)
            if face == "west" and r.get("north_cross_gable"):
                g = r["north_cross_gable"]
                wall_prof = [(u0, z), (g["cross_y0"], z),
                    (g["cross_y0"], g["cross_eave_lo_z"]),
                    (g["cross_ridge_at"], g["cross_ridge_z"]),
                    (u1, g["cross_eave_hi_z"])]
            _profile_wall(b, pl, wall_prof, spans, r["conf_plan"], mat)

    # ---- roof, carried EAVE_OVERHANG past the eave walls and past any end that is
    # not a parapet, and to `roof_extend` where the range runs into a neighbour
    ends = r["gable_ends"]
    lo_face, hi_face = ("south", "north") if ax == "y" else ("west", "east")
    a0 = l0 - (0.0 if ends.get(lo_face) == "parapet" else EAVE_OVERHANG)
    a1 = l1 + (0.0 if ends.get(hi_face) == "parapet" else EAVE_OVERHANG)
    ext = r["roof_extend"]
    for side, coord in ext.items():
        if side in ("south", "west"):
            a0 = min(a0, coord)
        else:
            a1 = max(a1, coord)
    if "roof_min" in r:
        a0 = max(a0, r["roof_min"])
    if r.get("north_cross_gable"):
        _crossed_stable_roof(b, r, roof_z)
        return
    ov_prof = list(prof)
    # overhang: continue each outer slope EAVE_OVERHANG beyond its wall
    (ca, za), (cb, zb_) = prof[0], prof[1]
    slope_lo = (zb_ - za) / max(cb - ca, 1e-6)
    (cy_, zy), (cz, zz) = prof[-2], prof[-1]
    slope_hi = (zz - zy) / max(cz - cy_, 1e-6)
    low_overhang = r.get("eave_lo_overhang", EAVE_OVERHANG)
    ov_prof[0] = (c0 - low_overhang, za - low_overhang * slope_lo)
    ov_prof[-1] = (c1 + EAVE_OVERHANG, zz + EAVE_OVERHANG * slope_hi)

    def P(c, l, z):
        return (c, l, z) if ax == "y" else (l, c, z)

    for (ca, za), (cb, zb2) in zip(ov_prof, ov_prof[1:]):
        pts=[P(ca, a0, za), P(cb, a0, zb2), P(cb, a1, zb2), P(ca, a1, za)]
        fragments=[pts]
        if r['name']=='north_range' and getattr(b,'params',None) and b.params.detail.get('dining_roof_junction'):
            from archetypes.masonry_house_v4_courtyard_roof import clip_host
            fragments=clip_host(pts,b.params)
        for fragment in fragments:
            _two_sided_roof(b,fragment,r['conf_roof'],ROOF)
    if getattr(b,"params",None) and b.params.detail.get("roof_edges"):
        return  # Closed caps own this ridge; do not tile a hidden duplicate roll.
    # the crested ridge: a low ridge roll the length of the roof
    cr = 0.12
    _up(b, [P(ra - cr, a0, rz + 0.02), P(ra, a0, rz + cr * 1.4),
            P(ra, a1, rz + cr * 1.4), P(ra - cr, a1, rz + 0.02)], r["conf_roof"], ROOF)
    _up(b, [P(ra, a0, rz + cr * 1.4), P(ra + cr, a0, rz + 0.02),
            P(ra + cr, a1, rz + 0.02), P(ra, a1, rz + cr * 1.4)], r["conf_roof"], ROOF)


def _stable_reworked(b, r):
    from archetypes.masonry_house_v4_west_roof import patches, profile, height
    g = r["stable_roof"]
    for face in ("north", "west", "east", "south"):
        kind = r["walls"][face]
        if kind == "none": continue
        axis = "x" if face in ("west", "east") else "y"
        sign = -1 if face in ("west", "south") else 1
        at = r["x0"] if face == "west" else r["x1"] if face == "east" else r["y0"] if face == "south" else r["y1"]
        pl = {"axis": axis, "sign": sign, "at": at}
        prof = profile(r, face)
        if face == "north":
            # The masonry gable has coping only on its two slopes. No raised
            # diagonal runs from its foot to the ordinary alley eave.
            lift = r["parapet_m"].get("north", 0)
            west_eave = g.get('north_west_eave', g['north_eave'])
            east_eave = height(r,g['front_x1'],r['y1']) if g.get('level_courtyard_gable') else g['north_eave']
            gp = [(g["front_x0"],west_eave),(r["ridge_at"],r["ridge_z"]),(g["front_x1"],east_eave)]
            prof = [(r["x0"],west_eave),(g["front_x0"],west_eave),
                (g["front_x0"],west_eave+lift),(r["ridge_at"],r["ridge_z"]+lift),
                (g["front_x1"],east_eave+lift),(g["front_x1"],east_eave)]
            _parapet(b,pl,gp,lift,r["conf_ends"][face],WALL_MAT[kind])
        spans=_kept(prof[0][0],prof[-1][0],r["wall_skip"].get(face,[]))
        _profile_wall(b,pl,prof,spans,r["conf_plan"],WALL_MAT[kind])
    for _,pts in patches(r):
        _two_sided_roof(b,pts,r["conf_roof"],ROOF)
    # A short ordinary eave beyond the north wall at the alley return only.
    a,c=r["x0"]-.15,g["front_x0"]
    if c>a:
        ze=g.get('north_west_eave', g['north_eave']);y=r["y1"]
        _two_sided_roof(b,[(a,y,ze),(c,y,ze),(c,y+.15,ze-.1),(a,y+.15,ze-.1)],r["conf_roof"],ROOF)


def _crossed_stable_roof(b, r, original_z):
    """One continuous envelope at the stable/north-range crossing (T-1805).

    The photographed street gable is narrower than the wing. Its exact hidden
    tie-in is unsurveyed: interpolate to the retained rear roof within the
    crossing range. The crossing roof wins wherever it is higher. This removes
    buried duplicate skins, their visible front-edge stripe and coplanar flicker.
    """
    g = r["north_cross_gable"]
    x0, x1, ra = r["x0"], r["x1"], r["ridge_at"]
    y0, y1 = r["y0"] - EAVE_OVERHANG, r["y1"]
    def north_z(y):
        ridge = g["cross_ridge_at"]
        if y >= ridge:
            return g["cross_eave_hi_z"] + (g["cross_y1"]-y) * (
                g["cross_ridge_z"]-g["cross_eave_hi_z"])/(g["cross_y1"]-ridge)
        base, ze = g["cross_y0"], g["cross_eave_lo_z"]
        kick = g["cross_kick"]
        run = kick["run_m"] if kick else 0
        zk = ze + run * math.tan(math.radians(kick["pitch_deg"])) if kick else ze
        return ze+(y-base)*(zk-ze)/run if run and y < base+run else (
            zk+(y-base-run)*(g["cross_ridge_z"]-zk)/(ridge-base-run))
    def height(x, y):
        old = original_z(min(x1, max(x0, x)))
        if y < g["cross_y0"]:
            # Continue the original slope to its eave overhang.
            edge = x0 if x < x0 else x1
            if x < x0 or x > x1:
                old += (x-edge)*(original_z(edge)-original_z(ra))/(edge-ra)
            return old
        foot = g["x0"] if x <= ra else g["x1"]
        front = g["eave_z"]+(x-foot)*(r["ridge_z"]-g["eave_z"])/(ra-foot)
        t = min(1., max(0., (y1-y)/(y1-g["cross_ridge_at"])))
        stable = front+(old-front)*t
        return max(north_z(y), stable)
    def subdivide(values, step=1.8):
        values=sorted(set(values)); result=[]
        for a,c in zip(values,values[1:]):
            n=max(1,math.ceil((c-a)/step))
            result.extend(a+(c-a)*i/n for i in range(n))
        return result+[values[-1]]
    xs=subdivide([x0-EAVE_OVERHANG,x0,g["x0"],ra,g["x1"],x1])
    ys=subdivide([y0,r["y0"],g["cross_y0"],g["cross_ridge_at"],y1])
    for a,c in zip(xs,xs[1:]):
        for lo,hi in zip(ys,ys[1:]):
            pts=[(a,lo,height(a,lo)),(c,lo,height(c,lo)),
                 (c,hi,height(c,hi)),(a,hi,height(a,hi))]
            # Explicit triangles also make the gently varying hidden tie-in
            # unambiguous to both Blender and the engine-neutral light writer.
            for indices in ((0,1,2),(0,2,3)):
                _two_sided_roof(b,[pts[i] for i in indices],r["conf_roof"],ROOF)
    # Carry only the exposed return past the street wall. There is NO roof edge
    # across the gable face, loft door or narrow flanking windows.
    for a,c in ((x0-EAVE_OVERHANG,g["x0"]),(g["x1"],x1)):
        if c-a > 1e-6:
            _two_sided_roof(b,[(a,y1,north_z(y1)),(c,y1,north_z(y1)),
                (c,y1+EAVE_OVERHANG,north_z(y1+EAVE_OVERHANG)),
                (a,y1+EAVE_OVERHANG,north_z(y1+EAVE_OVERHANG))],r["conf_roof"],ROOF)


def _parapet(b, pl, prof, lift, conf, mat) -> None:
    """The coping and the inner face of a parapet gable standing `lift` above its roof,
    in the gable wall's own stone: a street gable's coping is granite, not the
    courtyard's limestone trim."""
    inward = -pl["sign"]
    for (ua, za), (ub, zb) in zip(prof, prof[1:]):
        ta, tb = za + lift, zb + lift
        # coping: a slab over the wall top, WALL_T deep, projecting a little outward
        p_out = [_plane_point(pl, ua, ta + COPING_H, 0.08),
                 _plane_point(pl, ub, tb + COPING_H, 0.08)]
        p_in = [_plane_point(pl, ub, tb + COPING_H, -WALL_T),
                _plane_point(pl, ua, ta + COPING_H, -WALL_T)]
        _up(b, p_out + p_in, conf, mat)
        # its outer lip
        _poly_facing(b, [_plane_point(pl, ua, ta, 0.08), _plane_point(pl, ub, tb, 0.08),
                         _plane_point(pl, ub, tb + COPING_H, 0.08),
                         _plane_point(pl, ua, ta + COPING_H, 0.08)], conf, mat,
                     _plane_dir(pl))
        # the inner face above the roof, seen from the roof side
        inner = [_plane_point(pl, ua, za, -WALL_T), _plane_point(pl, ub, zb, -WALL_T),
                 _plane_point(pl, ub, tb + COPING_H, -WALL_T),
                 _plane_point(pl, ua, ta + COPING_H, -WALL_T)]
        want = (inward, 0.0, 0.0) if pl["axis"] == "x" else (0.0, inward, 0.0)
        _poly_facing(b, inner, conf, mat, want)


def _tower(b, t) -> None:
    mat = WALL_MAT.get(t["wall"], BRICK)
    seg = t["segments"]
    _drum(b, t["cx"], t["cy"], t["r"], t["z0"], t["wall_top_z"], t["conf_wall"], mat, seg)
    # a stone band at the wall top, where the cone's eave sits
    _drum(b, t["cx"], t["cy"], t["r"] + 0.04, t["wall_top_z"] - 0.35, t["wall_top_z"],
          t["conf_wall"], TRIM, seg)
    _cone(b, t["cx"], t["cy"], t["eave_r"], t["wall_top_z"], t["apex_z"], t["conf_roof"],
          ROOF, seg, soffit=t["r"])
    _finial(b, t["cx"], t["cy"], t["apex_z"], t["finial_m"], t["conf_roof"], COPPER)


def _bow(b, w) -> None:
    a0, a1 = w["a0"], w["a1"]
    if a1 < a0:
        a0, a1 = a1, a0
    if a1 - a0 > math.pi:            # take the short way round, into the courtyard
        a0, a1 = a1, a0 + 2 * math.pi
    _drum(b, w["cx"], w["cy"], w["r"], 0.0, w["wall_top_z"], w["conf_wall"], BRICK,
          seg=20, a0=a0, a1=a1)
    mat = COLOUR_MAT.get(w["roof_colour"], COPPER)
    _cone(b, w["cx"], w["cy"], w["r"] + EAVE_OVERHANG, w["wall_top_z"],
          w["wall_top_z"] + w["roof_rise_m"], w["conf_roof"], mat, seg=20, a0=a0, a1=a1,
          soffit=w["r"])
    # openings on the bow: the record's rows of lights, spread evenly round the arc
    rows = w["light_rows"]
    n = w["lights_per_row"]
    for i in range(n):
        a = a0 + (a1 - a0) * (i + 0.5) / n
        half = (a1 - a0) / n * 0.28
        for z0, z1 in rows:
            pts = []
            for aa in (a - half, a + half):
                pts.append((w["cx"] + (w["r"] + PANEL_PROUD) * math.cos(aa),
                            w["cy"] + (w["r"] + PANEL_PROUD) * math.sin(aa)))
            quad = [(pts[0][0], pts[0][1], z0), (pts[1][0], pts[1][1], z0),
                    (pts[1][0], pts[1][1], z1), (pts[0][0], pts[0][1], z1)]
            _poly_facing(b, quad, w["conf_wall"], GLASS, (math.cos(a), math.sin(a), 0.0))


def _bay(b, y) -> None:
    pts = y["pts"]
    # the bay's inside is the wall it stands on: the midpoint of its first and last
    # points, pushed back into the house
    mx = (pts[0][0] + pts[-1][0]) / 2.0
    my = (pts[0][1] + pts[-1][1]) / 2.0
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    ix, iy = mx + (mx - cx), my + (my - cy)
    zt, zb = y["wall_top_z"], y["band_top_z"]
    for p, q in zip(pts, pts[1:]):
        mxp, myp = (p[0] + q[0]) / 2.0, (p[1] + q[1]) / 2.0
        want = (mxp - ix, myp - iy, 0.0)
        _poly_facing(b, [(p[0], p[1], 0.0), (q[0], q[1], 0.0), (q[0], q[1], zt),
                         (p[0], p[1], zt)], y["conf_wall"], BRICK, want)
        if zb > zt:
            _poly_facing(b, [(p[0], p[1], zt), (q[0], q[1], zt), (q[0], q[1], zb),
                             (p[0], p[1], zb)], y["conf_wall"], GLASS, want)
        # first-floor window on each facet long enough to carry one
        flen = math.hypot(q[0] - p[0], q[1] - p[1])
        if flen > 1.2 and y["light_row"]:
            nx, ny = want[0], want[1]
            nl = math.hypot(nx, ny) or 1.0
            ox, oy = nx / nl * PANEL_PROUD, ny / nl * PANEL_PROUD
            t0, t1 = 0.2, 0.8
            a = (p[0] + (q[0] - p[0]) * t0 + ox, p[1] + (q[1] - p[1]) * t0 + oy)
            c = (p[0] + (q[0] - p[0]) * t1 + ox, p[1] + (q[1] - p[1]) * t1 + oy)
            lz0, lz1 = y["light_row"]
            _poly_facing(b, [(a[0], a[1], lz0), (c[0], c[1], lz0), (c[0], c[1], lz1),
                             (a[0], a[1], lz1)], y["conf_wall"], GLASS, want)
    # the ledge between the storey and the glazed band
    ap = y["apex"]
    for p, q in zip(pts, pts[1:]):
        _up(b, [(p[0], p[1], zb), (q[0], q[1], zb), (ap[0], ap[1], ap[2])],
            y["conf_roof"], COPPER)


def _dormer(b, d) -> None:
    f, bk = d["front"], d["back"]
    u0, u1 = sorted((d["u0"], d["u1"]))
    z0, ze, za = d["z0"], d["eave_z"], d["apex_z"]
    out = -1.0 if bk > f else 1.0               # which way the front looks, in x
    # front wall and cheeks
    _poly_facing(b, [(f, u0, z0), (f, u1, z0), (f, u1, ze), (f, u0, ze)], d["conf"], TRIM,
                 (out, 0.0, 0.0))
    for u, s in ((u0, -1.0), (u1, 1.0)):
        _poly_facing(b, [(f, u, z0), (bk, u, z0), (bk, u, ze), (f, u, ze)], d["conf"],
                     ROOF, (0.0, s, 0.0))
    lz0, lz1 = d["light"]
    m = (u1 - u0) * 0.22
    _poly_facing(b, [(f + out * PANEL_PROUD, u0 + m, lz0), (f + out * PANEL_PROUD, u1 - m, lz0),
                     (f + out * PANEL_PROUD, u1 - m, lz1), (f + out * PANEL_PROUD, u0 + m, lz1)],
                 d["conf"], GLASS, (out, 0.0, 0.0))
    # pyramid roof over the square, with a finial
    ov = 0.12
    xa, xb = sorted((f, bk))
    xa, xb = (xa - ov, xb) if out < 0 else (xa, xb + ov)
    ua, ub = u0 - ov, u1 + ov
    cx, cu = (f + bk) / 2.0, (u0 + u1) / 2.0
    ring = [(xa, ua, ze), (xb, ua, ze), (xb, ub, ze), (xa, ub, ze)]
    for p, q in zip(ring, ring[1:] + ring[:1]):
        _up(b, [p, q, (cx, cu, za)], d["conf"], ROOF)
    _finial(b, cx, cu, za, 0.35, d["conf"], COPPER)


def _turret(b, t) -> None:
    x0, x1 = sorted((t["x0"], t["x1"]))
    y0, y1 = sorted((t["y0"], t["y1"]))
    _box(b, x0, y0, t["z0"], x1, y1, t["top_z"], t["conf"], WOOD)
    lz0, lz1 = t["louvre"]
    inset = 0.12
    for pl, (u0, u1) in (({"axis": "x", "sign": 1, "at": x1}, (y0, y1)),
                         ({"axis": "x", "sign": -1, "at": x0}, (y0, y1)),
                         ({"axis": "y", "sign": 1, "at": y1}, (x0, x1)),
                         ({"axis": "y", "sign": -1, "at": y0}, (x0, x1))):
        _panel(b, pl, u0 + inset, u1 - inset, lz0, lz1, t["conf"], GLASS)
    ov = 0.18
    ring = [(x0 - ov, y0 - ov, t["top_z"]), (x1 + ov, y0 - ov, t["top_z"]),
            (x1 + ov, y1 + ov, t["top_z"]), (x0 - ov, y1 + ov, t["top_z"])]
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    for p, q in zip(ring, ring[1:] + ring[:1]):
        _up(b, [p, q, (cx, cy, t["apex_z"])], t["conf"], ROOF)
    _poly_facing(b, ring, t["conf"], ROOF, (0.0, 0.0, -1.0))
    _finial(b, cx, cy, t["apex_z"], t["finial_m"], t["conf"], COPPER)


def _chimney(b, c) -> None:
    _box(b, c["x0"], c["y0"], c["z0"], c["x1"], c["y1"], c["z1"] - 0.2, c["conf"], GRANITE)
    s = 0.08
    _box(b, c["x0"] - s, c["y0"] - s, c["z1"] - 0.2, c["x1"] + s, c["y1"] + s, c["z1"],
         c["conf"], TRIM, bottom=True)


def _arch_top(b, pl, uc, zs, r, conf, mat, off, seg=10) -> None:
    """The half-disc of an arched opening above its springing line."""
    pts = [_plane_point(pl, uc + r * math.cos(math.pi * i / seg), zs +
                        r * math.sin(math.pi * i / seg), off) for i in range(seg + 1)]
    _poly_facing(b, pts, conf, mat, _plane_dir(pl))


def _voussoirs(b, pl, uc, zs, r_in, r_out, n, conf, mat, off) -> None:
    """A ring of n wedges from r_in to r_out, with a joint between each."""
    if n <= 0 or r_out <= r_in:
        return
    for i in range(n):
        g = JOINT / max(r_out, 1e-6)
        a = math.pi * i / n + g / 2.0
        c = math.pi * (i + 1) / n - g / 2.0
        pts = [_plane_point(pl, uc + r_in * math.cos(a), zs + r_in * math.sin(a), off),
               _plane_point(pl, uc + r_out * math.cos(a), zs + r_out * math.sin(a), off),
               _plane_point(pl, uc + r_out * math.cos(c), zs + r_out * math.sin(c), off),
               _plane_point(pl, uc + r_in * math.cos(c), zs + r_in * math.sin(c), off)]
        _poly_facing(b, pts, conf, mat, _plane_dir(pl))


def _opening(b, o) -> None:
    kind = o["kind"]
    u0, u1, z0, z1, conf = o["u0"], o["u1"], o["z0"], o["z1"], o["conf"]
    if kind == "window" or kind == "dark":
        _panel(b, o, u0, u1, z0, z1, conf, GLASS)
    elif kind in ("door", "doors"):
        _panel(b, o, u0, u1, z0, z1, conf, WOOD)
        if kind == "doors":
            uc = (u0 + u1) / 2.0
            _panel(b, o, uc - 0.02, uc + 0.02, z0, z1, conf, GLASS, off=PANEL_PROUD + 0.01)
    elif kind == "band":
        _panel(b, o, u0, u1, z0, z1, conf, TRIM, off=0.06)
    elif kind == "arch":
        uc, r = (u0 + u1) / 2.0, (u1 - u0) / 2.0
        zs = o["spring_z"]
        _panel(b, o, u0, u1, z0, zs, conf, GLASS)
        _arch_top(b, o, uc, zs, r, conf, GLASS, PANEL_PROUD)
        if o.get("r_out", 0) > r:
            _voussoirs(b, o, uc, zs, r, o["r_out"], o["voussoirs"] or 15, conf, TRIM,
                       RING_PROUD)
    elif kind == "fan":
        # the Prairie Avenue door's fan: a carved tympanum inside a ring of voussoirs,
        # standing on the lintel over the door
        uc = (u0 + u1) / 2.0
        zs = o["spring_z"]
        _arch_top(b, o, uc, zs, o["r_in"], conf, TRIM, RING_PROUD + 0.01, seg=12)
        _voussoirs(b, o, uc, zs, o["r_in"] + 0.05, o["r_out"], o["voussoirs"] or 11, conf,
                   TRIM, RING_PROUD)


def _band(b, n) -> None:
    pl = n
    p = n["proj_m"]
    mat = COLOUR_MAT.get(n["colour"], GRANITE)
    u0, u1, z0, z1 = n["u0"], n["u1"], n["z0"], n["z1"]
    _panel(b, pl, u0, u1, z0, z1, n["conf"], mat, off=p)
    top = [_plane_point(pl, u0, z1, 0.0), _plane_point(pl, u1, z1, 0.0),
           _plane_point(pl, u1, z1, p), _plane_point(pl, u0, z1, p)]
    _up(b, top, n["conf"], mat)
    bot = [_plane_point(pl, u0, z0, 0.0), _plane_point(pl, u1, z0, 0.0),
           _plane_point(pl, u1, z0, p), _plane_point(pl, u0, z0, p)]
    _poly_facing(b, bot, n["conf"], mat, (0.0, 0.0, -1.0))


def _gate_piece(b, w) -> None:
    t = w["thick_m"]
    kind = w["kind"]
    if kind == "gate":
        t = 0.10
    mat = WOOD if kind == "gate" else GRANITE
    a = w["at"] - t / 2.0
    c = w["at"] + t / 2.0
    if w["axis"] == "x":
        _box(b, a, w["u0"], 0.0, c, w["u1"], w["z1"], w["conf"], mat)
    else:
        _box(b, w["u0"], a, 0.0, w["u1"], c, w["z1"], w["conf"], mat)
    if kind != "gate":
        s = 0.06
        if w["axis"] == "x":
            _box(b, a - s, w["u0"] - s, w["z1"], c + s, w["u1"] + s, w["z1"] + COPING_H,
                 w["conf"], TRIM, bottom=True)
        else:
            _box(b, w["u0"] - s, a - s, w["z1"], w["u1"] + s, c + s, w["z1"] + COPING_H,
                 w["conf"], TRIM, bottom=True)


def _ground(b, g) -> None:
    mat = LAWN if g["kind"] == "lawn" else DRIVE
    pts = [(x, y, g["lift_m"]) for x, y in g["pts"]]
    _up(b, pts, g["conf"], mat)


# ---------------------------------------------------------------------- build


def build(params: MasonryHouseParams, name: str):
    """Build one masonry house. Returns a Blender object at the local origin."""
    params.validate()
    if params.detail_profile == "glessner_v4":
        from archetypes.masonry_house_v4_detail import build as build_detail
        return build_detail(params, name)
    b = MeshBuilder(name)
    for r in params.ranges:
        _range(b, r)
    for t in params.towers:
        _tower(b, t)
    for w in params.bows:
        _bow(b, w)
    for y in params.bays:
        _bay(b, y)
    for d in params.dormers:
        _dormer(b, d)
    for t in params.turrets:
        _turret(b, t)
    for c in params.chimneys:
        _chimney(b, c)
    for o in params.openings:
        _opening(b, o)
    for n in params.bands:
        _band(b, n)
    for w in params.walls:
        _gate_piece(b, w)
    for g in params.ground:
        _ground(b, g)

    col = params.colours
    lawn = next((g["rgba"] for g in params.ground if g["kind"] == "lawn"),
                [0.10, 0.155, 0.045, 1.0])
    drive = next((g["rgba"] for g in params.ground if g["kind"] != "lawn"),
                 [0.30, 0.28, 0.24, 1.0])
    stone = materials.SUBSTRATES["stone"]
    brick = materials.SUBSTRATES["brick"]
    mats = [
        simple_material("granite", tuple(col["granite"]), roughness=stone.roughness),
        simple_material("brick", tuple(col["brick"]), roughness=brick.roughness),
        simple_material("limestone_trim", tuple(col["trim"]), roughness=stone.roughness),
        # The roof's COVERING is terracotta tile, which the town's sheet has no row for,
        # so the slot takes the sheet's own name for a covering it cannot name
        # (`roof_plane`, docs/GLB-CONTRACT.md § Roof coverings) and the tile's colour
        # arrives from the record's `roof_tint`. No relief map binds to it.
        simple_material(materials.roof_material_name(materials.roof_substrate("masonry_house")),
                        tuple(col["roof"]), roughness=0.80),
        simple_material("copper", tuple(col["copper"]), roughness=0.55),
        simple_material("glass", materials.GLASS.rgba, roughness=materials.GLASS.roughness),
        simple_material("oak", tuple(col["wood"]), roughness=0.70),
        simple_material("lawn", tuple(lawn), roughness=0.95),
        simple_material("drive", tuple(drive), roughness=0.92),
    ]
    return b.to_object(mats)
