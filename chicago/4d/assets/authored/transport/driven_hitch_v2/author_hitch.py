#!/usr/bin/env python3
"""Reproduce the authored current26 draft-hitch artifacts from exact source inputs."""
import argparse,importlib.util,runpy,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--horse',type=Path,required=True);p.add_argument('--wagon',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parent;out=a.output_dir.resolve()
if out.exists()and any(out.iterdir()):raise SystemExit('A new empty output directory is required')
out.mkdir(parents=True,exist_ok=True)
spec=importlib.util.spec_from_file_location('build_hitch_prototype',root/'build_hitch_prototype.py');m=importlib.util.module_from_spec(spec);sys.modules['build_hitch_prototype']=m;spec.loader.exec_module(m)
m.HORSE=a.horse.resolve();m.WAGON=a.wagon.resolve();m.HERE=out;m.PARAMETERS=out/'team-hitch-parameters.json';m.main()
runpy.run_path(str(root/'build_connection_units.py'),run_name='__main__')
runpy.run_path(str(root/'build_live_bindings.py'),init_globals={'PALM_SOURCE_OVERRIDE':str(root/'ACTUAL-1835-OTIS-PALM-SURFACES.json')},run_name='__main__')
