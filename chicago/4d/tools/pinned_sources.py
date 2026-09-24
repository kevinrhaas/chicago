#!/usr/bin/env python3
"""The remote raster regions a trace is made from, pinned by sha256 (T-1397).

THE FAULT THIS CLOSES. `tools/trace_river.py` fetched its region of the Wright 1834
sheet over the network with no pin at all. `fetch_region` used whatever the local
cache held, or whatever the server returned, hashed it, and wrote the hash into the
GeoJSON's provenance — without ever CHECKING it against anything. The hash was a
label, not a gate.

On 2026-09-19 the Boston Public Library's IIIF service re-encoded that one region:
same image, same 1120x1120 box, 263,865 bytes of JPEG became 231,112. The next
`.github/steward/pr-lap.sh` run re-traced the Chicago River from the new bytes and
committed it — the lap runs `node tools/rederive.mjs --run` on every merge, and
`trace_river.py` is one of its 152 steps, in a workflow that pip-installs numpy,
scipy and Pillow. Two pull requests that share no commits, #1518 and #1521, each
acquired the identical 694-line river diff and each failed the same four terrain
gates, neither of them anything to do with the ticket being worked.

Seven of the manifest's steps reach the network. Any of them could have done this.

THE RULE. A trace may not read bytes it was not made from. Every fetch of a pinned
region is held to that region's sha256 BEFORE a pixel is segmented, and a mismatch
refuses: it does not re-trace, and it does not write. The cache is held to the same
pin — a stale file in /tmp may not stand in for the source either, which is not
hypothetical: a cache stamped 2026-09-18 is exactly what made `dev` look
self-reproducing while the branches looked broken.

WHAT A MISMATCH MEANS. It is a finding, not a failure to paper over — the same line
`tools/refetch_control.py` draws for an OpenStreetMap node a mapper moved or
deleted. Upstream re-encoding a scan does not make the committed reading wrong; it
makes it un-re-derivable from the live source, and that is a fact about the source
that belongs in writing. Adopting the new bytes is a decision someone takes
deliberately, with the re-read reviewed against its neighbouring regions — never
something a lap does unattended.

WHY THE OFFLINE CHECK IS THE ONE IN check.sh. Asking the server whether it still
serves the pinned bytes needs the network, and a commit gate that needs the network
fails on aeroplanes and in offline sandboxes for reasons that have nothing to do
with the commit (`refetch_control.py` states this and stays out of the gate for it).
So `--check` is entirely offline: it holds the register to the shas the committed
readings RECORD in their own provenance, and it holds every manifest step that
reaches the network to fetching through this module. `--verify-upstream` is the
online half, run by hand.

  python3 tools/pinned_sources.py --check             offline; this is in check.sh
  python3 tools/pinned_sources.py --self-test         the assertions fire
  python3 tools/pinned_sources.py --verify-upstream   asks the server (network)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / "data" / "traces" / "pinned_sources.json"
MANIFEST = ROOT / "tools" / "derived_manifest.json"

# The module every pinned fetch must go through. A manifest step that opens a IIIF
# region itself is the fault this file exists to stop, so assertion C names it.
GATEWAY = "pinned_sources"


class SourceMoved(Exception):
    """The bytes are not the bytes the committed reading was made from.

    `recorded` says whether the register already KNOWS this source has moved, and
    the two cases must not get the same exit code:

      recorded=False  A NEW move. Nobody has looked at it, the committed reading
                      may or may not still be the right one, and the honest answer
                      is red — the lap aborts, the branch is left alone, and a
                      person decides. This is the state T-1397 was in, and the
                      state in which a lap silently committed a re-trace instead.

      recorded=True   The project has already adjudicated it: the reading stands,
                      `upstream.serves_the_pin: false` is committed, and `--check`
                      prints the NOTE on every gate run. Nothing is left to
                      re-derive, so the tool declines to re-trace, writes nothing,
                      and carries on. Red here would stop every lap in the queue
                      over a fact the project has already written down.
    """

    def __init__(self, message: str, recorded: bool = False):
        super().__init__(message)
        self.recorded = recorded


def load_register() -> dict:
    return json.loads(REGISTER.read_text())


def pins() -> list[dict]:
    return load_register()["pins"]


def pin_for(image: str, region) -> dict:
    """The pin for one (image, region), or a refusal naming what is registered.

    Refusing an UNREGISTERED region is half the point: a new trace cannot quietly
    acquire an unpinned network read by being new.
    """
    want = list(region)
    for p in pins():
        if p["image"] == image and list(p["region"]) == want:
            return p
    known = ", ".join(f"{p['id']} {p['region']}" for p in pins())
    raise SourceMoved(
        f"REFUSING: region {want} of {image} is not pinned in "
        f"{REGISTER.relative_to(ROOT)}.\n"
        f"  A trace may not read a remote raster this project has not pinned.\n"
        f"  Register it with the sha256 of the bytes the reading is made from.\n"
        f"  Pinned today: {known}")


def verify(image: str, region, raw: bytes) -> str:
    """Hold `raw` to its pin. Returns the sha256 on a match; raises on anything else."""
    p = pin_for(image, region)
    got = hashlib.sha256(raw).hexdigest()
    if got == p["sha256"]:
        return got
    up = p["upstream"]
    recorded = (not up.get("serves_the_pin", True)
                and got == up.get("now_serves_sha256"))
    if recorded:
        head = (f"DECLINING to re-trace {p['id']}: the source moved and this project "
                f"has already ruled on it.\n"
                f"  the reading stands (see the register's `the_reading_did_not_move_"
                f"with_it`), so there is nothing to re-derive.\n")
        tail = (f"  Writing nothing and carrying on. To adopt the new bytes, move the pin "
                f"deliberately\n"
                f"  and re-read the neighbouring regions with it — not from a lap.")
    else:
        head = f"REFUSING: the source under {p['id']} has moved, and nothing records it.\n"
        tail = (f"  NOT re-tracing and NOT writing. A re-encode upstream does not make the\n"
                f"  committed reading wrong — it makes it un-re-derivable from the live\n"
                f"  source, which is a finding to record (T-1397). If a copy of the pinned\n"
                f"  bytes survives, put it at {p['cache']} and this check proves it is the\n"
                f"  right one. Otherwise rule on it: either the reading stands and the\n"
                f"  pin's `upstream` block says so, or the new bytes are adopted in a\n"
                f"  deliberate re-read reviewed against the neighbouring regions.")
    raise SourceMoved(
        head
        + f"  pinned   {p['sha256']}  ({p['bytes']:,} bytes)\n"
        + f"  received {got}  ({len(raw):,} bytes)\n"
        + f"  region   {p['region']} of {p['image']}\n"
        + f"  This reading stands under: {', '.join(p['stands_under'])}\n"
        + tail,
        recorded=recorded)


def fetch_pinned(image: str, region, cache: Path, timeout: int = 180):
    """The one fetch the pinned traces share. Cache and network are held to the pin.

    The cache is verified too, and deliberately BEFORE the network is considered:
    the whole fault began with a cache that was right and a server that had moved,
    and the opposite — a cache that is wrong — must not be able to stand in either.
    """
    p = pin_for(image, region)
    x, y, w, h = region
    url = f"{image}/{x},{y},{w},{h}/full/0/default.jpg"
    cache = Path(cache)
    if cache.exists():
        raw = cache.read_bytes()
        if hashlib.sha256(raw).hexdigest() != p["sha256"]:
            raise SourceMoved(
                f"REFUSING: the cache at {cache} is not the pinned source for "
                f"{p['id']}.\n"
                f"  pinned   {p['sha256']}  ({p['bytes']:,} bytes)\n"
                f"  on disk  {hashlib.sha256(raw).hexdigest()}  ({len(raw):,} bytes)\n"
                f"  A stale or foreign file in /tmp may not stand in for the source.\n"
                f"  Delete it to re-fetch, or restore the pinned bytes there.")
        return raw, p["sha256"]
    print(f"fetching {url}")
    with urllib.request.urlopen(url, timeout=timeout) as r:  # noqa: S310
        raw = r.read()
    sha = verify(image, region, raw)          # refuses before anything is written
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_bytes(raw)
    return raw, sha


# ---------------------------------------------------------------------------
# the offline gate
# ---------------------------------------------------------------------------

def _walk(o, path=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from _walk(v, f"{path}/{k}")
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from _walk(v, f"{path}[{i}]")
    else:
        yield path, o


def recorded_shas() -> dict:
    """Every region sha a committed reading records in its own provenance.

    Read out of the files rather than listed here, so a reading that moves to a
    different encoding without its pin moving is a failure rather than a discovery.
    """
    found = {}
    for rel in sorted({s for p in pins() for s in p["stands_under"]}):
        doc = json.loads((ROOT / rel).read_text())
        for path, v in _walk(doc):
            if isinstance(v, str) and len(v) == 64 and re.fullmatch(r"[0-9a-f]{64}", v) \
                    and "sha256" in path.lower():
                found.setdefault(v, set()).add(rel)
    return found


def manifest_network_steps() -> list[tuple[str, tuple[str, ...]]]:
    """(tool, command) for every manifest step whose tool can reach the network.

    Read out of the manifest and the tools' own source rather than listed, so a
    NEW network reader in the manifest is a failure here rather than a discovery.
    """
    m = json.loads(MANIFEST.read_text())
    out = set()
    for s in m["steps"]:
        for a in s["command"]:
            if a.endswith(".py") and (ROOT / a).exists():
                src = (ROOT / a).read_text()
                if "urlopen" in src or "fetch_region" in src or "fetch_pinned" in src:
                    out.add((a, tuple(s["command"])))
    return sorted(out)


def pinned_readers() -> set[str]:
    """The tools whose remote reads go through this module, to a fixed point.

    Three of the five pinned readers never name this module: they set `tr.REGION`
    and call `tr.fetch_region`, which is the shared implementation and is now
    pinned. Following the delegation is what makes the assertion true rather than
    merely textual.
    """
    pinned = {f"tools/{GATEWAY}.py"}
    changed = True
    while changed:
        changed = False
        for path in sorted(ROOT.glob("tools/*.py")):
            rel = f"tools/{path.name}"
            if rel in pinned:
                continue
            src = path.read_text()
            if GATEWAY in src:
                pinned.add(rel); changed = True; continue
            # delegated: imports a module that is itself pinned, and opens no
            # socket of its own.
            if "urlopen" in src:
                continue
            for other in sorted(pinned):
                mod = Path(other).stem
                if f"import {mod}" in src and "fetch_region" in src:
                    pinned.add(rel); changed = True; break
    return pinned


def check(register=None, strict_manifest=True) -> int:
    reg = register if register is not None else load_register()
    ps = reg["pins"]
    problems = []

    # A. the register is a register: one pin per (image, region), full shas, a byte
    #    count, a reader and something it stands under.
    seen = set()
    for p in ps:
        key = (p["image"], tuple(p["region"]))
        if key in seen:
            problems.append(f"{p['id']}: two pins for the same region {p['region']}")
        seen.add(key)
        if not re.fullmatch(r"[0-9a-f]{64}", p.get("sha256", "")):
            problems.append(f"{p['id']}: sha256 is not a full 64-hex digest")
        if not isinstance(p.get("bytes"), int) or p["bytes"] <= 0:
            problems.append(f"{p['id']}: no byte count")
        if not p.get("read_by"):
            problems.append(f"{p['id']}: no tool reads it — a pin nobody reads is dead")
        for t in p.get("read_by", []):
            if not (ROOT / t).exists():
                problems.append(f"{p['id']}: read_by names {t}, which does not exist")
        if not p.get("stands_under"):
            problems.append(f"{p['id']}: nothing is recorded as standing under it")
        for rel in p.get("stands_under", []):
            if not (ROOT / rel).exists():
                problems.append(f"{p['id']}: stands_under names {rel}, which does not exist")

    # B. THE PIN IS THE SHA THE READING RECORDS. This is the assertion that would
    #    have caught T-1397 on the commit that made it: the lapped river.geojson
    #    records 23e14995, which is not any pin, so the file and the register
    #    disagree about which bytes the town's river was traced from.
    recorded = recorded_shas()
    pinned = {p["sha256"] for p in ps}
    for sha, wheres in sorted(recorded.items()):
        if sha not in pinned:
            problems.append(
                f"{', '.join(sorted(wheres))} records region sha {sha[:16]}, which is "
                f"not pinned — the committed reading was made from bytes the register "
                f"does not name")
    for p in ps:
        if p["sha256"] not in recorded:
            problems.append(
                f"{p['id']}: pinned {p['sha256'][:16]}, which no file under "
                f"stands_under records — the pin has drifted off its reading")

    # C. NO MANIFEST STEP READS A REMOTE SOURCE UNPINNED. The lap runs every
    #    manifest step on every merge, so an unpinned network read there is the
    #    whole fault waiting to happen again under a different tool's name.
    #
    #    Two of the seven reach the network only behind a flag the manifest does
    #    not pass — `--fetch` / `--map` read an Internet Archive djvu.xml once and
    #    commit the page text, and the manifest runs `--build`, which rebuilds the
    #    reading offline out of that committed text. That is a real exemption and
    #    it is ENUMERATED rather than inferred: the register names each one with
    #    its offline command, and this holds the manifest to it. A third tool
    #    joining them, or one of these two acquiring the network on its offline
    #    command, is red.
    if strict_manifest:
        pinned_tools = pinned_readers()
        offline = {o["tool"]: o for o in reg.get("offline_in_the_manifest", [])}
        for tool, command in manifest_network_steps():
            if tool in pinned_tools:
                continue
            o = offline.get(tool)
            if not o:
                problems.append(
                    f"{tool} is a manifest step that reaches the network, does not read "
                    f"through tools/{GATEWAY}.py, and is not declared offline in "
                    f"{REGISTER.relative_to(ROOT)} — the lap runs it on every merge")
                continue
            if list(command) != list(o["manifest_command"]):
                problems.append(
                    f"{tool} is declared offline on {o['manifest_command']}, but the "
                    f"manifest runs it as {list(command)}")
            for flag in o["network_only_behind"]:
                if flag in command:
                    problems.append(
                        f"{tool}: the manifest passes {flag}, which is its network mode")
        for tool in offline:
            if tool in pinned_tools:
                problems.append(
                    f"{tool} is declared offline but reads through tools/{GATEWAY}.py — "
                    f"drop the exemption")
            elif tool not in {t for t, _ in manifest_network_steps()}:
                problems.append(
                    f"{tool} is declared offline in the register but is not a manifest "
                    f"step that reaches the network — the exemption is stale")

    if problems:
        print(f"FAIL: {len(problems)} problem(s) with the pinned sources")
        for p in problems:
            print("  *", p)
        return 1
    moved = [p for p in ps if not p["upstream"].get("serves_the_pin", True)]
    nets = manifest_network_steps()
    npin = len([t for t, _ in nets if t in pinned_readers()]) if strict_manifest else 0
    print(f"OK   {len(ps)} pinned source region(s); "
          f"{len(recorded)} region sha(s) recorded by the readings they stand under; "
          f"{len(nets)} manifest step(s) can reach the network — {npin} pinned, "
          f"{len(nets) - npin} offline on the command the manifest runs")
    for p in moved:
        print(f"     NOTE {p['id']}: upstream no longer serves the pinned bytes "
              f"(checked {p['upstream']['checked']}) — the reading stands and is "
              f"recorded as un-re-derivable from the live source")
    return 0


def verify_upstream() -> int:
    """The online half. Not in check.sh — a commit gate may not need the network."""
    bad = 0
    for p in pins():
        x, y, w, h = p["region"]
        url = f"{p['image']}/{x},{y},{w},{h}/full/0/default.jpg"
        try:
            raw = urllib.request.urlopen(url, timeout=180).read()  # noqa: S310
        except Exception as e:  # noqa: BLE001
            print(f"?    {p['id']}: could not fetch — {e}")
            continue
        got = hashlib.sha256(raw).hexdigest()
        says = p["upstream"].get("serves_the_pin", True)
        now = got == p["sha256"]
        mark = "OK  " if now else "MOVED"
        print(f"{mark} {p['id']}: live {got[:16]} ({len(raw):,} B), "
              f"pinned {p['sha256'][:16]} ({p['bytes']:,} B)")
        if now != says:
            print(f"     the register says serves_the_pin: {says} — it is now {now}; "
                  f"update the pin's upstream block and say why in the same commit")
            bad = 1
    return bad


def self_test() -> int:
    """Break each assertion and require it to fire (T-0763's rule)."""
    good = load_register()

    def broken(mutate, what):
        reg = json.loads(json.dumps(good))
        mutate(reg)
        if check(reg, strict_manifest=False) == 0:
            print(f"FAIL: {what} did not fire")
            return False
        return True

    def bump_sha(reg):
        reg["pins"][0]["sha256"] = "0" * 64

    def drop_bytes(reg):
        del reg["pins"][1]["bytes"]

    def dup_region(reg):
        reg["pins"].append(json.loads(json.dumps(reg["pins"][0])))

    def orphan_reader(reg):
        reg["pins"][2]["read_by"] = ["tools/a_tool_that_is_not_here.py"]

    for mutate, what in ((bump_sha, "a pin that no reading records"),
                         (drop_bytes, "a pin with no byte count"),
                         (dup_region, "two pins for one region"),
                         (orphan_reader, "a reader that does not exist")):
        if not broken(mutate, what):
            return 1

    # THE ONE THAT MATTERS: wrong bytes must REFUSE, not trace and not write.
    p = pins()[0]
    try:
        verify(p["image"], p["region"], b"not the Wright sheet")
    except SourceMoved as e:
        if p["sha256"][:16] not in str(e):
            print("FAIL: the refusal does not name the pinned sha")
            return 1
    else:
        print("FAIL: bytes that are not the pinned source did not refuse")
        return 1

    # ...and a cache holding the wrong bytes must refuse too, without a fetch and
    # without overwriting the file it found.
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        c = Path(d) / "wrong.jpg"
        c.write_bytes(b"a stale region left by an earlier run")
        try:
            fetch_pinned(p["image"], p["region"], c)
        except SourceMoved as e:
            if "cache" not in str(e):
                print("FAIL: a wrong cache refused, but not as a cache")
                return 1
        else:
            print("FAIL: a cache that is not the pinned source did not refuse")
            return 1
        if c.read_bytes() != b"a stale region left by an earlier run":
            print("FAIL: the refusal overwrote the file it refused")
            return 1

    # AND THE TWO KINDS OF MOVE MUST NOT GET THE SAME EXIT CODE. A move the register
    # has ruled on declines and carries on; a move nobody has ruled on is red, and
    # that is what makes the lap abort instead of committing a re-trace (T-1397).
    #
    # Bytes with a chosen sha256 cannot be synthesised, so the register is pointed
    # at the sha of a payload we DO hold. That drives the real verify(), not a
    # restatement of its rule.
    probe = b"the bytes a re-encode upstream would serve"
    probe_sha = hashlib.sha256(probe).hexdigest()
    real_loader = globals()["load_register"]

    def with_register(mutate):
        reg = json.loads(json.dumps(real_loader()))
        mutate(reg)
        globals()["load_register"] = lambda: reg

    try:
        # (a) the register says this source moved and these are the bytes it moved
        #     to -> DECLINE, recorded, exit 0 at the caller.
        def ruled(reg):
            q = reg["pins"][0]
            q["upstream"] = {"serves_the_pin": False, "checked": "self-test",
                             "now_serves_sha256": probe_sha}
        with_register(ruled)
        try:
            verify(pins()[0]["image"], pins()[0]["region"], probe)
        except SourceMoved as e:
            if not e.recorded:
                print("FAIL: the recorded re-encode refused instead of declining")
                return 1
            if "DECLINING" not in str(e):
                print("FAIL: a recorded move did not say it was declining")
                return 1
        else:
            print("FAIL: the recorded re-encode did not raise at all")
            return 1

        # (b) same pin, DIFFERENT wrong bytes -> still red. A pin that has moved
        #     once does not become a licence to accept anything.
        try:
            verify(pins()[0]["image"], pins()[0]["region"], b"some third encoding")
        except SourceMoved as e:
            if e.recorded:
                print("FAIL: unknown bytes on a moved pin declined instead of refusing")
                return 1
        else:
            print("FAIL: unknown bytes on a moved pin did not raise")
            return 1

        # (c) a pin the register says is still served -> any mismatch is red.
        def unruled(reg):
            reg["pins"][0]["upstream"] = {"serves_the_pin": True, "checked": "self-test"}
        with_register(unruled)
        try:
            verify(pins()[0]["image"], pins()[0]["region"], probe)
        except SourceMoved as e:
            if e.recorded:
                print("FAIL: a move on a pin with nothing recorded declined")
                return 1
            if "REFUSING" not in str(e):
                print("FAIL: an unrecorded move did not say it was refusing")
                return 1
        else:
            print("FAIL: an unrecorded move did not raise")
            return 1
    finally:
        globals()["load_register"] = real_loader

    # An unregistered region must refuse rather than fetch.
    try:
        pin_for(p["image"], [0, 0, 1, 1])
    except SourceMoved:
        pass
    else:
        print("FAIL: an unpinned region did not refuse")
        return 1

    print("OK: the pinned-source assertions fire when the register or the bytes are wrong")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="hold the register (offline)")
    ap.add_argument("--self-test", action="store_true", help="the assertions fire")
    ap.add_argument("--verify-upstream", action="store_true",
                    help="ask the server whether it still serves the pinned bytes")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if args.verify_upstream:
        return verify_upstream()
    return check()


if __name__ == "__main__":
    sys.exit(main())
