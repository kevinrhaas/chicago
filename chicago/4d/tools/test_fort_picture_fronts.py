#!/usr/bin/env python3
"""First-fort opt-in fronts: constructor compatibility and real support clearance."""
from dataclasses import asdict, replace
import inspect
from pathlib import Path
import sys
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'generators'))

class NoBlender(ModuleType):
    def __getattr__(self, name):
        raise AssertionError('CPU fort test reached Blender runtime: ' + name)

sys.modules['bpy'] = NoBlender('bpy')
from archetypes.fort_structure_params import FortStructureParams  # noqa: E402
from archetypes import fort_structure as fort  # noqa: E402
from common.mesh import MeshBuilder  # noqa: E402


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
    print('PASS fort fronts: legacy16 positionals/two keyword-only opt-ins; '
          'support clearance, deterministic count, empty-front/default fallback and refusal')

if __name__ == '__main__':
    main()
