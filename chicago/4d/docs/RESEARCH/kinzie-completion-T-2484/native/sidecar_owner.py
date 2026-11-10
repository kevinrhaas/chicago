"""Re-run the actual frozen per-structure compiler without its file-emitting scene runner."""
import ast,copy,datetime,hashlib,importlib.util,json,sys
from pathlib import Path
def rederive(source_repo,source_sha,blob):
 app=Path(source_repo)/'chicago/4d';recipe='chicago/4d/tools/compile_scene.py';raw=(app/'tools/compile_scene.py').read_bytes()
 assert raw==blob(source_sha,recipe),'Live isolated SOURCE scene owner is not its pinned Git blob'
 sys.path.insert(0,str(app/'tools'));sys.path.insert(0,str(app/'generators'))
 spec=importlib.util.spec_from_file_location('frozen_kinzie_scene_owner',app/'tools/compile_scene.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 tree=ast.parse(raw);scene_fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=='compile_scene');inner=next(x for x in scene_fn.body if isinstance(x,ast.FunctionDef)and x.name=='build_sidecar')
 scene=m.load(m.DATA/'scenes/1812.json');datum=m.load(m.DATA/'datum.json');sources={p.stem:m.load(p)for p in(m.DATA/'sources').glob('*.json')};structure_names={p.stem:m.load(p).get('name',p.stem)for p in(m.DATA/'structures').glob('*.json')}
 trade_path=m.DATA/'reconstruction/1835_trade_roof_seats.json';trade={r['structure_id']:r for r in m.load(trade_path).get('unseatable',[])}if trade_path.exists()else{}
 ns=dict(vars(m),sources=sources,scene_id='1812',scene=scene,datum=datum,residents=m.compile_residents(),lodging=m.compile_lodging(),trade_roofs_unseatable=trade,structure_names=structure_names)
 exec(compile(ast.Module(body=[copy.deepcopy(inner)],type_ignores=[]),str(app/'tools/compile_scene.py')+' actual build_sidecar AST','exec'),ns)
 out={}
 for sid in['kinzie_house_1812','kinzie_house_1812_green']:
  record=m.load(m.DATA/'structures'/f'{sid}.json');phase=m.resolve_phase(record,datetime.date.fromisoformat(scene['target_date']));assert phase is not None;out[sid]=ns['build_sidecar'](record,phase)
 return out,{'actual_owner_path':recipe,'actual_owner_sha256':hashlib.sha256(raw).hexdigest(),'owner_extraction':'Actual compile_scene.compile_scene nested build_sidecar AST; actual frozen sources/scene/datum/resident/lodging/structure-name inputs; no emit/scene runner or file writes','source_sha':source_sha}
