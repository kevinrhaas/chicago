#!/usr/bin/env python3
"""Render retained 1871 plan pixels over the original Mitchell scan.

No coordinates are inferred or reprojected. Watercourses without retained source
pixels are listed as omitted. Run with --check to detect a stale plan or raster.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PLAN = ROOT.parent / "4d/data/context/1871/plan.json"
DEFAULT_OUTPUT = ROOT / "viewer/geography-features-1871.svg"
RASTER_URL = "../maps/images/1870_mitchell_map.jpg"


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def points(raw: list, width: int, height: int) -> list:
    if not isinstance(raw, list) or len(raw) < 2:
        raise ValueError("A retained line needs at least two source-pixel vertices")
    for point in raw:
        if not isinstance(point, list) or len(point) != 2:
            raise ValueError(f"Invalid source-pixel vertex: {point!r}")
        x, y = point
        if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in point):
            raise ValueError(f"Invalid source-pixel coordinates: {point!r}")
        if not (0 <= x <= width and 0 <= y <= height):
            raise ValueError(f"Source-pixel vertex outside the raster: {point!r}")
    return raw


def path_data(vertices: list, closed: bool = False) -> str:
    return "M " + " L ".join(f"{x},{y}" for x, y in vertices) + (" Z" if closed else "")


def build(plan_path: Path) -> str:
    raw = plan_path.read_bytes()
    plan = json.loads(raw)
    control = plan["map_control"]
    width, height = int(control["width"]), int(control["height"])
    raster = (plan_path.resolve().parents[3] / control["raster"]).resolve()
    raster_hash = hashlib.sha256(raster.read_bytes()).hexdigest()
    if raster_hash != control["sha256"]:
        raise ValueError("The Mitchell raster does not match the plan's recorded SHA-256")
    plan_hash = hashlib.sha256(raw).hexdigest()
    top = 300
    rows = math.ceil(len(plan["bridges"]) / 3)
    footer = top + height
    total_height = footer + 220 + rows * 43
    labels = {
        "waterway": ("#00718c", "14 7", "Watercourse centreline; width omitted"),
        "coast": ("#b74b16", "", "Outer shoreline / lake edge"),
        "lagoon": ("#7035a4", "9 5", "Lagoon water envelope"),
        "park": ("#237542", "18 7", "Park / cemetery outline"),
    }
    features = []
    omitted = []
    for record in plan["rivers"]:
        if record.get("source_pixels"):
            features.append(("waterway", record["id"], record.get("name", record["id"].replace("_", " ")), record["source_pixels"], False))
        else:
            omitted.append(record.get("name", record["id"].replace("_", " ")))
    features.append(("coast", "outer_shoreline", "Outer shoreline / lake edge", plan["shoreline_source_pixels"], False))
    for key, kind in [("water_polygons", "lagoon"), ("parks", "park")]:
        for record in plan[key]:
            features.append((kind, record["id"], record.get("name", record["id"].replace("_", " ")), record["source_pixels"], True))
    provenance = {
        "plan_path": "chicago/4d/data/context/1871/plan.json",
        "plan_sha256": plan_hash,
        "raster_url": RASTER_URL,
        "raster_sha256": raster_hash,
        "scene_date": plan["date"],
        "method": "Exact retained source_pixels and shoreline_source_pixels; no fitting, inverse projection, width buffer or inferred geometry in this overlay.",
        "feature_counts": {kind: sum(f[0] == kind for f in features) for kind in labels},
        "bridge_count": len(plan["bridges"]),
        "report_tabulated_bridge_count": sum(b.get("report_table_entry") is not False for b in plan["bridges"]),
        "map_only_crossing_count": sum(b.get("report_table_entry") is False for b in plan["bridges"]),
        "omitted_without_retained_pixels": omitted,
    }
    out = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {total_height}" width="{width}" height="{total_height}" role="group" aria-labelledby="title description">',
        '<title id="title">Chicago 1871: retained terrain readings on the original 1870 Mitchell map</title>',
        '<desc id="description">Source-pixel lines show watercourse centrelines, the outer lake edge, lagoon and park or cemetery outlines. Numbered circles mark retained bridge locations. These are generalized plan readings, not surveyed banks, bridge footprints or evidence of an exact October 1871 shoreline. The full original scan remains visible.</desc>',
        f'<metadata id="provenance">{esc(json.dumps(provenance, ensure_ascii=False, indent=2))}</metadata>',
        '<style>text{font-family:system-ui,sans-serif;fill:#17231f}.heading{font-size:43px;font-weight:750}.note{font-size:24px}.legend{font-size:25px}.bridge-label{font-size:24px;font-weight:800;fill:#af2925;stroke:white;stroke-width:4px;paint-order:stroke}.bridge-name{font-size:24px}.bridge-name:target{font-weight:800;fill:#af2925}a:focus-visible circle{stroke:#17231f;stroke-width:5px}</style>',
        f'<rect width="{width}" height="{total_height}" fill="#f5f2e9"/>',
        '<text x="38" y="60" class="heading">Read the terrain against Mitchell’s 1870 map</text>',
        '<text x="38" y="104" class="note">Retained source-pixel readings from the 1871 city plan. These generalized lines do not establish surveyed banks.</text>',
        '<text x="38" y="143" class="note">Bridge symbols mark positions, not span length or structure form. Use browser zoom to inspect the original ink.</text>',
    ]
    for i, (kind, (color, dash, label)) in enumerate(labels.items()):
        x = 40 + (i % 2) * 1180
        y = 185 + (i // 2) * 42
        out.append(f'<path d="M {x},{y-7} h 68" fill="none" stroke="{color}" stroke-width="5" stroke-dasharray="{dash or "none"}"/><text x="{x+83}" y="{y}" class="legend">{esc(label)}</text>')
    out.append('<circle cx="74" cy="262" r="9" fill="#af2925" stroke="white" stroke-width="3"/><text x="123" y="269" class="legend">Bridge points · numbered; not span footprints</text>')
    if provenance["map_only_crossing_count"]:
        out.append('<circle cx="1254" cy="262" r="9" fill="white" stroke="#af2925" stroke-width="3"/><text x="1303" y="269" class="legend">Open circle: map-attested span outside the report table</text>')
    out.append(f'<g transform="translate(0 {top})">')
    out.append(f'<image href="{RASTER_URL}" x="0" y="0" width="{width}" height="{height}"/>')
    for kind, feature_id, name, raw_points, closed in features:
        vertices = points(raw_points, width, height)
        color, dash, label = labels[kind]
        d = path_data(vertices, closed)
        out.append(f'<g id="feature-{esc(feature_id)}" class="feature {kind}" role="group" aria-label="{esc(name)}: {esc(label)}"><title>{esc(name)} — {esc(label)}; retained source-pixel reading</title>')
        out.append(f'<path d="{d}" fill="none" stroke="white" stroke-width="7" stroke-opacity="0.78" stroke-dasharray="{dash or "none"}"/>')
        out.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="4" stroke-dasharray="{dash or "none"}"/>')
        out.append('</g>')
    for i, bridge in enumerate(plan["bridges"], 1):
        point = bridge["source_pixels"]
        points([point, point], width, height)
        x, y = point
        name = bridge["name"]
        map_only = bridge.get("report_table_entry") is False
        basis = "; map-attested crossing outside the municipal report table" if map_only else "; report-tabulated bridge"
        fill, stroke = ("white", "#af2925") if map_only else ("#af2925", "white")
        out.append(f'<a class="bridge" href="#bridge-{esc(bridge["id"])}" aria-label="{i}. {esc(name)}"><title>{i}. {esc(name)} — retained point at pixel {x}, {y}{esc(basis)}; not a surveyed footprint</title><circle cx="{x}" cy="{y}" r="8" fill="{fill}" stroke="{stroke}" stroke-width="3"/><text x="{x+13}" y="{y-10}" class="bridge-label">{i}</text></a>')
    out.append('</g>')
    out.append(f'<text x="38" y="{footer+48}" class="heading">{len(plan["bridges"])} crossing locations</text>')
    out.append(f'<text x="38" y="{footer+90}" class="note">Public-domain original scan: S. Augustus Mitchell, 1870; University of Illinois via Wikimedia Commons.</text>')
    for i, bridge in enumerate(plan["bridges"]):
        x = 38 + (i // rows) * 790
        y = footer + 140 + (i % rows) * 43
        out.append(f'<text id="bridge-{esc(bridge["id"])}" x="{x}" y="{y}" class="bridge-name">{i+1}. {esc(bridge["name"])}</text>')
    y = footer + 165 + rows * 43
    out.append(f'<text x="38" y="{y}" class="note">Not drawn without retained pixels: {esc(", ".join(omitted)) or "none"}. No reconstructed river widths are shown.</text>')
    out.append(f'<a href="geography.html"><text x="38" y="{y+40}" class="note" text-decoration="underline">Return to the geography audit</text></a>')
    out.append('</svg>')
    return "\n".join(out) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true", help="fail if the checked-in SVG differs from the plan or source raster")
    args = parser.parse_args()
    result = build(args.plan)
    if args.check:
        if not args.output.exists() or args.output.read_text() != result:
            print("STALE: geography-features-1871.svg differs from the current plan. Run tools/build_geography_overlay.py.")
            return 1
        print("geography-features-1871.svg is current")
        return 0
    args.output.write_text(result)
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
