#!/usr/bin/env python3
"""Hold the walls' relief rule to what the generators build (T-1963).

    python3 tools/check_wall_relief.py --check       # the rule, on every committed record
    python3 tools/check_wall_relief.py --self-test   # prove the comparison fires
    python3 tools/check_wall_relief.py --table       # print each bound record's substrate and grain

WHAT IT GUARDS. `renderers/web/js/wall-relief.js` binds a relief map to a wall by
reading the record — route 2 of docs/RESEARCH/1835_photographic_fabric_preparation.md
section 5, and docs/GLB-CONTRACT.md section Wall substrates (PROPOSED, T-1963). The
price of that route is named there in terms: "the renderer then depends on a record
field staying in step with the generator's wall_substrate()". This is the check that
keeps it in step. It runs `renderers/web/js/wall-grain.js` itself, under node, over
every 1835 sidecar, and holds each answer to `generators/common/materials.py`:

  * SUBSTRATE. A frame dwelling or tavern is built `wall_substrate(cladding="clapboard")`
    outright; a storefront `wall_substrate(construction, cladding)` off its record, with
    the params' defaults (balloon_frame, clapboard). The renderer binds the clapboard
    face exactly where that comes out `clapboard`, and nowhere else.
  * FINISH. `wall_finish(paint, finish_key).key`, the same order: a stated coating, then
    the programme's finish_key, then unpainted.
  * GRAIN. 0.3 on a coating (`Finish.coating`), 1.0 on bare stock.
  * THE MATERIAL IS THERE. Every record bound for a `wall` has a web GLB carrying a
    material named `wall`, and every GLB carrying one is either bound or one of the
    upright-board storefronts the rule leaves flat, by name.

It reads; it writes nothing.
"""
from __future__ import annotations

import argparse
import json
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generators"))
from common import materials  # noqa: E402

SIDECARS = ROOT / "data" / "sidecars" / "1835"
WEB = ROOT / "assets" / "web"
RULE = ROOT / "renderers" / "web" / "js" / "wall-grain.js"
FRAME = {"frame_dwelling", "frame_storefront", "frame_tavern"}


def _val(sidecar: dict, name: str):
    a = (sidecar.get("attributes") or {}).get(name)
    return a.get("value") if isinstance(a, dict) else a


def load_records() -> dict[str, dict]:
    out = {}
    for f in sorted(SIDECARS.glob("*.json")):
        d = json.loads(f.read_text())
        if isinstance(d, dict) and d.get("id") and d.get("archetype"):
            out[d["id"]] = d
    return out


def js_rule(records: dict[str, dict]) -> dict[str, dict]:
    """Run wall-grain.js's `wallRelief` over every record, under node."""
    script = (
        "import { wallRelief } from %s;\n"
        "let s = ''; process.stdin.on('data', (c) => { s += c; });\n"
        "process.stdin.on('end', () => {\n"
        "  const recs = JSON.parse(s); const out = {};\n"
        "  for (const [id, r] of Object.entries(recs)) out[id] = wallRelief(r);\n"
        "  process.stdout.write(JSON.stringify(out));\n"
        "});\n" % json.dumps(RULE.as_uri()))
    res = subprocess.run(["node", "--input-type=module", "-e", script],
                         input=json.dumps(records), capture_output=True, text=True, check=False)
    if res.returncode != 0:
        raise SystemExit(f"node could not run {RULE.relative_to(ROOT)}: {res.stderr.strip()}")
    return json.loads(res.stdout)


def expected(sidecar: dict) -> dict:
    """What the generators build, asked of materials.py directly."""
    arch = sidecar.get("archetype")
    wall = None
    if arch in FRAME:
        if arch == "frame_storefront":
            sub = materials.wall_substrate(construction=_val(sidecar, "construction") or "balloon_frame",
                                           cladding=_val(sidecar, "cladding") or "clapboard")
        else:
            sub = materials.wall_substrate(cladding="clapboard")
        if sub.key == "clapboard":
            fin = materials.wall_finish(_val(sidecar, "paint"),
                                        (sidecar.get("reconstruction") or {}).get("finish_key"))
            wall = {"substrate": "clapboard", "finish": fin.key, "grain": 0.3 if fin.coating else 1.0}
    return {"wall": wall}


def glb_materials(path: Path) -> set[str]:
    b = path.read_bytes()
    if b[:4] != b"glTF":
        return set()
    (length,) = struct.unpack_from("<I", b, 12)
    doc = json.loads(b[20:20 + length])
    return {m.get("name") for m in doc.get("materials", [])}


def web_glb(sidecar: dict) -> Path | None:
    asset = sidecar.get("asset")
    if not isinstance(asset, str):
        return None
    p = WEB / Path(asset).name
    return p if p.exists() else None


def compare(records: dict, js: dict) -> list[str]:
    problems = []
    for rid, rec in records.items():
        want = expected(rec)["wall"]
        got = (js.get(rid) or {}).get("wall")
        if want is None and got is None:
            continue
        if want is None or got is None:
            problems.append(f"{rid}: wall-grain.js says {got}, materials.py builds {want}")
            continue
        for k in ("substrate", "finish"):
            if want[k] != got.get(k):
                problems.append(f"{rid}: wall {k} {got.get(k)!r}, materials.py builds {want[k]!r}")
        if abs(float(got.get("grain", -1)) - want["grain"]) > 1e-9:
            problems.append(f"{rid}: wall grain {got.get('grain')}, the finish wants {want['grain']}")
    return problems


def check_materials(records: dict, js: dict) -> tuple[list[str], dict]:
    problems, seen = [], {"bound": 0, "logs": 0, "left_flat": []}
    for rid, rec in records.items():
        glb = web_glb(rec)
        if glb is None:
            continue
        names = glb_materials(glb)
        has = "wall" in names
        if "log" in names and (js.get(rid) or {}).get("log"):
            seen["logs"] += 1
        bound = bool((js.get(rid) or {}).get("wall"))
        if bound and not has:
            problems.append(f"{rid}: bound for a clapboard wall but {glb.name} has no `wall` material")
        if has and bound:
            seen["bound"] += 1
        if has and not bound:
            if rec.get("archetype") == "frame_storefront" and _val(rec, "cladding") in ("vertical_board", "board_and_batten"):
                seen["left_flat"].append(rid)
            else:
                problems.append(f"{rid}: {glb.name} carries a `wall` the rule neither binds nor names")
    return problems, seen


def self_test() -> int:
    records = load_records()
    js = js_rule(records)
    fails = 0
    # 1. a coated wall read as bare
    rid = next(r for r, x in js.items() if (x.get("wall") or {}).get("grain") == 0.3)
    broken = json.loads(json.dumps(js))
    broken[rid]["wall"]["grain"] = 1.0
    if not compare(records, broken):
        print(f"self-test | FAIL: a coat read as bare stock on {rid} went unnoticed"); fails += 1
    # 2. an upright-board storefront bound as clapboard
    rid = next(r for r, x in records.items() if _val(x, "cladding") == "vertical_board")
    broken = json.loads(json.dumps(js))
    broken[rid]["wall"] = {"substrate": "clapboard", "finish": "unpainted", "grain": 1.0}
    if not compare(records, broken):
        print(f"self-test | FAIL: {rid}'s vertical boards bound as clapboard went unnoticed"); fails += 1
    # 3. a stated coating losing to the finish_key
    fake = {"x": {"id": "x", "archetype": "frame_dwelling",
                  "attributes": {"paint": {"value": "whitewash"}},
                  "reconstruction": {"finish_key": "weathered_timber"}}}
    if js_rule(fake)["x"]["wall"]["finish"] != "whitewash":
        print("self-test | FAIL: wall-grain.js let a finish_key outrank a stated coating"); fails += 1
    print("self-test | " + ("all three breakages caught" if not fails else f"{fails} breakage(s) missed"))
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--table", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    records = load_records()
    js = js_rule(records)
    if a.table:
        for rid, x in sorted(js.items()):
            if x.get("wall") or x.get("log"):
                print(f"{rid:60s} wall={x.get('wall')} log={bool(x.get('log'))}")
        return 0
    problems = compare(records, js)
    more, seen = check_materials(records, js)
    problems += more
    walls = sum(1 for x in js.values() if x.get("wall"))
    coated = sum(1 for x in js.values() if (x.get("wall") or {}).get("grain") == 0.3)
    for p in problems:
        print(f"FAIL: {p}")
    print(f"wall relief: {walls} clapboard walls bound ({coated} under a coat), "
          f"{seen['bound']} GLB `wall` materials bound, {seen['logs']} laid-log walls bound, "
          f"{len(seen['left_flat'])} upright-board storefronts left flat"
          + ("" if not problems else f" — {len(problems)} problem(s)"))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
