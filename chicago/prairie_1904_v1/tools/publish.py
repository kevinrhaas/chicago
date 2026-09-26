#!/usr/bin/env python3
"""Publish only the small, cleared research browser; archives stay off Pages."""
from pathlib import Path
import shutil,sys
P=Path(__file__).resolve().parents[1]
R=P.parents[1]
destination=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else R/'site/prairie-1904'
destination.mkdir(parents=True,exist_ok=True)
for name in ['viewer','data','maps','docs']:
 shutil.copytree(P/name,destination/name,dirs_exist_ok=True)
# Only government HABS reports/drawings explicitly selected for the public subset.
if (P/'research/public').exists():shutil.copytree(P/'research/public',destination/'research/public',dirs_exist_ok=True)
print('Prairie Avenue browser published:',destination)
