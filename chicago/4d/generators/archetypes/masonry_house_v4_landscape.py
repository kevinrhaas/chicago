"""Bounded, reconstructed turf microgeometry for the opt-in Glessner v4 model.

The existing record supplies the lawn and drive polygons and their elevations.
No planting bed, tree, or ground extent is invented here. Seeded clumps of short
grass supplement the turf texture, rather than claiming individual historic
blades. Each blade is one slender tapered triangle, 10–40 mm high and 1–3 mm
wide. The entire structure is capped at 20,000 blades/triangles and three plain
green material slots (25–27); all vertices carry reconstructed confidence 1.0.

Call add_lawn_blades(builder, params) after the record's ground surfaces are
emitted. The builder only needs raw(points, confidence, material).
"""
from __future__ import annotations

import math
import random

MAX_BLADES = 20_000
MATERIAL_SLOTS = (25, 26, 27)
BOUNDARY_MARGIN_M = 0.025


def _inside(point, polygon):
    x, y = point
    inside = False
    for a, b in zip(polygon, polygon[1:] + polygon[:1]):
        if (a[1] > y) != (b[1] > y):
            cross_x = a[0] + (y - a[1]) * (b[0] - a[0]) / (b[1] - a[1])
            if x < cross_x:
                inside = not inside
    return inside


def _edge_distance(point, polygon):
    x, y = point
    distance = math.inf
    for a, b in zip(polygon, polygon[1:] + polygon[:1]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        length2 = dx * dx + dy * dy
        t = max(0.0, min(1.0, ((x - a[0]) * dx + (y - a[1]) * dy) / length2)) if length2 else 0
        distance = min(distance, math.hypot(x - a[0] - t * dx, y - a[1] - t * dy))
    return distance


def _usable(point, lawn, exclusions, margin):
    return (_inside(point, lawn) and _edge_distance(point, lawn) >= margin
            and all(not _inside(point, polygon) and _edge_distance(point, polygon) >= margin
                    for polygon in exclusions))


def add_lawn_blades(builder, params, max_blades=MAX_BLADES, seed=18871904):
    """Append deterministic one-triangle blades; return their actual count.

    The lawn polygon overlaps the carriage drive in the source ground model.
    Explicitly excluding non-lawn surfaces prevents blades piercing that drive.
    Both roots and tips are checked, including a 25 mm boundary clearance.
    """
    if not 0 <= max_blades <= MAX_BLADES:
        raise ValueError(f"Grass blade budget must be between 0 and {MAX_BLADES}")
    lawns = [g for g in params.ground if g["kind"] == "lawn" and len(g["pts"]) >= 3]
    exclusions = [list(g["pts"]) for g in params.ground if g["kind"] != "lawn"]
    if not lawns or not max_blades:
        return 0
    bounds = []
    for ground in lawns:
        polygon = list(ground["pts"])
        x0, y0 = min(p[0] for p in polygon), min(p[1] for p in polygon)
        x1, y1 = max(p[0] for p in polygon), max(p[1] for p in polygon)
        bounds.append((ground, polygon, x0, y0, x1, y1))
    weights = [(entry[4] - entry[2]) * (entry[5] - entry[3]) for entry in bounds]
    rng = random.Random(seed)
    count = 0
    for _ in range(max_blades * 4):
        ground, polygon, x0, y0, x1, y1 = rng.choices(bounds, weights=weights, k=1)[0]
        cx, cy = rng.uniform(x0, x1), rng.uniform(y0, y1)
        if not _usable((cx, cy), polygon, exclusions, 0.05):
            continue
        radius = rng.uniform(0.025, 0.12)
        clump_direction = rng.uniform(0, 2 * math.pi)
        for _ in range(rng.randint(6, 14)):
            x, y = cx + rng.gauss(0, radius * 0.45), cy + rng.gauss(0, radius * 0.45)
            if not _usable((x, y), polygon, exclusions, 0.05):
                continue
            angle = clump_direction + rng.uniform(-1.6, 1.6)
            width = rng.uniform(0.001, 0.003)
            height = rng.triangular(0.01, 0.04, 0.022)
            bend = rng.uniform(-0.38, 0.38) * height
            dx, dy = math.cos(angle) * width / 2, math.sin(angle) * width / 2
            z = ground["lift_m"] + 0.0001
            points = [(x - dx, y - dy, z), (x + dx, y + dy, z),
                      (x - math.sin(angle) * bend, y + math.cos(angle) * bend, z + height)]
            if not all(_usable(p[:2], polygon, exclusions, BOUNDARY_MARGIN_M) for p in points):
                continue
            material = rng.choices(MATERIAL_SLOTS, weights=(2, 5, 3), k=1)[0]
            builder.raw(points, 1.0, material)
            count += 1
            if count >= max_blades:
                return count
    return count
