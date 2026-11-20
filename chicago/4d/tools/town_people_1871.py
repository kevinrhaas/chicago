#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""T-3690: the people of the 1871 city on the Sunday afternoon before the fire.

The owner, 2026-11-19 (T-3690): "1871 people, horses and wagons on every street ... Bring 1871 up
to that standard first (the living town on the pre-fire afternoon of 8 Oct 1871)", every person "a
carded figure (reconstructed names where no source names them, as other years do)", densities
"bounded by the 1870 census (~299,000) and the 1871 directory", dressed for October 1871.

No source names who walked which street on Sunday 8 October 1871, and the context city it stands in
is anonymous (L-1871-city-baseline). So everyone here is a RECONSTRUCTED household, as the 1812
gathering's unnamed people are (L-1812-gathering-people-3500): a name common in the period among
the household's community, an age, a birthplace, a trade from the 1871 directory's vocabulary, a
day, a body and its clothes, all ours and all marked so on the card (liberty L-town-people-1871;
the clothes L-wardrobe-1871). This writes:

    data/residents_1871/households/hh_1871_*.json   the cards, one household a file
    data/humans/inside_1871.json                    everyone's day (format chicago4d_inside_only_v2)
                                                    and the place in the city their household lives
                                                    (`near`, [local_e, local_n]); the runtime puts
                                                    the door and the places outside it on the
                                                    context city's own walks and buildings
                                                    (renderers/web/js/town-1871.js)
    data/humans/variation/dress_1871_town.json      each one's clothes (human-looks.js dressCloth)
    data/humans/variation/looks_1871_town.json      each one's complexion, hair, eyes and stature

HOW MANY, AND WHERE. The 1870 census counted 298,977 people in the city (census_1870_us_vol1).
The town is drawn at the scale 1835's is drawn at (2,830 carded there), about 3,500 people, so a
drawn person stands for some 85 of the city's: the hubs below are the places a visitor is taken
(the scene's anchors, the jaunt stops of T-3691, the refuges and the neighbourhoods named in the
accounts) and the share each gets follows the census's ward populations in the broad (the West
Division held about half the city, the North and South about a quarter each), with the business
district drawn denser than its few residents because on a Sunday afternoon it was walked by people
from everywhere. A density is never above the census's: the densest hub, State and Madison,
draws some 1,200 people a square kilometre where the wards about it housed several times that.

WHO. A household's community follows the hub's mix (the 1870 census's nativity: about half the city
foreign-born, Germans and Irish first, then Scandinavians, British, Canadians and Bohemians, and some
3,700 Black Chicagoans, most of them in the South Division). Its trade follows its class, with the
words of Edwards's 1871 directory. A household of means keeps a servant girl. The colouring each is
drawn in follows their community; no ancestry is read from any real person.

THE DAY. 8 October 1871 was a Sunday: the stores of State and Lake streets shut, church in the
morning, dinner at one, the afternoon for walking out, visiting and the parks, the horse cars
running. Other dates take a working day. Where outside each stands is their own street front, put
on the context city's walks at run time, so the people follow the streets wherever T-3684's work
moves them.

    python3 tools/town_people_1871.py            write
    python3 tools/town_people_1871.py --check    re-derive in memory and refuse drift (the gate)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIBERTY = "L-town-people-1871"
WARDROBE = "L-wardrobe-1871"
TICKET = "T-3690"
SCENE = "1871"
SCENE_DATE = (1871, 10, 8)
INSIDE = "data/humans/inside_1871.json"
DRESS = "data/humans/variation/dress_1871_town.json"
LOOKS = "data/humans/variation/looks_1871_town.json"
HOUSEHOLDS = "data/residents_1871/households"
TARGET = 3500
SOURCES = ["census_1870_us_vol1", "edwards_chicago_directory_1871", "mitchell_1870_chicago_map"]
DRESS_SOURCES = ["met_ci_1872_afternoon_dress", "met_ci_1870_1875_walking_dress", "met_ci_1875_top_hat",
                 "loc_leslies_1871_wells_street_briggs_house"]


def draw(pid, key):
    return int(hashlib.sha256(f"{pid}:{key}".encode()).hexdigest()[:8], 16) / 2**32


def choose(pid, key, values):
    return values[int(draw(pid, key) * len(values)) % len(values)]


def weighted(pid, key, table):
    """One key of {key: weight}, seeded."""
    total = sum(table.values())
    x = draw(pid, key) * total
    for k, w in table.items():
        x -= w
        if x < 0:
            return k
    return k


# ── where: the hubs ─────────────────────────────────────────────────────────────────────────
# id, the card's words for where the household lives, centre (local E, N), radius m, weight,
# community mix, class mix. Weights are shares of TARGET; the centres are the scene's anchors,
# the jaunt stops and the neighbourhoods of the accounts.
CBD = {"genteel": .3, "trade": .5, "labour": .2}
HUBS = [
    ("state_madison", "in the blocks about State and Madison streets", (862, -560), 420, 15,
     {"yankee": 44, "irish": 18, "german": 20, "british": 8, "scandinavian": 4, "black": 4, "french": 2}, CBD),
    ("court_house", "near the Court House square", (510, -330), 280, 7,
     {"yankee": 45, "irish": 20, "german": 20, "british": 10, "scandinavian": 5}, CBD),
    ("lake_street", "near Lake Street and the river", (700, -120), 320, 5,
     {"yankee": 35, "irish": 30, "german": 20, "british": 10, "scandinavian": 5}, {"genteel": .15, "trade": .45, "labour": .4}),
    ("kilgubbin", "by the North Branch near Kinzie Street", (120, 300), 260, 4,
     {"irish": 70, "german": 15, "yankee": 10, "scandinavian": 5}, {"genteel": .02, "trade": .28, "labour": .7}),
    ("north_clark", "on the North Side near Clark Street and Chicago Avenue", (545, 1080), 620, 11,
     {"german": 52, "yankee": 18, "irish": 12, "scandinavian": 10, "british": 6, "french": 2}, {"genteel": .2, "trade": .5, "labour": .3}),
    ("water_works", "on the North Side near the Water Works", (1120, 1100), 320, 4,
     {"yankee": 50, "german": 20, "irish": 18, "british": 12}, {"genteel": .45, "trade": .35, "labour": .2}),
    ("lincoln_park", "on the North Side near Lincoln Park", (520, 3000), 520, 4,
     {"german": 60, "yankee": 15, "irish": 10, "scandinavian": 10, "british": 5}, {"genteel": .15, "trade": .45, "labour": .4}),
    ("lake_shore_north", "on the North Side near the lake shore", (1250, 700), 300, 2,
     {"yankee": 40, "german": 30, "irish": 20, "british": 10}, {"genteel": .4, "trade": .4, "labour": .2}),
    ("milwaukee_avenue", "on the West Side near Milwaukee Avenue", (-650, 900), 500, 6,
     {"scandinavian": 45, "german": 30, "irish": 10, "yankee": 10, "british": 5}, {"genteel": .05, "trade": .45, "labour": .5}),
    ("west_madison", "on the West Side near Halsted and Madison streets", (-790, -540), 620, 11,
     {"irish": 32, "german": 28, "yankee": 25, "scandinavian": 8, "british": 7}, {"genteel": .15, "trade": .45, "labour": .4}),
    ("union_park", "on the West Side near Union Park", (-2300, -420), 450, 4,
     {"yankee": 55, "german": 15, "irish": 15, "british": 15}, {"genteel": .45, "trade": .4, "labour": .15}),
    ("canal_street", "on the West Side by the river, near Canal Street", (-180, -700), 350, 3,
     {"irish": 50, "german": 30, "yankee": 10, "scandinavian": 10}, {"genteel": .02, "trade": .28, "labour": .7}),
    ("dekoven", "on the West Side near DeKoven Street", (-330, -2030), 520, 9,
     {"irish": 42, "german": 25, "bohemian": 22, "yankee": 6, "scandinavian": 5}, {"genteel": .02, "trade": .38, "labour": .6}),
    ("south_wabash", "on the South Side near Wabash and Michigan avenues", (1050, -1650), 600, 7,
     {"yankee": 60, "british": 12, "german": 12, "irish": 14, "black": 2}, {"genteel": .55, "trade": .3, "labour": .15}),
    ("south_clark", "on the South Side near Clark Street", (640, -1600), 420, 4,
     {"black": 34, "irish": 26, "german": 20, "yankee": 15, "british": 5}, {"genteel": .05, "trade": .4, "labour": .55}),
    ("twelfth_street", "on the South Side near Twelfth and State streets", (865, -2166), 420, 3,
     {"irish": 30, "german": 30, "yankee": 25, "black": 10, "british": 5}, {"genteel": .1, "trade": .5, "labour": .4}),
    ("archer_road", "on the South Branch near Archer Road", (-760, -3950), 520, 3,
     {"irish": 72, "german": 18, "yankee": 5, "bohemian": 5}, {"genteel": .02, "trade": .23, "labour": .75}),
]
# A thin scatter elsewhere in the city: (centre, radius), each a hub of its own few households.
SCATTER = [(-1500, -1300), (-1600, 300), (-2700, -1600), (-1200, -2900), (200, -3000), (1000, -3200),
           (300, 2000), (-300, 1700), (900, 1900), (-1500, 1300), (-2900, 600), (1100, -2600),
           (-300, -1200), (300, -1100), (-1800, -2400), (600, -4300)]
SCATTER_WEIGHT = .8   # each


def hub_rows():
    rows = [dict(id=h[0], where=h[1], at=h[2], r=h[3], w=h[4], mix=h[5], cls=h[6]) for h in HUBS]
    for i, (e, n) in enumerate(SCATTER):
        rows.append(dict(id=f"city_{i + 1:02d}", where="in the city's outer streets", at=(e, n), r=380, w=SCATTER_WEIGHT,
                         mix={"german": 30, "irish": 28, "yankee": 22, "scandinavian": 10, "british": 6, "bohemian": 4},
                         cls={"genteel": .08, "trade": .42, "labour": .5}))
    total = sum(r["w"] for r in rows)
    for r in rows:
        r["quota"] = round(TARGET * r["w"] / total)
    return rows


# ── who: names, birthplaces, trades ─────────────────────────────────────────────────────────
NAMES = {
    "irish": {
        "m": ["Patrick", "John", "Michael", "James", "Thomas", "Daniel", "Dennis", "Timothy", "Edward", "William",
              "Martin", "Bartholomew", "Cornelius", "Jeremiah", "Owen", "Hugh", "Peter", "Bernard", "Terence", "Matthew"],
        "f": ["Mary", "Bridget", "Catherine", "Margaret", "Ellen", "Honora", "Johanna", "Ann", "Julia", "Winifred",
              "Elizabeth", "Norah", "Hannah", "Alice", "Sarah", "Mary Ann", "Kate", "Rose", "Delia", "Ellen"],
        "s": ["Murphy", "Sullivan", "Kelly", "O'Brien", "Ryan", "Walsh", "O'Connor", "McCarthy", "Doyle", "Lynch",
              "Fitzgerald", "Kennedy", "Daly", "Brennan", "Burke", "Carroll", "Gallagher", "Dunne", "Quinn", "Hogan",
              "Shea", "Connolly", "Moran", "Riordan", "Flanagan", "Hennessy", "McNamara", "Nolan", "Keane", "Duffy",
              "Cronin", "Driscoll", "Mahoney", "Hayes", "Mulcahy", "Tierney", "Callahan", "Foley", "Devine", "Rourke"],
        "born": ["County Cork, Ireland", "County Kerry, Ireland", "County Limerick, Ireland", "County Tipperary, Ireland",
                 "County Mayo, Ireland", "County Galway, Ireland", "County Clare, Ireland", "County Kilkenny, Ireland",
                 "County Waterford, Ireland", "County Roscommon, Ireland", "County Sligo, Ireland", "County Donegal, Ireland"],
        "came": (1846, 1869), "church": "Holy Family", },
    "german": {
        "m": ["Johann", "Heinrich", "Friedrich", "Wilhelm", "Carl", "August", "Georg", "Peter", "Jacob", "Christian",
              "Ludwig", "Joseph", "Franz", "Adam", "Philipp", "Gottlieb", "Hermann", "Conrad", "Nicholas", "Anton"],
        "f": ["Maria", "Anna", "Catharina", "Elisabeth", "Margaretha", "Sophia", "Christina", "Wilhelmina", "Barbara",
              "Louise", "Caroline", "Magdalena", "Dorothea", "Friederike", "Johanna", "Emilie", "Bertha", "Theresa"],
        "s": ["Schmidt", "Müller", "Schneider", "Fischer", "Weber", "Meyer", "Wagner", "Becker", "Hoffmann", "Schulz",
              "Koch", "Bauer", "Richter", "Klein", "Wolf", "Schröder", "Neumann", "Schwarz", "Zimmermann", "Braun",
              "Krüger", "Hartmann", "Lange", "Werner", "Krause", "Lehmann", "Huber", "Kaiser", "Fuchs", "Vogel",
              "Engel", "Roth", "Busch", "Haas", "Ziegler", "Kuhn", "Seidel", "Brandt", "Pfeiffer", "Lorenz"],
        "born": ["Prussia", "Bavaria", "Baden", "Hesse", "Württemberg", "Hanover", "Mecklenburg", "Saxony",
                 "the Rhine Province of Prussia", "Westphalia", "Holstein", "Hesse-Darmstadt"],
        "came": (1848, 1869), "church": "St. Michael's", },
    "yankee": {
        "m": ["John", "William", "George", "Charles", "James", "Henry", "Edward", "Samuel", "Joseph", "Thomas",
              "Frederick", "Albert", "Francis", "Benjamin", "Daniel", "Horace", "Walter", "Lyman", "Silas", "Edwin"],
        "f": ["Mary", "Sarah", "Elizabeth", "Emma", "Ellen", "Harriet", "Martha", "Jane", "Caroline", "Julia",
              "Frances", "Lucy", "Clara", "Emily", "Louisa", "Abby", "Helen", "Anna", "Susan", "Hattie"],
        "s": ["Smith", "Johnson", "Brown", "Williams", "Clark", "Wright", "Hall", "Allen", "Baker", "Cook",
              "Hill", "Wood", "Adams", "Phelps", "Sherman", "Wheeler", "Holmes", "Bradley", "Fuller", "Morse",
              "Howard", "Kimball", "Spencer", "Barnes", "Rice", "Ward", "Pratt", "Merrill", "Hubbard", "Chapin",
              "Stevens", "Fisher", "Lyman", "Porter", "Wells", "Parker", "Harris", "Dodge", "Kellogg", "Tuttle"],
        "born": ["New York", "Vermont", "Massachusetts", "Connecticut", "Maine", "New Hampshire", "Ohio", "Pennsylvania",
                 "Illinois", "Michigan", "New York", "Indiana"],
        "came": (1845, 1869), "church": "Second Presbyterian", },
    "british": {
        "m": ["William", "John", "James", "Thomas", "Robert", "George", "David", "Alexander", "Andrew", "Henry"],
        "f": ["Mary", "Jane", "Margaret", "Elizabeth", "Ann", "Agnes", "Isabella", "Janet", "Ellen", "Christina"],
        "s": ["Campbell", "Stewart", "Robertson", "Thomson", "Anderson", "Fraser", "Taylor", "Wilson", "Walker", "Hughes",
              "Roberts", "Evans", "Turner", "Green", "Cooper", "Mitchell", "Graham", "Ross", "Hunter", "Scott"],
        "born": ["England", "Scotland", "Canada West", "Wales", "England", "Scotland", "the North of Ireland"],
        "came": (1850, 1869), "church": "St. James's", },
    "scandinavian": {
        "m": ["Ole", "Hans", "Lars", "Nils", "Anders", "Peter", "Olaf", "Knud", "Erik", "Halvor", "Jens", "Gustaf"],
        "f": ["Anna", "Maria", "Karen", "Ingeborg", "Christine", "Bertha", "Hanna", "Sigrid", "Gunhild", "Johanna"],
        "s": ["Olson", "Hanson", "Larson", "Nelson", "Johnson", "Anderson", "Peterson", "Swenson", "Christianson",
              "Erickson", "Halvorson", "Thompson", "Jacobson", "Knudson", "Lund", "Berg"],
        "born": ["Norway", "Sweden", "Denmark", "Norway", "Sweden"],
        "came": (1852, 1869), "church": "Our Saviour's", },
    "bohemian": {
        "m": ["Josef", "Jan", "František", "Václav", "Karel", "Antonín", "Jakub", "Matěj"],
        "f": ["Marie", "Anna", "Kateřina", "Barbora", "Františka", "Josefa", "Terezie", "Magdalena"],
        "s": ["Novák", "Svoboda", "Dvořák", "Černý", "Procházka", "Kučera", "Veselý", "Horák", "Pospíšil", "Marek"],
        "born": ["Bohemia"], "came": (1853, 1869), "church": "St. Wenceslaus", },
    "french": {
        "m": ["Joseph", "Louis", "Jean-Baptiste", "Pierre", "François", "Antoine"],
        "f": ["Marie", "Josephine", "Adèle", "Julie", "Marguerite", "Louise"],
        "s": ["Lapointe", "Gagnon", "Tremblay", "Bouchard", "Roy", "Côté", "Pelletier", "Gauthier"],
        "born": ["Lower Canada", "Quebec"], "came": (1850, 1869), "church": "Notre Dame", },
    "black": {
        "m": ["John", "George", "William", "Henry", "Charles", "James", "Joseph", "Lewis", "Isaac", "Moses"],
        "f": ["Mary", "Sarah", "Eliza", "Jane", "Martha", "Harriet", "Lucy", "Frances", "Ann", "Maria"],
        "s": ["Johnson", "Jones", "Brown", "Williams", "Jackson", "Thomas", "Davis", "Green", "Taylor", "Washington",
              "Carter", "Wilson", "Bell", "Turner", "Hill", "Coleman"],
        "born": ["Kentucky", "Tennessee", "Missouri", "Virginia", "Illinois", "Ohio", "Indiana", "Maryland"],
        "came": (1850, 1869), "church": "Quinn Chapel", },
}
COMMUNITY_WORDS = {"irish": "Irish", "german": "German", "yankee": "American-born", "british": "British and Canadian",
                   "scandinavian": "Scandinavian", "bohemian": "Bohemian", "french": "French Canadian",
                   "black": "Black Chicagoan"}

# Trades by class, in the words the 1871 directory uses for them.
TRADES = {
    "genteel": ["merchant", "dry goods merchant", "wholesale grocer", "commission merchant", "lumber dealer",
                "grain dealer", "lawyer", "physician", "banker", "real estate dealer", "insurance agent",
                "hardware merchant", "manufacturer", "editor", "clergyman", "architect"],
    "trade": ["clerk", "clerk", "bookkeeper", "salesman", "grocer", "saloon keeper", "druggist", "jeweller", "tailor",
              "shoemaker", "carpenter", "painter", "cabinet maker", "printer", "cigar maker", "baker", "butcher",
              "machinist", "harness maker", "policeman", "fireman", "conductor", "carriage maker", "tinsmith",
              "upholsterer", "watchmaker", "brewer", "cooper", "blacksmith"],
    "labour": ["laborer", "laborer", "laborer", "lumber shover", "teamster", "drayman", "packing house hand",
               "brick maker", "moulder", "sailor", "porter", "stableman", "coal heaver", "hod carrier",
               "planing mill hand", "freight handler"],
}
# Trades the communities kept most to (a weighting, not a rule).
LEAN = {"irish": {"laborer": 3, "lumber shover": 2, "teamster": 2, "drayman": 2, "policeman": 2, "fireman": 2, "packing house hand": 2},
        "german": {"cabinet maker": 3, "baker": 3, "brewer": 3, "butcher": 2, "cigar maker": 2, "saloon keeper": 2, "tailor": 2, "shoemaker": 2},
        "scandinavian": {"carpenter": 3, "sailor": 3, "planing mill hand": 2, "laborer": 2},
        "bohemian": {"tailor": 3, "cigar maker": 2, "lumber shover": 3, "laborer": 2},
        "black": {"porter": 3, "barber": 3, "waiter": 3, "laborer": 2, "coachman": 2},
        "yankee": {"clerk": 2, "bookkeeper": 2, "merchant": 2, "lawyer": 2}}
WOMEN_TRADES = ["dressmaker", "milliner", "seamstress", "tailoress", "laundress", "boarding house keeper", "teacher"]


def pick_trade(pid, cls, com):
    pool = list(TRADES[cls]) + ([t for t in LEAN.get(com, {}) if t not in TRADES[cls] and cls != "genteel"])
    table = {t: (1 + LEAN.get(com, {}).get(t, 0)) for t in pool}
    return weighted(pid, "trade", table)


# ── households ──────────────────────────────────────────────────────────────────────────────
def gauss(pid, key, sd=1.0):
    u1 = max(draw(pid, key + ":1"), 1e-9)
    u2 = draw(pid, key + ":2")
    return math.sqrt(-2 * math.log(u1)) * math.cos(2 * math.pi * u2) * sd


def household(hid, hub, k):
    """One household: its people, its community, class, where it lives and its card."""
    com = weighted(hid, "community", hub["mix"])
    cls = weighted(hid, "class", hub["cls"])
    if com == "black" and cls == "genteel":
        cls = "trade"
    kind = weighted(hid, "kind", {"family": 70, "single": 18 if hub["id"] in ("state_madison", "court_house", "lake_street") else 8,
                                  "widow": 7})
    pool = NAMES[com]
    surname = choose(hid, "surname", pool["s"])
    # A place within the hub: a little gathered to its middle.
    ang = 2 * math.pi * draw(hid, "angle")
    rad = hub["r"] * math.sqrt(draw(hid, "radius")) * (.6 + .4 * draw(hid, "radius2"))
    near = [round(hub["at"][0] + rad * math.sin(ang), 1), round(hub["at"][1] + rad * math.cos(ang), 1)]
    came_lo, came_hi = pool["came"]
    persons = []

    def person(i, sex, age, rel, given, trade=None):
        pid = f"{hid}_{i}"
        persons.append({"id": pid, "given": given, "sex": sex, "age": age, "relationship": rel, "trade": trade})
        return pid

    if kind == "single":
        sex = "male" if draw(hid, "single_sex") < .82 else "female"
        age = 18 + int(draw(hid, "age") * 22)
        given = choose(hid, "given", pool["m" if sex == "male" else "f"])
        trade = pick_trade(hid, cls if cls != "genteel" else "trade", com) if sex == "male" else choose(hid, "wtrade", WOMEN_TRADES)
        person(1, sex, age, "head", given, trade)
    else:
        widow = kind == "widow"
        head_age = 26 + int(draw(hid, "age") * 34) if not widow else 34 + int(draw(hid, "age") * 30)
        if widow:
            person(1, "female", head_age, "head", choose(hid, "given", pool["f"]),
                   choose(hid, "wtrade", WOMEN_TRADES) if draw(hid, "works") < .7 else None)
            mother_age = head_age
        else:
            person(1, "male", head_age, "head", choose(hid, "given", pool["m"]), pick_trade(hid, cls, com))
            mother_age = max(20, head_age - int(draw(hid, "wife_age") * 9))
            person(2, "female", mother_age, "wife", choose(hid, "wife", pool["f"]))
        n_kids = int(draw(hid, "kids") * (5 if cls == "labour" else 4))
        age = min(mother_age - 19, 17)
        used = set()
        for j in range(n_kids):
            if age < 0:
                break
            sex = "male" if draw(hid, f"kid{j}") < .5 else "female"
            names = [x for x in pool["m" if sex == "male" else "f"] if x not in used]
            given = choose(hid, f"kidname{j}", names)
            used.add(given)
            trade = None
            if age >= 14 and sex == "male":
                trade = choose(hid, f"kidtrade{j}", ["clerk", "errand boy", "apprentice", "laborer", "newsboy"])
            person(3 + j, sex, age, "son" if sex == "male" else "daughter", given, trade)
            age -= 1 + int(draw(hid, f"gap{j}") * 3)
        if cls == "genteel" and draw(hid, "servant") < .75:
            scom = weighted(hid, "servant_com", {"irish": 50, "german": 25, "scandinavian": 20, "british": 5})
            spool = NAMES[scom]
            pid = person(9, "female", 16 + int(draw(hid, "servant_age") * 12), "servant", choose(hid, "servant_given", spool["f"]), "servant")
            persons[-1]["own_surname"] = choose(hid, "servant_surname", spool["s"])
            persons[-1]["community"] = scom
        if cls == "labour" and draw(hid, "boarder") < .3:
            bcom = com
            pid = person(10, "male", 19 + int(draw(hid, "boarder_age") * 15), "boarder", choose(hid, "boarder_given", NAMES[bcom]["m"]),
                         pick_trade(hid + "b", "labour", bcom))
            persons[-1]["own_surname"] = choose(hid, "boarder_surname", NAMES[bcom]["s"])
    came = came_lo + int(draw(hid, "came") * (came_hi - came_lo + 1))
    if com in ("yankee",) and draw(hid, "native") < .25:
        came = None   # born in Chicago or come as a child; not said
    born = choose(hid, "born", pool["born"])
    for p in persons:
        p.setdefault("community", com)
        p["surname"] = p.get("own_surname") or surname
        p["name"] = f"{p['given']} {p['surname']}"
        if p["relationship"] in ("son", "daughter") and came and SCENE_DATE[0] - p["age"] > came:
            p["born"] = "Illinois"
        elif p["relationship"] in ("servant", "boarder"):
            p["born"] = choose(p["id"], "born", NAMES[p["community"]]["born"])
        else:
            p["born"] = born
    return {"id": hid, "hub": hub, "community": com, "class": cls, "kind": kind, "surname": surname,
            "near": near, "came": came, "persons": persons}


# ── roles, bodies, dress ─────────────────────────────────────────────────────────────────────
def role_of(p, hh):
    age, sex = p["age"], p["sex"]
    if age < 2:
        return "infant"
    if age < 12:
        return "child"
    if p["relationship"] == "servant":
        return "servant"
    if sex == "female":
        if age < 18:
            return "girl"
        if p.get("trade"):
            return "woman_trade"
        return "lady" if hh["class"] == "genteel" else ("woman_trade" if hh["class"] == "trade" and draw(p["id"], "lady") < .5 else "woman")
    if age < 18:
        return "lad"
    if p.get("trade") in ("teamster", "drayman", "stableman", "coachman"):
        return "workman"
    return {"genteel": "gentleman", "trade": "tradesman", "labour": "workman"}[hh["class"]]


BODY_M = {"glessner_john_j_1904": 1.75, "mahoney_patrick_1835": 1.75, "billings_august_1904_stable_helper": 1.75,
          "bardwell_otis_1835": 1.75, "glessner_frances_m_1904": 1.65, "flynn_mary_1835_dress_study": 1.65,
          "ryan_kate_1904_cook": 1.65, "reynolds_mary_1904_maid": 1.65, "williamson_mattie_1904_cook_study": 1.65,
          "child_boy_1904": 1.208, "child_girl_1904": 1.205, "child_toddler_1904": .905,
          "teen_boy_1904": 1.65, "teen_girl_1904": 1.59}

# Cloths of 1870-72, linear RGB (the bodies draw flat colours; human-finery.js adds weave and trim).
COATS = [("black", [.016, .016, .018]), ("black", [.02, .019, .02]), ("dark brown", [.045, .03, .02]),
         ("navy", [.018, .024, .05]), ("charcoal", [.04, .04, .04]), ("olive brown", [.06, .05, .03]),
         ("bottle green", [.02, .04, .03])]
TROUSERS = [("grey", [.13, .13, .12]), ("dark grey", [.06, .06, .06]), ("drab", [.2, .17, .12]),
            ("black", [.02, .02, .02]), ("brown", [.07, .05, .035]), ("fawn", [.3, .24, .16])]
WAISTCOATS = [("black", [.02, .02, .02]), ("buff", [.36, .28, .16]), ("grey", [.12, .12, .11]),
              ("figured silk", [.2, .08, .06]), ("brown", [.07, .045, .03])]
SHIRTS = [("white", [.62, .6, .55]), ("unbleached", [.48, .43, .34]), ("blue check", [.2, .26, .38]),
          ("red flannel", [.28, .04, .03]), ("grey flannel", [.22, .22, .21]), ("blue", [.12, .17, .28])]
WORK = [("brown", [.08, .05, .03]), ("butternut", [.2, .14, .07]), ("blue", [.05, .08, .15]),
        ("grey", [.12, .12, .11]), ("dark green", [.04, .06, .04]), ("black", [.025, .025, .025])]
# Aniline purples and magentas were the fashion of the years (the Met's purple silk, ca. 1872).
SILKS = [("purple", [.12, .02, .2]), ("plum", [.1, .03, .06]), ("dark green", [.03, .07, .04]),
         ("brown", [.09, .05, .03]), ("fawn", [.36, .25, .13]), ("black", [.018, .018, .02]),
         ("slate blue", [.08, .1, .16]), ("maroon", [.13, .02, .03]), ("grey", [.16, .16, .15]),
         ("magenta", [.3, .03, .14]), ("tan", [.42, .3, .17]), ("navy", [.02, .03, .08])]
PRINTS = [("brown print", [.15, .09, .055]), ("blue print", [.08, .13, .26]), ("grey", [.17, .17, .16]),
          ("lilac print", [.25, .16, .3]), ("buff", [.4, .32, .2]), ("dark green", [.035, .07, .045]),
          ("madder print", [.2, .05, .04]), ("black", [.02, .02, .022])]
APRONS = [("white", [.6, .58, .54]), ("check", [.2, .24, .32]), ("brown holland", [.3, .23, .14])]
FELT = [("black", [.015, .015, .016]), ("brown", [.05, .035, .022]), ("grey", [.12, .11, .1]), ("drab", [.2, .16, .1])]
BONNET = [("black", [.02, .02, .02]), ("brown", [.08, .05, .03]), ("straw", [.5, .42, .25]), ("navy", [.02, .03, .08]),
          ("plum", [.1, .03, .06]), ("grey", [.16, .16, .15])]
TRIM_COL = [[.6, .3, .36], [.7, .62, .6], [.55, .5, .3], [.3, .05, .08], [.1, .2, .4], [.7, .7, .66]]


def r3(v):
    return [round(x, 4) for x in v]


def man_hat(pid, kind):
    """A felt hat: a stovepipe for a gentleman on a Sunday, a low-crowned round felt (the derby the
    years were taking up), a soft wide felt for a workman, or a flat low cap-like felt."""
    n, rgb = choose(pid, "felt", FELT if kind != "silk" else FELT[:1])
    if kind == "silk":
        return f"a black silk hat", {"kind": "round", "rgb": r3(rgb), "band": [.008, .008, .008], "crown_m": round(.165 + .02 * draw(pid, "crown"), 3),
                                     "brim_m": .045, "taper": round(.97 + .04 * draw(pid, "taper"), 3), "roll": .25, "droop": 0, "tilt": 0}
    if kind == "derby":
        return f"a {n} round felt hat", {"kind": "round", "rgb": r3(rgb), "band": [.01, .01, .01], "crown_m": round(.105 + .02 * draw(pid, "crown"), 3),
                                         "brim_m": .045, "taper": .9, "roll": .45, "droop": 0, "tilt": round((draw(pid, "tilt") - .5) * .02, 3)}
    if kind == "cap":
        return f"a {n} cloth cap", {"kind": "round", "rgb": r3(rgb), "band": r3(rgb), "crown_m": .055, "brim_m": .035,
                                    "taper": 1.08, "roll": 0, "droop": .3, "tilt": .02}
    return f"a {n} soft felt hat", {"kind": "round", "rgb": r3(rgb), "band": [.012, .011, .01], "crown_m": round(.1 + .03 * draw(pid, "crown"), 3),
                                    "brim_m": round(.07 + .02 * draw(pid, "brim"), 3), "taper": .95, "roll": .15, "droop": round(.1 + .2 * draw(pid, "droop"), 3), "tilt": 0}


def lady_hat(pid):
    """The small hat of 1870-72, tipped forward over a high chignon, trimmed with flowers or a
    ribbon: drawn as the ruched toque or the small straw (human-hats.js), its brim narrow."""
    n, rgb = choose(pid, "hat", BONNET)
    kind = "toque" if draw(pid, "hatkind") < .55 else "sailor"
    trim = {"flowers": {"n": 5 + int(draw(pid, "fl") * 6), "rgb": choose(pid, "fl1", TRIM_COL), "rgb2": [.3, .4, .25],
                        "side": 1 if draw(pid, "side") < .5 else -1, "spread": 1.2}} if draw(pid, "trim") < .6 else \
        {"bow": {"rgb": choose(pid, "bow", TRIM_COL)}}
    hat = {"kind": kind, "rgb": r3(rgb), "crown_m": .05 if kind == "sailor" else .07, "trim": trim}
    if kind == "sailor":
        hat["brim_m"] = .04
    return f"a small {n} {'straw ' if n == 'straw' else ''}hat trimmed with {'flowers' if 'flowers' in trim else 'a ribbon'}", hat


def dress_for(p, role, hh):
    pid, age, sex = p["id"], p["age"], p["sex"]
    c = lambda key, pal: choose(pid, key, pal)
    if role in ("child", "infant"):
        if age < 5:
            n, rgb = c("frock", [("white", [.6, .58, .54]), ("buff", [.4, .32, .2]), ("blue print", [.08, .13, .26]), ("red", [.3, .06, .05])])
            return {"asset": "child_toddler_1904", "colours": {"garment_upper__child_frock_1904": rgb, "garment_lower__child_frock_1904": rgb},
                    "hide": [], "worn": f"a little {n} frock"}
        if sex == "female":
            n, rgb = c("frock", PRINTS + SILKS[:4])
            return {"asset": "child_girl_1904", "colours": {"garment_upper__child_frock_1904": rgb, "garment_lower__child_frock_1904": rgb},
                    "hide": [], "worn": f"a {n} frock and stockings",
                    "finery": {"garment_lower__child_frock_1904": {"trims": [{"kind": "flounce", "from": "hem", "at_m": .05, "width_m": .08, "rgb": r3(rgb)}]}}}
        n, rgb = c("suit", WORK + COATS[:3])
        out = {"asset": "child_boy_1904", "colours": {"garment_upper__child_jacket_1904": rgb, "garment_lower__child_trousers_1904": rgb},
               "hide": [], "worn": f"a {n} jacket and knee trousers"}
        if draw(pid, "boycap") < .6:
            w, hat = man_hat(pid, "cap")
            out.update(hat=hat, worn=out["worn"] + f" and {w}")
        return out
    if sex == "female":
        if role in ("lady", "girl") or (role == "woman_trade" and draw(pid, "best") < .6):
            n, rgb = c("silk", SILKS)
            trim_rgb = r3([x * .55 for x in rgb]) if draw(pid, "trimdark") < .5 else choose(pid, "trimcol", [[.02, .02, .02], [.6, .58, .54], r3(rgb)])
            asset = "glessner_frances_m_1904" if role != "girl" else "teen_girl_1904"
            if role == "girl":
                return {"asset": "teen_girl_1904", "colours": {"garment_upper__child_frock_1904": rgb, "garment_lower__child_frock_1904": rgb},
                        "hide": [], "worn": f"a {n} dress to the ankle, flounced at the hem",
                        "finery": {"garment_lower__child_frock_1904": {"trims": [{"kind": "flounce", "from": "hem", "at_m": .06, "width_m": .12, "rgb": r3(rgb)},
                                                                                 {"kind": "ribbon", "from": "hem", "at_m": .2, "width_m": .04, "rgb": trim_rgb}]}}}
            w, hat = lady_hat(pid)
            silk = .4 + .4 * draw(pid, "sheen") if role == "lady" else .2
            jacket = {"garment_outer__lady_jacket_black": rgb, "garment_upper__lady_shirtwaist_white": rgb, "garment_lower__lady_skirt_black": rgb}
            skirt_trims = [{"kind": "flounce", "from": "hem", "at_m": .08, "width_m": .18, "rgb": r3(rgb)},
                           {"kind": "flounce", "from": "hem", "at_m": .28, "width_m": .12, "rgb": r3(rgb)}]
            if draw(pid, "fringe") < .5:
                skirt_trims.append({"kind": "braid" if draw(pid, "fringe2") < .5 else "lace", "from": "hem", "at_m": .42, "width_m": .05, "rgb": trim_rgb})
            return {"asset": asset, "colours": jacket, "hide": ["headwear_lady_hat", "lady_hat_plumes", "lace_jabot"],
                    "finery": {"garment_outer__lady_jacket_black": {"silk": round(silk, 2), "trims": [{"kind": "flounce" if draw(pid, "basque") < .5 else "lace", "from": "hem", "at_m": .03, "width_m": .06, "rgb": trim_rgb},
                                                                                                    {"kind": "ribbon", "from": "cuff", "at_m": .04, "width_m": .04, "rgb": trim_rgb}]},
                               "garment_lower__lady_skirt_black": {"silk": round(silk, 2), "trims": skirt_trims}},
                    "hat": hat,
                    "worn": f"a {n} {'silk' if role == 'lady' else 'wool'} day dress, its basque bodice and two-flounced skirt worn over a bustle; {w}"}
        if role == "servant":
            n, rgb = c("gown", PRINTS[:4] + [("black", [.02, .02, .022])])
            w, hat = lady_hat(pid)
            return {"asset": "reynolds_mary_1904_maid", "colours": {"garment_upper__maid_dress_black": rgb, "garment_lower__maid_skirt_black": rgb},
                    "hide": ["headwear_maid_cap", "apron_bib", "apron_bow", "apron_strap_frills", "apron_straps", "maid_apron_skirt", "white_cuffs"],
                    "hat": hat, "worn": f"her Sunday {n} dress and {w}, out on her afternoon"}
        n, rgb = c("gown", PRINTS)
        an, argb = c("apron", APRONS)
        if draw(pid, "body") < .5:
            return {"asset": "flynn_mary_1835_dress_study", "colours": {"garment_upper__plain_dress": rgb, "garment_lower__plain_dress": rgb,
                                                                        "garment_outer__plain_apron": argb},
                    "hide": [] if draw(pid, "apron") < .4 else ["separate_plain_apron"],
                    "worn": f"a {n} dress" + (f" and a {an} apron" if draw(pid, "apron") < .4 else "")}
        return {"asset": "ryan_kate_1904_cook", "colours": {"garment_upper__cook_print_dress": rgb, "garment_lower__cook_print_skirt": rgb,
                                                            "garment_outer__cook_apron_check": argb},
                "hide": ["headwear_cook_head_cloth"] + ([] if draw(pid, "apron") < .5 else ["cook_apron_bib", "cook_apron_skirt", "apron_ties", "apron_waistband"]),
                "worn": f"a {n} dress" + (f" and a {an} apron" if draw(pid, "apron") < .5 else "")}
    # Men and lads.
    if role == "gentleman" or (role == "tradesman" and draw(pid, "suit") < .7):
        cn, crgb = c("coat", COATS)
        tn, trgb = c("trousers", TROUSERS)
        wn, wrgb = c("waistcoat", WAISTCOATS + [(cn, crgb)])
        frock = role == "gentleman" and draw(pid, "frock") < .6
        silk = frock and draw(pid, "silk") < .55
        w, hat = man_hat(pid, "silk" if silk else "derby")
        return {"asset": "glessner_john_j_1904", "colours": {"garment_outer__frock_coat_black": crgb, "garment_lower__trousers_grey_1904": trgb},
                "hide": ["headwear_derby"] + ([] if frock else ["frock_coat_skirts"]),
                "pieces": {"waistcoat_high_cut": wrgb},
                "hat": hat, "worn": f"a {cn} {'frock coat' if frock else 'sack coat'}, a {wn} waistcoat, {tn} trousers and {w}"}
    if role == "lad":
        cn, crgb = c("coat", WORK + COATS[:2])
        out = {"asset": "teen_boy_1904", "colours": {"garment_upper__child_jacket_1904": crgb, "garment_lower__child_trousers_1904": crgb},
               "hide": [], "worn": f"a {cn} jacket and trousers"}
        w, hat = man_hat(pid, "cap")
        out.update(hat=hat, worn=out["worn"] + f" and {w}")
        return out
    sn, srgb = c("shirt", SHIRTS)
    wn, wrgb = c("waistcoat", WORK)
    tn, trgb = c("trousers", WORK + TROUSERS[:3])
    style = draw(pid, "workbody")
    w, hat = man_hat(pid, "cap" if draw(pid, "cap") < .45 else "soft")
    if style < .45:
        return {"asset": "mahoney_patrick_1835", "colours": {"garment_upper__shirt_unbleached_1835": srgb, "garment_outer__waistcoat_green_1835": wrgb,
                                                             "garment_lower__trousers_brown_1835": trgb},
                "hide": ["headwear_slouch_hat"] + ([] if draw(pid, "kerchief") < .5 else ["neckerchief_red"]),
                "hat": hat, "worn": f"a {sn} shirt, a {wn} vest, {tn} trousers and {w}"}
    if style < .75:
        return {"asset": "billings_august_1904_stable_helper", "colours": {"garment_upper__shirt_striped_1904": srgb, "garment_lower__trousers_dark_1904": trgb},
                "hide": ["headwear_felt_hat"], "hat": hat, "worn": f"a {sn} shirt, braces, {tn} trousers and {w}"}
    return {"asset": "bardwell_otis_1835", "colours": {"garment_upper__shirt_linen": srgb, "garment_outer__waistcoat_wool": wrgb,
                                                       "garment_lower__highwaist_pantaloons": trgb},
            "hide": [], "hat": hat, "worn": f"a {sn} shirt, a {wn} vest, {tn} trousers and {w}"}


def looks_for(p, asset):
    pid, age, sex, com = p["id"], p["age"], p["sex"], p["community"]
    if com == "black":
        skin = choose(pid, "skin", ["deep_brown", "deep_brown", "copper", "brown"])
        hair, eyes = "black", choose(pid, "eyes", ["dark_brown", "brown"])
    else:
        skins = {"irish": ["fair", "fair", "ruddy", "light"], "scandinavian": ["fair", "fair", "light"],
                 "german": ["fair", "light", "light", "ruddy"], "bohemian": ["light", "fair", "olive"],
                 "french": ["light", "olive", "fair"]}.get(com, ["fair", "light", "light", "ruddy", "olive"])
        skin = choose(pid, "skin", skins)
        hairs = {"scandinavian": ["fair", "sandy", "light_brown", "fair"], "irish": ["dark_brown", "black_brown", "red", "mid_brown", "sandy"],
                 "german": ["light_brown", "mid_brown", "fair", "dark_brown", "sandy"]}.get(com, ["dark_brown", "mid_brown", "light_brown", "black_brown", "sandy", "fair"])
        hair = choose(pid, "hair", hairs)
        eyes = choose(pid, "eyes", ["blue", "grey", "hazel", "brown"] if com not in ("scandinavian",) else ["blue", "blue", "grey"])
    if age >= 52:
        hair = choose(pid, "grey", ["white_grey", "grey_brown", "sandy_grey"])
    facial = []
    if age < 12:
        cut = ("girl_plait_1812" if draw(pid, "cut") < .6 else "girl_curls_1812") if sex == "female" else ("toddler_curls_1812" if age < 5 else "boy_fringe_1812")
        if age < 5 and sex == "female":
            cut = "toddler_curls_1812"
    elif sex == "female":
        cut = "centre_part_knot_1835"
    else:
        cut = choose(pid, "cut", ["short_side_part_1904", "short_side_part_1904", "brushed_forward_1835"])
        if age >= 20:
            w = draw(pid, "whiskers")
            # The years of the full beard and the side whiskers (the men of the Leslie's crowd, 1871).
            facial = ["beard_short"] if w < .3 else ["side_whiskers"] if w < .5 else ["side_whiskers_short"] if w < .62 else []
    facial += ["brows_fine", "lashes_upper"] if sex == "female" else ["brows_full"]
    base = BODY_M[asset]
    if age < 12:
        anchors = [(2, .85), (3, .905), (4, .99), (5, 1.06), (8, 1.205), (11, 1.40)]
    else:
        anchors = [(12, 1.45), (15, 1.59 if sex == "female" else 1.65), (17, 1.63 if sex == "female" else 1.72), (18, 1.62 if sex == "female" else 1.72)]
    if age >= 18:
        metres = (1.6 if sex == "female" else 1.72) + (draw(pid, "height") - .5) * .16
    else:
        lo = max((x for x in anchors if x[0] <= max(age, anchors[0][0])), key=lambda x: x[0])
        hi = min((x for x in anchors if x[0] >= min(age, anchors[-1][0])), key=lambda x: x[0])
        metres = lo[1] if lo[0] == hi[0] else lo[1] + (hi[1] - lo[1]) * (age - lo[0]) / (hi[0] - lo[0])
        metres *= 1 + (draw(pid, "height") - .5) * .035
    return {"complexion": {"value": skin.replace("_", " "), "drawn": skin, "grade": "reconstructed"},
            "hair": {"value": hair.replace("_", " "), "drawn": hair, "cut": cut, "facial": facial, "grade": "reconstructed"},
            "eyes": {"value": eyes.replace("_", " "), "drawn": eyes, "grade": "reconstructed"},
            "stature": {"inches": round(metres / .0254, 1), "grade": "reconstructed"},
            "height_scale": round(metres / base, 4), "heritage": {"origin": "not found"},
            "grade": "reconstructed", "liberty": LIBERTY}


LOOKS_BASIS = ("No picture of this person is known, and no source names them: complexion, hair, eyes and stature "
               "are seeded choices in the period's range for the household's community, not readings. Their "
               "clothes are October 1871's for their household's means and trade (liberties L-town-people-1871, "
               "L-wardrobe-1871).")


# ── days ─────────────────────────────────────────────────────────────────────────────────────
def S(a, b, where=None, at=None, activity=None, doing="", to=None):
    if where:
        return {"from": a, "to": b, "indoors": True, "where": where, "doing": doing}
    s = {"from": a, "to": b, "indoors": False, "at": at, "activity": activity, "doing": doing}
    if to:
        s["to_point"] = to
    return s


def away(a, b, doing):
    return {"from": a, "to": b, "indoors": True, "away": True, "doing": doing}


# Sunday 8 October 1871: a warm, dry, windy autumn Sunday (the accounts of the fire all say how
# dry and how windy). Church in the morning, dinner at one, the afternoon out of doors.
SUNDAY = {
    "gentleman": [S(0, 7, "home", doing="asleep"), S(7, 9.5, "home", doing="breakfast and the Sunday papers"),
                  away(9.5, 12.5, "at church and walking home"), S(12.5, 14.5, "home", doing="Sunday dinner"),
                  S(14.5, 15.5, at="front", activity="talk", doing="a word with the neighbours at the door"),
                  S(15.5, 18, at="stroll", activity="walk", to="stroll_end", doing="walking out with the family, as everyone does on a fine Sunday"),
                  S(18, 22, "home", doing="tea and the evening at home"), S(22, 24, "home", doing="asleep")],
    "lady": [S(0, 7, "home", doing="asleep"), S(7, 9.5, "home", doing="breakfast and dressing for church"),
             away(9.5, 12.5, "at church"), S(12.5, 14.5, "home", doing="Sunday dinner"),
             S(14.5, 15.25, "home", doing="receiving callers"),
             S(15.25, 17.75, at="stroll", activity="walk", to="stroll_end", doing="walking out in her Sunday dress, and calls on friends"),
             S(17.75, 22, "home", doing="tea and the evening"), S(22, 24, "home", doing="asleep")],
    "tradesman": [S(0, 7, "home", doing="asleep"), S(7, 9, "home", doing="breakfast"),
                  away(9, 12, "at church or Mass"), S(12, 14, "home", doing="dinner"),
                  S(14, 15, at="front", activity="talk", doing="a pipe at the door with the neighbours"),
                  S(15, 17.75, at="stroll", activity="walk", to="stroll_end", doing="a Sunday walk, to the lake, a park or a friend's"),
                  S(17.75, 21.5, "home", doing="supper and the evening"), S(21.5, 24, "home", doing="asleep")],
    "workman": [S(0, 7.5, "home", doing="asleep"), S(7.5, 8.5, "home", doing="breakfast"),
                away(8.5, 11, "at Mass or church"), S(11, 12.5, at="front", activity="talk", doing="talking at the door after church"),
                S(12.5, 14, "home", doing="dinner"),
                S(14, 16.75, at="front", activity="talk", doing="Sunday afternoon at the door and along the street with the neighbours"),
                S(16.75, 18, at="stroll", activity="walk", to="stroll_end", doing="a walk down the street and back"),
                S(18, 21.5, "home", doing="supper"), S(21.5, 24, "home", doing="asleep")],
    "woman": [S(0, 6.5, "home", doing="asleep"), S(6.5, 8.5, "home", doing="the fire, the breakfast and the children"),
              away(8.5, 10.5, "at early Mass or church"), S(10.5, 13.5, "home", doing="cooking the Sunday dinner"),
              S(13.5, 14.5, "home", doing="dinner"),
              S(14.5, 16, at="front", activity="talk", doing="talking with a neighbour at the door"),
              S(16, 17.25, at="stroll", activity="walk", to="stroll_end", doing="a walk with the children"),
              S(17.25, 21.5, "home", doing="supper and the evening"), S(21.5, 24, "home", doing="asleep")],
    "woman_trade": [S(0, 7, "home", doing="asleep"), S(7, 9, "home", doing="breakfast"),
                    away(9, 12, "at church"), S(12, 14, "home", doing="dinner"),
                    S(14, 17.5, at="stroll", activity="walk", to="stroll_end", doing="her Sunday afternoon, walking out and visiting"),
                    S(17.5, 21.5, "home", doing="supper and sewing"), S(21.5, 24, "home", doing="asleep")],
    "servant": [S(0, 5.5, "home", doing="asleep"), S(5.5, 9, "home", doing="the fires and the breakfast"),
                away(9, 10.5, "at early Mass"), S(10.5, 14.75, "home", doing="the Sunday dinner and the dishes"),
                S(14.75, 17.75, at="stroll", activity="walk", to="stroll_end", doing="her afternoon out"),
                S(17.75, 21.5, "home", doing="the tea and the evening"), S(21.5, 24, "home", doing="asleep")],
    "lad": [S(0, 7, "home", doing="asleep"), S(7, 9, "home", doing="breakfast"), away(9, 12, "at church or Sunday school"),
            S(12, 13.5, "home", doing="dinner"),
            S(13.5, 17.5, at="stroll", activity="walk", to="stroll_end", doing="out with his friends, down to the river and the lake"),
            S(17.5, 21, "home", doing="supper"), S(21, 24, "home", doing="asleep")],
    "girl": [S(0, 7, "home", doing="asleep"), S(7, 9, "home", doing="helping with breakfast"), away(9, 12, "at church"),
             S(12, 14, "home", doing="helping with dinner"),
             S(14, 17, at="stroll", activity="walk", to="stroll_end", doing="walking out with her sisters and friends"),
             S(17, 21, "home", doing="supper"), S(21, 24, "home", doing="asleep")],
    "child": [S(0, 7, "home", doing="asleep"), S(7, 9, "home", doing="breakfast"), away(9, 11.5, "at Sunday school"),
              S(11.5, 13.5, "home", doing="dinner"),
              S(13.5, 17.5, at="front", activity="walk", to="front_end", doing="playing along the walk near home with a grown-up of the household"),
              S(17.5, 19.5, "home", doing="supper"), S(19.5, 24, "home", doing="asleep")],
    # A driver of a horse car or a team works on the Sunday (the cars ran): out with it all day.
    "driver": [S(0, 5, "home", doing="asleep"), S(5, 5.5, "home", doing="breakfast"),
               away(5.5, 20.5, "out with his car or team; dinner at the barn or a stand"),
               S(20.5, 21.5, "home", doing="supper"), S(21.5, 24, "home", doing="asleep")],
}
# Any other day: the working week.
WEEKDAY = {
    "gentleman": [S(0, 6.5, "home", doing="asleep"), S(6.5, 7.5, "home", doing="breakfast"),
                  away(7.5, 12.5, "at business downtown"), S(12.5, 13.5, "home", doing="dinner"),
                  away(13.5, 18, "at business downtown"), S(18, 19, at="front", activity="talk", doing="home, a word at the door"),
                  S(19, 22, "home", doing="supper and the evening"), S(22, 24, "home", doing="asleep")],
    "tradesman": [S(0, 5.5, "home", doing="asleep"), S(5.5, 6.5, "home", doing="breakfast"),
                  away(6.5, 12, "at work"), S(12, 13, "home", doing="dinner"), away(13, 18, "at work"),
                  S(18, 19.5, at="front", activity="talk", doing="the evening at the door"), S(19.5, 24, "home", doing="supper and asleep")],
    "workman": [S(0, 5, "home", doing="asleep"), S(5, 5.75, "home", doing="breakfast"),
                away(5.75, 12, "at work in the yards and on the river"), S(12, 12.75, "home", doing="dinner"),
                away(12.75, 18.5, "at work"), S(18.5, 20, at="front", activity="talk", doing="a pipe at the door"),
                S(20, 24, "home", doing="supper and asleep")],
    "lady": [S(0, 7, "home", doing="asleep"), S(7, 10.5, "home", doing="breakfast and the household"),
             S(10.5, 12.5, at="stroll", activity="walk", to="stroll_end", doing="shopping and calls"),
             S(12.5, 15, "home", doing="dinner and sewing"), S(15, 16.5, at="front", activity="talk", doing="talking with a caller at the door"),
             S(16.5, 24, "home", doing="the evening")],
    "woman": [S(0, 5.5, "home", doing="asleep"), S(5.5, 9, "home", doing="breakfast and the house"),
              S(9, 10.5, at="front", activity="work", doing="scrubbing the step and the washing"),
              S(10.5, 15, "home", doing="the house and the dinner"), S(15, 16.25, at="stroll", activity="walk", to="stroll_end", doing="marketing"),
              S(16.25, 24, "home", doing="supper and the evening")],
    "woman_trade": [S(0, 6, "home", doing="asleep"), S(6, 7, "home", doing="breakfast"), away(7, 18, "at her work"),
                    S(18, 24, "home", doing="supper and the evening")],
    "servant": [S(0, 5.5, "home", doing="asleep"), S(5.5, 10, "home", doing="the fires, the breakfast and the rooms"),
                S(10, 11, at="front", activity="work", doing="sweeping the step and the walk"),
                S(11, 24, "home", doing="the dinner, the kitchen and the supper")],
    "lad": [S(0, 6, "home", doing="asleep"), S(6, 7, "home", doing="breakfast"), away(7, 17.5, "at school or at work"),
            S(17.5, 19, at="stroll", activity="walk", to="stroll_end", doing="errands"), S(19, 24, "home", doing="supper and asleep")],
    "girl": [S(0, 6.5, "home", doing="asleep"), S(6.5, 8, "home", doing="breakfast"), away(8, 15.5, "at school"),
             S(15.5, 16.5, at="front", activity="talk", doing="at the door with a friend"), S(16.5, 24, "home", doing="the house and supper")],
    "child": [S(0, 7, "home", doing="asleep"), S(7, 8.5, "home", doing="breakfast"), away(8.5, 15.5, "at school"),
              S(15.5, 17, at="front", activity="walk", to="front_end", doing="playing near home with a grown-up of the household"),
              S(17, 24, "home", doing="supper and asleep")],
    "driver": [S(0, 5, "home", doing="asleep"), S(5, 5.5, "home", doing="breakfast"),
               away(5.5, 20.5, "out with his car or team"), S(20.5, 24, "home", doing="supper and asleep")],
}


def routines():
    rows = {}
    for k in SUNDAY:
        rows[k] = [{"dates": {"from": "1871-10-08", "to": "1871-10-08"}, "spans": [dict(s) for s in SUNDAY[k]]},
                   {"spans": [dict(s) for s in WEEKDAY.get(k, SUNDAY[k])]}]
        for v in rows[k]:
            prev = 0
            for s in v["spans"]:
                assert s["from"] == prev and s["to"] > s["from"], (k, s)
                prev = s["to"]
            assert prev == 24, k
    return rows


# ── the drivers of the town's cars and teams (tools/lay_driven_1871.mjs reads these) ────────
DRIVERS_FILE = "data/transport/driven/drivers_1871.json"


def drivers():
    path = ROOT / DRIVERS_FILE
    return json.loads(path.read_text())["drivers"] if path.exists() else []


def driver_household(d):
    """A driver's household: the man and, as often as not, his wife and children."""
    hid = f"hh_1871_drv_{d['row']}"
    hub = next(h for h in hub_rows() if h["id"] == d["home_hub"])
    hh = household(hid, hub, 0)
    hh["kind"] = "driver"
    hh["class"] = "labour"
    head = hh["persons"][0]
    head.update(sex="male", relationship="head", trade=d["trade"])
    if head["age"] < 22:
        head["age"] = 22 + head["age"] % 10
    head["given"] = choose(hid, "drv_given", NAMES[hh["community"]]["m"])
    head["name"] = f"{head['given']} {head['surname']}"
    head["driver_of"] = d["row"]
    return hh


# ── cards ───────────────────────────────────────────────────────────────────────────────────
def age_words(a):
    return f"About {a}" if a >= 2 else ("Under one" if a < 1 else "About one")


def card(hh):
    hub, com = hh["hub"], hh["community"]
    head = hh["persons"][0]
    title = f"The {hh['surname']} household {hub['where']}" if hh["kind"] != "single" else f"{head['name']}, {hub['where']}"
    if hh["kind"] == "single":
        title = f"{head['name']}'s lodging {hub['where']}"
    came = hh["came"]
    persons = []
    for p in hh["persons"]:
        trade = p.get("trade")
        rel = p["relationship"]
        born_year = SCENE_DATE[0] - p["age"]
        here = (f"came to Chicago about {came}" if came and rel not in ("servant", "boarder") and not (p.get("born") == "Illinois")
                else "born in Chicago" if p.get("born") == "Illinois" and born_year > 1835 else "")
        occ_words = {"keeping house": "keeping house"}
        work = trade or ("keeping house" if rel in ("wife", "head") and p["sex"] == "female" else
                         "at school" if 6 <= p["age"] < 14 else "at home" if p["age"] < 6 else "")
        hist = [f"{'He' if p['sex'] == 'male' else 'She'} was born about {born_year} in {p['born']}"
                + (f" and {here}" if here else "") + "."]
        if trade and rel == "head":
            hist.append(f"{'He' if p['sex'] == 'male' else 'She'} works as a {trade}, and the household lives {hub['where']}.")
        elif rel == "wife":
            hist.append(f"She keeps house for her husband {head['given']} and their family {hub['where']}.")
        elif rel == "servant":
            hist.append(f"She is the hired girl of the {hh['surname']} household, living in, and has Sunday afternoons to herself.")
        elif rel == "boarder":
            hist.append(f"He boards with the {hh['surname']} household and works as a {trade}.")
        elif p["age"] >= 14 and trade:
            hist.append(f"{'He' if p['sex'] == 'male' else 'She'} lives at home and works as {'an' if trade[0] in 'aeiou' else 'a'} {trade}.")
        if p.get("driver_of"):
            hist.append(f"On this Sunday {'he' if p['sex'] == 'male' else 'she'} is out with {DRIVER_WORDS.get(p['driver_of'], 'a team')}.")
        hist.append(f"The family's church is {NAMES[p['community']]['church']}." if rel in ("head", "wife") and NAMES[p['community']].get('church') else "")
        facts = [{"label": "Name", "value": "Reconstructed (no source names them)", "grade": "reconstructed"},
                 {"label": "Age in 1871", "value": age_words(p["age"]), "grade": "reconstructed"},
                 {"label": "Born", "value": p["born"], "grade": "reconstructed"},
                 {"label": "Community", "value": COMMUNITY_WORDS[p["community"]], "grade": "reconstructed"}]
        if work:
            facts.append({"label": "Work", "value": work[0].upper() + work[1:], "grade": "reconstructed"})
        persons.append({
            "id": p["id"], "name": p["name"], "relationship": rel, "grade": "reconstructed", "sources": SOURCES,
            "sex": p["sex"],
            "age_band": {"value": f"{p['age']}-{p['age']}", "low": p["age"], "high": p["age"], "tier": "reconstructed",
                         "note": "Seeded within the household's believable spread of ages; not recorded."},
            **({"occupation": {"value": trade, "tier": "reconstructed",
                               "note": "A trade in the words of Edwards's 1871 directory, chosen for the household's means and community; not a listing."}} if trade else {}),
            "present_on_scene_date": {"value": "present", "confidence": "reconstructed",
                                      "note": "A reconstructed resident of the 1871 city; no source places this person."},
            "note": ("One of the city's 298,977 people of the 1870 census, whom no source names; carded so the streets of "
                     "8 October 1871 have their people. Name, age, birthplace, trade, household and day are reconstructed "
                     f"({LIBERTY})."),
            "reconstruction": {"stage": "reconstructed_resident", "ticket": TICKET, "liberty": LIBERTY,
                               "name": "reconstructed", "history": "reconstructed"},
            "name_basis": {"value": "reconstructed", "grade": "reconstructed",
                           "note": f"No source names {'him' if p['sex'] == 'male' else 'her'}: a name common among the {COMMUNITY_WORDS[p['community']]} people of the period, chosen for this card. Any likeness to a real Chicagoan of 1871 is the commonness of the name."},
            "card_facts": facts,
            "evidence": [],
            "history": {"title": "A reconstructed history", "grade": "reconstructed", "liberty": LIBERTY,
                        "caveat": "No source tells this life: every particular of it is ours.",
                        "paragraphs": [" ".join(x for x in hist if x)]},
        })
    return {
        "id": hh["id"], "scene": SCENE, "name": title, "head": head["id"], "division": hub["id"],
        "present_on_scene_date": {"value": "present", "confidence": "reconstructed", "sources": ["census_1870_us_vol1"],
                                  "note": "A reconstructed household of the 1870 census's city."},
        "associated_with": [{"kind": "home", "place_or_structure_id": hub["id"], "resolves_to": "neighbourhood",
                             "tier": "reconstructed", "source_id": "mitchell_1870_chicago_map",
                             "note": f"Lives {hub['where']}; the house is an anonymous building of the context city (L-1871-city-baseline), found at run time on the street nearest the household's place."}],
        **({"arrival": {"value": str(came), "precision": "year", "tier": "reconstructed"}} if came else {}),
        "card_evidence": [
            {"source_id": "census_1870_us_vol1", "locator": "Population of Chicago, 1870",
             "quote": "the 1870 Census counted 298,977 people living in Chicago, Illinois",
             "claim": "The city's count; this card is one of the reconstructed households drawn at about one person in eighty-five."},
            {"source_id": "edwards_chicago_directory_1871", "locator": "the directory's occupations",
             "claim": "The trades are in the directory's words; no listing is claimed for this household."}],
        "persons": persons,
    }


DRIVER_WORDS = {}


# ── generate ────────────────────────────────────────────────────────────────────────────────
def generate():
    hubs = hub_rows()
    hhs = []
    for hub in hubs:
        count, k = 0, 0
        while count < hub["quota"]:
            k += 1
            hh = household(f"hh_1871_{hub['id']}_{k:03d}", hub, k)
            hhs.append(hh)
            count += len(hh["persons"])
    for d in drivers():
        DRIVER_WORDS[d["row"]] = d["words"]
        hhs.append(driver_household(d))
    inside, care, dresses, looks, cards = [], [], {}, {}, {}
    for hh in hhs:
        cards[hh["id"]] = card(hh)
        adults = []
        for p in hh["persons"]:
            role = "driver" if p.get("driver_of") else role_of(p, hh)
            pid = p["id"]
            if role == "infant":
                care.append({"person": pid, "name": p["name"], "home": hh["id"], "near": hh["near"], "ask_order": 15,
                             "care_only": True, "age_1871": p["age"]})
                continue
            dress = dress_for(p, "workman" if role == "driver" else role, hh)
            entry = {"person": pid, "name": p["name"], "home": hh["id"], "near": hh["near"], "asset_id": dress["asset"],
                     "ask_order": {"head": 10, "wife": 12}.get(p["relationship"], 20 if p["age"] >= 18 else 25),
                     "routine": role, "shift": round((int(draw(pid, "shift") * 7) - 3) * .25, 2)}
            if p["age"] < 12:
                entry["age_1871"] = p["age"]
            else:
                adults.append(entry)
            if p.get("driver_of"):
                entry["drives"] = p["driver_of"]
            inside.append(entry)
            dresses[pid] = {k: dress[k] for k in ("colours", "hide", "worn", "hat", "finery", "pieces") if dress.get(k)}
            dresses[pid].update(grade="reconstructed", liberty=WARDROBE, sources=DRESS_SOURCES)
            looks[pid] = looks_for(p, dress["asset"])
        keepers = sorted([a for a in adults if a["routine"] != "driver"], key=lambda a: (0 if a["routine"] in ("woman", "lady", "servant", "woman_trade") else 1, a["person"]))
        for e in inside[-len(hh["persons"]):]:
            if e.get("home") != hh["id"] or "age_1871" not in e:
                continue
            if keepers:
                e["caregivers"] = [a["person"] for a in keepers[:3]]
                e["supervised"] = True
        for e in care:
            if e["home"] == hh["id"] and keepers:
                e["caregivers"] = [a["person"] for a in keepers[:3]]
    counts = {"people": len(inside), "in_care": len(care), "households": len(hhs),
              "by_hub": {}, "by_community": {}}
    for hh in hhs:
        counts["by_hub"][hh["hub"]["id"]] = counts["by_hub"].get(hh["hub"]["id"], 0) + len(hh["persons"])
        counts["by_community"][hh["community"]] = counts["by_community"].get(hh["community"], 0) + len(hh["persons"])
    doc = {
        "format": "chicago4d_inside_only_v2", "ticket": TICKET, "generated_by": "tools/town_people_1871.py", "scene": SCENE,
        "doc": ("The people of the 1871 city on Sunday 8 October, every one a reconstructed carded resident: built near "
                "the visitor at an hour their day has them out, drawn by the crowd beyond. Each person's day is `routine` "
                "(one of `routines`: the Sunday, then any other day) moved by their `shift` in hours; `home` is their "
                "household, whose house the runtime finds on the context city's street nearest `near` ([local_e, "
                "local_n]), and whose `points` (front, front_end, stroll, stroll_end) it lays on that street's walk "
                "(renderers/web/js/town-1871.js). `drives` names the car or team a driver is out with "
                "(data/transport/driven/loops.json)."),
        "provenance": {"grade": "reconstructed", "ticket": TICKET, "liberty": LIBERTY,
                       "basis": ("Everyone is a reconstructed resident bounded by the 1870 census; the name, household, trade, "
                                 "day, place, body and clothes are ours.")},
        "hubs": {h["id"]: {"where": h["where"], "at": list(h["at"]), "r": h["r"], "quota": h["quota"]} for h in hubs},
        "homes": {hh["id"]: (f"the {hh['surname']} house" if hh["kind"] != "single" else f"{hh['persons'][0]['name']}'s lodging")
                  for hh in hhs},
        "counts": counts, "routines": routines(), "people": inside, "care": care,
    }
    dress_doc = {"format": "chicago4d_human_dress_v1", "scene": SCENE, "ticket": TICKET, "generated_by": "tools/town_people_1871.py",
                 "liberty": WARDROBE, "persons": dresses}
    looks_doc = {"format": "chicago4d_human_looks_set_v1", "scene": SCENE, "ticket": TICKET, "generated_by": "tools/town_people_1871.py",
                 "liberty": LIBERTY, "basis": LOOKS_BASIS, "persons": looks}
    out = {INSIDE: doc, DRESS: dress_doc, LOOKS: looks_doc}
    for hid, c in cards.items():
        out[f"{HOUSEHOLDS}/{hid}.json"] = c
    return out


def render(rel, data):
    if rel == INSIDE:
        head = {k: v for k, v in data.items() if k not in ("people", "care")}
        text = json.dumps(head, indent=1, ensure_ascii=False)[:-2]
        for key in ("people", "care"):
            text += f',\n "{key}": [\n' + ",\n".join("  " + json.dumps(x, separators=(",", ":"), ensure_ascii=False) for x in data[key]) + "\n ]"
        return text + "\n}\n"
    if rel in (DRESS, LOOKS):
        head = {k: v for k, v in data.items() if k != "persons"}
        lines = [f' {json.dumps(k)}: {json.dumps(v, separators=(",", ":"), ensure_ascii=False)}' for k, v in data["persons"].items()]
        return json.dumps(head, indent=1, ensure_ascii=False)[:-2] + ',\n "persons": {\n' + ",\n".join(lines) + "\n }\n}\n"
    return json.dumps(data, indent=1, ensure_ascii=False) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    outputs = generate()
    texts = {rel: render(rel, data) for rel, data in outputs.items()}
    hdir = ROOT / HOUSEHOLDS
    have = {f"{HOUSEHOLDS}/{p.name}" for p in hdir.glob("*.json")} if hdir.exists() else set()
    if args.check:
        bad = [rel for rel, text in texts.items() if not (ROOT / rel).exists() or (ROOT / rel).read_text() != text]
        extra = sorted(have - set(texts))
        if bad or extra:
            raise SystemExit(f"FAIL 1871 town people stale: {len(bad)} differ ({', '.join(bad[:4])}), {len(extra)} not written by "
                             "this tool — run python3 tools/town_people_1871.py")
    else:
        for rel in have - set(texts):
            (ROOT / rel).unlink()
        for rel, text in texts.items():
            path = ROOT / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists() or path.read_text() != text:
                path.write_text(text)
    c = outputs[INSIDE]["counts"]
    print(f"ok 1871 town people {'reproduce' if args.check else 'written'}: {c['people']} people out and about, "
          f"{c['in_care']} in care, {c['households']} households; by community {c['by_community']}")


if __name__ == "__main__":
    main()
