#!/usr/bin/env python3
"""T-3382: write spec.py's children onto the 1904 Prairie Avenue household cards.

Run from chicago/4d:  python3 docs/RESEARCH/prairie-households-children-3382/apply.py
Idempotent: a person already on the card under the same id is replaced, a note already
carrying its addition is left alone. Then rebuild the scene (README.md lists the steps).
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
import spec  # noqa: E402

HH = ROOT / "data" / "residents_1904" / "households"
FAMILY = {"head", "wife", "husband", "son", "daughter"}
OLD = "The 1910 census was not read."
READ = ("The 1910 census (T624 roll 241, ED 166 and 167) was read for this card's children: "
        "the children it lists, and those the Blue Book lists at the number from 1890 to 1911, "
        "are on the card with the years each lived here, whether or not they were at home in 1904.")
UNREAD = ("The children the Blue Book lists at the number from 1890 to 1911 are on the card with the "
          "years each was listed, whether or not they were at home in 1904. The 1910 census was not read for this card.")


def person(e):
    p = {"id": e["id"], "name": e["name"], "relationship": e["rel"], "grade": e["grade"],
         "sources": list(dict.fromkeys(e["sources"]))}
    for k in ("printed_as", "born", "census_1910"):
        if e.get(k):
            p[k] = e[k]
    p["lived_here"] = dict(e["lived_here"])
    if e.get("own_card"):
        p["own_card"] = e["own_card"]
    p["note"] = e["note"]
    return p


def uses_1910(text_or_sources):
    return spec.C10 in json.dumps(text_or_sources) or "1910 census" in json.dumps(text_or_sources)


def main():
    cards, touched, read1910 = {}, set(), set()

    def card(hh):
        if hh not in cards:
            cards[hh] = json.loads((HH / f"{hh}.json").read_text())
        touched.add(hh)
        return cards[hh]

    for e in spec.NEW:
        c = card(e["hh"])
        new = person(e)
        ids = [p["id"] for p in c["persons"]]
        if new["id"] in ids:
            c["persons"][ids.index(new["id"])] = new
        else:
            last = max((i for i, p in enumerate(c["persons"]) if p["relationship"] in FAMILY), default=-1)
            c["persons"].insert(last + 1, new)
        if uses_1910(new):
            read1910.add(e["hh"])
    for e in spec.RECLASS:
        c = card(e["hh"])
        p = next(p for p in c["persons"] if p["id"] == e["id"])
        p["relationship"] = e["rel"]
        p["sources"] = list(dict.fromkeys(p["sources"] + e["add_sources"]))
        p["census_1910"] = e["census_1910"]
        if e["note_add"].strip() not in p.get("note", ""):
            p["note"] = (p.get("note", "") + e["note_add"]).strip()
        read1910.add(e["hh"])
    for (hh, pid), add in spec.NAME_NOTES.items():
        c = card(hh)
        p = next(p for p in c["persons"] if p["id"] == pid)
        if add.strip() not in p.get("note", ""):
            p["note"] = (p.get("note", "") + add).strip()
            if spec.C10 not in p["sources"]:
                p["sources"].append(spec.C10)
        read1910.add(hh)

    for hh in sorted(touched):
        c = cards[hh]
        n = c.get("not_in_this_household")
        if n:
            line = READ if hh in read1910 else UNREAD
            if line not in n["note"]:
                n["note"] = n["note"].replace(OLD, line) if OLD in n["note"] else n["note"].rstrip() + " " + line
            if hh in read1910 and spec.C10 not in n.get("sources", []):
                n.setdefault("sources", []).append(spec.C10)
        (HH / f"{hh}.json").write_text(json.dumps(c, indent=2, ensure_ascii=False) + "\n")
    print(f"{len(spec.NEW)} children added, {len(spec.RECLASS)} relationships corrected, "
          f"{len(spec.NAME_NOTES)} notes extended, on {len(touched)} cards ({len(read1910)} read in 1910)")


if __name__ == "__main__":
    main()
