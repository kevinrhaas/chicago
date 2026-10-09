"""Regression tests for unsafe evidence promotion and broken family membership."""
import copy
import unittest
from build_images import load_library, merge
from evidence_review import validate_reviews

class EvidenceReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records, errors, _ = merge(load_library())
        assert not errors, errors

    def changed(self, rid):
        records = copy.deepcopy(self.records)
        return records, next(r for r in records if r['id'] == rid)

    def test_complete_review(self):
        self.assertEqual(validate_reviews(self.records), [])
        records = [r for r in self.records if 'pa-1800-22' in r['building_ids']]
        self.assertEqual(len(records), 171)
        self.assertEqual(sum(r['evidence_review']['review_state'].startswith('unavailable') for r in records), 17)

    def test_quarantine_cannot_be_reclassified(self):
        for rid in ('a18-rba-lowe-glessner-stable-18th-c1900', 'a18-rba-mf-glessner-f69'):
            with self.subTest(rid=rid):
                records, r = self.changed(rid)
                r['evidence_review'].update(evidence_role='exterior reference', geometry_use='corroborate with dated evidence')
                self.assertTrue(any('quarantine' in e for e in validate_reviews(records)))

    def test_unavailable_image_cannot_be_geometry(self):
        records = copy.deepcopy(self.records)
        r = next(r for r in records if r.get('evidence_review', {}).get('review_state', '').startswith('unavailable'))
        r['evidence_review']['geometry_use'] = 'corroborate with dated evidence'
        self.assertTrue(any('unseen image' in e for e in validate_reviews(records)))

    def test_missing_review_fails(self):
        records, r = self.changed('a18-gh-florian-1948-ne-exterior')
        del r['evidence_review']
        self.assertTrue(any('missing' in e for e in validate_reviews(records)))

    def test_duplicate_family_must_be_reciprocal(self):
        records, r = self.changed('a18-rba-taylor-2135-glessner-ne')
        r['evidence_review']['family_members'].append('missing-source')
        self.assertTrue(any('inconsistent family' in e for e in validate_reviews(records)))

    def test_new_florian_views_are_link_only(self):
        for suffix in ('entry-curb', 'northeast-overall', 'courtyard-bow-chimney'):
            r = next(r for r in self.records if r['id'] == 'a18-gh-florian-1948-' + suffix)
            self.assertIsNone(r['local'])
            self.assertEqual(r['rights'], 'copyright — link only')
            self.assertEqual(r['evidence_review']['phase'], 'after target year')

if __name__ == '__main__': unittest.main()
