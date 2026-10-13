#!/usr/bin/env python3
"""The Glessner house's opening schedule, read off its record (T-2211, T-2212).

Every street-face and stable-face opening the v4 generator draws, with its position
and height in the record's feet, the sash the generator gives it, and the sources and
confidence of the record entry it comes from. It is written from
data/structures/glessner_house.json and never by hand, so it cannot drift from what is
built: `--check` fails when the committed schedule differs from a fresh reading.

  python3 tools/glessner_opening_schedule.py           write the schedule
  python3 tools/glessner_opening_schedule.py --check   exit 1 if it is stale

T-2211 wrote the street and stable faces (docs/RESEARCH/glessner-windows-2211/);
T-2212 adds everything else — the courtyard faces, the hall bow, the dining bay and
its glazed band, the stair tower, the dormers and the bow terrace — to
docs/RESEARCH/glessner-windows-2212/. Both are written and checked together.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "data/structures/glessner_house.json"
OUT = ROOT / "docs/RESEARCH/glessner-windows-2211"
COURT_OUT = ROOT / "docs/RESEARCH/glessner-windows-2212"
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


def court_window(width_m: float, height_m: float, z1_m: float, pattern: str | None) -> str:
    """The sash masonry_house_v4_detail.opening draws on a courtyard face (T-2212)."""
    if width_m < .45 and height_m < .45:
        return "basement light, recessed glass"
    if min(width_m, height_m) < .45:
        lights = max(2, round(height_m / .55))
        return f"single sash, {lights} lights on horizontal bars, limestone sill"
    built = ("two-over-two" if pattern == "two_over_two" else "one-over-one") + \
        " double-hung, upper sash outside the lower, rock-faced limestone sill and lintel"
    if width_m > 1.7:
        built = "two " + built + ", on a mullion"
    if z1_m < 1.8:
        built += ", behind vertical iron bars"
    return built


def rows(courtyard: bool = False) -> list[dict]:
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
        if is_street(grp["face"], grp["at"]) == courtyard:
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
                if courtyard:
                    built = (court_window(light_w * FT, (z[1] - z[0]) * FT, z[1] * FT, it.get("sash"))
                             if kind == "window" else
                             "open passage, no panel" if kind == "dark" else
                             "panelled wood leaf" if kind in ("door", "doors") else sash(it))
                elif kind == "window" and not it.get("style") in ("stable_leaded",):
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
                    "transom_ft": it.get("transom"), "sash": it.get("sash"), "built_as": built,
                    "confidence": conf, "sources": sources,
                })
    if courtyard:
        for r in out:
            del r["transom_ft"]
        order = {"west": 0, "south": 1, "east": 2}
    else:
        for r in out:
            del r["sash"]
        order = {"east": 0, "north": 1, "west": 2}
    out.sort(key=lambda r: (order[r["face"]], r["at_ft"][0], r["z_ft"][0]))
    return out


def attr(form: dict, key: str) -> tuple[dict, str | None, list]:
    a = form.get(key, {})
    return a.get("value", {}) or {}, a.get("confidence"), a.get("sources", [])


def facet_rows() -> list[dict]:
    """The lights on curved and canted faces, and on the roof (T-2212).

    These are not positioned along a wall plane, so each row names its structure
    and its count; heights are the record's feet above north grade."""
    record = json.loads(RECORD.read_text())
    form = next(p for p in record["phases"] if p["id"] == "as_built_1887")["form"]
    v4, _, _ = attr(form, "v4_detail")
    out = []

    def add(where, rec, what, count, z, built, conf, sources):
        out.append({"where": where, "record": rec, "what": what, "count": count,
                    "z_ft": [round(float(z[0]), 3), round(float(z[1]), 3)] if z else None,
                    "built_as": built, "confidence": conf, "sources": sources})

    bow, conf, src = attr(form, "hall_bow_height")
    for i, row in enumerate(bow.get("light_rows", [])):
        n = int(bow.get("lights_per_row", 0))
        if i == 0 and v4.get("bow_first_floor_central_door"):
            add("hall bow", "hall_bow_height", "first-floor lights either side of the garden door", n - 1, row,
                "one-over-one double-hung on the curved face", conf, src)
            add("hall bow", "hall_bow_height", "garden door at the centre of the first floor", 1, row,
                "door: four glazed lights over a raised panel", conf, src)
        else:
            add("hall bow", "hall_bow_height", "second-floor lights" if i else "first-floor lights", n, row,
                "one-over-one double-hung on the curved face", conf, src)
    terrace = v4.get("bow_terrace") or {}
    if terrace.get("window_count"):
        add("bow terrace", "v4_detail", "garden-level lights in the terrace wall", terrace["window_count"],
            terrace["window_z"], "dark recessed light behind vertical iron bars", *attr(form, "v4_detail")[1:])
    bay, conf, src = attr(form, "bay_dining_elevation")
    outline = attr(form, "bay_dining")[0].get("outline", [])
    facets = sum(1 for p, q in zip(outline, outline[1:])
                 if ((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2) ** .5 * FT > 1.2)
    if bay.get("light_row"):
        add("dining bay", "bay_dining_elevation", "first-floor lights, one to each principal facet", facets,
            bay["light_row"], "one-over-one double-hung between rock-faced stone jambs", conf, src)
    garden = v4.get("dining_garden_window_z")
    if garden:
        add("dining bay", "v4_detail", "garden-level lights", len(v4.get("dining_garden_window_facets", [0, 2, 4])),
            garden, "dark recessed light behind vertical iron bars", *attr(form, "v4_detail")[1:])
    if bay.get("glazed_band_top"):
        add("dining bay", "bay_dining_elevation", "glazed band over the masonry storey, on every facet", None,
            [bay["wall_top"][0], bay["glazed_band_top"][0]],
            "fixed lights in two rows, a mullion about every 0.55 m", conf, src)
    tower = v4.get("tower_stair_windows") or {}
    tconf, tsrc = attr(form, "v4_detail")[1:]
    for s_ in tower.get("slits", []):
        add("stair tower", "v4_detail", f"slit at azimuth {s_['azimuth_deg']} degrees", 1, s_["z"],
            "single light in a flat frame with a meeting rail", tconf, tsrc)
    for s_ in tower.get("lantern", []):
        cols, rws = tower.get("lantern_panes", [1, 2])
        add("stair tower", "v4_detail", f"lantern light at azimuth {s_['azimuth_deg']} degrees", 1, s_["z"],
            f"fixed sash, {cols} x {rws} lights", tconf, tsrc)
    dorm, conf, src = attr(form, "dormers")
    if dorm.get("centres_S"):
        add("east wing courtyard slope", "dormers", "pyramid-roofed dormers, centres S " +
            ", ".join(f"{c:g}" for c in dorm["centres_S"]), len(dorm["centres_S"]),
            [dorm["light"][0][0], dorm["light"][1][0]], "one undivided light in a timber frame", conf, src)
    wd = v4.get("west_dormer")
    if wd:
        add("stable alley slope", "v4_detail", "hipped dormer with a flared hood", 1, None,
            "clear stable light (masonry_house_v4_west_fabric)", tconf, tsrc)
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


COURT_FACES = {"west": "East wing, courtyard face (looking east)",
               "south": "North range and stable, courtyard face (looking north)",
               "east": "Stable, courtyard face (looking west)"}


def court_markdown(data: list[dict], facets: list[dict]) -> str:
    lines = ["# Glessner house — courtyard, bow, bay, tower and dormer opening schedule (T-2212)", "",
             "GENERATED by `python3 tools/glessner_opening_schedule.py` from "
             "`data/structures/glessner_house.json`; do not edit. Positions are the record's feet "
             "along each courtyard face; heights are feet above the record's north-grade datum. "
             "*Built as* is the sash the v4 generator draws at the full tier (the light tier keeps "
             "one pane). Every source id resolves in `data/sources/`. The street and stable faces "
             "are T-2211's (`../glessner-windows-2211/opening-schedule.md`).", ""]
    for face in ("west", "south", "east"):
        rs = [r for r in data if r["face"] == face]
        lines += [f"## {COURT_FACES[face]} — {len(rs)} opening(s)", "",
                  "| at (ft) | z (ft) | built as | what | record · confidence |", "|---|---|---|---|---|"]
        for r in rs:
            lines.append(f"| {r['at_ft'][0]:g}–{r['at_ft'][1]:g} | {r['z_ft'][0]:g}–{r['z_ft'][1]:g} | "
                         f"{r['built_as']} | {r['what']} | `{r['record']}` · {r['confidence']} |")
        lines.append("")
    lines += [f"## Curved and canted faces, tower and roof — {len(facets)} row(s)", "",
              "| where | what | count | z (ft) | built as | record · confidence |", "|---|---|---|---|---|---|"]
    for r in facets:
        z = f"{r['z_ft'][0]:g}–{r['z_ft'][1]:g}" if r["z_ft"] else "—"
        lines.append(f"| {r['where']} | {r['what']} | {r['count'] if r['count'] is not None else 'band'} | {z} | "
                     f"{r['built_as']} | `{r['record']}` · {r['confidence']} |")
    lines += ["", "## Sources by record entry", ""]
    seen = {}
    for r in data + facets:
        seen.setdefault(r["record"], r["sources"])
    for a in sorted(seen):
        lines.append(f"- `{a}`: " + ", ".join(f"[`{s}`](../../../data/sources/{s}.json)" for s in seen[a]))
    missing = sorted({s for v in seen.values() for s in v if not (ROOT / "data/sources" / f"{s}.json").exists()})
    if missing:
        raise SystemExit("unresolved source id(s): " + ", ".join(missing))
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    data = rows()
    court, facets = rows(courtyard=True), facet_rows()
    files = {OUT / "opening-schedule.json": json.dumps(data, indent=1, ensure_ascii=False) + "\n",
             OUT / "opening-schedule.md": markdown(data),
             COURT_OUT / "opening-schedule.json": json.dumps({"courtyard": court, "facets": facets},
                                                             indent=1, ensure_ascii=False) + "\n",
             COURT_OUT / "opening-schedule.md": court_markdown(court, facets)}
    if "--check" in argv:
        stale = [p.name for p, text in files.items() if not p.exists() or p.read_text() != text]
        if stale:
            print("glessner opening schedule is stale: " + ", ".join(stale) +
                  " — run python3 tools/glessner_opening_schedule.py")
            return 1
        print(f"glessner opening schedule: ok ({len(data)} street/stable openings, "
              f"{len(court)} courtyard openings, {len(facets)} bow/bay/tower/dormer rows)")
        return 0
    for p, text in files.items():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    print(f"wrote {len(data)} street/stable openings to {OUT.relative_to(ROOT)}/opening-schedule.{{md,json}}")
    print(f"wrote {len(court)} courtyard openings and {len(facets)} bow/bay/tower/dormer rows to "
          f"{COURT_OUT.relative_to(ROOT)}/opening-schedule.{{md,json}}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
