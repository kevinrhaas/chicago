#!/usr/bin/env python3
"""T-3522: no two of the 1812 townspeople dressed alike.

The owner, 2026-11-08, with a still of three 1812 townsmen on the prairie in the one black round
hat, dark waistcoat and grey trousers: "you need to vary the clothing more so everyone is their
unique person in 1812 all of these guys wear the same hat and clothing so do that across the
board".

Every 1812 settler, trader, engagé, servant and townswoman wears one of five dressed bodies
(settler_1812, trader_1812, engage_1812, woman_working_1812, lady_1812), each a single set of
flat cloth colours and one hat. This writes, for every drawn person on those bodies who is not a
soldier of Heald's company (the garrison's own dress is T-3523's) and not dressed by another
dress_1812_*.json, a seeded DRESS from the period range the 1812 dress readings give for their
trade and origin:

- the colour of each piece of cloth (`colours`, by the body's own material names), with its own
  dye lot and wear;
- the pieces worn today and those left off (`hide`: a waistcoat or neckerchief off in the August
  heat, a sash or apron, the body's own hat when another is worn);
- the hat (`hat`, drawn by renderers/web/js/human-hats.js): a felt round hat of the person's
  own crown, taper and brim, a straw hat, a knitted cap with a long or short fall, or none;
  or the head handkerchief (`headcloth`, human-hair.js) the women of the country wore.

The readings: people-1812-3466 day.json `dress` (trader_1812, engage_1812, settler_1812,
black_servant_1812), people-1812-3464 day.json `dress` (officer_wife, trader_wife_matron,
soldier_wife_laundress, woman_of_the_country, working_woman_enslaved), the builders' notes in
docs/RESEARCH/people-1812-dress/. Pieces and colour ranges are those readings' (graded there:
inferred for the engagé's and the women of the country's, reconstructed for the settler's and the
trader's); who wears which is reconstructed (liberty L-1812-town-dress-3522).

    python3 docs/RESEARCH/town-dress-1812-3522/dress.py          # write
    python3 docs/RESEARCH/town-dress-1812-3522/dress.py --check  # verify the file is current
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
INSTANCES = ROOT / 'data/humans/instances/1812'
INSIDE = ROOT / 'data/humans/inside_1812.json'
HOUSEHOLDS = ROOT / 'data/residents_1812/households'
VARIATION = ROOT / 'data/humans/variation'
OUT = VARIATION / 'dress_1812_town.json'
TICKET = 'T-3522'
LIBERTY = 'L-1812-town-dress-3522'
GEN = 'docs/RESEARCH/town-dress-1812-3522/dress.py'
BODIES = ('settler_1812', 'trader_1812', 'engage_1812', 'woman_working_1812', 'lady_1812')

SOURCES = {
    'settler': ['met_pixler_family_c1815', 'met_krimmel_1811_merrymaking_wayside_inn', 'met_krimmel_1811_black_sawyers_bank_of_pennsylvania', 'quaife_1913'],
    'trader': ['met_ci_1810_1820_coutts_coat_and_breeches', 'met_ci_1815_tailcoat', 'met_peale_1811_anthony_wayne_robinson',
               'met_krimmel_1811_chimney_sweeps_christ_church', 'met_pixler_family_c1815', 'kinzie_waubun_1856'],
    'engage': ['kinzie_waubun_1856', 'lambert_1810_travels_lower_canada_v1', 'heriot_1807_travels_through_the_canadas'],
    'working': ['kinzie_waubun_1856', 'lambert_1810_travels_lower_canada_v1', 'met_krimmel_1811_black_sawyers_bank_of_pennsylvania'],
    'country': ['kinzie_waubun_1856', 'lambert_1810_travels_lower_canada_v1'],
    'lady': ['kinzie_waubun_1856', 'met_krimmel_1811_sunday_morning_arch_street', 'met_ci_1810_1820_american_linen_dress',
             'met_ci_1810_1820_american_cap', 'met_pixler_family_c1815'],
}
READING = {
    'settler': 'docs/RESEARCH/people-1812-3466/day.json dress.settler_1812',
    'servant': 'docs/RESEARCH/people-1812-3466/day.json dress.black_servant_1812',
    'trader': 'docs/RESEARCH/people-1812-3466/day.json dress.trader_1812',
    'engage': 'docs/RESEARCH/people-1812-3466/day.json dress.engage_1812',
    'agent': 'docs/RESEARCH/people-1812-3463/day.json dress.wells_frontier_agent_1812',
    'working': 'docs/RESEARCH/people-1812-3464/day.json dress.soldier_wife_laundress_1812',
    'country': 'docs/RESEARCH/people-1812-3464/day.json dress.woman_of_the_country_1812',
    'headwrap': 'docs/RESEARCH/people-1812-3464/day.json dress.working_woman_enslaved_1812',
    'lady': 'docs/RESEARCH/people-1812-3464/day.json dress.officer_wife_1812',
    'matron': 'docs/RESEARCH/people-1812-3464/day.json dress.trader_wife_matron_1812',
}

# Who is which, where the readings name them (everyone else takes their body's role).
COUNTRY_WOMEN = {'laframboise_josette_1812', 'bisson_mrs', 'mirandeau_madeline_1812', 'ouilmette_archange'}   # woman_of_the_country
HEADWRAP = {'cicely'}                                       # working_woman_enslaved_1812
MATRONS = {'kinzie_eleanor'}                                # trader_wife_matron_1812
SERVANTS = {'black_jim', 'kinzie_servant_second'}           # black_servant_1812
FORGE = {'mirandeau_jean_baptiste'}                         # "Mirandeau at the forge: shirt sleeves"
CLERKS = {'chandonnai_jean_baptiste'}                       # "a man between the trader's and the engagé's dress"
# Wells on the 14th (people-1812-3463 dress.wells_frontier_agent_1812): "a round felt hat, a calico or linen
# shirt, a hunting frock ..." on the engagé's body, so his head is the felt hat and never a tuque.
FRONTIER_AGENT = {'wells_william'}

# ── colours: linear RGB, as the dressed bodies' own materials are written; a check, stripe or
# small print is drawn as its mean at a few metres. (name, rgb, words) ─────────────────────────
SHIRT = {
    'tow': ([0.40, 0.355, 0.27], 'an unbleached tow shirt'),
    'white': ([0.56, 0.53, 0.46], 'a white linen shirt'),
    'blue_check': ([0.27, 0.30, 0.37], 'a blue-and-white check shirt'),
    'red_check': ([0.34, 0.17, 0.145], 'a red-and-white check shirt'),
    'brown_check': ([0.24, 0.17, 0.11], 'a brown check shirt'),
    'blue_stripe': ([0.33, 0.37, 0.46], 'a blue-striped linen shirt'),
    'blue_calico': ([0.075, 0.10, 0.20], 'a blue calico shirt'),
    'pink_calico': ([0.46, 0.22, 0.24], 'a pink calico shirt'),
    'madder_calico': ([0.25, 0.05, 0.035], 'a madder-red calico shirt'),
    'red_calico': ([0.30, 0.06, 0.045], 'a red calico shirt'),
    'deerskin': ([0.29, 0.20, 0.115], 'a smoked deer-skin hunting shirt'),
    'butternut': ([0.26, 0.19, 0.10], 'a butternut-dyed linen hunting shirt'),
}
WAISTCOAT = {
    'brown': ([0.085, 0.052, 0.03], 'a brown waistcoat'), 'red': ([0.20, 0.035, 0.03], 'a red waistcoat'),
    'striped': ([0.21, 0.15, 0.09], 'a striped waistcoat'), 'buff': ([0.42, 0.33, 0.18], 'a buff waistcoat'),
    'black': ([0.02, 0.02, 0.022], 'a black waistcoat'), 'blue': ([0.03, 0.045, 0.10], 'a blue waistcoat'),
    'green': ([0.03, 0.06, 0.035], 'a green waistcoat'), 'yellow': ([0.52, 0.40, 0.14], 'a yellow waistcoat'),
    'white': ([0.55, 0.53, 0.47], 'a white waistcoat'), 'drab': ([0.20, 0.18, 0.13], 'a drab waistcoat'),
}
TROUSERS = {
    'natural': ([0.46, 0.41, 0.31], 'loose natural linen trousers'), 'tow': ([0.37, 0.32, 0.23], 'loose tow trousers'),
    'tan': ([0.33, 0.24, 0.13], 'tan linen trousers'), 'blue': ([0.06, 0.08, 0.15], 'blue cloth trousers'),
    'nankeen': ([0.50, 0.38, 0.18], 'nankeen trousers'), 'brown': ([0.12, 0.08, 0.05], 'brown trousers'),
    'drab': ([0.22, 0.21, 0.18], 'drab trousers'), 'ticking': ([0.33, 0.35, 0.40], 'blue-striped ticking trousers'),
    'deerskin': ([0.25, 0.165, 0.095], 'deer-skin trousers'), 'smoked': ([0.16, 0.10, 0.06], 'dark smoked deer-skin trousers'),
}
NECK = {
    'blue': ([0.04, 0.07, 0.17], 'a blue neckerchief'), 'red': ([0.26, 0.04, 0.035], 'a red neckerchief'),
    'black': ([0.016, 0.016, 0.018], 'a black silk neckerchief'), 'white': ([0.55, 0.53, 0.48], 'a white neckerchief'),
    'check': ([0.28, 0.25, 0.30], 'a check neckerchief'), 'yellow': ([0.40, 0.30, 0.08], 'a yellow print neckerchief'),
}
FELT = {
    'black': ([0.016, 0.015, 0.014], 'black'), 'rusty_black': ([0.04, 0.034, 0.028], 'rusty black'),
    'brown': ([0.075, 0.048, 0.027], 'brown'), 'drab': ([0.19, 0.165, 0.125], 'drab'), 'grey': ([0.12, 0.115, 0.105], 'grey'),
}
STRAW = {'new': ([0.55, 0.45, 0.24], 'natural'), 'old': ([0.40, 0.31, 0.15], 'weathered'), 'pale': ([0.62, 0.55, 0.36], 'pale')}
KNIT = {'red': ([0.33, 0.045, 0.035], 'red'), 'blue': ([0.04, 0.06, 0.16], 'blue'), 'white': ([0.50, 0.47, 0.40], 'undyed'),
        'brown': ([0.12, 0.075, 0.045], 'brown'), 'faded_red': ([0.26, 0.07, 0.055], 'faded red')}
SASH = {'red': ([0.30, 0.045, 0.032], 'a red worsted sash'), 'arrow': ([0.24, 0.085, 0.05], 'a red arrow sash with blue, green and yellow chevrons'),
        'blue': ([0.05, 0.07, 0.15], 'a blue sash'), 'green': ([0.04, 0.09, 0.05], 'a green sash'),
        'yellow': ([0.40, 0.30, 0.06], 'a yellow scarf'), 'belt': ([0.06, 0.035, 0.02], 'a leather belt')}
COAT = {'green': ([0.018, 0.034, 0.022], 'a dark green coat'), 'blue': ([0.02, 0.03, 0.075], 'a dark blue coat'),
        'brown_black': ([0.022, 0.016, 0.012], 'a brown-black coat'), 'brown': ([0.07, 0.045, 0.026], 'an old brown coat'),
        'bottle': ([0.012, 0.045, 0.035], 'a bottle-green coat')}
BREECHES = {'buff': ([0.50, 0.40, 0.25], 'buff breeches'), 'black': ([0.02, 0.02, 0.022], 'black breeches'),
            'nankeen': ([0.50, 0.38, 0.18], 'nankeen breeches'), 'drab': ([0.30, 0.27, 0.20], 'drab breeches'),
            'white': ([0.55, 0.53, 0.47], 'white breeches')}
GOWN_SHORT = {'madder': ([0.15, 0.075, 0.055], 'a madder-print short gown'), 'red': ([0.20, 0.07, 0.055], 'a red calico short gown'),
              'blue_print': ([0.07, 0.09, 0.17], 'a blue-print short gown'), 'brown_print': ([0.15, 0.09, 0.05], 'a brown-print short gown'),
              'stripe': ([0.30, 0.26, 0.28], 'a striped cotton short gown'), 'natural': ([0.40, 0.36, 0.28], 'a natural linen short gown'),
              'blue_linen': ([0.13, 0.17, 0.26], 'a blue linen short gown'), 'white': ([0.52, 0.50, 0.44], 'a white linen short gown')}
PETTICOAT = {'blue': ([0.065, 0.075, 0.095], 'a blue homespun petticoat'), 'brown': ([0.10, 0.065, 0.04], 'a brown homespun petticoat'),
             'madder': ([0.17, 0.05, 0.035], 'a madder homespun petticoat'), 'stripe': ([0.20, 0.17, 0.18], 'a striped homespun petticoat'),
             'stroud': ([0.025, 0.03, 0.055], 'a dark stroud petticoat'), 'black': ([0.018, 0.018, 0.02], 'a black stroud petticoat'),
             'pink_stripe': ([0.32, 0.20, 0.20], 'a pink-striped petticoat'), 'blue_stripe': ([0.22, 0.25, 0.32], 'a blue-striped petticoat')}
APRON = {'natural': ([0.40, 0.36, 0.29], 'a natural linen apron'), 'white': ([0.55, 0.53, 0.48], 'a white apron'),
         'blue_check': ([0.27, 0.30, 0.38], 'a blue-checked apron')}
HEADCLOTH = {'blue': ([0.05, 0.08, 0.16], 'a blue cotton handkerchief'), 'white': ([0.52, 0.50, 0.45], 'a white cotton handkerchief'),
             'red': ([0.26, 0.06, 0.045], 'a red cotton handkerchief'), 'yellow': ([0.40, 0.31, 0.09], 'a yellow print handkerchief'),
             'check': ([0.26, 0.28, 0.34], 'a check handkerchief')}
GOWN = {'white': ([0.58, 0.56, 0.50], 'a white muslin gown'), 'cream': ([0.55, 0.49, 0.36], 'a cream cotton gown'),
        'blue_print': ([0.06, 0.075, 0.115], 'a gown of small blue print'), 'buff_print': ([0.38, 0.29, 0.15], 'a gown of small buff print'),
        'brown': ([0.09, 0.06, 0.04], 'a dark brown stuff gown'), 'dark_blue': ([0.025, 0.03, 0.065], 'a dark blue printed gown'),
        'purple_brown': ([0.09, 0.045, 0.055], 'a purple-brown printed gown')}
SHOES = ([0.028, 0.019, 0.012], 'dark shoes')
MOCCASINS = [([0.17, 0.11, 0.065], 'smoked moccasins'), ([0.12, 0.075, 0.042], 'dark smoked moccasins'), ([0.21, 0.15, 0.09], 'pale moccasins')]
CAP_WHITE = [([0.58, 0.56, 0.51], 'a white linen cap'), ([0.50, 0.47, 0.40], 'an unbleached linen cap'), ([0.62, 0.61, 0.57], 'a white cotton cap')]
NECK_KERCHIEF = [([0.55, 0.53, 0.48], 'a white neck kerchief'), ([0.27, 0.30, 0.38], 'a blue-checked neck kerchief'),
                 ([0.40, 0.30, 0.10], 'a yellow print neck kerchief'), ([0.24, 0.06, 0.045], 'a red neck kerchief'),
                 ([0.47, 0.43, 0.35], 'an unbleached neck kerchief')]


def rng(pid, what, salt=0):
    h = hashlib.sha256(f'{TICKET}|{pid}|{what}|{salt}'.encode()).digest()
    return int.from_bytes(h[:8], 'big') / 2 ** 64


class Draw:
    """One person's seeded choices, rerolled by `salt` until they match nobody else's."""

    def __init__(self, pid, salt):
        self.pid, self.salt = pid, salt

    def r(self, what):
        return rng(self.pid, what, self.salt)

    def pick(self, what, weighted):
        total = sum(w for _, w in weighted)
        x = self.r(what) * total
        for k, w in weighted:
            x -= w
            if x < 0:
                return k
        return weighted[-1][0]

    def one(self, what, seq):
        return seq[int(self.r(what) * len(seq)) % len(seq)]

    def span(self, what, lo, hi):
        return round(lo + (hi - lo) * self.r(what), 3)

    def shade(self, what, rgb, faded=0.0):
        """A cloth's own dye lot and wear: a little lighter or darker, older cloth duller."""
        k = 0.86 + 0.28 * self.r(what + ':lot')
        out = [c * k for c in rgb]
        if faded:
            mean = sum(out) / 3
            out = [c + (mean * 1.15 - c) * faded for c in out]
        return [round(min(0.9, c), 4) for c in out]


def felt_hat(d, colour, crown, brim, taper, roll, droop, words):
    return {'kind': 'round', 'rgb': d.shade('hat', FELT[colour][0], 0.1 * d.r('hat_wear')),
            'band': d.shade('band', [0.012, 0.011, 0.01]) if d.r('band') < 0.7 else None,
            'crown_m': crown, 'brim_m': brim, 'taper': taper, 'roll': roll, 'droop': droop,
            '_words': f'a {FELT[colour][1]} felt round hat, {words}'}


def round_hat(d, town=False, frontier=False):
    """A felt round hat of 1810: the crown, taper and brim are the wearer's."""
    colour = d.pick('felt', [('black', 5), ('rusty_black', 3), ('brown', 3), ('drab', 2), ('grey', 1)] if not town
                    else [('black', 6), ('brown', 2), ('drab', 1)])
    style = d.pick('felt_style', [('tall', 5), ('tapered', 3)] if town else [('low_wide', 1), ('soft', 1)] if frontier else
                   [('tall', 4), ('low_wide', 4), ('soft', 3), ('tapered', 2)])
    if style == 'tall':
        h = felt_hat(d, colour, d.span('crown', .135, .16) if town else d.span('crown', .118, .14), d.span('brim', .045, .06),
                     d.span('taper', .92, 1.04) if town else d.span('taper', .88, .98), d.span('roll', .25, .7),
                     d.span('droop', -.05, .1), 'tall in the crown')
    elif style == 'low_wide':
        h = felt_hat(d, colour, d.span('crown', .085, .11), d.span('brim', .075, .1), d.span('taper', .9, 1.0), d.span('roll', 0, .25),
                     d.span('droop', .1, .35), 'low in the crown and wide in the brim')
    elif style == 'soft':
        h = felt_hat(d, colour, d.span('crown', .1, .125), d.span('brim', .06, .085), d.span('taper', .86, .95), d.span('roll', 0, .15),
                     d.span('droop', .3, .55), 'worn soft, its brim gone down before and behind')
    else:
        h = felt_hat(d, colour, d.span('crown', .12, .145), d.span('brim', .05, .07), d.span('taper', .8, .88), d.span('roll', .35, .8),
                     d.span('droop', -.15, .05), 'its crown tapering, the brim rolled at the sides')
    h['tilt'] = d.span('tilt', -.006, .008)
    return h, f'{style}:{colour}'


def straw_hat(d):
    c = d.pick('straw', [('new', 3), ('old', 3), ('pale', 1)])
    band = d.one('straw_band', [([0.015, 0.014, 0.013], 'a black band'), ([0.06, 0.035, 0.02], 'a brown band'), None])
    h = {'kind': 'straw', 'rgb': d.shade('hat', STRAW[c][0]), 'band': d.shade('band', band[0]) if band else None,
         'crown_m': d.span('crown', .07, .1), 'brim_m': d.span('brim', .07, .115), 'taper': d.span('taper', .9, 1.02),
         'roll': d.span('roll', 0, .2), 'droop': d.span('droop', -.05, .35), 'tilt': d.span('tilt', -.004, .008),
         '_words': f"a {STRAW[c][1]} straw hat{' with ' + band[1] if band else ''}"}
    return h, f'straw:{c}'


def knit_cap(d, colour):
    h = {'kind': 'knit', 'rgb': d.shade('hat', KNIT[colour][0], 0.1 * d.r('hat_wear')), 'tail_m': d.span('tail', .05, .13),
         '_words': f"{'an' if KNIT[colour][1][0] in 'aeiou' else 'a'} {KNIT[colour][1]} knitted cap, its top falling back"}
    return h, f'knit:{colour}'


def finish(person, d, colours, hide, worn, hat=None, headcloth=None, role=None):
    out = {'asset': person['asset'], 'role': role, 'reading': READING[role], 'colours': colours, 'hide': sorted(set(hide)), 'worn': '; '.join(worn)}
    if hat:
        out['hat'] = {k: v for k, v in hat.items() if not k.startswith('_') and v is not None}
    if headcloth:
        out['headcloth'] = headcloth
    return out


def man_settler(person, d, servant=False):
    a, old = person['asset'], person['old']
    faded = 0.3 if old else 0.15 * d.r('wear')
    colours, hide, worn = {}, [], []

    def put(mat, rgb, what, fade=faded):
        colours[mat] = d.shade(what, rgb, fade)
    # The settler reading: a tow or linen shirt (or checked); a hunting shirt for some Americans.
    s = d.pick('shirt', [('white', 3), ('red_check', 2), ('blue_check', 2), ('tow', 1)] if servant else
               [('tow', 4), ('white', 3), ('blue_check', 3), ('brown_check', 2), ('blue_stripe', 1), ('red_check', 1), ('butternut', 2)])
    put('garment_upper__shirt_tow_linen_1810', SHIRT[s][0], 'shirt')
    hunting = s == 'butternut'
    worn.append(SHIRT[s][1])
    if hunting or d.r('waistcoat') < (0.25 if servant else 0.4):
        # In shirt sleeves: the body's waistcoat stays on but in the shirt's own cloth, because the
        # trousers' top edge under it is cut for a waistcoat over it and shows ragged without one.
        colours['garment_outer__waistcoat_brown_1810'] = colours['garment_upper__shirt_tow_linen_1810']
        w = 'none'
        if not hunting:
            worn.append('in his shirt sleeves')
    else:
        w = d.pick('waistcoat', [('brown', 3), ('red', 2), ('striped', 3), ('drab', 2), ('black', 1), ('buff', 1), ('blue', 1)])
        put('garment_outer__waistcoat_brown_1810', WAISTCOAT[w][0], 'waistcoat')
        worn.append(WAISTCOAT[w][1])
    if d.r('neck') < 0.35:
        hide.append('neckerchief_blue')
        worn.append('open at the neck')
    else:
        n = d.pick('neck_colour', [('blue', 3), ('red', 2), ('black', 2), ('white', 1), ('check', 1), ('yellow', 1)])
        put('accessory__neckerchief_blue_1810', NECK[n][0], 'neck', 0)
        worn.append(NECK[n][1])
    t = d.pick('trousers', [('natural', 4), ('tow', 3), ('tan', 2), ('blue', 2), ('drab', 1), ('ticking', 1), ('brown', 1)])
    put('garment_lower__trousers_linen_1810', TROUSERS[t][0], 'trousers')
    worn.append(TROUSERS[t][1])
    if not servant and d.r('feet') < 0.3:
        m = d.one('moc', MOCCASINS)
        put('footwear__shoes_dark_1810', m[0], 'moc', 0)
        worn.append(m[1])
    else:
        put('footwear__shoes_dark_1810', SHOES[0], 'shoes', 0)
    # The head: a round black hat for the servant reading; felt or straw for the settler's.
    hide.append('headwear_round_hat')
    hk = d.pick('head', [('felt', 7), ('bare', 1)] if servant else [('felt', 6), ('straw', 4), ('bare', 1)])
    if hk == 'felt':
        hat, sig = round_hat(d)
        if servant:
            hat['rgb'] = d.shade('hat', FELT['black'][0], 0.1)
            hat['_words'] = 'a black' + hat['_words'][hat['_words'].index(' felt'):]
    elif hk == 'straw':
        hat, sig = straw_hat(d)
    else:
        hat, sig = None, 'bare'
        worn.append('bareheaded')
    if hat:
        worn.insert(0, hat['_words'])
    out = finish(person, d, colours, hide, worn, hat=hat, role='servant' if servant else 'settler')
    return out, (sig, s, w, t)


def man_engage(person, d):
    pid, old = person['pid'], person['old']
    faded = 0.3 if old else 0.15 * d.r('wear')
    colours, hide, worn = {}, [], []

    def put(mat, rgb, what, fade=faded):
        colours[mat] = d.shade(what, rgb, fade)
    # Wau-Bun's engagé of August 1812: "a suit of deer-skin, with belt, moccasins"; or the other
    # summer dress, a calico shirt, a bright sash, linen trousers, moccasins.
    suit = pid not in FORGE and (pid in FRONTIER_AGENT or d.r('suit') < 0.35)
    if suit:
        put('garment_upper__shirt_calico_blue_1812', SHIRT['deerskin'][0], 'shirt')
        tr = 'smoked'   # the trousers darker with wear and smoke than the shirt, as a worn suit is
        put('garment_lower__trousers_deerskin_1812', TROUSERS[tr][0], 'trousers')
        worn += ['a suit of smoked deer-skin, hunting shirt and trousers']
        s = 'deerskin'
    else:
        s = d.pick('shirt', [('blue_calico', 3), ('red_calico', 2), ('madder_calico', 1), ('blue_stripe', 2), ('white', 2), ('red_check', 1),
                             ('pink_calico', 1), ('blue_check', 1)])
        put('garment_upper__shirt_calico_blue_1812', SHIRT[s][0], 'shirt')
        tr = d.pick('trousers', [('natural', 3), ('blue', 2), ('deerskin', 2), ('tow', 1)])
        put('garment_lower__trousers_deerskin_1812', TROUSERS[tr][0], 'trousers')
        worn += [SHIRT[s][1], TROUSERS[tr][1]]
    sk = d.pick('sash', [('belt', 4), ('red', 1)] if suit else [('red', 4), ('arrow', 2), ('blue', 1), ('green', 1), ('yellow', 1)])
    if pid in FORGE:
        sk = 'belt'
    put('accessory__sash_worsted_red_1812', SASH[sk][0], 'sash', 0)
    if sk == 'belt':
        hide.append('sash_ends')
    worn.append(SASH[sk][1])
    m = d.one('moc', MOCCASINS)
    put('footwear__moccasins_smoked_1812', m[0], 'moc', 0)
    worn.append(m[1])
    # The head: the red tuque year round, a straw hat in summer, or bareheaded (Hubbard).
    hk = d.pick('head', [('tuque', 4), ('knit', 2), ('straw', 3), ('bare', 2)]) if pid not in FRONTIER_AGENT else 'felt'
    hat = None
    if hk == 'tuque':
        c = d.pick('tuque', [('red', 5), ('faded_red', 2), ('blue', 2), ('white', 1)])
        put('headwear__tuque_red_1812', KNIT[c][0], 'tuque', 0.1 * d.r('hat_wear'))
        worn.insert(0, f'a {KNIT[c][1]} tuque')
        sig = f'tuque:{c}'
    else:
        hide.append('headwear_tuque')
        if hk == 'knit':
            hat, sig = knit_cap(d, d.pick('knit', [('red', 4), ('blue', 2), ('brown', 1), ('white', 1)]))
        elif hk == 'straw':
            hat, sig = straw_hat(d)
        elif hk == 'felt':
            hat, sig = round_hat(d, frontier=True)
        else:
            sig = 'bare'
            worn.append('bareheaded, his hair long')
        if hat:
            worn.insert(0, hat['_words'])
    return finish(person, d, colours, hide, worn, hat=hat, role='agent' if pid in FRONTIER_AGENT else 'engage'), (sig, s, sk, tr)


def man_trader(person, d):
    pid, old = person['pid'], person['old']
    faded = 0.2 if old else 0.08 * d.r('wear')
    colours, hide, worn = {}, [], []

    def put(mat, rgb, what, fade=faded):
        colours[mat] = d.shade(what, rgb, fade)
    c = d.pick('coat', [('green', 3), ('blue', 3), ('brown_black', 2), ('brown', 2), ('bottle', 1)] if pid not in CLERKS else [('brown', 1)])
    put('garment_outer__tailcoat_green_1810', COAT[c][0], 'coat')
    w = d.pick('waistcoat', [('yellow', 2), ('buff', 3), ('white', 3), ('striped', 2), ('red', 1)] if pid not in CLERKS else [('striped', 1), ('red', 1)])
    put('garment_outer__waistcoat_yellow_1810', WAISTCOAT[w][0], 'waistcoat')
    if d.r('buttons') < 0.4:
        put('accessory__gilt_buttons_1810', COAT[c][0], 'buttons', 0)   # cloth-covered, the coat's colour
        btn = 'covered buttons'
    else:
        btn = 'gilt buttons'
    b = d.pick('breeches', [('buff', 3), ('black', 2), ('nankeen', 2), ('drab', 1), ('white', 1)])
    put('garment_lower__breeches_buff_1810', BREECHES[b][0], 'breeches')
    if d.r('tops') < 0.4:
        # The tops blacked like the shafts (left off, they would bare the knee under the breeches).
        put('footwear__boot_tops_tan_1810', [0.011, 0.01, 0.01], 'tops', 0)
        boots = 'plain black boots'
    else:
        boots = 'top boots with tan tops'
    hide.append('headwear_round_hat')
    hat, sig = round_hat(d, town=True)
    worn += [hat['_words'], f'{COAT[c][1]} with {btn}', WAISTCOAT[w][1], 'a white shirt and neckcloth', BREECHES[b][1], boots]
    return finish(person, d, colours, hide, worn, hat=hat, role='trader'), (sig, c, w, b)


def woman_working(person, d):
    pid, old = person['pid'], person['old']
    country, wrap = pid in COUNTRY_WOMEN, pid in HEADWRAP
    faded = 0.3 if old else 0.15 * d.r('wear')
    colours, hide, worn = {}, [], []

    def put(mat, rgb, what, fade=faded):
        colours[mat] = d.shade(what, rgb, fade)
    if country:
        g = d.pick('gown', [('red', 4), ('blue_print', 3), ('brown_print', 2), ('madder', 1)])
        p = d.pick('petticoat', [('stroud', 4), ('black', 3), ('blue', 1)])
    elif wrap:
        g = d.pick('gown', [('white', 1), ('natural', 1)])
        p = d.pick('petticoat', [('pink_stripe', 1), ('blue_stripe', 1), ('brown', 1)])
    else:
        g = d.pick('gown', [('madder', 3), ('blue_print', 2), ('brown_print', 2), ('stripe', 2), ('natural', 2), ('blue_linen', 1), ('red', 2)])
        p = d.pick('petticoat', [('blue', 3), ('brown', 3), ('madder', 2), ('stripe', 2), ('blue_stripe', 1)])
    put('garment_upper__short_gown_madder_print_1812', GOWN_SHORT[g][0], 'gown')
    put('garment_lower__petticoat_blue_homespun_1812', PETTICOAT[p][0], 'petticoat')
    worn += [GOWN_SHORT[g][1], PETTICOAT[p][1]]
    if not country and d.r('apron') < 0.45:   # out of the washhouse and kitchen, the apron is off
        hide += ['apron', 'apron_band']
        ap = 'none'
    else:
        ap = d.pick('apron', [('natural', 3), ('white', 2), ('blue_check', 3)])
        put('garment_outer__apron_natural_linen_1812', APRON[ap][0], 'apron')
        worn.append(APRON[ap][1])
    if d.r('kerchief') < 0.15:
        hide.append('neck_kerchief')
    else:
        k = d.one('kerchief', NECK_KERCHIEF if not wrap else NECK_KERCHIEF[:1] + NECK_KERCHIEF[4:])
        put('accessory__neck_kerchief_white_1812', k[0], 'kerchief', 0)
        worn.append(k[1])
    headcloth = None
    if country:
        hk = 'blue'   # Wau-Bun: "with a blue cotton handkerchief wrapped around her head" (direct)
    elif wrap:
        hk = d.pick('wrap', [('white', 2), ('red', 1), ('yellow', 1), ('check', 1)])
    else:
        hk = d.pick('head', [('cap', 3), ('blue', 1), ('white', 1)])   # "a cap or a cotton handkerchief tied round the head"
    if hk == 'cap':
        cp = d.one('cap', CAP_WHITE)
        put('headwear__linen_cap_white_1812', cp[0], 'cap', 0)
        worn.insert(0, cp[1])
    else:
        hide.append('headwear_linen_cap')
        headcloth = d.shade('headcloth', HEADCLOTH[hk][0], 0.1)
        worn.insert(0, f'{HEADCLOTH[hk][1]} wrapped round the head')
    if country or (not wrap and d.r('feet') < 0.15):
        m = d.one('moc', MOCCASINS)
        put('footwear__shoes_black_1812', m[0], 'moc', 0)
        worn.append(m[1])
    else:
        put('footwear__shoes_black_1812', [0.02, 0.016, 0.013], 'shoes', 0)
        worn.append('heavy shoes')
    role = 'country' if country else 'headwrap' if wrap else 'working'
    return finish(person, d, colours, hide, worn, headcloth=headcloth, role=role), (hk, g, p, ap)


def woman_lady(person, d):
    pid = person['pid']
    matron = pid in MATRONS
    colours, hide, worn = {}, [], []

    def put(mat, rgb, what, fade=0.05):
        colours[mat] = d.shade(what, rgb, fade)
    g = d.pick('gown', [('brown', 2), ('dark_blue', 2), ('purple_brown', 2)] if matron else
               [('white', 3), ('cream', 2), ('blue_print', 2), ('buff_print', 2)])
    put('garment_upper__gown_blue_print_1812', GOWN[g][0], 'gown')
    put('garment_lower__gown_blue_print_1812', GOWN[g][0], 'gown')
    worn.append(GOWN[g][1])
    cp = d.one('cap', CAP_WHITE)
    put('headwear__cotton_cap_white_1812', cp[0], 'cap', 0)
    worn.insert(0, cp[1] if not matron else 'a full white cap')
    if not matron and d.r('kerchief') < 0.25:
        hide.append('neck_kerchief')
        worn.append('a chemisette filling the neckline')
    else:
        put('accessory__muslin_kerchief_white_1812', [0.6, 0.59, 0.55], 'kerchief', 0)
        worn.append('a white muslin kerchief crossed in front')
    sh = d.one('shoes', [([0.02, 0.016, 0.013], 'flat black shoes'), ([0.09, 0.055, 0.03], 'flat brown shoes')])
    put('footwear__flat_shoes_black_1812', sh[0], 'shoes', 0)
    worn.append(sh[1])
    return finish(person, d, colours, hide, worn, role='matron' if matron else 'lady'), (g, sh[1], cp[1])


DRESSERS = {'settler_1812': lambda person, d: man_settler(person, d, servant=person['pid'] in SERVANTS), 'engage_1812': man_engage, 'trader_1812': man_trader,
            'woman_working_1812': woman_working, 'lady_1812': woman_lady}


def households():
    out = {}
    for f in sorted(HOUSEHOLDS.glob('*.json')):
        for p in json.loads(f.read_text()).get('persons', []):
            out[p['id']] = p
    return out


def others():
    """People another dress file already dresses (the camps, the children, the garrison)."""
    taken = set()
    for f in sorted(VARIATION.glob('dress_1812_*.json')):
        if f.name == OUT.name:
            continue
        taken |= set(json.loads(f.read_text()).get('persons', {}))
    return taken


def people():
    """Each townsperson's body, from the drawn instances and the people at doors."""
    found = {}
    for f in sorted(INSTANCES.glob('*.json')):
        if f.name == 'index.json':
            continue
        d = json.loads(f.read_text())
        a = d.get('appearance', {}).get('asset_id', '')
        if a in BODIES and d.get('person_id'):
            found.setdefault(d['person_id'], a)
    if INSIDE.exists():
        for row in json.loads(INSIDE.read_text()).get('people', []):
            if row.get('asset_id') in BODIES:
                found.setdefault(row['person'], row['asset_id'])
    hh, taken = households(), others()
    out = []
    for pid, asset in sorted(found.items()):
        p = hh.get(pid, {})
        occ = p.get('occupation')
        occ = occ.get('value') if isinstance(occ, dict) else occ
        if pid in taken or "Heald's company" in str(occ or ''):
            continue
        band = p.get('age_band') or {}
        born = str((p.get('born') or {}).get('value', ''))[:4]
        age = 1812 - int(born) if born.isdigit() else (band['low'] + band.get('high', band['low'])) / 2 if isinstance(band.get('low'), int) else None
        out.append({'pid': pid, 'asset': asset, 'old': age is not None and age >= 50})
    return out


def build():
    """Each person's dress, rerolled until it differs from everyone of the same body in at least
    two of its main choices (headwear, upper, middle, lower), or, failing that in 60 tries, the
    draw nearest to it; a person dressed exactly as another is never kept."""
    persons, seen = {}, {}
    for person in people():
        dresser = DRESSERS[person['asset']]
        others = seen.setdefault(person['asset'], [])
        best = None
        for salt in range(60):
            rec, sig = dresser(person, Draw(person['pid'], salt))
            near = max((sum(a == b for a, b in zip(sig, o)) for o in others), default=0)
            if best is None or near < best[0]:
                best = (near, rec, sig)
            if near <= len(sig) - 2:
                break
        near, rec, sig = best
        assert near < len(sig), f"{person['pid']} could not be dressed apart from the others"
        others.append(sig)
        rec['grade'] = 'reconstructed'
        rec['sources'] = SOURCES[{'servant': 'settler', 'headwrap': 'working', 'matron': 'lady', 'agent': 'engage'}.get(rec['role'], rec['role'])]
        persons[person['pid']] = rec
    return {
        'format': 'chicago4d_human_dress_v1', 'ticket': TICKET, 'scene': '1812', 'generated_by': GEN, 'liberty': LIBERTY,
        '_doc': ("Each 1812 townsperson's own dress of 14 August 1812: `colours` (linear RGB) replace the named material's "
                 'colour on clones (human-looks.js dressCloth), `hide` names pieces of the dressed body not worn today, '
                 '`hat` is a hat made for their head (human-hats.js), `headcloth` a handkerchief round the head (human-hair.js). '
                 'Pieces and colour ranges from the readings named in `reading`; who wears what is reconstructed, and no two '
                 'people of one body share a hat, upper and lower garment. Regenerate with the generator; never edit by hand.'),
        'persons': persons,
    }


def main():
    text = json.dumps(build(), indent=1, ensure_ascii=False) + '\n'
    if '--check' in sys.argv:
        if not OUT.exists() or OUT.read_text() != text:
            raise SystemExit(f'{OUT.relative_to(ROOT)} is stale: run {GEN}')
        print('town dress file current')
        return
    OUT.write_text(text)
    d = json.loads(text)
    print(f"wrote {OUT.relative_to(ROOT)}: {len(d['persons'])} people")


if __name__ == '__main__':
    main()
