#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Import boundary checks: rights, source changes, EXIF crops and immutable town data."""
import json
import copy
import pathlib
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image
import photo_face_library as P
import photo_reference_fit as R


class ImportBoundaries(unittest.TestCase):
    def test_monochrome_scan_exposure_is_not_eye_white_albedo(self):
        import historical_photo_shape as H
        entry={'sex':'female','historical':{'monochrome':True,'stand_in':{'label':'STAND-IN'},
                            'before_hair_rgb':[.08,.05,.03],'limits':[]}}
        corrected=[]
        for exposure in (.03,.85):
            face={'eyes':{'sclera_linear':[exposure]*3,'iris_linear':[.05]*3,'lid_rest':.1},
                  'hair_projection':{},'limits':[]}
            before=copy.deepcopy(entry)
            with patch.object(P,'native_iris_tone',return_value=np.array([.05,.04,.03])):
                H.appearance(face,entry,{'base_body':P.BASE['female']})
            corrected.append(face['eyes']['sclera_linear'])
            self.assertTrue(all(.4<=v<=.55 for v in corrected[-1]))
            self.assertGreater(corrected[-1][0],corrected[-1][2])
            self.assertEqual(entry,before)
        self.assertEqual(*corrected,'paper exposure must not darken or bleach the relit eye')

    def test_archive_skin_restoration_preserves_features_and_source(self):
        entry=next(e for e in json.loads(P.PILOT.read_text())['faces'] if e['id']=='ref_european_01_10')
        points=np.asarray(entry['landmarks']);rng=np.random.default_rng(3762)
        tone=np.array([.4,.27,.18]);noise=rng.uniform(.65,1.35,(313,313,1))
        photo=Image.fromarray(P.L.srgb8(tone*noise));before=np.asarray(photo).copy()
        after=np.asarray(P.restore_archive_skin(photo,points,.2))
        x,y=np.int64(points[50]);region=np.s_[y-4:y+5,x-4:x+5]
        self.assertLess(after[region][:,:,0].std(),before[region][:,:,0].std()*.5)
        self.assertLess(abs(float(after[region][:,:,0].mean()-before[region][:,:,0].mean())),10)
        for i in (70,300,33,263,0,17,98,327):
            x,y=np.int64(points[i]);np.testing.assert_array_equal(after[y,x],before[y,x])
        np.testing.assert_array_equal(np.asarray(photo),before)
        self.assertIs(P.restore_archive_skin(photo,points,1),photo)
        for value in (-.1,1.1,True,float('nan'),'smooth'):
            with self.assertRaises(ValueError):P.restore_archive_skin(photo,points,value)

    def test_lip_registration_tightens_painted_bounds_without_moving_other_features(self):
        target=np.array([[.90,.5],[.94,.5],[.92,.46],[.92,.54],[.84,.5]])
        members=[[0],[17],[61],[291],[4]];before=target.copy()
        out=P.mouth_uv_registration(target,members,{'lip_height_scale':.7,'lip_width_scale':.95})
        self.assertAlmostEqual(np.linalg.norm(out[1]-out[0]),.028)
        self.assertAlmostEqual(np.linalg.norm(out[3]-out[2]),.076)
        np.testing.assert_array_equal(out[4],before[4],'nose registration stays fixed')
        np.testing.assert_array_equal(target,before,'the calibrated UV source stays immutable')
        self.assertIs(P.mouth_uv_registration(target,members,None),target)
        self.assertIs(P.mouth_uv_registration(target,members,{'lip_height_scale':1}),target)
        for value in [True,.49,1.21,float('nan'),'small']:
            with self.assertRaises(ValueError):P.mouth_uv_registration(target,members,{'lip_height_scale':value})

    def test_fictional_child_pigment_softens_without_repainting_features(self):
        entry=next(e for e in json.loads(P.PILOT.read_text())['faces'] if e['id']=='ref_european_01_10')
        points=np.asarray(entry['landmarks'])
        for tone in ([.5,.3,.2],[.13,.07,.04]):
            rgb=np.broadcast_to(tone,(313,313,3)).copy()
            x,y=np.int64(points[50]);rgb[y-1:y+2,x-1:x+2]=np.array(tone)*.3
            features=[]
            for i in [0,70,107,133,300,336,362]:
                a,b=np.int64(points[i]);rgb[b-1:b+2,a-1:a+2]=np.array(tone)*.1;features.append((a,b))
            photo=Image.fromarray(P.L.srgb8(rgb));before=np.asarray(photo).copy()
            result,strength=P.soften_fictional_child_skin(photo,points,8);after=P.L.linear(np.asarray(result))
            self.assertEqual(strength,.7)
            self.assertGreater(after[y,x,0],tone[0]*.65,'dense pigment remains subtle rather than reading as dirt')
            for a,b in features:
                np.testing.assert_array_equal(np.asarray(result)[b-1:b+2,a-1:a+2],before[b-1:b+2,a-1:a+2])
            np.testing.assert_array_equal(np.asarray(photo),before)

    def test_unpictured_skin_cannot_carry_eyes_hair_or_background(self):
        entry=next(e for e in json.loads(P.PILOT.read_text())['faces'] if e['id']=='ref_european_01_10')
        points=np.asarray(entry['landmarks']);tone=np.array([.5,.3,.2])
        rgb=np.broadcast_to(tone,(313,313,3)).copy()
        distance,_,_,_,_,_=P.skin_support(rgb,points)
        rgb[distance==0]=.95  # bright source background, not forehead skin
        for i in [70,300,0]:
            x,y=np.int64(points[i]);rgb[y-1:y+2,x-2:x+3]=.003  # brows/lips
        before=rgb.copy();field=P.reference_skin_field(rgb,points)
        np.testing.assert_allclose(field,np.broadcast_to(tone,field.shape),atol=1e-6)
        np.testing.assert_array_equal(rgb,before,'continuation never edits the source')

    def test_face_edge_hair_is_not_stretched_over_the_cheek(self):
        # Use the real UV portrait's landmarks, but known flat skin and a dark
        # edge curl. Check both relative contrasts, without choosing a skin hue.
        entry=next(e for e in json.loads(P.PILOT.read_text())['faces'] if e['id']=='ref_european_01_10')
        points=np.asarray(entry['landmarks']);size=(313,313)
        for tone in ([.5,.3,.2],[.13,.07,.04]):
            rgb=np.broadcast_to(tone,(*size,3)).copy()
            distance,_,eye,margin,_,_=P.skin_support(rgb,points)
            yy,xx=np.indices(size)
            curl=(distance>0)&(distance<margin*.9)&(yy>points[33,1])&(yy<points[61,1])
            rgb[curl]=np.array(tone)*.05
            # Actual features safely inside the outline are retained.
            x,y=np.int64(points[0]);rgb[y-1:y+2,x-2:x+3]=np.array(tone)*.3
            photo=Image.fromarray(P.L.srgb8(rgb));before=np.asarray(photo).copy()
            after=np.asarray(P.photo_skin_edges(photo,points))
            self.assertTrue(curl.any())
            self.assertGreater(P.L.linear(after[curl]).mean(),np.mean(tone)*.8,'edge hair becomes the same reference skin')
            np.testing.assert_array_equal(after[y-1:y+2,x-2:x+3],before[y-1:y+2,x-2:x+3])
            np.testing.assert_array_equal(np.asarray(photo),before,'the source photograph is immutable')

    def test_photo_forehead_does_not_paint_bangs_on_the_skin(self):
        # Same relative hair/skin contrast on light and dark skin. The cleanup
        # takes its replacement from the person's own skin, not a fixed colour.
        for skin in ([.5,.3,.2],[.13,.07,.04]):
            rgb=np.full((100,100,3),skin,dtype=float)
            points=[[50,75]for _ in range(478)]
            boundary=(10,338,297,332,284,251,389,300,293,334,296,336,
                      107,66,105,63,70,162,21,54,103,67,109)
            corners=[[15,10],[85,10],[85,55],[15,55]]
            for k,i in enumerate(boundary):points[i]=corners[min(3,k*4//len(boundary))]
            rgb[20:48,45:49]=np.array(skin)*.08  # a fringe down the forehead
            rgb[62:65,25:40]=.005               # eyebrow below the forehead
            rgb[30,25]=np.array(skin)*.2        # an isolated natural freckle
            before=rgb.copy();after=P.clean_reference_forehead(rgb,points)
            self.assertTrue(np.array_equal(rgb,before),'input/source pixels are immutable')
            np.testing.assert_allclose(after[28:40,46],np.tile(skin,(12,1)),atol=.01)
            np.testing.assert_array_equal(after[62:65,25:40],before[62:65,25:40])
            np.testing.assert_array_equal(after[30,25],before[30,25])

    def test_blue_reference_iris_is_not_limited_to_the_stock_brown_channels(self):
        image=np.full((110,170,3),[195,191,187],dtype=np.uint8)
        points=[[85,55]for _ in range(478)]
        for outer,inner,upper,lower,centre,cx in [(33,133,159,145,468,55),(263,362,386,374,473,115)]:
            points[outer]=[cx-15,55];points[inner]=[cx+15,55]
            points[upper]=[cx,51];points[lower]=[cx,59];points[centre]=[cx,55]
            image[49:62,cx-6:cx+7]=[90,130,165]
        for start,cx in [(469,55),(474,115)]:
            for i,xy in enumerate([(cx-6,55),(cx,49),(cx+6,55),(cx,61)]):points[start+i]=list(xy)
        with patch.object(P,'measured_lid_rest',return_value=None):
            eyes=P.eye_appearance(Image.fromarray(image),points,'female',{'camera':{'px_per_m':1000}},{'base_body':P.BASE['female']})
        native=P.native_iris_tone('female')
        np.testing.assert_allclose(native*np.array(eyes['iris_gain']),eyes['iris_linear'],rtol=1e-12)
        self.assertGreater(eyes['iris_gain'][2],20,'the low-blue stock texture needs a larger gain to reproduce a blue iris')

    def test_reference_albedo_reduces_studio_shading_without_recolouring_skin(self):
        size=128;points=[[64,64]for _ in range(478)];points[468]=[44,60];points[473]=[84,60]
        for i,x in zip((50,101,118,205,280,330,347,425),(35,45,52,60,68,76,84,94)):points[i]=[x,80]
        flat=Image.new('RGB',(size,size),(145,113,95))
        self.assertTrue(np.array_equal(np.asarray(P.reference_albedo(flat,points)),np.asarray(flat)))
        y,x=np.indices((size,size));light=np.exp((x-64)*.009)*(1+np.where((x+y)%2,.03,-.03))
        rgb=np.array([.4,.25,.17])*light[...,None];photo=Image.fromarray(P.L.srgb8(rgb))
        before=P.L.linear(np.asarray(photo));after=P.L.linear(np.asarray(P.reference_albedo(photo,points)))
        a=P.gaussian_filter(before[:,:,0],5);b=P.gaussian_filter(after[:,:,0],5)
        self.assertLess(b[:,16:-16].std(),a[:,16:-16].std()*.65,'broad lighting is reduced before relighting')
        np.testing.assert_allclose(after[16:-16,16:-16,1]/after[16:-16,16:-16,0],before[16:-16,16:-16,1]/before[16:-16,16:-16,0],rtol=.025)
        fine_a=(before[:,:,0]/a)[16:-16,16:-16].std();fine_b=(after[:,:,0]/b)[16:-16,16:-16].std()
        self.assertGreater(fine_b,fine_a*.9,'fine photographic detail remains')

    def test_reference_solver_derivative_matches_finite_differences(self):
        from scipy.optimize._numdiff import approx_derivative
        rng=np.random.default_rng(3762)
        base=rng.normal(size=(12,3))*.05+[0,1.5,.1]
        pos=rng.normal(size=(3,12,3))*.008
        neg=rng.normal(size=(3,12,3))*.008
        observed=rng.normal(size=(12,2))*30+150
        sigma=np.linspace(2,5,12);centre=np.array([.1,-.2,.05]);spreads=np.array([.2,.3,.4])
        residual,jacobian,state=R.objective(base,pos,neg,observed,sigma,centre,spreads)
        p=np.array([.12,-.18,.07,900,155,144,.25,-.3,.2])
        np.testing.assert_allclose(jacobian(p),approx_derivative(residual,p),rtol=2e-6,atol=1e-7)
        rotation,_=R.rotation(*p[:3])
        np.testing.assert_allclose(rotation,P.F.rot(*p[:3]),atol=1e-15)
        delta=np.einsum('a,aij->ij',p[6:],np.where((p[6:]>=0)[:,None,None],pos,-neg))
        X=(base+delta-base.mean(0))@P.F.rot(*p[:3]).T
        pixels=np.column_stack((p[4]+p[3]*X[:,0],p[5]-p[3]*X[:,1]))
        np.testing.assert_allclose(residual(p),np.r_[((pixels-observed)/sigma[:,None]).ravel(),(p[6:]-centre)/spreads])

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
        for faces in ([self.entry()]*2,[{**self.entry(),'id':f'face_{i}'} for i in range(P.LIMIT+1)]):
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
