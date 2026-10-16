/**
 * The job pool: procedural geometry built on worker threads (T-2599, the first piece
 * of T-2556).
 *
 * Every layer of the town used to be built on the main thread, so a phone with six
 * to eight cores spent one of them building and the frame waited on it. This is a
 * small pool of module workers, sized `min(hardwareConcurrency − 1, 4)` and started
 * on the first job, with a promise per job. A job is a named kernel from kernels.js:
 * typed arrays and numbers in, typed arrays out, and the result's arrays come back by
 * TRANSFER, so the way home copies nothing. What a caller sends is its own business —
 * spatial-batch.js copies its inputs and transfers the copies, because the geometry
 * it reads may share a buffer with another one.
 *
 * **It degrades to the main thread, never to a missing layer.** With no `Worker`
 * (a tool harness in node), with `?jobs=0` (the kill switch, and the way to read the
 * before), or once a worker has failed to start, `runJob` runs the same kernel
 * synchronously and resolves with the same arrays. A job a failing worker drops is
 * REJECTED rather than re-run here, because its inputs went over by transfer; the
 * caller still holds its own source and re-runs from that (spatial-batch.js does).
 *
 * `jobsState` is what the page found, for `__chicago4d.jobs`.
 */
import { KERNELS } from './kernels.js';

export const jobsState = { mode: 'not started', reason: '', workers: 0,
  ran: { worker: 0, sync: 0 }, failed: [] };

let pool = null;
let nextId = 1;

function killSwitch() {
  try { return new URLSearchParams(globalThis.location?.search ?? '').get('jobs') === '0'; } catch { return false; }
}

function synchronous(reason) {
  pool = false;
  jobsState.mode = 'main thread';
  jobsState.reason = reason;
  jobsState.workers = 0;
}

/** Stop using workers; every job still pending on one is rejected. */
function fail(reason) {
  const pending = pool ? pool.workers.flatMap((w) => [...w.pending.values()]) : [];
  if (pool) for (const w of pool.workers) w.worker.terminate();
  synchronous(reason);
  jobsState.failed.push(reason);
  for (const job of pending) job.reject(new Error(reason));
}

function start() {
  if (pool !== null) return pool;
  if (typeof Worker === 'undefined') { synchronous('no Worker here'); return pool; }
  if (killSwitch()) { synchronous('?jobs=0'); return pool; }
  const cores = Number(globalThis.navigator?.hardwareConcurrency) || 2;
  const size = Math.max(1, Math.min(cores - 1, 4));
  const url = new URL('./worker.js', import.meta.url);
  try {
    pool = { workers: [] };
    for (let i = 0; i < size; i++) {
      const worker = new Worker(url, { type: 'module', name: `chicago4d-jobs-${i}` });
      const slot = { worker, pending: new Map() };
      worker.onmessage = ({ data: { id, result, error } }) => {
        const job = slot.pending.get(id);
        if (!job) return;
        slot.pending.delete(id);
        if (error) job.reject(new Error(error));
        else { jobsState.ran.worker++; job.resolve(result); }
      };
      // A module worker that cannot load (no module workers, a 404) reports here.
      worker.onerror = (event) => {
        event.preventDefault?.();
        fail(`worker ${i} failed: ${event.message || 'did not start'}`);
      };
      pool.workers.push(slot);
    }
  } catch (err) {
    if (pool) for (const w of pool.workers) w.worker.terminate();
    synchronous(`workers would not start: ${err?.message ?? err}`);
    return pool;
  }
  jobsState.mode = 'workers';
  jobsState.workers = size;
  return pool;
}

function runSync(kind, payload) {
  const kernel = KERNELS[kind];
  if (!kernel) throw new Error(`no job named ${kind}`);
  jobsState.ran.sync++;
  return kernel(payload);
}

/**
 * Run the kernel `kind` on `payload`, on the least-busy worker.
 * @param {string} kind a key of kernels.js `KERNELS`
 * @param {object} payload the kernel's argument; typed arrays and plain values
 * @param {{transfer?: Transferable[]}} [o] buffers to hand over rather than copy —
 *        the caller must not read them afterwards
 * @returns {Promise<object>} the kernel's result
 */
export function runJob(kind, payload, { transfer = [] } = {}) {
  const p = start();
  if (!p) return new Promise((resolve) => resolve(runSync(kind, payload)));
  const slot = p.workers.reduce((a, b) => (b.pending.size < a.pending.size ? b : a));
  const id = nextId++;
  return new Promise((resolve, reject) => {
    slot.pending.set(id, { resolve, reject });
    try {
      slot.worker.postMessage({ id, kind, payload }, transfer);
    } catch (err) {
      slot.pending.delete(id);
      reject(err);
    }
  });
}

/** Whether jobs are going to workers — false before the first job, too. */
export function jobsOnWorkers() {
  return Boolean(start());
}
