#!/usr/bin/env python3
"""Norris's 1844 firms, dated against 1835 (T-0588).

    tools/date_norris_1844_businesses.py [--check]

THE QUESTION THIS FILE ANSWERS, and it is a dating question, not a matching one:
of the firms Norris's 1844 volume prints, which ones does some printing put in the
town of 1 July 1835? Under the ratified ladder an 1844 listing alone never puts a
business in the 1835 town, so a firm reaches this scene only if a DATE reaches it,
and the ticket names the three printings that could carry one — the Historical
Sketch, the firm's own advertising card, and Fergus's 1843 directory. This walks
all three over every firm the volume prints and writes down what each one reached.

THE THREE DATING ROUTES, written out so they read back without the code:
  SKETCH. The 65 town findings read out of Norris's own Historical Sketch and
  Statistical Account (T-0567) carry a `describes_date`. A finding dated at or
  before 1835 whose PRINTED QUOTE names every significant word of a firm's name is
  a candidate dating; the reader's `normalized` gloss is deliberately NOT searched,
  because it is this project's prose and finding this project's own words in it
  would date nothing.
  OWN CARD. A card in the Advertising Directory (T-0568) may print its own
  founding — "established 18xx", "since 18xx", "commenced business in 18xx". The
  card's `dated_statement`, and a scan of the card's printed text for founding
  language beside a year, are both taken.
  FERGUS 1843. Fergus's 1843 directory (T-0571) is a year nearer the scene and its
  business entries are advertisements too. A Fergus entry matched to the firm and
  carrying founding language beside a year at or before 1835 is a dating; a Fergus
  entry with no such year is PRESENCE IN 1843 and is not one. Being in print in
  1843 is not being in business in 1835, and this file never treats it as though
  it were.

CONTINUITY IS THE FOURTH THING, AND IT IS WORTH LESS THAN A DATE. A firm the 1835
newspapers already carry — the 206 businesses of `gazetteer.json` — and Norris
still prints in 1844 is corroborated as having survived nine years. That is
CONTINUITY: it confirms a business the town already holds and it adds none, it
carries no founding date, and it moves no grade. It is recorded here because the
owner's ask was to validate and confirm as well as to add, and because a reader
who finds Newberry & Dole in both volumes should be able to see that this project
noticed. The rule is the standing one, adapted from names to firm styles:
  A firm printing and an 1835 business agree when the SET of surnames printed in
  the firm style is equal on both sides, and the given-name initials printed for a
  shared surname AGREE AS FAR AS BOTH SIDES GO. A ONE-surname firm additionally
  REQUIRES an initial printed on both sides and agreeing — "B. Jones & Co." against
  a town that holds a Jones is the eleven-Smiths refusal, however good it looks.
  Where a firm meets more than one 1835 business on that rule the match is
  AMBIGUOUS and is filed as such, not resolved.

  AS FAR AS BOTH SIDES GO means one side's initials must be CONTAINED IN the
  other's, and it is the whole of what this rule can say about initials it holds as
  a set rather than in the order printed. One man is printed with different NUMBERS
  of initials from year to year — 'W. Adams' in one volume and 'W. H. Adams' in the
  next — so a side printing FEWER is no evidence against him, and {W} against
  {W, H} is admitted. But an initial printed on one side and absent from the other
  WHILE THAT OTHER prints one this side lacks is two different men, and no amount of
  overlap redeems it: {W, H} against {R, E, W} meets on W and is REFUSED. That pair
  is real and is why this clause is written (T-1035) — Norris's boot and shoe firm
  'Adams, W. H. & Co' was counted present in Fergus's 1843 directory through
  'R. E. W. ADAMS, homoeopathic physician', on one shared initial out of three,
  because the rule asked only whether ANY initial agreed and never how many did not.

WHAT THIS WRITES INTO THE TOWN: nothing. That is the finding, not an omission —
see the `written` block, which carries the reason in the file rather than only in
a pull request nobody will read again.
"""
import json, os, re, sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIRECTORY = os.path.join(ROOT, "data/research/directories/claims/norris_1844_directory_entries.json")
ADVERTISER = os.path.join(ROOT, "data/research/directories/claims/norris_1844_advertiser.json")
SKETCH = os.path.join(ROOT, "data/research/directories/claims/norris_1844_town_findings.json")
FERGUS = os.path.join(ROOT, "data/research/directories/claims/fergus_1843_directory_entries.json")
GAZETTEER = os.path.join(ROOT, "data/research/newspapers/gazetteer.json")
OUT = os.path.join(ROOT, "data/research/directories/norris_1844_businesses_1835.json")

SCENE_YEAR = 1835

# Words a firm style carries that are not a partner's surname.
NOISE = {"co", "company", "and", "the", "of", "for", "at", "in", "jr", "sr", "jun",
         "junr", "esq", "city", "chicago", "ill", "illinois", "late", "son", "sons",
         "brother", "brothers", "bros", "agent", "agency", "store", "hotel", "house",
         "mrs", "miss", "mr", "dr", "doctor", "capt", "col", "rev", "gen", "maj", "master"}

# The fold the two Norris crosswalks use, so all three files agree about what "the
# same surname" means and can be read side by side.
FOLD = [(r"[^a-z]", ""), (r"^mc", "mac"), (r"ii", "n"), (r"rn", "m"), (r"vv", "w"),
        (r"1", "l"), (r"0", "o")]

FOUNDING = re.compile(
    r"(establish\w*|founded|commenc\w*|since|in business|opened|erected|"
    r"has carried on|for the last)\D{0,60}(1[78]\d\d)", re.I | re.S)
YEAR = re.compile(r"\b(1[78]\d\d)\b")


def fold(word):
    s = (word or "").lower()
    for pat, rep in FOLD:
        s = re.sub(pat, rep, s)
    return s


def firm_names(printed):
    """A printed firm style into (folded surname set, {surname: set of initials}).

    Splits on the ampersand, on 'and', and on the comma Norris uses between partners
    ('Jones, King & Co.'); an initial is a single letter, a surname is anything
    longer that is not one of the trade words above.

    Norris also alphabetises, and his alphabetising comma looks exactly like his
    partner comma: 'Jones, B. & Co' splits into 'Jones' / 'B.' / 'Co'. The middle
    part is an initial with no surname beside it, so an initial-only part that
    FOLLOWS a surname part is read as that surname's initial. One that follows
    nothing is a leading initial the part after it carries ('D. A. & E. M. Jones'),
    and is still dropped here."""
    if not printed:
        return set(), {}
    text = re.sub(r"[^A-Za-z&., ]", " ", printed)
    surnames, initials = set(), defaultdict(set)
    last_surname = None
    for part in re.split(r"&|\band\b|,", text):
        words = [w.strip(". ") for w in part.split()]
        words = [w for w in words if w and w.lower().strip(".") not in NOISE]
        inits = [w.upper() for w in words if len(w) == 1]
        longs = [w for w in words if len(w) > 1]
        if not longs:
            if inits and last_surname:
                initials[last_surname].update(inits)
            continue
        for w in longs:
            surnames.add(fold(w))
        last_surname = fold(longs[-1])
        initials[last_surname].update(inits)
    return {s for s in surnames if s}, {k: v for k, v in initials.items() if k}


def person_surname(printed):
    """A proprietor's printed name into (folded surname, set of initials). Handles the
    directory's inverted form ('Jones, William') as well as 'William Jones'."""
    if not printed:
        return None, set()
    text = re.sub(r"[^A-Za-z&., ]", " ", printed)
    if "," in text and not re.search(r"&|\band\b", text):
        head = text.split(",")[0]
        tail = text.split(",", 1)[1]
    else:
        head, tail = text, ""
    words = [w.strip(". ") for w in (head + " " + tail).split()]
    words = [w for w in words if w and w.lower().strip(".") not in NOISE]
    longs = [w for w in words if len(w) > 1]
    inits = {w.upper() for w in words if len(w) == 1}
    if not longs:
        return None, inits
    surname = fold(head.split()[-1].strip(". ")) if ("," in text and not re.search(r"&|\band\b", text)) else fold(longs[-1])
    for w in longs:
        if fold(w) != surname:
            inits.add(w[0].upper())
    return (surname or None), inits


def sketch_words(finding):
    """The words a town finding NAMES: the printed quote, plus the reader's index of
    the entities in it. The `normalized` gloss is deliberately left out — it is this
    project's own prose, and finding this project's words in it would date nothing.
    (It matters: the gloss says "Norris's summary of the beginning", which would put
    the author's own 1844 firm, J. W. Norris, into six statements about 1832.)"""
    words = set()
    for w in re.split(r"[^A-Za-z]+", finding["quote"]):
        if w:
            words.add(fold(w))
    for e in (finding.get("entities") or []):
        for w in re.split(r"[^A-Za-z]+", e):
            if w:
                words.add(fold(w))
    return {w for w in words if w}


def names_the_firm(surnames, finding):
    """True when a town finding names EVERY surname in the firm style."""
    if not surnames:
        return False
    words = sketch_words(finding)
    return all(s in words for s in surnames)


def year_at_or_before(text):
    """The earliest year printed in `text` that is at or before the scene, or None."""
    years = [int(y) for y in YEAR.findall(text or "")]
    early = [y for y in years if y <= SCENE_YEAR]
    return min(early) if early else None


def agree_rule(a_sur, a_ini, b_sur, b_ini):
    """The continuity rule of the docstring. -> (True/False, why).

    The initials are held as a SET, not in the order printed, so the strongest thing
    this can ask of them is CONTAINMENT: one side's initials must all be printed by
    the other. That admits the side that prints fewer ({W} against {W, H} is one man
    printed two ways) and refuses the side that prints a DIFFERENT one ({W, H}
    against {R, E, W} — see the docstring, T-1035). Overlap alone is not agreement."""
    if not a_sur or a_sur != b_sur:
        return False, None
    for s in a_sur:
        ia, ib = a_ini.get(s) or set(), b_ini.get(s) or set()
        if ia and ib and not (ia & ib):
            return False, "an initial printed on both sides contradicts"
        if ia and ib and not (ia <= ib or ib <= ia):
            return False, ("the two sides print initials neither holds for the other, "
                           "and agreeing on one of them is not agreeing")
    if len(a_sur) == 1:
        s = next(iter(a_sur))
        ia, ib = a_ini.get(s) or set(), b_ini.get(s) or set()
        if not (ia and ib and (ia & ib)):
            return False, "one surname, and no initial printed on both sides agrees"
    return True, None


def self_test():
    """The three claims this file makes about its own rules, each with a case that
    fires and a case that does not — so a green run means the measurement measured
    something, not that every route silently matched nothing."""
    cases, failed = [], 0

    def case(name, got, want):
        nonlocal failed
        ok = got == want
        cases.append((ok, name))
        if not ok:
            failed += 1

    finding = {"quote": "In 1832, Robert A. Kinzie built a store at Wolf Point.",
               "entities": ["Robert A. Kinzie"], "describes_date": "1832"}
    case("the sketch route fires when a finding names the firm",
         names_the_firm({"kinzie"}, finding), True)
    case("...and not when it names only part of it",
         names_the_firm({"kinzie", "hunter"}, finding), False)
    case("...and never through this project's own gloss",
         names_the_firm({"norris"}, {"quote": "the beginning of the settlement",
                                     "entities": [], "normalized": "Norris's summary"}), False)

    case("a firm style reads as its partners' surnames",
         firm_names("Newberry & Dole")[0], {"newberry", "dole"})
    case("two surnames in a firm style are a firm identity",
         agree_rule(*firm_names("Newberry & Dole"), {"newberry", "dole"}, {})[0], True)
    case("one surname with no initial on both sides is refused",
         agree_rule({"jones"}, {}, {"jones"}, {})[0], False)
    case("one surname with agreeing initials is a match",
         agree_rule({"jones"}, {"jones": {"B"}}, {"jones"}, {"jones": {"B"}})[0], True)
    case("a contradicted initial is refused",
         agree_rule({"jones"}, {"jones": {"B"}}, {"jones"}, {"jones": {"W"}})[0], False)
    case("a side printing FEWER initials than the other still agrees",
         agree_rule({"adams"}, {"adams": {"W"}}, {"adams"}, {"adams": {"W", "H"}})[0], True)
    case("...and the real Adams pair, agreeing on one initial out of three, does not",
         agree_rule(*firm_names("Adams, W. H. & Co"),
                    *firm_names("R. E. W. ADAMS"))[0], False)
    case("...while the exact Adams firm pairing still stands",
         agree_rule(*firm_names("Adams, W. H. & Co"),
                    *firm_names("W. H. ADAMS & CO."))[0], True)

    case("the alphabetising comma's initial attaches to the surname before it",
         firm_names("Jones, B. & Co")[1], {"jones": {"B"}})
    case("...and a leading initial-only part still attaches to nothing",
         firm_names("D. A. & E. M. Jones")[1], {"jones": {"E", "M"}})

    case("a founding year at or before the scene is read",
         year_at_or_before("established 1834"), 1834)
    case("...and a later one is not",
         year_at_or_before("first warehouse erected 1839"), None)
    case("founding language is what carries the year",
         bool(FOUNDING.search("established in 1834")), True)
    case("...and a street number is not founding language",
         bool(FOUNDING.search("126 Lake Street")), False)

    for ok, name in cases:
        print("  %s %s" % ("fires:" if ok else "FAILED:", name))
    print("SELF-TEST %s — %d case(s)" % ("PASS" if not failed else "FAIL", len(cases)))
    return 1 if failed else 0


def main():
    if "--self-test" in sys.argv:
        return self_test()
    directory = json.load(open(DIRECTORY, encoding="utf-8"))["claims"]
    cards = json.load(open(ADVERTISER, encoding="utf-8"))["claims"]
    sketch = json.load(open(SKETCH, encoding="utf-8"))["claims"]
    fergus = json.load(open(FERGUS, encoding="utf-8"))["claims"]
    town = json.load(open(GAZETTEER, encoding="utf-8"))["businesses"]

    # ---- every firm the volume prints, and where it prints it -------------------
    printings = []
    for e in directory:
        if e["kind"] != "business":
            continue
        printings.append({
            "printing": e["id"], "section": "directory",
            "as_printed": e["normalized"]["as_printed"],
            "name": e["normalized"]["printed_name"],
            "trade": e["normalized"].get("occupation"),
            "proprietors": [],
            "printed_page": e["locator"].get("printed_page"),
        })
    for c in cards:
        name = c["normalized"].get("firm")
        props = c["normalized"].get("proprietors") or []
        if not name and not props:
            continue
        printings.append({
            "printing": c["id"], "section": "advertising_directory",
            "as_printed": c["quote"],
            "name": name or (props[0] if props else None),
            "trade": c["normalized"].get("trade"),
            "proprietors": props,
            "printed_page": c["locator"].get("printed_page"),
            "dated_statement": c["normalized"].get("dated_statement"),
        })

    firms = {}
    for p in printings:
        sur, ini = firm_names(p["name"])
        for prop in p["proprietors"]:
            s, inits = person_surname(prop)
            if s:
                sur.add(s)
                ini.setdefault(s, set()).update(inits)
        key = p["name"].strip().lower() if p["name"] else p["printing"]
        f = firms.setdefault(key, {
            "firm": p["name"], "surnames": sur, "initials": {k: set(v) for k, v in ini.items()},
            "printings": [], "trades": [],
        })
        f["surnames"] |= sur
        for k, v in ini.items():
            f["initials"].setdefault(k, set()).update(v)
        f["printings"].append(p)
        if p.get("trade"):
            f["trades"].append(p["trade"])

    # ---- route SKETCH -----------------------------------------------------------
    early_findings = [t for t in sketch
                      if re.match(r"^1[0-9]{3}", str(t.get("describes_date")))
                      and int(str(t["describes_date"])[:4]) <= SCENE_YEAR]
    # ---- route FERGUS -----------------------------------------------------------
    fergus_firms = []
    for e in fergus:
        if e["kind"] != "business":
            continue
        sur, ini = firm_names(e["normalized"].get("printed_name") or e["quote"].split(",")[0])
        fergus_firms.append({"claim": e["id"], "quote": e["quote"], "surnames": sur, "initials": ini})
    # ---- route CONTINUITY (the town's own 1835 businesses) ----------------------
    town_firms = []
    for b in town:
        sur, ini = set(), defaultdict(set)
        for prop in (b.get("proprietors") or []):
            # A gazetteer proprietor is sometimes the firm style itself ("Newberry &
            # Dole") and sometimes one partner ("Oliver Newberry"). Read each the way
            # it is printed: an ampersand or an 'and' makes it a firm.
            if re.search(r"&|\band\b", prop):
                s2, i2 = firm_names(prop)
                sur |= s2
                for k, v in i2.items():
                    ini[k].update(v)
            else:
                s2, i2 = person_surname(prop)
                if s2:
                    sur.add(s2)
                    ini[s2].update(i2)
        town_firms.append({"id": b["id"], "name": b["name"], "surnames": sur,
                           "initials": {k: set(v) for k, v in ini.items()},
                           "proprietors": b.get("proprietors") or [], "trade": b.get("trade")})

    agree = agree_rule

    rows, continuity, ambiguous, refused_surname_only = [], [], [], []
    sketch_candidates = card_dated = fergus_founding = dated_1835 = 0
    in_fergus = 0

    for key in sorted(firms):
        f = firms[key]
        sur, ini = f["surnames"], f["initials"]
        row = {"firm": f["firm"],
               "printed_in": [{"printing": p["printing"], "section": p["section"],
                               "printed_page": p["printed_page"]} for p in f["printings"]],
               "trade": (f["trades"] or [None])[0]}

        # SKETCH
        hits = []
        if sur:
            for t in early_findings:
                if names_the_firm(sur, t):
                    hits.append({"claim": t["id"], "describes_date": t["describes_date"],
                                 "quote": t["quote"].strip()[:200]})
        sketch_candidates += len(hits)
        row["sketch"] = {"candidates": hits,
                         "dates_the_founding_at_or_before_1835": False} if hits else \
                        {"candidates": [], "dates_the_founding_at_or_before_1835": False}

        # OWN CARD
        card_years, statements = [], []
        for p in f["printings"]:
            if p["section"] != "advertising_directory":
                continue
            if p.get("dated_statement"):
                statements.append(p["dated_statement"])
            m = FOUNDING.search(p["as_printed"] or "")
            if m:
                card_years.append(int(m.group(2)))
        if statements:
            card_dated += 1
        early_card = [y for y in card_years if y <= SCENE_YEAR]
        row["own_card"] = {"dated_statements": statements,
                           "founding_years_printed": sorted(set(card_years)),
                           "dates_the_founding_at_or_before_1835": bool(early_card)}

        # FERGUS 1843
        fhits = []
        for e in fergus_firms:
            ok, _ = agree(sur, ini, e["surnames"], e["initials"])
            if not ok:
                continue
            m = FOUNDING.search(e["quote"])
            fy = int(m.group(2)) if m else None
            if m:
                fergus_founding += 1
            fhits.append({"claim": e["claim"], "founding_year_printed": fy,
                          "quote": e["quote"].strip()[:200]})
        row["fergus_1843"] = {
            "entries": fhits,
            "present_in_1843": bool(fhits),
            "dates_the_founding_at_or_before_1835":
                any(h["founding_year_printed"] and h["founding_year_printed"] <= SCENE_YEAR
                    for h in fhits)}

        if fhits:
            in_fergus += 1

        dated = (row["sketch"]["dates_the_founding_at_or_before_1835"]
                 or row["own_card"]["dates_the_founding_at_or_before_1835"]
                 or row["fergus_1843"]["dates_the_founding_at_or_before_1835"])
        if dated:
            dated_1835 += 1
        row["verdict"] = "dated_at_or_before_1835" if dated else "1844_evidence_only"
        row["why"] = ("No printing this project holds dates this firm's founding. "
                      "An 1844 listing alone never puts a business in the 1835 town, "
                      "so it is refused." if not dated else
                      "A printing dates the founding at or before 1835.")

        # CONTINUITY
        met = []
        for tb in town_firms:
            ok, _ = agree(sur, ini, tb["surnames"], tb["initials"])
            if ok:
                met.append(tb)
        if len(met) == 1:
            continuity.append({"firm_1844": f["firm"], "trade_1844": row["trade"],
                               "business_1835": met[0]["id"], "name_1835": met[0]["name"],
                               "proprietors_1835": met[0]["proprietors"],
                               "trade_1835": met[0]["trade"],
                               "printed_in": row["printed_in"],
                               "worth": "CONTINUITY, and nothing more: the firm the 1835 "
                                        "papers carry is still in print in 1844. It adds no "
                                        "business, dates no founding and moves no grade."})
            row["continuity_with_1835"] = met[0]["id"]
        elif len(met) > 1:
            ambiguous.append({"firm_1844": f["firm"], "meets": [m["id"] for m in met],
                              "rule": "More than one 1835 business meets this firm on the "
                                      "surname-set rule. Filed, not resolved."})
            row["continuity_with_1835"] = None
        else:
            row["continuity_with_1835"] = None
            if len(sur) == 1:
                s = next(iter(sur))
                near = [tb for tb in town_firms if tb["surnames"] == sur]
                if near:
                    # Say WHICH half of the rule refused it. Absence and contradiction are
                    # different findings, and reading the inverted style's initial turns
                    # some of these from the first into the second.
                    why = sorted({agree(sur, ini, tb["surnames"], tb["initials"])[1]
                                  for tb in near} - {None})
                    refused_surname_only.append(
                        {"firm_1844": f["firm"], "surname": s,
                         "meets_on_surname_alone": [tb["id"] for tb in near],
                         "rule": "%s. Refused — the eleven-Smiths rule."
                                 % "; ".join(w[0].upper() + w[1:] for w in why)})
        rows.append(row)

    written = {
        "firms_written_to_the_businesses_layer": 0,
        "why": "NONE, and the measurement is the reason rather than the excuse. Each of "
               "the three printings the ticket named was walked over every firm the "
               "volume prints, and not one of them dates a firm's founding at or before "
               "1835. The Historical Sketch names no 1844 firm in any of the 25 "
               "statements it dates at or before the scene — its early paragraphs are "
               "about the fort, the harbour, the mails, the two newspapers and a handful "
               "of houses, and the businesses in them (the Fur Company's traffic, R. A. "
               "Kinzie's store at Wolf Point, Mark Beaubien's Eagle) are places this town "
               "already holds, not firms Norris lists nine years later. The Advertising "
               "Directory's seven dated cards are dated December 1843 or 1844, which is "
               "what T-0568 reported after reading all 158 of them. And Fergus's 1843 "
               "directory advertises in the present tense: 153 of these 207 firms are "
               "already in it, which is continuity to 1843 and no more, and the single "
               "entry in the whole volume that prints a founding year prints 1839. So no "
               "firm here reaches the town of 1 July 1835, and writing one in would be the "
               "exact move the ticket forbids — stretching an 1844 listing back nine years "
               "to have something to show. The businesses layer is unchanged.",
        "what_the_pass_did_confirm": "Two of the 206 businesses the 1835 papers give the "
               "town are still in print in 1844 under the same firm style — Newberry & "
               "Dole, and G. S. Hubbard against Hubbard & Co. — which is the validating "
               "half of the owner's ask answered: the town's own businesses survive into "
               "the first directory, and this file names the two the rule admits, the two "
               "it leaves ambiguous and the eight it refuses on a surname alone — six of "
               "those eight on an initial that CONTRADICTS rather than one that is "
               "missing, which is the eleven-Smiths rule refusing on evidence.",
        "what_would_change_this": "A printing that dates a founding. The likeliest are the "
               "1839 Chicago directory, which this project cites but has never read entry "
               "by entry, and the old-settler reminiscences (T-0554), which date arrivals "
               "and openings by year as a matter of course.",
        }

    doc = {
        "schema": 1,
        "_doc": "GENERATED by tools/date_norris_1844_businesses.py. Every firm Norris's 1844 "
                "volume prints, walked against the three printings that could date its "
                "founding at or before 1835, and against the 206 businesses the 1835 papers "
                "already give the town. A MEASUREMENT: it writes no business, moves no grade "
                "and changes no record.",
        "generated_by": "tools/date_norris_1844_businesses.py",
        "source_id": "norris_directory_1844",
        "scene_date": "1835-07-01",
        "the_question": __doc__.split("THE QUESTION THIS FILE ANSWERS")[1].split("THE THREE DATING ROUTES")[0].strip(", \n"),
        "the_three_routes": __doc__.split("THE THREE DATING ROUTES, written out so they read back without the code:")[1].split("CONTINUITY IS THE FOURTH THING")[0].strip(),
        "continuity_rule": __doc__.split("CONTINUITY IS THE FOURTH THING, AND IT IS WORTH LESS THAN A DATE.")[1].split("WHAT THIS WRITES INTO THE TOWN")[0].strip(),
        "counts": {
            "firm_printings_read": len(printings),
            "firms_read": len(firms),
            "firms_in_the_directory_proper": sum(1 for p in printings if p["section"] == "directory"),
            "firms_in_the_advertising_directory": sum(1 for p in printings if p["section"] == "advertising_directory"),
            "sketch_findings_dated_at_or_before_1835": len(early_findings),
            "sketch_candidate_namings": sketch_candidates,
            "advertising_cards_carrying_any_date": card_dated,
            "firms_also_printed_in_fergus_1843": in_fergus,
            "fergus_1843_entries_with_founding_language": fergus_founding,
            "firms_dated_at_or_before_1835": dated_1835,
            "firms_written": 0,
            "firms_refused_as_1844_evidence_only": len(firms) - dated_1835,
            "continuity_with_a_business_the_town_already_holds": len(continuity),
            "continuity_ambiguous": len(ambiguous),
            "continuity_refused_on_a_surname_alone": len(refused_surname_only),
        },
        "written": written,
        "continuity": sorted(continuity, key=lambda c: (c["firm_1844"] or "")),
        "continuity_ambiguous": sorted(ambiguous, key=lambda c: (c["firm_1844"] or "")),
        "continuity_refused_on_a_surname_alone": sorted(refused_surname_only, key=lambda c: (c["firm_1844"] or "")),
        "firms": rows,
    }

    if "--check" in sys.argv:
        if not os.path.exists(OUT):
            print("norris 1844 businesses: %s is not committed" % OUT, file=sys.stderr)
            return 1
        if json.load(open(OUT, encoding="utf-8")) != doc:
            print("norris 1844 businesses: committed file does not match — regenerate",
                  file=sys.stderr)
            return 1
        print("norris 1844 businesses: matches the committed file")
        return 0
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    print(json.dumps(doc["counts"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
