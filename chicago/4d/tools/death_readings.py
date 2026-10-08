#!/usr/bin/env python3
"""T-2189 — the deaths the town's own registers and papers print, read off their structure.

    python3 tools/death_readings.py --report     every death reading, and what it names

A BURIAL IS A DEPARTURE, NOT A SIGHTING. Father St Cyr's register records five deaths at
Chicago before 1 July 1835, and the Chicago Democrat prints death and probate notices for
more. Until this module the layer read every one of them as an APPEARANCE: the civic mint
let a burial stand as the at-or-before leg of the presence bracket and then ruled the card
`uncertain` because nothing followed it, and the presence stage turned that `uncertain`
into `present`; the readmission stage priced a burial date against the persistence model as
if it were a sighting. So a man buried in October 1834 stood in the town of July 1835 with
a family modelled around him, and a two-year-old whose death notice was the only thing the
corpus held of him headed a household of six.

WHAT COUNTS AS A DEATH READING, and both halves are read from the readers' own structure,
never from prose:

  * a church row whose `cells.role` is `decedent` — the register reader writes the role
    of every name an entry carries, so the child's father (`parent`) and the priest
    (`officiant`) on the same entry are NOT deaths;
  * a newspaper entity whose `role` names the person as the dead one — the paper's
    extraction gives each name a role, so the widow administering an estate
    (`advertiser`), the father of a dead child (`parent`) and the `husband of the
    deceased` on the same claim are NOT deaths. The extraction writes that role in free
    words, so `is_death_role` is the one place the vocabulary is read: `decedent`, and a
    role that BEGINS `deceased` or `died` (`deceased, of Cook county`, `died in this
    town, 22 April 1834, …`). A role that merely mentions a death — `late occupant of
    the tavern stand`, `continuing the business of the late firm` — is not one.

A PRINTED DEATH IS DATED BY ITS ISSUE. A notice says the person was dead by the day the
paper went to press, so the issue date is a `not_later_than` on the death, which is all
the presence rule needs. And it is read across EVERY mention the gazetteer gives the
person, not only the appearance the identity master happened to keep: the master keeps
one press appearance per gazetteer person, so David Laughton's card held his estate's
notice of 20 August 1834 as a sighting and never saw the administrator's notice of
December at all.

`death_notice` — the old settlers' obituary — is the third kind and is NOT read here:
`mint_civic_residents.py` reaches it through the domain's own `places_in_1835` declaration
(T-1131), which is a different argument (its membership places nobody in 1835 at all).
"""
from __future__ import annotations

import argparse
import calendar
import functools
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
CHURCH_RECORDS = ROOT / "data" / "research" / "church" / "records"
NEWSPAPER_CLAIMS = ROOT / "data" / "research" / "newspapers" / "extracted"
GAZETTEER = ROOT / "data" / "research" / "newspapers" / "gazetteer.json"
DEATH_ROLE = "decedent"
DEATH_ROLE_OPENINGS = ("deceased", "died")


def is_death_role(role) -> bool:
    """Does a paper's free-worded entity role name THIS person as the dead one?"""
    text = str(role or "").strip().lower()
    return text == DEATH_ROLE or text.startswith(DEATH_ROLE_OPENINGS)


def _load(path: pathlib.Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


@functools.lru_cache(maxsize=None)
def church_deaths() -> dict:
    """record id -> the register row, for every row whose own role is the decedent."""
    out = {}
    if not CHURCH_RECORDS.exists():
        return out
    for path in sorted(CHURCH_RECORDS.glob("*.json")):
        for row in (_load(path) or {}).get("records") or []:
            if (row.get("cells") or {}).get("role") == DEATH_ROLE and row.get("id"):
                out[row["id"]] = row
    return out


@functools.lru_cache(maxsize=None)
def press_deaths() -> dict:
    """(`<issue>#<claim>`, normalized name) -> the claim, for every decedent the papers print."""
    out = {}
    if not NEWSPAPER_CLAIMS.exists():
        return out
    for path in sorted(NEWSPAPER_CLAIMS.glob("*.json")):
        doc = _load(path) or {}
        issue = doc.get("issue_id") or path.stem
        for claim in doc.get("claims") or []:
            for entity in claim.get("entities") or []:
                if not is_death_role(entity.get("role")):
                    continue
                where = f"{issue}#{claim.get('id')}"
                for key in ("normalized", "as_printed"):
                    if entity.get(key):
                        out[(where, entity[key])] = dict(claim, _issue=issue)
    return out


@functools.lru_cache(maxsize=None)
def gazetteer_mentions() -> dict:
    """gazetteer person id -> [(claim locator, as printed there)], every mention it holds."""
    if not GAZETTEER.exists():
        return {}
    out = {}
    for person in _load(GAZETTEER).get("persons") or []:
        rows = [(v.get("claim"), v.get("as_printed")) for v in person.get("variants") or []]
        out[person.get("id")] = [(c, printed) for c, printed in rows if c]
    return out


def latest_day(describes_date) -> str | None:
    """The LATEST ISO day a register date (`1834-07`, `1835-07-02`, `1835`) permits.

    A death is before the scene date only if EVERY day its entry permits is, so a month
    is read at its last day and a bare year at 31 December.
    """
    parts = str(describes_date or "").strip().split("-")
    if not parts[0].isdigit() or len(parts[0]) != 4 or not all(p.isdigit() for p in parts):
        return None
    year = int(parts[0])
    if len(parts) == 1:
        return f"{year:04d}-12-31"
    month = int(parts[1])
    if not 1 <= month <= 12:
        return None
    if len(parts) == 2:
        return f"{year:04d}-{month:02d}-{calendar.monthrange(year, month)[1]:02d}"
    return f"{year:04d}-{month:02d}-{int(parts[2]):02d}"


def issue_date(issue: str) -> str | None:
    """`chicago_democrat_1834_09_17` -> `1834-09-17`, read off the issue id's own tail."""
    parts = str(issue or "").split("_")[-3:]
    if len(parts) == 3 and all(p.isdigit() for p in parts):
        return "-".join(parts)
    return None


def printed_deaths(app: dict) -> list[dict]:
    """Every death the papers print for this press appearance's person, dated by issue.

    Read off the gazetteer person the appearance names (`record_id`), across all of its
    mentions, matching the entity on the claim by the name AS PRINTED there.
    """
    if app.get("domain") != "newspapers":
        return []
    out = []
    for where, printed in gazetteer_mentions().get(app.get("record_id")) or []:
        claim = press_deaths().get((where, printed))
        if claim is None:
            continue
        day = issue_date(claim["_issue"])
        if day:
            out.append({"kind": "notice", "record": where, "day": day,
                        "printed": claim.get("normalized") or claim.get("quote")})
    return sorted(out, key=lambda d: (d["day"], d["record"]))


def death_reading(app: dict) -> dict | None:
    """What a death reading says, if this identity-master appearance IS one.

    Returns `{"kind": "burial"|"notice", "record": …, "printed": …}`, or None. `printed` is
    the entry as the page gives it — the register's `entry_as_printed`, the paper's
    `normalized` claim — so a note can quote the words rather than paraphrase them.
    """
    if app.get("domain") == "church":
        row = church_deaths().get(app.get("record_id"))
        if row is None:
            return None
        return {"kind": "burial", "record": row.get("id"),
                "printed": (row.get("cells") or {}).get("entry_as_printed") or row.get("as_read"),
                "documented": row.get("confidence") == "documented"}
    if app.get("domain") == "newspapers":
        claim = press_deaths().get((app.get("locator"), app.get("as_read")))
        if claim is None:
            return None
        return {"kind": "notice", "record": app.get("locator"),
                "printed": claim.get("normalized") or claim.get("quote"),
                "documented": True}
    return None


def report() -> int:
    print(f"{len(church_deaths())} register row(s) whose role is the decedent")
    for rid, row in sorted(church_deaths().items()):
        print(f"  {rid:<22} {row.get('describes_date')!s:<11} {row.get('as_read')}")
    print(f"{len(press_deaths())} (claim, name) key(s) for the dead the papers print")
    for (where, name), _claim in sorted(press_deaths().items()):
        print(f"  {where:<36} {name}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--report", action="store_true")
    args = parser.parse_args()
    if args.report:
        return report()
    parser.print_usage()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
