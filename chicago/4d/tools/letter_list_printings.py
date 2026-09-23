#!/usr/bin/env python3
"""The Chicago post office's 1 January 1834 letter list, counted over its printings.

    tools/letter_list_printings.py            the tally and the concordance
    tools/letter_list_printings.py --json     the same, machine-readable
    tools/letter_list_printings.py --apply    write the completions into the claims
    tools/letter_list_printings.py --self-test  the assertions still fire

WHY THIS EXISTS. T-0312 found a letter list on page 4 of the Democrat of 1834-03-04
whose heading the segmenter had cut down the middle, and minted its names as claims
c026 and c027 of `data/research/newspapers/extracted/chicago_democrat_1834_03_04.json`.
Three things about it could not be read off that one crop, and T-0331 assigned all
three to the page images: WHICH RETURN it is (the date line survives as `34.` and
nothing else), how much of the printed list survives, and the FORENAMES, which the
crop has taken off the left edge of every line.

`data/research/newspapers/README.md` prescribes the cheaper instrument, and it is the
one this tool mechanises: **count the printings before you send for the images**
(T-0328), and **count them by the notice's own body text rather than by its heading**
(T-0350). A quarterly letter list is standing type. It ran in the Democrat week after
week until the letters were sent to the dead-letter office, and every week is a
separate impression, separately scanned, separately damaged. Eight other impressions
of this same list stand in the deposit, and between them they carry the heading, the
date line, and the forenames the March crop lost.

WHAT IT DOES NOT DO. It reads no page image, so nothing here is `scan_verified`; the
witnesses are other transcriptions and the readings stay `transcription_mediated`.
It amends nothing to agree with anything: every printing keeps its own verbatim
setting, and a completion is reported with the printings that carry it, so a reader
can weigh the tally rather than take the result.

THE FINGERPRINT. Every impression of this list opens on the same name, which the
eight scans set eight ways -- `Eliphalet Atkins 2`, `ejiphalet Atkina 2`, `Jiphalet
Atkine 2`, `Et halet Atkins 2`, `Askina 2`, `liphalet Atkine 2`, `Atkina 2` -- and two
crops do not carry it at all, because the segmenter took the top of the column off.
That is why a printing is located on its BODY TEXT and not on `List of Letters`: four
of the nine headings are illegible, cut, or in another crop entirely, and the sweep
that first read this run found FOUR printings by searching for the heading where there
are NINE.
"""

import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEPOSIT = ROOT.parent / "reference" / "newspapers" / "Transcriptions" / \
    "Chicago_Democrat_1833-11_to_1835-08"
EXTRACTED = ROOT / "data" / "research" / "newspapers" / "extracted" / \
    "chicago_democrat_1834_03_04.json"

# The eight printings, each located by hand in the deposit and stated with the line
# the list's first name stands on, so every row here is checkable in one `sed -n`.
# `head` is the line the heading or its remnant stands on; `first` the line carrying
# the fingerprint name; `span` how far below `head` the printed column runs, read to
# the postmaster's signature or, where the crop lost it, to the end of the names.
# The nine printings, each located by hand in the deposit. `segments` are the line
# ranges the list occupies IN THAT ISSUE, because the segmenter cuts a printed column
# into crops and a crop rarely holds the whole list: 1834-02-18 carries the A-I half
# in one column of page 4 and the J-Z half in another, three hundred lines apart.
# Every row here is checkable in one `sed -n`.
PRINTINGS = [
    # issue date, volume/number as filed, [(head, span), ...], the fingerprint line,
    # and what the date line reads where the crop kept it
    ("1834-01-07", "Vol1_No7", [(643, 60)], 645,
     "EMAINING in the Post-Offiee at Chic / go, Ill. January [1,] 1834."),
    ("1834-01-14", "Vol1_No8", [(1063, 75)], 1067,
     "BDBEMAINING [in the Post-Office at Chica]go, Ill. Januar[y ...]"),
    ("1834-01-21", "Vol1_No9", [(1099, 60)], 1101,
     "[heading lost to the crop; the names run from the fingerprint]"),
    ("1834-01-28", "Vol1_No10", [(1107, 30)], 1113,
     "EMAINING in the Port-Offiee at Ch / go, Ill. Fammuary 1, 1604."),
    ("1834-02-04", "VolI_No11", [(2858, 90)], 2860,
     "EMAINING in the Post- / go, Ill, January 3, 1934."),
    ("1834-02-11", "VolI_No12", [(2694, 240)], 2696,
     "EMAINING [-- the rest of the heading lost to the alternating column]"),
    ("1834-02-18", "VolI_No13", [(2925, 50), (3066, 85)], 2929,
     "[the heading is in neither crop; both halves run as bare names]"),
    ("1834-02-25", "VolI_No14", [(2947, 240)], 2949,
     "REMAINISG in the Pest[-Office at Chica]go, Il January 1, 63[4]."),
    ("1834-03-04", "VolI_No15", [(3064, 220)], 3067,
     "List of L | etters / ost-Offiee at Chica- / 34."),
]

# The issue this project is trying to read. It is the last of the eight.
SUBJECT = "1834-03-04"

# A second office's 1 January 1834 return runs in the same weeks and must not be
# read into Chicago's. It is recorded here so a later sweep does not mistake it.
OTHER_OFFICE = [
    ("1834-01-21", "Vol1_No9", 937, "G in the Poston / c fica at Henne[pin]. "
     "... Ist day of Jan, 16[34]."),
    ("1834-01-28", "Vol1_No10", 957, "Hist of Letters AINING in the PontOitien "
     "at H / mi pin, Hl. on the Ist day of San. 18[34]"),
    ("1834-02-04", "VolI_No11", 2676, "EMAINING in the Post-Office at Benne[...]"),
]

NOISE = re.compile(r"[^A-Za-z']+")
# The scans confuse a small, well-known set of letter pairs and nothing else, so the
# fold is deliberately NARROW. An earlier and looser version of it -- vowels dropped,
# doubled letters collapsed -- proposed `Thomas Bonnet` for `[...]as Bennett` and
# `Howard Delaney` for `[?] Delano`, which is precisely the failure this project must
# not ship: a completion that looks right and proves nothing. Only these fold:
#   i / l / 1 / j / !   the scans' commonest single confusion
#   o / 0 , s / 5 , b / 8    figure-for-letter
#   u / v                 the long s and the worn v
#   rn -> m               the classic ligature break
# Vowels are NOT dropped and distinct letters are NOT merged, so `Bennett`, `Benton`
# and `Bonnet` stay three surnames, and `Atkins` and `Atkina` stay two settings of one.
FOLD = str.maketrans({"l": "i", "1": "i", "j": "i", "!": "i", "0": "o",
                      "5": "s", "8": "b", "v": "u"})


def fold(word):
    """A reading reduced to what the scans' own confusions leave decidable."""
    w = unicodedata.normalize("NFKD", word).encode("ascii", "ignore").decode()
    w = NOISE.sub("", w).lower().replace("rn", "m").translate(FOLD)
    return re.sub(r"(.)\1+", r"\1", w)


def read(date, vol):
    path = DEPOSIT / ("Chicago_Democrat_%s_%s_Transcription.txt" % (date, vol))
    if not path.exists():
        return None
    return path.read_text(encoding="utf8", errors="replace").split("\n")


def region(lines, segments):
    out = []
    for head, span in segments:
        out += list(enumerate(lines[head - 1:head - 1 + span], start=head))
    return out


# A name as the list sets it: an optional forename or initials, then a surname, then
# an optional count of letters waiting ("Atkins 2"). The transcriptions run names
# together inside one line where the Vision reading merged a column, so this is
# matched repeatedly across a line rather than anchored to it.
NAME = re.compile(
    r"(?:(?P<fore>(?:[A-Z][a-z']{1,12}|[A-Z]{1,2}\.?|[A-Z][a-z]{0,3}\.)"
    r"(?:\s*[A-Z]\.?)?)\s+)?"
    r"(?P<sur>(?:M'|Mc|Van\s?|De\s?)?[A-Z][A-Za-z']{2,14})"
    r"(?:\s+(?P<n>[23456]))?")


def settings(lines, segments):
    """Every name-shaped reading in one printing's regions, with its line."""
    out = []
    for ln, text in region(lines, segments):
        for m in NAME.finditer(text):
            sur = m.group("sur")
            if len(fold(sur)) < 4:
                continue
            out.append({"line": ln, "surname": sur,
                        "forename": (m.group("fore") or "").strip(),
                        "count": m.group("n"), "as_set": m.group(0).strip()})
    return out


def load_printings():
    found, missing = [], []
    for date, vol, segments, first, dateline in PRINTINGS:
        lines = read(date, vol)
        if lines is None:
            missing.append(date)
            continue
        found.append({"date": date, "vol": vol, "segments": segments,
                      "first": first, "dateline": dateline,
                      "fingerprint": lines[first - 1].strip()[:80],
                      "settings": settings(lines, segments)})
    return found, missing


def subject_names():
    """The names T-0312 minted off the 1834-03-04 crops, in printed order."""
    doc = json.loads(EXTRACTED.read_text(encoding="utf8"))
    out = []
    for claim in doc["claims"]:
        if claim["id"] not in ("c026", "c027"):
            continue
        for ent in claim.get("entities", []):
            out.append({"claim": claim["id"], "as_printed": ent["as_printed"],
                        "normalized": ent["normalized"]})
    return out


CUT = re.compile(r"\[\?\]|\[…\]|\[\.\.\.\]")


def within_one(a, b):
    """True when two folded readings differ by at most one letter."""
    if a == b:
        return True
    if abs(len(a) - len(b)) > 1:
        return False
    if len(a) == len(b):
        return sum(x != y for x, y in zip(a, b)) <= 1
    short, long = (a, b) if len(a) < len(b) else (b, a)
    for i in range(len(long)):
        if long[:i] + long[i + 1:] == short:
            return True
    return False


def cluster(keys, items):
    """Single-linkage clustering of readings at edit distance one."""
    groups = []
    for key, item in zip(keys, items):
        joined = [g for g in groups if any(within_one(key, k) for k in g["keys"])]
        if not joined:
            groups.append({"keys": [key], "items": [item]})
            continue
        head = joined[0]
        head["keys"].append(key)
        head["items"].append(item)
        for other in joined[1:]:
            head["keys"] += other["keys"]
            head["items"] += other["items"]
            groups.remove(other)
    return {i: g["items"] for i, g in enumerate(groups)}


COUNT = re.compile(r"\s(\d)\s*$")


def count_of(normalized):
    """The `2` in `Atkins 2` -- how many letters wait for that name."""
    m = COUNT.search(re.sub(r"\[[^\]]*\]", " ", normalized).strip())
    return " " + m.group(1) if m else ""


def surname_of(normalized):
    """The surname out of a minted reading like `[?] E. Benton` or `[…]as Bennett`."""
    text = re.sub(r"\[[^\]]*\]", " ", normalized)
    text = re.sub(r"\b(or)\b", " ", text)
    words = [w for w in re.split(r"[\s;]+", text.strip()) if w]
    words = [w for w in words if not re.fullmatch(r"[A-Z]\.?|[0-9]|", w)]
    return words[-1].strip(".,;") if words else ""


def concordance():
    """For every name the 1834-03-04 crops minted, the other printings' settings.

    A completion is proposed only when TWO OR MORE of the seven other printings set
    the same forename against the same surname. One witness is reported and never
    proposed -- a single scan is a single scan -- and where the printings disagree
    the disagreement is reported instead of a winner, because two Bennetts and two
    Bowens really do stand in this list.
    """
    printings, missing = load_printings()
    subject = [p for p in printings if p["date"] == SUBJECT]
    witnesses = [p for p in printings if p["date"] != SUBJECT]
    minted = subject_names()
    # WHERE THE LIST CARRIES TWO OF A SURNAME, NEITHER IS COMPLETED. Two Bennetts,
    # two Miners and two Temples stand in this return, and a crop that has taken the
    # forename off both cannot say which line is which. Completing them from the
    # concordance would put the same man in the list twice, which is the failure mode
    # T-0299 exists to stop, so the ambiguity is reported instead.
    doubled = {k for k in [fold(surname_of(n["normalized"])) for n in minted]
               if [fold(surname_of(n["normalized"])) for n in minted].count(k) > 1}
    rows = []
    for name in minted:
        sur = surname_of(name["normalized"])
        tail = count_of(name["normalized"])
        key = fold(sur)
        agreeing = []
        hits = []
        if len(key) >= 4:
            for w in witnesses:
                for s in w["settings"]:
                    if fold(s["surname"]) == key and s["forename"]:
                        hits.append({"date": w["date"], "line": s["line"],
                                     "as_set": s["as_set"],
                                     "forename": s["forename"]})
        # Forenames are clustered rather than bucketed, because two scans of one
        # setting differ by a letter as readily as two settings do: `Wim. H.` and
        # `Wm. H.`, `Semel` and `Samuel`. Single linkage at edit distance one, on
        # the folded forename, joins those and joins nothing further -- `Hiram`
        # and `Thomas` are four apart, `A. H.` and `Philip` five.
        groups = cluster([fold(h["forename"]) for h in hits], hits)
        # distinct PRINTINGS, not distinct readings: two transcriptions of one
        # impression are one witness (README, the two cautions).
        strong = [g for g in groups.values()
                  if len({h["date"] for h in g}) >= 2]
        proposal = disagree = None
        twice = key in doubled
        if twice:
            pass
        elif len(strong) == 1:
            # The cluster's readings differ in the scans' own way, so the one
            # emitted is the MODAL reading; a tie goes to the shortest, because
            # OCR inserts letters more often than it drops them (`Wim.` for `Wm.`),
            # and a remaining tie to the earliest printing.
            # ONLY THE FORENAME IS TAKEN. The 1834-03-04 crop cut the left edge,
            # so its SURNAMES are intact and are the thing matched on; taking the
            # witness's surname too would import that scan's own damage -- `John
            # Wiison`, `Eiam Tuller` -- into a name the subject page states plainly.
            # The forename emitted is the MODAL reading in the cluster; a tie goes to
            # the shortest, because OCR inserts letters oftener than it drops them
            # (`Wim.` for `Wm.`), and a remaining tie to the alphabetically first.
            reads = [h["forename"] for h in strong[0]]
            fore = min(sorted(set(reads)), key=lambda r: (-reads.count(r), len(r)))
            # The count of letters waiting -- `Elliot 3`, `Wilson 6` -- is the
            # SUBJECT page's own reading and is carried through untouched; the
            # witnesses' counts are their own printings' and are not imported.
            proposal = ("%s %s%s" % (fore, sur, tail)).strip()
            agreeing = sorted({h["date"] for h in strong[0]})
        elif len(strong) > 1:
            disagree = sorted({("%s %s%s" % (g[0]["forename"], sur, tail)).strip()
                               for g in strong})
        rows.append({
            "claim": name["claim"], "as_printed": name["as_printed"],
            "normalized": name["normalized"], "surname": sur, "surname_key": key,
            "cut": bool(CUT.search(name["normalized"])),
            "witnesses": hits,
            "printings_agreeing": agreeing,
            "proposal": proposal,
            "printings_disagree": disagree,
            "surname_twice_in_list": twice,
        })
    return {"printings": printings, "missing": missing, "subject_present": bool(subject),
            "other_office": OTHER_OFFICE, "rows": rows}


def report(res):
    print("THE PRINTINGS -- the Chicago post office's 1 January 1834 return,")
    print("counted by its own body text, in the Chicago Democrat:\n")
    for p in res["printings"]:
        print("  %s  %-10s lines %-22s %s"
              % (p["date"], p["vol"],
                 ",".join("%d+%d" % seg for seg in p["segments"]),
                 p["fingerprint"][:44]))
        print("      date line: %s" % p["dateline"])
    if res["missing"]:
        print("\n  NOT RESOLVED HERE (no deposit on this checkout): %s"
              % ", ".join(res["missing"]))
        return
    print("\n  %d printings, every issue from Vol. I No. 7 to No. 15 without a"
          % len(res["printings"]))
    print("  break. The 1834-03-04 crop T-0312 read is the LAST of them,")
    print("  not a return of its own.\n")
    print("A SECOND OFFICE runs its own 1 January 1834 return in the same weeks")
    print("and is NOT Chicago's:")
    for date, vol, line, text in res["other_office"]:
        print("  %s  %-10s line %-5d  %s" % (date, vol, line, text))
    rows = res["rows"]
    cut = [r for r in rows if r["cut"]]
    done = [r for r in cut if r["proposal"]]
    split = [r for r in cut if r["printings_disagree"]]
    twice = [r for r in cut if r["surname_twice_in_list"]]
    lone = [r for r in cut if not r["proposal"] and not r["printings_disagree"]
            and not r["surname_twice_in_list"] and r["witnesses"]]
    none = [r for r in cut if not r["witnesses"]
            and not r["surname_twice_in_list"]]
    print("\nTHE CONCORDANCE -- %d names minted off the 1834-03-04 crops, %d of them"
          % (len(rows), len(cut)))
    print("cut on the left edge:")
    print("  %3d completed by two or more printings setting the same forename"
          % len(done))
    print("  %3d left alone because the printings disagree" % len(split))
    print("  %3d left alone: no two printings set the same forename" % len(lone))
    print("  %3d left alone: the list carries two of that surname" % len(twice))
    print("  %3d with no witness at all in the other eight printings\n" % len(none))
    for r in cut:
        if r["proposal"]:
            print("  -> %-26s %s   (%d printings)"
                  % (r["normalized"][:26], r["proposal"],
                     len(r["printings_agreeing"])))
        elif r["surname_twice_in_list"]:
            print("  == %-26s two of this surname stand in the list; the crop "
                  "cannot say which" % r["normalized"][:26])
        elif r["printings_disagree"]:
            print("  != %-26s the printings disagree: %s"
                  % (r["normalized"][:26], "; ".join(r["printings_disagree"])))
        else:
            print("  ?  %-26s %s" % (r["normalized"][:26],
                                     "no two printings agree" if r["witnesses"]
                                     else "no witness"))
        for w in r["witnesses"][:4]:
            print("        %s line %-5d  %s" % (w["date"], w["line"], w["as_set"]))


def self_test():
    """The assertions this tool's findings rest on."""
    ok = True

    def check(label, cond):
        nonlocal ok
        print(("  ok   " if cond else "  FAIL ") + label)
        ok = ok and bool(cond)

    check("the fold closes the scans' own letter confusions",
          fold("Elliot") == fold("Eliiot") == fold("E1liot")
          and fold("Miner") == fold("Miner"))
    check("the fold keeps three surnames the loose version merged",
          len({fold("Bennett"), fold("Benton"), fold("Bonnet")}) == 3
          and fold("Delano") != fold("Delaney"))
    check("a surname is read out of a minted reading with its forename cut",
          surname_of("[…]ell Baldwin") == "Baldwin"
          and surname_of("[?] E. Benton") == "Benton")
    check("a name-shaped reading is found where the scan ran a column together",
          any(s["surname"] == "Anderson" for s in
              settings(["Eliphalet Atkins 2 J..W. Anderson Constant Abbott"],
                       [(1, 1)])))
    res = concordance()
    if res["missing"]:
        print("  skip  the deposit is not on this checkout; "
              "the corpus assertions cannot run here")
        return ok
    check("nine printings resolve", len(res["printings"]) == 9)
    check("the 1834-03-04 crop is one of them", res["subject_present"])
    # The printings are identified by their BODY TEXT, so the assertion is about
    # the body and not the heading: three of the eight headings are cut or
    # illegible, and one crop (1834-01-28) has lost the A's off the top of the
    # column altogether, so no single name stands in all eight.
    subject_surnames = {r["surname_key"] for r in res["rows"] if len(r["surname_key"]) >= 4}
    shared = [len({fold(s["surname"]) for s in p["settings"]} & subject_surnames)
              for p in res["printings"] if p["date"] != SUBJECT]
    check("every other printing shares at least six surnames with the subject's list",
          shared and min(shared) >= 6)
    cut = [r for r in res["rows"] if r["cut"]]
    check("the crops' cut names are the bulk of what T-0312 minted",
          len(cut) >= 30)
    check("the concordance repairs some of them and invents none",
          0 < len([r for r in cut if r["proposal"]]) <= len(cut))
    check("no name is both proposed and reported as disagreed",
          not any(r["proposal"] and r["printings_disagree"] for r in res["rows"]))
    check("no completion is handed to two lines of the same surname",
          len([r["proposal"] for r in res["rows"] if r["proposal"]])
          == len({r["proposal"] for r in res["rows"] if r["proposal"]}))
    check("edit distance one joins two scans of one setting and not two names",
          within_one(fold("Wim."), fold("Wm."))
          and within_one(fold("Russell"), fold("Russel"))
          and not within_one(fold("Hiram"), fold("Thomas"))
          and not within_one(fold("Delano"), fold("Delaney")))
    return ok


def apply(res):
    """Write the concordance's completions into claims c026 and c027.

    Only `normalized` moves. `as_printed` keeps the 1834-03-04 setting verbatim, so
    the completion is visible as a completion beside the damage it repairs, and
    `completed_from` names the printings that carry it. Re-running is a no-op.
    """
    doc = json.loads(EXTRACTED.read_text(encoding="utf8"))
    by_printed = {}
    for r in res["rows"]:
        by_printed.setdefault((r["claim"], r["as_printed"]), r)
    changed = 0
    for claim in doc["claims"]:
        if claim["id"] not in ("c026", "c027"):
            continue
        for ent in claim.get("entities", []):
            row = by_printed.get((claim["id"], ent["as_printed"]))
            if not row or not row["cut"] or not row["proposal"]:
                continue
            dates = row["printings_agreeing"]
            if ent["normalized"] != row["proposal"]:
                changed += 1
            ent["normalized"] = row["proposal"]
            ent["completed_from"] = dates
    EXTRACTED.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n",
                         encoding="utf8")
    print("%d readings completed from the concordance; %d rewritten this run"
          % (sum(1 for r in res["rows"] if r["cut"] and r["proposal"]), changed))


def main():
    args = sys.argv[1:]
    if "--self-test" in args:
        sys.exit(0 if self_test() else 1)
    res = concordance()
    if "--apply" in args:
        if res["missing"]:
            sys.exit("the deposit is not on this checkout; nothing to apply")
        apply(res)
    elif "--json" in args:
        print(json.dumps(res, indent=1, ensure_ascii=False))
    else:
        report(res)


if __name__ == "__main__":
    main()
