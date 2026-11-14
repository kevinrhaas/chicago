#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""T-3553: the women of Prairie Avenue in 1904, each dressed as her own, by season.

The owner, 2026-11-14: "when i see shows like gilded age they are very fancy and lots of details
and you don't have that ... I would think maybe some of these women would have nicer clothing
... Give the women some variation in their clothing appearance". Until this every lady of the
avenue wore the one dark day suit of the reference body (lady_1904.json) in one of six colours.

What the women of these houses wore in 1904 is read from dated garments and hats in the Met's
Costume Institute (docs/RESEARCH/finery-3553/README.md, each a data/sources record): a lady's
tailored walking suit with soutache braid; an afternoon dress of coloured silk with a lace yoke,
lace at the wrist and a flounced, banded hem; the white summer "lingerie" dress of sheer cotton,
lace insertion and a satin sash; a shirtwaist and skirt; a velvet afternoon dress banded with
ribbon; black silk and jet for an older woman; striped and foulard-spotted silks; the wide picture
hat with plumes or flowers, the straw sailor, the brimless ruched toque. Each woman is dealt one of
those, seeded by her id, for summer (the record's own dress, the season the town opens in), for
spring and fall, and for winter (`seasons`, human-looks.js dressInSeason). Her colours, trims and
hat are reconstructed choices within the kinds the references show (liberty L-finery-3553); no
garment of any named woman is claimed. Servants stay plainer and varied: a maid's morning print
or her black afternoon dress, a cook's print and checked apron, a companion's shirtwaist.

Every colour is linear RGB, as the dressed bodies' materials are.
"""
import hashlib

TICKET = 'T-3553'
LIBERTY = 'L-finery-3553'
SOURCES = ['met_ci_1902_black_wool_suit', 'met_ci_1902_1905_blue_silk_dress', 'met_ci_1903_1905_linen_afternoon_dress',
           'met_ci_1903_white_lingerie_dress', 'met_ci_1903_white_cotton_dress', 'met_ci_1903_hallee_velvet_afternoon_dress',
           'met_ci_1900_1903_rouff_jet_dinner_dress', 'met_ci_1900_striped_summer_dress', 'met_ci_1900_1905_gluck_braided_ensemble',
           'met_ci_1901_1902_straw_tricorne', 'met_ci_1900_flower_wreath_hat', 'met_ci_1903_crocker_mourning_toque',
           'loc_detroit_1904_easter_crowds_fifth_avenue', 'loc_johnston_1905_fairbanks_cornerstone_address']

J = 'garment_outer__lady_jacket_black'
S = 'garment_lower__lady_skirt_black'
LADY_HAT_HIDE = ['headwear_lady_hat', 'lady_hat_plumes']


def draw(pid, key):
    return int(hashlib.sha256(f'{TICKET}:{pid}:{key}'.encode()).hexdigest()[:8], 16) / 2**32


def choose(pid, key, values):
    return values[int(draw(pid, key) * len(values))]


def pick(pid, key, weighted):
    total = sum(w for _, w in weighted)
    x = draw(pid, key) * total
    for v, w in weighted:
        x -= w
        if x < 0:
            return v
    return weighted[-1][0]


def r3(rgb):
    return [round(min(1.0, max(0.0, c)), 3) for c in rgb]


def scale(rgb, k):
    return r3([c * k for c in rgb])


# Cloth colours, linear. Rich dyes for silk, wool and velvet; light ones for summer lawn and silk.
RICH = [('navy', [.02, .03, .075]), ('black', [.012, .012, .014]), ('plum', [.09, .03, .06]), ('claret', [.13, .02, .03]),
        ('bottle green', [.02, .06, .035]), ('brown', [.08, .045, .025]), ('grey', [.16, .16, .15]), ('violet', [.07, .045, .1]),
        ('sapphire', [.025, .04, .11]), ('fawn', [.32, .24, .15])]
LIGHT = [('white', [.74, .73, .69]), ('ivory', [.66, .62, .52]), ('pale blue', [.36, .47, .60]), ('shell pink', [.62, .42, .42]),
         ('lavender', [.40, .33, .52]), ('eau-de-nil', [.42, .52, .40]), ('primrose', [.62, .56, .32]), ('dove grey', [.30, .29, .27]),
         ('biscuit', [.42, .34, .22])]
HALF_MOURNING = [('black', [.012, .012, .014]), ('grey', [.16, .16, .15]), ('mauve', [.22, .14, .25]), ('violet', [.07, .045, .1])]
LACE = [('cream', [.62, .58, .48]), ('white', [.72, .71, .67]), ('ecru', [.50, .43, .30])]
STRAW = [('natural straw', [.50, .42, .25]), ('white straw', [.62, .58, .48]), ('black straw', [.02, .02, .022])]
FLOWERS = [('pink roses', [.60, .30, .36], [.70, .62, .60]), ('white roses', [.70, .68, .64], [.60, .55, .40]),
           ('violets', [.20, .10, .40], [.30, .20, .50]), ('poppies', [.55, .08, .06], [.10, .08, .06]),
           ('cornflowers', [.15, .25, .62], [.70, .68, .64]), ('yellow roses', [.66, .52, .16], [.70, .66, .55])]
PLUMES = [('white', [.66, .64, .60]), ('black', [.02, .02, .022]), ('grey', [.30, .30, .30])]


def lace(pid, key):
    return choose(pid, key, LACE)


def tonal(rgb, k=1.6):
    """A damask's figure: the ground's own colour, lighter."""
    return r3([min(1.0, c * k + .01) for c in rgb])


def dark(rgb):
    return scale(rgb, .45)


def hat(pid, season, kind, base_rgb, matron=False):
    """A hat for the season and the dress: a straw in summer, felt or silk in spring and fall, a
    velvet toque or a plumed felt in winter."""
    if kind == 'sailor':
        name, rgb = choose(pid, 'sailor', STRAW[:2])
        return {'kind': 'sailor', 'rgb': rgb, 'band': dark(base_rgb) if sum(base_rgb) < .6 else [.015, .015, .02],
                'brim_m': round(.055 + draw(pid, 'sbrim') * .02, 3), 'crown_m': .065}, f'a {name} sailor'
    if matron or kind == 'toque':
        rgb = scale(base_rgb, .8) if not matron else [.012, .012, .014]
        trim = {'bow': {'rgb': rgb, 'side': 1}} if draw(pid, 'qtrim' + season) < .5 else {'plumes': {'n': 1, 'rgb': choose(pid, 'qplume', PLUMES[1:])[1], 'side': -1, 'length_m': .2}}
        return {'kind': 'toque', 'rgb': rgb, 'crown_m': round(.07 + draw(pid, 'qcrown') * .02, 3), 'puff': round(.15 + draw(pid, 'qpuff') * .15, 2),
                'trim': trim}, f'a ruched {"black silk" if matron else "velvet"} toque' + (' with a bow' if 'bow' in trim else ' and a plume')
    # A picture hat: straw in summer, felt or silk the rest of the year.
    if season == 'summer':
        sname, rgb = choose(pid, 'straw' + season, STRAW)
    else:
        sname, rgb = 'felt', scale(base_rgb, .9) if sum(base_rgb) < 1.2 else [.02, .02, .022]
    side = 1 if draw(pid, 'cockside') < .5 else -1
    spec = {'kind': 'picture', 'rgb': rgb, 'brim_m': round(.11 + draw(pid, 'brim') * .05, 3), 'cock': round(side * (.3 + draw(pid, 'cock') * .5), 2),
            'droop': round(draw(pid, 'droop') * .25, 2), 'crown_m': round(.055 + draw(pid, 'pcrown') * .025, 3)}
    if season == 'summer' or draw(pid, 'ptrim' + season) < .35:
        fname, a, b = choose(pid, 'flowers' + season, FLOWERS)
        spec['trim'] = {'flowers': {'n': 6 + int(draw(pid, 'nflowers') * 6), 'rgb': a, 'rgb2': b, 'side': -side, 'spread': round(1.2 + draw(pid, 'spread') * 1.6, 2)}}
        if draw(pid, 'bow' + season) < .4:
            spec['trim']['bow'] = {'rgb': dark(base_rgb) if sum(base_rgb) > .6 else base_rgb, 'side': side}
        words = f'a wide {sname} hat trimmed with {fname}'
    else:
        pname, prgb = choose(pid, 'plume' + season, PLUMES)
        spec['trim'] = {'plumes': {'n': 2 + int(draw(pid, 'nplumes') * 2), 'rgb': prgb, 'side': side}}
        words = f'a wide {sname} hat with {pname} ostrich plumes'
    return spec, words


def outfit(pid, season, kind, cloth):
    """One dress, by kind: colours, pieces left off, finery and words."""
    cname, rgb = cloth
    lname, lrgb = lace(pid, 'lace' + kind)
    colours = {J: rgb, S: rgb}
    hide, pieces, fin = [], {}, {}
    if kind == 'suit':
        braid = dark(rgb) if sum(rgb) > .3 else r3([.02, .02, .025]) if cname != 'black' else [.002, .002, .003]
        pieces = {'lady_jacket_revers': dark(rgb) if sum(rgb) > .15 else rgb}
        high = round(.1 + draw(pid, 'sbraid' + season) * .2, 3)
        fin = {J: {'trims': [{'kind': 'braid', 'from': 'hem', 'at_m': .05, 'width_m': .06, 'rgb': braid},
                             {'kind': 'braid', 'from': 'cuff', 'at_m': .06, 'width_m': .07, 'rgb': braid}]},
               S: {'trims': [{'kind': 'braid', 'from': 'hem', 'at_m': high, 'width_m': round(.07 + draw(pid, 'sbw') * .06, 3), 'rgb': braid},
                             {'kind': 'ribbon', 'from': 'hem', 'at_m': .05, 'width_m': .02, 'rgb': braid}]},
               'lady_jacket_revers': {'velvet': 1}}
        if draw(pid, 'suitcheck') < .25:
            check = tonal(rgb, 1.5)
            fin[J]['pattern'] = fin[S]['pattern'] = {'kind': 'check' if draw(pid, 'ck') < .5 else 'pinstripe', 'rgb': check, 'repeat_m': .012, 'contrast': .5}
        words = f'a {cname} tailored walking suit, braided at the hem and cuffs, velvet revers'
    elif kind == 'afternoon':
        hide = ['lady_jacket_basque']
        ribbon = dark(rgb) if sum(rgb) > .4 else tonal(rgb, 2.2)
        pat = pick(pid, 'apat' + season, [(None, 4), ('dot', 2), ('stripe', 2), ('damask', 2), ('sprig', 1)])
        fin = {J: {'silk': .7, 'trims': [{'kind': 'lace', 'from': 'top', 'at_m': .07, 'width_m': .13, 'rgb': lrgb},
                                         {'kind': 'ribbon', 'from': 'hem', 'at_m': .022, 'width_m': .045, 'rgb': ribbon},
                                         {'kind': 'lace', 'from': 'cuff', 'at_m': .06, 'width_m': .12, 'rgb': lrgb}]},
               S: {'silk': .7, 'trims': [{'kind': 'flounce', 'from': 'hem', 'at_m': .1, 'width_m': .2, 'rgb': tonal(rgb, 1.08)},
                                         {'kind': 'lace', 'from': 'hem', 'at_m': .25, 'width_m': .06, 'rgb': lrgb},
                                         {'kind': 'ribbon', 'from': 'hem', 'at_m': .32, 'width_m': .018, 'rgb': ribbon}]}}
        if draw(pid, 'bertha') < .5:
            pieces = {'lady_jacket_revers': lrgb}
            fin['lady_jacket_revers'] = {'trims': [{'kind': 'lace', 'from': 'top', 'at_m': .2, 'width_m': .5, 'rgb': lrgb}]}
            bertha = ', a lace bertha'
        else:
            hide = hide + ['lady_jacket_revers']
            bertha = ''
        figure = ''
        if pat:
            prgb = {'dot': LACE[1][1] if sum(rgb) < 1 else dark(rgb), 'stripe': tonal(rgb, 1.45) if sum(rgb) < 1 else dark(rgb),
                    'damask': tonal(rgb, 1.5), 'sprig': dark(rgb) if sum(rgb) > 1 else LACE[0][1]}[pat]
            rep = {'dot': .025, 'stripe': .016, 'damask': .09, 'sprig': .03}[pat]
            fin[J]['pattern'] = fin[S]['pattern'] = {'kind': pat, 'rgb': prgb, 'repeat_m': rep, 'contrast': 1 if pat != 'damask' else .9}
            figure = {'dot': 'spotted foulard ', 'stripe': 'striped ', 'damask': 'figured ', 'sprig': 'flowered '}[pat]
        words = f'a {cname} {figure}silk afternoon dress, a {lname} lace yoke and cuffs{bertha}, a flounced hem banded with lace and ribbon'
    elif kind == 'velvet':
        band = tonal(rgb, 2.2)
        # Her own banding: from one broad band to four narrow ones, or soutache, or jet.
        n = 1 + int(draw(pid, 'vbands' + season) * 4)
        w = round(.05 - .008 * n, 3)
        how = pick(pid, 'vhow' + season, [('ribbon', 3), ('braid', 1), ('jet', 1)])
        brgb = [.002, .002, .003] if how == 'jet' else band
        skirt = [{'kind': how if how != 'braid' else 'ribbon', 'from': 'hem', 'at_m': round(.06 + i * (w + .035), 3), 'width_m': w, 'rgb': brgb} for i in range(min(n, 3))]
        if how == 'braid':
            skirt = [{'kind': 'braid', 'from': 'hem', 'at_m': .14, 'width_m': .12, 'rgb': band}, {'kind': 'ribbon', 'from': 'hem', 'at_m': .05, 'width_m': .025, 'rgb': band}]
        fin = {J: {'velvet': 1, 'trims': [{'kind': how if how == 'jet' else 'ribbon', 'from': 'hem', 'at_m': .05, 'width_m': .05, 'rgb': brgb},
                                          {'kind': 'lace', 'from': 'cuff', 'at_m': .05, 'width_m': .1, 'rgb': lrgb}]},
               S: {'velvet': 1, 'trims': skirt}}
        if draw(pid, 'vyoke' + season) < .4:
            fin[J]['trims'].append({'kind': 'lace', 'from': 'top', 'at_m': .06, 'width_m': .11, 'rgb': lrgb})
        words = f'a {cname} velvet afternoon dress ' + {'ribbon': 'banded with ribbon', 'braid': 'worked with soutache', 'jet': 'trimmed with jet'}[how] + f', {lname} lace at the wrists'
    elif kind == 'jet':
        jet = [.002, .002, .003]
        fin = {J: {'silk': .6, 'trims': [{'kind': 'jet', 'from': 'top', 'at_m': .1, 'width_m': .13, 'rgb': jet},
                                         {'kind': 'jet', 'from': 'hem', 'at_m': .03, 'width_m': .04, 'rgb': jet},
                                         {'kind': 'jet', 'from': 'cuff', 'at_m': .05, 'width_m': .06, 'rgb': jet}]},
               S: {'silk': .6, 'pattern': {'kind': 'damask', 'rgb': tonal(rgb, 2.4), 'repeat_m': .09, 'contrast': 1},
                   'trims': [{'kind': 'flounce', 'from': 'hem', 'at_m': .07, 'width_m': .14, 'rgb': rgb},
                             {'kind': 'jet', 'from': 'hem', 'at_m': .17, 'width_m': .05, 'rgb': jet}]}}
        words = f'a {cname} figured silk dress worked with jet beads at the bodice, wrists and hem'
    elif kind == 'shirtwaist':
        hide = ['lady_jacket_revers', 'lady_jacket_basque']
        wname, wrgb = choose(pid, 'waist', LIGHT[:5])
        sk = cloth if sum(rgb) < .9 else choose(pid, 'wskirt', RICH[:3] + [('white linen', [.70, .69, .64])])
        colours = {J: wrgb, S: sk[1]}
        belt = [.012, .012, .014] if sum(sk[1]) < .5 else sk[1]
        sb = dark(sk[1]) if sum(sk[1]) > .5 else [.005, .005, .008]
        fin = {J: {'trims': [{'kind': 'tucks', 'from': 'top', 'at_m': .12, 'width_m': .16, 'rgb': wrgb, 'rows': 9},
                             {'kind': 'lace', 'from': 'top', 'at_m': .23, 'width_m': .035, 'rgb': lrgb},
                             {'kind': 'ribbon', 'from': 'hem', 'at_m': .025, 'width_m': .05, 'rgb': belt}]},
               S: {'trims': [{'kind': 'braid' if sum(sk[1]) < .5 else 'tucks', 'from': 'hem', 'at_m': .13, 'width_m': .08, 'rgb': sb, 'rows': 6},
                             {'kind': 'ribbon', 'from': 'hem', 'at_m': .05, 'width_m': .02, 'rgb': sb}]}}
        words = f'a tucked {wname} shirtwaist with lace insertion, a belted {sk[0]} skirt'
    else:  # lingerie
        wname, wrgb = choose(pid, 'lingerie', LIGHT[:2])
        sname, srgb = choose(pid, 'sash', [('pale blue', [.22, .34, .55]), ('rose', [.55, .25, .30]), ('lilac', [.33, .24, .45]),
                                           ('yellow', [.62, .50, .14]), ('black velvet', [.012, .012, .014])])
        hide = ['lady_jacket_revers', 'lady_jacket_basque']
        colours = {J: wrgb, S: wrgb}
        fin = {J: {'trims': [{'kind': 'lace', 'from': 'top', 'at_m': .08, 'width_m': .15, 'rgb': lrgb},
                             {'kind': 'ribbon', 'from': 'hem', 'at_m': .03, 'width_m': .06, 'rgb': srgb},
                             {'kind': 'lace', 'from': 'cuff', 'at_m': .06, 'width_m': .1, 'rgb': lrgb}]},
               S: {'trims': [{'kind': 'lace', 'from': 'hem', 'at_m': .09, 'width_m': .09, 'rgb': lrgb},
                             {'kind': 'tucks', 'from': 'hem', 'at_m': .22, 'width_m': .1, 'rgb': wrgb, 'rows': 6},
                             {'kind': 'lace', 'from': 'hem', 'at_m': .34, 'width_m': .06, 'rgb': lrgb},
                             {'kind': 'embroidery', 'from': 'hem', 'at_m': .5, 'width_m': .12, 'rgb': lrgb}]}}
        words = f'a {wname} lingerie dress of sheer cotton, {lname} lace yoke and insertion, a {sname} sash'
        cname, rgb = wname, wrgb
    return {'colours': {k: r3(v) for k, v in colours.items()}, 'hide': hide, 'pieces': {k: r3(v) for k, v in pieces.items()}, 'finery': fin}, words, rgb


SUMMER = [('afternoon', 4), ('lingerie', 4), ('shirtwaist', 3), ('suit', 1)]
MID = [('suit', 4), ('afternoon', 3), ('velvet', 1)]
WINTER = [('suit', 3), ('velvet', 3), ('afternoon', 1)]


def lady(pid, age):
    """A lady of the house, dressed for summer (her record), spring and fall, and winter."""
    matron = age is not None and age >= 60 and draw(pid, 'matron') < .7
    looks = {}
    for season, deal in (('summer', SUMMER), ('mid', MID), ('winter', WINTER)):
        if matron:
            kind = 'jet' if draw(pid, 'mkind' + season) < .55 else ('afternoon' if season != 'winter' else 'velvet')
            cloth = choose(pid, 'mcloth' + season, HALF_MOURNING if kind != 'velvet' else HALF_MOURNING[:1] + RICH[2:4])
        else:
            kind = pick(pid, 'kind' + season, deal)
            palette = LIGHT if season == 'summer' and kind in ('afternoon',) else RICH if kind in ('suit', 'velvet') else RICH + LIGHT
            if season == 'summer' and kind == 'suit':
                palette = [c for c in LIGHT if c[0] in ('dove grey', 'biscuit', 'ivory')] + [c for c in RICH if c[0] in ('navy', 'fawn', 'grey')]
            cloth = choose(pid, 'cloth' + season + kind, palette)
        d, words, rgb = outfit(pid, season, kind, cloth)
        hat_kind = 'sailor' if kind == 'shirtwaist' and season == 'summer' else 'toque' if (season == 'winter' and draw(pid, 'wtoque') < .5) else 'picture'
        h, hwords = hat(pid, season, hat_kind, rgb, matron=matron and season != 'summer')
        d['hat'] = h
        d['hide'] = sorted(set(d['hide'] + LADY_HAT_HIDE))
        d['worn'] = f'{words}; {hwords}'
        looks[season] = d
    rec = {**looks['summer'], 'seasons': {'spring': looks['mid'], 'fall': looks['mid'], 'winter': looks['winter']}}
    return rec


# --- servants: plainer, and still each her own ---------------------------------------------------
PRINT_GROUNDS = [('lilac', [.40, .33, .50]), ('blue', [.32, .40, .55]), ('pink', [.60, .42, .44]), ('grey', [.38, .38, .36]),
                 ('buff', [.52, .44, .30])]
PRINT_FIGURES = [[.07, .06, .14], [.05, .08, .2], [.25, .05, .06], [.66, .64, .60]]


def maid(pid, rgb):
    """A housemaid: her black (or dark) afternoon dress, or the print cotton she wears in the morning."""
    if draw(pid, 'mprint') < .45:
        gname, ground = choose(pid, 'mground', PRINT_GROUNDS)
        kind = choose(pid, 'mpattern', ['stripe', 'pinstripe', 'check', 'dot', 'sprig'])
        fig = choose(pid, 'mfig', PRINT_FIGURES[:3]) if sum(ground) > .9 else PRINT_FIGURES[3]
        rep = {'stripe': .012, 'pinstripe': .01, 'check': .01, 'dot': .016, 'sprig': .022}[kind]
        f = {'pattern': {'kind': kind, 'rgb': r3(fig), 'repeat_m': rep, 'contrast': .9}}
        words = {'stripe': 'striped', 'pinstripe': 'pin-striped', 'check': 'checked', 'dot': 'spotted', 'sprig': 'sprigged'}[kind]
        return {'colours': {'garment_upper__maid_dress_black': r3(ground), 'garment_lower__maid_skirt_black': r3(ground)},
                'finery': {'garment_upper__maid_dress_black': f, 'garment_lower__maid_skirt_black': f},
                'worn': f'a {gname} {words} cotton morning dress, white apron, collar, cuffs and cap'}
    return None


def cook(pid, rgb):
    """A cook: her print dress (the body's material says print; now it is drawn as one) and a checked apron."""
    gname, ground = choose(pid, 'cground', PRINT_GROUNDS + [('navy', [.04, .06, .12]), ('brown', [.12, .07, .04])])
    kind = choose(pid, 'cpattern', ['sprig', 'dot', 'stripe', 'check'])
    fig = PRINT_FIGURES[3] if sum(ground) < .6 else choose(pid, 'cfig', PRINT_FIGURES[:3])
    rep = {'stripe': .012, 'check': .012, 'dot': .016, 'sprig': .022}[kind]
    f = {'pattern': {'kind': kind, 'rgb': r3(fig), 'repeat_m': rep, 'contrast': .85}}
    aname, arw = choose(pid, 'capron', [('blue', [.12, .2, .42]), ('red', [.38, .06, .05]), ('brown', [.2, .12, .06])])
    words = {'stripe': 'striped', 'check': 'checked', 'dot': 'spotted', 'sprig': 'sprigged'}[kind]
    return {'colours': {'garment_upper__cook_print_dress': r3(ground), 'garment_lower__cook_print_skirt': r3(ground),
                        'garment_outer__cook_apron_check': [.62, .6, .55]},
            'finery': {'garment_upper__cook_print_dress': f, 'garment_lower__cook_print_skirt': f,
                       'garment_outer__cook_apron_check': {'pattern': {'kind': 'check', 'rgb': r3(arw), 'repeat_m': .018, 'contrast': .9}}},
            'worn': f'a {gname} {words} print working dress, a {aname}-and-white checked apron'}


def companion(pid, rgb):
    """A nurse, governess or companion: a tucked shirtwaist and her own skirt."""
    sname, srgb = choose(pid, 'wst', LIGHT[:5])
    kname, krgb = choose(pid, 'wsk', RICH[:3] + RICH[5:7])
    return {'colours': {'garment_upper__errand_shirtwaist_white': r3(srgb), 'garment_lower__errand_skirt_navy': r3(krgb)},
            'finery': {'garment_upper__errand_shirtwaist_white': {'trims': [{'kind': 'tucks', 'from': 'top', 'at_m': .12, 'width_m': .16, 'rgb': r3(srgb), 'rows': 8}]},
                       'garment_lower__errand_skirt_navy': {'trims': [{'kind': 'braid', 'from': 'hem', 'at_m': .12, 'width_m': .07, 'rgb': [.006, .006, .008]}]}},
            'worn': f'a tucked {sname} shirtwaist, a braided {kname} walking skirt'}


def girl(pid, role):
    """A daughter of the house: a white or pale frock with a coloured sash and lace, or a coloured one."""
    name, rgb = choose(pid, 'frock', LIGHT[:6] + [('navy', [.02, .03, .075]), ('red', [.2, .03, .03])])
    sname, srgb = choose(pid, 'gsash', [('pale blue', [.22, .34, .55]), ('rose', [.55, .25, .30]), ('red', [.35, .04, .04]), ('navy', [.02, .03, .075])])
    lrgb = LACE[1][1]
    fin = {'garment_upper__child_frock_1904': {'trims': [{'kind': 'lace', 'from': 'top', 'at_m': .05, 'width_m': .08, 'rgb': lrgb},
                                                         {'kind': 'ribbon', 'from': 'hem', 'at_m': .03, 'width_m': .05, 'rgb': srgb}]},
           'garment_lower__child_frock_1904': {'trims': [{'kind': 'lace' if sum(rgb) > 1 else 'ribbon', 'from': 'hem', 'at_m': .05, 'width_m': .06, 'rgb': lrgb if sum(rgb) > 1 else srgb},
                                                         {'kind': 'tucks', 'from': 'hem', 'at_m': .16, 'width_m': .08, 'rgb': r3(rgb), 'rows': 5}]}}
    return {'colours': {'garment_upper__child_frock_1904': r3(rgb), 'garment_lower__child_frock_1904': r3(rgb)},
            'finery': fin, 'worn': f'a {name} frock with lace and tucks, a {sname} sash, and stockings'}
