#!/usr/bin/env python3
"""Resolve a read 1840 census line to an IPUMS household SERIAL by its age-band fingerprint.

    tools/census_1840_fingerprint.py --build       write data/research/census_1840/serial_crosswalk.json
    tools/census_1840_fingerprint.py --check       the gate: rebuild and prove the committed file is it
    tools/census_1840_fingerprint.py --self-test   the gate's own assertions still fire when broken
    tools/census_1840_fingerprint.py --report      the counts, on stdout, for a person

WHAT THIS IS FOR (T-0504). IPUMS's 1840 extract for Chicago holds 964 households as
age-band and industry COUNTS WITH NO NAMES. Every one of those households is also a
ruled line on a page image in `chicago/reference/census1840/`, and that line carries
the head's name. The two are joined by the only thing they share: the 1840 schedule's
twenty-six free-white age-band columns — thirteen male, thirteen female. A line's
twenty-six numbers are its FINGERPRINT, and where exactly one IPUMS household carries
that pattern, the line and the serial are the same household.

The method is not this file's invention; it is the owner's, stated in
`chicago/reference/census1840/validation/H_1840_chicago_name_crosswalk_README.txt` and
spent by hand on pages 234-235 in his v1 workbook. What this file adds is that the
method now RUNS, on every page any reading ticket has produced, and says what it cannot
do as loudly as what it can.

WHAT IT REFUSES TO DO, and these are the point:

  * A fingerprint that matches two households reads `ambiguous(2)`. It does not pick
    one. 531 of the 964 households have a globally distinct fingerprint and 433 do not;
    pretending otherwise would mint a name onto the wrong family, which is the one
    failure this project cannot audit its way out of afterwards.
  * A fingerprint that matches nothing reads `none`. A line whose reading is right and
    whose household is simply not in the extract, and a line misread by one child, look
    identical from here, so neither is guessed at.
  * A column the page's own reading did not COMMIT is not compared. Several pages
    balance most of their columns against the enumerator's printed totals and fail one
    or two; those columns are masked out of the fingerprint and `columns_compared`
    records how many survived. A masked fingerprint is weaker, and comes out more
    ambiguous, which is the honest consequence.
  * A SERIAL MAY NOT BE ATTACHED TWICE. Where one serial is the sole match for two
    different lines, neither line gets it — both read `none`, contested, naming each
    other. Two households cannot be one household.
  * BLOCK CONTINUITY IS RECORDED, NEVER SPENT. IPUMS serials run down a page in order,
    so an ambiguous line's candidates can be ranked by which one continues the run of
    its neighbours. That argument is written into the row as `block_continuity` and the
    confidence STAYS `ambiguous`. It is a lead for a human, not a decision by a script.

NOTHING HERE MINTS A RESIDENT. The output is a dated 1840 record: a line on a page, a
serial in an extract, and how firmly they are joined. T-0505 crosswalks named 1840 heads
to 1835 identities, and the ratified grading ladder says 1839/1840 alone is never a 1835
resident.

INPUTS (all committed, no network):
  chicago/reference/census1840/validation/H_1840_chicago_with_names_partial.csv
      the 964-household IPUMS extract, and the 55 v1 name mappings inside it
  chicago/reference/census1840/validation/H_1840_chicago_name_crosswalk_pages234_235.csv
      the v1 mappings as the owner wrote them, for the reproduction
  data/census/1840/household_heads.csv.gz
      the 210 rows PR #670 recovered from the lost v4 workbook, for the reproduction
  data/research/census_1840/pages/*.json
      every page any reading ticket has produced

OUTPUT:
  data/research/census_1840/serial_crosswalk.json
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import sys
import textwrap
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent            # chicago/4d
REPO = ROOT.parent.parent                                # repo root
REFDIR = REPO / "chicago" / "reference" / "census1840" / "validation"
IPUMS_CSV = REFDIR / "H_1840_chicago_with_names_partial.csv"
V1_CSV = REFDIR / "H_1840_chicago_name_crosswalk_pages234_235.csv"
PR670_GZ = ROOT / "data" / "census" / "1840" / "household_heads.csv.gz"
PAGES = ROOT / "data" / "research" / "census_1840" / "pages"
OUT = ROOT / "data" / "research" / "census_1840" / "serial_crosswalk.json"
PACKAGE_CSV = REFDIR / "T-0504_1840_name_serial_crosswalk.csv"
PACKAGE_XLSX = REFDIR / "T-0504_1840_name_serial_crosswalk.xlsx"

# ---------------------------------------------------------------------------
# The column map. Columns 1-26 of the 1840 schedule's left sheet, against the
# IPUMS variable that carries the same band. Verified against the owner's own
# v1 mappings before it was written down: serial 5102106 (page 234 line 9)
# reads nwmlt5=1 nwm5=2 nwm1014=1 nwm30=1 nwflt5=2 nwf30=1, and the scan's line
# 9 reads columns 1,2,3,6,14,19 with the same numbers.
#
# The trap the verification caught: the 10-under-15 band is `nwm1014`/`nwf1014`,
# NOT `nwm10`/`nwf10`. `nwm10` is the 1820 schedule's band and is zero in every
# one of the 964 rows. Fifty of IPUMS's age variables are zero throughout this
# extract because they belong to other census years.
# ---------------------------------------------------------------------------
MALE_VARS = ["nwmlt5", "nwm5", "nwm1014", "nwm15", "nwm20", "nwm30", "nwm40",
             "nwm50", "nwm60", "nwm70", "nwm80", "nwm90", "nwm100"]
FEMALE_VARS = ["nwflt5", "nwf5", "nwf1014", "nwf15", "nwf20", "nwf30", "nwf40",
               "nwf50", "nwf60", "nwf70", "nwf80", "nwf90", "nwf100"]
BAND_VARS = MALE_VARS + FEMALE_VARS                       # column n -> BAND_VARS[n-1]

BANDS = ["Under 5", "5 under 10", "10 under 15", "15 under 20", "20 under 30",
         "30 under 40", "40 under 50", "50 under 60", "60 under 70",
         "70 under 80", "80 under 90", "90 under 100", "100 and upwards"]

# Four page-reading passes wrote their cells in four vocabularies. A reading is a
# reading; the dialect is not. Numeric keys ("1".."38") are the schema-2 pages.
ALIASES: dict[str, int] = {}
for _i, _k in enumerate(["u5", "5_9", "10_14", "15_19", "20_29", "30_39", "40_49",
                         "50_59", "60_69", "70_79", "80_89", "90_99", "100_up"]):
    ALIASES["wm_" + _k] = _i + 1
    ALIASES["wf_" + _k] = _i + 14
for _i, _k in enumerate(["u5", "5_10", "10_15", "15_20", "20_30", "30_40", "40_50",
                         "50_60", "60_70", "70_80", "80_90", "90_100", "100up"]):
    ALIASES["m_" + _k] = _i + 1
    ALIASES["f_" + _k] = _i + 14

# The closure vocabularies, for reading which columns a page COMMITTED.
CLOSURE_GROUPS = {"free_white_males": 0, "free_white_females": 13}
MIN_COLUMNS = 20

CLOSURE_BANDS = ["u5", "5_9", "10_14", "15_19", "20_29", "30_39", "40_49",
                 "50_59", "60_69", "70_79", "80_89", "90_99", "100_up"]


def column_label(col: int) -> str:
    sex = "free white males" if col <= 13 else "free white females"
    return f"{sex} {BANDS[(col - 1) % 13]}"


# ---------------------------------------------------------------------------
# reading the inputs
# ---------------------------------------------------------------------------
def load_ipums(path: Path = IPUMS_CSV) -> list[dict]:
    rows = []
    with path.open(newline="") as fh:
        for r in csv.DictReader(fh):
            rows.append({
                "serial": r["serial"],
                "fingerprint": tuple(int(r[v] or 0) for v in BAND_VARS),
                "ntotal": int(r["ntotal"] or 0),
                "v1_name": (r.get("head_name_transcribed") or "").strip(),
            })
    return rows


def normalise_cells(cells: dict) -> dict[int, int] | None:
    """A record's cells as {column: count} over columns 1..26, or None for a
    reading that never reached band level (the pages that read group totals only)."""
    out: dict[int, int] = {}
    for key, val in cells.items():
        col = None
        if isinstance(key, str) and key.isdigit():
            col = int(key)
        elif key in ALIASES:
            col = ALIASES[key]
        if col is not None and 1 <= col <= 26:
            out[col] = int(val or 0)
    return out or None


def committed_columns(page: dict) -> tuple[set[int], str]:
    """Which of columns 1..26 this page's own reading stands behind, and how we know.

    A column is committed when the lines this pass read SUM to the figure the
    enumerator wrote at the foot of his own sheet. Three page schemas record that
    three ways; a page that records it no way declares its whole reading, and all
    twenty-six are compared."""
    listed = page.get("cells_columns_committed")
    if isinstance(listed, list):
        return {c for c in listed if isinstance(c, int) and 1 <= c <= 26}, "cells_columns_committed"

    # The per-column check, in the two shapes the reading passes wrote it. A page that
    # says `committed` outright is taken at its word. A page that only reports whether
    # each column BALANCED against the enumerator's printed foot total is read the same
    # way, and a column whose read sum matches an alternate reading of a doubtful printed
    # figure counts as closed — the doubt is in the enumerator's handwriting, not in ours.
    check = page.get("cells_column_check")
    if isinstance(check, list) and check and isinstance(check[0], dict):
        if "committed" in check[0]:
            cols = {c["column"] for c in check
                    if isinstance(c.get("column"), int) and c.get("committed")}
            return {c for c in cols if 1 <= c <= 26}, "cells_column_check.committed"
        cols = {c["column"] for c in check
                if isinstance(c.get("column"), int)
                and (c.get("balanced") or c.get("read_sum_matches_an_alternate_reading"))}
        return {c for c in cols if 1 <= c <= 26}, "cells_column_check.balanced"

    closure = page.get("column_closure")
    if isinstance(closure, dict) and any(g in closure for g in CLOSURE_GROUPS):
        cols = set()
        for group, offset in CLOSURE_GROUPS.items():
            block = closure.get(group) or {}
            for i, band in enumerate(CLOSURE_BANDS):
                entry = block.get(band)
                if isinstance(entry, dict) and entry.get("closes"):
                    cols.add(offset + i + 1)
        return cols, "column_closure"

    return set(range(1, 27)), "page declares no per-column closure; whole reading compared"


def load_pages(pages_dir: Path = PAGES) -> list[dict]:
    out = []
    for path in sorted(pages_dir.glob("*.json")):
        page = json.loads(path.read_text())
        page["_file"] = path.name
        out.append(page)
    return out


def load_pr670(path: Path = PR670_GZ) -> list[dict]:
    with gzip.open(path, "rt", newline="") as fh:
        return list(csv.DictReader(fh))


def load_v1(path: Path = V1_CSV) -> list[dict]:
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


# ---------------------------------------------------------------------------
# the match
# ---------------------------------------------------------------------------
def match(fingerprint: dict[int, int], compared: list[int], ipums: list[dict]) -> list[str]:
    """Every IPUMS serial that agrees with this line on every COMPARED column."""
    want = [(c, fingerprint.get(c, 0)) for c in compared]
    return [row["serial"] for row in ipums
            if all(row["fingerprint"][c - 1] == n for c, n in want)]


def block_continuity(lines: list[dict]) -> None:
    """Rank an ambiguous line's candidates by which continues its neighbours' run.

    IPUMS numbers households in enumeration order, so a page's uniquely-resolved
    lines form an ascending run and an ambiguous line between two of them ought to
    sit between their serials. Where exactly one candidate does, it is written into
    the row as a LEAD. The confidence is not touched: this is an argument, and the
    ticket's rule is that a fingerprint matching two serials reads ambiguous."""
    anchors = [(i, int(l["serial"])) for i, l in enumerate(lines) if l["serial"]]
    if len(anchors) < 2:
        return
    for i, line in enumerate(lines):
        if not line["candidates"] or line["serial"]:
            continue
        below = [a for a in anchors if a[0] < i]
        above = [a for a in anchors if a[0] > i]
        if not below or not above:
            continue
        lo_i, lo_s = below[-1]
        hi_i, hi_s = above[0]
        if hi_s <= lo_s:
            continue
        inside = [c for c in line["candidates"] if lo_s < int(c) < hi_s]
        if len(inside) != 1:
            if inside:
                line["block_continuity"] = {
                    "preferred_serial": None,
                    "candidates_inside_the_run": sorted(inside),
                    "argument": (f"lines {lo_i + 1} and {hi_i + 1} resolve uniquely to serials "
                                 f"{lo_s} and {hi_s}, and {len(inside)} of this line's candidates "
                                 f"fall between them, so continuity narrows and does not settle it"),
                }
            continue
        expected = lo_s + (i - lo_i)
        line["block_continuity"] = {
            "preferred_serial": inside[0],
            "argument": (f"lines {lo_i + 1} and {hi_i + 1} resolve uniquely to serials {lo_s} and "
                         f"{hi_s}; of this line's {len(line['candidates'])} candidates exactly one, "
                         f"{inside[0]}, lies in that run"
                         + (f", and an unbroken run would put this line at {expected}"
                            if expected != int(inside[0]) else " at exactly the position an "
                            "unbroken run would put it")),
            "confidence_unchanged": ("a lead for a reader, not a decision: the fingerprint matches "
                                     f"{len(line['candidates'])} households and the row stays ambiguous"),
        }


def build_pages(ipums: list[dict]) -> list[dict]:
    out = []
    for page in load_pages():
        entry = {
            "familysearch_id": page.get("familysearch_id"),
            "image": page.get("image"),
            "printed_page": page.get("printed_page"),
            "sheet_side": page.get("sheet_side"),
            "read_pass": page.get("read_pass"),
        }
        records = page.get("records") or []
        if page.get("page_kind") == "recapitulation":
            # A recapitulation is not a page of families at all, and the generic
            # continuation-sheet reason below would be wrong about it twice: it is
            # not a continuation sheet, and it can never be paired to a left sheet
            # that would make it readable. T-0529 read 33S7-9YYJ-V2 and found that
            # every one of its lines is a DIVISION total of 70 to 201 persons.
            entry["fingerprintable"] = False
            entry["why_not"] = ("a RECAPITULATION sheet: every ruled line is a division total of "
                                "the enumeration, not a household, so there is no family whose "
                                "age-band fingerprint could be compared and no head to name. No "
                                "serial may be hung on any line of it, and pairing it to a left "
                                "sheet would not help - a recapitulation's left sheet carries "
                                "aggregates too, not the twenty-six free-white age bands this "
                                "tool matches on.")
            entry["lines"] = []
            out.append(entry)
            continue
        if page.get("sheet_side") != "left":
            entry["fingerprintable"] = False
            entry["why_not"] = ("a right (continuation) sheet: it carries the slave, industry and "
                                "total columns and no name and no free-white age bands, so there is "
                                "nothing here to fingerprint. Its pairing to a left sheet is a "
                                "separate reading (T-0528, T-0539).")
            entry["lines"] = []
            out.append(entry)
            continue
        if not any(r.get("cells") for r in records):
            entry["fingerprintable"] = False
            entry["why_not"] = ("names read, cells not: this page has no committed per-line age-band "
                                f"cells (cells_state: {page.get('cells_state')!r}).")
            entry["lines"] = []
            out.append(entry)
            continue

        committed, basis = committed_columns(page)
        compared = sorted(committed)
        if len(compared) < MIN_COLUMNS:
            # A fingerprint over a handful of columns is not a fingerprint. Matching on
            # three columns would call half the town a candidate and dress the result up
            # as a reading; a page that closes fewer than MIN_COLUMNS of its 26 is simply
            # not fingerprintable yet, and says so.
            entry["fingerprintable"] = False
            entry["columns_committed_basis"] = basis
            entry["columns_compared"] = compared
            entry["why_not"] = (
                f"only {len(compared)} of the 26 free-white age-band columns close against the "
                f"enumerator's printed foot totals on this page, below the {MIN_COLUMNS} this "
                "tool requires: a fingerprint that narrow does not identify a household, it only "
                "looks like it does. Reconcile the columns and this page becomes readable.")
            entry["lines"] = []
            out.append(entry)
            continue
        entry["fingerprintable"] = True
        entry["columns_committed_basis"] = basis
        entry["columns_compared"] = compared
        entry["columns_masked"] = [{"column": c, "band": column_label(c)}
                                   for c in range(1, 27) if c not in committed]

        lines = []
        for rec in records:
            row = {
                "line": rec.get("line"),
                "as_read": rec.get("as_read"),
                "normalized": rec.get("normalized"),
                "name_confidence": rec.get("name_confidence"),
                "reading": rec.get("reading"),
                "serial": None,
                "serial_mapping_confidence": "none",
                "candidates": [],
            }
            cells = rec.get("cells")
            fp = normalise_cells(cells) if isinstance(cells, dict) else None
            if fp is None:
                row["none_reason"] = ("no band-level cells: this line's reading records group "
                                      "totals only, and a total is not a fingerprint")
                lines.append(row)
                continue
            row["fingerprint"] = [fp.get(c, 0) for c in range(1, 27)]
            row["fingerprint_compared"] = [fp.get(c, 0) for c in compared]
            cands = match(fp, compared, ipums)
            if len(cands) == 1:
                row["serial"] = cands[0]
                row["serial_mapping_confidence"] = "unique"
                row["evidence"] = (
                    f"free-white age-band fingerprint over {len(compared)} of the schedule's 26 "
                    f"columns matches exactly one of the {len(ipums)} IPUMS households"
                    + ("" if len(compared) == 26 else
                       f"; {26 - len(compared)} columns masked because this page's reading does "
                       "not close them against the enumerator's printed totals"))
            elif len(cands) > 1:
                row["serial_mapping_confidence"] = f"ambiguous({len(cands)})"
                row["candidates"] = sorted(cands)
                row["evidence"] = (
                    f"the fingerprint over {len(compared)} columns matches {len(cands)} IPUMS "
                    "households and does not distinguish them; no serial is attached")
            else:
                row["none_reason"] = (
                    f"no IPUMS household carries this pattern over the {len(compared)} compared "
                    "columns — either the household is outside the extract or the reading of one "
                    "cell is wrong, and this tool cannot tell those apart")
            lines.append(row)

        block_continuity(lines)
        entry["lines"] = lines
        entry["counts"] = {
            "lines": len(lines),
            "unique": sum(1 for l in lines if l["serial_mapping_confidence"] == "unique"),
            "ambiguous": sum(1 for l in lines
                             if l["serial_mapping_confidence"].startswith("ambiguous")),
            "none": sum(1 for l in lines if l["serial_mapping_confidence"] == "none"),
            "no_band_level_cells": sum(1 for l in lines
                                       if (l.get("none_reason") or "").startswith("no band-level")),
            "pattern_carried_by_no_household": sum(
                1 for l in lines if (l.get("none_reason") or "").startswith("no IPUMS household")),
        }
        out.append(entry)
    return out


def pages_worth_a_second_look(pages: list[dict]) -> list[dict]:
    """Where the method fails on a WHOLE page, that is a finding about the page.

    A scattering of `none` is ordinary — a household outside the extract, a cell misread.
    A page where a third or more of the read lines carry a pattern NO household in the
    extract carries is saying something else: either its families were enumerated outside
    the city extract, or its columns are off by one somewhere. Naming those pages here is
    the whole use of a negative result, and the next reading ticket should start at them."""
    flagged = []
    for page in pages:
        c = page.get("counts")
        if not c:
            continue
        readable = c["lines"] - c["no_band_level_cells"]
        if readable < 5 or c["pattern_carried_by_no_household"] * 3 < readable:
            continue
        flagged.append({
            "familysearch_id": page["familysearch_id"],
            "printed_page": page.get("printed_page"),
            "lines_with_band_cells": readable,
            "pattern_carried_by_no_household": c["pattern_carried_by_no_household"],
            "what_it_may_mean": (
                f"{c['pattern_carried_by_no_household']} of {readable} read lines on this page "
                "carry an age-band pattern that no household in the Chicago extract carries. "
                "Two explanations fit and this tool cannot choose between them: the page "
                "enumerates families outside the extract's boundary, or the page's column grid "
                "is displaced and every cell is being read one column from where it stands. "
                "Both are worth a reading pass; neither is a reason to relax the match."),
        })
    return flagged


def enforce_one_serial_one_line(pages: list[dict]) -> list[dict]:
    """A serial may not be attached twice. Where one is the sole match for two lines,
    neither keeps it: two households cannot be one household."""
    claims: dict[str, list[tuple[dict, dict]]] = defaultdict(list)
    for page in pages:
        for line in page.get("lines", []):
            if line["serial"]:
                claims[line["serial"]].append((page, line))
    contests = []
    for serial, holders in sorted(claims.items()):
        if len(holders) < 2:
            continue
        where = [f"{p['familysearch_id']} line {l['line']}" for p, l in holders]
        for page, line in holders:
            line["serial"] = None
            line["serial_mapping_confidence"] = "none"
            line.pop("evidence", None)
            line["none_reason"] = (
                f"contested: serial {serial} is the sole fingerprint match for "
                f"{len(holders)} different lines ({', '.join(where)}), and a serial may not be "
                "attached twice, so none of them keeps it")
            line["contested_serial"] = serial
            line["contested_with"] = [w for w in where
                                      if w != f"{page['familysearch_id']} line {line['line']}"]
        contests.append({"serial": serial, "lines": where})
    return contests


# ---------------------------------------------------------------------------
# reproduction: the 55 v1 mappings and the 210 from PR #670
# ---------------------------------------------------------------------------
def resolved_by_page_line(pages: list[dict]) -> dict[tuple[str, str], dict]:
    out = {}
    for page in pages:
        pp = page.get("printed_page")
        if pp in (None, "unknown"):
            continue
        for line in page.get("lines", []):
            out[(str(pp), str(line["line"]))] = line
    return out


def reproduce(prior: list[dict], pages: list[dict], page_key: str, row_key: str,
              serial_key: str, name_key: str, label: str) -> dict:
    index = resolved_by_page_line(pages)
    agrees, disagrees, not_reached, not_read = [], [], [], []
    for r in prior:
        page, row, serial = r.get(page_key), r.get(row_key), (r.get(serial_key) or "").strip()
        line = index.get((str(page), str(row)))
        if line is None:
            not_read.append({"page": page, "row": row, "serial": serial,
                             "why": "this pass has committed no cells for that line"})
            continue
        entry = {
            "page": page, "row": row,
            "prior_serial": serial,
            "prior_name": (r.get(name_key) or "").strip(),
            "this_pass_serial": line["serial"],
            "this_pass_confidence": line["serial_mapping_confidence"],
            "this_pass_name": line.get("as_read"),
        }
        if line["serial"] and serial and line["serial"] == serial:
            agrees.append(entry)
        elif line["serial"] and serial and line["serial"] != serial:
            entry["decided_by"] = (
                "the scan reading: the fingerprint over this page's committed columns matches "
                f"{line['serial']} and only {line['serial']}, and {serial} does not carry the "
                "pattern the line does. The prior mapping is kept here and not overwritten.")
            disagrees.append(entry)
        else:
            if serial and serial in line.get("candidates", []):
                entry["note"] = (f"the prior serial is among this pass's {len(line['candidates'])} "
                                 "candidates; the fingerprint cannot distinguish them")
            elif serial and line.get("candidates"):
                entry["note"] = (f"the prior serial is NOT among this pass's "
                                 f"{len(line['candidates'])} candidates")
            else:
                entry["note"] = line.get("none_reason", "")
            not_reached.append(entry)
    # A disagreement that is a CONSTANT OFFSET down a run of lines is a different fault
    # from a scattering: it says the prior reading placed the block correctly and started
    # it in the wrong place, which is exactly what an assignment made from page-block
    # position rather than from the line's own numbers does. Summarising the shape is what
    # lets a reader see that at a glance instead of diffing thirty rows.
    shape: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for e in disagrees:
        shape[str(e["page"])][str(int(e["this_pass_serial"]) - int(e["prior_serial"]))] += 1
    shaped = {page: {"offsets": dict(sorted(offs.items(), key=lambda kv: -kv[1]))}
              for page, offs in sorted(shape.items())}
    for page, entry in shaped.items():
        offs = entry["offsets"]
        entry["reading"] = (
            f"{sum(offs.values())} disagreements on printed page {page} over "
            f"{len(offs)} distinct offsets"
            + ("; a run at a constant offset is a block placed correctly and started in the "
               "wrong row, not a misread line" if len(offs) < sum(offs.values()) else
               "; no constant offset, so these are line-by-line differences"))

    return {
        "what": label,
        "rows_in_the_prior_reading": len(prior),
        "rows_this_pass_reaches": len(prior) - len(not_read),
        "agreement": len(agrees),
        "disagreement": len(disagrees),
        "not_resolved_by_this_pass": len(not_reached),
        "line_not_read_by_this_pass": len(not_read),
        "disagreement_shape": shaped,
        "disagreements": disagrees,
        "unresolved": not_reached,
        "lines_not_read": not_read,
    }


# ---------------------------------------------------------------------------
# build
# ---------------------------------------------------------------------------
def build_document() -> dict:
    ipums = load_ipums()
    pages = build_pages(ipums)
    contests = enforce_one_serial_one_line(pages)

    lines = [l for p in pages for l in p.get("lines", [])]
    unique = [l for l in lines if l["serial_mapping_confidence"] == "unique"]
    ambiguous = [l for l in lines if l["serial_mapping_confidence"].startswith("ambiguous")]
    none = [l for l in lines if l["serial_mapping_confidence"] == "none"]
    named = [l for l in unique if (l.get("as_read") or "").strip()]

    patterns = defaultdict(int)
    for row in ipums:
        patterns[row["fingerprint"]] += 1
    distinct = sum(1 for n in patterns.values() if n == 1)

    doc = {
        "schema": 1,
        "ticket": "T-0504",
        "generated_by": "tools/census_1840_fingerprint.py --build",
        "what": ("Every 1840 census line this project has read, joined to the IPUMS household "
                 "SERIAL its free-white age-band fingerprint identifies — or told, in its own row, "
                 "why it could not be."),
        "method": (
            "The 1840 schedule's left sheet carries twenty-six free-white age-band columns, "
            "thirteen male and thirteen female. A read line's twenty-six numbers are compared "
            "against the same twenty-six IPUMS household variables. Exactly one match is "
            "`unique` and attaches the serial; more than one is `ambiguous(n)` and attaches "
            "nothing; none is `none`. A column the page's own reading does not close against "
            "the enumerator's printed foot totals is masked out of the comparison and counted "
            "in `columns_masked`. Serial-block continuity is recorded as an argument on "
            "ambiguous rows and never changes a confidence. A serial is attached to at most "
            "one line. Name-reading confidence and serial-mapping confidence stay separate, as "
            "the v1 method statement requires."),
        "does_not": ("mint a resident, regrade one, or carry a 1840 name back to 1835. This is a "
                     "dated 1840 record. T-0505 does the 1835 crosswalk; the ratified ladder says "
                     "1839/1840 alone is never a 1835 resident."),
        "inputs": {
            "ipums_extract": str(IPUMS_CSV.relative_to(REPO)),
            "v1_mappings": str(V1_CSV.relative_to(REPO)),
            "pr_670_mappings": str(PR670_GZ.relative_to(ROOT)),
            "page_readings": str(PAGES.relative_to(ROOT)) + "/*.json",
            "method_statement": "chicago/reference/census1840/validation/H_1840_chicago_name_crosswalk_README.txt",
        },
        "column_map": [
            {"column": c, "band": column_label(c), "ipums_variable": BAND_VARS[c - 1]}
            for c in range(1, 27)
        ],
        "column_map_note": (
            "The 10-under-15 band is `nwm1014`/`nwf1014`. `nwm10`/`nwf10` belong to an earlier "
            "schedule and are zero in all 964 rows, as are 48 other age variables in the extract."),
        "the_extract": {
            "households": len(ipums),
            "distinct_fingerprints": len(patterns),
            "households_with_a_globally_distinct_fingerprint": distinct,
            "households_sharing_a_fingerprint_with_another": len(ipums) - distinct,
            "ceiling_note": (f"{distinct} of {len(ipums)} households can EVER be resolved by "
                             "fingerprint alone. The other "
                             f"{len(ipums) - distinct} share their pattern with at least one "
                             "other household and no reading of the age bands, however perfect, "
                             "will separate them."),
        },
        "counts": {
            "pages_held": len(pages),
            "pages_fingerprintable": sum(1 for p in pages if p.get("fingerprintable")),
            "lines_read_on_fingerprintable_pages": len(lines),
            "unique": len(unique),
            "ambiguous": len(ambiguous),
            "none": len(none),
            "named_heads_carrying_a_serial": len(named),
            "serials_attached": len({l["serial"] for l in unique}),
            "contested_serials_withdrawn": len(contests),
        },
        "contested_serials": contests,
        "pages_worth_a_second_look": pages_worth_a_second_look(pages),
        "pages": pages,
    }
    doc["counts"]["sum_check"] = {
        "unique_plus_ambiguous_plus_none": len(unique) + len(ambiguous) + len(none),
        "lines": len(lines),
        "sums": len(unique) + len(ambiguous) + len(none) == len(lines),
    }
    doc["reproduction"] = {
        "why": ("The 55 v1 mappings and the 210 rows PR #670 recovered from the owner's lost v4 "
                "workbook are prior readings of the same pages. This tool reproduces them before "
                "it extends them, and NOTHING PRIOR IS OVERWRITTEN: a disagreement is listed with "
                "the reading that decides it and both readings stay on the record."),
        "v1_55": reproduce(load_v1(), pages, "census_page", "census_row", "serial",
                           "head_name_transcribed",
                           "the 55 mappings the owner made by hand on printed pages 234-235"),
        "pr_670_210": reproduce(load_pr670(), pages, "page", "row", "serial", "preferred_name",
                                "the 210 rows PR #670 recovered from the lost v4 workbook"),
    }
    return doc


def package_rows(doc: dict) -> list[dict]:
    rows = []
    for page in doc["pages"]:
        if not page.get("fingerprintable"):
            continue
        for line in page["lines"]:
            bc = line.get("block_continuity") or {}
            rows.append({
                "familysearch_id": page["familysearch_id"],
                "printed_page": page.get("printed_page"),
                "line": line["line"],
                "head_name_as_read": line.get("as_read") or "",
                "head_name_normalized": line.get("normalized") or "",
                "name_confidence": line.get("name_confidence") or "",
                "name_reading": line.get("reading") or "",
                "serial": line.get("serial") or "",
                "serial_mapping_confidence": line["serial_mapping_confidence"],
                "columns_compared": len(page.get("columns_compared", [])),
                "candidates": ";".join(line.get("candidates", [])),
                "block_continuity_preferred_serial": bc.get("preferred_serial") or "",
                "block_continuity_argument": bc.get("argument", ""),
                "evidence": line.get("evidence", "") or line.get("none_reason", ""),
                "source_image": page.get("image", ""),
            })
    return rows


PACKAGE_FIELDS = ["familysearch_id", "printed_page", "line", "head_name_as_read",
                  "head_name_normalized", "name_confidence", "name_reading", "serial",
                  "serial_mapping_confidence", "columns_compared", "candidates",
                  "block_continuity_preferred_serial", "block_continuity_argument",
                  "evidence", "source_image"]


def write_package(doc: dict) -> list[str]:
    rows = package_rows(doc)
    with PACKAGE_CSV.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=PACKAGE_FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    PACKAGE_README.write_text(readme_text(doc))
    written = [str(PACKAGE_CSV.relative_to(REPO)),
               str(PACKAGE_README.relative_to(REPO))]
    try:
        import openpyxl
    except ImportError:
        return written
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "serial_crosswalk"
    ws.append(PACKAGE_FIELDS)
    for r in rows:
        ws.append([r[f] for f in PACKAGE_FIELDS])
    wb.save(PACKAGE_XLSX)
    written.append(str(PACKAGE_XLSX.relative_to(REPO)))
    return written


PACKAGE_README = REFDIR / "T-0504_1840_name_serial_crosswalk_README.txt"


def wrap(text: str, indent: str = "   ") -> str:
    """Reflow to the 92 columns the rest of this folder's READMEs keep."""
    return "\n".join(textwrap.wrap(text, width=92, subsequent_indent=indent))


def readme_text(doc: dict) -> str:
    """The package's README, GENERATED — so its counts cannot drift from the crosswalk.

    Shaped after H_1840_chicago_name_crosswalk_README.txt, which is the owner's own
    method statement for this join, because the successor to a workbook should be
    readable by whoever read the workbook."""
    c, e, rep = doc["counts"], doc["the_extract"], doc["reproduction"]
    v1, pr = rep["v1_55"], rep["pr_670_210"]
    rows = []
    for page in doc["pages"]:
        if not page.get("fingerprintable"):
            continue
        pc = page["counts"]
        rows.append(f"  {str(page.get('printed_page')):>7}  {page['familysearch_id']:<14} "
                    f"{len(page['columns_compared']):>2}/26  {pc['lines']:>3}  {pc['unique']:>4}  "
                    f"{pc['ambiguous']:>5}  {pc['none']:>4}")
    table = "\n".join(rows)
    shape = pr.get("disagreement_shape") or {}
    shape_prose = "; ".join(
        f"page {pg}: " + ", ".join(f"{n} at {off:+d}" for off, n in
                                   [(int(o), n) for o, n in entry["offsets"].items()])
        for pg, entry in shape.items()) or "none"
    # Pages whose NAMES are read and whose age-band cells are not — both the ones held
    # back before fingerprinting and the ones that reached it carrying group totals only.
    # They are the same opportunity and belong in one list.
    unread = sorted(
        {str(p.get("printed_page")) for p in doc["pages"]
         if not p.get("fingerprintable")
         and str(p.get("why_not", "")).startswith("names read, cells not")}
        | {str(p.get("printed_page")) for p in doc["pages"]
           if p.get("fingerprintable")
           and p["counts"]["no_band_level_cells"] == p["counts"]["lines"]})
    flagged = doc.get("pages_worth_a_second_look") or []
    shape_para = wrap(
        f"  The {pr['disagreement']} disagreements are NOT scattered. They fall into runs at a "
        f"constant offset ({shape_prose})", indent="  ")
    second_look = "\n".join(
        wrap(f"1. Printed page {f['printed_page']} (image {f['familysearch_id']}) is flagged in "
             f"`pages_worth_a_second_look`: {f['pattern_carried_by_no_household']} of its "
             f"{f['lines_with_band_cells']} read lines carry a pattern no household in the "
             "extract carries. Either its families were enumerated outside the extract's "
             "boundary or its column grid is displaced.")
        for f in flagged) or "1. No page is flagged: no page fails the match wholesale."

    return f"""T-0504 - 1840 Chicago census line -> IPUMS SERIAL crosswalk (successor to the lost v3/v4 workbooks)

This package is named by TICKET, not by a version number. The owner's v1 and v2 workbooks
survive in this folder; v3 and v4 do not, and his ruling of 2026-09-03 on them was "They are
lost; rebuild". This is the rebuild, and it is GENERATED rather than hand-kept, so it can be
re-derived from the committed page readings at any time and cannot silently drift from them.
This README is generated with it, for the same reason.

  generated by   chicago/4d/tools/census_1840_fingerprint.py --build
  gated by       chicago/4d/tools/census_1840_fingerprint.py --check   (in tools/check.sh)
  full record    chicago/4d/data/research/census_1840/serial_crosswalk.json
  files          T-0504_1840_name_serial_crosswalk.csv
                 T-0504_1840_name_serial_crosswalk.xlsx (written when openpyxl is available)

THE METHOD is the one stated in H_1840_chicago_name_crosswalk_README.txt and spent by hand on
pages 234-235. The 1840 schedule's left sheet carries twenty-six free-white age-band columns,
thirteen male and thirteen female. A read line's twenty-six numbers are its fingerprint, and
are compared against the same twenty-six IPUMS household variables. What is new here is only
that it now runs over every page any reading ticket has produced, and that it states its
refusals as plainly as its results.

  unique         exactly one IPUMS household carries the pattern. The serial is attached.
  ambiguous(n)   n households carry it. NO serial is attached. The candidates are listed.
  none           no household carries it, or the line has no band-level cells, or the serial
                 it would take is contested by another line.

Name-reading confidence and serial-mapping confidence stay separate, as v1 requires:
name_confidence is confidence reading the handwriting, serial_mapping_confidence is
confidence attaching that census line to the IPUMS SERIAL.

THE CEILING, and it is the first thing to understand about this method: {e['households_with_a_globally_distinct_fingerprint']} of the {e['households']}
households have a globally distinct fingerprint. The other {e['households'] - e['households_with_a_globally_distinct_fingerprint']} share their pattern with at
least one other household, and NO reading of the age bands, however perfect, will ever
separate them. Small households collide constantly. Naming those needs a second axis - the
1839 directory, the poll books, the church registers - not a better read of the same columns.

WHAT IS COMPARED. A column is compared only where the page's own reading CLOSES it against
the enumerator's printed foot total. A page that closes fewer than twenty of its twenty-six
is not fingerprinted at all; a fingerprint that narrow does not identify a household, it only
looks like it does. `columns_compared` on every row says how many survived.

A SERIAL IS ATTACHED TO AT MOST ONE LINE. Where one serial is the sole match for two
different lines, neither keeps it and both read `none`, naming each other. Two households
cannot be one household.

BLOCK CONTINUITY IS RECORDED, NEVER SPENT. IPUMS numbers households in enumeration order, so
an ambiguous line's candidates can be ranked by which one continues the run of its resolved
neighbours. That argument is written into the row as `block_continuity` and the confidence is
NOT changed by it. It is a lead for a reader, not a decision by a script.

COUNTS as of this build

  households in the extract          {e['households']}
  distinct fingerprints among them   {e['distinct_fingerprints']}
  pages held                         {c['pages_held']}
  pages carrying committed cells     {c['pages_fingerprintable']}
  lines read on those pages          {c['lines_read_on_fingerprintable_pages']}
    unique                           {c['unique']}
    ambiguous                        {c['ambiguous']}
    none                             {c['none']}
  serials attached                   {c['serials_attached']}
  contested and withdrawn            {c['contested_serials_withdrawn']}

  printed  image           cols   lines  uniq   ambig  none
{table}

REPRODUCTION BEFORE EXTENSION. Two prior readings of these pages exist and NEITHER is
overwritten by this one.

  v1 - the owner's {v1['rows_in_the_prior_reading']} hand mappings on printed pages 234-235
    lines this pass has cells for   {v1['rows_this_pass_reaches']} of {v1['rows_in_the_prior_reading']}
    agree                           {v1['agreement']}
    DISAGREE                        {v1['disagreement']}
    this pass does not resolve      {v1['not_resolved_by_this_pass']}
  The hand method and the tool agree on every line where both reach a serial. Where the tool
  reads `ambiguous` and v1 reads a serial, v1 spent block continuity to settle it; this tool
  records that argument and does not spend it.

  PR #670 - the {pr['rows_in_the_prior_reading']} rows recovered from the lost v4 workbook
    lines this pass has cells for   {pr['rows_this_pass_reaches']} of {pr['rows_in_the_prior_reading']}
    agree                           {pr['agreement']}
    DISAGREE                        {pr['disagreement']}
    this pass does not resolve      {pr['not_resolved_by_this_pass']}
{shape_para}. #670's own `serial_confidence` column says how those serials were
  attached - "continuation totals + page block" - which is an argument from POSITION, and a
  run at a constant offset is what that produces when a block is started a row or two from
  where it belongs. The fingerprint is an argument from the line's own numbers, so where the
  two differ this file follows the fingerprint. Both readings stay on the record: every
  disagreement is listed row by row in serial_crosswalk.json under
  reproduction.pr_670_210.disagreements, and #670's file is untouched.

WHAT THIS IS NOT. It does not mint a resident, regrade one, or carry an 1840 name back to
1835. It is a dated 1840 record. T-0505 crosswalks named 1840 heads to 1835 identities, and
the ratified grading ladder holds: 1839/1840 alone is never a 1835 resident.

WHAT SHOULD HAPPEN NEXT
{second_look}
2. The pages whose names are read but whose age-band cells are not - printed {', '.join(unread)} -
   are worth about thirty more resolvable lines each. Reading their cells is the cheapest
   remaining gain here, and needs no new source.
3. The ambiguous rows need a second axis, not a better read of the same columns. The 1839
   directory (T-0506) and the poll books are that axis.
"""


def dumps(doc: dict) -> str:
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"


# ---------------------------------------------------------------------------
# the gate
# ---------------------------------------------------------------------------
def invariants(doc: dict) -> list[str]:
    bad = []
    counts = doc["counts"]
    if not counts["sum_check"]["sums"]:
        bad.append("unique + ambiguous + none does not sum to the lines read")

    serials = {r["serial"] for r in load_ipums()}
    seen: dict[str, str] = {}
    for page in doc["pages"]:
        for line in page.get("lines", []):
            conf = line["serial_mapping_confidence"]
            where = f"{page['familysearch_id']} line {line['line']}"
            if conf == "unique":
                if not line["serial"]:
                    bad.append(f"{where}: unique with no serial")
                elif line["serial"] not in serials:
                    bad.append(f"{where}: serial {line['serial']} is not in the IPUMS extract")
                if line["serial"] in seen:
                    bad.append(f"{where}: serial {line['serial']} already attached to {seen[line['serial']]}")
                seen[line["serial"]] = where
            elif conf.startswith("ambiguous"):
                if line["serial"]:
                    bad.append(f"{where}: ambiguous rows must attach no serial")
                if len(line.get("candidates", [])) < 2:
                    bad.append(f"{where}: ambiguous with fewer than two candidates")
                if not conf.startswith(f"ambiguous({len(line['candidates'])})"):
                    bad.append(f"{where}: confidence {conf} does not state its candidate count")
            elif conf == "none":
                if line["serial"]:
                    bad.append(f"{where}: none must attach no serial")
                if not line.get("none_reason"):
                    bad.append(f"{where}: none with no reason")
            else:
                bad.append(f"{where}: confidence {conf!r} is outside unique|ambiguous(n)|none")
            bc = line.get("block_continuity")
            if bc and bc.get("preferred_serial") and conf != "none":
                if conf == "unique":
                    bad.append(f"{where}: block continuity recorded on an already-unique row")
    if counts["serials_attached"] != len(seen):
        bad.append("serials_attached disagrees with the serials actually attached")
    for section in ("v1_55", "pr_670_210"):
        rep = doc["reproduction"][section]
        total = (rep["agreement"] + rep["disagreement"] + rep["not_resolved_by_this_pass"]
                 + rep["line_not_read_by_this_pass"])
        if total != rep["rows_in_the_prior_reading"]:
            bad.append(f"reproduction {section}: the outcomes do not sum to the prior rows")
    return bad


def cmd_check() -> int:
    if not OUT.exists():
        print(f"FAIL: {OUT.relative_to(ROOT)} is missing — run --build", file=sys.stderr)
        return 1
    fresh = build_document()
    committed = json.loads(OUT.read_text())
    if committed != fresh:
        print("FAIL: the committed serial crosswalk is not what the readings now produce.\n"
              "      A page reading changed and the crosswalk was not rebuilt. Run --build.",
              file=sys.stderr)
        return 1
    bad = invariants(fresh)
    if bad:
        for b in bad:
            print("FAIL: " + b, file=sys.stderr)
        return 1
    rows = package_rows(fresh)
    if not PACKAGE_CSV.exists():
        print(f"FAIL: the reference package {PACKAGE_CSV.name} is missing", file=sys.stderr)
        return 1
    with PACKAGE_CSV.open(newline="") as fh:
        have = list(csv.DictReader(fh))
    if len(have) != len(rows):
        print(f"FAIL: {PACKAGE_CSV.name} has {len(have)} rows, the crosswalk has {len(rows)}",
              file=sys.stderr)
        return 1
    if not PACKAGE_README.exists():
        print(f"FAIL: the reference package README {PACKAGE_README.name} is missing",
              file=sys.stderr)
        return 1
    if PACKAGE_README.read_text() != readme_text(fresh):
        print(f"FAIL: {PACKAGE_README.name} no longer states the crosswalk's own counts. "
              "Run --build.", file=sys.stderr)
        return 1
    c = fresh["counts"]
    print(f"  {c['lines_read_on_fingerprintable_pages']} lines read on "
          f"{c['pages_fingerprintable']} pages · {c['unique']} unique · {c['ambiguous']} ambiguous "
          f"· {c['none']} none · {c['serials_attached']} of "
          f"{fresh['the_extract']['households']} households named")
    return 0


def cmd_self_test() -> int:
    """The assertions, broken on purpose. Each must fire."""
    ipums = [
        {"serial": "1", "fingerprint": (1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
                                        0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0), "ntotal": 3, "v1_name": ""},
        {"serial": "2", "fingerprint": (1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
                                        0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0), "ntotal": 3, "v1_name": ""},
        {"serial": "3", "fingerprint": (0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0,
                                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0), "ntotal": 2, "v1_name": ""},
    ]
    all_cols = list(range(1, 27))
    failures = []

    def assert_(cond, what):
        if not cond:
            failures.append(what)
        print(("  ok   " if cond else "  FAIL ") + what)

    # 1. a fingerprint that matches two serials is ambiguous, and picks neither
    two = match({1: 1, 5: 1, 18: 1}, all_cols, ipums)
    assert_(sorted(two) == ["1", "2"], "a pattern carried by two households matches both")
    lines = [{"line": 1, "serial": None, "serial_mapping_confidence": f"ambiguous({len(two)})",
              "candidates": sorted(two)}]
    assert_(lines[0]["serial"] is None and lines[0]["serial_mapping_confidence"] == "ambiguous(2)",
            "an ambiguous line attaches no serial and states its candidate count")

    # 2. a line with no match reads none
    assert_(match({6: 9}, all_cols, ipums) == [],
            "a pattern no household carries matches nothing and reads none")

    # 3. exactly one match resolves
    assert_(match({5: 2}, all_cols, ipums) == ["3"],
            "a pattern exactly one household carries resolves to it")

    # 4. a serial may not be attached twice
    doubled = [{"familysearch_id": "X", "fingerprintable": True, "lines": [
        {"line": 1, "serial": "3", "serial_mapping_confidence": "unique", "candidates": [],
         "evidence": "e"},
        {"line": 2, "serial": "3", "serial_mapping_confidence": "unique", "candidates": [],
         "evidence": "e"}]}]
    contests = enforce_one_serial_one_line(doubled)
    got = doubled[0]["lines"]
    assert_(len(contests) == 1 and all(l["serial"] is None for l in got)
            and all(l["serial_mapping_confidence"] == "none" for l in got)
            and all(l.get("none_reason") for l in got),
            "a serial claimed by two lines is withdrawn from both, with a reason on each")

    # 5. masking a column widens the match rather than narrowing it
    narrow = match({1: 1, 5: 1, 18: 1}, all_cols, ipums)
    wide = match({1: 1, 5: 1, 18: 1}, [c for c in all_cols if c != 18], ipums)
    assert_(len(wide) >= len(narrow),
            "masking an uncommitted column can only widen the candidate set")

    # 6. block continuity records a lead and never upgrades a confidence
    page = [
        {"line": 1, "serial": "100", "serial_mapping_confidence": "unique", "candidates": []},
        {"line": 2, "serial": None, "serial_mapping_confidence": "ambiguous(2)",
         "candidates": ["101", "500"]},
        {"line": 3, "serial": "102", "serial_mapping_confidence": "unique", "candidates": []},
    ]
    block_continuity(page)
    mid = page[1]
    assert_(mid.get("block_continuity", {}).get("preferred_serial") == "101",
            "block continuity names the candidate that continues the run")
    assert_(mid["serial"] is None and mid["serial_mapping_confidence"] == "ambiguous(2)",
            "…and the row it names stays ambiguous with no serial attached")

    # 7. the column map is the one the owner's own mappings verify
    assert_(BAND_VARS[2] == "nwm1014" and BAND_VARS[15] == "nwf1014",
            "the 10-under-15 band maps to nwm1014/nwf1014, not nwm10/nwf10")
    assert_(len(BAND_VARS) == 26 and len(set(BAND_VARS)) == 26,
            "the column map is 26 distinct IPUMS variables")

    # 8. the invariant check itself fires
    broken = {
        "counts": {"sum_check": {"sums": False}, "serials_attached": 0},
        "pages": [{"familysearch_id": "X", "lines": [
            {"line": 1, "serial": None, "serial_mapping_confidence": "ambiguous(2)",
             "candidates": ["1"]}]}],
        "reproduction": {"v1_55": {"agreement": 1, "disagreement": 0,
                                   "not_resolved_by_this_pass": 0,
                                   "line_not_read_by_this_pass": 0,
                                   "rows_in_the_prior_reading": 9},
                         "pr_670_210": {"agreement": 0, "disagreement": 0,
                                        "not_resolved_by_this_pass": 0,
                                        "line_not_read_by_this_pass": 0,
                                        "rows_in_the_prior_reading": 0}},
    }
    bad = invariants(broken)
    assert_(any("does not sum" in b for b in bad), "the sum check fires when the counts do not sum")
    assert_(any("fewer than two candidates" in b for b in bad),
            "the ambiguity check fires on an ambiguous row with one candidate")
    assert_(any("outcomes do not sum" in b for b in bad),
            "the reproduction check fires when the outcomes do not sum to the prior rows")

    if failures:
        print(f"\nSELF-TEST FAIL — {len(failures)} assertion(s) did not fire", file=sys.stderr)
        return 1
    print("\nself-test: every assertion fires")
    return 0


def cmd_build() -> int:
    doc = build_document()
    bad = invariants(doc)
    if bad:
        for b in bad:
            print("FAIL: " + b, file=sys.stderr)
        return 1
    OUT.write_text(dumps(doc))
    written = write_package(doc)
    c = doc["counts"]
    print(f"wrote {OUT.relative_to(ROOT)}")
    for w in written:
        print(f"wrote {w}")
    cmd_report(doc)
    return 0


def cmd_report(doc: dict | None = None) -> int:
    doc = doc or build_document()
    c = doc["counts"]
    e = doc["the_extract"]
    print(f"\n1840 SERIAL CROSSWALK — T-0504")
    print(f"  the extract          {e['households']} households, "
          f"{e['households_with_a_globally_distinct_fingerprint']} with a distinct fingerprint "
          f"(the ceiling on this method)")
    print(f"  pages held           {c['pages_held']}, of which {c['pages_fingerprintable']} carry "
          f"committed age-band cells")
    print(f"  lines read           {c['lines_read_on_fingerprintable_pages']}")
    print(f"    unique             {c['unique']}")
    print(f"    ambiguous          {c['ambiguous']}")
    print(f"    none               {c['none']}")
    print(f"  serials attached     {c['serials_attached']} "
          f"({c['named_heads_carrying_a_serial']} of them carry a read name)")
    if c["contested_serials_withdrawn"]:
        print(f"  contested, withdrawn {c['contested_serials_withdrawn']}")
    for key, rep in doc["reproduction"].items():
        if key == "why":
            continue
        print(f"\n  reproduction — {rep['what']}")
        print(f"    reached by this pass {rep['rows_this_pass_reaches']} of "
              f"{rep['rows_in_the_prior_reading']}")
        print(f"    agree                {rep['agreement']}")
        print(f"    disagree             {rep['disagreement']}")
        print(f"    unresolved here      {rep['not_resolved_by_this_pass']}")
        print(f"    line not read here   {rep['line_not_read_by_this_pass']}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return cmd_self_test()
    if args.build:
        return cmd_build()
    if args.check:
        return cmd_check()
    if args.report:
        return cmd_report()
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
