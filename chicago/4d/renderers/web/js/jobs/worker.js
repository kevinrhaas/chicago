/**
 * The job pool's module worker (T-2599). It runs a kernel from kernels.js and hands
 * every array of the result back by transfer, so nothing is copied on the way home.
 */
import { KERNELS, transferablesOf } from './kernels.js';

self.onmessage = ({ data: { id, kind, payload } }) => {
  let result;
  try {
    const kernel = KERNELS[kind];
    if (!kernel) throw new Error(`no job named ${kind}`);
    result = kernel(payload);
  } catch (err) {
    self.postMessage({ id, error: String(err?.message ?? err) });
    return;
  }
  self.postMessage({ id, result }, [...transferablesOf(result)]);
};
