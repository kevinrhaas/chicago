"""T-3382: the children of the 1904 Prairie Avenue households, with the years each lived in
the house. Read by apply.py beside this file. Every entry names the sources it rests on; a
relationship the source does not print is said to be read from the listing.

lived_here.on_scene_date: 'yes' (here on 1 July 1904), 'no' (not here that day) or
'unknown' (the sources read do not reach 1904 either way).
"""
C10 = "census_1910_chicago_t624_roll241"
C00 = "census_1900_chicago_t623_roll245"
BB = lambda *ys: [f"chicago_blue_book_{y}" for y in ys]
LEAF = {"166/1A": "n1429", "166/1B": "n1430", "166/5A": "n1437", "166/5B": "n1438",
        "166/6A": "n1439", "166/6B": "n1440", "166/8A": "n1443", "166/8B": "n1444",
        "166/9A": "n1445", "167/2A": "n1451", "167/5B": "n1458", "167/6B": "n1460",
        "167/7B": "n1462"}


def c10(sheet, line, as_enumerated, relation):
    ed, sh = sheet.split("/")
    return {"date": "1910-04-15", "source": C10,
            "locator": f"ED {ed}, sheet {sh}, line {line}, leaf {LEAF[sheet]}",
            "as_enumerated": as_enumerated, "relation_as_enumerated": relation}


def born10(age, note_extra=""):
    y = 1910 - age
    return {"value": f"{y}", "confidence": "inferred", "sources": [C10],
            "note": f"The 1910 census gives age {age} on 15 April 1910, so born about {y - 1}-{y}.{note_extra}"}


LISTING_SON = "That they were a son of the house is read from the shared surname at the number; the Blue Book does not print the relationship."
LISTING_DR = "That she was a daughter of the house is read from the shared surname and 'Miss' at the number; the Blue Book does not print the relationship."

NEW = [
    # ---- 1600 Shortall
    dict(hh="hh_shortall_john_g", id="pa1904_shortall_john_g_son_john_l", name="John L. Shortall",
         rel="son", grade="inferred", sources=BB(1893, 1894), own_card="pa1904_shortall_john_l",
         printed_as="1600 Mr. & Mrs. John L. Shortall",
         lived_here={"years": "1893-1894", "on_scene_date": "no"},
         note="Listed at 1600 under John G. Shortall, with his wife, in the 1893 and 1894 editions, and from the 1895 edition next door at 1604, where he and his family live in 1904 on their own card. That he was John G. Shortall's son is read from the shared surname at the number; the Blue Book does not print it."),
    # ---- 1628 Einstein
    dict(hh="hh_einstein_m", id="pa1904_einstein_benjamin", name="Benjamin Einstein", rel="son",
         grade="inferred", sources=BB(1890, 1891, 1892, 1893, 1894, 1895, 1897, 1898, 1899, 1901),
         printed_as="1628 Benjamin Einstein", lived_here={"years": "1890-1901", "on_scene_date": "no"},
         note="Listed at 1628 under Mr. and Mrs. Morris Einstein in every edition read from 1890 to 1901, and not in 1902 or after. " + LISTING_SON + " The 1910 census has Julia Einstein the mother of seven children, six of them living (ED 166, sheet 8B, line 91, leaf n1444)."),
    dict(hh="hh_einstein_m", id="pa1904_einstein_arthur", name="Arthur Einstein", rel="son",
         grade="inferred", sources=BB(1890), printed_as="1628 Arthur Einstein",
         lived_here={"years": "1890", "on_scene_date": "no"},
         note="Listed at 1628 under Mr. and Mrs. Morris Einstein in the 1890 edition only. " + LISTING_SON),
    dict(hh="hh_einstein_m", id="pa1904_einstein_jennie_shafner", name="Jennie E. Shafner", rel="daughter",
         grade="attested", sources=[C10] + BB(1902, 1910, 1911), printed_as="1628 Mrs. Jennie E. Shaffner",
         lived_here={"years": "1902; 1910-1911", "on_scene_date": "unknown"},
         census_1910=c10("166/8B", 93, "Shafner, Jennie", "Daughter"),
         born=born10(56),
         note="The 1910 census lists her at 1628 as the Einsteins' daughter, divorced, aged 56 and born in West Virginia. The Blue Book lists Mrs. Jennie E. Shaffner at 1628 in the 1902 edition and again from 1910; it does not list her there in 1904 or 1905, so whether she was home that year is not documented."),
    dict(hh="hh_einstein_m", id="pa1904_einstein_emma_biers", name="Emma Biers", rel="daughter",
         grade="attested", sources=[C10] + BB(1895, 1910), printed_as="1628 Mrs. Emma Beirs",
         lived_here={"years": "1895; 1910", "on_scene_date": "unknown"},
         census_1910=c10("166/8B", 94, "Biers, Emma", "Daughter"),
         born=born10(54),
         note="The 1910 census lists her at 1628 as the Einsteins' daughter, a widow of 54, born in California. The Blue Book lists Mrs. Emma Beirs at 1628 in 1895 and 1910 only."),
    # ---- 1700 Lee
    dict(hh="hh_lee_blewett", id="pa1904_lee_martha", name="Martha Lee", rel="daughter", grade="attested",
         sources=[C10], lived_here={"years": "born about 1906; here in 1910", "on_scene_date": "no"},
         census_1910=c10("166/8A", 47, "Lee, Martha", "Daughter"), born=born10(3),
         note="The youngest of Frances Glessner Lee's three children, born after the scene: the 1910 census lists her at 1700 with her mother, brother John and sister Frances, aged 3 (her mother had borne three children, all living; ED 166, sheet 8A, lines 44-47). Her father is not in the house that day; the marriage ended in 1914."),
    # ---- 1701 Mrs. W. G. Hibbard
    dict(hh="hh_hibbard_mrs_william_gold", id="pa1904_hibbard_lilian_b", name="Lilian B. Hibbard", rel="daughter",
         grade="inferred", sources=BB(1890), printed_as="1701 Miss Lilian B. Hibbard",
         lived_here={"years": "1890", "on_scene_date": "no"},
         note="Listed at 1701 under Mr. and Mrs. William G. Hibbard in the 1890 edition, and not after. " + LISTING_DR),
    dict(hh="hh_hibbard_mrs_william_gold", id="pa1904_hibbard_f_v_s_at_1701", name="F. V. S. Hibbard", rel="son",
         grade="inferred", sources=BB(1894, 1895, 1897), own_card="pa1904_hibbard_f_vans",
         printed_as="1701 F. V. S. Hibbard", lived_here={"years": "1894-1897", "on_scene_date": "no"},
         note="Listed at 1701 under his parents in the 1894, 1895 and 1897 editions; in 1904 he and his wife keep their own house at 1620, on their own card. " + LISTING_SON + " The Frank Hibbard listed at 1701 again from the 1905 edition is very likely the same man, but the book does not say so."),
    dict(hh="hh_hibbard_mrs_william_gold", id="pa1904_hibbard_william_g_jr_at_1701", name="William G. Hibbard jr.", rel="son",
         grade="attested", sources=BB(1894, 1895, 1897, 1898, 1899), own_card="pa1904_hibbard_william_gold_jr",
         printed_as="1701 William G. Hibbard jr.", lived_here={"years": "1894-1899", "on_scene_date": "no"},
         note="Listed at 1701 under his parents from 1894 to 1899, as William G. Hibbard jr.: the 'jr.' names him the son of the house. From the 1901 edition he and his wife are across the street at 1637, where they live in 1904 on their own card."),
    # ---- 1720 Mrs. J. M. Walker
    dict(hh="hh_walker_mrs_james_m", id="pa1904_walker_wirt_d", name="Wirt D. Walker", rel="son", grade="inferred",
         sources=BB(1890, 1891, 1892, 1893, 1894, 1895), printed_as="1720 Wirt D. Walker",
         lived_here={"years": "1890-1895", "on_scene_date": "no"},
         note="Listed at 1720 under Mrs. James M. Walker from 1890 to 1895; a Mrs. Wirt D. Walker is listed there in 1901. " + LISTING_SON),
    dict(hh="hh_walker_mrs_james_m", id="pa1904_walker_henry_h_at_1720", name="Henry H. Walker", rel="son", grade="inferred",
         sources=BB(1902), own_card="pa1904_walker_henry_h", printed_as="1720 Mr. & Mrs. Henry H. Walker",
         lived_here={"years": "1902", "on_scene_date": "no"},
         note="Listed at 1720 with his wife in the 1902 edition; from 1903 they are next door at 1721, where they live in 1904 on their own card. " + LISTING_SON),
    # ---- 1729 Pullman
    dict(hh="hh_pullman_mrs_george_m", id="pa1904_pullman_florence_at_1729", name="Florence Pullman", rel="daughter",
         grade="attested", sources=["pullman_museum_children_page", "classic_chicago_pullman_finale"] + BB(1890, 1892, 1894),
         own_card="pa1904_lowden_mrs_frank_orren", born={"value": "1868", "confidence": "attested", "sources": ["pullman_museum_children_page"], "note": "Born 1868, died 1937 (the museum's page)."},
         lived_here={"years": "1870s-1896", "on_scene_date": "no"},
         note="The Pullmans' elder daughter, who grew up in the house. The Blue Book prints the household as Mr. and Mrs. Geo. M. Pullman '& drs.' in 1890 and 1892 and '& dr.' in 1894, when she was the daughter still at home. She married Frank Lowden in 1896 in the house itself, two of George Pullman's brothers taking the service. In 1904 she lives across the street at 1912 with her husband and children, on their own card."),
    dict(hh="hh_pullman_mrs_george_m", id="pa1904_pullman_harriett", name="Harriett Pullman", rel="daughter",
         grade="attested", sources=["pullman_museum_children_page"] + BB(1890, 1892),
         born={"value": "1869", "confidence": "attested", "sources": ["pullman_museum_children_page"], "note": "Born 1869, died 1956 at 87 (the museum's page)."},
         lived_here={"years": "1870s-about 1893", "on_scene_date": "no"},
         note="The younger daughter, who grew up in the house. The Blue Book's '& drs.' (two daughters at home) runs to the 1892 edition and is '& dr.' by 1894, so she had left between the two. She married Frank J. Carolan of San Francisco (the museum's page); the year of the marriage is not in the sources read."),
    dict(hh="hh_pullman_mrs_george_m", id="pa1904_pullman_george_m_jr", name="George M. Pullman jr.", rel="son",
         grade="attested", sources=["pullman_museum_children_page", "classic_chicago_pullman_finale"] + BB(1897, 1898),
         born={"value": "1875", "confidence": "attested", "sources": ["pullman_museum_children_page", "classic_chicago_pullman_finale"], "note": "One of identical twins born in 1875."},
         printed_as="1729 George M. Pullman, jr.", lived_here={"years": "1875-1898", "on_scene_date": "no"},
         note="One of the twins. As boys the twins were schooled at home on Prairie Avenue, and the Blue Book lists him at 1729 in the 1897 and 1898 editions. He married on 30 September 1899 in Carson, Nevada, and died at Menlo Park, California, in November 1901, aged 26, long before the scene. The census of 1910 has his mother the mother of four children, two then living (ED 166, sheet 6A, line 28, leaf n1439)."),
    dict(hh="hh_pullman_mrs_george_m", id="pa1904_pullman_w_sanger", name="W. Sanger Pullman", rel="son",
         grade="attested", sources=["pullman_museum_children_page", "classic_chicago_pullman_finale"] + BB(1895, 1897, 1898),
         born={"value": "1875", "confidence": "attested", "sources": ["pullman_museum_children_page", "classic_chicago_pullman_finale"], "note": "One of identical twins born in 1875."},
         printed_as="1729 W. Sanger Pullman", lived_here={"years": "1875-1898", "on_scene_date": "no"},
         note="Walter Sanger Pullman, called Sanger, the other twin, schooled at home on Prairie Avenue with his brother. The Blue Book lists him at 1729 from 1895 to 1898. Like his brother he made his home in California, and he died there, at Belmont, on 14 August 1905."),
    # ---- 1730 Mrs. J. E. Otis
    dict(hh="hh_otis_mrs_joseph_e", id="pa1904_otis_joseph_e_jr", name="Joseph E. Otis jr.", rel="son", grade="attested",
         sources=BB(1890, 1891), printed_as="1730 Joseph E. Otis jr.", lived_here={"years": "1890-1891", "on_scene_date": "no"},
         note="Listed at 1730 under Mr. and Mrs. Joseph E. Otis in the 1890 and 1891 editions; the 'jr.' names him the son of the house. The 1910 census has his mother the mother of eight children, four of them living (ED 166, sheet 6A, line 6, leaf n1439)."),
    dict(hh="hh_otis_mrs_joseph_e", id="pa1904_otis_ralph_c", name="Ralph C. Otis", rel="son", grade="attested",
         sources=[C10] + BB(1890, 1891, 1892, 1893, 1894, 1895, 1897, 1898, 1901), printed_as="1730 Ralph C. Otis",
         lived_here={"years": "1890-1901; 1910", "on_scene_date": "unknown"},
         census_1910=c10("166/6A", 7, "Otis, Ralph C.", "Son"), born=born10(40),
         note="Listed at 1730 under his parents from 1890, with his wife in 1901, and not in the 1902 to 1910 editions; the 1910 census finds him at home again, as son, aged 40, with his wife Evaleen. Whether he lived here in 1904 is not documented."),
    # ---- 1736 McBirney
    dict(hh="hh_mcbirney_hugh", id="pa1904_mcbirney_george_d", name="George D. McBirney", rel="son", grade="attested",
         sources=[C10] + BB(1897), printed_as="1736 George D. McBirney", lived_here={"years": "1897; 1910", "on_scene_date": "unknown"},
         census_1910=c10("166/6A", 18, "McBirney, George D.", "Son"),
         note="Listed at 1736 under his parents in the 1897 edition; the 1910 census finds him at home as their son, divorced. His mother had borne five children, only he then living (ED 166, sheet 6A, lines 16-18). Whether he lived here in 1904 is not documented."),
    # ---- 1800 Glessner
    dict(hh="hh_glessner_john_j", id="pa1904_glessner_george_m_at_1800", name="George M. Glessner", rel="son",
         grade="attested", sources=["glessner_house_family_page", "glessner_story_of_a_house_1923"] + BB(1895, 1897, 1898),
         own_card="pa1904_glessner_george_m", printed_as="1800 J. G. M. Glessner",
         born={"value": "1871", "confidence": "attested", "sources": ["glessner_house_family_page"], "note": "Born 1871 (the museum's family page)."},
         lived_here={"years": "1887-1898", "on_scene_date": "no"},
         note="John George Macbeth Glessner, the son of the house, moved in with his parents the night the family first slept here, 1 December 1887, at sixteen. The Blue Book lists him here as J. G. M. Glessner from 1895 to 1898. He married Alice Hamlin in 1898 and in 1904 lives with her and their four children a block north at 1706, in one of the two townhouses his parents built for their children; that household has its own card. His mother had borne three children, two of them living, by 1910 (ED 166, sheet 1B, line 54, leaf n1430)."),
    dict(hh="hh_glessner_john_j", id="pa1904_glessner_frances_at_1800", name="Frances Glessner", rel="daughter",
         grade="attested", sources=["glessner_house_family_page", "glessner_story_of_a_house_1923"] + BB(1898),
         own_card="pa1904_lee_frances_glessner",
         lived_here={"years": "1887-1898", "on_scene_date": "no"},
         note="The daughter of the house, nine when the family moved in on 1 December 1887. The 1898 Blue Book prints the household with '& dr.' for her. She married Blewett Lee on 9 February 1898 and within a few years was living one block north at 1700, the other of the twin townhouses her parents built; as Frances Glessner Lee she is on that card in 1904, and later made the Nutshell Studies of Unexplained Death."),
    # ---- 1812 Young
    dict(hh="hh_young_lawrence_a", id="pa1904_young_lawrence_r", name="Lawrence R. Young", rel="son", grade="inferred",
         sources=[C10], lived_here={"years": "born about 1903; here in 1910", "on_scene_date": "yes"},
         census_1910=c10("166/1A", 45, "Young, Lawrence R.", "Son"), born=born10(7),
         note="The Youngs' third child: the 1910 census lists him at 1812 aged 7, with his brother Henry W. and sister Alice, and their mother as having borne three children, all living (ED 166, sheet 1A, lines 41-45). Born about 1902-03 to a family listed here from the 1897 edition to 1914, he was very likely a baby in the house on 1 July 1904; that is inferred from his age, not recorded."),
    # ---- 1815 Meeker
    dict(hh="hh_meeker_arthur", id="pa1904_meeker_katherine", name="Katherine Meeker", rel="daughter", grade="inferred",
         sources=[C10, "wikipedia_arthur_meeker"], lived_here={"years": "1903-1910 and after", "on_scene_date": "yes"},
         census_1910=c10("167/6B", 84, "Meeker, Katherine", "Daughter"), born=born10(16),
         note="The eldest of Arthur Jr.'s three sisters, whom his biography mentions without naming. The 1910 census lists her at 1815 aged 16, with her sisters Grace and Mary and her brother, and their mother as having borne four children, all living (ED 167, sheet 6B, lines 82-87). The family is listed here from the 1903 edition, so she was very likely about ten and at home in 1904; that is inferred, not recorded."),
    dict(hh="hh_meeker_arthur", id="pa1904_meeker_grace", name="Grace Meeker", rel="daughter", grade="inferred",
         sources=[C10, "wikipedia_arthur_meeker"], lived_here={"years": "1903-1910 and after", "on_scene_date": "yes"},
         census_1910=c10("167/6B", 85, "Meeker, Grace", "Daughter"), born=born10(15),
         note="Named for her mother. The 1910 census lists her at 1815 aged 15 (ED 167, sheet 6B, line 85); with the family listed here from 1903 she was very likely at home in 1904, aged about nine, though no record of that year names her."),
    dict(hh="hh_meeker_arthur", id="pa1904_meeker_mary", name="Mary Meeker", rel="daughter", grade="inferred",
         sources=[C10, "wikipedia_arthur_meeker"], lived_here={"years": "born about 1903-04; here in 1910", "on_scene_date": "yes"},
         census_1910=c10("167/6B", 87, "Meeker, Mary", "Daughter"), born=born10(6),
         note="The youngest Meeker child: the 1910 census lists her at 1815 aged 6 (ED 167, sheet 6B, line 87), so she was born between April 1903 and April 1904 and was very likely a baby in the house on 1 July 1904. The 1914 Blue Book's '& dr.' is probably her eldest sister."),
    # ---- 1824 Cunningham
    dict(hh="hh_cunningham_secor", id="pa1904_cunningham_elizabeth_s", name="Elizabeth S. Cunningham", rel="daughter",
         grade="inferred", sources=[C10], lived_here={"years": "1898-1912", "on_scene_date": "yes"},
         census_1910=c10("166/8B", 60, "Cunningham, Elizabeth S.", "Daughter"), born=born10(21),
         note="The 1910 census lists her at 1824 as daughter, aged 21, with her brother Secor Jr.; their mother had borne two children, both living (ED 166, sheet 8B, lines 58-61). The family is listed here in every edition read from 1898 to 1912, so she very likely grew up in the house and was about fifteen in 1904; that is inferred from her age and the listings."),
    dict(hh="hh_cunningham_secor", id="pa1904_cunningham_secor_jr", name="Secor Cunningham jr.", rel="son",
         grade="inferred", sources=[C10] + BB(1910, 1911), printed_as="1824 Secor Cunningham jr.",
         lived_here={"years": "1898-1912", "on_scene_date": "yes"},
         census_1910=c10("166/8B", 61, "Cunningham, Secor Jr.", "Son"), born=born10(18),
         note="The son of the house: the 1910 census lists him at 1824 aged 18, and the Blue Book from the 1910 edition. With the family here from 1898, he was very likely about twelve and at home in 1904; that is inferred from his age and the listings."),
    # ---- 1834 Jones
    dict(hh="hh_jones_fernando", id="pa1904_jones_graham", name="Graham Jones", rel="son", grade="inferred",
         sources=BB(1890, 1891, 1892, 1893, 1894, 1895, 1897, 1898, 1907, 1908, 1909, 1910, 1911), printed_as="1834 Graham Jones",
         lived_here={"years": "1890-1898; 1907-1911", "on_scene_date": "no"},
         note="Listed at 1834 under Mr. and Mrs. Fernando Jones from 1890, with his own wife from 1897, until 1898, and again as Mr. and Mrs. Graham Jones from 1907; not in the editions of 1901 to 1906. " + LISTING_SON),
    # ---- 1900 E. G. Keith
    dict(hh="hh_keith_elbridge_g", id="pa1904_keith_elbridge_b", name="Elbridge B. Keith", rel="son", grade="inferred",
         sources=BB(1892, 1893, 1894, 1895), printed_as="1900 Elbridge B. Keith", lived_here={"years": "1892-1895", "on_scene_date": "no"},
         note="Listed at 1900 under Mr. and Mrs. Elbridge G. Keith from 1892 to 1895. " + LISTING_SON + " The 1910 census has Mrs. Keith the mother of six children, four of them living (ED 166, sheet 1A, line 11, leaf n1429)."),
    dict(hh="hh_keith_elbridge_g", id="pa1904_keith_carl", name="Carl Keith", rel="son", grade="inferred",
         sources=BB(1897, 1898, 1901), printed_as="1900 Carl Keith", lived_here={"years": "1897-1901", "on_scene_date": "no"},
         note="Listed at 1900 under Mr. and Mrs. Elbridge G. Keith in 1897, 1898 and 1901. " + LISTING_SON),
    # ---- 1905 Marshall Field
    dict(hh="hh_field_marshall", id="pa1904_field_marshall_jr_at_1905", name="Marshall Field jr.", rel="son", grade="attested",
         sources=["classic_chicago_prairie_kids_party", "wikipedia_marshall_field"] + BB(1892), own_card="pa1904_field_marshall_jr",
         born={"value": "1868", "confidence": "attested", "sources": ["wikipedia_marshall_field"], "note": "1868-1905 (Wikipedia)."},
         lived_here={"years": "by 1886 to about 1890", "on_scene_date": "no"},
         note="Marshall Field's only surviving son (a brother, Louis, died as a baby in 1866). He was at home here at seventeen, for the children's party his parents gave on 1 January 1886. He married Albertine Huck and by the 1892 edition of the Blue Book the couple had their own house a few doors south at 1919, where they live in 1904 on their own card. He died in 1905."),
    dict(hh="hh_field_marshall", id="pa1904_field_ethel", name="Ethel Field", rel="daughter", grade="attested",
         sources=["wikipedia_ethel_beatty", "classic_chicago_prairie_kids_party", "wikipedia_marshall_field"],
         born={"value": "1873", "confidence": "attested", "sources": ["wikipedia_ethel_beatty"], "note": "Born in Cook County, Illinois, in 1873 (Wikipedia)."},
         lived_here={"years": "by 1886 to 1891", "on_scene_date": "no"},
         note="Marshall Field's daughter, twelve at the children's party of 1 January 1886 in this house. She was married here, at 'the home of her parents, 1905 Prairie Avenue', to Arthur Magie Tree on 1 January 1891, and was later Countess Beatty."),
    # ---- 1906 Mrs. Edson Keith
    dict(hh="hh_keith_mrs_edson", id="pa1904_keith_edson_jr_at_1906", name="Edson Keith jr.", rel="son", grade="attested",
         sources=BB(1890, 1891, 1892), own_card="pa1904_keith_edson_jr", printed_as="1906 Edson Keith jr.",
         lived_here={"years": "1890-1892", "on_scene_date": "no"},
         note="Listed at 1906 under Mr. and Mrs. Edson Keith in 1890 and 1891, and with his wife in 1892; the 'jr.' names him the son of the house. From the 1894 edition he lives at 2110, where he and his family are on their own card in 1904. The 1910 census has his mother the mother of two children, both living (ED 166, sheet 8B, line 71, leaf n1444)."),
    dict(hh="hh_keith_mrs_edson", id="pa1904_keith_walter_w", name="Walter W. Keith", rel="son", grade="inferred",
         sources=[C10] + BB(1890, 1891, 1892, 1893, 1894, 1895, 1897), printed_as="1906 Walter W. Keith",
         lived_here={"years": "1890-1897", "on_scene_date": "no"},
         note="Listed at 1906 under his parents from 1890, and with his own wife in 1897. In 1910 the census finds Walter W. Keith, 40, next door at 1904 with his wife Frances and son Winchester (ED 166, sheet 8B, lines 76-78), and the widow at 1906 the mother of two living children; with Edson Keith jr. that makes the two. That he was her son is read from the listing and that count."),
    # ---- 1919 Marshall Field jr.
    dict(hh="hh_field_marshall_jr", id="pa1904_field_gwendolyn", name="Gwendolyn Field", rel="daughter", grade="inferred",
         sources=["wikipedia_marshall_field"], lived_here={"years": "a child here in 1903-1905", "on_scene_date": "yes"},
         note="Gwendolyn Mary Field, the daughter of Marshall Field Jr. and Albertine Huck (Wikipedia names her among their children). The household is listed here from the 1903 edition to 1905, and her father died in November 1905; her birth date is not in the source read, so her place in the house in 1904 is inferred as her brothers' is."),
    # ---- 1945 Corwith
    dict(hh="hh_corwith_mrs_henry", id="pa1904_corwith_john_w", name="John W. Corwith", rel="son", grade="inferred",
         sources=BB(1892, 1893, 1894, 1895, 1897, 1898, 1899, 1901, 1902), printed_as="1945 John W. Corwith",
         lived_here={"years": "1892-1902", "on_scene_date": "no"},
         note="Listed at 1945 under Mrs. Henry Corwith from 1892 to 1902, beside his brother Charles R. Corwith; not in 1903 or after. " + LISTING_SON),
    dict(hh="hh_corwith_mrs_henry", id="pa1904_corwith_frank", name="Frank Corwith", rel="son", grade="inferred",
         sources=BB(1892, 1893), printed_as="1945 Frank Corwith", lived_here={"years": "1892-1893", "on_scene_date": "no"},
         note="Listed at 1945 under Mrs. Henry Corwith in 1892 and 1893. " + LISTING_SON + " The household also printed '& dr.' from 1892 to 1894, a daughter the book does not name."),
    # ---- 2000 Clark
    dict(hh="hh_clark_john_m", id="pa1904_clark_bruce", name="Bruce Clark", rel="son", grade="inferred",
         sources=BB(1895), printed_as="2000 Bruce Clark", lived_here={"years": "1895", "on_scene_date": "no"},
         note="Listed at 2000 under Mr. and Mrs. John M. Clark in the 1895 edition. " + LISTING_SON),
    # ---- 2010 Grey
    dict(hh="hh_grey_w_l", id="pa1904_grey_walter_c", name="Walter C. Grey", rel="son", grade="attested",
         sources=[C10] + BB(1891, 1892, 1893, 1894, 1895, 1897, 1898, 1901, 1909, 1910, 1911), printed_as="2010 Walter Grey",
         lived_here={"years": "1891-1901; 1909-1911", "on_scene_date": "unknown"},
         census_1910=c10("167/5B", 72, "Grey, Walter C.", "Son"),
         note="Listed at 2010 under his parents from 1891 to 1901 and again from 1909; the 1910 census lists him there as son. The 1902 to 1908 editions do not list him, so whether he lived here in 1904 is not documented."),
    dict(hh="hh_grey_w_l", id="pa1904_grey_elizabeth_w", name="Elizabeth W. Grey", rel="daughter", grade="inferred",
         sources=[C10] + BB(1910, 1911), printed_as="2010 Miss Elizabeth Grey", lived_here={"years": "here in 1910-1911", "on_scene_date": "unknown"},
         census_1910=c10("167/5B", 73, "Grey, Elizabeth W.", "Daughter"),
         note="The 1910 census lists her at 2010 as William L. Grey's daughter; her age reads 14, but the figures on that line are hard to read and the Blue Book prints her as 'Miss' from 1910, so she may be older. She may be the unnamed '& dr.' of the 1904 listing, or her sister Florence may; the book does not say."),
    dict(hh="hh_grey_w_l", id="pa1904_grey_florence", name="Florence Grey", rel="daughter", grade="inferred",
         sources=BB(1907, 1908), printed_as="2010 Miss Florence Grey", lived_here={"years": "1907-1908", "on_scene_date": "unknown"},
         note="Listed at 2010 with William L. Grey in the 1907 and 1908 editions. " + LISTING_DR + " The household printed '& drs.' from 1895 to 1902 and '& dr.' from 1903 to 1906, so she may be the daughter at home in 1904."),
    dict(hh="hh_grey_w_l", id="pa1904_grey_charles_g", name="Charles G. Grey", rel="son", grade="attested",
         sources=[C10] + BB(1911), printed_as="2010 Charles G. Grey", lived_here={"years": "here in 1910-1911", "on_scene_date": "unknown"},
         census_1910=c10("167/5B", 74, "Grey, Charles G.", "Son"),
         note="The 1910 census lists him at 2010 as son (his age is not written); the Blue Book from 1911. Whether he lived here in 1904 is not documented."),
    # ---- 2021 High
    dict(hh="hh_high_mrs_james_l", id="pa1904_high_shirley_t", name="Shirley T. High", rel="son", grade="inferred",
         sources=[C10] + BB(1897, 1898, 1899, 1903, 1909, 1910, 1911), printed_as="2021 Shirley T. High",
         lived_here={"years": "1897-1899; 1903; 1909-1911", "on_scene_date": "no"},
         census_1910=c10("167/2A", 20, "High, Shirley T.", "Head"), born=born10(36),
         note="Listed at 2021 under Mr. and Mrs. James L. High from 1897 to 1899, with his own wife in 1903, and from 1909, when he heads the house: the 1910 census lists him there with his wife Helen and their sons James and Raymond (ED 167, sheet 2A, lines 20-23). The 1904 to 1908 editions do not list him there. " + LISTING_SON),
    # ---- 2026 Stettauer
    dict(hh="hh_stettauer_mrs_d", id="pa1904_stettauer_james", name="James Stettauer", rel="son", grade="inferred",
         sources=BB(1890, 1891, 1892, 1893, 1894, 1895), printed_as="2026 James Stettauer", lived_here={"years": "1890-1895", "on_scene_date": "no"},
         note="Listed at 2026 under Mr. and Mrs. D. Stettauer from 1890 to 1895, beside his brother Charles S. " + LISTING_SON),
    # ---- 2101 Pike
    dict(hh="hh_pike_eugene_s", id="pa1904_pike_charles_b", name="Charles B. Pike", rel="son", grade="inferred",
         sources=BB(1892, 1893, 1894, 1895, 1897, 1898, 1899), printed_as="2101 Charles B. Pike", lived_here={"years": "1892-1899", "on_scene_date": "no"},
         note="Listed at 2101 under Mr. and Mrs. Eugene S. Pike from 1892 to 1899, beside his brothers Eugene R. and William Wallace. " + LISTING_SON),
    # ---- 2112 Rothschild
    dict(hh="hh_rothschild_mrs_m_m", id="pa1904_rothschild_monroe_r", name="Monroe R. Rothschild", rel="son", grade="inferred",
         sources=BB(1897, 1898, 1899, 1901), printed_as="2112 Monroe R. Rothschild", lived_here={"years": "1897-1901", "on_scene_date": "no"},
         note="Listed at 2112 under Mrs. M. M. Rothschild from 1897 to 1901. " + LISTING_SON + " The 1910 census has her the mother of five children, all living (ED 167, sheet 7B, line 87, leaf n1462)."),
    dict(hh="hh_rothschild_mrs_m_m", id="pa1904_rothschild_mamie_f", name="Mamie F. Rothschild", rel="daughter", grade="attested",
         sources=[C10] + BB(1899, 1901, 1908, 1909, 1910), printed_as="2112 Miss Mamie F. Rothschild",
         lived_here={"years": "1899-1901; 1908-1910", "on_scene_date": "unknown"},
         census_1910=c10("167/7B", 89, "Austrian, Maurice R.", "Daughter"),
         note="Listed at 2112 as Miss Mamie F. Rothschild in 1899 and 1901; married to Alfred S. Austrian, she is back in the house from the 1908 edition, and the 1910 census lists her there as the widow's daughter, married eight years, with her own daughter Margaret, 6 (ED 167, sheet 7B, lines 88-90; the given name is written as it reads, 'Maurice R.'). Where she lived in 1904 is not in the sources read."),
    # ---- 2115 Armour
    dict(hh="hh_armour_mrs_philip_d", id="pa1904_armour_john_o", name="John O. Armour", rel="son", grade="inferred",
         sources=BB(1890, 1891), printed_as="2115 John O. Armour", lived_here={"years": "1890-1891", "on_scene_date": "no"},
         note="Listed at 2115 under Mr. and Mrs. Philip D. Armour in 1890 and 1891. " + LISTING_SON + " He was J. Ogden Armour, who succeeded his father at the head of Armour and Company, but the book does not say that either."),
    dict(hh="hh_armour_mrs_philip_d", id="pa1904_armour_philip_d_jr", name="Philip D. Armour jr.", rel="son", grade="attested",
         sources=BB(1890), printed_as="2115 Phillip D. Armour jr.", lived_here={"years": "1890", "on_scene_date": "no"},
         note="Listed at 2115 under his parents in the 1890 edition; the 'jr.' names him the son of the house."),
]

# Cards already on file whose relationship the 1910 (and 1900) census states.
RECLASS = [
    dict(hh="hh_otis_mrs_joseph_e", id="pa1904_jenkins_mrs_john_e", rel="daughter", add_sources=[C10],
         census_1910=c10("166/6A", 10, "Jenkins, Lillian", "Daughter"),
         note_add=" The 1910 census names her Lillian Jenkins and lists her as Mrs. Otis's daughter, aged 49, with her husband and their son Elliott, 19 (ED 166, sheet 6A, lines 9-11)."),
    dict(hh="hh_kellogg_mrs_c_p", id="pa1904_kellogg_mrs_lois", rel="daughter", add_sources=[C10],
         census_1910=c10("167/6B", 76, "Kellogg, Lois", "Daughter"),
         note_add=" The 1910 census lists Lois Kellogg at 1923 as the daughter of the head, Sarah H. Kellogg, divorced, aged 43 (ED 167, sheet 6B, lines 75-76)."),
    dict(hh="hh_mcbean_a_j", id="pa1904_mcbean_george_b", rel="son", add_sources=[C10],
         census_1910=c10("167/2A", 10, "McBean, George B.", "Son"),
         note_add=" The 1910 census again lists him as son, of the widowed Georgiana McBean (ED 167, sheet 2A, line 10)."),
    dict(hh="hh_mcbean_a_j", id="pa1904_mcbean_a_j_f", rel="son", add_sources=[C10],
         census_1910=c10("167/2A", 14, "McBean, Archibald J.", "Son"),
         note_add=" The 1910 census again lists him as son, as Archibald (ED 167, sheet 2A, line 14)."),
]

# Notes that name a '& dr.' daughter from the 1910 census, appended to the card's own line.
NAME_NOTES = {
    ("hh_einstein_m", "pa1904_einstein_daughter"): " The 1894 Blue Book lists a Miss Anna B. Einstein at 1628, and the 1910 census lists Anna B. Einstein there as the unmarried daughter at home (ED 166, sheet 8B, line 92), so she is very likely the one the book means.",
    ("hh_bellas_t_h", "pa1904_bellas_daughters"): " The 1910 census lists the household under Erastus Foote, with Emma L. Bellas, widow, as his sister and Helena M. Bellas, 23, and Edith Bellas, 20, as his nieces (ED 166, sheet 9A, lines 1-4): very likely the daughters the book means.",
    ("hh_buckingham_e", "pa1904_buckingham_daughters"): " The 1910 census names the daughters at home as Kate S. Buckingham, 51, and Lucy U. Buckingham, 40, with their brother Clarence (ED 167, sheet 5B, lines 81-84).",
    ("hh_longini_a", "pa1904_longini_daughter"): " The 1910 census lists Adele L. Stix, 30, at 1626 as the widowed Rose Longini's daughter, married six years to Solomon H. Stix (ED 166, sheet 5A, lines 45-49): very likely the daughter at home in 1904, married soon after.",
}
