# SPDX-License-Identifier: GPL-3.0-or-later
"""T-3693, Who Started the Fire?: a case jaunt at 137 DeKoven Street. Four stops on the night
(21:28-21:40, the fire burning), then the inquiry, the legend, the later suspects and the City
Council's verdict of 1997, told over the place with no date. Built by build.py; the order and the
night's hours are L-1871-who-started-3693 (claim 'case-walk')."""

P, LP = '[short pause]', '[long pause]'

DATE = '1871-10-08'

JAUNT = {
    'id': 'who-started-the-fire',
    'title': 'Who Started the Fire?',
    'category': 'Great Fire 1871',
    'menu_rank': 3,
    'hour': 'night',
    'premise': "Sunday night, 8 October 1871: fire in the O'Leary barn. The cow got the blame. Weigh what the O'Learys, their neighbours, the watchman, the inquiry, a boastful reporter and the later sleuths say, and decide who started it. Eight stops.",
    'opening': (
        "JAUNT: WHO STARTED THE FIRE? Sunday night, 8 October 1871, DeKoven Street on the West Side. Everyone knows "
        "the story: Mrs. O'Leary's cow kicked over a lamp and burned Chicago down. The official inquiry found no proof "
        "of it, a reporter later said he and his friends had made it up, and in 1997 the City Council cleared the cow.\n\n"
        "So who did it? Eight stops: the barn, the yard, the party next door, the watchman in the Court House tower, "
        "the inquiry, the legend, the other suspects and the verdict of 1997. Every witness is heard in their own words. "
        "Start across the street from the barn, just as the fire is found."),
    'stops': [
        {'id': 'the-barn', 'anchor': 'case_sullivan_seat', 'hour': '21:30', 'hour_evidence': ['sullivan-affidavit'],
         'evidence': ['sullivan-affidavit', 'first-seen', 'peg-leg', 'legend', 'case-walk'],
         'text': (
             "DeKoven Street, about half past nine on Sunday night. Flames are pouring out of the hayloft of the barn "
             "behind No. 137, the cottage of Patrick and Catherine O'Leary. Daniel Sullivan, a drayman from across the "
             "street, later known as 'Peg Leg', has just crossed over, cried 'Fire, fire,' and gone into the barn, where "
             "he found 'the hay in the loft on fire'. He tried to cut the animals loose, and saved only 'a half-burned "
             "calf'. While the city was still burning, someone said Mrs. O'Leary had been milking when her cow 'kicked "
             "over a lighted lamp'. That story went round the world. Was it true? Start with the woman who owned the cow.")},
        {'id': 'catherine', 'anchor': 'case_oleary_yard', 'hour': '21:35', 'hour_evidence': ['case-walk'],
         'evidence': ['oleary-testimony', 'oleary-affidavit', 'rogan', 'case-walk'],
         'text': (
             "The yard behind the cottage. Catherine O'Leary, who milks five cows and sells the milk, is watching "
             "everything she owns burn. Later she told the inquiry: 'I was in bed myself and my husband and five children "
             "when this fire commenced.' Two men came to the door, and her husband Patrick ran back to the bedroom and said "
             "'Kate the barn is afire.' A neighbour, Dennis Rogan, backed her up. At half past eight he had found the couple "
             "already in bed, and she told him it was because of a 'sore foot'. In a sworn statement a week later, the "
             "O'Learys said she milked at 4:30 and fed the horse at about seven, and 'She had no lighted lamp in the house "
             "or barn that evening.' But in the front of this cottage, there was a party.")},
        {'id': 'the-party', 'anchor': 'case_oleary_front', 'hour': '21:40', 'hour_evidence': ['case-walk'],
         'evidence': ['oleary-testimony', 'mclaughlin', 'party', 'case-walk'],
         'text': (
             "The front of No. 137, on DeKoven Street. The O'Learys rent these two front rooms to the McLaughlin family, "
             "and tonight they have company: young people celebrating 'the arrival of a cousin from Ireland'. Mr. "
             "McLaughlin plays the fiddle, and through the wall Catherine O'Leary heard it: 'There was a little music "
             "there.' Afterwards a neighbour across the street, Mrs. White, told her that someone from the party had gone "
             "to the barn to milk her cows. Why? 'Some said it was for oysters.' Catharine McLaughlin swore that no one "
             "from her family went to the barn, and that all were in the house when the fire broke out. They drank beer, "
             "Andreas wrote, 'but had no whisky or milk punch'. More than a mile away, in the Court House tower, the "
             "watchman has seen a glow.")},
        {'id': 'the-alarm', 'anchor': 'case_court_tower', 'hour': '21:28', 'hour_evidence': ['box-342'],
         'evidence': ['watchman', 'box-342', 'case-walk'],
         'text': (
             "The Court House cupola, 9:28 by the watchman's own account. Mathias Schaffer, on duty up here, sees the light "
             "of a fire to the southwest. Through his spy-glass he judges it near Canalport Avenue and Halsted Street, and "
             "signals the operator below, William J. Brown, to strike Box 342. That box is 'a point in the direction of "
             "the fire, but a mile beyond it.' Soon Schaffer sees the fire is closer, but no corrected alarm goes out, and "
             "engines that would have answered it stay in their houses. The historian A. T. Andreas called it 'a fatal "
             "mistake'. Something else is odd: no one near the barn pulled an alarm box at all. The inquiry noticed: 'If "
             "any person set the fire, either by accident or design, he was careful not to give the alarm.'")},
        {'id': 'the-inquiry', 'anchor': 'case_oleary_front', 'evidence': ['board-finding', 'oleary-testimony'],
         'text': (
             "Back on DeKoven Street, weeks later. On 23 November 1871 the Board of Police and Fire Commissioners opened "
             "an inquiry into how the fire began, and about fifty witnesses came. Catherine O'Leary was the star witness. "
             "She had lost her cows, her horse and her wagon, and 'Never had five cents insurance'. The Board found that "
             "the fire started in the O'Leary barn, and could say no more: 'There is no proof that any person had been in "
             "the barn after nightfall that evening.' A spark from a chimney, or a person? 'we are unable to determine.' "
             "The report was attacked, not for clearing her, but for covering up the Fire Department's mistakes. Andreas "
             "called it 'little more than an attempt to quiet' the complaints. Mrs. O'Leary was cleared on paper. The "
             "story was another matter.")},
        {'id': 'the-cow', 'anchor': 'case_barn_alley', 'evidence': ['legend', 'scapegoat', 'ahern'],
         'text': (
             "The alley behind the barn. While the city still burned, 'some now-forgotten tongue' said Mrs. O'Leary had "
             "been milking when the cow kicked over a lamp. Cartoonists drew her as a comic, hapless figure, and later "
             "painters named the cow Daisy. The Chicago History Museum explains why the story stuck: she could be made to "
             "stand for 'careless building, sloppy conduct, and a shiftless immigrant underclass', and blaming her fed "
             "'anti-Catholic, anti-immigrant, and possibly anti-female' feeling. Then Michael Ahern, who had covered the "
             "fire for the Chicago Republican, boasted in the Tribune that he and two friends made the whole thing up. The "
             "museum dates his boast to the fire's fortieth anniversary; other accounts say 1893. A colleague later said he "
             "had written Ahern's piece himself. If not the cow, who?")},
        {'id': 'other-suspects', 'anchor': 'case_sullivan_seat', 'evidence': ['peg-leg', 'cohn', 'meteor', 'sullivan-affidavit'],
         'text': (
             "Across the street, a few lots east, where Daniel Sullivan said he was sitting. In 1997 a lawyer and amateur "
             "historian, Richard Bales, checked his story against the land records. From here, he argued, another house "
             "would have blocked the view, and a man with a wooden leg could not have covered the 193 feet to the barn as "
             "fast as Sullivan said. Bales thought Sullivan started the fire himself, perhaps while feeding his own cow. A "
             "Tribune writer, Anthony DeBartolo, pointed instead to Louis M. Cohn, whose bequest to Northwestern University "
             "in 1944 came with a story: he and Mrs. O'Leary's son and other boys were 'shooting dice in the hayloft' when "
             "one knocked over a lantern. Some even blame a meteor. Carl Smith, a historian, calls them all 'interesting, "
             "but ultimately unprovable theory'.")},
        {'id': 'the-council', 'anchor': 'case_fire_academy', 'evidence': ['exoneration', 'fire-academy'],
         'text': (
             "The corner of Jefferson and DeKoven, today. By the 1880s the O'Leary cottage was gone. Since 1961 the Chicago "
             "Fire Academy, where the city trains its firefighters, has stood on the site, with a sculpture of a flame by "
             "its entrance. In 1971, the fire's hundredth year, the city's business association cleared Mrs. O'Leary and "
             "blamed Sullivan instead. Here, in October 1997, a City Council committee held a hearing, half serious and half "
             "fun. Aldermen William Beavers and Edward Burke decided that she and her cow 'had been unfairly maligned', and "
             "the full council passed a resolution clearing them of 'all blame'. Her great-great-granddaughter, Nancy "
             "Knight Connolly, said: 'We always knew that she was innocent'. The city had given its verdict. The evidence "
             "had not changed.")},
    ],
    'legs': [
        {'story': "Across DeKoven Street and round the side of the cottage to the yard.", 'evidence': ['oleary-place']},
        {'story': "Back round the cottage to its front door on DeKoven Street.", 'evidence': ['party']},
        {'note': "Up to the Court House cupola, more than a mile to the northeast: this leg goes Instantly.", 'mode': 'instantly',
         'evidence': ['watchman']},
        {'note': "Back to DeKoven Street, and on to November: this leg goes Instantly.", 'mode': 'instantly',
         'evidence': ['board-finding']},
        {'story': "Round to the alley behind the cottage, where the barn stood.", 'evidence': ['oleary-place']},
        {'story': "Out to DeKoven Street, across, and a few lots east.", 'evidence': ['sullivan-affidavit']},
        {'story': "West along DeKoven Street to the corner of Jefferson.", 'evidence': ['fire-academy']},
    ],
    'endings': [
        {'id': 'your-verdict', 'text': (
            "So who started the fire? Here is the case as it stands.\n\n"
            "Catherine O'Leary swore she was in bed, and a neighbour found her there at half past eight with a sore foot. "
            "The inquiry believed her, and in 1997 the City Council cleared her and her cow.\n\n"
            "Someone from the McLaughlin party may have gone out for milk, as Mrs. White heard. Catharine McLaughlin "
            "swore no one did.\n\n"
            "Daniel Sullivan was first into the barn. Richard Bales says his story does not fit the ground. Sullivan swore "
            "he saw the fire from across the street and ran in to save the animals.\n\n"
            "Louis Cohn's story of a dice game came out only after his death, and his own will does not mention it.\n\n"
            "A spark from a chimney, on 'that windy night', is still possible.\n\n"
            "The Board could not decide, and neither could Andreas. 'It is highly unlikely that we will ever have "
            "definitive knowledge of the cause of the fire.' Who do you think it was, and what would it take to be sure?")},
    ],
    'extra_evidence': [],
    'keepsake': ('News & Knowledge', "The Board's finding, 1871",
                 "'Whether it originated from a spark blown from a chimney on that windy night, or was set on fire by "
                 "human agency, we are unable to determine.'"),
}

DIRECTIONS = {
    'opening:opening': ('[intrigued]', [
        ('Everyone knows the story:', f'{P} Everyone knows the story:'),
        ('The official inquiry found no proof', f'{P} [wryly] The official inquiry found no proof'),
        ('So who did it?', f'{LP} So... who did it?'),
        ('Start across the street', f'{P} Start across the street'),
    ]),
    'stop:the-barn': ('[urgently]', [
        ('He tried to cut the animals loose,', f'{P} He tried to cut the animals loose,'),
        ('While the city was still burning,', f'{LP} [quietly] While the city was still burning,'),
        ('Was it true?', f'{P} Was it true?'),
    ]),
    'stop:catherine': ('[softly]', [
        ('Later she told the inquiry:', f'{P} Later she told the inquiry:'),
        ('A neighbour, Dennis Rogan, backed her up.', f'{P} A neighbour, Dennis Rogan, backed her up.'),
        ('But in the front of this cottage,', f'{LP} [intrigued] But in the front of this cottage,'),
    ]),
    'stop:the-party': ('[warmly]', [
        ('Afterwards a neighbour across the street,', f'{P} [conspiratorially] Afterwards a neighbour across the street,'),
        ('Why?', f'{P} Why?'),
        ('Catharine McLaughlin swore', f'{P} [seriously] Catharine McLaughlin swore'),
        ('More than a mile away,', f'{LP} More than a mile away,'),
    ]),
    'stop:the-alarm': ('[measured]', [
        ('Soon Schaffer sees the fire is closer,', f'{P} Soon Schaffer sees the fire is closer,'),
        ('Something else is odd:', f'{LP} [intrigued] Something else is odd:'),
    ]),
    'stop:the-inquiry': ('[measured]', [
        ('The Board found that', f'{P} The Board found that'),
        ('A spark from a chimney, or a person?', f'{P} A spark from a chimney... or a person?'),
        ('Mrs. O\'Leary was cleared on paper.', f'{LP} Mrs. O\'Leary was cleared on paper.'),
        ('The story was another matter.', '[wryly] The story was another matter.'),
    ]),
    'stop:the-cow': ('[wryly]', [
        ('The Chicago History Museum explains', f'{P} [seriously] The Chicago History Museum explains'),
        ('Then Michael Ahern,', f'{LP} [amused] Then Michael Ahern,'),
        ('If not the cow, who?', f'{P} If not the cow... who?'),
    ]),
    'stop:other-suspects': ('[intrigued]', [
        ('Bales thought Sullivan started the fire himself,', f'{P} Bales thought Sullivan started the fire himself,'),
        ('A Tribune writer,', f'{P} A Tribune writer,'),
        ('Some even blame a meteor.', f'{P} [amused] Some even blame a meteor.'),
    ]),
    'stop:the-council': ('[warmly]', [
        ('Here, in October 1997,', f'{P} Here, in October 1997,'),
        ('The city had given its verdict.', f'{LP} [quietly] The city had given its verdict.'),
        ('The evidence had not changed.', f'{P} The evidence had not changed.'),
    ]),
    'ending:your-verdict': ('[measured]', [
        ('Here is the case as it stands.', f'{P} Here is the case as it stands.'),
        ('Who do you think it was,', f'{LP} [softly] Who do you think it was,'),
    ]),
}
