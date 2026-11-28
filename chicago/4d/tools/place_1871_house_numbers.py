#!/usr/bin/env python3
"""Place the 1871 city's house numbers: each named building whose 1871 street number is read
shows it on its front door (T-3738).

    python3 tools/place_1871_house_numbers.py              # write data/house_numbers/1871.json
    python3 tools/place_1871_house_numbers.py --check      # the committed file is what this writes
    python3 tools/place_1871_house_numbers.py --self-test  # each fault the check refuses, planted

The owner, 2026-11-23 (thread "Add period street numbers to buildings"): "yes start with 1904, the
other years can come later, you can add tickets for the other years for later to the queue". T-3737
drew 1904's; this is 1871's, on the same atlas and layer (renderers/web/js/house-numbers.js).

WHICH NUMBERS. Chicago's houses were numbered by 1871, on the old system the 1909-11 renumbering
replaced. A number is shown only where the building's OWN record reads it from a source: its
`placement.symbolic_location` opens with the figures ("137 DeKoven Street, north side ...") and the
placement cites its sources. In the 1871 scene that is the four houses of DeKoven Street the fire
began among: the O'Learys' at No. 137 (Mountford's stereograph card prints "No. 137 DeKoven St.",
and Andreas gives it), the Forbes house at No. 133 and Dennis Sullivan's at No. 134 (Andreas vol. 2,
pp. 708-712), all `attested`; and Dalton's cottage, which its record places at 135, next east of the
O'Learys, between the printed 133 and 137 (`inferred`: no source read prints "No. 135"). Those are the old numbers (the O'Leary lot is 558 W. DeKoven today). The downtown
landmarks are known by name and corner in every source read for them (the Sherman House at Clark
and Randolph, the Tremont at Lake and Dearborn ...), and no number for any of them is read, so
they show none; nor do the context city's unnamed fronts, whose numbers are nobody's reading.

THE FORM. No picture of any of the three fronts is read with its number on it: Mountford's card
looks at the O'Leary cottages from the burnt lots behind them. So the form is reconstructed
(docs/LIBERTIES.md L-1871-house-numbers-3738): painted figures on the front door's top rail,
about 4 in high, as on a door without a transom in 1904's rule (T-3737), in white paint, a Roman
or a block letter dealt per house by a stable hash of its id.

HOW THE DOOR IS FOUND. As T-3737 finds it (tools/place_prairie_1904_house_numbers.py `doors_of`),
from the structure's own baked model, its door material counted as a leaf: the front door is the
one whose plane faces the street its record names, nearest to that street.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import place_prairie_1904_house_numbers as H  # noqa: E402

ROOT = H.ROOT
SCENE = ROOT / "data" / "scenes" / "1871.json"
SIDECARS = ROOT / "data" / "sidecars" / "1871"
CONTEXT = ROOT / "data" / "context" / "1871.json"
OUT = ROOT / "data" / "house_numbers" / "1871.json"
LIBERTY = "L-1871-house-numbers-3738"
TICKET = "T-3738"
# The 1871 models' door leaves are in a plain `door` material; T-3737's kits name theirs otherwise.
DOOR_MATS = tuple(H.DOOR_MATS) + ("door",)
FACE_COS = H.FACE_COS
FRONT_REACH_M = 30.0
LEAF_FIG_M = H.LEAF_FIG_M
NUMBER_RE = re.compile(r"\s*(\d{1,4})\s+((?:[NSEW]\.\s+)?[A-Z][A-Za-z.' ]*?(?:Street|Avenue|Place|Court))\b")
HANDS = {k: H.HANDS[k] for k in ("white_roman", "white_block")}


def hand_of(sid: str) -> str:
    keys = sorted(HANDS)
    return keys[int(hashlib.sha256(sid.encode()).hexdigest(), 16) % len(keys)]


def read_number(sc: dict):
    """(number, street, sources) from a structure's own placement, or None."""
    pl = sc.get("placement") or {}
    m = NUMBER_RE.match(pl.get("symbolic_location") or "")
    src = [s for s in pl.get("position_sources") or [] if s]
    if not m or not src:
        return None
    return m.group(1), m.group(2).strip(), src


def street_lines(ctx: dict) -> dict:
    out: dict[str, list] = {}
    for s in ctx["streets"]:
        if s.get("name"):
            out.setdefault(s["name"].lower(), []).append((s["a"], s["b"]))
    return out


def scene_sidecars() -> list[dict]:
    ids = json.loads(SCENE.read_text())["structure_ids"]
    return [json.loads((SIDECARS / f"{sid}.json").read_text()) for sid in ids if (SIDECARS / f"{sid}.json").exists()]


def number_printed(sid: str, number: str, sources: list) -> str | None:
    """Where 'No. <number>' is printed: the record's own reading of its source, or a source's citation."""
    rec = ROOT / "data" / "structures" / f"{sid}.json"
    if rec.exists() and re.search(rf"\bNo\. {number}\b", rec.read_text()):
        return f"data/structures/{sid}.json's reading of {', '.join(sorted(sources))}"
    for src in sorted(sources):
        p = ROOT / "data" / "sources" / f"{src}.json"
        if p.exists() and re.search(rf"\bNo\. {number}\b", json.loads(p.read_text()).get("citation", "")):
            return src
    return None


def place(sidecars=None):
    H.DOOR_MATS = DOOR_MATS   # doors_of reads the module's tuple
    streets = street_lines(json.loads(CONTEXT.read_text()))
    tracked = H.tracked_models()
    found, skipped = [], []
    for sc in sidecars if sidecars is not None else scene_sidecars():
        sid, pl = sc.get("id"), sc.get("placement") or {}
        if "asset" not in sc or pl.get("local_e") is None:
            continue   # grounds, squares and sands: no door
        read = read_number(sc)
        if not read:
            skipped.append({"structure": sid, "why": "no 1871 street number is read for it: its sources give it by name and place"})
            continue
        number, street, sources = read
        lines = streets.get(street.lower())
        glb = H.ASSETS / sc["asset"]
        if not lines or f"assets/{sc['asset']}" not in tracked or not glb.exists():
            skipped.append({"structure": sid, "why": f"its street ({street}) or its model is not in the scene"})
            continue
        best = None
        for d in H.doors_of(H.read_glb(glb)):
            mid = (d["lo"] + d["hi"]) / 2
            c = H.to_enu(pl, mid[0], mid[2])
            # the way to the street: the nearest point of its nearest segment
            a, b = min(lines, key=lambda ab: H.seg_dist(c, *ab)[0])
            dist = H.seg_dist(c, a, b)[0]
            dx, dy = b[0] - a[0], b[1] - a[1]
            L2 = dx * dx + dy * dy or 1.0
            t = max(0.0, min(1.0, ((c[0] - a[0]) * dx + (c[1] - a[1]) * dy) / L2))
            q = (a[0] + t * dx, a[1] + t * dy)
            if dist > FRONT_REACH_M:
                continue
            to_st = ((q[0] - c[0]) / (dist or 1), (q[1] - c[1]) / (dist or 1))
            nrm = (1.0, 0.0) if d["axis"] == 0 else (0.0, 1.0)
            ne = H.dir_to_enu(pl, *nrm)
            cos = ne[0] * to_st[0] + ne[1] * to_st[1]
            if abs(cos) < FACE_COS:
                continue
            if not best or dist < best[0]:
                best = (dist, d, 1 if cos > 0 else -1)
        if not best:
            skipped.append({"structure": sid, "why": f"its model has no door facing {street}"})
            continue
        _, d, outward = best
        ax, lat = d["axis"], 2 - d["axis"]
        lo, hi = d["lo"], d["hi"]
        n = [0.0, 0.0, 0.0]
        n[ax] = float(outward)
        tr = H.transom(d, outward)
        if tr:
            foot, head, face, l0, l1 = tr
            h = min(H.FIG_MAX_M, max(H.FIG_MIN_M, H.FIG_SHARE * HANDS[hand_of(sid)]["scale"] * (head - foot)))
            y, mid_lat, form = (foot + head) / 2, (l0 + l1) / 2, "transom"
        else:
            plane = d["pts"][:, ax]
            face = float(plane.max() if outward > 0 else plane.min())
            h, y = LEAF_FIG_M, float(hi[1]) - H.LEAF_RAIL_DROP_M
            mid_lat, form = float((lo[lat] + hi[lat]) / 2), "leaf"
        p = [0.0, 0.0, 0.0]
        p[ax] = face + outward * H.PROUD_M
        p[lat] = mid_lat
        p[1] = y
        printed = number_printed(sid, number, sources)
        found.append({
            "structure": sid, "street": street, "number": number,
            "at": [H.r3(v) for v in p], "normal": [H.r3(v) for v in n], "height_m": H.r3(h), "form": form,
            "hand": hand_of(sid), "grade": "reconstructed", "number_grade": "attested" if printed else "inferred",
            "sources": sorted(set(sources)),
            "note": (f"No. {number} {street}: " + (f"printed as 'No. {number}' in {printed}" if printed else
                     f"its record places it at {number}, between its neighbours' printed numbers, on its sources' "
                     "order of the houses") + "; the figures' form and paint are reconstructed."),
        })
    found.sort(key=lambda f: (f["street"], int(f["number"])))
    skipped.sort(key=lambda s: s["structure"])
    return found, skipped


def build() -> dict:
    found, skipped = place()
    forms: dict[str, int] = {}
    for f in found:
        forms[f["form"]] = forms.get(f["form"], 0) + 1
    return {
        "_doc": ("The 1871 city's house numbers (T-3738). GENERATED by tools/place_1871_house_numbers.py from the 1871 "
                 "scene's structure records and their baked models' front doors -- do not hand-edit; re-run the tool. "
                 "`at` and `normal` are in each structure's own frame (metres, as its GLB), so "
                 "renderers/web/js/house-numbers.js carries them through buildings.js's matrixOf."),
        "scene": "1871",
        "target_date": "1871-10-08",
        "ticket": TICKET,
        "generated_by": "tools/place_1871_house_numbers.py",
        "liberty": LIBERTY,
        "number_rule": ("The old (pre-1909) number each building's own record reads from its sources, attested where "
                        "'No. NNN' is printed (137 DeKoven Street on Mountford's 1871 card, 133 and 134 in Andreas), "
                        "inferred where the record places the house between printed neighbours (135). A building "
                        "known only by name and corner, and every unnamed context front, shows none."),
        "form_rule": ("Painted figures on the front door's top rail, about 4 in high (on the transom where a door has "
                      "one): no picture of these fronts with their numbers is read, so the form is reconstructed."),
        "hand_rule": "White paint, a Roman or a block letter, dealt per house by a stable hash of its id.",
        "hands": HANDS,
        "summary": {"numbers": len(found), "forms": forms,
                    "hands": {h: sum(1 for f in found if f["hand"] == h) for h in sorted(HANDS)},
                    "skipped": len(skipped)},
        "numbers": found,
        "skipped": skipped,
    }


def check(doc, sidecars=None) -> list[str]:
    """Every number is its own record's reading, figures only, once, on a structure of the scene."""
    scs = {sc["id"]: sc for sc in (sidecars if sidecars is not None else scene_sidecars())}
    faults, seen, on = [], set(), set()
    for f in doc["numbers"]:
        sid = f["structure"]
        key = (f["street"].lower(), f["number"])
        if key in seen:
            faults.append(f"{f['number']} {f['street']} is shown twice")
        seen.add(key)
        if sid in on:
            faults.append(f"{sid} carries two numbers")
        on.add(sid)
        sc = scs.get(sid)
        if not sc:
            faults.append(f"{sid}: not a structure of the 1871 scene (an unnamed front shows no number)")
            continue
        read = read_number(sc)
        if not read or read[0] != f["number"] or read[1].lower() != f["street"].lower():
            faults.append(f"{sid}: shows {f['number']} {f['street']}, which its own record does not read")
        if not f["number"].isdigit():
            faults.append(f"{sid}: number {f['number']!r} is not figures")
        if not f.get("sources"):
            faults.append(f"{sid}: a number with no source")
        if f["grade"] != "reconstructed":
            faults.append(f"{sid}: its figures' form is graded {f['grade']}, but no picture of it is read")
        if abs(sum(v * v for v in f["normal"]) - 1) > 1e-6:
            faults.append(f"{sid}: normal is not a unit")
        lim = (H.FIG_MIN_M, H.FIG_MAX_M) if f["form"] == "transom" else (LEAF_FIG_M - 1e-6, LEAF_FIG_M + 1e-6)
        if not (lim[0] <= f["height_m"] <= lim[1]):
            faults.append(f"{sid}: {f['form']} figures {f['height_m']} m tall")
        if f.get("hand") not in doc.get("hands", {}):
            faults.append(f"{sid}: hand {f.get('hand')!r} is not one of the file's hands")
    return faults


def self_test() -> int:
    doc = build()
    base = check(doc)
    if base or not doc["numbers"]:
        print("self-test: the built file already faults:", base or "no numbers")
        return 1
    cases = []
    d = copy.deepcopy(doc); d["numbers"].append(dict(d["numbers"][0], structure=d["skipped"][0]["structure"])); cases.append(("a number shown twice, on a second building", d))
    d = copy.deepcopy(doc); d["numbers"][0]["number"] = "139"; cases.append(("a number its record does not read", d))
    d = copy.deepcopy(doc); d["numbers"][0]["structure"] = "context1871_core_0125_001_s_02"; cases.append(("a number on an unnamed context front", d))
    d = copy.deepcopy(doc); d["numbers"][0]["number"] = "13O"; cases.append(("a letter for a figure", d))
    d = copy.deepcopy(doc); d["numbers"][0]["sources"] = []; cases.append(("a number with no source", d))
    d = copy.deepcopy(doc); d["numbers"][0]["grade"] = "attested"; cases.append(("an unpictured form graded attested", d))
    d = copy.deepcopy(doc); d["numbers"][0]["height_m"] = 0.4; cases.append(("figures a foot tall", d))
    ok = True
    for name, case in cases:
        got = check(case)
        print(f"   self-test | {name}: {'refused' if got else 'FAIL (passed)'}")
        ok &= bool(got)
    print("self-test:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    doc = build()
    faults = check(doc)
    if faults:
        print("HOUSE NUMBERS 1871 refused:\n  " + "\n  ".join(faults))
        return 1
    text = json.dumps(doc, indent=1, ensure_ascii=False) + "\n"
    if a.check:
        if not OUT.exists() or OUT.read_text() != text:
            print(f"STALE: {OUT.relative_to(ROOT)} is not what tools/place_1871_house_numbers.py writes; re-run it")
            return 1
        print(f"OK: {OUT.relative_to(ROOT)} is current ({doc['summary']['numbers']} numbers)")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text)
    print(f"wrote {OUT.relative_to(ROOT)} — {doc['summary']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
