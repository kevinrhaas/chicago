#!/usr/bin/env python3
"""T-3266: who lived in each 1904 Prairie Avenue house BEFORE 1 July 1904 — and, for a
house nobody is listed in on that day, who came after.

The owner, 2026-10-30, of 1808 Prairie: "you should have in there as former residents
the name of the people whose house it was like you call it the keith house". The 1904
cards (data/residents_1904/households/) seat only the household the 1904 Blue Book
lists, so the house the model calls the Keith house showed the Fields and nobody else,
and a house the register skips (1811, 1827) showed nobody at all.

Reads three things already in the repository:

  docs/RESEARCH/prairie-former-residents-3266/blue_book_prairie_readings.tsv
      every Prairie Avenue 1600-2140 reading of the Blue Book's street list and its
      alphabetical list, 16 editions 1890-1910 (read_blue_books.py beside it);
  docs/RESEARCH/prairie-households-1900-census-3258/census_1900_prairie_reading.tsv
      the heads of household the 1900 census enumerated at each number (T-3258);
  NAMESAKES below: the Prairie Avenue Historic District markers' name lines ("Osborn R.
      Keith Residence. Built 1886"), already transcribed into data/sources/hmdb_*.

and writes data/residents_1904/former_residents.json, which compile_scene.py carries
into data/sidecars/1904/people.json as `former_residents`, keyed by structure id.

WITNESS RULE. The Blue Book readings are the Internet Archive's OCR, not the page, so a
household is kept only where the book's two lists agree: its surname appears in the
ALPHABETICAL list at that number, and either the street list prints it too or the
alphabetical list does in a second edition. An OCR fragment ("ling", "saulus" from a
neighbouring column) or a number misread in one list does not meet it. A kept household
is graded `attested` (owner ruling 2026-10-30: a directory listing that puts a named
household at an address is attested).

A former residence is not a fact about 1904, and the card says so: each entry carries
the editions it was read in, never "lived here on the scene date".

    python3 tools/build_former_residents_1904.py           # write
    python3 tools/build_former_residents_1904.py --check   # fail if the file is stale
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
READINGS = ROOT / "docs/RESEARCH/prairie-former-residents-3266/blue_book_prairie_readings.tsv"
CENSUS = ROOT / "docs/RESEARCH/prairie-households-1900-census-3258/census_1900_prairie_reading.tsv"
HOUSEHOLDS = DATA / "residents_1904/households"
OUT = DATA / "residents_1904/former_residents.json"

SCENE_EDITION = 1904          # the edition canvassed from September 1903
LATER_EDITION = 1905          # canvassed from September 1904: the later bracket
EDITIONS_READ = [1890, 1891, 1892, 1893, 1894, 1895, 1897, 1898, 1899, 1901, 1902, 1903,
                 1904, 1905, 1907, 1908, 1909, 1910]

#: The district markers' name lines: the family each house is named for. Number →
#: (name, source id, the line as the marker prints it).
NAMESAKES = {
    1612: ("Joseph Goodman", "hmdb_prairie_lost_houses_1600_1700", "Joseph Goodman Residence. Built 1869"),
    1638: ("John G. Shortall", "hmdb_prairie_lost_houses_1600_1700", "John G. Shortall-Robert B. Gregory Residence. Built 1868"),
    1701: ("William G. Hibbard", "hmdb_prairie_lost_houses_1600_1700", "William G. Hibbard Residence. Built 1869"),
    1721: ("Wirt Dexter", "hmdb_prairie_lost_houses_1600_1700", "Wirt Dexter Residence. Built 1863"),
    1729: ("George M. Pullman", "hmdb_prairie_lost_houses_1600_1700", "George M. Pullman Residence. Built 1870-1876"),
    1800: ("John Glessner", "hmdb_prairie_heritage_preserved", "John Glessner Residence. Built 1887"),
    1801: ("William W. Kimball", "hmdb_prairie_heritage_preserved", "William W. Kimball Residence. Built 1890"),
    1808: ("Osborn R. Keith", "hmdb_prairie_lost_houses_1800_1900_west", "Osborn R. Keith Residence. Built 1886"),
    1811: ("Joseph G. Coleman", "hmdb_prairie_heritage_preserved", "Joseph G. Coleman Residence. Built 1886"),
    1812: ("George H. Wheeler", "hmdb_prairie_lost_houses_1800_1900_west", "George H. Wheeler Residence. Built 1884"),
    1815: ("Joseph Sears", "hmdb_prairie_lost_houses_1800_1900_east", "The home was built by Joseph Sears, the founder of the Chicago suburb of Kenilworth."),
    1824: ("Samuel B. Pomeroy", "hmdb_prairie_lost_houses_1800_1900_west", "Samuel B. Pomeroy Residence. Built 1857"),
    1834: ("Fernando Jones", "hmdb_prairie_lost_houses_1800_1900_west", "Fernando Jones Residence. Built 1866"),
    1900: ("Elbridge G. Keith", "hmdb_prairie_heritage_preserved", "Elbridge G. Keith Residence. Built 1870"),
    1912: ("Byran P. Moulton", "hmdb_prairie_lost_houses_1800_1900_west", "Byran P. Moulton Residence. Built 1882"),
    1919: ("Marshall Field Jr.", "hmdb_prairie_heritage_preserved", "Marshall Field Jr. Residence. Built 1867"),
    2009: ("Max A. Meyer", "hmdb_prairie_lost_houses_2000_2100", "Max A Meyer Residence. Built 1888"),
    2100: ("John B. Sherman", "hmdb_prairie_lost_houses_2000_2100", "John B. Sherman Residence. Built 1874"),
    2115: ("David Kelley", "hmdb_prairie_lost_houses_2000_2100", "David Kelley-Philip D. Armour Residence. Built 1871"),
    2140: ("William F. Tucker", "hmdb_prairie_lost_houses_2000_2100", "William F. Tucker-Byron L. Smith Residence. Built 1876"),
}

#: What a reading of a page image or another list adds to an empty house's note.
EMPTY_NOTES = {
    1811: ("David Mayer is listed at 1811 through the 1903 edition; the 1904 edition's "
           "alphabetical list prints him at 4706 Woodlawn av., so the family had left by "
           "the autumn of 1903."),
    1827: ("The 1900 census taker walked from 1823 straight to 1905 and enumerated nobody "
           "at 1827 (ED 40, sheet 4A, leaf n800), so the house looks to have stood empty "
           "after the Doanes."),
}

TITLES = ("Mr. & Mrs.", "Mr.& Mrs.", "Mrs.", "Mr.", "Miss", "Dr.", "Rev.", "Capt.", "Prof.")


def norm(s: str) -> str:
    return re.sub(r"[^a-z]", "", s.lower())


def street_surname(t: str) -> str:
    t = re.sub(r"\s*(&\s*(dr|drs|son|sons)\b\.?|\bjr\b\.?|\bir\b\.|\bsr\b\.?|,).*$", "", t).strip()
    words = re.sub(r"[^A-Za-z'\- ]", " ", t).split()
    return words[-1] if words else ""


def alpha_parts(t: str) -> tuple[str, str] | None:
    """'Keith Alice Miss' → ('Keith', 'Miss Alice Keith'). None for a line that is not in
    the alphabetical list's surname-first form ('Wm. G. Hibbard, 1701 Prairie av.' is a
    club roll's line the OCR read as one)."""
    words = t.replace(",", " ").split()
    if not words or words[0].endswith(".") or len(words[0]) < 2:
        return None
    sur, rest = words[0].strip(".'"), words[1:]
    suffix = ""
    for i, w in enumerate(rest):
        if w.rstrip(".") in ("jr", "sr"):
            suffix = rest.pop(i).rstrip(".") + "."
            break
    title = ""
    if rest and rest[-1].rstrip(".") in ("Mrs", "Miss", "Mr", "Dr", "Rev", "Capt", "Prof"):
        title = rest.pop().rstrip(".")
        title = title if title == "Miss" else title + "."
    given = " ".join(rest).strip()
    given = re.sub(r"\b([A-Z])\b(?!\.)", r"\1.", given)      # 'O. R' → 'O. R.'
    name = " ".join(p for p in (title, given, sur, suffix) if p)
    return sur, name


def load_readings():
    rows = []
    for line in READINGS.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        y, n, kind, t = line.split("\t", 3)
        rows.append((int(y), int(n), kind, t))
    return rows


def load_census():
    heads = defaultdict(list)
    for line in CENSUS.read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or not line.strip():
            continue
        f = line.split("\t")
        f += [""] * (14 - len(f))
        leaf, ed, sheet, ln, house, name, rel = f[:7]
        if rel != "Head" or not house.isdigit():
            continue
        surname, _, given = name.partition(",")
        given = re.sub(r"\b(Mr|Mrs)\.\s*$", "", given).strip()
        heads[int(house)].append({
            "surname": surname.strip(), "name": f"{given} {surname.strip()}".strip(),
            "locator": f"ED {ed}, sheet {sheet}, line {ln}, leaf n{leaf}", "as_enumerated": name,
            "note": f[13].strip(),
        })
    return heads


def structures_by_number() -> dict[int, str]:
    """The house at each number in the 1904 scene: a household card's own home where one
    is seated, otherwise the number's house record (outbuildings and the station left out)."""
    out: dict[int, str] = {}
    for p in sorted(HOUSEHOLDS.glob("hh_*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        n = int(re.search(r"at (\d{4})", d["name"]).group(1))
        out[n] = d["associated_with"][0]["place_or_structure_id"]
    skip = re.compile(r"coach_house|ranges|conservatory|alley_building|rear_building|shed_|station|house_1918_")
    for p in sorted((DATA / "structures").glob("*_prairie*.json")):
        m = re.search(r"_(1[6-9]\d\d|2[01]\d\d)_prairie(_front)?$", p.stem)
        if m and not skip.search(p.stem):
            out.setdefault(int(m.group(1)), p.stem)
    return out


def card_surnames() -> dict[str, set[str]]:
    out: dict[str, set[str]] = defaultdict(set)
    for p in sorted(HOUSEHOLDS.glob("hh_*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        sid = d["associated_with"][0]["place_or_structure_id"]
        for person in d["persons"]:
            if person.get("census_1900") and person.get("grade") != "attested":
                continue                         # 1900 staff do not name the household
            out[sid].add(norm(person["name"].replace(" jr.", "").split()[-1]))
    return out


def card_census_locators() -> dict[str, set[str]]:
    out: dict[str, set[str]] = defaultdict(set)
    for p in sorted(HOUSEHOLDS.glob("hh_*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        sid = d["associated_with"][0]["place_or_structure_id"]
        for person in d["persons"]:
            if person.get("census_1900"):
                out[sid].add(person["census_1900"].get("locator", ""))
    return out


def first_last(name: str) -> str:
    words = [w for w in re.sub(r"\b(Mr|Mrs|Miss|Dr|jr|Jr)\.?", "", name).split() if len(w.strip(".")) > 1]
    return norm(words[0] + words[-1]) if words else ""


def card_full_names() -> dict[str, set[str]]:
    out: dict[str, set[str]] = defaultdict(set)
    for p in sorted(HOUSEHOLDS.glob("hh_*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        sid = d["associated_with"][0]["place_or_structure_id"]
        for person in d["persons"]:
            if person["name"].startswith("Mrs. "):
                continue        # 'Mrs. George M. Pullman' is his widow, not him
            out[sid].add(first_last(person["name"]))
    return out


def same(a: str, b: str) -> bool:
    return a == b or (min(len(a), len(b)) >= 4 and difflib.SequenceMatcher(None, a, b).ratio() >= 0.8)


def _given_compatible(a: list[str], b: list[str]) -> bool:
    if not a or not b:
        return False
    for x, y in zip(a, b):
        x, y = x.strip(".").lower(), y.strip(".").lower()
        if x[:1] != y[:1]:
            return False
        if len(x) > 1 and len(y) > 1 and difflib.SequenceMatcher(None, x, y).ratio() < 0.5 \
                and not (x.startswith(y) or y.startswith(x)):
            return False
    return True


def tidy_members(names: list[str], counts: dict[str, int], surname: str) -> list[str]:
    """One line per person: the group's own spelling of the surname, and of several
    readings of one person ('Thos Murdoch', 'Thomas Murdoch'; 'A. H. Seelye', 'Alexander
    H. Seelye') the one read most often, then the fullest."""
    title_words = ("Mr.", "Mrs.", "Miss", "Dr.", "Rev.", "Capt.", "Prof.")
    people: list[dict] = []
    for raw in names:
        words = raw.replace("'", "").split()
        title = words[0] if words and words[0] in title_words else ""
        body = words[1:] if title else words
        suffix = body[-1] if body and body[-1] in ("jr.", "sr.") else ""
        body = body[:-1] if suffix else body
        given = [w for w in body if not same(norm(w), norm(surname))]
        name = " ".join(p for p in (title, *given, surname, suffix) if p)
        honorific = ("Dr.", "Rev.", "Capt.", "Prof.")
        hit = next((q for q in people if (q["title"] == title or (not q["title"] and title in honorific)
                                           or (not title and q["title"] in honorific))
                    and q["suffix"] == suffix
                    and _given_compatible(q["given"], given)), None)
        if hit is None:
            people.append({"title": title, "suffix": suffix, "given": given, "forms": [(name, raw)]})
        else:
            hit["forms"].append((name, raw))
            if len(given) > len(hit["given"]):
                hit["given"] = given
    out = []
    for q in people:
        best = max(q["forms"], key=lambda f: (counts.get(f[1], 0), len(f[0])))
        out.append(best[0])
    return out


def build() -> dict:
    readings = load_readings()
    census = load_census()
    houses = structures_by_number()
    on_card = card_surnames()
    census_on_card = card_census_locators()
    card_names = card_full_names()

    out_houses = {}
    for n in sorted(houses):
        sid = houses[n]
        # Surname groups, keyed by the ALPHABETICAL list's spelling (the cleaner of the two).
        alpha = [(y, t) for (y, m, k, t) in readings if m == n and k == "alpha"]
        street = [(y, t) for (y, m, k, t) in readings if m == n and k == "street"]
        groups: dict[str, dict] = {}
        for y, t in alpha:
            parts = alpha_parts(t)
            if parts is None:
                continue
            sur, name = parts
            key = next((g for g in groups if same(g, norm(sur))), norm(sur))
            g = groups.setdefault(key, {"spellings": [], "alpha": set(), "street": set(), "members": [], "printed": []})
            g["alpha"].add(y)
            g["spellings"].append(sur)
            g.setdefault("counts", defaultdict(int))[name] += 1
            if name not in g["members"]:
                g["members"].append(name)
        for y, t in street:
            s = norm(street_surname(t))
            key = next((g for g in groups if same(g, s)), None)
            if key:
                groups[key]["street"].add(y)
                groups[key]["spellings"].append(street_surname(t))
                if t not in groups[key]["printed"]:
                    groups[key]["printed"].append(t)
        kept = [g for g in groups.values() if g["street"] or len(g["alpha"]) >= 2]
        for g in kept:
            g["surname"] = max(sorted(set(g["spellings"])), key=g["spellings"].count)
            g["members"] = tidy_members(g["members"], g["counts"], g["surname"])

        entries = []
        for g in kept:
            eds = sorted(g["alpha"] | g["street"])
            entries.append({
                "surname": g["surname"], "first": eds[0], "last": eds[-1], "editions": eds,
                "members": g["members"], "printed": g["printed"][:3],
            })

        # A family in two editions or fewer, whose surname fills a house within twenty
        # numbers for five editions or more, is that house's family under a misread or
        # misprinted number (Mrs. H. O. Stone at 2033 for 2035), and is left out.
        def strong_nearby(surname):
            for m in range(n - 20, n + 21):
                if m == n:
                    continue
                eds = {y for (y, mm, k, t) in readings if mm == m and (
                    (k == "alpha" and (alpha_parts(t) or ("", ""))[0] and same(norm(alpha_parts(t)[0]), surname))
                    or (k == "street" and same(norm(street_surname(t)), surname)))}
                if len(eds) >= 5:
                    return True
            return False
        entries = [e for e in entries if len(e["editions"]) > 2 or not strong_nearby(norm(e["surname"]))]

        current = on_card.get(sid, set())
        listed_1904 = any(SCENE_EDITION in e["editions"] for e in entries)
        former, later = [], []
        for e in entries:
            if any(same(norm(e["surname"]), c) for c in current) and e["last"] >= SCENE_EDITION - 1:
                continue                          # the 1904 household itself
            if e["first"] <= SCENE_EDITION - 1:
                former.append(e)
            elif not current and e["first"] >= LATER_EDITION:
                later.append(e)

        def blue_book_entry(e, role):
            span = f"{e['first']}" if e["first"] == e["last"] else f"{e['first']}-{e['last']}"
            return {
                "name": e["members"][0] if len(e["members"]) == 1 else f"The {e['surname']} household",
                "members": e["members"],
                "role": role,
                "grade": "attested",
                "editions": e["editions"],
                "years": span,
                "sources": [f"chicago_blue_book_{y}" for y in e["editions"]],
                "seen": f"Blue Book {span} ({len(e['editions'])} edition{'s' if len(e['editions']) > 1 else ''})",
                "printed_as": e["printed"],
                "_surname": norm(e["surname"]),
                "_first": e["first"],
            }

        rows = [blue_book_entry(e, "lived here") for e in former]
        # The 1900 census: a head the cards do not seat, folded into the Blue Book family
        # of the same surname where there is one.
        for h in census.get(n, []):
            s = norm(re.sub(r"[\[(].*$", "", h["surname"]))
            if h["locator"] in census_on_card.get(sid, set()) or any(same(s, c) for c in current):
                continue
            row = next((r for r in rows if same(r["_surname"], s)), None)
            census_seen = {"date": "1900-06-01", "locator": h["locator"], "as_enumerated": h["as_enumerated"]}
            if row:
                row["sources"].append("census_1900_chicago_t623_roll245")
                row["census_1900"] = census_seen
                row["seen"] += "; 1900 census"
            else:
                rows.append({
                    "name": h["name"], "members": [h["name"]], "role": "lived here",
                    "grade": "attested", "editions": [], "years": "1900",
                    "sources": ["census_1900_chicago_t623_roll245"],
                    "seen": "1900 census" + (" (the handwriting is uncertain)" if "?" in h["name"] else ""),
                    "printed_as": [], "census_1900": census_seen,
                    "_surname": s, "_first": 1900,
                })
        # The house's namesake goes first: the family the model's name for it means.
        if n in NAMESAKES:
            who, src, line = NAMESAKES[n]
            s = norm(who.replace(" Jr.", "").split()[-1])
            row = next((r for r in rows if same(r["_surname"], s)), None)
            if row is None and first_last(who) not in card_names.get(sid, set()):
                row = {"name": who, "members": [who], "role": "built for", "grade": "attested",
                       "editions": [], "years": "", "sources": [], "seen": "", "printed_as": [],
                       "_surname": s, "_first": 0}
                rows.append(row)
            if row is not None:
                row["namesake"] = {"source": src, "marker": line}
                row["sources"].insert(0, src)
                row["seen"] = "District marker" + (f"; {row['seen']}" if row["seen"] else "")
                row["_first"] = -1
        rows.sort(key=lambda r: r["_first"])
        for r in rows:
            r.pop("_surname"); r.pop("_first")
            if not r["printed_as"]:
                r.pop("printed_as")

        later_rows = [blue_book_entry(e, "lived here after") for e in later]
        for r in later_rows:
            r.pop("_surname"); r.pop("_first"); r.pop("printed_as", None)

        house = {"address": f"{n} Prairie Avenue"}
        if not current:
            last = max(former, key=lambda e: e["last"], default=None)
            first_after = min(later, key=lambda e: e["first"], default=None)
            parts = [f"No edition of the Blue Book for 1904 or 1905 lists anyone at {n}."
                     " The register is selective, so silence is not proof the house was empty."]
            if last:
                parts.append(f"The last household listed before is the {last['surname']} household, "
                             f"in the {last['last']} edition.")
            if first_after:
                parts.append(f"The next is the {first_after['surname']} household, from the "
                             f"{first_after['first']} edition.")
            if n in EMPTY_NOTES:
                parts.append(EMPTY_NOTES[n])
            house["unlisted_on_scene_date"] = {
                "note": " ".join(parts),
                "sources": ["chicago_blue_book_1904", "chicago_blue_book_1905"]
                + (["census_1900_chicago_t623_roll245"] if n == 1827 else []),
            }
        elif listed_1904 is False and not rows:
            continue
        if rows:
            house["former"] = rows
        if later_rows:
            house["later"] = later_rows
        if len(house) > 1:
            out_houses[sid] = house

    return {
        "scene": "1904",
        "standard": ("Who lived in each 1904 Prairie Avenue house before 1 July 1904, and for a "
                     "house nobody is listed in on that day, who came after. Read from the Chicago "
                     "Blue Book's street and alphabetical lists, 1890-1910 (kept only where the two "
                     "agree), the 1900 census, and the district markers' name lines. "
                     "Built by tools/build_former_residents_1904.py (T-3266); not a 1904 fact."),
        "editions_read": EDITIONS_READ,
        "houses": out_houses,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    text = json.dumps(build(), indent=2, ensure_ascii=False) + "\n"
    if a.check:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != text:
            print(f"{OUT.relative_to(ROOT)} is stale: run tools/build_former_residents_1904.py", file=sys.stderr)
            return 1
        print("former residents: up to date")
        return 0
    OUT.write_text(text, encoding="utf-8")
    d = json.loads(text)
    print(f"wrote {OUT.relative_to(ROOT)}: {len(d['houses'])} houses, "
          f"{sum(len(h.get('former', [])) for h in d['houses'].values())} former households, "
          f"{sum(1 for h in d['houses'].values() if 'unlisted_on_scene_date' in h)} unlisted")
    return 0


if __name__ == "__main__":
    sys.exit(main())
