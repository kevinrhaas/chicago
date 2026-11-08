# SPDX-License-Identifier: GPL-3.0-or-later
"""T-3507, T-3508, T-3509: the 1812 Potawatomi and Miami cards made equal to the settlers'.

The owner, 2026-11-08, walking the camps:

  * "you have permission to reconstruct names for each of the natives. Do it in a researched and
    respectful naming and note that in the record. I want the native cards to be equivalent to
    the settler and population cards and note where there were reconstructions and derive a
    history for that individual as a reconstructed history" (T-3507);
  * "If you think or believe that someone you have names of natives you can respectfully include
    them and assign them to a likeness ... if you know of families and natives who were in and
    around the area and would have been at the camps possibly you should include them" (T-3508);
  * "Some of those folks will participate in the battle so please assign the likely battle
    participants" (T-3509).

This module holds the research and composes, for every Native card of the 1812 scene, what it
adds; the three generators that write those cards (docs/RESEARCH/gathering-people-1812-3500/
build.py, docs/RESEARCH/people-1812-town/cards.py, docs/RESEARCH/people-1812-3461/build.py) call
`apply_households` on their records before they write them, so each still reproduces its own
files and its --check still holds. Run as a script it writes the three cards of named men who
came to Chicago only after the 14th or whose presence is uncertain (Shabbona, Billy Caldwell,
Alexander Robinson):  python3 tools/native_cards_1812.py [--check]

WHAT IS ADDED, AND HOW IT IS GRADED

  NAMES (T-3507). No source names any one of the gathering but its chiefs. A card whose person
  no source names gets a name of our making, in English, as the treaty clerks of 1815 and 1816
  wrote many of the same bands' names ("Black Partridge", "White Hair", "Little Wolf",
  "Walker", "Lake", "Stout", "Trader": Kappler II), and made by the practice Morgan records
  (Ancient Society, 1877, pt. II ch. II and VI): each gens owned its names, a name "proclaimed
  by its signification the gens to which it belonged" (his Omaha examples: "Long Wing", "Bird
  singing at daylight", "One of the Birds", "Bird's Egg"), children had names of childhood,
  descent ran in the male line and no one married within the gens. So each family is given a
  gens from Morgan's own list for the Potawatomi (fifteen) or the Miami (nine named), the
  man's and the children's names speak of it, the wife is of another gens, and her name of
  hers. Potawatomi words are not composed: the only Potawatomi on a card is the gens's name as
  Morgan prints it. A reconstructed name is never a name a source gives anyone of these bands.
  Every such name is marked on the card (`name_basis`, grade reconstructed).

  NAMED MEN OF THE BANDS (T-3508). The chiefs and warriors who signed for the Potawatomi of the
  Illinois River at Portage des Sioux on 18 July 1815 (the treaty that forgave "every injury or
  act of hostility" of the war) and for the Ottawa, Chippewa and Potawatomi of the Illinois and
  Milwaukee rivers at St. Louis on 24 August 1816 (the cession that includes Chicago) are the
  men of the very bands Heald says came in "from all quarters". Those not carded already take
  the cards of men of the gathering whom no source names: their names are attested (the
  treaty's own spelling), their being at Chicago in August 1812 is not, and the card says so.
  Shabbona (Chamblee in 1816), Billy Caldwell and Alexander Robinson have cards of their own,
  with Shabbona's and Robinson's portraits from Kirkland (1893) as their likenesses.

  HISTORIES (T-3507). Each unnamed card gets a short history built from what the sources say of
  the bands (Governor Edwards's description of May 1812, printed by Andreas), the year's round,
  the gathering and the goods of 13 August (Wau-Bun), and what became of the bands (the 1833
  treaty and the removal). Every particular of a person's history is ours, and the card says so
  above it.

  15 AUGUST (T-3509). Heald counts "between four and five hundred" warriors in the attack,
  "mostly of the Potawatamie nation", of the 500 Helm counted at the council: most of the
  gathering's men. Which men fought no source records; a man of 16 to 55 is put "likely among
  the warriors who attacked the column", graded reconstructed; older men, women and children
  were at the camp, where Heald's prisoners were brought; the Miamis "did not assist us" (Heald).
  A named man's part is what his sources say, with their tier. Nothing of the fighting is drawn.

Liberty L-1812-native-cards-3507.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/residents_1812/households'
LIBERTY = 'L-1812-native-cards-3507'
TICKETS = ['T-3507', 'T-3508', 'T-3509']

MORGAN = 'morgan_1877_ancient_society'
K1815 = 'kappler_1904_treaty_potawatomi_1815'
K1816 = 'kappler_1904_treaty_ottawa_etc_1816'
KIRKLAND = 'kirkland_1893_chicago_massacre'


def _r(*parts) -> float:
    h = hashlib.sha256('|'.join(str(p) for p in ('T-3507',) + parts).encode()).digest()
    return int.from_bytes(h[:8], 'big') / 2 ** 64


def _pick(seq, *parts):
    return seq[int(_r(*parts) * len(seq)) % len(seq)]


# ── the bands of the Chicago country, May 1812 (Edwards's description, Andreas pp. 78-79) ──────
BANDS = {
    'black_partridge': {
        'name': "Black Partridge's village", 'where': 'on the south side of the Illinois River, opposite the head of Peoria Lake',
        'nation': 'Potawatomi', 'size': None,
        'cite': ('andreas_1884_v1', 'p. 79', 'The village of Black Partridge Muck-otey-pokee was on the south side of the Illinois River, opposite the head of Peoria Lake.')},
    'gomo': {
        'name': "Gomo's band", 'where': 'at the north end of Peoria Lake', 'nation': 'Potawatomi', 'size': 'about one hundred and fifty men',
        'cite': ('andreas_1884_v1', 'pp. 78-79 (Edwards, May 1812)', 'of about one hundred and fifty men, at the north end of Peoria Lake')},
    'pepper': {
        'name': "Pepper's band", 'where': 'on the River au Sable, below the Kankakee', 'nation': 'Potawatomi, Chippewa and Ottawa',
        'size': 'about two hundred men, of different nations',
        'cite': ('andreas_1884_v1', 'pp. 78-79 (Edwards, May 1812)', "Pepper's band at Sand River (River au Sable) ... consisting of about two hundred men, and of different nations")},
    'main_poc': {
        'name': "Main Poc's band", 'where': 'seven leagues up the Kankakee', 'nation': 'Potawatomi', 'size': 'about fifty men',
        'cite': ('andreas_1884_v1', 'pp. 78-79 (Edwards, May 1812)', "Main Poc's band lies seven leagues up the Quin-qui-quee, consisting of about fifty men")},
    'waubansee': {
        'name': "Waubansee's band", 'where': 'on the Fox River of the Illinois', 'nation': 'Potawatomi, Chippewa and Ottawa, mixed together',
        'size': 'about thirty men',
        'cite': ('andreas_1884_v1', 'p. 79 (Edwards, May 1812)', 'In the Fox River ... is another band of Pottawatomies, Chippewas and Ottawas, mixed together')},
    'portage': {
        'name': "the village at the portage", 'where': 'at the camping place of Chicago, three leagues from the fort', 'nation': 'Potawatomi, Chippewa and Ottawa',
        'size': 'about thirty men, Co-wa-bee-mai their chief',
        'cite': ('andreas_1884_v1', 'p. 79 (Edwards, May 1812)', 'At the camping place of Chicago, three leagues from the Lake Michigan, or Chicago Fort, is a village of Pottawatomies, Chippewas and Ottawas, of about thirty men.')},
    'calumet': {
        'name': 'the village on the Little Calumet', 'where': 'on the Little Calumet, about five leagues from Chicago', 'nation': 'Potawatomi',
        'size': 'about a hundred men',
        'cite': ('andreas_1884_v1', 'p. 79 (Edwards, May 1812)', "a river called the 'Little Calumick,' about five leagues from Chicago. Here is a village")},
    'st_joseph': {
        'name': 'the villages of the St. Joseph', 'where': 'on the St. Joseph River, east round the lake', 'nation': 'Potawatomi',
        'size': 'three or four villages',
        'cite': ('andreas_1884_v1', 'p. 79', 'Topenebe and Winnemeg were on the St. Joseph River')},
    'milwaukee': {
        'name': 'the villages at Milwaukee', 'where': 'on the Milwaukee River, thirty leagues up the lake', 'nation': 'Potawatomi',
        'size': 'several villages',
        'cite': ('andreas_1884_v1', 'p. 79 (Edwards, May 1812)', 'There are, generally, several villages of Pottawatomies here')},
    'fort_wayne': {
        'name': 'the Miami towns about Fort Wayne', 'where': 'on the upper Wabash and the Maumee, by Fort Wayne', 'nation': 'Miami',
        'size': None, 'cite': ('quaife_1913', 'App. IV (Heald, 1812)', 'Captain Wells, of Fort Wayne')},
}
# Which band each ground's families are put with (reconstructed, L-1812-native-cards-3507):
# the named men already carded at a ground (Black Partridge at the middle reach, the Blackbird
# at the south reach, Waubansee at the west bank, Topenebe at the mouth) set its band.
GROUND_BAND = {
    'middle': 'black_partridge', 'south_reach': 'pepper', 'west_bank': 'waubansee', 'mouth': 'st_joseph',
    'upper': 'calumet', 'south_bend': 'gomo', 'south_prairie': 'gomo', 'south_west': 'main_poc',
    'north_flat': 'portage', 'head_west': 'pepper', 'prairie_west': 'milwaukee', 'far_west': 'gomo',
    'horse_ground': 'waubansee', 'miami': 'fort_wayne',
}

# ── the gentes, as Morgan prints them (Ancient Society, pt. II ch. VI and notes 170, 172) ───────
GENTES = {
    'Potawatomi': [('Wolf', 'Mo-ăh′'), ('Bear', 'M′-ko′'), ('Beaver', 'Muk'), ('Elk', 'Mis-shă′-wă'), ('Loon', 'Maak'),
                   ('Eagle', 'K′-nou′'), ('Sturgeon', 'N′-mă′'), ('Carp', 'N′-mă-pe-nă′'), ('Bald Eagle', 'M′-ge-ze′-wä'),
                   ('Thunder', 'Che′-kwa'), ('Rabbit', 'Wä-bo′-zo'), ('Crow', 'Kä-käg′-she'), ('Fox', 'Wake-shĭ′'),
                   ('Turkey', 'Pen′-nă'), ('Black Hawk', 'M′-ke-tash′-she-kă-kah′')],
    'Miami': [('Wolf', 'Mo-wha′-wä'), ('Loon', 'Mon-gwä′'), ('Eagle', 'Ken-da-wă′'), ('Buzzard', 'Ah-pă′-kose-e-ă'),
              ('Panther', 'Ka-no-zä′-wa'), ('Turkey', 'Pĭ-la-wä′'), ('Raccoon', 'Ah-se-pon′-nä'), ('Snow', 'Mon-nă′-to'),
              ('Sun', 'Kul-swä′')],
}
# What each gens's names speak of: [nouns that take a word before them], [phrases of a man],
# [phrases of a woman or girl], [a child's name].
SPEAK = {
    'Wolf': (['Wolf', 'Wolf Track', 'Wolf Trail'], ['Howls at Night', 'Leads on the Trail'], ['Wolf Singing at Dusk', 'One of the Wolves', "Wolf's Den", 'Wolf Track in Snow'], ['Wolf Pup']),
    'Bear': (['Bear', 'Bear Track', 'Bear Paw'], ['Walks Like a Bear', 'Bear Coming Out'], ['One of the Bears', "Bear's Lodge", 'Bear in the Berries', 'Bear at the Spring'], ['Bear Cub']),
    'Beaver': (['Beaver', 'Beaver Dam', 'Beaver Tail'], ['Builds the Dam', 'Swims at Dusk'], ['One of the Beavers', "Beaver's Lodge", 'Beaver in Still Water', 'Beaver at Daylight'], ['Beaver Kit']),
    'Elk': (['Elk', 'Elk Horn', 'Elk Track'], ['Elk Calling', 'Stands in the Meadow'], ['One of the Elk', 'Elk at the Ford', "Elk's Trail", 'Elk Feeding at Dawn'], ['Elk Calf']),
    'Loon': (['Loon', 'Loon Feather', 'Loon Wing'], ['Loon Diving', 'Calls Across the Lake'], ['Loon Calling at Daylight', 'One of the Loons', "Loon's Egg", 'Loon on Still Water'], ['Loon Chick']),
    'Eagle': (['Eagle', 'Eagle Feather', 'Eagle Wing'], ['Circles Above', 'Long Wing'], ['One of the Eagles', "Eagle's Nest", 'Eagle at Sunrise', 'Eagle Feather Woman'], ['Young Eagle']),
    'Sturgeon': (['Sturgeon', 'Sturgeon Back'], ['Swims Deep', 'Comes Up the River'], ['One of the Sturgeon', 'Sturgeon in the Shallows', "Sturgeon's Run", 'Shining in the River'], ['Little Fish']),
    'Carp': (['Carp', 'Fish Scale'], ['Leaps in the Shallows', 'Swims Upstream'], ['One of the Fish', 'Fish in Clear Water', 'Shining Scales', 'Fish at the Weir'], ['Little Carp']),
    'Bald Eagle': (['Fishing Eagle', 'Eagle Shadow', 'White Head'], ['Sits Above the River', 'Fishes from the Sky'], ["One of the White Heads", "White Head's Nest", 'Bald Eagle at Daylight', 'Feather on the Water'], ['Eaglet']),
    'Thunder': (['Thunder', 'Thunder Cloud', 'Lightning'], ['Thunder Coming', 'Thunder Far Off'], ['Thunder Woman', 'Rain After Thunder', 'Bright Cloud', 'One of the Thunders'], ['Little Thunder']),
    'Rabbit': (['Rabbit', 'Rabbit Track'], ['Long Ears', 'Leaps Aside'], ['One of the Rabbits', "Rabbit's Path", 'Rabbit in the Grass', 'Rabbit at Dusk'], ['Rabbit Kit']),
    'Crow': (['Crow', 'Crow Wing', 'Crow Feather'], ['Crow Calling', 'Flies Ahead'], ['One of the Crows', 'Crow at Daylight', "Crow's Nest", 'Crow on the Cornfield'], ['Young Crow']),
    'Fox': (['Fox', 'Fox Track', 'Fox Tail'], ['Fox Running', 'Watches the Trail'], ['One of the Foxes', "Fox's Den", 'Fox at Dusk', 'Fox in the Snow'], ['Fox Kit']),
    'Turkey': (['Turkey', 'Turkey Feather', 'Turkey Foot'], ['Turkey Calling', 'Walks in the Woods'], ['Turkey Calling at Daylight', 'One of the Turkeys', "Turkey's Egg", 'Turkey in the Oaks'], ['Turkey Poult']),
    'Black Hawk': (['Hawk', 'Hawk Wing', 'Hawk Feather'], ['Hawk Circling', 'Sharp Eye'], ['One of the Hawks', "Hawk's Nest", 'Hawk Hovering at Noon', 'Hawk at Daylight'], ['Young Hawk']),
    'Buzzard': (['Buzzard', 'Buzzard Wing'], ['Circles High', 'Rides the Wind'], ['One of the Buzzards', 'Buzzard at Noon', 'Wing on the Wind', 'Circling High'], ['Young Buzzard']),
    'Panther': (['Panther', 'Panther Track'], ['Walks Softly', 'Waits in the Grass'], ['One of the Panthers', "Panther's Den", 'Panther at Dusk', 'Soft Step'], ['Panther Cub']),
    'Raccoon': (['Raccoon', 'Raccoon Track'], ['Washes at the Stream', 'Climbs at Night'], ['One of the Raccoons', 'Raccoon at the Stream', "Raccoon's Den", 'Raccoon in the Moonlight'], ['Raccoon Kit']),
    'Snow': (['Snow', 'Snowfall', 'Drift'], ['Snow Coming', 'Walks on Snow'], ['First Snow', 'Snow at Daylight', 'One of the Snows', 'Snow on the Pines'], ['Little Snow']),
    'Sun': (['Sun', 'Sunrise', 'Noon Sun'], ['Sun Rising', 'Sun Going Down'], ['Sun at Daylight', 'One of the Suns', 'Bright Morning', 'Sun on the Water'], ['Little Sun']),
}
WORDS = ['Gray', 'Black', 'White', 'Red', 'Yellow', 'Little', 'Great', 'Morning', 'Evening', 'Winter', 'Prairie',
         'Far', 'Standing', 'Swift', 'Lone', 'Tall']
# Names the period's own records give men of these bands (and the most famous), never given to
# a person no source names.
RECORDED = {'Black Partridge', 'White Hair', 'Little Wolf', 'Walker', 'Lake', 'Stout', 'Trader', 'Black Bird',
            'Mad Sturgeon', 'Catfish', 'Black Hawk', 'Little Turtle', 'Little Deer', 'Sulky', 'Straight Tree',
            'Little Chief', 'Gray Wolf'}

# ── the named men of the bands (Kappler II: the 1815 and 1816 treaties' own lists) ──────────────
# (name, treaty source, gloss the treaty prints, ground to put him at)
TREATY_MEN = [
    ('Sunawchewome', K1815, None, 'middle'), ('Neggeneshkek', K1815, None, 'middle'), ('Chawcawbeme', K1815, None, 'north_flat'),
    ('Bendegakewa', K1815, None, 'south_bend'), ('Wapewy', K1815, 'White Hair', 'south_bend'), ('Outawa', K1815, None, 'far_west'),
    ('Ignatius', K1816, None, 'middle'), ('Cunnepepy', K1816, None, 'south_reach'), ('Wonesee', K1816, None, 'south_reach'),
    ('Richeikeming', K1816, 'Lake', 'prairie_west'), ('Cabenaw', K1816, None, 'head_west'), ('Opaho', K1816, None, 'head_west'),
    ('Cowwesaut', K1816, None, 'upper'), ('Chekinaka', K1816, None, 'prairie_west'), ('Pemasaw', K1816, 'Walker', 'south_prairie'),
    ('Macheweskeaway', K1816, None, 'far_west'), ('Spanquissee', K1816, None, 'south_west'), ('Nangesay', K1816, 'Stout', 'head_west'),
    ('Takaonenee', K1816, None, 'prairie_west'), ('Cacake', K1816, None, 'south_bend'), ('Ottawonce', K1816, None, 'north_flat'),
    ('Shawanoe', K1816, None, 'south_west'), ('Tawwaning', K1816, 'Trader', 'mouth'), ('Cashshakee', K1816, None, 'upper'),
    ('Nigigwash', K1816, None, 'far_west'), ('Sheshebungge', K1816, None, 'prairie_west'), ('Mowais', K1816, 'Little Wolf', 'west_bank'),
]
TREATY_EVIDENCE = {
    K1815: {'source_id': K1815, 'locator': 'Kappler II, Treaty with the Potawatomi, 1815 (Portage des Sioux, 18 July 1815), the signers',
            'quote': 'the undersigned Chiefs and Warriors of the Poutawatamie Tribe or Nation, residing on the river Illinois',
            'claim': 'signed for the Potawatomi of the Illinois River at the peace of 1815'},
    K1816: {'source_id': K1816, 'locator': 'Kappler II, Treaty with the Ottawa, etc., 1816 (St. Louis, 24 August 1816), the signers',
            'quote': 'the chiefs and warriors of the united tribes of Ottawas, Chipawas, and Pottowotomees, residing on the Illinois and Melwakee rivers',
            'claim': 'signed for the Ottawa, Chippewa and Potawatomi of the Illinois and Milwaukee rivers in 1816'},
}
EXTRA_NOTES = {
    'Chawcawbeme': ' He may be the Co-wa-bee-mai whom Edwards names in May 1812 as chief of the village at the portage; the spelling is near, but no source joins the two.',
    'Ignatius': ' In 1816 he made the mark for his brother Sinnowchewone, as the treaty prints it; the Sunawchewome of 1815 is very likely the same man, so the two brothers are put in one lodge here.',
    'Sunawchewome': ' Written Sinnowchewone in 1816, when his brother Ignatius made his mark for him.',
    'Mowais': ' Wau-Bun says the point at the forks of the Chicago River was named for an Indian called Moa-way, "the Wolf"; whether he is that man is not known.',
}

# ── the 15th, as the sources give it ─────────────────────────────────────────────────────────
HELM_500 = {'source_id': 'quaife_1913', 'locator': 'App. VI, Helm (1814), lines 16634-16636',
            'quote': 'the tribes there assembled to amount of 500 warriors 179 women & children', 'claim': "Helm's count at the council"}
HEALD_400 = {'source_id': 'quaife_1913', 'locator': 'App. IV, Heald (23 Oct 1812), lines 16267-16269',
             'quote': 'Their number of warriors was between four and five hundred, mostly of the Potawatamie nation',
             'claim': 'the warriors in the attack'}
HEALD_CAMP = {'source_id': 'quaife_1913', 'locator': 'App. IV, Heald (23 Oct 1812), lines 16264-16266',
              'quote': 'we were taken back to their encampment near the fort, and distributed among the different tribes',
              'claim': 'the prisoners brought back to the camp'}
HEALD_MIAMI = {'source_id': 'quaife_1913', 'locator': 'App. IV, Heald (23 Oct 1812), line 16252',
               'quote': 'finding the Miamies did not assist us', 'claim': 'the Miami escort did not fight'}
GOODS = {'source_id': 'kinzie_waubun_1856', 'locator': 'ch. XVIII (Gutenberg #12183 lines 5427-5428)',
         'quote': 'On the 13th, the goods, consisting of blankets, broadcloths, calicoes, paints, etc., were distributed',
         'claim': 'the goods given out on the 13th'}


def _age(p):
    band = p.get('age_band') or {}
    return band.get('low') if isinstance(band.get('low'), int) else None


def _nation(hid, p):
    return 'Miami' if 'miami' in hid or 'miami' in p.get('id', '') else 'Potawatomi'


def _ground(hid, p):
    if 'horse_ground' in p.get('id', ''):
        return 'horse_ground'
    m = re.match(r'hh_(?:gathering|potawatomi_camp)_(.+)_1812$', hid)
    if m:
        return m.group(1)
    if 'miami' in hid:
        return 'miami'
    return None


def _role(p, age):
    if p.get('relationship') == 'child' or (age is not None and age < 15):
        return 'child'
    return 'woman' if p.get('sex') == 'female' else 'man'


# The two people of the named households whom no source names: their names, chosen by hand.
FIXED = {
    'main_poc_runner': ('Fox Running', 'Fox', "Main Poc's band", 'main_poc'),
    'waubeeneemah_wife': ('Rain After Thunder', 'Thunder', None, 'st_joseph'),
}
REVIEW_NAMED = ("review_required: a person of the Potawatomi gathering at Chicago in August 1812, the eve of the attack on the garrison "
                "and its families, whom no source names. The owner asked (2026-11-08) that each be given a researched, respectful name and "
                "a history, both marked reconstructed (liberty L-1812-native-cards-3507); the card says which of its facts are ours. "
                "touches_removal: these are the people removed from Chicago in 1835. Nothing of the fighting is staged in the scene.")
REVIEW_NAMED_MIAMI = ("review_required: a Miami man of the escort William Wells brought from Fort Wayne, whom no source names. The owner asked "
                      "(2026-11-08) that each be given a researched, respectful name and a history, both marked reconstructed (liberty "
                      "L-1812-native-cards-3507). Nothing of the fighting is staged in the scene.")


class _Names:
    """Every reconstructed name once in the scene."""

    def __init__(self, reserved=()):
        self.used = set(RECORDED) | {v[0] for v in FIXED.values()} | set(reserved)

    def make(self, gens, role, age, pid):
        nouns, man, woman, child = SPEAK[gens]
        if role == 'child':
            pool = list(child) + [f'Little {n}' for n in nouns] + [f'{w} {c}' for w in ('Small', 'Young', 'Morning', 'Winter', 'Spring') for c in child]
        elif role == 'woman':
            pool = list(woman) + [f'{w} {n} Woman' for w in WORDS if w not in ('Great',) for n in nouns[:2]]
        else:
            words = [w for w in WORDS if not (w == 'Little' and (age or 30) > 45)]
            if (age or 0) >= 50:
                words = ['Old'] + words
            pool = [f'{w} {n}' for w in words for n in nouns] + list(man)
        start = int(_r('name', pid) * len(pool))
        for k in range(len(pool)):
            name = pool[(start + k * 7) % len(pool)]
            if name not in self.used:
                self.used.add(name)
                return name
        for k in range(2, 99):   # pool spent: a name given again, as a gens gave a dead man's name again
            name = f'{pool[start]} the {("Second", "Third", "Fourth", "Fifth")[min(k - 2, 3)]}' if k < 6 else f'{pool[start]} ({k})'
            if name not in self.used:
                self.used.add(name)
                return name
        return pool[start]


def _gens_of(nation, key):
    return _pick(GENTES[nation], 'gens', key)


def _history(p, role, age, nation, band, gens, family, treaty=None):
    """A reconstructed history, a few sentences, every particular ours."""
    B = BANDS[band]
    he, his, him = ('she', 'her', 'her') if p.get('sex') == 'female' else ('he', 'his', 'him')
    He, His = he.capitalize(), his.capitalize()
    pid = p['id']
    out = []
    size = f" ({B['size']} in May 1812)" if B.get('size') else ''
    if nation == 'Miami':
        out.append(f"{He} came from {B['name']} {B['where']}, and rode to Chicago with William Wells's escort, which reached the fort on the 13th.")
    else:
        out.append(f"{His} family is put with {B['name']}, {B['where']}{size}, one of the bands of the Chicago country Governor Edwards described that spring.")
    g_name, g_word = gens
    if role == 'child':
        out.append(f"{He} is of the {g_name} gens ({g_word}, as Morgan writes it), {his} father's, and {his} name is a name of childhood, to be put aside for another as {he} grows up.")
    elif role == 'woman':
        out.append(f"{He} is of the {g_name} gens ({g_word}); {his} husband, since no one married within the gens, is of another, and {his} children are of his.")
    else:
        out.append(f"{He} is of the {g_name} gens ({g_word}), and {his} children are of it after {him}.")
    if family:
        lodge, kin = family
        out.append((f"In lodge no. {lodge} {he} lives with {kin}." if lodge else f"{He} is here with {kin}."))
    rounds = {
        'man': ["The winter before, he hunted with his family on the Kankakee and traded the skins at Kinzie's for powder, cloth and kettles.",
                "In the spring he helped at the sugar camp, and in summer fished the river and the lake while the corn grew at the village.",
                "He knows the portage and the Des Plaines from carrying canoes and packs across it in high water and low.",
                "He has a pony, and some winters went as far as the Wabash to hunt.",
                "He hunts deer in the oak openings, and in the fall goes after ducks and geese in the marshes of the Calumet."],
        'woman': ["She planted and hoed the village's corn, beans and squash in the spring, and made the rush and cattail mats the lodges here are covered with.",
                  "In March and April she boiled maple sap at the sugar camp and packed the sugar in birch-bark mococks to trade.",
                  "She dresses deerskins and sews moccasins, and is known at the Kinzies' for her work.",
                  "She gathers wild rice and rushes in the marshes in late summer and dries berries for the winter."],
        'child': ["The village's children run between the lodges and the river; the older ones carry wood and water for the kettle.",
                  "This summer is the first time this child has seen the fort, the soldiers and so many lodges in one place."],
    }
    if role == 'man' and (age or 0) >= 56:
        out.append("He has seen the French and the English traders come and go, and the Americans build the fort in 1803.")
    else:
        out.append(_pick(rounds[role], 'round', pid))
    if nation == 'Miami':
        out.append("At Chicago he camps with the escort south-west of the fort, with his pony.")
    elif role != 'child':
        out.append(f"{He} came in when the bands gathered at Chicago in August, and on the 13th was given cloth and blankets when the goods were handed out.")
    if treaty:
        out.append(treaty)
    return out


def _on_15(p, role, age, nation):
    if nation == 'Miami':
        return {'value': 'Rode out with the column; did not fight', 'grade': 'inferred',
                'note': 'Heald: "finding the Miamies did not assist us". Of the escort as a body; what this man did is not recorded.',
                'sources': ['quaife_1913']}
    if role == 'man' and 16 <= (age or 30) <= 55:
        return {'value': 'Likely among the warriors who attacked the column', 'grade': 'reconstructed',
                'note': 'Heald: "between four and five hundred" attacked, of the 500 at the council. Who fought is not recorded; that he did is our reading.',
                'sources': ['quaife_1913']}
    if role == 'man':
        return {'value': 'Likely stayed at the camp', 'grade': 'reconstructed',
                'note': "An older man; no source says who stayed at the camp on the 15th. Heald's prisoners were brought back to the encampment near the fort.",
                'sources': ['quaife_1913']}
    return {'value': 'At the camp by the fort', 'grade': 'inferred',
            'note': "Heald's prisoners were brought back to \"their encampment near the fort\". What this person saw or did is not recorded.",
            'sources': ['quaife_1913']}


# ── the named people already carded: their 15th, from their own sources ──────────────────────
NAMED_15 = {
    'black_partridge': ('Pulled Mrs Helm into the lake and brought her to the camp (Wau-Bun); kept watch at the Kinzie house on the 16th', 'inferred',
                        "Wau-Bun's account (Mrs Helm's story, family tradition). Helm (1814), a contemporary, says only that his wife was among the women.", ['kinzie_waubun_1856', 'quaife_1913']),
    'blackbird': ("Led the attack; received Heald's surrender", 'attested',
                  'Heald (1812): "met by one of the Potawatamie chiefs, called the Black Bird, with an interpreter".', ['quaife_1913']),
    'nuscotnemeg': ('Among the attackers; badly wounded, and carried off toward the Des Plaines by the 16th', 'inferred', 'Wau-Bun (family tradition).', ['kinzie_waubun_1856']),
    'naunongee': ('Among the attackers; killed Sergeant Hays and was mortally wounded by his bayonet', 'inferred',
                  'Wau-Bun (family tradition); Schoolcraft (1820, via Quaife) tells the same with the man unnamed.', ['kinzie_waubun_1856', 'quaife_1913']),
    'peesotum': ("Among the attackers; Mrs Helm saw him carry Wells's scalp", 'inferred', "Wau-Bun (Mrs Helm's story); Kirkland doubts the circumstances.", ['kinzie_waubun_1856']),
    'topenebe': ('Held the Kinzie boat at the river mouth and kept the family safe; hid Sergeant Griffith', 'inferred', 'Wau-Bun and Quaife.', ['kinzie_waubun_1856', 'quaife_1913']),
    'keepotah': ('Guarded the Kinzie boat; a sentinel at the Kinzie house on the 16th', 'inferred', 'Wau-Bun (family tradition).', ['kinzie_waubun_1856']),
    'waubansee': ('With Winnemeg, said to have tried to save the wounded Wells; a sentinel at the Kinzie house on the 16th', 'inferred',
                  'Wau-Bun (hearsay); Kirkland doubts the Wells story.', ['kinzie_waubun_1856']),
    'winnemeg': ('With Waubansee, said to have tried to save the wounded Wells', 'inferred', 'Wau-Bun (hearsay); Kirkland doubts it.', ['kinzie_waubun_1856']),
    'waubeeneemah': ('At the camp: screened Mrs Helm with a mat from the killing of a wounded prisoner', 'inferred', "Wau-Bun (Mrs Helm's story).", ['kinzie_waubun_1856']),
    'waubeeneemah_wife': ('At the camp: gave Mrs Helm water with maple sugar stirred in', 'inferred', "Wau-Bun (Mrs Helm's story).", ['kinzie_waubun_1856']),
    'main_poc_runner': ('Not recorded', 'inferred', 'The Missouri Gazette brings him on the 14th with a red belt; nothing more.', ['quaife_1913']),
}


def reconstructed_names(households: dict):
    """The reconstructed names already on these households' cards (for a later generator to avoid)."""
    return {p['name'] for h in households.values() for p in h['persons']
            if (p.get('name_basis') or {}).get('grade') == 'reconstructed'}


def on_disk(hids):
    out = {}
    for hid in hids:
        f = OUT / f'{hid}.json'
        if f.exists():
            out[hid] = json.loads(f.read_text())
    return out


def is_native(hid):
    return hid.startswith(('hh_gathering_', 'hh_potawatomi_camp_', 'hh_miami_escort'))


def apply_households(households: dict, drawn=None, lodges=None, families=None, reserved=()):
    """Add names, histories and the 15th to every Native card in `households` (id -> record), in place.

    drawn: person ids drawn as figures (a treaty man takes a drawn card), None for all;
    lodges: person id -> lodge door id; families: person id -> family key (one man, a woman,
    their children); reserved: reconstructed names another generator has already given.
    """
    names = _Names(reserved)
    lodges, families = lodges or {}, families or {}
    # Which treaty man takes which card: a man of 22-55 at his ground, drawn if we know who is.
    by_ground = {}
    for hid, hh in sorted(households.items()):
        if not hid.startswith('hh_gathering_'):
            continue
        for p in hh['persons']:
            age = _age(p)
            if _role(p, age) == 'man' and 22 <= (age or 0) <= 55 and (drawn is None or p['id'] in drawn):
                by_ground.setdefault(_ground(hid, p), []).append(p['id'])
    taken = {}
    for name, src, gloss, g in TREATY_MEN:
        pool = [x for x in by_ground.get(g, []) if x not in taken.values()]
        if name == 'Ignatius' and 'Sunawchewome' in taken:   # brothers: one lodge
            near = [x for x in pool if lodges.get(x) and lodges.get(x) == lodges.get(taken['Sunawchewome'])]
            pool = near or pool
        if pool:
            taken[name] = pool[int(_r('treaty', name) * len(pool)) % len(pool)]
    treaty_of = {pid: next((n, s, gl) for n, s, gl, _ in TREATY_MEN if n == name) for name, pid in taken.items()}

    everyone = {p['id']: p for hh in households.values() for p in hh['persons']}
    fam_members = {}
    for pid, key in families.items():
        fam_members.setdefault(key, []).append(pid)
    plan = {}
    for hid, hh in sorted(households.items()):
        if is_native(hid):
            hh['review_note'] = REVIEW_NAMED_MIAMI if 'miami' in hid else REVIEW_NAMED
            # Evidence every card of the household carried alike is said once, on the household.
            common = [e for e in (hh['persons'][0].get('evidence') or []) if all(e in (q.get('evidence') or []) for q in hh['persons'])]
            for q in hh['persons']:
                q['evidence'] = [e for e in (q.get('evidence') or []) if e not in common]
                if not q['evidence']:
                    del q['evidence']
            hh['card_evidence'] = common + [e for e in _household_evidence(hid, hh) if e not in common]
            for p in hh['persons']:
                plan[p['id']] = _apply_unnamed(hid, p, names, treaty_of.get(p['id']), lodges, families)
        else:
            for p in hh['persons']:
                if p['id'] in FIXED:
                    _apply_fixed(p)
                if p['id'] in NAMED_15:
                    v, grade, note, srcs = NAMED_15[p['id']]
                    p['on_15_august'] = {'value': v, 'grade': grade, 'note': note, 'sources': srcs}
                    p['card_facts'] = [f for f in p.get('card_facts', []) if f.get('label') != 'On 15 August'] + [
                        {'label': 'On 15 August', 'value': v, 'grade': grade}]
    # Histories last, so a family is named by its new names.
    for pid, (nation, band, gens, role, age, treaty_line) in plan.items():
        p = everyone[pid]
        fam = None
        key = families.get(pid)
        kin = [everyone[q] for q in fam_members.get(key, []) if q != pid and q in everyone] if key else []
        if kin:
            fam = (_lodge_number(lodges.get(pid)), _kin_words(p, kin))
        p['history'] = {
            'title': 'A reconstructed history', 'grade': 'reconstructed', 'liberty': LIBERTY,
            'caveat': 'No source tells this life: every particular of it is ours.',
            'paragraphs': _history(p, role, age, nation, band, gens, fam, treaty_line),
        }
    return households


def _household_evidence(hid, hh):
    """What every card of the household rests on, once: how the names are made, the band, the 15th."""
    miami = 'miami' in hid
    bands = sorted({GROUND_BAND.get(_ground(hid, p) or 'mouth', 'gomo') for p in hh['persons']})
    ev = [{'source_id': MORGAN, 'locator': 'pt. II, ch. II (VI, the right of bestowing names) and ch. VI (the gentes, notes 170 and 172)',
           'quote': 'These names either proclaimed by their signification the gens to which they belonged, or were known as such by common reputation.',
           'claim': 'how a reconstructed name is made'}]
    ev += [{'source_id': BANDS[b]['cite'][0], 'locator': BANDS[b]['cite'][1], 'quote': BANDS[b]['cite'][2],
            'claim': f"{BANDS[b]['name']}, the band these cards are put with (reconstructed)"} for b in bands]
    ev += [HEALD_MIAMI] if miami else [HELM_500, HEALD_400, HEALD_CAMP]
    return ev


def _kin_words(p, kin):
    me = _role(p, _age(p))
    rel = {('man', 'woman'): 'wife', ('man', 'man'): 'brother', ('woman', 'man'): 'husband', ('woman', 'woman'): 'sister',
           ('child', 'man'): 'father', ('child', 'woman'): 'mother'}

    def one(q):
        a = _age(q)
        r = _role(q, a)
        if r == 'child':
            word = ('sister' if q.get('sex') == 'female' else 'brother') if me == 'child' else ('daughter' if q.get('sex') == 'female' else 'son')
        else:
            word = rel[(me, r)]
        return f"{'his' if p.get('sex') == 'male' else 'her'} {word} {q['name']}" + (f' ({a})' if a is not None and r == 'child' else '')
    words = [one(q) for q in kin[:6]]
    return ', '.join(words[:-1]) + ' and ' + words[-1] if len(words) > 1 else words[0]


def _lodge_number(door):
    m = re.search(r'lodge(\d+)', door or '')
    return m.group(1) if m else None


def _apply_fixed(p):
    name, gens_name, _band, _b = FIXED[p['id']]
    old = p['name']
    gens = next(g for g in GENTES['Potawatomi'] if g[0] == gens_name)
    p['name'] = name
    p['also_written'] = sorted(set(p.get('also_written') or []) | {old})
    p['name_basis'] = {'value': 'reconstructed', 'grade': 'reconstructed', 'sources': [MORGAN],
                       'note': (f"No source names {'her' if p.get('sex') == 'female' or 'wife' in p['id'] else 'him'}. A name of our making, given in English "
                                f"as the treaty clerks of 1815-16 wrote many names of these bands, and made as Morgan says names were: a gens owned its "
                                f"names, and a name spoke of it. This one speaks of the {gens_name} ({gens[1]}).")}
    p['card_facts'] = [f for f in p.get('card_facts', []) if f.get('label') != 'Name'] + [
        {'label': 'Name', 'value': 'Reconstructed (no source names them)', 'grade': 'reconstructed'},
        {'label': 'Gens', 'value': f'{gens_name} ({gens[1]})', 'grade': 'reconstructed'}]
    p['sources'] = sorted(set(p.get('sources') or []) | {MORGAN})
    rec = dict(p.get('reconstruction') or {})
    rec.update({'name': 'reconstructed', 'name_ticket': 'T-3507', 'cards_liberty': LIBERTY})
    p['reconstruction'] = rec


def _apply_unnamed(hid, p, names, treaty, lodges, families):
    nation = _nation(hid, p)
    age = _age(p)
    role = _role(p, age)
    g = _ground(hid, p) or 'mouth'
    band = GROUND_BAND.get(g, 'gomo')
    # The family's gens is the man's; a woman's is another (no one married within the gens).
    gens = _gens_of(nation, families.get(p['id']) or lodges.get(p['id']) or p['id'])
    if role == 'woman':
        gens = _pick([x for x in GENTES[nation] if x != gens], 'wife', p['id'])
    old_name = p['name']
    facts = []
    sources = set(p.get('sources') or [])
    evidence = list(p.get('evidence') or [])
    treaty_line = None
    if treaty:
        tname, src, gloss = treaty
        year = '1815' if src == K1815 else '1816'
        p['name'] = tname + (f' ({gloss})' if gloss else '')
        p['name_basis'] = {'value': 'attested', 'grade': 'attested', 'sources': [src],
                           'note': (f"His name as the treaty of {year} prints it" + (f', with its gloss, {gloss}' if gloss else '') + '. '
                                    'That he was at Chicago in August 1812 no source says: he signed for the bands that gathered there, '
                                    'and is put among the men of the gathering (reconstructed).' + EXTRA_NOTES.get(tname, ''))}
        facts.append({'label': 'Name', 'value': f'Attested: he signed the treaty of {year}', 'grade': 'attested'})
        facts.append({'label': 'At Chicago, August 1812', 'value': 'Not recorded; put here as a man of the bands', 'grade': 'reconstructed'})
        sources.add(src)
        evidence.append(TREATY_EVIDENCE[src])
        treaty_line = (f"{tname} made his mark on the treaty of "
                       + ('Portage des Sioux, 18 July 1815, the peace of the Illinois River Potawatomi with the United States'
                          if src == K1815 else 'St. Louis, 24 August 1816, by which the bands of the Illinois and Milwaukee rivers ceded the land about Chicago')
                       + ': the one record of him we have. Everything else here is reconstructed.')
    else:
        p['name'] = names.make(gens[0], role, age, p['id'])
        p['name_basis'] = {'value': 'reconstructed', 'grade': 'reconstructed', 'sources': [MORGAN],
                           'note': (f"No source names {'her' if p.get('sex') == 'female' else 'him'}: our name, in English as the 1815-16 treaty clerks "
                                    f"wrote these bands' names, speaking of the {gens[0]} gens as Morgan says a name did."
                                    + (' A name of childhood.' if role == 'child' else ''))}
        facts.append({'label': 'Name', 'value': 'Reconstructed (no source names them)', 'grade': 'reconstructed'})
        sources.add(MORGAN)
    p['also_written'] = sorted(set(p.get('also_written') or []) | {old_name})
    B = BANDS[band]
    facts.append({'label': 'People', 'value': nation, 'grade': 'inferred'})
    facts.append({'label': 'Band', 'value': B['name'][0].upper() + B['name'][1:], 'grade': 'reconstructed'})
    facts.append({'label': 'Gens', 'value': f'{gens[0]} ({gens[1]})', 'grade': 'reconstructed'})
    if age is not None:
        facts.append({'label': 'Age in 1812', 'value': f'About {age}' if age else 'Under a year', 'grade': 'reconstructed'})
    on15 = _on_15(p, role, age, nation)
    p['on_15_august'] = on15
    facts.append({'label': 'On 15 August', 'value': on15['value'], 'grade': on15['grade']})
    p['card_facts'] = facts
    sources |= {B['cite'][0]}
    p['sources'] = sorted(sources)
    p['evidence'] = evidence
    p['review_note'] = REVIEW_NAMED_MIAMI if nation == 'Miami' else REVIEW_NAMED
    rec = dict(p.get('reconstruction') or {})
    rec.update({'name': 'attested' if treaty else 'reconstructed', 'history': 'reconstructed',
                'name_ticket': 'T-3508' if treaty else 'T-3507', 'cards_liberty': LIBERTY})
    p['reconstruction'] = rec
    return (nation, band, gens, role, age, treaty_line)


# ── the named men who came after the 14th, or may have been here ─────────────────────────────
REVIEW = ("review_required: a named Native man of the Chicago country in August 1812, the eve of the attack on the garrison and "
          "its families. touches_removal: his people were removed from Illinois after 1833. The card states what its sources say, "
          "with their tier, and stages no speech, ceremony or act of war.")


def _person(pid, name, also, note, presence, sources, evidence, facts, on15, portrait=None, born=None):
    p = {'id': pid, 'name': name, 'relationship': 'head', 'grade': 'attested', 'sources': sources, 'sex': 'male',
         'present_on_scene_date': presence, 'also_written': also, 'note': note,
         'review_required': True, 'touches_removal': True, 'review_note': REVIEW,
         'reconstruction': {'stage': 'named_after_the_14th', 'ticket': 'T-3508', 'liberty': LIBERTY},
         'evidence': evidence, 'card_facts': facts, 'on_15_august': on15}
    if born:
        p['born'] = born
    if portrait:
        p['portrait'] = portrait
    return p


def named_households():
    shabbona = _person(
        'shabbona', 'Shabbona', ['Shau-be-na', 'Shabonee', 'Chamblee (1816 treaty)', 'Chamblie'],
        ("An Ottawa by birth who married into a Potawatomi band of the Illinois River and later led it; in 1812 an aide to Tecumseh. "
         "By his own account, as Matson took it down, he set out for Chicago when he heard the warriors had gone there, and came in a few "
         "hours after the fight on the 15th with twenty-two men; Andreas thinks he was not there before it. As Chamblee he signed the "
         "1816 treaty that ceded the land about Chicago. He kept to peace in 1832, was granted land at Shabbona Grove and lost it, and died "
         "near Morris, Illinois, in July 1859."),
        {'value': 'absent', 'confidence': 'inferred',
         'note': 'Not at Chicago on the 14th: by his own account he arrived on the afternoon of the 15th, after the fight.'},
        ['andreas_1884_v1', KIRKLAND, K1816],
        [{'source_id': 'andreas_1884_v1', 'locator': 'pp. 108-110', 'quote': 'do not appear to have been present', 'claim': 'not at the attack (Andreas, of him and Caldwell)'},
         {'source_id': K1816, 'locator': 'Kappler II, Treaty with the Ottawa, etc., 1816, the signers', 'quote': 'Chamblee, his x mark', 'claim': 'signed the 1816 cession'},
         {'source_id': KIRKLAND, 'locator': 'the plate "Shaubena in old age (about 1856)"', 'quote': 'SHAUBENA IN OLD AGE. (ABOUT 1856.)', 'claim': 'his portrait'}],
        [{'label': 'People', 'value': 'Ottawa by birth; led a Potawatomi band', 'grade': 'attested'},
         {'label': 'Born', 'value': 'About 1775', 'grade': 'inferred'},
         {'label': 'On 14 August', 'value': 'Not yet at Chicago', 'grade': 'inferred'},
         {'label': 'On 15 August', 'value': 'Came in after the fight, by his own account', 'grade': 'inferred'}],
        {'value': 'Came in after the fight, by his own account', 'grade': 'inferred',
         'note': 'His account via Matson (1876), late recollection: he arrived a few hours after the battle and stood among the warriors guarding the Kinzie house that night.',
         'sources': ['andreas_1884_v1']},
        portrait={'image': 'humans/web/portraits/shabbona_kirkland_1893.jpg', 'caption': 'Shaubena in old age (about 1856): Kirkland 1893',
                  'source_id': KIRKLAND, 'grade': 'attested',
                  'why': 'His own likeness, some forty-four years after 1812: the face he was known by late in life, not his dress of 1812.'})
    caldwell = _person(
        'caldwell_billy', 'Billy Caldwell (Sauganash)', ['Sauganash ("the Englishman")', "Straight Tree (his first Indian name, Andreas)"],
        ("Son of a Potawatomi mother and an Irish-born British officer, born about 1780; in 1812 with Tecumseh and the British. Andreas and "
         "Currey say he was not at the evacuation. Wau-Bun brings him across the river by canoe on the 16th, when he talked the Wabash party "
         "out of harming the Kinzies; Quaife allows the story a 'kernel of fact' at most. He later led the united bands at the 1833 treaty, "
         "went west with them in 1836, and died at Council Bluffs on 28 September 1841."),
        {'value': 'absent', 'confidence': 'inferred', 'note': 'Not at Chicago on the 14th (Andreas; Currey); Wau-Bun brings him on the 16th.'},
        ['andreas_1884_v1', 'kinzie_waubun_1856', 'quaife_1913'],
        [{'source_id': 'andreas_1884_v1', 'locator': 'pp. 108-110', 'quote': 'do not appear to have been present', 'claim': 'not at the attack'}],
        [{'label': 'People', 'value': 'Potawatomi (mother); his father a British officer', 'grade': 'attested'},
         {'label': 'Born', 'value': 'About 1780', 'grade': 'inferred'},
         {'label': 'On 14 August', 'value': 'Not yet at Chicago', 'grade': 'inferred'},
         {'label': 'On 15 August', 'value': 'Not at Chicago; came on the 16th (Wau-Bun)', 'grade': 'inferred'}],
        {'value': 'Not at Chicago; came on the 16th (Wau-Bun)', 'grade': 'inferred', 'note': "Wau-Bun's account; Quaife doubts it.", 'sources': ['kinzie_waubun_1856', 'quaife_1913']})
    robinson = _person(
        'robinson_alexander', 'Alexander Robinson (Che-che-pin-qua)', ['Che-che-pin-qua (Andreas)', 'Chechepinquay'],
        ("A trader from St. Joseph, born at Mackinac to an Odawa mother and a Scottish father, by popular belief in 1762. Whether he was at "
         "Chicago in August 1812 the sources do not agree: Andreas has him arrive too late to stop the killing yet a witness to it; Quaife "
         "names him among the chiefs; Wau-Bun puts him only at St. Joseph afterwards, where he sheltered the Kinzies, and with his wife he "
         "paddled the Healds to Mackinac. He was later a chief of the united Potawatomi, Chippewa and Ottawa and signed the 1833 treaty, "
         "kept a reservation on the Des Plaines, and died there on 22 April 1872."),
        {'value': 'uncertain', 'confidence': 'inferred', 'note': 'The sources disagree whether he was here on the 14th.'},
        ['andreas_1884_v1', 'quaife_1913', 'kinzie_waubun_1856', KIRKLAND],
        [{'source_id': 'andreas_1884_v1', 'locator': 'p. 108', 'quote': 'arrived on the scene too late to do anything to prevent the massacre, of which he was a witness',
          'claim': 'his presence, as Andreas has it'},
         {'source_id': KIRKLAND, 'locator': 'the plate "Alexander Robinson (in old age)"', 'quote': 'ALEXANDER ROBINSON (in old age).', 'claim': 'his portrait'}],
        [{'label': 'People', 'value': 'Odawa mother, Scottish father; later a chief of the united bands', 'grade': 'attested'},
         {'label': 'Born', 'value': 'About 1762 (popular belief)', 'grade': 'inferred'},
         {'label': 'On 14 August', 'value': 'Uncertain: the sources disagree', 'grade': 'inferred'},
         {'label': 'On 15 August', 'value': 'Not in the fighting; afterwards sheltered the Kinzies and carried the Healds away', 'grade': 'inferred'}],
        {'value': 'Not in the fighting; afterwards sheltered the Kinzies and carried the Healds away', 'grade': 'inferred',
         'note': 'Wau-Bun and Andreas; whether he was a witness is disputed.', 'sources': ['kinzie_waubun_1856', 'andreas_1884_v1']},
        portrait={'image': 'humans/web/portraits/robinson_kirkland_1893.jpg', 'caption': 'Alexander Robinson (in old age), chief of the Pottowatomies, Chippewas, and others: Kirkland 1893',
                  'source_id': KIRKLAND, 'grade': 'attested',
                  'why': 'His own likeness, late in life (he died in 1872): his face, not his dress of 1812.'})
    # Where each card is found: none of them lived at Chicago in 1812, so the place is the one his
    # sources tie him to in August (reconstructed as a home, and said so).
    places = {
        'hh_shabbona_1812': ('kinzie_house_1812', 'andreas_1884_v1',
                             "Not his home: by his own account (via Matson) he came in on the afternoon of the 15th and stood among the Indians guarding the Kinzie house that night. His card is found there."),
        'hh_caldwell_billy_1812': ('kinzie_house_1812', 'kinzie_waubun_1856',
                                   "Not his home: Wau-Bun brings him to the Kinzie house on the 16th, where he turned the Wabash party away. His card is found there."),
        'hh_robinson_alexander_1812': ('potawatomi_camp_1812_mouth', 'andreas_1884_v1',
                                       "Not his home: a St. Joseph trader, put with Topenebe's St. Joseph people at the camp by the river mouth, if he was here at all. His card is found there."),
    }
    out = {}
    for hid, title, person in (('hh_shabbona_1812', 'Shabbona, who came to Chicago after the fight of 15 August 1812', shabbona),
                               ('hh_caldwell_billy_1812', 'Billy Caldwell (Sauganash), who came to Chicago on 16 August 1812', caldwell),
                               ('hh_robinson_alexander_1812', 'Alexander Robinson, trader of St. Joseph, perhaps at Chicago in August 1812', robinson)):
        out[hid] = {'id': hid, 'scene': '1812', 'name': title, 'head': person['id'], 'division': 'camp',
                    'review_required': True, 'touches_removal': True, 'review_note': REVIEW,
                    'present_on_scene_date': {'value': person['present_on_scene_date']['value'], 'confidence': 'inferred', 'sources': person['sources'],
                                              'note': "His card says how his presence is known."},
                    'associated_with': [{'kind': 'home', 'place_or_structure_id': places[hid][0], 'resolves_to': 'structure', 'from': None, 'to': None,
                                         'tier': 'reconstructed', 'source_id': places[hid][1], 'also_sources': [], 'note': places[hid][2]}],
                    'not_in_this_household': {'note': 'Not drawn in the scene: he was not, or may not have been, at Chicago on the 14th.', 'sources': person['sources'][:1]},
                    'persons': [person]}
    return out


def _text(rec):
    return json.dumps(rec, indent=1, ensure_ascii=False) + '\n'


def main(check=False):
    stale = []
    for hid, rec in named_households().items():
        path = OUT / f'{hid}.json'
        text = _text(rec)
        if check:
            if not path.exists() or path.read_text() != text:
                stale.append(path.name)
        else:
            path.write_text(text)
    if stale:
        print('STALE:', *stale, '- run python3 tools/native_cards_1812.py')
        return 1
    print(f"{len(named_households())} named households {'current' if check else 'written'}")
    return 0


if __name__ == '__main__':
    sys.exit(main('--check' in sys.argv))
