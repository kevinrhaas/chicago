# SPDX-License-Identifier: GPL-3.0-or-later
"""Physical master, exact optical regeneration and source policy; no browser."""
from pathlib import Path
import json
import subprocess
from transport.brougham.check_near import check_near
from transport.brougham.check_mid import verify as check_mid
from transport.brougham.optical_delivery import verify as check_optical
ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
    print(json.dumps(check_near(ROOT/'renderers/web/transport/parked-brougham', ROOT/'tools/transport/brougham')))
    print(json.dumps(check_mid()))
    print(json.dumps(check_optical()))
    # These CPU-only contracts unblock the actual T-3084 published parcel.
    # They read the real source and use only owned temporary regeneration output.
    subprocess.run(['node', str(ROOT/'tools/transport/brougham/check_full_policy.mjs')], check=True)
    subprocess.run(['node', str(ROOT/'tools/test_people_directory_probe.mjs')], check=True)
