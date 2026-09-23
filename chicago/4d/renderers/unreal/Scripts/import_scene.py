"""Local Unreal preview adapter: consumes existing glTF and scene sidecars read-only."""
import unreal, json, array, math, traceback, os
from pathlib import Path
ROOT=Path(os.environ['CHICAGO_SOURCE']).resolve()
OUT=Path(os.environ['CHICAGO_PROJECT']).resolve()/'Scripts'
OUT.mkdir(parents=True, exist_ok=True)
report={'source_commit':os.environ['CHICAGO_COMMIT'],'imported':[], 'skipped':[], 'errors':[], 'limitations':['Preview imports generated glTF terrain and structures. Web-renderer procedural streets, flora, props, and research UI are not ported.','Custom per-vertex confidence visualization is not implemented; source sidecars remain the provenance record.']}
def read(p): return json.loads(p.read_text())
scene=read(ROOT/'data/scenes/1835.json')
epoch=ROOT/'data/terrain/epochs'/scene['terrain_epoch']
meta=read(epoch/'heightfield.json')
heights=array.array('h'); heights.frombytes((epoch/meta['bin']).read_bytes())
def height(e,n):
    gx=(e-meta['origin_e'])/meta['cell_m']; gy=(n-meta['origin_n'])/meta['cell_m']
    if gx<0 or gy<0 or gx>meta['cols']-1 or gy>meta['rows']-1: raise ValueError('Placement outside heightfield')
    x=min(math.floor(gx),meta['cols']-2); y=min(math.floor(gy),meta['rows']-2); fx=gx-x; fy=gy-y; c=meta['cols']
    h=(heights[y*c+x]*(1-fx)+heights[y*c+x+1]*fx)*(1-fy)+(heights[(y+1)*c+x]*(1-fx)+heights[(y+1)*c+x+1]*fx)*fy
    return h*meta['scale']+meta['offset']
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
meshes=unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
if not levels.new_level('/Game/Chicago4D/Maps/Chicago1835_Preview'): raise RuntimeError('Cannot create level')
world=unreal.EditorLevelLibrary.get_editor_world()
world.get_world_settings().set_editor_property('default_game_mode',unreal.load_class(None,'/Script/Chicago4D.ChicagoGameMode'))
def ground_under(imported, e, n, rotation):
    # Match buildings.js groundUnder: bed rigid assets at the lowest of a 5x5
    # grid over their rotated footprint, rather than suspending downhill walls
    # from the height at a single origin. Unreal mesh bounds are centimetres.
    boxes = [mesh.get_bounding_box() for mesh in imported]
    min_x = min(box.min.x for box in boxes) / 100
    max_x = max(box.max.x for box in boxes) / 100
    min_y = min(box.min.y for box in boxes) / 100
    max_y = max(box.max.y for box in boxes) / 100
    angle = math.radians(rotation)
    c, s = math.cos(angle), math.sin(angle)
    samples = []
    for i in range(5):
        x = min_x + (max_x-min_x)*i/4
        for j in range(5):
            y = min_y + (max_y-min_y)*j/4
            samples.append(height(e+x*c-y*s, n-x*s-y*c))
    return min(samples)

def place(asset,id,loc,rotation=0,collision=True,terrain_anchor=False):
    dest='/Game/Chicago4D/Imported/'+id
    existing=unreal.EditorAssetLibrary.list_assets(dest,recursive=True,include_folder=False)
    objects=[unreal.load_asset(p) for p in existing] if existing else []
    if not objects:
        t=unreal.AssetImportTask();t.filename=str(ROOT/'assets'/asset);t.destination_path=dest;t.automated=True;t.save=True
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t]);objects=list(t.get_objects())
    imported=[o for o in objects if isinstance(o,unreal.StaticMesh)]
    if not imported: raise RuntimeError('No static mesh imported: '+asset)
    origin_height = loc[2] / 100
    if terrain_anchor:
        fitted_height = ground_under(imported, loc[0]/100, -loc[1]/100, rotation)
        loc = (loc[0], loc[1], fitted_height*100)
        if abs(origin_height-fitted_height) > 0.01:
            report.setdefault('terrain_fit', []).append({'id':id, 'origin_height_m':origin_height, 'footprint_height_m':fitted_height, 'lowered_m':origin_height-fitted_height})
    for mesh in imported:
        body=mesh.get_editor_property('body_setup')
        if collision:
            body.set_editor_property('collision_trace_flag',unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
            unreal.EditorAssetLibrary.save_loaded_asset(mesh)
        # Python Rotator positional order differs from C++; name each axis.
        actor=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(*loc),unreal.Rotator(pitch=0, yaw=rotation, roll=0))
        actor.set_actor_label(id)
        comp=actor.static_mesh_component;comp.set_static_mesh(mesh)
        comp.set_collision_profile_name('BlockAll' if collision else 'NoCollision')
        actor.set_editor_property('tags',[unreal.Name('Chicago4D'),unreal.Name(id)])
    report['imported'].append({'id':id,'asset':asset,'mesh_count':len(imported),'location_cm':loc,'yaw_deg':rotation})
for layer,asset in meta['glb'].items(): place(asset,layer,(0,0,0),collision=layer=='ground')
for i,row in enumerate(read(ROOT/'data/sidecars/1835/index.json')['structures']):
    sid=row if isinstance(row,str) else row['id']
    side=read(ROOT/'data/sidecars/1835'/f'{sid}.json')
    if not side.get('asset'):
        report['skipped'].append({'id':sid,'reason':'No glTF asset; '+str(side.get('drawn_by'))});continue
    try:
        p=side['placement'];e=p['local_e'];n=p['local_n'];h=0 if p.get('vertical_anchor')=='water' else height(e,n)
        place(side['asset'],sid,(e*100,-n*100,h*100),p.get('rotation_deg',0),terrain_anchor=p.get('vertical_anchor')!='water')
        if side.get('review_required'): report.setdefault('review_required',[]).append(sid)
    except Exception as exc:
        report['errors'].append({'id':sid,'error':str(exc)});unreal.log_error(str(exc))
    if i%25==0:
        OUT.joinpath('import_report.json').write_text(json.dumps(report,indent=2));unreal.log('CHICAGO_PROGRESS '+str(i))
s=scene['spawn'];e=s['local_e'];n=s['local_n'];h=height(e,n)
spawn=actors.spawn_actor_from_class(unreal.PlayerStart,unreal.Vector(e*100,-n*100,h*100+110),unreal.Rotator(pitch=0, yaw=s['yaw_deg']-90, roll=0));spawn.set_actor_label('Chicago1835_Start')
sun=actors.spawn_actor_from_class(unreal.DirectionalLight,unreal.Vector(0,0,10000),unreal.Rotator(pitch=-55, yaw=-35, roll=0));sun.set_actor_label('Chicago_Sun')
sun.light_component.set_mobility(unreal.ComponentMobility.MOVABLE);sun.light_component.set_intensity(5)
sun.light_component.set_editor_property('atmosphere_sun_light',True)
sky=actors.spawn_actor_from_class(unreal.SkyAtmosphere,unreal.Vector(0,0,0))
fill=actors.spawn_actor_from_class(unreal.SkyLight,unreal.Vector(0,0,1000));fill.light_component.set_mobility(unreal.ComponentMobility.MOVABLE);fill.light_component.set_editor_property('real_time_capture',True)
if report['errors']: raise RuntimeError('Import incomplete: '+str(report['errors']))
levels.save_current_level()
report['level']='/Game/Chicago4D/Maps/Chicago1835_Preview';report['spawn_cm']=[e*100,-n*100,h*100+110]
OUT.joinpath('import_report.json').write_text(json.dumps(report,indent=2))
unreal.log('CHICAGO_COMPLETE '+str(len(report['imported'])))
