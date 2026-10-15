"""Which scene a ruling in `data/exclusions.json` is a ruling FOR (T-2489).

The file began as the 1835 town's record: every entry is a building researched
for the town by the river on 1 July 1835, and until T-2489 only the 1835 scene
listed the `exclusions` layer. The 1812 scene needs the same disclosure — the
owner asked for every known structure of 1812, and a building researched and
ruled out of that year is a finding a visitor should be able to read — but an
1812 ruling is not an exclusion from 1835 (Guarie's trading house is not
"missing" from a town it vanished from half a century before), and an 1835
ruling is not one from 1812 (the Saloon Building is not late for a town that
had not been laid out).

So an entry may carry `scenes`, the scene ids it is a ruling for. An entry
without one is the 1835 town's, which is every entry written before this, so no
existing entry changes meaning. The compiler, the watch list and the validator
all ask this one function, so the panel and the gate cannot disagree about
which list an entry is on.
"""
from __future__ import annotations

HOME_SCENE = "1835"


def scenes_of(entry: dict) -> list[str]:
    """The scene ids an exclusion or watch-list entry is a ruling for."""
    return [str(s) for s in (entry.get("scenes") or [HOME_SCENE])]


def ruled_for(entry: dict, scene_id) -> bool:
    """True when `entry` is a ruling about the scene `scene_id`."""
    return str(scene_id) in scenes_of(entry)
