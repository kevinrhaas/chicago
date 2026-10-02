# Before/after shots kept with the research they belong to

Renders of THIS project's own model, not source material: a station, a pose and a date,
captured with `tools/shoot.mjs` against the published mirror so the pair is comparable.
They carry no third-party rights and are not source records — nothing may cite one as
evidence for anything about 1835, and `data/sources/` is where evidence lives.

They are committed because a fault reported from the walk is answered in a picture, and a
picture that lives in a run's scratch directory cannot be looked at again. Kept small
(under 60 KB, 960 px) for the same reason the repository has no image dump: this is a
record of a change, not a gallery.

| file | pose | what it shows |
|---|---|---|
| `sauganash_2026-09-04_before.jpg` | Lake Street, local ENU 126 / −110, bearing SW 225° | The Sauganash before **T-0626**: one 12 × 8 m block, the log cabin at the near end lettered PHILO CARPENTER / Druggist, and a SECOND log mass standing forward of the block's street face at the far end — the duplicate the owner reported. |
| `sauganash_2026-09-04_after.jpg` | the same | After: the measured 9.92 m five-bay frontage, the second two-storey mass running back behind the east end at the block's own ridge height, the cabin alone at the near end with its board retired, and nothing log-built in front of the street face. |

Reproduce either with, from `chicago/4d/`:

    node tools/shoot.mjs ../../site/4d /walk/index.html /tmp/shots --at 126,-110,225,pose

## The walk, fort to Wolf Point (T-1970, 2026-10-02)

Eight of the 1835 scene's own anchors, walked east to west: from the fort, up South Water
Street to the wharves and Hogan's store, along Lake Street past Market and the Green Tree to
Canal, and out to the forks. Shot at 1280 × 800 on the published mirror at build `2a02483d`
plus this ticket's change, full detail, then reduced to 960 px. Every stand is one a visitor
reaches from the scene's anchor list, so a later round re-shoots the same eight frames.

| file | anchor | what it shows |
|---|---|---|
| `walk_2026-10-02_1_fort_dearborn.jpg` | `fort_dearborn`, NE 45° | The fort from the south-west across the prairie: its log mass, the palisade and the roofs behind it. |
| `walk_2026-10-02_2_south_water.jpg` | `south_water`, E 90° | South Water Street east from Wells: the row of fronts on the right, a wagon at the edge, the river on the left. |
| `walk_2026-10-02_3_newberry_dole_wharf.jpg` | `newberry_dole_wharf`, NNW 339° | From the warehouse door across the wharf deck to its mooring posts and the north bank. |
| `walk_2026-10-02_4_first_post_office.jpg` | `first_post_office`, N 0° | Hogan's store with its Brewster, Hogan & Co. board, the crates and barrels at the door. |
| `walk_2026-10-02_5_lake_market.jpg` | `lake_market`, SE 135° | Lake and Market: the white frame house with its shutters, Lake Street's fronts beyond. |
| `walk_2026-10-02_6_green_tree.jpg` | `green_tree`, NNE 33° | The Green Tree from across Lake Street, with the log house beside it. |
| `walk_2026-10-02_7_lake_at_canal.jpg` | `lake_at_canal`, E 90° | Lake Street east from Canal: the open road, roofs thinning toward the river. |
| `walk_2026-10-02_8_forks.jpg` | `forks`, ENE 75° | "The forks, from Wolf Point" — and a log cabin filling the frame. The forks are not in view from this stand; see STATUS.md § T-1970. |

    node tools/shoot.mjs ../../site/4d /walk/index.html /tmp/walk \
      --anchors fort_dearborn,south_water,newberry_dole_wharf,first_post_office,lake_market,green_tree,lake_at_canal,forks
