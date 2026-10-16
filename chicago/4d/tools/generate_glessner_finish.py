"""Generate or check original joint maps for Glessner's plain brick surfaces."""
import argparse
import hashlib
import json
from pathlib import Path
from _glessner_lod import _geometry_modules

ROOT=Path(__file__).resolve().parents[1]


def generated():
    _geometry_modules(ROOT)
    from archetypes.masonry_house_v4_finish import maps
    record=json.loads((ROOT/'data/structures/glessner_house.json').read_text())
    phase=next(p for p in record['phases'] if p['id']=='as_built_1887')
    return maps(ROOT/'assets/textures/glessner-v4',phase['form']['surface_finish']['value'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true');args=parser.parse_args()
    from PIL import Image
    for suffix,expected in generated().items():
        path=ROOT/f'assets/textures/glessner-v4/flat_brick_{suffix}.png'
        if args.check:
            actual=Image.open(path) if path.exists() else None
            if actual is None or actual.mode!=expected.mode or actual.size!=expected.size or actual.tobytes()!=expected.tobytes():
                raise SystemExit('Plain brick map stale: run python3 tools/generate_glessner_finish.py')
        else:expected.save(path)
        print(('PASS' if args.check else 'WROTE')+f': {path.name}: {path.stat().st_size} bytes; '+hashlib.sha256(path.read_bytes()).hexdigest())
