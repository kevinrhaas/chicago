/**
 * Every job the pool can run, by name (T-2599). The worker and the pool's
 * synchronous fallback read this one table, so a job has one implementation and
 * the two paths cannot drift. A kernel is a pure function of typed arrays and
 * numbers that imports no bare specifier — see spatial-kernel.js for why.
 */
import { partitionTriangles } from './spatial-kernel.js';
import { latticeSlots } from './lattice-kernel.js';
import { inflateGzip } from './inflate-kernel.js';
import { slotZones, holdGround, dropGround } from './zone-kernel.js';

export const KERNELS = { partitionTriangles, latticeSlots, inflateGzip, slotZones, holdGround, dropGround };

/** The distinct ArrayBuffers under every typed array in a job's result. */
export function transferablesOf(value, out = new Set()) {
  if (ArrayBuffer.isView(value)) out.add(value.buffer);
  else if (Array.isArray(value)) for (const v of value) transferablesOf(v, out);
  else if (value && typeof value === 'object') for (const v of Object.values(value)) transferablesOf(v, out);
  return out;
}
