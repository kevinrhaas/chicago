# SPDX-License-Identifier: GPL-3.0-or-later
"""Flat gate entry so isolation probes include the actual CLI hierarchy controls."""
from pathlib import Path
import runpy

if __name__ == '__main__':
    runpy.run_path(str(Path(__file__).parent / 'transport' / 'test_carriage_c02_door_hierarchy.py'),
                  run_name='__main__')
