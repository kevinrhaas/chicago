# SPDX-License-Identifier: GPL-3.0-or-later
"""Reproduce the original parked1904 C02 material variant from the baseline GLB."""
from pathlib import Path
import argparse
import subprocess
import sys
import tempfile


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():
        parser.error('Fresh output directory required')
    tools=Path(__file__).resolve().parent
    with tempfile.TemporaryDirectory(prefix='c02-parked-source-') as temp:
        cushion=Path(temp)/'cushion'
        subprocess.run([sys.executable,str(tools/'c02_cushion/produce.py'),
            '--baseline',str(args.baseline.resolve()),'--out',str(cushion)],check=True)
        subprocess.run([sys.executable,str(tools/'refine_carriage_finish.py'),
            '--input',str(cushion/'carriage-c02.glb'),'--output',str(args.output.resolve())],check=True)


if __name__=='__main__':
    main()
