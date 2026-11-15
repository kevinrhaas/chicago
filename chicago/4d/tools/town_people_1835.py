#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""T-3556: the 1835 town's people, each going in and out of their own home and place of business.

The owner, 2026-11-15: *"Can you go ahead and fill out the 1835 people, include their ability to
enter and exit their homes or places of business and add all interactions with them as
possible"*. Before this the 1835 town drew four people with a day (data/humans/instances/1835/);
everybody else the residents layer holds present on 1 July 1835 had a roof (their own card's
`lives_at`, or tools/house_the_present_1835.py's seat) and no day.

This writes, from the household records and the housing deal (nothing here is a new reading of
any record; every choice below is the reconstruction liberty L-town-people-1835):

    data/humans/inside_1835.json              everyone present and under a roof with a door: home,
                                              place of business (`work`, their card's `works_at`),
                                              body, a day by their household role and trade
                                              (`routine`, one of ROUTINES, at their own `shift`),
                                              and the places outside their doors that day uses
    data/humans/doors_1835.json               every door of those homes and places of business
                                              (tools/derive_doors_scene.py, run here on the set)
    data/humans/variation/dress_1835_town.json  each one's own cloth colours (human-looks.js)
    data/humans/variation/looks_1835_town.json  each one's complexion, hair, eyes and stature

renderers/web/js/human-days.js plays them as it plays 1904's Prairie Avenue: nobody is built until
they are near the visitor at an hour the day has them out, or asked for at a door; a day's
`where` of `work` takes them into their place of business, where its door offers Ask for them.

    python3 tools/town_people_1835.py            write
    python3 tools/town_people_1835.py --check    re-derive in memory and refuse drift (the gate)

WHAT IS CHOSEN HERE (L-town-people-1835), said once:
  * THE BODY a person is drawn on comes from their household role, trade, age and community:
    the merchant's tail coat and top hat (Peck's), the clerk's or tradesman's shirt and waistcoat
    (Bardwell's), the labourer's slouch hat and braces (Mahoney's), a plain dress (Mary Flynn's,
    its apron off for a woman of a merchant's or professional man's household), the working
    woman's short gown, the Creole and Métis women's calico short gown and head handkerchief,
    the 1812 garrison's coat as the Fifth Infantry's, recoloured to the 1832 regulation, and the
    Potawatomi bodies of 1812 for the town's Native residents. Children wear the 1812 children's
    clothes. None of these is a picture of anyone.
  * THE AGE inside a record's band is seeded by the person's id (`age_of`); under 2 years is
    in household care (asked after at the door, never walking out), 2-11 a child kept company by
    the adults of the household, 12-17 an adult body drawn smaller.
  * THE DAY is a template of the period's working day by role (ROUTINES), turned to each person
    by a seeded shift of up to three quarters of an hour; where they stand outside is before
    their own door, beside their own house, or before their place of business.
  * COLOURING is seeded from the European range for most of the town; the town's free Black
    residents, Native people and Métis are drawn in the colouring their community names
    (`community` on their row), so that they are not drawn as everyone else; no ancestry is
    inferred from a surname.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

LIBERTY = "L-town-people-1835"
TICKET = "T-3556"
SCENE_DATE = (1835, 7, 1)
INSIDE = "data/humans/inside_1835.json"
DOORS = "data/humans/doors_1835.json"
DRESS = "data/humans/variation/dress_1835_town.json"
LOOKS = "data/humans/variation/looks_1835_town.json"
# The four of 1835 already drawn with their own days (data/humans/instances/1835/): their looks
# are given here too (they had none), their days stay theirs.
DRAWN = ("peck_philip", "rc_bardwell_otis", "rc_flynn_mary", "rc_mahoney_patrick")


def read(rel):
    return json.loads((ROOT / rel).read_text())


def draw(pid, key):
    return int(hashlib.sha256(f"{pid}:{key}".encode()).hexdigest()[:8], 16) / 2**32


def choose(pid, key, values):
    return values[int(draw(pid, key) * len(values)) % len(values)]


# ── who ─────────────────────────────────────────────────────────────────────────────────────
GENTEEL = ("merchant", "attorney", "physician", "forwarding", "land_agent", "auctioneer", "army_officer",
           "surveyor", "banker", "editor", "clergyman", "minister", "druggist", "dry_goods", "hardware",
           "commission", "judge", "postmaster", "printer", "notary", "justice")
KEEPERS = ("grocer", "tavern_keeper", "hotel_keeper", "refectory_keeper", "boarding_house_keeper", "trader",
           "baker", "clerk", "schoolteacher", "teacher", "watchmaker", "jeweller", "saddler", "bookseller")
TRADES = ("carpenter", "blacksmith", "cooper", "tailor", "shoemaker", "mason", "builder", "butcher",
          "brickmaker", "sawyer", "carriage_maker", "wheelwright", "painter", "tinsmith", "tanner",
          "joiner", "plasterer", "gunsmith", "millwright", "chairmaker", "cabinetmaker", "hatter", "harness")
LABOUR = ("labourer", "laborer", "teamster", "boatman", "farmer", "sailor", "drover", "carter", "porter",
          "ferryman", "fisherman", "voyageur", "hunter", "woodcutter")
WOMEN_TRADES = ("milliner", "dressmaker", "seamstress", "tailoress")
FEMALE_NAMES = {"mary", "sarah", "elizabeth", "margaret", "ann", "anna", "jane", "catherine", "eliza", "hannah",
                "susan", "nancy", "martha", "harriet", "julia", "emily", "lucy", "abigail", "rebecca", "rachel",
                "betsey", "polly", "bridget", "ellen", "frances", "caroline", "louisa", "maria", "charlotte",
                "esther", "lydia", "phebe", "phoebe", "clarissa", "matilda", "amanda", "almira", "lucinda",
                "josette", "archange", "madeline", "angelique", "therese", "marguerite", "emma", "isabella", "laura"}


def occupation(per):
    occ = per.get("occupation")
    v = (occ.get("value") if isinstance(occ, dict) else occ) or ""
    return "" if v in ("none_recorded", "unknown") else str(v).lower()


def sex_of(per, row):
    """The body's presentation: the record's sex, else its relationship, else the first name."""
    if per.get("sex") in ("male", "female"):
        return per["sex"]
    if row["relationship"] in ("wife", "daughter"):
        return "female"
    if row["relationship"] == "son":
        return "male"
    first = row["name"].replace("[?]", "").strip().split(" ")[0].lower().strip(".")
    return "female" if first in FEMALE_NAMES or first in ("mrs", "miss", "widow") else "male"


def age_of(pid, per):
    """Years on 1 July 1835: the record's birth year, else seeded inside its age band."""
    by = per.get("birth_year")
    by = by.get("value") if isinstance(by, dict) else by
    if str(by or "")[:4].isdigit():
        return max(0, SCENE_DATE[0] - int(str(by)[:4]))
    band = per.get("age_band") or {}
    lo, hi = band.get("low"), band.get("high")
    if isinstance(lo, int):
        hi = hi if isinstance(hi, int) else lo + 15
        return lo + int(draw(pid, "age") * (hi - lo + 1))
    return 18 + int(draw(pid, "age") * 22) if per.get("relationship") not in ("son", "daughter", "child") else 8


def household_kind(members):
    """Whether a household is a merchant's or professional man's (genteel), a keeper's or tradesman's,
    or a labouring one: by the trades its own people are recorded in."""
    occs = [occupation(p) for p in members]
    if any(any(w in o for w in GENTEEL) for o in occs):
        return "genteel"
    if any(any(w in o for w in KEEPERS + TRADES + WOMEN_TRADES) for o in occs):
        return "trade"
    return "labour"


def role_of(row, per, sex, age, hh_kind):
    occ = occupation(per)
    com = row.get("community") or ""
    if age < 2:
        return "infant"
    if age < 12:
        return "child"
    if occ == "soldier" or (row.get("lives_at") == "fort_dearborn_barracks" and sex == "male" and age >= 18 and not occ):
        return "soldier"
    if sex == "female":
        if age < 18:
            return "girl"
        if "laundress" in occ:
            return "laundress"
        if "domestic" in occ or "servant" in occ:
            return "domestic"
        if any(w in occ for w in WOMEN_TRADES + ("boarding_house_keeper", "schoolteacher", "teacher", "keeper")):
            return "woman_trade"
        return "lady" if hh_kind == "genteel" and com not in ("native", "metis") else "woman"
    if age < 18:
        return "lad"
    if any(w in occ for w in GENTEEL):
        return "gentleman"
    if any(w in occ for w in KEEPERS):
        return "keeper"
    if any(w in occ for w in TRADES):
        return "tradesman"
    if hh_kind == "genteel" and row["relationship"] in ("head", "son", "brother", "partner"):
        return "gentleman"
    return "labourer"


# ── bodies and dress ────────────────────────────────────────────────────────────────────────
BODY_M = {"peck_philip_1835": 1.75, "bardwell_otis_1835": 1.75, "mahoney_patrick_1835": 1.75,
          "settler_1812": 1.75, "private_first_infantry_1812": 1.75, "potawatomi_man_1812": 1.75,
          "flynn_mary_1835_dress_study": 1.65, "woman_working_1812": 1.65, "woman_country_1812": 1.65,
          "potawatomi_woman_1812": 1.65,
          "child_boy_1812": 1.205, "child_girl_1812": 1.205, "child_toddler_1812": .905,
          "potawatomi_boy_1812": 1.205, "potawatomi_girl_1812": 1.205}

# Cloths of the 1830s, linear RGB (the dressed bodies draw flat colours).
DARK = [("black", [.018, .018, .02]), ("dark blue", [.02, .03, .07]), ("bottle green", [.02, .045, .03]),
        ("claret", [.07, .02, .03]), ("brown", [.07, .042, .025]), ("drab", [.16, .13, .08])]
LIGHT_TROUSERS = [("stone", [.36, .32, .24]), ("nankeen", [.42, .32, .16]), ("white duck", [.55, .54, .5]),
                  ("grey", [.2, .2, .19]), ("fawn", [.32, .25, .16])]
WORK = [("brown", [.08, .05, .03]), ("butternut", [.22, .15, .07]), ("blue", [.05, .08, .15]),
        ("grey", [.13, .13, .12]), ("green", [.04, .07, .04]), ("russet", [.16, .07, .035])]
SHIRT = [("unbleached", [.5, .45, .36]), ("white", [.62, .6, .55]), ("check", [.25, .3, .4]),
         ("red flannel", [.3, .04, .03]), ("blue", [.15, .2, .3])]
GOWN = [("lilac print", [.25, .16, .3]), ("brown print", [.15, .09, .055]), ("blue print", [.08, .13, .26]),
        ("grey", [.17, .17, .16]), ("buff", [.4, .32, .2]), ("dark green", [.035, .07, .045]),
        ("plum", [.11, .03, .06]), ("rose", [.36, .16, .17]), ("black silk", [.02, .02, .022]), ("drab", [.2, .17, .12])]
APRON = [("linen", [.5, .46, .38]), ("check", [.2, .24, .32]), ("brown holland", [.3, .23, .14]), ("white", [.6, .58, .54])]
CALICO = [("red calico", [.32, .05, .04]), ("blue calico", [.06, .1, .26]), ("yellow calico", [.45, .32, .08]),
          ("green calico", [.06, .16, .07])]
INFANTRY = {"garment_upper__coat_blue_1812": [.012, .018, .05], "garment_upper__facings_red_1812": [.012, .018, .05]}


def dress_for(pid, role, sex, com, age):
    """{asset, colours, hide, worn} for one person."""
    c = lambda key, pal: choose(pid, key, pal)
    if role in ("child", "infant"):
        if com == "native":
            a = "potawatomi_girl_1812" if sex == "female" else "potawatomi_boy_1812"
            return {"asset": a, "colours": {}, "hide": [], "worn": "a child's dress of the camps"}
        if age < 5:
            n, rgb = c("frock", [("white", [.6, .58, .54]), ("buff", [.4, .32, .2]), ("blue print", [.08, .13, .26])])
            return {"asset": "child_toddler_1812", "colours": {"garment_upper__toddler_frock_white_1812": rgb, "garment_lower__toddler_frock_white_1812": rgb},
                    "hide": [], "worn": f"a little {n} frock"}
        if sex == "female":
            n, rgb = c("frock", GOWN)
            return {"asset": "child_girl_1812", "colours": {"garment_upper__frock_bodice_rose_1812": rgb, "garment_lower__frock_skirt_rose_1812": rgb},
                    "hide": [] if draw(pid, "pinafore") < .7 else ["pinafore_apron", "pinafore_bib"],
                    "worn": f"a {n} frock" + (" and a pinafore" if draw(pid, "pinafore") < .7 else "")}
        n, rgb = c("suit", WORK + [("nankeen", [.42, .32, .16])])
        return {"asset": "child_boy_1812", "colours": {"garment_upper__skeleton_jacket_blue_1812": rgb, "garment_lower__skeleton_trousers_blue_1812": rgb},
                "hide": [], "worn": f"a {n} skeleton suit"}
    if role == "soldier":
        summer = draw(pid, "fatigue") < .6
        cols = dict(INFANTRY)
        if not summer:
            cols["garment_lower__overalls_linen_1812"] = [.2, .3, .45]
        return {"asset": "private_first_infantry_1812", "colours": cols, "hide": [],
                "worn": "the infantry's dark blue coat and " + ("white summer trousers" if summer else "sky-blue trousers")}
    if com == "native":
        if sex == "female":
            return {"asset": "potawatomi_woman_1812", "colours": {}, "hide": [], "worn": "a trade-cloth dress"}
        return {"asset": "potawatomi_man_1812", "colours": {}, "hide": [], "worn": "a calico shirt, leggings and breechcloth"}
    if sex == "female":
        if role == "lady":
            n, rgb = c("gown", GOWN)
            return {"asset": "flynn_mary_1835_dress_study", "colours": {"garment_upper__plain_dress": rgb, "garment_lower__plain_dress": rgb},
                    "hide": ["separate_plain_apron"], "worn": f"a {n} day dress"}
        country = com in ("metis", "french_canadian") and draw(pid, "country") < .7
        short = not country and (role in ("laundress", "domestic") and draw(pid, "short") < .6
                                 or com in ("irish",) and draw(pid, "short") < .4)
        if country:
            n, rgb = c("calico", CALICO)
            pn, prgb = c("petticoat", WORK)
            return {"asset": "woman_country_1812", "colours": {"garment_upper__short_gown_red_calico_1812": rgb, "garment_lower__petticoat_dark_stroud_1812": prgb},
                    "hide": [], "worn": f"a {n} short gown, a {pn} petticoat and a head handkerchief"}
        if short:
            n, rgb = c("gown", GOWN)
            pn, prgb = c("petticoat", WORK)
            return {"asset": "woman_working_1812", "colours": {"garment_upper__short_gown_madder_print_1812": rgb, "garment_lower__petticoat_blue_homespun_1812": prgb},
                    "hide": [], "worn": f"a {n} short gown, a {pn} petticoat, apron and cap"}
        n, rgb = c("gown", GOWN)
        an, argb = c("apron", APRON)
        return {"asset": "flynn_mary_1835_dress_study", "colours": {"garment_upper__plain_dress": rgb, "garment_lower__plain_dress": rgb,
                                                                      "garment_outer__plain_apron": argb},
                "hide": [], "worn": f"a {n} dress and a {an} apron"}
    if role == "gentleman":
        cn, crgb = c("coat", DARK)
        tn, trgb = c("trousers", LIGHT_TROUSERS + DARK[:2])
        wn, wrgb = c("waistcoat", [("buff", [.4, .3, .16]), ("black", [.02, .02, .02]), ("figured silk", [.25, .1, .08]), ("white", [.58, .56, .5])])
        return {"asset": "peck_philip_1835", "colours": {"garment_outer__tailcoat_blue_1835": crgb, "garment_lower__trousers_stone_1835": trgb,
                                                          "garment_outer__waistcoat_buff_1835": wrgb},
                "hide": [], "worn": f"a {cn} tail coat, a {wn} waistcoat and {tn} trousers"}
    if role in ("keeper", "tradesman", "lad") and not (role == "lad" and draw(pid, "lad") < .4):
        wn, wrgb = c("waistcoat", DARK + WORK)
        tn, trgb = c("trousers", WORK + LIGHT_TROUSERS)
        sn, srgb = c("shirt", SHIRT[:3])
        return {"asset": "bardwell_otis_1835", "colours": {"garment_outer__waistcoat_wool": wrgb, "garment_lower__highwaist_pantaloons": trgb,
                                                            "garment_upper__shirt_linen": srgb},
                "hide": [], "worn": f"a {sn} shirt, a {wn} waistcoat and {tn} trousers"}
    if com in ("metis", "french_canadian") and draw(pid, "settler") < .5 or draw(pid, "settler") < .25:
        wn, wrgb = c("waistcoat", WORK)
        sn, srgb = c("shirt", SHIRT)
        return {"asset": "settler_1812", "colours": {"garment_outer__waistcoat_brown_1810": wrgb, "garment_upper__shirt_tow_linen_1810": srgb},
                "hide": [], "worn": f"a {sn} shirt, a {wn} waistcoat and a round hat"}
    wn, wrgb = c("waistcoat", WORK)
    tn, trgb = c("trousers", WORK)
    sn, srgb = c("shirt", SHIRT)
    return {"asset": "mahoney_patrick_1835", "colours": {"garment_outer__waistcoat_green_1835": wrgb, "garment_lower__trousers_brown_1835": trgb,
                                                          "garment_upper__shirt_unbleached_1835": srgb},
            "hide": [], "worn": f"a {sn} shirt, a {wn} waistcoat, {tn} trousers and a slouch hat"}


# ── looks ───────────────────────────────────────────────────────────────────────────────────
def looks_for(pid, sex, age, com, asset):
    if com == "free_black":
        skin = choose(pid, "skin", ["deep_brown", "deep_brown", "copper", "brown"])
        hair, eyes = "black", choose(pid, "eyes", ["dark_brown", "brown"])
    elif com == "native":
        skin, hair, eyes = choose(pid, "skin", ["copper", "copper", "tan"]), "black", "dark_brown"
    elif com == "metis":
        skin, hair, eyes = choose(pid, "skin", ["tan", "olive", "copper"]), choose(pid, "hair", ["black", "black_brown"]), choose(pid, "eyes", ["brown", "dark_brown"])
    else:
        skin = choose(pid, "skin", ["fair", "light", "light", "ruddy", "olive"] if com != "irish" else ["fair", "fair", "ruddy", "light"])
        hair = choose(pid, "hair", ["dark_brown", "mid_brown", "mid_brown", "light_brown", "black_brown", "sandy", "fair", "red"])
        eyes = choose(pid, "eyes", ["blue", "grey", "hazel", "brown", "brown"])
    if age >= 55 and com not in ("native",):
        hair = choose(pid, "grey", ["white_grey", "grey_brown", "sandy_grey"])
    facial = []
    if age < 12:
        cut = ("girl_plait_1812" if draw(pid, "cut") < .6 else "girl_curls_1812") if sex == "female" else (
            "toddler_curls_1812" if age < 5 else "boy_fringe_1812")
        if age < 5 and sex == "female":
            cut = "toddler_curls_1812"
    elif sex == "female":
        cut = "centre_part_low_1812" if com == "native" else "centre_part_knot_1835"
    else:
        cut = "clubbed_long_1812" if com == "native" else choose(pid, "cut", ["brushed_forward_1835", "brushed_forward_1835", "short_side_part_1904", "cropped_1812"])
        if age >= 20 and com not in ("native",):
            w = draw(pid, "whiskers")
            facial = ["side_whiskers"] if w < .3 else ["side_whiskers_short"] if w < .55 else ["beard_short"] if w < .62 else []
    facial += ["brows_fine", "lashes_upper"] if sex == "female" else ["brows_full"]
    base = BODY_M[asset]
    if age < 12:
        anchors = [(2, .85), (3, .905), (4, .99), (5, 1.06), (8, 1.205), (11, 1.40)]
    else:
        anchors = [(12, 1.45), (15, 1.59 if sex == "female" else 1.65), (17, 1.63 if sex == "female" else 1.72),
                   (18, 1.62 if sex == "female" else 1.72)]
    if age >= 18:
        metres = (1.6 if sex == "female" else 1.72) + (draw(pid, "height") - .5) * .16
    else:
        lo = max((x for x in anchors if x[0] <= max(age, anchors[0][0])), key=lambda x: x[0])
        hi = min((x for x in anchors if x[0] >= min(age, anchors[-1][0])), key=lambda x: x[0])
        metres = lo[1] if lo[0] == hi[0] else lo[1] + (hi[1] - lo[1]) * (age - lo[0]) / (hi[0] - lo[0])
        metres *= 1 + (draw(pid, "height") - .5) * .035
    inches = round(metres / .0254, 1)
    return {"complexion": {"value": skin.replace("_", " "), "drawn": skin, "grade": "reconstructed"},
            "hair": {"value": hair.replace("_", " "), "drawn": hair, "cut": cut, "facial": facial, "grade": "reconstructed"},
            "eyes": {"value": eyes.replace("_", " "), "drawn": eyes, "grade": "reconstructed"},
            "stature": {"inches": inches, "grade": "reconstructed"},
            "height_scale": round(metres / base, 4), "heritage": {"origin": "not found"},
            "grade": "reconstructed", "liberty": LIBERTY}


LOOKS_BASIS = ("No picture of this person is known. Complexion, hair, eyes and stature are seeded choices in "
               "the period's range, not readings; the town's free Black, Native and Métis residents are drawn "
               "in the colouring their community names, and no ancestry is inferred from a surname. Their "
               "clothes follow their household role and trade (liberty L-town-people-1835).")


# ── days ────────────────────────────────────────────────────────────────────────────────────
def S(a, b, where=None, at=None, activity=None, doing="", to=None):
    """A span of a routine: indoors in `where` ('home' | 'work'), or out at `at` doing `activity`."""
    if where:
        return {"from": a, "to": b, "indoors": True, "where": where, "doing": doing}
    s = {"from": a, "to": b, "indoors": False, "at": at, "activity": activity, "doing": doing}
    if to:
        s["to_point"] = to
    return s


def away(a, b, doing):
    return {"from": a, "to": b, "indoors": True, "away": True, "doing": doing}


# Each routine: the summer day (May to October) and the winter day (the rest), hours of 1835's
# working day (sun to sun for labour, a merchant's store open seven to evening, dinner at noon).
# 'front' stands before their home's door, 'yard' beside the house, 'work' before their place of
# business; `to` the far end of a walk along the frontage.
ROUTINES = {
    "gentleman": [
        S(0, 6, "home", doing="asleep"), S(6, 7, "home", doing="breakfast"),
        S(7, 8, at="work", activity="work", doing="opening for the day's business"),
        S(8, 11.5, "work", doing="at business"),
        S(11.5, 12.25, at="work", activity="talk", doing="at the door, talking with whoever passes"),
        S(12.25, 13, "home", doing="at dinner"),
        S(13, 14, at="front", activity="walk", to="front_end", doing="a turn along the street after dinner"),
        S(14, 17.5, "work", doing="at business, letters and accounts"),
        S(17.5, 18.5, at="work", activity="talk", doing="news and prices at the door"),
        S(18.5, 21.5, "home", doing="supper and the evening at home"), S(21.5, 24, "home", doing="asleep")],
    "keeper": [
        S(0, 5.5, "home", doing="asleep"), S(5.5, 6.5, "home", doing="breakfast"),
        S(6.5, 7.5, at="work", activity="work", doing="sweeping out and setting goods at the door"),
        S(7.5, 11, "work", doing="serving customers"),
        S(11, 12.5, at="work", activity="work", doing="seeing to goods and customers at the door"),
        S(12.5, 13.25, "home", doing="at dinner"),
        S(13.25, 16, "work", doing="serving customers"),
        S(16, 17.5, at="work", activity="talk", doing="talking with customers at the door"),
        S(17.5, 20, "work", doing="the evening trade"),
        S(20, 21, at="front", activity="talk", doing="a word with the neighbours"),
        S(21, 24, "home", doing="asleep")],
    "tradesman": [
        S(0, 5, "home", doing="asleep"), S(5, 6, "home", doing="breakfast"),
        S(6, 9.5, at="work", activity="work", doing="at work, in the open in summer"),
        S(9.5, 11.5, "work", doing="at the bench"),
        S(11.5, 12.25, "home", doing="at dinner"),
        S(12.25, 15, at="work", activity="work", doing="at work in the open"),
        S(15, 17.5, "work", doing="at the bench"),
        S(17.5, 18.5, at="work", activity="work", doing="finishing and clearing up"),
        S(18.5, 20.5, "home", doing="supper"),
        S(20.5, 21.5, at="front", activity="talk", doing="a pipe at the door with the neighbours"),
        S(21.5, 24, "home", doing="asleep")],
    "labourer": [
        S(0, 5, "home", doing="asleep"), S(5, 5.75, "home", doing="breakfast"),
        S(5.75, 6.5, at="front", activity="work", doing="splitting wood and carrying water before work"),
        away(6.5, 11.5, "at work about the town and the harbour, where is not recorded"),
        S(11.5, 12.25, "home", doing="at dinner"),
        S(12.25, 13.5, at="front", activity="talk", doing="resting after dinner, a pipe at the door"),
        away(13.5, 18.5, "at work about the town and the harbour, where is not recorded"),
        S(18.5, 19.5, "home", doing="supper"),
        S(19.5, 21, at="front", activity="talk", doing="the evening at the door"),
        S(21, 24, "home", doing="asleep")],
    "soldier": [
        S(0, 4.75, "home", doing="asleep in barracks"), S(4.75, 5.5, "home", doing="reveille and roll call"),
        S(5.5, 7.5, at="front", activity="work", doing="drill"),
        S(7.5, 8.25, "home", doing="breakfast"),
        S(8.25, 11.5, at="yard", activity="work", doing="fatigue duty about the fort"),
        S(11.5, 12.25, "home", doing="dinner"),
        S(12.25, 15, at="yard", activity="work", doing="fatigue duty about the fort"),
        S(15, 17.5, "home", doing="cleaning arms and kit"),
        S(17.5, 18.5, at="front", activity="stand", doing="evening parade"),
        S(18.5, 21, at="front", activity="talk", doing="off duty"),
        S(21, 24, "home", doing="asleep in barracks")],
    "woman": [
        S(0, 5, "home", doing="asleep"), S(5, 7, "home", doing="the fire, breakfast and the children"),
        S(7, 8, at="yard", activity="work", doing="milking, the hens and the garden"),
        S(8, 10, "home", doing="the day's work of the house"),
        S(10, 11, at="yard", activity="work", doing="washing and hanging it out"),
        S(11, 12.25, "home", doing="cooking the dinner"), S(12.25, 13, "home", doing="at dinner"),
        S(13, 14.25, at="front", activity="talk", doing="talking with a neighbour at the door"),
        S(14.25, 17, "home", doing="sewing and mending"),
        S(17, 17.75, at="yard", activity="work", doing="fetching water and wood"),
        S(17.75, 21.5, "home", doing="supper and the evening"), S(21.5, 24, "home", doing="asleep")],
    "lady": [
        S(0, 6, "home", doing="asleep"), S(6, 8, "home", doing="breakfast and the household"),
        S(8, 11, "home", doing="the household, sewing and letters"),
        S(11, 12, at="front", activity="walk", to="front_end", doing="calls and errands along the street"),
        S(12, 13, "home", doing="at dinner"),
        S(13, 14.5, at="front", activity="talk", doing="talking with a neighbour"),
        S(14.5, 17.5, "home", doing="sewing, reading and visitors"),
        S(17.5, 18.5, at="yard", activity="work", doing="the garden in the cool of the evening"),
        S(18.5, 22, "home", doing="supper and the evening"), S(22, 24, "home", doing="asleep")],
    "woman_trade": [
        S(0, 5.5, "home", doing="asleep"), S(5.5, 7, "home", doing="breakfast"),
        S(7, 11.5, "work", doing="at her trade"),
        S(11.5, 13, at="work", activity="talk", doing="with customers at the door"),
        S(13, 17, "work", doing="at her trade"),
        S(17, 18, at="front", activity="walk", to="front_end", doing="errands along the street"),
        S(18, 21.5, "home", doing="supper and the evening"), S(21.5, 24, "home", doing="asleep")],
    "domestic": [
        S(0, 4.75, "home", doing="asleep"), S(4.75, 6.5, "home", doing="the fires and the breakfast"),
        S(6.5, 8, at="yard", activity="work", doing="water, wood and the slops"),
        S(8, 10, "home", doing="the rooms"),
        S(10, 12, at="yard", activity="work", doing="scrubbing and washing in the yard"),
        S(12, 13.5, "home", doing="serving and clearing the dinner"),
        S(13.5, 15, at="front", activity="work", doing="sweeping and scouring the step"),
        S(15, 19, "home", doing="the kitchen and the supper"),
        S(19, 20, at="yard", activity="work", doing="the last water and the fires banked"),
        S(20, 24, "home", doing="asleep")],
    "laundress": [
        S(0, 5, "home", doing="asleep"), S(5, 6.5, "home", doing="the fire and the coppers"),
        S(6.5, 11.5, at="yard", activity="work", doing="washing at the tubs"),
        S(11.5, 12.5, "home", doing="dinner"),
        S(12.5, 16, at="yard", activity="work", doing="wringing, hanging and folding"),
        S(16, 18, "home", doing="ironing"),
        S(18, 19, at="front", activity="talk", doing="talking with a neighbour"),
        S(19, 24, "home", doing="supper and asleep")],
    "lad": [
        S(0, 5.5, "home", doing="asleep"), S(5.5, 6.5, "home", doing="breakfast"),
        S(6.5, 8, at="yard", activity="work", doing="wood, water and the beasts"),
        S(8, 11.5, "home", doing="lessons or work for the household"),
        S(11.5, 12.25, "home", doing="at dinner"),
        S(12.25, 14, at="front", activity="walk", to="front_end", doing="errands along the street"),
        S(14, 17, "home", doing="work for the household"),
        S(17, 18.5, at="yard", activity="work", doing="evening chores"),
        S(18.5, 21, "home", doing="supper"), S(21, 24, "home", doing="asleep")],
    "girl": [
        S(0, 5.5, "home", doing="asleep"), S(5.5, 7, "home", doing="helping with breakfast"),
        S(7, 8, at="yard", activity="work", doing="the hens and the garden"),
        S(8, 11.5, "home", doing="lessons, sewing and the house"),
        S(11.5, 12.75, "home", doing="helping with dinner"),
        S(12.75, 14, at="front", activity="talk", doing="talking with a friend at the door"),
        S(14, 17, "home", doing="sewing and the house"),
        S(17, 18, at="yard", activity="work", doing="fetching water"),
        S(18, 21, "home", doing="supper"), S(21, 24, "home", doing="asleep")],
    "child": [
        S(0, 7, "home", doing="asleep"), S(7, 9, "home", doing="breakfast and small chores"),
        S(9, 11.5, "home", doing="lessons, or minding the little ones"),
        S(11.5, 12.25, "home", doing="at dinner"),
        S(12.25, 13.75, at="front", activity="walk", to="front_end", doing="playing near home with a household adult"),
        S(13.75, 16, "home", doing="indoor play and chores"),
        S(16, 17, at="yard", activity="walk", to="yard_end", doing="playing by the house with a household adult"),
        S(17, 19.5, "home", doing="supper"), S(19.5, 24, "home", doing="asleep")],
}
# Roles whose day goes to their place of business; without one, it is their home.
AT_WORK = ("gentleman", "keeper", "tradesman", "woman_trade")


def winter(spans):
    """The same day, November to April: each spell outside half as long, the rest of it indoors at
    the place the spell was before (the work of the season is indoors)."""
    out = []
    for s in spans:
        if s.get("indoors"):
            out.append(dict(s))
            continue
        mid = round(s["from"] + (s["to"] - s["from"]) / 2, 2)
        where = "work" if s["at"] == "work" else "home"
        out += [dict(s, to=mid), S(mid, s["to"], where, doing="indoors out of the cold")]
    return out


def routines():
    rows = {}
    for k, spans in ROUTINES.items():
        rows[k] = [{"dates": {"months": [11, 12, 1, 2, 3, 4]}, "spans": winter(spans)}, {"spans": [dict(s) for s in spans]}]
        for v in rows[k]:
            prev = 0
            for s in v["spans"]:
                assert s["from"] == prev and s["to"] > s["from"], (k, s)
                prev = s["to"]
            assert prev == 24, k
    return rows


# ── places outside a door ───────────────────────────────────────────────────────────────────
STAND_M = 0.55
OUT_M = (0.9, 1.3, 1.8, 2.4, 3.0, 3.6)
SIDE_M = tuple(x / 2 for x in range(-5, 6))
WALK_M = (5.0, 3.5, 2.5)


def scene_rings(door_data):
    """Every standing 1835 building's walls, the fences of its lots (gates left open), and the
    stoops, mounting blocks and tie rails of the street fronts."""
    import prairie_barriers as pb
    import derive_doors_1812 as d1812
    rings = []
    for f in sorted((ROOT / "data/sidecars/1835").glob("*.json")):
        try:
            sc = json.loads(f.read_text())
        except ValueError:
            continue
        poly = (sc.get("footprint") or {}).get("polygon") if isinstance(sc, dict) else None
        pl = sc.get("placement") if isinstance(sc, dict) else None
        if poly and len(poly) >= 3 and pl and pl.get("vertical_anchor") != "water":
            ring = [d1812.to_world(float(u), float(v), pl) for u, v in poly]
            # A palisade's footprint is the ground it encloses; only its line is in the way.
            rings.append(ring + [ring[0]] + ring[:0:-1] if "palisade" in sc.get("id", "") else ring)
    for f in sorted((ROOT / "data/enclosures").glob("*.json")):
        doc = json.loads(f.read_text())
        if not isinstance(doc, dict) or str(doc.get("scene")) != "1835":
            continue
        gates = [(o["at_local_enu_m"], float(o.get("width_m") or 1.0) / 2 + .35) for o in doc.get("openings") or [] if o.get("at_local_enu_m")]
        for run in doc.get("runs") or []:
            path = run.get("path_local_enu_m") or []
            for a, b in zip(path, path[1:]):
                L = math.dist(a, b)
                k = max(1, int(L / .5))
                piece = []
                for i in range(k + 1):
                    q = (a[0] + (b[0] - a[0]) * i / k, a[1] + (b[1] - a[1]) * i / k)
                    if any(math.dist(q, g) < r for g, r in gates):
                        if len(piece) > 1:
                            rings.append(piece + piece[-2:0:-1])
                        piece = []
                    else:
                        piece.append(q)
                if len(piece) > 1:
                    rings.append(piece + piece[-2:0:-1])
    for row in door_data["structures"] + door_data.get("barriers", []):
        rings += pb.rings_from_plan(row.get("barrier"), row["placement"])
    return pb.Rings(rings)


def off_the_step(door, rings):
    """Where one coming out of `door` is clear of its stoop or steps (a stoop, a mounting block, a
    porch the model builds before it): the first place straight out from its answering place
    that stands a body's width off them, or None within 4 m."""
    angle = math.radians(door["outward_deg"])
    de, dn = math.sin(angle), math.cos(angle)
    e, n = door["step"]["local_e"], door["step"]["local_n"]
    for k in range(41):
        q = (round(e + de * k / 10, 2), round(n + dn * k / 10, 2))
        if rings.clear_point(q, .2):
            return q
    return None


def before_door(pid, key, door, rings, out_m=OUT_M, walk=True):
    """A clear place before `door` (and the far end of a walk along the frontage from it): the
    seeded first choice where it is clear, else the nearest clear one; None if the front has none."""
    angle = math.radians(door["outward_deg"])
    de, dn = math.sin(angle), math.cos(angle)
    base = off_the_step(door, rings)
    if base is None:
        return None
    side = (draw(pid, key + ":side") - .5) * 3
    pt = lambda o, s: (round(base[0] + o * de + s * dn, 2), round(base[1] + o * dn - s * de, 2))
    sides = sorted({round(side, 6), *SIDE_M}, key=lambda s: (abs(s - side), s))
    first = 1 if draw(pid, key + ":sign") < .5 else -1
    for o in out_m:
        for s in sides:
            at = pt(o, s)
            if not rings.clear_point(at, STAND_M) or not rings.clear_leg(base, at, .15):
                continue
            if not walk:
                return at, None
            for length in WALK_M:
                for sign in (first, -first):
                    end = (round(at[0] + sign * length * dn, 2), round(at[1] - sign * length * de, 2))
                    if rings.clear_point(end, STAND_M) and rings.clear_leg(at, end, .15):
                        return at, end
            return at, None
    return None


def beside_house(pid, sc, door, rings):
    """A clear place beside or behind the house (a side or the back, 1-3 m out from its wall),
    reached from the door's step in a straight clear line, and a few paces' walk from there."""
    import derive_doors_1812 as d1812
    poly = [tuple(map(float, q)) for q in sc["footprint"]["polygon"]]
    pl = sc["placement"]
    step = off_the_step(door, rings)
    if step is None:
        return None
    cands = []
    for a, b in zip(poly, poly[1:] + poly[:1]):
        L = math.dist(a, b)
        if L < 1:
            continue
        along = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
        normal = (along[1], -along[0])
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        if d1812.inside((mid[0] + normal[0] * .3, mid[1] + normal[1] * .3), poly):
            normal = (-normal[0], -normal[1])
        for t in (.5, .25, .75):
            for o in (1.2, 1.8, 2.6):
                u, v = a[0] + (b[0] - a[0]) * t + normal[0] * o, a[1] + (b[1] - a[1]) * t + normal[1] * o
                e, n = d1812.to_world(u, v, pl)
                cands.append((round(e, 2), round(n, 2)))
    cands.sort(key=lambda q: draw(pid, f"yard:{q[0]}:{q[1]}"))
    for at in cands:
        if math.dist(at, step) < 2.0 or not rings.clear_point(at, STAND_M) or not rings.clear_leg(step, at, .15):
            continue
        end = None
        for k in range(8):
            ang = 2 * math.pi * (k + draw(pid, "yardwalk")) / 8
            q = (round(at[0] + 2.5 * math.sin(ang), 2), round(at[1] + 2.5 * math.cos(ang), 2))
            if rings.clear_point(q, STAND_M) and rings.clear_leg(at, q, .15):
                end = q
                break
        return at, end
    return None


def bearing(a, b):
    return round((math.degrees(math.atan2(b[0] - a[0], b[1] - a[1])) + 360) % 360, 1)


# ── the town ────────────────────────────────────────────────────────────────────────────────
def roster():
    """Everyone present on 1 July 1835 with a roof: (row, person record, home, work)."""
    rows = read("data/sidecars/1835/people.json")["people"]
    seats = {s["household"]: s for s in read("data/reconstruction/1835_housing_seats.json")["seats"]}
    # A house the business register places at a standing building is the place of business of
    # its proprietors, partners and staff, where their own card names none (data/businesses/).
    trade_at = {}
    for f in sorted((ROOT / "data/businesses").glob("biz_*.json")):
        biz = json.loads(f.read_text())
        at = next((x["structure_id"] for x in biz.get("locations") or [] if x.get("structure_id")), None)
        if not biz.get("present_at_scene_date") or not at:
            continue
        for x in (biz.get("proprietors") or []) + (biz.get("partners") or []) + (biz.get("staff") or []):
            if x.get("person_id"):
                trade_at.setdefault(x["person_id"], at)
    files = {}
    out = []
    for row in rows:
        if row["present"] != "present":
            continue
        home = row.get("lives_at") or (seats.get(row["household"]) or {}).get("place")
        if not home:
            continue
        if row["file"] not in files:
            files[row["file"]] = read("data/residents/" + row["file"])
        per = next(p for p in files[row["file"]]["persons"] if p["id"] == row["id"])
        work = row.get("works_at") or trade_at.get(row["id"])
        work = work if work and work != home else None
        out.append((row, per, home, work, files[row["file"]]))
    return out


def generate():
    import derive_doors_scene as doors_tool
    people = roster()
    # The doors of every home and place of business named, read off their models.
    named = {x[2] for x in people} | {x[3] for x in people if x[3]}
    previous = doors_tool.wheres
    # (Never from yesterday's inside_1835.json, which this writes.)
    doors_tool.wheres = lambda scene, inside_file=True: (previous(scene, False) | named) if scene == "1835" else previous(scene, inside_file)
    try:
        door_all, _ = doors_tool.derive("1835")
    finally:
        doors_tool.wheres = previous
    byhome = {x["structure"]: x["doors"] for x in door_all["structures"]}
    sidecars = {}
    rings = scene_rings(door_all)

    def sidecar(sid):
        if sid not in sidecars:
            sidecars[sid] = read(f"data/sidecars/1835/{sid}.json")
        return sidecars[sid]

    drawn = {}
    for f in sorted((ROOT / "data/humans/instances/1835").glob("hi_*.json")):
        inst = json.loads(f.read_text())
        if inst.get("person_id") in DRAWN:
            drawn[inst["person_id"]] = inst["appearance"]["asset_id"]
    by_household = {}
    for row, per, home, work, hh in people:
        by_household.setdefault(row["household"], []).append(per)
    entries, care, dresses, looks = [], [], {}, {}
    skipped = {"no door to their home": 0, "no clear ground before their door": 0}
    fronts = {}   # (door id) -> how many stand before it, to spread a crowded house's people
    for row, per, home, work, hh in sorted(people, key=lambda x: x[0]["id"]):
        pid = row["id"]
        sex = sex_of(per, row)
        age = age_of(pid, per)
        com = row.get("community") or ""
        if pid in drawn:
            looks[pid] = looks_for(pid, sex, age, com, drawn[pid])
            continue
        if home not in byhome:
            skipped["no door to their home"] += 1
            continue
        kind = household_kind(by_household[row["household"]])
        role = role_of(row, per, sex, age, kind)
        dress = dress_for(pid, role, sex, com, age)
        asset = dress["asset"]
        door = byhome[home][0]
        prov = {"sources": per.get("sources") or []}
        if role == "infant":
            care.append({"person": pid, "name": row["name"], "home": home, "door": door["id"], "ask_order": 15, "care_only": True,
                         "age_1835": age, "provenance": prov})
            continue
        work_door = byhome[work][0] if role in AT_WORK and work in byhome else None
        work = work if work_door else None
        front = before_door(pid, "front", door, rings)
        if front is None:
            skipped["no clear ground before their door"] += 1
            continue
        yard = beside_house(pid, sidecar(home), door, rings) or front
        wk = before_door(pid, "work", work_door, rings) if work_door else None
        if work_door and wk is None:
            work, work_door = None, None
        pts = {"front": [*front[0], door["outward_deg"]], "yard": [*yard[0], bearing(yard[0], (door["step"]["local_e"], door["step"]["local_n"]))]}
        if front[1]:
            pts["front_end"] = list(front[1])
        if yard[1]:
            pts["yard_end"] = list(yard[1])
        if wk:
            pts["work"] = [*wk[0], work_door["outward_deg"]]
            if wk[1]:
                pts["work_end"] = list(wk[1])
        entry = {"person": pid, "name": row["name"], "home": home, "door": door["id"], "asset_id": asset,
                 "ask_order": {"head": 10, "wife": 12, "partner": 12}.get(row["relationship"], 20 if age >= 18 else 25),
                 "routine": role, "shift": round((int(draw(pid, "shift") * 7) - 3) * .25, 2), "points": pts}
        if work:
            entry["work"] = work
            entry["work_door"] = work_door["id"]
        if prov["sources"]:
            entry["provenance"] = prov
        if age < 12:
            entry["age_1835"] = age
        entries.append(entry)
        dresses[pid] = {k: dress[k] for k in ("colours", "hide", "worn") if dress.get(k)}
        looks[pid] = looks_for(pid, sex, age, com, asset)
    # A child out of doors is kept company by the household's grown-ups (never a claim of
    # parentage): the women of the house first, then the head, then anyone grown under the roof.
    grown = {}
    for e in entries:
        if "age_1835" not in e:
            grown.setdefault(e["home"], []).append(e)
    rel = {x[0]["id"]: x[0] for x in people}
    for e in entries + care:
        if "age_1835" not in e or e["age_1835"] >= 12:
            continue
        hh = rel[e["person"]]["household"]
        adults = sorted(grown.get(e["home"], []), key=lambda a: (0 if rel[a["person"]]["household"] == hh else 1,
                        0 if a["routine"] in ("woman", "lady", "domestic") else 1, a["person"]))
        if not adults:
            if not e.get("care_only"):
                e["routine"] = "child"
            continue
        e["caregivers"] = [a["person"] for a in adults[:4]]
        if not e.get("care_only"):
            e["supervised"] = True
    # Only the buildings someone in the file goes into keep their doors in doors_1835.json, so
    # derive_doors_scene.py --check, which reads the homes and places of business back out of
    # this file, reproduces it.
    used = {e["home"] for e in entries + care} | {e["work"] for e in entries if e.get("work")}
    doors_tool.wheres = lambda scene, inside_file=True: (previous(scene, False) | used) if scene == "1835" else previous(scene, inside_file)
    try:
        door_data, problems = doors_tool.derive("1835")
    finally:
        doors_tool.wheres = previous
    if problems:
        raise SystemExit("doors_1835: " + "; ".join(problems))
    # Expected by the human-days.js template reader (`expandInside`).
    inside = {
        "format": "chicago4d_inside_only_v2", "ticket": TICKET, "generated_by": "tools/town_people_1835.py",
        "doc": ("Everyone of the 1835 town present on 1 July and under a roof with a door: built near the visitor "
                "at an hour their day has them out, or on a door call. Each person's day is `routine` (one of "
                "`routines`, a summer and a winter day) moved by their `shift` in hours; `where` 'home' is their "
                "home, 'work' their place of business; `at` names one of their `points` ([local_e, local_n, "
                "heading_deg]); `to_point` the far end of a walk. Infants are in household care and asked after "
                "at the door. renderers/web/js/human-days.js expandInside."),
        "provenance": {"grade": "reconstructed", "ticket": TICKET, "liberty": LIBERTY,
                       "basis": ("Identity, household and presence from the household record and the 1835 housing deal; "
                                 "the day, the places outside the door, the body and the clothes are reconstructed.")},
        "counts": {"people": len(entries), "in_care": len(care), "at_a_place_of_business": sum(1 for e in entries if e.get("work")),
                   "left_out": skipped},
        "routines": routines(), "people": entries, "care": care,
    }
    dress_doc = {"format": "chicago4d_human_dress_v1", "scene": "1835", "ticket": TICKET, "generated_by": "tools/town_people_1835.py",
                 "liberty": LIBERTY, "persons": dresses}
    looks_doc = {"format": "chicago4d_human_looks_set_v1", "scene": "1835", "ticket": TICKET, "generated_by": "tools/town_people_1835.py",
                 "liberty": LIBERTY, "basis": LOOKS_BASIS, "persons": looks}
    return {INSIDE: inside, DOORS: json.dumps(door_data, indent=1) + "\n", DRESS: dress_doc, LOOKS: looks_doc}


def render(rel, data):
    if isinstance(data, str):
        return data
    if rel == INSIDE:
        # One person a line: a diff reads person by person, and the file stays small.
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
    bad = []
    outputs = generate()
    for rel, data in outputs.items():
        text = render(rel, data)
        json.loads(text)
        path = ROOT / rel
        if args.check:
            if not path.exists() or path.read_text() != text:
                bad.append(rel)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
    if bad:
        raise SystemExit("FAIL 1835 town people outputs stale: " + ", ".join(bad) + " — run python3 tools/town_people_1835.py")
    c = outputs[INSIDE]["counts"]
    print(f"ok 1835 town people {'reproduce' if args.check else 'written'}: {c['people']} people, {c['in_care']} in care, "
          f"{c['at_a_place_of_business']} with a place of business; left out {c['left_out']}")


if __name__ == "__main__":
    main()
