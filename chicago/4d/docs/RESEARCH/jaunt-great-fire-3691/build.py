#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""The Great Chicago Fire jaunt (T-3691). The owner, 2026-11-19: "i definitiely want a follow the
chicago fire like a timeline and you follow the start of the fire and you see it engulf an area
and then you move to the next stop and see that, through burning the north side, etc. you shoul be
sure to make it seasonal time of day etc"; "its ok and good if we look at the main landmarks and
watch them burn along with the whole streetscape".

Twelve stops in the fire's order, each at its date and hour (a stop's `date` + `hour` is the fire's
clock, which renderers/web/js/city-fire.js reads, T-3687), from the claims in claims.py. Each stop
is a viewpoint of its own in data/scenes/1871.json (ANCHORS below: a stand in the street, looking at
the landmark, at a distance where the building and the fire read), so that a landmark arriving
later under its own structure id does not move or hold the stop. Each stop is staged with unnamed
figures of the crowd (renderers/web/js/jaunt-stage.js); the named people of the night are told in
the text and cast once 1871 has their cards (T-3690).

    python3 docs/RESEARCH/jaunt-great-fire-3691/build.py           # write
    python3 docs/RESEARCH/jaunt-great-fire-3691/build.py --check   # the jaunt is as built

It writes data/jaunts/the-great-fire.json, its viewpoints in data/scenes/1871.json and its
narration direction (data/narration/direction/the-great-fire.json; nothing is recorded). The
grade-band tellings and the 18+ telling are words files built by
docs/RESEARCH/jaunt-grade-versions-3621/versions.py from this base.
"""
import json
import math
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
import claims as C  # noqa: E402

ID = 'the-great-fire'
TITLE = 'The Great Chicago Fire'
SCENE_PATH = ROOT / 'data/scenes/1871.json'

# ── the viewpoints: (id, label, short, stand e, stand n, the landmark e, n) ──────────────────
# Corners from the modern street grid, which keeps the 1871 lines (State and Madison is the
# survey's own corner): the stand is in the street, the landmark the building or its corner.
ANCHORS = [
    ('fire_oleary_barn', "DeKoven Street, before the O'Leary cottage, looking at the barn behind it", "O'Leary barn", (-300.0, -2004.0), (-300.0, -1958.0)),
    ('fire_st_pauls', "Clinton Street south of Mather, looking at St. Paul's church and Bateham's mills", "St. Paul's church", (-266.0, -1560.0), (-245.0, -1490.0)),
    # T-3751 (the owner, 2026-11-26: "The narration says the user is on Jackson Street, but the scene appears to be
    # elsewhere"): the stand was 60 m up Franklin, on Quincy; now the north-west corner of Jackson and Franklin
    # (the plan's corner at 220.8, -958.4), looking across at the stable on the south-east corner.
    ('fire_parmelee_stables', 'Jackson and Franklin, looking across the corner at the new Parmelee stable', 'Parmelee stable', (212.8, -950.4), (240.0, -985.0)),
    ('fire_court_house', 'Clark Street at Washington, looking at the Court House in its square', 'Court House', (580.0, -408.0), (507.0, -330.0)),
    ('fire_sherman_house', 'The Court House square at Clark and Randolph, looking at the Sherman House', 'Sherman House', (560.0, -284.0), (596.0, -240.0)),
    ('fire_crosbys', "Washington Street between Dearborn and State, looking at Crosby's Opera House", "Crosby's Opera House", (770.0, -400.0), (770.0, -366.0)),
    ('fire_state_kinzie', 'The foot of the State Street viaduct, looking at the corner of Kinzie Street', 'State and Kinzie', (835.0, 210.0), (848.0, 268.0)),
    ('fire_water_works', 'Chicago Avenue at the lake shore, looking at the Water Tower and the pumping works', 'Water Works', (1090.0, 1100.0), (1165.0, 1156.0)),
    ('fire_tribune', 'Dearborn and Madison, looking at the Tribune building on its corner', 'Tribune building', (683.0, -497.0), (718.0, -540.0)),
    ('fire_field_leiter', "State and Washington, looking at Field, Leiter and Co.'s marble store", 'Field, Leiter & Co.', (832.0, -402.0), (856.0, -372.0)),
    # T-3751 (the owner, 2026-11-26: "The narration describes a burned park, but the park appears undamaged"): the
    # stand is at the south side of Washington Square (the square is 570-671 E, 1391-1437 N), so the whole burnt
    # park, its families' goods and the house beyond (T-3689 builds it at 612-628 E, 1475-1487 N) are in the view.
    ('fire_ogden_house', 'Washington Square, looking at the house of Mahlon D. Ogden', 'Ogden house', (616.0, 1400.0), (620.0, 1481.0)),
    ('fire_old_cemetery', 'The old City Cemetery in Lincoln Park, looking south over the burning North Side', 'Old cemetery', (470.0, 2870.0), (420.0, 2420.0)),
]
ANCHOR = {a[0]: a for a in ANCHORS}


def hd(a, b):
    return round((math.degrees(math.atan2(b[0] - a[0], b[1] - a[1])) + 360) % 360, 1)


def scene_anchor(a):
    aid, label, short, stand, target = a
    return {'id': aid, 'label': label, 'short': short, 'glyph': 'street', 'local_e': stand[0], 'local_n': stand[1], 'yaw_deg': hd(stand, target)}


# ── the crowd (unnamed figures; the dress is a figure the town draws, L-1871-great-fire-jaunt) ─
MEN = ['mahoney_patrick_1835', 'bardwell_otis_1835', 'peck_philip_1835', 'glessner_john_j_1904', 'anonymous_working_driver_1904']
WOMEN = ['flynn_mary_1835_dress_study', 'reynolds_mary_1904_maid', 'ryan_kate_1904_cook']
CHILDREN = ['child_boy_1904', 'child_girl_1904']


def frame(aid):
    _, _, _, stand, target = ANCHOR[aid]
    de, dn = target[0] - stand[0], target[1] - stand[1]
    L = math.hypot(de, dn)
    f = (de / L, dn / L)
    r = (f[1], -f[0])          # the stand looking at the landmark has this on its right
    return stand, target, f, r, L


def mark(aid, a, b):
    """`a` m from the stand toward the landmark, `b` m to the right."""
    stand, _, f, r, _ = frame(aid)
    return [round(stand[0] + a * f[0] + b * r[0], 2), round(stand[1] + a * f[1] + b * r[1], 2)]


_CONTEXT = None


def clearance(p):
    """Metres from p to the nearest building the 1871 context draws (data/context/1871.json)."""
    global _CONTEXT
    if _CONTEXT is None:
        _CONTEXT = json.loads((ROOT / 'data/context/1871.json').read_text())['buildings']
    best = 1e9
    for b in _CONTEXT:
        if abs(b['e'] - p[0]) > 60 or abs(b['n'] - p[1]) > 60:
            continue
        th = math.radians(b['bearing_deg'])
        de, dn = p[0] - b['e'], p[1] - b['n']
        u, v = de * math.cos(th) - dn * math.sin(th), de * math.sin(th) + dn * math.cos(th)
        best = min(best, math.hypot(max(0, abs(u) - b['width_m'] / 2), max(0, abs(v) - b['depth_m'] / 2)))
    return best


def in_the_open(aid, a, b, least=1.5):
    """The farthest distance out to `a` along the stand's line (at offset b) that stands clear of the
    context's buildings: no figure is put inside one (the landmarks themselves arrive later)."""
    while a > 3 and clearance(mark(aid, a, b)) < least:
        a -= 1
    return a


def crowd(aid, watchers, fleers, seed):
    """Watchers stand about the stand, looking at the landmark; fleers come away from it past the
    stand and on behind. Deterministic from `seed`; every figure is unnamed."""
    _, target, _, _, L = frame(aid)
    cast, k = [], seed
    # The stop's view looks down the line from the stand to the landmark, and a phone held upright
    # sees about 20 degrees either side of it: the watchers stand 10-25 m out and near the line,
    # their backs to you, and the people getting away come down it toward you and past.
    watchers = [(in_the_open(aid, 10 + a, b * 0.45), b * 0.45, who) for a, b, who in watchers]
    fleers = [(in_the_open(aid, min(a0, L - 6), b0 * 0.35), b0 * 0.35, -4.0, b1 * 0.3, t, pace, who) for a0, b0, a1, b1, t, pace, who in fleers]
    for i, (a, b, who) in enumerate(watchers):
        dress = {'m': MEN, 'w': WOMEN, 'c': CHILDREN}[who][(k + i) % len({'m': MEN, 'w': WOMEN, 'c': CHILDREN}[who])]
        role = {'m': 'A man watching', 'w': 'A woman watching', 'c': 'A child watching'}[who]
        cast.append({'extra': f'{aid}_watch_{i}', 'dress': dress, 'name': f'{role} (unnamed)', 'at': mark(aid, a, b), 'heading': hd(mark(aid, a, b), target)})
    for i, (a0, b0, a1, b1, t, pace, who) in enumerate(fleers):
        pool = {'m': MEN, 'w': WOMEN, 'c': CHILDREN}[who]
        dress = pool[(k + 2 * i + 1) % len(pool)]
        role = {'m': 'A man getting away', 'w': 'A woman getting away', 'c': 'A child getting away'}[who]
        if clearance(mark(aid, a1, b1)) < 1.5:
            b1 = 0.0
        start, end = mark(aid, a0, b0), mark(aid, a1, b1)
        cast.append({'extra': f'{aid}_flee_{i}', 'dress': dress, 'name': f'{role} (unnamed)', 'at': start, 'heading': hd(start, end),
                     'beats': [{'t': t, 'walk': [mark(aid, (a0 + a1) / 2, (b0 + b1) / 2 + (1.5 if i % 2 else -1.5)), end], 'pace': pace}]})
    return cast


# ── the stops ───────────────────────────────────────────────────────────────────────────────
OPENING = ("JAUNT: THE GREAT CHICAGO FIRE. Sunday night, 8 October 1871, at the end of a dry summer. Since the 3rd of July only "
           "two and a half inches of rain have fallen on Chicago, and the West Side is built of wood. A strong wind is blowing "
           "from the south-west. The firemen are worn out: last night they fought another fire by the river, and worked on "
           "into this afternoon.\n\n"
           "Twelve stops, hour by hour, from a cow barn on the West Side, over two rivers, to the far end of the North Side, "
           "with the night and then the day as they were. Long rides go Instantly; every place keeps its stop.\n\n"
           "It begins in a barn on DeKoven Street, at about nine o'clock.")

STOPS = [
    dict(id='oleary-barn', anchor='fire_oleary_barn', date='1871-10-08', hour='21:00', hour_evidence=['lee'],
         evidence=['barn', 'legend', 'inquiry', 'sullivan', 'lee', 'alarm', 'wind'],
         text="Sunday 8 October 1871, about nine at night, on DeKoven Street. Behind the cottage at No. 137 stands the barn of "
              "Patrick and Catherine O'Leary, who keep cows and sell the milk to the neighbours. The "
              "loft \"had recently been filled with hay\". According to legend, Mrs. O'Leary was milking when her cow kicked over "
              "a lamp. The inquiry found the O'Learys in bed, and \"no proof that any person had been in the barn after nightfall "
              "that evening.\" Daniel Sullivan, a drayman across the street, saw the flames; \"he has a "
              "wooden leg\", and he ran anyway. He got out a calf: \"The hair on its back was on fire\". William Lee, "
              "two doors along, runs to the drug store for the alarm key and is refused it. \"The clock struck nine.\" "
              "Across the river, in the Court House tower, the watchman has not yet seen the light.",
         caption="Neighbours come out into DeKoven Street to watch the barn burn, and families carry what they can out of the cottages behind it.",
         cast=lambda: crowd('fire_oleary_barn', [(8, -6, 'm'), (9, -2, 'w'), (7, 3, 'm'), (10, 7, 'c'), (5, 10, 'w')],
                            [(40, -12, -8, -30, 2, 'hurry', 'w'), (38, 14, -10, 26, 4, 'hurry', 'm'), (36, 6, -6, 18, 7, 'brisk', 'c')], 0)),
    dict(id='st-pauls', anchor='fire_st_pauls', date='1871-10-08', hour='22:30', hour_evidence=['bateham'], since='Ninety minutes later',
         evidence=['alarm', 'little-giant', 'riley', 'st-pauls', 'bateham', 'wind'],
         text="Half past ten, Clinton and Mather Streets. The alarm came late, and wrong. At 9:28 Mathias Schaffer, the watchman in "
              "the Court House tower, read the light through his spy-glass and called Box 342, \"nearly a mile from the fire\". "
              "One engine, the Little Giant, fought it: \"For more than thirty minutes this engine battled alone.\" Then the gale "
              "took the fire over the firemen's heads. Richard Riley, a railroad contractor up on a lumber pile, saw \"A large "
              "mass of fire\" go \"whirling through the air for more than three blocks\" onto the cupola of this church, St. "
              "Paul's. The church is down. Behind it William B. Bateham's mills, with a thousand cords of kindling wood "
              "in the yard, are going too. Bateham, a member of the city council, turns away: \"The "
              "materials from this mill will fire the South Side, and nothing can prevent it now.\"",
         caption="Families from the blocks round the church hurry north with bundles and a mattress, and a few men stop at the corner to watch the mills go.",
         cast=lambda: crowd('fire_st_pauls', [(6, -8, 'm'), (8, -4, 'm'), (7, 6, 'w'), (4, 9, 'm')],
                            [(60, -14, -12, -26, 1, 'hurry', 'w'), (58, 10, -14, 22, 3, 'run', 'm'), (55, -4, -10, -10, 5, 'hurry', 'c'), (62, 2, -16, 4, 8, 'brisk', 'w')], 1)),
    dict(id='parmelee', anchor='fire_parmelee_stables', date='1871-10-08', hour='23:30', hour_evidence=['parmelee'], since='One hour later',
         evidence=['parmelee', 'gasworks'],
         text="Half past eleven, Jackson and Franklin Streets, across the South Branch of the river. Since half past nine brands have been falling on this side, and now one has caught. This is the new stable of "
              "the Parmelee Omnibus and Stage Company, \"the finest of its kind in the country\", built for $80,000 and to have "
              "been \"occupied for the first time on Wednesday\". At the stable the fire "
              "\"swept down upon them with such rapidity and terrific force as to compel them to flee for their lives.\" By "
              "midnight the gas works on Adams Street are burning, and the shanties of Conley's Patch beside them. Beyond lie the "
              "stone and marble blocks of LaSalle Street, a double row of \"fire-proof\" buildings. One writer asked: \"Would these "
              "succumb to the shower of brands and the triple-heated furnace which had been thrown about them?\"",
         caption="Stablemen lead nothing out in time; men run from the burning stable up Franklin Street, and others stand at the corner looking at the sky to the south-west.",
         cast=lambda: crowd('fire_parmelee_stables', [(6, -5, 'm'), (8, 4, 'm'), (5, 8, 'm')],
                            [(52, -8, -10, -18, 1, 'run', 'm'), (50, 6, -12, 14, 2, 'run', 'm'), (48, 0, -14, -2, 5, 'hurry', 'w')], 2)),
    dict(id='court-house', anchor='fire_court_house', date='1871-10-09', hour='01:30', hour_evidence=['tower'], since='Two hours later',
         evidence=['tower', 'mason', 'prisoners'],
         text="Half past one on Monday morning, the Court House square, in the heart of the city. Mathias Schaffer, the watchman "
              "whose alarm sent the engines astray, is still in the tower. Since ten o'clock sparks have been falling on the roof; "
              "it has caught \"five or six times\", and he has put it out with two Babcock fire-extinguishers. In the basement the "
              "mayor, Roswell B. Mason, has been giving orders since midnight: gunpowder to blow up buildings, and the jail "
              "emptied. Captain Hickey has had the cells unlocked, and the prisoners \"rushed into the street\", where a passing "
              "truck of ready-made clothing is emptied in an instant; the men charged with murder go out in handcuffs. Now the "
              "tower is alight. Schaffer and his relief, Dennis Denene, set the great bell ringing, and run for the stairs. It "
              "weighs 10,849 pounds, and it is still ringing.",
         caption="Released prisoners run out of the square, and men who came to save the city's records stand back across Clark Street to watch the tower.",
         cast=lambda: crowd('fire_court_house', [(10, -9, 'm'), (12, -3, 'm'), (9, 4, 'm'), (11, 9, 'w')],
                            [(70, -10, -6, -24, 1, 'run', 'm'), (68, 8, -8, 20, 2, 'flee', 'm'), (72, 2, -10, -4, 4, 'run', 'm'), (66, -4, -12, 8, 6, 'hurry', 'w')], 3)),
    dict(id='sherman-house', anchor='fire_sherman_house', date='1871-10-09', hour='02:05', hour_evidence=['mason', 'sherman-hour'], since='35 minutes later',
         evidence=['mason', 'sherman', 'sherman-hour', 'crossing'],
         text="Five past two, at the corner of Clark and Randolph. Behind you the Court House bell comes \"crashing and clanging "
              "down\", and Mayor Mason, who stayed until it fell, comes out to find LaSalle Street \"like a furnace, all fire\". "
              "Across Clark Street is the Sherman House, seven stories, with more than three hundred guests. Hours ago men were "
              "tearing down its awnings to save it. A writer for the Post watched it: \"for nearly an hour the house held good. "
              "Suddenly, a spirit of flame came from a window in the third story on the southern face\". Only the night clerk and "
              "an assistant are left to wake every room, and five ladies are sick in bed. North of the hotel lies the main river, "
              "the last line between the fire and the North Side. The wind is already carrying it over.",
         caption="Hotel guests come out with what luggage they can carry and hurry away north and east; a few stop on the corner and look back at the hotel.",
         cast=lambda: crowd('fire_sherman_house', [(6, -7, 'm'), (7, -2, 'w'), (5, 6, 'm')],
                            [(52, -6, -8, -22, 1, 'hurry', 'w'), (50, 4, -10, 16, 2, 'hurry', 'm'), (54, 0, -12, -4, 4, 'brisk', 'm'), (48, 8, -6, 24, 6, 'hurry', 'w')], 4)),
    dict(id='crosbys', anchor='fire_crosbys', date='1871-10-09', hour='02:20', hour_evidence=['crosbys-hour'], since='Fifteen minutes later',
         evidence=['crosbys', 'reopening', 'crosbys-falls', 'crosbys-hour'],
         text="Twenty past two, Washington Street between Dearborn and State. From the Court House the fire has turned east, "
              "This is Crosby's Opera House, opened in 1865, with seats for 2,500. All "
              "summer it was closed while $80,000 went on new ornament, upholstery and frescoes. It "
              "was to open again tomorrow night, Monday, with Theodore Thomas and his orchestra, and tonight, \"only an hour or two "
              "before the fire, it was lit up for the first time, that its effects might be seen by gaslight.\" Now the roof "
              "catches. \"In almost the time it takes to write these lines,\" wrote James Sheahan and George Upton, two Chicago "
              "newspapermen, the handsomest auditorium in the country is gone. The St. James Hotel next door, which \"had two or "
              "three times before stood the test of fire\", falls with it. And on the far side of the main river, the North Side "
              "has caught.",
         caption="People from the hotels and the stores on Washington Street hurry east toward the lake; two men stand in the roadway and watch the opera house roof.",
         cast=lambda: crowd('fire_crosbys', [(8, -6, 'm'), (9, 5, 'm'), (6, 9, 'w')],
                            [(38, -10, -6, -26, 1, 'hurry', 'm'), (36, 10, -8, 26, 2, 'hurry', 'w'), (40, 0, -10, 12, 5, 'brisk', 'c')], 5)),
    dict(id='north-side', anchor='fire_state_kinzie', date='1871-10-09', hour='02:30', hour_evidence=['wright'], since='Ten minutes later',
         evidence=['crossing', 'wright', 'mason-north', 'asleep', 'one-works'],
         text="Half past two, north of the main river, where the State Street viaduct comes down at Kinzie Street. The river did "
              "not stop it. \"About the time that the Sherman House was ablaze\", the wind carried the fire over the water, and it "
              "\"broke out just north of the bridge, at State street.\" Now Wright's stable on this corner is burning. An hour ago "
              "Judge Lambert Tree crossed the bridge when it \"was then "
              "burning in spots\". Mayor Mason and his son, cut off on the South Side, are coming over by the Wells Street bridge "
              "to get round the fire, and will find it here ahead of them. North of this corner most people are asleep; many will "
              "wake to find themselves \"surrounded by fire.\" Half a mile away on the lake shore stands the one building that pumps "
              "the water for the whole city.",
         caption="North Side people woken by the glare come out half-dressed, and the first of them start away north up State Street with what they can carry.",
         cast=lambda: crowd('fire_state_kinzie', [(6, -6, 'w'), (8, 0, 'm'), (6, 6, 'm'), (4, 9, 'c')],
                            [(52, -6, -4, -20, 2, 'hurry', 'w'), (50, 6, -6, 18, 3, 'hurry', 'm'), (54, 0, -8, 4, 6, 'brisk', 'm')], 6)),
    dict(id='water-works', anchor='fire_water_works', date='1871-10-09', hour='03:20', hour_evidence=['waterworks'], since='Fifty minutes later',
         evidence=['waterworks', 'one-works', 'water-tower', 'tower-stands'],
         text="Twenty past three, Chicago Avenue at the lake shore. Here are the Water Works: the engine house, and a hundred and "
              "fifty feet west of it the Water Tower, a stone tower round an iron column 130 feet high, up which the pumps force "
              "the water for the whole city. The engineer, Frank Trautman, has his engines running at thirty million gallons a "
              "day. D. W. Fuller, standing by, sees \"a fire-brand, apparently twelve feet "
              "in length,\" come whirling toward the tower and strike the corner of the engine house. \"In an instant, the roof was "
              "aflame.\" The roof is wood. Fuller looks at his watch: \"exactly twenty minutes past three.\" A few minutes before "
              "four the men are driven out. The tower will stand; the engines will stop. From now on the firemen can fight only "
              "where they can draw water from the river.",
         caption="Men from the works and the breweries along the shore come out on Chicago Avenue to watch the engine house roof, and families go by toward the lake.",
         cast=lambda: crowd('fire_water_works', [(10, -8, 'm'), (12, -2, 'm'), (9, 5, 'm'), (11, 10, 'w')],
                            [(30, -16, -6, -30, 2, 'hurry', 'w'), (34, 16, -8, 28, 4, 'hurry', 'm'), (28, -2, -10, -14, 7, 'brisk', 'c')], 7)),
    dict(id='tribune', anchor='fire_tribune', date='1871-10-09', hour='07:30', hour_evidence=['tribune-hour'], since='Four hours later',
         evidence=['bross', 'medill-white', 'tribune-falls', 'tribune-hour'],
         text="Half past seven on Monday morning, Dearborn and Madison Streets, in daylight. On this corner stands the Tribune "
              "building, which its owners call fireproof. At daybreak William Bross, "
              "a former lieutenant governor of Illinois and one of the paper's owners, rode here and \"found everything safe\". "
              "When fire crept under the sidewalk into the barber's shop in the basement, Bross put it out with his partners, "
              "Joseph Medill, one of the chief stockholders, and Horace White, the editor, \"with water and one of Babcock's "
              "fire-extinguishers.\" The forms went down to the presses for the morning's paper. Then the fire came back from the "
              "south, past the great Palmer House, to McVicker's Theatre across a narrow alley. \"The iron shutters on the alley "
              "side, bent by the fire, sprung out of place\". The Tribune goes, and with the Water Works gone there is nothing to "
              "stop what comes next.",
         caption="Printers and clerks come out of the Tribune with armfuls of papers and hurry up Dearborn Street; a few men stand on the burned corner opposite.",
         cast=lambda: crowd('fire_tribune', [(6, -6, 'm'), (8, 4, 'm'), (5, 8, 'm')],
                            [(40, -6, -8, -22, 1, 'hurry', 'm'), (42, 6, -10, 18, 3, 'brisk', 'm'), (38, 0, -12, -2, 6, 'hurry', 'w')], 8)),
    dict(id='state-street', anchor='fire_field_leiter', date='1871-10-09', hour='08:00', hour_evidence=['field-hour'], since='Thirty minutes later',
         evidence=['palmer', 'field-leiter', 'field-hour'],
         text="Eight o'clock, State Street at Washington. This store of white Massachusetts marble belongs to Potter Palmer, who "
              "built the Palmer House hotel a few blocks south. He rents it to Field, Leiter and Co., dry goods importers, for "
              "$52,000 a year. At first light their own men were \"showering that massive pile of pure marble and iron with water "
              "from their own pumping engines.\" Now the streams \"had ceased to run\", because the Water Works are gone, and men "
              "are carrying goods out of the lower floor into wagons. The fire comes at it \"from the north and eastwardly in the "
              "rear, and it soon yielded.\" Down State Street the Palmer House is already a ruin. On the North Side the fire has "
              "been running since half past two, and it has not stopped.",
         caption="Wagons wait at the kerb while men carry bolts of cloth out of the store; shoppers' carriages and porters hurry the goods away up State Street.",
         cast=lambda: crowd('fire_field_leiter', [(7, -8, 'm'), (9, 6, 'w'), (5, 10, 'm')],
                            [(40, -6, -6, -24, 1, 'hurry', 'm'), (42, 4, -8, 20, 2, 'hurry', 'm'), (38, 0, -10, -4, 5, 'brisk', 'w'), (44, 8, -6, 26, 8, 'hurry', 'm')], 9)),
    dict(id='ogden-house', anchor='fire_ogden_house', date='1871-10-09', hour='12:00', hour_evidence=['ogden-hour'], since='Four hours later',
         evidence=['ogden', 'first-mayor', 'st-michaels', 'monday', 'ogden-hour'],
         text="Midday on Monday, on the North Side, before the house of Mahlon D. Ogden, brother of William B. Ogden, Chicago's "
              "first mayor. It is made of wood, and it is standing. In front of it lies Washington Park, which "
              "filled in the night with fugitives and their furniture, until the fire came through and burned \"the accumulated "
              "furniture of fifty families.\" Men inside tore up the carpets, spread them over the walls "
              "and kept them wet, and when the hydrant failed, \"Several barrels of cider were used to saturate the carpets\". "
              "Around it now is \"nothing but this solitary building in an area of 2,600 acres.\" A mile north the fire is nearing "
              "St. Michael's, the great brick German church, whose steeple it will burn. "
              "Ahead of the fire, the people of the North Side are running for the lake and the old cemetery.",
         caption="The men who saved the house stand in the burnt park looking at it; a family picks through what is left of their furniture.",
         cast=lambda: crowd('fire_ogden_house', [(10, -6, 'm'), (12, 0, 'm'), (9, 6, 'm'), (6, -10, 'w'), (5, -12, 'c')], [], 10)),
    dict(id='old-cemetery', anchor='fire_old_cemetery', date='1871-10-09', hour='18:30', hour_evidence=['cemetery-hour'], since='Six hours later',
         evidence=['cemetery', 'chapel-chairs', 'beach', 'prairie', 'cemetery-hour'],
         text="Nightfall on Monday, the old City Cemetery at the south end of Lincoln Park. Most of its dead were moved years ago, "
              "leaving \"some old headstones scattered about\" among the grass and the small oaks. \"By nightfall on Monday there "
              "could not have been less than thirty thousand men, women, and children, huddled within this ghostly inclosure.\" "
              "They carried in beds, chairs and bundles, and many have watched them \"burn up before their eyes.\" South along the lake shore, \"Along the beach "
              "were judges, merchants, doctors, workingmen, women and children\", and \"Ladies were seen moving their chairs into "
              "the water, and sitting on the top of the backs\". Thousands more have gone west to the open prairie. Here they are "
              "\"blinded by smoke, weakened by hunger, and choking with thirst\", and nobody can say where the fire will stop.",
         caption="Families sit among the old graves with their bundles and chairs, looking south at the glow; others are still coming in from the burning streets.",
         cast=lambda: crowd('fire_old_cemetery', [(8, -8, 'w'), (10, -3, 'm'), (7, 3, 'c'), (9, 8, 'w'), (12, 12, 'm'), (6, -12, 'm')],
                            [(60, -8, 6, -6, 1, 'slow', 'w'), (64, 6, 8, 10, 3, 'slow', 'm')], 11)),
]

LEGS = [
    dict(note="North-east from the barn, the way the wind blew: this leg goes Instantly.", mode='instantly',
         story="North-east across Taylor Street through the wooden cottages, the way the wind is carrying the fire.", evidence=['wind'], story_evidence=['wind']),
    dict(note="Across the South Branch to Jackson Street: this leg goes Instantly.", mode='instantly',
         story="Over the South Branch of the river, as the brands come down on the South Side.", evidence=['parmelee'], story_evidence=['parmelee']),
    dict(note="North through the business district to the Court House square: this leg goes Instantly.", mode='instantly',
         story="North and east, two hours on, through the gas works' glare toward the heart of the city.", evidence=['gasworks'], story_evidence=['gasworks']),
    dict(story="Across the square to its corner on Clark and Randolph.", evidence=['sherman'], story_evidence=['sherman']),
    dict(story="East along Randolph and down to Washington Street, the way the fire turned.", evidence=['crosbys-falls'], story_evidence=['crosbys-falls']),
    dict(note="North over the main river by the State Street bridge: this leg goes Instantly.", mode='instantly',
         story="Over the main river, where the State Street bridge is burning in spots.", evidence=['wright'], story_evidence=['wright']),
    dict(note="Half a mile north-east to the lake shore: this leg goes Instantly.", mode='instantly',
         story="North-east through the North Side to the lake shore at Chicago Avenue.", evidence=['waterworks'], story_evidence=['waterworks']),
    dict(note="Back over the river to the South Side, four hours on: this leg goes Instantly.", mode='instantly',
         story="Back over the river to the South Side. The sun is up behind the smoke.", evidence=['bross'], story_evidence=['bross']),
    dict(story="East along Madison and up State Street to Washington.", evidence=['field-leiter'], story_evidence=['field-leiter']),
    dict(note="Over the river again to the North Side: this leg goes Instantly.", mode='instantly',
         story="Over the river again to the North Side, where the fire has run north all morning.", evidence=['monday'], story_evidence=['monday']),
    dict(note="North with the crowds to Lincoln Park: this leg goes Instantly.", mode='instantly',
         story="North with the crowds, to the old cemetery at the edge of Lincoln Park.", evidence=['cemetery'], story_evidence=['cemetery']),
]

ENDINGS = [
    dict(id='the-rain', evidence=['end', 'rain', 'toll', 'proclamation'],
         text="Monday night, 9 October 1871. At about half past ten the fire reaches the north end of Lincoln Park and burns the "
              "house of Dr. John H. Foster on Fullerton Avenue, \"just twenty-five hours from the commencement of the fire, and "
              "about four miles distant from the place of its origin.\" There it \"spent itself\". Then \"About eleven o'clock Monday "
              "night, the sky, as if in remorse at what the fiery element had done, poured down floods of rain.\" In the cemetery "
              "and on the prairie the people stand in it, soaked. The count, when it was made: 2,124 acres burned, 17,450 "
              "buildings destroyed, 98,500 people homeless, and \"more than 250\" dead. The mayor's first proclamation pledged the "
              "city's credit \"for the necessary expenses for the relief of the suffering\", and ended: \"It is believed the fire "
              "has spent its force and all will soon be well.\""),
]

PREMISE = ("Sunday night, 8 October 1871, to the rain on Monday night, in twelve stops at their hours: the O'Leary barn, St. "
           "Paul's, the Court House bell, Crosby's Opera House, the river crossed, the Water Works, the Tribune and the North Side.")

KEEPSAKE = {'family': 'News & Knowledge', 'id': 'mason-proclamation', 'title': "Mayor Mason's proclamation, October 1871",
            'text': "\"Public order will be preserved.\" The first proclamation of the mayor after the fire, as Sheahan and Upton printed it that autumn."}

# ── the narrator's direction (T-3578 format): a lead tag and edits that add only tags ─────────
P, LP = '[short pause]', '[long pause]'
DIRECTION = {
    'opening:opening': ('[hushed, ominous]', [('It begins in a barn', f'{P} It begins in a barn')]),
    'stop:oleary-barn': ('[quietly]', [('According to legend,', '[wryly] According to legend,'), ('"The clock struck nine."', f'{P} "The clock struck nine."'),
                                       ('Across the river, in the Court House tower,', f'{LP} [low] Across the river, in the Court House tower,')]),
    'stop:st-pauls': ('[urgent]', [('The alarm came late, and wrong.', '[grimly] The alarm came late, and wrong.'), ('Bateham, a member of the city council, turns away:', f'{P} Bateham, a member of the city council, turns away:')]),
    'stop:parmelee': ('[tense]', [('One writer asked:', f'{P} One writer asked:')]),
    'stop:court-house': ('[urgent]', [('Now the tower is alight.', f'{P} Now the tower is alight.'), ('and it is still ringing.', '[low] and it is still ringing.')]),
    'stop:sherman-house': ('[dramatic]', [('The wind is already carrying it over.', f'{P} [low] The wind is already carrying it over.')]),
    'stop:crosbys': ('[wistful]', [('Now the roof catches.', f'{P} [grimly] Now the roof catches.')]),
    'stop:north-side': ('[urgent]', [('The river did not stop it.', '[grimly] The river did not stop it.'), ('Half a mile away on the lake shore', f'{LP} Half a mile away on the lake shore')]),
    'stop:water-works': ('[tense]', [('The roof is wood.', f'{P} The roof is wood.'), ('The tower will stand; the engines will stop.', f'{P} [low] The tower will stand; the engines will stop.')]),
    'stop:tribune': ('[measured]', [('Then the fire came back from the south,', f'{P} [grimly] Then the fire came back from the south,')]),
    'stop:state-street': ('[measured]', [('Now the streams', f'{P} Now the streams')]),
    'stop:ogden-house': ('[quietly]', [('It is made of wood, and it is standing.', '[wonder] It is made of wood, and it is standing.')]),
    'stop:old-cemetery': ('[hushed]', [('and nobody can say where the fire will stop.', '[softly] and nobody can say where the fire will stop.')]),
    'ending:the-rain': ('[slowly]', [('Then "About eleven', f'{LP} [relieved] Then "About eleven'), ('The count, when it was made:', f'{LP} [somber] The count, when it was made:')]),
}


# ── building ────────────────────────────────────────────────────────────────────────────────
def read_s(text):
    return max(8, round(len(text.split()) / 3.8))


def dev_version(path):
    try:
        raw = subprocess.run(['git', 'show', f'origin/dev:chicago/4d/{path.relative_to(ROOT)}'], cwd=ROOT, capture_output=True, text=True, check=True).stdout
        return json.loads(raw)['content_version'] + 1
    except Exception:
        return 1


def build():
    staging = C.staging(TITLE)
    used = []

    def use(ids):
        for i in ids:
            if i not in used: used.append(i)
    stops = []
    for k, s in enumerate(STOPS):
        ev = list(s['evidence']) + (['drought'] if k == 0 else []) + ['stand', 'stage']
        use(ev)
        stop = {'id': s['id'], 'destination': {'kind': 'anchor', 'id': s['anchor']}, 'text': s['text'], 'read_s': read_s(s['text']),
                'evidence': ev, 'next': STOPS[k + 1]['id'] if k + 1 < len(STOPS) else ENDINGS[0]['id'],
                'hour': s['hour'], 'date': s['date'], 'hour_evidence': s['hour_evidence']}
        if 'since' in s: stop['since'] = s['since']
        stop['stage'] = {'caption': s['caption'], 'liberty': C.LIBERTY, 'cast': s['cast']()}
        stops.append(stop)
    legs = []
    for leg in LEGS:
        use(leg['evidence'] + leg['story_evidence'])
        assert len(leg['story']) <= 180, leg['story']
        legs.append({k: leg[k] for k in ('note', 'mode', 'story', 'evidence', 'story_evidence') if k in leg})
    endings = []
    for e in ENDINGS:
        use(e['evidence'])
        endings.append({'id': e['id'], 'default': True, 'completion_eligible': True, 'read_s': read_s(e['text']), 'text': e['text']})
    use(['proclamation', 'the-lost'])
    evidence = [({'id': cid} | staging[cid]) if cid in staging else ({'id': cid} | C.CLAIMS[cid]) for cid in used]
    path = ROOT / f'data/jaunts/{ID}.json'
    doc = {
        'schema_version': 1, 'content_version': dev_version(path),
        'category': 'The Great Fire', 'menu_group': 'Stories', 'menu_rank': 1, 'grade_band': GRADE_BAND, 'featured': True,
        'review_required': False, 'id': ID, 'scene': '1871', 'title': TITLE, 'premise': PREMISE,
        'default_mode': 'fly', 'allowed_modes': ['fly', 'instantly'], 'long_form': True,
        'ambience': {'season': 'fall'},
        'opening': {'text': OPENING, 'read_s': read_s(OPENING)},
        'stops': stops, 'legs': legs, 'endings': endings, 'keepsake': KEEPSAKE,
        'evidence': evidence, 'liberties': [C.LIBERTY],
    }
    assert len(PREMISE) <= 260, len(PREMISE)
    for s in stops:
        n = len(s['text'].split())
        assert 25 <= n <= 150, (s['id'], n)
    return path, doc


GRADE_BAND = '6-8'


def words(text):
    """tools/narrate_jaunts.mjs spokenWords: the words alone, tags, case and punctuation aside."""
    return re.findall(r'[^\W_]+', re.sub(r'\[[^\]]*\]', ' ', text).lower())


def opening_script(doc):
    """renderers/web/js/narration.js openingScript: the title, then the welcome without its leading
    "JAUNT: ITS TITLE." line, which the title replaces."""
    paras = [t.strip() for t in re.split(r'\n\s*\n', doc['opening']['text']) if t.strip()]
    if paras: paras[0] = re.sub(r'^JAUNT:\s*[^.!?]*[.!?]\s*', '', paras[0])
    body = '\n\n'.join(p for p in paras if p)
    return f"{doc['title'].strip()}.\n\n{body}" if body else ''


def direction(doc):
    texts = {'opening:opening': opening_script(doc), **{f'stop:{s["id"]}': s['text'] for s in doc['stops']},
             **{f'ending:{e["id"]}': e['text'] for e in doc['endings']}}
    scripts, misses = {}, []
    for key, text in texts.items():
        lead, edits = DIRECTION.get(key, ('', []))
        out = text
        for old, new in edits:
            if out.count(old) != 1: misses.append(f'{key}: {old!r} found {out.count(old)} times'); continue
            out = out.replace(old, new)
        out = (lead + ' ' + out).strip() if lead else out
        if words(out) != words(text): misses.append(f'{key}: the performed words differ from the panel\'s')
        scripts[key] = out
    if set(DIRECTION) - set(texts): misses.append(f'direction for parts it does not have: {sorted(set(DIRECTION) - set(texts))}')
    return {'$comment': "T-3578 format, written by docs/RESEARCH/jaunt-great-fire-3691/build.py: the same words as the panel shows, with "
                        "audio tags in square brackets and [short pause]/[long pause] for pauses. Performance only: a hush or a low "
                        "voice is a reading of the story, not evidence of how anyone spoke (L-jaunt-voices-3578). Keyed <part>:<id>. "
                        "Nothing is recorded until the owner asks.",
            'version': 1, 'jaunt': doc['id'], 'scripts': scripts}, misses


def scene_with_anchors():
    scene = json.loads(SCENE_PATH.read_text())
    ours = {a[0] for a in ANCHORS}
    kept = [a for a in scene['anchors'] if a['id'] not in ours]
    scene['anchors'] = kept + [scene_anchor(a) for a in ANCHORS]
    return scene


def main(check=False):
    path, doc = build()
    body = json.dumps(doc, indent=2, ensure_ascii=False) + '\n'
    perf, misses = direction(doc)
    if misses:
        raise SystemExit('direction refused:\n  ' + '\n  '.join(misses))
    dpath = ROOT / f'data/narration/direction/{ID}.json'
    dbody = json.dumps(perf, indent=2, ensure_ascii=False) + '\n'
    sbody = json.dumps(scene_with_anchors(), indent=2, ensure_ascii=False) + '\n'
    outs = [(path, body), (dpath, dbody), (SCENE_PATH, sbody)]
    if check:
        stale = [str(p.relative_to(ROOT)) for p, b in outs if not p.exists() or p.read_text() != b]
        if stale: raise SystemExit('stale: ' + ', '.join(stale) + '; run build.py')
        print('the-great-fire: as built')
        return
    for p, b in outs:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(b)
    w = [len(s['text'].split()) for s in doc['stops']]
    print(f'wrote {path.relative_to(ROOT)}: {len(doc["stops"])} stops ({min(w)}-{max(w)} words), '
          f'{sum(len(s["stage"]["cast"]) for s in doc["stops"])} castmates, {len(doc["evidence"])} claims; {len(ANCHORS)} viewpoints in 1871')


if __name__ == '__main__':
    main('--check' in sys.argv)
