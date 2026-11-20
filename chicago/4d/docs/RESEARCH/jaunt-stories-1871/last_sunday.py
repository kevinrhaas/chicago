# SPDX-License-Identifier: GPL-3.0-or-later
"""T-3692, The Last Sunday: 1871 Chicago at its peak, Sunday 8 October, mid-afternoon to dusk.
No fire clock: every stop is before the barn burns. Built by build.py; the route, its order and
its hours are L-1871-last-sunday-3692 (claim 'sunday-walk')."""

P, LP = '[short pause]', '[long pause]'

DATE = '1871-10-08'

JAUNT = {
    'id': 'the-last-sunday',
    'title': 'The Last Sunday',
    'category': 'Great Fire 1871',
    'menu_rank': 2,
    'hour': 'afternoon',
    'premise': "Sunday 8 October 1871, afternoon to dusk: the busiest, proudest city in the West on its last ordinary day, from Lake Street to State Street, the Water Tower and a barn on DeKoven Street. Nine stops.",
    'opening': (
        "JAUNT: THE LAST SUNDAY. Sunday 8 October 1871, early afternoon. It has not rained for more than a week, "
        "and a warm wind is blowing hard from the southwest. Last night a fire on the West Side burned four blocks "
        "near the river, and the firemen are still at it. This morning's Tribune gave that fire three columns, and "
        "then went on to the city's big plans.\n\n"
        "Nine stops: Lake Street, the Court House and the great hotel beside it, the grain market, a theatre getting "
        "ready for Monday night, the new stores of State Street, the Water Tower across the river, and then, as the "
        "light goes, a small cottage on DeKoven Street. Start on Lake Street."),
    'stops': [
        {'id': 'lake-street', 'anchor': 'sunday_lake_street', 'hour': '14:00',
         'evidence': ['lake-wholesale', 'pullman-raising', 'tribune-oct8', 'weather', 'sunday-walk'],
         'text': (
             "Lake Street at Clark, two in the afternoon. This was once the main street of Chicago. "
             "Until the mid-1860s it was 'the retail center of Chicago', and big wholesale houses still crowd the blocks "
             "between here and the river. Stone fronts with arched windows line both sides, with iron "
             "awnings over the walks and telegraph wires overhead. Some of these buildings once stood lower. From 1859 George M. Pullman, the man "
             "who later built sleeping cars, raised whole blocks of brick and stone on jack-screws to the new street level, "
             "'without even disturbing the operations of business inside'. Today is Sunday, and the stores are shut. In "
             "this morning's Tribune a man who watches land prices said: 'Every body seems to be swelled up with big schemes.' "
             "One block south stands the grandest of those schemes, a hotel of white marble.")},
        {'id': 'sherman-house', 'anchor': 'sunday_sherman_house', 'hour': '14:20',
         'evidence': ['sherman', 'thomas', 'court-house', 'sunday-walk'],
         'text': (
             "The Sherman House, at Clark and Randolph. Francis C. Sherman, who later served as mayor, built his first "
             "hotel on this corner in 1836-37. This one opened in July 1861: six storeys of 'the finest Athens marble, "
             "from the quarries at Lemont', with its main door on Clark Street through a two-storey porch. Its Randolph "
             "Street side looks out over the Court House square. This week it has a famous guest. The conductor Theodore "
             "Thomas and his orchestra are staying here. Tomorrow night they open a season of ten concerts with "
             "'his concert organization of sixty performers'. Across Randolph Street, in the square, a bell of more "
             "than five tons hangs in the Court House tower.")},
        {'id': 'court-house', 'anchor': 'sunday_court_house', 'hour': '14:40',
         'evidence': ['court-house', 'watchman', 'sunday-walk'],
         'text': (
             "Court House Square, the whole block between Randolph, Clark, Washington and LaSalle. Its lawns, trees and "
             "fountain give it 'the appearance of a park', and an iron fence runs round it. The building in the middle holds almost every "
             "city and county office, 'from the jail in its basement to the mayor's quarters'. John M. Van Osdel designed "
             "it in 1853. Since then the city has added wings, a new clock and a bronze bell of 10,849 pounds. Look up at "
             "the cupola. A spiral stair climbs to a balcony 120 feet high, the fire watchman's walk. Tonight the "
             "watchman on duty will be Mathias Schaffer, with his spy-glass. Below him is the telegraph office that sends "
             "the fire engines out. Across LaSalle Street, the grain of the West is bought and sold.")},
        {'id': 'chamber', 'anchor': 'sunday_chamber', 'hour': '15:00',
         'evidence': ['chamber', 'lasalle', 'sunday-walk'],
         'text': (
             "The Chamber of Commerce, on the southeast corner of Washington and LaSalle. Edward Burling designed it, and "
             "it opened on 30 August 1865. Charles Randolph, the president of the Board of Trade, gave the main speech "
             "that day. Inside is a great hall 'decorated with frescoes and paintings', and the business that matters most "
             "here is the Board's trade in grain. The hall is quiet on a Sunday. LaSalle Street around it, a row of stone fronts under mansard roofs, has become "
             "'the home of Insurance Companies and commission merchants', and the banks are moving in close. Two blocks "
             "east, on Washington Street, workmen are busy even today, getting a theatre ready for Monday night.")},
        {'id': 'crosbys', 'anchor': 'sunday_crosbys', 'hour': '15:20',
         'evidence': ['crosbys', 'crosby-tribune', 'crosby-gaslight', 'sunday-walk'],
         'text': (
             "Crosby's Opera House, on the north side of Washington Street between State and Dearborn. Uranus Crosby opened "
             "it in 1865, built by the architect W. W. Boyington: five storeys, a mansard roof, and statues of Painting, "
             "Sculpture, Music and Commerce over the arch. Shops fill the ground floor, and the theatre behind them seats "
             "three thousand. All summer it has been done over, at a cost of about $80,000. This morning's Tribune said "
             "'the whole house, gallery and all, is nearly sold for the first night.' The first night is tomorrow, when "
             "Theodore Thomas opens the season. Late this evening the gas will be lit inside for the first time, "
             "'that its effects might be seen by gaslight'. One block east is the newest shopping street in Chicago.")},
        {'id': 'state-street', 'anchor': 'sunday_state_street', 'hour': '15:40',
         'evidence': ['palmer-state', 'field-leiter', 'palmer-house', 'north-side', 'sunday-walk'],
         'text': (
             "State Street at Washington. Four years ago this stretch held a frame house, an ale store and a "
             "furniture shop. Then Potter Palmer, who had made his first fortune in trade, bought 'three-quarters "
             "of a mile of property along State Street south of Lake' to make it the city's great shopping street. On the "
             "northeast corner is the six-storey store of Field & Leiter, almost 150 feet long on State. Marshall Field "
             "and Levi Leiter moved here from Lake Street, and their clerks treat the ladies who shop here 'like guests "
             "rather than mere customers'. A few blocks south is Palmer's own new hotel, the Palmer House. Across the "
             "river, on the North Side, the oldest and richest families live under great elms.")},
        {'id': 'water-tower', 'anchor': 'sunday_water_tower', 'hour': '16:30',
         'evidence': ['water-works', 'one-pump', 'north-side', 'sunday-walk'],
         'text': (
             "The Water Tower, on Pine Street at Chicago Avenue, on the North Side. It was dedicated with a great "
             "celebration in 1867. Across the street, the Pumping Station draws clean water through a tunnel two miles "
             "out under the lake, far from the 'unspeakably polluted Chicago River'. W. W. Boyington, who also built "
             "Crosby's, designed both in 'castellated Gothic' stone. South of here, toward the river, are the homes of "
             "the old families, 'substantial and elegant, and shaded with grand elms'. For years the Board of Police and "
             "Fire Commissioners has warned that 'the water supply was insufficient'. The whole city depends on this one "
             "set of pumps, and the roof over them is made of wood.")},
        {'id': 'saturday-ruins', 'anchor': 'sunday_van_buren_bridge', 'hour': '17:10',
         'evidence': ['saturday-fire', 'saturday-sunday', 'firemen-tired', 'weather', 'sunday-walk'],
         'text': (
             "The east end of the Van Buren Street bridge, looking across to the West Side. Last night, between ten and eleven, a fire "
             "broke out in Lull & Holmes's planing mill on Canal Street, in a district insurance men call the 'Red Flash'. "
             "By this afternoon four blocks and nearly a million dollars of property were gone. 'The piles of coal and "
             "lumber burned all day on Sunday', and thousands of people came to look. Many of the firemen worked eighteen "
             "hours straight, until three o'clock this afternoon. They are 'nearly exhausted', and some of their equipment "
             "is damaged. No rain has fallen for more than a week, and the wind is still strong from the southwest. Ten "
             "blocks south, on DeKoven Street, a woman has milked her cows for the evening.")},
        {'id': 'dekoven', 'anchor': 'sunday_dekoven', 'hour': '17:45',
         'evidence': ['oleary-place', 'oleary-affidavit', 'party', 'shavings', 'sunday-walk'],
         'text': (
             "137 DeKoven Street, on the West Side, at dusk. This is a neighbourhood of small wooden houses, with 'wood "
             "shavings piled in every barn and under every house'. Patrick and Catherine O'Leary and their five children "
             "live in the back of this cottage, and rent the front to the McLaughlin family. Behind it is a wooden barn, "
             "sixteen by twenty feet, its loft newly filled with hay. Inside are five cows, a calf and a horse. Catherine "
             "O'Leary sells milk to the neighbours. She milked at half past four, and at about seven she will feed the "
             "horse by the fence and shut him in. Tonight the McLaughlins have a party for a cousin just arrived from "
             "Ireland. Mr. McLaughlin is a fiddler, and there will be music. The wind has not dropped.")},
    ],
    'legs': [
        {'story': "One block south on Clark Street, to the corner of Randolph.", 'evidence': ['sherman']},
        {'story': "Across Randolph Street and through the gate into the square.", 'evidence': ['court-house']},
        {'story': "Across the square to the corner of Washington and LaSalle.", 'evidence': ['chamber']},
        {'story': "East along Washington Street, past Clark and Dearborn.", 'evidence': ['crosbys']},
        {'story': "On to the corner of State Street.", 'evidence': ['field-leiter']},
        {'note': "Across the river to the North Side, more than a mile: this leg goes Instantly.", 'mode': 'instantly',
         'evidence': ['water-works']},
        {'note': "Back across the river and south to Van Buren Street, nearly two miles: this leg goes Instantly.",
         'mode': 'instantly', 'evidence': ['saturday-fire']},
        {'note': "Ten blocks south on the West Side, to DeKoven Street: this leg goes Instantly.", 'mode': 'instantly',
         'evidence': ['oleary-place']},
    ],
    'endings': [
        {'id': 'the-barn', 'text': (
            "That night, at about nine, Daniel Sullivan, a drayman sitting on the sidewalk across DeKoven Street, saw "
            "fire in the O'Leary barn. Within thirty minutes it 'was beyond the control of the Fire Department.' In the "
            "Court House cupola Mathias Schaffer saw the glow, judged it too far away, and called the wrong alarm box. "
            "By Monday morning the Court House bell had fallen through the burning building. The Sherman House was "
            "'one of the most complete wrecks of the night', and Crosby's Opera House never opened. At about three in the "
            "morning the pumping works became 'an utter wreck'. Theodore Thomas 'was compelled to run for his life'.\n\n"
            "According to legend, Mrs. O'Leary's cow kicked over a lamp. The historian A. T. Andreas wrote in 1885: "
            "'There is no proof that Mrs. O'Leary is responsible for the fire.' The Great Chicago Fire jaunt begins in that barn.")},
    ],
    'extra_evidence': ['first-seen', 'legend', 'what-burned', 'watchman', 'thomas'],
    'keepsake': ('News & Knowledge', "The Tribune, Sunday morning, 8 October 1871",
                 "'There has scarcely been a time for ten years past when there seemed to be so many schemes of one kind "
                 "or another on foot'."),
}

DIRECTIONS = {
    'opening:opening': ('[warmly]', [
        ('Sunday 8 October 1871, early afternoon.', f'{P} Sunday... 8 October 1871. Early afternoon.'),
        ('and a warm wind is blowing hard', '[lightly] and a warm wind is blowing hard'),
        ('Last night a fire on the West Side', f'{P} Last night a fire on the West Side'),
        ('then went on to the city', '[amused] then went on to the city'),
        ('and then, as the light goes,', f'{P} and then, as the light goes,'),
        ('Start on Lake Street.', f'{P} Start on Lake Street.'),
    ]),
    'stop:lake-street': ('[brightly]', [
        ('Some of these buildings once stood lower.', f'{P} Some of these buildings once stood lower.'),
        ('Today is Sunday, and the stores are shut.', f'{P} [softly] Today is Sunday, and the stores are shut.'),
        ('Every body seems to be swelled up', '[amused] Every body seems to be swelled up'),
        ('One block south stands', f'{P} One block south stands'),
    ]),
    'stop:sherman-house': ('[admiring]', [
        ('This week it has a famous guest.', f'{P} This week it has a famous guest.'),
        ('Tomorrow night they open', '[excited] Tomorrow night they open'),
        ('Across Randolph Street, in the square,', f'{P} Across Randolph Street, in the square,'),
    ]),
    'stop:court-house': ('[measured]', [
        ('Look up at the cupola.', f'{P} Look up at the cupola.'),
        ('Tonight the watchman on duty', f'{P} [quietly] Tonight the watchman on duty'),
        ('Across LaSalle Street,', f'{P} Across LaSalle Street,'),
    ]),
    'stop:chamber': ('[measured]', [
        ('The hall is quiet on a Sunday.', f'{P} [softly] The hall is quiet on a Sunday.'),
        ('Two blocks east, on Washington Street,', f'{P} Two blocks east, on Washington Street,'),
    ]),
    'stop:crosbys': ('[excited]', [
        ('All summer it has been done over,', f'{P} All summer it has been done over,'),
        ('The first night is tomorrow,', f'{P} The first night is tomorrow,'),
        ('Late this evening the gas will be lit', f'{P} [softly] Late this evening the gas will be lit'),
        ('One block east is', f'{P} One block east is'),
    ]),
    'stop:state-street': ('[brightly]', [
        ('Then Potter Palmer,', f'{P} Then Potter Palmer,'),
        ('A few blocks south is', f'{P} A few blocks south is'),
        ('Across the river, on the North Side,', f'{P} [warmly] Across the river, on the North Side,'),
    ]),
    'stop:water-tower': ('[admiring]', [
        ('For years the Board of Police', f'{LP} [seriously] For years the Board of Police'),
        ('The whole city depends on this one set of pumps,', f'{P} The whole city depends on this one set of pumps,'),
        ('and the roof over them is made of wood.', '[quietly] and the roof over them... is made of wood.'),
    ]),
    'stop:saturday-ruins': ('[seriously]', [
        ('By this afternoon four blocks', f'{P} By this afternoon four blocks'),
        ('Many of the firemen worked', f'{P} Many of the firemen worked'),
        ('No rain has fallen for more than a week,', f'{P} No rain has fallen for more than a week,'),
        ('Ten blocks south, on DeKoven Street,', f'{LP} [softly] Ten blocks south, on DeKoven Street,'),
    ]),
    'stop:dekoven': ('[quietly]', [
        ('Behind it is a wooden barn,', f'{P} Behind it is a wooden barn,'),
        ('Tonight the McLaughlins have a party', f'{P} [warmly] Tonight the McLaughlins have a party'),
        ('The wind has not dropped.', f'{LP} [softly] The wind... has not dropped.'),
    ]),
    'ending:the-barn': ('[quietly]', [
        ('Within thirty minutes', f'{P} Within thirty minutes'),
        ('In the Court House cupola', f'{P} In the Court House cupola'),
        ('By Monday morning', f'{LP} [sadly] By Monday morning'),
        ('Theodore Thomas', f'{P} Theodore Thomas'),
        ('According to legend,', f'{LP} [wryly] According to legend,'),
        ('The Great Chicago Fire jaunt begins in that barn.', f'{P} [softly] The Great Chicago Fire jaunt... begins in that barn.'),
    ]),
}
