// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * fort-fire.js — the burning of the first Fort Dearborn, 16 August 1812 (T-3553).
 *
 * The owner, 2026-11-16: "add the burning of Fort Dearborn where you can witness and also join
 * the party and help light Fort Dearborn on fire ... the fire should be photographic realistic
 * and actual progress on burn of building sequence and blackening and eventually all turned to
 * ash ... fire and smoke must be very realistic".
 *
 * Two parts:
 *
 *   createFireFx(parent)   the fire as it is drawn: flames (camera-facing cards, each a column of
 *                          rising turbulent noise coloured along a black-body ramp and blended as
 *                          premultiplied light, so it reads in daylight as well as at dusk), wood
 *                          smoke (lit cards: dark brown-grey where it leaves the flames and glows
 *                          with them from below, greyer and thinner as it rises, swells and goes
 *                          down the wind), sparks and embers thrown up, and the glow on the ground
 *                          under a burning building. Immediate mode: each frame the burn says
 *                          where the flames are, and what smoke and sparks to throw.
 *
 *   createFortFire({...})  the burn: each building of the stage's `fire.burns` catches where it
 *                          is lit (a castmate's torch, the visitor's, or the heat of a neighbour),
 *                          the fire runs over its walls and up into its roof, its timbers blacken
 *                          piece by piece, the roof falls in and the walls after it, and what is
 *                          left is a smoking heap of charcoal and ash, glowing at first, then grey.
 *                          The buildings are the town's own batched pieces (buildings.js): their
 *                          paint is darkened and their placement brought down where they stand,
 *                          and all of it is given back when the stage is let go.
 *
 * The record: Heald's report, 'The next morning, they set fire to the fort and left the place';
 * Wau-Bun, 'The following morning, the work of plunder being completed, the Indians set fire to
 * the fort'; Quaife, the brick magazine 'alone defied the fire'. How fast it caught, how each
 * building burned and fell, in what order, and that the visitor may put a torch to it, is ours:
 * docs/LIBERTIES.md L-1812-burning-of-the-fort. The burn is time compressed: a building that
 * would burn for an hour or more goes from the first flame to its heap in about two minutes.
 */
import * as THREE from 'three';

const clamp = (x, a, b) => Math.min(b, Math.max(a, x));
const smooth = (t) => { t = clamp(t, 0, 1); return t * t * (3 - 2 * t); };
const lerp = (a, b, t) => a + (b - a) * t;

/** A small seeded stream, so a building burns the same way every time it is watched. */
function stream(seed) {
  let s = 2166136261 >>> 0;
  for (const ch of String(seed)) { s ^= ch.charCodeAt(0); s = Math.imul(s, 16777619) >>> 0; }
  return () => { s ^= s << 13; s >>>= 0; s ^= s >>> 17; s ^= s << 5; s >>>= 0; return s / 4294967296; };
}

// ── the timing of a burn (seconds of the stage's clock; compressed) ─────────────────────────────
export const BURN = Object.freeze({
  spread_mps: 0.42,   // how fast the fire runs over a building's walls from where it caught
  rise_s: 6,          // a patch of wall from the first lick to full flame
  hold_s: 34,         // ... burning at full
  fade_s: 16,         // ... dying down to embers
  roof_lag_s: 7,      // the roof above a burning wall catches after this
  fall_after_s: 20,   // the roof starts to fall this long after the whole building is alight
  fall_s: 15,         // ... and the building is down this long after that
  heap_s: 70,         // the heap glows and flames this long, then lies grey and smoking
  catch_gap_m: 6.5,   // a neighbour this near catches from the heat
});
const CHAR = new THREE.Color(0.055, 0.047, 0.042);     // charred pine and oak, as a multiplier
const SOOT = new THREE.Color(0.42, 0.36, 0.33);        // the brick magazine, smoked
const WIND = new THREE.Vector3(0.92, 0, -0.38).normalize(); // toward the east-north-east, off over the lake
const WIND_MPS = 1.7;

// ── the noise every shader here shares ─────────────────────────────────────────────────────────
const NOISE_GLSL = /* glsl */`
  float fhash(vec3 p) { p = fract(mod(p, 289.0) * 0.3183099 + 0.1); p *= 17.0; return fract(p.x * p.y * p.z * (p.x + p.y + p.z)); }
  float fnoise(vec3 x) {
    vec3 i = floor(x), f = fract(x); f = f * f * (3.0 - 2.0 * f);
    return mix(mix(mix(fhash(i), fhash(i + vec3(1, 0, 0)), f.x), mix(fhash(i + vec3(0, 1, 0)), fhash(i + vec3(1, 1, 0)), f.x), f.y),
               mix(mix(fhash(i + vec3(0, 0, 1)), fhash(i + vec3(1, 0, 1)), f.x), mix(fhash(i + vec3(0, 1, 1)), fhash(i + vec3(1, 1, 1)), f.x), f.y), f.z);
  }
  float ffbm(vec3 p) {
    float a = 0.5, s = 0.0;
    for (int i = 0; i < FIRE_OCTAVES; i++) { s += a * fnoise(p); p = p * 2.07 + vec3(1.7, 9.2, 3.1); a *= 0.5; }
    return s;
  }
`;

// ── flames ──────────────────────────────────────────────────────────────────────────────────────
const FLAME_VERT = /* glsl */`
  attribute vec3 iPos;      // the flame's foot, world
  attribute vec3 iShape;    // width, height, heat 0..1.4
  attribute float iSeed;
  uniform vec3 uWind;
  varying vec2 vUv;
  varying float vHeat;
  varying float vSeed;
  #include <fog_pars_vertex>
  void main() {
    vUv = uv; vHeat = iShape.z; vSeed = iSeed;
    // A flame stands up: turned about the vertical to face the eye, and leaning down the wind
    // more the higher it goes.
    vec3 right = vec3(viewMatrix[0][0], viewMatrix[1][0], viewMatrix[2][0]);
    right = normalize(vec3(right.x, 0.0, right.z) + vec3(1e-4, 0.0, 0.0));
    float y = position.y;
    vec3 world = iPos + right * position.x * iShape.x + vec3(0.0, y * iShape.y, 0.0) + uWind * (y * y * iShape.y * 0.22);
    vec4 mvPosition = viewMatrix * vec4(world, 1.0);
    // Drawn a little toward the eye, so a flame at a wall is not cut by the wall it stands at.
    mvPosition.xyz += normalize(-mvPosition.xyz) * min(0.9, iShape.x * 0.3);
    gl_Position = projectionMatrix * mvPosition;
    #include <fog_vertex>
  }
`;
const FLAME_FRAG = /* glsl */`
  uniform float uTime;
  varying vec2 vUv;
  varying float vHeat;
  varying float vSeed;
  ${NOISE_GLSL}
  #include <fog_pars_fragment>
  void main() {
    vec2 p = vec2(vUv.x * 2.0 - 1.0, vUv.y);
    // The seed folded small and the clock kept short (fort-fire update): value noise fed
    // numbers in the thousands loses its hash to float rounding and draws its lattice as
    // flat squares in the flame.
    float sd = fract(vSeed * 0.6180339) * 17.0;
    float t = uTime + sd * 3.0;
    // Turbulence carried up through the flame faster than it grows, a second layer folded
    // into the first, so it breaks into tongues that lick up, part and go out.
    vec3 q = vec3(p.x * 1.6 + sd, p.y * 2.2 - t * 2.0, t * 0.35 + sd * 0.5);
    float n1 = ffbm(q);
    float n2 = ffbm(vec3(p.x * 3.4 + n1 * 1.5 + sd * 0.3, p.y * 3.8 - t * 3.3, t * 0.6 + sd * 0.7));
    // The flame sways, its top far more than its foot.
    float x = p.x + (n1 - 0.5) * 2.0 * p.y + sin(t * 1.3 + sd) * 0.12 * p.y;
    float hw = mix(0.72, 0.2, pow(p.y, 0.8));
    float e = abs(x) / hw;
    float env = exp(-e * e * 1.7) * (1.0 - smoothstep(0.4, 0.98, abs(p.x)));
    float d = env * smoothstep(0.0, 0.16, p.y) * (1.3 * (1.0 - p.y) + 0.12);
    // The noise eats it, more the higher it goes, so its top is ragged and broken.
    // (fbm sits near 0.5: stretched, so the flame truly parts into tongues and gaps)
    float nc = clamp((n2 - 0.5) * 2.4 + 0.5, 0.0, 1.0);
    float heat = (d * (0.12 + 1.6 * nc) - 0.3 * p.y - 0.06) * vHeat * 1.4;
    heat = clamp(heat, 0.0, 1.5);
    // Black-body, as a wood fire's flame runs: dull red at its ragged edge, orange, yellow, and
    // a pale yellow only at the hottest of its foot.
    vec3 c = mix(vec3(0.5, 0.06, 0.008), vec3(1.0, 0.3, 0.035), smoothstep(0.0, 0.3, heat));
    c = mix(c, vec3(1.0, 0.56, 0.13), smoothstep(0.28, 0.7, heat));
    c = mix(c, vec3(1.0, 0.8, 0.45), smoothstep(0.8, 1.35, heat));
    float a = smoothstep(0.0, 0.22, heat);
    vec3 rgb = c * (0.25 + 1.3 * heat) * a;
    // Soot where the tongues go out: the flame's tip turns to a dark smoke over it.
    float soot = env * smoothstep(0.35, 0.85, p.y) * smoothstep(0.35, 0.75, n1) * (1.0 - a) * 0.45 * min(vHeat, 1.0);
    gl_FragColor = vec4(rgb, a * 0.5 + soot);
    #include <tonemapping_fragment>
    #include <colorspace_fragment>
    #ifdef USE_FOG
      #ifdef FOG_EXP2
        float fogFactor = 1.0 - exp(-fogDensity * fogDensity * vFogDepth * vFogDepth);
      #else
        float fogFactor = smoothstep(fogNear, fogFar, vFogDepth);
      #endif
      gl_FragColor.rgb = mix(gl_FragColor.rgb, fogColor * gl_FragColor.a, fogFactor);
    #endif
  }
`;

// ── sparks and embers ──────────────────────────────────────────────────────────────────────────
const SPARK_VERT = /* glsl */`
  attribute float aSize;
  attribute float aHeat;
  uniform float uScale;
  varying float vHeat;
  void main() {
    vHeat = aHeat;
    vec4 mv = modelViewMatrix * vec4(position, 1.0);
    gl_PointSize = clamp(aSize * uScale / max(0.5, -mv.z), 1.0, 9.0);
    gl_Position = projectionMatrix * mv;
  }
`;
const SPARK_FRAG = /* glsl */`
  varying float vHeat;
  void main() {
    vec2 c = gl_PointCoord - 0.5;
    float a = (1.0 - smoothstep(0.0, 0.5, length(c))) * vHeat;
    vec3 col = mix(vec3(1.0, 0.25, 0.03), vec3(1.0, 0.75, 0.35), vHeat);
    gl_FragColor = vec4(col * a * 2.6, a);
    #include <tonemapping_fragment>
    #include <colorspace_fragment>
  }
`;

/** The smoke's puffs: four billows in a 2 x 2 sheet, density in alpha (made once, on a canvas). */
let puffSheet = null;
function smokeSheet() {
  if (puffSheet || typeof document === 'undefined') return puffSheet;
  const N = 128, c = document.createElement('canvas'); c.width = c.height = N * 2;
  const g = c.getContext('2d'), img = g.createImageData(N * 2, N * 2);
  const rnd = stream('smoke-sheet');
  const lattice = new Float32Array(32 * 32 * 4).map(() => rnd());
  const vn = (x, y, k) => {
    const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi;
    const u = xf * xf * (3 - 2 * xf), v = yf * yf * (3 - 2 * yf);
    const at = (i, j) => lattice[(((j & 31) * 32 + (i & 31)) * 4) + k];
    return lerp(lerp(at(xi, yi), at(xi + 1, yi), u), lerp(at(xi, yi + 1), at(xi + 1, yi + 1), u), v);
  };
  for (let tile = 0; tile < 4; tile++) {
    const ox = (tile % 2) * N, oy = Math.floor(tile / 2) * N;
    for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) {
      const u = x / N * 2 - 1, v = y / N * 2 - 1;
      let f = 0, a = 0.5, s = 3.2;
      for (let o = 0; o < 5; o++) { f += a * vn(u * s + tile * 7.3 + 11, v * s + tile * 3.1 + 5, tile); s *= 2.03; a *= 0.5; }
      // A billow: round, its edge worn into by the noise.
      const r = Math.hypot(u, v) + (f - 0.48) * 0.9;
      const dens = clamp(1 - smooth((r - 0.3) / 0.5), 0, 1) * (0.4 + 1.0 * f) * (1 - smooth((Math.hypot(u, v) - 0.6) / 0.38));
      const i = ((oy + y) * N * 2 + ox + x) * 4;
      const lum = 200 + 55 * f;
      img.data[i] = lum; img.data[i + 1] = lum; img.data[i + 2] = lum; img.data[i + 3] = clamp(dens, 0, 1) * 255;
    }
  }
  g.putImageData(img, 0, 0);
  puffSheet = new THREE.CanvasTexture(c);
  puffSheet.colorSpace = THREE.SRGBColorSpace;
  return puffSheet;
}

/** A soft round glow, for the ground under a fire. */
let glowTexture = null;
function glowMap() {
  if (glowTexture || typeof document === 'undefined') return glowTexture;
  const c = document.createElement('canvas'); c.width = c.height = 64;
  const g = c.getContext('2d'), grad = g.createRadialGradient(32, 32, 0, 32, 32, 32);
  grad.addColorStop(0, 'rgba(255,255,255,1)'); grad.addColorStop(0.45, 'rgba(255,255,255,0.45)'); grad.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = grad; g.fillRect(0, 0, 64, 64);
  glowTexture = new THREE.CanvasTexture(c);
  return glowTexture;
}

/** How much a tier draws: a phone keeps the whole fire, in fewer and larger pieces. */
export function fireBudget(tier = 'full') {
  return tier === 'light'
    ? { flames: 90, smoke: 150, sparks: 120, octaves: 3, spacing: 1.45 }
    : tier === 'balanced'
      ? { flames: 170, smoke: 280, sparks: 220, octaves: 4, spacing: 1.15 }
      : { flames: 240, smoke: 420, sparks: 320, octaves: 4, spacing: 1 };
}

/**
 * The fire as drawn, under `parent`. Each frame: `flame(x, y, z, w, h, heat, seed)` for every
 * flame burning (world metres, the flame's foot), `smoke(at, opts)` and `sparks(at, n)` to throw
 * some, `glow(x, y, z, r, heat)` under a fire; then `update(dt, camera)` draws them.
 */
export function createFireFx(parent, { tier = 'full' } = {}) {
  const budget = fireBudget(tier);
  const group = new THREE.Group(); group.name = 'fort-fire'; parent?.add?.(group);

  // Flames: one card each, a quad standing on its foot.
  const card = new THREE.PlaneGeometry(1, 1, 1, 1); card.translate(0, 0.5, 0);
  const fg = new THREE.InstancedBufferGeometry();
  fg.index = card.index; fg.setAttribute('position', card.getAttribute('position')); fg.setAttribute('uv', card.getAttribute('uv'));
  const fPos = new THREE.InstancedBufferAttribute(new Float32Array(budget.flames * 3), 3).setUsage(THREE.DynamicDrawUsage);
  const fShape = new THREE.InstancedBufferAttribute(new Float32Array(budget.flames * 3), 3).setUsage(THREE.DynamicDrawUsage);
  const fSeed = new THREE.InstancedBufferAttribute(new Float32Array(budget.flames), 1).setUsage(THREE.DynamicDrawUsage);
  fg.setAttribute('iPos', fPos); fg.setAttribute('iShape', fShape); fg.setAttribute('iSeed', fSeed);
  fg.instanceCount = 0;
  const flameMat = new THREE.ShaderMaterial({
    // The fog's own uniforms (the renderer fills them from the scene's fog each frame).
    uniforms: { fogDensity: { value: 0.00025 }, fogNear: { value: 1 }, fogFar: { value: 2000 }, fogColor: { value: new THREE.Color(0xffffff) },
      uTime: { value: 0 }, uWind: { value: WIND.clone().multiplyScalar(0.55) } },
    vertexShader: FLAME_VERT, fragmentShader: FLAME_FRAG, defines: { FIRE_OCTAVES: budget.octaves },
    transparent: true, depthWrite: false, fog: true, side: THREE.DoubleSide,
    blending: THREE.CustomBlending, blendSrc: THREE.OneFactor, blendDst: THREE.OneMinusSrcAlphaFactor, blendEquation: THREE.AddEquation,
  });
  flameMat.name = 'fort_fire_flame';
  const flames = new THREE.Mesh(fg, flameMat);
  flames.frustumCulled = false; flames.renderOrder = 7; flames.name = 'fort-fire:flames'; // after the smoke: a fire shows through its own smoke
  group.add(flames);
  let flameCount = 0;
  const flameList = [];

  // Smoke: lit cards (the town's own sun and sky light them), sorted far to near each frame.
  const sheet = smokeSheet();
  const smokeMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 1, metalness: 0, transparent: true, depthWrite: false,
    alphaMap: null, map: sheet, side: THREE.DoubleSide });
  smokeMat.name = 'fort_fire_smoke';
  smokeMat.onBeforeCompile = (shader) => {
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', '#include <common>\nattribute vec4 iPuff;\nvarying vec4 vPuff;\nvarying vec3 vSph;')
      .replace('#include <uv_vertex>', '#include <uv_vertex>\nvPuff = iPuff;\nvSph = vec3(position.xy * 2.0, 0.0);\n'
        + '{ float c = cos(iPuff.w), s = sin(iPuff.w); vec2 r = mat2(c, s, -s, c) * (uv - 0.5) + 0.5;\n'
        + '  float tile = floor(iPuff.z + 0.5); vMapUv = (clamp(r, 0.02, 0.98) + vec2(mod(tile, 2.0), floor(tile / 2.0))) * 0.5; }');
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', '#include <common>\nvarying vec4 vPuff;\nvarying vec3 vSph;')
      .replace('#include <map_fragment>', '#include <map_fragment>\ndiffuseColor.a = sampledDiffuseColor.a * vPuff.x * (1.0 - smoothstep(0.5, 1.0, length(vSph.xy)));\n')
      // A billow is round: lit as a ball is, so the sun picks out its top and its edge.
      .replace('#include <normal_fragment_maps>', '#include <normal_fragment_maps>\n{ vec2 o = vSph.xy; float z = sqrt(max(0.05, 1.0 - dot(o, o))); normal = normalize(vec3(o * 0.85, z)); }')
      .replace('#include <emissivemap_fragment>', '#include <emissivemap_fragment>\ntotalEmissiveRadiance += vec3(1.0, 0.36, 0.08) * vPuff.y * 1.3 * clamp(0.5 - 0.5 * vSph.y, 0.0, 1.0) * diffuseColor.a;');
  };
  smokeMat.customProgramCacheKey = () => 'fort_fire_smoke_v2';
  const quad = new THREE.PlaneGeometry(1, 1);
  const iPuff = new THREE.InstancedBufferAttribute(new Float32Array(budget.smoke * 4), 4).setUsage(THREE.DynamicDrawUsage);
  quad.setAttribute('iPuff', iPuff);
  const smoke = new THREE.InstancedMesh(quad, smokeMat, budget.smoke);
  smoke.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
  smoke.setColorAt(0, new THREE.Color(1, 1, 1));
  smoke.instanceColor.setUsage(THREE.DynamicDrawUsage);
  smoke.count = 0; smoke.frustumCulled = false; smoke.renderOrder = 6; smoke.name = 'fort-fire:smoke';
  smoke.castShadow = false; smoke.receiveShadow = false;
  group.add(smoke);
  const puffs = [];

  // Sparks: points, each thrown up and carried, cooling from yellow to a dull red, then out.
  const sg = new THREE.BufferGeometry();
  const sPos = new THREE.BufferAttribute(new Float32Array(budget.sparks * 3), 3).setUsage(THREE.DynamicDrawUsage);
  const sSize = new THREE.BufferAttribute(new Float32Array(budget.sparks), 1).setUsage(THREE.DynamicDrawUsage);
  const sHeat = new THREE.BufferAttribute(new Float32Array(budget.sparks), 1).setUsage(THREE.DynamicDrawUsage);
  sg.setAttribute('position', sPos); sg.setAttribute('aSize', sSize); sg.setAttribute('aHeat', sHeat);
  sg.setDrawRange(0, 0);
  const sparkMat = new THREE.ShaderMaterial({ uniforms: { uScale: { value: 260 } }, vertexShader: SPARK_VERT, fragmentShader: SPARK_FRAG,
    transparent: true, depthWrite: false, blending: THREE.CustomBlending, blendSrc: THREE.OneFactor, blendDst: THREE.OneMinusSrcAlphaFactor });
  sparkMat.name = 'fort_fire_sparks';
  const sparkPoints = new THREE.Points(sg, sparkMat); sparkPoints.frustumCulled = false; sparkPoints.renderOrder = 8; sparkPoints.name = 'fort-fire:sparks';
  group.add(sparkPoints);
  const sparkList = [];

  // The glow on the ground under each fire.
  const glowMat = new THREE.MeshBasicMaterial({ map: glowMap(), color: 0xff7a2a, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
    polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2, toneMapped: true });
  glowMat.name = 'fort_fire_glow';
  const glowGeo = new THREE.PlaneGeometry(1, 1); glowGeo.rotateX(-Math.PI / 2);
  const glows = new THREE.InstancedMesh(glowGeo, glowMat, 24); glows.count = 0; glows.frustumCulled = false; glows.renderOrder = 4;
  glows.setColorAt(0, new THREE.Color(1, 1, 1)); glows.name = 'fort-fire:glow';
  group.add(glows);
  let glowCount = 0;

  const rnd = stream('fire-fx');
  const m4 = new THREE.Matrix4(), q4 = new THREE.Quaternion(), s4 = new THREE.Vector3(), p4 = new THREE.Vector3(), col = new THREE.Color();
  const camPos = new THREE.Vector3();
  let time = 0;

  const api = {
    group,
    budget,
    /** Begin a frame's list of flames and glows. */
    begin() { flameList.length = 0; glowCount = 0; },
    flame(x, y, z, w, h, heat, seed, keep = false) { if (heat > 0.02) flameList.push({ x, y, z, w, h, heat, seed, keep }); },
    /** Throw `n` puffs of smoke from `at` (world): `dark` 0 grey .. 1 thick brown-black, `glow`
     *  how much the fire under it lights it, `size` metres across at birth, `up` m/s. */
    smoke(at, { n = 1, dark = 0.7, glow = 0.6, size = 2, up = 2.2, life = 16, spread = 0.6 } = {}) {
      for (let k = 0; k < n; k++) {
        if (puffs.length >= budget.smoke) puffs.shift();
        puffs.push({ p: new THREE.Vector3(at.x + (rnd() - 0.5) * spread, at.y, at.z + (rnd() - 0.5) * spread),
          v: new THREE.Vector3((rnd() - 0.5) * 0.5, up * (0.7 + 0.6 * rnd()), (rnd() - 0.5) * 0.5),
          age: 0, life: life * (0.8 + 0.4 * rnd()), s0: size * (0.75 + 0.5 * rnd()), dark, glow, rot: rnd() * 6.283, spin: (rnd() - 0.5) * 0.18,
          tile: Math.floor(rnd() * 4) });
      }
    },
    sparks(at, n = 1, { up = 4, spread = 0.8 } = {}) {
      for (let k = 0; k < n; k++) {
        if (sparkList.length >= budget.sparks) sparkList.shift();
        sparkList.push({ p: new THREE.Vector3(at.x + (rnd() - 0.5) * spread, at.y + rnd() * 0.6, at.z + (rnd() - 0.5) * spread),
          v: new THREE.Vector3((rnd() - 0.5) * 1.6, up * (0.5 + rnd()), (rnd() - 0.5) * 1.6), age: 0, life: 1.4 + rnd() * 3.2, size: 0.05 + rnd() * 0.09, w: rnd() * 6.28 });
      }
    },
    glow(x, y, z, r, heat) {
      if (glowCount >= 24 || heat <= 0.01) return;
      m4.compose(p4.set(x, y + 0.08, z), q4.identity(), s4.set(r, 1, r));
      glows.setMatrixAt(glowCount, m4);
      glows.setColorAt(glowCount, col.setRGB(1, 0.5, 0.18).multiplyScalar(clamp(heat, 0, 1.2) * 0.3));
      glowCount++;
    },
    update(dt, camera) {
      const step = Number.isFinite(dt) && dt > 0 ? Math.min(dt, 0.25) : 0;
      time += step;
      flameMat.uniforms.uTime.value = time % 300; // kept short: see FLAME_FRAG
      if (camera) camera.getWorldPosition(camPos);
      // Flames: the hottest first, so a phone's budget keeps the heart of the fire.
      // A torch in a hand is never the one dropped.
      if (flameList.length > budget.flames) flameList.sort((a, b) => (b.keep ? 1e9 : b.heat * b.h) - (a.keep ? 1e9 : a.heat * a.h));
      flameCount = Math.min(flameList.length, budget.flames);
      for (let i = 0; i < flameCount; i++) {
        const f = flameList[i];
        fPos.setXYZ(i, f.x, f.y, f.z); fShape.setXYZ(i, f.w, f.h, f.heat); fSeed.setX(i, f.seed);
      }
      fg.instanceCount = flameCount;
      if (flameCount) { fPos.needsUpdate = true; fShape.needsUpdate = true; fSeed.needsUpdate = true; }
      flames.visible = flameCount > 0;
      // Smoke: rises while it is hot, slows, swells, and goes down the wind.
      for (let i = puffs.length - 1; i >= 0; i--) {
        const s = puffs[i];
        s.age += step;
        if (s.age >= s.life) { puffs.splice(i, 1); continue; }
        const lift = Math.exp(-s.age / 5);
        s.v.y = lerp(s.v.y, 0.35 + 1.9 * lift, 1 - Math.exp(-step * 0.6));
        s.v.x += (WIND.x * WIND_MPS - s.v.x) * (1 - Math.exp(-step * 0.35));
        s.v.z += (WIND.z * WIND_MPS - s.v.z) * (1 - Math.exp(-step * 0.35));
        s.p.addScaledVector(s.v, step);
        s.rot += s.spin * step;
      }
      if (camera && puffs.length > 1) puffs.sort((a, b) => b.p.distanceToSquared(camPos) - a.p.distanceToSquared(camPos));
      const n = Math.min(puffs.length, budget.smoke);
      if (camera) camera.getWorldQuaternion(q4);
      for (let i = 0; i < n; i++) {
        const s = puffs[i], k = s.age / s.life;
        const size = s.s0 + 3.3 * Math.sqrt(s.age) * (0.8 + 0.3 * s.dark);
        m4.compose(s.p, q4, s4.set(size, size, size));
        smoke.setMatrixAt(i, m4);
        // Dark brown-black from the flames, thinning to a warm grey as it mixes with the air.
        const shade = lerp(lerp(0.06, 0.16, 1 - s.dark), lerp(0.22, 0.4, 1 - s.dark), smooth(s.age / 8));
        smoke.setColorAt(i, col.setRGB(shade * 1.04, shade, shade * 0.95));
        const near = camera ? smooth((s.p.distanceTo(camPos) - 0.35 * size) / (0.9 * size)) : 1;
        const alpha = near * smooth(s.age / 0.7) * (1 - smooth((k - 0.25) / 0.75)) * lerp(0.38, 0.66, s.dark) / (1 + 0.05 * size);
        iPuff.setXYZW(i, alpha, s.glow * Math.exp(-s.age / 0.9), s.tile, s.rot);
      }
      smoke.count = n;
      if (n) { smoke.instanceMatrix.needsUpdate = true; smoke.instanceColor.needsUpdate = true; iPuff.needsUpdate = true; }
      smoke.visible = n > 0;
      // Sparks.
      let m = 0;
      for (let i = sparkList.length - 1; i >= 0; i--) {
        const e = sparkList[i];
        e.age += step;
        if (e.age >= e.life) { sparkList.splice(i, 1); continue; }
        e.w += step * 3;
        e.v.y += (1.2 - e.v.y) * (1 - Math.exp(-step * 0.9));
        e.v.x += (WIND.x * WIND_MPS + Math.sin(e.w) * 1.2 - e.v.x) * (1 - Math.exp(-step * 1.2));
        e.v.z += (WIND.z * WIND_MPS + Math.cos(e.w * 1.3) * 1.2 - e.v.z) * (1 - Math.exp(-step * 1.2));
        e.p.addScaledVector(e.v, step);
      }
      for (const e of sparkList) {
        if (m >= budget.sparks) break;
        sPos.setXYZ(m, e.p.x, e.p.y, e.p.z); sSize.setX(m, e.size); sHeat.setX(m, (1 - e.age / e.life) * (0.6 + 0.4 * Math.sin(e.w * 4) ** 2));
        m++;
      }
      sg.setDrawRange(0, m);
      if (m) { sPos.needsUpdate = true; sSize.needsUpdate = true; sHeat.needsUpdate = true; }
      sparkPoints.visible = m > 0;
      glows.count = glowCount; glows.visible = glowCount > 0;
      if (glowCount) { glows.instanceMatrix.needsUpdate = true; glows.instanceColor.needsUpdate = true; }
    },
    set visible(v) { group.visible = !!v; },
    get visible() { return group.visible; },
    get counts() { return { flames: flameCount, smoke: smoke.count, sparks: sg.drawRange.count, glows: glowCount }; },
    clear() { flameList.length = 0; puffs.length = 0; sparkList.length = 0; glowCount = 0; fg.instanceCount = 0; smoke.count = 0; sg.setDrawRange(0, 0); glows.count = 0; },
    dispose() {
      group.removeFromParent();
      for (const o of [fg, quad, sg, glowGeo, card]) o.dispose();
      for (const o of [flameMat, smokeMat, sparkMat, glowMat]) o.dispose();
    },
  };
  return api;
}

// ── what is left: a heap of charcoal and ash, glowing at first ─────────────────────────────────
const heapMats = new Set();
function heapMaterial() {
  const mat = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.97, metalness: 0, emissive: 0x000000 });
  mat.name = 'fort_fire_heap';
  mat.userData.heat = { value: 1 };
  mat.userData.time = { value: 0 };
  mat.onBeforeCompile = (shader) => {
    shader.uniforms.uHeat = mat.userData.heat; shader.uniforms.uTime = mat.userData.time;
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', '#include <common>\nattribute float aEmber;\nvarying float vEmber;\nvarying vec3 vHeapW;')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\nvEmber = aEmber;\nvHeapW = (modelMatrix * vec4(position, 1.0)).xyz;');
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', `#include <common>\nuniform float uHeat;\nuniform float uTime;\nvarying float vEmber;\nvarying vec3 vHeapW;\n#define FIRE_OCTAVES 2\n${NOISE_GLSL}`)
      .replace('#include <emissivemap_fragment>', `#include <emissivemap_fragment>
        { float n = ffbm(vec3(vHeapW.x * 1.7, vHeapW.z * 1.7, uTime * 0.35));
          float hot = smoothstep(0.42, 0.95, vEmber * 0.75 + n * 0.55) * uHeat;
          float flick = 0.7 + 0.3 * fnoise(vec3(vHeapW.xz * 3.0, uTime * 1.6));
          totalEmissiveRadiance += vec3(1.0, 0.24, 0.035) * hot * hot * flick * 3.2; }`);
  };
  mat.customProgramCacheKey = () => 'fort_fire_heap_v1';
  heapMats.add(mat);
  return mat;
}

/**
 * A heap over `rects` ([{ cx, cz, sx, sz, peak }], world metres, axis-aligned), laid on the
 * ground (`groundAt(x, z)` -> y), with charred timbers lying on it and a few posts left standing.
 */
function buildHeap(rects, groundAt, seed) {
  const rnd = stream(`heap:${seed}`);
  const group = new THREE.Group(); group.name = `fort-fire:heap:${seed}`;
  const mat = heapMaterial();
  for (const r of rects) {
    const sx = r.sx + 1.4, sz = r.sz + 1.4;
    const nx = clamp(Math.round(sx / 0.45), 6, 40), nz = clamp(Math.round(sz / 0.45), 6, 40);
    const geo = new THREE.PlaneGeometry(sx, sz, nx, nz); geo.rotateX(-Math.PI / 2);
    const pos = geo.getAttribute('position'), colors = new Float32Array(pos.count * 3), ember = new Float32Array(pos.count);
    for (let i = 0; i < pos.count; i++) {
      const lx = pos.getX(i), lz = pos.getZ(i);
      const u = lx / (sx / 2), v = lz / (sz / 2);
      const edge = Math.max(Math.abs(u), Math.abs(v));
      const lumpy = 0.55 + 0.45 * Math.sin(lx * 1.9 + seed.length) * Math.cos(lz * 2.3) + (rnd() - 0.5) * 0.5;
      const mound = (1 - smooth((edge - 0.45) / 0.55)) * (0.7 + 0.3 * (1 - Math.min(1, Math.hypot(u, v))));
      const h = r.peak * mound * clamp(lumpy, 0.15, 1.3);
      const x = r.cx + lx, z = r.cz + lz;
      pos.setXYZ(i, x, groundAt(x, z) + h - 0.04, z);
      // Charcoal black where the timbers lay, grey and white ash over it, and the scorched
      // ground at the edge.
      const ash = smooth((rnd() * 0.7 + lumpy * 0.5 - 0.45) / 0.5) * (1 - smooth((edge - 0.75) / 0.25));
      const scorched = smooth((edge - 0.8) / 0.2);
      const c0 = [0.028 + rnd() * 0.02, 0.025 + rnd() * 0.016, 0.022 + rnd() * 0.014];
      const ashC = [0.15 + rnd() * 0.07, 0.145 + rnd() * 0.065, 0.135 + rnd() * 0.06]; // linear: a mid grey, not snow
      const earth = [0.11, 0.085, 0.06];
      for (let k = 0; k < 3; k++) colors[i * 3 + k] = lerp(lerp(c0[k], ashC[k], ash * 0.8), earth[k], scorched);
      ember[i] = (1 - smooth((edge - 0.25) / 0.6)) * (0.4 + 0.6 * rnd()) * (1 - ash * 0.6);
    }
    geo.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    geo.setAttribute('aEmber', new THREE.BufferAttribute(ember, 1));
    geo.computeVertexNormals();
    const mesh = new THREE.Mesh(geo, mat); mesh.receiveShadow = true; mesh.castShadow = false;
    group.add(mesh);
  }
  // The timbers that did not burn through: lying on the heap at all angles, and at a corner or
  // two a post still standing, black.
  const beams = [];
  for (const r of rects) {
    const n = clamp(Math.round((r.sx * r.sz) / 5), 3, 16);
    for (let i = 0; i < n; i++) beams.push({ r, stand: false });
    if (r.post) for (let i = 0; i < 2; i++) beams.push({ r, stand: true });
  }
  if (beams.length) {
    const timber = new THREE.BoxGeometry(1, 1, 1);
    const char = new THREE.MeshStandardMaterial({ color: 0x0b0908, roughness: 0.92, metalness: 0, emissive: 0x000000 });
    char.name = 'fort_fire_timber';
    const inst = new THREE.InstancedMesh(timber, char, beams.length);
    const m = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler(), s = new THREE.Vector3(), p = new THREE.Vector3();
    beams.forEach((b, i) => {
      const { r } = b;
      const x = r.cx + (rnd() - 0.5) * r.sx * (b.stand ? 1.0 : 0.85), z = r.cz + (rnd() - 0.5) * r.sz * (b.stand ? 1.0 : 0.85);
      if (b.stand) {
        const h = 1.2 + rnd() * 1.6;
        e.set((rnd() - 0.5) * 0.35, rnd() * 6.28, (rnd() - 0.5) * 0.35);
        p.set(x, groundAt(x, z) + h / 2 - 0.1, z); s.set(0.2, h, 0.2);
      } else {
        const len = 1.2 + rnd() * Math.min(3.4, Math.max(r.sx, r.sz) * 0.6);
        e.set((rnd() - 0.5) * 0.5, rnd() * 6.28, (rnd() - 0.5) * 0.25);
        p.set(x, groundAt(x, z) + r.peak * (0.3 + rnd() * 0.5), z); s.set(len, 0.18 + rnd() * 0.1, 0.2 + rnd() * 0.1);
      }
      m.compose(p, q.setFromEuler(e), s);
      inst.setMatrixAt(i, m);
    });
    inst.castShadow = true; inst.receiveShadow = true;
    group.add(inst);
  }
  group.userData.material = mat;
  return group;
}

// ── the burn ───────────────────────────────────────────────────────────────────────────────────

/** The palisade archetypes burn as a line of pickets; anything else as a building. */
const PICKET_LIKE = /pickets|palisade|covered_way/;

/**
 * The burn of a stage's buildings. `buildings` is the buildings layer (its `batches`, each with
 * `userData.batchIndex` naming the structure each instance draws); `groundAt(x, z)` the ground's
 * height at a world point; `extras(id)` any other objects drawn for a structure (a fort's hung
 * gates), brought down with it; `nameOf(id)` what the visitor is told they lit. `buildings` may
 * be a function that returns the layer (a detail switch builds a new one).
 */
export function createFortFire({ parent, buildings, groundAt = () => 0, extras = () => [], nameOf = (id) => id, tier = () => 'full', onChange = () => {}, setup = () => null } = {}) {
  let undo = null;
  let fx = null, spec = null, clock = 0, burns = [], torch = null, torchReach = 0, torchKindle = null;
  const v3 = new THREE.Vector3(), box = new THREE.Box3(), m4 = new THREE.Matrix4(), w4 = new THREE.Matrix4(), inv = new THREE.Matrix4();
  const col = new THREE.Color(), col2 = new THREE.Color(), gv = new THREE.Vector3(), av = new THREE.Vector3(), m4id = new THREE.Matrix4();

  /** Every instance the batches draw for `id`, with its placement and paint as they were. */
  function piecesOf(id) {
    const out = [];
    const layer = typeof buildings === 'function' ? buildings() : buildings;
    for (const batch of layer?.batches ?? []) {
      const idx = batch.userData?.batchIndex;
      if (!idx) continue;
      for (let i = 0; i < idx.length; i++) {
        if (idx[i] !== id) continue;
        const matrix = batch.getMatrixAt(i, new THREE.Matrix4());
        const paint = batch.getColorAt(i, new THREE.Color());
        const visible = batch.getVisibleAt ? batch.getVisibleAt(i) : true;
        let b = null;
        try { b = batch.getBoundingBoxAt(batch.getGeometryIdAt(i), new THREE.Box3()); } catch { b = null; }
        if (b) b.applyMatrix4(matrix).applyMatrix4(batch.matrixWorld);
        out.push({ batch, i, matrix, paint, visible, box: b, cy: b ? (b.min.y + b.max.y) / 2 : 0 });
      }
    }
    return out;
  }

  function emittersFor(b, rnd) {
    const out = [], s = fx.budget.spacing;
    const { min, max } = b.box, ground = b.ground, H = Math.max(1, max.y - ground);
    const add = (x, y, z, nx, nz, kind, w, h) => out.push({ x, y, z, nx, nz, kind, w, h, seed: rnd() * 100, reach: 0, life: BURN.hold_s * (0.75 + 0.5 * rnd()), jitter: rnd() * 3 });
    const sides = [
      [[min.x, min.z], [max.x, min.z], 0, -1], [[max.x, min.z], [max.x, max.z], 1, 0],
      [[max.x, max.z], [min.x, max.z], 0, 1], [[min.x, max.z], [min.x, min.z], -1, 0],
    ];
    if (b.kind === 'pickets') {
      // A line of pickets burns along its foot and up the stakes, both faces.
      const sp = 2.3 * s;
      for (const [a, z, nx, nz] of sides) {
        const L = Math.hypot(z[0] - a[0], z[1] - a[1]); const k = Math.max(1, Math.round(L / sp));
        if (L < 4 && b.box.max.x - b.box.min.x > 4 && b.box.max.z - b.box.min.z > 4 && b.id.includes('covered_way')) continue;
        for (let i = 0; i < k; i++) {
          // Never in step: the stakes burn in clumps, some high, some low.
          const f = clamp((i + 0.5 + (rnd() - 0.5) * 0.8) / k, 0, 1), x = lerp(a[0], z[0], f), zz = lerp(a[1], z[1], f);
          const side = rnd() < 0.5 ? 1 : -1, big = rnd();
          add(x + nx * 0.25 * side, groundAt(x, zz) + 0.05, zz + nz * 0.25 * side, nx, nz, 'picket', (1.5 + 1.6 * big) * s, H * (0.7 + 0.9 * big * big + 0.25 * rnd()));
        }
      }
      return out;
    }
    // A building: along the foot of each wall (doors, windows, the logs' seams), and over its roof.
    const sp = 2.4 * s;
    for (const [a, z, nx, nz] of sides) {
      const L = Math.hypot(z[0] - a[0], z[1] - a[1]); const k = Math.max(1, Math.round(L / sp));
      for (let i = 0; i < k; i++) {
        const f = (i + 0.5) / k, x = lerp(a[0], z[0], f), zz = lerp(a[1], z[1], f);
        const big = rnd(); add(x + nx * 0.35, groundAt(x, zz) + 0.1, zz + nz * 0.35, nx, nz, 'wall', (1.8 + 1.4 * big) * s, H * (0.4 + 0.45 * big * big));
      }
    }
    const sx = max.x - min.x, sz = max.z - min.z;
    const kx = Math.max(1, Math.round((sx - 1) / (2.6 * s))), kz = Math.max(1, Math.round((sz - 1) / (2.6 * s)));
    for (let i = 0; i < kx; i++) for (let j = 0; j < kz; j++) {
      const x = min.x + 0.6 + (sx - 1.2) * (i + 0.5) / kx, z = min.z + 0.6 + (sz - 1.2) * (j + 0.5) / kz;
      add(x, ground + H * 0.66, z, 0, 0, 'roof', (4.6 + 2.4 * rnd()) * s, H * (0.95 + 0.6 * rnd()));
    }
    return out;
  }

  function prepare(id, kind) {
    const pieces = piecesOf(id);
    if (!pieces.length) return null;
    const bb = new THREE.Box3();
    for (const p of pieces) if (p.box && p.visible) bb.union(p.box);
    if (bb.isEmpty()) for (const p of pieces) if (p.box) bb.union(p.box);
    if (bb.isEmpty()) return null;
    const cx = (bb.min.x + bb.max.x) / 2, cz = (bb.min.z + bb.max.z) / 2;
    const ground = Math.max(bb.min.y, groundAt(cx, cz) - 0.3);
    const ext = extras(id).map((o) => {
      // A house door's hung leaf (house-doors.js) blackens with its building's walls.
      const paints = [];
      o.traverse?.((m) => { if (m.isMesh && /^house-door-leaf:/.test(m.name) && m.material?.color && !paints.some((x) => x.mat === m.material)) paints.push({ mat: m.material, color: m.material.color.clone() }); });
      return { o, matrix: o.matrix.clone(), auto: o.matrixAutoUpdate, paints };
    });
    const lo = Math.min(...pieces.map((p) => p.cy)), hi = Math.max(...pieces.map((p) => p.cy));
    for (const p of pieces) p.hfrac = hi > lo ? (p.cy - lo) / (hi - lo) : 0.5; // 1 the roof's ridge, 0 the sills
    const b = { id, kind: PICKET_LIKE.test(id) ? 'pickets' : kind, pieces, extras: ext, box: bb, ground, lit: null, from: null,
      emitters: [], heap: null, fallStart: Infinity, down: 0, char: 0, heat: 0, name: nameOf(id), rnd: stream(`burn:${id}`) };
    b.emitters = kind === 'stands' ? [] : emittersFor(b, b.rnd);
    b.tilt = new THREE.Vector3(b.rnd() - 0.5, 0, b.rnd() - 0.5).normalize();
    return b;
  }

  /** Light `b` at `at` (world; its nearest point to it): the fire runs out over it from there. */
  function light(b, at, t = clock) {
    if (!b || b.lit !== null || b.kind === 'stands') return false;
    b.lit = t;
    const p = at ? b.box.clampPoint(at, new THREE.Vector3()) : b.box.getCenter(new THREE.Vector3());
    b.from = p;
    let last = 0;
    for (const e of b.emitters) {
      const d = Math.hypot(e.x - p.x, (e.kind === 'roof' ? b.ground : e.y) - p.y, e.z - p.z);
      e.reach = d / BURN.spread_mps * (e.kind === 'picket' ? 0.55 : 1) + e.jitter + (e.kind === 'roof' ? BURN.roof_lag_s : 0);
      last = Math.max(last, e.reach);
    }
    b.involved = last;
    b.fallStart = last + (b.kind === 'pickets' ? BURN.hold_s * 0.55 : BURN.fall_after_s) + b.rnd() * 6;
    onChange({ lit: b.id });
    return true;
  }

  function intensity(e, te) {
    if (te < 0) return 0;
    const up = smooth(te / BURN.rise_s);
    const down = te > e.life ? 1 - smooth((te - e.life) / BURN.fade_s) : 1;
    return up * Math.max(0.05, down);
  }

  /** The buildings' pieces where the burn has them: blackened, and coming down. */
  function fallOf(b) {
    const t = b.lit === null ? -1 : clock - b.lit;
    return (t - b.fallStart) / (b.kind === 'pickets' ? BURN.fall_s * 2.2 : BURN.fall_s);
  }
  function pose(b) {
    const t = b.lit === null ? -1 : clock - b.lit;
    const fallT = fallOf(b);
    for (const p of b.pieces) {
      // Blackened from where it caught, the roof last; the magazine only smoked.
      let c;
      if (b.kind === 'stands') c = b.char;
      else c = t < 0 ? 0 : smooth((t - 4 - p.hfrac * 10) / ((b.involved ?? 20) * 0.6 + 18));
      const k = b.kind === 'stands' ? 0 : smooth(fallT * 1.15 - (1 - p.hfrac) * 0.25);
      if (p.paint && Math.abs(c - (p.c ?? -1)) > 0.004) {
        p.c = c;
        col.copy(p.paint).lerp(col2.copy(p.paint).multiply(b.kind === 'stands' ? SOOT : CHAR), c);
        p.batch.setColorAt(p.i, col);
      }
      const kk = k >= 0.999 ? 1 : k <= 0 ? 0 : k;
      if (kk === p.k) continue;
      p.k = kk;
      if (kk === 1) p.batch.setMatrixAt(p.i, m4.makeScale(0, 0, 0));
      else if (kk === 0) p.batch.setMatrixAt(p.i, p.matrix);
      else p.batch.setMatrixAt(p.i, fallMatrix(b, kk, p.batch, m4).multiply(p.matrix));
    }
    const leafChar = t < 0 ? 0 : smooth((t - 6) / ((b.involved ?? 20) * 0.6 + 18));
    for (const x of b.extras) {
      for (const q of x.paints) q.mat.color.copy(q.color).lerp(col2.copy(q.color).multiply(CHAR), leafChar);
      if (b.down >= 0.999) { x.o.visible = false; continue; }
      x.o.visible = true;
      x.o.matrixAutoUpdate = false;
      // The fall is in world metres; a gate's holder sits in its own parent's frame.
      if (b.down > 0) {
        fallMatrix(b, b.down, null, m4);
        const pw = x.o.parent?.matrixWorld;
        if (pw && !pw.equals(m4id)) m4.premultiply(inv.copy(pw).invert()).multiply(pw);
        x.o.matrix.copy(m4.multiply(x.matrix));
      } else x.o.matrix.copy(x.matrix);
      x.o.updateMatrixWorld(true);
    }
  }

  /** The placement that brings a building's piece down `k` of the way: sinking where it stood,
   *  crushed down on its sills, leaning a little the way it falls. In the batch's own frame. */
  function fallMatrix(b, k, batch, out) {
    const H = b.box.max.y - b.ground;
    gv.set((b.box.min.x + b.box.max.x) / 2, b.ground, (b.box.min.z + b.box.max.z) / 2);
    const squash = lerp(1, 0.18, smooth(k * 1.2));
    const sink = H * 0.55 * k * k;
    out.makeTranslation(-gv.x, -gv.y, -gv.z);
    out.premultiply(w4.makeScale(1, squash, 1));
    out.premultiply(w4.makeRotationAxis(av.set(b.tilt.z, 0, -b.tilt.x).normalize(), 0.12 * k));
    out.premultiply(w4.makeTranslation(gv.x, gv.y - sink, gv.z));
    if (batch && !batch.matrixWorld.equals(m4id)) { inv.copy(batch.matrixWorld).invert(); out.premultiply(inv).multiply(batch.matrixWorld); }
    return out;
  }

  function heapFor(b) {
    const { min, max } = b.box, sx = max.x - min.x, sz = max.z - min.z, H = max.y - b.ground;
    let rects;
    if (b.kind === 'pickets') {
      const w = 1.1, peak = 0.22;
      if (b.id.includes('covered_way')) rects = [{ cx: (min.x + max.x) / 2, cz: (min.z + max.z) / 2, sx: Math.max(w, sx), sz: Math.max(w, sz), peak }];
      else rects = [
        { cx: (min.x + max.x) / 2, cz: min.z, sx, sz: w, peak }, { cx: (min.x + max.x) / 2, cz: max.z, sx, sz: w, peak },
        { cx: min.x, cz: (min.z + max.z) / 2, sx: w, sz, peak }, { cx: max.x, cz: (min.z + max.z) / 2, sx: w, sz, peak },
      ];
    } else rects = [{ cx: (min.x + max.x) / 2, cz: (min.z + max.z) / 2, sx, sz, peak: clamp(0.25 + H * 0.085, 0.3, 1.1), post: sx * sz > 15 }];
    const heap = buildHeap(rects, groundAt, b.id);
    heap.scale.y = 0.01;
    // Scaled about the ground, not the origin.
    heap.position.y = 0;
    fx.group.add(heap);
    return heap;
  }

  const api = {
    get active() { return !!spec; },
    get clock() { return clock; },
    get fx() { return fx; },
    /** Take up a stage's `fire`: { burns: [ids], stands: [ids], start_s, lit: [ids] (lit at the
     *  start, at their centres), visitor }. */
    start(next, { camera = null } = {}) {
      api.clear();
      if (!next || !Array.isArray(next.burns) || !next.burns.length) return api;
      spec = next;
      fx ??= createFireFx(parent, { tier: tier() });
      try { undo = setup(next) ?? null; } catch { undo = null; }
      burns = [];
      for (const id of next.burns) { const b = prepare(id, 'building'); if (b) burns.push(b); }
      for (const id of next.stands ?? []) { const b = prepare(id, 'stands'); if (b) burns.push(b); }
      // Who catches from whom: each pair near enough, and how long the heat takes to carry.
      for (const b of burns) {
        b.near = [];
        for (const o of burns) {
          if (o === b) continue;
          const gap = Math.max(0, Math.max(b.box.min.x - o.box.max.x, o.box.min.x - b.box.max.x, b.box.min.z - o.box.max.z, o.box.min.z - b.box.max.z));
          if (gap <= BURN.catch_gap_m) b.near.push({ o, delay: 12 + gap * 3.5 + b.rnd() * 6 });
        }
      }
      clock = 0;
      const ahead = Number.isFinite(next.start_s) ? next.start_s : 0;
      // A fire already burning when the visitor comes: lit a little apart, and run on `start_s`
      // seconds (unseen) to where it has got to.
      for (const id of next.lit ?? []) { const b = burns.find((x) => x.id === id); if (b) light(b, null, -12 * b.rnd()); }
      if (ahead > 0) {
        for (let t = 0; t < ahead; t += 0.5) api.update(0.5, null, { quiet: true });
        for (const b of burns) if (b.lit !== null) b.lit -= clock;
        clock = 0;
      }
      return api;
    },
    /** `id` catches, at `at` (world) or its middle. */
    ignite(id, at = null) { return light(burns.find((b) => b.id === id), at); },
    /** The visitor puts a torch to the nearest of the fort's unlit buildings within `reach` metres
     *  of `at` (world): { lit, name } or { none: 'far' | 'all' }. */
    kindle(at, reach = 30) {
      const left = burns.filter((b) => b.lit === null && b.kind !== 'stands');
      if (!left.length) return { none: 'all' };
      let best = null, far = Infinity;
      for (const b of left) { const d = b.box.distanceToPoint(at); if (d < far) { far = d; best = b; } }
      if (!best || far > reach) return { none: 'far', nearest: best?.name ?? null, distance: Math.round(far) };
      torchKindle = { b: best, at: at.clone(), t: 0 };
      return { lit: best.id, name: best.name };
    },
    /** The visitor's own torch, held low at the right of the view while they are at the stop. */
    holdTorch(on) { torchReach = on ? 1 : 0; return api; },
    update(dt, camera = null, { quiet = false } = {}) {
      if (!spec || !fx) return;
      const step = Number.isFinite(dt) && dt > 0 ? dt : 0;
      clock += step;
      fx.begin();
      const rnd = Math.random;
      let smokeRate = 0, sparkRate = 0;
      const live = [];
      for (const b of burns) {
        if (b.kind === 'stands') {
          // Smoked by the fires round it, never alight.
          const heat = Math.max(0, ...b.near.map(({ o }) => o.heat));
          b.char = Math.min(1, b.char + step * heat / 70);
          if (!quiet) pose(b);
          continue;
        }
        if (b.lit === null) {
          if (!quiet) pose(b);
          continue;
        }
        const t = clock - b.lit;
        let heat = 0;
        const down = b.down = smooth(fallOf(b));
        for (const e of b.emitters) {
          const I = intensity(e, t - e.reach) * (1 - down * (e.kind === 'roof' ? 1 : 0.75));
          if (I <= 0.02) continue;
          heat += I;
          // As the building comes down its flames come down with it, onto the heap.
          const y = lerp(e.y, b.ground + 0.15, down);
          const h = e.h * (0.45 + 0.55 * I) * (1 - 0.55 * down) * (0.86 + 0.14 * Math.sin(clock * 1.7 + e.seed) + 0.08 * Math.sin(clock * 4.3 + e.seed * 2.1));
          fx.flame(e.x, y, e.z, e.w * (0.7 + 0.3 * I), h, 0.55 + 0.55 * I, e.seed);
          live.push({ e, b, I, top: y + h * 0.8 });
        }
        b.heat = b.emitters.length ? clamp(heat / (b.emitters.length * 0.55), 0, 1) : 0;
        // The heap: it rises as the building comes down, glows, flames low, and goes grey.
        if (down > 0.2 && !b.heap) b.heap = heapFor(b);
        if (b.heap) {
          b.heap.scale.y = Math.max(0.01, smooth((down - 0.2) / 0.8));
          const after = Math.max(0, t - b.fallStart - BURN.fall_s * 0.6);
          const glow = (1 - smooth(after / BURN.heap_s)) * 0.9 + 0.08;
          b.heap.userData.material.userData.heat.value = glow * smooth((down - 0.3) / 0.5);
          b.heap.userData.material.userData.time.value = clock;
          if (down > 0.5) {
            const { min, max } = b.box;
            const n = b.kind === 'pickets' ? 6 : 5;
            for (let i = 0; i < n; i++) {
              const hr = stream(`${b.id}:h${i}`);
              const x = lerp(min.x, max.x, 0.15 + 0.7 * hr()), z = lerp(min.z, max.z, 0.15 + 0.7 * hr());
              const I = glow * (0.55 + 0.45 * hr()) * smooth((down - 0.5) / 0.4);
              if (I < 0.12) continue;
              fx.flame(x, groundAt(x, z) + 0.1, z, 1.6, 0.6 + 1.6 * I, 0.6 + 0.4 * I, hr() * 100);
              live.push({ e: { x, z, kind: 'heap', nx: 0, nz: 0 }, b, I: I * 0.7, top: groundAt(x, z) + 0.6 + 1.2 * I });
            }
            // Grey smoke goes up from the heap for as long as it lies there.
            smokeRate += 0.6 + 2.5 * glow;
            if (rnd() < step * (0.8 + 2 * glow)) {
              const x = lerp(min.x, max.x, rnd()), z = lerp(min.z, max.z, rnd());
              fx.smoke({ x, y: groundAt(x, z) + 0.6, z }, { dark: 0.2 + 0.5 * glow, glow: glow * 0.5, size: 1.4, up: 1.2 + glow, life: 18 });
            }
          }
        }
        if (b.heat > 0.05) {
          const c = b.box.getCenter(v3);
          fx.glow(c.x, b.ground, c.z, Math.max(b.box.max.x - b.box.min.x, b.box.max.z - b.box.min.z) + 4, b.heat * (0.85 + 0.15 * Math.sin(clock * 11 + c.x)));
        }
        // The heat carries to its neighbours.
        for (const { o, delay } of b.near) {
          if (o.lit !== null || o.kind === 'stands') continue;
          if (t > delay && b.heat > 0.25) light(o, b.box.getCenter(new THREE.Vector3()));
        }
        if (!quiet) pose(b);
      }
      // Smoke and sparks from the flames, the budget shared out by how hard each burns.
      if (live.length) {
        const total = live.reduce((s, x) => s + x.I, 0);
        const perSecond = fx.budget.smoke / 15 * Math.min(1, total / 14);
        const sparksPerSecond = fx.budget.sparks / 2.6 * Math.min(1, total / 10);
        const pick = () => { let r = rnd() * total; for (const x of live) { r -= x.I; if (r <= 0) return x; } return live[live.length - 1]; };
        let n = perSecond * step; while (n > 0) { if (n >= 1 || rnd() < n) { const x = pick();
          fx.smoke({ x: x.e.x + x.e.nx * 0.4, y: x.top, z: x.e.z + x.e.nz * 0.4 }, { dark: 0.55 + 0.45 * x.I, glow: 0.4 + 0.6 * x.I, size: 1.6 + 1.6 * x.I, up: 1.8 + 1.6 * x.I }); } n -= 1; }
        let m = sparksPerSecond * step; while (m > 0) { if (m >= 1 || rnd() < m) { const x = pick(); fx.sparks({ x: x.e.x, y: x.top - 0.5, z: x.e.z }, 1, { up: 3 + 4 * x.I }); } m -= 1; }
      }
      // The visitor's torch: held, and put to the building they chose.
      if (torchKindle) {
        torchKindle.t += step;
        if (torchKindle.t > 0.65 && torchKindle.b.lit === null) light(torchKindle.b, torchKindle.at);
        if (torchKindle.t > 1.2) torchKindle = null;
      }
      if (torchReach && camera && !quiet) {
        torch ??= makeTorch(fx.group);
        torch.visible = true;
        const lunge = torchKindle ? Math.sin(Math.min(1, torchKindle.t / 1.2) * Math.PI) : 0;
        camera.updateMatrixWorld();
        // Held where it reads the same at any field of view (the app's is narrower than 60 degrees).
        const reach = camera.isPerspectiveCamera ? Math.tan(Math.PI / 6) / Math.tan(THREE.MathUtils.degToRad(camera.fov) / 2) : 1;
        // A phone held upright sees far less to either side: the brand comes in toward the middle.
        const side = 0.4 * clamp((camera.aspect ?? 1.6) / 1.6, 0.32, 1);
        torch.position.set(side, -0.5 + 0.1 * lunge, -1.3 - 0.5 * lunge).multiplyScalar(reach).applyMatrix4(camera.matrixWorld);
        torch.quaternion.setFromRotationMatrix(camera.matrixWorld).multiply(TORCH_TILT);
        torch.scale.setScalar((camera.aspect ?? 1.6) < 1 ? 0.72 : 1);
        torch.updateMatrixWorld(true);
        const tip = torch.userData.tip.getWorldPosition(new THREE.Vector3());
        fx.flame(tip.x, tip.y - 0.04, tip.z, 0.2, 0.36, 0.95, 7.7, true);
        if (rnd() < step * 3) fx.smoke(tip, { n: 1, dark: 0.55, glow: 0.6, size: 0.25, up: 0.9, life: 4, spread: 0.05 });
        if (rnd() < step * 4) fx.sparks(tip, 1, { up: 1.5, spread: 0.1 });
      } else if (torch) torch.visible = false;
      for (const x of extraFlames) fx.flame(x.x, x.y, x.z, x.w, x.h, x.heat, x.seed, true);
      extraFlames.length = 0;
      fx.update(step, quiet ? null : camera);
    },
    /** A flame for this frame only (a castmate's torch). */
    flameNow(at, { w = 0.3, h = 0.5, heat = 0.95, seed = 3.3 } = {}) { extraFlames.push({ x: at.x, y: at.y, z: at.z, w, h, heat, seed }); },
    smokeNow(at, opts) { fx?.smoke(at, opts); },
    sparksNow(at, n, opts) { fx?.sparks(at, n, opts); },
    clear() {
      for (const b of burns) {
        for (const p of b.pieces) { p.batch.setMatrixAt(p.i, p.matrix); if (p.paint) p.batch.setColorAt(p.i, p.paint); }
        for (const x of b.extras) { x.o.matrix.copy(x.matrix); x.o.matrixAutoUpdate = x.auto; x.o.visible = true; x.o.updateMatrixWorld(true); for (const q of x.paints) q.mat.color.copy(q.color); }
        if (b.heap) { b.heap.removeFromParent(); b.heap.traverse((o) => { if (o.isMesh) { o.geometry.dispose(); if (o.material !== b.heap.userData.material) o.material.dispose(); } }); heapMats.delete(b.heap.userData.material); b.heap.userData.material.dispose(); }
      }
      burns = []; spec = null; clock = 0; torchKindle = null; torchReach = 0;
      try { undo?.(); } catch { /* given back as far as it goes */ }
      undo = null;
      if (torch) torch.visible = false;
      fx?.clear();
    },
    dispose() { api.clear(); fx?.dispose(); fx = null; },
    snapshot() {
      return { clock: +clock.toFixed(1), ...(fx ? fx.counts : {}), burns: burns.map((b) => ({ id: b.id, kind: b.kind,
        lit: b.lit === null ? null : +b.lit.toFixed(1), heat: +b.heat.toFixed(2), down: +b.down.toFixed(2), char: +(b.kind === 'stands' ? b.char : b.lit === null ? 0 : smooth((clock - b.lit - 4) / ((b.involved ?? 20) * 0.6 + 18))).toFixed(2),
        heap: !!b.heap })) };
    },
  };
  const extraFlames = [];
  return api;
}

const TORCH_TILT = new THREE.Quaternion().setFromEuler(new THREE.Euler(0.55, 0.1, -0.25));
/** A firebrand: a split pine stick with a head of bark and pitch wound on it. */
function makeTorch(parent) {
  const g = new THREE.Group(); g.name = 'fort-fire:torch';
  const wood = new THREE.MeshStandardMaterial({ color: 0x5a3c22, roughness: 0.85 });
  const head = new THREE.MeshStandardMaterial({ color: 0x1a120c, roughness: 0.9, emissive: 0x2a0800 });
  const stick = new THREE.Mesh(new THREE.CylinderGeometry(0.016, 0.022, 0.62, 7), wood); stick.position.y = 0.0;
  const knot = new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.035, 0.16, 8), head); knot.position.y = 0.36;
  const tip = new THREE.Object3D(); tip.position.y = 0.44;
  g.add(stick, knot, tip);
  g.userData.tip = tip;
  for (const o of [stick, knot]) { o.castShadow = false; o.renderOrder = 8; }
  parent.add(g);
  return g;
}

