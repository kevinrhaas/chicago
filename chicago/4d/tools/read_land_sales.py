#!/usr/bin/env python3
"""The Illinois State Archives land tract sales, read into the research shape (T-0557).

    tools/read_land_sales.py --build       derive every generated file from the TSV
    tools/read_land_sales.py --check       the gate: re-derive and refuse any drift
    tools/read_land_sales.py --self-test   the gate's assertions still fire when broken

WHAT THIS READS. `data/research/land_sales/text/*.tsv` is the committed deposit: one
row per sale, every field exactly as the database printed it, harvested by
`tools/harvest_land_sales.py --sweep` (which reaches the network and is therefore run
deliberately, never by the gate). Everything else under `data/research/land_sales/`
is derived from that file by --build and re-derived by --check, so a hand-edit to a
generated file is a gate failure and not a silent divergence.

WHY A SALE IS NOT A RESIDENT, and it is the only thing about this source that
matters. The register records a TRANSACTION. A man who entered eighty acres in T40N
R14E in 1835 may have been standing in Chicago, in Vandalia, or in Connecticut; the
purchase says only that he bought. The one column that speaks to where he lived is
`Residence`, and it names a COUNTY — COOK, MACON, VERMILION — never a town. So:

  * a purchase alone proposes NOTHING about residence, and this file grades it
    `inferred` with the reasoning written on the row;
  * a purchase whose Residence column reads COOK is contemporary evidence that the
    purchaser lived in Cook County on the date of sale, and is graded `documented`
    for exactly that and no more — Cook County in 1835 is far larger than the town;
  * nothing here mints a resident or regrades one. `resident_crosswalk.json` proposes
    a correspondence and states the rule that made it; T-0514 and T-0515 write people.

A surname-only purchaser is always a refusal, however good the tract agreement is.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import namesake  # noqa: E402  (the namesake rule this imports rather than restates)

ROOT = Path(__file__).resolve().parent.parent
DOMAIN = ROOT / "data" / "research" / "land_sales"
RESIDENTS = ROOT / "data" / "residents"
SOURCE_ID = "isa_public_domain_land_tract_sales"
# The one file under the domain that is NOT derived from the deposit: the RULINGS on the
# crosswalk's proposals (T-0700). A judgement is not a derivation, so it is hand-authored,
# it is not in GENERATED, and --check validates it instead of re-deriving it.
RULINGS_NAME = "resident_rulings.json"
# `named` is T-0993's addition, and it is the ruling layer's missing direction.
# `upheld` and `refused` can only ADJUDICATE a proposal the mechanical rule made:
# they confirm it or take it away. But `namesake.choose` weighs the FIRST forename
# token and nothing else, so a register that prints a man's MIDDLE name in the
# forename's place — BLANCHARD GURTREY, for Francis Gurtrey Blanchard — is a
# refusal no reading of any page can ever overturn, because the rulings file was
# only allowed to subtract. `named` lets a hand ruling GIVE a match the rule could
# not reach, under the guards in check_rulings(): only where the surname gathered
# rivals and the forename failed to choose among them, never onto a surname-only
# purchaser, and never onto somebody the residents layer does not hold.
RULING_KINDS = ("upheld", "refused", "named")
# THE FIRMS THE REGISTER SELLS TO, DECLARED (T-0851). `namesake.firm_style` reads the
# page rather than this list — a partnership is recognised by the words the register
# printed, not by being named here — but a firm the reading finds and nobody has looked
# at is a purchaser going onto no card and into no business, silently. So `check` fails
# on a derived firm that is not declared here. Adding a deposit that carries a new one
# is meant to stop the build: read the rows, then add the spelling.
KNOWN_FIRMS = ("GARRETT A ET CO", "PRUYNE P AND CO")
# THE BUYERS THAT ARE NEITHER PEOPLE NOR PARTNERSHIPS (T-1033). The town lots brought
# three of them and the firm test could not see one: it looks for the conjunction the
# register sets before `CO` — `GARRETT A ET CO` — and a body corporate has no partner in
# front of it to conjoin. So `UNION HOTEL CO` bought two lots and would have gone to the
# forename rule as a man named Union, and `COOK CNTY COM` — the county commissioners,
# twenty-four lots, the fourth busiest buyer in the whole reading — was refused only
# because no Cook of the layer is called Cnty. Being refused for the wrong reason is not
# the same as being read. BODY_WORDS below is the test, asked of everything AFTER the
# surname so that Thomas Church stays a man, and a spelling it catches must be declared
# here with what the register's own page says the body was. The guard is the firms' one:
# an undeclared body stops the build rather than passing quietly.
BODY_WORDS = frozenset((
    "CNTY", "COUNTY", "COM", "COMMRS", "CO", "COMPANY", "COMPY", "SCHOOL", "SCHOOLS",
    "TRUSTEE", "TRUSTEES", "BANK", "CHURCH", "CITY", "STATE", "TOWN"))
KNOWN_BODIES = {
    "COOK CNTY COM": "The commissioners of Cook County, buying on the county's account. "
                     "The register gives the residence as UNKNOWN on every one of the "
                     "twenty-four rows, as it does for every town lot.",
    "CHICAGO CITY SCHOOLS": "The town's school fund, the same body whose section 16 the "
                            "school-section sales above are the selling of.",
    "UNION HOTEL CO": "A hotel company. Which house it was, and who stood in it, is not "
                      "on the register's page and is not guessed at here.",
}
# THE DEPOSITS, IN THE ORDER THEY WERE ADDED, and that order is load-bearing. Record
# ids are positional — `ls0001` upward across the whole reading — and data/structures/
# *.json cite them by id, so a new deposit APPENDS and never renumbers what is already
# cited. Each carries the (township, range) pairs its sweep asked for, section by
# section, and the ticket that read them; coverage is derived from exactly that.
# A deposit read BY SECTION carries the (township, range) pairs its sweep asked for. The
# town lots have none — the register gives them no section, which is the whole reason they
# were invisible — so that deposit carries `pairs: ()` and declares the county's
# sectionless group instead of a grid of sections (T-1033).
DEPOSITS = (
    {"tsv": "isa_land_tract_sales_t39n_t40n_r14e_through_1836.tsv",
     "ticket": "T-0675", "pairs": ((39, 14), (40, 14))},
    {"tsv": "isa_land_tract_sales_t39n_t40n_r13e_t38n_t41n_r14e_t38n_r15e_through_1836.tsv",
     "ticket": "T-0676", "pairs": ((39, 13), (40, 13), (38, 14), (41, 14), (38, 15))},
    {"tsv": "isa_land_tract_sales_cook_town_lots_through_1836.tsv",
     "ticket": "T-1033", "pairs": (), "county": "COOK", "sectionless": True},
)


# THE COMPLETENESS PROBE (T-0830). The deposits above are read BY SECTION, and a
# section query is blind by construction to a row the register gives no section: a town
# lot is described by its plat — `L2BL46CHIOT` — with Section, Township, Range and
# Meridian all empty. So no walk of any section, however complete, can reach one, and
# the domain could not tell whether that mattered. This file is the query that can: ONE
# county, listed, walked to its end (`harvest_land_sales.py --county-list COOK`). It is
# the results page's own nine columns and nothing more — it is here to MEASURE the
# sweep, not to be read as one — and `build_coverage` derives the measurement from it.
PROBE = {"tsv": "isa_land_tract_sales_cook_county_list_through_1836.tsv",
         "ticket": "T-0830", "county": "COOK", "through_year": 1836}
PROBE_COLS = ["purchase_no", "purchaser", "legal_description", "section", "township",
              "range", "meridian", "date_purchased", "county"]
# THE TOWN LOTS, HARVESTED AND NOT YET READ (T-1032). The probe NAMES the 619 rows the
# register gives no section; this file is their DETAIL pages, one fetch per row
# (`harvest_land_sales.py --town-lots COOK`), carrying the sweep's own sixteen columns so
# that reading them later needs no second shape. It is deliberately NOT in DEPOSITS. A
# deposit mints record ids, proposes a resident crosswalk and puts firms in front of the
# ruling layer, and none of that can be done honestly while `tract()` has no way to say
# what ground `L2BL46CHIOT` is — its LOT pattern is the school section's `LOT5BL3` and
# matches none of these. Reading them is T-1033. Until then the file is held here rather
# than left stray, and `check_harvested` below re-checks it against the probe it was drawn
# from every time the gate runs: a harvest that drifted from its own list, or that quietly
# acquired a section, is a fault and not a silence.
HARVESTED = {"tsv": "isa_land_tract_sales_cook_town_lots_through_1836.tsv",
             "ticket": "T-1032", "read_by": "T-1033"}
# T-1033 JOINED IT. The file above is now the third entry of DEPOSITS and derives records,
# entries, coverage and a crosswalk like any other — `tract()` can say what a lot and a
# block in a named plat is, or refuse it, which is what was missing. `HARVESTED` stays
# because `check_harvested` below is still worth running: being a deposit makes the file
# derived-from, and it says nothing about whether it is still FAITHFUL to the county list
# it was drawn from. Those are two different questions and the gate asks both.


# The seven townships the deposits above declare, as the probe's list page spells them.
def declared_townships() -> frozenset:
    return frozenset(("%dN" % tw, "%dE" % rg) for dep in DEPOSITS for tw, rg in dep["pairs"])


def read_probe(domain: Path) -> list:
    """The probe's rows, or [] when it is not committed. Header checked like a deposit."""
    path = domain / "text" / PROBE["tsv"]
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    if lines[0].split("\t") != PROBE_COLS:
        raise SystemExit("land_sales: the probe's header is not the harvest's list header")
    out = []
    for n, line in enumerate(lines[1:], start=2):
        if not line.strip():
            continue
        cells = line.split("\t")
        if len(cells) != len(PROBE_COLS):
            raise SystemExit("land_sales: %s line %d has %d cells, not %d"
                             % (PROBE["tsv"], n, len(cells), len(PROBE_COLS)))
        out.append(dict(zip(PROBE_COLS, cells)))
    return out


def build_probe(rows: list, probe: list) -> dict:
    """What the whole-county list says about the by-section sweep beside it.

    Three disjoint groups, and the answer is different for each: a row inside the seven
    declared townships (the sweep must hold it), a row sectioned outside them (out of
    what the deposits declare, and not a hole in them), and a row with NO section (which
    no section query could ever return, and which the deposits therefore cannot hold).
    """
    if not probe:
        return {}
    held = {r["purchase_no"] for r in rows}
    seven = declared_townships()
    inside = [r for r in probe if (r["township"].strip(), r["range"].strip()) in seven]
    sectionless = [r for r in probe if not r["section"].strip()]
    outside = [r for r in probe
               if r["section"].strip() and (r["township"].strip(), r["range"].strip()) not in seven]
    missed = [r for r in inside if r["purchase_no"] not in held]
    # T-1033 read the sectionless group into the deposit, so this group has an answer now
    # and it is the same question asked of it: how many does the domain HOLD?
    missed_sectionless = [r for r in sectionless if r["purchase_no"] not in held]
    missed_outside = [r for r in outside if r["purchase_no"] not in held]
    years, codes = {}, {}
    for r in sectionless:
        y = r["date_purchased"][-4:]
        years[y] = years.get(y, 0) + 1
        m = re.search(r"(CHI[A-Z]*)$", r["legal_description"])
        code = m.group(1) if m else "(no town code)"
        codes[code] = codes.get(code, 0) + 1
    outside_townships = {}
    for r in missed_outside:
        key = "T%s R%s" % (r["township"].strip() or "?", r["range"].strip() or "?")
        outside_townships[key] = outside_townships.get(key, 0) + 1
    return {
        "ticket": PROBE["ticket"],
        "deposit": PROBE["tsv"],
        "query": "county %s alone, no township and no section, walked to the end of the "
                 "results through the More cursor" % PROBE["county"],
        "why": "A section query cannot return a row the register gives no section, so the "
               "by-section sweep could not measure its own completeness. The county's own "
               "list page can, because it holds every row the county holds.",
        "rows_dated_through_%d" % PROBE["through_year"]: len(probe),
        "inside_the_declared_townships": len(inside),
        "of_those_missing_from_the_deposit": len(missed),
        "sectioned_outside_the_declared_townships": len(outside),
        "of_those_missing_from_the_deposit_too": len(missed_outside),
        "carrying_no_section_at_all": len(sectionless),
        "of_those_missing_from_the_deposit_now": len(missed_sectionless),
        "sectionless_by_year": dict(sorted(years.items())),
        "sectionless_by_town_code": dict(sorted(codes.items(), key=lambda kv: -kv[1])),
        "the_seven_townships_are_read_whole": not missed,
        "the_sectionless_rows_are_read_whole": not missed_sectionless,
        "complete_for_%d_cook_county" % PROBE["through_year"]:
            not missed and not missed_sectionless and not missed_outside,
        "what_is_still_outside_it": {
            "rows": len(missed_outside),
            "ticket": "T-1033",
            "what": "Rows the county list gives a section that is NOT in one of the seven "
                    "townships the deposits declare. They are not a hole in this domain — "
                    "no deposit ever promised them — and they are the whole of the "
                    "difference between it and Cook County.",
            "by_township": dict(sorted(outside_townships.items(),
                                       key=lambda kv: (-kv[1], kv[0]))),
        } if missed_outside else None,
        "reading": "TWO of the three groups are now closed. The by-section sweep is READ "
                   "WHOLE for the ground it declares: every one of the %d rows the county "
                   "lists inside the seven declared townships through %d is in the "
                   "deposit. And the %d rows that carry NO section — the ones no section "
                   "query could ever return, every one of them a lot and a block in a "
                   "platted town — were read at their own detail pages by T-1032 and "
                   "joined to the deposit by T-1033: %d of them are held, %d are missing. "
                   "%d of the sectionless carry a town code (%s) where a legal "
                   "description would go and %d carries none at all; this project still "
                   "does not expand those codes, so `tract()` resolves the lot and the "
                   "block and refuses the plat. What is left between this domain and the "
                   "whole of %d Cook County is ONE group and it is named above: %d rows "
                   "sectioned outside the seven townships the deposits declare. Their "
                   "dates are the register's own and are carried unsmoothed, including "
                   "the four this project does not believe."
                   % (len(inside), PROBE["through_year"], len(sectionless),
                      len(sectionless) - len(missed_sectionless), len(missed_sectionless),
                      sum(n for c, n in codes.items() if c.startswith("CHI")),
                      ", ".join(sorted(c for c in codes if c.startswith("CHI"))),
                      sum(n for c, n in codes.items() if not c.startswith("CHI")),
                      PROBE["through_year"], len(missed_outside)),
    }


def deposit_of(name: str) -> dict:
    for d in DEPOSITS:
        if d["tsv"] == name:
            return d
    raise SystemExit("land_sales: no deposit named %s" % name)


def records_name(tsv: str) -> str:
    """The records file a deposit derives: one per deposit, named after it."""
    return "records/entries_" + tsv[len("isa_land_tract_sales_"):-len(".tsv")] + ".json"

# T-0557 read three sections of T39N R14E — 16, 21 and 29 — as truncated: their section
# query returned exactly 150 rows, the database's per-page ceiling, and the pass took
# that for the end of what could be asked. It is not. The results page carries a More
# button whose keyset cursor walks the rest, `harvest_land_sales.py` follows it, and
# T-0675 read all three whole: 337 sales through 1836 in section 16, 4 in 21, 4 in 29,
# against the 154 the first page gave. So no section of these two townships is
# truncated now, and nothing here may say the source cannot be paged.
TRUNCATED = set()

# The database's own abbreviations, expanded only where the expansion is the Archives'
# own and not this project's guess. Anything absent stays as the register wrote it.
SALE_TYPES = {"FD": "federal land sale (cash entry)",
              "SC": "school section sale",
              "CN": "canal land sale"}

COLS = ["purchase_no", "purchaser", "residence", "social_status", "aliquot_or_lot",
        "section", "township", "range", "meridian", "county", "acres", "price_per_acre",
        "total_price", "type_of_sale", "date_purchased", "volume", "page"]

# `LOT8BL47` is a town lot; `E2NE` is a half quarter-section. The two resolve to
# different things on the ground and the distinction is kept structurally rather than
# left for a downstream regex to guess at.
LOT = re.compile(r"^LOT(\d+)BL(\d+)$")
HALF = re.compile(r"^([NSEW])2([NS][EW])(FR|VOID|VO)?$")
QUARTER = re.compile(r"^([NS][EW])([NS][EW])?(FR|VOID|VO)?$")
# A LOT AND A BLOCK IN A PLATTED TOWN (T-1033). `L4BL36CHIOT` is lot 4 of block 36 in
# whatever plat `CHIOT` names; `L2B17CHIOT` is the same thing one letter shorter, and the
# register uses both spellings on the same page. A leading run of halves is a part OF the
# lot — `W2L3B34CHIOT` is the west half, `E2E2L1B46CHI` the east half of the east half —
# and it is carried as written rather than reduced to a fraction, because a half of a half
# is how the clerk described the ground and an eighth is this project's arithmetic.
# The trailing letters are the register's own code for the plat. THEY ARE NOT EXPANDED
# HERE (T-0830's rule, unchanged): the Archives' key for them is not reachable from this
# runner, so the code is carried verbatim as `town_code` and `plat` stays null. Guessing
# which addition `CHIV` names would put a house in the wrong half of the town.
TOWN_LOT = re.compile(r"^((?:[NSEW]2)*)L(\d+)(BL|B)(\d+)([A-Z]*)$")
# THE TOWN CODES THIS READING HAS SEEN, longest first so `CHIOT` never eats `CHIOTV`.
# Membership is all this list is for — a code that is not on it is still carried, and
# still refuses to be a plat.
TOWN_CODES = ("CHIOTVO", "CHIOTV", "CHIOT", "CHIV", "CHI")

SUFFIXES = {"JR", "SR", "II", "III"}


def load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def dump(p: Path, doc) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_tsv(domain: Path) -> list:
    """Every committed deposit, in DEPOSITS order, each row carrying the file it is on.

    A row's citation is a file AND a line, so the file travels with the row: two
    deposits both have a line 2 and they are not the same sale.
    """
    rows = []
    for dep in DEPOSITS:
        path = domain / "text" / dep["tsv"]
        if not path.exists():
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        head = lines[0].split("\t")
        if head != COLS:
            raise SystemExit("land_sales: the deposit's header is not the harvest's header")
        for n, line in enumerate(lines[1:], start=2):
            if not line.strip():
                continue
            cells = line.split("\t")
            if len(cells) != len(COLS):
                raise SystemExit("land_sales: %s line %d has %d cells, not %d"
                                 % (dep["tsv"], n, len(cells), len(COLS)))
            row = dict(zip(COLS, cells))
            row["_line"] = n
            row["_file"] = dep["tsv"]
            rows.append(row)
    return rows


def tract(row: dict) -> dict:
    """The tract a footprint can be resolved against — structured, never smoothed.

    `part` is the aliquot description as the register wrote it. `resolves` says what
    kind of thing it is, because a town lot and a half quarter-section are not the
    same object and a map that treats them alike puts a house in a cornfield.

    `refusal` is what this reading declines to say about the tract, and why. It is set
    and not null wherever the page does not carry the answer — an unparsable sectionless
    tract, a lot with no town code, a town code ending in the letters that mean VOID
    elsewhere. A refusal is a reading, not a gap: it names the question and leaves it
    open rather than settling it with the likelier of two guesses (T-1033).
    """
    part = row["aliquot_or_lot"]
    sectionless = not row["section"].strip()
    t = {"section": row["section"], "township": row["township"], "range": row["range"],
         "meridian": row["meridian"], "part": part, "resolves": "unparsed",
         "lot": None, "block": None, "lot_fraction": None, "town_code": None,
         "plat": None, "void": part.endswith(("VOID", "VO")), "refusal": None}
    m = LOT.match(part)
    if m:
        t["resolves"] = "town_lot"
        t["lot"], t["block"] = m.group(1), m.group(2)
        return t
    if HALF.match(part):
        t["resolves"] = "half_quarter_section"
        return t
    if QUARTER.match(part):
        t["resolves"] = "quarter_section" if len(QUARTER.match(part).group(0).rstrip("FRVOID")) <= 2 \
            else "quarter_quarter_section"
        return t
    # A row the register gives no section is described by a plat, not by the survey, and
    # the two are read by different rules. Asking the aliquot patterns above about
    # `L2BL46CHIOT` and then falling through to `unparsed` was the old behaviour and it
    # said nothing; this branch either resolves the lot and block or says why it will not.
    if sectionless:
        m = TOWN_LOT.match(part)
        if not m:
            t["resolves"] = "refused"
            t["void"] = None
            t["refusal"] = ("The register gives this row no section and its tract is not a "
                            "lot and a block: %r matches no form this reading can parse. "
                            "It is carried as printed and resolved to nothing, because a "
                            "guess here would invent ground." % part)
            return t
        fraction, lot, _sep, block, code = m.groups()
        t["resolves"] = "town_plat_lot"
        t["lot"], t["block"] = lot, block
        t["lot_fraction"] = fraction or None
        t["town_code"] = code or None
        # THE `VO` TRAP (T-1032 named it, T-1033 rules on it). `tract()` reads a trailing
        # `VO` as the register's void mark, and twenty of these rows end `CHIOTVO`. The
        # mark is defined on an ALIQUOT — `E2SEVO`, a half quarter-section struck out —
        # where the letters before it are the survey's own. Here the trailing letters are
        # a town code, so the test is a category error and the answer it gives is noise.
        # The evidence does not settle what `CHIOTVO` is: nineteen of the twenty carry a
        # price between $1,500 and $9,600, which a void sale in this register also does
        # (`E2NEVOID`, $100), and none of the twenty has a `CHIOT` peer on the same lot
        # and block, which a voided-and-resold Original Town lot would be expected to.
        # So this reading REFUSES the question rather than answering it either way: void
        # is null on every town-plat lot, and the refusal is on the record.
        t["void"] = None
        if code and code.endswith("VO"):
            t["refusal"] = ("The town code %r ends in the letters this register uses "
                            "elsewhere to strike a sale out, and nothing reachable here "
                            "says which it is: a void sale of a %s lot, or a fifth plat "
                            "code. The code is carried verbatim and `void` is null — "
                            "neither claimed nor denied (T-1033)." % (code, code[:-2]))
        elif not code:
            t["refusal"] = ("The tract names a lot and a block and no town at all, so "
                            "which plat it belongs to is not on the page (T-1033).")
        elif code not in TOWN_CODES:
            t["refusal"] = ("%r is a town code this reading has never seen. The lot and "
                            "the block are the register's own and stand; the code is "
                            "carried verbatim and is not assumed to be one of the five "
                            "already read (T-1033)." % code)
        return t
    return t


def iso_date(us: str) -> str:
    m = re.match(r"^(\d{2})/(\d{2})/(\d{4})$", us)
    return "%s-%s-%s" % (m.group(3), m.group(1), m.group(2)) if m else us


def normalize_name(as_read: str) -> str:
    """`DEVINPORT WILLIAM` reads back as `William Devinport`. The register's spelling is
    NEVER corrected here — that is what `resident_crosswalk.json` is for.

    A FIRM READS BACK AS A FIRM (T-0851). `GARRETT A ET CO` used to come back as
    `A Et Co Garrett`, which is not a name of anything: the words the register sets
    to say the buyer was a house were being read as forenames and then title-cased.
    A partnership style is EXPANDED and nothing else is touched — `ET CO` and `AND
    CO` are the register's abbreviation for `& Co.`, and expanding an abbreviation
    is not correcting a spelling. What stands before the conjunction is the one
    partner the register names; who else stood in the house is not on the page.
    """
    parts = [p for p in as_read.split() if p]
    if not parts:
        return as_read
    style = namesake.firm_style(" ".join(parts[1:]))
    if style:
        head = [w for w in parts[1:]]
        cut = next(i for i, w in enumerate(head)
                   if w.strip(",.").upper() in namesake.PARTNERSHIP_CONJUNCTIONS
                   and head[i + 1].strip(",.").upper() in namesake.PARTNERSHIP_HEADS)
        partner = " ".join(g.title() if len(g) > 1 else g.upper() for g in head[:cut])
        return (partner + " " + parts[0].title() + " & Co.").strip()
    surname, given = parts[0], parts[1:]
    suffix = ""
    if given and given[-1].upper() in SUFFIXES:
        suffix = " " + given[-1].title()
        given = given[:-1]
    out = " ".join(g.title() if len(g) > 1 else g.upper() for g in given)
    return (out + " " + surname.title() + suffix).strip()


def surname_of(as_read: str) -> str:
    return (as_read.split() or [""])[0].upper()


def givens_of(as_read: str) -> list:
    return [p.upper() for p in as_read.split()[1:] if p.upper() not in SUFFIXES]


def list_name(row: dict) -> str:
    """The query a row was read under, which is what a declaration can promise.

    A sectioned row names its section. A town lot has none to name, so it names the one
    query that could reach it: the county's own list, sectionless (T-1033).
    """
    if not row["section"].strip():
        return "%s county list, no section" % (row["county"] or "?")
    return "T%s R%s sec %s" % (row["township"], row["range"], row["section"])


def build_records(rows: list, start: int = 1) -> dict:
    records = []
    for i, row in enumerate(rows, start=start):
        cook = row["residence"].upper() == "COOK"
        records.append({
            "id": "ls%04d" % i,
            "as_read": row["purchaser"],
            "normalized": normalize_name(row["purchaser"]),
            "locator": {"list": list_name(row), "line": row["_line"],
                        "purchase_no": row["purchase_no"],
                        "volume": row["volume"], "page": row["page"],
                        "text_file": row["_file"]},
            "reading": "transcription_mediated",
            "confidence": "documented" if cook else "inferred",
            "notes": ("The register's Residence column reads COOK: contemporary evidence "
                      "that this purchaser lived in Cook County on %s, and evidence of "
                      "nothing narrower — the county in 1835 reaches far beyond the town."
                      % iso_date(row["date_purchased"])) if cook else
                     ("Residence %r. A purchase is a transaction and not a residence, so "
                      "the row is graded inferred: what it documents is that this name "
                      "entered this tract on %s."
                      % (row["residence"] or "(blank)", iso_date(row["date_purchased"]))),
            "sale": {
                "purchase_no": row["purchase_no"],
                "residence_as_read": row["residence"],
                "social_status_as_read": row["social_status"],
                "date_purchased": iso_date(row["date_purchased"]),
                "date_as_read": row["date_purchased"],
                "acres": row["acres"],
                "price_per_acre": row["price_per_acre"],
                "total_price": row["total_price"],
                "type_of_sale": row["type_of_sale"],
                "type_of_sale_expanded": SALE_TYPES.get(row["type_of_sale"]),
                "county": row["county"],
                "volume": row["volume"],
                "page": row["page"],
            },
            "tract": tract(row),
        })
    return {
        "schema": 1,
        "domain": "land_sales",
        "source_id": SOURCE_ID,
        "generated_by": "tools/read_land_sales.py --build",
        "note": "Every field is the database's own. `normalized` reads the register's "
                "SURNAME FORENAME back as a name and corrects no spelling. `confidence` "
                "is documented only where the register itself states a residence of COOK.",
        "records": records,
    }


def build_coverage(rows: list, probe: list) -> dict:
    # A DECLARATION is a promise that something in the domain reaches the item, and the
    # gate is right to call a declared item nothing reaches a hole. Every section of
    # every township in DEPOSITS was queried; only the ones that returned a sale through
    # 1836 can be declared. The rest were read and were empty, which is a fact worth
    # keeping and is not coverage — so it is kept beside the declaration rather than
    # inside it, one block per deposit, because the two readings are two promises.
    reached = {list_name(r) for r in rows}
    truncated = ["T%s R%s sec %s" % tr for tr in sorted(TRUNCATED)]
    declarations, empty = [], []
    for dep in DEPOSITS:
        if dep.get("sectionless"):
            # Not a grid of sections: one query, the county listed whole, and the group
            # of it that carries no section at all. Every one of those rows was then read
            # at its own detail page, so what is declared is the GROUP and not a township
            # (T-1033). There is no empty-section block to keep beside it, because no
            # section was asked for.
            declarations.append({
                "unit": "list",
                "ticket": dep["ticket"],
                "note": "Read in full: %s's list was walked to its end through the More "
                        "cursor, every row it returned with no section was taken, and "
                        "each of those was then read at its own detail page into %s. A "
                        "section query cannot reach these rows, so this is the only "
                        "query that declares them." % (dep["county"], dep["tsv"]),
                "items": [n for n in sorted(reached)
                          if n == "%s county list, no section" % dep["county"]],
            })
            continue
        queried = ["T%dN R%dE sec %02d" % (tw, rg, sn)
                   for tw, rg in dep["pairs"] for sn in range(1, 37)]
        declarations.append({
            "unit": "list",
            "ticket": dep["ticket"],
            "note": "Read in full: the section query was walked to its end through the "
                    "More cursor, so every sale it holds through 1836 is in %s."
                    % dep["tsv"],
            "items": [n for n in queried if n in reached and n not in truncated],
        })
        empty.append({
            "ticket": dep["ticket"],
            "deposit": dep["tsv"],
            "note": "Walked section by section to the end of the results; the section "
                    "holds no sale dated on or before 31 December 1836. Read, empty, and "
                    "not a hole.",
            "items": [n for n in queried if n not in reached and n not in truncated],
        })
    townships = ", ".join("T%dN R%dE" % tr for dep in DEPOSITS for tr in dep["pairs"])
    return {
        "schema": 1,
        "domain": "land_sales",
        "generated_by": "tools/read_land_sales.py --build",
        "note": "The reading is BY SECTION because a whole-township query stops at the "
                "database's 150-row page and looks complete. %d section queries were run "
                "(%s, third principal meridian, sections 01-36) and each was walked to "
                "its end through the results page's own More button, whose keyset cursor "
                "returns the rows after the last one shown (T-0675). Every section here "
                "is therefore read whole, including the three — 16, 21 and 29 — that "
                "T-0557 declared truncated because it took the first page for the whole. "
                "A declaration promises that a record reaches the item, so a section that "
                "was walked and held no sale through 1836 is listed under "
                "`queried_no_sales_through_1836` instead — read, empty, and not a hole. "
                "T-0676 added the five ring townships, which are the last of what T-0610 "
                "asked for: nothing around the town is unread now. T-0830 then MEASURED "
                "that claim against the whole county, listed in one query, and "
                "`completeness_probe` below is the result: right about every section it "
                "declares, and blind to a row the register gives no section. THAT "
                "BLINDNESS IS CLOSED (T-1033): the third deposit is not read by section "
                "at all — it is the county's own list, the group of it that carries no "
                "section, every row of which is a lot and a block in a platted town and "
                "was read at its own detail page. It declares that group and not a grid."
                % (36 * sum(len(d["pairs"]) for d in DEPOSITS), townships),
        "declarations": declarations,
        "queried_no_sales_through_1836": empty,
        "completeness_probe": build_probe(rows, probe),
        "not_read": {
            "ticket": "T-0676",
            "truncated_at_the_150_row_ceiling": truncated,
            "townships_not_read": [],
            "note": "Nothing is left unread of what T-0610 asked for: T-0675 walked the "
                    "two townships the town stands on to the end of every section, and "
                    "T-0676 did the same for the five ring townships. Both lists are kept "
                    "as the shape a future hole would fill. What remains outside this "
                    "domain is stated in the README and is not a hole in it: purchasers "
                    "whose stated residence is Cook County but whose ground lies "
                    "elsewhere, which the database cannot be asked for, and the canal "
                    "sections, which the land office did not sell. What T-0830 then "
                    "found is a hole of a different shape and it is named in "
                    "`completeness_probe` above: the sweep is complete for every section "
                    "it declares, and Cook County's register also holds sales with NO "
                    "section — town lots described by their plat — which no section "
                    "query can return. T-1032 harvested those and T-1033 read them into "
                    "the third deposit, so they are no longer counted-and-unread. What "
                    "is left between this domain and the whole of 1836 Cook County is "
                    "the rows sectioned OUTSIDE the seven declared townships, and "
                    "`completeness_probe` names them and counts them by township.",
        },
    }


def resident_names() -> list:
    """Every person the residents layer holds, as (id, name, household id)."""
    out = []
    index = load(RESIDENTS / "index.json")
    for entry in index.get("households") or []:
        path = RESIDENTS / entry["file"]
        if not path.exists():
            continue
        hh = load(path)
        for person in hh.get("persons") or []:
            if person.get("name"):
                out.append((person.get("id"), person["name"], hh.get("id")))
    return out


def merged_card_surnames() -> list:
    """(surname a town card printed, the person that card was RULED to be), for every
    ratified card merge that folded a DIFFERENTLY SPELLED surname (T-1001).

    The register spells a purchaser the way its clerk heard him, and so did every list
    the town's cards were minted from. Where two of those spellings turned out to be one
    man, `data/residents/card_merge_rulings.json` says so and
    `tools/consolidate_town_cards.py --apply` lands it: the folded card leaves
    `households/`, its record is kept whole under `merged/`, and `index.json`'s `merged`
    table redirects the id. That table remembers the NAME the folded card carried, which
    is the thing this function needs — because after a merge the surname the register
    printed can vanish from the residents layer entirely, and a purchaser the town has
    already adjudicated then reaches nobody.

    KIMBERLEY EDMUND S is the case it was written for. `kimberley_ed` folded onto
    `kimberly_edmund_s` under C9, and with it went the only Kimberley the layer held; the
    register still prints KIMBERLEY, and without this the entry would be lost to a letter.

    THIS IS NOT A FOLD AND MUST NEVER BECOME ONE. Nothing here compares two spellings or
    measures a distance between them: it reads a WRITTEN RULING that a specific card of
    that specific spelling names a specific person. T-1001 measured what a mechanical
    one-letter fold would do to this domain instead — a new rival for 200 of the 427
    named purchaser spellings, 42 proposals changing shape, 18 hand rulings undercut —
    and `tools/measure_surname_fold.py` prints the table. Ruled, one card at a time, on a
    page: never inferred from a resemblance.
    """
    index = load(RESIDENTS / "index.json")
    table = index.get("merged") or []
    forward = {e["person"]: e.get("merged_into_person") for e in table}

    def survivor_of(pid, seen=None):
        seen = seen or set()
        while pid in forward and pid not in seen:
            seen.add(pid)
            pid = forward[pid]
        return pid

    live = {}
    for entry in index.get("households") or []:
        path = RESIDENTS / entry["file"]
        if not path.exists():
            continue
        for person in load(path).get("persons") or []:
            if person.get("id") and (person.get("name") or "").split():
                live[person["id"]] = person["name"].split()[-1].upper()
    out = []
    for entry in table:
        name = entry.get("name") or ""
        if not name.split():
            continue
        surname = name.split()[-1].upper()
        survivor = survivor_of(entry.get("merged_into_person"))
        # The survivor must still be a person the layer holds — a merge onto a card that
        # was itself later folded is followed above, and a dangling one is simply skipped.
        # And the spelling must actually DIFFER: forty-eight of the forty-nine merges the
        # town has landed fold a card of the same surname, and those add nothing at all.
        if survivor not in live or live[survivor] == surname:
            continue
        out.append((surname, survivor, entry.get("person")))
    return out


def load_rulings(domain: Path) -> dict:
    """The hand-authored rulings, keyed by the purchaser spelling they rule on.

    Absent is legal and means "nobody has ruled yet" — which is the state every spelling
    was in before T-0700, and the state the other twenty-six are still in (T-0850).
    """
    path = domain / RULINGS_NAME
    if not path.exists():
        return {}
    doc = load(path)
    return {r["purchaser_as_read"]: r for r in doc.get("ruled") or []}


def firm_purchaser(as_read: str, style: str, sales: list, record_ids: list,
                   candidates: list, residences: list) -> dict:
    """A partnership that entered ground, recorded as the entity that entered it (T-0851).

    Until this ticket the register's two firms had nowhere to go. One was written onto
    a man's card — Peter Pruyne's paragraph said the register entered HIM as `PRUYNE P
    AND CO` — and the other was refused by hand in `resident_rulings.json`, which left
    A. Garrett & Co.'s eighty acres in the deposit and in no reading of it. This block
    is the reading: what the house bought, when, where, for how much, and the one
    partner the page names.

    WHAT IT DOES NOT SAY. It does not identify the firm with the town's business layer,
    it does not place anybody on the ground, and it does not name a partner the register
    left silent. `names_one_partner` is a PROPOSAL about the partner's name and carries
    the same grade the person rule would have given it — `forename_agrees` or the weaker
    `initial_agrees` — because that is all the page supports. The purchase stays the
    firm's on either verdict.
    """
    def num(v):
        try:
            return float(v)
        except ValueError:
            return 0.0
    partner_as_read = as_read.split()[0] + " " + " ".join(
        w for w in givens_of(as_read)[:_style_cut(as_read)])
    partner_as_read = partner_as_read.strip()
    named = {"as_read": partner_as_read, "resident_id": None, "resident_name": None,
             "household_id": None, "match": None, "rule": None, "rivals": []}
    givens = givens_of(as_read)[:_style_cut(as_read)]
    if candidates and givens:
        ruling = namesake.choose(" ".join(givens), [
            {"key": pid, "name": name, "given": " ".join(name.split()[:-1])}
            for pid, name, hh in candidates])
        if ruling["named"]:
            pid, name, hh = [c for c in candidates if c[0] == ruling["named"]][0]
            named.update({
                "resident_id": pid, "resident_name": name, "household_id": hh,
                "match": ruling["grade"],
                "rule": "%s, the partner %s names, matches %s: %s, and the forename "
                        "agrees %s. THIS IS A PROPOSAL ABOUT THE PARTNER'S NAME AND NOT "
                        "A PURCHASE BY HIM." % (partner_as_read, as_read, name,
                                                ruling["why"],
                                                "in full" if ruling["grade"] == "forename_agrees"
                                                else "as an initial only"),
                "rivals": ruling["rivals"],
            })
        else:
            named["rule"] = "%s, the partner %s names, is refused against every person " \
                            "of the surname: %s." % (partner_as_read, as_read, ruling["why"])
            named["rivals"] = ruling["rivals"]
    elif not candidates:
        named["rule"] = "The residents layer holds nobody of the surname %s." % as_read.split()[0].title()
    return {
        "firm_as_read": as_read,
        "firm_style": style,
        "firm_expanded": normalize_name(as_read),
        "record_ids": record_ids,
        "sales": len(sales),
        "acres_stated": "%.2f" % sum(num(r["acres"]) for r in sales),
        "total_price": "%.2f" % sum(num(r["total_price"]) for r in sales),
        "first_sale": min(iso_date(r["date_purchased"]) for r in sales),
        "last_sale": max(iso_date(r["date_purchased"]) for r in sales),
        "tracts": [dict(tract(r), date_purchased=iso_date(r["date_purchased"]),
                        acres=r["acres"], total_price=r["total_price"]) for r in sales],
        "residence_column": ", ".join(residences),
        "names_one_partner": named,
        "silent_partners": "The register names one partner and abbreviates the rest. Who "
                           "else stood in this house is not on this page, and nothing "
                           "here proposes them.",
        "what_it_evidences": "A partnership of this name entered this ground on this "
                             "date. It is not evidence that the firm kept a house in the "
                             "town, that it stood on the tract, or that the partner the "
                             "register names bought anything himself.",
        "why_it_is_not_a_match": "This crosswalk proposes correspondences between a "
                                 "purchaser and a PERSON, and the purchaser here is not "
                                 "one. The refusal is in refusals[] with this block named "
                                 "as what carries the sale instead.",
    }


def _style_cut(as_read: str) -> int:
    """How many given words stand BEFORE the partnership conjunction."""
    head = givens_of(as_read)
    for i, w in enumerate(head[:-1]):
        if w.strip(",.").upper() in namesake.PARTNERSHIP_CONJUNCTIONS \
                and head[i + 1].strip(",.").upper() in namesake.PARTNERSHIP_HEADS:
            return i
    return len(head)


def build_resident_crosswalk(rows: list, ids: dict, domain: Path = DOMAIN,
                            rulings: dict | None = None) -> dict:
    """Propose a correspondence between a purchaser and a person the town already holds.

    THE SURNAME GATHERS THE RIVALS AND THE FORENAME DECIDES BETWEEN THEM (T-0697).
    Until this ticket the middle clause was a COUNT — exactly one person of the surname
    could exist in the residents layer — and a count of namesakes says nothing about the
    reading in hand. It made the rule fire LESS as the town grew truer: T-0514 seated 531
    people and this crosswalk LOST three rulings with nothing new read. The reading is now
    put to every person of the surname and named onto the one it agrees with, on the merge
    rules this project already ratified (`tools/namesake.py`, which restates identity
    master's M1/M2/M3 and R3/R4 and imports the directories' forename rule). Two
    survivors or none is still a refusal, written out with the rivals NAMED, because an
    absent match reads exactly like a pair nobody looked at — and "there are 5" never said
    which five people refused the reading.
    """
    # `record_ids` is the ruling's anchor: WHICH sales this purchaser spelling was
    # adjudicated from. tools/measure_research_spend.py asks for it in as many words —
    # "a spelling pair whose evidence names no unit this domain has read — write the
    # record id" — and it is provenance either way: a refusal a reader cannot trace back
    # to the rows behind it is a refusal nobody can check.
    by_name, residences = {}, {}
    for row in rows:
        by_name.setdefault(row["purchaser"], []).append(ids[row["purchase_no"]])
        # EVERY row of a spelling, not the first. T-0700: Frank Dill enters the same
        # quarter-section twice on one day and only the SECOND row states COOK, so a
        # first-row read graded him `inferred` and printed `residence_column: UNKNOWN`
        # while the register was saying Cook County on the page. The README's rule is
        # that a COOK row grades `documented` for residence in Cook County on the date
        # of sale; it can only fire if the reading sees the row that carries it.
        seen_res = residences.setdefault(row["purchaser"], [])
        if row["residence"] not in seen_res:
            seen_res.append(row["residence"])
    rulings = load_rulings(domain) if rulings is None else rulings
    people = resident_names()
    by_surname = {}
    for pid, name, hh in people:
        by_surname.setdefault(name.split()[-1].upper(), []).append((pid, name, hh))
    # T-1001. A SURNAME THE TOWN'S OWN CARD PRINTED STILL GATHERS THE MAN IT WAS RULED TO
    # BE. A landed card merge can take the register's spelling out of the residents layer
    # altogether — `kimberley_ed` folded onto `kimberly_edmund_s` and the layer's only
    # Kimberley went with it — and a purchaser this project has already adjudicated would
    # then be refused against nobody. The person is gathered under the folded card's
    # surname and weighed by the ordinary forename rule, with his LIVE card's name, so
    # nothing about the decision is special-cased: only which bucket he stands in. See
    # `merged_card_surnames` for why this is a ruling and not a fold.
    by_person = {pid: (pid, name, hh) for pid, name, hh in people}
    via_merge = {}
    for surname, survivor, folded in merged_card_surnames():
        row = by_person.get(survivor)
        if not row:
            continue
        bucket = by_surname.setdefault(surname, [])
        if all(c[0] != survivor for c in bucket):
            bucket.append(row)
            via_merge[(surname, survivor)] = folded
    matches, refusals, firms, bodies = [], [], [], []
    sales_of = {}
    for row in rows:
        sales_of.setdefault(row["purchaser"], []).append(row)
    seen = set()
    for row in rows:
        as_read = row["purchaser"]
        if as_read in seen:
            continue
        seen.add(as_read)
        surname, givens = surname_of(as_read), givens_of(as_read)
        cook = any(r.upper() == "COOK" for r in residences[as_read])
        candidates = by_surname.get(surname, [])
        # THE BUYER WAS A HOUSE (T-0851), and this is asked before the surname gathers
        # anybody. `GARRETT A ET CO` entered eighty acres in T38N R14E on 1 December
        # 1835; `tools/namesake.py` drops the firm words to compare two readings of one
        # man, so what reached the forename rule was `A`, and `A` names the town's A.
        # Garrett — a house's purchase written onto a man's card. The identification of
        # the firm with him is probably right and is NOT what is refused here; what is
        # refused is spending a partnership's entry as a person's.
        style = namesake.firm_style(" ".join(givens))
        if style:
            firms.append(firm_purchaser(as_read, style, sales_of[as_read],
                                        sorted(by_name[as_read]), candidates,
                                        residences[as_read]))
            named = firms[-1]["names_one_partner"]
            refusals.append({
                "a": as_read,
                "b": (named["resident_name"] if named.get("resident_name")
                      else "(the residents layer)"),
                "rule": "%s is refused against %s: the register sets %r after the name, "
                        "which is the page saying the purchaser was a PARTNERSHIP, and "
                        "this crosswalk proposes correspondences between a purchaser and "
                        "a PERSON. %s"
                        % (as_read,
                           named["resident_name"] if named.get("resident_name")
                           else "every person of the surname",
                           style,
                           ("The identification of the firm with %s is probably right "
                            "and is not what is refused; what is refused is writing the "
                            "house's entry onto his card as his own."
                            % named["resident_name"]) if named.get("resident_name") else
                           "The residents layer holds nobody the firm's named partner "
                           "could be, so there is not even a card to refuse it against."),
                "record_ids": sorted(by_name[as_read]),
                "evidence": ["data/research/land_sales/text/" + row["_file"]],
                "firm": True,
                "firm_style": style,
                "carried_by": "firm_purchasers[]",
            })
            continue
        # THE BUYER WAS A BODY (T-1033), asked immediately after the firm test and for
        # the same reason: a county's lots are not a man's, and a refusal that says so is
        # a reading where a refusal on a missing forename is an accident.
        if BODY_WORDS & set(givens):
            bodies.append({
                "body_as_read": as_read,
                "what_the_register_sold_to": KNOWN_BODIES.get(as_read),
                "record_ids": sorted(by_name[as_read]),
                "lots": len(sales_of[as_read]),
                "residence_column": ", ".join(residences[as_read]),
                "declared": as_read in KNOWN_BODIES,
            })
            refusals.append({
                "a": as_read, "b": "(the residents layer)",
                "rule": "%s is refused against every person: the words the register sets "
                        "after the surname (%s) say the buyer was a BODY and not a man, "
                        "and this crosswalk proposes correspondences between a purchaser "
                        "and a PERSON. Its ground is carried in body_purchasers[] so the "
                        "reading is not lost with the proposal."
                        % (as_read, ", ".join(sorted(BODY_WORDS & set(givens)))),
                "record_ids": sorted(by_name[as_read]),
                "evidence": ["data/research/land_sales/text/" + row["_file"]],
                "body": True,
                "carried_by": "body_purchasers[]",
            })
            continue
        if not givens:
            refusals.append({
                "a": as_read, "b": "(the residents layer)",
                "rule": "%r is a surname with no forename, and a surname-only purchaser "
                        "is always a refusal against %s however well the tract agrees."
                        % (as_read, "(the residents layer)"),
                "record_ids": sorted(by_name[as_read]),
                "evidence": ["data/research/land_sales/text/" + row["_file"]],
            })
            continue
        if not candidates:
            refusals.append({
                "a": as_read, "b": "0 residents named %s" % surname.title(),
                "rule": "%s is refused against 0 residents named %s: the residents layer "
                        "holds nobody of the surname." % (as_read, surname.title()),
                "record_ids": sorted(by_name[as_read]),
                "evidence": ["data/residents/index.json"],
            })
            continue
        ruling = namesake.choose(" ".join(givens), [
            {"key": pid, "name": name, "given": " ".join(name.split()[:-1])}
            for pid, name, hh in candidates])
        if not ruling["named"]:
            rival_names = [r["name"] for r in ruling["rivals"]]
            # A HAND RULING MAY NAME WHAT THE RULE COULD NOT (T-0993). The forename test
            # reads the first token, so a purchaser the register printed by his middle
            # name alone is refused here for ever — and the man may be the best-attested
            # bearer of the surname the town holds. `named` is the ruling that says so,
            # and it may only be made HERE: the surname gathered candidates, and the
            # ruling must name one of them.
            named = rulings.get(as_read)
            if (named and named.get("ruling") == "named"
                    and any(c[0] == named.get("resident_id") for c in candidates)):
                pid, name, hh = [c for c in candidates if c[0] == named["resident_id"]][0]
                matches.append({
                    "purchaser_as_read": as_read,
                    "record_ids": sorted(by_name[as_read]),
                    "resident_id": pid,
                    "resident_name": name,
                    "household_id": hh,
                    "match": "named_by_ruling",
                    "rule": named["reasoning"],
                    "rivals": ruling["rivals"],
                    "residence_column": ", ".join(residences[as_read]),
                    "evidence_grade": "documented" if cook else "inferred",
                    "ruling": {"ruling": "named", "ruled_on": named.get("ruled_on"),
                               "ticket": named.get("ticket"),
                               "checked_against": named.get("checked_against") or [],
                               "reasoning": named["reasoning"]},
                    "was_refused_as": "%s is refused against %s: %s."
                        % (as_read, " and ".join(rival_names) if len(rival_names) <= 3
                           else "%d residents named %s" % (len(candidates), surname.title()),
                           ruling["why"]),
                    "what_it_evidences": (
                        "The register states this purchaser's residence as COOK, so the "
                        "sale is contemporary evidence that a man of this name lived in "
                        "Cook County on the date of sale. It is not evidence that he "
                        "lived in the town."
                        if cook else
                        "A purchase and nothing more. It dates and places a transaction; "
                        "it proposes no residence, and under the ratified ladder it "
                        "corroborates rather than mints."),
                })
                continue
            refusals.append({
                "a": as_read,
                "b": rival_names[0] if len(rival_names) == 1
                     else "%d residents named %s" % (len(candidates), surname.title()),
                "rule": "%s is refused against %s: %s."
                        % (as_read, " and ".join(rival_names) if len(rival_names) <= 3
                           else "%d residents named %s" % (len(candidates), surname.title()),
                           ruling["why"]),
                "rivals": ruling["rivals"],
                "record_ids": sorted(by_name[as_read]),
                "evidence": ["data/residents/index.json"],
            })
            continue
        pid, name, hh = [c for c in candidates if c[0] == ruling["named"]][0]
        grade = ruling["grade"]
        why = "in full" if grade == "forename_agrees" else "as an initial only"
        proposed = "%s matches %s: %s, and the forename agrees %s." % (
            as_read, name, ruling["why"], why)
        # T-1001. Say so where the surname reached this person through a RULED card merge
        # rather than off his live card, because the sentence above would otherwise read
        # as if the layer still spelled him the register's way, and it does not.
        folded_card = via_merge.get((surname, pid))
        if folded_card:
            proposed += (" The surname reaches him through a ruled card merge and not off "
                         "his card: the town held %s until data/residents/"
                         "card_merge_rulings.json folded it onto this person, and the "
                         "register's spelling is the one that card carried."
                         % folded_card)
        # THE RULING, if one has been made — and it is a SECOND decision, not this one.
        # `namesake.choose` above says which person of the surname a reading names; it
        # PROPOSES, and tools/spend_land_sales.py re-adjudicates nothing by its own rule
        # 1, so before T-0700 there was nobody between the proposal and the card. A hand
        # ruling of `refused` moves the proposal out of `matches[]` and states the ruling
        # as the rule that refused it; the card is retracted by spend_land_sales.py
        # --build. The two are held in separate names — `ruling` is the mechanical rule's
        # verdict, `verdict` the hand ruling on it — because collapsing them would let a
        # judgement be read as a derivation.
        verdict = rulings.get(as_read)
        if verdict and verdict.get("ruling") == "refused":
            refusals.append({
                "a": as_read, "b": name,
                "rule": verdict["reasoning"],
                "record_ids": sorted(by_name[as_read]),
                "evidence": ["data/research/land_sales/" + RULINGS_NAME],
                "ruled_on": verdict.get("ruled_on"),
                "ruled_under": verdict.get("ticket"),
                "was_proposed_as": proposed,
            })
            continue
        matches.append({
            "purchaser_as_read": as_read,
            "record_ids": sorted(by_name[as_read]),
            "resident_id": pid,
            "resident_name": name,
            "household_id": hh,
            "match": grade,
            "rule": proposed,
            "via_card_merge": folded_card,
            "rivals": ruling["rivals"] if len(candidates) > 1 else [],
            # EVERY row of the spelling, not the first (T-0700). The register states
            # residence per row, and Frank Dill's second row is the one that says COOK.
            "residence_column": ", ".join(residences[as_read]),
            "evidence_grade": "documented" if cook else "inferred",
            "ruling": ({"ruling": verdict["ruling"], "ruled_on": verdict.get("ruled_on"),
                        "ticket": verdict.get("ticket"),
                        "checked_against": verdict.get("checked_against") or [],
                        "reasoning": verdict["reasoning"]} if verdict else None),
            "what_it_evidences": (
                "The register states this purchaser's residence as COOK, so the sale is "
                "contemporary evidence that a man of this name lived in Cook County on "
                "the date of sale. It is not evidence that he lived in the town."
                if cook else
                "A purchase and nothing more. It dates and places a transaction; it "
                "proposes no residence, and under the ratified ladder it corroborates "
                "rather than mints."),
        })
    # T-0697, and it is the same rule read from the other end. `choose` asks which of
    # several people of a surname a reading names; this asks whether several readings
    # named onto ONE person are one man. `H Bond` is met by both HARVEY and HEMAN and
    # the initial cannot say which, and `WENTWORTH ELIJAH SEN` is the father of
    # `WENTWORTH ELIJAH` against a town holding one card. Both groups are refused
    # whole, with the rival readings named: keeping the first and dropping the rest
    # would be the count of namesakes again, wearing a hat.
    #
    # A HAND-NAMED READING IS NOT PUT TO THIS RULE (T-0993). `collide` asks whether
    # several readings THE MECHANICAL RULE named onto one person are one man, and it
    # asks it with the same forename test that made them — which is exactly the test a
    # `named` ruling exists because it failed. BLANCHARD GURTREY against BLANCHARD F G
    # is "the forenames do not agree", and letting that stand would refuse the whole
    # group: a hand ruling would take three upheld matches down with it. So a
    # `named_by_ruling` match is kept whole and is not a member of any group; the
    # question it would be asked has already been answered, in writing, with sources.
    by_person = {}
    for mt in matches:
        if mt["match"] == "named_by_ruling":
            continue
        by_person.setdefault(mt["resident_id"], []).append(mt)
    kept = []
    for mt in matches:
        if mt["match"] == "named_by_ruling":
            kept.append(mt)
            continue
        group = by_person[mt["resident_id"]]
        if len(group) == 1:
            kept.append(mt)
            continue
        verdict = namesake.collide([{"key": g["purchaser_as_read"],
                                     "given": " ".join(g["purchaser_as_read"].split()[1:])}
                                    for g in group])
        if verdict["same_man"]:
            kept.append(mt)
            continue
        refusals.append({
            "a": mt["purchaser_as_read"], "b": mt["resident_name"],
            "rule": "%s is refused against %s: %s."
                    % (mt["purchaser_as_read"], mt["resident_name"], verdict["why"]),
            "rival_readings": [g["purchaser_as_read"] for g in group
                               if g["purchaser_as_read"] != mt["purchaser_as_read"]],
            "record_ids": mt["record_ids"],
            "evidence": ["data/residents/index.json"],
        })
    matches = kept
    return {
        "schema": 1,
        "domain": "land_sales",
        "generated_by": "tools/read_land_sales.py --build",
        # T-0635. What this file adjudicates FROM, stated once at the top in the narrow
        # form T-0598 asks for. Every ruling below rests on the same deposit — the
        # Illinois public-domain tract-sales database — so a per-entry repetition would
        # say nothing a reader could not read here. Without it the second hop of
        # tools/measure_research_spend.py counted all fourteen matches UNSOURCED, which
        # is that instrument saying, correctly, that a crosswalk which cannot name what
        # it rests on cannot be spent.
        "source_id": SOURCE_ID,
        "note": "PROPOSALS, not identities. Nothing here mints a resident, regrades one, "
                "or writes to data/residents/. T-0514 and T-0515 spend this file. A match "
                "carrying a `ruling` block has been ADJUDICATED (T-0700, "
                "resident_rulings.json); one carrying `ruling: null` is still only what "
                "the mechanical rule proposed, and a refused proposal is in refusals[] "
                "with the ruling as its rule.",
        "ruled": {"upheld": sum(1 for m in matches if (m.get("ruling") or {}).get("ruling") == "upheld"),
                  "named": sum(1 for m in matches if (m.get("ruling") or {}).get("ruling") == "named"),
                  "refused": sum(1 for r in refusals if r.get("ruled_under")),
                  "unruled": sum(1 for m in matches if not m.get("ruling"))},
        "counts": {"purchasers": len({r["purchaser"] for r in rows}),
                   "matched": len(matches), "refused": len(refusals),
                   "firms": len(firms), "bodies": len(bodies)},
        "matches": matches,
        "refusals": refusals,
        # T-0851. The purchasers this crosswalk CANNOT propose, because they are not
        # people — and the block that carries their ground so the reading is not lost
        # with the proposal. Every firm is also in refusals[], so the count of
        # adjudicated spellings stays whole.
        "firm_purchasers": firms,
        # T-1033. The same block for a buyer that is a body rather than a partnership:
        # a county, a school fund, a hotel company. Every one is also in refusals[].
        "body_purchasers": bodies,
    }


def build_crosswalk(rows: list, ids: dict) -> dict:
    """The within-domain identity layer: two spellings in THIS source, one purchaser.

    The only rule strong enough to use here is tract agreement — the same aliquot part
    of the same section entered on dates a fortnight apart, once VOID and once not, is
    the register re-writing an entry it had cancelled. That is a refusal all the same,
    because a re-entry can be a different man buying cancelled ground, and this project
    would rather carry two rows than invent one person.
    """
    by_tract = {}
    for row in rows:
        key = (row["township"], row["range"], row["section"],
               re.sub(r"(VOID|VO|FR)$", "", row["aliquot_or_lot"]))
        by_tract.setdefault(key, []).append(row)
    refusals = []
    for key, group in sorted(by_tract.items()):
        names = sorted({r["purchaser"] for r in group})
        if len(names) < 2:
            continue
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                a, b = names[i], names[j]
                if surname_of(a) == surname_of(b) or givens_of(a) == givens_of(b):
                    refusals.append({
                        "a": a, "b": b,
                        "rule": "%s and %s entered the same tract (T%s R%s sec %s, %s) and "
                                "are not merged: tract agreement is where two spellings "
                                "MIGHT be one man, and it is never proof that they are."
                                % (a, b, key[0], key[1], key[2], key[3]),
                        "record_ids": sorted(ids[r["purchase_no"]] for r in group
                                             if r["purchaser"] in (a, b)),
                        "evidence": sorted({"data/research/land_sales/text/" + r["_file"]
                                            for r in group}),
                    })
    return {
        "schema": 1,
        "domain": "land_sales",
        "generated_by": "tools/read_land_sales.py --build",
        "note": "The ONLY place two differently-spelled names in this domain may become "
                "one person, in data/research/newspapers/identity.json's shape and under "
                "its rules. No merge is made here at all, and every near-pair the tract "
                "index found is written out as a refusal so the next pass does not have "
                "to find them again.",
        "passes": [{
            "ticket": dep["ticket"],
            "what": "Every pair of differently-spelled purchasers entering the same tract "
                    "in %s through 1836."
                    % " and ".join("T%dN R%dE" % tr for tr in dep["pairs"]),
            "merges": 0,
            "refusals": sum(1 for r in refusals
                            if "data/research/land_sales/text/" + dep["tsv"] in r["evidence"]),
        } for dep in DEPOSITS],
        "merges": [],
        "refusals": refusals,
    }


def build_entries(rows: list, records: list) -> dict:
    """`entries.json` — the flat, verbatim list T-0557 asked for, one object per sale."""
    return {
        "schema": 1,
        "domain": "land_sales",
        "source_id": SOURCE_ID,
        "generated_by": "tools/read_land_sales.py --build",
        "scope": "Third principal meridian, %s, every sale dated on or before "
                 "31 December 1836 — and, from T-1033, every sale Cook County's register "
                 "gives NO section at all through the same date: a lot and a block in a "
                 "platted town, which no township can hold because the register states "
                 "none."
                 % ", ".join("T%dN R%dE" % tr for dep in DEPOSITS for tr in dep["pairs"]),
        "note": "Fields are the database's own, unsummarised. `tract` is derived and is "
                "the only computed field here.",
        "count": len(rows),
        "entries": [{
            "record_id": rec["id"],
            "purchase_no": row["purchase_no"],
            "purchaser_as_read": row["purchaser"],
            "purchaser_normalized": rec["normalized"],
            "residence_as_read": row["residence"],
            "social_status_as_read": row["social_status"],
            "aliquot_or_lot_as_read": row["aliquot_or_lot"],
            "section": row["section"], "township": row["township"],
            "range": row["range"], "meridian": row["meridian"], "county": row["county"],
            "acres": row["acres"], "price_per_acre": row["price_per_acre"],
            "total_price": row["total_price"], "type_of_sale": row["type_of_sale"],
            "date_purchased": iso_date(row["date_purchased"]),
            "date_purchased_as_read": row["date_purchased"],
            "volume": row["volume"], "page": row["page"],
            "tract": rec["tract"],
        } for row, rec in zip(rows, records)],
    }


GENERATED = tuple(records_name(d["tsv"]) for d in DEPOSITS) + (
    "entries.json", "coverage.json", "crosswalk.json", "resident_crosswalk.json")


def derive(domain: Path) -> dict:
    """Every generated file, from every committed deposit.

    One records file PER DEPOSIT, named after it, and the ids run on across them in
    DEPOSITS order — so the second reading appends to the first rather than renumbering
    the ids data/structures/*.json already cite.
    """
    rows = read_tsv(domain)
    out, ordered, n = {}, [], 1
    for dep in DEPOSITS:
        mine = [r for r in rows if r["_file"] == dep["tsv"]]
        recs = build_records(mine, start=n)
        n += len(mine)
        out[records_name(dep["tsv"])] = recs
        ordered += recs["records"]
    ids = {row["purchase_no"]: rec["id"] for row, rec in zip(rows, ordered)}
    out["entries.json"] = build_entries(rows, ordered)
    out["coverage.json"] = build_coverage(rows, read_probe(domain))
    out["crosswalk.json"] = build_crosswalk(rows, ids)
    out["resident_crosswalk.json"] = build_resident_crosswalk(rows, ids, domain)
    return out


def build(domain: Path = DOMAIN, quiet: bool = False) -> int:
    out = derive(domain)
    bad = []
    # T-0851. A firm the reading found and nobody declared is a purchaser that reaches
    # no card, no business and no eye. It stops the build rather than passing quietly.
    undeclared = [f["firm_as_read"] for f in out["resident_crosswalk.json"]["firm_purchasers"]
                  if f["firm_as_read"] not in KNOWN_FIRMS]
    for spelling in undeclared:
        bad.append("land_sales: %r is a partnership the register sells to and it is not in "
                   "KNOWN_FIRMS — read the rows it entered, then declare the spelling "
                   "(tools/read_land_sales.py, T-0851)" % spelling)
    undeclared_bodies = [b["body_as_read"] for b in
                         out["resident_crosswalk.json"]["body_purchasers"]
                         if not b["declared"]]
    for spelling in undeclared_bodies:
        bad.append("land_sales: %r is a buyer the register's own words mark as a BODY and "
                   "it is not in KNOWN_BODIES — read the rows it entered, then declare "
                   "what the page says it was (tools/read_land_sales.py, T-1033)"
                   % spelling)
    # T-1033: these were appended to a name that does not exist here, so an undeclared
    # firm crashed the build with a NameError instead of naming itself. It is meant to
    # stop the build, and now it stops it by saying which spelling stopped it.
    if bad:
        for line in bad:
            print(line)
        return 1
    for rel, doc in out.items():
        dump(domain / rel, doc)
    if not quiet:
        x = out["resident_crosswalk.json"]["counts"]
        print("land sales: %d sales, %d purchasers, %d matched, %d refused"
              % (out["entries.json"]["count"], x["purchasers"], x["matched"], x["refused"]))
    return 0


def check_rulings(domain: Path, rows: list, ids: dict) -> list:
    """The rulings file is hand-authored, so the gate reads it rather than re-deriving it.

    What it holds: a ruling names a spelling the register actually sold to, it rules on a
    proposal the mechanical rule actually made, it agrees with that proposal about WHO is
    being ruled on, and it says on the record what kind of ruling it is and why. A ruling
    that fails any of those rules on nothing at all.

    A `named` ruling is the one that does NOT rule on a proposal, because there is none —
    it gives a match the mechanical rule refused (T-0993). Its guards are the mirror of
    the others and are no looser: the spelling must be one the rule refused AFTER the
    surname gathered rivals, so a surname-only purchaser stays the refusal this domain's
    README says it always is; and the person named must be one of those rivals, so a
    ruling cannot reach outside the surname to somebody nobody weighed.
    """
    path = domain / RULINGS_NAME
    if not path.exists():
        return []
    doc = load(path)
    bad = []
    if doc.get("schema") != 1:
        bad.append("land_sales: %s: schema must be 1" % RULINGS_NAME)
    mechanical = build_resident_crosswalk(rows, ids, domain, rulings={})
    proposed = {m["purchaser_as_read"]: m["resident_id"] for m in mechanical["matches"]}
    # The refusals a `named` ruling may overturn: the ones the FORENAME made, which are
    # the only ones carrying `rivals`. A surname-only refusal and a surname the layer
    # holds nobody of both land here without one, and neither is reachable.
    nameable = {r["a"]: [v["key"] for v in r["rivals"]]
                for r in mechanical["refusals"] if r.get("rivals")}
    mechanically_refused = {r["a"] for r in mechanical["refusals"]}
    seen = set()
    for r in doc.get("ruled") or []:
        who = r.get("purchaser_as_read")
        if who in seen:
            bad.append("land_sales: %s: %r is ruled on twice" % (RULINGS_NAME, who))
        seen.add(who)
        if r.get("ruling") == "named":
            if who in proposed:
                bad.append("land_sales: %s: %r is NAMED by hand and the mechanical rule "
                           "already proposes %r — uphold or refuse it, do not name it"
                           % (RULINGS_NAME, who, proposed[who]))
            elif who not in nameable:
                bad.append("land_sales: %s: %r cannot be named: the rule refused it "
                           "before any person of the surname was weighed, and a ruling "
                           "may only choose among the rivals it names"
                           % (RULINGS_NAME, who))
            elif r.get("resident_id") not in nameable[who]:
                bad.append("land_sales: %s: %r is named onto %r, who is not among the "
                           "%d resident(s) of the surname the rule weighed"
                           % (RULINGS_NAME, who, r.get("resident_id"), len(nameable[who])))
        elif who not in proposed:
            # T-1033: UNLESS THE RULE HAS CAUGHT UP WITH IT. T-0700 refused WILSON
            # JOHN L against the town's one John Wilson by hand. Joining the town lots
            # gave `namesake.collide` a second reading of that surname — the register
            # also sells to WILSON JOHN S — so the rule now refuses the spelling on its
            # own, before any hand ruling is consulted, and there is no proposal left for
            # the ruling to move. Rule and ruling AGREE; the ruling is superseded, not
            # empty, and its reasoning is still what refusals[] carries. An `upheld` or
            # `named` ruling in this position is a different thing and still fails here,
            # because it would name a person the rule no longer reaches at all.
            if r.get("ruling") == "refused" and who in mechanically_refused:
                continue
            bad.append("land_sales: %s: %r is not a purchaser the crosswalk proposed a "
                       "match for — a ruling on nothing" % (RULINGS_NAME, who))
            continue
        elif r.get("resident_id") != proposed[who]:
            bad.append("land_sales: %s: %r is ruled against %r and the crosswalk proposed "
                       "%r" % (RULINGS_NAME, who, r.get("resident_id"), proposed[who]))
        if r.get("ruling") not in RULING_KINDS:
            bad.append("land_sales: %s: %r has ruling %r, not one of %s"
                       % (RULINGS_NAME, who, r.get("ruling"), ", ".join(RULING_KINDS)))
        for field in ("ruled_on", "ticket", "reasoning"):
            if not (r.get(field) or "").strip():
                bad.append("land_sales: %s: %r states no %s" % (RULINGS_NAME, who, field))
        if not (r.get("checked_against") or []):
            bad.append("land_sales: %s: %r names nothing it was checked against — a "
                       "judgement nobody can go back to" % (RULINGS_NAME, who))
    return bad


def check_harvested(domain: Path) -> list:
    """The town-lot harvest still says what the probe said, row for row (T-1032).

    Not a derivation — nothing downstream is built from this file yet — so the gate can
    only ask whether the harvest is FAITHFUL: the same 619 purchase numbers the probe
    found sectionless, no more and no fewer; the purchaser, date and legal description
    the list page printed, unchanged by the detail page; and Section, Township, Range and
    Meridian still empty, because a row that arrived with a section was never one of
    these and its presence would mean the wrong page was read.
    """
    probe = read_probe(domain)
    if not probe:
        return []      # no list to be faithful to; the self-test's fixture is one
    path = domain / "text" / HARVESTED["tsv"]
    if not path.exists():
        return ["land_sales: %s is declared and not committed (%s)"
                % (HARVESTED["tsv"], HARVESTED["ticket"])]
    lines = path.read_text(encoding="utf-8").splitlines()
    if lines[0].split("\t") != COLS:
        return ["land_sales: %s: header is not the harvest's header" % HARVESTED["tsv"]]
    got = {}
    bad = []
    for n, line in enumerate(lines[1:], start=2):
        if not line.strip():
            continue
        cells = line.split("\t")
        if len(cells) != len(COLS):
            bad.append("land_sales: %s line %d has %d cells, not %d"
                       % (HARVESTED["tsv"], n, len(cells), len(COLS)))
            continue
        got[cells[0]] = dict(zip(COLS, cells))
    if bad:
        return bad
    want = {r["purchase_no"]: r for r in probe if not r["section"].strip()}
    for pno in sorted(set(want) - set(got)):
        bad.append("land_sales: %s: the probe lists sectionless sale %s and the harvest "
                   "has no detail page for it" % (HARVESTED["tsv"], pno))
    for pno in sorted(set(got) - set(want)):
        bad.append("land_sales: %s: %s is not one of the probe's sectionless rows"
                   % (HARVESTED["tsv"], pno))
    for pno in sorted(set(got) & set(want)):
        row, listed = got[pno], want[pno]
        for col, on_list in (("purchaser", "purchaser"),
                             ("date_purchased", "date_purchased"),
                             ("aliquot_or_lot", "legal_description")):
            if row[col] != listed[on_list]:
                bad.append("land_sales: %s: %s's detail page says %s %r and the list page "
                           "says %r — the harvest is not the rows it was drawn from"
                           % (HARVESTED["tsv"], pno, col, row[col], listed[on_list]))
        for col in ("section", "township", "range", "meridian"):
            if row[col].strip():
                bad.append("land_sales: %s: %s carries %s %r and a sectionless row carries "
                           "none" % (HARVESTED["tsv"], pno, col, row[col]))
    return bad[:20]


def check(domain: Path = DOMAIN, quiet: bool = False) -> list:
    bad = []
    missing = [d["tsv"] for d in DEPOSITS if not (domain / "text" / d["tsv"]).exists()]
    if missing:
        return ["land_sales: the deposit %s is not committed" % m for m in missing]
    bad += check_harvested(domain)
    rows = read_tsv(domain)
    ordered, n = [], 1
    for dep in DEPOSITS:
        mine = [r for r in rows if r["_file"] == dep["tsv"]]
        ordered += build_records(mine, start=n)["records"]
        n += len(mine)
    bad += check_rulings(domain, rows,
                         {row["purchase_no"]: rec["id"] for row, rec in zip(rows, ordered)})
    out = derive(domain)
    # T-0851. A firm the reading found and nobody declared is a purchaser that reaches
    # no card, no business and no eye. It stops the build rather than passing quietly.
    undeclared = [f["firm_as_read"] for f in out["resident_crosswalk.json"]["firm_purchasers"]
                  if f["firm_as_read"] not in KNOWN_FIRMS]
    for spelling in undeclared:
        bad.append("land_sales: %r is a partnership the register sells to and it is not in "
                   "KNOWN_FIRMS — read the rows it entered, then declare the spelling "
                   "(tools/read_land_sales.py, T-0851)" % spelling)
    undeclared_bodies = [b["body_as_read"] for b in
                         out["resident_crosswalk.json"]["body_purchasers"]
                         if not b["declared"]]
    for spelling in undeclared_bodies:
        bad.append("land_sales: %r is a buyer the register's own words mark as a BODY and "
                   "it is not in KNOWN_BODIES — read the rows it entered, then declare "
                   "what the page says it was (tools/read_land_sales.py, T-1033)"
                   % spelling)
    for rel, doc in out.items():
        path = domain / rel
        if not path.exists():
            bad.append("land_sales: %s is not committed — run --build" % rel)
            continue
        if load(path) != doc:
            bad.append("land_sales: %s has drifted from the deposit — it is generated by "
                       "tools/read_land_sales.py --build and must not be hand-edited" % rel)
    if not bad and not quiet:
        print("land sales: %d sales re-derived from the deposit, no drift"
              % out["entries.json"]["count"])
    return bad


def _fixture(tmp: Path) -> Path:
    d = tmp / "land_sales"
    (d / "text").mkdir(parents=True)
    (d / "text" / DEPOSITS[0]["tsv"]).write_text(
        "\t".join(COLS) + "\n"
        + "\t".join(["0000001", "CHIPMAN ANSEL", "COOK", "", "E2NE", "04", "39N", "14E",
                     "3", "COOK", "80.00", "1.25", "100.00", "FD", "11/17/1834", "687",
                     "267"]) + "\n"
        + "\t".join(["0000002", "BRIGGS", "UNKNOWN", "", "LOT8BL47", "07", "39N", "14E",
                     "3", "COOK", "0000.00", "000.00", "40.00", "SC", "10/24/1833", "817",
                     "029"]) + "\n"
        # Section 16 is the school section, the deepest of the three the More cursor
        # opened (T-0675). A sale in it must reach coverage like any other; until then
        # the fixture could not tell "declared read" from "refused as truncated" at all.
        + "\t".join(["0000003", "HALE JOHN", "UNKNOWN", "", "LOT2BL79", "16", "39N",
                     "14E", "3", "COOK", "0000.00", "000.00", "60.00", "SC",
                     "10/22/1833", "817", "100"]) + "\n"
        # A SECOND row for the same purchaser spelling, and the COOK one is the second.
        # T-0700: build_resident_crosswalk read the residence off the first row of a
        # spelling, so a purchaser whose Cook County row came second was graded inferred
        # while the register said COOK on the page. Frank Dill is the real case.
        + "\t".join(["0000005", "HALE JOHN", "COOK", "", "LOT3BL79", "16", "39N",
                     "14E", "3", "COOK", "0000.00", "000.00", "60.00", "SC",
                     "10/22/1833", "817", "101"]) + "\n"
        # THE READING NO FORENAME RULE CAN REACH (T-0993). The register prints Francis
        # Gurtrey Blanchard's MIDDLE name in the forename's place, so `namesake.choose`
        # weighs GURTREY against every Blanchard the town holds and names none of them.
        # It is here so the `named` ruling has something to name, and so the guard that
        # a `named` ruling may only choose among the rivals the rule weighed has a real
        # cluster to be held against. LAST, so the ids above it do not move.
        + "\t".join(["0000006", "BLANCHARD GURTREY", "UNKNOWN", "", "LOT1BL2", "16",
                     "39N", "14E", "3", "COOK", "0000.00", "000.00", "32.00", "SC",
                     "10/22/1833", "817", "027"]) + "\n", encoding="utf-8")
    # The second deposit — the ring townships (T-0676). It is in the fixture because a
    # reading spread over two files is exactly what can go wrong quietly: ids that
    # restart, a coverage block that declares one file's sections against the other's
    # rows, a citation that names the wrong deposit.
    (d / "text" / DEPOSITS[1]["tsv"]).write_text(
        "\t".join(COLS) + "\n"
        + "\t".join(["0000004", "HUNTER EDWARD E", "UNKNOWN", "", "E2SW", "02", "38N",
                      "14E", "3", "COOK", "80.00", "1.25", "100.00", "FD", "11/15/1834",
                      "687", "260"]) + "\n"
        # A FIRM (T-0851), on the tract and the day the register really records it. The
        # page sets `ET CO` after the name; those words used to fold away before the
        # forename rule was asked, so `A` named the town's A. Garrett and a house's
        # eighty acres were proposed as a man's purchase.
        + "\t".join(["0000006", "GARRETT A ET CO", "UNKNOWN", "", "W2SW", "33", "38N",
                      "14E", "3", "COOK", "80.00", "1.25", "100.00", "FD", "12/01/1835",
                      "687", "300"]) + "\n", encoding="utf-8")
    # The third deposit — the town lots (T-1033). Five REAL rows of the committed file,
    # chosen because each is a different thing the tract grammar has to do: the plain
    # `BL` spelling, a half of a half, the `CHIOTVO` code whose last two letters mean
    # VOID everywhere else in this register, a tract that names a lot and a block and no
    # town, and one the parser must refuse rather than guess at. They are LAST so the ids
    # above them do not move, which is the whole point of appending a deposit.
    (d / "text" / DEPOSITS[2]["tsv"]).write_text(
        "\t".join(COLS) + "\n"
        + "\t".join(["0362468", "BEAUBIEN J B", "UNKNOWN", "I", "L4BL36CHIOT", "", "", "",
                      "", "COOK", "0000.00", "000.00", "37.00", "CN", "09/27/1830",
                      "L5A", "013"]) + "\n"
        + "\t".join(["0363250", "DALTON GEORGE", "UNKNOWN", "", "E2E2L1B46CHI", "", "",
                      "", "", "COOK", "0000.00", "000.00", "343.75", "CN", "06/25/1836",
                      "L5A", "016"]) + "\n"
        + "\t".join(["0364011", "HALE EBENEZER", "UNKNOWN", "", "L4BL6CHIOTVO", "", "",
                      "", "", "COOK", "0000.00", "000.00", "7310.00", "CN", "06/21/1836",
                      "L5A", "002"]) + "\n"
        + "\t".join(["0514846", "COOK CNTY COM", "UNKNOWN", "", "L6BL17", "", "", "",
                      "", "COOK", "0000.00", "000.00", "00000.00", "CN", "11/10/1831",
                      "L5A", "005"]) + "\n"
        + "\t".join(["0365596", "PERKINS EPH JR", "UNKNOWN", "", "L1013CHIOT", "", "",
                      "", "", "COOK", "0000.00", "000.00", "5100.00", "CN", "06/24/1836",
                      "L5A", "004"]) + "\n", encoding="utf-8")
    build(d, quiet=True)
    return d


def self_test() -> int:
    fired = []
    with tempfile.TemporaryDirectory() as td:
        d = _fixture(Path(td))
        if check(d, quiet=True):
            print("SELF-TEST: the fixture is not green to begin with"); return 1

        recs = load(d / records_name(DEPOSITS[0]["tsv"]))
        if recs["records"][0]["confidence"] != "documented":
            print("SELF-TEST: a COOK residence must grade documented"); return 1
        fired.append("a COOK residence grades documented")
        if recs["records"][1]["confidence"] != "inferred":
            print("SELF-TEST: a purchase with no stated residence must grade inferred"); return 1
        fired.append("a purchase with no stated residence grades inferred")

        cross = load(d / "resident_crosswalk.json")
        # T-0851. A firm is not a person, and the reading of it is not lost with the
        # proposal: it is refused against every person AND carried in its own block.
        firm = [f for f in cross["firm_purchasers"] if f["firm_as_read"] == "GARRETT A ET CO"]
        if len(firm) != 1:
            print("SELF-TEST: a partnership must reach firm_purchasers[]"); return 1
        if any(m["purchaser_as_read"] == "GARRETT A ET CO" for m in cross["matches"]):
            print("SELF-TEST: a partnership must never be proposed as a person"); return 1
        if firm[0]["firm_expanded"] != "A Garrett & Co.":
            print("SELF-TEST: a firm must read back as a firm, not as 'A Et Co Garrett'"); return 1
        if firm[0]["names_one_partner"]["resident_id"] != "garrett_a":
            print("SELF-TEST: the partner the register names is still proposed, as a partner"); return 1
        if firm[0]["acres_stated"] != "80.00":
            print("SELF-TEST: the firm's block must carry the ground it entered"); return 1
        gref = [r for r in cross["refusals"] if r["a"] == "GARRETT A ET CO"]
        if not gref or gref[0].get("carried_by") != "firm_purchasers[]":
            print("SELF-TEST: a firm's refusal must say what carries the sale instead"); return 1
        fired.append("a partnership is refused as a person and carried as a firm")
        briggs = [r for r in cross["refusals"] if r["a"] == "BRIGGS"]
        if not briggs:
            print("SELF-TEST: a surname-only purchaser must be refused"); return 1
        fired.append("a surname-only purchaser is refused")
        # A ruling that names no record is a ruling nobody can check, and the spend
        # meter counts it as nothing at all.
        if briggs[0].get("record_ids") != ["ls0002"]:
            print("SELF-TEST: a refusal must name the records it was made from"); return 1
        fired.append("a refusal names the records it was made from")

        hale = [m for m in cross["matches"] if m["purchaser_as_read"] == "HALE JOHN"]
        if not hale or hale[0]["evidence_grade"] != "documented":
            print("SELF-TEST: a COOK row anywhere in a spelling must grade the match "
                  "documented, not only a COOK row that comes first"); return 1
        if hale[0]["residence_column"] != "UNKNOWN, COOK":
            print("SELF-TEST: the match must print every residence its rows state"); return 1
        fired.append("a COOK row that is not the first still grades the match documented")

        # THE RULING LAYER (T-0700). A refusal moves the proposal out of matches[] and
        # states the ruling as the rule that refused it — and the gate refuses a ruling
        # that rules on a proposal nobody made.
        rulings = d / RULINGS_NAME
        dump(rulings, {"schema": 1, "ruled": [{
            "purchaser_as_read": "HALE JOHN", "resident_id": hale[0]["resident_id"],
            "ruling": "refused", "ruled_on": "2026-09-05", "ticket": "T-0700",
            "checked_against": ["the fixture"], "reasoning": "the fixture refuses it"}]})
        build(d, quiet=True)
        cross = load(d / "resident_crosswalk.json")
        if any(m["purchaser_as_read"] == "HALE JOHN" for m in cross["matches"]):
            print("SELF-TEST: a refused ruling must leave matches[]"); return 1
        ref = [r for r in cross["refusals"] if r["a"] == "HALE JOHN"]
        if not ref or ref[0].get("ruled_under") != "T-0700":
            print("SELF-TEST: a refused ruling must land in refusals[] naming its ticket")
            return 1
        if cross["ruled"]["refused"] != 1:
            print("SELF-TEST: the crosswalk must count what has been ruled"); return 1
        fired.append("a refused ruling moves the proposal into refusals[] under its ticket")

        doc = load(rulings)
        doc["ruled"][0]["purchaser_as_read"] = "NOBODY AT ALL"
        dump(rulings, doc)
        if not check(d, quiet=True):
            print("SELF-TEST: a ruling on a proposal nobody made did not fail the gate")
            return 1
        fired.append("a ruling on a proposal nobody made fails the gate")
        doc["ruled"][0].update({"purchaser_as_read": "HALE JOHN", "reasoning": ""})
        dump(rulings, doc)
        if not check(d, quiet=True):
            print("SELF-TEST: a ruling with no reasoning did not fail the gate"); return 1
        fired.append("a ruling that states no reasoning fails the gate")

        # THE `named` RULING (T-0993). The other direction of the same layer: a hand
        # ruling GIVES a match the forename rule refused, and the gate holds it to the
        # mirror of the guards `upheld` and `refused` are held to.
        gurtrey = [r for r in cross["refusals"] if r["a"] == "BLANCHARD GURTREY"]
        if not gurtrey or not gurtrey[0].get("rivals"):
            print("SELF-TEST: a middle name in the forename's place must be refused "
                  "with the rivals named"); return 1
        fired.append("a reading the forename rule cannot place is refused with rivals")
        dump(rulings, {"schema": 1, "ruled": [{
            "purchaser_as_read": "BLANCHARD GURTREY",
            "resident_id": gurtrey[0]["rivals"][0]["key"],
            "ruling": "named", "ruled_on": "2026-09-10", "ticket": "T-0993",
            "checked_against": ["the fixture"], "reasoning": "the fixture names it"}]})
        build(d, quiet=True)
        if check(d, quiet=True):
            print("SELF-TEST: a named ruling on a reading the rule weighed rivals for "
                  "must pass the gate"); return 1
        named = [m for m in load(d / "resident_crosswalk.json")["matches"]
                 if m["purchaser_as_read"] == "BLANCHARD GURTREY"]
        if not named or named[0]["match"] != "named_by_ruling":
            print("SELF-TEST: a named ruling must move the refusal into matches[]")
            return 1
        if not named[0].get("was_refused_as"):
            print("SELF-TEST: a named match must carry the refusal it overturned")
            return 1
        fired.append("a named ruling moves a refusal into matches[] under its ticket")

        doc = load(rulings)
        doc["ruled"][0]["purchaser_as_read"] = "BRIGGS"
        dump(rulings, doc)
        if not check(d, quiet=True):
            print("SELF-TEST: a named ruling on a surname-only purchaser did not fail "
                  "the gate"); return 1
        fired.append("a named ruling cannot reach a surname-only purchaser")
        doc["ruled"][0].update({"purchaser_as_read": "BLANCHARD GURTREY",
                                "resident_id": "nobody_at_all"})
        dump(rulings, doc)
        if not check(d, quiet=True):
            print("SELF-TEST: a named ruling onto somebody outside the rivals did not "
                  "fail the gate"); return 1
        fired.append("a named ruling cannot reach outside the rivals the rule weighed")

        # A RULING THE RULE HAS CAUGHT UP WITH (T-1033). `COOK CNTY COM` is refused by
        # the rule itself — the forename names none of the Cooks the layer holds — so a
        # hand REFUSAL of it has no proposal to move and agrees with the rule anyway.
        # That is not a ruling on nothing. An UPHELD one in the same place is, and the
        # gate must still say so, because it would name a person nothing reaches.
        dump(rulings, {"schema": 1, "ruled": [
            {"purchaser_as_read": "COOK CNTY COM", "resident_id": "cook_daniel",
             "ruling": "refused", "ruled_on": "2026-09-11", "ticket": "T-1033",
             "checked_against": ["the fixture"], "reasoning": "a county is not a man"}]})
        build(d, quiet=True)
        if check(d, quiet=True):
            print("SELF-TEST: a refusal the rule also makes must not read as a ruling on "
                  "nothing"); return 1
        fired.append("a hand refusal the rule has caught up with still passes the gate")
        doc = load(rulings)
        doc["ruled"][0]["ruling"] = "upheld"
        dump(rulings, doc)
        build(d, quiet=True)
        if not check(d, quiet=True):
            print("SELF-TEST: an upheld ruling on a proposal the rule refuses did not "
                  "fail the gate"); return 1
        fired.append("an upheld ruling on a proposal the rule refuses fails the gate")

        rulings.unlink()
        build(d, quiet=True)
        cross = load(d / "resident_crosswalk.json")

        ring = load(d / records_name(DEPOSITS[1]["tsv"]))
        if [r["id"] for r in ring["records"]] != ["ls0006", "ls0007"]:
            print("SELF-TEST: the second deposit's ids must continue the first's"); return 1
        if ring["records"][0]["locator"]["text_file"] != DEPOSITS[1]["tsv"]:
            print("SELF-TEST: a record must cite the deposit it is on"); return 1
        fired.append("a second deposit appends its ids and cites its own file")

        # THE TOWN LOTS (T-1033). A lot and a block in a platted town is a different
        # object from a quarter-section, and the whole reason the 619 sat outside the
        # deposits for a fortnight was that `tract()` had no way to say so.
        lots = load(d / records_name(DEPOSITS[2]["tsv"]))
        if [r["id"] for r in lots["records"]][0] != "ls0008":
            print("SELF-TEST: the third deposit's ids must continue the second's"); return 1
        fired.append("a third deposit appends its ids after the second's")
        by_pno = {r["locator"]["purchase_no"]: r["tract"] for r in lots["records"]}
        plain = by_pno["0362468"]
        if plain["resolves"] != "town_plat_lot" or (plain["lot"], plain["block"]) != ("4", "36"):
            print("SELF-TEST: a lot and a block in a platted town must resolve"); return 1
        if plain["town_code"] != "CHIOT" or plain["plat"] is not None:
            print("SELF-TEST: a town code is carried verbatim and never expanded to a plat")
            return 1
        if plain["section"].strip():
            print("SELF-TEST: a sectionless row must never acquire a section"); return 1
        fired.append("a town lot resolves its lot and block and refuses to name the plat")
        half = by_pno["0363250"]
        if half["lot_fraction"] != "E2E2" or half["lot"] != "1":
            print("SELF-TEST: a half of a half of a lot is carried as the clerk wrote it")
            return 1
        fired.append("a part OF a town lot keeps the register's own fractions")
        vo = by_pno["0364011"]
        if vo["void"] is not None or "VOID" not in (vo["refusal"] or "").upper():
            print("SELF-TEST: a CHIOTVO lot must neither be called void nor called valid")
            return 1
        if vo["town_code"] != "CHIOTVO":
            print("SELF-TEST: the CHIOTVO code is carried whole, not split at the VO")
            return 1
        fired.append("a town code ending in VO leaves `void` null and states the question")
        bare = by_pno["0514846"]
        if bare["town_code"] is not None or not bare["refusal"]:
            print("SELF-TEST: a lot and block naming no town must say the plat is not on "
                  "the page"); return 1
        fired.append("a lot and block naming no town refuses the plat and says why")
        refused = by_pno["0365596"]
        if refused["resolves"] != "refused" or refused["lot"] is not None:
            print("SELF-TEST: an unparsable sectionless tract must refuse, not guess")
            return 1
        if not (refused["refusal"] or "").strip():
            print("SELF-TEST: a refusal must state its reason"); return 1
        fired.append("an unparsable sectionless tract is refused with a stated reason")
        # The school section's `LOT5BL3` is a town lot too and is read by the OTHER
        # grammar, in aliquot space, with a section on the row. The two must not collide.
        school = next(r["tract"] for r in load(d / records_name(DEPOSITS[0]["tsv"]))["records"]
                      if r["tract"]["part"].startswith("LOT"))
        if school["resolves"] != "town_lot" or school["town_code"] is not None:
            print("SELF-TEST: a sectioned LOTnBLn is not a town-plat lot"); return 1
        fired.append("the school section's lots and the plat's lots stay two kinds")

        # A BUYER THAT IS A BODY (T-1033). The county commissioners are in the fixture
        # because the firm test cannot see them — there is no conjunction before `COM` —
        # and the refusal they used to get was an accident of no Cook being called Cnty.
        cross_lots = load(d / "resident_crosswalk.json")
        body = [b for b in cross_lots["body_purchasers"]
                if b["body_as_read"] == "COOK CNTY COM"]
        if len(body) != 1 or not body[0]["declared"]:
            print("SELF-TEST: a declared body must reach body_purchasers[]"); return 1
        if any(m["purchaser_as_read"] == "COOK CNTY COM" for m in cross_lots["matches"]):
            print("SELF-TEST: a body must never be proposed as a person"); return 1
        if not any(r["a"] == "COOK CNTY COM" and r.get("body")
                   for r in cross_lots["refusals"]):
            print("SELF-TEST: a body must be refused for being a body"); return 1
        fired.append("a body corporate is refused as a body and carried with its ground")
        was = dict(KNOWN_BODIES)
        try:
            KNOWN_BODIES.pop("COOK CNTY COM")
            if not check(d, quiet=True):
                print("SELF-TEST: an undeclared body did not stop the gate"); return 1
        finally:
            KNOWN_BODIES.clear()
            KNOWN_BODIES.update(was)
        build(d, quiet=True)
        fired.append("an undeclared body stops the gate until somebody reads its rows")

        cov = load(d / "coverage.json")
        # T-0675 read the three sections T-0557 could not, so they MUST be declared now;
        # the assertion is the same discipline pointed the other way — a section whose
        # sales are in the deposit and whose coverage is silent is a hole in the record.
        if "T39N R14E sec 16" not in cov["declarations"][0]["items"]:
            print("SELF-TEST: a section whose sales are held must be declared read")
            return 1
        if cov["not_read"]["truncated_at_the_150_row_ceiling"]:
            print("SELF-TEST: no section of R14E is truncated after T-0675"); return 1
        # The ring's own declaration, under its own ticket: a second deposit that read
        # nothing would look exactly like one whose sections all came back empty.
        ringdec = [x for x in cov["declarations"] if x["ticket"] == DEPOSITS[1]["ticket"]]
        if [x["items"] for x in ringdec] != [["T38N R14E sec 02", "T38N R14E sec 33"]]:
            print("SELF-TEST: the ring deposit must declare the sections it reached"); return 1
        if "T38N R14E sec 01" not in cov["queried_no_sales_through_1836"][1]["items"]:
            print("SELF-TEST: a ring section walked and empty must be recorded as read"); return 1
        fired.append("every section walked whole is declared read, and none is truncated")

        for rel, breaker in (
            ("entries.json", lambda doc: doc.update({"count": 999})),
            ("coverage.json", lambda doc: doc["declarations"][0]["items"].append("T99N R99E sec 01")),
            ("crosswalk.json", lambda doc: doc["merges"].append({"into": "x", "from": "y"})),
            ("resident_crosswalk.json", lambda doc: doc["refusals"].clear()),
            (records_name(DEPOSITS[0]["tsv"]),
             lambda doc: doc["records"][0].update({"as_read": "CHIPMAN ANCEL"})),
            (records_name(DEPOSITS[1]["tsv"]),
             lambda doc: doc["records"][0].update({"as_read": "HUNTER EDWARD"})),
        ):
            doc = load(d / rel)
            breaker(doc)
            dump(d / rel, doc)
            if not check(d, quiet=True):
                print("SELF-TEST: a hand-edit to %s did not fail the gate" % rel); return 1
            fired.append("a hand-edit to %s fails the gate" % rel)
            build(d, quiet=True)

        tsv = d / "text" / DEPOSITS[0]["tsv"]
        tsv.write_text(tsv.read_text(encoding="utf-8").replace("E2NE", "E2NW"),
                       encoding="utf-8")
        if not check(d, quiet=True):
            print("SELF-TEST: a changed deposit did not fail the gate"); return 1
        fired.append("a changed deposit fails the gate")

    # T-1001 — THE SURNAME A RULED CARD MERGE TOOK OUT OF THE LAYER. These run on a
    # synthetic residents layer rather than the committed one, because the committed one
    # is what the assertion is meant to survive the editing of.
    with tempfile.TemporaryDirectory() as td:
        fake = Path(td) / "residents"
        (fake / "households").mkdir(parents=True)
        (fake / "households" / "hh_one.json").write_text(json.dumps({
            "id": "hh_one",
            "persons": [{"id": "kimberly_edmund_s", "name": "Dr Edmund Stoughton Kimberly"},
                        {"id": "allen_lieut_james", "name": "Lieut. James Allen"}]}),
            encoding="utf-8")
        (fake / "index.json").write_text(json.dumps({
            "households": [{"file": "households/hh_one.json"}],
            "merged": [
                # the case: a DIFFERENT spelling, folded onto a person the layer holds
                {"person": "kimberley_ed", "name": "Ed Kimberley",
                 "merged_into_person": "kimberly_edmund_s"},
                # the same surname, folded — adds nothing and must not be carried
                {"person": "allen_james", "name": "James Allen",
                 "merged_into_person": "allen_lieut_james"},
                # a chain: the middle card was folded onward, and the end of it is what counts
                {"person": "kimberlie_e", "name": "E Kimberlie",
                 "merged_into_person": "kimberley_ed"},
                # a card folded onto somebody the layer no longer holds at all
                {"person": "ghost_a", "name": "A Ghost",
                 "merged_into_person": "nobody_at_all"},
            ]}), encoding="utf-8")
        real, globals()["RESIDENTS"] = RESIDENTS, fake
        try:
            got = merged_card_surnames()
        finally:
            globals()["RESIDENTS"] = real
        by_surname = {row[0]: row[1] for row in got}
        if by_surname.get("KIMBERLEY") != "kimberly_edmund_s":
            print("SELF-TEST: a ruled card merge must leave its own surname gathering the "
                  "person it was ruled to be"); return 1
        fired.append("a folded card's surname still gathers the person it was ruled to be")
        if "ALLEN" in by_surname:
            print("SELF-TEST: a merge of the same surname adds nothing and must not be "
                  "carried — it would put one man in his own bucket twice"); return 1
        fired.append("a merge that does not change the spelling is not carried")
        if by_surname.get("KIMBERLIE") != "kimberly_edmund_s":
            print("SELF-TEST: a card folded onto a card that was itself folded must "
                  "follow the chain to the person the layer actually holds"); return 1
        fired.append("a chain of merges resolves to the surviving person")
        if "GHOST" in by_surname:
            print("SELF-TEST: a merge onto somebody the layer does not hold must be "
                  "skipped, not proposed"); return 1
        fired.append("a merge onto a person the layer has lost is skipped")

    # T-1032. The town-lot harvest is checked against the probe it was drawn from, and
    # a fixture is the only way to prove that check still fires: the real pair is green,
    # and a gate nobody has watched fail is a gate nobody knows works.
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        (d / "text").mkdir(parents=True)
        listed = [("0000001", "BEAUBIEN J B", "L4BL36CHIOT", "", "", "", "", "09/27/1830", "COOK"),
                  ("0000002", "EGAN WILLIAM B", "L1BL17CHIV", "", "", "", "", "06/20/1836", "COOK"),
                  ("0000003", "ABELL SIDNEY", "SW", "04", "38N", "12E", "3", "08/08/1835", "COOK")]
        (d / "text" / PROBE["tsv"]).write_text(
            "\n".join(["\t".join(PROBE_COLS)] + ["\t".join(r) for r in listed]) + "\n")

        def harvest(rows):
            (d / "text" / HARVESTED["tsv"]).write_text(
                "\n".join(["\t".join(COLS)] + ["\t".join(r) for r in rows]) + "\n")

        def row(pno, who, lot, section=""):
            out = dict.fromkeys(COLS, "")
            out.update({"purchase_no": pno, "purchaser": who, "aliquot_or_lot": lot,
                        "county": "COOK", "type_of_sale": "CN", "section": section,
                        "date_purchased": {"0000001": "09/27/1830",
                                           "0000002": "06/20/1836"}[pno]})
            return [out[c] for c in COLS]

        harvest([row("0000001", "BEAUBIEN J B", "L4BL36CHIOT"),
                 row("0000002", "EGAN WILLIAM B", "L1BL17CHIV")])
        if check_harvested(d):
            print("SELF-TEST: a faithful harvest of the probe's sectionless rows must be "
                  "green:", check_harvested(d)[0]); return 1
        fired.append("a harvest that matches the probe row for row is green")

        harvest([row("0000001", "BEAUBIEN J B", "L4BL36CHIOT")])
        if not any("has no detail page" in b for b in check_harvested(d)):
            print("SELF-TEST: a sectionless row with no detail page must fail"); return 1
        fired.append("a sectionless row the harvest never fetched fails the gate")

        harvest([row("0000001", "BEAUBIEN J B", "L4BL36CHIOT"),
                 row("0000002", "EGAN WILLIAM B", "L1BL17CHIV"),
                 ["0000003"] + [""] * (len(COLS) - 1)])
        if not any("not one of the probe's sectionless rows" in b for b in check_harvested(d)):
            print("SELF-TEST: a row the probe never called sectionless must fail"); return 1
        fired.append("a harvested row the probe does not list as sectionless fails the gate")

        harvest([row("0000001", "BEAUBIEN J B", "L4BL36CHIOT"),
                 row("0000002", "EGAN WILLIAM B", "L1BL17CHIV", section="17")])
        if not any("and a sectionless row carries none" in b for b in check_harvested(d)):
            print("SELF-TEST: a harvested row that arrived with a section must fail"); return 1
        fired.append("a harvested row that acquired a section fails the gate")

        harvest([row("0000001", "BEAUBIEN J B", "L4BL36CHIOT"),
                 row("0000002", "SOMEBODY ELSE", "L1BL17CHIV")])
        if not any("the harvest is not the rows it was drawn from" in b
                   for b in check_harvested(d)):
            print("SELF-TEST: a detail page that disagrees with the list page must fail")
            return 1
        fired.append("a detail page that disagrees with the list page fails the gate")

    print("read_land_sales --self-test: %d assertions fire when broken" % len(fired))
    for f in fired:
        print("  · %s" % f)
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    if args.build:
        return build()
    if args.check:
        bad = check()
        for b in bad:
            print("  ✗ %s" % b)
        return 1 if bad else 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
