# SPDX-License-Identifier: GPL-3.0-or-later
"""Explicit optional-study producer; never changes the original C02 baseline."""
import argparse
from apply_cushion import run_once
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--baseline',required=True);p.add_argument('--out',required=True);a=p.parse_args();run_once(a.baseline,a.out)
