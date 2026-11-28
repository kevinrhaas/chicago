# SPDX-License-Identifier: GPL-3.0-or-later
"""The claims of the Great Chicago Fire jaunt (T-3691): every fact and hour its stops tell, each
with its source and locator (build.py reads this).

Three books, read in the Internet Archive's plain-text OCR of each scan (2026-11-19). A quotation
is the OCR read as corrected where the machine misread a letter ("lire" for "fire"); nothing else
in a quotation is changed. Printed page numbers are read from the running heads.

  A  Andreas, History of Chicago, vol. II (1885): the inquiry's report and the October 1871
     affidavits it prints; the firemen's and neighbours' statements to Andreas and C. C. P.
     Holden; Holden's timetable; Bross's, White's and Mayor Mason's narratives.
  S  Sheahan and Upton, The Great Conflagration (1871), including the inquiry testimony of
     November 1871 as the papers reported it.
  C  Colbert and Chamberlin, Chicago and the Great Conflagration (1871).

An hour is `attested` where the source gives it, and `inferred`, with its reasoning, where it is
read from the order of events (the fire's clock is a stop's date and hour, T-3687).
"""

A = 'andreas_1885_v2'
S = 'sheahan_upton_1871_great_conflagration'
C = 'colbert_chamberlin_1871_chicago_great_conflagration'
LIBERTY = 'L-1871-great-fire-jaunt'
AV = 'Andreas vol. II (1885), Internet Archive historyofchicago02andr plain-text OCR read as corrected'
SV = 'Sheahan and Upton (1871), Internet Archive cu31924028806855 plain-text OCR read as corrected'
CV = 'Colbert and Chamberlin (1871), Internet Archive cu31924028806814 plain-text OCR read as corrected'


def att(src, loc, text):
    return {'text': text, 'confidence': 'attested', 'sources': [src] if isinstance(src, str) else src, 'locator': loc}


def inf(src, text, reasoning):
    return {'text': text, 'confidence': 'inferred', 'sources': [src] if isinstance(src, str) else src, 'reasoning': reasoning}


CLAIMS = {
    # ── the night, the weather, the firemen ─────────────────────────────────────────────────
    'drought': att(A, f'p. 702, {AV}: the drought of 1871',
        'Andreas: "One and a half inches of rain fell in Chicago on the 3d of July, but from that date to the time of the fire, '
        'on the 9th of October, only two and a half inches fell, whereas the quantity falling in that line had averaged eight '
        'and three-quarter inches in former years."'),
    'wind': att(A, f'p. 709, {AV}: the report of the Board of Police and Fire Commissioners, 1871',
        'The Board of Police and Fire Commissioners, reporting on the inquiry: the fire spread "with the wind then blowing '
        'strongly from the southwest, and carrying the fire from building to building in a neighborhood composed wholly of dry '
        'wooden buildings, with wood shavings piled in every barn and under every house". The firemen were worn out: "A large '
        'part of the Department had worked on Saturday night, and Sunday until 3 p. m.", eighteen hours on end, "and they were '
        'nearly exhausted when this fire commenced". The firemen could not "prevent the wind, which soon became a gale, from '
        'carrying burning shingles and brands over their heads".'),
    # ── 1 the barn ───────────────────────────────────────────────────────────────────────────
    'barn': att(A, f'pp. 707-708, {AV}: the opening of "The Great Conflagration"',
        'Andreas: "About fifteen minutes before nine o\'clock on the evening of Sunday, October 8, 1871, fire was discovered in '
        'a barn on the rear of lot No. 137 DeKoven Street. The property was owned by Patrick O\'Leary." The barn "contained '
        'several cows, a calf and a horse, all belonging to the O\'Leary family. Mrs. O\'Leary was engaged in the business of '
        'supplying milk to neighboring families." Its upper part "had recently been filled with hay". Patrick and Catharine '
        'O\'Leary signed their affidavit of 15 October 1871 with their marks (Andreas spells her Catharine; she is the '
        'Catherine of the legend).'),
    'legend': att(A, f'p. 708, {AV}: "The Origin of the Fire"',
        'Andreas: "For all time, the legend of Mrs. O\'Leary\'s cow will be accepted. While the city was still enveloped in '
        'flames, some now-forgotten tongue declared that Mrs. O\'Leary was engaged in milking a cow, when the unruly animal '
        'kicked over a lighted lamp, and so ignited the straw and refuse on the barn floor". "There is no proof that Mrs. '
        'O\'Leary is responsible for the fire."'),
    'inquiry': att(A, f'p. 709, {AV}: the Board\'s report on the inquiry begun 23 November 1871',
        'The Board of Police and Fire Commissioners found "that the fire originated in a two-story barn in the rear of No. 137 '
        'DeKoven Street", first seen by "a drayman by the name of Daniel [Dennis] Sullivan". "There is no proof that any person '
        'had been in the barn after nightfall that evening." "Mr. O\'Leary and all his family prove to have been in bed and '
        'asleep at the time."'),
    'sullivan': att(S, f'pp. 427-428, {SV}: the testimony of Daniel Sullivan, of No. 134 DeKoven Street, before the commissioners',
        'Daniel Sullivan, of No. 134 DeKoven Street, testified that from across the street he saw fire in O\'Leary\'s barn. '
        '"He ran across the street as fast as he could — he has a wooden leg — and cried out "Fire" as loud as he could". He cut '
        'two cows loose, but they would not leave; "his wooden leg went between two boards", and "just then saw a calf with a '
        'rope around its neck. The hair on its back was on fire". He pulled it out of the barn.'),
    'lee': att(A, f'pp. 714-715, {AV}: the statement of William Lee, of No. 133 DeKoven Street',
        'William Lee, "two doors east of the O\'Leary cottage", saw "fire coming out of the roof" of the O\'Leary barn, and ran '
        'to "Bruno Goll\'s drug store, on the corner of Canal and Twelfth streets", for the key to the alarm box; the druggist '
        'would not give it to him. "Mr. Lee returned to his house. The clock struck nine." The calf, "the only animal saved from '
        'the O\'Leary barn", stood all night beside the Lees\' baby in its cradle in a vacant lot across the street.'),
    # ── 2 the church and the mills ───────────────────────────────────────────────────────────
    'alarm': att(A, f'pp. 711-712, {AV}: the statements of Mathias Schaffer and John Campion',
        '"Mathias Schaffer, the watchman in the tower, says that it was 9:28 p. m., when he first discovered the light of the '
        'fire. Observing it through his spy-glass, he located the scene near the corner of Canalport Avenue and Halsted Street, '
        'and rang up the night operator, signaling him to give Box 342." John Campion, of the "Little Giant": "The alarm first '
        'received from the Court-house tower was for Box 342, which was nearly a mile from the fire".'),
    'little-giant': att(A, f'p. 711, {AV}: the statement of William Musham, foreman of the "Little Giant" No. 6',
        'The "Little Giant", engine No. 6, took the plug at DeKoven and Jefferson streets and laid its hose through Patrick '
        'O\'Leary\'s lot: "For more than thirty minutes this engine battled alone." Its foreman, William Musham: "It was too much '
        'for us."'),
    'riley': att(A, f'pp. 715-716, {AV}: the statement of Richard Riley',
        'Richard Riley, "a railroad contractor", watched from a pile of lumber at Taylor and Canal streets: "A large mass of '
        'fire, seemingly two feet in length and one foot in thickness, arose from a spot just north of Taylor Street, and went '
        'whirling through the air for more than three blocks, alighting on the cupola of the German Catholic Church, on the '
        'northeast corner of Mather and Clinton streets. The entire building was almost instantaneously enveloped in flames."'),
    'st-pauls': inf(A,
        'The church at Clinton and Mather streets that the brand fell on was St. Paul\'s, the German Catholic parish church.',
        'Andreas, vol. II p. 406: "St. Paul\'s Church was established in 1868, at the corner of Mather and Clinton streets, by '
        'members from the Church of St. Francis D\'Assissium" (a German parish) and served "until the buildings were destroyed '
        'by the great fire occurring that year"; Riley (p. 715) calls the church on that corner "the German Catholic Church". The '
        'same corner and the same fire make them one church.'),
    'bateham': att(A, f'pp. 717-718, {AV}: the statement of William B. Bateham',
        'William B. Bateham, "member of the Common Council in 1871", owned the mills on Canal Street south of Harrison, with "a '
        'thousand cords of fire-kindling wood, in piles twenty-five feet high" in the yard. "At ten o\'clock it looked as if '
        'this were possible, for the church had gone down in ruins in advance of the main body of flame." "At half-past ten, the '
        'heroic men were driven from Bateham\'s works by the intense heat. As Mr. Bateham turned from his property he remarked: '
        '"The materials from this mill will fire the South Side, and nothing can prevent it now.""'),
    # ── 3 across the South Branch ────────────────────────────────────────────────────────────
    'parmelee': att(A, f'p. 719, {AV}: "The Fire crosses to the South Side"',
        'Andreas: "From as early as half-past nine, showers of sparks and burning brands fell upon the South Side". "The first '
        'building to ignite on the South Side was the new stable owned by the Parmelee Omnibus and Stage Company, situated on '
        'southeast corner of Jackson and Franklin streets. This spacious structure had just been completed at an expense of '
        '$80,000, and would have been occupied for the first time on Wednesday, October 11. The building was the finest of its '
        'kind in the country." J. W. Parmelee and J. E. Sullivan were at the stable: "At half-past eleven, October 8, 1871, the '
        'fire swept down upon them with such rapidity and terrific force as to compel them to flee for their lives."'),
    'gasworks': att(A, f'pp. 719-720, {AV}: Holden\'s timetable, and Colbert as Andreas quotes him',
        'Holden\'s timetable: "At about twelve o\'clock, the gas works and "Conley\'s Patch" were on fire." Colbert, quoted by '
        'Andreas, puts the first South Side fire "in a building of the South Division gas works on Adams Street", and asks of '
        'what lay beyond the shanties of Conley\'s Patch, "along LaSalle Street", a "splendid double row of "fire-proof" '
        'mercantile buildings": "Would these succumb to the shower of brands and the triple-heated furnace which had been thrown '
        'about them?"'),
    # ── 4 the Court House ────────────────────────────────────────────────────────────────────
    'tower': att(A, f'pp. 724-725, {AV}: the burning of the Court House; Mathias Schaffer\'s statement',
        'Mathias Schaffer, the watchman in the Court House tower, "was relieved at eleven o\'clock by Dennis Denene, but remained '
        'in the tower. By ten o\'clock, cinders and burning materials were seen flying over the South Side. The roof of the '
        'Court House caught fire five or six times before he left the building, which was at half-past one. He used two Babcock '
        'fire-extinguishers." "Schaffer and Denene caused the Court-house bell to be rung constantly until they were driven from '
        'the tower." The bell "weighed 10,849 pounds".'),
    'mason': att(A, f'p. 725, {AV}: Mayor Mason\'s statement; the volume\'s index (Mason, Roswell B.)',
        'The mayor, Roswell B. Mason (Andreas\'s index; "Mayor R. B. Mason" in the text): he "reached the Court House soon after '
        'twelve o\'clock. He was busily occupied giving orders from the office of the Police Commissioners, which was in the '
        'basement of the building. It was then that the mayor issued orders to Alderman J. H. Hildreth, to use powder in blowing '
        'up buildings, at about one a. m. The mayor also went to the jail, in the same basement, and ordered the prisoners '
        'removed to a place of safety." He stayed until "the famous bell came crashing and clanging down": "By this incident, we '
        'fix the instant of the falling of the bell at five minutes past two." In the street, LaSalle Street "appeared like a '
        'furnace, all fire".'),
    # T-3814: what the people in the streets carried, and the wagons (the stops' staging reads these).
    'goods': att(A, f'pp. 729, 734 and 746, {AV}: Horace White\'s narrative and a North Side narrative',
        'Andreas: "Sober men and women were hurrying through the streets from the burning quarter \u2014 some with bundles of '
        'clothing on their shoulders; others, dragging trunks along the sidewalk by means of strings and ropes fastened to the '
        'handles, children trudging by their sides or borne in their arms. Now and then a sick man or women would be observed, '
        'half concealed in a mattress doubled up and borne by two men." On the North Side at dawn: "I saw one man carrying the '
        'rubber tube and broken standard of a drop-light; another was trundling a wheelbarrow on which was a cook stove, while '
        'on his back was a huge feather bed. One woman had a live hen in her arms, several had cats, and numbers had canary birds '
        'in cages." And of the wagons: "Expressmen, and owners of every description of wagons, were extortionate in their '
        'demands, asking from twenty to fifty dollars for conveying a small load a few blocks."'),
    'prisoners': att(A, f'p. 725, {AV}: the county jail in the Court House basement',
        '"Captain Hickey, seeing that there was no hope of saving the building, ordered the cells to be unlocked, and in a moment '
        'the released prisoners, all bareheaded, many barefooted, rushed into the street, yelling like demons. A large truck, '
        'loaded with ready-made clothing, was passing the corner of Randolph Street at the time. In an instant the ex-prisoners '
        'swarmed upon it, emptied it of its contents". The men "charged with murder" were "securely handcuffed and led away '
        'between guards."'),
    # ── 5 the Sherman House ──────────────────────────────────────────────────────────────────
    'sherman': att(A, f'pp. 725-727, {AV}: Alonzo Hannis; a writer in the Post; W. S. Walker',
        'Alonzo Hannis crossed to the South Side "shortly after half-past eleven", when "men were trying to save the Sherman '
        'House, by tearing down awnings and other combustible materials." It was "the seven-story Sherman". A writer in the Post: '
        '"The woodwork and roof were smoking in places, but for nearly an hour the house held good. Suddenly, a spirit of flame '
        'came from a window in the third story on the southern face". W. S. Walker: "Upwards of three hundred guests were lodged '
        'there", with "only the night clerk and an assistant" left in charge, and of the ladies "five were so sick as to be '
        'confined to their beds."'),
    'sherman-hour': inf([S, A],
        'The Sherman House, across Clark Street from the Court House, was burning by about five past two on Monday morning.',
        'Sheahan and Upton (pp. 76-77): after the Court House dome fell, "The Sherman House was the next to go"; and (p. 105) '
        'before the Court House roof fell in at twenty past two, "about the time that the Sherman House was ablaze", the fire had '
        'reached the North Side. Andreas (p. 725) puts the bell\'s fall at five past two.'),
    # ── 6 Crosby's ───────────────────────────────────────────────────────────────────────────
    'crosbys': att(C, f'pp. 147-148, {CV}: the public buildings of 1865-1871',
        'Colbert and Chamberlin: "Crosby\'s Opera-house was completed in the summer of 1865. It stood on the north side of '
        'Washington Street", seating "2500 people"; "it cost $375,000". "In 1871 the Opera-house was also remodeled."'),
    'reopening': att(S, f'pp. 94-95, {SV}: the Crosby Opera House',
        'Sheahan and Upton, two Chicago newspapermen writing that autumn: "The Crosby Opera House, had been closed during the summer and fall for renovation. Its proprietor '
        'had expended $80,000 upon it in ornamentation, upholstery and frescoing. It was to have been reopened to the public on '
        'Monday evening, the night after the fire, by the Theodore Thomas orchestral troupe, and on Sunday evening, only an hour '
        'or two before the fire, it was lit up for the first time, that its effects might be seen by gaslight." "The carpet and '
        'upholstery were made expressly for it in France".'),
    'crosbys-falls': att([S, C], f'Sheahan and Upton pp. 77-78, {SV}; Colbert and Chamberlin p. 207, {CV}',
        'Colbert and Chamberlin: "From the Court-house the course of the main column seemed to tend eastward, and Hooley\'s '
        'Opera-house, the Times building, Crosby\'s magnificent Opera-house (to be re-opened that very night), fell rapidly before '
        'it." Sheahan and Upton: the fire "caught the roof of Crosby\'s Opera House. In almost the time it takes to write these '
        'lines, that noble building, with the handsomest operatic auditorium in the country", was destroyed, "while the St. James '
        'Hotel adjoining it on the east, which had two or three times before stood the test of fire, at last yielded and fell."'),
    'crosbys-hour': inf([C, A],
        'Crosby\'s Opera House was burning by about twenty past two on Monday morning.',
        'Colbert and Chamberlin (p. 207) have the main column turn east from the Court House and Crosby\'s fall "rapidly before '
        'it"; the Court House bell fell at five past two (Andreas p. 725). Some minutes after that is the earliest the column can '
        'have reached Washington Street between Dearborn and State.'),
    # ── 7 across the main river ──────────────────────────────────────────────────────────────
    'crossing': att(S, f'p. 105, {SV}: "The Fire in the North Division"',
        'Sheahan and Upton: "Precisely at twenty minutes past two o\'clock, the roof of the centre building of the Court House '
        'fell in, and before that event, and about the time that the Sherman House was ablaze, the fire, carried by the wind, had '
        'fallen upon the north side, and broke out just north of the bridge, at State street. North of the bridge was a long '
        'viaduct of wood, erected on trestle work."'),
    'wright': att(A, f'pp. 719 and 724, {AV}: Holden\'s timetable; Judge Tree',
        'Holden\'s timetable: "At not later than 1:30, Judge Lambert Tree crossed State-street bridge, which was then burning in '
        'spots. At 2:30, Wright\'s stable on the southeast corner of State and Kinzie streets, at the northern end of the viaduct, '
        'took fire." Tree lived on the North Side, "at the corner of Ohio and Cass streets".'),
    'mason-north': att(A, f'p. 725, {AV}: Mayor Mason\'s statement',
        'Cut off on the South Side, Mayor Mason and his son crossed by the Wells Street bridge to the North Side, and "inferred '
        'that the fire had attacked Wright\'s stables, just northeast of the State-street viaduct." They went on east to the Rush '
        'Street bridge, "which they reached ahead of the fire", and "reached their home at half-past four."'),
    'asleep': att(A, f'pp. 754-755, {AV}: the North Side',
        'Andreas: "The people of that section, for the most part, were awakened to a consciousness of peril only by finding '
        'themselves surrounded by fire." (The OCR reads "conif peril".)'),
    # ── 8 the Water Works ────────────────────────────────────────────────────────────────────
    'waterworks': att(A, f'pp. 741-742, {AV}: the burning of the Water Works',
        'Frank Trautman, the engineer, had his engines "running at the rate of thirty million gallons a day. The reservoir was '
        'full". "Soon after three o\'clock, D. W. Fuller, who was standing just north of the main building, noticed a fire-brand, '
        'apparently twelve feet in length, whirling through the air, directly toward the water-tower, located about one hundred '
        'and fifty feet west of the engine building." It struck the corner of the engine-house. "In an instant, the roof was '
        'aflame. Mr. Fuller glanced at his watch; the time was exactly twenty minutes past three." "A few minutes before four '
        'o\'clock, they were driven from the buildings by the intense heat."'),
    'one-works': att(A, f'pp. 709-710, {AV}: the Board\'s report',
        'The Board: "The single set of pumping works, upon which the salvation of the city depended, were roofed with wood, had '
        'no appliance by which water could be raised to the roof in case of fire". "After the Water Works burned, the firemen '
        'could do little good with their engines, except on the banks of the river."'),
    'water-tower': att(C, f'pp. 154-155, {CV}: the water tower and the lake tunnel',
        'Colbert and Chamberlin: the water tower "consists essentially of an iron column, three feet in internal diameter, and '
        '130 feet high, up which the water is forced by powerful pumps", and "The column is surrounded by a spiral stairway, '
        'inside a stone tower". Beside it were "buildings to contain the four pumping engines".'),
    'tower-stands': inf(C,
        'The stone Water Tower stood through the fire.',
        'Colbert and Chamberlin, writing weeks after the fire, describe the tower in the present tense: "It is situated about '
        'half a block west of the old pumping works, on the east end of Chicago Avenue" (p. 154), where of every building '
        'burned they write in the past; Andreas (p. 742) has the brand fly "toward the water-tower" and the engine-house roof, not '
        'the tower, catch.'),
    # ── 9 the Tribune ────────────────────────────────────────────────────────────────────────
    'bross': att(A, f'pp. 731-732, {AV}: the narrative of ex-Lieutenant-Governor Bross',
        'William Bross, "Ex-Lieutenant-Governor Bross" of Illinois and one of the Tribune\'s owners, reached home on Michigan '
        'Avenue toward five, as "the day was beginning to break", and "rode as fast as I could to the Tribune office. I found '
        'everything safe". The fire had "crawled under the sidewalk from the wooden pavement, and caught the woodwork of the '
        'barber\'s shop, which comprised a portion of our basement". They put it out "believing, as we did, that the building was '
        'fire-proof. My associates, Mr. Medill and Mr. White, were present, and, with the help of some of our employes, we went to '
        'work with water and one of Babcock\'s fire-extinguishers." "The forms had been sent down stairs", to issue the paper.'),
    'medill-white': att([A, C], f'Andreas p. 734, {AV}; Colbert and Chamberlin pp. 379-380, {CV}',
        'Andreas: "Mr. Horace White, at that time editor of the Tribune". Colbert and Chamberlin: "Joseph Medill, one of its '
        'chief stockholders (since elected mayor of the city)". The Tribune building stood "on the corner of Madison and Dearborn '
        'Streets" and was counted among the city\'s fire-proof buildings (Colbert and Chamberlin, p. 151).'),
    'tribune-falls': att([S, C], f'Sheahan and Upton pp. 78-79, {SV}; Colbert and Chamberlin p. 209, {CV}',
        'Sheahan and Upton: "The Tribune building, one of the noblest structures in the city, on the southeast corner of Dearborn '
        'and Madison streets, had already stood the test bravely." Then "far to the south the flames had seized the huge '
        'eight-story Palmer House, and came sweeping northward with fearful rapidity to McVicker\'s Theatre, separated from the '
        'east wall of the Tribune building only by a narrow alley. This new onset of the fire was irresistible." "Its roof '
        'yielded. The iron shutters on the alley side, bent by the fire, sprung out of place". Colbert and Chamberlin: "It '
        'surrounded the fated structure, and ruined it too."'),
    'tribune-hour': inf([C, A],
        'The Tribune building was lost at about half past seven on Monday morning.',
        'Colbert and Chamberlin (p. 209) give "half-past seven in the evening", but the building\'s own owner found it standing at '
        'daybreak and the fire back upon it that morning (Bross, in Andreas pp. 731-732), and the paper was then printed elsewhere; '
        'the hour is theirs and the morning is Bross\'s.'),
    # ── 10 State Street ──────────────────────────────────────────────────────────────────────
    'palmer': att([C, A], f'Colbert and Chamberlin pp. 209-210, {CV}; Andreas vol. II, "Hotels", the Palmer House, {AV}',
        'Colbert and Chamberlin: the fire "fell upon Potter Palmer\'s store of Massachusetts marble, for which Field, Leiter & '
        'Co., dry goods importers, were paying the owner $52,000 a year rent. This splendid building, with such of its contents as '
        'had not been removed in wagons, went like all the rest." Andreas: "The Palmer House was built in 1869-70, by Potter '
        'Palmer, at the northwest corner of State and Quincy streets", a hotel "with handsome stone fronts".'),
    'field-leiter': att([A, S], f'Andreas pp. 734-735 (Horace White\'s narrative), {AV}; Sheahan and Upton p. 79, {SV}',
        'Horace White, after daylight, saw "that the employes of Messrs. Field, Leiter & Co.\'s immense dry goods store were '
        'showering that massive pile of pure marble and iron with water from their own pumping engines." Later, at State Street, '
        '"the streams of water, which had before been showering it as though it had been a great artificial fountain, had ceased '
        'to run." "But why were men carrying out goods from the lower story?" Sheahan and Upton: "At Field & Leiter\'s mammoth '
        'establishment, on the corner of State and Washington streets, a determined effort was made to save the building but it '
        'was useless. The flames attacked it from the north and eastwardly in the rear, and it soon yielded."'),
    'field-hour': inf([C, A],
        'Field, Leiter & Co.\'s store was burning by about eight on Monday morning.',
        'Colbert and Chamberlin (pp. 209-210) take the fire from the Tribune building through Booksellers\' Row to Potter Palmer\'s '
        'store, in that order; Horace White saw the store\'s own streams playing after daylight and stopped by the time he came '
        'back from breakfast (Andreas p. 735). After the Tribune (about half past seven) and after breakfast makes about eight.'),
    # ── 11 the North Side ────────────────────────────────────────────────────────────────────
    'ogden': att([S, C], f'Sheahan and Upton pp. 209-211, {SV}; Colbert and Chamberlin p. 348, {CV}',
        'Colbert and Chamberlin: "the residence of Mahlon D. Ogden, brother of Wm. B. Ogden", which "faces Washington Park", and '
        '"the Ogden mansion is of wood". Sheahan and Upton: "Its escape is a marvel." "In front of the house and between it and '
        'the approaching fire was a small park — just one vacant block. But this park early in the night was filled with fugitives '
        'and their furniture." The men left in the house "tore up the carpets, and used all the blankets on the premises. These '
        'they spread over the fronts of the house and of the barn exposed to the fire", and kept them wet; when the hydrant failed, "Several barrels of cider were used to saturate the carpets". "In front was the '
        'grand blaze from the accumulated furniture of fifty families." By dawn the fire had passed north, "leaving nothing but '
        'this solitary building in an area of 2,600 acres."'),
    'first-mayor': att(S, f'p. 28, {SV}: the city charter of 1837',
        'Sheahan and Upton: "In 1837 the Legislature incorporated the City of Chicago, and in May following the Hon. William B. '
        'Ogden was elected Mayor of Chicago."'),
    'st-michaels': att(A, f'p. 405, {AV}: St. Michael\'s Church',
        'St. Michael\'s, the German congregation of the Redemptorist Fathers, built at Hurlbut and Linden streets "a very large '
        'brick building two hundred feet long by eighty feet wide, with a tower surmounted by a low steeple containing a chime of '
        'bells". In the great fire its walls "remained substantially intact. The steeple, however, was burned, and the bells fell '
        'to the ground."'),
    'monday': att(A, f'p. 737, {AV}: the North Side on Monday',
        'Andreas: "The day of the 9th (Monday) was one of excitement and dread. On the North Side, all the people were still '
        'flying from the scourge which pursued them."'),
    'ogden-hour': inf([S, A],
        'At midday on Monday the Ogden house stood alone, and the fire was burning north toward North Avenue.',
        'Sheahan and Upton (p. 210): the house was saved by dawn, after "three or four hours of hard labor". The fire burned on '
        'north all Monday (Andreas p. 737) and took both sides of North Avenue before it reached the groves beyond (p. 757); St. '
        'Michael\'s stood near North Avenue. Midday is a time inside that day, not a recorded hour.'),
    # ── 12 the refugees ──────────────────────────────────────────────────────────────────────
    'cemetery': att(C, f'pp. 265-268, {CV}: "The Night after the Fire"',
        'Colbert and Chamberlin: the refugees were at "Lincoln Park and the old cemetery to the south of it, and along the '
        'Lake-shore Drive", "compelled to see the household gods and valuables which they had moved into the cemetery or the park '
        'burn up before their eyes." "It is an old burial-ground, from which many of the bodies had been removed, leaving some old '
        'headstones scattered about", graves standing "among the thick undergrowth of grass and small oak trees". The refugees '
        'were "blinded by smoke, weakened by hunger, and choking with thirst". "By nightfall on Monday there could not have been less than thirty thousand men, women, and '
        'children, huddled within this ghostly inclosure."'),
    'chapel-chairs': att(A, f'p. 737, {AV}: a North Side narrative',
        'On the lake shore: "Ladies were seen moving their chairs into the water, and sitting on the top of the backs, while '
        'resting their feet on the seats of the chairs." At Lincoln Park the fire came "entering this area of solitude, in which '
        'stood the old chapel of the cemetery, built of brick", and "desolated and scorched that structure. This chapel was '
        'surrounded by no buildings".'),
    'beach': att(S, f'pp. 113-114, {SV}: the North Division beach',
        'Sheahan and Upton: "Along the beach were judges, merchants, doctors, workingmen, women and children".'),
    'the-lost': att(S, f'pp. 113-114, {SV}: the flight from the North Division',
        'Sheahan and Upton, of the North Side in the night: on the beach, "Hemmed in between pier and lumber yard, were many '
        'fugitives, men, women and children, of whom many are known to have perished, and it is feared the number is very great." '
        '"The clothing of the women was repeatedly on fire, and bundles of rescued articles had to be thrown into the lake to '
        'extinguish them." Among the houses of the poor to the west, "Here and there sidewalks would fall in, precipitating all '
        'upon them into the vaults beneath. It is assumed, that of necessity, many hundreds perished in this flight." "In a '
        'district embracing 75,000 people, there were necessarily many who were upon beds of sickness." The number of those who '
        'perished there, "whole families", "will never be known." (Their "many hundreds" is a guess of that week; Colbert and '
        'Chamberlin\'s count is more than 250 dead in all.)'),
    'prairie': att(A, f'p. 757, {AV}: the fugitives',
        'Thousands fled west and north-west over the North Branch bridges: "After reaching the prairie, the army of fugitives '
        'settled down, wherever they could find room."'),
    'cemetery-hour': inf(C,
        'The refugees in the cemetery are seen at nightfall on Monday, about half past six.',
        'Colbert and Chamberlin count the cemetery\'s thirty thousand "By nightfall on Monday" (p. 266); the sun set a little '
        'before half past five that day, and full dark is an hour later.'),
    # ── the ending ───────────────────────────────────────────────────────────────────────────
    'end': att(A, f'pp. 754-755, {AV}: a North Side narrative',
        '"The fire finally spent itself in burning the residence of Dr. John H. Foster, on the north end of Lincoln Park, as then '
        'located, being on Fullerton Avenue." "As nearly as I can learn, his house was burned at half past ten o\'clock on Monday '
        'night — just twenty-five hours from the commencement of the fire, and about four miles distant from the place of its '
        'origin."'),
    'rain': att(A, f'p. 757, {AV}: the fugitives on the prairie',
        'Andreas: "About eleven o\'clock Monday night, the sky, as if in remorse at what the fiery element had done, poured down '
        'floods of rain." The refugees on the prairie, "Hungry, fatigued, worn out in body and fainting in soul", were "subjected '
        'to a penetrating rainstorm". "The rain, which began about eleven o\'clock Monday night, effected a perceptible check on the flames."'),
    'toll': att(C, f'pp. 287-288, {CV}: the burnt district',
        'Colbert and Chamberlin: "The total area burned over in the city, including streets, was 2124 acres". "The number of '
        'buildings destroyed was 17,450; of persons rendered homeless, 98,500. Of the latter, more than 250 paid the last debt of '
        'nature".'),
    'proclamation': att(S, f'p. 104, {SV}: "the first proclamation of the Mayor of the city"',
        'Mayor Mason\'s first proclamation, as Sheahan and Upton print it: "Be it known, That the faith and credit of the City of '
        'Chicago is hereby pledged for the necessary expenses for the relief of the suffering. Public order will be preserved." It '
        'ends: "It is believed the fire has spent its force and all will soon be well. R. B. Mason, Mayor."'),
}


def staging(title):
    """The jaunt's reconstruction, declared: where the stands are, who is on the streets and how they move."""
    return {
        'stand': {
            'text': 'Each stop is watched from a reconstructed stand in the street, at a distance where the building and the fire '
                    'read: its corner from the modern street grid (the corners survive), not a surveyed 1871 point.',
            'confidence': 'reconstructed', 'sources': [], 'liberty': LIBERTY},
        'stage': {
            'text': f'{title}: the people on the streets at each stop are unnamed figures standing for the crowds the accounts '
                    'describe, watching, carrying what they can, and getting away. Where each stands, when each moves and how, '
                    'what each carries (bundles, trunks, bird cages, feather beds, bolts of cloth: the kinds the accounts list, '
                    'their make drawn plainly), the wagons and their loads, '
                    'and the clothes they are drawn in (the town\'s 1835 and 1904 wardrobes, until 1871 dress is drawn) are '
                    'reconstruction. Nobody is shown hurt.',
            'confidence': 'reconstructed', 'sources': [], 'liberty': LIBERTY},
    }
