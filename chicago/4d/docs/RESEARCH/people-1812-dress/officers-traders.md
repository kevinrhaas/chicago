# 1812 dress: officers, traders and settlers (dress build, 2026-11-08)

Group `officers-traders`. Five role assets on the shared portable male rig, built like the 1812
private (T-3451): a generator per role, a recipe, a test, four LODs each in `assets/humans/` and
`assets/humans/web/`. Each asset is a ROLE: it names no one, it is graded reconstructed, and the
person who wears it brings their own face, height, build and colouring through the variation kit.

## The assets

| asset | role | body | wears it |
|---|---|---|---|
| `officer_first_infantry_1812` | company officer of the First Infantry, captain | prepared_adult_25 | Captain Nathan Heald |
| `officer_first_infantry_1812_lieutenant` | the same coat, epaulette on the LEFT, straight sword | prepared_adult_25 | Lieutenant Linai Helm; Ensign George Ronan |
| `surgeons_mate_first_infantry_1812` | the same coat, black velvet collar, black plume, no epaulette, no lace | prepared_adult_25 | Surgeon's mate Isaac Van Voorhis |
| `trader_1812` | prosperous trader about 1810 | prepared_adult_35 | John Kinzie; the clerk Chandonnai and the officials Irwin and Lalime (people-1812-3466); Charles Lee and Thomas Burns in their best; **Captain William Wells on the 14th** (see below) |
| `settler_1812` | settler or working man about 1810 | prepared_adult_35 | Thomas Burns, John Cooper, Charles Lee and his son, Liberty White, Louis Fettle, the American men of the militia; **Black Jim** and the second Kinzie servant (people-1812-3466 `black_servant_1812`: shirt, waistcoat, linen trousers, round black hat, no livery) |

Files: `tools/human_officer_1812.py`, `tools/human_trader_1812.py`, `tools/human_settler_1812.py`;
`data/humans/recipes/officer_1812.json` (three proof variants), `trader_1812.json`, `settler_1812.json`;
`tools/test_human_officer_1812.py` (12 tests), `test_human_trader_1812.py` (8), `test_human_settler_1812.py` (5), all
passing; `python3 tools/human_contract.py --glb` passes on all 40 GLBs. Each recipe carries
`role_1812` `{module, prepare, assembly}` (`officer_1812_v1`, `trader_1812_v1`, `settler_1812_v1`).
The anonymous person ids are `anonymous_captain_first_infantry_1812`,
`anonymous_lieutenant_first_infantry_1812`, `anonymous_surgeons_mate_first_infantry_1812` (record
`data/sources/quaife_1913.json`), `anonymous_trader_1812` (record `kinzie_waubun_1856`) and
`anonymous_settler_1812` (record `quaife_1913`); none collides with `data/sidecars/1812/people.json`.

### Choices the brief asked me to name

- **Epaulettes.** The 1814 printing's light artillery text: "a captain, one on the right shoulder ... the
  lieutenants, one on the left". So Heald's asset has it on the right, and the lieutenant variant has it on
  the left. Ensign Ronan wears the lieutenant variant (people-1812-3463: "as a lieutenant"; no ensign's rule
  was found, so that is ours). The surgeon's mate wears none (a staff appointment; ours).
- **Surgeon's mate.** The coordinator's condition was "no new geometry beyond the plume colour". It holds:
  the collar has its own material only in his variant (captain and lieutenant share the cuffs' scarlet), the
  plume is the same mesh in black, and the epaulette and collar lace are left out. He costs a third set of
  GLBs (about 7.3 MB of web LODs), so the integrator decides whether to ship it. Without it he wears the
  lieutenant asset.
- **Sword.** Captain: curved, with a stirrup hilt and brass mounts (Heald's surviving sword, Kirkland's 1893
  plate of Darius Heald holding it; people-1812-3463). Lieutenant and surgeon's mate: straight, brass-mounted
  (by analogy with the artillery). Black scabbard, brass locket and chape, on a white waist belt over the
  coat. All rigid on the pelvis.
- **No sash** (only "on a tour of duty"), **no crossbelts or cartridge box**, no lace on the breast (the one
  picture showing it, Peale's Pike of 1808, is `check_required` and so stays out of the asset; collar loops
  rest on the 1813 change taking lace away).
- **Wells.** people-1812-3463 reads his dress on the 14th as frontier dress: a long queue tied with black
  ribbon, a round felt hat, a calico or linen shirt, a hunting frock or short blue coat, breechcloth,
  leggings, moccasins. Neither of my assets is that. Of the two, **`trader_1812` is the better stand-in for
  the 14th** (round felt hat, coat, a civilian of standing). It is wrong below the waist (breeches and top
  boots, where he wore leggings and moccasins) and has no queue (the hair is the shared short04 cap).
  A truer figure for him is the engagé group's deer-skin or calico-and-leggings dress if it fits a man of
  his build, or a later `frontier_agent_1812` role. I did not build that role: it was not asked of this
  group, and it would be a fourth outfit. His dress of the 15th ("painted black & dressed like an Indian")
  is the battle jaunt's and is not drawn by any asset here.
- **The trader's hat.** dress.json's evidence says "tall round hat with a moderate brim" (Krimmel's man of
  1811-13 wears a tall hat), so it is not the low-crowned felt the brief suggested. To keep it from reading
  as the 1835 top hat, its crown is lower (12.5 cm against 16) and tapers to the top (flare 0.85, where the
  1835 hat flares out), with a wider brim curled at the sides.
- **Trader colours.** Dark green coat (Peale's Robinson 1811 and Krimmel's man both wear green, and it sets
  him apart from the officers' and the 1835 merchant's blue), yellow waistcoat (Robinson; the Pixler father),
  buff breeches and top boots with tan tops (Krimmel). people-1812-3466's working variants (Kinzie at the
  bench in a round jacket, Chandonnai's calico shirt and sash) are not built: one asset, as asked.
- **Settler.** Built on the 1835 labourer, made lighter: no braces (one draw fewer). It has
  an unbleached tow shirt, a blue neckerchief, a brown waistcoat closed to the chest, loose natural linen
  trousers, dark shoes, and a black round hat with a soft brim (the sawyers' "black round hats"; the
  labourer's hat re-measured). The militia's musket and belts are carried things, not part of the dress.
- **Bodies.** The officer is on the 25 body: three of its four wearers were in their early twenties (Heald
  was 37). The trader and the settler are on the 35 body (Kinzie 49, Wells 42, Burns an old soldier).

## Budget (web LODs, meshopt; the private for comparison)

| asset | lod0 | lod1 | lod2 | lod3 | materials (draws) |
|---|---|---|---|---|---|
| private_first_infantry_1812 | 4.590 MB / 44,914 | 1.673 MB / 27,310 | 0.680 MB / 13,442 | 0.342 MB / 6,489 | 15 |
| officer_first_infantry_1812 | 4.593 MB / 44,879 | 1.683 MB / 27,287 | 0.697 MB / 13,425 | 0.366 MB / 6,479 | 15 |
| officer_first_infantry_1812_lieutenant | 4.593 MB / 44,809 | 1.683 MB / 27,246 | 0.698 MB / 13,403 | 0.367 MB / 6,475 | 15 |
| surgeons_mate_first_infantry_1812 | 4.576 MB / 44,235 | 1.668 MB / 26,902 | 0.686 MB / 13,244 | 0.357 MB / 6,408 | 16 |
| trader_1812 | 4.603 MB / 46,383 | 1.681 MB / 28,188 | 0.689 MB / 13,852 | 0.350 MB / 6,669 | 13 |
| settler_1812 | 4.516 MB / 44,317 | 1.605 MB / 26,956 | 0.628 MB / 13,281 | 0.302 MB / 6,428 | 11 |

(size / triangles). Every asset uses the shared skin atlas and flat colours (the one 256 px weave
texture the builder makes for the weave material, as the private does). The officer variants' triangle
counts are at or under the private's. Their files are 0.1 to 7 per cent larger (lod3 +24 KB), because the
small silver and brass pieces add vertices in many little primitives. The trader is about 3 per cent over
the private's triangles at every LOD (+1,469 at lod0; +180 at lod3), and +0.3 to +2.6 per cent in bytes:
the 1835 merchant's tailcoat shell, waistcoat and shirt front, which it reuses, are heavier than the
private's coat. If the 250 MB phone budget needs it, the cheapest cuts are the trader's waistcoat front
(2,032 triangles, mostly under the coat) and the shirt front (1,278). The settler is the lightest.
Masters (`assets/humans/<asset>.lod*.glb`) total 154 MB for the 20 files.

**Normal readback** (the integrator's `--normal-tolerance 5e-3`, needed on this machine): the officer's
three builds reported max_vector_delta 0.0012906586516286988 (the 25 body), and the trader and settler
0.002817095693194529 (the 35 body). The committed private fails the same 1e-3 bound here, with the shim and
with the real pinned Blender 4.5.3 binary I downloaded and sha-checked to test it (since deleted). So it is
this machine's encoding, not the shim; the shim was not changed.

## Stills

Shot with a scratch rig (`stills.mjs` + `still.html`, the lineup page's dressed lighting: ACES, sky fill,
low sun front left; skin and hair dressed as humans.js dresses them for 1812, no person variation), idle
clip at t = 1 s, eye height 1.68 m, at 3 m (front, side, back, three-quarter), at 10 m (front, side, back),
a head close-up, and a walk frame at 3 m side. In
the session scratch folder (not committed):
`sheet_captain_3m.jpg`, `sheet_captain_misc.jpg`, `sheet_lieutenant_3m.jpg`, `sheet_surgeon_3m.jpg`,
`sheet_trader_3m.jpg`, `sheet_trader_misc.jpg`, `sheet_settler_3m.jpg`, `sheet_settler_misc.jpg`,
`sheet_final_check.jpg` (the three officers side by side, heads and the settler walking); singles are
`<tag>_3m_front.jpg` and so on. The best: `captain_3m_three.jpg`, `captain_3m_side.jpg`,
`trader_3m_three.jpg`, `settler_3m_three.jpg`.

Compare with: Krimmel's Philadelphia soldiery (`met_krimmel_1813_philadelphia_soldiery`: the officer in the
long-skirted coat and chapeau worn fore-and-aft), Krimmel's chimney sweeps before Christ Church (the man in
the green tailcoat, top boots and tall hat), Peale's Robinson (green coat, yellow waistcoat, neckcloth), and
Krimmel's Black sawyers (shirt-sleeves, waistcoats, black round hats).

### Fixed after looking

These were fixed after looking at the stills. The epaulette first read as a white block down the upper arm
(silver toned to a grey, the pad narrowed, the fringe shortened). The chapeau was too tall and pointed from
the front (lowered to 16.5 cm over the seat and given a rounded arch). The turnbacks were too wide (17° at the
hem, from 26°). The pantaloons were too tight (more ease and smoothing). The trader's boot tops were cut
saw-toothed (now cut on a ring of the shaft) and his hat read as a straight 1835 top hat. His neckcloth
showed above the coat collar behind. The settler's hat read as a modern pork-pie (now the labourer's soft
brim), and his sleeves were too puffed.

### What still reads wrong

- **Costume-shop flatness.** Every cloth is one flat colour with no fold, wear or soiling. The white of
  the officer's waistcoat band, belt and pantaloons runs together at the waist into one white block.
- **The collar lace** shows at 1 m as a few ragged grey bits along the front of the collar (a strip cut
  from a coarse collar loft); at 3 m and beyond it reads as nothing. Leaving it off would lose nothing
  visible.
- **The pantaloons and breeches** still show the body's shape at the fork. That is fair for 1812 pantaloons,
  which were close, but it reads modern and athletic.
- **The chapeau** reads right from the side (the half-moon worn fore-and-aft). From the front it is a
  plain black arch: no binding, no loop showing from the front, no eagle on the cockade.
- **The sword** hangs well back at 24°. In the walk clip it is rigid on the pelvis, so it does not swing,
  and the left skirt can pass through it at full stride.
- **The trader's waistcoat** stops short of the sides above the coat's waist (hidden by the coat when
  standing; it may show a gap with arms raised). There is a small white mark at the back of his collar.
- **The settler's waistcoat** edges at the shoulder straps are stepped (the labourer's V cut on the
  body's triangles) and show at 1 m.
- **Hair.** Every figure wears the shared short04 cap. No queue for Wells. No era cut is set for 1812.

## Sources

Cited, all cleared (`public_domain`): `us_1814_military_laws_and_regulations`, `met_krimmel_1813_philadelphia_soldiery`,
`us_1812_rules_and_articles_albany`, `loc_ogden_1888_infantry_artillery_1802_1810`, `quaife_1913`,
`kirkland_1893_chicago_massacre`, `kinzie_waubun_1856`, `met_krimmel_1811_chimney_sweeps_christ_church`,
`met_krimmel_1811_black_sawyers_bank_of_pennsylvania`, `met_krimmel_1811_merrymaking_wayside_inn`,
`met_pixler_family_c1815`.
**New records written by this group** (copied from T-3461's `dress.json` `new_sources`, where the researcher
viewed each object on 2026-11-07; schema-checked; type `object` given as `photograph`, as
`met_ci_1833_tailcoat_and_trousers` is): `data/sources/met_ci_1810_1820_coutts_coat_and_breeches.json`,
`data/sources/met_ci_1815_tailcoat.json`, `data/sources/met_peale_1811_anthony_wayne_robinson.json`.
The Krimmel 1811 and Pixler records I cite were written by other builders this session; I did not change
them. Not used for any asset: `inde_peale_1808_zebulon_pike` (check_required) and
`reenact_23rd_us_1812_uniform_notes` (a lead, not verified).

## Rows for shared files (the integrator adds these; I edited none)

### `tools/check.sh` (beside the T-3451 step)

```
step "An 1812 First Infantry officer's dress (captain, lieutenant, surgeon's mate) is sourced, layered and skinned on the shared rig" \
  python3 tools/test_human_officer_1812.py
step "An 1812 trader's dress is sourced, layered and skinned on the shared rig" \
  python3 tools/test_human_trader_1812.py
step "An 1812 settler's working dress is sourced, layered and skinned on the shared rig" \
  python3 tools/test_human_settler_1812.py
```

### `data/humans/variation/axes.json` (beside `private_first_infantry_1812`)

```
    "officer_first_infantry_1812": {"base_age_years": 25, "sex": "male", "basis": "data/humans/recipes/officer_1812.json: the prepared_adult_25 engineering body, a company officer (captain), 1812 dress build."},
    "officer_first_infantry_1812_lieutenant": {"base_age_years": 25, "sex": "male", "basis": "data/humans/recipes/officer_1812.json: the prepared_adult_25 engineering body, a lieutenant or ensign, 1812 dress build."},
    "surgeons_mate_first_infantry_1812": {"base_age_years": 25, "sex": "male", "basis": "data/humans/recipes/officer_1812.json: the prepared_adult_25 engineering body, a surgeon's mate, 1812 dress build."},
    "trader_1812": {"base_age_years": 35, "sex": "male", "basis": "data/humans/recipes/trader_1812.json: the prepared_adult_35 engineering body, a prosperous trader, 1812 dress build."},
    "settler_1812": {"base_age_years": 35, "sex": "male", "basis": "data/humans/recipes/settler_1812.json: the prepared_adult_35 engineering body, a settler or working man, 1812 dress build."},
```

### `docs/LIBERTIES.md`: a supplement paragraph under `L-human-modular-dress-1789`

**The 1812 officers', trader's and settler's supplement, 2026-11-08 (the 1812 dress build):** three more
role dresses on the same component path, each anonymous, graded reconstructed and naming no one; the
person who wears one brings their own face, height and build. **Officer** (`tools/human_officer_1812.py`,
`data/humans/recipes/officer_1812.json`; assets `officer_first_infantry_1812`,
`officer_first_infantry_1812_lieutenant`, `surgeons_mate_first_infantry_1812`; the 25 body). This is a
company officer of the First Infantry in August 1812, read from the 1814 printing of the staff and
artillery officers' dress by analogy (`us_1814_military_laws_and_regulations`: chapeau, black cockade, "A
white feather to rise eight inches", white leather waist belts, epaulettes by rank, "Sashes ... to be worn
only on a tour of duty", surgeons and mates "the cape ... of black velvet; the plume black"), from the 1813
change read backwards (scarlet collar and cuffs and lace, taken away in 1813, were worn before), from
Krimmel's officer of 1811-13 (`met_krimmel_1813_philadelphia_soldiery`: long skirts, the chapeau worn
fore-and-aft, high boots) and from Heald's surviving sword (`quaife_1913` ch. XI; Kirkland 1893's plate).
Ours: the cut (the private's coat with skirts to the bend of the knee), the white turnbacks and waistcoat,
the collar's lace loops and their place, ten silver buttons, the epaulette's size, the chapeau's size and
the cockade's place, the sword's length, curve and hang, and the lieutenant's straight sword. The ensign
wears the lieutenant's left-shoulder epaulette, and the surgeon's mate none; no source was read for
either. No sash is drawn (the everyday figure), and no lace on the breast (Peale's Pike of 1808 shows it,
but its record is `check_required`). The surgeon's mate's black velvet collar is the 1814 artillery rule;
an unverified transcription gives medical staff blue collars, and he may well have worn civilian dress.
**Trader** (`tools/human_trader_1812.py`, `trader_1812`; the 35 body). This is a prosperous trader about
1810 as `docs/RESEARCH/people-1812-3461/dress.json` reads the type: a dark green tailcoat cut square at
the waist (Peale's Robinson, 1811; Krimmel's man before Christ Church, 1811-13; the cut after the Coutts
coat and a coat of about 1815, both British), a yellow waistcoat, a white neckcloth with shirt collar
points, buff breeches and top boots with tan tops, and a tall round hat kept lower and tapering. Nothing
describes Kinzie's or any Chicago man's clothes, and Kinzie has no portrait. The colours, the cut and the
hat's height are ours. It also stands for Wells on 14 August in place of his frontier dress, which no
asset draws. **Settler** (`tools/human_settler_1812.py`, `settler_1812`; the 35 body). This is plain
working dress about 1810: an unbleached shirt, a neckerchief, a brown waistcoat, loose linen trousers,
shoes and a black round hat, after Krimmel's Philadelphia sawyers and country inn and the Pixler family.
No source describes any Chicago settler's clothes in 1812, so every garment is reconstructed. It is also
worn by Black Jim, with nothing that implies a status the record does not give. **How to resolve:** a
portrait, inventory or description of any of these men's clothes replaces the role dress for that man;
an 1812 infantry officer's dress regulation (the War Department's of 1810-12, or the 30 December 1812
description, verified) replaces the analogies.

### `assets/LICENSES.md` (beside the private's rows)

| `humans/officer_first_infantry_1812.lod0.glb` | Original CC0-1.0 export of the canonical builder over the shared male base and the 1812 First Infantry officer's components (`tools/human_officer_1812.py`, a captain, 1812 dress build); reconstructed under L418 and L-human-modular-dress-1789, not a likeness. |
| `humans/web/officer_first_infantry_1812.lod0.glb` | Original CC0-1.0 export of the canonical builder over the shared male base and the 1812 First Infantry officer's components (`tools/human_officer_1812.py`, a captain, 1812 dress build); reconstructed under L418 and L-human-modular-dress-1789, not a likeness. |
| `humans/officer_first_infantry_1812.lod1.glb` | Original CC0-1.0 export of the canonical builder over the shared male base and the 1812 First Infantry officer's components (`tools/human_officer_1812.py`, a captain, 1812 dress build); reconstructed under L418 and L-human-modular-dress-1789, not a likeness. |
| `humans/web/officer_first_infantry_1812.lod1.glb` | Original CC0-1.0 export of the canonical builder over the shared male base and the 1812 First Infantry officer's components (`tools/human_officer_1812.py`, a captain, 1812 dress build); reconstructed under L418 and L-human-modular-dress-1789, not a likeness. |
| `humans/officer_first_infantry_1812.lod2.glb` | Original CC0-1.0 export of the canonical builder over the shared male base and the 1812 First Infantry officer's components (`tools/human_officer_1812.py`, a captain, 1812 dress build); reconstructed under L418 and L-human-modular-dress-1789, not a likeness. |
| `humans/web/officer_first_infantry_1812.lod2.glb` | Original CC0-1.0 export of the canonical builder over the shared male base and the 1812 First Infantry officer's components (`tools/human_officer_1812.py`, a captain, 1812 dress build); reconstructed under L418 and L-human-modular-dress-1789, not a likeness. |
| `humans/officer_first_infantry_1812.lod3.glb` | Original CC0-1.0 export of the canonical builder over the shared male base and the 1812 First Infantry officer's components (`tools/human_officer_1812.py`, a captain, 1812 dress build); reconstructed under L418 and L-human-modular-dress-1789, not a likeness. |
| `humans/web/officer_first_infantry_1812.lod3.glb` | Original CC0-1.0 export of the canonical builder over the shared male base and the 1812 First Infantry officer's components (`tools/human_officer_1812.py`, a captain, 1812 dress build); reconstructed under L418 and L-human-modular-dress-1789, not a likeness. |
| `humans/officer_first_infantry_1812_lieutenant.lod0.glb` | Original CC0-1.0 export of the canonical builder over the shared male base and the 1812 First Infantry officer's components (`tools/human_officer_1812.py`, a lieutenant, 1812 dress build); reconstructed under L418 and L-human-modular-dress-1789, not a likeness. |
| `humans/web/officer_first_infantry_1812_lieutenant.lod0.glb` | Original CC0-1.0 export of the canonical builder over the shared male base and the 1812 First Infantry officer's components (`tools/human_officer_1812.py`, a lieutenant, 1812 dress build); reconstructed under L418 and L-human-modular-dress-1789, not a likeness. |
| `humans/officer_first_infantry_1812_lieutenant.lod1.glb` | Original CC0-1.0 export of the canonical builder over the shared male base and the 1812 First Infantry officer's components (`tools/human_officer_1812.py`, a lieutenant, 1812 dress build); reconstructed under L418 and L-human-modular-dress-1789, not a likeness. |
| `humans/web/officer_first_infantry_1812_lieutenant.lod1.glb` | Original CC0-1.0 export of the canonical builder over the shared male base and the 1812 First Infantry officer's components (`tools/human_officer_1812.py`, a lieutenant, 1812 dress build); reconstructed under L418 and L-human-modular-dress-1789, not a likeness. |
| `humans/officer_first_infantry_1812_lieutenant.lod2.glb` | Original CC0-1.0 export of the canonical builder over the shared male base and the 1812 First Infantry officer's components (`tools/human_officer_1812.py`, a lieutenant, 1812 dress build); reconstructed under L418 and L-human-modular-dress-1789, not a likeness. |
| `humans/web/officer_first_infantry_1812_lieutenant.lod2.glb` | Original CC0-1.0 export of the canonical builder over the shared male base and the 1812 First Infantry officer's components (`tools/human_officer_1812.py`, a lieutenant, 1812 dress build); reconstructed under L418 and L-human-modular-dress-1789, not a likeness. |
| `humans/officer_first_infantry_1812_lieutenant.lod3.glb` | Original CC0-1.0 export of the canonical builder over the shared male base and the 1812 First Infantry officer's components (`tools/human_officer_1812.py`, a lieutenant, 1812 dress build); reconstructed under L418 and L-human-modular-dress-1789, not a likeness. |
| `humans/web/officer_first_infantry_1812_lieutenant.lod3.glb` | Original CC0-1.0 export of the canonical builder over the shared male base and the 1812 First Infantry officer's components (`tools/human_officer_1812.py`, a lieutenant, 1812 dress build); reconstructed under L418 and L-human-modular-dress-1789, not a likeness. |
| `humans/surgeons_mate_first_infantry_1812.lod0.glb` | Original CC0-1.0 export of the canonical builder over the shared male base and the 1812 First Infantry officer's components (`tools/human_officer_1812.py`, a surgeon's mate, 1812 dress build); reconstructed under L418 and L-human-modular-dress-1789, not a likeness. |
| `humans/web/surgeons_mate_first_infantry_1812.lod0.glb` | Original CC0-1.0 export of the canonical builder over the shared male base and the 1812 First Infantry officer's components (`tools/human_officer_1812.py`, a surgeon's mate, 1812 dress build); reconstructed under L418 and L-human-modular-dress-1789, not a likeness. |
| `humans/surgeons_mate_first_infantry_1812.lod1.glb` | Original CC0-1.0 export of the canonical builder over the shared male base and the 1812 First Infantry officer's components (`tools/human_officer_1812.py`, a surgeon's mate, 1812 dress build); reconstructed under L418 and L-human-modular-dress-1789, not a likeness. |
| `humans/web/surgeons_mate_first_infantry_1812.lod1.glb` | Original CC0-1.0 export of the canonical builder over the shared male base and the 1812 First Infantry officer's components (`tools/human_officer_1812.py`, a surgeon's mate, 1812 dress build); reconstructed under L418 and L-human-modular-dress-1789, not a likeness. |
| `humans/surgeons_mate_first_infantry_1812.lod2.glb` | Original CC0-1.0 export of the canonical builder over the shared male base and the 1812 First Infantry officer's components (`tools/human_officer_1812.py`, a surgeon's mate, 1812 dress build); reconstructed under L418 and L-human-modular-dress-1789, not a likeness. |
| `humans/web/surgeons_mate_first_infantry_1812.lod2.glb` | Original CC0-1.0 export of the canonical builder over the shared male base and the 1812 First Infantry officer's components (`tools/human_officer_1812.py`, a surgeon's mate, 1812 dress build); reconstructed under L418 and L-human-modular-dress-1789, not a likeness. |
| `humans/surgeons_mate_first_infantry_1812.lod3.glb` | Original CC0-1.0 export of the canonical builder over the shared male base and the 1812 First Infantry officer's components (`tools/human_officer_1812.py`, a surgeon's mate, 1812 dress build); reconstructed under L418 and L-human-modular-dress-1789, not a likeness. |
| `humans/web/surgeons_mate_first_infantry_1812.lod3.glb` | Original CC0-1.0 export of the canonical builder over the shared male base and the 1812 First Infantry officer's components (`tools/human_officer_1812.py`, a surgeon's mate, 1812 dress build); reconstructed under L418 and L-human-modular-dress-1789, not a likeness. |
| `humans/trader_1812.lod0.glb` | Original CC0-1.0 export of the canonical builder over the shared male base and the 1812 trader's components (`tools/human_trader_1812.py`, a trader, 1812 dress build); reconstructed under L418 and L-human-modular-dress-1789, not a likeness. |
| `humans/web/trader_1812.lod0.glb` | Original CC0-1.0 export of the canonical builder over the shared male base and the 1812 trader's components (`tools/human_trader_1812.py`, a trader, 1812 dress build); reconstructed under L418 and L-human-modular-dress-1789, not a likeness. |
| `humans/trader_1812.lod1.glb` | Original CC0-1.0 export of the canonical builder over the shared male base and the 1812 trader's components (`tools/human_trader_1812.py`, a trader, 1812 dress build); reconstructed under L418 and L-human-modular-dress-1789, not a likeness. |
| `humans/web/trader_1812.lod1.glb` | Original CC0-1.0 export of the canonical builder over the shared male base and the 1812 trader's components (`tools/human_trader_1812.py`, a trader, 1812 dress build); reconstructed under L418 and L-human-modular-dress-1789, not a likeness. |
| `humans/trader_1812.lod2.glb` | Original CC0-1.0 export of the canonical builder over the shared male base and the 1812 trader's components (`tools/human_trader_1812.py`, a trader, 1812 dress build); reconstructed under L418 and L-human-modular-dress-1789, not a likeness. |
| `humans/web/trader_1812.lod2.glb` | Original CC0-1.0 export of the canonical builder over the shared male base and the 1812 trader's components (`tools/human_trader_1812.py`, a trader, 1812 dress build); reconstructed under L418 and L-human-modular-dress-1789, not a likeness. |
| `humans/trader_1812.lod3.glb` | Original CC0-1.0 export of the canonical builder over the shared male base and the 1812 trader's components (`tools/human_trader_1812.py`, a trader, 1812 dress build); reconstructed under L418 and L-human-modular-dress-1789, not a likeness. |
| `humans/web/trader_1812.lod3.glb` | Original CC0-1.0 export of the canonical builder over the shared male base and the 1812 trader's components (`tools/human_trader_1812.py`, a trader, 1812 dress build); reconstructed under L418 and L-human-modular-dress-1789, not a likeness. |
| `humans/settler_1812.lod0.glb` | Original CC0-1.0 export of the canonical builder over the shared male base and the 1812 settler's components (`tools/human_settler_1812.py`, a settler, 1812 dress build); reconstructed under L418 and L-human-modular-dress-1789, not a likeness. |
| `humans/web/settler_1812.lod0.glb` | Original CC0-1.0 export of the canonical builder over the shared male base and the 1812 settler's components (`tools/human_settler_1812.py`, a settler, 1812 dress build); reconstructed under L418 and L-human-modular-dress-1789, not a likeness. |
| `humans/settler_1812.lod1.glb` | Original CC0-1.0 export of the canonical builder over the shared male base and the 1812 settler's components (`tools/human_settler_1812.py`, a settler, 1812 dress build); reconstructed under L418 and L-human-modular-dress-1789, not a likeness. |
| `humans/web/settler_1812.lod1.glb` | Original CC0-1.0 export of the canonical builder over the shared male base and the 1812 settler's components (`tools/human_settler_1812.py`, a settler, 1812 dress build); reconstructed under L418 and L-human-modular-dress-1789, not a likeness. |
| `humans/settler_1812.lod2.glb` | Original CC0-1.0 export of the canonical builder over the shared male base and the 1812 settler's components (`tools/human_settler_1812.py`, a settler, 1812 dress build); reconstructed under L418 and L-human-modular-dress-1789, not a likeness. |
| `humans/web/settler_1812.lod2.glb` | Original CC0-1.0 export of the canonical builder over the shared male base and the 1812 settler's components (`tools/human_settler_1812.py`, a settler, 1812 dress build); reconstructed under L418 and L-human-modular-dress-1789, not a likeness. |
| `humans/settler_1812.lod3.glb` | Original CC0-1.0 export of the canonical builder over the shared male base and the 1812 settler's components (`tools/human_settler_1812.py`, a settler, 1812 dress build); reconstructed under L418 and L-human-modular-dress-1789, not a likeness. |
| `humans/web/settler_1812.lod3.glb` | Original CC0-1.0 export of the canonical builder over the shared male base and the 1812 settler's components (`tools/human_settler_1812.py`, a settler, 1812 dress build); reconstructed under L418 and L-human-modular-dress-1789, not a likeness. |
