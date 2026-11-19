#!/usr/bin/env python3
"""Portable 1871 context forms and original facade maps, without Blender.

python3 generators/city_context_emit.py          # writes kit.glb + kit.json
python3 generators/city_context_emit.py --check  # reproduce and compare every byte

Inputs are the adjacent explicit recipe and this generator. The shared GLB has
one textured material and two meshes per family: individual facade bays nearby,
four walls carrying the same facade atlas at a distance. Neither tier is an
identified historic building. All vertices carry reconstructed confidence.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
from pathlib import Path
import random
import struct
import sys

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
FOLDER = ROOT / "data/context/1871"
RECIPE = FOLDER / "kit-recipe.json"
sys.path.insert(0, str(ROOT / "tools"))
from compile_scene import cite  # shared source names, URLs, evidence ladder and limits


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()


def png(image):
    stream = io.BytesIO()
    image.save(stream, "PNG", optimize=False, compress_level=9)
    return stream.getvalue()


def make_atlas(recipe):
    """8x8 cells: material rows; wall, window, door, shop, loading and trim cells.

    Maps are original procedural illustrations, not photographs or evidence.
    Margins repeat the cell edge so mip filtering cannot borrow another facade.
    """
    size = recipe["texture_size"]
    tile = size // 8
    color = Image.new("RGB", (size, size), (125, 119, 106))
    height = Image.new("L", (size, size), 128)
    orm = Image.new("RGB", (size, size), (255, 235, 0))
    families = {"brick": (145, 82, 60), "timber": (180, 168, 139),
                "stone": (181, 163, 132), "weathered": (123, 113, 94)}
    slots = {}
    rand = random.Random(18711008)
    for row, (family, base) in enumerate(families.items()):
        for col, kind in enumerate(("wall", "window", "door", "shop", "loading", "trim")):
            x0, y0 = col * tile, row * tile
            im = Image.new("RGB", (tile, tile), base)
            relief = Image.new("L", (tile, tile), 128)
            surface = Image.new("RGB", (tile, tile), (250, 237, 0))
            d, h, p = ImageDraw.Draw(im), ImageDraw.Draw(relief), ImageDraw.Draw(surface)
            if family in ("brick", "stone"):
                course = 4 if family == "brick" else 12
                unit = 12 if family == "brick" else 28
                d.rectangle((0, 0, tile, tile), fill=(105, 101, 89))
                h.rectangle((0, 0, tile, tile), fill=113)
                for y in range(-course, tile + course, course):
                    offset = (unit // 2) * ((y // course) % 2)
                    for x in range(-unit, tile + unit, unit):
                        light = rand.randint(-12, 10)
                        tone = tuple(max(0, min(255, v + light)) for v in base)
                        rect = (x + offset + 1, y + 1, x + offset + unit - 1, y + course - 1)
                        d.rectangle(rect, fill=tone)
                        h.rectangle(rect, fill=128 + rand.randint(-2, 2))
            else:
                for y in range(0, tile, 9):
                    v = rand.randint(-8, 8)
                    d.rectangle((0, y, tile, y + 8), fill=tuple(c + v for c in base))
                    d.line((0, y + 8, tile, y + 8), fill=tuple(int(c * .72) for c in base))
                    h.line((0, y + 8, tile, y + 8), fill=108)
            if kind in ("window", "door", "shop", "loading"):
                rect = {"window": (.29, .20, .71, .78), "door": (.29, .24, .71, 1.0),
                        "shop": (.12, .20, .88, .91), "loading": (.15, .22, .85, 1.0)}[kind]
                a, b, c, e = [round(v * tile) for v in rect]
                frame = (192, 178, 146) if family in ("brick", "stone") else (208, 197, 165)
                d.rectangle((a - 4, b - 4, c + 4, e + 3), fill=(73, 65, 53))
                d.rectangle((a - 2, b - 3, c + 3, e + 1), fill=frame)
                d.rectangle((a, b, c, e), fill=(40, 48, 46))
                h.rectangle((a - 4, b - 4, c + 4, e + 3), fill=151)
                h.rectangle((a, b, c, e), fill=72)
                p.rectangle((a, b, c, e), fill=(202, 82, 0))
                if kind in ("door", "loading"):
                    d.rectangle((a + 2, b + tile // 5, c - 2, e), fill=(78, 66, 50))
                    for q in (a + 6, (a + c) // 2, c - 6):
                        d.line((q, b + tile // 5, q, e), fill=(110, 91, 66), width=2)
                    p.rectangle((a, b + tile // 5, c, e), fill=(232, 223, 0))
                else:
                    d.rectangle((a + 2, b + 2, c - 2, (b + e) // 2), fill=(65, 78, 78))
                    d.line(((a + c) // 2, b, (a + c) // 2, e), fill=frame, width=2)
                    d.line((a, (b + e) // 2, c, (b + e) // 2), fill=frame, width=2)
                    if kind == "shop":
                        d.rectangle((a - 3, b - 12, c + 3, b - 5), fill=(66, 60, 48))
                    d.line((a - 5, e + 3, c + 5, e + 3), fill=(206, 190, 155), width=3)
            elif kind == "trim":
                d.rectangle((0, 0, tile, tile), fill=tuple(min(255, int(c * 1.10)) for c in base))
            # Reserve a four-pixel gutter in each UV rectangle, replicated outward.
            for target, source in ((color, im), (height, relief), (orm, surface)):
                target.paste(source, (x0, y0))
            slots[f"{family}_{kind}"] = (col, row)
    # Slate, wood shingles and an opaque dark roof/iron surface use dedicated cells.
    for col, (name, base, step) in enumerate((("slate", (66, 71, 69), 14),
                                            ("shingle", (102, 94, 76), 12),
                                            ("dark", (62, 59, 51), 32))):
        x0, y0 = col * tile, 4 * tile
        d, h = ImageDraw.Draw(color), ImageDraw.Draw(height)
        d.rectangle((x0, y0, x0 + tile - 1, y0 + tile - 1), fill=base)
        for y in range(0, tile, step):
            d.line((x0, y0 + y, x0 + tile - 1, y0 + y), fill=tuple(max(0, c - 15) for c in base))
            h.line((x0, y0 + y, x0 + tile - 1, y0 + y), fill=108)
            for x in range((y // step % 2) * 9, tile, 19):
                d.line((x0 + x, y0 + y, x0 + x, min(y0 + tile - 1, y0 + y + step)), fill=tuple(c + 6 for c in base))
        slots[name] = (col, 4)
    # Far silhouettes retain the actual number of storeys/bays in a single
    # textured face. They never turn a five-storey block into one giant window.
    free = [(x, y) for y in range(8) for x in range(8) if (x, y) not in slots.values()]
    for t in recipe["templates"]:
        for face, bays in (("front", t["front_bays"]), ("side", t["side_bays"])):
            col, row = free.pop(0)
            for atlas in (color, height, orm):
                source_col, source_row = slots[f"{t['material']}_window"]
                source = atlas.crop((source_col*tile,source_row*tile,(source_col+1)*tile,(source_row+1)*tile))
                composite = Image.new(atlas.mode, (tile*bays,tile*t["storeys"]))
                for floor in range(t["storeys"]):
                    for bay in range(bays): composite.paste(source,(bay*tile,floor*tile))
                atlas.paste(composite.resize((tile,tile),Image.Resampling.LANCZOS),(col*tile,row*tile))
            slots[f"{t['id']}_far_{face}"]=(col,row)
    for name, base in (("bark",(89,69,46)),("foliage_green",(83,103,55)),("foliage_ochre",(127,116,62))):
        col,row=free.pop(0); x0,y0=col*tile,row*tile
        d=ImageDraw.Draw(color)
        d.rectangle((x0,y0,x0+tile-1,y0+tile-1),fill=base)
        for _ in range(450):
            x,y=rand.randrange(tile),rand.randrange(tile)
            tone=tuple(max(0,min(255,c+rand.randint(-12,12))) for c in base)
            if name=="bark": d.line((x0+x,y0+y,x0+x,min(y0+tile-1,y0+y+12)),fill=tone)
            else: d.ellipse((x0+x,y0+y,min(x0+tile-1,x0+x+3),min(y0+tile-1,y0+y+3)),fill=tone)
        slots[name]=(col,row)
    # Height-derived normal: shallow mortar/clapboard relief and recess/frame edges.
    height = height.filter(ImageFilter.GaussianBlur(.55))
    pix = height.load()
    normal = Image.new("RGB", (size, size))
    out = normal.load()
    for y in range(size):
        for x in range(size):
            dx = (pix[min(x + 1, size - 1), y] - pix[max(x - 1, 0), y]) / 90
            dy = (pix[x, min(y + 1, size - 1)] - pix[x, max(y - 1, 0)]) / 90
            inv = 1 / math.sqrt(dx * dx + dy * dy + 1)
            out[x, y] = (round(127.5 * (1 - dx * inv)), round(127.5 * (1 + dy * inv)), round(127.5 * (1 + inv)))
    return [png(color), png(normal), png(orm)], slots


class Mesh:
    def __init__(self, slots):
        self.p, self.n, self.uv, self.idx = [], [], [], []
        self.slots = slots

    def face(self, points, tile, centre=None):
        a, b, c = points[:3]
        u, v = [b[i] - a[i] for i in range(3)], [c[i] - a[i] for i in range(3)]
        normal = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]
        length = math.sqrt(sum(t * t for t in normal))
        if length < 1e-9:
            return
        normal = [t / length for t in normal]
        reversed_face = False
        if centre is not None:
            mid = [sum(p[k] for p in points) / len(points) for k in range(3)]
            if sum(normal[k] * (mid[k] - centre[k]) for k in range(3)) < 0:
                points = list(reversed(points))
                normal = [-t for t in normal]
                reversed_face = True
        col, row = self.slots[tile]
        gutter = .015
        u0, v0, u1, v1 = (col + gutter) / 8, (row + gutter) / 8, (col + 1 - gutter) / 8, (row + 1 - gutter) / 8
        coords = [(u0, v1), (u1, v1), (u1, v0), (u0, v0)]
        if len(points) == 3:
            coords = [(u0, v1), (u1, v1), ((u0 + u1) / 2, v0)]
        if reversed_face: coords = list(reversed(coords))
        base = len(self.p)
        for p, uv in zip(points, coords):
            self.p.append(p); self.n.append(normal); self.uv.append(uv)
        for i in range(1, len(points) - 1):
            self.idx.extend((base, base + i, base + i + 1))

    def box(self, x0, x1, y0, y1, z0, z1, tile, top=None):
        centre = [(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2]
        for pts in ([(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0)],
                    [(x1,y0,z1),(x0,y0,z1),(x0,y1,z1),(x1,y1,z1)],
                    [(x0,y0,z1),(x0,y0,z0),(x0,y1,z0),(x0,y1,z1)],
                    [(x1,y0,z0),(x1,y0,z1),(x1,y1,z1),(x1,y1,z0)]):
            self.face(pts, tile, centre)
        self.face([(x0,y1,z0),(x1,y1,z0),(x1,y1,z1),(x0,y1,z1)], top or tile, centre)


def build_mesh(t, slots, far=False):
    m = Mesh(slots)
    w, d, h, rise = (t[k] for k in ("width_m", "depth_m", "eave_m", "rise_m"))
    fam, roof = t["material"], t["roof"]
    # Facade subdivisions carry a standard glazed bay without stretching a
    # whole floor across a wall. Far tier shares the silhouette and a broad bay.
    sides = [((-w/2,-d/2),(w/2,-d/2), t["front_bays"], True),
             ((w/2,d/2),(-w/2,d/2), t["front_bays"], False),
             ((-w/2,d/2),(-w/2,-d/2), t["side_bays"], False),
             ((w/2,-d/2),(w/2,d/2), t["side_bays"], False)]
    for side_index, (a, b, bays, front) in enumerate(sides):
        rows, cols = (1, 1) if far else (t["storeys"], bays)
        for floor in range(rows):
            for bay in range(cols):
                p = [a[k] + (b[k] - a[k]) * bay / cols for k in range(2)]
                q = [a[k] + (b[k] - a[k]) * (bay + 1) / cols for k in range(2)]
                y0, y1 = h * floor / rows, h * (floor + 1) / rows
                kind = "window"
                if front and floor == 0 and not far:
                    if t.get("warehouse") and bay == cols // 2: kind = "loading"
                    elif bay == cols // 2: kind = "door"
                    elif t.get("shop"): kind = "shop"
                texture = f"{t['id']}_far_{'front' if side_index < 2 else 'side'}" if far else f"{fam}_{kind}"
                m.face([(p[0],y0,p[1]),(q[0],y0,q[1]),(q[0],y1,q[1]),(p[0],y1,p[1])], texture, (0,h/2,0))
    over = .23 if far else .34
    x0, x1, z0, z1 = -w/2-over, w/2+over, -d/2-over, d/2+over
    roof_tile = "shingle" if fam in ("timber", "weathered") else "slate"
    if roof == "flat":
        m.box(x0,x1,h-.22,h+.13,z0,z1,f"{fam}_trim", "dark")
        if not far:
            m.box(-w/2+.28,w/2-.28,h+.13,h+.16,-d/2+.28,d/2-.28,"dark")
    elif roof == "gable":
        m.face([(x0,h,z0),(x0,h,z1),(0,h+rise,z1),(0,h+rise,z0)], roof_tile, (0,h,0))
        m.face([(x1,h,z1),(x1,h,z0),(0,h+rise,z0),(0,h+rise,z1)], roof_tile, (0,h,0))
        m.face([(-w/2,h,-d/2),(w/2,h,-d/2),(0,h+rise,-d/2)], f"{fam}_wall", (0,h,0))
        m.face([(w/2,h,d/2),(-w/2,h,d/2),(0,h+rise,d/2)], f"{fam}_wall", (0,h,0))
    elif roof == "hip":
        r0, r1 = z0 + min(w/2, d/2), z1 - min(w/2, d/2)
        m.face([(x0,h,z0),(x1,h,z0),(0,h+rise,r0)], roof_tile, (0,h,0))
        m.face([(x1,h,z1),(x0,h,z1),(0,h+rise,r1)], roof_tile, (0,h,0))
        m.face([(x0,h,z1),(x0,h,z0),(0,h+rise,r0),(0,h+rise,r1)], roof_tile, (0,h,0))
        m.face([(x1,h,z0),(x1,h,z1),(0,h+rise,r1),(0,h+rise,r0)], roof_tile, (0,h,0))
    elif roof == "mansard":
        inset = min(1.3,w*.2)
        bottom=[(x0,h,z0),(x1,h,z0),(x1,h,z1),(x0,h,z1)]
        top=[(x0+inset,h+rise,z0+inset),(x1-inset,h+rise,z0+inset),(x1-inset,h+rise,z1-inset),(x0+inset,h+rise,z1-inset)]
        for i in range(4): m.face([bottom[i],bottom[(i+1)%4],top[(i+1)%4],top[i]],roof_tile,(0,h,0))
        m.face(top,"dark",(0,h,0))
        if not far:
            for x in (-w*.25,w*.25):
                m.box(x-.55,x+.55,h+.45,h+1.9,z0+.12,z0+.85,f"{fam}_window", "slate")
    if not far:
        # A stone plinth and cornice are physical silhouette/shadow lines.
        m.box(-w/2-.04,w/2+.04,0,.30,-d/2-.04,d/2+.04,f"{fam}_trim")
        cw=.7 if not t.get("factory") else 1.4
        cx, cz=w*.29,d*.19
        ch=h+rise*.7+(1.2 if not t.get("factory") else 11)
        m.box(cx-cw/2,cx+cw/2,h-.1,ch,cz-cw/2,cz+cw/2,"brick_wall","dark")
        m.box(cx-cw*.62,cx+cw*.62,ch-.17,ch+.02,cz-cw*.62,cz+cw*.62,"brick_trim","dark")
        if t.get("shop"):
            m.box(-w/2-.12,w/2+.12,h/t["storeys"]-.23,h/t["storeys"]-.02,-d/2-.3,-d/2+.03,f"{fam}_trim")
        if t["id"] in ("timber_cottage","timber_house","villa_hip"):
            # Modest front stoop, safe as context rather than a walkable interior.
            m.box(-.8,.8,0,.26,-d/2-.75,-d/2,f"{fam}_trim")
    elif t.get("factory"):
        # Factory stacks are skyline forms, retained in the distant tier.
        cx,cz=w*.29,d*.19
        m.box(cx-.7,cx+.7,h-.1,h+rise*.7+11,cz-.7,cz+.7,"brick_wall","dark")
    return m


# Integrate after Mesh and before glb(). These generic early-autumn silhouettes
# are reconstructed context, not identified species, measured trees or phenology.
# Atlas tile names needed: bark, foliage_green, foliage_ochre.

def build_tree_mesh(t, slots, far=False):
    """Original portable deciduous tree: 96 near / 28 far triangles.

    t: id, form ('round'|'oval'|'spreading'), height_m, crown_r_m,
    trunk_r_m. All numbers are metres. Base at (0,0,0), +Y up.
    Every face will receive the shared kit's reconstructed _CONFIDENCE=1.
    """
    m = Mesh(slots)
    height = float(t["height_m"])
    radius = float(t["crown_r_m"])
    trunk = float(t.get("trunk_r_m", .22))
    form = t.get("form", "round")

    def cross(a, b):
        return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])

    def unit(a):
        d = math.sqrt(sum(v*v for v in a)) or 1
        return tuple(v/d for v in a)

    def branch(a, b, r0, r1, sides):
        axis = unit(tuple(b[k]-a[k] for k in range(3)))
        ref = (1,0,0) if abs(axis[0]) < .9 else (0,0,1)
        u = unit(cross(axis, ref))
        v = cross(axis, u)
        rings = []
        for centre, r in ((a,r0),(b,r1)):
            rings.append([tuple(centre[k]+r*(u[k]*math.cos(i*2*math.pi/sides)+v[k]*math.sin(i*2*math.pi/sides)) for k in range(3)) for i in range(sides)])
        centre = tuple((a[k]+b[k])/2 for k in range(3))
        for i in range(sides):
            j=(i+1)%sides
            m.face([rings[0][i],rings[0][j],rings[1][j],rings[1][i]], "bark", centre)

    # Twenty triangles, no transparency, no hidden interior or leaf-card sorting.
    # Axis-normalising the icosahedron puts extrema exactly at centre +/- radii.
    phi=(1+math.sqrt(5))/2
    vertices=[(-1,phi,0),(1,phi,0),(-1,-phi,0),(1,-phi,0),
              (0,-1,phi),(0,1,phi),(0,-1,-phi),(0,1,-phi),
              (phi,0,-1),(phi,0,1),(-phi,0,-1),(-phi,0,1)]
    faces=[(0,11,5),(0,5,1),(0,1,7),(0,7,10),(0,10,11),
           (1,5,9),(5,11,4),(11,10,2),(10,7,6),(7,1,8),
           (3,9,4),(3,4,2),(3,2,6),(3,6,8),(3,8,9),
           (4,9,5),(2,4,11),(6,2,10),(8,6,7),(9,8,1)]

    def crown(centre, radii, index):
        points=[tuple(centre[k]+p[k]*radii[k]/phi for k in range(3)) for p in vertices]
        for face_index, face in enumerate(faces):
            # Sparse ochre is a reconstructed early-autumn variation, not a
            # species identification or an assertion about 8 October's weather.
            tile="foliage_ochre" if (face_index+index*3)%11 == 0 else "foliage_green"
            first=len(m.p)
            m.face([points[k] for k in face], tile, centre)
            # Smooth crown normals retain the low-cost portable silhouette
            # without making every triangular lobe a separate flat plane.
            for i in range(first,len(m.p)):
                n=tuple((m.p[i][k]-centre[k])/(radii[k]*radii[k]) for k in range(3))
                m.n[i]=unit(n)

    if form == "oval":
        centre=(0,.64*height,0); radii=(.82*radius,.36*height,.78*radius)
        lobes=[((-.35*radius,.52*height,.10*radius),(.65*radius,.23*height,.68*radius)),
               ((.35*radius,.57*height,-.10*radius),(.65*radius,.26*height,.68*radius))]
    elif form == "spreading":
        centre=(0,.72*height,0); radii=(radius,.28*height,.82*radius)
        lobes=[((-.39*radius,.60*height,.18*radius),(.61*radius,.23*height,.72*radius)),
               ((.39*radius,.62*height,-.18*radius),(.61*radius,.24*height,.72*radius))]
    else:
        centre=(0,.67*height,0); radii=(radius,.33*height,.88*radius)
        lobes=[((-.35*radius,.55*height,.16*radius),(.65*radius,.25*height,.70*radius)),
               ((.35*radius,.59*height,-.16*radius),(.65*radius,.27*height,.70*radius))]

    branch((0,0,0),(0,.65*height,0),trunk,trunk*.42,4 if far else 6)
    crown(centre,radii,0)
    if not far:
        for index,(position,extent) in enumerate(lobes,1):
            crown(position,extent,index)
        for end in ((-.48*radius,.57*height,.10*radius),
                    (.48*radius,.61*height,-.10*radius),
                    (.08*radius,.68*height,.46*radius)):
            branch((0,.29*height,0),end,trunk*.55,trunk*.12,4)
    return m



def glb(recipe):
    maps, slots = make_atlas(recipe)
    blob = bytearray(); views=[]; accessors=[]; meshes=[]; nodes=[]
    def view(data, target=None):
        while len(blob)%4: blob.append(0)
        off=len(blob); blob.extend(data)
        entry={"buffer":0,"byteOffset":off,"byteLength":len(data)}
        if target: entry["target"]=target
        views.append(entry); return len(views)-1
    def accessor(values, width, kind="f", bounds=False):
        flat=[v for row in values for v in row] if width>1 else values
        packed=struct.pack("<"+kind*len(flat),*flat)
        item={"bufferView":view(packed,34963 if kind=="I" else 34962),"componentType":5125 if kind=="I" else 5126,"count":len(values),"type":{1:"SCALAR",2:"VEC2",3:"VEC3"}[width]}
        if bounds:
            item["min"]=[min(row[k] for row in values) for k in range(width)]
            item["max"]=[max(row[k] for row in values) for k in range(width)]
        accessors.append(item); return len(accessors)-1
    stats=[]; vegetation=[]
    for t in recipe["templates"]+recipe.get("vegetation",[]):
        record=dict(t); record["nodes"]={}; record["triangles"]={}
        is_tree="form" in t
        if is_tree:
            record.update(width_m=2*t["crown_r_m"],depth_m=2*t["crown_r_m"],eave_m=t["height_m"],vegetation=True)
        for tier in ("near","far"):
            m=build_tree_mesh(t,slots,tier=="far") if is_tree else build_mesh(t,slots,tier=="far")
            attrs={"POSITION":accessor(m.p,3,bounds=True),"NORMAL":accessor(m.n,3),"TEXCOORD_0":accessor(m.uv,2),"_CONFIDENCE":accessor([1.0]*len(m.p),1)}
            meshes.append({"name":f"{t['id']}__{tier}","primitives":[{"attributes":attrs,"indices":accessor(m.idx,1,"I"),"material":0}]})
            nodes.append({"name":f"{t['id']}__{tier}","mesh":len(meshes)-1,"extras":{"context_template":t["id"],"tier":tier,"confidence":"reconstructed","scene_year":1871}})
            record["nodes"][tier]=nodes[-1]["name"]; record["triangles"][tier]=len(m.idx)//3
        (vegetation if is_tree else stats).append(record)
    images=[{"bufferView":view(data),"mimeType":"image/png","name":name} for data,name in zip(maps,("original_facade_basecolor","original_facade_normal","original_facade_orm"))]
    document={"asset":{"version":"2.0","generator":"city_context_emit.py","extras":{"confidence":"reconstructed","source_limit":recipe["source_limit"],"license":recipe["license"]}},"scene":0,"scenes":[{"nodes":list(range(len(nodes)))}],"nodes":nodes,"meshes":meshes,"materials":[{"name":"city_context_1871_atlas","pbrMetallicRoughness":{"baseColorTexture":{"index":0},"metallicRoughnessTexture":{"index":2},"metallicFactor":0,"roughnessFactor":1},"normalTexture":{"index":1,"scale":.45},"occlusionTexture":{"index":2,"strength":.28}}],"textures":[{"sampler":0,"source":i} for i in range(3)],"samplers":[{"magFilter":9729,"minFilter":9987,"wrapS":33071,"wrapT":33071}],"images":images,"accessors":accessors,"bufferViews":views,"buffers":[{"byteLength":len(blob)}]}
    encoded=json.dumps(document,separators=(",",":"),ensure_ascii=False).encode()
    encoded+=b" "*((-len(encoded))%4); blob.extend(b"\0"*((-len(blob))%4))
    output=struct.pack("<III",0x46546c67,2,12+8+len(encoded)+8+len(blob))+struct.pack("<II",len(encoded),0x4e4f534a)+encoded+struct.pack("<II",len(blob),0x004e4942)+blob
    return output,stats,vegetation


def main():
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("--check",action="store_true"); args=ap.parse_args()
    recipe=json.loads(RECIPE.read_text())
    records = {}
    citation_ids = sorted(set(recipe.get("citation_sources", recipe["sources"])) | set(recipe["sources"]))
    for source_id in citation_ids:
        source=ROOT/"data/sources"/f"{source_id}.json"
        if not source.exists():
            raise SystemExit(f"Unregistered source: {source_id}")
        record=json.loads(source.read_text())
        records[source_id] = record
        if record.get("rights_status") in ("restricted","check_required"):
            raise SystemExit(f"Source not cleared for generated geometry: {source_id}")
    input_files = [RECIPE, Path(__file__), ROOT/"tools/compile_scene.py", ROOT/"tools/tiers.py", ROOT/"data/source.schema.json"] + [ROOT/"data/sources"/f"{sid}.json" for sid in citation_ids]
    input_hash = digest(canonical({p.relative_to(ROOT).as_posix(): digest(p.read_bytes()) for p in input_files}))
    data,templates,vegetation=glb(recipe)
    definition={"schema":"chicago-city-context-kit-v1","generated_by":"generators/city_context_emit.py","recipe":"context/1871/kit-recipe.json","glb":"context/1871/kit.glb","confidence":"reconstructed","sources":recipe["sources"],"source_limit":recipe["source_limit"],"license":recipe["license"],"coordinates":recipe["coordinates"],"input_sha256":input_hash,"citations":cite(citation_ids,records),"asset_sha256":digest(data),"asset_bytes":len(data),"templates":templates,"vegetation":vegetation,"vegetation_note":recipe.get("vegetation_note")}
    outputs={FOLDER/"kit.glb":data,FOLDER/"kit.json":canonical(definition)}
    for path,contents in outputs.items():
        if args.check:
            if not path.exists() or path.read_bytes()!=contents: raise SystemExit(f"Stale generated context kit: {path.relative_to(ROOT)}")
        else: path.write_bytes(contents)
    print(f"1871 context kit: {len(templates)} forms, {len(data):,} bytes; deterministic {'check passed' if args.check else 'build complete'}")


if __name__ == "__main__":
    main()
