# SPDX-License-Identifier: GPL-3.0-or-later
"""Read-only gate entrypoint for exact original W01 plus authored CC0 maps.

The isolation instrument keys top-level tools; keep production generation in
transport/ and expose only its --verify mode to the shared-tree gate.
"""
from pathlib import Path
import sys
from transport.generate_parked_wagon_fine_wood import main

ROOT = Path(__file__).resolve().parents[1]
if __name__ == '__main__':
    sys.argv = [__file__, '--parameters', str(ROOT/'data/transport/parked/wagon-w01.json'),
                '--output-dir', str(ROOT/'renderers/web/transport/parked-wagon-fine-wood'), '--verify']
    main()
