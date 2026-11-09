#!/usr/bin/env python3
"""T-3520: no two of the 1812 town's children dressed alike, and the girls look like girls.

The owner, 2026-11-08, of the children in the fort yard: "they all look identical", then
"their hair is short they all look like boys i am not sure that is typical".

The town's nineteen children wear three dressed bodies (child_toddler_1812, child_girl_1812,
child_boy_1812), each one set of flat cloth colours and the same cropped hair: eight little
ones in one white frock, six girls in one rose frock and pinafore, five boys in one blue suit.
This writes, for each, a seeded DRESS in the shape of the Native people's
(data/humans/variation/dress_1812_native.json, T-3506): the colour of each piece of cloth,
the pinafore worn or not, the shoes, and the hair: its cut, and for a girl the plait hanging
down her back. tools/human_variation_kit.py carries it into the persons table; the runtime
(renderers/web/js/human-looks.js `dressCloth`, human-hair.js) recolours clones of the body's
own materials, hides the pinafore, and grows the hair: no new model, texture or program.

What it decides, said here (liberty L-1812-children-dress-3520):

  * CLOTH. The little ones' frocks: white muslin was the frock of a family that could keep it
    white, and the period pictures of eastern children show it most; at a frontier post the
    commoner frocks were coloured cottons, checks and sprigged prints that hid the dirt. So two
    in eight stay white and the rest take a print or a check. The girls' frocks the same range
    in stronger grounds (madder, indigo, green, buff, lilac, a brown check), most with a
    pinafore over, white or unbleached. The boys' skeleton suits blue, brown, green, grey,
    nankeen or plum, the collar white. Which child wears which is drawn from a seeded order so
    that no two of a kind share a colour while the palette lasts.
  * HAIR. Boys keep a crop, some cut straight across the brow and fuller. Girls wear their hair
    longer than a boy's, parted in the middle: most worn loose, curling to the shoulders; the
    rest drawn back and plaited, the plait hanging down the back (15 to 30 cm). The little
    girls among the toddlers wear it loose to the neck, the little boys a crop. The eastern portraits of about
    1805-1815 (Joshua Johnson's children) show some girls with hair cut short in curls, a
    fashion of the cities; the longer plait for a girl of a soldier's or a trader's family is
    our reconstructed choice, not a recorded fact of any of them.

Run from chicago/4d:
    python3 docs/RESEARCH/children-1812-3520/children.py          # write
    python3 docs/RESEARCH/children-1812-3520/children.py --check  # verify the file is current
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LOOKS = ROOT / 'data/humans/variation/looks'
INSTANCES = ROOT / 'data/humans/instances/1812'
OUT = ROOT / 'data/humans/variation/dress_1812_children.json'
TICKET = 'T-3520'
LIBERTY = 'L-1812-children-dress-3520'
GEN = 'docs/RESEARCH/children-1812-3520/children.py'
SOURCES = ['met_johnson_1805_rutter_children', 'met_johnson_1805_emma_van_name', 'met_ci_1813_beecher_child_dress',
           'kinzie_waubun_1856', 'quaife_1913']

# Linear RGB, as the dressed bodies' own materials are written. A check or a small print seen at
# a few metres reads as its mean.
TODDLER_FROCKS = [
    ('white', [0.66, 0.65, 0.61], 'white muslin'),
    ('white_worn', [0.60, 0.58, 0.52], 'white muslin, washed grey'),
    ('cream', [0.58, 0.52, 0.40], 'unbleached cotton'),
    ('blue_check', [0.30, 0.36, 0.46], 'blue-and-white check'),
    ('pink_sprig', [0.52, 0.30, 0.29], 'pink sprigged cotton'),
    ('buff', [0.47, 0.36, 0.20], 'buff calico'),
    ('lilac', [0.38, 0.30, 0.42], 'lilac print'),
    ('green_sprig', [0.27, 0.34, 0.21], 'green sprigged cotton'),
]
TODDLER_SHOES = [('red', [0.30, 0.045, 0.035], 'red'), ('brown', [0.09, 0.05, 0.03], 'brown'), ('black', [0.02, 0.019, 0.018], 'black')]
GIRL_FROCKS = [
    ('rose', [0.40, 0.22, 0.20], 'faded rose print'),
    ('madder', [0.24, 0.07, 0.05], 'madder-red calico'),
    ('indigo', [0.07, 0.10, 0.20], 'indigo-ground print'),
    ('blue', [0.21, 0.28, 0.40], 'faded blue cotton'),
    ('green', [0.09, 0.15, 0.08], 'green print'),
    ('buff', [0.44, 0.32, 0.15], 'buff-and-yellow calico'),
    ('lilac', [0.30, 0.21, 0.33], 'lilac print'),
    ('brown_check', [0.20, 0.13, 0.08], 'brown check'),
]
PINAFORES = [('white', [0.70, 0.69, 0.63], 'a white linen pinafore'), ('unbleached', [0.56, 0.49, 0.37], 'an unbleached linen pinafore'),
             ('none', None, 'no pinafore')]
SUITS = [
    ('blue', [0.03, 0.04, 0.095], None, 'dark blue'),
    ('brown', [0.11, 0.065, 0.04], None, 'brown'),
    ('green', [0.03, 0.075, 0.045], None, 'bottle green'),
    ('grey', [0.15, 0.15, 0.14], None, 'grey'),
    ('nankeen', [0.07, 0.06, 0.05], [0.48, 0.37, 0.20], 'a dark jacket over nankeen trousers'),
    ('plum', [0.11, 0.045, 0.07], None, 'plum'),
]
GIRL_HAIR = [('girl_plait_1812', 1), ('girl_curls_1812', 2)]


def rng(pid, what):
    return int(hashlib.sha256(f'{TICKET}:{pid}:{what}'.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def order(pids, what):
    """A seeded order of `pids`: the i-th takes the palette's i-th colour, so none repeat while it lasts."""
    return sorted(pids, key=lambda p: rng(p, what))


def pick(pid, what, weighted):
    total = sum(w for _, w in weighted)
    u = rng(pid, what) * total
    for v, w in weighted:
        u -= w
        if u <= 0:
            return v
    return weighted[-1][0]


def children():
    out = {}
    for f in sorted(INSTANCES.glob('hi_town_*.json')):
        r = json.loads(f.read_text())
        if r.get('display') != 'shown':
            continue
        a = r['appearance']['asset_id']
        if a in ('child_toddler_1812', 'child_girl_1812', 'child_boy_1812'):
            out[r['person_id']] = a
    return out


def main(check=False):
    kids = children()
    want = {}
    by = {a: [p for p, x in kids.items() if x == a] for a in set(kids.values())}
    for i, pid in enumerate(order(by.get('child_toddler_1812', []), 'frock')):
        name, rgb, what = TODDLER_FROCKS[i % len(TODDLER_FROCKS)]
        shoe = TODDLER_SHOES[int(rng(pid, 'shoes') * len(TODDLER_SHOES))]
        looks = json.loads((LOOKS / f'{pid}.json').read_text())
        girl = looks['hair']['cut'] != 'cropped_1812'   # the reading's sex, as looks.py cut it
        hair = {'cut': 'toddler_curls_1812' if girl else 'cropped_1812'}
        want[pid] = {'asset': 'child_toddler_1812', 'colours': {
            'garment_upper__toddler_frock_white_1812': rgb, 'garment_lower__toddler_frock_white_1812': rgb,
            'footwear__toddler_shoes_red_1812': shoe[1]}, 'hide': [], 'hair': hair,
            'worn': f"a frock of {what}, {shoe[2]} shoes; {'hair loose to the neck' if girl else 'hair cropped'}"}
    for i, pid in enumerate(order(by.get('child_girl_1812', []), 'frock')):
        name, rgb, what = GIRL_FROCKS[i % len(GIRL_FROCKS)]
        pin = PINAFORES[0 if rng(pid, 'pinafore') < 0.45 else 1 if rng(pid, 'pinafore') < 0.75 else 2]
        cut = pick(pid, 'hair', GIRL_HAIR)
        hair = {'cut': cut}
        if cut == 'girl_plait_1812':
            hair['tail_cm'] = round(15 + 15 * rng(pid, 'plait'), 1)
        colours = {'garment_upper__frock_bodice_rose_1812': rgb, 'garment_lower__frock_skirt_rose_1812': rgb}
        if pin[1]:
            colours['garment_outer__pinafore_linen_1812'] = pin[1]
        want[pid] = {'asset': 'child_girl_1812', 'colours': colours, 'hide': [] if pin[1] else ['pinafore_apron', 'pinafore_bib'],
                     'hair': hair,
                     'worn': f"a frock of {what}, {pin[2]}; " + (f"hair plaited down the back, {hair['tail_cm']:.0f} cm" if 'tail_cm' in hair else 'hair worn loose to the shoulders')}
    for i, pid in enumerate(order(by.get('child_boy_1812', []), 'suit')):
        name, jacket, trousers, what = SUITS[i % len(SUITS)]
        cut = 'boy_fringe_1812' if rng(pid, 'hair') < 0.5 else 'cropped_1812'
        want[pid] = {'asset': 'child_boy_1812', 'colours': {
            'garment_upper__skeleton_jacket_blue_1812': jacket, 'garment_lower__skeleton_trousers_blue_1812': trousers or jacket},
            'hide': [], 'hair': {'cut': cut},
            'worn': f"a skeleton suit, {what}; " + ('hair cut straight across the brow' if cut == 'boy_fringe_1812' else 'hair cropped')}
    for rec in want.values():
        rec['colours'] = {k: [round(x, 4) for x in v] for k, v in rec['colours'].items()}
    doc = {
        'format': 'chicago4d_human_dress_v1', 'ticket': TICKET, 'scene': '1812', 'generated_by': GEN, 'liberty': LIBERTY,
        'sources': SOURCES,
        '_doc': 'Each 1812 town child\'s own cloth colours, pinafore and hair (T-3520). Read by tools/human_variation_kit.py '
                'into the persons table beside dress_1812_native.json. The range of cloths and cuts is inferred from the '
                'eastern portraits and dress of about 1805-1815 named in the sources; which child wears which, and every '
                'girl\'s plait, is reconstructed (see the liberty). Regenerate; never edit by hand.',
        'persons': dict(sorted(want.items())),
    }
    text = json.dumps(doc, indent=1) + '\n'
    if check:
        if not OUT.exists() or OUT.read_text() != text:
            raise SystemExit(f'{OUT.relative_to(ROOT)} is stale: run python3 {GEN}')
        print(f'1812 children\'s dress: {len(want)} children, current')
        return 0
    OUT.write_text(text)
    print(f'wrote {OUT.relative_to(ROOT)}: {len(want)} children')
    return 0


if __name__ == '__main__':
    sys.exit(main('--check' in sys.argv))
