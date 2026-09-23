#!/usr/bin/env python3
"""Can this repository reproduce the bytes it publishes? — the control K39 could not get.

ROADMAP K40. `tools/measure_web_derivatives.py` asks whether a shipped derivative still
DESCRIBES its master: triangles, node identity, contract attributes, bounds, materials,
size, and (assertion 9) the sha256 of the master it was made from. All nine can be green
on a file this repository cannot produce, because none of them runs the step. This one
runs the step and compares bytes.

    tools/measure_web_reproduction.py --plan [--chunks N]     print the commands to run
    tools/measure_web_reproduction.py --chunk K/N             produce chunk K of N
    tools/measure_web_reproduction.py --palette-chunk K/N     re-produce the failures
                                                              with BAKE_PALETTE=1
    tools/measure_web_reproduction.py --report                the census

## Why it is chunked, and why that is the tool's shape rather than an aside

The control is `tools/web_derivatives.sh` itself — never a reimplementation of it, because
a reimplementation would answer a question about the copy. It costs ~2.4 s per asset, so a
full 334-asset control is ~13 minutes, and a steward run's harness caps a single foreground
command at TEN. Every agent that has wanted this number has had to invent a chunked loop
first. `--chunk K/N` is that loop, so the next one does not.

The work tree defaults to `$WEB_REPRO_WORK` or `/tmp/web-reproduction`, and this tool will
not write into `assets/` under any flag: a measurement that can author the thing it
measures is not a measurement. It reads `assets/gltf/` and `assets/web/` and nothing else.

## What it measured, 2026-08-16 (K40) — see docs/RESEARCH/web-reproduction.md

    334 derivatives   142 reproduce   192 do not
      of the 192: 189 come back BYTE FOR BYTE under BAKE_PALETTE=1 — the palette-era set,
                  counted exactly rather than inferred
                    3 reproduce under neither, and all three are already owned:
                    the two K37 placeholders that compress smaller, and the terrain
                    R-W6(b) holds at 14 bits against a 16-bit ask

And the control's own headline, which is what it was built to settle: on all 189 of the
palette-era set the bytes this runner produces are **md5-identical to the bytes the nightly
bake put in PR #175**. This runner CAN regenerate what the nightly ships. What was wrong was
never the extraction — it was that K36(b)'s step change was carried through 38 files and not
through 334.

**The vertex signature is not the palette signature, and K39's 195 was not this set.**
K39 counted derivatives carrying fewer vertices than their masters — 195 — and reasoned
that "only the palette-era step produces this". Measured against the exact control the two
sets differ in BOTH directions: 189 in common, **6 welded files that today's step
reproduces exactly** (2-4 vertices each: `optimize` dedups without the palette pass), and
3 non-reproducing files with no weld at all. So the cheap proxy is neither the set nor a
bound on it, and this tool reports both so the difference cannot be rounded off again.
Do not quote 195, and do not build a gate on the vertex count.
"""

import argparse
import hashlib
import json
import os
import pathlib
import struct
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
GLTF = ROOT / "assets" / "gltf"
WEB = ROOT / "assets" / "web"
STEP = ROOT / "tools" / "web_derivatives.sh"


def work_dir(arg=None):
    d = pathlib.Path(arg or os.environ.get("WEB_REPRO_WORK") or "/tmp/web-reproduction")
    d = d.resolve()
    # A measurement that can author the thing it measures is not a measurement.
    if d == (ROOT / "assets").resolve() or (ROOT / "assets").resolve() in d.parents:
        sys.exit(f"refusing to write a control into the asset tree: {d}")
    return d


def masters():
    return sorted(p.name for p in GLTF.glob("*.glb"))


def chunk_of(names, spec):
    try:
        k, n = (int(x) for x in spec.split("/"))
    except ValueError:
        sys.exit(f"--chunk wants K/N, got {spec!r}")
    if not 1 <= k <= n:
        sys.exit(f"chunk {k} is not in 1..{n}")
    size = -(-len(names) // n)
    return names[(k - 1) * size: k * size]


def md5(p):
    return hashlib.md5(p.read_bytes()).hexdigest()


def glb_json(p):
    b = p.read_bytes()
    if b[:4] != b"glTF":
        sys.exit(f"not a GLB: {p}")
    off = 12
    while off < len(b):
        length, kind = struct.unpack_from("<II", b, off)
        if kind == 0x4E4F534A:
            return json.loads(b[off + 8: off + 8 + length].decode("utf-8"))
        off += 8 + length
    sys.exit(f"no JSON chunk in {p}")


def vertices(p):
    """POSITION count over every primitive — the cheap signature K39 used, kept here to
    be REPORTED against the exact answer rather than trusted."""
    doc = glb_json(p)
    acc = doc.get("accessors", [])
    return sum(
        acc[prim["attributes"]["POSITION"]]["count"]
        for mesh in doc.get("meshes", [])
        for prim in mesh.get("primitives", [])
        if "POSITION" in prim.get("attributes", {})
    )


def produce(names, out, palette):
    out.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    if palette:
        env["BAKE_PALETTE"] = "1"
    for i, name in enumerate(names, 1):
        r = subprocess.run(
            [str(STEP), "--out", str(out), "--only", name],
            cwd=ROOT, env=env, capture_output=True, text=True,
        )
        if r.returncode != 0 or not (out / name).exists():
            print(r.stdout[-2000:], r.stderr[-2000:], file=sys.stderr)
            sys.exit(f"the step failed on {name}")
        print(f"   {i:3d}/{len(names)}  {name}")
    print(f"== {len(names)} produced into {out}"
          f"{' with BAKE_PALETTE=1' if palette else ''}")


def report(work, as_json):
    today, pal = work / "today", work / "palette"
    names = masters()
    missing = [n for n in names if not (today / n).exists()]
    if missing:
        sys.exit(f"the control is incomplete — {len(missing)} of {len(names)} missing from "
                 f"{today}. Run every --chunk first (--plan prints them).")

    rows = []
    for n in names:
        m, w, c = GLTF / n, WEB / n, today / n
        row = {
            "name": n,
            "master_bytes": m.stat().st_size,
            "shipped_bytes": w.stat().st_size,
            "control_bytes": c.stat().st_size,
            "passthrough": md5(m) == md5(w),
            "reproduces": md5(w) == md5(c),
            "welded": vertices(w) < vertices(m),
            "palette_era": None,
        }
        if not row["reproduces"] and (pal / n).exists():
            row["palette_era"] = md5(w) == md5(pal / n)
        rows.append(row)

    ok = [r for r in rows if r["reproduces"]]
    bad = [r for r in rows if not r["reproduces"]]
    era = [r for r in bad if r["palette_era"]]
    neither = [r for r in bad if r["palette_era"] is False]
    unasked = [r for r in bad if r["palette_era"] is None]
    delta = sum(r["control_bytes"] - r["shipped_bytes"] for r in bad)
    shipped_total = sum(r["shipped_bytes"] for r in rows)

    print("== can this repository reproduce what it publishes? (ROADMAP K40)")
    print(f"   {len(rows)} derivatives   {len(ok)} reproduce   {len(bad)} do not")
    if unasked:
        print(f"   {len(unasked)} of the failures have no BAKE_PALETTE=1 control yet "
              f"(run --palette-chunk)")
    if era or neither:
        print(f"   of the {len(bad)}: {len(era)} reproduce byte-for-byte under "
              f"BAKE_PALETTE=1 — the palette-era set")
        print(f"                  {len(neither)} reproduce under neither step:")
        for r in neither:
            print(f"                    {r['name']}  shipped {r['shipped_bytes']} "
                  f"control {r['control_bytes']}")
    print(f"   regenerating every failure costs {delta:+,} bytes on a "
          f"{shipped_total:,}-byte tree ({delta / shipped_total * 100:+.2f} %, "
          f"{delta / (25 * 1024 * 1024) * 100:+.3f} % of the 25 MB budget)")

    # The cheap proxy, reported against the exact answer. See the header.
    welded = {r["name"] for r in rows if r["welded"] and not r["passthrough"]}
    failed = {r["name"] for r in bad}
    print(f"   vertex-signature proxy: {len(welded)} welded, and it is NOT this set — "
          f"{len(welded & failed)} shared, {len(welded - failed)} welded files reproduce "
          f"exactly, {len(failed - welded)} failures carry no weld")

    if as_json:
        out = work / "reproduction.json"
        out.write_text(json.dumps(rows, indent=1) + "\n", encoding="utf-8")
        print(f"   wrote {out}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--chunk", metavar="K/N")
    ap.add_argument("--palette-chunk", metavar="K/N")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--chunks", type=int, default=4)
    ap.add_argument("--work", metavar="DIR")
    ap.add_argument("--json", action="store_true", help="write reproduction.json beside the control")
    a = ap.parse_args()
    work = work_dir(a.work)

    if a.plan:
        n = a.chunks
        print(f"# {len(masters())} masters, ~2.4 s each — {n} chunks of about "
              f"{len(masters()) * 2.4 / n / 60:.1f} min, under the 10-minute ceiling")
        for k in range(1, n + 1):
            print(f"tools/measure_web_reproduction.py --chunk {k}/{n}")
        print("tools/measure_web_reproduction.py --report        # names the failures")
        for k in range(1, n + 1):
            print(f"tools/measure_web_reproduction.py --palette-chunk {k}/{n}")
        print("tools/measure_web_reproduction.py --report --json")
        return 0

    if a.chunk:
        produce(chunk_of(masters(), a.chunk), work / "today", palette=False)
        return 0

    if a.palette_chunk:
        today = work / "today"
        if not today.exists():
            sys.exit("run the plain --chunk control first: the palette control only ever "
                     "runs over the files that failed it")
        failed = [n for n in masters()
                  if (today / n).exists() and md5(WEB / n) != md5(today / n)]
        if not failed:
            print("nothing failed today's step — no palette control to take")
            return 0
        produce(chunk_of(failed, a.palette_chunk), work / "palette", palette=True)
        return 0

    if a.report:
        return report(work, a.json)

    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
