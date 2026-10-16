/**
 * Inflate a gzipped buffer (T-2677). The prebuilt frontage ships gzipped, because
 * 74.5 MiB raw would not fit the published tree's budget — twice, because the
 * deflate window is 32 KB and the town's timber repeats over far longer runs than
 * that: one pass is 10.76 MB, a second 6.93 MB, a third no smaller. Inflating 78 MB on
 * the main thread put about a second of long tasks back into the boot at the
 * phone profile — most of what the prebuild had taken out. Here it runs on a pool
 * worker, and the result comes home by transfer. The one async kernel: the worker
 * awaits a kernel's result, and the pool's main-thread fallback resolves the same
 * promise.
 */
export async function inflateGzip({ bytes, passes = 1 }) {
  let out = bytes;
  // Up to `passes` times, and only while it still reads as gzip: a server that
  // sent it with Content-Encoding has already taken one pass off.
  for (let i = 0; i < passes && out[0] === 0x1f && out[1] === 0x8b; i += 1) {
    const stream = new Blob([out]).stream().pipeThrough(new DecompressionStream('gzip'));
    out = new Uint8Array(await new Response(stream).arrayBuffer());
  }
  return { bytes: out };
}
