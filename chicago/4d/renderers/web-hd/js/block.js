/**
 * THE GLESSNER BLOCK, AS BOTH SPIKE PAGES LOAD IT (T-2558, RENDERING.md H0).
 *
 * One module, imported by index.html (three's WebGPU build) and classic.html (three's
 * WebGL build). It imports `three`, and each page's import map decides which three that
 * is, so both pages place the SAME GLBs from the SAME published sidecars with the SAME
 * arithmetic, and the only thing that differs between them is the renderer.
 *
 * Copy, don't couple (RENDERING.md section 3). The four pieces walk/ already has are
 * COPIED here, not imported, so walk/'s no-build gate never depends on this directory:
 *
 *   heightfield ... terrain.js `Heightfield.adopt` / `sample` (float32 or scaled int16,
 *                   row 0 at the south edge), bilinear, clamped.
 *   placement ..... buildings.js: `local_e`, `local_n`, `rotation_deg` and the lowest
 *                   ground under a 5 x 5 sample of the building's own rotated box.
 *   frame ......... terrain.js `enuToWorld` (x east, y up, z south) and angles.js
 *                   `bearingToYaw`.
 *   sun ........... world.js `solarPosition` (NOAA) and `sunDirection`.
 *
 * Paths are relative to where the page would sit if published beside walk/
 * (`site/4d/<dir>/`): data at `../data/`, walk/'s loaders at `../walk/vendor/`.
 * `tools/measure_hd_spike.mjs` serves it that way without publishing it.
 */

import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { KTX2Loader } from 'three/addons/loaders/KTX2Loader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';

const DEG = Math.PI / 180;

/** The block: every 1904 structure placed within this many metres of Glessner House. */
export const BLOCK_RADIUS_M = 60;
export const BLOCK_CENTRE_ID = 'glessner_house';
export const YEAR = '1904';

export function enuToWorld(e, n, y = 0, target = new THREE.Vector3()) {
  return target.set(e, y, -n);
}

export function bearingToYaw(deg) { return -deg * DEG; }

/** terrain.js's Heightfield, the two methods the block needs. */
export class Heightfield {
  adopt(meta, buffer) {
    const cols = meta.cols | 0;
    const rows = meta.rows | 0;
    const encoding = meta.encoding || 'float32';
    let data;
    if (encoding === 'float32') {
      data = new Float32Array(buffer, 0, cols * rows);
    } else if (encoding === 'int16') {
      const raw = new Int16Array(buffer, 0, cols * rows);
      const scale = meta.scale ?? 0.01;
      const offset = meta.offset ?? 0;
      data = new Float32Array(raw.length);
      for (let i = 0; i < raw.length; i += 1) data[i] = raw[i] * scale + offset;
    } else {
      throw new Error(`heightfield: unknown encoding '${encoding}'`);
    }
    this.cols = cols;
    this.rows = rows;
    this.cellM = meta.cell_m ?? 1;
    this.originE = meta.origin_e ?? 0;
    this.originN = meta.origin_n ?? 0;
    this.data = data;
    return this;
  }

  sample(e, n) {
    let gx = (e - this.originE) / this.cellM;
    let gy = (n - this.originN) / this.cellM;
    gx = Math.max(0, Math.min(this.cols - 1, gx));
    gy = Math.max(0, Math.min(this.rows - 1, gy));
    const x0 = Math.min(Math.floor(gx), this.cols - 2);
    const y0 = Math.min(Math.floor(gy), this.rows - 2);
    const fx = gx - x0;
    const fy = gy - y0;
    const d = this.data;
    const r0 = y0 * this.cols;
    const r1 = r0 + this.cols;
    return (d[r0 + x0] * (1 - fx) + d[r0 + x0 + 1] * fx) * (1 - fy)
      + (d[r1 + x0] * (1 - fx) + d[r1 + x0 + 1] * fx) * fy;
  }
}

/** world.js's NOAA solar position, verbatim in its arithmetic. */
export function solarPosition({ lat, lon, date, localMeanTime = '12:00' }) {
  const mod = (a, n) => ((a % n) + n) % n;
  const mod360 = (a) => mod(a, 360);
  const [y, mo, d] = date.split('-').map(Number);
  const [hh, mm] = localMeanTime.split(':').map(Number);
  const utcHours = hh + (mm || 0) / 60 - lon / 15;
  const a = Math.floor((14 - mo) / 12);
  const yy = y + 4800 - a;
  const mm2 = mo + 12 * a - 3;
  const jdn = d + Math.floor((153 * mm2 + 2) / 5) + 365 * yy + Math.floor(yy / 4)
    - Math.floor(yy / 100) + Math.floor(yy / 400) - 32045;
  const T = (jdn - 0.5 + utcHours / 24 - 2451545.0) / 36525;
  const L0 = mod360(280.46646 + T * (36000.76983 + 0.0003032 * T));
  const M = 357.52911 + T * (35999.05029 - 0.0001537 * T);
  const e = 0.016708634 - T * (0.000042037 + 0.0000001267 * T);
  const C = Math.sin(M * DEG) * (1.914602 - T * (0.004817 + 0.000014 * T))
    + Math.sin(2 * M * DEG) * (0.019993 - 0.000101 * T)
    + Math.sin(3 * M * DEG) * 0.000289;
  const omega = 125.04 - 1934.136 * T;
  const lambda = L0 + C - 0.00569 - 0.00478 * Math.sin(omega * DEG);
  const eps0 = 23 + (26 + (21.448 - T * (46.815 + T * (0.00059 - T * 0.001813))) / 60) / 60;
  const eps = eps0 + 0.00256 * Math.cos(omega * DEG);
  const decl = Math.asin(Math.sin(eps * DEG) * Math.sin(lambda * DEG)) / DEG;
  const varY = Math.tan(eps / 2 * DEG) ** 2;
  const eqTime = 4 / DEG * (
    varY * Math.sin(2 * L0 * DEG)
    - 2 * e * Math.sin(M * DEG)
    + 4 * e * varY * Math.sin(M * DEG) * Math.cos(2 * L0 * DEG)
    - 0.5 * varY * varY * Math.sin(4 * L0 * DEG)
    - 1.25 * e * e * Math.sin(2 * M * DEG)
  );
  const hourAngle = mod(utcHours * 60 + eqTime + 4 * lon, 1440) / 4 - 180;
  const latR = lat * DEG, declR = decl * DEG, haR = hourAngle * DEG;
  const cosZenith = Math.min(1, Math.max(-1,
    Math.sin(latR) * Math.sin(declR) + Math.cos(latR) * Math.cos(declR) * Math.cos(haR)));
  const zenith = Math.acos(cosZenith);
  let azimuth;
  const denom = Math.cos(latR) * Math.sin(zenith);
  if (Math.abs(denom) < 1e-9) {
    azimuth = hourAngle > 0 ? 180 : 0;
  } else {
    const cosAz = Math.min(1, Math.max(-1, (Math.sin(latR) * cosZenith - Math.sin(declR)) / denom));
    const az = Math.acos(cosAz) / DEG;
    azimuth = hourAngle > 0 ? mod360(az + 180) : mod360(540 - az);
  }
  return { azimuthDeg: mod360(azimuth), elevationDeg: 90 - zenith / DEG };
}

export function sunDirection(azimuthDeg, elevationDeg, target = new THREE.Vector3()) {
  const az = azimuthDeg * DEG;
  const el = elevationDeg * DEG;
  return target.set(Math.sin(az) * Math.cos(el), Math.sin(el), -Math.cos(az) * Math.cos(el)).normalize();
}

async function getJSON(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${url}: HTTP ${res.status}`);
  return res.json();
}

/** The asset a phone boots: the `light` level where a record has one (scene-loader.js). */
function bootAsset(row, sidecar) {
  return sidecar.asset_lods?.light ?? row.asset ?? sidecar.asset;
}

/**
 * The block's records, read from the published 1904 index and sidecars: the rows within
 * BLOCK_RADIUS_M of Glessner House's placement, nearest first.
 */
export async function readBlock(dataBase) {
  const index = await getJSON(new URL(`sidecars/${YEAR}/index.json`, dataBase));
  const rows = (index.structures ?? []).map((r) => (typeof r === 'string' ? { id: r } : r));
  const sidecars = await Promise.all(rows.map((r) => getJSON(
    new URL(r.sidecar ?? `sidecars/${YEAR}/${r.id}.json`, dataBase)).catch(() => null)));
  const centre = sidecars.find((s) => s?.id === BLOCK_CENTRE_ID)?.placement;
  if (!centre) throw new Error(`${BLOCK_CENTRE_ID} is not in the ${YEAR} index`);
  const block = [];
  rows.forEach((row, i) => {
    const sc = sidecars[i];
    const p = sc?.placement;
    if (!p || !Number.isFinite(p.local_e) || !Number.isFinite(p.local_n)) return;
    const dist = Math.hypot(p.local_e - centre.local_e, p.local_n - centre.local_n);
    if (dist <= BLOCK_RADIUS_M) block.push({ id: row.id, sidecar: sc, asset: bootAsset(row, sc), dist });
  });
  block.sort((a, b) => a.dist - b.dist || a.id.localeCompare(b.id));
  return { block, centre };
}

/**
 * Load the block onto `group`. `prepareMaterial(material, mesh)` is the page's one hook:
 * the classic page patches walk/'s confidence view on, the WebGPU page swaps in a node
 * material carrying the TSL node.
 */
export async function loadBlock({ renderer, dataBase, onProgress = () => {} }) {
  const [scene, datum] = await Promise.all([
    getJSON(new URL(`scenes/${YEAR}.json`, dataBase)),
    getJSON(new URL('datum.json', dataBase)),
  ]);
  const hfMetaUrl = new URL(`terrain/epochs/${scene.terrain_epoch}/heightfield.json`, dataBase);
  const hfMeta = await getJSON(hfMetaUrl);
  const hfBin = await (await fetch(new URL(hfMeta.bin, hfMetaUrl))).arrayBuffer();
  const heightfield = new Heightfield().adopt(hfMeta, hfBin);

  const { block, centre } = await readBlock(dataBase);

  const ktx2 = new KTX2Loader();
  ktx2.detectSupport(renderer);
  const loader = new GLTFLoader();
  loader.setKTX2Loader(ktx2);
  loader.setMeshoptDecoder(MeshoptDecoder);

  const group = new THREE.Group();
  group.name = 'glessner-block';
  const loaded = [];
  const problems = [];
  let bytes = 0;
  for (const rec of block) {
    try {
      const url = new URL(rec.asset, dataBase);
      const buf = await (await fetch(url)).arrayBuffer();
      bytes += buf.byteLength;
      const gltf = await loader.parseAsync(buf, String(url));
      const root = gltf.scene;
      root.name = rec.id;
      const p = rec.sidecar.placement;
      root.updateMatrixWorld(true);
      const box = new THREE.Box3().setFromObject(root);
      const th = bearingToYaw(p.rotation_deg ?? 0);
      const cos = Math.cos(th);
      const sin = Math.sin(th);
      let lowest = heightfield.sample(p.local_e, p.local_n);
      if (!box.isEmpty()) {
        for (let i = 0; i <= 4; i += 1) {
          const lx = box.min.x + ((box.max.x - box.min.x) * i) / 4;
          for (let j = 0; j <= 4; j += 1) {
            const lz = box.min.z + ((box.max.z - box.min.z) * j) / 4;
            lowest = Math.min(lowest, heightfield.sample(
              p.local_e + lx * cos + lz * sin, p.local_n + lx * sin - lz * cos));
          }
        }
      }
      const y = p.vertical_anchor === 'water' ? 0 : lowest;
      enuToWorld(p.local_e, p.local_n, y, root.position);
      root.rotation.set(0, th, 0);
      root.traverse((o) => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
      group.add(root);
      loaded.push({ id: rec.id, asset: rec.asset, bytes: buf.byteLength, dist: Math.round(rec.dist * 10) / 10 });
    } catch (err) {
      problems.push(`${rec.id}: ${err.message}`);
    }
    onProgress(loaded.length + problems.length, block.length);
  }
  ktx2.dispose();

  // The ground: the heightfield itself, a 240 m square around the block at 2 m.
  const SPAN = 240;
  const STEP = 2;
  const segs = SPAN / STEP;
  const ground = new THREE.PlaneGeometry(SPAN, SPAN, segs, segs);
  ground.rotateX(-Math.PI / 2);
  const pos = ground.attributes.position;
  for (let i = 0; i < pos.count; i += 1) {
    const e = centre.local_e + pos.getX(i);
    const n = centre.local_n - pos.getZ(i);
    pos.setXYZ(i, e, heightfield.sample(e, n) - 0.02, -n);
  }
  ground.computeVertexNormals();
  ground.computeBoundingSphere();
  const groundMesh = new THREE.Mesh(ground, new THREE.MeshStandardMaterial({ color: 0x6d6a4f, roughness: 1 }));
  groundMesh.name = 'ground';
  groundMesh.receiveShadow = true;
  group.add(groundMesh);

  const sun = solarPosition({
    lat: datum.origin_lat, lon: datum.origin_lon,
    date: scene.target_date, localMeanTime: scene.lighting?.local_time ?? '12:00',
  });

  return { group, loaded, problems, bytes, heightfield, centre, scene, datum, sun, block };
}

/** The sun and sky both pages light the block with: one shadowing sun, one hemisphere. */
export function addLights(scene3d, sun, centreWorld) {
  const dir = sunDirection(sun.azimuthDeg, sun.elevationDeg);
  const light = new THREE.DirectionalLight(0xfff4e0, 3.0);
  light.position.copy(centreWorld).addScaledVector(dir, 150);
  light.target.position.copy(centreWorld);
  light.castShadow = true;
  light.shadow.mapSize.set(2048, 2048);
  const c = light.shadow.camera;
  c.left = -90; c.right = 90; c.top = 90; c.bottom = -90; c.near = 1; c.far = 400;
  light.shadow.bias = -0.0005;
  light.shadow.normalBias = 0.02;
  scene3d.add(light, light.target);
  scene3d.add(new THREE.HemisphereLight(0xbcd2ea, 0x5d5848, 1.1));
  // The sky as walk/ draws it (world.js): a dome that is NOT tone-mapped. A flat
  // `scene.background` colour is the one thing the two renderers treat differently —
  // WebGPURenderer passes it through the tone-mapping output, WebGLRenderer clears with
  // it — so a background would read as a capture difference that walk/ never has.
  const sky = new THREE.Mesh(new THREE.SphereGeometry(1500, 32, 16), new THREE.MeshBasicMaterial({
    color: 0x9fb6cc, side: THREE.BackSide, fog: false, toneMapped: false, depthWrite: false,
  }));
  sky.name = 'sky';
  sky.position.copy(centreWorld);
  scene3d.add(sky);
  return light;
}

/**
 * The fixed stands the measurements read from: the scene's own spawn (walk/'s first
 * view, facing west-south-west at the Glessner lot) and an oblique from the north-east
 * corner of 18th and Prairie. Eye heights are above the heightfield.
 */
export function stands(load) {
  const sp = load.scene.spawn;
  const c = load.centre;
  const hf = load.heightfield;
  const at = (e, n, h) => enuToWorld(e, n, hf.sample(e, n) + h);
  const yaw = (sp.yaw_deg ?? 0) * DEG;
  const spawnEye = at(sp.local_e, sp.local_n, 1.6);
  return [
    { id: 'spawn', eye: spawnEye,
      look: spawnEye.clone().add(new THREE.Vector3(Math.sin(yaw), -0.08, -Math.cos(yaw))) },
    { id: 'oblique-ne', eye: at(c.local_e + 70, c.local_n + 45, 22), look: at(c.local_e + 15, c.local_n + 5, 6) },
  ];
}

/**
 * The dolly the moving reading drives: from the spawn toward the Glessner front and
 * around its corner, `frames` steps, the same path on every page.
 */
export function dollyPose(load, t) {
  const c = load.centre;
  const hf = load.heightfield;
  const a = (-30 + 120 * t) * DEG;
  const r = 55 - 20 * t;
  const e = c.local_e + 18 + r * Math.cos(a);
  const n = c.local_n + 6 + r * Math.sin(a);
  const eye = enuToWorld(e, n, hf.sample(e, n) + 1.6 + 6 * t);
  const look = enuToWorld(c.local_e + 18, c.local_n + 6, hf.sample(c.local_e, c.local_n) + 5);
  return { eye, look };
}
