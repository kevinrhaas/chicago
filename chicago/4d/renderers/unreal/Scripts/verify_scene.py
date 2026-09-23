"""Editor-side structural checks. These do not substitute for a packaged play test."""
import json
import os
from pathlib import Path
import unreal

out = Path(os.environ['CHICAGO_PROJECT']) / 'Scripts'
report = json.loads((out/'import_report.json').read_text())
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assert levels.load_level(report['level']), 'Map did not load'
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
owned = [actor for actor in actors if unreal.Name('Chicago4D') in actor.tags]
expected = sum(row['mesh_count'] for row in report['imported'])
assert len(owned) == expected, (len(owned), expected)
placements = {row['id']: row for row in report['imported']}
rotation_checks = []
for actor in owned:
    rotation = actor.get_actor_rotation()
    expected_yaw = placements[actor.get_actor_label()]['yaw_deg']
    assert abs(rotation.pitch) < 0.001 and abs(rotation.roll) < 0.001, (actor.get_actor_label(), rotation)
    assert abs((rotation.yaw - expected_yaw + 180) % 360 - 180) < 0.001, (actor.get_actor_label(), rotation, expected_yaw)
    if actor.get_actor_label() == 'fort_dearborn_garrison_garden':
        center, extent = actor.get_actor_bounds(False)
        assert extent.z * 2 < 150, ('Garden fence tilted above its 1.2m height', extent)
        rotation_checks.append({'id': actor.get_actor_label(), 'yaw_deg': rotation.yaw, 'world_height_cm': extent.z * 2})
    component = actor.static_mesh_component
    if actor.get_actor_label() == 'water':
        assert str(component.get_collision_profile_name()) == 'NoCollision'
    else:
        body = component.static_mesh.get_editor_property('body_setup')
        assert body.get_editor_property('collision_trace_flag') == unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE
        assert str(component.get_collision_profile_name()) == 'BlockAll'
world = unreal.EditorLevelLibrary.get_editor_world()
mode = world.get_world_settings().get_editor_property('default_game_mode')
assert mode == unreal.load_class(None, '/Script/Chicago4D.ChicagoGameMode')
pawn = unreal.get_default_object(mode).get_editor_property('default_pawn_class')
assert pawn == unreal.load_class(None, '/Script/Chicago4D.ChicagoWalker')
starts = [a for a in actors if isinstance(a, unreal.PlayerStart)]
assert len(starts) == 1
assert abs(starts[0].get_actor_rotation().pitch) < 0.001
assert abs(starts[0].get_actor_rotation().roll) < 0.001
assert len(rotation_checks) == 1
assert not report['errors']
(out/'verification.json').write_text(json.dumps({
    'imported_mesh_actors': len(owned), 'solid_and_water_collision_profiles': 'pass',
    'native_body_free_pawn': 'pass', 'player_start_count': len(starts),
    'upright_structure_rotations': 'pass', 'garden_fence': rotation_checks,
    'source_commit': report['source_commit'], 'play_test': 'Required separately'
}, indent=2)+'\n')
unreal.log('CHICAGO_VERIFY_PASS')
