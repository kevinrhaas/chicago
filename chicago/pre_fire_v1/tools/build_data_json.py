#!/usr/bin/env python3
"""Regenerate viewer/data.json from the CSVs.

The viewer reads one pre-flattened JSON rather than eight CSVs, so that file is
build output — but it used to be maintained by hand, which meant every CSV edit
risked silently diverging from what the viewer actually showed. This script makes
the CSVs the single source of truth.

    python3 tools/build_data_json.py           regenerate
    python3 tools/build_data_json.py --check   fail if the committed file is stale

Run from the pre_fire_v1 directory.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "viewer" / "data.json"

# csv path -> key in data.json
TABLES = {
    "data/buildings.csv": "buildings",
    "maps/map_references.csv": "maps",
    "maps/city_extent_events.csv": "cityExtentEvents",
    "maps/landform_events.csv": "landformEvents",
    "data/building_names.csv": "names",
    "data/media.csv": "media",
    "data/media_buildings.csv": "mediaBuildings",
}

# The viewer only needs these columns; carrying the rest bloats the payload the
# browser downloads without changing what it renders.
COLUMNS = {
    "buildings": ["building_id", "canonical_name", "year_started", "year_completed",
                  "year_demolished", "status", "address_historical", "latitude", "longitude",
                  "building_type", "fire_fate_1871", "confidence", "needs_review"],
    "names": ["building_name_id", "building_id", "name", "name_type", "sequence"],
}


def read(rel: str) -> list[dict]:
    p = ROOT / rel
    if not p.exists():
        print(f"  missing: {rel}", file=sys.stderr)
        return []
    with p.open(newline="") as f:
        rows = list(csv.DictReader(f))
    # strip a UTF-8 BOM off the first header if present
    return [{(k.lstrip("﻿") if k else k): v for k, v in r.items()} for r in rows]


def count_period(year: str) -> str | None:
    try:
        y = int(str(year)[:4])
    except (ValueError, TypeError):
        return None
    if y < 1830:
        return "pre-1830"
    if y < 1840:
        return "1830s"
    if y < 1850:
        return "1840s"
    if y < 1860:
        return "1850s"
    if y < 1870:
        return "1860s"
    return "1870s"


def fire_fate_class(raw: str) -> str:
    """Classify the free-text fire_fate_1871 column.

    The column was written by hand across several research tranches and holds
    thirty-odd phrasings of about five ideas ('destroyed', 'destroyed in Great
    Chicago Fire, 1871', 'probably destroyed', 'not established', ...). These
    rules reproduce the counts the dataset has always reported; keep them in
    sync if new phrasings appear.
    """
    v = (raw or "").strip().lower()
    if not v:
        return "other"
    if v.startswith("probably"):
        return "probable"
    if "not applicable" in v or "damaged" in v:
        return "other"
    if "destroyed" in v:
        return "documented_loss"
    if (v in ("unknown", "uncertain", "not established")
            or "unresolved" in v
            or "survival not established" in v
            or v == "no-destruction-reported"):
        return "unresolved"
    return "other"


def build() -> dict:
    data: dict = {}
    for rel, key in TABLES.items():
        rows = read(rel)
        cols = COLUMNS.get(key)
        data[key] = [{c: r.get(c, "") for c in cols} for r in rows] if cols else rows

    sources = read("data/sources.csv")
    bsources = read("data/building_sources.csv")
    assertions = read("data/assertions.csv")

    buildings = data["buildings"]
    media = data["media"]
    linked = {m["building_id"] for m in data["mediaBuildings"] if m.get("building_id")}

    periods = Counter()
    for b in buildings:
        p = count_period(b.get("year_completed") or b.get("year_started"))
        if p:
            periods[p] += 1

    fates = Counter(fire_fate_class(b.get("fire_fate_1871", "")) for b in buildings)

    data["statistics"] = {
        "generated_from_files": sorted(TABLES) + ["data/sources.csv",
                                                  "data/building_sources.csv",
                                                  "data/assertions.csv"],
        "building_or_structure_records": len(buildings),
        "source_records": len(sources),
        "building_source_links": len(bsources),
        "field_level_assertions": len(assertions),
        "map_references": len(data["maps"]),
        "local_map_images": sum(1 for m in data["maps"] if m.get("local_image_path")),
        "media_records": len(media),
        "building_media_assets": sum(1 for m in media
                                     if "images/buildings" in (m.get("local_path") or "")),
        "building_media_links": len(data["mediaBuildings"]),
        "buildings_with_media": len(linked),
        "geocoded_records": sum(1 for b in buildings if (b.get("latitude") or "").strip()),
        "needs_review_records": sum(1 for b in buildings
                                    if str(b.get("needs_review", "")).strip().lower()
                                    in ("true", "yes", "1")),
        "documented_or_asserted_1871_fire_losses": fates.get("documented_loss", 0),
        "probable_1871_fire_losses": fates.get("probable", 0),
        "unresolved_1871_fire_fates": fates.get("unresolved", 0),
        "records_by_period": dict(sorted(periods.items())),
        "records_by_confidence": dict(sorted(Counter(
            b.get("confidence", "") for b in buildings).items())),
    }
    return data


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="fail if the committed data.json differs from a fresh build")
    args = ap.parse_args()

    data = build()
    text = json.dumps(data, indent=1, ensure_ascii=False) + "\n"

    if args.check:
        current = OUT.read_text() if OUT.exists() else ""
        if current != text:
            print("STALE: viewer/data.json does not match the CSVs. "
                  "Run tools/build_data_json.py.", file=sys.stderr)
            return 1
        print("data.json is current")
        return 0

    OUT.write_text(text)
    s = data["statistics"]
    print(f"wrote {OUT.relative_to(ROOT)}  "
          f"{s['building_or_structure_records']} buildings · {s['media_records']} media · "
          f"{s['building_media_links']} media links · {s['buildings_with_media']} buildings with media")
    return 0


if __name__ == "__main__":
    sys.exit(main())
