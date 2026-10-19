#!/usr/bin/env python3
"""The visitor-UI lint (T-2668; design doc "Field Navigator Mk II", NAV-1003 and section 12).

    python3 tools/check_visitor_ui.py --check       lint every visitor surface below
    python3 tools/check_visitor_ui.py --self-test   plant each fault and require it refused

The design doc is written for students of 14 to 16, mostly on phones, and its section 12
"Remove from visitor UI" names what they must never read: file paths, ids and snake_case,
"Tier 1 · period/eyewitness", the order book, ticket references. So this refuses, in any
string a visitor reads:

  - a file path, a link, an id or snake_case word, or a ticket number
    (compile_summaries.lint_string, imported, so this lint, the string table's, the Guide's
    and the summary records' agree on what an id is);
  - the words "tier", "ticket" and "order book", in any case and either number. A grade is
    Attested, Inferred or Reconstructed (section 03); "tier" is the data's word for it.

WHAT IT READS — the surfaces, and why each is one:

  table   every string in the Navigator string table, renderers/web/js/strings/, and each
          Navigator app manifest's name and screen code (the same read check_strings.py does).
  page    the visible text of the shipped static pages (renderers/web/index.html and the
          portal's two): text between tags and the title, aria-label, placeholder and alt
          attributes, with scripts, styles and comments removed. A hidden panel counts: a
          tap opens it.
  goto    compiled data a visitor surface prints verbatim. The Go to list's business rows
          (js/destinations.js) print each firm's name, trade and street, and, for a firm
          with no roof to stand at, `where.limit_reason` from data/businesses/index.json,
          which main.js also says aloud when the row is picked. A firm not trading at the
          scene date shows "Not present at this scene date" instead, so its reason is not read.

  Already linted elsewhere, with the same lint_string: the summary records
  (compile_summaries.py), the time-stream caption decks (check_timestream.py), the Guide's
  glossary and FAQ (check_guide.py) and the templated building card (test_fallback_summary).

  NOT YET READ, and why. Strings built in JavaScript (template literals in js/*.js) are not
  read: telling a visible literal from a class name or a key statically is noise, and the
  honest check is the rendered DOM in the smoke, which wants the runner. The Shops & work
  card's location lines (`basis` and every location's `limit_reason`, js/businesses.js)
  are research prose that Researcher mode (T-2657) takes off the visitor's path. Guide ›
  About this destination (T-2667) folded the old hub into four cards and put its order
  book behind `data-researcher`; its topics' JS-filled entries are the research records
  themselves, rendered from the data, and no gate reads them for a visitor yet. What's New (js/changelog.js) is the release history Manager and the launcher parse,
  held by its own length budget, and is not rewritten after the fact.

THE RESEARCHER-MODE EXEMPTION (owner ruling 2026-10-16: strings shown only in Researcher
mode are exempt). Researcher mode itself is T-2657; this is the contract it builds on:

  - in the table, a key with a `researcher` segment — the `researcher` namespace
    (js/strings/researcher.js) or a key such as `guide.researcher.why-full` in an app's own
    section. js/strings/index.js exports isResearcherKey() so the page shows such a string
    only while Researcher mode is on;
  - in a page, any element carrying `data-researcher`, and everything inside it.
    css/skins.css (every page loads it) hides `[data-researcher]` until the root carries
    `data-researcher-mode`, so a marked element is off the visitor's screen today, before
    the switch exists, and the exemption cannot be used to hide a leak in plain sight.

THE ALLOWLIST, below, is for a leak another ticket owns the fix for. Each entry names the
surface, a pattern the finding must match, the reason and the owning ticket, and an entry
that matches nothing is itself a failure, so it comes out when its ticket lands.
"""

import argparse
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from compile_summaries import lint_string  # noqa: E402

WEB = ROOT / "renderers" / "web"
PAGES = [WEB / "index.html", WEB / "portal" / "index.html", WEB / "portal" / "pending.html"]
BUSINESSES = ROOT / "data" / "businesses" / "index.json"
SKINS = WEB / "css" / "skins.css"
HIDE_RULE = re.compile(r"html:not\(\[data-researcher-mode\]\)\s*\[data-researcher\]\s*\{\s*display:\s*none")

# Section 12's words. Whole words, either number, any case; "order book" across a line break.
WORDS = [
    (re.compile(r"\btiers?\b", re.IGNORECASE), "the word `tier` (a grade is Attested, Inferred or Reconstructed)"),
    (re.compile(r"\btickets?\b", re.IGNORECASE), "the word `ticket`"),
    (re.compile(r"\border[\s-]+books?\b", re.IGNORECASE), "the words `order book`"),
]

RESEARCHER = "researcher"
MARKER = "data-researcher"

# Each entry: surface, a regex the finding's "where: text" must match, why, and the ticket
# that owns the fix. An entry that matches nothing fails the gate (it is stale).
ALLOWLIST = [
    {"surface": "goto", "match": r"^businesses/index\.json biz_(chicago_post_office|cook_county_offices|"
                                 r"indian_agency_chicago|us_land_office_chicago) ",
     "ticket": "T-2657",
     "why": "Four authored civic-office records whose limit is a research ruling that cites research "
            "notes, exclusion ids and a file path. Rewording it here would drop the pointers a "
            "researcher follows; Researcher mode is where those ids and paths are shown."},
]


def is_researcher_key(key):
    return RESEARCHER in str(key).split(".")


def problems(text):
    """What in this string a visitor must never read."""
    found = list(lint_string(text))
    for pattern, what in WORDS:
        for m in pattern.finditer(text):
            found.append(f"{what} (`{m.group(0)}`)")
    return found


# ------------------------------------------------------------------- the surfaces

def table_strings(dump=None):
    """(where, text) for the string table and the app manifests, Researcher keys left out."""
    if dump is None:
        from check_strings import read_table
        dump = read_table()
    for key, value in list(dump["entries"]) + list(dump.get("apps", [])):
        if not is_researcher_key(key):
            yield f"{key}", value


VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param",
        "source", "track", "wbr"}
VISIBLE_ATTRS = ("title", "aria-label", "placeholder", "alt")
# An unclosed <li>, <p>, <option> … ends at the next sibling of its own kind, so a marked
# item cannot spread its exemption onto the items after it.
AUTO_CLOSE = {"li", "p", "dt", "dd", "option", "tr", "td", "th"}


class _Visible(HTMLParser):
    """The text a visitor can read on a static page, each piece with its line, skipping
    scripts, styles, comments and every element under a `data-researcher` marker."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []      # (tag, exempt)
        self.out = []        # (line, text)
        self.skip = 0        # inside <script>/<style>

    def exempt(self):
        return bool(self.stack) and self.stack[-1][1]

    def handle_starttag(self, tag, attrs):
        if tag in AUTO_CLOSE and self.stack and self.stack[-1][0] == tag:
            self.stack.pop()
        names = dict(attrs)
        exempt = self.exempt() or MARKER in names
        if tag in ("script", "style"):
            self.skip += 1
        if not exempt and not self.skip:
            for a in VISIBLE_ATTRS:
                if names.get(a):
                    self.out.append((self.getpos()[0], names[a]))
        if tag not in VOID:
            self.stack.append((tag, exempt))

    def handle_startendtag(self, tag, attrs):
        names = dict(attrs)
        if not (self.exempt() or MARKER in names or self.skip):
            for a in VISIBLE_ATTRS:
                if names.get(a):
                    self.out.append((self.getpos()[0], names[a]))

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.skip:
            self.skip -= 1
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        if self.skip or self.exempt() or not data.strip():
            return
        self.out.append((self.getpos()[0], " ".join(data.split())))


def page_strings(pages=PAGES):
    for path in pages:
        if not Path(path).is_file():
            continue
        parser = _Visible()
        parser.feed(Path(path).read_text(encoding="utf-8"))
        parser.close()
        for line, text in parser.out:
            yield f"{Path(path).name}:{line}", text


def goto_strings(index=None):
    """What the Go to list prints for each business row (js/destinations.js)."""
    if index is None:
        if not BUSINESSES.is_file():
            return
        index = json.loads(BUSINESSES.read_text(encoding="utf-8"))
    rows = index.get("businesses", []) if isinstance(index, dict) else index
    for b in rows:
        where = b.get("where") or {}
        rid = b.get("id", "?")
        for field, value in (("name", b.get("name")), ("trade", b.get("trade")), ("street", where.get("street"))):
            if isinstance(value, str) and value.strip():
                yield f"businesses/index.json {rid} {field}", value
        if b.get("present_at_scene_date") is not False and where.get("limit_reason"):
            yield f"businesses/index.json {rid} limit_reason", where["limit_reason"]


def lint(surfaces, allowlist=ALLOWLIST):
    """(failures, allowed, stale): each failure "surface | where: problem — in 'text'"."""
    failures, allowed, used = [], [], set()
    for surface, strings in surfaces:
        for where, text in strings:
            found = problems(text)
            if not found:
                continue
            subject = f"{where}: {text}"
            hit = next((i for i, a in enumerate(allowlist)
                        if a["surface"] == surface and re.search(a["match"], subject)), None)
            line = f"{surface} | {where}: {'; '.join(found)} — in {text[:90]!r}"
            if hit is None:
                failures.append(line)
            else:
                used.add(hit)
                allowed.append(f"{line} [allowed: {allowlist[hit]['ticket']}]")
    stale = [f"allowlist entry for {a['ticket']} ({a['surface']}: {a['match']}) matches nothing — "
             f"take it out" for i, a in enumerate(allowlist) if i not in used]
    return failures, allowed, stale


def contract_errors(css_text=None):
    """The exemption is honest only while a marked element is really hidden from a visitor."""
    if css_text is None:
        css_text = SKINS.read_text(encoding="utf-8") if SKINS.is_file() else ""
    if HIDE_RULE.search(css_text):
        return []
    return ["contract | css/skins.css no longer hides [data-researcher] while Researcher mode is off, "
            "so the marker would exempt text a visitor can read"]


def surfaces(dump=None, pages=PAGES, index=None):
    return [("table", list(table_strings(dump))), ("page", list(page_strings(pages))),
            ("goto", list(goto_strings(index)))]


# ------------------------------------------------------------------- self-test

def self_test():
    import tempfile
    failures = []

    def expect(cond, what):
        print(f"   {'ok  ' if cond else 'FAIL'} {what}")
        if not cond:
            failures.append(what)

    from check_strings import read_table
    dump = read_table()
    index = json.loads(BUSINESSES.read_text(encoding="utf-8")) if BUSINESSES.is_file() else {"businesses": []}
    base = surfaces(dump, PAGES, index)
    f, _, stale = lint(base)
    expect(not f and not stale, f"the committed visitor UI passes ({(f + stale)[:2]})")

    def planted_table(value, key="planted.string"):
        d = json.loads(json.dumps(dump))
        d["entries"].append([key, value])
        return lint(surfaces(d, PAGES, index))[0]

    for label, value, needle in [
        ("a file path", "See data/scenes/1835.json for more.", "file path"),
        ("a snake_case id", "Inspect glessner_house now.", "snake_case"),
        ("the word tier", "A tier 1 source.", "`tier`"),
        ("the word ticket", "Its own ticket will refine it.", "`ticket`"),
        ("the words order book", "Open the Order Book.", "`order book`"),
        ("a ticket number", "Fixed under T-2624.", "ticket number"),
    ]:
        expect(any(needle in e for e in planted_table(value)), f"{label} in the string table is refused")
    expect(not planted_table("See data/scenes/1835.json, tier 1.", key="researcher.planted"),
           "the same string under the researcher namespace is exempt")
    expect(not planted_table("ticket T-2624", key="guide.researcher.why"),
           "a researcher segment inside an app's own section is exempt")
    expect(planted_table("ticket", key="researchers.note"),
           "a namespace merely starting with `researcher` is not exempt")

    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "index.html"
        page.write_text(
            "<main><p>Fine words.</p>\n"
            "<p>Straight from <code>docs/LIBERTIES.md</code>.</p>\n"
            "<button title=\"Open the order book\">x</button>\n"
            "<img alt=\"tier_one\">\n"
            "<section data-researcher><p>ticket T-1 at data/x.json</p><br><b title=\"tier\">y</b></section>\n"
            "<div data-researcher title=\"order book\"></div>\n"
            "<p>After the marker: the tickets.</p>\n"
            "<script>const a = 'data/x.json';</script><style>.tier{}</style><!-- tier -->\n"
            "</main>", encoding="utf-8")
        got = lint([("page", list(page_strings([page])))], allowlist=[])[0]
        expect(any("index.html:2" in e and "file path" in e for e in got), "a path in a page's <code> is refused, with its line")
        expect(any("index.html:3" in e and "`order book`" in e for e in got), "a title attribute is read")
        expect(any("index.html:4" in e and "snake_case" in e for e in got), "an alt attribute is read")
        expect(not any(":5" in e or ":6" in e for e in got), "a data-researcher subtree and its own attributes are exempt")
        expect(any("index.html:7" in e and "`ticket`" in e for e in got), "the exemption ends with the marked element")
        expect(not any(":8" in e for e in got), "scripts, styles and comments are not visible text")

    def planted_goto(row):
        idx = json.loads(json.dumps(index))
        idx.setdefault("businesses", []).append(row)
        return lint(surfaces(dump, PAGES, idx))[0]

    expect(any("limit_reason" in e and "snake_case" in e for e in planted_goto(
        {"id": "biz_planted", "name": "A firm", "where": {"kind": "anchored", "limit_reason":
         "The register places this house against tremont_house_1 (action: new_building)."}})),
        "a Go to row's limit naming a structure id is refused (the T-2620 finding)")
    expect(not planted_goto({"id": "biz_gone", "name": "A firm", "present_at_scene_date": False,
                             "where": {"limit_reason": "against tremont_house_1"}}),
           "a firm not trading at the scene date is not read (its row says so instead)")
    expect(any(" name:" in e for e in planted_goto({"id": "biz_x", "name": "biz_x", "where": {}})),
           "a business named by its id is refused")

    f2, _, stale2 = lint(base, allowlist=ALLOWLIST + [{"surface": "page", "match": "^nothing-here$",
                                                       "ticket": "T-0000", "why": "planted"}])
    expect(any("T-0000" in s for s in stale2), "an allowlist entry that matches nothing is refused as stale")
    f3, _, _ = lint(base, allowlist=[])
    expect(bool(f3), "without the allowlist the leaks it holds are reported")
    expect(not contract_errors(), "css/skins.css hides a [data-researcher] element while Researcher mode is off")
    expect(bool(contract_errors(".x { display: none; }")), "a stylesheet without that rule is refused")
    expect(all(a.get("ticket", "").startswith("T-") and a.get("why") for a in ALLOWLIST),
           "every allowlist entry names its owning ticket and its reason")

    print(f"   {len(failures)} planted fault(s) got through" if failures else "   every planted fault refused")
    return 1 if failures else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true")
    g.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    found = surfaces()
    failures, allowed, stale = lint(found)
    failures += contract_errors()
    print("  read " + ", ".join(f"{len(s)} {name} string(s)" for name, s in found))
    for line in allowed:
        print(f"  allowed {line}")
    for line in failures + stale:
        print(f"FAIL {line}")
    if failures or stale:
        print(f"VISITOR UI FAIL — {len(failures)} leak(s), {len(stale)} stale allowlist entr(ies)")
        return 1
    print(f"VISITOR UI PASS — no path, id, snake_case, tier, ticket or order book a visitor reads "
          f"({len(allowed)} held by the allowlist for the ticket that owns the fix)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
