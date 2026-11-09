# Back yards and side yards, Prairie Avenue district, 1 July 1904 (T-3488)

The research behind `tools/lay_prairie_1904_back_yards.py` and liberty `L-prairie-back-yards-3488`.
Written 2026-11-07 for the owner's ask of that day (back yards with terraces by the rear doors, walks
to the coach houses and the front steps, gangways and gardens). Section 0 is what changed when the
texts were read off their scans for the source records; the note below it is the survey as written,
and where section 0 corrects it, section 0 wins.

## 0. Read again at the source (T-3488 source records)

New records in `data/sources/`:

- `sheldon_artistic_houses_1884_field_house` — *Artistic Houses* vol. 2 pt 1 (1884), pp. 43-47,
  read off the archive.org scan `Artistichouses2`: "abundant breathing-room on the southern side,
  where a spacious lawn and scattered shade-trees suggest green fields" (p. 43); "Stables and other
  out-buildings are in the rear, on the side nearest the lake" (p. 44). The title page names no
  author; the Sheldon attribution is the catalogue's.
- `chicago_tribune_1899_08_15_butterflies_pullman_lawn` — read off the page image: "John Algots,
  keeper of the Pullman greenhouse, was at work on the lawn **in front of the residence**"; "Several
  young birch trees in the corner of the lawn"; "The vines on the side of the house". The article
  names no street side: **the note's placing of this lawn and its birches in the 18th Street court
  is not supported by it** (it rests on a 1897 item not read at its scan). The Pullman lot is left
  as T-1881/T-1934 drew it; no birches are added.
- `inter_ocean_1887_01_02_prairie_avenue_homes` — read only through chicagology's transcription
  (no scan found), so `verified: false`. Allerton's "unrivaled grounds" and "the lawn south of his
  home"; Einstein's house "stands back in well-kept grounds"; Glessner's "grounds within are not
  visible except from the house of the owner".
- `picturesque_chicago_1892_prairie_avenue_text` — p. 104: "the back yards of the buildings on the
  east side" along the Illinois Central.
- `glessner_scrapbook_1887_queer_house_clipping` — the court "40 x 100 ... to be sodded and adorned
  with fountain and flowers": the clipping's **newspaper is not identified** (the Glessner House
  blog says so), so it is not the "Chicago Herald" the note names.
- `glessner_blog_2015_06_queer_quaint_dutch` — the museum's statement that the courtyard's fountain
  and gardens were "eliminated in later modifications".
- `rand_mcnally_1893_guide_prairie_avenue_text` — p. 234: "the magnificent conservatory and spacious
  lawn, forming a private park, on the south side of Eighteenth Street".
- `chicago_tribune_1903_08_09_sherman_will_dooryard` — the widow's "dooryard" trees and lawn are at
  one of "three homes ... at Mount Clemens, Newport, and Chicago"; **the item cannot be tied to 2100
  Prairie**, so 2100 takes the district rule like any other lot.

What the layout does with this: no lot's back yard is drawn as a source shows it, because no source
shows one that the scene does not already draw (Glessner's court, Pullman's grounds, Field's lawn,
all left alone). Everything the tool lays is the district rule of section 2, as
`L-prairie-back-yards-3488` records, with two departures the owner asked for: a paved terrace at
every back door that has room ("patios and entertaining space near the rear doors"), and walks
round to the front steps ("walkways to the carriage houses and to the front steps and maybe in
gangways"). The back doors themselves are new: no worked model was built with one.

---


Research note for the owner's request: "if you see or have knowledge of backyard gardens in 1904 include them". Repo read-only; nothing here is committed.

**Tiers used below.** *Attested*: a source states it, quoted with a locator. *Inferred*: reasoned from a source of another date or kind, with the reasoning given. *Reconstructed*: a modelling choice for which no source was found. **What I checked and could not verify** is said where it applies. Quotes marked **[fetch]** were read through a web-page fetch of a transcription (chicagology.com or the Glessner House blog), not off a page scan. Re-read them against the original before a record quotes them.

**The finding, in one line.** No source found names a *kitchen garden*, a *tennis lawn*, a *grape arbor* or a *rose garden* on any lot in the drawn district in or near 1904. What the sources do attest is **lawns and shade trees** (on side yards above all), **vines on walls**, **glass** (Field, Pullman, perhaps 2140 and 2120), **walled service yards** and **stables on the alley**. One flower-garden scheme (Glessner) is attested as *intended in 1887 and dropped*.

---

## 1. House by house

### 1800 Prairie, Glessner: the courtyard (the best-documented back yard)
- **Size and place**: an enclosed court south of the house and its east and north ranges, open to the alley through a gate in the stable range, closed on the south by the wall of 1808 (O. R. Keith). "The court, 40 x 100" (Chicago Herald, late 1887, "A Queer House Out on the Avenue", as transcribed on the Glessner House blog, 8 June 2015, https://glessnerhouse.blogspot.com/2015/06/queer-quaint-and-dutch.html) **[fetch]**. *Attested* (a newspaper's round figure).
- **What was intended (1887)**: "It is the yard of the mansion, completely shut out from the view of neighbors or passers-by, … and is to be sodded and adorned with fountain and flowers and a neat bit of shrubbery." (same article) **[fetch]**. "The grounds within are not visible except from the house of the owner." (Inter Ocean, 2 Jan 1887, chicagology transcription, https://chicagology.com/chicagostreets/prairieavenue/) **[fetch]**.
- **What was dropped**: the museum states that "Richardson's original design for the Glessner courtyard did feature a fountain and elaborate gardens; these were eliminated in later modifications, presumably due to the fact the Glessners spent their summers in New Hampshire." (Glessner House blog, 8 June 2015, notes) **[fetch]**. That is later scholarship by the house's own institution, not a period source. The design watercolour (stream-1800 `a18-gh-courtyard-watercolor`) is already excluded as an unbuilt design.
- **Vines (attested 1887)**: "The Virginia Creeper vines on the courtyard walls were carried from the old home. All were properly trimmed before replanting except one which was fifty-five feet long, and which when planted was trained its full length. We hardly expected that to grow, but it did, and flourished." (`glessner_story_of_a_house_1923`, HABS ILL-1015 data p. 9). Boston ivy on the street fronts (same page). Their extent in 1904 is not recorded.
- **Ground**: HABS photograph 5 (`habs_glessner_photo_05_court_c1923`, rights check_required) shows "a lawn with a hard carriage drive along the south side" and "bare vine stems on the tower and the bow", c. 1923. HABS data p. 2: in 1946 "the courtyard entirely paved to serve as a parking lot", so it was not paved before 1946. The scene already draws lawn and drive (LIBERTIES L295 and its successors).
- **Summer**: the 1904 household card records the family at The Rocks, New Hampshire, at the 1900 enumeration (`hh_glessner_john_j`). On 1 July the court would have been kept, not used.
- **Recommendation**: keep lawn and drive. **Add the Virginia creeper on the court walls** (attested planting; its 1904 extent *reconstructed*: the stair tower and the bow, which HABS 5 shows carrying stems in 1923). **No fountain and no flower beds**: the museum says these were eliminated. A visitor should be able to read why the court is plain.

### 1729 Prairie, Pullman (house lot) and 1800 Calumet (glasshouse "park")
- "John Algots, keeper of the Pullman green house, was at work on the lawn"; "Several young birch trees in the corner of the lawn presented a curious sight"; "The vines on the side of the house …"; "a stream of water from the lawn hose" (Chicago Tribune, 15 Aug 1899, "Butterflies in a Cloud", via chicagology 1729 page) **[fetch]**. *Attested* for 1899: a lawn on the house lot with young birches in one corner, vines on a side wall, a hose, and a resident greenhouse keeper.
- "The corner of the lawn runs almost to the spot where stood the once famous massacre tree" (Tribune, 20 Oct 1897) **[fetch]**. The tree stood in 18th Street east of Prairie (stream-chicagology-north #82), so this lawn is the **18th Street (south) side** of the house.
- The fallen tree's trunk was "deposited in Mr. Pullman's two gardens, one on each side of Eighteenth street" (Tribune, 20 May 1894) **[fetch]**. So there were two gardens: the house lot and the glasshouse ground at 1800 Calumet.
- Rand McNally 1893 guide, p. 234 (stream-streetscape #4): conservatory and lawn on the south side of 18th Street toward Calumet. Chicagology: the 1892 Beman addition with "outdoor terraces set with marble mosaics".
- Post-1904, describing the house still standing: "it is surrounded with large gardens, shaded in spring and summer with trees" (Tribune, 29 Mar 1921) **[fetch]**. It is evidence of the 1921 state only. Mrs. Pullman held the house from 1897 to 1921, so it is a fair *inferred* bound for 1904.
- **Photos**: Inland Architect 1894 conservatory plate (`inland_1894_pullman_conservatory`, public domain): gravel drive between stone gate piers, lawn, shrubs, young trees. AIC Lowe c. 1897 (`aic_lowe_pullman_conservatory_c1897`, AIC "contact archives"): a large tree in leaf and shrubs. Taylor AIC 16554 (rights check_required): broad lawn on 18th Street. CHM Clark 1905 (`chm_clark_i71913_pullman_1905`, no known restrictions): in leaf.
- **Where on the lot**: the Sanborn 1911 sheet 20 draws the 1B range north of the court and the stable at the east end, looking south onto the court. The court between the range and the 18th Street wall (piers and urns, stream-1600-1700 #19) is the lawn the 1897 and 1899 texts describe. The front yard already carries lindens and the coping border.
- **Recommendation**: in the 18th Street court, lawn, a clump of 3 to 5 young birches in the south-east corner (attested 1899, five summers before the scene, so *inferred*), and creeper on a side wall (attested 1899). At 1800 Calumet, lawn and drive as drawn, plus a few shade trees (*inferred* from the 1897 photograph and the 1921 text).

### 1905 Prairie, Marshall Field
- "a large and roomy mansion, standing by itself, with abundant breathing-room on the southern side, where a spacious lawn and scattered shade-trees suggest green fields and the natural attractions of the country." … "a high porte-cochere on the northern side, and a fine large conservatory on the" southern. (Sheldon, *Artistic Houses* vol. 2 pt 1, p. 43–44, 1883–84; archive.org `Artistichouses2`, read off the OCR text). *Attested* for 1883.
- "Stables and other out-buildings are in the rear, on the side nearest the lake" (same text, as quoted in stream-1900 `a19-ah-field-text`).
- "a conservatory fitted with rare flowers" (Inter Ocean, 2 Jan 1887) **[fetch]**. "The extensive conservatory that spans the south wall of the house" (Inter Ocean, 27 Nov 1873) **[fetch]**.
- 1912 Prairie's lot was "overlooking the open grounds of Mr. Field" (Tribune, 8 June 1887, stream-1900 #24).
- c. 1905: `cdn_dn0003324_field_residence` (public domain) shows the iron picket fence along "the street line and the south yard". The south yard was still open at the scene date.
- **Recommendation**: the south yard (on a 166.7-ft lot with a 55-ft house) as open lawn with scattered shade trees (*attested* 1883; *inferred* for 1904 from the c. 1905 fence). Elms or maples are *reconstructed* species. No beds are attested.

### 1918/1936 Prairie, Thompson–Allerton (NW corner of 20th)
- Samuel Allerton "refused $117,000 for the lawn south of his home"; "its unrivaled grounds" (Inter Ocean, 2 Jan 1887) **[fetch]**. "big red brick house and ample grounds" (Tribune, 9 Jan 1898, per stream-1900 #23). The 1883 New Chicago Album vignette (`newberry_new_chicago_album_1883_residences`, no known restrictions) shows the villa "behind trees and a long iron fence, lawn and curving walk". Sanborn census ruling r28-allerton: the bare "1936" corner is "the Allerton lawn".
- Lot 193 ft by 175 ft. The barn is 39 × 80 ft (Tribune, 30 Oct 1869).
- **Recommendation**: the 20th Street corner as lawn with a curving walk and trees (*attested* 1883–1898).

### 1701 Prairie, Hibbard (east side, backing on the IC)
- The rear photograph (`glessner_blog_1701_hibbard_rear_photo`, check_required; undated, after 1874) is the one period photograph of a back yard in the district: "a two-storey columned rear porch/veranda with balustrades and steps down to the lawn … and children with prams on the lawn". The lawn falls toward the lake.
- **Recommendation**: a rear lawn east of the house to the railway fence (*inferred* for 1904). No beds are shown.

### 1637 Prairie, Spalding
- The undated engraving of the remodel (`glessner_blog_1637_spalding_remodel_engraving`, rights unknown) shows a "high brick garden wall at left and iron fence at right". The Sanborn 1911 sheet shows three unbuilt lot strips (27, 25 and 19 ft) between 1625 and 1637 (census `s20-vacant-east-1625-1637`).
- *Hypothesis, not evidence*: the wall enclosed a garden on the open strips north of the house. No deed or lot owner has been read, so do not draw it as Spalding's until one is.

### 1628 Prairie, Einstein
- "stands back in well-kept grounds" (Inter Ocean, 2 Jan 1887, stream-chicagology-north #117). A two-storey barn was permitted in 1882. Lawn only.

### 1827 Prairie, Doane
- The photograph (`chicagology_1827_doane_exterior`, check_required) shows a "low cast-iron fence on a stone curb around a lawn, and the coach house … visible at right rear across the side yard". The side yard is lawn, open to the coach house (*inferred* for 1904).

### 1815 Prairie, Sears/Meeker
- The Sears children's log-cabin playhouse stood in the grounds until 1892 and was then moved to Kenilworth (stream-chicagology-north #100). **Absent in 1904.** No garden evidence for the Meekers' years was found. The memoir *Chicago, with Love* (1955) was not reachable.

### 1811 Prairie, Coleman–Ames
- "light on all sides … 2 story stable" (`chicago_tribune_1904_04_16_1811_prairie_to_rent`). On the 1891 plate (`carlson_greeley_1891_prairie_environs`) the house runs 5.7–32.8 m from the street and the stable 38–46 m on a 150-ft lot. That leaves **about 5 m between house and stable**: a service yard, not a garden.

### 1801 Prairie, Kimball
- The carriage house is attached to the south side (HABS ILL-1077 p. 5). The HABS description of the yard ("no landscaping", south yard paved, chain-link) is the 1967 state and **not 1904 evidence**. George Glessner's 1887 photograph shows the lot empty with a diagonal path (Glessner House blog, May 2013). For 1904, the narrow south yard between the carriage house and 1811 is lawn (*reconstructed*).

### 2100 Prairie, Sherman
- The widow "will have to take care of the trees in her dooryard, saw off the dead limbs herself, and keep her own lawn in trim" (Tribune, 9 Aug 1903, stream-newspapers-south #28). Mature trees and a lawn (*attested* 1903). "Dooryard" does not say front or rear.

### Walls the 1911 Sanborn draws (backcast to 1904 by the census; *inferred*)
- **2036 Buckingham**: a 6-ft brick wall along 21st Street and an 8-ft wall on the alley line, so a walled corner yard.
- **2010**: an 8-ft brick wall along the alley south of the stable.
- **2005**: a 16-ft brick wall on the south line from the rear range to the alley.
- **2140 Smith**: the stable "standing free in the yard, north of the house", an 8-ft wall closing the yard on the north, and a one-storey **glass room lettered GLASS** (a conservatory candidate, 1911 only).
- **2000 / 2026**: house "set back on a deep lawn" and "the wide unbuilt ground south of the house … Lawn in 1904" (census).
- **2120 Gorton**: a domed or conservatory bay in the undated chicagology photo, possibly the music room.

### No garden evidence found
1808 O. R. Keith, 1900 Elbridge Keith, 1906 Edson Keith, 1919 Field Jr., 1700/1706 Glessner children, 1912 Lowden, 2115 Armour (its elms are in the *front* lawn, Tribune 7 Jan 1901), 1945 Corwith (creeper-covered in 1928, `chicago_tribune_1928_07_29_famous_homes_corwith`; inferred for 1904 at most), 2013 Reid (the NRHP 2003 "rear garden" plan and photos postdate its 1910 coach house: **not 1904**).

**Sanborn greenhouses**: on sheets 20, 28 and 35 only Pullman (1800 Calumet "GREEN HO. GLASS RF."), Field ("Greenhouse" at the bay) and 2140 ("GLASS") carry glass. No other lot has a free-standing greenhouse.

---

## 2. The general pattern, and a rule

### What a back yard was here (evidence)
- **Depth.** Lots are 176–182 ft to a 20-ft alley (median 178.8 ft, `data/street_grid/1904.json`). In the sidecar placement notes the main body's rear corner stands at a median of about 28 m off the rear lot line, and the coach house at 0–1.75 m. With a stable 8–12 m deep, the ground between house and stable is about **10–18 m deep**, less any rear wing. It is often only ~5 m (1811), and the house's own rear wings fill part of it.
- **Use.** In the 1900 census a coachman's family lived "in the rear building behind the house" at several households (household cards). Laundresses were enumerated at 16 of the 71 carded households, so wash was done at home. **No live-in gardener was enumerated at any carded household.** The only gardener named in the district is Pullman's greenhouse keeper (1899). The yard was the stable's and the kitchen's working court: carriage way, cinder, ash box, drying. It was not a cultivated plot.
- **Display went on the side yard, not the back.** Every attested lawn with trees (Field, Allerton, 2000, 2026, Doane, Pullman's 18th Street side) is a *side* yard on a double lot, seen from the street. The single exception is the east side backing on the IC (Hibbard), where the rear faced the lake: "the back yards of the buildings on the east side" (*Picturesque Chicago*, 1892, pp. 101–104).
- **Enclosure.** Brick walls of 6–16 ft on alley and side lines (Sanborn). Glessner's court was "completely shut out from the view".
- **Season.** 1 July 1904 was a Friday, so not the conventional Monday wash day (a convention, *reconstructed*). Many households summered away (Glessner). Lawns would have been mown by day-men or coachmen, and beds were bedded out (front-yard rule).

### Proposed deterministic rule (seed by parcel id, as `plant_prairie_1904_front_yards.py` does)
Apply in order. The first match wins.
1. **Attested lots, drawn as their sources say**: 1800 court (lawn, drive, creeper), 1729 18th Street court (lawn, birch clump, creeper), 1905 south yard and 1918/1936 corner (lawn, scattered shade trees, Allerton's curving walk), 1701 rear lawn to the IC, 2100 lawn with mature trees, 1800 Calumet (as drawn, plus trees).
2. **Side lawn**: the lot has unbuilt frontage beside the house of at least 0.6 × the house's own width (2000, 2026, 1801 south strip, 1906/1908, 1923, 1709, 1720, 2140), or the census writes "lawn". Turf to the side fence, 1–3 shade trees (maple or elm, seeded) where the strip is ≥ 12 m wide, a shrub border along the lot line using the front-yard plant list, and at most one bedded-out round bed on lots of ≥ 100 ft frontage. *Reconstructed* except as cited.
3. **Service court** (default for Prairie lots with a stable on the alley): a cinder carriage way from the stable's doors to the kitchen or rear-wing door; turf on the rest only where the free depth is ≥ 6 m; one tree when depth ≥ 14 m and width ≥ 15 m (hash < 0.35); creeper on the stable's yard face (hash < 0.33); an ash box at the alley; clothes posts without lines where the household card lists a laundress. No flower garden. *Reconstructed.*
4. **Walled yard**: lots where Sanborn draws a brick wall (2036, 2010, 2005, 2140) take rule 3 inside the walls, with creeper on the wall's yard face (hash < 0.5).
5. **Open rear, no outbuilding** (1608, 2003, 2005, east-side lots on the IC without a stable): lawn to a board fence, a lilac or two at the fence (seeded). On IC lots, a rear lawn as at Hibbard.
6. **Modest lots** (Indiana and Calumet frame houses, flats, rooming houses, lots with a `_shed` or `_rear_dwelling` record): beaten-earth drying yard with lines, a board fence, and on hash < 0.3 a small vegetable or flower patch of ≤ 3 × 4 m against the sunny fence. This is the **only place a kitchen garden appears, and it is reconstructed** (no source names one in the district). Record it as such.
7. **Commercial, institutional or vacant**: none.

Every item of rules 2–6 belongs under one liberty (e.g. `L-prairie-back-yards-1904`) in `docs/LIBERTIES.md`, tier *reconstructed*. A photograph of a given lot overrides its rule.

---

## 3. Sources worth adding as records (none exist in `data/sources/` for these texts)
1. **Sheldon, *Artistic Houses*, vol. 2 pt 1 (1883–84), pp. 43–47**, "Mr. Marshall Field's House". https://archive.org/details/Artistichouses2. Public domain. The quote is verified on the OCR text.
2. **Chicago Herald, late 1887, "A Queer House Out on the Avenue"**, as transcribed by the Glessner House blog, 8 June 2015. https://glessnerhouse.blogspot.com/2015/06/queer-quaint-and-dutch.html. The text is PD; the blog is check_required. The original issue date is not established, so find the scan.
3. **Glessner House blog, 8 June 2015** (the same URL), as a separate secondary record for the museum's statement that the fountain and gardens were eliminated.
4. **Daily Inter Ocean, 2 Jan 1887** (Prairie Avenue survey; chicagology transcription): Allerton's lawn, Field's conservatory, Glessner's enclosed grounds, Shortall's iron fence, the Einstein grounds. Only a 1620 extract of it exists now (`inter_ocean_1887_1620_prairie_olive_green`).
5. **Chicago Tribune, 15 Aug 1899, "Butterflies in a Cloud"**: the Pullman lawn, birches, vines and greenhouse keeper. https://chicagology.com/chicagostreets/prairieavenue/1729prairie/. Find the archive.org issue `per_chicago-daily-tribune_1899-08-15`.
6. **Chicago Tribune, 20 May 1894, "Chips for Souvenirs"** ("Mr. Pullman's two gardens"). Same page.
7. **Chicago Tribune, 20 Oct 1897** (the corner of the Pullman lawn) and **29 Mar 1921** ("surrounded with large gardens"; post-1904, carried only as a bound).
8. **Daily Inter Ocean, 27 Nov 1873** (the Field conservatory "spans the south wall"). https://chicagology.com/chicagostreets/prairieavenue/1905prairie/
9. **Chicago Sunday Tribune, 9 Aug 1903**, the Sherman will. https://archive.org/details/per_chicago-daily-tribune_1903-08-09_62_32
10. **Chicago Tribune, 9 Jan 1898**, Allerton's "ample grounds", and **8 June 1887**, the "open grounds of Mr. Field". Both are chicagology transcriptions. Find the scans.
11. **Rand McNally's bird's-eye views and guide (1893), pp. 232–234**, text. https://archive.org/details/randmcnallycosbi00lawr. Public domain.
12. **Picturesque Chicago (1892), pp. 101–104**, text ("back yards … on the east side"). https://archive.org/details/picturesquechica00baltiala. Public domain. Only its plate is a record now.

**Period photographs of back or side yards on these blocks** (URL, rights):
- Hibbard rear: https://glessnerhouse.blogspot.com/2014/06/prairie-avenue-in-1874.html. Rights unknown; text cross-check only.
- Pullman conservatory, Inland 1894: https://digital-libraries.artic.edu/digital/collection/mqc/id/8465. Public domain.
- Lowe c. 1897: https://digital-libraries.artic.edu/digital/collection/mqc/id/76204. AIC "contact archives".
- Taylor 16554: https://digital-libraries.artic.edu/digital/collection/mqc/id/29313. check_required.
- Doane side yard: https://chicagology.com/chicagostreets/prairieavenue/1827prairie/. check_required.
- Allerton lawn, 1883 album: https://collections.carli.illinois.edu/digital/collection/nby_chicago/id/7411. No known restrictions.
- Glessner court, HABS 5, c. 1923: https://hdl.loc.gov/loc.pnp/hhh.il0118/photos.060907p. check_required. Post-date.
- Florian 1948: copyright; post-date.

**Leads not reached**: Frances Glessner's journal (Glessner House; the blog quotes none on the court); Molloy, *Chicago's Historic Prairie Avenue* (Arcadia 2003); Meeker, *Chicago, with Love* (1955); the Houghton courtyard elevations; the 1891 Greeley-Carlson plates for other lots' outbuildings. Tribune full-text search for "Prairie avenue" with "garden" or "lawn" for 1900–1905 could also be run on the archive.org OCR.
