# SPDX-License-Identifier: GPL-3.0-or-later
"""The claims the ten 1904 story jaunts stand on (build.py).

Each claim is one statement a stop, a leg or an ending rests on, with the sources it was read
from and where in them. A quotation in a jaunt's words must stand verbatim in an attested claim
it cites (tools/audit_jaunt_refusals.py, rule Q), so every quoted fragment the stories use is
copied here from the source's own text as read on 2026-11-15. Claims already carried by another
1904 jaunt are BORROWED by id (`borrow`), so the same fact is worded and located one way.
"""

LIBERTY = 'L-1904-story-jaunts'

# (jaunt id, claim id) -> borrowed claim, copied whole from that jaunt at build time.
BORROW = {
    'field-rich': 'prairie-ghosts-at-night', 'field-razed': 'prairie-ghosts-at-night',
    'fieldjr-shot': 'prairie-ghosts-at-night', 'fieldjr-rumour': 'prairie-ghosts-at-night',
    'fieldjr-listing': 'prairie-ghosts-at-night', 'fieldjr-marker': 'prairie-ghosts-at-night',
    'pullman-raise': 'prairie-ghosts-at-night', 'pullman-strike': 'prairie-ghosts-at-night',
    'pullman-grave': 'prairie-ghosts-at-night', 'pullman-widow': 'prairie-ghosts-at-night',
    'pullman-glare': 'prairie-ghosts-at-night', 'pullman-razed': 'prairie-ghosts-at-night',
    'battle-statue': 'prairie-ghosts-at-night', 'battle-ground': 'prairie-ghosts-at-night', 'battle-bones': 'prairie-ghosts-at-night',
    'kimball-start': 'prairie-ghosts-at-night', 'keith-houses': 'prairie-ghosts-at-night',
    'keith-death': 'prairie-ghosts-at-night', 'keith-same': 'prairie-ghosts-at-night',
    'ekeith-marker': 'prairie-ghosts-at-night', 'lee-nutshell': 'prairie-ghosts-at-night',
    'richardson-dates': 'prairie-ghosts-at-night',
    'reading-class': 'glessner-household-tour', 'journal-silver': 'glessner-household-tour',
    'frances-born': 'glessner-household-tour', 'neighbours': 'glessner-household-tour',
    'yellow-glass': 'glessner-household-tour', 'narrow-windows': 'glessner-household-tour',
    'servants-unseen': 'glessner-household-tour', 'mattie-cake': 'glessner-household-tour',
    'creeper': 'glessner-household-tour', 'john-machines': 'glessner-household-tour',
}

OTHER_MRS = 'chicago_treasure_houses_2017_other_mrs_field'
SECOND_MRS = 'chicago_treasure_houses_2017_second_mrs_field'
LADIES = 'chicago_treasure_houses_2017_other_ladies'
CGY = 'chicagology_1612_prairie_occupants'
TWINS = 'pullman_museum_twins_page'
BEHRING = 'pullman_museum_behring_page'
GH = 'glessner_house_family_page'


def A(text, sources, locator):
    return {'text': text, 'confidence': 'attested', 'sources': sources, 'locator': locator}


def I(text, sources, reasoning):
    return {'text': text, 'confidence': 'inferred', 'sources': sources, 'reasoning': reasoning}


CLAIMS = {
    # ── 1. The widow behind Marshall Field's house ──────────────────────────────────────────
    'caton-death': A("Arthur J. Caton died 'November 18, 1904, at New York's Waldorf-Astoria hotel'. 'The cause of death was inexact. Some said he succumbed to liver failure. Others ascribed the demise to peritonitis.' An Ottawa, Illinois Times story suggested he may have taken his own life.",
                     [OTHER_MRS], "The post's last paragraph."),
    'caton-family': A("Delia Spencer, the daughter of one of the founders of the Hibbard, Spencer & Bartlett hardware firm, married Arthur Caton in 1876. He was the son of Judge John Dean Caton, one of Illinois' first chief justices; a lawyer, sportsman and clubman, he loved golf and polo and bred horses and dogs on the family's Ottawa farm.",
                      [OTHER_MRS, SECOND_MRS], "Other Mrs. Field: the paragraphs on Delia and the Catons; Second Mrs. Field: 'Delia Spencer married Arthur Caton in 1876.'"),
    'caton-parties': A("Arthur Meeker's mother 'always declared that nobody ever gave such wonderful parties as Delia Caton'. The Catons had no children and entertained in 'their big, elaborate house on Calumet Avenue'.",
                       [SECOND_MRS], "The paragraph quoting Meeker on the Catons' entertaining."),
    'tunnel': A("Arthur Meeker: 'The gossip of the day cast the worst light on the affair; it was even absurdly asserted that an underground tunnel connected the Caton house on Calumet with the Field house on Prairie, which was just in front of it, or just back.'",
                [SECOND_MRS, OTHER_MRS], "Second Mrs. Field: the Meeker paragraph; Other Mrs. Field: the Beveridge Chronicle's 'subterranean tunnel'."),
    'europe': A("There were rumours that Field and Delia Caton were lovers for nearly 30 years, and 'Delia sometimes traveled to Europe with Marshall Field without Arthur accompanying them.'",
                [OTHER_MRS], "The paragraph quoting The Chronicle of Catherine Eddy Beveridge."),
    'nannie': A("Field proposed to Nannie Douglas Scott by jumping aboard her train as it left Chicago; he got off at the next stop and walked back to work. Their marriage foundered: by Longstreet's account 'Mrs. Field led Marshall Field a hell-on-earth life'. Nannie took to the South of France, and died in France in 1896.",
                [OTHER_MRS], "The post's opening paragraphs and the paragraph on Nannie's death."),
    'white-sale': A("Field was reluctant to make a speech at one of the Catons' grand dinners, and Delia sprang to her feet and said: Mr. Field just wants me to remind you that the White Sale starts next Monday.",
                    [SECOND_MRS], "The paragraph quoting Meeker, Chicago, With Love."),
    'fell-in-love': A("Meeker: 'he fell in love with his friend's wife years before he was able to marry her.' And: 'In the Nineties, divorce was unthinkable: they had to wait for him (Arthur Caton) to die, which, distressingly, he didn't do until 1904.'",
                      [SECOND_MRS], "The Meeker paragraphs."),
    'london': A("The marriage licence acquired in London in 1905 gave Delia as 46 and Field as 70. They married at St. Margaret's, Westminster; 'The ceremony was quiet, and attended only by a few friends.' Field died in 1906 of pneumonia after a round of golf in a foursome that included Robert Todd Lincoln. Delia was left $1 million and the Field mansion on Prairie Avenue, moved to Washington, D.C., where her house was known as the Pink Palace, and died in 1937.",
                [SECOND_MRS, 'wikipedia_marshall_field'], "Second Mrs. Field: the paragraphs on the marriage and after; Wikipedia: the death on 16 January 1906."),
    'field-staff': A("The census of 1 June 1900 enumerated John Dunford, coachman, born in England, as the head of his own household in the rear building behind 1905 Prairie, and Thomas Benson, butler, born in Ireland, in the house.",
                     ['census_1900_chicago_t623_roll245'], "ED 40, sheet 4A, lines 38-39, leaf n800."),
    # ── 2. The divorce at 1612 Prairie ──────────────────────────────────────────────────────
    'brown-suit': A("Catherine G. Brown was the 'former wife of Charles E. Brown, 1612 Prairie avenue'. Mrs. Brown, who is 27 years old and the daughter of Gen. Graves, a wealthy resident of Buffalo, first attracted notoriety in May, 1904, when her husband filed a bill for divorce. By a court order issued by Judge Tuley Mrs. Brown was given possession of the residence, 1612 Prairie avenue, where she and her husband and their son had lived, and was granted temporary alimony amounting to $200 a month while the suit was pending. Habitual drunkenness and statutory charges were the grounds.",
                    [CGY], "Chicago Tribune, 11 March 1905, 'Story of Divorce Case', as transcribed."),
    'brown-november': A("In November Mr. Brown appeared in court and charged that his wife had conducted herself in a disgraceful manner, had been habitually intoxicated, and had done many freakish things, such as playing a violin in a broken automobile while a man pushed the machine along a public highway, and dancing about the rear of their home clothed only in a nightrobe.",
                        [CGY], "Chicago Tribune, 11 March 1905, 'Story of Divorce Case', as transcribed."),
    'brown-edsall': A("He also charged her with receiving the attentions of E. C. Edsall, an automobile salesman. With Edsall, the husband charged, Mrs. Brown ran away to an eastern summer resort and later to New York City.",
                      [CGY], "Chicago Tribune, 11 March 1905, as transcribed."),
    'brown-decree': A("After a bitter fight Mr. Brown was granted a divorce about six weeks before 11 March 1905, and given possession of the Prairie avenue property, and the custody of the one son, Charles Edward Brown.",
                      [CGY], "Chicago Tribune, 11 March 1905, the last paragraph, as transcribed."),
    'brown-arrest': A("In March 1905 Mrs. Catherine G. Brown was arrested at 3667 Wabash avenue, where she had been living under the name of Kittie Casey, according to the police, and fined $85 for disorderly conduct. 'I am penniless,' she said. 'I cannot pay the fine.' In her cell she said: 'It's all because a woman is jealous of me, I guess.' Justice Hurley called her 'a problem in humanity to me.'",
                      [CGY], "Chicago Tribune, 11 March 1905, as transcribed."),
    'brown-sale': A("On 8 March 1905 the lot at 1612 Prairie passed from Brown (printed 'Chas. S. Brown') to the Rt. Rev. Chas. Palmerston Anderson, bishop of the Protestant Episcopal church in the diocese of Chicago.",
                    [CGY], "Chicago Tribune, 14 March 1905, the transfer list, as transcribed."),
    'studebaker-1884': A("On 21 February 1884 about 200 of the intimate friends and relatives of the bride and groom were received at the residence of W. F. Studebaker, No. 1612 Prairie avenue, after the Studebaker-Innis wedding. 'The large residence was brilliantly illuminated, and every room was elaborately decorated with smilax and cut flowers.'",
                         [CGY], "Chicago Tribune, 22 February 1884, 'Wedding Bells', as transcribed."),
    'studebaker-1887': A("Inter Ocean, 2 January 1887: 'Morning and night, a showy turnout is noticed before the squarely-built house, with the number 1612 over the portals.' Its owner was one of the Studebaker Brothers, the carriage makers.",
                         [CGY], "Inter Ocean, 2 January 1887, as transcribed."),
    'goodman-razed': A("Joseph Goodman Residence, 1612 S. Prairie Avenue: razed circa 1960.",
                       ['hmdb_prairie_lost_houses_1600_1700'], "The 1612 S. Prairie Avenue entry."),
    # ── 3. The young wife at 1700 Prairie ───────────────────────────────────────────────────
    'fanny-young': A("Fanny Glessner was born on 25 March 1878, the youngest child and only daughter, and was tutored at home. She toured Europe for fourteen months in 1896 and 1897 with her aunt Helen Macbeth, made her debut in November 1897, and on 9 February 1898 married Blewett Lee, a law partner of one of her brother George's friends.",
                     [GH], "The biography of Frances Glessner Lee."),
    'lee-at-19': A("She married a young attorney, Blewett Lee, at 19. 'The couple had three children and at first appeared happy, but Glessner Lee eventually received a divorce.'",
                   ['harvard_magazine_2005_glessner_lee'], "The article's fourth paragraph."),
    'lee-twins': A("Within a few years of the wedding the Lees moved one block north into 1700 S. Prairie Avenue (demolished), one of two twin townhouses that John and Frances Glessner built for their children; their children were John Glessner Lee (1898), Frances Lee (1903) and Martha Lee (1906). 'The marriage was not a happy one and the couple divorced in 1914.'",
                   [GH], "The biography of Frances Glessner Lee."),
    'twins-1902': A("George Glessner photographed the pair at 1700-1706 Prairie under construction in the summer of 1901, a year before the Glessner and Lee families moved in (1902).",
                    ['glessner_blog_1700_1706_construction_1901_photo'], "The photograph and its caption."),
    'george-family': A("George Glessner married Alice Hamlin in June 1898; their children were Elizabeth (1899), Frances (1900), John (1902) and Emily (1904). Photography was his lifelong passion, and in 1902 he was named utility manager of International Harvester.",
                       [GH], "The biography of George Macbeth Glessner."),
    'lee-son': A("Their son attributed the failed marriage partly to her 'creative urge coupled with high manual dexterity—the desire to make things—which [Lee] did not share.'",
                 ['harvard_magazine_2005_glessner_lee'], "The article's fourth paragraph."),
    'silversmith': A("In 1904 Frances Glessner set up a workbench in the basement of Glessner House and began producing simple and elegant objects; her pieces bear her hallmark, 'a G encircling a honeybee', for her bee keeping. She studied with Annibale Fogliata, a master jewelry craftsman of Hull House, and Madeline Yale Wynne, a noted Chicago silversmith.",
                     [GH], "The biography of Frances Macbeth Glessner."),
    'lee-later': A("In 1931 Frances Glessner Lee gave $250,000 to Harvard to create a chair in legal medicine; in 1943 New Hampshire appointed her State Police Captain, the first woman state police captain in the country. Her twenty miniature crime scenes, the Nutshell Studies of Unexplained Death, became the teaching tool of the Seminars in Homicide Investigation, and Erle Stanley Gardner dedicated a Perry Mason novel to her. She died at The Rocks on 27 January 1962.",
                   [GH], "The biography of Frances Glessner Lee."),
    'nutshell-made': A("The Nutshells were built at one inch to a foot with dental tools and a carpenter's help; she wrote to an adviser, 'I found myself constantly tempted to add more clues and details…stop me when I go too far.'",
                       ['harvard_magazine_2005_glessner_lee'], "The article's picture caption."),
    # ── 4. The reading class in the fortress ────────────────────────────────────────────────
    'class-harper': A("In 1893 William Rainey Harper, president of the University of Chicago, asked Frances Glessner for advice on how to introduce faculty wives to women of the city. The result was her Monday Morning Reading Class, which met for two hours in the library of the house every Monday from October to May. During the first hour the women sewed and listened to a professional reader; during the second there was lighter reading or a lecture. Membership was by invitation only, and the class continued until 1930.",
                      [GH], "The biography of Frances Macbeth Glessner."),
    'frances-mind': A("John Glessner wrote of his wife: 'She had a clean and wholesome and orderly mind, a heart overflowing with love for family and friends and for all in any need.'",
                      [GH], "The biography of Frances Macbeth Glessner, quoting The Story of a House."),
    'kimball-dying': A("'Mr. Kimball died at home after a lingering illness on December 16, 1904. His funeral was held in his home'. 'The honorary pallbearers included: Marshall Field, Robert T. Lincoln, Lambert Tree, Robert H. McCormick, Watson F. Blair, Charles H. Deere and J. J. Glessner.'",
                       ['chicago_scots_2012_kimball'], "The post's paragraph on his death and funeral."),
    'kimball-four': A("Kimball came to Chicago in 1857 and traded his Iowa property for four pianos, which he sold from a second-storey office; he married Evaline M. Cone in 1865, and they had no children.",
                      ['chicago_scots_2012_kimball'], "The post's paragraphs on his life."),
    # ── 5. Hattie Pullman and her surviving son ─────────────────────────────────────────────
    'pullman-children': A("George M. Pullman married Harriett Sanger on 13 June 1867. Their children were Florence (1868-1937), Harriett (1869-1956) and the twins George, Jr. (1875-1901) and Walter Sanger, known as Sanger (1875-1905).",
                          [TWINS], "The page's first paragraph."),
    'twins-boys': A("As boys the twins were schooled at their home on Prairie Avenue, allegedly 'arranging and promoting pit bull fights'; as teenagers they 'frequently were seen riding around Chicago in cabs filled with champagne bottles.' Sent to Harvard Training School, 'Sanger and George were ranked 147 and 148 out of a class of 148 students.'",
                    [TWINS], "The page's third paragraph."),
    'twins-will': A("'Pullman's will stipulated that the twins were to be given a yearly stipend of only $3,000.'",
                    [TWINS], "The page's fourth paragraph."),
    'george-jr': A("George, Jr. secretly married Lynn Fernald, 'his brother's betrothed'. Frederick Bowers sued George for $100,000, 'eventually settling for $50,000.' George died of complications from pneumonia in November, 1901.",
                   [TWINS], "The page's fourth, sixth and eighth paragraphs."),
    'sanger-money': A("Sanger, 'while widely acknowledged as the smarter of the 2, was very poor with money.' He was expelled from the New York Athletic Club for non-payment of dues, and in 1901 his sister-in-law's luggage was held for five months by a creditor of his. His mother 'paid the unnamed woman $10,000 to leave Sanger and never return.'",
                      [TWINS], "The page's fourth and sixth paragraphs; the date of the payment is not given."),
    'sanger-death': A("Sanger 'died after being thrown from a horse and carriage after yet another wild ride in August, 1905.' A 1901 headline in the World: 'Death of George Pullman a Warning to Rich Fathers.'",
                      [TWINS], "The page's last paragraph."),
    'lowden-house': A("The 1904 Blue Book lists Mr. and Mrs. Frank Orren Lowden at 1912 Prairie; Florence Pullman married Frank Lowden.",
                      ['chicago_blue_book_1904', 'pullman_museum_children_page'], "Blue Book, Prairie Av. street list, '1912 Mr. & Mrs. Frank Orren Lowden'; the children page."),
    'lowden-razed': A("Bryan P. Moulton Residence, 1912 S. Prairie Avenue: razed 1939.",
                      ['hmdb_prairie_lost_houses_1800_1900_west'], "The 1912 S. Prairie Avenue entry."),
    'pullman-coachman': A("The census of 1 June 1900 enumerated Henry Windish, coachman, born in Germany, as the head of his own household in the dwelling behind 1729 Prairie.",
                          ['census_1900_chicago_t623_roll245'], "ED 40, sheet 1A, line 3, leaf n794."),
    # ── 6. The man who said he was Pullman's son ────────────────────────────────────────────
    'behring-mother': A("Gustave Behring, 28, a sergeant in the German Army, was told on his mother's deathbed that his real father was George M. Pullman. She said she had been a governess in Chicago 'for a house on the west side'; when she became pregnant Pullman allegedly packed her off to Germany and supplied her with $500.",
                        [BEHRING], "The page's second paragraph, after the Cedar Rapids Evening Gazette, 14 December 1897."),
    'behring-office': A("At the Pullman building Pullman threw him out of his office; Behring was confined for a time in a mental institution, and was arrested six times more lurking outside the building. Four days before Pullman's death the conversation was recorded: BEHRING: You are my father! PULLMAN: You are a crazy man!",
                        [BEHRING], "The page's third paragraph."),
    'behring-steps': A("'Less than 12 hours after the funeral, Behring showed up at the family's residence on Prairie Avenue, demanding to speak to Mrs. Harriett Pullman.' He was met on the steps by Pullman's sons and the family lawyers, and was eventually arrested again; on 29 October 1897 an insanity expert pronounced him sane.",
                       [BEHRING], "The page's fourth paragraph."),
    'behring-ship': A("In September 1898 detectives escorted Behring to the Cunard liner Campania, bound for Bremen.",
                      [BEHRING], "The page's sixth paragraph, after the New York Times."),
    'behring-1901': A("'on June 25, 1901, Behring was again arrested at the law offices of Frank Lowden (Florence Pullman's husband) demanding $5,000 in cash and $10,000 a month for 6 months. Judge Davis, Lowden's partner, held Behring at gunpoint until the police arrived'.",
                      [BEHRING], "The page's last paragraph."),
    # ── 7. Pullman's ghosts at Eighteenth Street ────────────────────────────────────────────
    'statue-models': A("Rohl-Smith obtained his models at Fort Sheridan, where he met survivors of Wounded Knee, whom he described as 'Indians of the most untamed sort'. His figures 'may have owed more to Buffalo Bill Cody's Wild West Show than to actual research.'",
                       ['karamanski_2004_monuments_lost_nation_p6'], "Page 6 of the essay."),
    'statue-doubt': A("'Some historians regard the incident as the product of romantic imagination instead of eyewitness testimony, stating that Margaret Helm was not the beneficiary of Black Partridge's dramatic rescue. In fact, before the battle turned into a massacre, Mrs. Helm rode her horse to the shore of Lake Michigan where she found refuge.'",
                      ['karamanski_2004_monuments_lost_nation_p6'], "Page 6 of the essay."),
    'cavalry-1894': A("'a year after the statue's dedication', the Seventh Cavalry, 'which had fought Indians so fiercely at Little Big Horn and Wounded Knee, came to Chicago to quell the Pullman riots of 1894.'",
                      ['karamanski_2004_monuments_lost_nation_p6'], "Page 6 of the essay."),
    # ── 8. The madams to the west ───────────────────────────────────────────────────────────
    'levee': A("Chicago's Levee District ran from Eighteenth Street to the north to Twenty-second Street to the south, Wabash to the east and Clark to the west, 'several blocks away from Prairie Avenue'.",
               [LADIES], "The post's first paragraphs."),
    'everleigh-sisters': A("The sisters were born Simms (in Greene County, Virginia, Ada in 1864 and Minna in 1866; the Kentucky childhood was 'another story concocted by the sisters'). With an inheritance of some $35,000 they ran a house in Omaha, then bought Effie Hankins's brothel at 2131-2133 South Dearborn, and took the name Everleigh from their grandmother, who signed her letters 'Everly yours'. The club opened on February 1, 1900, and turned away many of its first callers.",
                           [LADIES, 'wikipedia_everleigh_club'], "Other Ladies: the Everleigh paragraph; Wikipedia: History."),
    'everleigh-rooms': A("The club occupied two mansions, 50 rooms with themes such as the Japanese Throne Room, the Mirror Room and the Silver Parlor; it had 'a $15,000 gold-leafed piano for the Music Room' and '$650 gold cuspidors'. A bottle of champagne cost $12 'in an era when an entire meal could be had for fifty cents', and the entrance fee alone was $50.",
                         [LADIES, 'wikipedia_everleigh_club'], "Other Ladies: the club paragraph; Wikipedia: History."),
    'everleigh-roles': A("Ada, the quieter sister, kept the books and hired the women; Minna met the guests. The club employed '15 to 25 cooks and maids', and its women were called 'butterflies'.",
                         ['wikipedia_everleigh_club', LADIES], "Wikipedia: The sisters' separate responsibilities, Interior layout; Other Ladies."),
    'prince-henry': A("On March 3, 1902, Prince Henry of Prussia visited the club; when a slipper came off during a dance and spilled champagne and one of his party drank from it, the custom of drinking champagne from a woman's shoe began.",
                      ['wikipedia_everleigh_club'], "Interior layout."),
    'vic-shaw': A("The Everleigh Club and Vic Shaw's 'resort' were the preeminent brothels in Chicago, 'with Shaw's business existing on Prairie Avenue for a time.' Shaw lived until 1952 in a crumbling mansion at 2906 Prairie Avenue with a dog, cat and parrot.",
                  [LADIES], "The post's second and last paragraphs."),
    'everleigh-clients': A("The blog names actor John Barrymore, authors Ring Lardner and Theodore Dreiser, and Marshall Field, Jr. among the club's famed clients, and says rumours persisted for years that the young Field had been shot there; Wikipedia: 'A rival madam maliciously accused the Everleigh sisters of murdering Field.'",
                           [LADIES, 'wikipedia_everleigh_club'], "Other Ladies: the clients paragraph; Wikipedia: Scandals."),
    'everleigh-close': A("Mayor Carter Harrison Jr. ordered the club closed on October 24, 1911. Minna: 'If the Mayor says we must close, that settles it...I'll close up shop and walk out with a smile on my face.' The building was razed in July 1933.",
                         ['wikipedia_everleigh_club'], "Closing."),
    'levee-near': I("The Levee's eastern edge, Wabash Avenue, lay three blocks west of Prairie Avenue, with Indiana and Michigan Avenues between.",
                    [LADIES], "The blog gives the Levee's bounds as Eighteenth to Twenty-second, Wabash to Clark, 'several blocks away from Prairie Avenue'; the avenues between, Indiana and Michigan, are the city's grid west of Prairie."),
    'church-1904': I("First Presbyterian Church stood at Indiana Avenue and Twenty-first Street in 1904, two blocks west of Prairie Avenue and at the Levee's eastern edge.",
                     ['otis_1913_first_presbyterian_21st_indiana_1887', 'sanborn_1911_chicago_v3_sheet_35', LADIES],
                     "The church's own structure record dates it 1870-1873 to after 1911 and the 1911 Sanborn sheet draws it at Indiana and Twenty-first; the Levee ran east to Wabash, one block beyond Indiana and Michigan."),
    # ── 9. Marshall Field Jr., one year out ─────────────────────────────────────────────────
    'field-children': A("Marshall and Nannie Field had three children: Louis, who died in infancy, and Marshall, Jr. and Ethel, raised at 1905 Prairie, 'the first in Chicago to be completely wired for electricity', built in 1876 at a cost of some $2 million.",
                        [OTHER_MRS], "The post's second paragraph."),
    'field-heirs': A("Marshall Field Jr. (1868-1905) married Albertine Huck, and they were the parents of Henry Field, Marshall Field III and Gwendolyn. Field's will held his remaining estate in trust for 40 years for his two grandsons, 60 percent to Marshall Field III and 40 percent to Henry, who died in 1917.",
                     ['wikipedia_marshall_field'], "Family; Death and legacy."),
    'field-six-weeks': A("'Despite the aid of Chicago's best surgeons, Field died of what the Tribune termed an accidentally self-inflicted gunshot wound. Six weeks later, Marshall Field, Sr. was dead.'",
                         [LADIES], "The clients paragraph."),
    # ── 10. The merchant who walked into the lake ───────────────────────────────────────────
    'keith-argus': A("Edson Keith 'disappeared from his home at 1906 Prairie avenue about 6 o'clock in the morning' of Monday 21 September 1896; the Argus report put the place at the lake 'at the foot of Thirteenth street', and 'search was made for the missing man all day Monday'. 'He was 63 years old and came to Chicago in 1854.'",
                     ['ann_arbor_argus_1896_09_25_keith'], "The whole item."),
    'keith-night': A("He had spent another sleepless night pacing the hallways of his home, and his butler found him in a state of deliriousness at 2 AM. A hat and coat were found on the beach on Monday morning, and only when the household staff read the Tuesday newspaper did they realise what had happened. Fishermen on the beach told what they had seen.",
                     ['postcardhistory_2023_edson_keith'], "The post's second to fourth paragraphs."),
    'keith-warning': A("His brother Elbridge and his wife had spoken with Mrs. Keith a few weeks before, and she had said, 'I … suspect that he was losing control of his mind through long suffering.'",
                       ['postcardhistory_2023_edson_keith'], "The post's sixth paragraph."),
    'keith-kind': A("His personal secretary said he had never heard him say anything nasty or unkind about anyone. The firm, founded in 1858 by Osborn R. Keith and Albert Faxon on Lake Street, had become Edson Keith & Company, with annual sales of $4.5 million in the mid-1880s, over 200 employees in Chicago and 500 more in a Milwaukee factory.",
                    ['postcardhistory_2023_edson_keith'], "The post's seventh to ninth paragraphs."),
    'keith-will': A("His will of 13 March 1895 left $300,000 each to his wife Susan and to his two sons, Edson, Jr. and Walter W.",
                    ['postcardhistory_2023_edson_keith'], "The post's aside on the will."),
    'keith-dragged': A("The evidence came to the family 'with paralyzing suddenness' on Tuesday, and 'the lake is now being dragged for the recovery of the remains.'",
                       ['ann_arbor_argus_1896_09_25_keith'], "The whole item."),
    'keith-razed': A("Osborn R. Keith Residence, 1808 S. Prairie Avenue: the north wall was retained during demolition in 1968 to preserve the private courtyard of the adjacent Glessner house.",
                     ['hmdb_prairie_lost_houses_1800_1900_west'], "The 1808 S. Prairie Avenue entry."),
    'stanley-1808': A("The 1904 Blue Book lists Mr. and Mrs. Stanley Field at 1808 Prairie.",
                      ['chicago_blue_book_1904'], "Prairie Av. street list, the 1808 line."),
    'keith-coachman': A("The census of 1 June 1900 enumerated Paul Rasmussen, coachman, born in Denmark, as the head of his own household in the rear building behind 1906 Prairie.",
                        ['census_1900_chicago_t623_roll245'], "ED 40, sheet 4B, line 98, leaf n801."),
}

# The reconstructed claims every story jaunt carries: the day and the staging.
def staging(title):
    return {
        'day': {'text': f"{title}: the day, Monday 21 November 1904, the hour and the order of the walk are this jaunt's framing, chosen because the stories meet on it (three days after Arthur Caton's death, a Monday of the Reading Class, before Kimball's death in December). No visit on that day is asserted.",
                'confidence': 'reconstructed', 'sources': [], 'liberty': LIBERTY},
        'stage': {'text': f"{title}: who is seen at each stop, where they stand, what they do and when are reconstructed. People with cards in the town play themselves; people the town has no card for (and the unnamed servants, callers and passers-by) are unnamed figures in period dress, and no likeness is claimed. No word anyone says is asserted.",
                  'confidence': 'reconstructed', 'sources': [], 'liberty': LIBERTY},
    }
