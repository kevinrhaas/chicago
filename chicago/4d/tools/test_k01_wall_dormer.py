#!/usr/bin/env python3
"""T-1890: a flat-capped stone wall dormer on the main mansard's lower face — 1801's third storey.

The Taylor print (c. 1895) and HABS photograph 2 (1965) both show 1801 Prairie's front carried up a
storey behind the bow's balcony: a stone wall from the hooded dormer to the south pavilion, one
light in it south of its middle, under an eave at about 11.25 m, the mansard's slate rising over it.
The build had laid the mansard's lower face down to the cornice there. This holds the kit and the
record to what the ticket built:

  * a lower-face dormer on the main mansard may take the `flat` head (its stone face and cheeks
    under K05's hip at a flat's fall, the kit's dormer overhang and fascia), where a `hip` head
    is still refused there;
  * a flat-capped face may be wider than its light (`face_width_m`, up to 3.5 m) and its light may
    stand `face_shift_m` off its middle; a face narrower than its light, one over 3.5 m, a shift
    that puts the light off the face, or either key on another head is refused;
  * 1801's record stands that wall dormer at v 3.9-6.85 with its light's middle at about v 5.8,
    and the built face and glass are where the record says;
  * (2026-11-06) the light may stand in a lugged `architrave` with a projecting sill, as HABS
    photograph 2 shows 1801's: a head taller than the frieze, lugs or a sill off the face, a sill
    less proud than the band, a missing key, or one on another head is refused, and the built
    frame and sill stand where the record says.

    python3 tools/test_k01_wall_dormer.py
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generators"))

from archetypes import k01_frontage as K1  # noqa: E402
from archetypes import k01_frontage_params as KP  # noqa: E402

SID = "kimball_house_1801_prairie"
failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


st = json.loads((ROOT / "data" / "structures" / f"{SID}.json").read_text())


def with_wall(edit, what):
    st_ = copy.deepcopy(st)
    d = next(x for x in st_["phases"][0]["form"]["mansard"]["value"]["dormers"] if x.get("head") == "flat")
    edit(d)
    try:
        KP.from_phase(st_["phases"][0], st_)
    except KP.ParamError:
        check(True, what)
        return
    check(False, what)


p = KP.from_phase(st["phases"][0], st)
walls = [d for d in p.mansard["dormers"] if d["head"] == "flat"]
check(len(walls) == 1, f"1801's mansard carries one flat-capped wall dormer ({len(walls)})")
w = walls[0]
lo, hi = w["along_m"] - w["width_m"] / 2, w["along_m"] + w["width_m"] / 2
check(w["face"] == "street" and abs(lo - 3.9) < 1e-6 and abs(hi - 6.85) < 1e-6,
      f"it stands on the street face from v {lo:.3f} to {hi:.3f} (3.9-6.85: the hooded dormer to the pavilion)")
check(abs(w["along_m"] + w["light_shift_m"] - 5.795) < 1e-6 and w["sash_width_m"] < w["width_m"],
      f"its one light's middle at v {w['along_m'] + w['light_shift_m']:.3f}, south of the face's")
check(w["overhang_m"] > 0 and w["fascia_m"] > 0, "its cap takes the kit's dormer overhang and fascia")
top = w["foot_m"] + w["sill_m"] + w["head_m"]
check(abs(top - 11.25) < 0.01, f"its eave at {top:.3f} m (the prints' triangulated 11.1-11.75 m)")

with_wall(lambda d: d.update(head="hip", hip_pitch_deg=30.0), "a hipped head on the main mansard is still refused")
with_wall(lambda d: d.update(face_width_m=3.6), "a wall dormer over 3.5 m across is refused")
with_wall(lambda d: d.update(face_width_m=1.2), "a face narrower than its light and surround is refused")
with_wall(lambda d: d.update(face_shift_m=1.0), "a light shifted off its face is refused")
with_wall(lambda d: d.update(head="round", sash=dict(d["sash"], variant="k06.opening.sash_round_plain")),
          "a face wider than its light on a round head is refused")

ar = w.get("architrave") or {}
check(ar.get("band_m") == 0.18 and ar.get("lug_m") == 0.08 and ar.get("sill_proud_m") == 0.12,
      "its light stands in a lugged architrave with a projecting sill (HABS photograph 2, the Taylor print)")
with_wall(lambda d: d["architrave"].update(band_m=0.3), "an architrave head taller than the frieze under the cap is refused")
with_wall(lambda d: d.update(face_width_m=2.5) or d["architrave"].update(lug_m=0.15),
          "an architrave whose lugs or sill run off the face is refused")
with_wall(lambda d: d["architrave"].update(sill_proud_m=0.03), "a sill standing out less than the band is refused")
with_wall(lambda d: d["architrave"].pop("lug_m"), "an architrave missing a key is refused")
with_wall(lambda d: d.update(head="round", sash=dict(d["sash"], variant="k06.opening.sash_round_plain"),
                             face_width_m=None) or d.pop("face_width_m") or d.pop("face_shift_m"),
          "an architrave on a round head is refused")

asm = K1.build(p, SID)
D, o = p.depth_m, p.eave_overhang_m
face = [q for q in asm.prims["dormer_stone"].pos
        if abs(q[0] - (D + o - w["face_setback_m"])) < 1e-3 and 3.8 < -q[2] < 7.0 and 9.5 < q[1] < 11.3]
check(face and abs(min(-q[2] for q in face) - 3.9) < 1e-3 and abs(max(-q[2] for q in face) - 6.85) < 1e-3,
      f"the built face stands {w['face_setback_m']} m in from the fascia from v 3.9 to 6.85 ({len(face)} vertices)")
nf = D + o - w["face_setback_m"]
lc = w["along_m"] + w["light_shift_m"]
frame = [q for q in asm.prims["dormer_stone"].pos if abs(q[0] - (nf + ar["proud_m"])) < 1e-3
         and 3.8 < -q[2] < 7.0 and 9.0 < q[1] < 11.3]
sills = [q for q in asm.prims["dormer_stone"].pos if abs(q[0] - (nf + ar["sill_proud_m"])) < 1e-3
         and 3.8 < -q[2] < 7.0 and 9.0 < q[1] < 11.3]
reach = w["sash_width_m"] / 2 + ar["band_m"] + ar["lug_m"]
check(frame and abs(max(abs(-q[2] - lc) for q in frame) - reach) < 1e-3,
      f"the built architrave stands {ar['proud_m']} m proud, its lugs {reach:.2f} m either side of the light's middle")
check(sills and abs(max(abs(-q[2] - lc) for q in sills) - (w["sash_width_m"] / 2 + ar["band_m"] + ar["sill_ext_m"])) < 1e-3,
      f"the built sill stands {ar['sill_proud_m']} m proud and runs past the band")
glass = [q for q in asm.prims["glass"].pos if q[0] > D - 0.5 and 3.8 < -q[2] < 7.0 and 9.5 < q[1] < 11.3]
mid = (min(-q[2] for q in glass) + max(-q[2] for q in glass)) / 2 if glass else 0.0
check(glass and abs(mid - 5.795) < 0.02, f"its glass stands where the record puts the light (middle v {mid:.3f})")

if failures:
    print(f"\n{len(failures)} failure(s)")
    sys.exit(1)
print("\nall wall-dormer checks pass")
