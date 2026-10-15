"""Generate/check the original Glessner foliage atlas from its shared numeric layout."""
import argparse
import hashlib
import io
import json
from pathlib import Path
from _glessner_lod import _geometry_modules

ROOT=Path(__file__).resolve().parents[1]


def generated():
    _,pm,_=_geometry_modules(ROOT)
    from archetypes.masonry_house_v4_vines import make_layout,draw_atlas,validate_spec
    record=json.loads((ROOT/'data/structures/glessner_house.json').read_text())
    phase=next(p for p in record['phases'] if p['id']=='as_built_1887')
    params=pm.from_phase(phase,record);spec=params.detail['vines']
    validate_spec(spec,params)
    plants=make_layout(params,spec);buffer=io.BytesIO();draw_atlas(plants,buffer)
    return buffer.getvalue(),plants


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true');args=parser.parse_args()
    data,plants=generated();path=ROOT/'assets/textures/glessner-v4/vines_atlas.png'
    if args.check:
        from PIL import Image
        expected=Image.open(io.BytesIO(data))
        actual=Image.open(path) if path.exists() else None
        if actual is None or actual.mode!=expected.mode or actual.size!=expected.size or actual.tobytes()!=expected.tobytes():
            raise SystemExit('Vine atlas stale: run python3 tools/generate_glessner_vines.py')
        data=path.read_bytes()  # PNG compressor versions do not change the artwork.
    else:path.write_bytes(data)
    print(('PASS' if args.check else 'WROTE')+': seven original vine studies, '+
          str(sum(len(p['leaves']) for p in plants))+' leaf polygons; '+
          str(len(data))+'bytes; SHA256 '+hashlib.sha256(data).hexdigest())
