/**
 * proof.js — strategy A on the T-1801 proof assembly, in the town's own lighting.
 *
 * Query: ?mode=current|courses|proposed|glessner &tier=full|balanced|light
 *        &view=wide|close &light=scene|neutral &finish=unpainted|white_lead|whitewash
 *
 *   current   the proof built with the town's opening (`--opening flat`), no maps:
 *             colour and roughness from the material, as buildings.js draws a wall today
 *   courses   the recessed build with the library's COURSE-BEARING wall maps bound
 *             (clapboard_weathered_oak, hewn_log_oak_chinked) — the route the
 *             preparation map refused, shown so the refusal is a picture and not a claim
 *   proposed  the recessed build with the no-course maps and strategy A's two patches
 *   glessner  the promoted Glessner v4 web derivative, in the same light and exposure
 *
 * Strategy A is `renderers/web/js/roof-relief.js` generalised: a metric UV derived in
 * the vertex shader from world position on the face's own frame, one shared relief
 * pair per substrate, colour left on the material (the town: on the vertex stream).
 * The two patches the preparation map priced are the fragment edits in `relief()`:
 *   1. albedo modulation   diffuse *= 2 * orl.B   (orl.B = 0.5 * L / mean L)
 *   2. roughness by ratio  roughness = finish roughness * orl.G / mean(orl.G)
 */

import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';
import { createWorld } from '/js/world.js';

const q = new URLSearchParams(location.search);
const MODE = q.get('mode') || 'proposed';
const TIER = q.get('tier') || 'full';
const VIEW = q.get('view') || 'wide';
const LIGHT = q.get('light') || 'scene';
const FINISH = q.get('finish') || 'unpainted';
// reflective: the sheet's GLASS colour at roughness 0.05, the room behind doing the depth.
// transmission: the GLB's own KHR_materials_transmission (Glessner's dielectric).
const GLASS = q.get('glass') || 'reflective';

// materials.py's FINISHES, the three a clapboard wall is dealt most often
// `grain` is how much of the wood's own albedo variation a finish lets through. A coat
// of white lead hides the grain's colour and keeps its relief; at full strength it read
// as a painted photograph of wood (first pass of this proof). The sheet marks a finish
// `coating: True`, and 0.3 is this proof's reading of how much a weathered coat shows.
const FINISHES = {
  unpainted: { rgb: null, roughness: null, grain: 1.0 }, // the GLB's own: roughness 0.86
  white_lead: { rgb: [0.90, 0.89, 0.85], roughness: 0.60, grain: 0.3 },
  whitewash: { rgb: [0xd8 / 255, 0xd1 / 255, 0xbc / 255], roughness: 0.90, grain: 0.3 },
};

// GLB material -> proof substrate (tools/fabric_proof_1835_maps.py). Trim and sash take
// nothing, and that is a finding rather than a saving: the face frame puts the grain
// horizontal on EVERY vertical face, so a casing's upright boards came out grained across
// their length, and a check across a 22 mm muntin read as a break. A grain axis per
// board is something the vertex shader cannot know from a position and a normal.
const SUBSTRATE = {
  proposed: { wall_clapboard: 'clapboard', log: 'log',
              chinking: 'chinking', sign: 'sign', deck: 'deck' },
  courses: { wall_clapboard: 'clapboard_courses', log: 'log_courses', chinking: 'chinking',
             sign: 'sign', deck: 'deck' },
};
// The deck's boards run ACROSS the walk (three +z); every other horizontal face falls
// back to world x, as roof-relief.js does.
const FLAT_AXIS = { deck: new THREE.Vector3(0, 0, 1) };
// signboard_weathered was generated as UPRIGHT planks; a signboard's boards run along it.
const TURN = { sign: true };

const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(1);
renderer.setSize(innerWidth, innerHeight);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 0.95; // world.js BASE_EXPOSURE
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = TIER === 'light' ? THREE.PCFShadowMap : THREE.PCFSoftShadowMap;
document.body.appendChild(renderer.domElement);

const scene = new THREE.Scene();
const portrait = innerWidth < innerHeight;
const camera = new THREE.PerspectiveCamera(portrait ? 68 : 46, innerWidth / innerHeight, 0.1, 100000); // the town's sky is 45 km out

// --- light: the town's OWN rig (renderers/web/js/world.js createWorld, the walkthrough's
// sun, sky, environment, exposure and shadow map at 12:30 on 1 July 1835), or a neutral
// overcast field with no sun at all
const pmrem = new THREE.PMREMGenerator(renderer);
let world = null;
if (LIGHT === 'scene') {
  const datum = await (await fetch('/site/data/datum.json')).json();
  world = createWorld({ renderer, scene, datum, lowSpec: TIER === 'light',
    sceneJson: { target_date: '1835-07-01', lighting: { local_time: '12:30' } } });
} else {
  // Overcast: a vertical gradient, brighter at the zenith, no sun and no shadow.
  const g = new THREE.Mesh(new THREE.SphereGeometry(500, 32, 16), new THREE.ShaderMaterial({
    side: THREE.BackSide,
    vertexShader: 'varying vec3 vP; void main(){ vP = position; gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.0); }',
    fragmentShader: 'varying vec3 vP; void main(){ float h = clamp(normalize(vP).y, -1.0, 1.0); '
      + 'vec3 c = mix(vec3(0.30,0.29,0.27), vec3(1.25,1.25,1.22), smoothstep(-0.2, 1.0, h)); gl_FragColor = vec4(c, 1.0); }',
  }));
  const envScene = new THREE.Scene(); envScene.add(g);
  scene.environment = pmrem.fromScene(envScene, 0, 0.1, 1000).texture; // the sphere is 500 m out
  scene.background = new THREE.Color(0x9ea3a6);
}

// --- ground: the library's packed loam tone, flat, so contact shadows have somewhere to land
const ground = new THREE.Mesh(new THREE.PlaneGeometry(400, 400),
  new THREE.MeshStandardMaterial({ color: new THREE.Color().setRGB(0.075, 0.066, 0.046), roughness: 1 }));
ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true;
if (MODE !== 'glessner') scene.add(ground);

// --- the relief binding
const texLoader = new THREE.TextureLoader();
const loadTex = (url, aniso) => new Promise((res, rej) => texLoader.load(url, (t) => {
  t.wrapS = t.wrapT = THREE.RepeatWrapping; t.colorSpace = THREE.NoColorSpace; t.anisotropy = aniso; res(t);
}, undefined, () => rej(new Error(`map did not load: ${url}`))));

function relief(material, set, flatAxis, turn = false, grain = 1.0) {
  material.normalMap = set.normal;
  material.roughnessMap = set.orl;
  material.aoMap = set.orl;
  material.userData.chiSubstrate = set.key;
  material.onBeforeCompile = (shader) => {
    shader.uniforms.chiTileM = { value: set.tileM };
    shader.uniforms.chiMeanRough = { value: set.meanRough };
    shader.uniforms.chiFlatAxis = { value: flatAxis ?? new THREE.Vector3(1, 0, 0) };
    // Uniforms, never code: three caches a program by onBeforeCompile's SOURCE TEXT, so
    // a branch written into the string per material is silently shared by all of them.
    shader.uniforms.chiTurn = { value: turn ? 1 : 0 };
    shader.uniforms.chiGrain = { value: grain };
    shader.vertexShader = 'uniform float chiTileM;\nuniform vec3 chiFlatAxis;\nuniform float chiTurn;\n'
      + shader.vertexShader.replace('#include <project_vertex>', `#include <project_vertex>
  {
    vec3 chiP = ( modelMatrix * vec4( transformed, 1.0 ) ).xyz;
    vec3 chiN = normalize( mat3( modelMatrix ) * objectNormal );
    vec3 chiT = cross( chiN, vec3( 0.0, 1.0, 0.0 ) );
    float chiL = length( chiT );
    chiT = chiL > 1e-4 ? chiT / chiL : chiFlatAxis;
    vec3 chiB = cross( chiT, chiN );
    vec2 chiUv = vec2( dot( chiP, chiT ), dot( chiP, chiB ) ) / chiTileM;
    chiUv = mix( chiUv, chiUv.yx, chiTurn );
    vNormalMapUv = chiUv; vRoughnessMapUv = chiUv; vAoMapUv = chiUv;
  }`);
    shader.fragmentShader = 'uniform float chiMeanRough;\nuniform float chiGrain;\n' + shader.fragmentShader
      .replace('#include <map_fragment>', `#include <map_fragment>
  diffuseColor.rgb *= mix( 1.0, 2.0 * texture2D( roughnessMap, vRoughnessMapUv ).b, chiGrain );`)
      .replace('#include <roughnessmap_fragment>', `float roughnessFactor = roughness;
  roughnessFactor *= clamp( texture2D( roughnessMap, vRoughnessMapUv ).g / chiMeanRough, 0.0, 1.6 );`);
  };
  material.needsUpdate = true;
}

// --- the painted signboard's lettering: a trade name only, in the place signage.js draws it
function lettering() {
  const c = document.createElement('canvas'); c.width = 1024; c.height = 160;
  const g = c.getContext('2d');
  g.fillStyle = '#231e19'; g.textAlign = 'center'; g.textBaseline = 'middle';
  g.font = 'bold 118px Georgia, "Times New Roman", serif';
  g.fillText('GROCERIES', 512, 86);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8;
  const m = new THREE.Mesh(new THREE.PlaneGeometry(2.2, 0.34),
    new THREE.MeshStandardMaterial({ map: t, transparent: true, roughness: 0.7,
      polygonOffset: true, polygonOffsetFactor: -2 }));
  m.position.set(2.4, 2.72, 0.0565);
  return m;
}

const VIEWS = {
  proof: {
    wide: portrait ? { p: [2.6, 1.65, 8.4], t: [2.6, 1.55, 0] } : { p: [4.6, 1.7, 9.2], t: [4.6, 1.45, 0] },
    close: { p: [2.05, 1.62, 2.45], t: [2.45, 1.65, 0] },
  },
  // Glessner's own review stands, render_structure_review.py's frame: Blender (x, y, z)
  // is three (x, z, -y). Wide is 'prairie-entry-detail' (10.9 m off the facade);
  // close is the same line at 5.9 m, the proof's close distance scaled to a taller house.
  glessner: {
    wide: { p: [60, 1.7, -12.5], t: [49.15, 4.5, -12.5] },
    close: { p: [55, 1.7, -12.5], t: [49.15, 3.2, -12.5] },
  },
};

async function main() {
  const t0 = performance.now();
  const work = '/work/';
  const aniso = TIER === 'light' ? 4 : 8;
  const px = TIER === 'light' ? '512' : '1024';
  const sets = {};
  if (MODE === 'proposed' || MODE === 'courses') {
    const maps = await (await fetch(`${work}maps/maps.json`)).json();
    const keys = [...new Set(Object.values(SUBSTRATE[MODE]))];
    await Promise.all(keys.map(async (key) => {
      const rec = maps[key][TIER === 'light' ? 'light' : 'full'];
      const [normal, orl] = await Promise.all([
        loadTex(`${work}maps/${key}/${px}/normal_gl.png`, aniso),
        loadTex(`${work}maps/${key}/${px}/orl.png`, aniso)]);
      sets[key] = { key, normal, orl, tileM: rec.span_m, meanRough: rec.mean_roughness };
    }));
  }

  const loader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
  const url = MODE === 'glessner'
    ? `/site/data/gltf/glessner_house__as_built_1887${TIER === 'light' ? '.light' : ''}.glb`
    : `${work}fabric_proof_1835${MODE === 'current' ? '.flat' : ''}.web.glb`;
  const gltf = await loader.loadAsync(url);
  const root = gltf.scene;
  const finish = FINISHES[FINISH];
  root.traverse((o) => {
    if (!o.isMesh) return;
    o.castShadow = true; o.receiveShadow = true;
    const mats = Array.isArray(o.material) ? o.material : [o.material];
    for (const m of mats) {
      if (MODE === 'glessner') continue;
      if (m.name === 'glass' && GLASS === 'reflective') {
        const g = new THREE.MeshStandardMaterial({ name: 'glass', roughness: 0.05, metalness: 0 });
        g.color.setRGB(0.09, 0.11, 0.13, THREE.LinearSRGBColorSpace); // materials.GLASS
        o.material = g;
        continue;
      }
      if (m.name === 'wall_clapboard' && finish.rgb) {
        m.color.setRGB(...finish.rgb, THREE.LinearSRGBColorSpace); // the sheet's rgba is linear, as the GLB's factor is
        m.roughness = finish.roughness;
      }
      const key = SUBSTRATE[MODE]?.[m.name];
      if (key && sets[key]) {
        relief(m, sets[key], FLAT_AXIS[m.name], TURN[m.name],
          m.name === 'wall_clapboard' ? finish.grain : 1.0);
      }
    }
  });
  scene.add(root);
  if (MODE !== 'glessner') scene.add(lettering());

  const v = VIEWS[MODE === 'glessner' ? 'glessner' : 'proof'][VIEW];
  camera.position.set(...v.p); camera.lookAt(...v.t);
  world?.aim(camera);

  // The first frame compiles. The second is measured with the shadow pass, and a third
  // with the shadow map held, so the main pass can be read on its own.
  renderer.render(scene, camera);
  renderer.render(scene, camera);
  const loadMs = performance.now() - t0;
  const info = renderer.info;
  const withShadow = { calls: info.render.calls, triangles: info.render.triangles };
  renderer.shadowMap.autoUpdate = false;
  renderer.render(scene, camera);
  const mainPass = { calls: info.render.calls, triangles: info.render.triangles };
  renderer.shadowMap.autoUpdate = true;
  // the captured frame: a fixed render, not a loop — Glessner's 3.2 M triangles take
  // seconds a frame on the software rasteriser and a loop starves the screenshot
  renderer.render(scene, camera);
  const seen = new Set(); let gpuBytes = 0;
  scene.traverse((o) => {
    if (!o.isMesh) return;
    for (const m of (Array.isArray(o.material) ? o.material : [o.material])) {
      for (const k of ['map', 'normalMap', 'roughnessMap', 'aoMap', 'metalnessMap', 'emissiveMap']) {
        const t = m[k];
        if (!t || seen.has(t.uuid) || !t.image) continue;
        seen.add(t.uuid);
        const w = t.image.width ?? 0, h = t.image.height ?? 0;
        gpuBytes += Math.round(w * h * 4 * 4 / 3);
      }
    }
  });
  window.__proof = {
    mode: MODE, tier: TIER, view: VIEW, light: LIGHT, finish: FINISH, glass: GLASS,
    calls: mainPass.calls, triangles: mainPass.triangles,
    callsWithShadow: withShadow.calls, trianglesWithShadow: withShadow.triangles,
    textures: seen.size, gpuBytes, loadMs: Math.round(loadMs),
    materials: [...new Set((() => { const a = []; root.traverse((o) => { if (o.isMesh) a.push(...[].concat(o.material).map((m) => m.name)); }); return a; })())],
  };
  document.getElementById('tag').textContent = MODE === 'glessner'
    ? `Glessner v4 (1904 default) · ${TIER} · ${LIGHT} light`
    : `1835 proof · ${MODE} · ${TIER}${FINISH !== 'unpainted' ? ` · ${FINISH.replace('_', ' ')}` : ''} · ${LIGHT} light`;
  document.body.dataset.ready = '1';
}

main().catch((err) => { window.__proofError = String(err?.stack ?? err); document.body.dataset.ready = 'error'; });
