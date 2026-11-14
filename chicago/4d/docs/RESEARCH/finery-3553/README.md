# Finery: the women's dress of 1904, and the cloth of 1812 as its records name it (T-3553)

The owner, 2026-11-14 (thread "Dress women in finer, varied clothing"): *"Can you improve the
women's clothing for people like when i see shows like gilded age they are very fancy and lots of
details and you don't have that while i get that is fiction I would think maybe some of these
women would have nicer clothing and while it is frontier a bit I imagine they would have fine
dresses. Give the women some variation in their clothing appearance"*.

## What was there

- 1904: 99 ladies of the Prairie Avenue houses wore the one reconstructed day suit of the
  reference body (`data/humans/recipes/lady_1904.json`: shirtwaist, black jacket with revers and
  basque, gored skirt, one wide black hat with plumes) in six dark colours. Maids, cooks and
  companions were recoloured the same way. The cook's material is named "print" and her apron
  "check"; both were drawn as flat colours.
- 1812: the dress files already name each person's cloth from the period readings (a red calico
  short gown, a blouse of blue-and-white check, a blue-striped petticoat, ticking trousers, a
  frock of pink sprigged cotton), but every cloth was drawn as one flat colour.
- 1835: one drawn woman (Mary Flynn), a plain working dress; nothing to vary yet (the 1835
  population is T-3556's).

## What the references show (each is a `data/sources/` record, viewed 2026-11-14)

The Met's Costume Institute, open-access photographs of dated garments, 1899–1905 (none of
Chicago, none of anyone drawn here):

| source | what it shows | drawn as |
|---|---|---|
| `met_ci_1902_black_wool_suit` (already the lady's reference) | black wool suit, cream lace yoke and collar, braid at the skirt's seams | the walking suit |
| `met_ci_1900_1905_gluck_braided_ensemble` | cream silk coat and skirt with frogged braid and braid scrolls | soutache braid at hem and cuffs |
| `met_ci_1902_1905_blue_silk_dress` | pale blue-green silk, lace yoke and collar, lace motifs on the skirt, lace at the wrists, tucks and a band above the hem | the coloured silk afternoon dress |
| `met_ci_1903_white_lingerie_dress` | sheer white cotton, lace yoke, satin sash, insertion bands | the lingerie dress and sash |
| `met_ci_1903_white_cotton_dress` | tucked bodice, bishop sleeves into long cuffs, tucked skirt and flounce | pin tucks and the flounce |
| `met_ci_1903_1905_linen_afternoon_dress` | cream linen, openwork embroidery, a deep worked hem band | embroidered bands |
| `met_ci_1903_hallee_velvet_afternoon_dress` | brown silk velvet, ribbon bands crossing the bodice and the hem, lace collar and cuffs | the velvet afternoon dress |
| `met_ci_1900_1903_rouff_jet_dinner_dress` | dark velvet, a jet-beaded bolero, lace front, a wide sash | jet beading for an older woman |
| `met_ci_1900_striped_summer_dress` | pale green stripe with black velvet ribbon, flounced hem | striped summer silk |
| `met_ci_1901_1902_straw_tricorne` | straw, the brim turned up and waved, ostrich plumes and dotted ribbon | the picture hat and plumes |
| `met_ci_1900_flower_wreath_hat` | a wreath of silk flowers with leaves, a velvet bow | flowers and bow |
| `met_ci_1903_crocker_mourning_toque` | a brimless ruched black silk toque | the toque |

Street distance: `loc_detroit_1904_easter_crowds_fifth_avenue` and
`loc_johnston_1905_fairbanks_cornerstone_address` (already the lady's reference set) show dark
coats and bodices, white collars, lace jabots and trimmed hats on women of the years.

## What was built

- **The cloth** (`renderers/web/js/fabric.js`, the garments' one program, no texture): a woven
  or printed figure (stripe, check, dot, sprig, damask, plaid, pin stripe) run round the body so
  it falls down a skirt's gores, faded to its mean colour before it can alias; up to four trims
  laid at a height from the hem or the top, or round the sleeves' ends: ribbon or velvet bands,
  lace (a fine net with flowers over the shadow of the cloth beneath, a scalloped foot), soutache
  braid in scrolls, pin tucks, jet beads, a gathered flounce, embroidered sprays; silk (smoother,
  shinier) and velvet (a dark face, a bright rim).
- **The person's numbers** (`renderers/web/js/human-finery.js`): a dress record's `finery` laid
  on that person's own material clones, in the garment's own bind-pose units.
- **Hats** (`renderers/web/js/human-hats.js`): the picture hat (wide brim, low crown, perched and
  tipped, one side turned up, the edge waved), the straw sailor and the ruched toque, with ostrich
  plumes, silk flowers and leaves, and a ribbon bow.
- **By season** (`human-looks.js dressInSeason`, `humans.js setSeason`): a record's own dress is
  summer's (the town opens in summer); `seasons.spring|fall|winter` lay another over it, and the
  Settings › Season choice redresses everyone who has one.
- **1904** (`tools/finery_1904.py`, called by `tools/prairie_people.py`): each lady is dealt, by
  her id, a summer dress (silk afternoon dress, white lingerie dress, shirtwaist and skirt, a few
  light suits), a spring and fall one (suits, afternoon dresses, some velvet) and a winter one
  (suits, velvets, a few silks), each with its own colours, lace, trims, figure and hat. A woman of
  sixty or more mostly wears black, grey or mauve silk with jet (half-mourning colours) and a toque
  outside summer. Maids wear their dark afternoon dress or (45 %) a morning print; cooks a print
  dress and a checked apron; companions a tucked shirtwaist and a braided skirt; girls a white or
  pale frock with lace, tucks and a coloured sash.
- **1812** (`tools/finery_words.py`, called by `tools/human_variation_kit.py`): every garment whose
  record's words name a check, a stripe, ticking, a calico, a print or a sprig is drawn with that
  figure, its mean colour kept to the record's.

## What is reconstructed (liberty L-finery-3553)

Every woman's choice of dress, its colours, its trims and its hat; every 1812 figure's colour
where its words give one colour, and every figure's scale. No garment of any named woman is
claimed, and no picture is traced or sampled.

## Not done

- Shapes: the bodice, sleeves and skirt are the reference body's own (no pouched front, no
  leg-of-mutton or bishop sleeve, no train). Those need new GLB pieces and are not in this change.
- Furs and coats for winter.
- 1835 has one drawn woman; her dress is unchanged.
