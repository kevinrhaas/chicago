# SPDX-License-Identifier: GPL-3.0-or-later
"""Flat gate entry so the existing isolation probe measures the C02 checker."""
from pathlib import Path
import runpy

if __name__ == '__main__':
    runpy.run_path(str(Path(__file__).parent / 'transport' / 'test_carriage_c02_door.py'),
                  run_name='__main__')
