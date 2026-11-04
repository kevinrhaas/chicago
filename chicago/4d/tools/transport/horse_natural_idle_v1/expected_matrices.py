"""Independent Euler/hierarchy expectation for new idle keys, not native proof.

Does not import the quaternion exporter or read its appended quaternion streams.
The accepted old body/leg world matrices remain exact input data. New neck/head/
tail local rotations are independently composed as rotation matrices through the
unchanged parent hierarchy from the explicit motion recipe.
"""
import copy
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP = ROOT.parents[2]
OLD = APP / 'tools/transport/horse_eye_smooth_normals_v1/fixtures'
AUTHORED = APP / 'assets/authored/transport/horse_standing'
PARENT_MATRICES_SHA = '294f0a1a8a1f154831b5d6fd3207bfda9c1ec7dd61ee2bf9802d4248e532a107'
RECIPE_SHA = 'f948df0e0dc510475df1de85ba5954f46c1b4035f041df582265a37a4ff4b1ef'


def need(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def mul(a, b):
    return [[sum(a[row][k] * b[k][column] for k in range(4))
             for column in range(4)] for row in range(4)]


def rigid_inverse(matrix):
    rotation = [[matrix[column][row] for column in range(3)] for row in range(3)]
    translation = [-sum(rotation[row][k] * matrix[k][3] for k in range(3)) for row in range(3)]
    return [rotation[row] + [translation[row]] for row in range(3)] + [[0, 0, 0, 1]]


def value_at(knots, time):
    if time in (0, 12):
        return 0.0
    for index in range(len(knots) - 1):
        left, right = knots[index:index + 2]
        if left[0] <= time <= right[0]:
            x = (time - left[0]) / (right[0] - left[0])
            blend = 3 * x ** 2 - 2 * x ** 3
            return (1 - blend) * left[1] + blend * right[1]
    raise ValueError('uncovered independent reference time')


def rotation_for(joint, time, recipe):
    bounds = recipe['max_local_rotation_degrees']
    if joint in (2, 3):
        role = 'neck' if joint == 2 else 'head'
        yaw = math.radians(bounds[role + '_yaw'] * value_at(recipe['look_shape_knots'], time))
        pitch = math.radians(bounds[role + '_pitch'] * value_at(recipe['nod_shape_knots'], time))
        cy, sy, cp, sp = math.cos(yaw), math.sin(yaw), math.cos(pitch), math.sin(pitch)
        return [[cy, sy * sp, sy * cp, 0], [0, cp, -sp, 0],
                [-sy, cy * sp, cy * cp, 0], [0, 0, 0, 1]]
    role = 'tail_base' if joint == 4 else 'tail_tip'
    roll = math.radians(bounds[role + '_roll'] * value_at(recipe[role + '_shape_knots'], time))
    c, s = math.cos(roll), math.sin(roll)
    return [[c, -s, 0, 0], [s, c, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]


def generate():
    parent_raw = (OLD / 'accepted-stationary65-matrices.json').read_bytes()
    recipe_raw = (AUTHORED / 'natural-planted-idle-v1-recipe.json').read_bytes()
    controls_raw = (OLD / 'rig26-controls.json').read_bytes()
    need(sha(parent_raw) == PARENT_MATRICES_SHA, 'accepted old65 input must remain exact')
    need(sha(recipe_raw) == RECIPE_SHA, 'explicit reviewed new recipe required')
    parent = json.loads(parent_raw)
    recipe = json.loads(recipe_raw)
    controls = json.loads(controls_raw)
    need(len(parent['frames']) == 65 and len(controls['nodes']) == 26, 'original65/26 inventory')
    frames = copy.deepcopy(parent['frames'])
    for index, frame in enumerate(frames):
        time = frame['time_s']
        need(time == 12 * index / 64, 'same independently accepted source time grid')
        old = parent['frames'][index]['global_canonical_matrices']
        new = frame['global_canonical_matrices']
        for joint in (2, 3, 4, 5):
            ancestor = controls['nodes'][joint]['parent_index']
            need(ancestor in (1, 2, 4), 'explicit unchanged target parent')
            old_local = mul(rigid_inverse(old[ancestor]), old[joint])
            # Rest-local translation is retained; rotation is postmultiplied in
            # the exact local control frame, independently of glTF quaternion IO.
            new[joint] = mul(new[ancestor], mul(old_local, rotation_for(joint, time, recipe)))
        for joint in set(range(26)) - {2, 3, 4, 5}:
            need(new[joint] == old[joint], 'all old body/leg world matrices exact')
    return {'schema': 'natural_planted_idle_independent_expected65_v1',
            'status': 'INDEPENDENT_RECONSTRUCTED_KEY_EXPECTATION_NOT_NATIVE_OR_PHYSICAL_PROOF',
            'parent65_sha256': sha(parent_raw), 'motion_recipe_sha256': sha(recipe_raw),
            'controls26_sha256': sha(controls_raw),
            'method': 'Independent Euler rotation matrices and rigid hierarchy composition; no exporter import, new glTF key readback, renderer, skin evaluation or native certificate.',
            'new_rotation_joints': [2, 3, 4, 5], 'frames': frames,
            'new_native129': 'UNRUN', 'old_certificate_transferred': False}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    need(not args.out.exists(), 'fresh output required')
    args.out.write_text(json.dumps(generate(), indent=2) + '\n')
    print(args.out)
