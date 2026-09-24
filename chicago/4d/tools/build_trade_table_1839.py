#!/usr/bin/env python3
"""*Fergus' Directory of the City of Chicago, 1839* — the trade table (T-1346).

WHY THIS EXISTS. The resident reconstruction programme draws a reconstructed head's
TRADE, and the file it was going to draw it from was never built: T-1162, "the 1835
occupation model", was withdrawn when its five figures were folded into
`data/reconstruction/1835_town_model.json`. What the fold kept was the establishment
comparison (how many stores, taverns, printing offices) and the seven industry
columns of the 1840 schedule. What it lost was the one thing T-1162 § 2 named first:
*the 1839 share per trade — count over all 1839 entries with a trade*. The order
book (T-1166) therefore buckets a person as `trade` or `none` and can say nothing
about WHICH trade, and T-1347 cannot draw one without inventing the distribution it
draws from. This tool builds that distribution out of committed text and nothing
else.

WHAT IT READS. `claims/fergus_1839_directory_entries.json` — the 1,655 entries
`read_fergus_1839.py --build` segments off the committed page text, each carrying
the printed occupation exactly as set. Nothing here opens a page; this is an
aggregate over a reading somebody else already made and the gate already re-derives.

WHAT IT IS NOT. 1839 is four years after the scene, and this volume is Fergus's
1876 completion of a list that "was never written" (printed page 3 — see
`read_fergus_1839.py`'s header, which carries the compiler's own two warnings). A
share here is the shape of a LATER town recalled later still, and the table says so
on every row. It is a prior for a draw, never a count of 1835 and never evidence
about any person.

THE READING IS RULE-BASED AND THE RULES ARE HERE. A printed trade is normalised by
an ordered list of committed rules — OCR repairs, then refusals, then the trade
patterns — and the FIRST rule that matches decides. Every entry the rules cannot
place is REFUSED IN WRITING with its count and its class; the refusals are in the
output and they balance: mapped + refused == entries carrying a printed trade. A
normaliser that silently drops what it cannot read is how a share becomes a fiction.

  python3 tools/build_trade_table_1839.py --build
  python3 tools/build_trade_table_1839.py --check
  python3 tools/build_trade_table_1839.py --self-test
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENTRIES = os.path.join(ROOT, "data/research/directories/claims/fergus_1839_directory_entries.json")
INDEX = os.path.join(ROOT, "data/residents/index.json")
TOWN_MODEL = os.path.join(ROOT, "data/reconstruction/1835_town_model.json")
OUT = os.path.join(ROOT, "data/research/directories/fergus_1839_trade_table.json")

SOURCE_ID = "fergus_directory_1839"

# --------------------------------------------------------------------------
# 1. OCR repairs — the scan's own damage, repaired by an explicit table.
#
# This scan turns `r` into `i'` inside a word often enough that four of the
# town's commonest trades arrive broken. A general rule for it would also
# rewrite words that are correctly set, so the repairs are named one by one and
# a fifth broken word arrives as a refusal rather than as a silent miscount.
# --------------------------------------------------------------------------
OCR_REPAIRS = {
    "laboi'er": "laborer",
    "cai'penter": "carpenter",
    "clei'k": "clerk",
    "bakei'": "baker",
    "forwai'ding": "forwarding",
    "merch'ts": "merchants",
    "att'yand": "attorney and",
    "contrac'r": "contractor",
    "coui't": "court",
    "shav-ing-shop": "shaving shop",
    "haircutting": "hair cutting",
    "hair-cutting": "hair cutting",
    "drygoods": "dry goods",
    "aud": "and",
    "cabinetmaker": "cabinet maker",
    "tailoi": "tailor",
}

# --------------------------------------------------------------------------
# 2. Refusals — what is printed in the trade slot and is not a trade.
#
# Each class states what it catches and why the entry cannot be counted. A
# refused entry is still an entry: it is listed, counted, and its share of the
# volume is printed, because the honest measure of this table is how much of
# the directory it could NOT read.
# --------------------------------------------------------------------------
REFUSALS_FIRST = [
    ("not_legible", r"^[^a-z]*$|^.{0,2}$",
     "fewer than three letters survive the scan — a speck, a rule or a broken line"),
    ("a_firm_style", r"&|\bbrothers\b|\b(?:and|&)\s+(?:co|company)\b",
     "a firm's trading style, not one person's trade — the entry names a house"),
    # A PROPER-NAMED HOUSE IS NOT A TRADE. "Smith, John, American Hotel" says where
    # the man was and not what he did there, and reading it as tavern-keeping would
    # promote every porter and every boarder in the volume to a landlord. A BARE
    # house-word is the opposite case — "boarding-house", "saloon", "grocery" is
    # the trade itself — so the rule fires only on a house carrying a proper name,
    # and steps aside wherever the phrase also carries a trade or a post.
    ("a_house_not_a_trade",
     r"^(?!.*\band\b)(?!.*\b(?:boarding|keeper|clerk|pastor|rector|minister|sexton|"
     r"superintendent|proprietors?|managers?|steward|porter|waiter|cook|bar-?keeper|"
     r"private|eating|coffee|refectory|livery)\b)"
     r"(?:the\s+)?[a-z.'\-]+(?:\s+[a-z.'\-]+){0,2}\s+"
     r"(?:hotel|house|saloon|exchange|church|theatre|society)$",
     "a named house, church or place of business standing where a trade would be "
     "set — it says where the person was, not what they did there"),
]

# …and the classes that may fire only AFTER every trade pattern has been tried,
# because each of them would otherwise swallow a phrase that does carry a trade.
REFUSALS_LAST = [
    ("an_employer_or_a_name", r"^(?:and|with|agents? for|assistant|late)\b|\b[a-z]\.(?:\s|$)|"
     r"^[a-z.'\-]+\s+[a-z]$",
     "the segmenter carried a name, an initial or an employer into the trade slot; "
     "the volume gives this person no trade of their own"),
    ("an_address", r"^\d|\bst\b$|^street$|\bavenue\b|^cor\b|^at\b|^bds\b|ward$",
     "an address or a ward printed where a trade would be, the entry giving no "
     "trade at all"),
]

# --------------------------------------------------------------------------
# 3. The trade patterns — ordered, first match wins, most specific first.
#
# A pattern maps a printed phrase onto `vocabulary.occupations` in
# data/residents/index.json where that list holds the trade, and onto a named
# term OUTSIDE it where the 1839 volume attests a trade the 1835 vocabulary has
# no word for. The second class is not a defect to be hidden: it is the
# extension T-1347 will have to make before it can write one of these people,
# and it is printed as its own section of the table.
#
# `column` is the 1840 schedule's industry column the trade falls in, so the
# 1839 shape can be set against the one measurement of Chicago's employment
# this project holds. Learned professions carries engineers, as the schedule's
# own heading does.
# --------------------------------------------------------------------------
AGR, COM, MFG, OCN, RIV, PRO = (
    "Agriculture", "Commerce", "Manufactures and trades",
    "Navigation of the ocean", "Navigation of canals, lakes and rivers",
    "Learned professions and engineers")

TRADES = [
    # professions and offices
    (r"attorney|counsel|\blaw\b(?!.*student)|\bjudge\b|solicitor", "attorney", PRO, True),
    (r"physician|\bdoctor\b|\bsurgeon\b|\bdrs?\b", "physician", PRO, True),
    (r"dentist", "dentist", PRO, True),
    (r"survey|draughtsman|engineer", "surveyor", PRO, True),
    (r"school|teacher|professor|academy|tuition", "schoolteacher", PRO, True),
    (r"student", "student", PRO, False),
    (r"minister|pastor|clergy|preacher", "minister", PRO, True),
    (r"priest|father\b", "priest", PRO, True),
    (r"editor|publisher", "editor", PRO, True),
    (r"postmaster|post-?office", "postmaster", PRO, True),
    (r"sheriff|constable", "sheriff", PRO, True),
    (r"county clerk", "county_clerk", PRO, True),
    (r"city clerk|town clerk", "town_clerk", PRO, True),
    (r"assessor", "town_assessor", PRO, True),
    (r"alderman|coroner|recorder|city (?:collector|treasurer|crier|marshal|wood inspector)|"
     r"county (?:collector|commissioner)|street commissioner|\bmarshal\b|inspector port|"
     r"school inspector",
     "town_officer", PRO, False),
    (r"justice of (?:the )?peace", "justice_of_the_peace", PRO, True),
    (r"fire warden|fireman", "fire_warden", PRO, True),
    (r"indian agent|sub-?agent", "indian_agent", PRO, True),
    (r"interpreter", "interpreter", PRO, True),
    (r"midwife|nurse", "domestic", PRO, False),
    # commerce
    (r"forwarding|commission", "forwarding_and_commission", COM, True),
    (r"auctioneer", "auctioneer", COM, True),
    (r"dry ?goods|draper", "dry_goods_merchant", COM, True),
    (r"hardware|stove", "hardware_merchant", COM, True),
    (r"drug|apothecar|chemist", "druggist", COM, True),
    (r"book ?seller|stationer|book ?store|book ?bind", "bookseller", COM, True),
    (r"lumber|wood merchant|timber", "lumber_merchant", COM, True),
    (r"grocer|grocery|groceries|provision|flour|fish dealer|meat market|crockery|cutlery", "grocer", COM, True),
    (r"liquor|wine|spirit", "liquor_dealer", COM, True),
    (r"ship chandler", "ship_chandler", COM, True),
    (r"land agent|real estate|land claims|land office", "land_agent", COM, True),
    (r"insurance", "insurance_agent", COM, True),
    (r"speculat", "speculator", COM, True),
    (r"pedlar|pedler|huckster", "pedlar", COM, True),
    (r"trader|indian trade", "trader", COM, True),
    (r"\bclerk\b|book ?keeper|cashier|salesman|accountant|teller", "clerk", COM, True),
    (r"\bbank(?:er|ers|ing)\b|broker|capitalist|lottery", "banker", COM, False),
    (r"warehouse", "warehouseman", COM, False),
    (r"merchant|\bstore\b|shop ?keeper|dealer", "merchant", COM, True),
    # lodging, victualling and service
    (r"barber|hair cutting|shaving", "barber_surgeon", MFG, True),
    (r"boarding", "boarding_house_keeper", COM, True),
    (r"hotel|tavern|inn ?keeper|landlord|saloon|ball-?alley", "tavern_keeper", COM, True),
    (r"refectory|restaurant|eating|coffee ?house|victual", "refectory_keeper", COM, True),
    (r"confection|ice ?cream|candies", "confectioner", MFG, True),
    (r"livery|hostler|ostler", "livery_stable_keeper", COM, True),
    (r"bar-?tender|bar-?keeper", "bar_keeper", COM, False),
    (r"steward", "steward", MFG, False),
    (r"sexton", "sexton", MFG, False),
    (r"laundress|washer", "laundress", MFG, True),
    (r"domestic|servant|cook\b|waiter|chamber ?maid", "domestic", MFG, False),
    (r"\bporter\b|helper|labor(?:er|ers)?\b|labour|wood.?chopper", "labourer", MFG, True),
    # building and the mechanic trades
    (r"carpenter|joiner|stair-?builder|house-?mover|sash", "carpenter", MFG, True),
    (r"builder|contractor(?! *,)|bridge", "builder", MFG, True),
    (r"mason|bricklayer|stone ?cutter|lime burner", "mason", MFG, True),
    (r"brick ?maker", "brickmaker", MFG, True),
    (r"plasterer", "plasterer", MFG, True),
    (r"painter|glazier|dyer|scourer", "painter", MFG, True),
    (r"blacksmith|horse ?shoer|farrier|smith\b", "blacksmith", MFG, True),
    (r"gunsmith", "gunsmith", MFG, True),
    (r"locksmith|machinist|foundry|found(?:er|ryman)|moulder|molder|copper|iron\b",
     "founder", MFG, True),
    (r"engraver", "engraver", MFG, False),
    (r"mill ?wright", "millwright", MFG, False),
    (r"foreman", "foreman", MFG, False),
    (r"tinner|tin ?smith|tin and|\btin\b", "tinsmith", MFG, True),
    (r"silver ?smith", "silversmith", MFG, True),
    (r"watch ?maker|jewell?er|clock", "watchmaker", MFG, True),
    (r"cooper", "cooper", MFG, True),
    (r"wheelwright|wagon|carriage|plow ?maker|fanning ?mill|cradle", "carriage_maker", MFG, True),
    (r"cabinet|chair ?maker|furniture|undertaker|turner|upholster", "cabinet_maker",
     MFG, False),
    (r"trunk", "trunk_maker", MFG, True),
    (r"harness|saddle", "harness_maker", MFG, True),
    (r"tanner|currier|leather", "tanner", MFG, True),
    (r"boot|shoe ?maker|shoes|cordwainer", "shoemaker", MFG, True),
    (r"tailor|clothier|cloak|clothing|cutter\b", "tailor", MFG, True),
    (r"milliner|mantua|dress ?maker|bonnet|seamstress|tailoress", "milliner", MFG, True),
    (r"hatter|hat and cap|\bcaps?\b|\bhats?\b", "hatter", MFG, True),
    (r"sail ?maker", "sailmaker", MFG, True),
    (r"ship ?carpenter|ship ?builder", "ship_carpenter", MFG, True),
    (r"baker|bake ?house", "baker", MFG, True),
    (r"butcher|sausage", "butcher", MFG, True),
    (r"brewer|brewery|malt", "brewer", MFG, True),
    (r"distiller", "liquor_dealer", MFG, True),
    (r"soap|candle", "soap_and_candle_maker", MFG, True),
    (r"packer|pork", "packer", MFG, True),
    (r"miller|grist|mill\b", "miller", MFG, True),
    (r"sawyer|saw ?mill", "sawyer", MFG, True),
    (r"printer|compositor|pressman|type", "printer", MFG, True),
    (r"cigar|tobacco", "confectioner", MFG, False),
    (r"musician|violinist|vocalist|actor|actress|comedian|dancing", "music_teacher",
     MFG, False),
    # carriage, the river and the lake
    (r"drayman|dray\b|cartman|carter|\bdriver\b", "drayman", RIV, False),
    (r"teamster|teaming", "teamster", RIV, True),
    (r"drover|cattle|herdsman|horse ?dealer", "drover", AGR, True),
    (r"mail contractor|stage", "mail_contractor", RIV, True),
    (r"ferry", "ferryman", RIV, True),
    (r"boatman|waterman|canal|steam ?boat|steamer|vessel|\bmate\b|pilot|north branch",
     "boatman", RIV, True),
    (r"master mariner|captain|\bcapt\b|schooner|\bbark\b|\bbrig\b", "master_mariner", OCN, True),
    (r"sailor|seaman|mariner|fisherman|\bship\b", "seaman", OCN, True),
    (r"light-?house", "lighthouse_keeper", RIV, True),
    (r"harbour|harbor", "harbour_agent", RIV, True),
    # the land
    (r"farmer|farming", "farmer", AGR, True),
    (r"gardener|florist|nursery|milk ?man|cow ?feeder|dairy", "gardener", AGR, False),
    (r"hunter|trapper", "hunter", AGR, True),
    # the garrison
    (r"garrison|\barmy\b|lieut|sergeant|private\b", "soldier", PRO, True),
]

COLUMN_KEYS = {AGR: "nindagr", COM: "nindcom", MFG: "nindmfg", OCN: "nindocn",
               RIV: "nindriv", PRO: "nindeng"}


def head_phrase(printed):
    """The trade slot's own words, with the employer and address cut away.

    The segmenter puts everything after the name into `occupation`, and in this
    volume that slot often carries the employer too — "clerk, Charles Walker &
    Co". The trade is what stands before the first comma; the rest names
    somebody else's house and is not this person's trade.
    """
    text = (printed or "").strip().lower()
    text = text.split(",")[0]
    for broken, repaired in OCR_REPAIRS.items():
        text = text.replace(broken, repaired)
    text = re.sub(r"[’']s\b", "", text)
    text = re.sub(r"[^a-z0-9&.\- ]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip(" .-")
    return text


def classify(phrase):
    """(trade, column, in_vocabulary) or (None, refusal_class, refusal_note).

    The order is the argument. What cannot be a trade at all goes first; the
    trade patterns next; and the classes that could swallow a real trade — an
    employer's name, an address — only after every trade pattern has failed.
    """
    for name, pattern, why in REFUSALS_FIRST:
        if re.search(pattern, phrase):
            return None, name, why
    for pattern, trade, column, in_vocab in TRADES:
        if re.search(pattern, phrase):
            return trade, column, in_vocab
    for name, pattern, why in REFUSALS_LAST:
        if re.search(pattern, phrase):
            return None, name, why
    return None, "no_rule_reaches_it", ("the trade slot carries words no committed "
                                        "rule places — a forename the segmenter kept, "
                                        "a works, a vessel or a trade this volume "
                                        "prints once. Counted, printed, and left for "
                                        "a reader rather than guessed at")


def read_entries():
    with open(ENTRIES, encoding="utf-8") as fh:
        return json.load(fh)["claims"]


def vocabulary():
    with open(INDEX, encoding="utf-8") as fh:
        return set(json.load(fh)["vocabulary"]["occupations"])


def industry_columns_1840():
    with open(TOWN_MODEL, encoding="utf-8") as fh:
        model = json.load(fh)
    section = {s["key"]: s for s in model["sections"]}["occupations"]
    return section["tables"]["employment_shape_1840"]["rows"]


def build_table():
    entries = read_entries()
    vocab = vocabulary()

    mapped = {}          # trade -> {count, forms{}, column, in_vocabulary}
    refused = {}         # class -> {count, why, forms{}}
    with_trade = 0

    for entry in entries:
        printed = (entry.get("normalized") or {}).get("occupation")
        if not (printed or "").strip():
            continue
        with_trade += 1
        phrase = head_phrase(printed)
        trade, column, flag = classify(phrase)
        if trade is None:
            slot = refused.setdefault(column, {"count": 0, "why": flag, "forms": {}})
            slot["count"] += 1
            slot["forms"][phrase] = slot["forms"].get(phrase, 0) + 1
            continue
        row = mapped.setdefault(trade, {"count": 0, "column": column,
                                        "in_vocabulary": bool(flag), "forms": {}})
        row["count"] += 1
        row["forms"][phrase] = row["forms"].get(phrase, 0) + 1

    mapped_total = sum(r["count"] for r in mapped.values())
    refused_total = sum(r["count"] for r in refused.values())

    rows = []
    for trade in sorted(mapped, key=lambda t: (-mapped[t]["count"], t)):
        row = mapped[trade]
        in_vocab = trade in vocab
        rows.append({
            "trade": trade,
            "in_vocabulary": in_vocab,
            "column_1840": row["column"],
            "count": row["count"],
            "share_of_mapped": round(row["count"] / mapped_total, 5) if mapped_total else 0,
            "printed_forms": [{"as_printed": form, "n": n} for form, n in
                              sorted(row["forms"].items(), key=lambda kv: (-kv[1], kv[0]))],
        })

    # The 1839 shape by industry column, set against the 1840 schedule's own.
    by_column = {}
    for row in rows:
        by_column[row["column_1840"]] = by_column.get(row["column_1840"], 0) + row["count"]
    columns = []
    for row_1840 in industry_columns_1840():
        column = row_1840["column"]
        n_1839 = by_column.get(column, 0)
        share_1839 = round(n_1839 / mapped_total, 5) if mapped_total else 0
        columns.append({
            "column": column,
            "ipums_variable": row_1840["ipums_variable"],
            "persons_1840": row_1840["persons"],
            "share_of_employed_1840": row_1840["share_of_employed"],
            "entries_1839": n_1839,
            "share_of_mapped_1839": share_1839,
            "delta": round(share_1839 - row_1840["share_of_employed"], 5),
        })
    # Mining has no 1839 entry and the schedule returns two persons; the row is
    # printed at zero rather than dropped, because a column this reading cannot
    # fill is a finding about the reading.

    outside = sorted((r["trade"] for r in rows if not r["in_vocabulary"]))

    doc = {
        "schema": 1,
        "$schema_note": "DERIVED — regenerate with tools/build_trade_table_1839.py "
                        "--build; tools/check.sh re-derives it. Do not hand-edit.",
        "id": "fergus_1839_trade_table",
        "ticket": "T-1346",
        "generated_by": "tools/build_trade_table_1839.py --build",
        "source_id": SOURCE_ID,
        "describes_date": "1839",
        "reads": "data/research/directories/claims/fergus_1839_directory_entries.json",
        "not_a_reading": "an aggregate over a committed reading — no page was opened "
                         "here, nobody is named, and no person's card is touched",
        "date_note": "1839 IS FOUR YEARS AFTER THE SCENE, and this volume is Fergus's "
                     "1876 completion of a list that, in the compiler's own words, "
                     "\"was never written\". Every share below is the shape of a LATER "
                     "town recalled later still. It is a prior for a draw and it is "
                     "not a count of 1835, nor evidence about any person in it.",
        "how_to_use_it": "T-1347 draws a reconstructed head's trade from `rows`, "
                         "renormalised over the trades it is drawing for. A row whose "
                         "`in_vocabulary` is false may not be written onto a person "
                         "until data/residents/index.json carries the term.",
        "supersedes": "the per-trade table T-1162 was withdrawn before building; its "
                      "§2 asked for exactly this share and nothing else supplies it",
        "counts": {
            "entries": len(entries),
            "entries_with_a_printed_trade": with_trade,
            "mapped": mapped_total,
            "refused": refused_total,
            "distinct_trades": len(rows),
            "trades_outside_the_1835_vocabulary": len(outside),
            "share_mapped": round(mapped_total / with_trade, 5) if with_trade else 0,
        },
        "method": {
            "the_slot": "The segmenter puts everything after the name into the "
                        "occupation slot, employer and all. The trade is what stands "
                        "before the first comma; the rest names somebody else's house.",
            "first_rule_wins": "OCR repairs, then refusals, then the trade patterns, "
                               "in the order they are written in the tool. The first "
                               "rule that matches decides, so a specific trade is "
                               "always set above the general one it contains.",
            "nothing_is_dropped": "mapped + refused == entries with a printed trade. "
                                  "Every refusal carries its class, its reason and "
                                  "every form it caught.",
            "compounds": "A compound trade — \"carpenter and builder\", \"grocer and "
                         "liquor dealer\" — is counted once, under whichever of its "
                         "trades the ordered rules reach first. The volume prints no "
                         "second slot and this table invents none.",
            "determinism": "Sorted throughout and rounded to five places, so two "
                           "builds on one set of inputs are byte-identical.",
        },
        "trades_outside_the_1835_vocabulary": {
            "terms": outside,
            "note": "The 1839 volume prints these trades and data/residents/index.json "
                    "has no word for any of them. They are counted here because a "
                    "share that quietly drops a town's draymen is wrong about its "
                    "carpenters too. T-1347 must extend the vocabulary before it may "
                    "write one of these people.",
        },
        "rows": rows,
        "against_the_1840_industry_columns": {
            "note": "The 1840 schedule counts PERSONS IN FAMILIES by industry and this "
                    "table counts DIRECTORY ENTRIES by trade. The two are not the same "
                    "unit and the deltas are read as shape, not as error.",
            "columns": columns,
        },
        "refusals": [
            {
                "class": name,
                "count": refused[name]["count"],
                "why": refused[name]["why"],
                "forms": [{"as_printed": form, "n": n} for form, n in
                          sorted(refused[name]["forms"].items(),
                                 key=lambda kv: (-kv[1], kv[0]))],
            }
            for name in sorted(refused, key=lambda n: (-refused[n]["count"], n))
        ],
    }
    return doc


def write(doc):
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, ensure_ascii=False)
        fh.write("\n")


def report(doc):
    c = doc["counts"]
    print(f"  {c['entries']:,} entries, {c['entries_with_a_printed_trade']:,} carrying a "
          f"printed trade")
    print(f"  mapped {c['mapped']:,} ({c['share_mapped']:.1%}) onto {c['distinct_trades']} "
          f"trades; refused {c['refused']:,}")
    print(f"  {c['trades_outside_the_1835_vocabulary']} trade(s) the 1835 vocabulary "
          f"has no word for")
    for row in doc["rows"][:12]:
        mark = " " if row["in_vocabulary"] else "*"
        print(f"    {row['count']:>4}  {row['share_of_mapped']:.3f}  {mark}{row['trade']}")
    for refusal in doc["refusals"]:
        print(f"    refused {refusal['count']:>4}  {refusal['class']}")


def self_test():
    """The rules' own assertions. Each one fires if the rule it pins is broken."""
    cases = [
        # the slot is cut at the first comma, so an employer is never a trade
        ("clerk, Charles Walker & Co", "clerk"),
        ("carpenter, Alex. Loyd", "carpenter"),
        # the scan's four broken trades are repaired by name
        ("laboi'er", "labourer"),
        ("cai'penter", "carpenter"),
        ("clei'k", "clerk"),
        # a compound is counted once, under the rule that reaches it first
        ("carpenter and builder", "carpenter"),
        ("boot and shoe maker", "shoemaker"),
        ("attorney and counsellor at law", "attorney"),
        # British spelling is the layer's, not the volume's
        ("laborer", "labourer"),
        # a trade outside the vocabulary is still counted
        ("drayman", "drayman"),
        # a bare house-word IS the trade; a house carrying a proper name is not
        ("boarding-house", "boarding_house_keeper"),
        ("saloon", "tavern_keeper"),
        # and the barber's saloon is neither
        ("haircutting and shaving saloon", "barber_surgeon"),
        ("bookkeeper", "clerk"),
    ]
    problems = []
    for printed, want in cases:
        got, _, _ = classify(head_phrase(printed))
        if got != want:
            problems.append(f"{printed!r} -> {got!r}, wanted {want!r}")

    refusals = [
        ("Briggs & Humphrey", "a_firm_style"),
        ("American Hotel", "a_house_not_a_trade"),
        ("121 Lake st", "an_address"),
        ("with Sylvester Marsh", "an_employer_or_a_name"),
        ("\\", "not_legible"),
    ]
    for printed, want in refusals:
        trade, klass, _ = classify(head_phrase(printed))
        if trade is not None or klass != want:
            problems.append(f"{printed!r} -> {trade or klass!r}, wanted refusal {want!r}")

    # the balance: nothing may be dropped between the entries and the table
    doc = build_table()
    c = doc["counts"]
    if c["mapped"] + c["refused"] != c["entries_with_a_printed_trade"]:
        problems.append("mapped + refused does not equal the entries carrying a trade")
    if sum(r["count"] for r in doc["rows"]) != c["mapped"]:
        problems.append("the rows do not sum to the mapped total")
    # and the build is stable
    if json.dumps(build_table(), sort_keys=True) != json.dumps(doc, sort_keys=True):
        problems.append("two builds on one set of inputs differ")

    for problem in problems:
        print(f"  FAIL {problem}", file=sys.stderr)
    if problems:
        return 1
    print(f"  {len(cases) + len(refusals)} rule case(s), the balance and the rebuild hold")
    return 0


def main():
    argv = sys.argv[1:]
    if "--self-test" in argv:
        return self_test()
    doc = build_table()
    if "--check" in argv:
        if not os.path.exists(OUT):
            print(f"  FAIL {os.path.relpath(OUT, ROOT)} is missing — run --build",
                  file=sys.stderr)
            return 1
        with open(OUT, encoding="utf-8") as fh:
            have = json.load(fh)
        if json.dumps(have, sort_keys=True) != json.dumps(doc, sort_keys=True):
            print("  FAIL the committed trade table does not re-derive from the "
                  "committed entries — re-run --build", file=sys.stderr)
            return 1
        report(doc)
        return 0
    if "--build" in argv:
        write(doc)
        report(doc)
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
