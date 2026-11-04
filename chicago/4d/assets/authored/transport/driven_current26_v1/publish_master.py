#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
from pathlib import Path
import argparse,hashlib,json
p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args()
s=Path(__file__).with_name('horse-current26-inplace-master.glb');b=s.read_bytes()
assert hashlib.sha256(b).hexdigest()=='ad9dc060f8630d0de04fef97d716e8c82be3ac8bf070684e78107720c5221ec6'
o=Path(a.output);o.parent.mkdir(parents=True,exist_ok=True);o.write_bytes(b)
print(json.dumps({'output':str(o),'bytes':len(b),'sha256':hashlib.sha256(o.read_bytes()).hexdigest()}))
