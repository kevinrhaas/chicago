#!/usr/bin/env python3
"""A resident's trades, professions and offices as DATED PLURAL ROLES (T-1229, of T-1145).

    python3 tools/derive_resident_roles.py             what the cards would carry, read out
    python3 tools/derive_resident_roles.py --write     write roles[] and the 1835 view
    python3 tools/derive_resident_roles.py --check     it re-derives, and nothing has drifted
    python3 tools/derive_resident_roles.py --self-test the rules below, held over fixtures

WHY A SINGULAR FIELD IS THE DEFECT. `persons[].occupation` holds ONE trade and one
confidence, so a man printed as a candle manufacturer in 1833, a brickmaker in 1839 and a
school inspector in the same register can only be one of them on his own card. Daniel
Elston is the fixture the owner named: the card showed `soap_and_candle_maker` and graded
it an attested 1835 occupation, which is two errors in one field — it erased four other
roles, and it dated the surviving one to a year no source cited for it describes.

WHAT THIS TOOL ASSERTS, and it is three sentences.

  1. `roles[]` is CANONICAL. Every role the card's own evidence carries becomes a row
     naming a controlled role, the kind of role it is, the bound its evidence permits,
     how it was dated, its confidence and the sources it rests on. Two roles are two
     rows; a role whose date is unknown stays unknown and is never widened to 1835.

  2. `occupation` is a GENERATED COMPATIBILITY VIEW of the roles that actually cover
     1835-07-01 — the field the renderer, the people index and the scene compiler still
     read. Where two roles cover the day, both stand in `roles[]` and
     `occupation.roles_at_scene_date` names both, so the singular field can no longer
     decide which of a man's two trades the town is told about.

  3. A ROLE THAT DOES NOT REACH 1835 CANNOT FILL THE 1835 FIELD. That is T-0991's
     repair, and it is made here rather than by hand: the six trades
     `tools/audit_scene_window_trades.py` still reports keep their printing as a dated
     pre-scene role, the 1835 field falls to `none_recorded`, and
     `occupation.withdrawn_from_scene_date` carries the audit's own verdict and note so
     the withdrawal states its reason on the card rather than only in a ledger.

THE DATE RULE IS THE AUDIT'S, DELIBERATELY. A role derived from the 1835 block is bounded
by the `describes_date` spans of the sources that block cites, and it "covers" the scene
date on exactly `audit_scene_window_trades.covers_scene` — the span names a year range
containing 1835. That is a bound from the SOURCE and not a claim about the man, which is
why `dated_by` says which of the two a row is and why `precision` can say `source_span`.
Widening it would quietly re-assert what T-0837's write gate refuses; narrowing it would
disagree with the audit this repair is measured by, and a second opinion on that rule is
the one thing a compatibility view must not have.

AND SINCE T-1404, EVERY ROLE SAYS WHETHER THE TRADE HAD PREMISES OF ITS OWN. `premises`
is read off `data/businesses/rulings/premises_rulings.json`, one ruling per occupation of the
closed vocabulary, and it is the half of T-1182's clause 3 that is NOT a business record:
a clerk, a labourer, a teamster or a boatman kept no house of trade, so the answer to
"where did this man work?" is `no_fixed_premises` on the role itself, with the ruling's
basis saying where the work was done and which ticket owes the workplace link. An
`own_premises` role says the trade implies a house, and
tools/complete_inwindow_trades.py raises one for every keeper who holds none. A role
whose printing has not been ruled into the vocabulary (`role: null`) carries `premises:
null`, because a trade nobody has adjudicated is not a trade this can answer for.

WHAT THIS TICKET DOES NOT READ. The newspaper gazetteer's `persons[].occupations[]`, the
1839 directory and civic-register crosswalks and the 1843/1844 identity-master appearances
are T-1254, together with each role's stated place and employer and the migration table.
The people view's dated timeline is T-1255. This tool reads the CARD, and only the card.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
HOUSEHOLDS = DATA / "residents" / "households"
SOURCES = DATA / "sources"
INDEX = DATA / "residents" / "index.json"
PREMISES_RULINGS = DATA / "businesses" / "rulings" / "premises_rulings.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_scene_window_trades import VERDICTS, covers_scene  # noqa: E402

SCENE_DATE = "1835-07-01"
ABSENT = "none_recorded"
GENERATOR = "tools/derive_resident_roles.py"
TICKET = "T-1229"

# The grades that make a role a CLAIM, and so the grades that may fill the 1835 view.
# Identical to the audit's, and for the same reason: `reconstructed` is this dataset's
# word for a figure the reconstruction supplies rather than a source.
CLAIMING = ("attested", "documented", "inferred")

ROLE_KINDS = ("trade", "profession", "office", "employment", "business_interest")
ROLE_PRECISION = ("day", "month", "year", "source_span", "unknown")
DATED_BY = ("source_describes_date", "printing_year", "stated_date", "undated")

# WHICH KIND A CONTROLLED ROLE IS. The residents vocabulary has never separated these —
# `postmaster` and `blacksmith` sit in one alphabetical list — and T-1145 needs the
# separation because an office and a trade are held on different evidence and, from
# T-1254, by different bodies. The two sets below are enumerated rather than matched:
# a fuzzy rule is how every milliner in this corpus once compiled as a grain MILLER
# (T-0376). Anything not named here is a `trade`, and `--self-test` refuses a name in
# either set that the manifest vocabulary does not carry.
OFFICES = frozenset({
    "county_clerk", "fire_warden", "indian_agent", "justice_of_the_peace",
    "land_office_receiver", "land_office_register", "lighthouse_keeper",
    "militia_officer", "postmaster", "public_administrator", "sheriff", "sub_agent",
    "town_assessor", "town_clerk", "town_president",
})
PROFESSIONS = frozenset({
    "army_officer", "army_surgeon", "attorney", "barber_surgeon", "chaplain",
    "dancing_master", "dentist", "editor", "engineer", "interpreter", "minister",
    "music_teacher", "physician", "priest", "schoolteacher", "surveyor",
})


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dumps(doc) -> str:
    return json.dumps(doc, indent=1, ensure_ascii=False) + "\n"


def describes_date(sid: str) -> str:
    path = SOURCES / f"{sid}.json"
    if not path.exists():
        return ""
    try:
        return str(read_json(path).get("describes_date") or "")
    except Exception:
        return ""


def kind_of(role: str) -> str:
    if role in OFFICES:
        return "office"
    if role in PROFESSIONS:
        return "profession"
    return "trade"


def _ends(span: str) -> tuple[str, str]:
    """The two ends of a `describes_date`, as the source writes them.

    `1833-11/1835-08` is a slashed range, `1673-1857` a hyphenated one of bare years,
    `1839` a single year and `1833-11` a single month. Anything this cannot read is an
    unknown bound and says so rather than guessing at one.
    """
    span = (span or "").strip()
    if not span:
        return "", ""
    if "/" in span:
        a, b = span.split("/", 1)
        return a.strip(), b.strip()
    parts = span.split("-")
    if len(parts) == 2 and all(p.isdigit() and len(p) == 4 for p in parts):
        return parts[0], parts[1]
    if span.replace("-", "").isdigit() and len(parts) <= 2:
        return span, span
    return "", ""


def _precision(frm: str, to: str) -> str:
    if not frm or not to:
        return "unknown"
    if frm != to:
        return "source_span"
    return {4: "year", 7: "month", 10: "day"}.get(len(frm), "source_span")


def _bound(sources: list[str]) -> tuple[str, str, str]:
    """The widest bound the cited sources permit, and how precise it is."""
    ends = [_ends(describes_date(s)) for s in sources]
    starts = sorted(a for a, _ in ends if a)
    finishes = sorted(b for _, b in ends if b)
    if not starts or not finishes:
        return "", "", "unknown"
    frm, to = starts[0], finishes[-1]
    return frm, to, _precision(frm, to)


def scene_role(occ: dict, person_id: str, person: dict | None = None) -> dict | None:
    """The role the 1835 `occupation` block is standing on, whatever year it is about.

    ONCE A TRADE IS WITHDRAWN THE BLOCK NO LONGER NAMES IT, so the withdrawal is read
    first. Without that this tool is not idempotent: it would withdraw a trade on one
    run and then, finding `none_recorded`, delete the role carrying it on the next —
    losing the very evidence the withdrawal was written to preserve.
    """
    if isinstance(occ.get("promoted_from_roles"), dict):
        # A PROMOTED BLOCK IS NOT A SOURCE, IT IS THIS TOOL'S OWN VIEW (T-1299). Its value
        # and its citations came off the role rows that filled it, and those rows are
        # still in `roles[]`. Reading the block back would emit a second row asserting the
        # same trade out of the same printing, with a bound read off the source's
        # `describes_date` rather than the run of the person's own mentions — the same
        # non-idempotence the withdrawal below is read first to avoid.
        return None
    withdrawn = occ.get("withdrawn_from_scene_date")
    if isinstance(withdrawn, dict) and withdrawn.get("value"):
        role, confidence = withdrawn.get("value"), withdrawn.get("confidence")
    else:
        role, confidence = occ.get("value"), occ.get("confidence")
    if not role or role == ABSENT:
        return None
    sources = [s for s in (occ.get("sources") or []) if s]
    if not sources:
        # A BLOCK WITH NO SOURCES IS NOT AN ASSERTION, IT IS A VIEW. Since T-1254 the
        # external evidence can promote a trade INTO this field, and that write leaves it
        # citing nothing of its own — the citations are on the role rows that put it
        # there. Reading it back as a role would launder an inferred press reading into a
        # card-block assertion, and would emit a sourceless row the gate refuses anyway.
        return None
    frm, to, precision = _bound(sources)
    covers = any(covers_scene(describes_date(s)) for s in sources)
    verdict, ledger_note = VERDICTS.get(person_id, (None, None))
    row = {
        "role": role,
        "kind": kind_of(role),
        "as_printed": None,
        "from": frm or None,
        "to": to or None,
        "precision": precision,
        "dated_by": "source_describes_date" if sources else "undated",
        "covers_scene_date": covers,
        "fills_scene_view": covers,
        "confidence": confidence,
        "sources": sources,
        "claim": None,
        "place": NOT_STATED,
        "employer_or_body": FOLD.get(role, (None, None, None))[2] or NOT_STATED,
        "note": None,
    }
    if covers:
        row["note"] = (
            "THE BOUND IS THE SOURCE'S, NOT THE MAN'S. This role is carried by the card's "
            "1835 occupation block and is dated by what the cited source or sources are "
            "ABOUT, which is why `precision` can be no better than the span they cover. "
            "The span reaches 1835, so this role stands in the scene-date view. The "
            "printing the trade was read off is not on the card and is fetched by T-1254."
            + corroborator_ruling(sources, person))
    else:
        row["note"] = (
            "A DATED ROLE THAT DOES NOT REACH THE SCENE DATE (T-0991, withdrawn from the "
            "1835 field by " + GENERATOR + "). No source cited for this trade describes "
            "1835, so it is retained here with the bound its evidence permits and the "
            "1835 compatibility view reads `" + ABSENT + "` instead. "
            "tools/audit_scene_window_trades.py's verdict is `" + (verdict or "unadjudicated")
            + "`" + (": " + ledger_note if ledger_note else "."))
    return row


def later_role(occ: dict) -> dict | None:
    """T-0693's `later_occupation` pointer, as the dated role it has always been."""
    later = occ.get("later_occupation")
    if not isinstance(later, dict):
        return None
    printed = (later.get("value") or "").strip()
    year = str(later.get("describes_date") or "").strip()
    if not printed:
        return None
    return {
        "role": None,
        "kind": "trade",
        "as_printed": printed,
        "from": year or None,
        "to": year or None,
        "precision": "year" if year else "unknown",
        "dated_by": "printing_year" if year else "undated",
        "covers_scene_date": False,
        "fills_scene_view": False,
        "confidence": later.get("confidence"),
        "sources": [s for s in (later.get("sources") or []) if s],
        "claim": None,
        "place": NOT_STATED,
        "employer_or_body": NOT_STATED,
        "note": (
            "A TRADE PRINTED AGAINST THIS NAME IN A LATER VOLUME, and this row says which "
            "year rather than leaving it to a pointer (T-0693, carried here by " + GENERATOR
            + "). `role` is null because the directory's wording has not been adjudicated "
            "into the closed vocabulary — the printing is what the source gives and the "
            "printing is what is kept. T-1254 is where the controlled term is ruled on. It "
            "is not a claim about " + SCENE_DATE + " and never becomes one: the year is "
            + (year or "not stated") + "."),
    }


# --------------------------------------------------------------------------
# T-1254 (of T-1145): THE EXTERNAL STRUCTURED ROLE EVIDENCE
#
# Everything above reads the CARD. The evidence below is held in the research tree —
# the newspaper gazetteer, the 1839 city register, and the 1843 and 1844 directory
# crosswalks — and each of those files has already done the hard half: it says which
# resident card an entry belongs to, and on what rule. This section carries the ROLE out
# of those records and onto the person, with the date the record permits, the place it
# states and the body or firm it names.
#
# IT IS READ THROUGH THE CARD WHEREVER THE CARD POINTS. The gazetteer is reached by the
# person's own `press_evidence[].record_id`, which is the identity match the resident
# programme made and graded; this tool does not re-match names. The three directory
# crosswalks key their matches by `person_id` directly, which is the same thing said in
# the other direction.
#
# THE DATE RULE, PER SOURCE, and each is the tightest bound the record actually gives:
#
#   gazetteer   The person's mentions are dated ISSUES, so the bound is `first_seen` to
#               `last_seen` and `dated_by` is `stated_date`. The scene date is covered
#               when it falls INSIDE that run — containment, not the year-overlap rule
#               the card's own block uses. That is not a second opinion on the card's
#               rule: the card cites a SOURCE and can be dated no better than the run of
#               that source, while here the record names the days, and a rule may be
#               tightened by better evidence without being contradicted.
#
#   1843/1844   A trade printed in a directory five years after the scene. The bound is
#               the volume's year, `dated_by` is `printing_year`, and `covers_scene_date`
#               is FALSE always. This is the back-projection T-1145 exists to refuse.
#
#   1839        The city register is a retrospective table set in 1876. Its own crosswalk
#               says what a match may carry: a later office is corroboration of CONTINUED
#               RESIDENCE, never an 1835 fact, and only a row whose term covers the scene
#               (the 1834 sheriffs' rows) carries `reaches_scene`. That flag is honoured
#               here, and then only when the volume is one the card's own grade stands
#               on — which is the same rule tools/validate.py applies from the outside.
#
# WHAT IS NOT PARSED. `place` and `employer_or_body` are taken from the STRUCTURED fields
# the research records already carry — the directories' address and place-of-business
# columns, the register's `body`, and the office bodies named in the fold table below.
# The printed occupation lines of 1843 and 1844 also carry firms and addresses inside the
# prose ("clerk, Charles Walker & Co", "(sign of the three hats), hat, cap, and fur
# manufacturer, 10S Lake Street"), and this tool does NOT dig them out with a pattern. A
# fuzzy rule is how every milliner in this corpus once compiled as a grain MILLER
# (T-0376); a prose firm gets `not_stated` and keeps its wording in `as_printed`, where
# the business band (T-1180 onward) can rule on it.

NOT_STATED = "not_stated"

# THE FOLD, and it is a table because it has to be arguable. The left side is the
# wording a source printed; the right side is (controlled role or None, kind or None,
# employer/body or None). A printing that names TWO trades ("baker and confectioner",
# "watchmaker and jeweller", "saddler and harness maker") folds to NEITHER — picking one
# is a silent refusal of the other — and a printing with no controlled word ("capitalist",
# "ventriloquist", "botanic practitioner") folds to nothing at all. Both leave `role`
# null with the printing intact, and both are counted as such in the migration table.
# Anything absent from this table is unresolved, never guessed.
FOLD: dict[str, tuple[str | None, str | None, str | None]] = {
    # --- offices and public bodies -------------------------------------------------
    "President, Board of Trustees of the Town of Chicago": ("town_president", "office", "town_of_chicago"),
    "president of the board of trustees": ("town_president", "office", "town_of_chicago"),
    "town clerk": ("town_clerk", "office", "town_of_chicago"),
    "clerk of the board of trustees": ("town_clerk", "office", "town_of_chicago"),
    "secretary, Board of Trustees": (None, None, "town_of_chicago"),
    "secretary to the town trustees": (None, None, "town_of_chicago"),
    "school trustee": (None, None, "town_of_chicago"),
    "judge of election": (None, None, "town_of_chicago"),
    "county clerk": ("county_clerk", "office", "cook_county"),
    # --- the 1839 city register's own office codes, read with their underscores out ---
    "fire warden": ("fire_warden", "office", None),
    "sheriff of cook county": ("sheriff", "office", "cook_county"),
    "alderman": (None, None, None),
    "school inspector": (None, None, None),
    "mayor of chicago": (None, None, None),
    "collector": (None, None, None),
    "treasurer": (None, None, None),
    "sealer of weights and measures": (None, None, None),
    "Sheriff of Cook County": ("sheriff", "office", "cook_county"),
    "Public Administrator of Cook county": ("public_administrator", "office", "cook_county"),
    "public administrator": ("public_administrator", "office", "cook_county"),
    "justice of the peace": ("justice_of_the_peace", "office", "cook_county"),
    "justice": ("justice_of_the_peace", "office", "cook_county"),
    "deputy surveyor of Cook County": ("surveyor", "profession", "cook_county"),
    "clerk of the circuit court": (None, None, "cook_county_circuit_court"),
    "circuit judge": (None, None, "state_of_illinois"),
    "Judge of the fifth Judicial Circuit": (None, None, "state_of_illinois"),
    "Secretary of State of Illinois": (None, None, "state_of_illinois"),
    "railroad commissioner": (None, None, "state_of_illinois"),
    "postmaster": ("postmaster", "office", "united_states_post_office"),
    "postmaster general": (None, None, "united_states_post_office"),
    "Receiver of Public Moneys": ("land_office_receiver", "office", "united_states_land_office"),
    "receiver, United States Land Office": ("land_office_receiver", "office", "united_states_land_office"),
    "register land office": ("land_office_register", "office", "united_states_land_office"),
    "Indian agent": ("indian_agent", "office", "united_states_indian_department"),
    "indian agent": ("indian_agent", "office", "united_states_indian_department"),
    "U.S. light-house keeper": ("lighthouse_keeper", "office", "united_states_treasury"),
    "Secretary of War": (None, None, "united_states_war_department"),
    "deputy collector and inspector of Port of Chicago": (None, None, "united_states_treasury"),
    "deputy-collector and inspector Port of Chicago": (None, None, "united_states_treasury"),
    # --- the army and the militia --------------------------------------------------
    "army officer": ("army_officer", "profession", "united_states_army"),
    "Lieutenant, U.S. Army": ("army_officer", "profession", "united_states_army"),
    "Major, 5th Infantry, commanding the post": ("army_officer", "profession", "united_states_army"),
    "post adjutant": (None, None, "united_states_army"),
    "acting commissary of subsistence": (None, None, "united_states_army"),
    "assistant commissary of subsistence": (None, None, "united_states_army"),
    "soldier": ("soldier", "trade", "united_states_army"),
    "militia officer": ("militia_officer", "office", None),
    "colonel of the Cook county regiment": ("militia_officer", "office", "cook_county_regiment"),
    # --- the professions -----------------------------------------------------------
    "attorney": ("attorney", "profession", None),
    "attorney at law": ("attorney", "profession", None),
    "counsellor at law": ("attorney", "profession", None),
    "physician": ("physician", "profession", None),
    "dentist": ("dentist", "profession", None),
    "surgeon dentist": ("dentist", "profession", None),
    "surveyor": ("surveyor", "profession", None),
    "minister": ("minister", "profession", None),
    "Baptist pastor": ("minister", "profession", None),
    "schoolteacher": ("schoolteacher", "profession", None),
    "schoolmaster": ("schoolteacher", "profession", None),
    "botanic practitioner": (None, None, None),
    # --- the trades ----------------------------------------------------------------
    "auctioneer": ("auctioneer", "trade", None),
    "baker": ("baker", "trade", None),
    "blacksmith": ("blacksmith", "trade", None),
    "bookseller": ("bookseller", "trade", None),
    "boot and shoe maker": ("shoemaker", "trade", None),
    "shoemaker": ("shoemaker", "trade", None),
    "brickmaker": ("brickmaker", "trade", None),
    "patent press-brick maker": ("brickmaker", "trade", None),
    "patent press brickmaker": ("brickmaker", "trade", None),
    "builder": ("builder", "trade", None),
    "butcher": ("butcher", "trade", None),
    "carpenter": ("carpenter", "trade", None),
    "carriage maker": ("carriage_maker", "trade", None),
    "clothier": ("clothier", "trade", None),
    "confectioner": ("confectioner", "trade", None),
    "cooper": ("cooper", "trade", None),
    "dressmaker": ("dressmaker", "trade", None),
    "dress maker": ("dressmaker", "trade", None),
    "dry goods merchant": ("dry_goods_merchant", "trade", None),
    "farmer": ("farmer", "trade", None),
    "founder": ("founder", "trade", None),
    "grocer": ("grocer", "trade", None),
    "wholesale grocer": ("grocer", "trade", None),
    "harbour agent": ("harbour_agent", "employment", None),
    "hardware merchant": ("hardware_merchant", "trade", None),
    "hatter": ("hatter", "trade", None),
    "hotel keeper": ("hotel_keeper", "trade", None),
    "insurance agent": ("insurance_agent", "trade", None),
    "fire insurance agent": ("insurance_agent", "trade", None),
    "jeweller": ("jeweller", "trade", None),
    "laborer": ("labourer", "trade", None),
    "land agent": ("land_agent", "trade", None),
    "house and lot agent": ("land_agent", "trade", None),
    "liquor seller": ("liquor_dealer", "trade", None),
    "wine and liquor merchant": ("liquor_dealer", "trade", None),
    "liveryman": ("livery_stable_keeper", "trade", None),
    "lumber merchant": ("lumber_merchant", "trade", None),
    "mason": ("mason", "trade", None),
    "merchant": ("merchant", "trade", None),
    "commission merchant": ("forwarding_and_commission", "trade", None),
    "commission and forwarding merchant": ("forwarding_and_commission", "trade", None),
    "forwarding and commission merchant": ("forwarding_and_commission", "trade", None),
    "printer": ("printer", "trade", None),
    "provision dealer": ("provision_dealer", "trade", None),
    "provision store": ("provision_dealer", "trade", None),
    "saddler": ("saddler", "trade", None),
    "sailor": ("seaman", "trade", None),
    "shipcarpenter": ("ship_carpenter", "trade", None),
    "shipwright": ("ship_carpenter", "trade", None),
    "silversmith": ("silversmith", "trade", None),
    "speculator": ("speculator", "trade", None),
    "stationer": ("stationer", "trade", None),
    "stove dealer": ("stove_dealer", "trade", None),
    "stove and hollow ware dealer": ("stove_dealer", "trade", None),
    "tailor": ("tailor", "trade", None),
    "tavern keeper": ("tavern_keeper", "trade", None),
    "teamster": ("teamster", "trade", None),
    "tinsmith": ("tinsmith", "trade", None),
    "watchmaker": ("watchmaker", "trade", None),
    # --- printings that name TWO trades, and so fold to neither ---------------------
    "baker and confectioner": (None, None, None),
    "watchmaker and jeweller": (None, None, None),
    "saddler and harness maker": (None, None, None),
    "carpenter and builder": (None, None, None),
    "grocery and provisions": (None, None, None),
    "carpenter and wagon maker": (None, None, None),
    # --- printings with no controlled word ------------------------------------------
    "administratrix": (None, None, None),
    "appraiser": (None, None, None),
    "barber": (None, None, None),
    "book-keeper": (None, None, None),
    "cabinet maker": (None, None, None),
    "capitalist": (None, None, None),
    "caulker": (None, None, None),
    "cloak maker": (None, None, None),
    "contractor": (None, None, None),
    "daguerreotype": (None, None, None),
    "fancy store keeper": (None, None, None),
    "florist": (None, None, None),
    "habit maker": (None, None, None),
    "land owner": (None, None, None),
    "leather dealer": (None, None, None),
    "mechanic": (None, None, None),
    "newspaper agent": (None, None, None),
    "newspaper subscription agent": (None, None, None),
    "overseer of harbor": (None, None, None),
    "price reporter for the Chicago Democrat": (None, None, None),
    "retired printer": (None, None, None),
    "shopkeeper": (None, None, None),
    "steamboat owner": (None, None, None),
    "storekeeper": (None, None, None),
    "ventriloquist": (None, None, None),
    "water borer": (None, None, None),
}

RESEARCH = DATA / "research"
GAZETTEER = RESEARCH / "newspapers" / "gazetteer.json"
DIRECTORIES = RESEARCH / "directories"
REGISTER_1839 = DIRECTORIES / "fergus_1839_register_crosswalk_1835.json"
FERGUS_1843 = DIRECTORIES / "fergus_1843_crosswalk_1835.json"
NORRIS_1844 = DIRECTORIES / "norris_1844_crosswalk_1835.json"

MIGRATION_TABLE = ROOT / "docs" / "RESEARCH" / "roles-migration-2026-09.md"


def _fold(printed: str) -> tuple[str | None, str | None, str | None, str]:
    """(role, kind, employer, disposition) for one printed wording."""
    key = (printed or "").strip()
    if key not in FOLD:
        return None, None, None, "unresolved"
    role, kind, body = FOLD[key]
    if role is None:
        return None, None, body, "refused"
    return role, kind or kind_of(role), body, ("asserted" if role == key else "folded")


def _external_note(what: str, why: str) -> str:
    return what + " " + why


def _load(path: Path):
    return read_json(path) if path.exists() else None


def gazetteer_index() -> dict[str, dict]:
    doc = _load(GAZETTEER)
    if not doc:
        return {}
    return {p["id"]: p for p in doc.get("persons") or [] if p.get("id")}


def gazetteer_roles(person: dict, index: dict[str, dict]) -> list[dict]:
    """The trades the 1833-1835 press printed against this name, as dated roles.

    The gazetteer attaches `occupations[]` to a PERSON RECORD compiled across every
    mention, so no one string can be tied to one issue; the bound is therefore the run
    of the person's own mentions, which the record dates to the day. The grade is
    `inferred` and not `attested`, and that is the honest rung: the paper printed the
    trade against the name, and the resident programme's identity rule tied the name to
    this card, so the trade is inferred FOR THIS PERSON rather than stated OF him.
    """
    rows = []
    for ev in person.get("press_evidence") or []:
        record = index.get(ev.get("record_id") or "")
        if not record:
            continue
        source = ev.get("source")
        frm, to = record.get("first_seen") or "", record.get("last_seen") or ""
        covers = bool(frm and to and frm <= SCENE_DATE <= to)
        for printed in sorted(set(record.get("occupations") or [])):
            role, kind, body, disposition = _fold(printed)
            rows.append({
                "role": role,
                "kind": kind or "trade",
                "as_printed": printed,
                "from": frm or None,
                "to": to or None,
                "precision": _precision(frm, to),
                "dated_by": "stated_date" if frm else "undated",
                "covers_scene_date": covers,
                # T-1299: A PRESS READING THAT REACHES THE DAY STANDS IN THE FIELD. This
                # was `False` for every row while T-1254's other three derivers were
                # untaught — the row said its evidence reached 1 July 1835 and said in
                # the same breath that it did not count. All four agree now, so the two
                # flags say the same thing here as they do on the card's own block.
                "fills_scene_view": covers,
                "confidence": "inferred",
                "sources": [source] if source else [],
                "claim": record.get("id"),
                "place": NOT_STATED,
                "employer_or_body": body or NOT_STATED,
                "note": _external_note(
                    "PRINTED AGAINST THIS NAME IN THE 1833-1835 PRESS and carried here from "
                    "the newspaper gazetteer (T-1254, by " + GENERATOR + "). The gazetteer "
                    "holds its trades on the PERSON record and not on a single issue, so the "
                    "bound is the run of this person's own dated mentions, "
                    + (frm + " to " + to if frm and to else "which the record does not give")
                    + ", and the grade is `inferred`: the paper printed the trade, and the "
                    "resident programme's identity rule tied the printing to this card.",
                    "The scene date falls inside that run, so this role stands in the "
                    "1835 view (T-1299)." if covers else
                    "The scene date falls outside that run, so this role does not stand in "
                    "the 1835 view."),
                "_disposition": disposition,
                "_offered_by": "newspaper_gazetteer",
            })
    return rows


def register_1839_roles(person_id: str, person: dict) -> list[dict]:
    """The offices the Fergus 1839 city register prints, as dated roles."""
    doc = _load(REGISTER_1839)
    if not doc:
        return []
    rows = []
    listed = set(person.get("sources") or [])
    source = doc.get("source_id")
    for match in (doc.get("residents") or {}).get("matches") or []:
        if match.get("person_id") != person_id:
            continue
        for entry in match.get("entries_1839") or []:
            # The register's office column is a CODE, not a printing. It is read with
            # its underscores out, and that reading is what `as_printed` carries — the
            # nearest thing to a wording this record has.
            office = (entry.get("office") or entry.get("role") or "").replace("_", " ")
            role, kind, body, disposition = _fold(office)
            year = str(entry.get("year") or "") or "1839"
            # The flag is the crosswalk's own, and it is honoured only where the volume
            # is one the card's grade already stands on. That is tools/validate.py's
            # rule, applied here rather than tripped over there.
            reaches = bool(entry.get("reaches_scene")) and source in listed
            rows.append({
                "role": role,
                "kind": kind or "office",
                "as_printed": office or None,
                "from": year,
                "to": year,
                "precision": "year",
                "dated_by": "stated_date" if entry.get("year") else "printing_year",
                "covers_scene_date": reaches,
                "fills_scene_view": False,
                "confidence": "inferred",
                "sources": [source] if source else [],
                "claim": entry.get("claim"),
                "place": NOT_STATED,
                "employer_or_body": entry.get("body") or body or NOT_STATED,
                "note": _external_note(
                    "AN OFFICE FROM THE FERGUS 1839 CITY REGISTER, carried here by its own "
                    "crosswalk (T-1254, by " + GENERATOR + "). The register is a "
                    "retrospective table set in 1876, and its carry rule is explicit: a "
                    "later office is corroboration of CONTINUED RESIDENCE and never an "
                    "1835 fact.",
                    "The crosswalk marks this row as reaching the scene date and the volume "
                    "is one this card already stands on." if reaches else
                    "It therefore does not stand in the 1835 view."),
                "_disposition": disposition,
                "_offered_by": "fergus_1839_register",
            })
    return rows


def directory_roles(person_id: str, path: Path, year: str, entries_key: str,
                    occupation_key: str, place_keys: tuple[str, ...],
                    offered_by: str) -> list[dict]:
    """A trade printed in a directory YEARS after the scene, as the later role it is."""
    doc = _load(path)
    if not doc:
        return []
    source = doc.get("source_id")
    rows = []
    for match in doc.get("matches") or []:
        if match.get("person_id") != person_id:
            continue
        for entry in match.get(entries_key) or []:
            printed = (entry.get(occupation_key) or "").strip()
            if not printed:
                continue
            role, kind, body, disposition = _fold(printed)
            place = next((entry.get(k) for k in place_keys if entry.get(k)), None)
            rows.append({
                "role": role,
                "kind": kind or "trade",
                "as_printed": printed,
                "from": year,
                "to": year,
                "precision": "year",
                "dated_by": "printing_year",
                "covers_scene_date": False,
                "fills_scene_view": False,
                "confidence": "inferred",
                "sources": [source] if source else [],
                "claim": entry.get("claim"),
                "place": place or NOT_STATED,
                "employer_or_body": body or NOT_STATED,
                "note": _external_note(
                    "A TRADE PRINTED IN THE " + year + " DIRECTORY, " +
                    str(int(year) - 1835) + " years after the scene, carried here by its "
                    "crosswalk (T-1254, by " + GENERATOR + ").",
                    "It is NOT a claim about " + SCENE_DATE + " and never becomes one: "
                    "back-projecting a later volume onto the scene is the defect T-1145 "
                    "exists to refuse. `place` is the address or place of business the "
                    "record states in its own column; a firm named only inside the printed "
                    "line stays in `as_printed` for the business band to rule on."),
                "_disposition": disposition,
                "_offered_by": offered_by,
            })
    return rows


def corroborator_ruling(sources: list[str], person: dict | None) -> str:
    """T-1254's ruling on a scene-date role citing a volume the card does not list.

    T-1229 found four of them — Peter Cohen, Ira Couch, John Murphy and William Walters —
    and asked for a ruling: either the volume joins the person's `sources[]`, or the role
    says why a corroborator does not. IT DOES NOT JOIN. That list is what the person's
    1835 RESIDENCY grade stands on, and a hotel history or a Wolf Point building record
    speaks to the TRADE and says nothing about who lived in the town on 1 July 1835;
    putting it there would make the residency appear to rest on a volume that never
    addressed it. So the role states the difference instead, in its own note, and
    tools/validate.py's gate is unchanged: at least one source in common is required, and
    a corroborator beside it is a citation working correctly.
    """
    if not person:
        return ""
    extra = sorted(set(sources or []) - set(person.get("sources") or []))
    if not extra:
        return ""
    return (" A CORROBORATOR, NOT A SECOND FOUNDATION (T-1254): " + ", ".join(extra) +
            " " + ("corroborates" if len(extra) == 1 else "corroborate") + " this role "
            "and " + ("is" if len(extra) == 1 else "are") + " deliberately absent from "
            "the person's own `sources[]`, which lists what the 1835 RESIDENCY grade "
            "stands on. A volume that speaks to the trade and not to the residence does "
            "not join it.")


def _key(row: dict) -> tuple:
    """Two rows are the SAME assertion when one source dates one role to one bound."""
    return (tuple(row.get("sources") or ()), row.get("role") or "",
            row.get("as_printed") if not row.get("role") else "",
            row.get("from") or "", row.get("to") or "")


def fold_duplicates(rows: list[dict]) -> tuple[list[dict], int]:
    """One source printing two words for one controlled role asserts it ONCE.

    E. K. Hubbard is `fire insurance agent` and `insurance agent` in the same run of the
    same paper; both fold to `insurance_agent`, and two rows would put the trade in the
    1835 view twice. The survivor keeps the first wording and names the others, so the
    fold is visible on the card rather than only in the table.
    """
    kept: dict[tuple, dict] = {}
    folded = 0
    for row in rows:
        k = _key(row)
        if k not in kept:
            kept[k] = row
            continue
        folded += 1
        survivor = kept[k]
        others = set(filter(None, [survivor.get("_also_printed"), row.get("as_printed")]))
        survivor["_also_printed"] = ", ".join(sorted(others))
    for row in kept.values():
        also = row.pop("_also_printed", None)
        if also:
            row["note"] += (" SYNONYM-FOLDED (T-1254): the same source prints this role "
                            "as " + also + " as well, and one source asserting one role "
                            "over one bound is one row.")
    return list(kept.values()), folded


_PREMISES: dict[str, str] | None = None


def premises_of(role: str | None) -> str | None:
    """Whether this trade implies a house of trade of its own (T-1404, of T-1182).

    A ruling MISSING for a role of the closed vocabulary is a fault and not a silent null:
    the whole point of the field is that no in-window tradesman falls out of both halves of
    the clause, and a null that means "unruled" is indistinguishable from a null that means
    "the printing has not been adjudicated".
    """
    global _PREMISES
    if _PREMISES is None:
        doc = read_json(PREMISES_RULINGS)
        _PREMISES = {r["occupation"]: r["premises"] for r in doc["rulings"]}
    if not role:
        return None
    value = _PREMISES.get(role)
    if value is None:
        raise SystemExit(
            "%s: no premises ruling covers the role %r. Rule it in %s — an unruled trade is a "
            "tradesman who falls out of both halves of T-1182's clause 3."
            % (GENERATOR, role, PREMISES_RULINGS.relative_to(ROOT)))
    return value


def roles_for(person: dict, gazetteer: dict[str, dict] | None = None) -> list[dict]:
    occ = person.get("occupation")
    if not isinstance(occ, dict):
        return []
    pid = person.get("id")
    rows = [r for r in (scene_role(occ, pid, person), later_role(occ)) if r]
    rows += gazetteer_roles(person, gazetteer if gazetteer is not None else {})
    rows += register_1839_roles(pid, person)
    rows += directory_roles(pid, FERGUS_1843, "1843", "entries_1843", "occupation_1843",
                            ("address_1843",), "fergus_1843_directory")
    rows += directory_roles(pid, NORRIS_1844, "1844", "entries_1844", "occupation_1844",
                            ("place_of_business_1844", "address_1844"),
                            "norris_1844_directory")
    rows, _ = fold_duplicates(rows)
    rows.sort(key=lambda r: (r["from"] or "9999", r["to"] or "9999",
                             r["role"] or r["as_printed"] or "",
                             r["sources"][0] if r["sources"] else ""))
    for row in rows:
        row.pop("_disposition", None)
        row.pop("_offered_by", None)
        row["premises"] = premises_of(row.get("role"))
    return rows


def filling(roles: list[dict]) -> list[dict]:
    """The admitted rows standing behind the singular field, one per role, in row order.

    The field names a role once however many rows assert it, and T-1299 needs the ROWS
    and not only the names: a promoted block cites the sources of the roles that filled
    it, and the grade it is held at is the grade of the row it took the value from.
    """
    seen, kept = set(), []
    for r in roles:
        if not (r["fills_scene_view"] and r["confidence"] in CLAIMING and r["role"]):
            continue
        if r["role"] in seen:
            continue
        seen.add(r["role"])
        kept.append(r)
    return kept


def view(roles: list[dict]) -> tuple[str, list[str]]:
    """The 1835 compatibility view: the claiming roles that cover the scene date.

    ONLY AN ADMITTED ROW FILLS IT, and that is `fills_scene_view` rather than
    `covers_scene_date`. The two came apart in T-1254, when the external volumes arrived:
    ten press readings REACH 1 July 1835 — L. G. Curtiss is printed an attorney in the
    Democrat of that very day — and admitting them into the singular field is not this
    generator's to do alone. Three other tools derive that field (T-0693's
    tools/qualify_later_trades.py, the ladder resident pass, and T-0837's write gate,
    which requires the field to cite an 1835 source of its own), and a value written here
    that those three do not derive is a value the gate reverts on the next run. So the
    row says plainly that its evidence reaches the day, and says just as plainly that it
    does not stand in the field; T-1296 is where the three generators are made to agree.

    THE NAMED LIST IS IN ROW ORDER and the singular value is the STRONGEST claim in it,
    not simply the first, so that an inferred reading can never displace an attested one
    by sorting earlier.
    """
    kept = filling(roles)
    at = [r["role"] for r in kept]
    strongest = next((r["role"] for r in kept if r["confidence"] == "attested"), None)
    return (strongest or (at[0] if at else ABSENT)), at


def proposed(households: Path = HOUSEHOLDS) -> dict[str, dict]:
    """Every card this tool would change, keyed by path stem, with the whole new doc."""
    out: dict[str, dict] = {}
    gazetteer = gazetteer_index()
    for path in sorted(households.glob("*.json")):
        doc = read_json(path)
        before = dumps(doc)
        for person in doc.get("persons") or []:
            occ = person.get("occupation")
            if not isinstance(occ, dict):
                continue
            roles = roles_for(person, gazetteer)
            value, at = view(roles)
            if not roles:
                # NOTHING TO SAY, SO NOTHING IS WRITTEN. A person with no role evidence
                # carries neither `roles[]` nor the view keys, and the gate reads that
                # absence as the assertion it is: a card with no roles cannot hold a
                # trade in the 1835 field, because a trade in that field IS role
                # evidence and would have produced a row. Writing `roles: []` and an
                # empty view onto the other 1,148 cards would churn the whole residents
                # tree every run to say what their `none_recorded` already says.
                person.pop("roles", None)
                for key in ("derived_from", "roles_at_scene_date"):
                    occ.pop(key, None)
                continue
            person["roles"] = roles
            withdrawn = occ.get("withdrawn_from_scene_date")
            held = (withdrawn.get("value") if isinstance(withdrawn, dict)
                    and withdrawn.get("value") else occ.get("value"))
            was_promoted = isinstance(occ.get("promoted_from_roles"), dict)
            # A PROMOTED BLOCK IS RE-DERIVED EVERY RUN, not only on the run that first
            # filled the field. `held` equals `value` the moment the promotion is
            # committed, so a branch keyed on `held != value` alone would write the block
            # once and then never touch it again — and a correction to its citations, its
            # grade or its prose would sit uncommitted while `--check` called the card
            # clean. The write below is idempotent, so re-deriving it costs a comparison.
            if value != ABSENT and (held != value or was_promoted):
                # THE FIELD GAINS A TRADE ITS ROLES REACH (T-1299). Until the four
                # derivers of this field agreed, a press reading that covered 1 July 1835
                # stood in `roles[]` saying so and was kept out of the field anyway. It is
                # admitted here, and the block is made to carry what the write gate
                # (tools/audit_scene_window_trades.py, T-0837) asks of any standing 1835
                # trade: the sources the rows that filled it cite, at least one of which
                # describes 1835, because that is what admitted the rows.
                kept = filling(roles)
                grade = next((r["confidence"] for r in kept if r["role"] == value),
                             "inferred")
                cites = sorted({s for r in kept for s in (r.get("sources") or []) if s})
                occ.pop("withdrawn_from_scene_date", None)
                occ["value"] = value
                occ["confidence"] = grade
                occ["sources"] = cites
                occ["promoted_from_roles"] = {
                    # NOT `roles`: `roles_at_scene_date` two lines below names exactly the
                    # rows this was promoted out of, and the card prints that one. A second
                    # copy of the same list would be a figure nobody reads.
                    "sources": cites,
                    "ticket": "T-1299",
                    "note": (
                        "THE CITATIONS ARE THE ROWS', NOT THE BLOCK'S OWN. This field was "
                        "promoted out of `roles[]` by " + GENERATOR + " and holds nothing "
                        "those rows do not already say; it is recorded here so the block "
                        "cannot be mistaken for a second, independently sourced assertion "
                        "of the same trade, and so that " + GENERATOR + " reads its own "
                        "write as a view rather than as evidence on the next run."),
                }
                occ["note"] = (
                    "A TRADE READ FOR " + SCENE_DATE + " OUT OF THIS CARD'S OWN ROLES. "
                    "`" + str(value) + "` is the strongest claiming role in `roles[]` "
                    "whose bound contains the scene date, and the grade above is that "
                    "row's: `inferred` where the evidence is a trade printed against this "
                    "name in the 1833-1835 press, because the paper printed the trade and "
                    "the resident programme's identity rule tied the printing to this "
                    "card. The field used to read `" + ABSENT + "` while the row beneath "
                    "it said the evidence reached the day — the four tools that derive "
                    "this field disagreed, and T-1299 is where they were made to agree "
                    "(written by " + GENERATOR + ").")
            elif held != value:
                verdict, ledger_note = VERDICTS.get(person.get("id"), ("unadjudicated", None))
                # A PROMOTION THAT NO LONGER HOLDS LEAVES THE CARD (T-1299), along with
                # the citations it put on the block. A field reading `none_recorded` may
                # not go on citing the sources of a trade it has stopped asserting.
                if occ.pop("promoted_from_roles", None) is not None:
                    occ.pop("sources", None)
                occ["withdrawn_from_scene_date"] = {
                    "value": held,
                    # The grade the trade was held at, which after the first withdrawal
                    # is on the withdrawal and not on the field it was taken off.
                    "confidence": (withdrawn.get("confidence")
                                   if isinstance(withdrawn, dict) and withdrawn.get("value")
                                   else occ.get("confidence")),
                    "verdict": verdict,
                    "ticket": "T-0991",
                    "note": ledger_note or (
                        "No verdict is recorded for this person in "
                        "tools/audit_scene_window_trades.py's table."),
                }
                occ["value"] = value
                occ["confidence"] = "reconstructed"
                occ["note"] = (
                    "NO TRADE IS RECORDED FOR " + SCENE_DATE + ", AND ONE IS RECORDED FOR "
                    "ANOTHER YEAR. The trade this field used to carry — `" + str(held) +
                    "` — is not gone: it stands in `roles[]` with the bound its sources "
                    "permit, and `withdrawn_from_scene_date` above carries the audit's "
                    "verdict for withdrawing it. The 1835 field asserts what the sources "
                    "reach, which here is nothing, because no source cited for the trade "
                    "describes 1835 (T-0837's write rule, T-0872's measurement, T-0991's "
                    "repair, made by " + GENERATOR + ").")
            elif "withdrawn_from_scene_date" in occ:
                # The trade reaches 1835 after all — a source moved, or one was added.
                # The withdrawal is not a record, it is a refusal, and a refusal that no
                # longer fires must leave the card rather than sit on it contradicting
                # the field above.
                occ.pop("withdrawn_from_scene_date")
            occ["derived_from"] = "roles"
            occ["roles_at_scene_date"] = at
        if dumps(doc) != before:
            out[path.name] = doc
    return out


# --------------------------------------------------------------------------
# THE MIGRATION TABLE (T-1145 acceptance 3 and 9, T-1254)
#
# "Produce a reconciliation table: offered, asserted, synonym-folded, refused and
# unresolved", published at docs/RESEARCH/roles-migration-2026-09.md, "with one row per
# person carrying 2+ roles (the audit found 176), because the population profile (T-1160)
# counts multi-role persons from it." The table is GENERATED and `--check` refuses drift
# in it for the same reason it refuses drift in a card: a disposition table nobody
# regenerates stops describing the tree it is about.

DISPOSITIONS = ("asserted", "folded", "refused", "unresolved")


def offered() -> tuple[dict[str, dict[str, int]], int, list[tuple[str, list[dict]]]]:
    """Every row the external records offer, by source and disposition, before folding."""
    gazetteer = gazetteer_index()
    tally: dict[str, dict[str, int]] = {}
    duplicates = 0
    people: list[tuple[str, list[dict]]] = []
    for path in sorted(HOUSEHOLDS.glob("*.json")):
        for person in read_json(path).get("persons") or []:
            occ = person.get("occupation")
            if not isinstance(occ, dict):
                continue
            pid = person.get("id")
            external = (gazetteer_roles(person, gazetteer)
                        + register_1839_roles(pid, person)
                        + directory_roles(pid, FERGUS_1843, "1843", "entries_1843",
                                          "occupation_1843", ("address_1843",),
                                          "fergus_1843_directory")
                        + directory_roles(pid, NORRIS_1844, "1844", "entries_1844",
                                          "occupation_1844",
                                          ("place_of_business_1844", "address_1844"),
                                          "norris_1844_directory"))
            for row in external:
                bucket = tally.setdefault(row["_offered_by"], dict.fromkeys(DISPOSITIONS, 0))
                bucket[row["_disposition"]] += 1
            _, folded = fold_duplicates(list(external))
            duplicates += folded
            rows = roles_for(person, gazetteer)
            if len(rows) >= 2:
                people.append((pid, rows))
    return tally, duplicates, people


def migration_table() -> str:
    tally, duplicates, people = offered()
    total = {d: sum(b[d] for b in tally.values()) for d in DISPOSITIONS}
    reaching = sum(1 for _, rows in people for r in rows if r["covers_scene_date"])
    filling = sum(1 for _, rows in people for r in rows if r["fills_scene_view"])
    places = sum(1 for _, rows in people for r in rows if r["place"] != NOT_STATED)
    bodies = sum(1 for _, rows in people
                 for r in rows if r["employer_or_body"] != NOT_STATED)
    out: list[str] = []
    w = out.append
    w("# The role migration — the external structured evidence, and what became of it")
    w("")
    w("GENERATED by `" + GENERATOR + " --table`. Do not hand-edit: `--check` re-derives")
    w("this file and refuses drift, because a disposition table nobody regenerates stops")
    w("describing the tree it is about. T-1254, of T-1145 (acceptance 3 and 9).")
    w("")
    w("## What was offered, and what was made of it")
    w("")
    w("Four research records hold structured role evidence about people the residents")
    w("layer carries: the newspaper gazetteer compiled from the 1833-1835 Chicago press,")
    w("the Fergus 1839 city register's office tables, and the Fergus 1843 and Norris 1844")
    w("directory crosswalks. Every row each of them offers about a resident is listed")
    w("below under the disposition it received.")
    w("")
    w("- **asserted** — the printing IS a word in the residents vocabulary.")
    w("- **folded** — a synonym ruled onto a controlled word (`boot and shoe maker` ->")
    w("  `shoemaker`, `counsellor at law` -> `attorney`).")
    w("- **refused** — a printing deliberately given no controlled word: one that names")
    w("  TWO trades (`watchmaker and jeweller`), or one the vocabulary has no word for")
    w("  (`ventriloquist`, `capitalist`, `botanic practitioner`).")
    w("- **unresolved** — a printing the fold table does not rule on at all. Overwhelmingly")
    w("  the compound directory lines that carry a trade, an address and a firm in one")
    w("  string (`clerk, Charles Walker & Co`); the row still exists, dated and cited,")
    w("  with its wording in `as_printed` and `role: null`.")
    w("")
    w("A refused or unresolved row is NOT a dropped row. Every one of them is on the card")
    w("as a dated role carrying its printing, its bound and its source; what it does not")
    w("carry is a controlled word, and it may not fill the 1835 view without one.")
    w("")
    w("| record | offered | asserted | folded | refused | unresolved |")
    w("| --- | ---: | ---: | ---: | ---: | ---: |")
    for name in sorted(tally):
        b = tally[name]
        w("| `" + name + "` | " + str(sum(b.values())) + " | " +
          " | ".join(str(b[d]) for d in DISPOSITIONS) + " |")
    w("| **total** | **" + str(sum(total.values())) + "** | " +
      " | ".join("**" + str(total[d]) + "**" for d in DISPOSITIONS) + " |")
    w("")
    w("`" + str(duplicates) + "` further row(s) were SYNONYM-FOLDED INTO EACH OTHER: one")
    w("source printing two wordings for one controlled role over one bound asserts that")
    w("role once, and the survivor names the other wording in its note.")
    w("")
    w("## What the roles now carry")
    w("")
    w("- `" + str(len(people)) + "` people carry two or more roles, listed below.")
    w("- `" + str(reaching) + "` of their roles reach " + SCENE_DATE + ", of which `" +
      str(filling) + "` stand in the 1835 compatibility view.")
    w("- The `" + str(reaching - filling) + "` that reach the day WITHOUT filling the")
    w("  field are the migration's open question, and they are held open on purpose. Four")
    w("  tools derive `persons[].occupation` and only one of them was taught about roles:")
    w("  this generator, T-0693's `tools/qualify_later_trades.py`, the ladder resident")
    w("  pass, and T-0837's write gate, which refuses a standing 1835 trade whose block")
    w("  cites no 1835 source of its own — and a block filled from roles cites nothing,")
    w("  because its citations are on the rows. Writing the trade in anyway was measured:")
    w("  17 gate steps went red, one of them the trade-census count, which suddenly saw a")
    w("  lawyer no practitioner ruling held. T-1296 makes the four agree; until it does,")
    w("  the rows say plainly that the evidence reaches the day and the field does not")
    w("  carry it, which is a state that can be read and argued with.")
    w("- `" + str(places) + "` carry a stated `place` and `" + str(bodies) + "` a stated")
    w("  `employer_or_body`. Both default to `" + NOT_STATED + "`, which is an assertion:")
    w("  the record does not say. Places come from the directories' own address and")
    w("  place-of-business columns and bodies from the register's `body` column and the")
    w("  offices in the fold table; a firm named only inside a printed line is left in")
    w("  `as_printed` for the business band (T-1180 onward) rather than parsed out.")
    w("")
    w("## The corroborator ruling (T-1229's finding, ruled here)")
    w("")
    w("T-1229 found four scene-date roles citing a volume the person's own `sources[]`")
    w("does not list — Peter Cohen, Ira Couch, John Murphy and William Walters. **The")
    w("volume does not join the list.** `sources[]` is what the person's 1835 RESIDENCY")
    w("grade stands on, and a hotel history or a Wolf Point building record speaks to the")
    w("TRADE while saying nothing about who lived in the town on 1 July 1835; adding it")
    w("would make the residency appear to rest on a volume that never addressed it. The")
    w("role says so instead, in its own note, and the validator's gate is unchanged: at")
    w("least one source in common, with corroborators beside it.")
    w("")
    w("## Daniel Elston, the fixture")
    w("")
    for pid, rows in people:
        if pid != "elston_daniel":
            continue
        w("| role | as printed | from | to | reaches " + SCENE_DATE + " | fills it | place | body |")
        w("| --- | --- | --- | --- | --- | --- | --- | --- |")
        for r in rows:
            w("| " + (("`" + r["role"] + "`") if r["role"] else "_none_") + " | " +
              (r["as_printed"] or "—") + " | " + (r["from"] or "—") + " | " +
              (r["to"] or "—") + " | " + ("yes" if r["covers_scene_date"] else "no") +
              " | " + ("yes" if r["fills_scene_view"] else "no") +
              " | " + r["place"] + " | " + r["employer_or_body"] + " |")
        w("")
    w("## Every person carrying two or more roles")
    w("")
    w("| person | roles | reaching " + SCENE_DATE + " | printings |")
    w("| --- | ---: | ---: | --- |")
    for pid, rows in people:
        reach = sum(1 for r in rows if r["covers_scene_date"])
        printings = "; ".join(sorted({(r["as_printed"] or r["role"] or "?") for r in rows}))
        w("| `" + pid + "` | " + str(len(rows)) + " | " + str(reach) + " | " +
          printings.replace("|", "/") + " |")
    w("")
    return "\n".join(out)


def table(write_it: bool = True) -> int:
    doc = migration_table()
    if not write_it:
        current = MIGRATION_TABLE.read_text(encoding="utf-8") if MIGRATION_TABLE.exists() else ""
        if current != doc:
            print(f"{MIGRATION_TABLE.relative_to(ROOT)} is not what "
                  f"{GENERATOR} --table derives — run it and commit the result.",
                  file=sys.stderr)
            return 1
        return 0
    MIGRATION_TABLE.parent.mkdir(parents=True, exist_ok=True)
    MIGRATION_TABLE.write_text(doc, encoding="utf-8")
    print(f"wrote {MIGRATION_TABLE.relative_to(ROOT)}")
    return 0


def report() -> int:
    changes = proposed()
    total = sum(len(p.get("roles") or [])
                for doc in changes.values() for p in doc.get("persons") or [])
    withdrawn = [(p.get("id"), (p.get("occupation") or {}).get("withdrawn_from_scene_date"))
                 for doc in changes.values() for p in doc.get("persons") or []
                 if (p.get("occupation") or {}).get("withdrawn_from_scene_date")]
    print(f"{len(changes)} card(s) would change, carrying {total} role(s)")
    if withdrawn:
        print(f"\n{len(withdrawn)} trade(s) withdrawn from the {SCENE_DATE} view:")
        for pid, w in withdrawn:
            print(f"  {pid:<20} {w['value']:<26} {w['verdict']}")
    return 0


def write() -> int:
    changes = proposed()
    for name, doc in changes.items():
        (HOUSEHOLDS / name).write_text(dumps(doc), encoding="utf-8")
    print(f"wrote {len(changes)} card(s) under {HOUSEHOLDS.relative_to(ROOT)}")
    # THE TABLE IS WRITTEN AFTER THE CARDS, and it has to be: it counts the roles that
    # reach the scene date from the view the cards now carry, so a table derived before
    # the write describes the tree as it was a second ago.
    return table()


def check() -> int:
    if table(write_it=False):
        return 1
    changes = proposed()
    if not changes:
        n = sum(len(p.get("roles") or []) for path in sorted(HOUSEHOLDS.glob("*.json"))
                for p in read_json(path).get("persons") or [])
        print(f"{n} role(s) stand on the cards, and every one of them re-derives")
        return 0
    print(f"{len(changes)} resident card(s) do not carry what {GENERATOR} derives — run "
          f"--write and commit them.", file=sys.stderr)
    for name in sorted(changes)[:10]:
        print(f"  {name}", file=sys.stderr)
    if len(changes) > 10:
        print(f"  …and {len(changes) - 10} more", file=sys.stderr)
    return 1


def self_test() -> int:
    """The rules above, held over fixtures rather than over the tree."""
    import tempfile
    failures = []

    def holds(label, got, want):
        if got != want:
            failures.append(f"{label}: got {got!r}, wanted {want!r}")

    vocab = set((read_json(INDEX).get("vocabulary") or {}).get("occupations") or [])
    holds("every office is in the manifest vocabulary", sorted(OFFICES - vocab), [])
    holds("every profession is in the manifest vocabulary", sorted(PROFESSIONS - vocab), [])
    holds("no role is both an office and a profession", sorted(OFFICES & PROFESSIONS), [])
    holds("an unlisted word is a trade", kind_of("blacksmith"), "trade")
    holds("an office is an office", kind_of("postmaster"), "office")
    holds("a profession is a profession", kind_of("attorney"), "profession")

    holds("a slashed run reads both ends", _ends("1833-11/1835-08"), ("1833-11", "1835-08"))
    holds("a hyphenated year range reads both ends", _ends("1673-1857"), ("1673", "1857"))
    holds("a bare year is its own bound", _ends("1839"), ("1839", "1839"))
    holds("a bare month is its own bound", _ends("1833-11"), ("1833-11", "1833-11"))
    holds("prose names no bound", _ends("nineteenth century"), ("", ""))
    holds("a span is a span", _precision("1833-11", "1835-08"), "source_span")
    holds("one year is year precision", _precision("1839", "1839"), "year")
    holds("one month is month precision", _precision("1833-11", "1833-11"), "month")
    holds("no bound is unknown precision", _precision("", ""), "unknown")

    # THE VIEW, over synthetic roles.
    def role(**kw):
        base = {"role": "cooper", "covers_scene_date": True, "fills_scene_view": True,
                "confidence": "attested"}
        base.update(kw)
        return base
    holds("nothing covering leaves the field absent",
          view([role(covers_scene_date=False, fills_scene_view=False)]), (ABSENT, []))
    holds("a role that reaches the day and is not admitted does not fill it",
          view([role(fills_scene_view=False)]), (ABSENT, []))
    holds("an attested role outranks an inferred one that sorts first",
          view([role(role="grocer", confidence="inferred"), role()]),
          ("cooper", ["grocer", "cooper"]))
    holds("one controlled role is named once however many rows carry it",
          view([role(), role()]), ("cooper", ["cooper"]))
    holds("one covering role fills it", view([role()]), ("cooper", ["cooper"]))
    holds("two covering roles are both named",
          view([role(), role(role="grocer")]), ("cooper", ["cooper", "grocer"]))
    holds("a reconstructed role is not a claim",
          view([role(confidence="reconstructed")]), (ABSENT, []))
    holds("a role with no controlled word cannot fill the field",
          view([role(role=None)]), (ABSENT, []))

    with tempfile.TemporaryDirectory() as tmp:
        hh = Path(tmp) / "households"
        hh.mkdir()

        def card(name, pid, occ):
            (hh / f"{name}.json").write_text(json.dumps(
                {"id": name, "persons": [{"id": pid, "name": pid, "occupation": occ}]}),
                encoding="utf-8")

        # Real source ids, so the fixtures read the committed describes_date.
        card("hh_window", "window", {"value": "clothier", "confidence": "attested",
                                     "sources": ["chicago_democrat_1833_1835"],
                                     "note": "held"})
        card("hh_early", "early", {"value": "blacksmith", "confidence": "attested",
                                   "sources": ["chicago_democrat_1833_11_26"],
                                   "note": "held"})
        card("hh_later", "later", {"value": ABSENT, "confidence": "reconstructed",
                                   "note": "held",
                                   "later_occupation": {
                                       "value": "attorney at law", "describes_date": 1843,
                                       "confidence": "attested",
                                       "sources": ["fergus_chicago_directory_1843"]}})
        card("hh_none", "none", {"value": ABSENT, "confidence": "reconstructed",
                                 "note": "held"})
        out = proposed(hh)

        w = out["hh_window.json"]["persons"][0]
        holds("an in-window trade keeps the field", w["occupation"]["value"], "clothier")
        holds("…and names itself in the scene-date list",
              w["occupation"]["roles_at_scene_date"], ["clothier"])
        holds("…and its note is not rewritten", w["occupation"]["note"], "held")
        holds("…and it carries one role", len(w["roles"]), 1)
        holds("…bounded by the run of the paper",
              (w["roles"][0]["from"], w["roles"][0]["to"]), ("1833-11", "1835-08"))

        e = out["hh_early.json"]["persons"][0]
        holds("a pre-scene trade leaves the field", e["occupation"]["value"], ABSENT)
        holds("…at reconstructed", e["occupation"]["confidence"], "reconstructed")
        holds("…and the trade is not lost", e["roles"][0]["role"], "blacksmith")
        holds("…and the withdrawal states what it withdrew",
              e["occupation"]["withdrawn_from_scene_date"]["value"], "blacksmith")
        holds("…and the role does not reach the scene",
              e["roles"][0]["covers_scene_date"], False)

        lt = out["hh_later.json"]["persons"][0]
        holds("a later trade becomes a dated role", lt["roles"][0]["as_printed"],
              "attorney at law")
        holds("…dated by the year it was printed", lt["roles"][0]["from"], "1843")
        holds("…with no controlled word yet", lt["roles"][0]["role"], None)
        holds("…and it does not reach the scene date", lt["roles"][0]["covers_scene_date"],
              False)
        holds("…and the 1835 field stays absent", lt["occupation"]["value"], ABSENT)

        holds("the card's own scene role is admitted to the view",
              w["roles"][0]["fills_scene_view"], True)
        holds("…and a pre-scene one is not", e["roles"][0]["fills_scene_view"], False)
        holds("a later printing is never admitted", lt["roles"][0]["fills_scene_view"],
              False)

        # THE FOLD, held over its own table rather than over the tree.
        holds("a controlled word is asserted as itself", _fold("cooper")[0], "cooper")
        holds("…and says so", _fold("cooper")[3], "asserted")
        holds("a synonym folds", _fold("boot and shoe maker")[:1] + (_fold(
            "boot and shoe maker")[3],), ("shoemaker", "folded"))
        holds("a printing naming two trades folds to neither",
              _fold("watchmaker and jeweller")[0], None)
        holds("…and is a refusal, not an oversight",
              _fold("watchmaker and jeweller")[3], "refused")
        holds("a printing the table does not rule on is unresolved",
              _fold("clerk, Charles Walker & Co")[3], "unresolved")
        holds("an office carries the body it was held for",
              _fold("county clerk")[2], "cook_county")
        holds("every folded word is in the manifest vocabulary",
              sorted({r for r, _, _ in FOLD.values() if r} - vocab), [])
        holds("a duplicate pair folds to one row", len(fold_duplicates([
            {"sources": ["s"], "role": "insurance_agent", "as_printed": "insurance agent",
             "from": "1834", "to": "1835", "note": "n"},
            {"sources": ["s"], "role": "insurance_agent",
             "as_printed": "fire insurance agent", "from": "1834", "to": "1835",
             "note": "n"}])[0]), 1)
        holds("…and the survivor names the other wording", "fire insurance agent" in
              fold_duplicates([
                  {"sources": ["s"], "role": "insurance_agent",
                   "as_printed": "insurance agent", "from": "1834", "to": "1835",
                   "note": "n"},
                  {"sources": ["s"], "role": "insurance_agent",
                   "as_printed": "fire insurance agent", "from": "1834", "to": "1835",
                   "note": "n"}])[0][0]["note"], True)
        holds("two different bounds are two assertions", len(fold_duplicates([
            {"sources": ["s"], "role": "surveyor", "as_printed": "surveyor",
             "from": "1834", "to": "1835", "note": "n"},
            {"sources": ["s"], "role": "surveyor", "as_printed": "surveyor",
             "from": "1839", "to": "1839", "note": "n"}])[0]), 2)
        holds("a corroborator is ruled on where one is cited",
              "CORROBORATOR" in corroborator_ruling(["a", "b"], {"sources": ["a"]}), True)
        holds("…and nothing is said where every source is listed",
              corroborator_ruling(["a"], {"sources": ["a"]}), "")

        holds("a card with no role evidence gains no roles[]",
              "roles" in (out.get("hh_none.json") or {"persons": [{}]})["persons"][0], False)

        # IDEMPOTENCE — the gate's whole claim. Write once, and there is nothing left.
        for name, doc in out.items():
            (hh / name).write_text(dumps(doc), encoding="utf-8")
        holds("a second derivation proposes nothing", sorted(proposed(hh)), [])

    for line in failures:
        print(f"FAIL {line}", file=sys.stderr)
    print(f"self-test: {56 - len(failures)}/56 assertions hold")
    return 1 if failures else 0


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "--report"
    sys.exit({"--report": report, "--write": write, "--check": check,
              "--self-test": self_test, "--table": table}.get(arg, report)())
