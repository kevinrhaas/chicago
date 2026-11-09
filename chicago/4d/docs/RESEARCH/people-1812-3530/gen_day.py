#!/usr/bin/env python3
"""T-3530: the day reading for the Potawatomi family who live at the lodges by the river all 1812.

    python3 docs/RESEARCH/people-1812-3530/gen_day.py [--check]

WHY. The owner, 2026-11-09, on the card asking whether T-3528's year-round lodges by the river
should have people living in them, chose "One family lives there all year": "Two or three lodges
with a small Potawatomi family of about six to eight, with researched reconstructed names and
histories like the gathering's people."

This writes docs/RESEARCH/people-1812-3530/day.json in the shape of the other 1812 day readings
(docs/RESEARCH/people-1812-34NN/day.json), which docs/RESEARCH/people-1812-town/cards.py turns
into the household card (hh_potawatomi_lodges_1812), place_town.py into the drawn instances and
looks.py into their looks; tools/native_cards_1812.py then gives each a reconstructed name,
gens and history as it does every unnamed Native card.

WHAT IS THE SOURCES' AND WHAT IS OURS. Currey (1912 ch. II) has the Potawatomi come and go by
habit, camp by the river at the creek's mouth, and bring in furs and maple sugar to the traders;
Juliette Kinzie (Wau-Bun ch. XV, 1831) saw families carry their goods "to their
wintering-grounds" and come back in spring. Everything about this family is reconstructed
(liberty L-1812-river-family-3530): that one family stayed by the river through the winter,
rather than going to the wintering grounds, hunting from here and trading at the post (the
owner's choice); who is in it (a man, his wife, her mother, a son of sixteen, a daughter of
twelve, a boy of eight and a girl of five); their ages, looks and dress; and every hour of their
days. Their days run in four kinds: the warm months at the lodges (April to October), a trading
morning at the government factory about one day in six until Irwin left on 5 July (the
factory's own record), the cold months (November to March) more indoors with the man out
hunting, and 15 August, when the man and his son are away with the warriors (reconstructed, as
native_cards_1812.py grades every man of 16 to 55 of the gathering). Nothing of the fighting,
the trade or any ceremony is staged.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / 'day.json'
HOME = 'potawatomi_trading_lodges_1812'
HH = 'hh_potawatomi_lodges_1812'
LIB = 'L-1812-river-family-3530'

# Points on the ground (local E, N), clear of the lodges the archetype lays there
# (generators/archetypes/lodge_camp.py layout for the record; doors in data/humans/doors_1812.json).
P = {
    'hearth_w': (701.9, -26.0, 200),     # west hearth, 700.69/-27.14
    'hearth_e': (716.9, -27.0, 190),     # east hearth, 716.64/-28.44
    'rack': (720.0, -21.0, 160),         # drying rack, 720.74/-19.64
    'mortar': (709.9, -20.2, 200),       # mortar, 708.87/-21.29
    'woodpile': (712.0, -31.6, 95),      # woodpile, 713.41/-30.77
    'scaffold': (720.0, -28.4, 70),      # scaffold, 721.07/-26.69
    'hide': (705.0, -31.4, 230),         # hide frame, 703.73/-30.04
    'canoe_w': (707.6, -16.6, 20),       # by the west canoe, 706.42/-18.31
    'canoe_e': (716.3, -16.6, 340),      # by the east canoe, 714.97/-18.29
    'bank': (711.0, -11.5, 0),           # the river bank north of the canoes
    'yard': (712.0, -26.5, 0),           # the open middle of the ground
    'play': (711.0, -15.0, 30),          # between the canoes and the bank
    'factory': (1080.0, 216.0, 275),     # before first_fort_outer_factory (as the T-3467 readings stand)
}
FACTORY_NEAR = [(1078.6, 217.6, 275), (1079.2, 214.2, 275), (1081.6, 218.4, 275)]


def at(key, de=0.0, dn=0.0):
    e, n, h = P[key]
    return {'local_e': round(e + de, 2), 'local_n': round(n + dn, 2), 'heading_deg': h}


def indoors(a, b, doing, basis='@lodge'):
    return {'from': a, 'to': b, 'indoors': True, 'where': HOME, 'doing': doing, 'grade': 'reconstructed', 'basis': basis}


def out(a, b, where, doing, key, act='stand', de=0.0, dn=0.0, basis='@lodge_work', with_=None):
    s = {'from': a, 'to': b, 'indoors': False, 'where': where, 'doing': doing, 'at': at(key, de, dn), 'activity': act,
         'grade': 'reconstructed', 'basis': basis}
    if with_:
        s['with'] = with_
    return s


def away(a, b, doing, basis='@away'):
    return {'from': a, 'to': b, 'indoors': False, 'where': 'away (not drawn)', 'doing': doing, 'grade': 'reconstructed', 'basis': basis}


W = 'outdoors at the lodges by the river'
FAM = {k: f'new:river_lodges_{k}_1812' for k in ('man', 'woman', 'grandmother', 'son', 'daughter', 'boy', 'girl')}

# ── each person's warm-month day, cold-month day, and the special ones ──────────────────────
WARM = {
    'man': [indoors(0, 5.0, 'asleep in the lodge'), out(5.0, 6.0, W, 'at the fire in the morning', 'hearth_w', 'sit'),
            out(6.0, 9.5, 'outdoors on the river bank', 'fishing from the bank below the lodges', 'bank', 'work', basis='@river_round'),
            out(9.5, 10.5, W, 'eating at the fire with the household', 'hearth_w', 'sit', de=0.8, basis='@meal'),
            out(10.5, 13.0, W, 'mending a canoe drawn up on the bank', 'canoe_w', 'work'),
            out(13.0, 16.0, W, 'resting by the lodge', 'yard', 'sit', de=-1.0),
            out(16.0, 18.0, W, 'cleaning the fish and setting them on the rack', 'rack', 'work'),
            out(18.0, 19.5, W, 'eating at the fire with the household', 'hearth_w', 'sit', de=0.8, basis='@meal'),
            out(19.5, 21.0, W, 'evening at the fire', 'hearth_w', 'sit', de=0.8),
            indoors(21.0, 24, 'asleep in the lodge')],
    'woman': [indoors(0, 5.0, 'asleep in the lodge'), out(5.0, 6.5, W, 'lighting the fire and putting the kettle on', 'hearth_w', 'work'),
              out(6.5, 9.5, W, 'pounding corn at the mortar', 'mortar', 'work'),
              out(9.5, 10.5, W, 'eating at the fire with the household', 'hearth_w', 'sit', dn=0.9, basis='@meal'),
              out(10.5, 13.5, W, 'scraping a deerskin on the frame', 'hide', 'work'),
              out(13.5, 16.0, W, 'sewing moccasins in the shade of the lodge', 'yard', 'sit', de=0.4),
              out(16.0, 18.0, W, 'cooking at the east fire', 'hearth_e', 'work'),
              out(18.0, 19.5, W, 'eating at the fire with the household', 'hearth_w', 'sit', dn=0.9, basis='@meal'),
              out(19.5, 21.0, W, 'evening at the fire', 'hearth_w', 'sit', dn=0.9),
              indoors(21.0, 24, 'asleep in the lodge')],
    'grandmother': [indoors(0, 6.0, 'asleep in the bark house'), out(6.0, 9.5, W, 'tending the east fire', 'hearth_e', 'work'),
                    out(9.5, 10.5, W, 'eating at the fire with the household', 'hearth_w', 'sit', de=-0.9, basis='@meal'),
                    out(10.5, 13.0, W, 'weaving a rush mat in the shade', 'yard', 'sit', de=1.2, dn=0.6),
                    indoors(13.0, 15.5, 'resting in the bark house'),
                    out(15.5, 18.0, W, 'turning the fish on the rack', 'rack', 'work', de=-0.8),
                    out(18.0, 19.5, W, 'eating at the fire with the household', 'hearth_w', 'sit', de=-0.9, basis='@meal'),
                    indoors(19.5, 24, 'asleep in the bark house')],
    'son': [indoors(0, 5.5, 'asleep in the lodge'), out(5.5, 9.5, 'outdoors on the river bank', 'fishing with his father', 'bank', 'work', de=1.6, basis='@river_round'),
            out(9.5, 10.5, W, 'eating at the fire with the household', 'hearth_w', 'sit', dn=-0.9, basis='@meal'),
            out(10.5, 13.0, W, 'cutting and carrying firewood to the pile', 'woodpile', 'work'),
            out(13.0, 16.0, W, 'helping mend the canoe', 'canoe_w', 'work', de=1.2),
            out(16.0, 18.0, W, 'carrying water up from the river', 'canoe_e', 'work'),
            out(18.0, 19.5, W, 'eating at the fire with the household', 'hearth_w', 'sit', dn=-0.9, basis='@meal'),
            out(19.5, 21.0, W, 'evening at the fire', 'hearth_w', 'sit', dn=-0.9),
            indoors(21.0, 24, 'asleep in the lodge')],
    'daughter': [indoors(0, 5.5, 'asleep in the lodge'), out(5.5, 6.5, W, 'carrying water from the river for the kettle', 'canoe_e', 'work'),
                 out(6.5, 9.5, W, 'pounding corn with her mother', 'mortar', 'work', de=1.0),
                 out(9.5, 10.5, W, 'eating at the fire with the household', 'hearth_w', 'sit', de=0.9, dn=0.9, basis='@meal'),
                 out(10.5, 13.5, W, 'gathering rushes for mats by the river', 'bank', 'work', de=-2.5),
                 out(13.5, 16.0, W, 'weaving with her grandmother', 'yard', 'work', de=1.8, dn=0.6),
                 out(16.0, 18.0, W, 'helping at the east fire', 'hearth_e', 'work', de=0.8),
                 out(18.0, 19.5, W, 'eating at the fire with the household', 'hearth_w', 'sit', de=0.9, dn=0.9, basis='@meal'),
                 out(19.5, 21.0, W, 'evening at the fire', 'hearth_w', 'sit', de=0.9, dn=0.9),
                 indoors(21.0, 24, 'asleep in the lodge')],
    'boy': [indoors(0, 6.0, 'asleep in the lodge'), out(6.0, 9.5, W, 'playing on the bank by the canoes', 'play', 'work', basis='@child'),
            out(9.5, 10.5, W, 'eating at the fire with the household', 'hearth_w', 'sit', de=-0.8, dn=-0.8, basis='@meal'),
            out(10.5, 13.0, W, 'carrying sticks to the woodpile', 'woodpile', 'work', de=-1.0, basis='@child'),
            out(13.0, 16.0, W, 'playing on the bank by the canoes', 'play', 'work', de=1.4, basis='@child'),
            out(16.0, 18.0, W, 'watching the fish set on the rack', 'rack', 'work', dn=-1.2, basis='@child'),
            out(18.0, 19.5, W, 'eating at the fire with the household', 'hearth_w', 'sit', de=-0.8, dn=-0.8, basis='@meal'),
            indoors(19.5, 24, 'asleep in the lodge')],
    'girl': [indoors(0, 6.5, 'asleep in the lodge'), out(6.5, 9.5, W, 'beside her mother at the mortar', 'mortar', 'work', dn=1.0, basis='@child'),
             out(9.5, 10.5, W, 'eating at the fire with the household', 'hearth_w', 'sit', de=0.6, dn=-0.8, basis='@meal'),
             out(10.5, 13.0, W, 'playing on the bank by the canoes', 'play', 'work', de=-1.2, basis='@child'),
             indoors(13.0, 15.0, 'asleep in the heat of the day'),
             out(15.0, 18.0, W, 'with her grandmother at the rack', 'rack', 'work', de=-1.6, basis='@child'),
             out(18.0, 19.5, W, 'eating at the fire with the household', 'hearth_w', 'sit', de=0.6, dn=-0.8, basis='@meal'),
             indoors(19.5, 24, 'asleep in the lodge')],
}
COLD = {
    'man': [indoors(0, 6.5, 'asleep in the lodge'), out(6.5, 7.5, W, 'splitting wood at the pile', 'woodpile', 'work', basis='@winter'),
            away(7.5, 16.0, 'hunting in the timber along the river and the South Branch', '@winter'),
            out(16.0, 17.0, W, 'hanging the day\'s game on the scaffold', 'scaffold', 'work', basis='@winter'),
            indoors(17.0, 24, 'by the fire in the lodge, and asleep', '@winter')],
    'woman': [indoors(0, 7.0, 'asleep in the lodge'), out(7.0, 8.0, W, 'bringing in wood from the pile', 'woodpile', 'work', de=1.0, basis='@winter'),
              indoors(8.0, 11.0, 'sewing by the fire in the lodge', '@winter'),
              out(11.0, 13.0, W, 'scraping a winter hide on the frame', 'hide', 'work', basis='@winter'),
              indoors(13.0, 24, 'cooking and sewing by the fire in the lodge, and asleep', '@winter')],
    'grandmother': [indoors(0, 10.5, 'by the fire in the bark house', '@winter'),
                    out(10.5, 12.0, W, 'feeding the east fire', 'hearth_e', 'work', basis='@winter'),
                    indoors(12.0, 24, 'by the fire in the bark house, and asleep', '@winter')],
    'son': [indoors(0, 6.5, 'asleep in the lodge'), out(6.5, 7.5, W, 'carrying wood with his father', 'woodpile', 'work', de=-1.2, basis='@winter'),
            away(7.5, 16.0, 'hunting with his father', '@winter'),
            out(16.0, 17.0, W, 'helping hang the game', 'scaffold', 'work', de=-1.2, basis='@winter'),
            indoors(17.0, 24, 'by the fire in the lodge, and asleep', '@winter')],
    'daughter': [indoors(0, 7.0, 'asleep in the lodge'), out(7.0, 8.0, W, 'breaking the ice for water at the river', 'canoe_e', 'work', basis='@winter'),
                 indoors(8.0, 11.0, 'working quills by the fire', '@winter'),
                 out(11.0, 13.0, W, 'bringing in wood from the pile', 'woodpile', 'work', de=1.2, basis='@winter'),
                 indoors(13.0, 24, 'by the fire in the lodge, and asleep', '@winter')],
    'boy': [indoors(0, 11.5, 'by the fire in the lodge', '@winter'),
            out(11.5, 13.5, W, 'playing in the snow between the lodges', 'yard', 'stand', dn=1.4, basis='@winter'),
            indoors(13.5, 24, 'by the fire in the lodge, and asleep', '@winter')],
    'girl': [indoors(0, 11.5, 'by the fire in the lodge', '@winter'),
             out(11.5, 13.0, W, 'playing in the snow by her brother', 'yard', 'stand', de=1.4, dn=1.4, basis='@winter'),
             indoors(13.0, 24, 'by the fire in the lodge, and asleep', '@winter')],
}
TRADE = {   # the man, the woman and the daughter take furs and sugar to the factory
    'man': lambda: [indoors(0, 5.0, 'asleep in the lodge'), out(5.0, 8.0, W, 'loading the canoe with packs of furs', 'canoe_w', 'work', basis='@trade'),
                    away(8.0, 9.0, 'paddling down the river to the fort', '@trade'),
                    {'from': 9.0, 'to': 11.5, 'indoors': False, 'where': 'outdoors before first_fort_outer_factory',
                     'doing': 'trading furs at the government factory', 'at': {'local_e': FACTORY_NEAR[0][0], 'local_n': FACTORY_NEAR[0][1], 'heading_deg': 275},
                     'activity': 'stand', 'with': [FAM['woman'], FAM['daughter']], 'grade': 'reconstructed', 'basis': '@trade'},
                    away(11.5, 12.5, 'paddling home up the river', '@trade'),
                    out(12.5, 16.0, W, 'resting by the lodge after the trip', 'yard', 'sit', de=-1.0, basis='@trade')] + WARM['man'][6:],
    'woman': lambda: [indoors(0, 5.0, 'asleep in the lodge'), out(5.0, 8.0, W, 'packing maple sugar in bark boxes for trade', 'yard', 'work', basis='@trade'),
                      away(8.0, 9.0, 'paddling down the river to the fort', '@trade'),
                      {'from': 9.0, 'to': 11.5, 'indoors': False, 'where': 'outdoors before first_fort_outer_factory',
                       'doing': 'trading maple sugar at the government factory', 'at': {'local_e': FACTORY_NEAR[1][0], 'local_n': FACTORY_NEAR[1][1], 'heading_deg': 275},
                       'activity': 'stand', 'with': [FAM['man'], FAM['daughter']], 'grade': 'reconstructed', 'basis': '@trade'},
                      away(11.5, 12.5, 'paddling home up the river', '@trade'),
                      out(12.5, 16.0, W, 'putting away the cloth and kettles traded for', 'yard', 'sit', de=0.4, basis='@trade')] + WARM['woman'][6:],
    'daughter': lambda: [indoors(0, 5.5, 'asleep in the lodge'), out(5.5, 8.0, W, 'helping her mother pack the sugar', 'yard', 'work', de=1.0, basis='@trade'),
                         away(8.0, 9.0, 'in the canoe to the fort', '@trade'),
                         {'from': 9.0, 'to': 11.5, 'indoors': False, 'where': 'outdoors before first_fort_outer_factory',
                          'doing': 'with her parents at the factory', 'at': {'local_e': FACTORY_NEAR[2][0], 'local_n': FACTORY_NEAR[2][1], 'heading_deg': 275},
                          'activity': 'stand', 'with': [FAM['man'], FAM['woman']], 'grade': 'reconstructed', 'basis': '@trade'},
                         away(11.5, 12.5, 'in the canoe home', '@trade'),
                         out(12.5, 16.0, W, 'weaving with her grandmother', 'yard', 'work', de=1.8, dn=0.6)] + WARM['daughter'][6:],
}
AUG15 = {
    'man': [indoors(0, 5.0, 'asleep in the lodge'), away(5.0, 21.0, 'away with the warriors', '@aug15'), indoors(21.0, 24, 'asleep in the lodge')],
    'son': [indoors(0, 5.0, 'asleep in the lodge'), away(5.0, 21.0, 'away with the warriors', '@aug15'), indoors(21.0, 24, 'asleep in the lodge')],
}

PEOPLE = [   # key, relationship, sex, age, dress role, height (in), build, hair, name, stands for
    ('man', 'head', 'm', 38, 'potawatomi_man_1812', 68, 'lean', 'black, straight', 'The man of the lodges by the river'),
    ('woman', 'wife', 'f', 33, 'potawatomi_woman_1812', 62, 'medium', 'black, straight', 'His wife'),
    ('grandmother', 'mother-in-law', 'f', 57, 'potawatomi_elder_woman_1812', 61, 'slight', 'grey streaked black, straight', "The wife's mother"),
    ('son', 'son', 'm', 16, 'potawatomi_child_1812', 66, 'lean', 'black, straight', 'Their son'),
    ('daughter', 'daughter', 'f', 12, 'potawatomi_child_1812', 58, 'slight', 'black, straight', 'Their elder daughter'),
    ('boy', 'son', 'm', 8, 'potawatomi_child_1812', 49, "a child's", 'black, straight', 'Their younger son'),
    ('girl', 'daughter', 'f', 5, 'potawatomi_child_1812', 42, "a child's", 'black, straight', 'Their younger daughter'),
]

FACTS = [
    {'claim': 'Before 1812 the Potawatomi came and went at Chicago as a habit.', 'source': 'currey_1912_old_fort_dearborn',
     'locator': 'ch. II, Gutenberg #52346 lines 1360-1361',
     'quote': 'The Indians continued to come and go on their nomadic excursions according to their habit',
     'tier': 'compiled secondary (Currey 1912)'},
    {'claim': 'Their usual camping place was the State Street creek on the south bank.', 'source': 'currey_1912_old_fort_dearborn',
     'locator': 'ch. II, Gutenberg #52346 lines 1361-1363',
     'quote': 'while in this vicinity they lived in their wigwams near the river, their favorite camping place being at a point on the south bank',
     'tier': 'compiled secondary (Currey 1912)'},
    {'claim': 'The traders wanted their furs.', 'source': 'currey_1912_old_fort_dearborn',
     'locator': 'ch. II, Gutenberg #52346 lines 1366-1368',
     'quote': 'who were anxious to sell them supplies in exchange for the furs brought in by them',
     'tier': 'compiled secondary (Currey 1912)'},
    {'claim': 'Furs and maple sugar brought in for trade.', 'source': 'currey_1912_old_fort_dearborn',
     'locator': 'ch. II, Gutenberg #52346 lines 1372-1373',
     'quote': 'the Indians also brought in quantities of maple sugar put up in birch-bark packages',
     'tier': 'compiled secondary (Currey 1912)'},
    {'claim': "Most families left for winter hunting grounds and came back in spring (Juliette Kinzie's own observation, March 1831); this family is put as staying, which is ours.",
     'source': 'kinzie_waubun_1856', 'locator': 'ch. XV, Gutenberg #12183 lines 4138-4140',
     'quote': 'carried with them to their wintering-grounds, to be brought back in the spring, when they returned to make their corn-fields',
     'tier': "Juliette Kinzie's own observation (1831), Wau-Bun 1856"},
]

BASES = {
    'lodge': ("Indoors in the lodges by the river (T-3528's record, which gives no lodge to a family). Which lodge "
              "each sleeps in, and the hours, are this reading's."),
    'lodge_work': ("Ordinary work of a family camp at the yard the record draws (hearths, rack, mortar, woodpile, "
                   "scaffold, hide frame, canoes). The tasks and hours are this reading's; no source gives them."),
    'meal': "Cooking and eating at the hearth out of doors in the warm months; the hours are this reading's.",
    'river_round': "Fishing the river from the bank below the lodges; ordinary work in the warm months, not recorded for any day.",
    'child': "A child near the lodges, playing or helping; the hours are this reading's.",
    'winter': ("The cold months, November to March: more of the day indoors by the fire, the men out hunting through the "
               "middle of it. That this family winters here at all is the owner's choice (2026-11-09) and reconstructed; "
               "Wau-Bun has most families go to their wintering grounds (fact wintering)."),
    'away': "Off the scene for the span.",
    'trade': ("A trading morning at the government factory outside the fort, which Matthew Irwin kept until he left on "
              "5 July 1812: furs and maple sugar for cloth, kettles and powder (facts traders, sugar). The canoe trip is "
              "off the scene; the day and hours are this reading's."),
    'aug15': ("15 August 1812. Heald counts 'between four and five hundred' warriors in the attack, of the 500 Helm counted; "
              "which men fought no source records, and that these two were among them is reconstructed (as native_cards_1812.py "
              "grades every man of 16 to 55 of the gathering). Nothing of the fighting is drawn."),
}


def person(key, rel, sex, age, role, h, build, hair, name):
    pid = FAM[key]
    days = [{'from_date': '1812-11-01', 'to_date': '1812-12-31', 'label': 'the cold months', 'day': COLD[key]},
            {'from_date': '1812-01-01', 'to_date': '1812-03-31', 'label': 'the cold months', 'day': COLD[key]}]
    if key in AUG15:
        days.insert(0, {'from_date': '1812-08-15', 'to_date': '1812-08-15', 'label': '15 August', 'day': AUG15[key]})
    if key in TRADE:
        days.append({'from_date': '1812-04-01', 'to_date': '1812-07-04', 'frequency': 'about one day in six',
                     'label': 'a trading morning at the factory', 'day': TRADE[key]()})
    is_child = age < 15
    return {
        'person_id': pid,
        'name': f'{name} (name not recorded)',
        'present': {'status': 'present', 'grade': 'reconstructed',
                    'basis': ("Put at the lodges by the river through all of 1812, the owner's choice (2026-11-09); no source "
                              "names or counts this family.")},
        'presence': {'from': '1812-01-01', 'to': '1812-12-31', 'grade': 'reconstructed',
                     'basis': ("All year at the lodges by the river: the warm months at the yard, the cold months more "
                               "indoors, a trading morning at the factory now and then until it closed (see days).")},
        'sex': sex,
        'age_1812': {'value': age, 'grade': 'reconstructed', 'basis': 'Chosen for a family of three generations; not recorded.'},
        'dress_role': role,
        'looks': {'complexion': 'brown, a warm medium-to-deep tone weathered by sun', 'hair': hair, 'eyes': 'dark brown',
                  'height_in': h, 'build': build, 'grade': 'reconstructed',
                  'basis': ("Heritage, not a description: no source read describes this person's face, colouring or stature. "
                            "Drawn from the variation kit with the same care and range as everyone else in the town, with no "
                            "exaggerated features." + (' Age shown in grey hair.' if age >= 50 else ''))},
        'card': {
            'household': HH, 'name': f'{name} (name not recorded)', 'relationship': rel,
            'grade': 'reconstructed', 'sex': sex, 'age': age,
            'home': {'place_or_structure_id': HOME, 'tier': 'reconstructed'},
            'review_required': True, 'touches_removal': True, 'touches_native_history': True,
            'note': ("A family put at the lodges by the river through 1812, standing for the families Currey says came and "
                     "went to trade and camped by the creek's mouth. No source names or counts them; their names, ages, "
                     "history and days are reconstructed."),
        },
        'facts': FACTS,
        'day': WARM[key],
        'days': days,
    }


def build():
    return {
        'meta': {'ticket': 'T-3530', 'group': 'A Potawatomi family living at the lodges by the river, all 1812',
                 'written': '2026-11-09', 'liberty': LIB,
                 'read': ["Currey 1912 (Gutenberg #52346) ch. II lines 1360-1373", "Wau-Bun (Gutenberg #12183) ch. XV lines 4138-4140",
                          "docs/RESEARCH/people-1812-3467/day.json (the gathering's readings: shape, points of the factory)",
                          "data/structures/potawatomi_trading_lodges_1812.json and its lodge_camp layout"]},
        'bases': BASES,
        'people': [person(*row) for row in PEOPLE],
        'dress': {}, 'not_placed': [], 'new_sources': [],
    }


def main(check=False):
    text = json.dumps(build(), indent=1, ensure_ascii=False) + '\n'
    if check:
        if not OUT.exists() or OUT.read_text() != text:
            raise SystemExit(f'stale: {OUT}')
        print(f'current: {OUT}')
        return
    OUT.write_text(text)
    print(f'wrote {OUT}')


if __name__ == '__main__':
    main('--check' in sys.argv)
