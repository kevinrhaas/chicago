#!/usr/bin/env python3
"""Regressions found while reconciling PRs #1033 and #971 (T-0976)."""
import copy
import unittest
from unittest.mock import patch

import mint_civic_residents as mint
import synthesize_resident_research as synthesis
import consolidate_resident_evidence as consolidation


class ReconciliationTests(unittest.TestCase):
    def test_uncertain_contraction_does_not_create_a_rival_full_forename(self):
        self.assertEqual(consolidation.split_name("Alex[r]. Loyd"),
                         consolidation.split_name("Alexander Loyd"))

    def test_matched_abbreviation_keeps_the_established_card(self):
        previous = {"id": "hh_loyd_alexander", "persons": [
            {"id": "loyd_alexander", "name": "Alexander Loyd"}]}
        row = mint._row(name="A Loyd", canonical_person_id="loyd_alexander")
        doc = mint.record(row, [mint._app()], {}, set(), previous)
        self.assertEqual(doc["id"], "hh_loyd_alexander")
        self.assertEqual(doc["persons"][0]["id"], "loyd_alexander")
        self.assertEqual(doc["persons"][0]["name"], "Alexander Loyd")
        # A different canonical person cannot borrow that card's identity.
        row["canonical_person_id"] = "someone_else"
        fresh = mint.record(row, [mint._app()], {}, set(), previous)
        self.assertEqual(fresh["persons"][0]["name"], "A Loyd")

    def test_occupation_refusals_from_pr971_keep_the_dated_pointer(self):
        cases = [
            (["fergus_chicago_directory_1839", "norris_chicago_directory_1843"],
             "Bailey, Bennett, carpenter and builder. Carried as 1837 and 1839 evidence; the 1835 grade does not move."),
            (["fergus_chicago_directory_1839"],
             "Chapman, Charles II., real estate dealer, where II. is the printer's H.")]
        for sources, summary in cases:
            with self.subTest(summary=summary):
                occupation = {"value": "none_recorded", "later_occupation": {"year": 1839}}
                person = {"id": "fixture", "occupation": copy.deepcopy(occupation)}
                refusals = []
                synthesis.promote(person, {}, {"ticket": "T-0976", "sources": sources,
                                              "summary": summary}, refusals)
                self.assertEqual(person["occupation"], occupation)
                self.assertTrue(refusals)

    def test_trade_source_must_cover_the_scene_year(self):
        # PR #971's positive fixture used 1834 alone. That is not an 1835
        # attestation under dev's stronger rule. Keep that guard, and test both sides.
        for date, allowed in [("1834", False), ("1839", False), ("", False),
                              ("1835", True), ("1833–1836", True)]:
            with self.subTest(date=date), patch.object(synthesis, "source_doc", return_value={"describes_date": date}):
                person = {"id": "fixture", "occupation": {"value": "none_recorded"}}
                refusals = []
                synthesis.promote(person, {}, {"ticket": "T-0976", "sources": ["fixture"],
                                              "summary": "He is a blacksmith."}, refusals)
                self.assertEqual(person["occupation"]["value"], "blacksmith" if allowed else "none_recorded")
                self.assertEqual(bool(refusals), not allowed)


if __name__ == "__main__":
    unittest.main()
