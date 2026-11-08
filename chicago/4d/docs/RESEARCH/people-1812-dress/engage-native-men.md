# 1812 dress: the engagé and the Potawatomi man (group "engage-native-men")

Two role assets on the shared male rig, built like the 1812 private (T-3451): one generator, one
recipe and one test per role, four LODs exported to `assets/humans/` and `assets/humans/web/`, the
contract checked on all sixteen GLBs. Each asset is a ROLE, never a person: every wearer gets his own
face, height, build, complexion and hair from the variation kit and the looks layer.

## Assets

| asset id | role | body | files |
|---|---|---|---|
| `engage_1812` | a French Canadian or Métis engagé / voyageur of a Chicago trading household | `prepared_adult_35` | `tools/human_engage_1812.py`, `data/humans/recipes/engage_1812.json`, `tools/test_human_engage_1812.py` |
| `potawatomi_man_1812` | a Potawatomi man of the camp at Chicago, everyday dress of 14 August 1812 | `prepared_adult_25` | `tools/human_potawatomi_man_1812.py`, `data/humans/recipes/potawatomi_man_1812.json`, `tools/test_human_potawatomi_man_1812.py` |

Web LODs (meshopt) against the private's (`private_first_infantry_1812`):

| LOD | private | `engage_1812` | `potawatomi_man_1812` |
|---|---|---|---|
| lod0 | 4,589,652 B, 44,914 tris | 4,463,424 B, 41,661 tris | 4,554,528 B, 44,047 tris |
| lod1 | 1,672,800 B, 27,310 tris | 1,574,512 B, 25,362 tris | 1,651,276 B, 26,791 tris |
| lod2 | 680,468 B, 13,442 tris | 614,148 B, 12,538 tris | 667,496 B, 13,198 tris |
| lod3 | 341,616 B, 6,489 tris | 297,364 B, 6,107 tris | 336,864 B, 6,392 tris |

Both are under the private at every LOD: the shared skin atlas, flat colours in the materials, the
recipe's `lod_ratios` equal to the soldier's (the tests check it). Masters (`assets/humans/*.lod*.glb`):
engagé 8.78 / 8.08 / 7.47 / 7.22 MB; Potawatomi 9.08 / 8.26 / 7.55 / 7.26 MB.

LOD0 body custom-normal readback, built with `--normal-tolerance 5e-3` as the coordinator directed:
engagé max vector delta **0.002817**; Potawatomi **0.001291**.

## Who wears which

**`engage_1812`** — the engagés, boatmen and carriers of Kinzie's and the other trading households
(Wau-Bun's engagé, the Kinzie boatmen), Antoine Ouilmette (a French Canadian of Chicago since about
1790, Potawatomi by marriage), Point de Sable's kind of men (Point de Sable himself left Chicago in
1800), and the Chicago militia of 1812, whose men were drawn from the same households. **Jean
Lalime** does not need it: he was killed by John Kinzie in the spring of 1812 (after 13 April) and is
`dead_before` the scene date in `docs/RESEARCH/people-1812-3461/civilians.json` (`lalime_john`,
`present_14aug`), so he is not in the August town. If he is ever drawn on an earlier date, an interpreter at the fort fits the trader's
civil dress (shirt, waistcoat, coat, round hat) better than the engagé's, and the trader's asset of
the officers-traders group should serve.

**`potawatomi_man_1812`** — every Potawatomi man of the camp: the men, the chiefs and the elders
(they differ by looks and age; medals and gorgets, recorded only for named men, are not drawn, so no
new geometry), and the Miami of Wells's escort (see below). Grey hair and the hair cut are the looks
layer's.

## Evidence choices

### The engagé

Garments (each graded `inferred`, with source ids and scope in the recipe): a blue calico shirt (the
1835 labourer's cut, worn outside the trousers under the sash), a red worsted sash knotted at the
left hip with two ends hanging, deer-skin trousers (the labourer's trouser shell), smoked moccasins
(the shared closed foot loft) and a red knitted cap with its top falling back.

- **Deer-skin trousers, not breechcloth and leggings**: Wau-Bun gives the Chicago engagé of 1812 "a
  suit of deer-skin, with belt, moccasins"; Hubbard (1818) wore breech-cloth and leggings, but that
  is the Potawatomi man's dress here, and keeping the two roles apart at a distance matters.
- **Sash**: Wau-Bun's Fox River *mitiff* (1830) with "a coloured scarf round the waist"; Lambert
  (1810) and Heriot (1807) the habitant's worsted sash. Red, as the sources' commonest.
- **The head** is the hard choice. Summer evidence leans to a bare head (Hubbard, 1818: a red knit
  cap "sometimes in winter", otherwise "usually went bareheaded", hair long) or a straw hat
  (Lambert's habitant in summer; Wau-Bun's 1830 mitiff; Heriot's summer straw hats); the red knitted
  cap is the year-round one (Lambert: "worn the whole year round"; Wau-Bun's voyageurs' tuque, ch.
  IV; Heriot's knitted caps). The cap is modelled because a bare head would show the shared short
  European crop where these men wore their hair long or in a queue, and no kerchief is in any text
  read. A bareheaded engagé with long hair and the straw hat are recorded alternatives, not modelled.
- `review_required: true` (it may stand for a Métis man: an evidence-bounded depiction under the
  standing constraint), `touches_removal: false` with its own prose (the dress touches no removal
  history; a wearer such as Ouilmette, whose family went west with the Potawatomi, carries his own
  flag on his own record).

### The Potawatomi man

Garments follow Keating's Metea (Fort Wayne, 1823), the nearest dated, detailed eyewitness
description of a Potawatomi man, with the goods given out to the camp on the 13th (Wau-Bun; Heald):
a blue-and-white check trade shirt worn loose to mid-thigh, a blue broadcloth breechcloth with flaps
before and behind, scarlet stroud leggings to the instep with flaps along the outer seam and the
undyed white selvage at the flap's edge, dark woven garters below the knee, a white wool blanket
with dark stripes near its ends belted round the waist and open in front, a dark leather belt, one
silver arm band on each upper arm and three small silver brooches down the shirt, smoked moccasins.
All `inferred` but the leggings (`reconstructed`: Keating's men of 1823 wore leather; stroud is the
T-3467 day research's "more usual" reading and the broadcloth of the 13th).

- **Blanket round the waist, not over the shoulders**: Keating's "secured round his waist by a
  belt"; Lambert's "In warm weather ... fasten it round their waist"; it is August (T-3467: "set
  aside in the heat of the day"), and a mantle over the lowered arms cannot be built on this rig
  without the arms passing through it.
- **Shirt colour**: the T-3467 research names "checked blue-and-white, red-and-white or brown linen
  shirts"; a red-and-white check drawn as one flat colour read as a pink-brown jersey in the stills,
  so the blue-and-white check (its blend at a distance, a grey-blue) was chosen.
- **Silver**: Wau-Bun's list of the annual presents (ch. I: "silver-works (comprising arm-bands,
  bracelets, brooches; and ear-bobs)"). No gorget, medal or nose ring (recorded only for named men),
  no ear-bobs (too small to read).
- **Head and hair**: bare head; the asset carries only the shared short04 cap, and the hair is drawn
  per person by the looks layer's `clubbed_behind_1812` cut (T-3467: "long and tied or clubbed
  behind"; Keating's Metea with a lock and feathers, 1823; the Pecatonica man's plaited hair). The
  cloth head wrap (Lewis's Cha-co-to, 1827; Quaife's 1833 "handkerchief turbans") is later and a
  minority, so none is built in.
- **Not drawn**: paint (no war paint before the 15th; Keating's touch of vermilion is left out),
  feathers, arms, knife or pouch, quill and bead ornament on the garters, anything ceremonial or of
  the Plains.
- `review_required: true` and `touches_removal: true`, each with its own prose; the builder refuses a
  variant without them, and the test checks it.

### The Miami of Wells's escort

No source read describes their dress in 1812. Keating (p. 91) says only that "diversities of dress"
distinguish the Algonquian nations, without saying how; his Miami half-blood at Fort Wayne (p. 107)
wore a capote in place of a blanket; Lewis's Mi-a-qu-a (1826-27: broad silver arm bands, nose ring,
turban) is one chief's treaty dress fourteen years on. The T-3467 research's own grade note says the
same. So **`miami_man_1812` should map to `potawatomi_man_1812`**; no separate GLB was built. A
colour-only variant (a capote is new geometry, so not that) can be added if the integrator wants one,
but nothing in the evidence would pick its colours.

## Stills (people-match style rig: sky, sun, ground, skin atlas, looks complexion, fabric shader)

Scratch, the session scratch folder (not committed):

- engagé: `eng2_3m_front.jpg`, `eng2_3m_side.jpg`, `eng2_3m_back.jpg`, `eng2_3m_three.jpg`,
  `eng2_10m_front.jpg`, `eng2_close_headback.jpg`; sheets `eng2_sheet3m.jpg`, `eng2_sheetclose.jpg`.
- Potawatomi man: `pot3_3m_front.jpg`, `pot3_3m_side.jpg`, `pot3_3m_back.jpg`,
  `pot3_3m_three.jpg`, `pot3_10m_front.jpg`, `pot3_close_legs.jpg`; sheets `pot3_sheet3m.jpg`,
  `pot3_sheetclose.jpg` (complexion `brown`). `pot1_*` is the first build (pink-brown shirt, drum-like
  blanket, jagged flap selvage), kept for comparison.

## What still reads wrong

- **Engagé**: the deer-skin trousers take the fabric shader's cotton twill (see the fabric.js row
  below), so at 3 m they read as khaki cloth, not hide. The cap's tip is a closed tube end, not a
  pompom or a soft fold. The sash is a smooth band with no fringe at its ends.
- **Potawatomi man**: the blanket round the waist still reads stiffer than wool (no cloth simulation:
  a hanging loft with folds and drooping corners), and its top edge shows as a thin white rim above
  the belt at the sides; the arm bands read bright, almost white, because there is no metallic
  channel in the dress materials; the brooches read as buttons at 3 m. The breechcloth's front flap
  shows as a square of blue in the blanket's opening, which is right but looks plain. The stroud
  leggings take cotton twill, not wool (fabric.js row below). The white selvage on the flaps is a
  flat strip.
- Both: flat colours, so no calico print or check; T-pose fitting, so the stills are A-pose stills
  of the rig; moccasins are the shared closed foot loft, no seam or cuff.

## Rows for shared files (for the integrator)

### `assets/LICENSES.md` (sixteen rows; the private's wording)

```
| `humans/engage_1812.lod0.glb` | Original CC0-1.0 export of the canonical builder over the shared male base and the 1812 engagé's components (`tools/human_engage_1812.py`); reconstructed under L418 and L-human-modular-dress-1789, not a likeness. |
| `humans/web/engage_1812.lod0.glb` | Original CC0-1.0 export of the canonical builder over the shared male base and the 1812 engagé's components (`tools/human_engage_1812.py`); reconstructed under L418 and L-human-modular-dress-1789, not a likeness. |
```
and the same two for `lod1`, `lod2`, `lod3`; then

```
| `humans/potawatomi_man_1812.lod0.glb` | Original CC0-1.0 export of the canonical builder over the shared male base and the 1812 Potawatomi man's components (`tools/human_potawatomi_man_1812.py`); reconstructed under L418 and L-human-modular-dress-1789, not a likeness of any person; held for review under the AGENTS.md standing constraint. |
| `humans/web/potawatomi_man_1812.lod0.glb` | Original CC0-1.0 export of the canonical builder over the shared male base and the 1812 Potawatomi man's components (`tools/human_potawatomi_man_1812.py`); reconstructed under L418 and L-human-modular-dress-1789, not a likeness of any person; held for review under the AGENTS.md standing constraint. |
```
and the same two for `lod1`, `lod2`, `lod3`.

### `data/humans/variation/axes.json` (`assets` block)

```
"engage_1812": {"base_age_years": 35, "sex": "male", "basis": "data/humans/recipes/engage_1812.json: the same prepared_adult_35 engineering body as the 1835 labourer, an engagé of a trading household."},
"potawatomi_man_1812": {"base_age_years": 25, "sex": "male", "basis": "data/humans/recipes/potawatomi_man_1812.json: the prepared_adult_25 engineering body, a Potawatomi man of the 1812 camp (also chiefs, elders and the Miami escort)."},
```

### `tools/check.sh` (after the private's step)

```
step "An 1812 engagé's working dress is sourced, layered and skinned on the shared rig" \
  python3 tools/test_human_engage_1812.py
step "An 1812 Potawatomi man's everyday dress is sourced, layered, skinned and held for review on the shared rig" \
  python3 tools/test_human_potawatomi_man_1812.py
```

Each test takes about 20 s.

### `docs/LIBERTIES.md` / `data/liberties.json`: supplement to L-human-modular-dress-1789

**The 1812 engagé and Potawatomi man supplement, 2026-11-08:** two role dresses on the same
component path, each anonymous, graded reconstructed and naming no one. **The engagé**
(`tools/human_engage_1812.py`, `data/humans/recipes/engage_1812.json`, asset `engage_1812`, the
shared male body at 35): a French Canadian or Métis engagé of a Chicago trading household, after
Wau-Bun's engagé of 1812 ("a suit of deer-skin, with belt, moccasins", `kinzie_waubun_1856`) and the
habitant and voyageur dress of Lambert (1810), Heriot (1807) and Hubbard (1818): the 1835 labourer's
shirt and trouser shells in blue calico and deer-skin, a red worsted sash 8.5 cm deep knotted at the
left hip with ends of 30 and 23 cm, the shared closed foot loft as smoked moccasins, and a red knitted
cap seated 8.8 cm below the crown with its top rising 7.5 cm and falling 7.5 cm back, rigid on the
head. The cap is chosen over the bare head that Hubbard gives for summer because the shared short
crop beneath would misrepresent hair worn long; the straw hat and a bare head with long hair are
recorded alternatives. Held for review as a possible Métis depiction; `touches_removal` false.
**The Potawatomi man** (`tools/human_potawatomi_man_1812.py`, `data/humans/recipes/potawatomi_man_1812.json`,
asset `potawatomi_man_1812`, the shared male body at 25): everyday dress of 14 August 1812 after
Keating's Metea (1823, `keating_1824_narrative_v1`) and the goods given out to the camp on the 13th
(`kinzie_waubun_1856`): the labourer's shirt shell in a blue-and-white check with a hanging skirt to
0.70 m, a blue broadcloth breechcloth with flaps before and behind to 0.52 and 0.545 m, scarlet
stroud leggings on the shared trouser shell cut off at 0.78 m with flaps 3.2 cm wide along the outer
seam and a 9 mm white selvage, dark garters 5 cm below the knee, a white wool blanket with dark
stripes 5 cm from its ends belted round the waist from 1.04 to 0.505 m and open 30 to 42 degrees
either side of the front, a dark leather belt, a silver band on each upper arm and three silver
brooches. The blanket is worn round the waist (Keating; Lambert's warm-weather wrap) because a
mantle over the lowered arms cannot be built on this rig; the stroud is the T-3467 research's reading
where Keating's men wore leather. No paint, feathers, arms, medal or gorget, nothing ceremonial and
nothing of the Plains; the bare head carries the shared short04 cap and the hair is grown per person
by the looks layer (`clubbed_behind_1812`). The Miami of Wells's escort wear the same dress because
no source read distinguishes theirs. Held for review and flagged `touches_removal` under the
AGENTS.md standing constraint. **Colour:** every colour is chosen by eye within the colours the
sources name; the calico's print and the check are drawn as flat colours. **How to resolve:** a
dated description or picture of a Chicago engagé or of a Potawatomi or Miami man of 1810-1815, or
the judgment of people with standing to review the Native depiction, replaces these choices.

### `renderers/web/js/fabric.js` (`clothFor`)

The dress materials are named for what they are, but `clothFor` gives every `garment_*` that is not
wool/coat/linen/shirt a cotton twill. Suggested:

```js
if (/deerskin|buckskin|leather/.test(name)) return null;           // hide: no weave
if (/wool|stroud|broadcloth|coat|waistcoat|vest|jacket/.test(name)) return CLOTHS.wool;
```

That gives `garment_lower__trousers_deerskin_1812` no weave, and the stroud leggings and broadcloth
breechcloth the wool weave.

### Looks and hair

The looks layer already draws `clubbed_behind_1812` for the Native men (the coordinator's plan);
the Potawatomi asset has no headwear, so the hair layer's band cut does not apply to it. The engagé's
cap is `headwear__tuque_red_1812`: the hair layer cuts strands above its band as for any hat, so a
long or clubbed cut for an engagé shows below the cap at the back.

### Mapping for `place_town.py`

- `engage_1812` → `engage_1812`
- `potawatomi_man_1812` (men, named leaders, elders) → `potawatomi_man_1812`
- `miami_man_1812` → `potawatomi_man_1812` (no separate asset; see above)
- `potawatomi_woman_1812`, `potawatomi_child_1812`: not built by this group.

### New source records (created; public-domain books and paintings, checked absent first)

- `data/sources/keating_1824_narrative_v1.json` — Keating, *Narrative of an Expedition to the Source
  of St. Peter's River* (1824), vol. 1 (Internet Archive).
- `data/sources/lambert_1810_travels_lower_canada_v1.json` — Lambert, *Travels through Lower Canada
  and the United States* (1810), vol. 1 (Internet Archive).
- `data/sources/heriot_1807_travels_through_the_canadas.json` — Heriot, *Travels through the
  Canadas* (1807) (Internet Archive).
- `data/sources/saam_lewis_1835_cha_co_to.json` — James Otto Lewis, *Cha-Co-To*, lithograph (SAAM).
- `data/sources/saam_catlin_1830_on_saw_kie.json` — George Catlin, *On-saw-kie*, painting (SAAM).

The two pictures are judged against, never copied: no pixels or traced shapes enter the assets.

### Suggestion for the people-match reference set

If people-match is extended to 1812, the two pictures above (Lewis's Cha-co-to; Catlin's On-saw-kie)
are the nearest Potawatomi likenesses read, both later than 1812 and so references for dress and
complexion only, not for any person.
