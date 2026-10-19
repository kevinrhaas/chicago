# SPDX-License-Identifier: GPL-3.0-or-later
"""Original mechanical flat-foot gait, not measured human biomechanics.

Pure source-frame mathematics. Authored GLB deformation must be checked separately.
"""
from __future__ import annotations
import math
SPEED_M_S = 0.6
CYCLE_DURATION_S = 1.2
FPS = 30
CYCLE_FRAMES = 36
STANCE_FRACTION = 0.62
SWING_LIFT_M = 0.065
PELVIS_DROP_M = 0.040
PELVIS_BOB_M = 0.005

def prepare_legs(bones: dict, scale: float = 1.0) -> dict:
    if not math.isfinite(scale) or scale <= 0:
        raise ValueError('positive finite source scale required')
    legs = {}
    for side in ('l', 'r'):
        hip, knee, ankle = ([float(v)*scale for v in bones[name+'_'+side]['head_m']]
                            for name in ('thigh', 'calf', 'foot'))
        if not all(math.isfinite(v) for p in (hip, knee, ankle) for v in p):
            raise ValueError('finite actual prepared joints required')
        if max(abs(hip[0]-knee[0]), abs(hip[0]-ankle[0]),
               abs(hip[2]-knee[2]), abs(hip[2]-ankle[2])) > 1e-6:
            raise ValueError('sagittal solver requires reviewed vertical rest-leg frame')
        lengths = (math.dist(hip, knee), math.dist(knee, ankle))
        if min(lengths) <= 1e-5 or not hip[1] > knee[1] > ankle[1]:
            raise ValueError('ordered nonzero downward actual leg segments required')
        legs[side] = dict(hip=hip, knee=knee, ankle=ankle, lengths=lengths)
    return legs

def foot_trajectory(phase: float, offset: float) -> tuple[float, float, bool]:
    q = (phase+offset) % 1.0
    half = SPEED_M_S*CYCLE_DURATION_S*STANCE_FRACTION/2
    if q < STANCE_FRACTION:
        return 0.0, half-SPEED_M_S*CYCLE_DURATION_S*q, True
    u = (q-STANCE_FRACTION)/(1-STANCE_FRACTION)
    smooth = u**3*(10+u*(-15+6*u))
    endpoint_tangent = -SPEED_M_S*CYCLE_DURATION_S*(1-STANCE_FRACTION)
    z = -half + endpoint_tangent*u + (2*half-endpoint_tangent)*smooth
    return SWING_LIFT_M*math.sin(math.pi*u)**2, z, False

def pose_at_phase(legs: dict, phase: float) -> dict:
    if not math.isfinite(phase):
        raise ValueError('finite phase required')
    lowering = PELVIS_DROP_M+PELVIS_BOB_M*math.cos(4*math.pi*phase)
    result = dict(pelvis_delta_m=(0.0, -lowering, 0.0), x_rotations_rad={}, legs={})
    for side, offset in (('l', 0.0), ('r', 0.5)):
        leg = legs[side]
        lift, z, support = foot_trajectory(phase, offset)
        hip, ankle = leg['hip'], leg['ankle']
        target = (ankle[0], ankle[1]+lift, ankle[2]+z)
        dy, dz = target[1]-(hip[1]-lowering), target[2]-hip[2]
        l1, l2 = leg['lengths']
        cos_bend = (dy*dy+dz*dz-l1*l1-l2*l2)/(2*l1*l2)
        if not -1.0 <= cos_bend <= 1.0:
            raise ValueError(f'{side}: unreachable source-rig target at phase {phase}')
        knee_angle = math.acos(cos_bend)
        hip_angle = math.atan2(-dz, -dy)-math.atan2(l2*math.sin(knee_angle), l1+l2*math.cos(knee_angle))
        result['x_rotations_rad'].update({
            'thigh_'+side: hip_angle, 'calf_'+side: knee_angle,
            'foot_'+side: -hip_angle-knee_angle, 'ball_'+side: 0.0})
        result['legs'][side] = dict(support=support, ankle_target_m=target)
    return result

def linearize_action(action) -> int:
    """Legacy and Blender4.5 layered Action collections; no bpy import required."""
    curves = list(getattr(action, 'fcurves', ()))
    for layer in getattr(action, 'layers', ()):
        for strip in getattr(layer, 'strips', ()):
            for bag in getattr(strip, 'channelbags', ()):
                curves.extend(bag.fcurves)
    seen = set()
    count = 0
    for curve in curves:
        if id(curve) in seen:
            continue
        seen.add(id(curve))
        for key in curve.keyframe_points:
            key.interpolation = 'LINEAR'
            count += 1
    if count == 0:
        raise ValueError('action contains no accessible keyed FCurves to linearize')
    return count
