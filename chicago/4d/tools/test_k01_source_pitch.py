#!/usr/bin/env python3
"""T-1872: a K01 hip whose pitch a source reads may stand below the contract's ordinary band.

RECONSTRUCTION-RULES.md § Starting ranges, Main roof gives an ordinary hip or gable 25-45
degrees and says the street silhouette outranks the range. K01 already let a pitch read off
a source stand ABOVE the band, into the steep one (T-2542 1811's gable, T-3280 1919's hip);
1712 Prairie's low Italianate hip, which the 1893 Rand McNally strip draws rising no more than
about 1.8 m over its 10.65 m front, is the first read BELOW it. This holds the rule both ways:

  * 1712 as committed: its 18-degree hip is inferred, names the drawing, and builds;
  * a reconstructed pitch keeps the floor: the same 18 degrees with no source reading it is
    refused, and so is an inferred one that names no source;
  * the new floor is the flat band's top: a sourced hip at the flat band's top builds, and
    one below it (a deck, K05's flat roof, not a hip) is refused;
  * the ceiling is unchanged: a sourced pitch past the steep band's top is refused.

    python3 tools/test_k01_source_pitch.py
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generators"))

from archetypes import k01_frontage_params as KP  # noqa: E402

failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


def resolves(st, phase):
    try:
        return KP.from_phase(phase, st)
    except (KP.ParamError, ValueError):
        return None


def with_pitch(st, value, confidence, sources):
    phase = copy.deepcopy(st["phases"][-1])
    rp = phase["form"]["roof_pitch_deg"]
    rp["value"], rp["confidence"] = value, confidence
    if sources is None:
        rp.pop("sources", None)
    else:
        rp["sources"] = sources
    return phase


def main() -> int:
    st = json.loads((ROOT / "data" / "structures" / "house_1712_prairie.json").read_text())
    k01 = json.loads((ROOT / "data" / "components" / "prairie_1904" / "k01_contract.json").read_text())
    ranges = next(f for f in k01["families"] if f["family"] == "roof")["parameters"]["pitch_deg"]["ranges"]
    floor, flat_top, steep_top = ranges["ordinary"][0], ranges["flat"][1], ranges["steep"][1]

    rp = st["phases"][-1]["form"]["roof_pitch_deg"]
    src = rp.get("sources") or []
    check(rp["value"] < floor and rp["confidence"] != "reconstructed" and src,
          f"1712: its hip at {rp['value']} deg is {rp['confidence']}, under the {floor}-deg floor, read off {src}")
    p = resolves(st, st["phases"][-1])
    check(p is not None and abs(p.roof_pitch_deg - rp["value"]) < 1e-9, "1712: the committed record builds at its pitch")

    check(resolves(st, with_pitch(st, rp["value"], "reconstructed", src)) is None,
          f"refused: a reconstructed {rp['value']} deg hip (only a source goes under {floor})")
    check(resolves(st, with_pitch(st, rp["value"], "inferred", None)) is None,
          f"refused: an inferred {rp['value']} deg hip that names no source")
    check(resolves(st, with_pitch(st, floor, "reconstructed", src)) is not None,
          f"a reconstructed hip at the {floor}-deg floor still builds")
    check(resolves(st, with_pitch(st, flat_top, "inferred", src)) is not None,
          f"a sourced hip at the flat band's top ({flat_top} deg) builds")
    check(resolves(st, with_pitch(st, flat_top - 0.5, "inferred", src)) is None,
          f"refused: a sourced hip under the flat band's top ({flat_top - 0.5} deg is a deck, not a hip)")
    check(resolves(st, with_pitch(st, steep_top + 1, "inferred", src)) is None,
          f"refused: a sourced pitch past the steep band's top ({steep_top + 1} deg)")

    if failures:
        print(f"test_k01_source_pitch: {len(failures)} failed")
        return 1
    print("test_k01_source_pitch: all passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
