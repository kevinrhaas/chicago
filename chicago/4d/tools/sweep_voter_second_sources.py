#!/usr/bin/env python3
"""The second-source sweep for the 1835 poll list (T-0493).

    tools/sweep_voter_second_sources.py --sweep    fetch, search, write the log

A man on the 1835 poll list was in Chicago in 1835, and that is the strongest
residence evidence this project holds short of a newspaper naming him. Seventy of
the eighty-five reach no resident under `read_voter_lists.py`'s matching rules, and
the owner's grading ladder turns on whether a SECOND independent source names them:
a second source makes the man `attested`; the poll alone makes him `inferred`.

So every one of the seventy is searched, and EVERY SEARCH IS RECORDED — including,
and especially, the ones that found nothing. A negative search is evidence. An
unrecorded search is work the next sweep has to do again.

WHAT IS SEARCHED, and what each is worth:

  Andreas vol. 1 (`historyofchicago01andr`) — the full OCR text is fetched from
  archive.org and searched here rather than through the site's full-text index,
  because that index is demonstrably lossy (`data/sources/andreas_1884_v1.json`
  says so) and a miss through it is not a miss. Fetched, not committed: it is 5 MB
  of OCR of a book this repository does not hold, so the sha256 of what was read is
  recorded instead and every hit carries its verbatim passage.

  The Illinois State Archives public-domain land tract sales database — a purchase
  in T39N R14E before 1836 is an independent civic record of the man.

  earlychicago.com — tier 4, a pointer only, never evidence on its own.

  Genealogy Trails Cook County — the publisher of the transcription being read. It
  is checked so the check is on the record, and a hit there is NOT independent.

A HIT IS NOT A MATCH. What this file records is that a passage in Andreas names
this surname and a forename consistent with the poll entry. Whether the man in the
passage is the man on the poll is an identity judgement, and it belongs to the
consolidation (T-0513) and the mint (T-0514), not to a grep.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CIVIC = ROOT / "data" / "research" / "civic"
CROSSWALK = CIVIC / "voter_crosswalk.json"
LOG = CIVIC / "search_log.json"

ANDREAS_ITEM = "historyofchicago01andr"
ANDREAS_URLS = [
    "https://dn760009.eu.archive.org/0/items/%s/%s_djvu.txt" % (ANDREAS_ITEM, ANDREAS_ITEM),
    "https://archive.org/download/%s/%s_djvu.txt" % (ANDREAS_ITEM, ANDREAS_ITEM),
]
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/126 Safari/537.36")

# Things the sweep noticed that no automated rule could have produced, written down
# because the next sweep would otherwise spend its budget finding them again.
OBSERVATIONS = [
    {"about": "Ballingale, P.",
     "note": "The sweep returns a clean negative for the spelling the poll prints. "
             "Andreas nevertheless sets a 'P. Ballingall' — two Ls — among the "
             "officers of a masonic lodge elected in December 1849. That is LATER "
             "EVIDENCE and under the owner's grading ladder it can never make an "
             "1835 resident on its own; it is recorded because it shows what this "
             "sweep's negatives are worth. A negative is a negative FOR A SPELLING, "
             "and these lists spell badly."},
    {"about": "the fourteen clean negatives",
     "note": "A negative in Andreas is not an absence from Chicago. Andreas is a "
             "compilation of 1884 that names the men its informants remembered; a "
             "cooper who voted once and left is exactly the man it omits. Under the "
             "grading ladder these men stand on the 1835 poll ALONE, which makes "
             "them `inferred` and not `attested` — and inferred is the right answer, "
             "not a failure of the sweep."},
]

PROBES = [
    {"source": "Illinois State Archives — Public Domain Land Tract Sales",
     "url": "https://apps.ilsos.gov/isa/landsrch.jsp",
     "also_tried": "A separate request to the same host on the same day returned "
                   "HTTP 403 rather than timing out. The database is up and will not "
                   "answer this runner; it holds no opinion about these men either "
                   "way, and nothing here may be read as an absence from it.",
     "what_was_wanted": "a land purchase in T39N R14E, 1830-1835, as a second "
                        "independent civic record for a man on the 1835 poll"},
    {"source": "earlychicago.com",
     "url": "http://earlychicago.com/",
     "what_was_wanted": "a tier-4 pointer to a contemporary record naming the man"},
    {"source": "Genealogy Trails, Cook County, Illinois",
     "url": "https://genealogytrails.com/ill/cook/",
     "what_was_wanted": "any Cook County record naming the man APART FROM the "
                        "voter-list page this ticket is reading, which is the same "
                        "transcription and is therefore not independent"},
]


def fetch(url: str, timeout=300):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def dump(p: Path, doc) -> None:
    p.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def flatten(text: str) -> str:
    """OCR of a 19th-century page breaks words across lines and doubles its spaces.
    Searching the flattened text finds a name the raw text hides; the PASSAGE that
    comes back is cut from this same flattened form and says so."""
    return re.sub(r"\s+", " ", text)


def split_entry(as_read: str):
    if "," in as_read:
        s, f = as_read.split(",", 1)
        return s.strip(), f.strip()
    return as_read.strip(), ""


def forename_letters(forenames: str):
    out = []
    for tok in re.split(r"[\s.]+", forenames):
        tok = re.sub(r"[^A-Za-z]", "", tok)
        if tok and tok.lower() not in ("col", "maj", "major", "capt", "dr", "mr",
                                       "lt", "rev", "gen", "hon", "jr", "sr"):
            out.append(tok)
    return out


def name_patterns(surname: str, forenames):
    """The ways this book sets a name, and no others.

    An earlier pass of this sweep matched the surname alone in a 60-character
    window and called that a hit; it returned `bond-holders` for `Bond, H.` and
    `hard bread` for `Bread, A.O.T.`. A surname is a common English word often
    enough that proximity is not evidence. So the search is for a NAME — a
    forename or initial standing immediately in front of the surname, with up to
    two middle initials between, or the index form `Surname, Forename` this
    volume's index uses — and it is case-sensitive, because `bread` is not
    `Bread`.
    """
    if not forenames:
        return []
    def alt(tok):
        # an initial stands for itself or for any forename beginning with it,
        # which is how the book prints the same man two ways on facing pages
        if len(tok) == 1:
            return r"%s(?:\.|[a-z]+)" % re.escape(tok)
        return r"%s\b" % re.escape(tok)
    first = alt(forenames[0])
    middles = r"(?:\s+[A-Z](?:\.|[a-z]+)){0,2}"
    s = re.escape(surname)
    return [
        re.compile(r"\b%s%s\s+%s\b" % (first, middles, s)),          # Alvin Calhoun
        re.compile(r"\b%s,?\s+%s%s\b" % (s, first, middles)),        # Calhoun, Alvin
    ]


def search_andreas(flat: str, surname: str, forenames):
    """Every NAME-SHAPED passage naming this man, and a count of the bare-surname
    appearances that were deliberately not counted as evidence.

    A hit means the book sets this surname behind a forename the poll prints. It
    does NOT mean the man in the passage is the man on the poll — that is an
    identity judgement, and it belongs to T-0513 and T-0514.
    """
    hits = []
    seen = set()
    for pattern in name_patterns(surname, forenames):
        for m in pattern.finditer(flat):
            if any(abs(m.start() - o) < 40 for o in seen):
                continue
            seen.add(m.start())
            s = max(0, m.start() - 240)
            e = min(len(flat), m.end() + 240)
            hits.append({"matched": m.group(0), "passage": flat[s:e],
                         "offset": m.start()})
            if len(hits) >= 3:
                break
        if len(hits) >= 3:
            break
    bare = len(re.findall(r"\b%s\b" % re.escape(surname), flat))
    return hits, bare - len(hits)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sweep", action="store_true", required=True)
    ap.parse_args()

    cross = load(CROSSWALK)
    targets = [e for e in cross["entries"]
               if e["list"] == "poll_1835" and e["outcome"] != "matched"]

    blob, used_url, err = None, None, None
    for url in ANDREAS_URLS:
        try:
            blob = fetch(url)
            used_url = url
            break
        except Exception as exc:                                  # network, not logic
            err = "%s: %s" % (url, exc)
    if blob is None:
        sys.exit("Andreas vol. 1 could not be fetched (%s). The sweep records "
                 "negatives and a negative that is really a fetch failure is a lie, "
                 "so nothing is written." % err)
    text = blob.decode("utf-8", "replace")
    flat = flatten(text)
    sha = hashlib.sha256(blob).hexdigest()

    probes = []
    for probe in PROBES:
        entry = dict(probe)
        try:
            body = fetch(probe["url"], timeout=45)
            entry["result"] = "reachable"
            entry["bytes"] = len(body)
        except urllib.error.HTTPError as exc:
            # A refusal is not an absence. The database may hold the man and simply
            # will not answer this runner, and the grading ladder must never read
            # that as "no second source".
            entry["result"] = "inaccessible"
            entry["detail"] = "HTTP %s %s" % (exc.code, exc.reason)
        except Exception as exc:
            entry["result"] = "inaccessible"
            entry["detail"] = str(exc)
        entry["searched_on"] = date.today().isoformat()
        probes.append(entry)

    searches = []
    for e in targets:
        surname, forenames = split_entry(e["as_read"])
        letters = forename_letters(forenames)
        hits, surname_only = search_andreas(flat, surname, letters)
        searches.append({
            "record_id": e["record_id"],
            "as_read": e["as_read"],
            "normalized": e["normalized"],
            "crosswalk_outcome": e["outcome"],
            "source": "andreas_1884_v1",
            "query": "the name %r set as the book sets a name — a forename or "
                     "initial of %s standing immediately in front of the surname, "
                     "or the index form; case-sensitive" % (e["as_read"], letters
                                                            or "[none printed]"),
            "searched_on": date.today().isoformat(),
            "result": "hit" if hits else (
                "the surname appears, never behind a forename the poll prints"
                if surname_only else "negative"),
            "bare_surname_appearances_not_counted": surname_only,
            "hits": hits,
            "limitation": "Andreas is a compilation of 1884, tier 3, and its OCR is "
                          "lossy: a negative here is a negative SEARCH and not an "
                          "absence from the book.",
        })

    found = [s for s in searches if s["result"] == "hit"]
    dump(LOG, {
        "schema": 1,
        "_doc": "GENERATED by tools/sweep_voter_second_sources.py --sweep. Every "
                "second-source search made for a man on the 1835 poll list who "
                "reaches no resident, positive and negative alike. A negative is "
                "evidence; an unrecorded search is work the next sweep repeats.",
        "generated_by": "tools/sweep_voter_second_sources.py --sweep",
        "ticket": "T-0493",
        "swept_on": date.today().isoformat(),
        "corpus": {
            "source_id": "andreas_1884_v1",
            "item": ANDREAS_ITEM,
            "url": used_url,
            "sha256": sha,
            "bytes": len(blob),
            "committed": False,
            "why_not_committed": "5 MB of OCR of a book this repository does not "
                                 "hold. The sha256 fixes what was read and every hit "
                                 "carries its verbatim passage.",
        },
        "probes": probes,
        "observations": OBSERVATIONS,
        "counts": {
            "names_swept": len(searches),
            "with_a_second_source_hit": len(found),
            "surname_appears_but_never_as_this_man": sum(
                1 for s in searches if s["result"].startswith("the surname")),
            "negative": sum(1 for s in searches if s["result"] == "negative"),
        },
        "searches": searches,
    })
    print("swept %d name(s): %d hit, %d surname-only, %d negative; %d probe(s)"
          % (len(searches), len(found),
             sum(1 for s in searches if s["result"].startswith("the surname")),
             sum(1 for s in searches if s["result"] == "negative"), len(probes)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
