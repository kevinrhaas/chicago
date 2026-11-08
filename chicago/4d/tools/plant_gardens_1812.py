"""The 1812 scene's other gardens and fields, planted for 14 August 1812 (T-3477).

The owner, 2026-11-07: *"can you do a sweep of 1812 and 1835 and improve all of the gardens?
... all of the gardens should be unique, not necessarily wildly different crops but different
sizes and layouts that are sensible for the design of the property and the family and team at
hand, like I think Lees place had a large garden? and kinize?"*. Until now the commanding
officer's garden (tools/plant_gardens.py, T-3407) was the only planted ground in the scene.

THE READING is /mnt/project-files/garden-research/gardens-1812.md (copied into
docs/RESEARCH/gardens-1812/README.md), every claim with its quote and its source. What it
found, and what this builds from it:

  attested gardens  Kinzie's kitchen garden north of the house (Whistler 1808; Quaife p. 166;
                    J. H. Kinzie's recollection of 'the garden and the shrubbery, the fence
                    paling that surrounded it'); Ouilmette's garden behind the house, with the
                    currant bushes the sergeant hid behind on 17 August (Wau-Bun ch. XIX);
                    Lee's 'cabin and garden on the lake shore' (Andreas p. 92); the sutler's
                    garden and Coursoll's 'inclosed field' (the draught); the cabin's 'small
                    enclosure' at Lee's Place (Wau-Bun ch. XVIII).
  reconstructed     a garden at each other house that kept a household in 1812 (La Lime's,
                    Burns's, Clark's and the discharged soldier's at the forks), and the
                    factory's and the agency's paled yards as kitchen gardens. Nobody wrote
                    them down; a family on this frontier in August grew potatoes, corn,
                    beans, squash and cabbages behind the house (Kirkland 1893's 'little
                    garden-patches ... cleared around the human habitations' is the form, not
                    the evidence).
  the owner's ruling (2026-11-07): Lee's Place in August 1812 is LEFT UNPLANTED. White and
                    Cardin were killed there in April and the guard order kept everyone near
                    the fort, so the cabin's little enclosure is four months of weeds over
                    the last pot-herbs, with a volunteer pumpkin.

Each garden is sized and laid for its household: Kinzie's the largest and best kept, a full
kitchen range in two rows of beds either side of a walk from the south gate and a border of
currants and gooseberries under the north paling; Ouilmette's plainer and currant-heavy, hill
corn with beans and squash beside a creole patch; Burns's a rough soldier-settler's clearing;
Clark's small, the cattle dealer's; the soldier's smaller still; Lee's a contractor-farmer's
garden on the sand, melons and cucumbers first; the sutler's a market garden in blocks down a
middle walk; the factory's neat, the agency's crowded with the families sheltering in it;
Coursoll's a field of corn in hills with pumpkins; La Lime's sown in May and neglected since
its head was killed in June. The crops and their stage are M'Mahon's August (the corn in
tassel, the onions' tops falling, the turnips just sown).

WHAT IS NOT DONE HERE. The company's eight-acre cornfield at the forks is a field of some
twenty thousand corn hills and wants a cheaper way to draw a field than one plant at a time;
it is left to its own piece of work.

Every garden here is reconstructed in its layout and crops (docs/LIBERTIES.md
L-t3477-gardens-1812). Called by tools/plant_gardens.py, which writes data/gardens/1812.json
and checks it; this module also holds every bed clear of the scene's buildings, fences, worn
trails, worn yards, planted stems and yard goods, and on dry ground (`clearance`).
"""
from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

TICKET = "T-3477"
LIBERTY = "L-t3477-gardens-1812"
FT = 0.3048
#: how far along the cabin's front the enclosure's centre stands from the landing path
LEES_SIDE_M = -9.2
DATA = ROOT / "data"

# The crops this file adds to the officer's garden's table, and its new plans.
NEW_CROPS = {
    "turnip": ("turnips, just sown", "reconstructed",
               "M'Mahon's August: 'The first week in this month, is a very principal time for sowing your general "
               "crops of turnep'; by the middle of the month the drills show their seed leaves."),
    "weed": ("weeds: ragweed, lamb's-quarters, smartweed", "reconstructed",
             "An annual weed stand on ground tilled last year and not this: waist to head high by August."),
    # T-3498: the forks field's corn, drawn four hills to a stand
    "corn_stand": ("Indian corn in the field, in hills, with pumpkins", "attested",
                   "The draught letters the field 'Company Garden & public Cornfield'; corn in hills three and a half "
                   "feet apart, tasselled and in the ear by mid-August, pumpkins running between (Brackenridge's creole "
                   "field). The spacing, stage and pumpkins are reconstructed; four hills are drawn as one stand."),
}

SRC_MMAHON = ["mmahon_1857_american_gardeners_calendar"]


def rect(u0, v0, u1, v1):
    return [[round(u0, 2), round(v0, 2)], [round(u1, 2), round(v0, 2)], [round(u1, 2), round(v1, 2)],
            [round(u0, 2), round(v1, 2)]]


def frame_at(e0, n0, rot_deg=0.0):
    """A plan frame whose (0, 0) is (e0, n0) local ENU, turned clockwise by rot_deg."""
    r = math.radians(rot_deg)
    return {"origin": [round(e0, 3), round(n0, 3)],
            "u": [round(math.cos(r), 6), round(-math.sin(r), 6)],
            "v": [round(math.sin(r), 6), round(math.cos(r), 6)]}


def to_enu(fr, u, v):
    (oe, on), (ue, un), (ve, vn) = fr["origin"], fr["u"], fr["v"]
    return oe + ue * u + ve * v, on + un * u + vn * v


def to_plan(fr, e, n):
    (oe, on), (ue, un), (ve, vn) = fr["origin"], fr["u"], fr["v"]
    de, dn = e - oe, n - on
    return de * ue + dn * un, de * ve + dn * vn


# ------------------------------------------------------------------------------------ the gardens
#: Each garden: id, the structure it belongs to, its name and place words, its frame (an ENU
#: corner and a clockwise turn, or a structure record's own frame), its size, whether its own
#: paling lays the walks (ground) or it is beds on open ground ('beds', clearing the sward), and
#: its beds as (id, plan, u0, v0, u1, v1, words).
GARDENS = [
    {
        "id": "kinzie_garden_1812", "structure_id": "kinzie_garden_1812", "record": "kinzie_garden_1812",
        "name": "Kinzie's kitchen garden",
        "where": "North of the Kinzie house, inside its paling, the gate on the south toward the yard",
        "household": "John and Eleanor Kinzie, their four children and the household's servants and engagés",
        "ground": None, "walk_grade": "reconstructed", "paling_inset_m": 0.2,
        "grade": "attested",
        "why": ("The largest and best-kept garden on the bank: a full kitchen range in two rows of beds either side "
                "of a walk from the gate, and the 'shrubbery' J. H. Kinzie remembered as a border of currants and "
                "gooseberries under the north paling."),
        "beds": [
            ("border_w", "bushes", 0.5, 13.4, 22.0, 15.1, "currants and gooseberries under the north paling, west of the walk"),
            ("border_e", "bushes", 24.0, 13.4, 45.5, 15.1, "currants and gooseberries under the north paling, east of the walk"),
            ("s1", "roots", 0.6, 0.6, 10.6, 6.4, "onions, beets, carrots and parsnips in drills"),
            ("s2", "cabbage", 11.2, 0.6, 20.2, 6.4, "cabbages heading, and the late savoys newly set"),
            ("herb_w", "herb", 20.8, 0.6, 22.0, 3.2, "sage, thyme and parsley by the gate"),
            ("herb_e", "herb", 24.0, 0.6, 25.2, 3.2, "sage, thyme and parsley by the gate"),
            ("s3", "potato", 25.8, 0.6, 35.2, 6.4, "potatoes earthed up, their tops yellowing"),
            ("s4", "melons", 35.8, 0.6, 45.4, 6.4, "musk-melons and cucumbers fruiting"),
            ("n1", "corn_beans", 0.6, 7.0, 10.6, 12.7, "garden Indian corn with running beans on poles"),
            ("n2", "turnip", 11.2, 7.0, 22.0, 12.7, "a turnip bed sown this week, drills of seed leaves"),
            ("n3", "onion_salad", 24.0, 7.0, 34.4, 12.7, "onions and lettuce"),
            ("n4", "squash", 35.0, 7.0, 45.4, 12.7, "squashes and pumpkins"),
        ],
    },
    {
        "id": "ouilmette_garden_1812", "structure_id": "ouilmette_house_1812", "corner": (1108.0, 351.5),
        "size": (13.5, 9.5), "name": "Ouilmette's garden",
        "where": "Behind Antoine Ouilmette's house, west of Kinzie's horse mill",
        "household": "Antoine Ouilmette, his Potawatomi wife Archange, their children and Mrs. Bisson",
        "ground": "beds", "grade": "attested",
        "why": ("Smaller and plainer than Kinzie's, and currant-heavy: the bushes the sergeant hid behind on 17 "
                "August, two rows of them already standing (data/flora/plantings/ouilmette_garden_1812.json) and "
                "more planted round them, then hill corn with beans and squash among it, potatoes and onions."),
        "beds": [
            ("currants", "currant_rows", 6.6, 0.6, 13.2, 6.3, "the currant bushes, dense enough to hide a man"),
            ("corn", "corn_beans_squash", 0.5, 3.4, 6.0, 9.0, "corn in hills, beans climbing the stalks and squash between"),
            ("onions", "roots_onion", 0.5, 0.6, 6.0, 2.8, "onions in drills, their tops falling"),
            ("potatoes", "potato", 6.6, 6.9, 13.0, 9.0, "a block of potatoes"),
        ],
        "stems": [[8.9, 1.8], [10.7, 1.8], [12.5, 1.8], [8.9, 3.6], [10.7, 3.6], [12.5, 3.6]],
        "new_bushes": [[8.9, 5.4], [10.7, 5.4], [12.5, 5.4], [7.1, 1.8], [7.1, 3.6], [7.1, 5.4], [11.6, 0.8]],
    },
    {
        "id": "lalime_garden_1812", "structure_id": "lalime_house_1812", "corner": (1095.0, 353.0),
        "size": (11.0, 7.5), "name": "La Lime's dooryard patch",
        "where": "Behind the interpreter Jean La Lime's house",
        "household": "Jean La Lime's household; La Lime himself killed by Kinzie in June 1812",
        "ground": "beds", "grade": "reconstructed",
        "why": ("Planted in May and neglected since June, when its head was killed: corn hills going to weeds, the "
                "squash vines sprawling, lamb's-quarters and purslane between the hills. Who lived in the house "
                "after him is not known."),
        "beds": [
            ("patch", "neglected", 0.4, 0.4, 10.6, 7.1, "corn hills gone to weeds, squash sprawling"),
        ],
    },
    {
        "id": "burns_garden_1812", "structure_id": "burns_house_1812", "corner": (788.0, 115.5),
        "size": (15.0, 12.0), "name": "The Burns family's garden",
        "where": "A clearing behind the Burns cabin on the north bank, above the bank path",
        "household": "Burns, a discharged soldier, his wife and their children, the youngest born in April",
        "ground": "beds", "grade": "reconstructed",
        "why": ("A soldier-settler's subsistence patch cut out of the woods, rougher than any garden on the bank: "
                "potatoes, corn in hills, pumpkins, cabbages and beans, in uneven beds."),
        "beds": [
            ("potatoes", "potato", 0.5, 0.5, 7.0, 5.4, "potatoes"),
            ("corn", "field_corn", 0.6, 6.1, 7.4, 11.5, "corn in hills, a pumpkin among it"),
            ("cabbages", "cabbage", 7.8, 0.6, 14.4, 3.5, "cabbages"),
            ("beans", "pole_bean", 7.6, 4.1, 14.5, 7.2, "beans on poles"),
            ("pumpkins", "squash", 7.9, 7.9, 14.4, 11.6, "pumpkins"),
        ],
    },
    {
        "id": "clark_garden_1812", "structure_id": "forks_house_clark_1812", "corner": (118.0, -82.0),
        "size": (11.0, 10.0), "name": "Clark's garden",
        "where": "North of Clark's house at the forks, west of the bank path",
        "household": "Clark, a cattle dealer",
        "ground": "beds", "grade": "reconstructed",
        "why": "A small garden: potatoes, cabbages and pumpkins. A cattle dealer's living was his cattle, not his garden.",
        "beds": [
            ("potatoes", "potato", 0.5, 0.5, 10.5, 4.2, "potatoes"),
            ("cabbages", "cabbage", 0.5, 4.8, 5.2, 9.5, "cabbages"),
            ("pumpkins", "squash", 5.8, 4.8, 10.5, 9.5, "pumpkins"),
        ],
    },
    {
        "id": "soldier_garden_1812", "structure_id": "forks_house_soldier_1812", "corner": (46.0, 51.0),
        "size": (9.0, 8.0), "name": "The discharged soldier's garden",
        "where": "East of the discharged soldier's house at the forks",
        "household": "A discharged soldier, unnamed",
        "ground": "beds", "grade": "reconstructed",
        "why": "Like the Burns patch but smaller: potatoes, a few corn hills, cabbages and beans.",
        "beds": [
            ("potatoes", "potato", 0.5, 0.5, 4.3, 7.5, "potatoes"),
            ("corn", "field_corn", 4.9, 3.8, 8.5, 7.5, "a few corn hills"),
            ("cabbages", "cabbage", 4.9, 0.5, 8.5, 1.8, "cabbages"),
            ("beans", "pole_bean", 4.9, 2.2, 8.5, 3.3, "beans on poles"),
        ],
    },
    {
        "id": "lee_garden_1812", "structure_id": "lee_house_1812", "corner": (1103.0, -446.0),
        "size": (20.0, 16.0), "name": "Lee's garden on the lake shore",
        "where": "Landward of Charles Lee's house on the lake shore south of the fort",
        "household": "Charles Lee, the farmer who supplied the garrison, his wife and their children",
        "ground": "beds", "grade": "attested",
        "why": ("Andreas names 'the cabin and garden on the lake shore near the fort'. A contractor-farmer's town "
                "garden on sand: the melons, water-melons, cucumbers and squash in hills that warm sand favours, "
                "and potatoes, beans, cabbages and onions."),
        "beds": [
            ("melons", "melons", 0.6, 8.6, 12.4, 15.4, "musk-melons and water-melons in hills on the sand"),
            ("vines", "vines", 13.0, 8.6, 19.4, 15.4, "cucumbers and squash"),
            ("potatoes", "potato", 0.6, 0.6, 8.4, 7.9, "potatoes"),
            ("beans", "pole_bean", 9.0, 0.6, 13.6, 7.9, "beans on poles"),
            ("cabbages", "cabbage", 14.2, 3.8, 19.4, 7.9, "cabbages"),
            ("onions", "roots_onion", 14.2, 0.6, 19.4, 3.2, "onions"),
        ],
    },
    {
        "id": "factory_garden_1812", "structure_id": "first_fort_outer_factory", "corner": (1075.0, 211.0),
        "size": (15.0, 13.0), "name": "The factory's kitchen garden",
        "where": "In the paled yard east of the government factory",
        "household": "Matthew Irwin, the factor, and his household",
        "ground": "beds", "grade": "reconstructed",
        "why": ("The draught draws a yard lettered 'Paling' east of the factory and says nothing of its use. A "
                "government official's household garden, kept neat: cabbages, onions, beans, salad, herbs and a "
                "melon bed."),
        "beds": [
            ("cabbages", "cabbage", 0.6, 0.6, 7.0, 5.8, "cabbages"),
            ("onions", "onion_salad", 7.6, 0.6, 14.4, 5.8, "onions and lettuce"),
            ("beans", "pole_bean", 0.6, 6.6, 5.4, 12.4, "beans on poles"),
            ("herbs", "herb", 6.0, 6.6, 8.2, 12.4, "pot herbs"),
            ("melons", "melons", 8.8, 6.6, 14.4, 12.4, "musk-melons"),
        ],
    },
    {
        "id": "agency_garden_1812", "structure_id": "first_fort_outer_agents_house", "corner": (1075.0, 159.5),
        "size": (15.0, 9.5), "name": "The agency yard's vegetables",
        "where": "In the paled yard east of the Indian agent's house",
        "household": "The families who took shelter in the Agency House after the April killings",
        "ground": "beds", "grade": "reconstructed",
        "why": ("After April 'the inhabitants outside the fort ... intrenched themselves in the Agency House' "
                "(Wau-Bun ch. XVIII): its yard crowded with potatoes and cabbages, made in a hurry."),
        "beds": [
            ("potatoes", "potato", 0.5, 0.5, 9.0, 9.0, "potatoes, planted close"),
            ("cabbages", "cabbage", 9.6, 0.5, 14.5, 9.0, "cabbages"),
        ],
    },
    {
        "id": "sutlers_garden_1812", "structure_id": "first_fort_outer_sutlers_garden",
        "record": "first_fort_outer_sutlers_garden",
        "name": "The sutler's garden",
        "where": "Between the fort and the river mouth, inside its paling",
        "household": "The post's sutler, who sold to the soldiers",
        "ground": None, "walk_grade": "reconstructed", "paling_inset_m": 0.2, "grade": "attested",
        "why": ("Lettered 'a Sutlers Garden' on the draught. A market garden for the garrison: a walk down the middle "
                "and four blocks of beds a side, plainer and more of a production garden than the officers', with "
                "no small fruit. Its north end is left to the way worn in from the fort road to the house the "
                "draught draws inside it."),
        "beds": [
            ("w1", "cabbage", 0.5, 0.6, 6.6, 6.5, "cabbages and savoys"),
            ("w2", "roots_onion", 0.5, 7.1, 6.6, 13.0, "onions"),
            ("w3", "potato", 0.5, 13.6, 6.6, 19.5, "potatoes"),
            ("w4", "potato", 0.5, 20.1, 6.6, 26.0, "potatoes"),
            ("e1", "vines_cucumber", 8.1, 0.6, 14.2, 6.5, "cucumbers"),
            ("e2", "melons", 8.1, 7.1, 14.2, 13.0, "musk-melons"),
            ("e3", "pole_bean", 8.1, 13.6, 14.2, 19.5, "beans on poles"),
            ("e4", "turnip", 8.1, 20.1, 14.2, 26.0, "turnips sown this week"),
        ],
    },
    {
        "id": "coursoll_field_1812", "structure_id": "coursoll_field_1812", "record": "coursoll_field_1812",
        "name": "Coursoll's field",
        "where": "North of the river, inside its worm fence, by Le Mai's house",
        "household": "Le Mai's household; the field is 'Coursoll's' on the draught",
        "ground": "beds", "grade": "attested",
        "why": ("Quaife's 'house and inclosed field north of the river, belonging to Mr. Coursoll'. No crop is "
                "named: Indian corn in hills three and a half feet apart, a pumpkin in every third hill, the creole "
                "field's 'Corn, pumpkins, and spring wheat' (Brackenridge) less the wheat."),
        "beds": [
            ("field", "hill_field", 1.6, 1.6, 29.4, 16.6, "Indian corn in hills, with pumpkins"),
        ],
    },
    {
        # T-3498 (the owner, 2026-11-08: "Sure do it"): the eight acres at the forks
        "id": "forks_company_cornfield_1812", "structure_id": "forks_company_cornfield_1812",
        "record": "forks_company_cornfield_1812", "ticket": "T-3498",
        "name": "The company garden and public cornfield",
        "where": "At the forks, on the south side of the main river, inside its worm fence",
        "household": "The garrison: Heald's company, worked by its fatigue parties",
        "ground": "beds", "grade": "attested",
        # a stand of four hills grown whole is a garden plant's cost: grow them only round the eye
        "rings_m": {"near": 6, "mid": 15}, "ground_cell_m": 2.0,
        "why": ("The draught's 'Company Garden & public Cornfield Eight acres'; Quaife p. 166, 'a small field of eight or "
                "nine acres had been reduced to cultivation and made to serve as the company gardens and public "
                "cornfield'. About seven acres of Indian corn in hills, tasselled and in the ear in mid-August, pumpkins "
                "between; the company garden an acre's corner nearest the bank path to the fort, in mess strips: "
                "potatoes, cabbages, beans, onions and a strip of turnips just sown. A path is trodden through the corn "
                "to where the fatigue party is at work."),
        "beds": [
            ("corn_west", "stand_field", 1.6, 1.6, 96.9, 215.2, "Indian corn in hills, with pumpkins"),
            ("corn_east", "stand_field", 98.9, 1.6, 148.3, 162.8, "Indian corn in hills, with pumpkins"),
            ("mess_potatoes_1", "potato", 100.9, 210.0, 148.3, 215.2, "the company's potatoes"),
            ("mess_potatoes_2", "potato", 100.9, 203.6, 148.3, 208.8, "the company's potatoes"),
            ("mess_cabbages", "cabbage", 100.9, 197.2, 148.3, 202.4, "the company's cabbages"),
            ("mess_beans", "pole_bean", 100.9, 190.8, 148.3, 196.0, "the company's beans on poles"),
            ("mess_onions", "roots_onion", 100.9, 184.4, 148.3, 189.6, "the company's onions"),
            ("mess_turnips", "turnip", 100.9, 178.0, 148.3, 183.2, "turnips, sown this week"),
            ("mess_potatoes_3", "potato", 100.9, 171.6, 148.3, 176.8, "the company's potatoes"),
            ("mess_cabbages_2", "cabbage", 100.9, 165.2, 148.3, 170.4, "the company's cabbages"),
        ],
    },
    {
        "id": "lees_place_garden_1812", "structure_id": "lees_place_cabin_1812", "lees_place": True,
        "size": (14.0, 10.0), "name": "The little enclosure at Lee's Place",
        "where": "On the river side of the cabin at Lee's Place, on the South Branch",
        "household": "Nobody since April: White and Cardin killed there, the soldier and the boy fled",
        "ground": False, "grade": "attested",
        "why": ("The 'small enclosure' the corporal jumped over in April (Wau-Bun ch. XVIII). The owner's ruling "
                "(2026-11-07): the place is left unplanted in 1812. Four months untended, it is a stand of weeds "
                "over the last pot-herbs, with a volunteer pumpkin."),
        "beds": [
            ("enclosure", "weeds", 0.4, 0.4, 13.6, 9.6, "weeds over last year's beds, a few pot-herbs, a volunteer pumpkin"),
        ],
    },
]


def _seg_dist(u, v, a, b):
    """Plan distance from (u, v) to the segment a-b."""
    (au, av), (bu, bv) = a, b
    du, dv = bu - au, bv - av
    t = max(0.0, min(1.0, ((u - au) * du + (v - av) * dv) / (du * du + dv * dv or 1.0)))
    return math.hypot(u - au - du * t, v - av - dv * t)


def keep_clear(fr, W, D, pad=1.5):
    """T-3498: where the scene's own people stand or walk inside a garden's plan, as (a, b, r)
    segments in plan metres: each person's placement and every leg of their route. A field's corn
    is not grown on them (a soldier at work hoeing stands between hills, not inside a stand)."""
    out = []
    inside = lambda u, v: -2 <= u <= W + 2 and -2 <= v <= D + 2
    for f in sorted((DATA / "humans" / "instances" / "1812").glob("*.json")):
        h = json.loads(f.read_text())
        pl = h.get("placement") or {}
        if pl.get("local_e") is None:
            continue
        pts = [to_plan(fr, pl["local_e"], pl["local_n"])]
        for st in ((h.get("behaviour") or {}).get("route") or []):
            pts.append(to_plan(fr, st["local_e"], st["local_n"]))
        if not any(inside(u, v) for u, v in pts):
            continue
        out.append((pts[0], pts[0], pad))
        # the walk out to the route, each leg of it, and back round to its start
        legs = list(zip(pts, pts[1:])) + ([(pts[-1], pts[1])] if len(pts) > 2 else [])
        out += [(a, b, pad * 0.9) for a, b in legs]
    return out


def frame_of(g):
    """The garden's frame and size."""
    if g.get("record"):
        import plant_gardens as P
        rec = json.loads((DATA / "structures" / f"{g['record']}.json").read_text())
        fr = P.garden_frame(rec)
        return {"origin": fr["origin"], "u": fr["u"], "v": fr["v"]}, tuple(fr["size"])
    if g.get("lees_place"):
        # the cabin's own frame: u along its front, v out of its front toward the river
        sc = json.loads((DATA / "sidecars" / "1812" / "lees_place_cabin_1812.json").read_text())
        pl = sc["placement"]
        rot = float(pl.get("rotation_deg", 0.0))
        W, D = g["size"]
        r = math.radians(rot)
        ue, un = math.cos(r), -math.sin(r)
        ve, vn = math.sin(r), math.cos(r)
        # the reading puts it on the river side of the cabin, 1.5 to 11.5 m out of its front wall
        # (centre near E -1648.9, N -4231.4); the path from the landing comes straight up to the
        # door there, so the enclosure stands beside the path, a metre clear of it, on the side
        # away from the cart standing in the cabin's yard
        ce, cn = -1648.9 + ue * LEES_SIDE_M, -4231.4 + un * LEES_SIDE_M
        # the cabin's +v runs out of its front toward the river and the landing
        return ({"origin": [round(ce - ue * W / 2 - ve * D / 2, 3), round(cn - un * W / 2 - vn * D / 2, 3)],
                 "u": [round(ue, 6), round(un, 6)], "v": [round(ve, 6), round(vn, 6)]}, (W, D))
    e0, n0 = g["corner"]
    return frame_at(e0, n0), tuple(g["size"])


# ------------------------------------------------------------------------------------ planting
def plant_bed(plan, poly, rng, grid, inside, edge_dist, g=None):
    """[(kind, u, v, yaw_local_deg, scale)] for one bed by its plan; the 1835 town's plans where
    the bed is one of those, else this scene's."""
    import plant_dooryards_1835 as T
    shared = {"potato", "cabbage", "corn", "field_corn", "pole_bean", "vines", "roots", "onion_salad", "herb",
              "bushes", "raspberry", "strawberry"}
    if plan in shared:
        return T.plant_bed(plan, poly, rng, grid, inside, edge_dist)
    out = []

    def put(kind, u, v, scale=(0.88, 1.12), yaw=None, skip=0.0):
        if rng.random() < skip:
            return
        out.append((kind, u, v, rng.uniform(0, 360) if yaw is None else yaw, rng.uniform(*scale)))

    u0, v0, u1, v1 = T._bbox(poly)
    along_u = (u1 - u0) >= (v1 - v0)

    def drills(kind, pitch, step=1.0, margin=0.4, scale=(0.92, 1.08)):
        if along_u:
            v = v1 - margin
            while v > v0 + margin * 0.9:
                u = u0 + 0.6
                while u < u1 - 0.5:
                    if inside(poly, u, v) and edge_dist(poly, u, v) > 0.3:
                        put(kind, u, v, scale, yaw=180.0 * rng.randrange(2) + rng.uniform(-3, 3))
                    u += step
                v -= pitch
        else:
            u = u0 + margin
            while u < u1 - margin * 0.9:
                v = v0 + 0.6
                while v < v1 - 0.5:
                    if inside(poly, u, v) and edge_dist(poly, u, v) > 0.3:
                        put(kind, u, v, scale, yaw=90.0 + 180.0 * rng.randrange(2) + rng.uniform(-3, 3))
                    v += step
                u += pitch

    if plan == "melons":
        # musk-melons in hills six feet every way (M'Mahon), a water-melon hill in about one in four
        # where the bed is big enough to take their nine feet, else cucumbers
        big = (u1 - u0) > 8 and (v1 - v0) > 5
        for u, v, j in grid(poly, 6 * FT, 6 * FT, 0.8, rng, jitter=0.12, stagger=True):
            k = "watermelon" if big and rng.random() < 0.25 else ("muskmelon" if rng.random() < 0.8 else "cucumber")
            put(k, u, v, (1.1, 1.3) if k == "watermelon" else (0.9, 1.1))
    elif plan == "vines_cucumber":
        for u, v, _ in grid(poly, 4 * FT, 4 * FT, 0.5, rng, jitter=0.1, stagger=True):
            put("cucumber", u, v, (0.9, 1.1))
    elif plan == "squash":
        # pumpkins and squashes in hills ten feet apart (M'Mahon), a little closer in a kitchen bed
        for u, v, _ in grid(poly, 8 * FT, 8 * FT, 1.1, rng, jitter=0.18, stagger=True):
            put("squash", u, v, (0.95, 1.2))
    elif plan == "turnip":
        drills("turnip", 0.45, step=1.0, scale=(0.85, 1.1))
    elif plan == "roots_onion":
        drills("onion", 0.42)
    elif plan == "corn_beans":
        # garden Indian corn in drills six feet apart, hills two and a half feet asunder (M'Mahon),
        # and between the corn drills a drill of running beans on poles
        for u, v, j in grid(poly, 2.5 * FT, 3 * FT, 0.5, rng, jitter=0.05):
            put("corn" if j % 2 == 0 else "pole_bean", u, v, (0.9, 1.08))
    elif plan == "corn_beans_squash":
        # hill corn the way it was grown beside the lodges: hills three and a half feet each way, a
        # bean pole in one hill in three, a squash among them in one in seven
        for u, v, _ in grid(poly, 3.5 * FT, 3.5 * FT, 0.5, rng, jitter=0.12):
            x = rng.random()
            put("squash" if x < 0.14 else "pole_bean" if x < 0.45 else "corn", u, v, (0.86, 1.06))
    elif plan == "stand_field":
        # T-3498: a field too big to grow hill by hill: corn in hills three and a half feet each way,
        # laid four hills to a stand (two by two); none on a path the garrison's people walk or a place
        # they stand at work (keep_clear, from their own records)
        S = 3.5 * FT
        clear = (g or {}).get("_keep_clear", [])
        u = u0 + 0.6 + S
        while u <= u1 - 0.6 - S + 1e-9:
            v = v0 + 0.6 + S
            while v <= v1 - 0.6 - S + 1e-9:
                pu, pv = u + rng.uniform(-0.08, 0.08), v + rng.uniform(-0.08, 0.08)
                if all(_seg_dist(pu, pv, a, b) > r for a, b, r in clear):
                    put("corn_stand", pu, pv, (0.94, 1.06), yaw=rng.choice((0, 90, 180, 270)) + rng.uniform(-3, 3))
                v += 2 * S
            u += 2 * S
    elif plan == "hill_field":
        # a field's corn in hills three and a half feet each way, a pumpkin vine in every third hill's
        # gap; the hills lean and vary more than a garden's
        for u, v, j in grid(poly, 3.5 * FT, 3.5 * FT, 0.6, rng, jitter=0.12):
            put("corn", u, v, (0.82, 1.06))
            if (j % 3 == 1) and rng.random() < 0.55:
                put("squash", u + 1.75 * FT, v + rng.uniform(-0.2, 0.2), (0.9, 1.15))
    elif plan == "currant_rows":
        # the bushes the flora layer already stands here are kept; the garden adds the rows round them
        for u, v in g["new_bushes"]:
            put("currant", u + rng.uniform(-0.12, 0.12), v + rng.uniform(-0.12, 0.12), (0.85, 1.1))
        for u, v in ((7.1, 0.8), (12.5, 0.8)):
            put("gooseberry", u + rng.uniform(-0.1, 0.1), v, (0.8, 1.0))
    elif plan == "neglected":
        # corn hills three and a half feet apart, nearly a third of them choked out by weeds, the rest
        # stunted for want of hoeing; weeds thick in the gaps and a squash vine in about one hill in twelve
        for u, v, _ in grid(poly, 3.5 * FT, 3.5 * FT, 0.5, rng, jitter=0.15):
            x = rng.random()
            if x < 0.3:
                put("weed", u, v, (0.75, 1.1))
            elif x < 0.38:
                put("squash", u, v, (0.85, 1.05))
            else:
                put("corn", u, v, (0.62, 0.85))
            for _ in range(2):
                if rng.random() < 0.6:
                    put("weed", u + 1.75 * FT * rng.choice((-1, 1)) + rng.uniform(-0.2, 0.2),
                        v + rng.uniform(-0.45, 0.45), (0.55, 0.95))
    elif plan == "weeds":
        # a stand of annual weeds over the old beds, waist to head high, thick in patches and thin in
        # others; a few pot-herbs come up through it near the edges and one volunteer pumpkin
        for u, v, _ in grid(poly, 0.75, 0.75, 0.3, rng, jitter=0.36):
            patch = 0.5 + 0.5 * math.sin(u * 0.9 + rng.random() * 0.4) * math.cos(v * 1.1)
            if edge_dist(poly, u, v) < 1.2 and rng.random() < 0.1:
                put("herb", u, v, (0.9, 1.25))
            else:
                put("weed", u, v, (0.6 + 0.5 * patch, 0.9 + 0.5 * patch), skip=0.35 - 0.3 * patch)
        cu, cv = u0 + (u1 - u0) * rng.uniform(0.3, 0.7), v0 + (v1 - v0) * rng.uniform(0.3, 0.7)
        put("squash", cu, cv, (1.0, 1.2))
    else:
        raise ValueError(f"no plan {plan!r}")
    return out


def build(grid, inside, edge_dist) -> tuple[list[dict], dict]:
    gardens = []
    for g in GARDENS:
        fr, (W, D) = frame_of(g)
        theta = math.degrees(math.atan2(fr["u"][1], fr["u"][0]))
        beds, plants = [], {}
        stems = [tuple(s) for s in g.get("stems", [])]
        if g.get("rings_m"):
            g = {**g, "_keep_clear": keep_clear(fr, W, D)}
        for bid, plan, a, b, c, d, words in g["beds"]:
            poly = rect(a, b, c, d)
            beds.append({"id": bid, "name": words, "crop": plan, "plan": plan, "grade": "reconstructed",
                         "sources": SRC_MMAHON,
                         "note": f"{g['name']}: laid out for this household by tools/plant_gardens_1812.py (T-3477); "
                                 f"the bed and what grows in it are reconstructed.",
                         "poly": poly})
            rng = random.Random(f"{g.get('ticket', TICKET)}:{g['id']}:{bid}")
            for kind, u, v, yaw, scale in plant_bed(plan, poly, rng, grid, inside, edge_dist, g):
                # nothing planted on a bush the flora layer already stands (Ouilmette's currants)
                if any(math.hypot(u - su, v - sv) < 1.1 for su, sv in stems):
                    continue
                e, n = to_enu(fr, u, v)
                plants.setdefault(kind, []).append([round(e, 2), round(n, 2), round((yaw + theta) % 360, 1),
                                                    round(scale, 3), rng.randrange(3)])
        rec = {
            "id": g["id"], "structure_id": g["structure_id"], "name": g["name"], "where": g["where"],
            "household": g["household"], "grade": g["grade"], "why": g["why"],
            "frame": fr, "size_m": [round(W, 3), round(D, 3)],
        }
        if g.get("rings_m"):
            rec["rings_m"] = g["rings_m"]
            rec["ground_cell_m"] = g["ground_cell_m"]
        if g["ground"] == "beds":
            rec["ground"] = "beds"
            # open ground: the sward does not grow through the garden (gardens.js keepOut)
            rec["clears_sward"] = True
        elif g["ground"] is False:
            # untended ground: no tilled bed is drawn and the sward grows up among the weeds
            rec["ground"] = False
        else:
            rec["walk_grade"] = g["walk_grade"]
            rec["paling_inset_m"] = g["paling_inset_m"]
        rec["beds"] = [{k: bd[k] for k in ("id", "name", "crop", "grade", "sources", "note", "poly")} for bd in beds]
        for bd in rec["beds"]:
            bd["crop"] = crop_of(bd["crop"])
        rec["plants"] = {k: plants[k] for k in sorted(plants)}
        gardens.append(rec)
    crops = {k: {"name": v[0], "grade": v[1], "sources": SRC_MMAHON, "note": v[2]} for k, v in NEW_CROPS.items()}
    return gardens, crops


def crop_of(plan: str) -> str:
    """The crop a bed is named by in Inspect: its main kind."""
    return {"bushes": "currant", "roots": "onion", "onion_salad": "onion", "field_corn": "corn", "vines": "cucumber",
            "melons": "muskmelon", "stand_field": "corn", "vines_cucumber": "cucumber", "roots_onion": "onion", "corn_beans": "corn",
            "corn_beans_squash": "corn", "hill_field": "corn", "currant_rows": "currant", "neglected": "weed",
            "weeds": "weed"}.get(plan, plan)


# ------------------------------------------------------------------------------------ clearance
def clearance(doc: dict) -> list[str]:
    """Every bed of this file's gardens (not the officer's, which T-3407 holds to the draught) clear of
    the scene's other buildings, fences, worn trails, worn yards, planted stems and yard goods, inside
    its own fence where it has one, and on dry ground."""
    import generate_yard_goods_1812 as yg
    wg = yg.wg
    out = []
    items = []
    for lot in json.loads((DATA / "yard" / "1812" / "yard_goods_1812.json").read_text())["lots"]:
        for it in lot["items"]:
            items.append((lot["structure_id"], it["kind"], *it["at_local_enu_m"]))
    yard = json.loads((DATA / "yard" / "1812" / "yard_goods_1812.json").read_text())
    for w in yard.get("wagons", []):
        # a cart and its shafts: about three metres every way from where it stands
        items.append((w["belongs_to"], w["kind"], *w["at_local_enu_m"]))
    own = {g["id"]: g for g in GARDENS}
    for g in doc["gardens"]:
        spec = own.get(g["id"])
        if not spec:
            continue
        fence = spec.get("record")
        field = ("lees_place_field_fence_1812",) if spec.get("lees_place") else ()
        fr = g["frame"]
        for b in g["beds"]:
            u0 = min(p[0] for p in b["poly"]); u1 = max(p[0] for p in b["poly"])
            v0 = min(p[1] for p in b["poly"]); v1 = max(p[1] for p in b["poly"])
            pts = [to_enu(fr, u0 + (u1 - u0) * i / 6, v0 + (v1 - v0) * j / 6) for i in range(7) for j in range(7)]
            where = f"{g['id']}: bed {b['id']}"
            hs = wg.height([p[0] for p in pts], [p[1] for p in pts])
            for (e, n), h in zip(pts, hs):
                if not math.isfinite(h) or h < yg.DRY_Y:
                    out.append(f"{where} lies on wet ground at ({e:.1f}, {n:.1f})")
                    break
            for sid, ring in wg.FOOTPRINTS.items():
                if sid.startswith("potawatomi_camp"):
                    continue
                isfence = yg.ARCH.get(sid) in yg.FENCES
                for e, n in pts:
                    if sid == fence:
                        if not wg._point_in_ring(ring, e, n) or yg._ring_dist(ring, e, n) < 0.3:
                            out.append(f"{where} reaches its own fence {sid} at ({e:.1f}, {n:.1f})")
                            break
                    elif sid in field and wg._point_in_ring(ring, e, n) and yg._ring_dist(ring, e, n) >= 0.6:
                        continue    # the cabin's enclosure stands inside Lee's Place's own field
                    elif wg._point_in_ring(ring, e, n) or yg._ring_dist(ring, e, n) < (0.6 if isfence else 0.5):
                        out.append(f"{where} runs into {sid} at ({e:.1f}, {n:.1f})")
                        break
            for tid, line, half in yg.TRAILS:
                for e, n in pts:
                    if min(yg._seg_dist(e, n, *line[i], *line[i + 1]) for i in range(len(line) - 1)) < half:
                        out.append(f"{where} lies on the trail {tid} at ({e:.1f}, {n:.1f})")
                        break
            for sid, ring in yg.YARDS.items():
                for e, n in pts:
                    if wg._point_in_ring(ring, e, n):
                        out.append(f"{where} lies in the worn yard of {sid} at ({e:.1f}, {n:.1f})")
                        break
            for sid, kind, e, n in items:
                u, v = to_plan(fr, e, n)
                pad = 3.0 if kind in ("cart", "farm_box", "wagon") else 1.0
                if u0 - pad < u < u1 + pad and v0 - pad < v < v1 + pad:
                    out.append(f"{where} lies on {sid}'s {kind} at ({e:.1f}, {n:.1f})")
        stems_ok = {tuple(s) for s in spec.get("stems", [])}
        for stid, se, sn in yg.STEMS:
            su, sv = to_plan(fr, se, sn)
            if not (-0.5 < su < g["size_m"][0] + 0.5 and -0.5 < sv < g["size_m"][1] + 0.5):
                continue
            if any(math.hypot(su - a, sv - b) < 0.3 for a, b in stems_ok):
                continue
            out.append(f"{g['id']}: the planted stem {stid} stands in the garden at ({se:.1f}, {sn:.1f})")
        for kind, rows in g["plants"].items():
            for e, n, *_ in rows:
                for stid, se, sn in yg.STEMS:
                    if math.hypot(e - se, n - sn) < 0.8:
                        out.append(f"{g['id']}: a {kind} at ({e}, {n}) is planted on the stem {stid}")
    return out
