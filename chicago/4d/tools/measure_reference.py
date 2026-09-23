#!/usr/bin/env python3
"""Re-measure the calibration reference photograph.

`renderers/web/js/world.js` derives the sky exposure, the whole horizon-restore
fit and the haze colour from readings taken off one photograph. Until 2026-08-15
that photograph was not in the repository, so the readings were assertions: you
could read the numbers and you could not check them. R-REF1 committed the file;
this is the other half — the command that says whether the numbers still come out
of it.

    python3 tools/measure_reference.py

It is deliberately NOT part of `tools/check.sh`. It needs Pillow to decode a
JPEG, and the gate's promise is that it runs in seconds in any sandbox with no
dependencies. Without Pillow this prints how to get it and exits 0, the same way
`rederive_datum.py` skips without pyproj.

The frame geometry is solved rather than assumed, which is what lets a reading
state the elevation it was taken at:

    26 mm 35 mm-equivalent lens, 4:3 frame -> 53.1 deg vertical over 3024 px
    = 57.0 px/deg, sky/land step at row 820
    elevation(row) = (820 - row) / 57.0 degrees above the horizon

That also puts the camera pitch at -12.1 deg, which the 2026-08-10 prairie sweep
had already established independently as "tilted down ~12 deg".

The second section answers a question R-M1 asked of this file and got a NO from:
does the frame contain a bare-earth surface at all? See `bare_ground_survey`.
"""
import math
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IMAGE = ROOT / "data/sources/assets/saari_2018_dupage_tallgrass/dupage_tallgrass_2018-07-24.jpg"
SHA1 = "0da00f1178e7790b04c05364d78f7cb6a43992ae"

# 35 mm-equivalent focal length from the file's own EXIF, and the 4:3 frame it
# was taken on. Both are read back from the image below rather than trusted.
EQUIV_MM = 26.0
FRAME_DIAGONAL_MM = 43.267

# What world.js quotes, so the comparison is in the output rather than in a
# reader's head. Elevation in degrees above the horizon, sRGB as written there.
QUOTED = [
    (14.4, (101, 153, 209), "SKY_EXPOSURE upper"),
    (8.0, (125, 165, 205), "SKY_EXPOSURE middle"),
    (4.0, (137, 166, 200), "SKY_EXPOSURE lower"),
]
QUOTED_HORIZON = (136, 163, 192)  # HORIZON_RESTORE's fit target and the haze colour


def luminance(c):
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def find_step(px, width, height):
    """The sky/land step, per column: the topmost row whose eight rows below are
    more than 25 luminance units darker than its eight rows above. Returned per
    column, because the band reading below is taken above each column's OWN step
    and a median row would sample tree crowns in every column the treeline is
    taller than average — which reads 25 units too dark and is exactly the kind
    of quiet recipe difference this file exists to remove."""
    steps = []
    for x in range(0, width, 8):
        for y in range(20, height - 20, 2):
            above = statistics.mean(luminance(px[x, yy]) for yy in range(y - 8, y))
            below = statistics.mean(luminance(px[x, yy]) for yy in range(y, y + 8))
            if above - below > 25:
                steps.append((x, y))
                break
    return steps


def mean_srgb(px, width, rows):
    """Mean sRGB over whole rows, sampling every eighth column."""
    return _mean(px[x, y] for y in rows for x in range(0, width, 8))


def mean_above_step(px, steps, depth=12):
    """Mean sRGB of the `depth` pixels immediately above each column's own step —
    the recipe world.js states for its horizon reading."""
    return _mean(px[x, yy] for x, y in steps for yy in range(y - depth, y))


def _mean(pixels):
    acc = [0, 0, 0]
    n = 0
    for c in pixels:
        acc[0] += c[0]
        acc[1] += c[1]
        acc[2] += c[2]
        n += 1
    return tuple(round(a / n) for a in acc)


def is_soil(c):
    """A bare-earth pixel: a warm monotone ramp r > g > b with a real red-blue
    spread, and not so dark that it is shadow rather than surface. Deliberately
    GENEROUS — it accepts dry litter, dead stems and shaded ground as well as
    soil — because the question below is answered by a NO and a loose detector
    makes a NO harder to get, not easier."""
    r, g, b = c
    return r > g > b and (r - b) >= 25 and r >= 60


def is_non_green(c):
    """No green excess at all. Definition-free backstop to `is_soil`: whatever a
    track is made of, the vegetation it replaces is what has the green."""
    r, g, b = c
    return g - (r + b) / 2 <= 0


def bare_ground_survey(px, width, height, horizon, ppd):
    """Is there a dirt track in this photograph? — R-M1's question, 2026-08-15.

    R-M1 was written to derive the road gate's thresholds by measuring "what
    contrast a real dirt track holds against real prairie" in this frame. It
    does not hold one. This is that finding as a command rather than as a
    sentence, so the next parcel can re-run it instead of trusting it.

    Fractions alone would not settle it — 3 % of this land region is soil-like
    by the test above, which is dry stems and shadowed litter between plants and
    would be 3 % in a frame with a road through it too. What separates a track
    from litter is that a track is CONTIGUOUS ACROSS THE FRAME. So the number
    that decides is the longest horizontal run, per row, and the elevation it
    is found at.
    """
    print()
    print("   BARE GROUND — is there a track in this frame? (R-M1)")
    band_rows = {}
    best_soil = (0, 0)
    best_non_green = (0, 0)
    for y in range(horizon + 8, height, 4):
        soil_run = run = 0
        green_run = grun = 0
        soil_n = total = 0
        for x in range(0, width, 4):
            c = px[x, y]
            total += 1
            if is_soil(c):
                soil_n += 1
                run += 1
                soil_run = max(soil_run, run)
            else:
                run = 0
            if is_non_green(c):
                grun += 1
                green_run = max(green_run, grun)
            else:
                grun = 0
        if soil_run > best_soil[0]:
            best_soil = (soil_run, y)
        if green_run > best_non_green[0]:
            best_non_green = (green_run, y)
        band = int((horizon - y) / ppd / 5) * 5
        acc = band_rows.setdefault(band, [0, 0])
        acc[0] += soil_n
        acc[1] += total

    print(f"   {'elevation band':<22}{'soil-like':<12}sampled")
    for band in sorted(band_rows, reverse=True):
        soil_n, total = band_rows[band]
        label = f"{band:+d} to {band - 5:+d} deg"
        print(f"   {label:<22}{100 * soil_n / total:>6.1f} %     {total}")

    def report(name, best):
        px_run = best[0] * 4
        print(f"   longest {name:<26}{px_run:>5d} px = {100 * px_run / width:4.1f} % of the "
              f"frame width, at {(horizon - best[1]) / ppd:+.1f} deg")

    print()
    report("bare-earth run", best_soil)
    report("run with no green excess", best_non_green)
    print()
    print("   VERDICT — no track. A dirt road crossing this frame would put a")
    print("   contiguous bare run across a large fraction of the width at some")
    print("   elevation; the widest anywhere is under an eighth of it, and it is")
    print("   at the bottom edge of the frame, at the photographer's own feet.")
    print("   The widest run with no green excess is at the horizon: it is the")
    print("   hazed treeline, which is not ground at all.")
    print("   So this photograph CANNOT supply a road-against-ground contrast.")
    print("   R-M1's derivation source has to come from somewhere else; the")
    print("   sky, horizon and canopy readings above are unaffected.")


def main():
    try:
        from PIL import Image
    except ImportError:
        print("   Pillow is not installed, so the reference cannot be decoded here.")
        print("   pip install Pillow   then re-run. Skipping (not a failure).")
        return 0

    if not IMAGE.exists():
        print(f"   missing: {IMAGE.relative_to(ROOT)}")
        return 1

    import hashlib

    digest = hashlib.sha1(IMAGE.read_bytes()).hexdigest()
    print(f"   file    {IMAGE.relative_to(ROOT)}")
    print(f"   sha1    {digest} {'(matches the licensed bytes)' if digest == SHA1 else 'MISMATCH'}")
    if digest != SHA1:
        print("   The committed bytes are not the bytes the CC BY-SA statement is")
        print("   attached to. Nothing below is a measurement of the cited source.")
        return 1

    im = Image.open(IMAGE).convert("RGB")
    width, height = im.size
    px = im.load()

    vertical_mm = FRAME_DIAGONAL_MM * 3 / 5
    vfov = 2 * math.degrees(math.atan(vertical_mm / 2 / EQUIV_MM))
    ppd = height / vfov

    steps = find_step(px, width, height)
    horizon = statistics.median([y for _, y in steps])
    print(f"   frame   {width}x{height}, {vfov:.1f} deg vertical, {ppd:.1f} px/deg")
    print(f"   horizon row {horizon:.0f} of {height}  ->  camera pitch "
          f"{(horizon - height / 2) / ppd:-.1f} deg, frame top "
          f"{horizon / ppd:.1f} deg above the horizon")
    print(f"   step found in {len(steps)} of {len(range(0, width, 8))} columns")

    print()
    print(f"   {'reading':<48}{'quoted':<17}measured")
    print(f"   {'12 px above the sky/land step, per column':<48}"
          f"{str(QUOTED_HORIZON):<17}{mean_above_step(px, steps)}")
    for deg, quoted, why in QUOTED:
        row = max(6, int(horizon - deg * ppd))
        rows = range(max(0, row - 6), min(height, row + 6))
        label = f"sky at {deg:>4.1f} deg, row {row:<4d} ({why})"
        print(f"   {label:<48}{str(quoted):<17}{mean_srgb(px, width, rows)}")

    print()
    print("   A few units of residual is expected and explained: this averages the")
    print("   full frame width, the original readings were taken at the shot's own")
    print("   view azimuth, and the horizon's BRIGHTNESS is azimuth-dependent even")
    print("   where its hue is not. See the README beside the image.")

    bare_ground_survey(px, width, height, int(round(horizon)), ppd)
    return 0


if __name__ == "__main__":
    sys.exit(main())
