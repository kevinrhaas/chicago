// SPDX-License-Identifier: GPL-3.0-or-later
// Far-detail simplification of the two dense V19 body shells (T-3558). Reads
// {parts:{name:[{P:[...],N:[...]}]},ratio,error} as JSON on stdin; welds exact P/N
// corners, simplifies with meshoptimizer (pinned 1.2.0, passed by --tools-root), and
// writes the kept triangles back with each kept corner's ORIGINAL position; corners that
// share a position are welded for the simplifier and carry their averaged normal.
import { createRequire } from 'node:module';
import path from 'node:path';
const root = process.argv[process.argv.indexOf('--tools-root') + 1];
const require = createRequire(path.join(root, 'noop.js'));
const { MeshoptSimplifier } = require('meshoptimizer');
const input = JSON.parse(await new Promise(r => { let s = ''; process.stdin.on('data', d => s += d); process.stdin.on('end', () => r(s)); }));
await MeshoptSimplifier.ready;
const out = {};
for (const [name, list] of Object.entries(input.parts)) {
  out[name] = list.map(({ P, N }) => {
    const key = new Map(), pos = [], nor = [], idx = [];
    for (let i = 0; i < P.length / 3; i++) {
      const k = `${P[3 * i]},${P[3 * i + 1]},${P[3 * i + 2]}`;
      if (!key.has(k)) { key.set(k, pos.length / 3); pos.push(P[3 * i], P[3 * i + 1], P[3 * i + 2]); nor.push(0, 0, 0); }
      const v = key.get(k); idx.push(v);
      for (let a = 0; a < 3; a++) nor[3 * v + a] += N[3 * i + a];
    }
    for (let v = 0; v < nor.length / 3; v++) {
      const l = Math.hypot(nor[3 * v], nor[3 * v + 1], nor[3 * v + 2]) || 1;
      for (let a = 0; a < 3; a++) nor[3 * v + a] /= l;
    }
    const target = Math.max(3, Math.floor(idx.length * input.ratio / 3) * 3);
    const [kept, error] = MeshoptSimplifier.simplify(new Uint32Array(idx), new Float32Array(pos), 3, target, input.error, []);
    const RP = [], RN = [];
    for (const i of kept) { RP.push(pos[3 * i], pos[3 * i + 1], pos[3 * i + 2]); RN.push(nor[3 * i], nor[3 * i + 1], nor[3 * i + 2]); }
    return { P: RP, N: RN, before: idx.length / 3, after: kept.length / 3, error };
  });
}
process.stdout.write(JSON.stringify(out));
