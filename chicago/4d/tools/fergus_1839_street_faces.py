#!/usr/bin/env python3
"""What Fergus 1839 says about the STREETS of Chicago, compiled (T-0506).

The 1839 street face is the best proxy for 1835 this project will ever hold: for
1,655 entries it prints a trade and a street, and no other source in the corpus
gives both for so many people at once. This compiles them — every street name as
printed, the trades standing on it, and every entry with a business address — so
the street tickets (T-0444..T-0447, T-0451) have something to read.

`--build` writes `data/research/directories/fergus_1839_street_faces.json`;
`--check` rebuilds and compares.

TWO THINGS THIS IS NOT.
  * It is not an 1835 street face. 1839 is four years late and the volume is
    Fergus's 1876 recollection of it; a trade here is a candidate for 1835, never
    an 1835 fact, and nothing downstream may place a shop from this file alone.
  * It is not an address list. Fergus prints on page 3 that no street but Lake
    carried numbers in 1839 and "the numbers now given are those of the present
    day" — 1876's. The street NAME is the whole of what survives, which is why
    this file counts streets and not addresses.

THE TRADES WITH NO VOCABULARY WORD are listed for T-0418, which owns the gap in
`compile_register.py`'s TRADE_TO_OCCUPATION. A trade this directory prints and the
residents vocabulary cannot say is a trade this project would have to drop on the
floor, and counting them is the point of the list.
"""
import json, os, re, sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
ENTRIES = os.path.join(ROOT, "data/research/directories/claims/fergus_1839_directory_entries.json")
TOWN = os.path.join(ROOT, "data/research/directories/claims/fergus_1839_town_findings.json")
OUT = os.path.join(ROOT, "data/research/directories/fergus_1839_street_faces.json")

from compile_register import occupation_of  # noqa: E402  the closed vocabulary's table

# The compiler's abbreviations, folded so that "So. Water st", "S. Water street"
# and "South Water st" count as one street. The fold is on the KEY only; every
# spelling the volume actually prints is kept beside it.
DIRS = {"n": "North", "no": "North", "north": "North", "s": "South", "so": "South",
        "south": "South", "e": "East", "east": "East", "w": "West", "west": "West"}
SUFFIX = re.compile(r"\b(?:st|street|streets|sts|ave|avenue|av|road|rd|alley|place|court|square)\b\.?",
                    re.I)


AVENUE = re.compile(r"\b(?:ave|avenue|av)\b\.?$", re.I)


def street_key(printed: str) -> str:
    """One street, folded to a comparable key. 'So. Water st' -> 'south water'.

    The suffix is dropped, with ONE exception: an avenue keeps it. Michigan avenue
    and Michigan street are two different streets in this town and folding them
    together would invent a street face neither of them has.
    """
    avenue = bool(AVENUE.search((printed or "").strip(" .,")))
    s = SUFFIX.sub("", printed or "").strip(" .,")
    toks = [t.strip(" .,") for t in s.split() if t.strip(" .,")]
    # "north end of Michigan ave." reads out of the address as "of Michigan ave";
    # the preposition is not part of the street's name.
    STOP = ("of", "the", "near", "cor", "bet", "opposite", "and", "at", "end", "foot")
    while toks and (toks[0].strip(".").lower() in STOP
                    or (len(toks) > 1 and toks[1].strip(".").lower() == "of")):
        toks = toks[1:]
    out = []
    for i, tok in enumerate(toks):
        bare = tok.strip(".").lower()
        if i == 0 and bare in DIRS:
            out.append(DIRS[bare].lower())
        else:
            out.append(bare)
    if avenue:
        out.append("avenue")
    return " ".join(out)


def main():
    entries = json.load(open(ENTRIES, encoding="utf-8"))["claims"]
    town = json.load(open(TOWN, encoding="utf-8"))["claims"]

    streets = defaultdict(lambda: {"printed": Counter(), "entries": 0, "trades": Counter(),
                                   "firms": 0})
    trades = Counter()
    untranslatable = Counter()
    with_address = 0
    for c in entries:
        n = c["normalized"]
        trade = (n["occupation"] or "").strip()
        if trade:
            trades[trade] += 1
            if occupation_of(trade) is None:
                untranslatable[trade] += 1
        if n["address"]:
            with_address += 1
        for printed in n["streets"]:
            key = street_key(printed)
            if not key:
                continue
            row = streets[key]
            row["printed"][printed] += 1
            row["entries"] += 1
            if n["firm"]:
                row["firms"] += 1
            if trade:
                row["trades"][trade] += 1

    for c in town:
        for printed in c["normalized"]["streets"]:
            key = street_key(printed)
            if key:
                streets[key]["printed"][printed] += 1

    rows = []
    for key in sorted(streets, key=lambda k: (-streets[k]["entries"], k)):
        row = streets[key]
        rows.append({
            "street": key,
            "as_printed": [p for p, _ in row["printed"].most_common()],
            "entries": row["entries"],
            "firms": row["firms"],
            "trades": [{"trade": t, "n": n} for t, n in row["trades"].most_common()],
        })

    businesses = [{
        "claim": c["id"],
        "as_printed": c["normalized"]["as_printed"],
        "printed_page": c["locator"]["printed_page"],
        "address": c["normalized"]["address"],
        "streets": c["normalized"]["streets"],
        "address_is_street_only": bool(c["normalized"]["number_is_1876"]),
    } for c in entries if c["kind"] == "business" and c["normalized"]["address"]]

    doc = {
        "schema": 1,
        "_doc": "GENERATED by tools/fergus_1839_street_faces.py --build out of the committed "
                "Fergus 1839 claims. Streets as printed, the trades standing on each, the "
                "firms with an address, and the trades the residents vocabulary cannot say. "
                "1839 evidence recalled in 1876 — never on its own an 1835 fact.",
        "generated_by": "tools/fergus_1839_street_faces.py --build",
        "source_id": "fergus_chicago_directory_1839",
        "ticket": "T-0506",
        "number_rule": "Fergus, printed page 3: 'There were no numbers on any street (except "
                       "Lake Street,) at that time — the numbers now given are those of the "
                       "present day.' Every address number in this volume off Lake street is "
                       "an 1876 number. This file counts STREETS, not addresses.",
        "counts": {
            "entries": len(entries),
            "entries_with_an_address": with_address,
            "distinct_streets": len(rows),
            "distinct_trades": len(trades),
            "trades_the_vocabulary_cannot_say": len(untranslatable),
            "entries_under_a_trade_the_vocabulary_cannot_say": sum(untranslatable.values()),
            "firms_with_an_address": len(businesses),
        },
        "streets": rows,
        "trades": [{"trade": t, "n": n} for t, n in trades.most_common()],
        "trades_with_no_vocabulary_word": {
            "for": "T-0418",
            "note": "Each of these is printed by Fergus as somebody's trade and has no word in "
                    "the residents vocabulary (compile_register.py TRADE_TO_OCCUPATION). A "
                    "person compiled from this directory would arrive trade-less. Listed, not "
                    "invented: adding a word to a closed vocabulary is T-0418's call.",
            "trades": [{"trade": t, "n": n} for t, n in untranslatable.most_common()],
        },
        "firms_with_an_address": businesses,
    }
    if "--check" in sys.argv:
        if json.load(open(OUT, encoding="utf-8")) != doc:
            print("fergus 1839 street faces: the committed file does not match — regenerate",
                  file=sys.stderr)
            return 1
        print("fergus 1839 street faces: matches the committed file")
        return 0
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    print(json.dumps(doc["counts"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
