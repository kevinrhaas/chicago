// T-2380: native palisade geometry, its real gap and legacy fence defaults.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath, pathToFileURL} from 'node:url';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const web = path.join(root, 'renderers/web');
const three = pathToFileURL(path.join(web, 'vendor/three-0.185.1/three.module.js')).href;
const THREE = await import(three);
const moduleURL = text => 'data:text/javascript;base64,' + Buffer.from(text).toString('base64');
const fileURL = name => pathToFileURL(path.join(web, 'js', name)).href;
const gpu = moduleURL(fs.readFileSync(path.join(web, 'js/gpu-pick.js'), 'utf8')
  .replace("from 'three'", `from '${three}'`)
  .replace("from './compact-streams.js'", `from '${fileURL('compact-streams.js')}'`));
const source = fs.readFileSync(path.join(web, 'js/enclosures.js'), 'utf8');
const {createEnclosures} = await import(moduleURL(source.replace("from 'three'", `from '${three}'`)
  .replace("from './gates.js'", `from '${fileURL('gates.js')}'`)
  .replace("from './gpu-pick.js'", `from '${gpu}'`)
  .replace("from './compact-streams.js'", `from '${fileURL('compact-streams.js')}'`)));
const fixture = {id: 'fixture', structure_id: 'log_jail',
  runs: [{id: 'ring', path_local_enu_m: [[0, 0], [8, 0], [8, 6], [0, 6], [0, 0]]}],
  openings: [{id: 'access', at_local_enu_m: [4, 0], width_m: 2}],
  form: {height_m: {value: 3.05, confidence: 'reconstructed'},
    post_spacing_m: {value: 2.44}, post_size_m: {value: .18},
    board_width_m: {value: .254}, board_gap_m: {value: .006}, rail_courses: {value: 3}}};
// Measured from the actual unmodified c6e6dd native renderer before T-2380.
const defaults = {
  'board/light': '98449fd0437ebbfca121ae5261890c15446dc808ceee2133c02f0575edf08427',
  'board/balanced': '98449fd0437ebbfca121ae5261890c15446dc808ceee2133c02f0575edf08427',
  'board/full': 'ecdc8c0e71f387072dfcfbeb114ca9526d9c919eda597364fb1bccec8d1837c4',
  'picket/light': '87b229927df03fa9115008144e64153b5043f2352d093717e42b7143b234139a',
  'picket/balanced': '87b229927df03fa9115008144e64153b5043f2352d093717e42b7143b234139a',
  'picket/full': 'bae6076f81a8034925d1d753cb041274de72d8660949752ba76d5f800cb552ab',
  'post_and_rail/light': '9e5c948717fd5d952d54182c63d47f4641af32f46e01adca8487e45af094cf99',
  'post_and_rail/balanced': '9e5c948717fd5d952d54182c63d47f4641af32f46e01adca8487e45af094cf99',
  'post_and_rail/full': '9e5c948717fd5d952d54182c63d47f4641af32f46e01adca8487e45af094cf99',
};
let record;
const oldFetch = globalThis.fetch;
globalThis.fetch = async url => new Response(JSON.stringify(String(url).endsWith('index.json')
  ? {enclosures: [{id: 'fixture', file: 'fixture.json'}]} : record), {status: 200});
function digest(layer) {
  const h = crypto.createHash('sha256');
  layer.group.traverse(o => {
    if (!o.isMesh) return;
    h.update(JSON.stringify({position: o.position.toArray(), scale: o.scale.toArray(),
      rotation: o.rotation.toArray(), pick: o.userData.pickId}));
    for (const [name, attribute] of Object.entries(o.geometry.attributes).sort(([a], [b]) => a.localeCompare(b))) {
      h.update(name);
      h.update(Buffer.from(attribute.array.buffer, attribute.array.byteOffset, attribute.array.byteLength));
    }
  });
  return h.digest('hex');
}
async function build(detail = 'full') {
  const problems = [];
  const layer = await createEnclosures({dataBase: new URL('https://fixture.invalid/data/'),
    terrain: {surfaceHeight: () => 0, isWater: () => false}, problems, detail});
  assert.deepEqual(problems, []);
  return layer;
}
try {
  for (const [key, expected] of Object.entries(defaults)) {
    const [kind, detail] = key.split('/');
    record = structuredClone(fixture); record.form.fence_type = {value: kind, confidence: 'inferred'};
    const layer = await build(detail);
    assert.equal(digest(layer), expected, `${key}: legacy positions/normals/grades/mesh transforms changed`);
    layer.dispose();
  }
  let fullTriangles = 0, lightTriangles = 0;
  for (const detail of ['light', 'balanced', 'full']) {
    record = structuredClone(fixture);
    Object.assign(record.form, {fence_type: {value: 'board', confidence: 'inferred'},
      top_shape: {value: 'pointed', confidence: 'inferred'},
      point_height_m: {value: .127, confidence: 'reconstructed'}});
    const layer = await build(detail); layer.group.updateMatrixWorld(true);
    const box = new THREE.Box3().setFromObject(layer.group);
    assert(Math.abs(box.min.y) < .001 && Math.abs(box.max.y - 3.05) < .001, 'total height includes the point');
    assert.equal(layer.census.dropped, 0);
    let triangles = 0, slopeFaces = 0;
    layer.group.traverse(o => {
      if (!o.isMesh) return;
      const p = o.geometry.getAttribute('position'), n = o.geometry.getAttribute('normal');
      for (let i = 0; i < p.count; i += 3) {
        const vs = [0, 1, 2].map(k => new THREE.Vector3().fromBufferAttribute(p, i + k).applyMatrix4(o.matrixWorld));
        const norm = new THREE.Vector3().fromBufferAttribute(n, i);
        assert(Math.abs(norm.length() - 1) < .009, 'outward normals remain unit within Int8 quantisation');
        const cross = vs[1].clone().sub(vs[0]).cross(vs[2].clone().sub(vs[0]));
        assert(cross.length() > 1e-8, 'no degenerate tip faces');
        assert(cross.normalize().dot(norm.clone().normalize()) > .99, 'point/body winding agrees with outward normal');
        if (norm.y > .3 && norm.y < .95) slopeFaces++;
        assert(!vs.some(v => Math.abs(v.z) < .02 && v.x > 3.25 && v.x < 4.75), 'the gate retains a clear walking passage');
        triangles++;
      }
    });
    if (detail === 'full') { fullTriangles = triangles; assert(slopeFaces > 0, 'Full retains pointed stock edges'); }
    else { lightTriangles = triangles; assert.equal(slopeFaces, 0, 'plank tiers omit thin tip edges'); }
    layer.dispose();
  }
  assert(lightTriangles < fullTriangles, 'Light remains below Full with the same pointed silhouette');
  for (const point of [0, -1, 3.05, Infinity]) {
    record = structuredClone(fixture);
    Object.assign(record.form, {fence_type: {value: 'board'}, top_shape: {value: 'pointed'}, point_height_m: {value: point}});
    await assert.rejects(build(), /point must be positive/);
  }
  console.log(`enclosure points: PASS (9 legacy byte controls; pointed bounds, winding, normals, gap and tier ladder; Full${fullTriangles}/Light${lightTriangles} triangles)`);
} finally { globalThis.fetch = oldFetch; }
