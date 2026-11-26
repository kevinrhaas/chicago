#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Import boundary checks: rights, source changes, EXIF crops and immutable town data."""
import json
import pathlib
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
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

    def test_child_requires_its_own_texture_only_path(self):
        with patch.object(P,'ROOT',self.root):
            child={**self.entry(),'age':7,'population':'child','texture_only':True}
            P.validate_entry(child)
            for change in ({'texture_only':False},{'age':1},{'age':18},{'fitted':{'values':{'head_shape':.8}}}):
                with self.assertRaises(ValueError):P.validate_entry({**child,**change})

    def test_identical_atlases_share_a_file_and_remove_the_previous_copy(self):
        image=Image.new('RGB',(128,128),(90,70,50));shared={}
        crowd=P.save_texture(image,self.root,'faces_light.jpg',shared)
        (self.root/'page_00_face_light.jpg').write_bytes(b'previous build copy')
        review=P.save_texture(image,self.root,'page_00_face_light.jpg',shared)
        self.assertEqual(crowd,review)
        self.assertFalse((self.root/'page_00_face_light.jpg').exists())
        self.assertTrue((self.root/crowd['file']).exists())
        self.assertEqual(P.save_texture(image,self.root,'faces_light.jpg',shared),crowd)
        distinct=P.save_texture(Image.new('RGB',(128,128),(30,40,90)),self.root,'different.jpg',shared)
        self.assertNotEqual(distinct['file'],crowd['file'])
        self.assertTrue((self.root/distinct['file']).exists())

    def test_forehead_lighting_joins_without_losing_photo_detail(self):
        # A photograph lit differently from the surrounding skin: the old narrow
        # fade made its upper hull edge a visible horizontal forehead band.
        size = 240
        covered = np.zeros((size, size), dtype=bool)
        covered[48:224, 24:216] = True
        skin = np.broadcast_to(np.array([110, 76, 53], dtype=np.uint8), (size, size, 3)).copy()
        photo = np.broadcast_to(np.array([175, 130, 95], dtype=np.uint8), skin.shape).copy()
        y, x = np.indices((size, size))
        detail = np.where(((x + y) % 2)[100:164, 84:156, None], 20, -20)
        photo[100:164, 84:156] = photo[100:164, 84:156] + detail
        alpha = np.minimum(1, P.distance_transform_edt(covered) / 6)[..., None]
        former = np.uint8(photo * alpha + skin * (1 - alpha))
        joined = P.blend_face_photo(photo, skin, covered)
        old_edge = P.L.linear(former)[35:75, 120, 0]
        new_edge = P.L.linear(joined)[35:75, 120, 0]
        self.assertLess(np.abs(np.diff(new_edge)).max(), np.abs(np.diff(old_edge)).max() * .25)
        self.assertLess(np.abs(np.diff(new_edge, n=2)).max(), np.abs(np.diff(old_edge, n=2)).max() * .25)
        core = (slice(112, 152), slice(96, 144), 0)
        self.assertGreater(P.L.linear(joined)[core].std(), P.L.linear(photo)[core].std() * .95,
                           'smoothing the whole face would erase its photographic detail')

    def test_photo_blending_preserves_identical_skin_and_uncovered_skin(self):
        rng = np.random.default_rng(3769)
        skin = rng.integers(0, 256, (96, 96, 3), dtype=np.uint8)
        photo = np.full_like(skin, 180)
        empty = np.zeros(skin.shape[:2], dtype=bool)
        self.assertTrue(np.array_equal(P.blend_face_photo(photo, skin, empty), skin))
        covered = empty.copy(); covered[15:82, 15:82] = True
        self.assertTrue(np.array_equal(P.blend_face_photo(skin, skin, covered), skin))


if __name__=='__main__':
    unittest.main()
