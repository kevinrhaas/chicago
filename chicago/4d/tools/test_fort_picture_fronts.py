#!/usr/bin/env python3
"""First-fort opt-in fronts: constructor compatibility and real support clearance."""
from dataclasses import asdict, replace
import inspect
import json
from pathlib import Path
import sys
import struct
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'generators'))

class NoBlender(ModuleType):
    def __getattr__(self, name):
        raise AssertionError('CPU fort test reached Blender runtime: ' + name)

sys.modules['bpy'] = NoBlender('bpy')
from archetypes.fort_structure_params import FortStructureParams, from_phase  # noqa: E402
from archetypes import fort_structure as fort  # noqa: E402
from common.mesh import MeshBuilder  # noqa: E402


def check_canopy_contact():
    """Measure the emitted support against the independent canopy polygon."""
    ids = ('north_range', 'officers_barracks', 'commanding_officers_barracks',
           'soldiers_barracks_sw', 'soldiers_barracks_se')
    f32 = lambda x: struct.unpack('<f', struct.pack('<f', x))[0]

    def vertical_residual(point, roof):
        a, b, c = roof[:3]
        u = tuple(y-x for x, y in zip(a, b))
        v = tuple(y-x for x, y in zip(a, c))
        n = (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2],
             u[0]*v[1]-u[1]*v[0])
        assert abs(n[2]) > 0
        return sum(k*(q-p) for k, p, q in zip(n, a, point))/n[2]

    for suffix in ids:
        record = json.loads((ROOT/'data/structures'/
                             ('first_fort_dearborn_'+suffix+'.json')).read_text())
        phase = next(p for p in record['phases'] if p['id'] == 'first_fort_1803')
        p = from_phase(phase, record)
        b = MeshBuilder('canopy-contact-'+suffix)
        fort._gallery_two_storeys(b, p, 1.0)
        roof = [b.verts[i] for i in b.faces[-1]]
        assert roof == [(0.0, p.depth_m, p.wall_height_m),
                        (p.width_m, p.depth_m, p.wall_height_m),
                        (p.width_m, p.depth_m+2.1+.15, p.wall_height_m-.45),
                        (0.0, p.depth_m+2.1+.15, p.wall_height_m-.45)]
        # Each unchanged post has five faces, with its foot open at the ground.
        first = len(fort._gallery_post_centres(p, .14))*5
        bottom = p.wall_height_m-.45-.14
        posts = [b.verts[i] for face in b.faces[:first] for i in face]
        assert min(v[2] for v in posts) == 0 and max(v[2] for v in posts) == bottom
        beam = [[b.verts[i] for i in face] for face in b.faces[first:first+5]]
        top = {v for face in beam for v in face if v[2] > bottom+1e-9}
        assert len(top) == 4
        assert max(abs(vertical_residual(v, roof)) for v in top) <= 1e-12, suffix
        # No duplicate coplanar timber face under the double-sided roof sheet.
        assert not any(all(abs(vertical_residual(v, roof)) <= 1e-12 for v in face)
                       for face in beam)
        # The next primitive is still the unchanged upper deck's bottom face.
        assert [b.verts[i] for i in b.faces[first+5]] == [
            (0.0, p.depth_m, p.storey_height_m-.14),
            (p.width_m, p.depth_m, p.storey_height_m-.14),
            (p.width_m, p.depth_m+2.1, p.storey_height_m-.14),
            (0.0, p.depth_m+2.1, p.storey_height_m-.14)]
        roof32 = [tuple(map(f32, v)) for v in roof]
        assert max(abs(vertical_residual(tuple(map(f32, v)), roof32)) for v in top) <= 2e-6
        # This geometric oracle rejects the original 30–58 mm separated beam.
        assert min(abs(vertical_residual((v[0], v[1], p.wall_height_m-.45), roof))
                   for v in top) >= .02999


def main():
    args = (13.35, 4.0, 'barracks', 2, 5.0, 'gable', 34.0, 'log',
            'unpainted', 2, True, False, 0.35, False, False, {})
    names = ('width_m', 'depth_m', 'kind', 'stories', 'wall_height_m',
             'roof_type', 'roof_pitch_deg', 'construction', 'paint',
             'chimneys', 'gallery', 'loopholes', 'upper_overhang_m',
             'sun_dial', 'lantern', 'confidence')
    p = FortStructureParams(*args)
    p.validate()
    assert p.__match_args__ == names
    assert all(getattr(p, name) == value for name, value in zip(names, args))
    signature = inspect.signature(FortStructureParams)
    for name in ('gallery_storeys', 'face_openings'):
        assert signature.parameters[name].kind == inspect.Parameter.KEYWORD_ONLY
    assert p.gallery_storeys == 1 and p.face_openings is None

    # An absent cover and a horizontal cover are different physical contracts.
    # The flat positive control prevents fixing none by dropping both branches.
    for roof_type in ('none', 'flat'):
        shell = replace(p, roof_type=roof_type)
        cover = MeshBuilder('cover-'+roof_type)
        assert fort._roof(cover, shell, 0.0, 0.0, 24.0, 15.0, 4.0, .5) == 4.0
        if roof_type == 'none':
            assert cover.verts == [] and cover.faces == []
        else:
            assert [[cover.verts[i] for i in face] for face in cover.faces] == [
                [(0.0, 0.0, 4.0), (0.0, 15.0, 4.0),
                 (24.0, 15.0, 4.0), (24.0, 0.0, 4.0)]]
            assert cover.mat_index == [fort.M_ROOF]


    # A five-bay front put the old centre support directly through the centre sash.
    holes = []
    for storey in (0.0, 2.5):
        for centre in (1.335, 4.005, 6.675, 9.345, 12.015):
            holes.append(dict(face='front', kind='window', u0=centre-.36,
                              u1=centre+.36, z0=storey+.65, z1=storey+2.05))
    explicit = replace(p, gallery_storeys=2, face_openings=holes)
    explicit.validate()
    centres = fort._gallery_post_centres(explicit, .14)
    assert len(centres) == 5 and centres[0] == 0 and centres[-1] == p.width_m
    assert 6.675 not in centres
    margin = .07 + fort.openings.CASING_W_M + fort.openings.SILL_HORN_M
    for centre in centres:
        for opening in holes:
            assert (centre <= opening['u0'] - margin + 1e-9
                    or centre >= opening['u1'] + margin - 1e-9)
    assert centres == fort._gallery_post_centres(explicit, .14)
    assert all(b-a >= .14-1e-9 for a, b in zip(centres, centres[1:]))

    old_grid = [p.width_m*i/4 for i in range(5)]
    for empty in (None, []):
        legacy = replace(explicit, face_openings=empty)
        assert fort._gallery_post_centres(legacy, .14) == old_grid

    # The disabled, old one-gallery builder never consults the new support logic.
    original = fort._gallery_post_centres
    def forbidden(*_args):
        raise AssertionError('disabled gallery path reached new support derivation')
    fort._gallery_post_centres = forbidden
    try:
        builder = MeshBuilder('legacy-fort-gallery')
        fort._gallery(builder, p, 1.0)
        assert builder.verts and builder.faces
    finally:
        fort._gallery_post_centres = original

    dense = replace(explicit, face_openings=[dict(face='front', kind='window',
                    u0=.01, u1=p.width_m-.01, z0=1.0, z1=2.0)])
    dense.validate()
    try:
        fort._gallery_post_centres(dense, .14)
    except ValueError:
        pass
    else:
        raise AssertionError('an impossible end support was silently placed across a hole')
    assert asdict(p)['face_openings'] is None
    check_canopy_contact()
    print('PASS fort fronts: legacy16 positionals/two keyword-only opt-ins; '
          'support clearance, deterministic count, empty-front/default fallback and refusal; '
          'all five canopy joints, unchanged roofs/posts/decks and Float32 contact')

if __name__ == '__main__':
    main()
