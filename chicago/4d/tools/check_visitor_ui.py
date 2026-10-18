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
  are research prose that T-2825 rewrites (no mode shows internal ids or ticket numbers,
  owner 2026-10-18), and the Evidence hub's JS-filled topics are the hub's fold into
  Guide › About this destination (T-2667). What's New (js/changelog.js) is the release history Manager and the launcher parse,
  held by its own length budget, and is not rewritten after the fact.

THE RESEARCHER-MODE EXEMPTION, AND HOW NARROW IT IS. The owner ruled on 2026-10-16 that
strings shown only in Researcher mode (T-2657) are exempt, and narrowed it on 2026-10-18:
"rewrite the records so you are not referring to internal ticket numbers or internal record
ids in researcher or educator mode", and "If in that mode you want to refer to the tickets as
a link or something as an external source or link back, ok, but I don't want to talk internal
ticket language to researchers." So a Researcher-mode string is READ like any other and may
carry exactly one thing a visitor's may not: the words "order book" (Researcher mode is where
the order book lives). It still refuses a path, a link, an id, snake_case, a ticket number,
"tier" and "ticket". A ticket may reach a researcher only as a LINK: an <a> whose href opens
it in kevinrhaas/chicago-tickets, behind a label in plain words, inside a `data-researcher`
element. A ticket link anywhere else is refused, and so is one whose label is empty.

Which strings are Researcher mode's:

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
# The one word a Researcher-mode string may carry that a visitor's may not.
RESEARCHER_ALLOWS = {"the words `order book`"}
# A link that opens a ticket: the tickets repository, or a ticket number in the address.
TICKET_HREF = re.compile(r"github\.com/kevinrhaas/chicago-tickets|\bT-\d{3,5}\b")

# Each entry: surface, a regex the finding's "where: text" must match, why, and the ticket
# that owns the fix. An entry that matches nothing fails the gate (it is stale).
ALLOWLIST = [
    {"surface": "page", "match": r"^index\.html:\d+: The order book: what the models say",
     "ticket": "T-2667",
     "why": "The Evidence hub's order-book topic. T-2667 folds the hub into Guide › About this "
            "destination and moves the order book behind Researcher mode."},
    {"surface": "goto", "match": r"^businesses/index\.json biz_(chicago_post_office|cook_county_offices|"
                                 r"indian_agency_chicago|us_land_office_chicago) ",
     "ticket": "T-2825",
     "why": "Four authored civic-office records whose limit is a research ruling that cites research "
            "notes, exclusion ids and a file path. The owner ruled on 2026-10-18 that no mode shows "
            "internal ids or ticket numbers, so Researcher mode does not hold them either: T-2825 "
            "rewrites the records themselves."},
]


def is_researcher_key(key):
    return RESEARCHER in str(key).split(".")


def problems(text, researcher=False):
    """What in this string a visitor must never read. `researcher`: a string only Researcher
    mode shows, which may carry the words "order book" and nothing else a visitor's may not."""
    found = list(lint_string(text))
    for pattern, what in WORDS:
        if researcher and what in RESEARCHER_ALLOWS:
            continue
        for m in pattern.finditer(text):
            found.append(f"{what} (`{m.group(0)}`)")
    return found


# ------------------------------------------------------------------- the surfaces

def table_strings(dump=None):
    """(where, text, researcher) for the string table and the app manifests."""
    if dump is None:
        from check_strings import read_table
        dump = read_table()
    for key, value in list(dump["entries"]) + list(dump.get("apps", [])):
        yield f"{key}", value, is_researcher_key(key)


VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param",
        "source", "track", "wbr"}
VISIBLE_ATTRS = ("title", "aria-label", "placeholder", "alt")
# An unclosed <li>, <p>, <option> … ends at the next sibling of its own kind, so a marked
# item cannot spread its exemption onto the items after it.
AUTO_CLOSE = {"li", "p", "dt", "dd", "option", "tr", "td", "th"}


class _Visible(HTMLParser):
    """The text a reader can see on a static page, each piece with its line and whether it
    sits under a `data-researcher` marker (Researcher mode's), skipping scripts, styles and
    comments; and every link that opens a ticket, with its label and the same flag."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []      # (tag, researcher)
        self.out = []        # (line, text, researcher)
        self.links = []      # [line, researcher, label] for each ticket link
        self.open_link = None
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
        if not self.skip:
            for a in VISIBLE_ATTRS:
                if names.get(a):
                    self.out.append((self.getpos()[0], names[a], exempt))
            if tag == "a" and TICKET_HREF.search(names.get("href") or ""):
                self.open_link = [self.getpos()[0], exempt, ""]
                self.links.append(self.open_link)
        if tag not in VOID:
            self.stack.append((tag, exempt))

    def handle_startendtag(self, tag, attrs):
        names = dict(attrs)
        if not self.skip:
            for a in VISIBLE_ATTRS:
                if names.get(a):
                    self.out.append((self.getpos()[0], names[a], self.exempt() or MARKER in names))

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.skip:
            self.skip -= 1
        if tag == "a":
            self.open_link = None
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        if self.skip or not data.strip():
            return
        text = " ".join(data.split())
        if self.open_link is not None:
            self.open_link[2] = f"{self.open_link[2]} {text}".strip()
        self.out.append((self.getpos()[0], text, self.exempt()))


def _parse(path):
    parser = _Visible()
    parser.feed(Path(path).read_text(encoding="utf-8"))
    parser.close()
    return parser


def page_strings(pages=PAGES):
    for path in pages:
        if not Path(path).is_file():
            continue
        for line, text, researcher in _parse(path).out:
            yield f"{Path(path).name}:{line}", text, researcher


def ticket_link_errors(pages=PAGES):
    """A ticket reaches a reader only as a link in Researcher mode, behind plain words
    (owner, 2026-10-18). Its label is linted with the page's other text."""
    errs = []
    for path in pages:
        if not Path(path).is_file():
            continue
        for line, researcher, label in _parse(path).links:
            where = f"link | {Path(path).name}:{line}"
            if not researcher:
                errs.append(f"{where}: a link to a ticket outside Researcher mode (a `data-researcher` element)")
            if not label:
                errs.append(f"{where}: a link to a ticket with no label in plain words")
    return errs


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
        for where, text, *flag in strings:
            found = problems(text, researcher=bool(flag and flag[0]))
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
    f += ticket_link_errors()
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
    # The owner, 2026-10-18 (T-2657): no internal ticket number or record id in any mode.
    expect(not planted_table("Open the order book.", key="researcher.planted"),
           "the words order book under the researcher namespace are allowed (Researcher mode holds it)")
    expect(not planted_table("The order book, bucket by bucket.", key="guide.researcher.why"),
           "and under a researcher segment inside an app's own section")
    for label, value, needle in [("a ticket number", "Fixed under T-2624.", "ticket number"),
                                 ("a snake_case id", "Inspect glessner_house.", "snake_case"),
                                 ("a file path", "See data/scenes/1835.json.", "file path"),
                                 ("the word ticket", "Its own ticket will settle it.", "`ticket`"),
                                 ("the word tier", "A tier 1 source.", "`tier`")]:
        expect(any(needle in e for e in planted_table(value, key="researcher.planted")),
               f"{label} in a Researcher-mode string is still refused")
    expect(planted_table("Open the order book.", key="researchers.note"),
           "a namespace merely starting with `researcher` is not Researcher mode's")

    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "index.html"
        page.write_text(
            "<main><p>Fine words.</p>\n"
            "<p>Straight from <code>docs/LIBERTIES.md</code>.</p>\n"
            "<button title=\"Open the order book\">x</button>\n"
            "<img alt=\"tier_one\">\n"
            "<section data-researcher><p>The order book.</p><br><b title=\"The order book\">y</b></section>\n"
            "<div data-researcher title=\"order book\"></div>\n"
            "<p>After the marker: the tickets.</p>\n"
            "<script>const a = 'data/x.json';</script><style>.tier{}</style><!-- tier -->\n"
            "</main>", encoding="utf-8")
        got = lint([("page", list(page_strings([page])))], allowlist=[])[0]
        expect(any("index.html:2" in e and "file path" in e for e in got), "a path in a page's <code> is refused, with its line")
        expect(any("index.html:3" in e and "`order book`" in e for e in got), "a title attribute is read")
        expect(any("index.html:4" in e and "snake_case" in e for e in got), "an alt attribute is read")
        expect(not any(":5" in e or ":6" in e for e in got),
               "a data-researcher subtree and its own attributes may name the order book")
        expect(any("index.html:7" in e and "`ticket`" in e for e in got), "the exemption ends with the marked element")
        expect(not any(":8" in e for e in got), "scripts, styles and comments are not visible text")

    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "index.html"
        page.write_text(
            "<main><section data-researcher><p>Seated by T-1198 at data/x.json.</p>\n"
            "<p><a href=\"https://github.com/kevinrhaas/chicago-tickets/blob/main/T-1000-1249/T-1198-x.md\">How this was decided</a></p>\n"
            "<p><a href=\"https://github.com/kevinrhaas/chicago-tickets/blob/main/T-1198.md\"></a></p></section>\n"
            "<p><a href=\"https://github.com/kevinrhaas/chicago-tickets/blob/main/T-1198.md\">The work record</a></p>\n"
            "<p><a href=\"https://example.org/x\">A source</a></p>\n"
            "<section data-researcher><a href=\"#T-1198\">T-1198</a></section></main>", encoding="utf-8")
        got = lint([("page", list(page_strings([page])))], allowlist=[])[0]
        links = ticket_link_errors([page])
        expect(any("index.html:1" in e and "ticket number" in e for e in got) and any("index.html:1" in e and "file path" in e for e in got),
               "a ticket number and a path in Researcher-mode text are refused")
        expect(not any(":2" in e for e in got + links),
               "a ticket as a link behind plain words, in Researcher mode, is allowed")
        expect(any(":3" in e and "no label" in e for e in links), "a ticket link with no label is refused")
        expect(any(":4" in e and "outside Researcher mode" in e for e in links), "a ticket link outside Researcher mode is refused")
        expect(not any(":5" in e for e in got + links), "a link to anything else is not a ticket link")
        expect(any(":6" in e and "ticket number" in e for e in got), "a ticket link labelled with its number is refused")

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
    failures += contract_errors() + ticket_link_errors()
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
