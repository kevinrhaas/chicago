#!/usr/bin/env python3
"""Do the School Section's east-west tier lines run level, or do they carry a skew?

T-0959. `data/traces/vectors/school_section_blocks_1834.json` draws all thirteen
east-west lines LEVEL — one northing end to end — because the generator that made it
(tools/generate_school_section_grid.py) carries only the MEDIAN of the bands it
measured each line in. The medians are in that file; the band values are not, and a
median cannot tell you whether the bands trended. A rival reading of the same sheet
(PR #978, closed under T-0930) draws the same lines with 25.7 m of rise over 1,588 m,
0.93 degrees, and grades them `attested`.

This tool re-takes the measurement and KEEPS the bands. For each ruled line it samples
the registered raster in bands along the line's length, picks the darkness centroid in
each, and fits northing against easting by least squares. A line that is level in the
drawing gives a slope indistinguishable from zero; a line that carries the survey's
skew gives the same slope on every line, because one survey ruled them all.

It reads the raster THROUGH the committed registration
(data/traces/gcp/wright_1834_nara_hup_gcps.json), the same affine the grid was built
with, so its answer is about the drawing and not about a second fit.

Nothing is written unless --out is given; the tool prints its table either way.
"""
import argparse
import json
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# The measured (pre-anchor) northings of the thirteen ruled east-west lines, copied from
# tools/generate_school_section_grid.py so that this is a re-measurement of the same lines
# and not a re-discovery of different ones.
EW_MEASURED = [-545.99, -686.96, -832.66, -979.93, -1129.40, -1280.50, -1399.14,
               -1545.43, -1660.67, -1808.40, -1924.45, -2077.60, -2204.64]
EW_NAMES = ["Madison", "Monroe", "Adams", "Jackson", None, None, None, None, None,
            None, None, None, "section line (south)"]

# The fourteen ruled north-south lines, same source, same reason.
NS_MEASURED = [-768.14, -648.20, -508.13, -382.15, -270.51, -147.95, -41.80, 67.40,
               203.90, 346.36, 459.60, 577.59, 698.70, 834.90]
NS_NAMES = ["section line (west)", None, "Des Plaines", "Jefferson", "Clinton", "Canal",
            None, "Market", None, "Wells", None, "Clark", None,
            "section line (east), State Street"]
MEASURED_NORTH, MEASURED_SOUTH = -545.99, -2204.64

# The section's own east and west limits in the measured frame (the two section lines of
# the NS table), narrowed at each end so no band straddles the section line's own ink.
MEASURED_WEST, MEASURED_EAST = -768.14, 834.90


def load(p):
    return json.loads((ROOT / p).read_text())


def affine():
    gcp = load("data/traces/gcp/wright_1834_nara_hup_gcps.json")
    datum = load("data/datum.json")
    # T-1092 re-seated this trace onto the ELEVEN-POINT registration T-1091 adopted,
    # and re-baked what stands on the ground that moved. `fit` IS that registration;
    # the eight-point fit it superseded is kept beside it as `retained_fit` for the
    # adjudication that compares the two. Reading `retained_fit` here would seat the
    # ground on a fit this project no longer holds.
    c = gcp["fit"]["coefficients"]
    a, b, cc, d, e, f = c["a"], c["b"], c["c"], c["d"], c["e"], c["f"]
    det = a * e - b * d
    oE, oN = datum["origin_utm_e"], datum["origin_utm_n"]

    def local_to_pixel(x, y):
        dE, dN = (x + oE) - cc, (y + oN) - f
        return ((e * dE - b * dN) / det, (-d * dE + a * dN) / det)

    return local_to_pixel, gcp


def centroid(ys, darks, floor):
    """Darkness-weighted centroid of the peak, over the samples above `floor`."""
    num = den = 0.0
    for y, v in zip(ys, darks):
        w = v - floor
        if w > 0:
            num += y * w
            den += w
    return (num / den) if den > 0 else None


def fit(xs, ys):
    """Least squares ys = a + b*xs. Returns (b, a, rms of residuals)."""
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    b = sxy / sxx if sxx else 0.0
    a = my - b * mx
    rms = math.sqrt(sum((y - (a + b * x)) ** 2 for x, y in zip(xs, ys)) / n)
    return b, a, rms


def measure_family(axis, table, names, lo, hi, darkness, args):
    """Measure one family of ruled lines. `axis` is 'ew' or 'ns'.

    For an east-west line the bands run along easting and the pick is a northing;
    for a north-south line the bands run along northing and the pick is an easting.
    The fit is always pick-against-band, so the slope of an EW line is dy/dx and the
    slope of an NS line is dx/dy. A rigid rotation of the drawing under the
    registration makes those two slopes EQUAL AND OPPOSITE; anything else does not.
    """
    span = hi - lo
    inset = abs(span) * 0.03
    centres = [lo + inset + (span - 2 * inset) * (k + 0.5) / args.bands
               for k in range(args.bands)]
    half = args.band_width_m / 2
    nsub = 25
    steps = int(2 * args.window_m / args.step_m)

    rows = []
    for j, c0 in enumerate(table):
        picks = []
        for bc in centres:
            coords, darks = [], []
            ok = True
            for st in range(steps + 1):
                c = c0 - args.window_m + st * args.step_m
                acc = cnt = 0.0
                for t in range(nsub):
                    b = bc - half + args.band_width_m * t / (nsub - 1)
                    d = darkness(b, c) if axis == "ew" else darkness(c, b)
                    if d is not None:
                        acc += d
                        cnt += 1
                if cnt < nsub * 0.8:
                    ok = False
                    break
                coords.append(c)
                darks.append(acc / cnt)
            if not ok or not darks:
                continue
            dlo, dhi = min(darks), max(darks)
            if dhi - dlo < 12.0:       # no ruled line stands out of the paper here
                continue
            pick = centroid(coords, darks, dlo + 0.55 * (dhi - dlo))
            if pick is None:
                continue
            picks.append((bc, pick, dhi - dlo))

        row = dict(axis=axis, index=j, sheet_name=names[j],
                   committed_coord_m=c0, bands_read=len(picks))
        if len(picks) >= 4:
            xs = [p[0] for p in picks]
            ys = [p[1] for p in picks]
            b, a, rms = fit(xs, ys)
            row.update(
                slope_m_per_m=round(b, 6),
                skew_deg=round(math.degrees(math.atan(b)), 3),
                rise_over_section_m=round(b * abs(span), 2),
                band_scatter_rms_m=round(rms, 2),
                band_along_m=[round(v, 1) for v in xs],
                band_pick_m=[round(v, 2) for v in ys],
                median_pick_m=round(sorted(ys)[len(ys) // 2], 2),
                contrast_median=round(sorted(p[2] for p in picks)[len(picks) // 2], 1),
            )
        rows.append(row)
        print("  %-2s %-2d %-22s bands=%-3d %s" % (
            axis, j, names[j] or "(unnamed)", row["bands_read"],
            ("slope %+.5f = %+.3f deg  rise %+7.2f m  scatter %5.2f m" % (
                row["slope_m_per_m"], row["skew_deg"], row["rise_over_section_m"],
                row["band_scatter_rms_m"])) if "slope_m_per_m" in row else "TOO FEW BANDS"))
    return rows


def digest(rows, span):
    solid = [r for r in rows if "slope_m_per_m" in r]
    if not solid:
        return dict(lines_fitted=0)
    sl = sorted(r["slope_m_per_m"] for r in solid)
    med = sl[len(sl) // 2]
    mean = sum(sl) / len(sl)
    sd = math.sqrt(sum((s - mean) ** 2 for s in sl) / len(sl)) if len(sl) > 1 else 0.0
    pos = sum(1 for s in sl if s > 0)
    return dict(lines_fitted=len(solid),
                lines_sloping_positive=pos,
                median_slope_m_per_m=round(med, 6),
                median_skew_deg=round(math.degrees(math.atan(med)), 3),
                median_rise_over_section_m=round(med * span, 2),
                mean_slope_m_per_m=round(mean, 6),
                slope_sd=round(sd, 6),
                slope_min=round(sl[0], 6), slope_max=round(sl[-1], 6))


def conformality(gcp, ew_slope, ns_slope):
    """What the committed registration alone does to a grid that is SQUARE ON THE PAPER.

    The fit is a general affine, not a similarity: it carries a rotation AND two different
    axis scales. Such a map does not preserve angles, so a square grid goes in and a skewed
    one comes out. This works out how much, so the measurement above can be compared against
    a prediction that assumes Wright ruled square and the paper is innocent.
    """
    c = gcp["fit"]["coefficients"]
    a, b, d, e = c["a"], c["b"], c["d"], c["e"]
    det = a * e - b * d
    frob = a * a + b * b + d * d + e * e
    disc = max(frob * frob - 4 * det * det, 0.0)
    s1 = math.sqrt(max((frob + math.sqrt(disc)) / 2, 0.0))
    s2 = math.sqrt(max((frob - math.sqrt(disc)) / 2, 0.0))

    def inv(vx, vy):
        return ((e * vx - b * vy) / det, (-d * vx + a * vy) / det)

    def fwd(vx, vy):
        return (a * vx + b * vy, d * vx + e * vy)

    # Both families carried back into pixel space, so the angle the draughtsman actually
    # ruled can be compared with the angle the registered frame reports.
    pux, puy = inv(1.0, ew_slope)
    pvx, pvy = inv(ns_slope, 1.0)
    paper_angle = abs(math.degrees(math.atan2(pvy, pvx) - math.atan2(puy, pux)))
    if paper_angle > 180:
        paper_angle = 360 - paper_angle
    ground_angle = abs(math.degrees(math.atan2(1.0, ns_slope) - math.atan2(ew_slope, 1.0)))
    if ground_angle > 180:
        ground_angle = 360 - ground_angle
    # What the map alone does to a right angle laid on the paper at the plat's orientation.
    gux, guy = fwd(pux, puy)
    gwx, gwy = fwd(-puy, pux)
    square_out = abs(math.degrees(math.atan2(gwy, gwx) - math.atan2(guy, gux)))
    if square_out > 180:
        square_out = 360 - square_out
    return dict(
        # Of the eleven-point fit in force (T-1091), which is the one this measurement
        # is made through since T-1092 re-seated the grid onto it.
        rotation_deg=gcp["fit"].get("rotation_deg"),
        rms_m=gcp["fit"].get("rms_m"),
        singular_values=[round(s1, 6), round(s2, 6)],
        anisotropy_pct=round(100 * (s1 / s2 - 1), 3) if s2 else None,
        a_right_angle_on_the_paper_comes_out_at_deg=round(square_out, 3),
        angle_between_the_two_families_on_the_paper_deg=round(paper_angle, 3),
        angle_between_the_two_families_in_the_registered_frame_deg=round(ground_angle, 3),
        note=("A rotation preserves angles and would tilt the two families equally and "
              "OPPOSITELY. This map does not: its two axis scales differ by the anisotropy "
              "above, so a right angle ruled on the paper does not come out a right angle. "
              "That is the mechanism; the cardinal control below is the evidence, because it "
              "needs no assumption about what Wright ruled."),
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bands", type=int, default=10)
    ap.add_argument("--band-width-m", type=float, default=90.0)
    ap.add_argument("--window-m", type=float, default=22.0,
                    help="half-height of the search window about the committed line")
    ap.add_argument("--step-m", type=float, default=0.35)
    ap.add_argument("--out")
    args = ap.parse_args()

    try:
        from PIL import Image
    except ImportError:
        print("pillow is not installed; skipping (install pillow to run this)", file=sys.stderr)
        return 0
    Image.MAX_IMAGE_PIXELS = None

    local_to_pixel, gcp = affine()
    raster = gcp["raster"]
    img_path = ROOT.parent.parent / raster["working_copy"]
    if not img_path.exists():
        print("raster not present at %s; skipping" % img_path, file=sys.stderr)
        return 0
    im = Image.open(img_path).convert("L")
    W, H = im.size
    px = im.load()

    lac = [l["box"] for l in gcp["lacunae"]["found"]]

    def in_lacuna(u, v):
        return any(b[0] <= u <= b[2] and b[1] <= v <= b[3] for b in lac)

    def darkness(x, y):
        u, v = local_to_pixel(x, y)
        if not (0 <= u < W - 1 and 0 <= v < H - 1) or in_lacuna(u, v):
            return None
        u0, v0 = int(u), int(v)
        fu, fv = u - u0, v - v0
        g = (px[u0, v0] * (1 - fu) * (1 - fv) + px[u0 + 1, v0] * fu * (1 - fv) +
             px[u0, v0 + 1] * (1 - fu) * fv + px[u0 + 1, v0 + 1] * fu * fv)
        return 255.0 - g

    ew_span = MEASURED_EAST - MEASURED_WEST
    ns_span = MEASURED_NORTH - MEASURED_SOUTH

    print("EAST-WEST tier lines, banded along easting:")
    ew = measure_family("ew", EW_MEASURED, EW_NAMES, MEASURED_WEST, MEASURED_EAST,
                        darkness, args)
    print("\nNORTH-SOUTH lines, banded along northing:")
    ns = measure_family("ns", NS_MEASURED, NS_NAMES, MEASURED_SOUTH, MEASURED_NORTH,
                        darkness, args)

    dew = digest(ew, ew_span)
    dns = digest(ns, ns_span)
    print("\nEW: %s" % json.dumps(dew))
    print("NS: %s" % json.dumps(dns))

    verdict = None
    if dew.get("lines_fitted") and dns.get("lines_fitted"):
        a_ew = dew["median_skew_deg"]
        a_ns = dns["median_skew_deg"]
        print("\nmedian EW skew %+.3f deg; median NS skew %+.3f deg; sum %+.3f deg"
              % (a_ew, a_ns, a_ew + a_ns))
        rigid = abs(a_ew + a_ns) < 0.5 * max(abs(a_ew), abs(a_ns))
        conf = conformality(gcp, dew["mean_slope_m_per_m"], dns["mean_slope_m_per_m"])

        # THE CONTROL, and it needs no assumption about what Wright ruled. Section 16's four
        # boundaries are PLSS lines: they run true north and true east ON THE GROUND by
        # definition of the survey that laid them, and the registration's own G1 is one of
        # their corners. Whatever tilt THEY show in this frame is the frame's.
        cardinal = []
        for fam, rows_, names_, idxs in (("ew", ew, EW_NAMES, (0, len(EW_MEASURED) - 1)),
                                         ("ns", ns, NS_NAMES, (0, len(NS_MEASURED) - 1))):
            for i in idxs:
                r = rows_[i]
                if "skew_deg" in r:
                    cardinal.append(dict(axis=fam, index=i, sheet_name=names_[i],
                                         tilt_deg=r["skew_deg"],
                                         band_scatter_rms_m=r["band_scatter_rms_m"]))
        ctilt = [c["tilt_deg"] for c in cardinal]
        cmean = sum(ctilt) / len(ctilt) if ctilt else 0.0
        imean = (dew["mean_slope_m_per_m"] + dns["mean_slope_m_per_m"]) / 2
        imean_deg = math.degrees(math.atan(imean))
        control = dict(
            _doc=("Section 16's north, south, east and west boundaries are PLSS lines and run "
                  "true east-west and true north-south on the ground by definition. They are "
                  "measured here exactly as the interior lines are. Any tilt they carry in the "
                  "registered frame belongs to the frame."),
            lines=cardinal,
            mean_tilt_deg=round(cmean, 3),
            interior_mean_tilt_deg=round(imean_deg, 3),
            difference_deg=round(cmean - imean_deg, 3),
            all_tilt_the_same_way=all(t > 0 for t in ctilt) or all(t < 0 for t in ctilt),
        )
        agrees = bool(ctilt) and control["all_tilt_the_same_way"] and \
            abs(cmean - imean_deg) < 0.5 * max(abs(cmean), abs(imean_deg), 1e-9)
        verdict = dict(
            ew_median_skew_deg=a_ew, ns_median_skew_deg=a_ns,
            sum_deg=round(a_ew + a_ns, 3),
            lines_tilting_the_same_way="%d of %d east-west and %d of %d north-south" % (
                dew["lines_sloping_positive"], dew["lines_fitted"],
                dns["lines_sloping_positive"], dns["lines_fitted"]),
            is_a_rigid_rotation=rigid,
            reads_as="a rigid rotation of the drawing under the registration"
                     if rigid else
                     "NOT a rigid rotation: the two families do not tilt equally and "
                     "oppositely, which is a grid that has stopped being square",
            cardinal_control=control,
            the_frame_tilts_lines_known_to_be_cardinal=agrees,
            conformality=conf,
            ruling=("THE TILT IS THE FRAME'S, NOT WRIGHT'S. Two things say so and neither "
                    "assumes anything about the drawing. First, every line of BOTH families "
                    "tilts the same way; a rotation of the drawing under its registration "
                    "tilts them equally and oppositely, so this is not one. Second, the "
                    "section's four PLSS boundaries — lines that run true north and true east "
                    "on the ground by definition — tilt in this frame by the same amount and "
                    "the same way as the interior lines do. A frame that tilts a line known to "
                    "be cardinal is telling you about itself. The mechanism is in "
                    "`conformality`: the fit is a general affine with two different axis "
                    "scales, so it does not preserve angles. The committed grid is rescaled "
                    "onto the section's own statute-mile square, which takes that distortion "
                    "out with the rest of it — so LEVEL IS RIGHT, and right for a stated reason "
                    "rather than because a median was carried. The grade stays `inferred`: a "
                    "tilt the frame puts on its own control is not attested by the survey."
                    if (not rigid and agrees) else
                    "UNSETTLED — the measurement does not reproduce the pattern this ruling was "
                    "written for; re-read it rather than quoting it."),
        )
        print("reads as: %s" % verdict["reads_as"])
        print("CARDINAL CONTROL — the section's four PLSS boundaries, true north and east on "
              "the ground, measure %+.3f deg of tilt in this frame against %+.3f deg for the "
              "interior lines" % (cmean, imean_deg))
        print("a right angle ruled on the paper leaves this fit at %.3f deg"
              % conf["a_right_angle_on_the_paper_comes_out_at_deg"])
        print("RULING: %s" % verdict["ruling"])

    if args.out:
        out = dict(
            _doc=__doc__.strip(),
            ticket="T-0959",
            generated_by="tools/measure_school_section_tier_skew.py",
            source="wright_1834_nara_hup",
            raster={k: raster[k] for k in ("working_copy", "sha256", "width", "height")},
            registration="data/traces/gcp/wright_1834_nara_hup_gcps.json",
            method=dict(bands=args.bands, band_width_m=args.band_width_m,
                        window_m=args.window_m, step_m=args.step_m,
                        pick="darkness-weighted centroid above 55% of the band's own range",
                        rejected="a band with no ruled line above 12/255 of contrast, or any "
                                 "sample falling in a lacuna box, is dropped rather than picked"),
            east_west=dict(span_m=round(ew_span, 2), summary=dew, lines=ew),
            north_south=dict(span_m=round(ns_span, 2), summary=dns, lines=ns),
            verdict=verdict,
        )
        p = ROOT / args.out
        p.write_text(json.dumps(out, indent=2, ensure_ascii=True) + "\n")
        print("\nwrote %s" % args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
