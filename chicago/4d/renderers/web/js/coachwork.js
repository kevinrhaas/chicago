// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * Each carriage its own (Kevin, 2026-11-13, of the 1904 carriages on their loops): "make
 * the carriages look different ... other things that might make each of them look
 * unique, i imagine they were typically black".
 *
 * One brougham model drives every 1904 loop, so a driven row's `vehicle_finish` makes the
 * coach its own with NO texture (1904's phone memory is at its ceiling) and no new
 * geometry:
 *
 *  - its paint: the panels, the body's black timber, the running gear (wheels, pole,
 *    springs) and the trim each take the row's colour, and its lacquer is glossy or
 *    dulled by the row's age;
 *  - road dust and dried mud, thickest at the bottom of the body and thrown up the
 *    lower panels in splashes, and caked round each wheel's tyre and felloe (on the
 *    wheel, so it turns with it);
 *  - scuffs and rubbed places in the lacquer, fine horizontal marks most where boots,
 *    kerbs and harness meet a coach: the step, the lower panels, the shafts and pole.
 *
 * Every mark is placed by the row's own seed (a string, hashed), so no two coaches carry
 * the same marks, and none changes across a reload. Per-coach differences are UNIFORMS,
 * never code, so every coach compiles one program; the cache key names the chain, as
 * confidence.js requires of a hook it chains beneath (see fabric.js).
 *
 * The colours, wear and marks are reconstructed authoring choices: the 1893 Studebaker
 * catalogue shows the type, not these coaches (liberty L-1904-more-carriages-3555).
 */
import * as THREE from 'three';

const KEY = 'chicago-coachwork-v1';
const WHEELS = /^vehicle_wheel_/;
// The brougham's own material names (renderers/web/transport/parked-brougham/brougham.json).
const ROLE_OF = [
  [/lacquer/, 'panels'],
  [/painted_coach_timber/, 'timber'],
  [/upholstery|leather/, 'upholstery'],
  [/bright_trim/, 'trim'],
  [/quarter_surface/, 'quarter'],
  [/iron/, 'iron'],
  [/glass/, 'glass'],
];
export const FINISH_KEYS = Object.freeze(['panels', 'timber', 'gear', 'quarter', 'upholstery', 'trim', 'trim_metalness',
  'gloss', 'dust', 'scuffs', 'seed', 'dust_rgb', 'grade', 'liberty', 'basis']);

const rgb = (v, label) => {
  if (!Array.isArray(v) || v.length !== 3 || !v.every(n => Number.isFinite(n) && n >= 0 && n <= 1)) throw Error(`coachwork: ${label} must be three linear channels in [0, 1]`);
  return v;
};
const unit = (v, label) => {
  if (!Number.isFinite(v) || v < 0 || v > 1) throw Error(`coachwork: ${label} must be in [0, 1]`);
  return v;
};

/** A finish, checked: colours in linear RGB, gloss/dust/scuffs in [0, 1], a seed string. */
export function readFinish(finish) {
  if (!finish || typeof finish !== 'object') throw Error('coachwork: a finish object required');
  for (const key of Object.keys(finish)) if (!FINISH_KEYS.includes(key)) throw Error(`coachwork: unknown finish key ${key}`);
  if (typeof finish.seed !== 'string' || !finish.seed) throw Error('coachwork: a seed string required');
  for (const key of ['panels', 'timber', 'gear', 'quarter', 'upholstery', 'trim', 'dust_rgb']) if (finish[key] != null) rgb(finish[key], key);
  for (const key of ['gloss', 'dust', 'scuffs', 'trim_metalness']) if (finish[key] != null) unit(finish[key], key);
  return finish;
}

/** FNV-1a of the seed, as three offsets for the noise (metres of pattern space). */
export function seedOffsets(seed) {
  let h = 0x811c9dc5;
  for (let i = 0; i < seed.length; i++) { h ^= seed.charCodeAt(i); h = Math.imul(h, 0x01000193) >>> 0; }
  const next = () => { h ^= h >>> 15; h = Math.imul(h, 0x2c1b3c6d) >>> 0; h ^= h >>> 12; h = Math.imul(h, 0x297a2d39) >>> 0; h ^= h >>> 15; return (h >>> 0) / 4294967296; };
  return [next() * 97, next() * 97, next() * 97];
}

const VERTEX = `
  vChiCoachP = ( chiCoachFrame * vec4( transformed, 1.0 ) ).xyz;`;
const DECLARE = `
uniform vec4 chiCoach;      // dust, scuffs, dulled lacquer, mode (0 body, 1 wheel, 2 no marks)
uniform vec4 chiCoachSeed;  // seed offsets, wheel radius
uniform vec3 chiCoachDust;
varying vec3 vChiCoachP;
float chiCoachHash( vec3 p ) {
  p = fract( p * 0.3183099 + vec3( 0.71, 0.113, 0.419 ) );
  p *= 17.0;
  return fract( p.x * p.y * p.z * ( p.x + p.y + p.z ) );
}
float chiCoachNoise( vec3 x ) {
  vec3 i = floor( x ), f = fract( x );
  f = f * f * ( 3.0 - 2.0 * f );
  return mix( mix( mix( chiCoachHash( i ), chiCoachHash( i + vec3( 1.0, 0.0, 0.0 ) ), f.x ),
                   mix( chiCoachHash( i + vec3( 0.0, 1.0, 0.0 ) ), chiCoachHash( i + vec3( 1.0, 1.0, 0.0 ) ), f.x ), f.y ),
              mix( mix( chiCoachHash( i + vec3( 0.0, 0.0, 1.0 ) ), chiCoachHash( i + vec3( 1.0, 0.0, 1.0 ) ), f.x ),
                   mix( chiCoachHash( i + vec3( 0.0, 1.0, 1.0 ) ), chiCoachHash( i + vec3( 1.0, 1.0, 1.0 ) ), f.x ), f.y ), f.z );
}
`;
// After the paint's colour is known: dust and mud, then scuffs; the roughness they add
// is kept for the roughness step below.
const COLOR = `
  float chiCoachRough = 0.0;
  if ( chiCoach.w < 1.5 ) {
    vec3 p = vChiCoachP + chiCoachSeed.xyz;
    float lift;
    if ( chiCoach.w < 0.5 ) {
      // Up from the road: the vehicle frame's y is height above the ground it stands on.
      float h = vChiCoachP.y;
      lift = smoothstep( 0.95, 0.2, h );
      // Splashes thrown up by the wheels, longer than high.
      float splash = smoothstep( 0.6, 0.82, chiCoachNoise( p * vec3( 7.0, 19.0, 7.0 ) ) ) * smoothstep( 1.25, 0.35, h );
      lift = max( lift * ( 0.55 + 0.45 * chiCoachNoise( p * 2.3 ) ), splash );
    } else {
      // Round the tyre and felloe, on the wheel itself (it turns with it).
      float r = length( vChiCoachP.yz ) / max( chiCoachSeed.w, 0.1 );
      lift = smoothstep( 0.7, 0.97, r ) * ( 0.6 + 0.4 * chiCoachNoise( p * 6.0 ) ) + 0.25 * smoothstep( 0.35, 0.0, r );
    }
    float dust = clamp( chiCoach.x * lift, 0.0, 1.0 );
    diffuseColor.rgb = mix( diffuseColor.rgb, chiCoachDust * ( 0.8 + 0.4 * chiCoachNoise( p * 31.0 ) ), dust * 0.85 );
    // Scuffs: fine marks along the coach, most low down where boots, kerbs and harness rub.
    float along = vChiCoachP.x * 0.6 + vChiCoachP.z * 2.1;
    float mark = smoothstep( 0.78, 0.93, chiCoachNoise( vec3( along * 3.0, vChiCoachP.y * 70.0, 0.5 ) + chiCoachSeed.xyz ) );
    float where = smoothstep( 0.45, 0.75, chiCoachNoise( p * 1.7 + 3.1 ) ) * ( chiCoach.w < 0.5 ? smoothstep( 1.9, 0.5, vChiCoachP.y ) : 0.5 );
    float scuff = clamp( chiCoach.y * mark * where, 0.0, 1.0 );
    // Rubbed lacquer shows the grey of its ground coats and loses its shine.
    diffuseColor.rgb = mix( diffuseColor.rgb, diffuseColor.rgb * 0.55 + vec3( 0.045, 0.043, 0.04 ), scuff );
    chiCoachRough = dust * 0.55 + scuff * 0.3;
  }`;
const ROUGHNESS = `
  roughnessFactor = clamp( roughnessFactor + chiCoach.z * 0.32 + chiCoachRough, 0.04, 1.0 );`;
const ANCHORS = ['#include <color_fragment>', '#include <roughnessmap_fragment>'];

const patched = new WeakSet();
function patchMaterial(material, uniforms) {
  if (patched.has(material)) return;
  patched.add(material);
  const prior = material.onBeforeCompile;
  const hadKey = Object.prototype.hasOwnProperty.call(material, 'customProgramCacheKey');
  const priorKey = hadKey ? String(material.customProgramCacheKey())
    : (typeof prior === 'function' && prior !== THREE.Material.prototype.onBeforeCompile ? prior.toString() : '');
  material.onBeforeCompile = (shader, renderer) => {
    if (typeof prior === 'function') prior(shader, renderer);
    if (!ANCHORS.every(a => shader.fragmentShader.includes(a)) || !shader.vertexShader.includes('#include <begin_vertex>')) return;
    Object.assign(shader.uniforms, uniforms);
    shader.vertexShader = 'uniform mat4 chiCoachFrame;\nvarying vec3 vChiCoachP;\n'
      + shader.vertexShader.replace('#include <begin_vertex>', `#include <begin_vertex>${VERTEX}`);
    shader.fragmentShader = DECLARE + shader.fragmentShader
      .replace('#include <color_fragment>', `#include <color_fragment>${COLOR}`)
      .replace('#include <roughnessmap_fragment>', `#include <roughnessmap_fragment>${ROUGHNESS}`);
  };
  material.customProgramCacheKey = () => `${priorKey}|${KEY}`;
  material.needsUpdate = true;
}

const roleOf = name => ROLE_OF.find(([re]) => re.test(name ?? ''))?.[1] ?? null;
const wheelOf = node => { for (let n = node; n; n = n.parent) if (WHEELS.test(n.name)) return n; return null; };
const gearOf = node => { for (let n = node; n; n = n.parent) if (/^vehicle_(wheel_|steer_front|running_gear|team_pole)/.test(n.name) || n.name === 'hubcap') return true; return false; };

/**
 * Give a loaded vehicle (its parsed glTF scene, owned by this one assembly) the row's
 * finish. Every mesh takes its own material, so one coach's paint never reaches
 * another's. Returns { materials, dispose } — dispose restores and frees the copies.
 */
export function applyCoachwork(vehicle, finish, { wheelRadius_m = 0.6 } = {}) {
  if (!vehicle?.traverse) throw Error('coachwork: a loaded vehicle scene required');
  readFinish(finish);
  const seed = seedOffsets(finish.seed);
  const dust = new THREE.Color().setRGB(...(finish.dust_rgb ?? [0.12, 0.1, 0.078]), THREE.LinearSRGBColorSpace);
  vehicle.updateMatrixWorld(true);
  const toVehicle = new THREE.Matrix4().copy(vehicle.matrixWorld).invert();
  const made = [], restore = [];
  vehicle.traverse(node => {
    if (!node.isMesh || Array.isArray(node.material) || node.material?.visible === false) return;
    const role = roleOf(node.material.name);
    if (!role) return;
    const wheel = wheelOf(node), gear = gearOf(node);
    const material = node.material.clone();
    // Paint: the body's colours, or the running gear's where the part is the gear.
    const paint = role === 'timber' ? (gear ? finish.gear ?? finish.timber : finish.timber)
      : role === 'panels' ? finish.panels : role === 'quarter' ? finish.quarter ?? finish.panels
        : role === 'upholstery' ? finish.upholstery : role === 'trim' ? finish.trim : null;
    if (paint) material.color.setRGB(...paint, THREE.LinearSRGBColorSpace);
    if (role === 'trim' && finish.trim_metalness != null) material.metalness = finish.trim_metalness;
    // Marks: glass is left clean, upholstery inside is left unmarked, the rest carries the road.
    const mode = role === 'glass' || role === 'upholstery' ? 2 : wheel ? 1 : 0;
    const frame = new THREE.Matrix4();
    if (wheel) {
      // The wheel's own frame: its axle is x, so the tyre is round in y and z.
      wheel.updateMatrixWorld(true);
      frame.copy(wheel.matrixWorld).invert().multiply(node.matrixWorld);
    } else frame.copy(toVehicle).multiply(node.matrixWorld);
    const uniforms = {
      chiCoach: { value: new THREE.Vector4(finish.dust ?? 0, finish.scuffs ?? 0, 1 - (finish.gloss ?? 1), mode) },
      chiCoachSeed: { value: new THREE.Vector4(...seed, wheelRadius_m) },
      chiCoachDust: { value: dust.clone() },
      chiCoachFrame: { value: frame },
    };
    if (mode !== 2) patchMaterial(material, uniforms);
    material.userData = { ...material.userData, chicago4d_coachwork: { role, mode, seed: finish.seed } };
    restore.push([node, node.material]);
    node.material = material; made.push(material);
  });
  return {
    materials: made,
    dispose() {
      for (const [node, original] of restore) node.material = original;
      for (const m of made) m.dispose();
      made.length = 0; restore.length = 0;
    },
  };
}
