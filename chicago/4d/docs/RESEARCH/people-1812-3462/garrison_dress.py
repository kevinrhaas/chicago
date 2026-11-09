# SPDX-License-Identifier: GPL-3.0-or-later
"""T-3523: what each man of the 1812 garrison wears and carries, by his rank and his duty.

The owner, 2026-11-08, beside an Ogden-style plate of the army about 1812: "and all the men
soldiers have the same hats? Dont the soldiers have different appearance based on rank? and
none of them appear to have firearms?" T-3462 stood every enlisted man in the one private's
dress, his rank only on his card. This is the table place.py reads to dress and arm each man,
and it writes data/humans/variation/dress_1812_garrison.json, which the variation kit carries
into the persons file (`dress`) and the renderer draws (human-looks.js recolours and hides,
human-garrison.js draws the rank marks, drum, fife case and musket at load). No new figure file.

What the readings give (docs/RESEARCH/people-1812-3461/dress.json and its sources):

  * NCOs and musicians draw the private's clothing (the 1802 act, Sec. 8; again in January
    1812): one cap, so every enlisted man wears the same felt cap, as the plate shows.
  * Sergeants two white worsted epaulettes, corporals one on the right shoulder: inferred by
    analogy from the light dragoons' rule printed in 1814 (p. 271); the worsted's colour is
    reconstructed.
  * Musicians in red coats faced blue: Krimmel's volunteer drummer of 1811-13, inferred for the
    regulars; the drum's paint is reconstructed; a fifer's fife case in place of the cartridge
    box is reconstructed.
  * Officers: chapeau, epaulettes by grade (a captain one on the right, lieutenants on the
    left: the light artillery's rule printed 1814, p. 273, by analogy; the ensign as a
    lieutenant, reconstructed), a crimson sash round the waist only on a tour of duty (the
    artillery officers' text, p. 263-268), the surgeon's mate's black velvet cape and black
    plume (the same text), and swords (the figures' own).
  * Fatigue: "one coarse linen frock and trowsers for fatigue clothing" a year (1802 act; again
    1812); no fatigue cap is issued, so a man at work is bareheaded or in a round hat of his
    own (reconstructed); a man in shirt-sleeves and waistcoat is as well supported. Drawn on the
    1812 settler's working body (shirt, neckerchief, waistcoat, loose trousers), recoloured to
    unbleached linen with the black stock for the neckerchief; the frock itself is not drawn.
  * Arms: the men still had their muskets on the 14th; what was destroyed the night of the 13th
    was the surplus (Heald's report, "the surplus arms and ammunition", Quaife 1913). How each
    duty carries them is reconstructed (liberty L-1812-garrison-dress-3523): a sentry walking his
    post at the shoulder, the guard's sergeant and corporal and a sentry standing at the order,
    men under arms walking out from the pickets at the shoulder, men at chores unarmed, and the
    party at the cornfield at the forks with its arms piled at the field's edge.

Run through place.py (which writes the file with the instances); `--check` there checks it too.
"""
from __future__ import annotations

LIBERTY = 'L-1812-garrison-dress-3523'
SOURCES = ['us_1812_rules_and_articles_albany', 'us_1814_military_laws_and_regulations',
           'met_krimmel_1813_philadelphia_soldiery', 'loc_ogden_1888_infantry_artillery_1802_1810', 'quaife_1913']

FATIGUE_ASSET = 'settler_1812'
DRESS_ASSET = 'private_first_infantry_1812'

# The fatigue dress on the settler's body: unbleached shirt, black stock, linen trousers; the
# waistcoat white (the issued vest) or left off (shirt-sleeves), the round hat kept or left off.
FATIGUE_COLOURS = {
    'garment_upper__shirt_tow_linen_1810': [0.62, 0.58, 0.49],
    'accessory__neckerchief_blue_1810': [0.010, 0.010, 0.011],
    'garment_outer__waistcoat_brown_1810': [0.70, 0.69, 0.64],
    'garment_lower__trousers_linen_1810': [0.56, 0.52, 0.43],
    'headwear__round_hat_black_1810': [0.014, 0.013, 0.012],
    'footwear__shoes_dark_1810': [0.012, 0.011, 0.011],
}
# The musicians' coat: scarlet faced blue (the private's coat and facings recoloured).
MUSICIAN_COLOURS = {
    'garment_upper__coat_blue_1812': [0.36, 0.028, 0.022],
    'garment_upper__facings_red_1812': [0.014, 0.019, 0.055],
}
SURGEON_COLOURS = {
    'garment_upper__facings_scarlet_1812': [0.008, 0.008, 0.009],
    'headwear__plume_white_1812': [0.012, 0.012, 0.013],
}

# Station -> duty dress. Stations not named keep the dress coat, unarmed.
# The fatigue party drawn up on the parade to be told off stands in its coats (Paul Grummo's
# own record, T-3452, among them); the men already at their work are in fatigue clothes.
FATIGUE = {'garden_a', 'garden_b', 'garden_c', 'garden_d', 'sutler_garden', 'forks_cornfield_a', 'forks_cornfield_b',
           'forks_walk', 'road_walk_b', 'bake_house', 'armourer', 'wharf_a', 'wharf_b'}
SHOULDER = {'gate_west', 'gate_east', 'magazine', 'road_walk', 'river_walk'}
ORDER = {'gate_sergeant', 'gate_corporal', 'blockhouse_se'}
# The cornfield party's arms, piled just outside the field's west edge (E 142.4, the T-2512
# rectangle), on the record of its first man.
PILES = {'forks_cornfield_a': {'local_e': 140.3, 'local_n': -238.6, 'heading_deg': 20, 'count': 3, 'scene': '1812'}}
# The wagon round's two men (T-3497) are drawn by the wagon's own driver figure: not here.
SKIP = {'mills_elias', 'moffett_william'}

OFFICERS = {
    'heald_nathan': ('captain', ['sash_crimson'], [],
                     "the captain's coat and chapeau, his silver epaulette on the right shoulder, a crimson sash round the waist (on duty) and his sword"),
    'helm_linai': ('second lieutenant', ['epaulette_bullion_l', 'sash_crimson'], ['epaulette_right'],
                   "the officer's coat and chapeau, a lieutenant's silver epaulette on the left shoulder, a crimson sash round the waist (on duty) and his sword"),
    'ronan_george': ('ensign', ['epaulette_bullion_l', 'sash_crimson'], ['epaulette_right'],
                     "the officer's coat and chapeau, a silver epaulette on the left shoulder as a lieutenant wears it (an ensign's is not recorded), a crimson sash round the waist (on duty) and his sword"),
    'van_voorhis_isaac': ("surgeon's mate", [], [],
                          "the officer's coat with the medical staff's black velvet collar and cuffs, a chapeau with a black plume, no sash, and his sword"),
}


def _hat_kept(pid):
    """One in three at work keeps a round hat of his own; the rest are bareheaded."""
    return sum(map(ord, pid)) % 3 == 0


def _waistcoat_kept(pid):
    return sum(map(ord, pid)) % 4 != 1


def dress_for(pid, rank, station):
    """(asset, garrison dress record or None, words for the card)."""
    if pid in SKIP:
        return DRESS_ASSET, None, None
    rec = {'rank': rank, 'station': station, 'marks': [], 'colours': {}, 'hide': [], 'arms': None, 'carry': None}
    words = []
    asset = DRESS_ASSET
    if station in FATIGUE:
        asset = FATIGUE_ASSET
        rec['colours'] = dict(FATIGUE_COLOURS)
        hat, vest = _hat_kept(pid), _waistcoat_kept(pid)
        if not hat:
            rec['hide'].append('headwear_round_hat')
        if not vest:
            rec['hide'].append('waistcoat_brown')
        words.append('his fatigue clothes: an unbleached linen shirt' + (' and white waistcoat' if vest else ' in his sleeves')
                     + ', a black stock and loose linen trousers, ' + ('a round hat of his own' if hat else 'bareheaded')
                     + ', without coat, cap or belts')
    else:
        if rank in ('drummer', 'fifer'):
            rec['colours'] = dict(MUSICIAN_COLOURS)
            rec['hide'].append('cartridge_box_and_scabbard')
            rec['carry'] = 'drum' if rank == 'drummer' else 'fife'
            words.append("a musician's red coat faced blue, the felt cap, white overalls, " +
                         ('his drum on its carriage' if rank == 'drummer' else 'his fife case at his hip'))
        else:
            words.append("the company's blue coat faced red, the tall felt cap with its white feather, white crossbelts and linen overalls")
        if rank == 'sergeant':
            rec['marks'] = ['epaulette_worsted_l', 'epaulette_worsted_r']
            words.append("a sergeant's two white worsted epaulettes")
        elif rank == 'corporal':
            rec['marks'] = ['epaulette_worsted_r']
            words.append("a corporal's white worsted epaulette on the right shoulder")
    if station in SHOULDER:
        rec['arms'] = 'shoulder'
        words.append('his musket with the bayonet fixed, at the shoulder')
    elif station in ORDER:
        rec['arms'] = 'order'
        words.append('his musket with the bayonet fixed, at the order')
    elif station in FATIGUE:
        words.append('no musket at his work' + (' (the party\'s arms stand piled at the field\'s edge)' if station.startswith('forks_') else ''))
    if station in PILES:
        rec['pile'] = dict(PILES[station])
    return asset, _finish(rec), '; '.join(words)


def officer_dress(pid):
    rank, marks, hide, words = OFFICERS[pid]
    rec = {'rank': rank, 'station': 'officer', 'marks': marks, 'colours': dict(SURGEON_COLOURS) if pid == 'van_voorhis_isaac' else {},
           'hide': hide, 'arms': None, 'carry': None}
    return _finish(rec), words


def _finish(rec):
    out = {k: v for k, v in rec.items() if v not in (None, [], {})}
    out['grade'] = 'reconstructed'
    out['liberty'] = LIBERTY
    return out


def dress_file(entries):
    """entries: {pid: (asset, rec, words)}."""
    persons = {}
    for pid in sorted(entries):
        asset, rec, words = entries[pid]
        if rec is None:
            continue
        p = {'asset': asset, 'origin': 'garrison'}
        if rec.get('colours'):
            p['colours'] = rec['colours']
        p['hide'] = rec.get('hide', [])
        p['garrison'] = {k: v for k, v in rec.items() if k not in ('colours', 'hide')}
        p['worn'] = words
        persons[pid] = p
    return {
        'format': 'chicago4d_human_dress_v1',
        'ticket': 'T-3523',
        'scene': '1812',
        'generated_by': 'docs/RESEARCH/people-1812-3462/place.py (garrison_dress.py)',
        'liberty': LIBERTY,
        'sources': SOURCES,
        '_doc': ("Each man of the 1812 garrison's dress by rank and duty: `colours` (linear RGB) replace the named "
                 "material's colour on clones and `hide` names pieces not worn (human-looks.js dressCloth); `garrison` "
                 "is what human-garrison.js draws: `marks` (epaulette_worsted|bullion_l|r, sash_crimson), `carry` "
                 "(drum, fife), `arms` (shoulder, order: the musket in a held hand) and a `pile` of arms in the scene. "
                 "From the 1812 dress research (docs/RESEARCH/people-1812-3461/dress.json); who wears what is "
                 "reconstructed. Regenerate with the generator; never edit by hand."),
        'persons': persons,
    }
