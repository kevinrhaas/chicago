"""T-2202: record-driven house-side curb, access paving and passage floor.

One construction for full and reduced meshes. Coordinates are metric building
coordinates resolved by masonry_house_params; no street geometry is duplicated.
All reconstructed dimensions, grade clearances and sources live in the record.
"""
from __future__ import annotations

import math

TRIM, LAWN, DRIVE, MORTAR = 2, 7, 8, 9
# opening() already emits the bottom reveal at the door datum, from -0.29 m
# to +0.016 m relative to the facade. Meet that face, never overlay it.
DOOR_REVEAL_FRONT_M = .016


def _slab(b, corners, z, conf, material, bottom=-0.06):
    """Closed solid: its skirts reach below grade instead of floating sheets."""
    top = [(x, y, z) for x, y in corners]
    b.raw(top, conf, material, (0, 0, 1))
    b.raw([(x, y, bottom) for x, y in corners], conf, material, (0, 0, -1))
    for a, c in zip(corners, corners[1:] + corners[:1]):
        # corners are counterclockwise, so the right normal is outward.
        b.raw([(*a, bottom), (*c, bottom), (*c, z), (*a, z)], conf, material,
              (c[1] - a[1], a[0] - c[0], 0))


def _paving(b, p, q, r, s, z_front, z_back, f, material, edges=True):
    """A quad corridor, front p/q to back s/r, with recessed transverse joints."""
    distance = max(math.dist(p, s), math.dist(q, r))
    count = max(1, math.ceil(distance / f['paving_joint_spacing_m']))
    half_gap = min(.02, f['joint_width_m'] / distance / 2)
    def across(t):
        a = tuple(p[i] + (s[i] - p[i]) * t for i in range(2))
        c = tuple(q[i] + (r[i] - q[i]) * t for i in range(2))
        return a, c, z_front + (z_back - z_front) * t
    # Recessed bed covers joints too; terrain can never show between paving units.
    b.raw([(*p, z_front-.003), (*q, z_front-.003), (*r, z_back-.003),
           (*s, z_back-.003)], f['conf'], MORTAR, (0, 0, 1))
    for i in range(count):
        t0 = i / count + (half_gap if i else 0)
        t1 = (i + 1) / count - (half_gap if i < count-1 else 0)
        a, c, z0 = across(t0); d, e, z1 = across(t1)
        b.raw([(*a, z0), (*c, z0), (*e, z1), (*d, z1)], f['conf'], material, (0, 0, 1))
    if not edges: return
    # Skirts close both long edges; open ends meet the next surface exactly.
    mid = ((p[0]+q[0]+r[0]+s[0])/4, (p[1]+q[1]+r[1]+s[1])/4)
    for a, c in ((p, s), (q, r)):
        _edge(b, a, c, z_front, z_back, mid, f['conf'], material)


def _edge(b, a, c, za, zc, mid, conf, material, top=0.0):
    """Close a paving edge a-c (heights za, zc) against the ground at `top`.

    Above the ground the skirt runs down into grade, facing away from `mid`. T-2976:
    where the paving is sunk below the ground (the carriage passage's approach and
    ramps, over which the renderer cuts the field out) it is a dressed retaining face
    from the paving up to the ground, facing `mid`. The edge is split where it crosses.
    """
    out = ((a[0]+c[0])/2-mid[0], (a[1]+c[1])/2-mid[1], 0)
    pieces = [(0.0, 1.0)]
    if (za - top) * (zc - top) < 0:
        t = (top - za) / (zc - za)
        pieces = [(0.0, t), (t, 1.0)]
    for t0, t1 in pieces:
        p0 = (a[0]+(c[0]-a[0])*t0, a[1]+(c[1]-a[1])*t0); z0 = za+(zc-za)*t0
        p1 = (a[0]+(c[0]-a[0])*t1, a[1]+(c[1]-a[1])*t1); z1 = za+(zc-za)*t1
        if (z0+z1)/2 >= top:
            pts = [(*p0, -.06), (*p1, -.06), (*p1, z1), (*p0, z0)]
            b.raw(pts, conf, material, out)
        else:
            pts = [(*p0, z0), (*p1, z1), (*p1, top), (*p0, top)]
            pts = [v for i, v in enumerate(pts) if i < 2 or abs(v[2]-pts[3-i][2]) > 1e-6]
            if len(pts) >= 3:
                b.raw(pts, conf, TRIM, (-out[0], -out[1], 0))


def _curb(b, path, f, reduced=False):
    """Sweep a dressed/chamfered stone profile around two rounded plan corners.

    True 4–5 mm joints split solids at regular arc lengths; no coplanar ink strips.
    Corner stations are retained when a joint falls inside a curved stone.
    """
    lengths = [0.0]
    for a, c in zip(path, path[1:]): lengths.append(lengths[-1] + math.dist(a, c))
    total = lengths[-1]
    h = f['curb_width_m']/2
    top = f['walk_z'] + f['curb_height_m']
    bevel = min(.035, h/3)
    profile = [(-h, f['curb_base_z']), (h, f['curb_base_z']),
               (h, top-bevel), (h-bevel, top), (-h+bevel, top), (-h, top-bevel)]
    if reduced:
        # Light keeps curb height, width, joints and plan curves. Sub-35 mm
        # bevels and the hidden bottom/joint-end faces are omitted, like other
        # v4 surface microdetail; no existing house geometry is reduced further.
        profile = [(-h, f['curb_base_z']), (h, f['curb_base_z']), (h, top), (-h, top)]
    def station(distance):
        i = next((i for i in range(len(path)-1) if distance <= lengths[i+1]+1e-9), len(path)-2)
        a, c = path[i], path[i+1]
        length = lengths[i+1]-lengths[i]
        t = (distance-lengths[i])/length
        tangent = ((c[0]-a[0])/length, (c[1]-a[1])/length)
        # bisect tangent at a sampled arc vertex to join adjacent faces exactly
        if abs(distance-lengths[i+1]) < 1e-8 and i+2 < len(path):
            nxt = path[i+2]; d = math.dist(c, nxt)
            tx, ty = tangent[0]+(nxt[0]-c[0])/d, tangent[1]+(nxt[1]-c[1])/d
            size = math.hypot(tx, ty); tangent = (tx/size, ty/size)
        normal = (-tangent[1], tangent[0])
        xy = (a[0]+(c[0]-a[0])*t, a[1]+(c[1]-a[1])*t)
        return [(xy[0]+normal[0]*u, xy[1]+normal[1]*u, z) for u,z in profile], tangent, normal
    pieces = max(1, math.ceil(total/f['joint_spacing_m']))
    for piece in range(pieces):
        lo = total*piece/pieces + (f['joint_width_m']/2 if piece else 0)
        hi = total*(piece+1)/pieces - (f['joint_width_m']/2 if piece+1<pieces else 0)
        stations = [lo] + [v for v in lengths if lo+1e-8<v<hi-1e-8] + [hi]
        rings = [station(t) for t in stations]
        for (a, _, na), (c, _, nc) in zip(rings, rings[1:]):
            for i in range(len(profile)):
                if reduced and i == 0: continue  # buried underside
                j = (i+1)%len(profile)
                du, dz = profile[j][0]-profile[i][0], profile[j][1]-profile[i][1]
                b.raw([a[i], c[i], c[j], a[j]], f['conf'], TRIM,
                      (dz*(na[0]+nc[0]), dz*(na[1]+nc[1]), -2*du))
        ends = [] if reduced else [(rings[0][0], rings[0][1], -1), (rings[-1][0], rings[-1][1], 1)]
        for ring, tangent, sign in ends:
            b.raw(ring, f['conf'], TRIM, (tangent[0]*sign, tangent[1]*sign, 0))


def add_frontage(b, params, reduced=False):
    f = params.detail.get('prairie_frontage')
    if not f: return
    wall, outer, radius = f['wall_x'], f['outer_x']-f['curb_width_m']/2, f['corner_radius_m']
    for low, high in f['lawns']:
        y0, y1 = low+f['curb_width_m']/2, high-f['curb_width_m']/2
        rad = min(radius, (y1-y0)/2)
        path = [(wall, y0), (outer-rad, y0)]
        steps = 3 if reduced else 8
        for i in range(1, steps+1):
            angle = -math.pi/2 + i*math.pi/(2*steps)
            path.append((outer-rad+rad*math.cos(angle), y0+rad+rad*math.sin(angle)))
        path.append((outer, y1-rad))
        for i in range(1, steps+1):
            angle = i*math.pi/(2*steps)
            path.append((outer-rad+rad*math.cos(angle), y1-rad+rad*math.sin(angle)))
        path.append((wall, y1))
        _curb(b, path, f, reduced)
        inset = f['curb_width_m']
        _slab(b, [(wall,low+inset),(outer-inset,low+inset),
                  (outer-inset,high-inset),(wall,high-inset)], f['lawn_z'],f['conf'],LAWN)
    entry=params.detail.get('prairie_entry')
    if entry:
        low,high=f['entry_y'];wall=params.width_m;front=entry['threshold_front_x']
        half=entry['recess_base_width_m']/2;mid=entry['centre_u']
        # One broad tread meets the recessed door, with only one front riser.
        _paving(b,(f['walk_x'],low),(f['walk_x'],high),(front,high),(front,low),
                f['walk_z'],f['walk_z'],f,TRIM)
        _slab(b,[(entry['threshold_back_x'],mid-half),(front,mid-half),
                 (front,mid+half),(entry['threshold_back_x'],mid+half)],
              entry['sill_z'],entry['conf'],TRIM)
    else:
        low, high = f['entry_y']; run = f['step_run_m']; edge = params.width_m
        _paving(b, (f['walk_x'],low),(f['walk_x'],high),(edge+2*run,high),(edge+2*run,low),
                f['walk_z'],f['walk_z'],f,TRIM)
        # Wide lower tread, then the doorway-width threshold. The remaining shoulders
        # reach the wall at approach height, so a narrower upper tread leaves no void.
        _slab(b,[(wall,low),(edge+2*run,low),(edge+2*run,high),(wall,high)],
              f['walk_z'],f['conf'],TRIM)
        door_low, door_high = f['door_y']
        _slab(b,[(wall,door_low-.12),(edge+2*run,door_low-.12),
                 (edge+2*run,door_high+.12),(wall,door_high+.12)],
              (f['walk_z']+f['door_z'])/2,f['conf'],TRIM)
        sill_back = edge + DOOR_REVEAL_FRONT_M
        _slab(b,[(sill_back,door_low),(edge+run,door_low),(edge+run,door_high),(sill_back,door_high)],
              f['door_z'],f['conf'],TRIM)
    p,q,inner_p,inner_q = _passage_mouth(params)
    low,high = f['porte_y']
    _paving(b,(f['walk_x'],high),(f['walk_x'],low),q,p,
            f['walk_z'],f['passage_front_z'],f,DRIVE)
    # The threshold's inner half lies between the passage's own reveals; only the
    # half outside the facade needs its sides closed (T-2976).
    _paving(b,p,q,inner_q,inner_p,f['passage_front_z'],f['passage_front_z'],f,TRIM,edges=False)
    wall = params.width_m
    mid = ((p[0]+inner_p[0])/2, (p[1]+q[1])/2)
    for a in (p, q):
        _edge(b, a, (wall, a[1]), f['passage_front_z'], f['passage_front_z'], mid, f['conf'], TRIM)


def _passage_mouth(params):
    p,q,r,s = params.detail['underpass']['pts']
    half = params.detail['prairie_frontage']['porte_threshold_depth_m']/2
    def inset(a,c):
        t = half/(a[0]-c[0])
        return (a[0]-half, a[1]+(c[1]-a[1])*t)
    return (p[0]+half,p[1]), (q[0]+half,q[1]), inset(p,s), inset(q,r)


def passage_floor(b, params):
    f = params.detail.get('prairie_frontage')
    if not f: return False
    p,q,r,s = params.detail['underpass']['pts']
    _,_,p,q = _passage_mouth(params)
    # Its sides are the underpass's own reveals, which run down past the floor.
    _paving(b,p,q,r,s,f['passage_front_z'],f['passage_court_z'],f,DRIVE,
            edges=min(f['passage_front_z'],f['passage_court_z'])>=0)
    return True


def passage_ground(params):
    """T-2976: the sunk floor of the carriage way, piece by piece, in building metres.

    Each piece is a plan quad and the paving height at its four corners, exactly as
    add_frontage, passage_floor and the courtyard ramp lay it: the approach falling
    from the walk to the mouth, the threshold, the passage floor and the court ramp.
    compile_scene declares them so the renderer cuts the ground out over them and
    the walk follows them; [] when nothing is sunk below the ground.
    """
    f = params.detail.get('prairie_frontage')
    u = params.detail.get('underpass')
    if not f or not u or min(f['passage_front_z'], f['passage_court_z']) >= 0:
        return []
    p,q,inner_p,inner_q = _passage_mouth(params)
    _,_,r,s = u['pts']
    low,high = f['porte_y']
    zf, zc, zw = f['passage_front_z'], f['passage_court_z'], f['walk_z']
    pieces = [
        ([(f['walk_x'],high),(f['walk_x'],low),q,p], [zw,zw,zf,zf]),
        ([p,q,inner_q,inner_p], [zf]*4),
        ([inner_p,inner_q,r,s], [zf,zf,zc,zc]),
    ]
    ramp = court_ramp(params)
    if ramp:
        pieces.append((ramp['pts'], ramp['z']))
    # T-2978: the court ground's fall to the mouth, under its lawn, walk and drive. The
    # ramp is listed first, so where the two overlap the walk reads the ramp's paving.
    from archetypes.masonry_house_v4_ground import fall_quads
    turf = (params.detail.get('court_ground') or {}).get('turf_lift_m', 0.0)
    for pts, zs in fall_quads(params):
        pieces.append((pts, [turf + z for z in zs]))
    return [{'pts': [tuple(round(v, 4) for v in pt) for pt in pts], 'z': [round(z, 4) for z in zs]}
            for pts, zs in pieces]


def court_ramp(params):
    """T-2976: the carriage way's ramp from the passage's court mouth up to the drive.

    Runs `passage_ramp_run_m` into the court along the drive's own two edges, from the
    passage floor's court height to the drive's lift. None when the record has none.
    """
    spec = params.detail.get('court_ground') or {}
    f = params.detail.get('prairie_frontage') or {}
    run = spec.get('passage_ramp_run_m')
    drive = next((g for g in params.ground if g['kind'] == 'drive'), None)
    if not run or not drive or 'passage_court_z' not in f or len(drive['pts']) != 4:
        return None
    m0, a1, b1, m1 = drive['pts']        # mouth north, far north, far south, mouth south
    def along(a, c):
        t = run / math.dist(a, c)
        return (a[0]+(c[0]-a[0])*t, a[1]+(c[1]-a[1])*t)
    zc, zd = f['passage_court_z'], drive['lift_m']
    pts = [tuple(m0), along(m0, a1), along(m1, b1), tuple(m1)]
    # T-2978: it rises to the drive where the court's fall has sunk the drive.
    from archetypes.masonry_house_v4_ground import fall_height
    h = fall_height(params)
    return {'pts': pts, 'z': [zc, zd + h(*pts[1]), zd + h(*pts[2]), zc]}
