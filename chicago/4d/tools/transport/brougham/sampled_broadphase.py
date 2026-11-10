# SPDX-License-Identifier: GPL-3.0-or-later
"""External candidate: exact original AABB predicate on a bounded Y shortlist."""
from collections import OrderedDict
import hashlib
import numpy as np

MAX_FIXED = 100000
CACHE_BYTES = 16 * 1024 * 1024
CACHE_ENTRIES = 4096


class FixedYBroadphase:
    def __init__(self, flo, fhi, *, cache_bytes=CACHE_BYTES, cache_entries=CACHE_ENTRIES):
        count = len(flo)
        if count > MAX_FIXED or len(fhi) != count:
            raise ValueError('Bounded corresponding fixed boxes required')
        for boxes in (flo, fhi):
            if isinstance(boxes, np.ndarray):
                if boxes.shape != (count, 3):
                    raise ValueError('Fixed bounds must be N x 3')
            elif any(len(row) != 3 for row in boxes):
                raise ValueError('Fixed bounds must be N x 3')
        if not isinstance(cache_bytes, int) or isinstance(cache_bytes, bool) or not 0 <= cache_bytes <= CACHE_BYTES:
            raise ValueError('Cache byte cap may only be reduced')
        if not isinstance(cache_entries, int) or isinstance(cache_entries, bool) or not 0 <= cache_entries <= CACHE_ENTRIES:
            raise ValueError('Cache entry cap may only be reduced')
        # The cache owns immutable snapshots. Later caller edits cannot make a
        # previously cached shortlist stale, and geometry itself is never copied.
        self._lo = np.array(flo, dtype=np.float64, copy=True)
        self._hi = np.array(fhi, dtype=np.float64, copy=True)
        if not np.isfinite(self._lo).all() or not np.isfinite(self._hi).all():
            raise ValueError('Nonfinite fixed bounds are not qualified')
        if np.any(self._lo > self._hi):
            raise ValueError('Inverted fixed bounds are not qualified')
        self._lo.setflags(write=False); self._hi.setflags(write=False)
        self._lo_order = np.argsort(self._lo[:, 1], kind='stable')
        self._hi_order = np.argsort(self._hi[:, 1], kind='stable')
        self._lo_y = self._lo[self._lo_order, 1]
        self._hi_y = self._hi[self._hi_order, 1]
        for a in (self._lo_order, self._hi_order, self._lo_y, self._hi_y):
            a.setflags(write=False)
        self._cache = OrderedDict(); self._cache_bytes = 0
        self._byte_cap = cache_bytes; self._entry_cap = cache_entries
        self._queries = self._hits = self._misses = self._evictions = 0
        self._max_cache_bytes = self._max_cache_entries = self._max_prefix = self._max_y = 0
        self._candidate_y_total = 0

    def candidates(self, lo, hi, tolerance=1e-8):
        if len(lo) != 3 or len(hi) != 3 or isinstance(tolerance, (bool, np.bool_)) or not 0 < tolerance <= 1e-8:
            raise ValueError('Original bounded AABB/tolerance inputs required')
        lo = np.asarray(lo, dtype=np.float64); hi = np.asarray(hi, dtype=np.float64)
        if lo.shape != (3,) or hi.shape != (3,) or not np.isfinite(lo).all() or not np.isfinite(hi).all():
            raise ValueError('Finite three-coordinate posed bounds required')
        lower = lo - tolerance; upper = hi + tolerance
        key = (float(lower[1]), float(upper[1]))
        self._queries += 1
        if key in self._cache:
            self._hits += 1; ids = self._cache.pop(key); self._cache[key] = ids
        else:
            self._misses += 1
            stop = int(np.searchsorted(self._lo_y, upper[1], side='right'))
            start = int(np.searchsorted(self._hi_y, lower[1], side='left'))
            if stop <= len(self._hi_y) - start:
                possible = self._lo_order[:stop]
                ids = possible[self._hi[possible, 1] >= lower[1]]
            else:
                possible = self._hi_order[start:]
                ids = possible[self._lo[possible, 1] <= upper[1]]
            self._max_prefix = max(self._max_prefix, len(possible))
            # The native np.flatnonzero result is ascending ORIGINAL fixed IDs,
            # never endpoint-sort order. Duplicates cannot occur in a permutation.
            ids.sort(); ids.setflags(write=False)
            if self._entry_cap and ids.nbytes <= self._byte_cap:
                while self._cache and (self._cache_bytes + ids.nbytes > self._byte_cap
                                       or len(self._cache) >= self._entry_cap):
                    _, old = self._cache.popitem(last=False)
                    self._cache_bytes -= old.nbytes; self._evictions += 1
                self._cache[key] = ids; self._cache_bytes += ids.nbytes
                self._max_cache_bytes = max(self._max_cache_bytes, self._cache_bytes)
                self._max_cache_entries = max(self._max_cache_entries, len(self._cache))
        self._max_y = max(self._max_y, len(ids)); self._candidate_y_total += len(ids)
        # Exact unchanged six-condition predicate remains the final authority.
        # No Y-rotation assumption, polygon proxy, surface exemption or slack.
        keep = (np.all(self._hi[ids] >= lower, axis=1)
                & np.all(self._lo[ids] <= upper, axis=1))
        return ids[keep]

    def reading(self):
        snapshot_bytes = self._lo.nbytes + self._hi.nbytes
        index_bytes = sum(a.nbytes for a in (self._lo_order, self._hi_order, self._lo_y, self._hi_y))
        return {'fixed_boxes': len(self._lo), 'queries': self._queries, 'cache_hits': self._hits,
                'cache_misses': self._misses, 'evictions': self._evictions,
                'cache_bytes': self._cache_bytes, 'cache_entries': len(self._cache),
                'max_cache_bytes': self._max_cache_bytes, 'max_cache_entries': self._max_cache_entries,
                'cache_byte_cap': self._byte_cap, 'cache_entry_cap': self._entry_cap,
                'owned_immutable_fixed_box_bytes': snapshot_bytes, 'owned_sorted_index_bytes': index_bytes,
                'max_endpoint_prefix_or_suffix': self._max_prefix, 'max_y_candidates': self._max_y,
                'total_y_candidates_filtered': self._candidate_y_total,
                'query_temporary_upper_bound_bytes': len(self._lo) * 128 + 65536,
                'python_cache_metadata_reserve_bytes': self._entry_cap * 512,
                'fixed_bounds_sha256': hashlib.sha256(self._lo.tobytes()+self._hi.tobytes()).hexdigest(),
                'tolerance_or_candidate_predicate_changed': False}
