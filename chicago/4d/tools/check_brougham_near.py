# SPDX-License-Identifier: GPL-3.0-or-later
"""Read the exact V17 near delivery; no producer or browser is launched."""
from pathlib import Path
import json
from transport.brougham.check_near import check_near
ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
    print(json.dumps(check_near(ROOT/'renderers/web/transport/parked-brougham', ROOT/'tools/transport/brougham')))
