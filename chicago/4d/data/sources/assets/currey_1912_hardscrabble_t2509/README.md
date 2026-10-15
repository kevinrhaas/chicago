# Lee's Place, the Currey 1912 plate "Hardscrabble" — reference copy for the image gate (T-2509)

The halftone plate captioned **"HARDSCRABBLE."** facing p. 74 of J. Seymour Currey, *The Story of
Old Fort Dearborn* (Chicago: A. C. McClurg & Co., 1912). The book does not name the plate's maker
or say when or from what it was drawn. Its source record is
`data/sources/currey_1912_hardscrabble_plate.json` (tier 5, a retrospective illustration); the
book's text is `data/sources/currey_1912_old_fort_dearborn.json`.

The copy here is Project Gutenberg's scan (eBook #52346, `images/hardscrabble.png`, fetched
2026-10-15), brought in with its attribution as the owner directed on 2026-10-11 for the pictures
the image gate builds against ("pictures from chicagology and other sites are brought in with
their attribution, not left as links").

**Rights: public_domain.** Published in the United States in 1912. Forms, counts and proportions
are read from it; nothing is derived from the image as an asset (no texture, no traced mesh), and
the copy is unaltered.

| file | what |
|---|---|
| `currey_1912_hardscrabble.png` | the plate, 659 x 362 px greyscale, sha256 `56677f4e75126a5211409d45b5e09f0007e35f3e538a76119a8b979c69a4d747` |
| (camera) | `data/reference_views/lees_place_cabin_1812/currey_1912_hardscrabble.json`; its `solve` field says how and how far |

**The caption**, as printed beneath the plate: "There was a farmhouse standing on the west bank of
the South Branch of the Chicago river some four miles from the mouth of the river, built some time
after Fort Dearborn had been established This house and the farm adjoining it was owned by a man
named Charles Lee, who, however, did not live on the premises, but occupied a house near the fort.
The house and farm were known as Lee's Place, or Hardscrabble. It was here that two men in the
employ of Lee were killed by Indians in the April preceding the evacuation and destruction of Fort
Dearborn and the massacre of the troops."

**How it is used.** `node tools/photo_match.mjs data/reference_views/lees_place_cabin_1812/currey_1912_hardscrabble.json`
renders the committed GLB from that camera and writes it beside the plate, with the match record
the image gate reads.
