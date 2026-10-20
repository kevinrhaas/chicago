#!/usr/bin/env python3
"""T-2668 — the visitor-UI lint's own parts, on fixtures (no node, no committed data):
what counts as a leak, the Researcher-mode exemption in the table and in a page, the Go to
rows it reads, and the allowlist's matching and staleness.

    python3 tools/test_check_visitor_ui.py
"""
import tempfile
import unittest
from pathlib import Path

import check_visitor_ui as v


class Problems(unittest.TestCase):
    def test_each_fault_is_named(self):
        cases = {
            "See docs/LIBERTIES.md": "file path",
            "Open glessner_house": "snake_case",
            "A Tier 1 source": "`tier`",
            "two tiers of pigeon holes": "`tier`",
            "its own ticket": "`ticket`",
            "the Order  Book": "`order book`",
            "order-book": "`order book`",
            "under T-2624": "ticket number",
        }
        for text, needle in cases.items():
            with self.subTest(text=text):
                self.assertTrue(any(needle in p for p in v.problems(text)), v.problems(text))

    def test_plain_words_pass(self):
        for text in ("Frontier town", "Ticketed? No.", "In order. A book of hours.", "Attested · 1835",
                     "Reconstructed from the sources under Sources."):
            with self.subTest(text=text):
                # "Ticketed" and "Frontier" are not the words; "order" and "book" apart are not "order book".
                self.assertEqual(v.problems(text), [])


class Exemption(unittest.TestCase):
    def test_researcher_keys(self):
        self.assertTrue(v.is_researcher_key("researcher.order-book"))
        self.assertTrue(v.is_researcher_key("guide.researcher.why"))
        self.assertFalse(v.is_researcher_key("researchers.note"))
        self.assertFalse(v.is_researcher_key("hud.tab.sources"))

    def test_table_flags_researcher_keys(self):
        # T-2657: a researcher key is read, flagged, not skipped.
        dump = {"entries": [["hud.a", "ticket"], ["researcher.b", "ticket"]], "apps": [["app.x.label", "Tier"]]}
        self.assertEqual([(k, r) for k, _, r in v.table_strings(dump)],
                         [("hud.a", False), ("researcher.b", True), ("app.x.label", False)])

    def test_researcher_may_name_the_order_book_and_nothing_else(self):
        # The owner, 2026-10-18: no internal ticket number or record id in researcher mode.
        self.assertEqual(v.problems("the order book", researcher=True), [])
        self.assertTrue(v.problems("the order book"))
        for text in ("under T-2624", "Open glessner_house", "See docs/LIBERTIES.md", "its own ticket", "a Tier 1 source"):
            with self.subTest(text=text):
                self.assertTrue(v.problems(text, researcher=True))

    def test_page_marker_covers_its_subtree_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "p.html"
            page.write_text('<div><p>one</p><aside data-researcher title="t"><p>two<img alt="a"></p>'
                            '<ul><li>three</li></ul></aside><p title="four">five</p></div>', encoding="utf-8")
            texts = [(t, r) for _, t, r in v.page_strings([page])]
        self.assertEqual(texts, [("one", False), ("t", True), ("two", True), ("a", True), ("three", True),
                                 ("four", False), ("five", False)])

    def test_unclosed_marked_item_does_not_spread(self):
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "p.html"
            page.write_text("<ul><li data-researcher>hidden<li>shown</ul>", encoding="utf-8")
            texts = [(t, r) for _, t, r in v.page_strings([page])]
        self.assertEqual(texts, [("hidden", True), ("shown", False)])

    def test_ticket_links(self):
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "p.html"
            page.write_text('<div data-researcher><a href="https://github.com/kevinrhaas/chicago-tickets/x">how this was decided</a></div>'
                            '<a href="https://github.com/kevinrhaas/chicago-tickets/y">the work record</a>', encoding="utf-8")
            errs = v.ticket_link_errors([page])
        self.assertEqual(len(errs), 1)
        self.assertIn("outside Researcher mode", errs[0])


class GoTo(unittest.TestCase):
    def test_rows(self):
        index = {"businesses": [
            {"id": "a", "name": "A & Co.", "trade": "grocer", "where": {"street": "Lake Street", "limit_reason": "No street."}},
            {"id": "b", "name": "B", "present_at_scene_date": False, "where": {"limit_reason": "against x_y"}},
        ]}
        got = list(v.goto_strings(index))
        self.assertIn(("businesses/index.json a limit_reason", "No street."), got)
        self.assertNotIn("businesses/index.json b limit_reason", [w for w, _ in got])


class Allowlist(unittest.TestCase):
    surfaces = [("page", [("index.html:9", "the order book"), ("index.html:10", "a ticket")])]

    def test_held_and_reported(self):
        allow = [{"surface": "page", "match": r"order book", "ticket": "T-1", "why": "w"}]
        failures, allowed, stale = v.lint(self.surfaces, allow)
        self.assertEqual(len(allowed), 1)
        self.assertEqual(len(failures), 1)
        self.assertIn("index.html:10", failures[0])
        self.assertEqual(stale, [])

    def test_surface_must_match(self):
        allow = [{"surface": "table", "match": r"order book", "ticket": "T-1", "why": "w"}]
        failures, _, stale = v.lint(self.surfaces, allow)
        self.assertEqual(len(failures), 2)
        self.assertEqual(len(stale), 1)

    def test_contract(self):
        self.assertEqual(v.contract_errors("html:not([data-researcher-mode]) [data-researcher] { display: none !important; }"), [])
        self.assertTrue(v.contract_errors(""))


if __name__ == "__main__":
    unittest.main(verbosity=1)
