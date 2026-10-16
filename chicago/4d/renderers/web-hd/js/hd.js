/**
 * HD — three's WebGPURenderer on the Glessner block, the confidence view as ONE TSL node
 * composed onto every material (T-2558, RENDERING.md H0).
 *
 * walk/'s confidence view is a string patch against three's GLSL chunk names
 * (`confidence.js`). Here it is a function of nodes: the same channel (`_confidence`, 0 /
 * 0.5 / 1), the same weights, the same two tints and the same ordered 4 x 4 Bayer
 * screen-door, read in the same pixel frame (gl_FragCoord's, bottom-up), so a capture of
 * this page and of classic.html can be compared pixel for pixel (kill criterion K3).
 *
 * Which backend runs is three's choice, not this page's: WebGPU where the browser offers
 * an adapter, WebGL2 where it does not. `?force-webgl=1` asks for the fallback on a
 * browser that has both.
 */

import * as THREE from 'three/webgpu';
import {
  Fn, If, Discard, attribute, uniform, float, vec4, mix, abs, min, clamp, mod, floor,
  screenCoordinate, screenSize, materialColor, vertexColor,
} from 'three/tsl';
import { runSpike, fail } from './harness.js';

const confMode = uniform(0);
const reconAlpha = uniform(0.34);
// confidence.js's defaults: `derived` amber for inferred, `inferred` slate for reconstructed.
const tintInferred = uniform(new THREE.Color(0xe2a63f));
const tintRecon = uniform(new THREE.Color(0x93a6bb));

/** confidence.js `chicago_bayer4`, as arithmetic on the cell instead of a table. */
function bayer4(x, y) {
  const a = mod(x, 2);
  const b = mod(y, 2);
  const c = mod(floor(x.div(2)), 2);
  const d = mod(floor(y.div(2)), 2);
  return abs(a.sub(b)).mul(8).add(b.mul(4)).add(abs(c.sub(d)).mul(2)).add(d).add(0.5).div(16);
}

/** The node: walk/'s FRAGMENT_DISCARD then FRAGMENT_TINT, on the material's own colour. */
function confidenceColor(hasChannel, useVertexColors) {
  return Fn(() => {
    const raw = hasChannel ? attribute('_confidence', 'float') : float(0);
    const conf = clamp(raw, 0, 1);
    const wRecon = clamp(conf.sub(0.75).mul(4), 0, 1).mul(confMode);
    const alpha = mix(float(1), reconAlpha, wRecon);
    const fx = floor(screenCoordinate.x);
    const fy = floor(screenSize.y.sub(screenCoordinate.y));
    If(wRecon.greaterThan(0).and(bayer4(fx, fy).greaterThanEqual(alpha)), () => { Discard(); });
    const base = useVertexColors ? vec4(materialColor).mul(vertexColor()) : vec4(materialColor);
    const wInferred = float(1).sub(min(abs(conf.sub(0.5)).mul(4), 1)).mul(confMode);
    let rgb = mix(base.rgb, tintInferred, wInferred.mul(0.72));
    rgb = mix(rgb, tintRecon, wRecon.mul(0.80));
    return vec4(rgb, base.a);
  })();
}

const NODE_CLASS = {
  MeshStandardMaterial: THREE.MeshStandardNodeMaterial,
  MeshPhysicalMaterial: THREE.MeshPhysicalNodeMaterial,
  MeshLambertMaterial: THREE.MeshLambertNodeMaterial,
  MeshBasicMaterial: THREE.MeshBasicNodeMaterial,
};
const COPY = [
  'name', 'color', 'roughness', 'metalness', 'map', 'lightMap', 'lightMapIntensity', 'aoMap',
  'aoMapIntensity', 'emissive', 'emissiveIntensity', 'emissiveMap', 'bumpMap', 'bumpScale',
  'normalMap', 'normalMapType', 'normalScale', 'roughnessMap', 'metalnessMap', 'alphaMap',
  'side', 'transparent', 'opacity', 'toneMapped', 'fog', 'alphaTest', 'depthWrite', 'depthTest', 'flatShading',
  'polygonOffset', 'polygonOffsetFactor', 'polygonOffsetUnits', 'clearcoat', 'clearcoatRoughness',
  'sheen', 'sheenColor', 'sheenRoughness', 'transmission', 'ior', 'specularIntensity', 'specularColor',
];

const PIXEL = new Uint8Array(4);
const made = new Map();
let converted = 0;
let unconverted = 0;

/** A node material carrying the confidence node, one per (source material, has channel). */
function nodeMaterialFor(src, hasChannel) {
  const key = `${src.uuid}|${hasChannel}`;
  if (made.has(key)) return made.get(key);
  const Klass = NODE_CLASS[src.type];
  if (!Klass) { unconverted += 1; made.set(key, src); return src; }
  const m = new Klass();
  for (const k of COPY) {
    if (!(k in src) || !(k in m) || src[k] === undefined) continue;
    const v = src[k];
    if (v && typeof v.copy === 'function' && m[k] && typeof m[k].copy === 'function' && !v.isTexture) m[k].copy(v);
    else m[k] = v;
  }
  m.vertexColors = false; // multiplied inside the node, before the tint, as walk/ does
  m.colorNode = confidenceColor(hasChannel, !!src.vertexColors);
  converted += 1;
  made.set(key, m);
  return m;
}

try {
  const params = new URLSearchParams(location.search);
  const renderer = new THREE.WebGPURenderer({
    antialias: true, powerPreference: 'high-performance',
    forceWebGL: params.get('force-webgl') === '1',
  });
  await renderer.init();
  const backendName = () => (renderer.backend?.isWebGPUBackend ? 'webgpu' : 'webgl2-fallback');
  await runSpike({
    renderer,
    backend: backendName,
    prepare(mesh) {
      const hasChannel = !!mesh.geometry?.attributes?._confidence;
      mesh.material = Array.isArray(mesh.material)
        ? mesh.material.map((m) => nodeMaterialFor(m, hasChannel))
        : nodeMaterialFor(mesh.material, hasChannel);
    },
    setView(on) { confMode.value = on ? 1 : 0; },
    async finish() {
      const b = renderer.backend;
      if (b.isWebGPUBackend) { await b.device.queue.onSubmittedWorkDone(); return; }
      b.gl.readPixels(0, 0, 1, 1, b.gl.RGBA, b.gl.UNSIGNED_BYTE, PIXEL);
    },
  });
  window.__hd.materials = { converted, unconverted };
} catch (err) {
  fail(err);
}
