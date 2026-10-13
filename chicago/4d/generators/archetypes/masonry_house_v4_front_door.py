"""Glessner v4 Prairie Avenue front door (T-2216, audit GA-14).

The leaf as Richardson's office drew it on sheet No. 95 (Art Institute of
Chicago, mqc 69517; its 'Copy' No. 95A, mqc 69194, agrees line for line):

  a studded oak border round two fields, its inside corners cusped;
  a square iron grille in the upper field, six bars each way running past its
  frame to round knobs, the centre three cells by four filled with the house
  number 1800 over three rows of curled scrolls;
  an iron strap across the leaf on the middle rail, with a boss and knob at its
  centre and a latch plate with a drop ring at its left end, and iron corners;
  two fielded panels in the lower field.

The other No. 95A (mqc 69279), a floral rosette grille endorsed 'Not Correct',
is not drawn. An undated photograph of the front shows 1800 and a knob on the
dark leaf where this sheet puts them, which is why this sheet is the built door.

Positions are the sheet's shares of the leaf (f across from the VIEWER'S LEFT,
t down from the top), applied to HABS sheet 5's leaf. Every depth is
reconstructed. Oak members carry their own grain: stiles run it upright, rails
and panels run it across, each member's figure shifted so no two line up.
"""
from __future__ import annotations

import math


def _plane_point(pl, u, z, off=0.0):
    # masonry_house._plane_point, restated so this module imports without Blender.
    at = pl['at'] + pl['sign'] * off
    return (at, u, z) if pl['axis'] == 'x' else (u, at, z)


def _plane_dir(pl):
    return (pl['sign'], 0.0, 0.0) if pl['axis'] == 'x' else (0.0, pl['sign'], 0.0)

WOOD, IRON = 6, 10

BACK, FIELD, BORDER = -.305, -.262, -.246
GRILLE = (.232, .776, .13, .492)        # f0, f1, t0, t1: the frame's outside
PANELS = ((.236, .781, .616, .719), (.236, .781, .77, .87))
RAIL = (.513, .603)                      # the middle rail between the two fields
STILE, TOP, FOOT = .085, .05, .04


def _norm(v):
    length = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / length for c in v)


class Door:
    def __init__(self, b, o):
        self.b, self.o, self.conf = b, o, o['conf']
        self.reduced = not getattr(b, 'smooth_rock_faces', True)
        a, c, z0, z1 = o['u0'], o['u1'], o['z0'], o['z1']
        self.la, self.lc, self.lz0, self.lz1 = a + .025, c - .025, z0 + .02, z1 - .02
        self.w, self.h = self.lc - self.la, self.lz1 - self.lz0
        # +1 when u increases to the viewer's right, seen from outside (T-2214).
        self.right = -o['sign'] if o['axis'] == 'y' else o['sign']
        self.n = _plane_dir(o)
        self.members = 0

    # Shares of the leaf to plane coordinates.
    def u(self, f):
        return self.la + f * self.w if self.right > 0 else self.lc - f * self.w

    def z(self, t):
        return self.lz1 - t * self.h

    def rect(self, f0, f1, t0, t1):
        u0, u1 = sorted((self.u(f0), self.u(f1)))
        return [(u0, self.z(t1)), (u1, self.z(t1)), (u1, self.z(t0)), (u0, self.z(t0))]

    def point(self, u, z, d):
        return _plane_point(self.o, u, z, d)

    def solid(self, poly, d0, d1, mat, grain=None):
        """A prism from depth d0 out to d1: its face and sides, never its back."""
        front = [self.point(u, z, d1) for u, z in poly]
        idx = self.b.raw(front, self.conf, mat, self.n)
        cu = sum(p[0] for p in poly) / len(poly)
        cz = sum(p[1] for p in poly) / len(poly)
        centre = self.point(cu, cz, (d0 + d1) / 2)
        for p, q in zip(poly, poly[1:] + poly[:1]):
            quad = [self.point(*p, d0), self.point(*q, d0), self.point(*q, d1), self.point(*p, d1)]
            mid = tuple(sum(v[k] for v in quad) / 4 for k in range(3))
            self.b.raw(quad, self.conf, mat, tuple(mid[k] - centre[k] for k in range(3)))
        if grain and idx:
            self.grain(idx, grain)

    def grain(self, idx, across):
        """Each oak member's own figure: upright on stiles, across on rails and panels."""
        uvs = getattr(self.b, 'roof_uvs', None)
        if uvs is None:
            return
        self.members += 1
        su, sz = (self.members * .377) % .8, (self.members * .911) % 2.4
        along = 1 if self.o['axis'] == 'x' else 0
        for i in idx:
            v = self.b.verts[i]
            u, z = v[along] + su, v[2] + sz
            # Metres; assign_metric_uvs divides by oak's 0.8 x 2.4 m repeat,
            # whose long side is the grain.
            uvs[i] = (z, u) if across == 'across' else (u, z)

    def box(self, f0, f1, t0, t1, d0, d1, mat, grain=None):
        self.solid(self.rect(f0, f1, t0, t1), d0, d1, mat, grain)

    def box_m(self, u0, u1, z0, z1, d0, d1, mat):
        self.solid([(u0, z0), (u1, z0), (u1, z1), (u0, z1)], d0, d1, mat)

    def stud(self, u, z, d, r=.011, height=.009, sides=8):
        """A domed nail head standing on the oak, not a painted dot."""
        if self.reduced:
            return
        base = [(u + r * math.cos(2 * math.pi * k / sides), z + r * math.sin(2 * math.pi * k / sides))
                for k in range(sides)]
        mid = [(u + .72 * (p[0] - u), z + .72 * (p[1] - z)) for p in base]
        top = self.point(u, z, d + height)
        for k in range(sides):
            j = (k + 1) % sides
            a, c = base[k], base[j]
            ma, mc = mid[k], mid[j]
            out = _norm(tuple(self.point((a[0] + c[0]) / 2, (a[1] + c[1]) / 2, d)[i] - self.point(u, z, d)[i]
                              for i in range(3)))
            want = tuple(out[i] + .6 * self.n[i] for i in range(3))
            self.b.raw([self.point(*a, d), self.point(*c, d), self.point(*mc, d + .65 * height),
                        self.point(*ma, d + .65 * height)], self.conf, IRON, want)
            self.b.raw([self.point(*ma, d + .65 * height), self.point(*mc, d + .65 * height), top],
                       self.conf, IRON, tuple(out[i] + 1.6 * self.n[i] for i in range(3)))

    def tube(self, path, radius, sides=6):
        """Round wrought-iron stock along a path of (u, z, d)."""
        if self.reduced or len(path) < 2:
            return
        rings = []
        for i, (u, z, d) in enumerate(path):
            a, c = path[max(0, i - 1)], path[min(len(path) - 1, i + 1)]
            length = math.hypot(c[0] - a[0], c[1] - a[1]) or 1
            nu, nz = -(c[1] - a[1]) / length, (c[0] - a[0]) / length
            rings.append([(u + radius * nu * math.cos(th), z + radius * nz * math.cos(th), d + radius * math.sin(th))
                          for th in (2 * math.pi * j / sides for j in range(sides))])
        for i in range(len(rings) - 1):
            for j in range(sides):
                k = (j + 1) % sides
                quad = [rings[i][j], rings[i + 1][j], rings[i + 1][k], rings[i][k]]
                centre = path[i]
                mid = tuple(sum(q[m] for q in quad) / 4 for m in range(3))
                want = self.point(*mid)
                want = tuple(want[m] - self.point(*centre)[m] for m in range(3))
                self.b.raw([self.point(*q) for q in quad], self.conf, IRON, want)

    # The parts, outermost first.
    def leaf(self, subtract, interior_recess, glass_pane):
        f0, f1, t0, t1 = GRILLE
        inset = .013 / self.w
        light = self.rect(f0 + inset, f1 - inset, t0 + inset * self.w / self.h, t1 - inset * self.w / self.h)
        whole = [(min(self.la, self.lc), self.lz0), (max(self.la, self.lc), self.lz0),
                 (max(self.la, self.lc), self.lz1), (min(self.la, self.lc), self.lz1)]
        for fragment in subtract(whole, [light]):
            self.solid(fragment, BACK, FIELD, WOOD, 'upright')
        interior_recess(self.b, light, lambda u, z, off: self.point(u, z, off), self.n, front=-.279)
        glass_pane(self.b, [self.point(u, z, -.273) for u, z in light], self.n, self.conf)

    def border(self):
        self.box(0, STILE, 0, 1, FIELD, BORDER, WOOD, 'upright')
        self.box(1 - STILE, 1, 0, 1, FIELD, BORDER, WOOD, 'upright')
        for t0, t1 in ((0, TOP), (RAIL[0], RAIL[1]), (1 - FOOT, 1)):
            self.box(STILE, 1 - STILE, t0, t1, FIELD, BORDER, WOOD, 'across')
        # The fields' inside corners are cusped on the sheet: a quarter-round lobe
        # of the border into each corner is the bounded stand-in for the ogee.
        # The light tier, at its triangle cap, keeps the square corners.
        if self.reduced:
            return
        r = .05
        for f in (STILE, 1 - STILE):
            for t, down in ((TOP, 1), (RAIL[0], -1), (RAIL[1], 1), (1 - FOOT, -1)):
                into_u = (1 if f < .5 else -1) * self.right
                cu, cz = self.u(f), self.z(t)
                steps = 6
                lobe = [(cu, cz)] + [(cu + into_u * r * math.cos(math.pi / 2 * k / steps),
                                      cz - down * r * math.sin(math.pi / 2 * k / steps)) for k in range(steps + 1)]
                self.solid(lobe, FIELD, BORDER, WOOD, 'across')

    def panels(self):
        for f0, f1, t0, t1 in PANELS:
            # A moulding round the sinking, then the field bevelled up to its flat.
            m = .014
            u0, u1 = sorted((self.u(f0), self.u(f1)))
            z0, z1 = self.z(t1), self.z(t0)
            for a, c, p, q in ((u0 - m, u1 + m, z0 - m, z0), (u0 - m, u1 + m, z1, z1 + m),
                               (u0 - m, u0, z0, z1), (u1, u1 + m, z0, z1)):
                self.solid([(a, p), (c, p), (c, q), (a, q)], FIELD, FIELD + .008, WOOD, 'across')
            iu, iz = .045, .03
            outer = [(u0, z0), (u1, z0), (u1, z1), (u0, z1)]
            inner = [(u0 + iu, z0 + iz), (u1 - iu, z0 + iz), (u1 - iu, z1 - iz), (u0 + iu, z1 - iz)]
            lo, hi = FIELD + .001, FIELD + .011
            idx = self.b.raw([self.point(u, z, hi) for u, z in inner], self.conf, WOOD, self.n)
            self.grain(idx, 'across')
            for k in range(4):
                j = (k + 1) % 4
                quad = [self.point(*outer[k], lo), self.point(*outer[j], lo),
                        self.point(*inner[j], hi), self.point(*inner[k], hi)]
                mid_o = ((outer[k][0] + outer[j][0]) / 2, (outer[k][1] + outer[j][1]) / 2)
                out = self.point(*mid_o, 0)
                cen = self.point((u0 + u1) / 2, (z0 + z1) / 2, 0)
                want = tuple(out[i] - cen[i] + 2 * self.n[i] * (hi - lo) / .045 for i in range(3))
                idx = self.b.raw(quad, self.conf, WOOD, want)
                self.grain(idx, 'across')

    def grille(self):
        f0, f1, t0, t1 = GRILLE
        bw = .026
        u0, u1 = sorted((self.u(f0), self.u(f1)))
        z0, z1 = self.z(t1), self.z(t0)
        front = -.236
        for a, c, p, q in ((u0, u1, z0, z0 + bw), (u0, u1, z1 - bw, z1), (u0, u0 + bw, z0, z1), (u1 - bw, u1, z0, z1)):
            self.box_m(a, c, p, q, FIELD, front, IRON)
        ext = .035 * self.w
        bar = .015
        cols = [u0 + (u1 - u0) * k / 7 for k in range(1, 7)]
        rows = [z1 - (z1 - z0) * k / 7 for k in range(1, 7)]
        for u in cols:
            self.box_m(u - bar / 2, u + bar / 2, z0 - ext, z1 + ext, FIELD - .004, -.244, IRON)
            for z in (z0 - ext, z1 + ext):
                self.stud(u, z, -.244, r=.012, height=.011)
        for z in rows:
            self.box_m(u0 - ext, u1 + ext, z - bar / 2, z + bar / 2, FIELD - .002, -.238, IRON)
            for u in (u0 - ext, u1 + ext):
                self.stud(u, z, -.238, r=.012, height=.011)
        # The filled centre: columns between the second and fifth bars, rows
        # between the first and fifth, read across from the viewer's left.
        left, right_ = (cols[1], cols[4]) if self.right > 0 else (cols[4], cols[1])
        cell_u = (right_ - left) / 3
        cell_z = (rows[0] - rows[4]) / 4
        d = -.249
        self.number(left, cell_u, rows[0], cell_z, d)
        for row in range(1, 4):
            for col in range(3):
                cu = left + cell_u * (col + .5)
                cz = rows[0] - cell_z * (row + .5)
                self.scroll(cu, cz, min(abs(cell_u), cell_z) * .40, d)

    def scroll(self, cu, cz, radius, d):
        """One curl: a spiral of round bar turned in on itself, a cell's width."""
        path = []
        turns = 1.55
        for i in range(37):
            s = i / 36
            th = math.pi * .5 + 2 * math.pi * turns * s
            rr = radius * (1 - .78 * s)
            path.append((cu + self.right * rr * math.cos(th), cz + rr * math.sin(th), d))
        self.tube(path, .0055)

    def number(self, left, cell_u, top, cell_z, d):
        """1800, the house number, in the grille's top filled row."""
        width = cell_u * 3
        pitch = width / 4
        gh = cell_z * .74
        gw = abs(pitch) * .62
        base = top - cell_z / 2 - gh / 2
        r = .0055
        for k, ch in enumerate('1800'):
            cu = left + pitch * (k + .5)
            if ch == '1':
                self.tube([(cu, base, d), (cu, base + gh, d)], r)
                self.tube([(cu, base + gh, d), (cu - self.right * gw * .35, base + gh * .8, d)], r)
                self.tube([(cu - self.right * gw * .22, base, d), (cu + self.right * gw * .22, base, d)], r)
            elif ch == '8':
                for cz, rx, rz in ((base + gh * .27, gw * .44, gh * .27), (base + gh * .76, gw * .36, gh * .24)):
                    self.tube([(cu + rx * math.cos(2 * math.pi * i / 20), cz + rz * math.sin(2 * math.pi * i / 20), d)
                               for i in range(21)], r)
            else:
                self.tube([(cu + gw * .42 * math.cos(2 * math.pi * i / 22), base + gh / 2 + gh * .5 * math.sin(2 * math.pi * i / 22), d)
                           for i in range(23)], r)

    def hardware(self):
        on = BORDER
        t = (RAIL[0] + RAIL[1]) / 2
        half = .017
        sz = self.z(t)
        u0, u1 = sorted((self.u(.06), self.u(.93)))
        self.box_m(u0, u1, sz - half, sz + half, on, on + .007, IRON)
        # Lozenge ends on the strap, at the stiles.
        for f in (.06, .93):
            cu = self.u(f)
            self.solid([(cu - .035, sz), (cu, sz - .04), (cu + .035, sz), (cu, sz + .04)], on, on + .008, IRON)
        if not self.reduced:
            step = .1
            count = int((u1 - u0 - .1) / step)
            for k in range(count + 1):
                self.stud(u0 + .05 + (u1 - u0 - .1) * k / max(1, count), sz, on + .007, r=.008, height=.006)
        # The boss and knob at the strap's centre.
        cu = self.u(.5)
        boss = [(cu - .07, sz), (cu - .03, sz - .045), (cu, sz - .058), (cu + .03, sz - .045),
                (cu + .07, sz), (cu + .03, sz + .045), (cu, sz + .058), (cu - .03, sz + .045)]
        self.solid(boss, on, on + .014, IRON)
        if self.reduced:
            self.box_m(cu - .022, cu + .022, sz - .022, sz + .022, on + .014, on + .04, IRON)
        else:
            self.stud(cu, sz, on + .014, r=.027, height=.032, sides=12)
        # The latch plate and drop ring at the left end.
        pu0, pu1 = sorted((self.u(.125), self.u(.195)))
        self.box_m(pu0, pu1, self.z(.645), self.z(.53), on, on + .008, IRON)
        ru, rz = self.u(.095), self.z(.565)
        self.tube([(ru + .05 * math.cos(2 * math.pi * i / 24), rz + .03 * math.sin(2 * math.pi * i / 24), on + .018)
                   for i in range(25)], .006)
        # Iron corners on the border, each arm ending in a small curl.
        arm, width = .17, .032
        for f, t_ in ((0, 0), (1, 0), (0, 1), (1, 1)):
            cu, cz = self.u(f), self.z(t_)
            du = (1 if f == 0 else -1) * self.right
            dz = -1 if t_ == 0 else 1
            inset = .012
            cu += du * inset
            cz += dz * inset
            self.box_m(*sorted((cu, cu + du * arm)), *sorted((cz, cz + dz * width)), on, on + .006, IRON)
            self.box_m(*sorted((cu, cu + du * width)), *sorted((cz, cz + dz * arm)), on, on + .006, IRON)
            for eu, ez, a0 in ((cu + du * arm, cz + dz * width / 2, 0), (cu + du * width / 2, cz + dz * arm, 1)):
                rr = .018
                path = []
                for i in range(15):
                    th = math.pi * 1.6 * i / 14
                    if a0 == 0:
                        path.append((eu + du * rr * math.sin(th), ez - dz * rr * (1 - math.cos(th)) + dz * rr * 0, on + .008))
                    else:
                        path.append((eu - du * rr * (1 - math.cos(th)), ez + dz * rr * math.sin(th), on + .008))
                self.tube(path, .005)

    def studs(self):
        if self.reduced:
            return
        count = max(2, round(self.h * .94 / .16))
        for f in (.045, .955):
            for k in range(count + 1):
                t = .03 + .94 * k / count
                if RAIL[0] + .01 < t < RAIL[1] - .01 and f < .5:
                    continue
                self.stud(self.u(f), self.z(t), BORDER)
        across = max(2, round(self.w * .8 / .16))
        for t in (.022, .978):
            for k in range(across + 1):
                self.stud(self.u(.1 + .8 * k / across), self.z(t), BORDER)


def build(b, o, subtract, interior_recess, glass_pane):
    door = Door(b, o)
    door.leaf(subtract, interior_recess, glass_pane)
    door.border()
    door.panels()
    door.grille()
    door.hardware()
    door.studs()
