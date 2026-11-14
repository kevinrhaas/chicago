#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""T-3553: a dress record's own words, drawn as its cloth.

The 1812 dress files (the camps T-3506, the town T-3522, the children T-3520, the garrison T-3523)
already name each person's cloth from the period readings: "a red calico short gown", "a blouse of
blue-and-white check", "a blue-striped petticoat", "blue-striped ticking trousers", "a frock of pink
sprigged cotton". Until now each was drawn as one flat colour, the mean of its figure, so a
calico or a check read as plain cloth and the women of the camps and the town looked more alike
than their records say they were. The owner, 2026-11-14: "Give the women some variation in their
clothing appearance".

This reads those words and nothing else: a garment whose words name a check, a stripe, ticking, a
calico, a print or a sprig gets that figure (human-finery.js, fabric.js), in the colours the words
give, laid over a ground chosen so the cloth's mean colour stays the record's own colour (so at a
distance, where the shader fades a figure to its mean, nobody changes). Where the words give one
colour ("a red calico"), the figure's colour is a seeded choice among the small figures of the
period's printed cottons (a dark figure on a light ground, a light one on a dark ground), and its
scale a seeded few centimetres: reconstructed renderings (liberty L-finery-3553), not a reading.
A garment the words do not name, or one the body does not wear, is left as it was.
"""
import hashlib
import re

TICKET = 'T-3553'
# The words for a garment, and the token its material's name carries on the 1812 and 1835 bodies.
NOUNS = [('short gown', ('short_gown',)), ('petticoat', ('petticoat',)), ('apron', ('apron',)), ('pinafore', ('pinafore',)),
         ('neck kerchief', ('kerchief',)), ('neckerchief', ('neckerchief', 'kerchief')), ('blouse', ('calico_shirt', 'calico_blouse', 'shirt', 'blouse')),
         ('shirt', ('shirt',)), ('frock', ('frock',)), ('gown', ('gown',)), ('trousers', ('trousers',))]
WHITE = [.56, .54, .48]
COLOURS = {'blue': [.05, .09, .26], 'red': [.32, .05, .04], 'brown': [.12, .07, .04], 'green': [.06, .14, .06], 'yellow': [.50, .38, .08],
           'pink': [.6, .3, .32], 'lilac': [.35, .22, .45], 'indigo': [.03, .05, .15], 'madder': [.3, .06, .04], 'buff': [.5, .4, .24]}
DARK_FIGURES = [[.2, .04, .03], [.03, .05, .14], [.04, .03, .02], [.05, .1, .04]]
LIGHT_FIGURES = [[.55, .5, .38], [.5, .38, .08], [.6, .58, .52], [.35, .06, .04]]


def draw(pid, key):
    return int(hashlib.sha256(f'{TICKET}:{pid}:{key}'.encode()).hexdigest()[:8], 16) / 2**32


def r3(rgb):
    return [round(min(1.0, max(0.0, c)), 4) for c in rgb]


def figure(words):
    """The figure the words name: check, stripe, pinstripe (ticking) or sprig (calico, print)."""
    if re.search(r'\bcheck(ed)?\b', words):
        return 'check'
    if 'ticking' in words:
        return 'pinstripe'
    if re.search(r'strip(ed|e)\b', words):
        return 'stripe'
    if re.search(r'\b(calico|print|sprigged)\b', words):
        return 'sprig'
    return None


def toward(c, x, limit):
    """x moved toward c just far enough that every channel of limit(k) stays within 0..1."""
    for k in (1, .9, .8, .7, .6, .5, .4, .3, .2, .1, 0):
        y = [ci + k * (xi - ci) for ci, xi in zip(c, x)]
        if all(0 <= v <= 1 for v in limit(y)):
            return y
    return list(c)


def named_colour(words):
    """The colour of the figure the words give ("blue-and-white check", "blue-striped")."""
    m = re.search(r'\b(blue|red|brown|green|yellow|pink|lilac)(-and-white|-striped|-checked)', words)
    return COLOURS.get(m.group(1)) if m else None


def finery_from_worn(pid, dress):
    worn = dress.get('worn') or ''
    colours = dress.get('colours') or {}
    hidden = set(dress.get('hide') or [])
    out = {}
    for item in worn.split('; '):
        kind = figure(item)
        if not kind or 'handkerchief' in item:
            continue
        noun = next((n for n in NOUNS if n[0] in item), None)
        if not noun:
            continue
        mats = [m for m in colours if any(t in m for t in noun[1]) and m.startswith(('garment_', 'accessory_'))]
        # A short gown is not a gown; a neck kerchief is not a neckerchief's own word.
        if noun[0] == 'gown':
            mats = [m for m in mats if 'short_gown' not in m]
        if noun[0] == 'shirt':
            mats = [m for m in mats if 'calico_blouse' not in m] or mats
        mats = [m for m in mats if not any(h in m for h in hidden)] or mats
        for m in mats:
            if m in out:
                continue
            c = colours[m]
            key = f'{m}|{kind}'
            if kind in ('check', 'stripe'):
                # A two-colour cloth whose mean is the record's colour: a ground and the figure.
                named = named_colour(item)
                light = WHITE if ('white' in item or 'linen' in item or named) else [min(1.0, x * 1.6 + .02) for x in c]
                # The light ground no further from the colour than its dark figure can balance.
                ground = toward(c, light, lambda g: [2 * x - y for x, y in zip(c, g)])
                fig = [2 * x - y for x, y in zip(c, ground)]
                rep = round(.01 + draw(pid, key + 'rep') * .01, 4) if kind == 'check' else round(.009 + draw(pid, key + 'rep') * .007, 4)
                out[m] = {'ground': r3(ground), 'pattern': {'kind': kind, 'rgb': r3(fig), 'repeat_m': rep, 'contrast': 1}}
            elif kind == 'pinstripe':
                fig = toward(c, COLOURS['blue'], lambda f: [(x - .12 * y) / .88 for x, y in zip(c, f)])
                ground = [(x - .12 * y) / .88 for x, y in zip(c, fig)]
                out[m] = {'ground': r3(ground), 'pattern': {'kind': 'pinstripe', 'rgb': r3(fig), 'repeat_m': .008, 'contrast': 1}}
            else:
                pool = DARK_FIGURES if sum(c) > .9 else LIGHT_FIGURES
                fig = toward(c, pool[int(draw(pid, key + 'fig') * len(pool))], lambda f: [(x - .16 * y) / .84 for x, y in zip(c, f)])
                ground = [(x - .16 * y) / .84 for x, y in zip(c, fig)]
                rep = round(.018 + draw(pid, key + 'rep') * .014, 4)
                out[m] = {'ground': r3(ground), 'pattern': {'kind': 'sprig', 'rgb': r3(fig), 'repeat_m': rep, 'contrast': 1}}
    return out or None
