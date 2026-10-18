#!/usr/bin/env python3
"""Rebuild the original, unpublished-quality transport studies from JSON inputs."""
import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--only', choices=['wagon', 'carriage', 'horse', 'harness'])
parser.add_argument('--output-dir', type=Path, default=ROOT / 'renderers/web/transport')
args = parser.parse_args()
for name in ([args.only] if args.only else ['wagon', 'carriage', 'horse', 'harness']):
    subprocess.run([
        sys.executable, str(Path(__file__).with_name(f'generate_{name}.py')),
        '--parameters', str(ROOT / 'data/transport/studies' / f'{name}.json'),
        '--output-dir', str(args.output_dir / name),
    ], check=True)
