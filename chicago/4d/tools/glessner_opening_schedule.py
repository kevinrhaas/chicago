#!/usr/bin/env python3
"""The Glessner house's street and stable opening schedule, read off its record (T-2211).

Every street-face and stable-face opening the v4 generator draws, with its position
and height in the record's feet, the sash the generator gives it, and the sources and
confidence of the record entry it comes from. It is written from
data/structures/glessner_house.json and never by hand, so it cannot drift from what is
built: `--check` fails when the committed schedule differs from a fresh reading.

  python3 tools/glessner_opening_schedule.py           write the schedule
  python3 tools/glessner_opening_schedule.py --check   exit 1 if it is stale

Courtyard, dormer and turret openings are T-2212's schedule, not this one.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "data/structures/glessner_house.json"
OUT = ROOT / "docs/RESEARCH/glessner-windows-2211"
FT = 0.3048
# Street and stable faces: the Prairie front (east, at 0), 18th Street (north) and the
# alley (west, at 161.25). Everything else on this record faces a courtyard.
STREET = {("east", 0.0), ("west", 161.25)}


def is_street(face: str, at: float) -> bool:
    return face == "north" or (face, float(at)) in STREET


def sash(item: dict) -> str:
    """The sash masonry_house_v4_detail.opening draws for this item."""
    kind, style = item.get("kind", "window"), item.get("style", "")
    if style == "gable_slit":
        return ("round-headed fixed light, stone transom, one-over-one sash"
                if item.get("transom") else "arched slot")
    if style == "pigeon_vent":
        return "open pigeon hole"
    if style == "stable_leaded":
        return "leaded stable light"
    if kind in ("door", "doors"):
        return {"porte_cochere": "two oak leaves", "prairie_front_door": "oak door, glazed upper leaf",
                "service_door": "boarded door", "stable_carriage_doors": "two glazed-over-board leaves"
                }.get(style, kind)
    if kind == "arch":
        return "open arch"
    if kind == "dark":
        return "open loft, leaves stood inward"
    if kind in ("band", "fan"):
        return "carved stone (" + kind + ")"
    return ""


def window_sash(width_m: float, height_m: float, grid: bool) -> str:
    if grid or (width_m < .45 and height_m < .45):
        return "basement grille light, recessed glass"
    if min(width_m, height_m) < .45:
        lights = max(2, round(height_m / .55))
        return f"single sash, {lights} lights on horizontal bars"
    if width_m > 1.7:
        return "two one-over-one double-hung units on a mullion"
    return "one-over-one double-hung, upper sash outside the lower"


def rows() -> list[dict]:
    record = json.loads(RECORD.read_text())
    phase = next(p for p in record["phases"] if p["id"] == "as_built_1887")
    form = phase["form"]
    heights = form.get("opening_heights", {}).get("value", {})
    groups = [(k, form[k]["value"], form[k].get("confidence"), form[k].get("sources", []))
              for k in form if k.startswith("openings_")]
    v4 = form.get("v4_detail", {})
    groups += [("v4_detail", g, v4.get("confidence"), v4.get("sources", []))
               for g in v4.get("value", {}).get("supplemental_openings", [])]
    out = []
    for attr, grp, conf, sources in groups:
        if not is_street(grp["face"], grp["at"]):
            continue
        for it in grp["items"]:
            spans = it["at"]
            if spans and not isinstance(spans[0], (list, tuple)):
                spans = [spans]
            if "z" in it:
                z, zfrom = it["z"], "item"
            else:
                z, zfrom = heights.get(attr, {}).get(it.get("row", "")), "opening_heights." + it.get("row", "")
            lights = int(it.get("lights", 1))
            mull = float(it.get("mullion_ft", 0.6))
            for a, b in spans:
                width = abs(b - a)
                light_w = (width - mull * (lights - 1)) / lights if lights > 1 else width
                kind = it.get("kind", "window")
                if kind == "window" and not it.get("style") in ("stable_leaded",):
                    built = window_sash(light_w * FT, (z[1] - z[0]) * FT, bool(it.get("grid")))
                    if it.get("grid"):
                        built = f"{it['grid'][0]} x {it['grid'][1]} " + built
                else:
                    built = sash(it)
                out.append({
                    "face": grp["face"], "record": attr, "what": it.get("what", ""),
                    "at_ft": [round(min(a, b), 3), round(max(a, b), 3)],
                    "z_ft": [round(z[0], 3), round(z[1], 3)], "z_from": zfrom,
                    "lights": lights, "kind": kind, "style": it.get("style"),
                    "transom_ft": it.get("transom"), "built_as": built,
                    "confidence": conf, "sources": sources,
                })
    order = {"east": 0, "north": 1, "west": 2}
    out.sort(key=lambda r: (order[r["face"]], r["at_ft"][0], r["z_ft"][0]))
    return out


FACES = {"east": "Prairie Avenue front (east)", "north": "18th Street (north), house and stable",
         "west": "Alley (west), stable"}


def markdown(data: list[dict]) -> str:
    lines = ["# Glessner house — street and stable opening schedule (T-2211)", "",
             "GENERATED by `python3 tools/glessner_opening_schedule.py` from "
             "`data/structures/glessner_house.json`; do not edit. Positions are the record's feet "
             "along each face (S from the south end of the Prairie front, W from its east end on "
             "18th Street and the alley); heights are feet above the record's ground datum. "
             "*Built as* is the sash the v4 generator draws. Every source id resolves in "
             "`data/sources/`. Courtyard, dormer and turret openings are T-2212's.", ""]
    used = sorted({s for r in data for s in r["sources"]})
    for face in ("east", "north", "west"):
        rs = [r for r in data if r["face"] == face]
        lines += [f"## {FACES[face]} — {len(rs)} opening(s)", "",
                  "| at (ft) | z (ft) | lights | built as | what | record · confidence |",
                  "|---|---|---|---|---|---|"]
        for r in rs:
            z = f"{r['z_ft'][0]:g}–{r['z_ft'][1]:g}"
            if r["transom_ft"]:
                z += f" (transom {r['transom_ft'][0]:g}–{r['transom_ft'][1]:g})"
            lines.append(f"| {r['at_ft'][0]:g}–{r['at_ft'][1]:g} | {z} | {r['lights']} | {r['built_as']} | "
                         f"{r['what']} | `{r['record']}` · {r['confidence']} |")
        lines.append("")
    lines += ["## Sources by record entry", ""]
    for attr in sorted({r["record"] for r in data}):
        srcs = next(r["sources"] for r in data if r["record"] == attr)
        lines.append(f"- `{attr}`: " + ", ".join(f"[`{s}`](../../../data/sources/{s}.json)" for s in srcs))
    missing = [s for s in used if not (ROOT / "data/sources" / f"{s}.json").exists()]
    if missing:
        raise SystemExit("unresolved source id(s): " + ", ".join(missing))
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    data = rows()
    files = {OUT / "opening-schedule.json": json.dumps(data, indent=1, ensure_ascii=False) + "\n",
             OUT / "opening-schedule.md": markdown(data)}
    if "--check" in argv:
        stale = [p.name for p, text in files.items() if not p.exists() or p.read_text() != text]
        if stale:
            print("glessner opening schedule is stale: " + ", ".join(stale) +
                  " — run python3 tools/glessner_opening_schedule.py")
            return 1
        print(f"glessner opening schedule: ok ({len(data)} street/stable openings)")
        return 0
    OUT.mkdir(parents=True, exist_ok=True)
    for p, text in files.items():
        p.write_text(text)
    print(f"wrote {len(data)} street/stable openings to {OUT.relative_to(ROOT)}/opening-schedule.{{md,json}}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
