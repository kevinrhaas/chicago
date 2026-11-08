#!/usr/bin/env python3
"""T-3506: no two of the 1812 Potawatomi and Miami people dressed alike.

The owner, 2026-11-08, walking the camps: "all the people look identical like all wearing the
same clothing and identical hair etc all men look same and all women ... while I can
understand a tribe may have similar things they look identical".

Every Native figure of 1812 wears one of four dressed bodies (potawatomi_man_1812, _woman_,
_boy_, _girl_), each a single set of flat cloth colours. This writes, for every Potawatomi and
Miami person with a looks file, a seeded DRESS: the colour of each piece of cloth from the
colours the 1812 dress research names (docs/RESEARCH/people-1812-3467/day.json `dress`;
docs/RESEARCH/people-1812-3461/native.json `dress_evidence`), which pieces are worn today
(the blanket set aside in the August heat, the silver, the garters, the selvage), and the
hair: where it is tied, how long, and for a few a cloth tied round the head. The runtime
(renderers/web/js/human-looks.js `dressCloth`, human-hair.js) recolours clones of the
body's own materials and hides pieces: no new model, texture or program.

Grades: the pieces and the range of colours are inferred (Keating 1824 of Metea at Fort Wayne;
Wau-Bun's goods of 13 August and its lists of the Malden presents; Hubbard 1818; the 1826-37
Lewis, Winter and McKenney-Hall portraits for the later end); which person wears which is
reconstructed (liberty L-1812-native-dress-3506).

    python3 docs/RESEARCH/native-dress-1812-3506/dress.py          # write
    python3 docs/RESEARCH/native-dress-1812-3506/dress.py --check  # verify the file is current
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LOOKS = ROOT / 'data/humans/variation/looks'
INSIDE = ROOT / 'data/humans/inside_1812.json'
INSTANCES = ROOT / 'data/humans/instances/1812'
OUT = ROOT / 'data/humans/variation/dress_1812_native.json'
TICKET = 'T-3506'
LIBERTY = 'L-1812-native-dress-3506'
GEN = 'docs/RESEARCH/native-dress-1812-3506/dress.py'

# ── the colours (linear RGB, as the dressed bodies' own materials are written) ──────────────
# Stroud and broadcloth: the trade's dark indigo and scarlet, with black and a little green.
INDIGO = [0.022, 0.032, 0.085]
NAVY = [0.03, 0.045, 0.11]
SCARLET = [0.26, 0.045, 0.035]
CRIMSON = [0.17, 0.035, 0.03]
BLACK_CLOTH = [0.016, 0.016, 0.019]
GREEN_STROUD = [0.028, 0.07, 0.04]
DEERSKIN = [0.17, 0.11, 0.065]
SMOKED = [0.12, 0.075, 0.042]
# Shirts and blouses, seen at a few metres: a check or a small print reads as its mean.
SHIRTS = {
    'blue_check': ([0.27, 0.30, 0.37], 'blue-and-white check'),
    'red_check': ([0.40, 0.19, 0.16], 'red-and-white check'),
    'brown_check': ([0.24, 0.17, 0.11], 'brown check'),
    'blue_stripe': ([0.33, 0.37, 0.46], 'blue-striped linen'),
    'madder_print': ([0.25, 0.045, 0.032], 'madder-red calico'),
    'rose_print': ([0.40, 0.15, 0.17], 'rose calico'),
    'indigo_print': ([0.07, 0.09, 0.18], 'indigo-ground calico'),
    'buff_print': ([0.44, 0.31, 0.14], 'buff-and-yellow calico'),
    'brown_print': ([0.18, 0.09, 0.05], 'brown calico'),
    'white_linen': ([0.56, 0.53, 0.46], 'plain white linen, washed'),
    'green_print': ([0.10, 0.16, 0.08], 'green calico'),
}
MEN_SHIRT = [('blue_check', 5), ('red_check', 3), ('brown_check', 2), ('blue_stripe', 2), ('madder_print', 3),
             ('indigo_print', 2), ('buff_print', 1), ('white_linen', 3), ('brown_print', 1), ('green_print', 1)]
WOMEN_SHIRT = [('madder_print', 4), ('rose_print', 3), ('indigo_print', 3), ('blue_check', 2), ('red_check', 2),
               ('buff_print', 2), ('brown_print', 2), ('white_linen', 1), ('green_print', 1)]
CHILD_SHIRT = [('madder_print', 3), ('rose_print', 2), ('blue_check', 2), ('indigo_print', 2), ('buff_print', 2),
               ('white_linen', 2), ('red_check', 1), ('brown_print', 1)]
BLANKETS = {   # body, stripe
    'white': ([0.47, 0.45, 0.39], [0.025, 0.03, 0.06], 'white, dark-barred'),
    'white_plain': ([0.50, 0.48, 0.42], [0.42, 0.40, 0.35], 'plain white'),
    'blue': ([0.035, 0.055, 0.14], [0.45, 0.43, 0.37], 'blue, white-barred'),
    'scarlet': ([0.27, 0.04, 0.035], [0.02, 0.02, 0.025], 'scarlet, black-barred'),
    'green': ([0.035, 0.08, 0.05], [0.40, 0.38, 0.33], 'green, white-barred'),
    'grey': ([0.21, 0.20, 0.18], [0.04, 0.04, 0.05], 'grey, worn'),
}
MEN_BLANKET = [('white', 5), ('white_plain', 2), ('blue', 3), ('scarlet', 3), ('green', 1), ('grey', 1)]
WOMEN_BLANKET = [('white', 3), ('white_plain', 3), ('blue', 3), ('scarlet', 2), ('grey', 2), ('green', 1)]
GARTERS = [([0.035, 0.04, 0.075], 'dark blue'), ([0.22, 0.04, 0.03], 'red'), ([0.30, 0.22, 0.06], 'yellow and red'),
           ([0.03, 0.03, 0.03], 'black')]
BELTS = [([0.06, 0.035, 0.02], 'a leather belt'), ([0.25, 0.05, 0.04], 'a red woven sash'),
         ([0.05, 0.07, 0.14], 'a blue woven sash'), ([0.22, 0.17, 0.06], 'a yellow-and-red finger-woven sash')]
RIBBON_HEM = [([0.40, 0.38, 0.32], 'the undyed selvage'), ([0.24, 0.035, 0.03], 'a red silk ribbon'),
              ([0.40, 0.30, 0.05], 'a yellow silk ribbon'), ([0.04, 0.07, 0.16], 'a blue silk ribbon')]
HEADCLOTHS = [([0.30, 0.06, 0.04], 'a red handkerchief'), ([0.06, 0.08, 0.20], 'a blue handkerchief'),
              ([0.40, 0.32, 0.10], 'a yellow print handkerchief'), ([0.50, 0.47, 0.41], 'a white handkerchief')]


def rng(pid, what):
    h = hashlib.sha256(f'{TICKET}|{pid}|{what}'.encode()).digest()
    return int.from_bytes(h[:8], 'big') / 2 ** 64


def pick(pid, what, weighted):
    total = sum(w for _, w in weighted)
    x = rng(pid, what) * total
    for k, w in weighted:
        x -= w
        if x < 0:
            return k
    return weighted[-1][0]


def one(pid, what, seq):
    return seq[int(rng(pid, what) * len(seq)) % len(seq)]


def shade(pid, what, rgb, faded=0.0):
    """A cloth's own dye lot and wear: a little lighter or darker, older cloth duller."""
    k = 0.85 + 0.3 * rng(pid, what + ':lot')
    out = [c * k for c in rgb]
    if faded:
        mean = sum(out) / 3
        out = [c + (mean * 1.15 - c) * faded for c in out]
    return [round(min(0.9, c), 4) for c in out]


def assets():
    """Each Native person's dressed body, from the drawn instances and the people at doors."""
    out = {}
    for f in sorted(INSTANCES.glob('*.json')):
        if f.name == 'index.json':
            continue
        d = json.loads(f.read_text())
        a = d.get('appearance', {}).get('asset_id', '')
        if a.startswith('potawatomi_') and d.get('person_id'):
            out[d['person_id']] = a
    for row in json.loads(INSIDE.read_text()).get('people', []):
        if row.get('asset_id', '').startswith('potawatomi_'):
            out.setdefault(row['person'], row['asset_id'])
    return out


CHIEFS = {'black_partridge', 'blackbird', 'waubansee', 'topenebe', 'winnemeg', 'nuscotnemeg', 'keepotah',
          'waubeeneemah', 'naunongee'}


def dress_for(pid, asset, looks):
    origin = looks['heritage']['origin']
    kind = asset.split('_')[1]                     # man | woman | boy | girl
    age = looks.get('_age')
    old = age is not None and age >= 55
    faded = 0.35 if old else 0.12 * rng(pid, 'wear')
    colours, hide, worn = {}, [], []
    chief = pid in CHIEFS

    def put(mat, rgb, what, fade=faded):
        colours[mat] = shade(pid, what, rgb, fade)

    if kind == 'man':
        s = pick(pid, 'shirt', [('white_linen', 3), ('blue_check', 2), ('brown_check', 2)] if old else MEN_SHIRT)
        put('garment_upper__shirt_check_blue_1812', SHIRTS[s][0], 'shirt'); worn.append(f'a shirt of {SHIRTS[s][1]}')
        bc = pick(pid, 'breech', [('indigo', 6), ('scarlet', 2), ('black', 2)])
        put('garment_lower__breechcloth_broadcloth_blue_1812', {'indigo': INDIGO, 'scarlet': SCARLET, 'black': BLACK_CLOTH}[bc], 'breech')
        worn.append({'indigo': 'a breechcloth of blue broadcloth', 'scarlet': 'a breechcloth of red stroud', 'black': 'a breechcloth of black stroud'}[bc])
        lg = pick(pid, 'leggings', [('scarlet', 4), ('navy', 4), ('deerskin', 3), ('black', 1), ('green', 1), ('crimson', 1)])
        put('garment_lower__leggings_stroud_scarlet_1812',
            {'scarlet': SCARLET, 'navy': NAVY, 'deerskin': DEERSKIN, 'black': BLACK_CLOTH, 'green': GREEN_STROUD, 'crimson': CRIMSON}[lg], 'leggings')
        worn.append({'scarlet': 'scarlet stroud leggings', 'navy': 'blue stroud leggings', 'deerskin': 'smoked deerskin leggings',
                     'black': 'black stroud leggings', 'green': 'green stroud leggings', 'crimson': 'faded red stroud leggings'}[lg])
        if lg == 'deerskin' or rng(pid, 'selvage') < 0.25:
            hide.append('legging_selvage')
        if rng(pid, 'garters') < 0.3:
            hide.append('garters')
        else:
            g = one(pid, 'garter', GARTERS); put('accessory__garters_woven_dark_1812', g[0], 'garter', 0); worn.append(f'{g[1]} garters')
        b = one(pid, 'belt', BELTS); put('accessory__belt_leather_1812', b[0], 'belt'); worn.append(b[1])
        # The blanket: in the August heat most men have set it aside; elders and chiefs keep it.
        if rng(pid, 'blanket') < (0.75 if old or chief else 0.45):
            k = pick(pid, 'blanket_colour', MEN_BLANKET)
            put('garment_outer__blanket_wool_white_1812', BLANKETS[k][0], 'blanket')
            put('garment_outer__blanket_stripe_dark_1812', BLANKETS[k][1], 'blanket_stripe', faded * 0.5)
            worn.append(f'a {BLANKETS[k][2]} blanket')
        else:
            hide += ['blanket_wrap', 'blanket_stripes']
        if not chief and rng(pid, 'armbands') < 0.45:
            hide.append('silver_arm_bands')
        else:
            worn.append('silver armbands')
        if not chief and rng(pid, 'brooches') < 0.5:
            hide.append('silver_brooches')
        else:
            worn.append('silver brooches on the shirt')
        put('footwear__moccasins_smoked_1812', one(pid, 'moc', [DEERSKIN, SMOKED, [0.21, 0.15, 0.09]]), 'moc', 0)
    elif kind == 'woman':
        s = pick(pid, 'shirt', WOMEN_SHIRT)
        put('garment_upper__calico_shirt_1812', SHIRTS[s][0], 'shirt'); worn.append(f'a blouse of {SHIRTS[s][1]}')
        sk = pick(pid, 'skirt', [('indigo', 6), ('black', 3), ('navy', 2), ('crimson', 1)])
        put('garment_lower__strouding_skirt_blue_1812', {'indigo': INDIGO, 'black': BLACK_CLOTH, 'navy': NAVY, 'crimson': CRIMSON}[sk], 'skirt')
        worn.append({'indigo': 'a wrapped skirt of dark blue stroud', 'black': 'a wrapped skirt of black stroud',
                     'navy': 'a wrapped skirt of blue stroud', 'crimson': 'a wrapped skirt of red stroud'}[sk])
        hem = RIBBON_HEM[0] if rng(pid, 'ribbon') < 0.65 else one(pid, 'ribbon_colour', RIBBON_HEM[1:])
        put('garment_lower__strouding_selvage_white_1812', hem[0], 'hem', 0); worn.append(f'{hem[1]} at the hem')
        lg = pick(pid, 'leggings', [('scarlet', 5), ('navy', 3), ('green', 1), ('black', 1)])
        put('garment_lower__cloth_leggings_red_1812', {'scarlet': CRIMSON, 'navy': NAVY, 'green': GREEN_STROUD, 'black': BLACK_CLOTH}[lg], 'leggings')
        worn.append({'scarlet': 'red cloth leggings', 'navy': 'blue cloth leggings', 'green': 'green cloth leggings', 'black': 'black cloth leggings'}[lg])
        if rng(pid, 'blanket') < (0.7 if old else 0.45):
            k = pick(pid, 'blanket_colour', WOMEN_BLANKET)
            put('garment_outer__trade_blanket_white_1812', BLANKETS[k][0], 'blanket'); worn.append(f'a {BLANKETS[k][2]} blanket')
        else:
            hide.append('trade_blanket')
        if rng(pid, 'brooches') < 0.3:
            hide.append('silver_brooches')
        else:
            worn.append('silver brooches at the neck')
        put('footwear__moccasins_smoked_1812', one(pid, 'moc', [DEERSKIN, SMOKED, [0.21, 0.15, 0.09]]), 'moc', 0)
    elif kind == 'boy':
        s = pick(pid, 'shirt', CHILD_SHIRT)
        put('garment_upper__calico_shirt_madder_1812', SHIRTS[s][0], 'shirt'); worn.append(f'a shirt of {SHIRTS[s][1]}')
        lg = pick(pid, 'leggings', [('navy', 4), ('scarlet', 3), ('deerskin', 2)])
        put('garment_lower__stroud_leggings_blue_1812', {'navy': NAVY, 'scarlet': SCARLET, 'deerskin': DEERSKIN}[lg], 'leggings')
        worn.append({'navy': 'blue stroud leggings', 'scarlet': 'red stroud leggings', 'deerskin': 'deerskin leggings'}[lg])
    else:  # girl
        s = pick(pid, 'shirt', CHILD_SHIRT)
        put('garment_upper__calico_blouse_rose_1812', SHIRTS[s][0], 'shirt'); worn.append(f'a blouse of {SHIRTS[s][1]}')
        sk = pick(pid, 'skirt', [('indigo', 5), ('black', 2), ('navy', 2)])
        put('garment_lower__stroud_skirt_blue_1812', {'indigo': INDIGO, 'black': BLACK_CLOTH, 'navy': NAVY}[sk], 'skirt')
        lg = pick(pid, 'leggings', [('scarlet', 4), ('navy', 2), ('green', 1)])
        put('garment_lower__stroud_leggings_red_1812', {'scarlet': SCARLET, 'navy': NAVY, 'green': GREEN_STROUD}[lg], 'leggings')
        worn.append('a wrapped stroud skirt and cloth leggings')

    hair = hair_for(pid, kind, looks, old)
    if hair.get('headcloth'):
        worn.append(f"{hair['headcloth']['what']} tied round the head")
    return {'asset': asset, 'origin': origin, 'colours': colours, 'hide': sorted(set(hide)), 'hair': hair,
            'worn': '; '.join(worn)}


HAIR_MEN = [('clubbed_behind_1812', 5), ('tied_high_1812', 2), ('clubbed_long_1812', 3), ('side_part_tied_1812', 2)]
HAIR_WOMEN = [('centre_part_clubbed_1812', 5), ('centre_part_low_1812', 3), ('centre_part_tied_high_1812', 2)]


def hair_for(pid, kind, looks, old):
    base = looks.get('hair', {})
    h = {}
    if kind in ('man', 'boy'):
        h['cut'] = pick(pid, 'cut', HAIR_MEN if kind == 'man' else [('clubbed_behind_1812', 1), ('tied_high_1812', 1)])
        h['tail_cm'] = 0 if kind == 'boy' else round(8 + 16 * rng(pid, 'tail'), 1)
    else:
        h['cut'] = pick(pid, 'cut', HAIR_WOMEN)
        h['tail_cm'] = round(10 + 18 * rng(pid, 'tail'), 1) if kind == 'woman' else round(6 + 8 * rng(pid, 'tail'), 1)
    if not old and base.get('drawn') == 'black':
        h['drawn'] = pick(pid, 'hair_colour', [('black', 6), ('blue_black', 2), ('black_brown', 2)])
    # A handkerchief tied round the head: a minority in 1812 (the cloth turbans of the 1830s
    # portraits are later); men and some older women.
    if kind == 'man' and rng(pid, 'headcloth') < (0.25 if old else 0.12) or kind == 'woman' and rng(pid, 'headcloth') < 0.08:
        c = one(pid, 'headcloth_colour', HEADCLOTHS)
        h['headcloth'] = {'rgb': shade(pid, 'headcloth', c[0], 0.1), 'what': c[1]}
    return h


def build():
    persons = {}
    for pid, asset in sorted(assets().items()):
        f = LOOKS / f'{pid}.json'
        if not f.exists():
            continue
        looks = json.loads(f.read_text())
        if looks.get('heritage', {}).get('origin') not in ('Potawatomi', 'Miami'):
            continue
        looks['_age'] = age_of(pid)
        persons[pid] = dress_for(pid, asset, looks)
    return {
        'format': 'chicago4d_human_dress_v1', 'ticket': TICKET, 'scene': '1812', 'generated_by': GEN, 'liberty': LIBERTY,
        '_doc': ('Each Potawatomi and Miami person\'s own dress of 14 August 1812: `colours` (linear RGB) replace the '
                 'named material\'s colour on clones (human-looks.js dressCloth), `hide` names pieces of the dressed '
                 'body not worn today, `hair` overrides the looks cut and colour and may add a tied tail and a '
                 'headcloth (human-hair.js). Pieces and colour range inferred from the 1812 dress research; who wears '
                 'what is reconstructed. Regenerate with the generator; never edit by hand.'),
        'persons': persons,
    }


_AGES = None


def age_of(pid):
    global _AGES
    if _AGES is None:
        _AGES = {}
        for f in (ROOT / 'data/residents_1812/households').glob('*.json'):
            for p in json.loads(f.read_text()).get('persons', []):
                band = p.get('age_band') or {}
                if isinstance(band.get('low'), int):
                    _AGES[p['id']] = (band['low'] + band.get('high', band['low'])) / 2
    return _AGES.get(pid)


def main():
    text = json.dumps(build(), indent=1, ensure_ascii=False) + '\n'
    if '--check' in sys.argv:
        if not OUT.exists() or OUT.read_text() != text:
            raise SystemExit(f'{OUT.relative_to(ROOT)} is stale: run {GEN}')
        print('dress file current')
        return
    OUT.write_text(text)
    d = json.loads(text)
    print(f"wrote {OUT.relative_to(ROOT)}: {len(d['persons'])} people")


if __name__ == '__main__':
    main()
