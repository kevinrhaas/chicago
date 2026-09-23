#!/usr/bin/env python3
"""measure_plate_join.py — is this crop a panel of a sheet this project already holds?

T-0055 asked that question of ONE crop and answered it by hand: the Kinzie view,
`p6_1.png`, is panel 12 of `kurz_allison_1893`, proved three ways — the printed
numeral, the sheet's own key line, and a normalised cross-correlation of the crop
against the committed sheet. It left the two fort crops marked *unconfirmed* in the
2026-08-11 README because its scope was the Kinzie plate and nothing else was
measured. **T-1107 is that measurement, and this file is the method made repeatable
so the fourth crop does not need a fourth improvisation.**

## What it finds

Three crops the fort layers have cited by committed path since T-0097 are panels of
`kurz_allison_1893` — Kurz & Allison, *Chicago In Early Days, 1779-1857* (1893),
`public_domain`, whole sheet committed at `chicago/reference/photos/IMG_5382.png`:

    crop      panel  the sheet's own key line                              ncc    control
    p4_0.png    1    "No. 1.  Old Fort Dearborn.  Erected 1803."           0.896   0.400
    p3_1.png    5    "No. 5.  Fort Dearborn, as re[built] ... 1835.
                      Population 3,265."                                   0.812   0.337
    p4_1.png    8    "No. 8.  Chicago in 1830 - From the Lake.
                      Population 96."                                      0.863   0.325

`control` is the best correlation the same crop reaches anywhere in the 1853
bird's-eye panel, the control T-0055 used: a different picture of the same town, in
the same ink, on the same paper, photographed in the same exposure. The join is not
a resemblance — it is between two and two-and-a-half times the best the same crop
can do against a decoy.

## The finding that was not expected

**`p4_1.png` is not a fort plate. It is panel 8, "Chicago in 1830 - From the Lake",
population 96.** The 2026-08-11 README grouped it with `p4_0` as one of two "Fort
Dearborn from across the river" views and `data/enclosures/fort_dearborn_apron.json`
called them "the two Fort Dearborn plates"; the ticket warned that `p4_1` "is a wider
view than `p4_0` and may be a different sheet entirely - do not assume the batch is
homogeneous". It is the same sheet and a different subject: a town view of 1830 in
which the fort is one building among many, five years before the scene date and
before the rebuilt walls of panel 5.

That does not retract a measurement taken off it. `measure_fort_ways_plate.py` asks
`p4_1` whether a travelled way is drawn AT the fort and `generate_fort_trees.py` asks
it what stands round the buildings on both banks — both are questions about what the
picture draws, and the picture is unchanged by being named. What changes is the DATE
a reader should attach to the answer, and that a claim about the 1835 fort now rests
on panel 1 (1803) and panel 5 (1835) rather than on a pair the README called
interchangeable.

## What identification buys, and what it does not

Exactly what T-0055 said it buys, three more times: a `source_id` with a date, a
publisher, a holding institution and an expired copyright ("Copyrighted 1893 by Kurz
& Allison, 76 & 78 Wabash Avenue, Chicago, Ills.", printed at the foot of the sheet)
in place of a path to a crop of unstated rights. These are still tier-5 retrospective
lithographs published fifty-eight years after the scene date. They may drive massing,
roof form, fenestration rhythm, materials and setting as `inferred`, and they may
never drive a coordinate. No confidence anywhere moves because of this file.

## The method, and why it is a gate

Normalised cross-correlation of the crop against the whole sheet, over a sweep of
scales, computed exactly: the numerator by FFT, the window means and variances by
integral image, so the score at every offset is a true Pearson correlation and not a
rescaled dot product. The peak is reported with its scale and its box in sheet
pixels; the control is the peak of the SAME map restricted to the 1853 panel.

`--gate` re-measures all four committed joins (the three above plus T-0055's panel 12,
which is the method's own calibration) and fails if a peak moves off its recorded box,
drops below its recorded floor, or stops beating its control by the recorded margin.
It is cheap insurance on something easy to get wrong later: if either image is ever
re-cropped, re-scanned or re-compressed, four source citations quietly stop pointing
at what they say they point at, and nothing else in this repository would notice.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
SHEET = REPO / "chicago" / "reference" / "photos" / "IMG_5382.png"
PLATES = ROOT / "data" / "sources" / "assets" / "prefire_views_kevin_2026_08"

# The 1853 bird's-eye panel, in sheet pixels: T-0055's control, and a decoy with
# every nuisance variable of the real thing — same ink, same paper, same exposure.
CONTROL_BOX = (460, 840, 1580, 1420)

# THE COMMITTED JOINS. Each row is a claim the gate re-proves: this crop is that
# panel, at that scale, in that box, by that margin over the control. `ncc` and
# `control` are the measured figures, recorded to three places; the gate's slack is
# NCC_SLACK and BOX_SLACK below, wide enough for a resize library's rounding and far
# too narrow for a different picture.
JOINS = [
    {
        "crop": "p6_1.png",
        "panel": 12,
        "key": "No. 12.  The Old Kinzie Mansion, built 1832.  Population 310.",
        "numeral": "12.",
        "scale": 0.880,
        "box": (95, 1163, 439, 1416),
        "ncc": 0.861,
        "control": 0.342,
        "note": "T-0055's join, re-measured by this file. It is the calibration: a "
                "result this file must reproduce to be believed about the other three.",
    },
    {
        "crop": "p4_0.png",
        "panel": 1,
        "key": "No. 1.  Old Fort Dearborn.  Erected 1803.",
        "numeral": "1.",
        "scale": 0.295,
        "box": (99, 78, 553, 331),
        "ncc": 0.896,
        "control": 0.400,
        "note": "The fort from across the river, the plate measure_picket_plate.py and "
                "measure_fort_works_plate.py read. Top-left vignette of the sheet.",
    },
    {
        "crop": "p3_1.png",
        "panel": 5,
        "key": "No. 5.  Fort Dearborn, as re[built] ... 1835.  Population 3,265.",
        "numeral": "5.",
        "scale": 0.425,
        "box": (1486, 77, 1945, 323),
        "ncc": 0.812,
        "control": 0.337,
        "note": "The rebuilt fort behind its palisade, top-right vignette. The one panel "
                "of the sheet whose key line names the scene year.",
    },
    {
        "crop": "p4_1.png",
        "panel": 8,
        "key": "No. 8.  Chicago in 1830 - From the Lake.  Population 96.",
        "numeral": None,
        "scale": 0.735,
        "box": (533, 342, 1511, 831),
        "ncc": 0.863,
        "control": 0.325,
        "note": "NOT A FORT PLATE. The centre vignette, an 1830 town view; the crop is "
                "taken inside the frame and carries no numeral of its own, so the panel "
                "number is read off the sheet at (572,304), outside the frame's top-left "
                "corner, where this sheet prints the numbers of its two largest panels.",
    },
]

NCC_SLACK = 0.020      # a peak may drift this far below its recorded figure
BOX_SLACK = 4          # pixels, on each edge
MARGIN_SLACK = 0.050   # the peak-minus-control margin may shrink this much


class Fault(Exception):
    """A measurement could not be taken at all."""


class MissingReader(Fault):
    """numpy or Pillow is absent, so no raster can be read.

    T-1083's rule: a tool degrades politely and says what it could not ask; a GATE
    may not count that skip as a pass. `C4D_GATE_REQUIRE_READERS=1`, which the
    workflow sets, turns the skip red. tools/check_gate_readers.py enumerates this
    step among the ones that stop re-reading.
    """


def _numpy():
    try:
        import numpy as np
        from PIL import Image
    except ImportError as exc:      # pragma: no cover - environment, not logic
        raise MissingReader(f"needs numpy and Pillow ({exc})") from exc
    Image.MAX_IMAGE_PIXELS = None
    return np, Image


def ncc_map(img, tpl, np):
    """True normalised cross-correlation of tpl over img, one value per offset.

    Numerator by FFT; window mean and variance by integral image. The result at
    (y,x) is Pearson's r between tpl and the img window whose top-left is (x,y).
    """
    ih, iw = img.shape
    th, tw = tpl.shape
    if th > ih or tw > iw:
        return None
    t = tpl - tpl.mean()
    tnorm = float(np.sqrt((t * t).sum()))
    if tnorm == 0.0:
        return None
    F = np.fft.rfft2(img, s=(ih, iw))
    T = np.fft.rfft2(t[::-1, ::-1], s=(ih, iw))
    num = np.fft.irfft2(F * T, s=(ih, iw))[th - 1:ih, tw - 1:iw]
    ii = np.zeros((ih + 1, iw + 1), np.float64)
    ii[1:, 1:] = img.cumsum(0).cumsum(1)
    i2 = np.zeros((ih + 1, iw + 1), np.float64)
    i2[1:, 1:] = (img.astype(np.float64) ** 2).cumsum(0).cumsum(1)

    def window(I):
        return I[th:, tw:] - I[:-th, tw:] - I[th:, :-tw] + I[:-th, :-tw]

    n = th * tw
    s1 = window(ii)
    var = window(i2) - s1 * s1 / n
    var[var < 1e-6] = 1e-6
    return num / (np.sqrt(var) * tnorm)


def _restricted_peak(m, box, tw, th, np):
    """The peak of m among offsets whose window lies inside box."""
    x0, y0, x1, y1 = box
    xs0, ys0 = max(0, x0), max(0, y0)
    xs1 = min(m.shape[1], max(0, x1 - tw + 1))
    ys1 = min(m.shape[0], max(0, y1 - th + 1))
    if xs1 <= xs0 or ys1 <= ys0:
        return None
    sub = m[ys0:ys1, xs0:xs1]
    return float(sub.max())


def measure(crop_path, sheet_path, scales, control=CONTROL_BOX):
    """Peak correlation of a crop against a sheet, with the control's best."""
    np, Image = _numpy()
    for p in (crop_path, sheet_path):
        if not p.exists():
            raise Fault(f"missing image {p}")
    sheet = np.asarray(Image.open(sheet_path).convert("L"), np.float32)
    crop = Image.open(crop_path).convert("L")
    best = None
    for s in scales:
        tw = max(8, int(round(crop.width * s)))
        th = max(8, int(round(crop.height * s)))
        m = ncc_map(sheet, np.asarray(crop.resize((tw, th), Image.LANCZOS), np.float32), np)
        if m is None:
            continue
        idx = int(np.argmax(m))
        y, x = divmod(idx, m.shape[1])
        peak = float(m[y, x])
        if best is None or peak > best["ncc"]:
            best = {
                "ncc": round(peak, 3),
                "scale": round(float(s), 4),
                "box": (int(x), int(y), int(x + tw), int(y + th)),
                "control": round(_restricted_peak(m, control, tw, th, np) or -1.0, 3),
            }
    if best is None:
        raise Fault(f"{crop_path.name} is larger than {sheet_path.name} at every scale")
    return best


def _sweep(centre, span=0.010, step=0.005):
    n = int(round(span / step))
    return [round(centre + i * step, 4) for i in range(-n, n + 1)]


def check_join(join, sheet=SHEET, plates=PLATES):
    """Re-measure one committed join. Returns (reading, [complaints])."""
    got = measure(plates / join["crop"], sheet, _sweep(join["scale"]))
    bad = []
    if got["ncc"] < join["ncc"] - NCC_SLACK:
        bad.append(f"the peak fell to {got['ncc']} from a recorded {join['ncc']}")
    for i, edge in enumerate(("x0", "y0", "x1", "y1")):
        if abs(got["box"][i] - join["box"][i]) > BOX_SLACK:
            bad.append(f"the match moved: {edge} {got['box'][i]} against a recorded "
                       f"{join['box'][i]}")
    margin = round(got["ncc"] - got["control"], 3)
    recorded = round(join["ncc"] - join["control"], 3)
    if margin < recorded - MARGIN_SLACK:
        bad.append(f"the margin over the control fell to {margin} from a recorded "
                   f"{recorded}")
    if got["control"] >= got["ncc"]:
        bad.append(f"the control ({got['control']}) is no worse than the join "
                   f"({got['ncc']}) — this is not an identification")
    got["margin"] = margin
    return got, bad


def gate(quiet=False):
    failures = 0
    for join in JOINS:
        got, bad = check_join(join)
        for complaint in bad:
            print(f"  FAIL  {join['crop']} / panel {join['panel']}: {complaint}")
            failures += 1
        if not bad and not quiet:
            print(f"  ok    {join['crop']} = kurz_allison_1893 panel {join['panel']:>2} "
                  f"— ncc {got['ncc']} at {got['scale']}x, control {got['control']}")
    if failures:
        print("  The four panel citations in data/sources/kurz_allison_1893.json and "
              "the README's Identifications table rest on these joins; one of them no "
              "longer measures as recorded.")
        return 1
    if not quiet:
        print("  four crops, four panels of one sheet, every join re-measured")
    return 0


def self_test():
    """Break each assertion and watch it fire. No committed file is touched."""
    np, Image = _numpy()
    failures = []
    calib = JOINS[0]

    got, bad = check_join(calib)
    if bad:
        failures.append("SELF-TEST FAIL: the committed calibration join does not pass "
                        "its own gate")

    # 1. a join whose recorded box is somewhere else must be caught
    moved = dict(calib, box=(calib["box"][0] + 40,) + tuple(calib["box"][1:]))
    if not check_join(moved)[1]:
        failures.append("SELF-TEST FAIL: a match 40 px off its recorded box passed")

    # 2. a floor the measurement cannot reach must be caught
    if not check_join(dict(calib, ncc=0.99))[1]:
        failures.append("SELF-TEST FAIL: a peak far below its recorded floor passed")

    # 3. a margin the measurement cannot reach must be caught
    if not check_join(dict(calib, control=0.10))[1]:
        failures.append("SELF-TEST FAIL: a collapsed margin over the control passed")

    # 4. the measurement itself must refuse a picture that is not on the sheet:
    #    the crop's own rows shuffled — same histogram, same size, same ink.
    rng = np.random.default_rng(1107)
    src = Image.open(PLATES / calib["crop"]).convert("L")
    arr = np.asarray(src)
    shuffled = arr[rng.permutation(arr.shape[0]), :]
    scrambled = ROOT / "tools" / f".selftest_{calib['crop']}"
    Image.fromarray(shuffled).save(scrambled)
    try:
        decoy = measure(scrambled, SHEET, _sweep(calib["scale"]))
    finally:
        scrambled.unlink(missing_ok=True)
    if decoy["ncc"] >= got["ncc"] - 0.15:
        failures.append(f"SELF-TEST FAIL: row-shuffled noise scored {decoy['ncc']} "
                        f"against the real join's {got['ncc']} — the measure does not "
                        f"discriminate")

    for line in failures:
        print(f"  {line}")
    if failures:
        print(f"  SELF-TEST FAILED: {len(failures)} assertion(s) did not fire")
        return 1
    print("  self-test: every assertion fires when broken, and row-shuffled noise "
          f"reaches only {decoy['ncc']} against the join's {got['ncc']}")
    return 0


def report():
    print("  kurz_allison_1893 — Chicago In Early Days, 1779-1857 (1893), fifteen "
          "numbered vignettes")
    print(f"  sheet: {SHEET.relative_to(REPO)}")
    print(f"  control: the 1853 bird's-eye panel, sheet pixels {CONTROL_BOX}")
    print()
    for join in JOINS:
        got, bad = check_join(join)
        print(f"  {join['crop']}  ->  panel {join['panel']}")
        print(f"      key      {join['key']}")
        print(f"      numeral  {join['numeral'] or 'none in the crop — read off the sheet'}")
        print(f"      match    ncc {got['ncc']} at {got['scale']}x, sheet px {got['box']}")
        print(f"      control  {got['control']}  (margin {got['margin']})")
        print(f"      note     {join['note']}")
        for complaint in bad:
            print(f"      FAIL     {complaint}")
        print()
    return gate(quiet=True)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="is this crop a panel of a sheet this project already holds?")
    ap.add_argument("--gate", action="store_true",
                    help="re-measure the committed joins; fail if one has moved")
    ap.add_argument("--self-test", action="store_true",
                    help="break each of the gate's assertions and watch it fire")
    ap.add_argument("--quiet", action="store_true", help="gate output only")
    ap.add_argument("--json", action="store_true", help="machine-readable reading")
    ap.add_argument("--crop", help="measure some other crop against the sheet")
    ap.add_argument("--scale", type=float, default=None,
                    help="centre of the scale sweep for --crop (default: a wide sweep)")
    args = ap.parse_args()

    if args.self_test:
        return self_test()
    if args.crop:
        scales = (_sweep(args.scale) if args.scale
                  else [round(0.10 + 0.02 * i, 4) for i in range(56)])
        got = measure(pathlib.Path(args.crop), SHEET, scales)
        got["margin"] = round(got["ncc"] - got["control"], 3)
        print(json.dumps(got, indent=1) if args.json
              else f"  ncc {got['ncc']} at {got['scale']}x, sheet px {got['box']}, "
                   f"control {got['control']} (margin {got['margin']})")
        return 0
    if args.gate:
        return gate(quiet=args.quiet)
    if args.json:
        print(json.dumps([dict(join, measured=check_join(join)[0]) for join in JOINS],
                         indent=1))
        return 0
    return report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except MissingReader as exc:
        required = bool(os.environ.get("C4D_GATE_REQUIRE_READERS"))
        print(f"  {'FAIL' if required else 'skip'} — {exc}; the four joins stand on "
              f"the banked reading in this file's JOINS table and were NOT re-measured")
        sys.exit(1 if required else 0)
    except Fault as exc:
        print(f"  FAIL — {exc}")
        sys.exit(1)
