# SPDX-License-Identifier: GPL-3.0-or-later
"""Bounded candidate accelerator for the existing triangle SAT; not app code.

The scalar checker remains the numerical authority at decision boundaries.  This
module changes neither the axis inventory nor the caller's interval recursion.
"""
from __future__ import annotations

import numpy as np

BATCH_CAP = 2048
AXIS_CUTOFF = 1e-14
CONTACT_TOLERANCE = 1e-8
MAX_OWNED_WORKSPACE_BOUND = 16 * 1024 * 1024
EPS = np.finfo(np.float64).eps


def separation_batch(a, b, *, scalar, decision_thresholds=CONTACT_TOLERANCE):
    """Return SAT gaps for <=2048 corresponding triangle pairs and diagnostics.

    `decision_thresholds` is either one scalar or an N x (1 or 2) array. Interval
    integration must pass BOTH the original tolerance and displacement+tolerance.
    No interval subdivision, depth, displacement or classification is done here.
    A conservative numerical ambiguity guard is checked against actual bounded
    source-pair measurements; it is not a universal numeric proof. Ambiguous rows
    use the exact original scalar function. The guard is not a contact tolerance.
    """
    if not callable(scalar):
        raise TypeError('The original scalar separation function is required')
    count = len(a)
    if count > BATCH_CAP or len(b) != count:
        raise ValueError('Paired SAT batches must have equal lengths <=2048')
    # Upper bound on explicitly bounded NumPy workspace, including input copies,
    # edge/cross/norm/projection/reduction temporaries and substantial reserve.
    # This is not a process-RSS or allocator-arena claim.
    owned_bound = count * 6144 + 65536
    if owned_bound > MAX_OWNED_WORKSPACE_BOUND:
        raise MemoryError('SAT owned workspace bound exceeded')
    for value in (a, b):
        if isinstance(value, np.ndarray):
            if value.shape != (count, 3, 3):
                raise ValueError('SAT inputs must be N x 3 x 3')
        elif any(len(tri) != 3 or any(len(vertex) != 3 for vertex in tri) for tri in value):
            raise ValueError('SAT inputs must be N x 3 x 3')
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    if a.shape != (count, 3, 3) or b.shape != a.shape:
        raise ValueError('SAT inputs must be corresponding N x 3 x 3 triangles')
    if not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError('Nonfinite geometry is not qualified')
    if not np.isscalar(decision_thresholds):
        if isinstance(decision_thresholds, np.ndarray):
            shape = decision_thresholds.shape
            if len(shape) != 2 or shape[0] != count or shape[1] not in (1, 2):
                raise ValueError('Use one/two bounded decision thresholds per pair')
        elif len(decision_thresholds) != count or any(len(row) not in (1, 2) for row in decision_thresholds):
            raise ValueError('Use one/two bounded decision thresholds per pair')
    thresholds = np.asarray(decision_thresholds, dtype=np.float64)
    if thresholds.ndim == 0:
        thresholds = np.broadcast_to(thresholds, (count, 1))
    if thresholds.ndim != 2 or thresholds.shape[0] != count or thresholds.shape[1] not in (1, 2):
        raise ValueError('Use one scalar or one/two decision thresholds per pair')
    if not np.isfinite(thresholds).all():
        raise ValueError('Finite original decision thresholds are required')
    if not count:
        return np.empty(0), {'pairs': 0, 'batch_cap': BATCH_CAP, 'scalar_fallback_rows': 0,
                             'owned_workspace_upper_bound_bytes': owned_bound}

    ea = np.roll(a, -1, axis=1) - a
    eb = np.roll(b, -1, axis=1) - b
    na = np.cross(ea[:, 0], ea[:, 1])
    nb = np.cross(eb[:, 0], eb[:, 1])
    axes = np.empty((count, 17, 3), dtype=np.float64)
    axes[:, 0] = na
    axes[:, 1] = nb
    axes[:, 2:11] = np.cross(ea[:, :, None, :], eb[:, None, :, :]).reshape(count, 9, 3)
    axes[:, 11:14] = np.cross(na[:, None, :], ea)
    axes[:, 14:17] = np.cross(nb[:, None, :], eb)
    lengths = np.linalg.norm(axes, axis=2)
    valid = lengths > AXIS_CUTOFF
    # Norm calculations may choose different sum kernels. Never decide an axis
    # on opposite sides of the scalar's strict cutoff when rounding could matter.
    near_axis_cutoff = np.any(np.abs(lengths - AXIS_CUTOFF)
                             <= 128 * EPS * np.maximum(lengths, AXIS_CUTOFF), axis=1)
    np.divide(axes, lengths[:, :, None], out=axes, where=valid[:, :, None])
    axes[~valid] = 0
    pa = np.einsum('bvk,bak->bva', a, axes, optimize=False)
    pb = np.einsum('bvk,bak->bva', b, axes, optimize=False)
    amin, amax = pa.min(axis=1), pa.max(axis=1)
    bmin, bmax = pb.min(axis=1), pb.max(axis=1)
    axis_gaps = np.maximum(amin - bmax, bmin - amax)
    axis_gaps[~valid] = -np.inf
    gaps = axis_gaps.max(axis=1)
    scale = np.maximum(1., np.maximum(np.abs(a).max(axis=(1, 2)), np.abs(b).max(axis=(1, 2))))
    # A numerical ambiguity guard, validated/reported on the actual source subset.
    # Proximity triggers recomputation rather than changing a branch threshold.
    error_bound = 512 * EPS * scale
    near_decision = np.any(np.abs(gaps[:, None] - thresholds) <= error_bound[:, None], axis=1)
    fallback = near_axis_cutoff | near_decision | ~valid.any(axis=1) | ~np.isfinite(gaps)
    for i in np.flatnonzero(fallback):
        # Includes max(empty) behavior for degenerate pairs: never manufacture a
        # separating axis or silently turn invalid geometry into clearance.
        gaps[i] = scalar(a[i], b[i])
    return gaps, {'pairs': count, 'batch_cap': BATCH_CAP, 'axis_count_before_filter': 17,
        'valid_axis_count_min': int(valid.sum(axis=1).min()),
        'valid_axis_count_max': int(valid.sum(axis=1).max()),
        'scalar_fallback_rows': int(fallback.sum()),
        'axis_cutoff_ambiguous_rows': int(near_axis_cutoff.sum()),
        'decision_ambiguous_rows': int(near_decision.sum()),
        'max_roundoff_guard_m': float(error_bound.max()),
        'owned_workspace_upper_bound_bytes': owned_bound,
        'owned_workspace_cap_bytes': MAX_OWNED_WORKSPACE_BOUND,
        'contact_tolerance_changed': False, 'interval_semantics_changed': False}
