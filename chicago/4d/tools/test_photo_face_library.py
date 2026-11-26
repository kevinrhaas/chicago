#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Import boundary checks: rights, source changes, EXIF crops and immutable town data."""
import json
import pathlib
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image
import photo_face_library as P


class ImportBoundaries(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        (self.root/'data/sources').mkdir(parents=True)
        self.source = self.root/'data/sources/test.json'
        self.source.write_text(json.dumps({'rights_status':'cleared','asset_use':'texture','url':'https://example.org/portrait'}))

    def tearDown(self):
        self.tmp.cleanup()

    def entry(self):
        return {'id':'sample','sex':'male','age':40,'source':'test','photo':'portrait.jpg','photo_sha256':'wrong'}

    def test_missing_or_uncleared_source(self):
        with patch.object(P,'ROOT',self.root):
            with self.assertRaises(FileNotFoundError): P.source_record('missing')
            for change in ({'rights_status':'check_required'},{'asset_use':'geometry'},{'url':'file:///unknown'}):
                rec=json.loads(self.source.read_text());rec.update(change);self.source.write_text(json.dumps(rec))
                with self.assertRaises(ValueError): P.source_record('test')
            with self.assertRaises(ValueError): P.source_record('../outside')

    def test_source_replacement_fails_before_output(self):
        Image.new('RGB',(200,200)).save(self.root/'portrait.jpg')
        out=self.root/'review'
        with patch.object(P,'ROOT',self.root):
            with self.assertRaisesRegex(ValueError,'source photo changed'):
                P.build({'faces':[self.entry()]},out)
        self.assertFalse(out.exists(),'no partial output from a failed batch preflight')

    def test_orientation_is_applied_before_crop(self):
        image=Image.new('RGB',(200,300))
        exif=Image.Exif();exif[274]=6
        path=self.root/'oriented.jpg';image.save(path,exif=exif)
        self.assertEqual(P.read_photo(path).size,(300,200))
        self.assertEqual(P.read_photo(path,[100,0,300,200]).size,(200,200))
        for crop in ([-1,0,200,200],[0,0,301,200],[0,0,200,201],[0,0,100,100]):
            with self.assertRaises(ValueError):P.read_photo(path,crop)

    def test_duplicate_ids_and_capacity_fail_before_output(self):
        for faces in ([self.entry()]*2,[{**self.entry(),'id':f'face_{i}'} for i in range(257)]):
            with self.assertRaises(ValueError):P.build({'faces':faces},self.root/'review')
        self.assertFalse((self.root/'review').exists())

    def test_only_calibrated_adult_faces(self):
        with patch.object(P,'ROOT',self.root):
            for change in ({'age':12},{'age':101},{'sex':'unknown'},{'id':'../../resident'}):
                with self.assertRaises(ValueError):P.validate_entry({**self.entry(),**change})


if __name__=='__main__':
    unittest.main()
