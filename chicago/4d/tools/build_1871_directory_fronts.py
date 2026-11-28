#!/usr/bin/env python3
"""T-3803: the firms of October 1871 on the shop faces round the jaunt stops, from
Edwards' 1871 directory, placed by the city's own (pre-1909) street numbers.

    python3 tools/build_1871_directory_fronts.py --ocr <edwardsannualdir141871chic_djvu.txt>
    python3 tools/build_1871_directory_fronts.py --check     # the committed file still parses and
                                                             # every face, firm and boundary agrees

Writes data/context/1871/directory_fronts.json. The OCR text is the Internet Archive's
djvu.txt of `edwards_chicago_directory_1871` (archive.org item edwardsannualdir141871chic,
7.7 MB); it is not committed, so the extraction runs where the text is and `--check`
re-reads only what the file itself states (the numbering model, faces, firms).

WHAT IT READS. Two parts of the book. The alphabetical directory (pp. ~68-960) prints a
person or firm, the trade and the business address before any residence ("r."/"h."); the
classified business directory (pp. 977 ff., "a classified list of all trades") prints each
business under its trade heading. A firm at a numbered address on one of the faces below
is kept, with every listing's printed page (read off the OCR's running page numbers, so
+-1) and its line in the djvu text. A clerk's or salesman's line is not a business and
is dropped; an address after "room" is an upstairs office.

THE NUMBERING MODEL (pre-1909: Chicago renumbered the loop in 1911). Read from the
directory itself, and from one photograph (see NUMBERING below for each boundary's
evidence):
  * the Court House square has no street numbers of its own, so on each of its four
    streets one parity is missing for exactly the square's frontage. That gap fixes the
    numbers at Clark and LaSalle on Randolph and Washington, and at Randolph and
    Washington on Clark and LaSalle, and says which side is odd;
  * Carbutt's stereograph "Lake street, East from Clark" (nypl_carbutt_lake_street_east_
    from_clark_stereo) shows painted wall signs numbered 124, 120 and 118 on the first
    buildings east of Clark on the NORTH side; the 1871 directory has Bassett & Hammond,
    hats, caps and furs, at 124 Lake and Cogswell & Co., jewelry, at 120 Lake, which are
    the firms those signs name. Lake is even on the north, unlike Randolph;
  * corner listings ("90, 92 and 94 Lake, cor. Dearborn"; "123 Lake and 35 Clark" with the
    Saloon Building at Lake and Clark; "192 Lake and 20 5th av."), named blocks with a
    number, and Andreas's "nearly midway between State and Dearborn" for Crosby's Opera
    House at 63-69 Washington.
A firm's place along its face is its number's share of the face's span, which assumes
evenly spread numbers: that is an inference, and each firm says so.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "context" / "1871" / "directory_fronts.json"
CONTEXT = ROOT / "data" / "context" / "1871.json"

# ---------------------------------------------------------------------------
# NUMBERING. Numbers at each cross street's centre line. E-W streets count west
# from the lake, N-S streets south from the river. `odd` names the side the odd
# numbers stand on.
NUMBERING = {
    "Lake": {
        "axis": "ew", "odd": "s",
        "at": {"Wabash Avenue": 22, "State Street": 56, "Dearborn Street": 90, "Clark Street": 125,
               "LaSalle Street": 157, "Fifth Avenue": 191},
        "evidence": [
            "Carbutt's 'Lake street, East from Clark' shows wall signs numbered 124 (Bassett & Hammond, hats, caps and furs: 124 Lake in the directory), 120 (watches and jewelry: Cogswell & Co., 120 Lake) and 118 on the first fronts east of Clark on the north side: even north, Clark at about 125",
            "'Norris B. F. & Co. watches and jewelry, 123 Lake, and 35 Clark' and the Saloon Building, 'Lake, cor. Clark' (its janitor at 123 Lake): odd south, 123 at the Clark corner",
            "'VanSchaack, Stevenson & Reid ... 90, 92 and 94 Lake, cor. Dearborn': Dearborn at about 90",
            "'Rockwood & Blocki, drugs, whol. 192 Lake and 20 5th av.': Fifth Avenue at about 191",
            "between those, about 34 numbers a block, the spacing the anchors share; Wabash and State are spaced, not read",
        ],
        "conflicts": ["'Marine Company of Chicago ... 156 Lake' would put an even number on the south side if its office was the Marine Bank building (Lake, se. cor. LaSalle); the photograph and the Saloon Building outweigh it"],
    },
    "Randolph": {
        "axis": "ew", "odd": "n",
        "at": {"Wabash Avenue": 23, "State Street": 57, "Dearborn Street": 91, "Clark Street": 125,
               "LaSalle Street": 161, "Fifth Avenue": 195},
        "evidence": [
            "no even number between 126 and 148 and almost none to 162: the Court House square's frontage on the south side, Clark at about 125 and LaSalle at about 161",
            "odd numbers run through it (143 Randolph, the Fidelity Safe Depository, north side between Clark and LaSalle): odd north",
            "east of Clark the blocks are spaced like Lake's, which shares the original town's lots",
        ],
    },
    "Washington": {
        "axis": "ew", "odd": "n",
        "at": {"Wabash Avenue": 18, "State Street": 49, "Dearborn Street": 83, "Clark Street": 106,
               "LaSalle Street": 148, "Fifth Avenue": 182},
        "evidence": [
            "no odd number between 107 and 147: the Court House square's frontage on the north side, Clark at about 106 and LaSalle at about 148",
            "'Methodist Church blk. room 2, 108 Washington' (Clark, se. cor. Washington): even south, Clark at 106-108",
            "Crosby's Opera House at 63-69 Washington, north side, 'nearly midway between State and Dearborn' (Andreas vol. 2, p. 601): State at about 49 and Dearborn at about 83",
            "even numbers 150-176 under the Commercial Insurance building (160 and 162 Washington, south side between LaSalle and Fifth Avenue)",
        ],
    },
    "Madison": {
        "axis": "ew", "odd": "n",
        "at": {"Wabash Avenue": 22, "State Street": 56, "Dearborn Street": 90, "Clark Street": 125,
               "LaSalle Street": 161, "Fifth Avenue": 195},
        "evidence": [
            "'Farwell Hall, 148 Madison' (south side between Clark and LaSalle) and 'Pope's blk.' at 137-145 (north side between Clark and LaSalle): even south, odd north",
            "'163 Madison, cor. LaSalle': LaSalle at about 161",
            "the gaps in each parity at 90-99 and 116-135 fall at Dearborn and Clark",
        ],
    },
    "Clark Street": {
        "axis": "ns", "odd": "e",
        "at": {"South Water Street": 1, "Lake Street": 34, "Randolph Street": 72, "Washington Street": 99,
               "Madison Street": 129, "Monroe Street": 159},
        "evidence": [
            "no even number between 74 and 98: the Court House square's frontage on the west side, Randolph at about 72 and Washington at about 99",
            "'Hooley's Opera House, 87 and 89 Clark', opposite the square: odd east",
            "'Washington Block, 122 Clark' (west side between Washington and Madison) and 'Morrison Block' (east side between Madison and Monroe) at 131",
            "'Norris B. F. & Co. ... 123 Lake, and 35 Clark' at the Lake corner: Lake at about 34",
        ],
        "conflicts": ["'9 M. E. Church blk. 100 Clark' is even on the east side; the block's own entrance was on Washington (108)"],
    },
    "LaSalle Street": {
        "axis": "ns", "odd": "e",
        "at": {"South Water Street": 1, "Lake Street": 20, "Randolph Street": 57, "Washington Street": 99,
               "Madison Street": 138, "Monroe Street": 175},
        "evidence": [
            "no odd number between 57 and 99: the Court House square's frontage on the east side, Randolph at about 57 and Washington at about 99",
            "'Oriental bldg.' at 122 LaSalle and the Mercantile building at 120 (west side between Washington and Madison): even west",
            "'Lewis, Brooks & Co. ... 134 LaSalle, cor. Madison': Madison at about 138",
        ],
    },
    "Dearborn Street": {
        "axis": "ns", "odd": "e",
        "at": {"South Water Street": 1, "Lake Street": 30, "Randolph Street": 64, "Washington Street": 96,
               "Madison Street": 130, "Monroe Street": 166},
        "evidence": [
            "'Fullerton C. W. room 2, 94 Dearborn' in the Fullerton block (Washington, nw. cor. Dearborn): even west, Washington at about 96",
            "the Tremont House (Lake, se. cor. Dearborn, 180 ft on Dearborn) leaves the odd numbers in the 30s and 40s thin",
            "'Honore Block, 182 Dearborn' (west side between Monroe and Adams): Monroe below 182",
            "Randolph and Madison are spaced between those, not read",
        ],
    },
    "State Street": {
        "axis": "ns", "odd": "e",
        "at": {"South Water Street": 1, "Lake Street": 40, "Randolph Street": 74, "Washington Street": 108,
               "Madison Street": 142, "Monroe Street": 176},
        "evidence": [
            "'Crosby Music Hall, 86 and 88 State' in Crosby's building (west side between Randolph and Washington): even west",
            "even numbers 84-104 thin where Crosby's building fronts the west side; Field, Leiter & Co. (State, ne. cor. Washington) prints no number",
            "Lake, Madison and Monroe are spaced at the 34 numbers a block the other streets share, not read",
        ],
    },
}
# The faces round the jaunt stops (the detail rings), each block both sides.
FACE_RUNS = {
    "Lake": ["Wabash Avenue", "State Street", "Dearborn Street", "Clark Street", "LaSalle Street", "Fifth Avenue"],
    "Randolph": ["Wabash Avenue", "State Street", "Dearborn Street", "Clark Street", "LaSalle Street", "Fifth Avenue"],
    "Washington": ["Wabash Avenue", "State Street", "Dearborn Street", "Clark Street", "LaSalle Street", "Fifth Avenue"],
    "Madison": ["Wabash Avenue", "State Street", "Dearborn Street", "Clark Street", "LaSalle Street", "Fifth Avenue"],
    "Clark Street": ["South Water Street", "Lake Street", "Randolph Street", "Washington Street", "Madison Street", "Monroe Street"],
    "LaSalle Street": ["Lake Street", "Randolph Street", "Washington Street", "Madison Street", "Monroe Street"],
    "Dearborn Street": ["Lake Street", "Randolph Street", "Washington Street", "Madison Street", "Monroe Street"],
    "State Street": ["Lake Street", "Randolph Street", "Washington Street", "Madison Street", "Monroe Street"],
}
STREET_NAME = {"Lake": "Lake Street", "Randolph": "Randolph Street", "Washington": "Washington Street",
               "Madison": "Madison Street"}
# How the directory spells each street after a number.
SPELL = {"Lake": "Lake", "Randolph": "Randolph", "Washington": "Washington", "Madison": "Madison",
         "Clark Street": "Clark", "LaSalle Street": "La ?Salle", "Dearborn Street": "Dearborn", "State Street": "State"}

EMPLOYEE = re.compile(r"\b(clk|clerk|salesman|saleswoman|bkpr|bookkeeper|porter|lab|laborer|teamster|cashier|"
                      r"collector|watchman|janitor|janitress|driver|cook|waiter|bellboy|student|stndent|elk|"
                      r"engineer|foreman|supt|asst|sec|secretary|treas|pres|agt|agent|with|traveling|trav|"
                      r"compositor|printer|cutter|operator|messenger|carrier|apprentice|wks|works|packer|"
                      r"shipping|entry|reporter|editor|draughtsman|draftsman|copyist|ofhce|office)\b\.?", re.I)
UPSTAIRS_TRADE = re.compile(r"\b(lawyer|attorney|real ?est|real estate|insurance|ins\. agt|architect|physician|dentist|"
                            r"surgeon|notary|broker|stenograph|photograph|artist|engraver|lithograph|publisher|"
                            r"music teacher|teacher|dressmkr|dressmaker|civil engineer|patent)\w*", re.I)
ABBREV = [
    (r"\bmer\.? tailors?", "merchant tailors"), (r"\brealestate\b", "real estate"),
    (r"\b(grain|stove|coal|wood|lumber|hide|wine|tea|hat|cigar|fruit|produce)\s?(?:dlrs?\.?|dealers?)", r"\1 dealers"),
    (r"\bwhol\.?", "wholesale"), (r"\bmnfrs?\.?", "manufacturers"), (r"\bmnfr\.?", "manufacturer"),
    (r"\bcom\.? mers?\.?", "commission merchants"), (r"\bmers?\.", "merchants"), (r"\bdlrs?\.?", "dealers"),
    (r"\bgds\.?", "goods"), (r"\bmkrs?\.?", "makers"), (r"\bmkr\b", "maker"), (r"\bmatl\.?", "materials"),
    (r"\bimptrs?\.?", "importers"), (r"\bfurn\.", "furnishing"), (r"\bmfg\.?", "manufacturing"),
    (r"\bdrugs\b", "drugs"), (r"\bagts?\.?", "agents"), (r"\bpropr\.?", "proprietor"), (r"\bsupt\.?", "superintendent"),
    (r"watchmkr", "watchmaker"), (r"shoemkr", "shoemaker"), (r"hatmkr", "hatmaker"), (r"jewlr", "jeweler"),
]


def norm(s):
    return re.sub(r"\s+", " ", s).strip()


def page_index(lines):
    """Running page numbers, OCR'd as lone numbers on a line. A number is a page when the
    next one or two pages follow within a few hundred lines; the rest are ad copy."""
    cand = [(i, int(l.strip())) for i, l in enumerate(lines) if re.fullmatch(r"\s*\d{2,4}\s*", l)]
    pages = []
    last = 0
    for k, (i, n) in enumerate(cand):
        if n <= last or n > last + 12 and last:
            continue
        ok = any(cand[j][1] in (n + 1, n + 2) and cand[j][0] - i < 1600 for j in range(k + 1, min(k + 8, len(cand))))
        if ok:
            pages.append((i, n)); last = n
    out = [0] * len(lines)
    p, k = 0, 0
    for i in range(len(lines)):
        while k < len(pages) and pages[k][0] <= i:
            p = pages[k][1]; k += 1
        out[i] = p
    return out


def entries(lines, a, b):
    """Join an entry's wrapped lines: a continuation starts lower case, with a digit or
    punctuation, or follows a hyphen."""
    cur = None
    for i in range(a, b):
        s = lines[i].strip()
        if not s or re.fullmatch(r"\d{1,4}", s):
            continue
        cont = bool(re.match(r"[a-z0-9(.,\-&;:']", s)) or s.startswith("av.") or (cur and cur[1].endswith("-"))
        if cur and cont:
            cur[1] = cur[1].rstrip("-") + ("" if cur[1].endswith("-") else " ") + s
        else:
            if cur:
                yield cur
            cur = [i, s]
    if cur:
        yield cur


def addr_re():
    streets = "|".join(f"(?P<s{k}>{v})" for k, v in enumerate(SPELL.values()))
    num = r"(?P<num>\d{1,3}(?:(?:\s*,\s*\d{1,3})*\s*(?:and|&|to)\s*\d{1,3})?)"
    return re.compile(r"(?<![\w.])" + num + r"\s+(?:" + streets + r")\b(?!\s*(?:av|pl|ct)\b)")


STREET_KEYS = list(SPELL.keys())


def find_addrs(text):
    rx = addr_re()
    for m in rx.finditer(text):
        pre = text[max(0, m.start() - 4):m.start()]
        if re.search(r"\b[WNS]\.\s*$", pre):
            continue
        key = next(STREET_KEYS[k] for k in range(len(STREET_KEYS)) if m.group(f"s{k}"))
        nums = sorted(int(x) for x in re.findall(r"\d{1,3}", m.group("num")))
        if nums[-1] - nums[0] > 8:
            continue
        yield m, key, nums


GIVEN = set()


def given_names(lines, start, end):
    """Words the alphabetical list prints second ("Smith Peter, ...") a dozen times or more."""
    seen = Counter()
    for i in range(start, end):
        m = re.match(r"\s*[A-Z][a-z'\-]+\s+([A-Z][a-z]+)\b", lines[i])
        if m:
            seen[m.group(1).lower()] += 1
    return {w for w, n in seen.items() if n >= 12} - {"brothers", "bros", "sons", "company", "co"}


def pretty_name(raw):
    """The name as a sign painter would letter it: a firm as printed, a person's
    'Surname Given' turned round."""
    s = norm(raw).strip(" ,.;:*")
    s = re.sub(r"\s*\((?:[^)]*)\)\s*", " ", s).strip()
    s = s.replace(" ,", ",").replace("&.", "&").replace("<fc", "&").replace(" Jt ", " & ").replace("<t", "&")
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\bMcl(?=[a-z])", "McI", s)  # the OCR reads McI as Mcl
    s = re.sub(r"^[A-Z] (?=[A-Z][a-z])", "", s)  # a margin mark read as a letter
    s = re.sub(r"(?<= )([A-Z])$", r"\1.", s)  # the closing initial's period, stripped above
    # An OCR'd period after a whole surname in a partnership is the printed comma.
    s = re.sub(r"\b([A-Z][a-z]{3,})\. (?=[A-Z][a-z]+(?:,| &))", lambda m: m.group(1) + ", "
               if m.group(1) not in ("Chas", "Thos", "Jas", "Jno", "Geo", "Wm") else m.group(0), s)
    firm = bool(re.search(r"&|\bCo\b|\bCO\b|Bros|BROS|Company|COMPANY|Sons|SONS|Brothers", s))
    if firm:
        pair = re.fullmatch(r"([A-Z][a-z'\-]+) ((?:[A-Z]\. ?)+)& ((?:[A-Z]\. ?)+)", s)
        if pair:  # "Cherry C. & J." is C. & J. Cherry
            return f"{pair.group(2).strip()} & {pair.group(3).strip()} {pair.group(1)}"
        return s.rstrip(".") + ("." if re.search(r"\bCo$|\b[A-Z]$", s.rstrip(".")) else "")
    parts = s.split(" ")
    # Only a person is printed surname first: every word after it an initial, a title or a
    # given name the directory prints in that place often ("Great Union Band" stays as it is).
    person = all(re.fullmatch(r"[A-Z]\.?|Miss|Mrs\.?|Jr\.?|Sr\.?|Chas\.|Wm\.|Geo\.|Jas\.|Thos\.|Jno\.", w)
                 or w.lower() in GIVEN for w in parts[1:]) \
        or (2 <= len(parts) <= 4 and re.fullmatch(r"[A-Z]\.", parts[-1]) is not None)
    if len(parts) >= 2 and person and re.fullmatch(r"[A-Z][A-Za-z'\-]+", parts[0]):
        given = " ".join(parts[1:])
        title = re.search(r"\b(Miss|Mrs)\.?(?=\s|$)", given)
        if title:
            given = (title.group(1) + (". " if title.group(1) == "Mrs" else " ")
                     + re.sub(r"\s*\b(Miss|Mrs)\.?(?=\s|$)", "", given)).strip()
        return re.sub(r"\b([A-Z])\b(?!\.)", r"\1.", f"{given} {parts[0]}".replace("  ", " "))
    return s


def plausible(name, vocab):
    """OCR sense check: every capitalised word of the name occurs at least twice in the book."""
    words = re.findall(r"[A-Za-z][A-Za-z'\-]{2,}", name)
    if not words:
        return False
    for w in words:
        if w.lower() in ("and", "the", "co", "bros", "brothers", "sons", "company"):
            continue
        if vocab.get(w.lower(), 0) < 2:
            return False
        if re.search(r"[^A-Za-z'\-]", w) or re.search(r"(.)\1\1", w):
            return False
    return not re.search(r"[0-9^<>{}|\\~«»■•_=]", name)


def trade_text(t):
    t = norm(t).strip(" ,.;")
    for a, b in ABBREV:
        t = re.sub(a, b, t, flags=re.I)
    t = re.sub(r"\s+", " ", t).strip(" ,.;")
    return t


def heading_like(h):
    """A trade heading is Title Case words (and, of, the): never a block, a room or a firm."""
    if re.search(r"\b(blk|bldg|block|room|rooms|agt|agts|av|Bros|BROS|Co)\b|&|[A-Z]{2}", h):
        return False
    words = re.findall(r"[A-Za-z']+", h)
    return 0 < len(words) <= 7 and all(w[0].isupper() or w in ("and", "of", "the", "for", "in") for w in words)


def classified(lines, start, pages):
    """The classified directory: (heading, name, address text, line, page) per business."""
    out = []
    heading = None
    pending = None
    for i in range(start, len(lines)):
        s = lines[i].strip()
        if not s or re.fullmatch(r"\d{1,4}", s) or re.fullmatch(r"[A-Z]{3}", s):
            continue
        h = re.fullmatch(r"\*?\s*([A-Z][A-Za-z'’ ,&\-]{3,60}?)\.\s*", s)
        if h and re.search(r"[a-z]", h.group(1)) and not re.search(r"\d", s) and heading_like(h.group(1)):
            heading = h.group(1).strip()
            pending = None
            continue
        q = re.fullmatch(r"\((Wholesale|Retail|Manufacturers|Importers|Jobbers)\.?\)\s*", s)
        if q and heading:
            heading = f"{heading} ({q.group(1).lower()})"
            continue
        if re.search(r"\d", s):
            text = s if not pending else pending[1] + " " + s
            ln = i if not pending else pending[0]
            pending = None
            out.append((heading, text, ln, pages[ln]))
        elif re.fullmatch(r"[A-Z0-9 .,&'\-]+", s) and len(s) > 3:
            pending = (i, s)
    return out


def fit_streets(ctx):
    """Each named street as a straight line through its core segments."""
    agg = defaultdict(list)
    for s in ctx["streets"]:
        n = s.get("name")
        if not n:
            continue
        mx, my = (s["a"][0] + s["b"][0]) / 2, (s["a"][1] + s["b"][1]) / 2
        if not (150 < mx < 1150 and -850 < my < 150):
            continue
        agg[n].append(s)
    fits = {}
    for n, segs in agg.items():
        pts = [p for s in segs for p in (s["a"], s["b"])]
        ew = sum(abs(s["a"][0] - s["b"][0]) for s in segs) > sum(abs(s["a"][1] - s["b"][1]) for s in segs)
        xs = [p[0] for p in pts] if ew else [p[1] for p in pts]
        ys = [p[1] for p in pts] if ew else [p[0] for p in pts]
        mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
        sxx = sum((x - mx) ** 2 for x in xs) or 1
        slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
        fits[n] = {"ew": ew, "m": slope, "c": my - slope * mx, "w": segs[0]["width_m"], "walk": segs[0].get("walk_m", 3)}
    return fits


def cross(f1, f2):
    """Intersection of two fitted streets (one ew, one ns)."""
    ew, ns = (f1, f2) if f1["ew"] else (f2, f1)
    # ew: n = m1 e + c1 ; ns: e = m2 n + c2
    m1, c1, m2, c2 = ew["m"], ew["c"], ns["m"], ns["c"]
    n = (m1 * c2 + c1) / (1 - m1 * m2)
    e = m2 * n + c2
    return [round(e, 2), round(n, 2)]


def build_faces(ctx):
    fits = fit_streets(ctx)
    faces = []
    for key, run in FACE_RUNS.items():
        street = STREET_NAME.get(key, key)
        model = NUMBERING[key]
        for x0, x1 in zip(run, run[1:]):
            a, b = cross(fits[street], fits[x0]), cross(fits[street], fits[x1])
            lo, hi = model["at"][x0], model["at"][x1]
            # Sides: an E-W street's n/s, a N-S street's e/w.
            sides = ("n", "s") if model["axis"] == "ew" else ("e", "w")
            for side in sides:
                parity = "odd" if side == model["odd"] else "even"
                fid = f"{key.split()[0].lower()}_{side}_{x0.split()[0].lower()}_{x1.split()[0].lower()}"
                faces.append({
                    "id": fid, "street": street, "directory_street": key, "side": side,
                    "between": [x0, x1], "numbers": [lo, hi], "parity": parity,
                    "a": a, "b": b, "half_m": round(fits[street]["w"] / 2 + fits[street]["walk"], 2),
                    "cross_half_m": [round(fits[x0]["w"] / 2 + fits[x0]["walk"], 2), round(fits[x1]["w"] / 2 + fits[x1]["walk"], 2)],
                })
    return faces


def face_for(faces, key, num):
    par = "odd" if num % 2 else "even"
    for f in faces:
        lo, hi = f["numbers"]
        if f["directory_street"] == key and f["parity"] == par and lo <= num < hi:
            return f
    return None


def extract(ocr):
    raw = Path(ocr).read_text(encoding="utf-8", errors="replace")
    lines = [re.sub(r"[ \t]+", " ", l) for l in raw.split("\n")]
    pages = page_index(lines)
    vocab = Counter(w.lower() for w in re.findall(r"[A-Za-z][A-Za-z'\-]{2,}", raw))
    cls_start = next(i for i, l in enumerate(lines) if "Classified List of all Trades" in l)
    ctx = json.loads(CONTEXT.read_text())
    faces = build_faces(ctx)
    firms = {}
    street_trades = defaultdict(Counter)

    def good_trade(t):
        if not t:
            return None
        t = re.sub(r"\s*\((wholesale|retail|manufacturers|importers|jobbers)\)", lambda m: "", t, flags=re.I) \
            if re.search(r"wholesale", t, re.I) and t.lower().count("wholesale") > 1 else t
        t = re.sub(r"^(and|&)\s+", "", t.strip())
        words = re.findall(r"[A-Za-z][A-Za-z'\-]*", t)
        if not words or re.search(r"[0-9^<>{}|\\~«»■•_=:;!?€]", re.sub(r"\((wholesale|retail|manufacturers|importers|jobbers)\)", "", t)) or len(t) > 48:
            return None
        if re.search(r"[()]", re.sub(r"\((wholesale|retail|manufacturers|importers|jobbers)\)", "", t)):
            return None
        lower = t[0].islower()
        if lower and "." in t:
            return None
        if lower and re.search(r"[A-Z]", t):
            return None
        if not lower and not heading_like(re.sub(r"\s*\(.*?\)", "", t)):
            return None
        if any(len(w) > 2 and vocab.get(w.lower(), 0) < 3 for w in words):
            return None
        return t

    def add(key, nums, name, trade, section, line, page, text, upstairs):
        num = nums[0]
        f = face_for(faces, key, num)
        if not f:
            return
        raw = norm(name).strip(" ,.;:*")
        if re.search(r",|\b(agt|agts|office|propr|proprs|line|depot|room|cor|and)\b\.?$|\bagt\b|\boffice\b|\bpropr", raw, re.I):
            return
        if re.fullmatch(r"[A-Z0-9 .&'\-]+", raw) and re.search(r"[A-Z]{3}", raw):
            raw = re.sub(r"[A-Z][A-Z']+", lambda m: m.group(0).capitalize(), raw)
        # Lower-case words other than particles are a trade run into the name, or OCR.
        if any(w not in ("and", "of", "the", "jr", "sr") for w in re.findall(r"\b[a-z][a-z']*\b", raw)):
            return
        sign = pretty_name(raw)
        m = re.fullmatch(r"([A-Z][a-z'\-]+) ((?:[A-Z][a-z]+ )?(?:(?:[A-Z]\.|Chas\.|Wm\.|Geo\.|Jas\.|Thos\.|Jno\.|Th\.) ?)*)(& .*)", sign)
        if m and m.group(2).strip() and all(w.lower() in GIVEN for w in re.findall(r"[A-Z][a-z]{2,}", m.group(2))):
            sign = f"{m.group(2).strip()} {m.group(1)} {m.group(3)}"
        if sign.endswith("&") or re.search(r"&\S|[^A-Za-z .,&'\-]", sign) or len(sign) > 30:
            return
        if not plausible(sign, vocab) or len(sign) < 4 or re.search(r"\b(The|Pany|Clark|Lake|State)$|^(The|And)\b", sign):
            return
        if any(vocab.get(w.lower(), 0) < 4 for w in re.findall(r"[A-Za-z']{3,}", sign) if w.lower() not in ("bros", "sons")):
            return
        if any(len(w) == 2 and w not in ("Co", "Jr", "Sr", "De", "Du", "Le", "La", "Mc") for w in re.findall(r"\b[A-Za-z]{2}\b", sign)):
            return
        # A firm is merged across the two lists only under the same name: one surname at one
        # number is often several people and a partnership, each listed apart.
        who = " ".join(re.findall(r"[a-z']+", sign.lower()))
        if not who:
            return
        key_id = f"{f['id']}|{num}|{who}"
        r = firms.get(key_id)
        street = SPELL[key].replace(" ?", "")
        if not r:
            r = firms[key_id] = {"name": sign, "trade": None, "numbers": sorted(set(nums)), "face": f["id"],
                                 "address": f"{' and '.join(str(n) for n in sorted(set(nums)))} {street}",
                                 "floor": "upstairs" if upstairs else "street", "listings": [], "_trades": {}}
        t = good_trade(trade)
        if t:
            r["_trades"][section] = t
        if not upstairs:
            r["floor"] = "street"
        if not any(x["section"] == section for x in r["listings"]):
            r["listings"].append({"section": section, "page": page, "line": line + 1, "text": norm(text)[:110]})

    # The alphabetical directory.
    alpha_start = next(i for i, l in enumerate(lines) if i > 9000 and pages[i] >= 60)
    GIVEN.update(given_names(lines, alpha_start, cls_start))
    for i, text in entries(lines, alpha_start, cls_start):
        t = norm(text)
        bus = re.split(r",?\s+(?:r|h|bds|res)\.\s", t)[0]
        found = list(find_addrs(bus))
        first = found[0][0].start() if found else 0
        for m, key, nums in found:
            head = bus[:first].rstrip(" ,.")
            # name, then the trade after the first comma (or after the initials' last period)
            parts = [p.strip() for p in re.split(r",", head) if p.strip()]
            if not parts:
                continue
            name = parts[0]
            trade = ", ".join(parts[1:])
            if not trade:
                mm = re.match(r"(.+?(?:\b[A-Z]\.|&\s*Co\.|Bros\.))\s+([a-z].*)$", name)
                if mm:
                    name, trade = mm.group(1), mm.group(2)
            if trade and EMPLOYEE.search(trade.split(" ")[0]):
                continue
            if not trade and not re.search(r"&|\bCo\b|Bros", name):
                continue
            upstairs = bool(re.search(r"\b(room|rooms|up stairs)\b", bus[max(0, m.start() - 18):m.start()], re.I)) \
                or bool(UPSTAIRS_TRADE.search(trade or ""))
            add(key, nums, name, trade_text(trade) if trade else None, "alphabetical", i, pages[i], t, upstairs)
    # The classified business directory.
    for heading, text, line, page in classified(lines, cls_start, pages):
        if not heading:
            continue
        for m, key, nums in find_addrs(text):
            name = text[:m.start()].rstrip(" ,.")
            name = re.sub(r",?\s*(room|rooms)\s*[\d\s,and]*$", "", name, flags=re.I).rstrip(" ,.")
            if not name or len(name) > 60:
                continue
            upstairs = bool(re.search(r"\b(room|rooms)\b", text[:m.start()], re.I)) or bool(UPSTAIRS_TRADE.search(heading))
            f = face_for(faces, key, nums[0])
            if f:
                street_trades[f["street"]][heading.split(" (")[0]] += 1
            add(key, nums, name, heading, "classified", line, page, text, upstairs)
    # One firm a number at street level, the best-attested; upstairs offices kept beside it.
    byface = {f["id"]: f for f in faces}
    RETAIL = re.compile(r"hat|cap|fur|boot|shoe|cloth|dry goods|jewel|watch|drug|hardware|book|station|music|"
                        r"piano|confection|cigar|tobacco|grocer|tea|millin|furnish|carpet|crockery|glass|china|"
                        r"gun|saddl|trunk|tailor|fancy|toys|notion|gas fixture|stove|lamp|bank|restaurant|saloon|"
                        r"photograph|picture|frame|optic|perfum|cutlery|silver|clock|furniture|wine|liquor", re.I)
    def score(r):
        t = r["trade"] or ""
        return (len(r["listings"]) * 3 + (2 if r["trade"] else 0) + (2 if RETAIL.search(t) else 0)
                + (1 if re.search(r"&|Co\.|Bros", r["name"]) else 0) - (3 if r["floor"] == "upstairs" else 0))
    groups = defaultdict(list)
    for r in firms.values():
        r["trade"] = r["_trades"].get("alphabetical") or r["_trades"].get("classified")
        cls = r["_trades"].get("classified")
        if cls and r["trade"] != cls and len(cls) <= 40:
            r["heading"] = cls
        del r["_trades"]
        groups[(r["face"], r["numbers"][0])].append(r)
    out = []
    for (face, num), rs in groups.items():
        rs.sort(key=score, reverse=True)
        street = [r for r in rs if r["floor"] == "street" and (r["trade"] or re.search(r"&|Co\.|Bros", r["name"]))][:1]
        up = [r for r in rs if r["floor"] == "upstairs" and r["trade"]][:1]
        out.extend(street + up)
    # A firm listed at two numbers of one face is lettered once, at its best-attested number.
    best = {}
    for r in sorted(out, key=score, reverse=True):
        best.setdefault((r["face"], r["name"]), r)
    out = [r for r in out if best[(r["face"], r["name"])] is r]
    for r in out:
        f = byface[r["face"]]
        lo, hi = f["numbers"]
        r["along"] = round((r["numbers"][0] + (r["numbers"][-1] - r["numbers"][0]) / 2 - lo) / max(1, hi - lo), 3)
        r["id"] = re.sub(r"[^a-z0-9]+", "_", r["name"].lower()).strip("_")[:36] + f"_{r['numbers'][0]}_{f['directory_street'].split()[0].lower()}"
        r["listings"].sort(key=lambda x: x["section"])
    seen = Counter()
    for r in out:
        seen[r["id"]] += 1
        if seen[r["id"]] > 1:
            r["id"] += f"_{seen[r['id']]}"
    out.sort(key=lambda r: (r["face"], r["numbers"][0], r["floor"]))
    out = [{k: r[k] for k in ("id", "face", "name", "trade", "heading", "address", "numbers", "floor", "along", "listings") if k in r}
           for r in out]
    NOT_A_SHOP = re.compile(r"Inspectors|Consuls|Wholesale Dealers|Companies|Offices|Agents|Brokers|Publications|"
                            r"Justices|Builders|Manufacturers|Printed|Engineers", re.I)
    trades = {k: [t for t, _ in v.most_common(60) if good_trade(t) and not UPSTAIRS_TRADE.search(t)
                  and not NOT_A_SHOP.search(t)][:16] for k, v in sorted(street_trades.items())}
    return faces, out, trades


DOC = ("T-3803. The firms Edwards' 1871 directory lists at numbered addresses on the shop faces round the 1871 jaunt "
       "stops, the pre-1909 street numbering that places them, and the faces themselves. Written by "
       "tools/build_1871_directory_fronts.py from the directory's OCR text; renderers/web/js/city-signs-1871.js "
       "letters each front in the detail rings with the firm whose number falls on it, or, where none does, a trade "
       "of that street from the classified directory. GRADES: a firm at its listed address is ATTESTED (the "
       "listing: page and line given); the face it stands on is INFERRED from the numbering model (each boundary's "
       "evidence below); its place along the face is INFERRED as its number's share of the face's span, which "
       "assumes evenly spread numbers; the front it is painted on is a generated front (L-1871-city-baseline), and "
       "the sign's form, colours, lettering and the words beyond the listing are RECONSTRUCTED "
       "(docs/LIBERTIES.md L-1871-directory-signs). Listing pages are the book's printed page numbers as the OCR "
       "carries them, +-1; `line` is the line in the archive.org djvu text. Names are as the OCR reads them; a name "
       "with a word the book prints only once is left out as a likely misreading.")


def write(ocr):
    faces, firms, trades = extract(ocr)
    doc = {
        "_doc": DOC,
        "schema": "chicago-1871-directory-fronts-v1",
        "ticket": "T-3803",
        "scene": "1871",
        "source_id": "edwards_chicago_directory_1871",
        "photo_source_id": "nypl_carbutt_lake_street_east_from_clark_stereo",
        "text": "archive.org edwardsannualdir141871chic, edwardsannualdir141871chic_djvu.txt",
        "liberty": "L-1871-directory-signs",
        "grades": {"listing": "attested", "face": "inferred", "position": "inferred", "sign": "reconstructed"},
        "numbering": {
            "rule": "Pre-1909 (old) numbers: east-west streets count west from the lake, north-south streets south from the river; one parity a side. 'at' is the number at each cross street's centre line, read or spaced as each street's evidence says.",
            "streets": NUMBERING,
        },
        "faces": faces,
        "street_trades": trades,
        "firms": firms,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=None, ensure_ascii=False, separators=(",", ":")).replace('{"id"', '\n{"id"') + "\n")
    c = Counter(f["face"] for f in firms)
    print(f"wrote {OUT.relative_to(ROOT)}: {len(firms)} firms on {len(c)} of {len(faces)} faces "
          f"({sum(1 for f in firms if f['floor'] == 'street')} at street level)")


def check():
    doc = json.loads(OUT.read_text())
    errs = []
    faces = {f["id"]: f for f in doc["faces"]}
    if doc.get("source_id") != "edwards_chicago_directory_1871":
        errs.append("source_id")
    for sid in (doc["source_id"], doc["photo_source_id"]):
        if not (ROOT / "data" / "sources" / f"{sid}.json").exists():
            errs.append(f"source {sid} does not resolve")
    for key, m in doc["numbering"]["streets"].items():
        vals = list(m["at"].values())
        if vals != sorted(vals):
            errs.append(f"{key}: numbers do not rise along the street")
        if not m.get("evidence"):
            errs.append(f"{key}: a boundary without evidence")
    for r in doc["firms"]:
        f = faces.get(r["face"])
        if not f:
            errs.append(f"{r['id']}: no face {r['face']}"); continue
        lo, hi = f["numbers"]
        n = r["numbers"][0]
        if not (lo <= n < hi) or (n % 2 == 1) != (f["parity"] == "odd"):
            errs.append(f"{r['id']}: {n} is not on {f['id']}")
        if not r["listings"] or not all(x.get("line") and x.get("section") for x in r["listings"]):
            errs.append(f"{r['id']}: no locator")
        if not (0 <= r["along"] <= 1):
            errs.append(f"{r['id']}: along {r['along']}")
        # Every word of the sign's name is in every listing it cites (the name is the
        # listing's, reordered, never a merge of two people's names).
        words = [w.lower() for w in re.findall(r"[A-Za-z']+", r["name"]) if len(w) > 1]
        for x in r["listings"]:
            said = " " + " ".join(re.findall(r"[a-z']+", x["text"].lower())) + " "
            if any(f" {w} " not in said for w in words):
                errs.append(f"{r['id']}: name not in its listing on p. {x['page']}")
    if errs:
        print("DIRECTORY FRONTS FAIL —", "; ".join(errs[:12]))
        return 1
    print(f"DIRECTORY FRONTS PASS — {len(doc['firms'])} firms on {len(faces)} faces, every one on its face's "
          f"parity and span, named as its listings name it, every listing located")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--ocr")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.check:
        sys.exit(check())
    if not a.ocr:
        ap.error("--ocr <djvu.txt> or --check")
    write(a.ocr)
    sys.exit(check())
