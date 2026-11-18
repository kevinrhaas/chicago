#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Where the 1812 camps' horse pickets stand, for tools/lay_town_riders.mjs (T-3560).

Kevin, 2026-11-17: "there would be horses at the native camps". The lodge_camp archetype
already lays the camps' horse lines: `picket` stakes across the open of the men's grounds, the
horse ground and the Miami escort's camp (generators/archetypes/lodge_camp.py `layout`, the
counts in each record's `horse_pickets`), with no horse at them. This prints every stake in
local ENU metres, with its camp's dates (the camp is drawn only within them, T-3527) and the
plans of the camp's dwellings, so a horse can be tied at each stake clear of the lodges.

    python3 tools/camp_pickets_1812.py      JSON on stdout
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_camp_ground_1812 as g  # noqa: E402


def main() -> None:
    out = []
    for sc in g.camps():
        rec = json.loads((g.DATA / "structures" / f"{sc['id']}.json").read_text(encoding="utf-8"))
        phase = next(p for p in rec["phases"] if p["id"] == sc.get("phase", rec["phases"][0]["id"]))
        params = g.lodge_camp_params.from_phase(phase, rec)
        place = sc.get("placement") or {}
        stakes = []
        for kind, x, y, _rot, _extra in g.lodge_camp.layout(params):
            if kind == "picket":
                e, n = g._to_enu(x, y, place)
                stakes.append([g._round(e), g._round(n)])
        if not stakes:
            continue
        out.append({"camp": sc["id"], "name": sc.get("name"), "window": g.window(sc),
                    "stakes": stakes, "dwellings": g.dwellings(sc)})
    json.dump(out, sys.stdout, indent=1)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
