"""T-3385: from tone_read.py's medians, the brick's reflectance as the plate saw it, relative to
two references in the same picture, and the palette hypotheses each reading allows.

    python3 classify.py readings.jsonl

The print is modelled as value = black + (white - black) * (R / R_white) ^ (1 / gamma) (T-3244's
model), so two surfaces in one light give R_a / R_b = ((v_a - black) / (v_b - black)) ^ gamma,
gamma 1.8-2.2. References: the light dressings on the same face (limestone_trim, dress_stone,
carved_trim; taken as a light limestone, linear 0.45, 0.42, 0.35) and the house's slate (neutral
0.12; on a different plane, so a weaker check). Plates: blue-sensitive and orthochromatic.
"""
import json, sys

PLATES = {"blue": (0.05, 0.15, 0.80), "ortho": (0.05, 0.45, 0.50)}
LIMESTONE = (0.45, 0.42, 0.35)
SLATE = (0.12, 0.12, 0.12)
# palette means (linear), k03_face_brick.json; kept here so the note reproduces on its own
HYP = {
    "pressed_red": (0.300, 0.075, 0.048),
    "pressed_red_deep": (0.197, 0.050, 0.035),
    "red_brown": (0.197, 0.098, 0.068),
    "pressed_brown": (0.140, 0.075, 0.050),
    "pressed_buff": (0.391, 0.251, 0.115),
    "common_buff": (0.407, 0.256, 0.154),
    "common_salmon": (0.407, 0.220, 0.139),
}


def plate(rgb, w):
    return sum(a * b for a, b in zip(rgb, w))


def predicted(ref):
    return {h: [plate(c, w) / plate(ref, w) for w in PLATES.values()] for h, c in HYP.items()}


def implied(v, r, k):
    if v is None or r is None or r - k < 8:
        return None
    x = max(v - k, 1.0) / (r - k)
    return (x ** 2.2, x ** 1.8)


def fits(rng, pred):
    lo, hi = min(rng), max(rng)
    out = []
    for h, (b, o) in pred.items():
        plo, phi = min(b, o), max(b, o)
        gap = 0.0 if (plo <= hi and phi >= lo) else min(abs(plo - hi), abs(phi - lo))
        out.append((gap / max(phi, 1e-6), h))
    out.sort()
    return [h for g, h in out if g < 0.25][:4] or [out[0][1] + "?"]


def main(path):
    pt, ps = predicted(LIMESTONE), predicted(SLATE)
    for line in open(path):
        d = json.loads(line)
        k = d["print_black_p1"]
        cam = d["camera"].split("/")
        for which, trim in (("brick_front", "trim_front"), ("brick_side", "trim_side")):
            b = d.get(which)
            if not b or b["n"] < 400:
                continue
            t = d.get(trim) if d.get(trim, {}).get("n", 0) >= 200 else None
            s = d.get("slate") if d.get("slate", {}).get("n", 0) >= 400 else None
            rt = implied(b["median"], t and t["median"], k)
            rs = implied(b["median"], s and s["median"], k)
            print(f'{cam[2][:30]:30} {cam[3][:-5][:24]:24} {which:11} b{b["median"]:4.0f}'
                  f' trim {t["median"] if t else "-":>5} slate {s["median"] if s else "-":>5} k{k:3.0f}'
                  f' | vs trim {"%.2f-%.2f" % rt if rt else "    -    "} {",".join(fits(rt, pt)) if rt else "":40}'
                  f' | vs slate {"%.2f-%.2f" % rs if rs else "    -    "} {",".join(fits(rs, ps)) if rs else ""}')


if __name__ == "__main__":
    main(sys.argv[1])
