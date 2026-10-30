#!/usr/bin/env python3
"""T-3046 (of T-3026): Glessner's course relief, high courses against low, re-read on the LAID beds.

T-3044's `read_courses.py` placed each course on the printed string's beds, which the model
laid until T-3045. Since T-3045 the model lays beds 8-23 at `ashlar_course_scale` over the
printed inches, so a relief row read on the printed beds straddles two courses. This reader
uses T-3044's own camera, sampling, opening registration and lip measure unchanged, and only
re-bases the beds: the render's are the laid string's, and the photograph's are the laid
string fitted to it about bed 7 (the fit reads about 1.0 since T-3045).

  node tools/photo_match.mjs data/reference_views/glessner_house/taylor-2135-ne.json --out /tmp/x
  python3 docs/RESEARCH/glessner-course-relief-T-3046/read_relief.py --render <the bare render> [--out f.json]
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    "read_courses", HERE.parent / "glessner-course-reading-T-3044" / "read_courses.py")
rc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rc)


def laid_beds():
    """The beds as masonry_house_params lays them: the printed inches, scaled between two beds."""
    rec = json.loads(rc.RECORD.read_text())
    v = rec["phases"][0]["form"]["v4_detail"]["value"]
    courses = v["ashlar_courses_in"]
    stretch = v.get("ashlar_course_scale") or {}
    lo, hi = stretch.get("beds", (0, 0))
    laid = [h * (stretch["scale"] if lo < i + 1 <= hi else 1.0) for i, h in enumerate(courses)]
    return courses, rc.NG_OVER_WALK + np.cumsum(laid) / 12.0


def read(render_path):
    photo, render = rc.gray(rc.PHOTO), rc.gray(render_path)
    courses, beds = laid_beds()
    bed7 = float(beds[6])
    cal = rc.openings(photo, render)
    zs = np.arange(0, 26, 0.01)
    z = np.arange(8.0, 22.6, 0.01)
    zz = np.arange(0, 26, 0.005)
    piers, rows = {}, []
    for key, (t0, t1, half) in rc.PIERS.items():
        p = rc.profile(photo, "prairie", t0, t1, zs)
        r = rc.profile(render, "prairie", t0, t1, zs)
        s, o = cal[half]["scale"], cal[half]["offset_ft"]
        pz = rc.norm(np.interp(s * z + o, zs, p))
        cc, k, off = rc.fit(pz, z, r, zs, bed7)
        piers[key] = {"corr": round(float(cc), 3), "scale_about_bed7": round(float(k), 4),
                      "offset_ft": round(float(off), 2)}
        praw = rc.profile(photo, "prairie", t0, t1, zz, smooth=0)
        rraw = rc.profile(render, "prairie", t0, t1, zz, smooth=0)
        for i in range(7, 22):
            for src, prof, place in (("photo", praw, lambda q: s * (bed7 + off + k * (q - bed7)) + o),
                                     ("render", rraw, lambda q: q + 0.09)):
                lo, hi = place(beds[i - 1]), place(beds[i])
                band = prof[(zz > lo + 0.03 * (hi - lo)) & (zz < hi - 0.03 * (hi - lo))]
                if len(band) < 5:
                    continue
                med = float(np.median(band))
                lip = float(band[: max(2, len(band) // 4)].min())
                rows.append({"pier": key, "course": i + 1, "in": courses[i], "src": src,
                             "lip": round((med - lip) / med, 4)})
    relief = {}
    for src in ("photo", "render"):
        tall = [q["lip"] for q in rows if q["src"] == src and q["in"] >= 11.5]
        low = [q["lip"] for q in rows if q["src"] == src and q["in"] < 11.5]
        relief[src] = {"high_courses": len(tall), "low_courses": len(low),
                       "high_lip": round(float(np.mean(tall)), 3), "low_lip": round(float(np.mean(low)), 3),
                       "high_over_low": round(float(np.mean(tall) / np.mean(low)), 2)}
    return {"laid_beds_over_walk_ft": [round(float(b), 2) for b in beds], "piers": piers,
            "relief_lower_lip": relief, "relief_rows": rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--render", required=True)
    ap.add_argument("--out")
    args = ap.parse_args()
    out = read(args.render)
    if args.out:
        Path(args.out).write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: out[k] for k in ("piers", "relief_lower_lip")}, indent=1))


if __name__ == "__main__":
    main()
