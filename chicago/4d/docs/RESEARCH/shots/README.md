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

    node tools/shoot.mjs ../../site/chicago/4d /walk/index.html /tmp/shots --at 126,-110,225,pose
