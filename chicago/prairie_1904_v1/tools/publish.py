#!/usr/bin/env python3
"""Publish only the small, cleared research browser; archives stay off Pages."""
from pathlib import Path
import shutil,sys
P=Path(__file__).resolve().parents[1]
R=P.parents[1]
args=[a for a in sys.argv[1:] if not a.startswith('--')]
destination=Path(args[0]).resolve() if args else R/'site/prairie-1904'
# --no-image-files: the /4d/ dev-preview mirror leaves the image derivatives out — they are
# ~35 MB that tools/site_budget.py counts against the 4D tree's 256 MB budget, and the
# viewer shows each from its holder's own URL when the local copy is absent (T-1821).
image_files='--no-image-files' not in sys.argv
destination.mkdir(parents=True,exist_ok=True)
for name in ['viewer','data','maps','docs']:
 shutil.copytree(P/name,destination/name,dirs_exist_ok=True)
# Only government HABS reports/drawings explicitly selected for the public subset.
if (P/'research/public').exists():shutil.copytree(P/'research/public',destination/'research/public',dirs_exist_ok=True)
# Derivatives of public-domain / no-known-restrictions images only (research/images/README.md).
if image_files and (P/'research/images/files').exists():shutil.copytree(P/'research/images/files',destination/'research/images/files',dirs_exist_ok=True)
print('Prairie Avenue browser published:',destination)
