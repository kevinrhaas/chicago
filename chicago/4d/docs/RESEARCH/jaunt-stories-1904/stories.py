# SPDX-License-Identifier: GPL-3.0-or-later
"""The ten 1904 story jaunts: their words, their stops and who plays each scene (build.py).

Every jaunt is set on one day, Monday 21 November 1904, in the fall. What happened before that
day is told as the street remembers it; what happened after is the ending. Each stop is staged:
the people of the house with a card in the town play themselves, and everyone else is an
unnamed figure in period dress, named in the cast for who they stand for. No word anyone says
is staged; the narrator tells the stop.

`h` is build.py: h.at(structure, a, b) is a mark `a` metres out from the structure's front
toward its framing stand and `b` metres along it; h.cast/h.extra build castmates; h.beat a beat.
"""


def jaunts(h):
    at, P, cast, extra, beat, anchor = h.at, h.P, h.cast, h.extra, h.beat, h.anchor
    out = []

    # ── 1 ── Field and Mrs. Caton ───────────────────────────────────────────────────────────
    F, C, A = 'marshall_field_house_1905_prairie', 'house_1910_calumet', 'house_1900_calumet'
    out.append(dict(
        id='field-and-mrs-caton', title='The Merchant and Mrs. Caton', hour='morning',
        premise="Three days after Arthur Caton died in a New York hotel, the whole street is whispering about his widow Delia and the richest man in Chicago, whose house stands just across the alley.",
        opening="JAUNT: THE MERCHANT AND MRS. CATON. Monday morning, 21 November 1904. A telegram has come from New York, and the blinds are down in a house on Calumet Avenue.\n\nFour stops, on foot, from the widow's door, through the back yards the servants share, to the front steps of Marshall Field, the merchant prince of Chicago. Everybody on Prairie Avenue knows this story. Nobody says it out loud. Thirty years of dinners, voyages and rumours are about to come to an end, and this morning the only people talking are the ones who carry the coal.\n\nStart at Calumet Avenue, at the house with the drawn blinds.",
        keepsake=('Neighbors', 'A Widow\'s Calling Card', 'An interpretive card of the Caton and Field households in November 1904, not a historical artifact.'),
        extra_evidence=['london'],
        stops=[
            dict(id='widow', dest=('structure', C),
                 text="Calumet Avenue, behind Prairie. This is the Caton house, and its blinds are drawn. On Friday Arthur J. Caton died at New York's Waldorf-Astoria hotel, and nobody can quite say of what. \"Some said he succumbed to liver failure. Others ascribed the demise to peritonitis.\" A newspaper downstate will hint that he took his own life. He was a judge's son, a lawyer who loved golf and polo and bred horses and dogs on the family farm. His wife Delia, a hardware heiress he married in 1876, gave the best parties in town: Arthur Meeker's mother \"always declared that nobody ever gave such wonderful parties as Delia Caton\". There were no children. This morning there is a widow, a house full of servants, and a caller on the steps. Go round the back, to the yards between Calumet and Prairie.",
                 evidence=['caton-death', 'caton-family', 'caton-parties'],
                 links=[('structure', C, 'The Caton house')],
                 caption="A maid opens the Caton door to an early caller, and the coachman waits at the curb with his hat in his hand.",
                 cast=lambda: [
                     extra('caton_maid', 'maid_1904', 'A maid of the Caton house (no card in the town; an unnamed figure)', at(C, 1.6, 0.6), face=at(C, 9, 0), hidden=True,
                           beats=[beat(4, show=True), beat(9, greet=True), beat(10, talk=True), beat(22, talk=False), beat(26, hide=True)]),
                     extra('caton_caller', 'gentleman_1904', 'A caller leaving his card (unnamed)', at(C, 10, 9),
                           beats=[beat(0, walk=[at(C, 9, 3), at(C, 3.4, 0.8)], pace='slow'), beat(9, face='caton_maid', talk=True), beat(21, talk=False),
                                  beat(24, walk=[at(C, 9, 1), at(C, 9.5, -12)], pace='slow')]),
                     extra('caton_coachman', 'coachman_livery_1904', 'The Caton coachman (no card in the town; an unnamed figure)', at(C, 8.6, -4.5), face=at(C, 1, 0)),
                 ]),
            dict(id='yards', dest=('structure', A),
                 text="The back yards, where Calumet meets Prairie at the rear fence. Turn round and the Field house is right there, its coach house on the alley. The servants of the two houses have shared this ground for years, and they have heard the talk. Arthur Meeker, who grew up on this street, wrote it down: \"it was even absurdly asserted that an underground tunnel connected the Caton house on Calumet with the Field house on Prairie, which was just in front of it, or just back.\" Meeker called it absurd, and it was. But a society diarist recorded that \"Delia sometimes traveled to Europe with Marshall Field without Arthur accompanying them.\" Now Arthur is dead, Field's wife has been dead eight years, and a laundress from the Field house is leaning on the fence. Walk on to Prairie Avenue and find the man himself.",
                 evidence=['tunnel', 'europe', 'nannie', 'field-staff'],
                 links=[('structure', F, 'The Marshall Field house'), ('person', 'pa1904_field_marshall_c1900_karolina_hall', 'Karolina Hall')],
                 caption="Karolina Hall comes over from the Field yard to the fence, where a Caton maid is waiting with the news.",
                 cast=lambda: [
                     cast('pa1904_field_marshall_c1900_karolina_hall', at(A, 42, 2),
                          beats=[beat(0, walk=[at(A, 30, 3), at(A, 15.2, -5.4)], pace='brisk'), beat(19, face='caton_laundress', talk=True), beat(33, talk=False)]),
                     extra('caton_laundress', 'maid_1904', 'A Caton laundress (no card in the town; an unnamed figure)', at(A, 4, -12),
                           beats=[beat(1, walk=[at(A, 9, -9), at(A, 13.8, -6.6)], pace='walk'), beat(14, face='pa1904_field_marshall_c1900_karolina_hall'), beat(20, talk=True), beat(34, talk=False)]),
                     cast('pa1904_field_marshall_c1900_maggie_fitzsimmons', at(A, 36, 7), face=at(A, 14, -6)),
                 ]),
            dict(id='field', dest=('structure', F),
                 text="1905 Prairie, the Marshall Field house: built in 1876 for some $2 million, \"the first in Chicago to be completely wired for electricity\". Field is the richest merchant in the city. Years ago he proposed to his first wife by jumping aboard her train as it left Chicago; one account says that \"Mrs. Field led Marshall Field a hell-on-earth life\", and Nannie Field died in France in 1896. Meeker put the rest plainly: \"he fell in love with his friend's wife years before he was able to marry her.\" And: \"In the Nineties, divorce was unthinkable: they had to wait for him (Arthur Caton) to die, which, distressingly, he didn't do until 1904.\" That was Friday. Thomas Benson, the butler, has the door; John Dunford, the coachman, comes round from the stable. The house will be razed in 1955.",
                 evidence=['field-children', 'nannie', 'fell-in-love', 'field-staff', 'field-razed', 'field-rich'],
                 links=[('person', 'pa1904_field_marshall', 'Marshall Field'), ('person', 'pa1904_field_marshall_c1900_thomas_benson', 'Thomas Benson'), ('person', 'pa1904_field_marshall_c1900_john_dunford', 'John Dunford')],
                 caption="Marshall Field comes out of his door, and stops on the steps to look east, toward Calumet Avenue, before his coachman reaches him.",
                 cast=lambda: [
                     cast('pa1904_field_marshall', at(F, 1.4, 0), face=at(F, 9, 0), hidden=True,
                          beats=[beat(3, show=True), beat(5, walk=[at(F, 4.2, 0.6)], pace='slow'), beat(10, heading=h.hd(at(F, 4, 0), at(F, -30, 0))), beat(19, face='pa1904_field_marshall_c1900_john_dunford'), beat(23, walk=[at(F, 11, 1.5)], pace='slow')]),
                     cast('pa1904_field_marshall_c1900_thomas_benson', at(F, 1.8, -1.6), face=at(F, 9, 0)),
                     cast('pa1904_field_marshall_c1900_john_dunford', at(F, 9, -14),
                          beats=[beat(6, walk=[at(F, 9.5, -5), at(F, 9.5, -0.3)], pace='walk'), beat(18, face='pa1904_field_marshall')]),
                 ]),
            dict(id='talk', dest=('anchor', 'field_house'),
                 text="From up the street the Field house looks like any other on the row. It is not. Field never liked making speeches, and one night at one of the Catons' grand dinners he was called on to say a few words. Delia sprang to her feet and spoke for him: \"Mr. Field just wants me to remind you that the White Sale starts next Monday.\" It was a joke about his store, made by another man's wife, at her husband's table, and the guests who told it afterwards told it as the night everybody saw how close those two were. The ladies passing the Field house this morning are not looking at it, and they are talking about nothing else. Arthur Caton is not yet buried. Everyone can guess what happens next, and nobody can say it.",
                 evidence=['white-sale', 'caton-parties', 'london'],
                 links=[('source', SRC_SECOND, 'The Second Mrs. Field')],
                 caption="Two ladies of the street walk past the Field house with their heads together, and do not look at it.",
                 cast=lambda: [
                     extra('lady_left', 'lady_1904', 'A lady of the street (unnamed)', P(1409.8, -3318),
                           beats=[beat(0, walk=[P(1410.6, -3340), P(1411.2, -3372)], pace='slow'), beat(1, talk=True)]),
                     extra('lady_right', 'lady_1904', 'A second lady of the street (unnamed)', P(1411.4, -3317),
                           beats=[beat(0, walk=[P(1412.2, -3340), P(1412.8, -3372)], pace='slow')]),
                 ]),
        ],
        legs=[
            dict(story="Through the gap to the rear yards: the Caton fence on one side, Marshall Field's coach house on the other.", evidence=['tunnel'], story_evidence=['tunnel']),
            dict(story="Round by the side path to Prairie Avenue and the front of 1905, the house the gossip pointed at.", evidence=['field-children'], story_evidence=['tunnel']),
            dict(story="North along the walk to look back at the Field house the way the neighbours do.", evidence=['white-sale'], story_evidence=['white-sale']),
        ],
        endings=[dict(id='london', text="End of the walk. They waited less than a year. In 1905 they married in London, at St. Margaret's, Westminster; the licence gave Delia as 46 and Field as 70. \"The ceremony was quiet, and attended only by a few friends.\" They came home to Chicago as man and wife, and in January 1906 Marshall Field was dead of pneumonia, caught on a New Year's golf course with Robert Todd Lincoln. After thirty years of waiting they had a few months. Delia got $1 million and the house, moved to Washington, where her mansion was called the Pink Palace, and lived until 1937.")],
    ))

    # ── 2 ── The divorce at 1612 ────────────────────────────────────────────────────────────
    G, N8, S6, E3 = 'goodman_house_1612_prairie', 'house_1608_prairie', 'house_1616_prairie', 'house_1613_prairie'
    out.append(dict(
        id='scandal-at-1612', title='The Scandal at 1612 Prairie', hour='afternoon',
        premise="A carriage-maker's showplace has become the most talked-about house on the block: a society divorce, a judge's order, a violin in a broken automobile, and a small boy in the middle of it all.",
        opening="JAUNT: THE SCANDAL AT 1612 PRAIRIE. A Monday afternoon in November 1904, at the quiet north end of Prairie Avenue.\n\nFour stops along one short block. The house at 1612 has been a showplace for twenty years. This year it is a battlefield. A husband has gone to court, a judge has handed the house to the wife, and in November the husband stood up in open court and said things about her that the whole city has now read in the Tribune. The neighbours keep their curtains closed and their ears open.\n\nStart next door, where you can see the house the way it used to be.",
        keepsake=('Neighbors', 'The 1612 Court Papers', 'An interpretive card of the Brown divorce of 1904 and 1905 as the Tribune reported it, not a historical artifact.'),
        extra_evidence=['brown-arrest', 'brown-sale', 'brown-decree'],
        stops=[
            dict(id='showplace', dest=('structure', N8),
                 text="1608 Prairie, and beside it the big square house at 1612. Twenty years ago it belonged to a Studebaker, of the Studebaker Brothers carriage works, and it was the brightest house on the street. In February 1884 some two hundred guests came here from a family wedding, and \"The large residence was brilliantly illuminated, and every room was elaborately decorated with smilax and cut flowers.\" A society column of 1887 noticed the traffic: \"Morning and night, a showy turnout is noticed before the squarely-built house, with the number 1612 over the portals.\" A carriage-maker's house should have the finest carriages at its door, and it did. Look at it now. No turnout stands at the curb this afternoon. A maid from next door is watching it from her steps. Walk to the gate of 1612.",
                 evidence=['studebaker-1884', 'studebaker-1887'],
                 links=[('structure', G, '1612 Prairie')],
                 caption="A maid at 1608 sweeps her steps and keeps one eye on the house next door.",
                 cast=lambda: [
                     extra('maid_1608', 'maid_1904', 'A maid at 1608 Prairie (unnamed)', at(N8, 2.6, 0.2), face=at(G, 3, 0),
                           beats=[beat(6, heading=h.hd(at(N8, 2.6, 0.2), at(N8, 9, 0))), beat(14, face=at(G, 3, 0))]),
                 ]),
            dict(id='decree', dest=('structure', G),
                 text="1612 Prairie. The Tribune has the story, and so does everybody else. Last May the husband, Charles E. Brown, filed a bill for divorce. His wife Catherine is 27, \"the daughter of Gen. Graves, a wealthy resident of Buffalo\". The grounds were \"Habitual drunkenness and statutory charges\". Then Judge Tuley gave Mrs. Brown possession of this house, where she and her husband and their son had lived, and $200 a month while the suit was pending. So the wife holds the fortress and the husband is outside it. Behind those windows live a woman the papers have made famous and a small boy. The house will stand until it is razed circa 1960. Step next door and hear what the husband said in November.",
                 evidence=['brown-suit', 'goodman-razed'],
                 links=[('source', CGY_SRC, 'The 1612 Prairie occupants')],
                 caption="A lady comes out onto the steps of 1612, looks up and down the street, and goes back in before anyone can stop her.",
                 cast=lambda: [
                     extra('catherine_brown', 'lady_1904', 'Catherine G. Brown (no card in the town; an unnamed figure plays her)', at(G, 1.5, 0), face=at(G, 9, 0), hidden=True,
                           beats=[beat(4, show=True), beat(6, walk=[at(G, 3.6, 0.4)], pace='slow'), beat(10, heading=h.hd(at(G, 3.6, 0), at(G, 9, 14))), beat(14, heading=h.hd(at(G, 3.6, 0), at(G, 9, -14))),
                                  beat(19, walk=[at(G, 1.5, 0)], pace='brisk'), beat(22, hide=True)]),
                     extra('brown_maid', 'maid_1904', 'A maid of 1612 (unnamed)', at(G, 1.9, -1.5), face=at(G, 9, 0), hidden=True,
                           beats=[beat(5, show=True), beat(21, hide=True)]),
                 ]),
            dict(id='charges', dest=('structure', S6),
                 text="1616 Prairie, the next door south, where the neighbours read the Tribune with their coffee. In November Mr. Brown went back to court and charged that his wife \"had conducted herself in a disgraceful manner, had been habitually intoxicated, and had done many freakish things, such as playing a violin in a broken automobile while a man pushed the machine along a public highway, and dancing about the rear of their home clothed only in a nightrobe.\" There was more. He named a man: \"E. C. Edsall, an automobile salesman.\" With Edsall, the husband charged, she ran off to an eastern summer resort and later to New York City. It is the most delicious scandal on Prairie Avenue in years, and two maids on these steps are making the most of it. But a divorce is not only about two people. Look for the boy.",
                 evidence=['brown-november', 'brown-edsall'],
                 caption="Two maids on the steps of 1616 share the newspaper and look over at 1612.",
                 cast=lambda: [
                     extra('maid_1616', 'maid_1904', 'A maid at 1616 Prairie (unnamed)', at(S6, 2.8, 0.7), face=at(G, 4, 0),
                           beats=[beat(2, talk=True), beat(16, face='cook_1616'), beat(30, talk=False)]),
                     extra('cook_1616', 'cook_1904', 'A cook at 1616 Prairie (unnamed)', at(S6, 2.8, -0.9), face='maid_1616',
                           beats=[beat(17, talk=True), beat(30, talk=False), beat(31, face=at(G, 4, 0))]),
                 ]),
            dict(id='boy', dest=('structure', E3),
                 text="Across the street at 1613, look back at the west side of the block. The boy is Charles Edward Brown, the couple's only son, and he is the real prize in this fight. A nurse walks him along the sidewalk past his own front door; his mother has the house, and his father wants it back, and wants him. The court has not decided. In the newspapers he is a line at the end of every story. On this walk he is the only person in the whole affair who has done nothing at all. The Tribune will report the end of it in March 1905. By then the house, the boy and the woman will each have gone a different way.",
                 evidence=['brown-decree', 'brown-suit'],
                 caption="A nurse walks a small boy along the far sidewalk past the door of 1612, and he stops to look up at it.",
                 cast=lambda: [
                     extra('charles_edward', 'child_boy_1904', 'Charles Edward Brown, the son (no card in the town; an unnamed figure plays him)', at(N8, 10, 10),
                           beats=[beat(0, walk=[at(G, 10, 2)], pace='slow'), beat(9, face=at(G, 2, 0)), beat(15, walk=[at(S6, 10, -10)], pace='slow')]),
                     extra('nurse_1612', 'maid_1904', 'A nurse of the Brown household (unnamed)', at(N8, 10.6, 11),
                           beats=[beat(0, walk=[at(G, 10.6, 3)], pace='slow'), beat(9, face='charles_edward'), beat(14, walk=[at(S6, 10.6, -9)], pace='slow')]),
                 ]),
        ],
        legs=[
            dict(story="A few steps south to the gate of 1612, the house the whole street is watching.", evidence=['brown-suit'], story_evidence=['brown-suit']),
            dict(story="Next door south, to the neighbours with the morning's Tribune.", evidence=['brown-november'], story_evidence=['brown-november']),
            dict(story="Across Prairie Avenue to look back at the west side of the block.", evidence=['brown-decree'], story_evidence=['brown-decree']),
        ],
        endings=[dict(id='march', text="End of the walk. After a bitter fight, early in 1905, the husband won: the divorce, the house on Prairie Avenue and the custody of the boy. On 8 March 1905 he sold the house to Charles Palmerston Anderson, the Episcopal bishop of Chicago. That same week the Tribune found Catherine Brown in a police cell, arrested at 3667 Wabash Avenue, where the police said she had been living as Kittie Casey, and fined $85. \"I am penniless,\" she said. \"I cannot pay the fine.\" In her cell she said: \"It's all because a woman is jealous of me, I guess.\" The general's daughter from Buffalo had held 1612 Prairie for less than a year.")],
    ))

    # ── 3 ── Frances Glessner Lee at 1700 ───────────────────────────────────────────────────
    L, GG = 'glessner_lee_house_1700_prairie', 'george_glessner_house_1706_prairie'
    GD = anchor('glessner_tour_door')
    HB = anchor('glessner_tour_hall_bow')
    out.append(dict(
        id='frances-glessner-lee', title='The Daughter Who Made Things', hour='morning',
        premise="At 26, Frances Glessner Lee has a lawyer husband, two children and a fine new house her parents built. Her hands want something else, and a block south her mother has just found it.",
        opening="JAUNT: THE DAUGHTER WHO MADE THINGS. A grey Monday morning, 21 November 1904, at the north end of the Glessner family's world.\n\nFour stops, from the twin houses the Glessners built for their two children, down to the great stone house at Eighteenth Street where the daughter grew up. Frances Glessner Lee is 26. She was taught at home, married at 19, and she is the last person on this street anyone would expect to change the way murders are investigated. Watch her hands.\n\nStart at 1700 Prairie, at the door of the young Lees.",
        keepsake=('Neighbors', 'A Honeybee Hallmark', 'An interpretive card of Frances Glessner Lee and her mother in 1904, not a historical artifact.'),
        extra_evidence=['lee-later', 'nutshell-made', 'lee-nutshell'],
        stops=[
            dict(id='lees', dest=('structure', L),
                 text="1700 Prairie, the north half of a pair of twin townhouses. John and Frances Glessner built them for their two children, and the young families moved in in 1902. This one belongs to their daughter Frances and her husband Blewett Lee, a lawyer. She was born in 1878, the youngest child and only daughter, \"tutored at home\" in the stone house down the street, and she toured Europe at 18. On 9 February 1898, at 19, she married Lee in her parents' house; the cook baked the wedding cake. Now there is a boy, John, who is six, and a baby girl born last year. Watch the front door. Her husband is leaving for his office, and she stays on the step. Next door lives her brother.",
                 evidence=['lee-twins', 'fanny-young', 'lee-at-19', 'mattie-cake', 'twins-1902'],
                 links=[('person', 'pa1904_lee_frances_glessner', 'Frances Glessner Lee'), ('person', 'pa1904_lee_blewett', 'Blewett Lee')],
                 caption="Blewett Lee comes down his steps and sets off for his office; his wife and their son stay at the door.",
                 cast=lambda: [
                     cast('pa1904_lee_blewett', at(L, 1.6, 0.5), face=at(L, 9, 0), hidden=True,
                          beats=[beat(2, show=True), beat(5, walk=[at(L, 4, 0.5), at(L, 10, 1.5), at(L, 10.6, 30)], pace='brisk')]),
                     cast('pa1904_lee_frances_glessner', at(L, 1.5, -0.6), face=at(L, 9, 0), hidden=True,
                          beats=[beat(3, show=True), beat(6, walk=[at(L, 3, -0.6)], pace='slow'), beat(12, face=at(L, 10.6, 25)), beat(26, face=at(L, 9, 0))]),
                     cast('pa1904_lee_john_glessner', at(L, 2.2, -1.6), face=at(L, 9, 0), hidden=True,
                          beats=[beat(4, show=True), beat(13, face=at(L, 10.6, 25))]),
                 ]),
            dict(id='george', dest=('structure', GG),
                 text="1706 Prairie, the other twin, shares a wall with the Lees. Here lives her brother George Glessner, his wife Alice and their four children, Elizabeth, Frances, John and the new baby, Emily, born this year. George takes photographs the way other men breathe; he photographed these very houses going up in 1901, and in 1902 he was made a manager at International Harvester. His is the kind of life the street understands: a job, a camera, a nursery full of children. His sister's life is supposed to look the same from the sidewalk, and it does. But her son will say, years later, that what broke her marriage was her \"creative urge coupled with high manual dexterity—the desire to make things—which [Lee] did not share.\" Walk south a block to find out where that urge came from.",
                 evidence=['george-family', 'twins-1902', 'lee-son'],
                 links=[('person', 'pa1904_glessner_george_m', 'George M. Glessner'), ('person', 'pa1904_glessner_alice_hamlin', 'Alice Hamlin Glessner')],
                 caption="George and Alice Glessner come out with their children for a morning walk.",
                 cast=lambda: [
                     cast('pa1904_glessner_george_m', at(GG, 1.6, 0.4), face=at(GG, 9, 0), hidden=True,
                          beats=[beat(3, show=True), beat(6, walk=[at(GG, 4.5, 0.4), at(GG, 10, 1)], pace='slow'), beat(15, face='pa1904_glessner_elizabeth')]),
                     cast('pa1904_glessner_alice_hamlin', at(GG, 1.5, -0.6), face=at(GG, 9, 0), hidden=True,
                          beats=[beat(4, show=True), beat(7, walk=[at(GG, 4.5, -0.6), at(GG, 10, -0.4)], pace='slow'), beat(16, talk=True), beat(26, talk=False)]),
                     cast('pa1904_glessner_elizabeth', at(GG, 2.4, 1.6), face=at(GG, 9, 0), hidden=True,
                          beats=[beat(5, show=True), beat(8, walk=[at(GG, 10.2, 2.4)], pace='walk')]),
                     cast('pa1904_glessner_frances', at(GG, 2.4, -1.8), face=at(GG, 9, 0), hidden=True,
                          beats=[beat(6, show=True), beat(9, walk=[at(GG, 10.4, -1.8)], pace='walk')]),
                     cast('pa1904_glessner_john', at(GG, 3, 0), face=at(GG, 9, 0), hidden=True,
                          beats=[beat(7, show=True), beat(10, walk=[at(GG, 9.8, 0.4)], pace='slow')]),
                 ]),
            dict(id='mother', dest=('anchor', 'glessner_tour_door'),
                 text="1800 Prairie, the house she grew up in, built like a fortress at Eighteenth Street. Her mother, Frances Glessner, is 56, and this year she has done something few ladies of Prairie Avenue would do. In 1904 she set up a workbench in the basement and began to make silver with her own hands. She takes lessons from Annibale Fogliata, a master jewelry craftsman of Hull House, and from Madeline Yale Wynne, a Chicago silversmith. Every piece she makes carries her mark, \"a G encircling a honeybee\", because she keeps bees as well. She has kept a journal since 1879; she misses nothing. The daughter comes to the door. Inside is a mother who has decided, at 56, to learn a trade.",
                 evidence=['silversmith', 'journal-silver', 'frances-born'],
                 links=[('person', 'glessner_frances_m', 'Frances M. Glessner'), ('person', 'pa1904_lee_frances_glessner', 'Frances Glessner Lee')],
                 caption="Frances Glessner Lee comes down the walk to her mother's door, and her mother opens it herself.",
                 cast=lambda: [
                     cast('pa1904_lee_frances_glessner', P(GD[0] + 2.5, GD[1] + 22), beats=[beat(0, walk=[P(GD[0] - 0.4, GD[1] + 6), P(GD[0] - 2.4, GD[1] + 0.2)], pace='walk'), beat(14, face='glessner_frances_m'), beat(16, greet=True)]),
                     cast('glessner_frances_m', P(GD[0] - 4.6, GD[1] - 0.6), face=P(GD[0], GD[1]), hidden=True,
                          beats=[beat(11, show=True), beat(15, greet=True), beat(17, talk=True), beat(30, talk=False)]),
                 ]),
            dict(id='court', dest=('anchor', 'glessner_tour_hall_bow'),
                 text="The courtyard, the sunny private heart of the fortress. The mother shows the daughter what her hands have made. It is easy to see what the daughter sees: a woman of 56 who was given permission by nobody, doing exact, patient, beautiful work at a bench. Frances Glessner Lee is clever, and she is bored, and her marriage is \"not a happy one\". Her son will say that she had the \"creative urge coupled with high manual dexterity\" that her husband never shared. Everything that happens to her next starts with what she is looking at now: small things, made precisely, by hand, in a house where every detail is a clue. She will have one more child. Then she will leave, and she will build something nobody on this street could ever have imagined.",
                 evidence=['lee-son', 'lee-twins', 'silversmith'],
                 links=[('person', 'glessner_frances_m', 'Frances M. Glessner')],
                 caption="Mother and daughter stand together in the courtyard, and the cook looks out from the service door.",
                 cast=lambda: [
                     cast('glessner_frances_m', P(HB[0] + 2.4, HB[1] + 1.6), face=P(HB[0] + 2.6, HB[1] - 0.6), beats=[beat(2, talk=True), beat(20, talk=False)]),
                     cast('pa1904_lee_frances_glessner', P(HB[0] + 2.6, HB[1] - 0.4), face=P(HB[0] + 2.4, HB[1] + 1.6), beats=[beat(21, talk=True), beat(32, talk=False)]),
                     cast('glessner_williamson_martha_l', P(HB[0] - 5.2, HB[1] + 1.4), face=P(HB[0] + 2.5, HB[1] + 0.6)),
                 ]),
        ],
        legs=[
            dict(story="Next door, through the shared wall, to the brother's half of the twin houses.", evidence=['george-family'], story_evidence=['twins-1902']),
            dict(story="South a block along Prairie Avenue to the stone house at Eighteenth Street.", evidence=['silversmith'], story_evidence=['silversmith']),
            dict(story="Through the house to the courtyard, where the windows are wide.", evidence=['narrow-windows'], story_evidence=['narrow-windows']),
        ],
        endings=[dict(id='nutshell', text="End of the walk. Martha was born in 1906. In 1914 the Lees divorced. Years later Frances Glessner Lee made the Nutshell Studies of Unexplained Death: tiny, exact rooms where a death has happened, built at one inch to a foot, every clue in place. She wrote to an adviser, \"I found myself constantly tempted to add more clues and details…stop me when I go too far.\" In 1931 she gave Harvard $250,000 for legal medicine, and in 1943 New Hampshire made her the first woman state police captain in the country. Detectives still train on her rooms. The girl who was tutored at home taught the police how to look.")],
    ))

    # ── 4 ── The Reading Class ──────────────────────────────────────────────────────────────
    GH, KM = anchor('glessner_house'), 'kimball_house_1801_prairie'
    SS = anchor('glessner_household_service_stair')
    out.append(dict(
        id='monday-reading-class', title='Monday at the Fortress', hour='morning',
        premise="Every Monday from October to May the ladies of Chicago come to the stone fortress at Eighteenth and Prairie to sew and listen. This Monday the house across the street is waiting for a death.",
        opening="JAUNT: MONDAY AT THE FORTRESS. Monday morning, 21 November 1904, at the corner of Eighteenth Street and Prairie Avenue.\n\nFive stops in and around the Glessner House. Today is a Monday, which means the Reading Class: the wives of University of Chicago professors and the ladies of the South Side, gathering in the library at the invitation of Frances Glessner. Inside these walls everything runs like a clock, and servants are rarely seen. Across Eighteenth Street, in the house of the piano king, the clock is running down.\n\nStart at the corner, where the neighbours first saw what Richardson had built.",
        keepsake=('News & Knowledge', 'The Reading Class Invitation', 'An interpretive card of the Monday Morning Reading Class at 1800 Prairie in 1904, not a historical artifact.'),
        extra_evidence=['frances-mind', 'class-harper', 'kimball-dying'],
        stops=[
            dict(id='fortress', dest=('anchor', 'glessner_house'),
                 text="The corner of Eighteenth and Prairie. The house is granite, low and hard, with windows on the street side barely wide enough to light a corridor. Its architect, H. H. Richardson, died in 1886 before it was finished; it went up between June 1886 and December 1887. Not everyone liked it. George Pullman, just across the way, complained: \"I do not know what I have ever done to have that thing staring me in the face every time I go out of my door\". Pullman is seven years dead now, and the house is still staring. What the passers-by never see is the other side: generous windows onto a sunny courtyard, and a household that runs like a machine. The Glessner carriage is at the curb. The ladies are arriving on foot.",
                 evidence=['narrow-windows', 'richardson-dates', 'pullman-glare', 'neighbours'],
                 links=[('person', 'glessner_john_j', 'John J. Glessner')],
                 caption="Ladies come down Prairie Avenue in twos for the Monday class, past the Glessner carriage at the curb.",
                 teams=lambda: [dict(team='prairie_driven_brougham_glessner_1904', at=P(1398.6, -3238), heading=180.0)],
                 cast=lambda: [
                     extra('guest_a', 'lady_1904', 'A member of the Reading Class (unnamed)', P(1391.4, -3196), beats=[beat(0, walk=[P(1391.6, -3218), P(1392.2, -3226.6)], pace='slow'), beat(1, talk=True), beat(16, talk=False)]),
                     extra('guest_b', 'lady_1904', 'A second member of the class (unnamed)', P(1390.4, -3195), beats=[beat(0, walk=[P(1390.6, -3218), P(1391.2, -3227.6)], pace='slow')]),
                     extra('guest_c', 'lady_1904', 'A professor\'s wife, new to the class (unnamed)', P(1404, -3196), beats=[beat(3, walk=[P(1400, -3212), P(1394, -3220), P(1392.8, -3225.4)], pace='walk')]),
                 ]),
            dict(id='hostess', dest=('anchor', 'glessner_tour_door'),
                 text="The front door. In 1893 William Rainey Harper, the president of the new University of Chicago, asked Frances Glessner how the professors' wives might meet the women of the city. Her answer was this: the Monday Morning Reading Class. It meets in the library for two hours every Monday from October to May. For the first hour the ladies sew while a professional reader reads aloud; the second hour is lighter, a reading or a lecture. Nobody joins by asking. \"Membership was by invitation only\", and for a professor's wife new to Chicago an invitation is the way in. Mrs. Glessner greets her guests herself. Christine Nelson, the parlor maid, stands ready for their wraps. Then the door shuts, and the house does what it was built to do.",
                 evidence=['class-harper', 'reading-class'],
                 links=[('person', 'glessner_frances_m', 'Frances M. Glessner'), ('person', 'pa1904_glessner_john_j_c1900_christine_nelson', 'Christine Nelson')],
                 caption="Frances Glessner greets her guests at the door while Christine Nelson stands behind her.",
                 cast=lambda: [
                     cast('glessner_frances_m', P(GD[0] - 3.6, GD[1] + 0.3), face=P(GD[0] + 4, GD[1]), beats=[beat(3, greet=True), beat(5, talk=True), beat(14, talk=False), beat(18, greet=True)]),
                     cast('pa1904_glessner_john_j_c1900_christine_nelson', P(GD[0] - 4.8, GD[1] - 1.2), face=P(GD[0] + 4, GD[1])),
                     extra('guest_d', 'lady_1904', 'A member of the Reading Class (unnamed)', P(GD[0] + 3, GD[1] + 14), beats=[beat(0, walk=[P(GD[0] + 0.5, GD[1] + 3), P(GD[0] - 2.2, GD[1] + 0.4)], pace='slow'), beat(12, face='glessner_frances_m')]),
                     extra('guest_e', 'lady_1904', 'A second member of the class (unnamed)', P(GD[0] + 4, GD[1] + 18), beats=[beat(4, walk=[P(GD[0] + 1.5, GD[1] + 4), P(GD[0] - 1, GD[1] + 1.4)], pace='slow')]),
                 ]),
            dict(id='hall', dest=('anchor', 'glessner_tour_hall_bow'),
                 text="Inside, the house turns its back on the street and opens to the courtyard. The door to the court has yellow glass under chipped white glass, which gives the hall \"a feeling of sunlight even in cloudy weather\", and today is cloudy. The plan is a puzzle box: every principal room has two or more ways in and out, and the passages are \"so planned that servants rarely are in evidence\". So while the needles go in and out in the library, a whole second household is moving round them unseen: the cook, the maids, the man who keeps the fires. Frances Glessner wanted a house where the work never showed. She got one. The ladies sew. The reader reads. And the help keeps out of sight in the court, where only you can see them.",
                 evidence=['yellow-glass', 'servants-unseen', 'creeper'],
                 links=[('person', 'pa1904_glessner_john_j_c1900_mary_reynolds', 'Mary Reynolds')],
                 caption="Below the hall bay, the household works out of sight: a maid crosses the court with a tray, and the cook waits at the service door.",
                 cast=lambda: [
                     cast('pa1904_glessner_john_j_c1900_mary_reynolds', P(HB[0] - 7, HB[1] + 1.4), beats=[beat(1, walk=[P(HB[0] - 1, HB[1] + 1.2), P(HB[0] + 3.2, HB[1] + 3.6)], pace='slow'), beat(14, face=P(HB[0] + 4, HB[1] + 6))]),
                     cast('glessner_williamson_martha_l', P(HB[0] - 6, HB[1] - 0.8), face=P(HB[0] + 3, HB[1] + 3)),
                 ]),
            dict(id='bench', dest=('anchor', 'glessner_household_service_stair'),
                 text="The service stair, down to the basement. Down there is the newest room in the house: the workbench Frances Glessner set up this year, where she makes silver with a hammer and a torch and stamps each piece with \"a G encircling a honeybee\". Upstairs she is the most correct hostess in Chicago. Downstairs she is a craftsman taking lessons from a Hull House jeweller. Both are true, and she has been running this house, and that class, by the clock for eleven years. But across Eighteenth Street a neighbour has been ill for a long time, and this morning the doctor is calling again. Look out through the gates toward the corner house: the house of William W. Kimball, the piano maker.",
                 evidence=['silversmith', 'journal-silver', 'class-harper'],
                 links=[('person', 'pa1904_glessner_john_j_c1900_august_billings', 'August Billings')],
                 caption="August Billings brings the coal up from the cellar and stops at the stair to look toward the street.",
                 cast=lambda: [
                     cast('pa1904_glessner_john_j_c1900_august_billings', P(SS[0] - 1.6, SS[1] + 2.4), face=P(SS[0] + 4, SS[1] + 1), beats=[beat(3, walk=[P(SS[0] + 1.8, SS[1] + 3.4)], pace='slow'), beat(12, face=P(SS[0] + 30, SS[1] + 12))]),
                 ]),
            dict(id='kimball', dest=('anchor', 'kimball_house'),
                 text="1801 Prairie, across Eighteenth Street: the Kimball house. William Wallace Kimball came to Chicago in 1857 and traded his Iowa land for four pianos, which he sold from a second-floor office. Now his factory turns out about a hundred pianos and organs a week, and his name is on pianos all over America. He and his wife Evaline have no children. And he is dying. He will die \"at home after a lingering illness\" on 16 December, and his funeral will be held in this house. Watch the doctor going up the steps, and the steward who lets him in. Among his honorary pallbearers will be \"Marshall Field, Robert T. Lincoln\" and, from the house of the Reading Class, \"J. J. Glessner\".",
                 evidence=['kimball-four', 'kimball-start', 'kimball-dying'],
                 links=[('person', 'pa1904_kimball_william_w', 'William W. Kimball'), ('person', 'pa1904_kimball_mrs_william_w', 'Evalyne M. Kimball'), ('person', 'pa1904_kimball_william_w_c1900_ernest_sibbald', 'Ernest Sibbald')],
                 caption="A doctor climbs the Kimball steps; Ernest Sibbald, the steward, opens the door, and Mrs. Kimball waits in the hall.",
                 cast=lambda: [
                     extra('doctor', 'gentleman_1904', 'A doctor calling (unnamed)', at(KM, 13, 18), beats=[beat(0, walk=[at(KM, 10, 4), at(KM, 3, 0.6)], pace='brisk'), beat(14, face='pa1904_kimball_william_w_c1900_ernest_sibbald'), beat(20, hide=True)]),
                     cast('pa1904_kimball_william_w_c1900_ernest_sibbald', at(KM, 1.6, -0.4), face=at(KM, 9, 0), hidden=True, beats=[beat(10, show=True), beat(21, hide=True)]),
                     cast('pa1904_kimball_mrs_william_w', at(KM, 1.2, 1.1), face=at(KM, 9, 0), hidden=True, beats=[beat(13, show=True), beat(22, hide=True)]),
                 ]),
        ],
        legs=[
            dict(story="Down the walk to the front door, where the guests are going in.", evidence=['class-harper'], story_evidence=['class-harper']),
            dict(story="Through the house to the courtyard side, where the windows are generous.", evidence=['narrow-windows'], story_evidence=['narrow-windows']),
            dict(story="Across the court to the service stair, the household's own way in.", evidence=['servants-unseen'], story_evidence=['servants-unseen']),
            dict(story="Out through the gates and across Eighteenth Street to the Kimball house.", evidence=['kimball-four'], story_evidence=['kimball-dying']),
        ],
        endings=[dict(id='clock', text="End of the walk. W. W. Kimball died on 16 December 1904, and John Glessner crossed Eighteenth Street to stand among his honorary pallbearers. The Reading Class went on. It met every Monday from October to May, \"until 1930\". When Frances Glessner died, her husband tried to say who she had been. \"She had a clean and wholesome and orderly mind, a heart overflowing with love for family and friends and for all in any need.\" That is the house in one sentence: clean, wholesome, orderly, and full of people you never see.")],
    ))

    # ── 5 ── The Pullman twins ──────────────────────────────────────────────────────────────
    PM, PC, LW, DX = 'pullman_house_1729_prairie', 'pullman_house_1729_prairie_conservatory', 'moulton_lowden_house_1912_prairie', 'house_1726_prairie'
    out.append(dict(
        id='the-pullman-twins', title='The Last Pullman Twin', hour='dusk',
        premise="George Pullman left his twin sons $3,000 a year and a name they could not live up to. One is dead. At dusk in 1904 the other is still riding hard, and his mother is still paying.",
        opening="JAUNT: THE LAST PULLMAN TWIN. Dusk on a Monday in November 1904. The lamps are coming on along Prairie Avenue.\n\nFour stops, from the biggest house on the street to the house of the one Pullman child who turned out the way her father wanted. George Pullman built sleeping cars, a company town and a fortune. He could not build sons. His twins, George Jr. and Sanger, were born in 1875 into more money than almost anyone in America, and spent their lives showing the city what that does to a boy.\n\nStart at the Pullman house, where the widow lives with the shades half drawn.",
        keepsake=('Neighbors', 'The Pullman Allowance', 'An interpretive card of the Pullman family in 1904, not a historical artifact.'),
        extra_evidence=['sanger-death', 'pullman-grave'],
        stops=[
            dict(id='widow', dest=('structure', PM),
                 text="1729 Prairie, the Pullman house, the biggest pile on the block. Harriett Sanger married George Pullman in 1867, and they had four children: Florence, Harriett, and in 1875 the twins, George Jr. and Walter Sanger, whom everyone calls Sanger. George Pullman died in 1897 and left his widow this house, which she still keeps. To the twins he left a judgment, written into his will: \"Pullman's will stipulated that the twins were to be given a yearly stipend of only $3,000.\" Their father knew them. Mrs. Pullman's carriage is at the door; Henry Windish, the coachman, has it ready, and Miss Robinson, her companion, is with her. The house will be razed in 1922. Go round to the glasshouse, where the boys grew up.",
                 evidence=['pullman-children', 'twins-will', 'pullman-widow', 'pullman-coachman', 'pullman-razed', 'pullman-strike'],
                 links=[('person', 'pa1904_pullman_mrs_george_m', 'Harriet Sanger Pullman'), ('person', 'pa1904_robinson_miss_r_s', 'Miss R. S. Robinson'), ('person', 'pa1904_pullman_mrs_george_m_c1900_henry_windish', 'Henry Windish')],
                 caption="Harriett Pullman comes out on the arm of her companion to her waiting carriage, and the housekeeper watches from the door.",
                 teams=lambda: [dict(team='prairie_driven_brougham_north_loop_1904', at=P(1406.2, -3180), heading=0.0)],
                 cast=lambda: [
                     cast('pa1904_pullman_mrs_george_m', at(PM, 1.6, 0.6), face=at(PM, 9, 0), hidden=True,
                          beats=[beat(3, show=True), beat(5, walk=[at(PM, 5, 0.6), at(PM, 13.6, -1.6)], pace='slow'), beat(26, face=at(PM, 20, -2.5))]),
                     cast('pa1904_robinson_miss_r_s', at(PM, 1.4, -0.6), face=at(PM, 9, 0), hidden=True,
                          beats=[beat(4, show=True), beat(6, walk=[at(PM, 5, -0.6), at(PM, 13.2, -3)], pace='slow')]),
                     cast('pa1904_pullman_mrs_george_m_c1900_emma_scott', at(PM, 2, 1.8), face=at(PM, 9, 0), hidden=True, beats=[beat(5, show=True)]),
                 ]),
            dict(id='boys', dest=('structure', PC),
                 text="The Pullman conservatory, glass and palms at the side of the house. The twins grew up here. They were schooled at home on Prairie Avenue, and the story went round that they were \"arranging and promoting pit bull fights\". As teenagers they \"frequently were seen riding around Chicago in cabs filled with champagne bottles.\" Their father sent them east to a training school for Harvard, where \"Sanger and George were ranked 147 and 148 out of a class of 148 students.\" Last and next to last, side by side, as close as twins should be. And the cleverer twin was Sanger: \"widely acknowledged as the smarter of the 2\". It never helped him. Cross the street to look at the house where the other twin's story ended.",
                 evidence=['twins-boys', 'sanger-money'],
                 links=[('person', 'pa1904_pullman_mrs_george_m_c1900_samuel_whatter_jr', 'Samuel Whatter Jr.')],
                 caption="Samuel Whatter Jr., the groom, leans on the stable gate beside the glasshouse and talks with a stable hand.",
                 cast=lambda: [
                     cast('pa1904_pullman_mrs_george_m_c1900_samuel_whatter_jr', at(PC, 3, 6), face=at(PC, 4, 9), beats=[beat(2, talk=True), beat(18, talk=False)]),
                     extra('pullman_hand', 'stable_helper_1904', 'A Pullman stable hand (unnamed)', at(PC, 4.6, 8.4), face=at(PC, 3, 6), beats=[beat(19, talk=True), beat(30, talk=False)]),
                 ]),
            dict(id='george', dest=('structure', DX),
                 text="From the west side of the street, look back at the Pullman house in the dusk. The other twin is gone. George Jr. secretly married Lynn Fernald, \"his brother's betrothed\": he stole his own twin's bride. A man named Frederick Bowers sued him for $100,000, \"eventually settling for $50,000.\" Then in November 1901 George died of pneumonia, at 26. The World printed a headline: \"Death of George Pullman a Warning to Rich Fathers.\" So Sanger is the last of the twins. He is 29 now, and still poor with money: thrown out of the New York Athletic Club for unpaid dues, and his debts so tangled that a creditor once held his sister-in-law's luggage for five months. His mother has paid before. Walk south to the sister who never needed paying for.",
                 evidence=['george-jr', 'sanger-death', 'sanger-money'],
                 caption="A pair of gentlemen stroll past the Pullman house and turn to look at it.",
                 cast=lambda: [
                     extra('stroller_a', 'gentleman_1904', 'A gentleman of the street (unnamed)', at(PM, 10.4, 26), beats=[beat(0, walk=[at(PM, 10.4, 2)], pace='slow'), beat(12, face=at(PM, 2, 0)), beat(13, talk=True), beat(24, talk=False), beat(26, walk=[at(PM, 10.4, -26)], pace='slow')]),
                     extra('stroller_b', 'gentleman_1904', 'A second gentleman (unnamed)', at(PM, 11.4, 27), beats=[beat(0, walk=[at(PM, 11.4, 3)], pace='slow'), beat(12, face='stroller_a'), beat(26, walk=[at(PM, 11.4, -25)], pace='slow')]),
                 ]),
            dict(id='sister', dest=('structure', LW),
                 text="1912 Prairie, the Lowden house. Florence, the eldest Pullman child, married Frank Orren Lowden, a lawyer, and here they live with their children. Lowden is a lawyer, and when trouble comes to the family, it tends to come to his office. Their mother once \"paid the unnamed woman $10,000 to leave Sanger and never return.\" The children play at their nurse's feet on a quiet Monday evening, the way the twins once did on this same street. The house will be razed in 1939. And the last twin is still out there, riding hard.",
                 evidence=['lowden-house', 'sanger-money', 'lowden-razed', 'pullman-children'],
                 links=[('person', 'pa1904_lowden_frank_orren', 'Frank Orren Lowden'), ('person', 'pa1904_lowden_mrs_frank_orren', 'Florence Pullman Lowden')],
                 caption="Frank Lowden comes home on foot; Florence meets him on the steps while the nurse brings the children in.",
                 cast=lambda: [
                     cast('pa1904_lowden_frank_orren', at(LW, 10.6, 20), beats=[beat(0, walk=[at(LW, 10.6, 1), at(LW, 4, 0.4)], pace='brisk'), beat(16, face='pa1904_lowden_mrs_frank_orren'), beat(17, greet=True)]),
                     cast('pa1904_lowden_mrs_frank_orren', at(LW, 1.6, -0.3), face=at(LW, 9, 0), hidden=True, beats=[beat(9, show=True), beat(11, walk=[at(LW, 3, -0.4)], pace='slow'), beat(16, face='pa1904_lowden_frank_orren'), beat(18, talk=True), beat(30, talk=False)]),
                     cast('pa1904_lowden_frank_orren_c1900_anna_peterson', at(LW, 6, -3.5), face=at(LW, 6, 0)),
                     cast('pa1904_lowden_frank_orren_c1900_pullman_lowden', at(LW, 6.8, -1.5), face='pa1904_lowden_frank_orren_c1900_anna_peterson'),
                     cast('pa1904_lowden_frank_orren_c1900_florence_lowden', at(LW, 6.4, -2.2), face='pa1904_lowden_frank_orren_c1900_anna_peterson'),
                 ]),
        ],
        legs=[
            dict(story="Along the side of the house to the conservatory, the glasshouse where the twins were boys.", evidence=['twins-boys'], story_evidence=['twins-boys']),
            dict(story="Across Prairie Avenue to look back at the house the twins grew up in.", evidence=['george-jr'], story_evidence=['george-jr']),
            dict(story="South two blocks to 1912 Prairie, the house of the eldest Pullman daughter.", evidence=['lowden-house'], story_evidence=['lowden-house']),
        ],
        endings=[dict(id='ride', text="End of the walk. Sanger Pullman lived nine more months. In August 1905 he \"died after being thrown from a horse and carriage after yet another wild ride\". His mother had now buried her husband and both her sons; her husband lay in Graceland under a \"lead-lined mahogany coffin, which was then sealed inside a block of concrete\", so that nobody could ever get at him. Nobody could get at the boys, either, not their father, not their money, not their mother's $10,000. The World had said it in 1901, and it was still true: \"a Warning to Rich Fathers.\"")],
    ))

    # ── 6 ── Gustave Behring ────────────────────────────────────────────────────────────────
    PA = anchor('pullman_house')
    out.append(dict(
        id='pullmans-other-son', title="Pullman's Other Son", hour='afternoon',
        premise="A German sergeant swore George Pullman was his father. He followed the family for four years, to the office, to the funeral, to the front steps, and once to the wrong end of a judge's gun.",
        opening="JAUNT: PULLMAN'S OTHER SON. A Monday afternoon in November 1904, outside the Pullman house at Eighteenth Street.\n\nFour stops, around the Pullman house and down the street to the house of the family's son-in-law. George Pullman had twin sons, and the whole city knew their names. There was a third young man who claimed the name too. His mother told him on her deathbed who his father was, and he crossed an ocean to say so to Pullman's face. The family called him a madman. The doctors kept saying he was sane.\n\nStart at the front of the house, where his story begins.",
        keepsake=('News & Knowledge', 'A Claim on the Pullman Name', 'An interpretive card of the Behring affair of 1897 to 1901 as the papers reported it, not a historical artifact.'),
        extra_evidence=['behring-1901'],
        stops=[
            dict(id='mother', dest=('structure', PM),
                 text="1729 Prairie, the Pullman house. Picture a German Army sergeant named Gustave Behring, 28 years old, at his mother's bedside. Dying, she told him his real father was George M. Pullman. She had been a governess in Chicago \"for a house on the west side\", she said, and when she became pregnant, Pullman packed her off to Germany with $500. Behring came to Chicago. He went to the Pullman building and was thrown out of Pullman's office. He was locked up for a time in an asylum, and arrested six more times lurking outside the building. Four days before Pullman died, their conversation was recorded. \"BEHRING: You are my father! PULLMAN: You are a crazy man!\" The house will be razed in 1922. Walk round to the front steps.",
                 evidence=['behring-mother', 'behring-office', 'pullman-razed'],
                 caption="A stranger in a dark coat stops on the walk at the Pullman gate, looks up at the house, and walks on.",
                 cast=lambda: [
                     extra('stranger', 'gentleman_1904', 'A stranger at the gate (unnamed; nobody is known to have been here on this day)', at(PM, 12, 22),
                           beats=[beat(0, walk=[at(PM, 12, 2)], pace='slow'), beat(9, face=at(PM, 1, 0)), beat(22, walk=[at(PM, 12, -24)], pace='walk')]),
                 ]),
            dict(id='steps', dest=('anchor', 'pullman_house'),
                 text="The front steps. Pullman died in October 1897. His family buried him under concrete and steel. And \"Less than 12 hours after the funeral, Behring showed up at the family's residence on Prairie Avenue, demanding to speak to Mrs. Harriett Pullman.\" He never reached the door. On these steps he was met by Pullman's two sons, the twins, and by the family's lawyers. He was arrested again, and on 29 October 1897 an insanity expert examined him and pronounced him sane. Not a madman, then. Just a man who would not go away. The Pullmans' housekeeper, Emma Scott, still answers this door. Walk round the corner to the glasshouse.",
                 evidence=['behring-steps', 'pullman-grave', 'pullman-strike'],
                 links=[('person', 'pa1904_pullman_mrs_george_m_c1900_emma_scott', 'Emma Scott')],
                 caption="Emma Scott, the housekeeper, opens the front door, looks out at the empty steps, and closes it again.",
                 cast=lambda: [
                     cast('pa1904_pullman_mrs_george_m_c1900_emma_scott', at(PM, 1.6, 0), face=at(PM, 9, 0), hidden=True, beats=[beat(5, show=True), beat(7, walk=[at(PM, 3.2, 0)], pace='slow'), beat(11, heading=h.hd(at(PM, 3, 0), at(PM, 9, 12))), beat(16, walk=[at(PM, 1.6, 0)], pace='slow'), beat(19, hide=True)]),
                 ]),
            dict(id='ship', dest=('structure', PC),
                 text="The conservatory, the family's glass parlour. Behind this glass the Pullmans waited for the problem to leave. In September 1898 it did: detectives walked Behring up the gangway of the Cunard liner Campania, bound for Bremen. Europe could have him. But he came back. A man who has been told by his dying mother who his father was does not stay deported. And by 1901 the twins who had blocked the steps had troubles of their own. One of them, George Jr., would be dead by November. Florence Pullman's husband, Frank Lowden, was a lawyer. So when Behring came back, he went to Lowden. Walk south down Prairie to the Lowden house.",
                 evidence=['behring-ship', 'george-jr', 'lowden-house'],
                 caption="The groom Samuel Whatter Jr. comes out of the stable yard by the glasshouse and stands looking down the street.",
                 cast=lambda: [
                     cast('pa1904_pullman_mrs_george_m_c1900_samuel_whatter_jr', at(PC, 3, 9), beats=[beat(2, walk=[at(PC, 5, 3)], pace='slow'), beat(12, face=at(PC, 25, -30))]),
                 ]),
            dict(id='gun', dest=('structure', LW),
                 text="1912 Prairie, where Frank Lowden lives with Florence and their children. Lowden is a careful man, but even careful men have bad afternoons. \"on June 25, 1901, Behring was again arrested at the law offices of Frank Lowden (Florence Pullman's husband) demanding $5,000 in cash and $10,000 a month for 6 months.\" Lowden's partner did not wait for the police to talk him out of it: \"Judge Davis, Lowden's partner, held Behring at gunpoint until the police arrived\". The house will be razed in 1939. Watch Lowden come home this afternoon, and look back down the street before he goes in.",
                 evidence=['behring-1901', 'lowden-house', 'lowden-razed'],
                 links=[('person', 'pa1904_lowden_frank_orren', 'Frank Orren Lowden')],
                 caption="Frank Lowden comes up his walk, stops on the steps to look back down the street, and goes in.",
                 cast=lambda: [
                     cast('pa1904_lowden_frank_orren', at(LW, 10.6, 22), beats=[beat(0, walk=[at(LW, 10.6, 1), at(LW, 3.6, 0.3)], pace='walk'), beat(15, heading=h.hd(at(LW, 3.6, 0), at(LW, 11, 22))), beat(22, walk=[at(LW, 1.4, 0)], pace='walk'), beat(25, hide=True)]),
                     cast('pa1904_lowden_frank_orren_c1900_john_halloran', at(LW, 1.6, -1.2), face=at(LW, 9, 0), hidden=True, beats=[beat(13, show=True), beat(25, hide=True)]),
                 ]),
        ],
        legs=[
            dict(story="Round to the front steps, where the twins and the lawyers met him after the funeral.", evidence=['behring-steps'], story_evidence=['behring-steps']),
            dict(story="Along the side of the house to the conservatory.", evidence=['behring-ship'], story_evidence=['behring-ship']),
            dict(story="South down Prairie Avenue to 1912, the house of the family's lawyer.", evidence=['behring-1901'], story_evidence=['behring-1901']),
        ],
        endings=[dict(id='name', text="End of the walk. Gustave Behring was arrested, locked up, examined, found sane, put on a ship and arrested again, and as the papers told it his story ends at the point of a judge's gun. \"You are my father!\" \"You are a crazy man!\" Those two sentences are all that is left of the only conversation the two men ever had, and you can decide for yourself which of them was telling the truth.")],
    ))

    # ── 7 ── The bronze at Eighteenth Street ────────────────────────────────────────────────
    MO = 'fort_dearborn_massacre_monument_1893'
    BG = anchor('haunted_battle_ground')
    out.append(dict(
        id='bronze-at-eighteenth', title='The Bronze at Eighteenth Street', hour='afternoon',
        premise="George Pullman set up a bronze of the battle of 1812 at his own door. A year later the army came to Chicago again, this time for his own workers. A walk about history, and who gets to cast it.",
        opening="JAUNT: THE BRONZE AT EIGHTEENTH STREET. A Monday afternoon in November 1904, at the corner of Eighteenth Street and Prairie Avenue.\n\nFour stops round one street corner. There is a battlefield under the pavement, a bronze that tells a story about it, the house of the man who paid for the bronze, and the house that stared back at him. Every stop is a question about what really happened, and who decided how it would be remembered.\n\nStart where the street starts: the ground where the battle was fought.",
        keepsake=('News & Knowledge', 'The Monument Question', 'An interpretive card about the 1893 monument at Eighteenth Street and the history behind it, not a historical artifact.'),
        extra_evidence=['pullman-grave'],
        stops=[
            dict(id='ground', dest=('anchor', 'haunted_battle_ground'),
                 text="Prairie Avenue at Eighteenth Street. Before the houses, this was sand hills by the lake. On 15 August 1812 the Battle of Fort Dearborn was fought across them, and the dead \"lay in the sand, half buried where they were killed, until 1816\". For a century a big cottonwood tree marked the spot. In 1900 a Tribune writer swore that the Pullman house in front of this corner \"stands about where the massacre took place\". Now look at the street in 1904: brick, granite, gas lamps, a schoolteacher bringing her class to see the sights. The battle is ninety-two years gone, and it has become a lesson. The question is who wrote the lesson. Walk east along Eighteenth Street to the bronze.",
                 evidence=['battle-ground', 'battle-bones'],
                 caption="A teacher leads a line of schoolchildren along Eighteenth Street toward the monument.",
                 cast=lambda: [
                     extra('teacher', 'lady_1904', 'A schoolteacher (unnamed)', P(BG[0] - 10, BG[1] + 3), beats=[beat(0, walk=[P(BG[0] + 4, BG[1] + 2), P(BG[0] + 40, BG[1] + 1)], pace='slow'), beat(8, talk=True), beat(20, talk=False)]),
                     extra('pupil_1', 'child_boy_1904', 'A pupil (unnamed)', P(BG[0] - 12.5, BG[1] + 3.6), beats=[beat(0.6, walk=[P(BG[0] + 2, BG[1] + 2.6), P(BG[0] + 38, BG[1] + 1.6)], pace='slow')]),
                     extra('pupil_2', 'child_girl_1904', 'A pupil (unnamed)', P(BG[0] - 13.5, BG[1] + 2.4), beats=[beat(1.2, walk=[P(BG[0] + 1, BG[1] + 1.6), P(BG[0] + 37, BG[1] + 0.6)], pace='slow')]),
                     extra('pupil_3', 'teen_boy_1904', 'An older pupil (unnamed)', P(BG[0] - 15, BG[1] + 3.2), beats=[beat(1.8, walk=[P(BG[0] - 0.5, BG[1] + 2.4), P(BG[0] + 35.5, BG[1] + 1.4)], pace='slow')]),
                     extra('pupil_4', 'child_girl_1904', 'A pupil (unnamed)', P(BG[0] - 16.4, BG[1] + 2.2), beats=[beat(2.4, walk=[P(BG[0] - 2, BG[1] + 1.4), P(BG[0] + 34, BG[1] + 0.4)], pace='slow')]),
                 ]),
            dict(id='bronze', dest=('structure', MO),
                 text="The monument. George Pullman paid for it and set it up in 1893, near his own front door: Carl Rohl-Smith's bronze of the Potawatomi chief Black Partridge saving Margaret Helm, an officer's wife. It is dramatic and noble, and it may never have happened. \"Some historians regard the incident as the product of romantic imagination instead of eyewitness testimony\", and they say \"Mrs. Helm rode her horse to the shore of Lake Michigan where she found refuge.\" The sculptor found his models at Fort Sheridan, among survivors of Wounded Knee, whom he called \"Indians of the most untamed sort\". One historian says the figures \"may have owed more to Buffalo Bill Cody's Wild West Show than to actual research.\" The teacher is reading the plaque aloud. Now look at the house the bronze stands guard over.",
                 evidence=['battle-statue', 'statue-doubt', 'statue-models'],
                 caption="The teacher reads to her class at the foot of the monument while the children look up at the bronze.",
                 cast=lambda: [
                     extra('teacher', 'lady_1904', 'A schoolteacher (unnamed)', at(MO, 5, 1), face=at(MO, 0, 0), beats=[beat(2, talk=True), beat(28, talk=False), beat(29, face='pupil_3')]),
                     extra('pupil_1', 'child_boy_1904', 'A pupil (unnamed)', at(MO, 6.4, -1.4), face=at(MO, 0, 0)),
                     extra('pupil_2', 'child_girl_1904', 'A pupil (unnamed)', at(MO, 7, 0.2), face=at(MO, 0, 0)),
                     extra('pupil_3', 'teen_boy_1904', 'An older pupil (unnamed)', at(MO, 7.4, 2), face=at(MO, 0, 0)),
                     extra('pupil_4', 'child_girl_1904', 'A pupil (unnamed)', at(MO, 6.2, 3), face=at(MO, 0, 0)),
                 ]),
            dict(id='strike', dest=('structure', PM),
                 text="1729 Prairie, the Pullman house. The man who paid for the bronze built sleeping cars, and a company town south of the city where his workers paid him rent. In 1894 he cut their wages, but \"he didn't reduce the rent in Pullman\", and they struck. And here is the twist the bronze cannot tell: \"a year after the statue's dedication\", the Seventh Cavalry, the regiment of Wounded Knee, \"came to Chicago to quell the Pullman riots of 1894.\" The regiment came to Chicago to put down a strike against the man who had put a battle of 1812 at his door. Pullman died in 1897. The house will be razed in 1922. Cross Prairie to the house that stared at his.",
                 evidence=['pullman-strike', 'cavalry-1894', 'pullman-raise', 'pullman-razed'],
                 caption="Two working men carrying tools stop on the far walk to look at the Pullman house, then go on.",
                 cast=lambda: [
                     extra('worker_a', 'working_driver_1904', 'A working man (unnamed)', at(PM, 26, 18), beats=[beat(0, walk=[at(PM, 26, 2)], pace='walk'), beat(9, face=at(PM, 0, 0)), beat(10, talk=True), beat(20, talk=False), beat(22, walk=[at(PM, 26, -24)], pace='walk')]),
                     extra('worker_b', 'stable_helper_1904', 'A second working man (unnamed)', at(PM, 27, 19), beats=[beat(0, walk=[at(PM, 27, 3)], pace='walk'), beat(9, face='worker_a'), beat(22, walk=[at(PM, 27, -23)], pace='walk')]),
                 ]),
            dict(id='grave', dest=('anchor', 'glessner_house'),
                 text="The Glessner corner, diagonally across from Pullman. Pullman hated this house: \"I do not know what I have ever done to have that thing staring me in the face every time I go out of my door\". He spent his last years between the bronze and the granite. When he died, his family was afraid that his body would be dug up by robbers, or by men who had worked for him. They buried him in a \"lead-lined mahogany coffin, which was then sealed inside a block of concrete\", under steel rails \"bolted together at right angles\". One historian is honest about the legends: \"Whether it's true or not, we don't really know.\" That is the lesson of this corner. Bronze, granite and concrete, and under all of it, the sand.",
                 evidence=['pullman-glare', 'pullman-grave', 'neighbours'],
                 caption="The class files past the Glessner corner on its way home, and the teacher looks back at the Pullman house.",
                 cast=lambda: [
                     extra('teacher', 'lady_1904', 'A schoolteacher (unnamed)', P(1400, -3212), beats=[beat(0, walk=[P(1395, -3215), P(1393.4, -3250)], pace='slow'), beat(14, face=at(PM, 0, 0))]),
                     extra('pupil_1', 'child_boy_1904', 'A pupil (unnamed)', P(1401.6, -3210.5), beats=[beat(0.6, walk=[P(1394.4, -3216), P(1392.6, -3252)], pace='slow')]),
                     extra('pupil_2', 'child_girl_1904', 'A pupil (unnamed)', P(1403, -3209), beats=[beat(1.2, walk=[P(1395.4, -3216.8), P(1393.8, -3253)], pace='slow')]),
                     extra('pupil_3', 'teen_boy_1904', 'An older pupil (unnamed)', P(1404.4, -3207.6), beats=[beat(1.8, walk=[P(1394.6, -3218), P(1392.8, -3254)], pace='slow')]),
                     extra('pupil_4', 'child_girl_1904', 'A pupil (unnamed)', P(1405.8, -3206.2), beats=[beat(2.4, walk=[P(1395.2, -3219), P(1393.6, -3255)], pace='slow')]),
                 ]),
        ],
        legs=[
            dict(story="East along Eighteenth Street to the bronze at the Pullman fence.", evidence=['battle-statue'], story_evidence=['battle-statue']),
            dict(story="Back round the Pullman grounds to the front of the house on Prairie Avenue.", evidence=['pullman-strike'], story_evidence=['cavalry-1894']),
            dict(story="Across to the Glessner corner, diagonally opposite Pullman's door.", evidence=['neighbours'], story_evidence=['pullman-glare']),
        ],
        endings=[dict(id='sand', text="End of the walk. In 1904 the bronze still stands at Eighteenth Street, telling its story one way. Some historians doubt the rescue it shows ever happened. Pullman lies at Graceland under his concrete, the strike he broke is in every history book, and the ground under this corner still holds the sand of 1812. A monument tells you who paid for it. The rest you have to dig for.")],
    ))

    # ── 8 ── The Everleigh sisters ──────────────────────────────────────────────────────────
    I1, I2 = 'house_1801_indiana', 'house_1913_indiana'
    CO = anchor('glessner_tour_corner')
    FP = anchor('first_presbyterian')
    out.append(dict(
        id='sisters-of-the-levee', title='The Sisters of the Levee', hour='dusk',
        premise="Three blocks west of the mansions, two sisters from Virginia run the most famous house in Chicago, with gold cuspidors and a $15,000 piano. Prairie Avenue pretends not to know the way.",
        opening="JAUNT: THE SISTERS OF THE LEVEE. Dusk on a Monday in November 1904, at Eighteenth Street and Prairie Avenue.\n\nFour stops, walking west from Millionaire's Row toward the Levee, the city's red-light district, and ending at a church on its edge. Prairie Avenue is three blocks from the most famous address in Chicago, and it is not the Glessner House. Two sisters who called themselves Everleigh opened a club on Dearborn Street in 1900, and the richest men in the world have found their way to it.\n\nStart at the corner. Watch which way the cabs turn.",
        keepsake=('News & Knowledge', 'A Card from the Levee', 'An interpretive card about Chicago\'s Levee and the Everleigh Club around 1904, not a historical artifact.'),
        extra_evidence=['everleigh-close'],
        stops=[
            dict(id='corner', dest=('anchor', 'glessner_tour_corner'),
                 text="Eighteenth and Prairie, as the lamps come on. Eighteenth Street is a border. To the north and east: the mansions. To the south and west, \"several blocks away from Prairie Avenue\", begins the Levee, the district that runs from Eighteenth Street to Twenty-second, Wabash to Clark, home of the city's most famous brothels. The ladies of Prairie Avenue never mention it. And yet one of the two most famous houses in Chicago, Vic Shaw's, stood for a time on Prairie Avenue itself. The two gentlemen hurrying round this corner are not going home. Follow them west.",
                 evidence=['levee', 'vic-shaw', 'levee-near'],
                 caption="Two gentlemen in evening coats come round the corner and walk briskly west along Eighteenth Street.",
                 cast=lambda: [
                     extra('gent_a', 'gentleman_1904', 'A gentleman out for the evening (unnamed)', P(CO[0] - 4, CO[1] - 14), beats=[beat(0, walk=[P(CO[0] - 6, CO[1] - 2), P(CO[0] - 40, CO[1] - 1)], pace='brisk'), beat(2, talk=True), beat(14, talk=False)]),
                     extra('gent_b', 'gentleman_1904', 'A second gentleman (unnamed)', P(CO[0] - 5, CO[1] - 15.4), beats=[beat(0.3, walk=[P(CO[0] - 7.2, CO[1] - 3.2), P(CO[0] - 41, CO[1] - 2.2)], pace='brisk')]),
                 ]),
            dict(id='sisters', dest=('structure', I1),
                 text="Indiana Avenue, a block west. Keep walking and in three more blocks there is Dearborn Street, and at 2131 and 2133 Dearborn, the Everleigh Club. Its owners are two sisters, Ada and Minna. They say they are from Kentucky; that was \"another story concocted by the sisters\". They were born Simms, in Virginia, in 1864 and 1866. With about $35,000 they ran a house in Omaha, then came to Chicago and bought out a madam's house on Dearborn. They took a new name from their grandmother, who signed her letters \"Everly yours\". The club opened on 1 February 1900, and on the first night they turned many callers away. In this business, the Everleighs understood, saying no is how you make a price.",
                 evidence=['everleigh-sisters', 'levee'],
                 caption="A cab horse clops past on Indiana Avenue, and a gentleman on the corner checks his watch and turns west.",
                 cast=lambda: [
                     extra('gent_c', 'gentleman_1904', 'A gentleman on the corner (unnamed)', at(I1, 4, 6), face=at(I1, 9, 0), beats=[beat(8, face=at(I1, 30, -6)), beat(14, walk=[at(I1, 7, -6), at(I1, 45, -7)], pace='brisk')]),
                     extra('cabman', 'working_driver_1904', 'A cabman waiting for a fare (unnamed)', at(I1, 9.4, -5), face=at(I1, 9.4, 10)),
                 ]),
            dict(id='rooms', dest=('structure', I2),
                 text="Further south along Indiana, with the Levee two blocks west. Inside the Everleigh Club are fifty rooms across two mansions: a Japanese Throne Room, a Mirror Room, a Silver Parlor, \"a $15,000 gold-leafed piano for the Music Room\" and \"$650 gold cuspidors\". A bottle of champagne costs $12, \"in an era when an entire meal could be had for fifty cents\", and the entrance fee alone is $50. Ada keeps the books and hires the women. Minna meets the guests. In March 1902 Prince Henry of Prussia came, and when a slipper flew off during a dance and spilled champagne, one of his party drank from it, and a whole custom began. The club keeps 15 to 25 cooks and maids, and its women are called \"butterflies\".",
                 evidence=['everleigh-rooms', 'everleigh-roles', 'prince-henry'],
                 caption="Two maids hurry home along Indiana Avenue at dusk, keeping close to the houses.",
                 cast=lambda: [
                     extra('maid_x', 'maid_1904', 'A maid going home (unnamed)', at(I2, 5, 24), beats=[beat(0, walk=[at(I2, 5.4, -30)], pace='brisk'), beat(1, talk=True), beat(15, talk=False)]),
                     extra('maid_y', 'cook_1904', 'A cook going home (unnamed)', at(I2, 6, 25), beats=[beat(0, walk=[at(I2, 6.4, -29)], pace='brisk')]),
                 ]),
            dict(id='church', dest=('anchor', 'first_presbyterian'),
                 text="First Presbyterian Church, at Indiana and Twenty-first Street. It stands at the Levee's eastern edge, close enough to hear it on a summer night. The club's famed clients, the stories say, include the actor John Barrymore and the authors Ring Lardner and Theodore Dreiser, and gossips name the young Marshall Field Jr., who lives a few blocks from here, among them. \"A rival madam maliciously accused the Everleigh sisters\" of far worse, later, and the rumour never died. The minister's door is lit. So is the club's. Tonight, as every night, the Levee is busier.",
                 evidence=['church-1904', 'everleigh-clients', 'levee'],
                 caption="A family comes out of the church hall into the dusk while a cab goes by the other way.",
                 cast=lambda: [
                     extra('elder', 'gentleman_1904', 'A church member (unnamed)', P(FP[0] + 17.6, FP[1] + 48), beats=[beat(2, walk=[P(FP[0] + 14, FP[1] + 40), P(FP[0] + 12, FP[1] + 24)], pace='slow'), beat(3, talk=True), beat(16, talk=False)]),
                     extra('elder_wife', 'lady_1904', 'His wife (unnamed)', P(FP[0] + 18.8, FP[1] + 48.4), beats=[beat(2.4, walk=[P(FP[0] + 15.2, FP[1] + 40.4), P(FP[0] + 13.2, FP[1] + 24.4)], pace='slow')]),
                     extra('elder_girl', 'teen_girl_1904', 'Their daughter (unnamed)', P(FP[0] + 18, FP[1] + 50), beats=[beat(3, walk=[P(FP[0] + 14.6, FP[1] + 42), P(FP[0] + 12.6, FP[1] + 26)], pace='slow')]),
                 ]),
        ],
        legs=[
            dict(story="West along Eighteenth Street, past the last of the mansions, to Indiana Avenue.", evidence=['levee'], story_evidence=['levee-near']),
            dict(story="South along Indiana Avenue, with the Levee's noise two blocks to the west.", evidence=['levee'], story_evidence=['everleigh-rooms']),
            dict(story="South to Twenty-first Street and the church at the Levee's edge.", evidence=['church-1904'], story_evidence=['church-1904']),
        ],
        endings=[dict(id='close', text="End of the walk. The Everleigh Club lasted eleven years. On 24 October 1911 the mayor, Carter Harrison Jr., ordered it closed, and Minna took it the way she took everything: \"If the Mayor says we must close, that settles it...I'll close up shop and walk out with a smile on my face.\" The building was razed in July 1933. Prairie Avenue never once admitted that it knew the way to Dearborn Street. It only ever knew the way back.")],
    ))

    # ── 9 ── Marshall Field Jr. ─────────────────────────────────────────────────────────────
    FJ = 'marshall_field_jr_house_1919_prairie'
    FA = anchor('field_house')
    out.append(dict(
        id='one-year-and-a-day', title='One Year and a Day', hour='afternoon',
        premise="Marshall Field Jr. has a wife, three children, a new wing on his house and the biggest fortune in Chicago coming to him. On this November afternoon he has one year and a day left.",
        opening="JAUNT: ONE YEAR AND A DAY. A Monday afternoon, 21 November 1904, at the Field houses on Prairie Avenue.\n\nFour stops between two houses: the father's and the son's. Marshall Field built one of the great stores of America and the biggest fortune in Chicago. His only surviving son lives two doors away. He is 36 and rich, and he has spent his whole life waiting to become the man his father is. Count the days with him. Exactly one year and one day from now, a shot will be fired in the house at 1919.\n\nStart at the son's front door.",
        keepsake=('Neighbors', 'The Field Inheritance', 'An interpretive card of the Field family on Prairie Avenue in 1904, not a historical artifact.'),
        extra_evidence=['fieldjr-shot', 'field-six-weeks', 'london', 'field-rich'],
        stops=[
            dict(id='son', dest=('structure', FJ),
                 text="1919 Prairie, the house of Mr. and Mrs. Marshall Field Jr. He bought it in 1890, and two years ago D. H. Burnham & Company built \"a huge addition\" for him. He married Albertine Huck, and they have three children: Henry, Marshall III and little Gwendolyn. Look at them on the front walk this afternoon, the nurse with the youngest, the boys in their coats. Everything a man could want is on this walk. Everything except his own name, which belongs to his father. He has been Junior all his life. Walk north, two doors up, to the house where the name lives.",
                 evidence=['fieldjr-marker', 'fieldjr-listing', 'field-heirs'],
                 links=[('person', 'pa1904_field_marshall_jr', 'Marshall Field jr.'), ('person', 'pa1904_field_mrs_marshall_jr', 'Albertine Huck Field')],
                 caption="Marshall Field Jr. and his wife come out to the walk where the nurse is waiting with their children.",
                 cast=lambda: [
                     cast('pa1904_field_marshall_jr', at(FJ, 1.6, 0.4), face=at(FJ, 9, 0), hidden=True, beats=[beat(3, show=True), beat(5, walk=[at(FJ, 6.6, 0.8)], pace='slow'), beat(13, face='pa1904_field_henry'), beat(15, talk=True), beat(26, talk=False)]),
                     cast('pa1904_field_mrs_marshall_jr', at(FJ, 1.5, -0.7), face=at(FJ, 9, 0), hidden=True, beats=[beat(4, show=True), beat(6, walk=[at(FJ, 6.4, -0.8)], pace='slow'), beat(14, face='pa1904_field_gwendolyn')]),
                     extra('field_nurse', 'maid_1904', 'The children\'s nurse (unnamed)', at(FJ, 8.6, -2.2), face=at(FJ, 2, 0)),
                     cast('pa1904_field_gwendolyn', at(FJ, 8.4, -1.4), face=at(FJ, 2, 0)),
                     cast('pa1904_field_henry', at(FJ, 9, 1.6), face=at(FJ, 2, 0)),
                     cast('pa1904_field_marshall_iii', at(FJ, 9.6, 0.4), face=at(FJ, 2, 0)),
                 ]),
            dict(id='father', dest=('structure', F),
                 text="1905 Prairie, the father's house, where the son grew up. It was \"the first in Chicago to be completely wired for electricity\". There was a first son, Louis, who died a baby; this one lived, and was raised to inherit the store that taught America to \"Give the lady what she wants\". His father is \"the wealthiest and most powerful businessman in Chicago\". The father does not hand over power. He is planning to hand it past his son entirely: his will is going to put the fortune in trust for forty years, for the grandsons playing on the walk at 1919. The son walks up to his father's door for his Monday call. Benson the butler lets him in. The house will be razed in 1955.",
                 evidence=['field-children', 'field-rich', 'field-heirs', 'field-razed', 'field-staff'],
                 links=[('person', 'pa1904_field_marshall', 'Marshall Field'), ('person', 'pa1904_field_marshall_c1900_thomas_benson', 'Thomas Benson')],
                 caption="Marshall Field Jr. walks up to his father's door, and Thomas Benson opens it for him.",
                 cast=lambda: [
                     cast('pa1904_field_marshall_jr', at(F, 10.4, -24), beats=[beat(0, walk=[at(F, 10.4, -1), at(F, 3, 0)], pace='walk'), beat(18, face='pa1904_field_marshall_c1900_thomas_benson'), beat(22, walk=[at(F, 1.4, 0)], pace='slow'), beat(24, hide=True)]),
                     cast('pa1904_field_marshall_c1900_thomas_benson', at(F, 1.8, -1), face=at(F, 9, 0), hidden=True, beats=[beat(14, show=True), beat(17, greet=True), beat(25, hide=True)]),
                 ]),
            dict(id='talk', dest=('anchor', 'field_house'),
                 text="Up the street, look back at the two houses. This is what the street sees: a dutiful son making his call. Here is what the street says, behind its curtains. The Levee is three blocks west, and the Everleigh Club on Dearborn Street counts the richest young men in Chicago among its guests; the gossips name Marshall Field Jr. among them. Nobody has proved it, and nobody ever will. But a year and a day from now, the story they tell will be this: \"The most popular story is that he was in fact shot at the Everleigh Club\", and carried home to look like an accident. Other people will say he did it himself. Go back to 1919.",
                 evidence=['fieldjr-rumour', 'everleigh-clients', 'fieldjr-shot'],
                 caption="A gentleman and a lady walk past the Field houses, and the gentleman tips his head toward 1919.",
                 cast=lambda: [
                     extra('gossip_m', 'gentleman_1904', 'A gentleman of the street (unnamed)', P(FA[0] + 4.6, FA[1] - 50), beats=[beat(0, walk=[P(FA[0] + 4.2, FA[1] - 10), P(FA[0] + 4, FA[1] + 20)], pace='slow'), beat(4, talk=True), beat(18, talk=False)]),
                     extra('gossip_f', 'lady_1904', 'A lady of the street (unnamed)', P(FA[0] + 5.6, FA[1] - 50.5), beats=[beat(0, walk=[P(FA[0] + 5.2, FA[1] - 10.5), P(FA[0] + 5, FA[1] + 19.5)], pace='slow'), beat(9, face='gossip_m')]),
                 ]),
            dict(id='shot', dest=('structure', FJ),
                 text="1919 again, as the afternoon goes. The children have gone in. On Wednesday, 22 November 1905, one year and a day from this afternoon, Marshall Field Jr. will be shot in this house. He will live five days. At Mercy Hospital he will say, \"I shot myself with that revolver – accidentally\". The coroner's jury will agree that he \"had shot himself unintentionally while examining a revolver\". Two reporters will be tipped that he spent the evening at the Everleigh Club; the sisters will deny it, and nobody will confirm it. The house will go on standing. Look at the lit windows. The son of the richest man in Chicago is home for dinner, with one year and a day left.",
                 evidence=['fieldjr-shot', 'fieldjr-rumour'],
                 caption="A maid draws the curtains at 1919 as the light goes, and the nurse takes the children in.",
                 cast=lambda: [
                     extra('field_nurse', 'maid_1904', 'The children\'s nurse (unnamed)', at(FJ, 6, -1.6), beats=[beat(1, walk=[at(FJ, 1.4, -0.4)], pace='walk'), beat(9, hide=True)]),
                     cast('pa1904_field_gwendolyn', at(FJ, 6.6, -0.8), beats=[beat(1.2, walk=[at(FJ, 1.4, 0)], pace='slow'), beat(10, hide=True)]),
                     cast('pa1904_field_henry', at(FJ, 7.4, 0.8), beats=[beat(2, walk=[at(FJ, 1.4, 0.4)], pace='walk'), beat(9, hide=True)]),
                     cast('pa1904_field_marshall_iii', at(FJ, 8, -0.2), beats=[beat(3, walk=[at(FJ, 1.4, 0.2)], pace='walk'), beat(10, hide=True)]),
                 ]),
        ],
        legs=[
            dict(story="North two doors, past the Moulton house, to the father's door at 1905.", evidence=['field-children'], story_evidence=['field-heirs']),
            dict(story="North along the walk to look back at both Field houses the way the street does.", evidence=['fieldjr-rumour'], story_evidence=['fieldjr-rumour']),
            dict(story="Back south along the walk to 1919, as the lamps come on.", evidence=['fieldjr-shot'], story_evidence=['fieldjr-shot']),
        ],
        endings=[dict(id='six-weeks', text="End of the walk. Marshall Field Jr. died at Mercy Hospital on Monday 27 November 1905. His father was 71 and had just remarried. On New Year's Day he went out to play golf, caught pneumonia, and \"Six weeks later, Marshall Field, Sr. was dead.\" The fortune went in trust to the boys from the front walk at 1919, just as the will had planned. The son never got to be anything but Junior. His sons got everything.")],
    ))

    # ── 10 ── Edson Keith ───────────────────────────────────────────────────────────────────
    EK, BK, OK, N3 = 'edson_keith_house_1906_prairie', 'elbridge_keith_house_1900_prairie', 'keith_house_1808_prairie', 'house_1613_prairie'
    out.append(dict(
        id='the-walk-to-the-lake', title='The Walk to the Lake', hour='daybreak',
        premise="At daybreak a widow rises at 1906 Prairie, eight years after her husband walked out of this door at six in the morning and never came back. Retrace his last walk, from his brother's door to the lake.",
        opening="JAUNT: THE WALK TO THE LAKE. Daybreak on a Monday in November 1904, at the south end of Prairie Avenue.\n\nFour stops, north along Prairie toward the lake. The Keiths are the steadiest family on the street: three brothers, three houses, one great wholesale firm. But one Monday morning eight years ago, at about this hour, the gentlest of them got up after a sleepless night, put on his hat and coat, and walked out of his front door. He walked.\n\nStart at his door, where his widow still lives.",
        keepsake=('Neighbors', 'The Keith Brothers', 'An interpretive card of the Keith households of Prairie Avenue in 1904, not a historical artifact.'),
        extra_evidence=['keith-will', 'keith-dragged'],
        stops=[
            dict(id='door', dest=('structure', EK),
                 text="1906 Prairie, at daybreak. The widow here is Mrs. Edson Keith. Eight years ago her husband, Edson, a merchant, \"disappeared from his home at 1906 Prairie avenue about 6 o'clock in the morning\". He was 63 and had come to Chicago in 1854. For at least ten years he had barely slept. That last night he paced the halls again, and \"his butler found him in a state of deliriousness at 2 AM\". By six he was gone. Hilda Johnson, the ladies' maid, is first up; Paul Rasmussen, the coachman, is crossing the yard. Mrs. Keith comes to the door to look at the weather. Walk north to the brother's house next door.",
                 evidence=['keith-argus', 'keith-night', 'keith-death', 'keith-same', 'keith-houses', 'keith-coachman'],
                 links=[('person', 'pa1904_keith_mrs_edson', 'Mrs. Edson Keith'), ('person', 'pa1904_keith_mrs_edson_c1900_hilda_johnson', 'Hilda Johnson'), ('person', 'pa1904_keith_mrs_edson_c1900_paul_rasmussen', 'Paul Rasmussen')],
                 caption="Mrs. Edson Keith opens her door at first light and looks up the street toward the lake; her maid stands behind her.",
                 cast=lambda: [
                     cast('pa1904_keith_mrs_edson', at(EK, 1.5, 0.3), face=at(EK, 9, 0), hidden=True, beats=[beat(4, show=True), beat(6, walk=[at(EK, 3.2, 0.3)], pace='slow'), beat(11, heading=h.hd(at(EK, 3, 0), at(EK, 10, 30))), beat(24, face=at(EK, 9, 0))]),
                     cast('pa1904_keith_mrs_edson_c1900_hilda_johnson', at(EK, 1.8, -1.2), face=at(EK, 9, 0), hidden=True, beats=[beat(5, show=True)]),
                     cast('pa1904_keith_mrs_edson_c1900_paul_rasmussen', at(EK, 6, -11), beats=[beat(2, walk=[at(EK, 7, -4), at(EK, 9.2, -2.6)], pace='walk'), beat(14, face='pa1904_keith_mrs_edson')]),
                 ]),
            dict(id='brother', dest=('structure', BK),
                 text="1900 Prairie, the house of his brother Elbridge, built in 1870 in the Second Empire style that once ruled this street. Elbridge and his wife saw it coming. A few weeks before that Monday they spoke with Edson's wife, and she told them, \"I … suspect that he was losing control of his mind through long suffering.\" His personal secretary said he had never heard him say anything nasty or unkind about anyone. That was Edson Keith: the gentle brother, the one who never raised his voice. Elbridge is up early this morning too, and he still passes his brother's door. Walk north up Prairie, the way Edson went.",
                 evidence=['keith-warning', 'keith-kind', 'ekeith-marker', 'keith-houses'],
                 links=[('person', 'pa1904_keith_elbridge_g', 'Elbridge G. Keith'), ('person', 'pa1904_keith_mrs_elbridge_g', 'Mrs. Elbridge G. Keith')],
                 caption="Elbridge Keith comes down his steps in the half light, and his wife watches him go from the door.",
                 cast=lambda: [
                     cast('pa1904_keith_elbridge_g', at(BK, 1.6, 0.3), face=at(BK, 9, 0), hidden=True, beats=[beat(3, show=True), beat(5, walk=[at(BK, 5, 0.3), at(BK, 10.2, 2), at(BK, 10.6, 34)], pace='walk')]),
                     cast('pa1904_keith_mrs_elbridge_g', at(BK, 1.5, -0.7), face=at(BK, 9, 0), hidden=True, beats=[beat(4, show=True), beat(7, walk=[at(BK, 3, -0.6)], pace='slow'), beat(12, face=at(BK, 10.6, 30))]),
                 ]),
            dict(id='firm', dest=('structure', OK),
                 text="1808 Prairie, the Osborn R. Keith house. He and Albert Faxon founded the family firm on Lake Street in 1858, and by the 1880s Edson Keith & Company was selling $4.5 million a year, with two hundred people in Chicago and five hundred more in a Milwaukee factory. Three Keith houses on one street, and a fortune. In 1904 the house is Stanley Field's, but the street still calls it a Keith house. Edson walked past it in the dark that Monday, going north, toward the lake. It is a long walk for a sick man. The house will be razed in 1968, all but the north wall that screens the Glessner courtyard. Keep going north to Sixteenth Street.",
                 evidence=['keith-kind', 'stanley-1808', 'keith-razed'],
                 caption="A milkman's boy runs the morning round past 1808, the only other soul on the street.",
                 cast=lambda: [
                     extra('milk_boy', 'errand_1904', 'An errand boy on the morning round (unnamed)', at(OK, 10.4, -26), beats=[beat(0, walk=[at(OK, 10.4, 30)], pace='brisk')]),
                 ]),
            dict(id='lake', dest=('structure', N3),
                 text="Sixteenth Street, at the north end of the avenue. East of here, past the railroad, is the lake. This is as far as the street goes. Edson Keith went on. On the beach that Monday morning someone found a hat and a coat. Fishermen on the beach told what they had seen. The papers do not agree where: one says the foot of Sixteenth Street, another the foot of Thirteenth. All day Monday they searched. The servants worked it out only on Tuesday, when they read it in the newspaper. Stand here and look east at first light. The lake is grey and flat and very large, and it has never given back anything it did not want to.",
                 evidence=['keith-night', 'keith-death', 'keith-argus'],
                 caption="A lone gentleman in a hat and coat walks east along Sixteenth Street toward the lake and does not look back.",
                 cast=lambda: [
                     extra('walker', 'gentleman_1904', 'A gentleman walking east (unnamed; not Edson Keith, who died in 1896)', at(N3, 14, 12), beats=[beat(2, walk=[at(N3, 16, 26), at(N3, 40, 30)], pace='slow')]),
                 ]),
        ],
        legs=[
            dict(story="North two doors, as he went, to his brother Elbridge's house.", evidence=['keith-houses'], story_evidence=['keith-warning']),
            dict(story="North up Prairie Avenue in the half light, past the houses of the old firm.", evidence=['keith-kind'], story_evidence=['keith-kind']),
            dict(story="North all the way to Sixteenth Street, the long walk toward the lake.", evidence=['keith-death'], story_evidence=['keith-death']),
        ],
        endings=[dict(id='dragged', text="End of the walk. The news came to the family \"with paralyzing suddenness\", and the dispatch reported that \"the lake is now being dragged for the recovery of the remains.\" Edson Keith had made his will the year before, leaving $300,000 each to his wife Susan and their two sons. His wife stayed on at 1906 Prairie, and his brother next door. The street remembers him as the gentle brother, the one who never said an unkind word about anyone, who walked out of his own front door at six one Monday morning and went to the lake.")],
    ))
    return out


SRC_SECOND = 'chicago_treasure_houses_2017_second_mrs_field'
CGY_SRC = 'chicagology_1612_prairie_occupants'
