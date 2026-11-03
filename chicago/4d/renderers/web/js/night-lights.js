/**
 * T-3332 — THE TOWN BY NIGHT: lit windows and the lamps outside.
 *
 * Time of day (T-3331, time-of-day.js) darkens the town; this layer puts back the
 * light people made. Two parts, both priced for a phone:
 *
 *  1. WINDOWS. Every building's `glass` material (the archetypes' dark pane) is
 *     patched once at load to add an emissive glow: the era's lamp colour, a slow
 *     candle flicker, and lit or dark building by building. Which buildings are lit
 *     follows the clock: most in the evening, fewer as the hours go on, a few all
 *     night. By day the glow uniform is exactly 0, so the shipped frame is unchanged
 *     to the bit, and the patch adds no texture, attribute or draw.
 *  2. LAMPS. A short list of outdoor lights per scene (data/night_lights/<scene>.json)
 *     drawn as a flame sprite and a warm pool on the ground, both additive. No real
 *     three.js light is added: a point light recompiles every material in the scene
 *     and costs every fragment every frame, day or night; a sprite and a pool cost
 *     two small draws, and nothing at all while the group is hidden by day.
 *
 * What a scene's lights stand on, and what is ours, is in its data file and in
 * docs/LIBERTIES.md (L-night-lights-3332).
 */
import * as THREE from 'three';
import { captureHooks, registerPatch } from './batch-material.js';
import { onDaylight, minutesOf } from './time-of-day.js';

export const WINDOW_PATCH = 'night-windows-v1';

/** Shared by every patched pane, so one write relights the town. */
const WIN = {
  uWinGlow: { value: 0 },          // 0 by day; up to 1 once the sky is dark
  uWinShare: { value: 0 },         // the share of buildings lit at this hour
  uWinColor: { value: new THREE.Color(1.0, 0.55, 0.22) },
  uWinIntensity: { value: 1.0 },
  uWinTime: { value: 0 },
};

/** The scene's window table, set by createNightLights (null = no glow anywhere). */
let windowTable = null;
let lastClock = null;
let lastGrade = null;

/**
 * The share of buildings lit at minute `m` of the day, from a table of
 * [`HH:MM`, share] steps read as a step function round the clock.
 */
export function shareAt(table, m) {
  if (!Array.isArray(table) || !table.length) return 0;
  const steps = table.map(([t, s]) => [minutesOf(t) ?? 0, Number(s) || 0]).sort((a, b) => a[0] - b[0]);
  let share = steps[steps.length - 1][1];
  for (const [t, s] of steps) if (m >= t) share = s;
  return share;
}

/** How far the windows show: none while the day is bright, whole once it is dusk. */
export function windowGlowFor(grade) {
  if (!grade || (grade.sunK === 1 && grade.fillK === 1)) return 0;
  // The sky's fill share is the honest measure of how dark the street is.
  const t = Math.min(1, Math.max(0, (0.75 - grade.fillK) / 0.55));
  return t * t * (3 - 2 * t);
}

function refreshWindows() {
  const glow = windowTable ? windowGlowFor(lastGrade) : 0;
  WIN.uWinGlow.value = glow;
  WIN.uWinShare.value = glow > 0 ? shareAt(windowTable.share_by_hour, lastClock ?? 0) : 0;
}

onDaylight(({ grade, sunTime }) => {
  lastGrade = grade;
  lastClock = minutesOf(sunTime) ?? 0;
  refreshWindows();
});

const WINDOW_VERT_DECL = /* glsl */`
flat varying float vChiWinId;
`;
const WINDOW_VERT = /* glsl */`
#ifdef USE_BATCHING
  vChiWinId = float( getIndirectIndex( gl_DrawID ) );
#else
  vChiWinId = dot( modelMatrix[3].xz, vec2( 0.173, 0.291 ) );
#endif
`;
const WINDOW_FRAG_DECL = /* glsl */`
flat varying float vChiWinId;
uniform float uWinGlow;
uniform float uWinShare;
uniform vec3 uWinColor;
uniform float uWinIntensity;
uniform float uWinTime;
float chiWinHash( float n ) { return fract( sin( n * 12.9898 + 4.1414 ) * 43758.5453 ); }
`;
const WINDOW_FRAG = /* glsl */`
  if ( uWinGlow > 0.0 ) {
    float chiH = chiWinHash( vChiWinId );
    if ( chiH < uWinShare ) {
      // A candle's slow breathing, phased per building; one building is one light.
      float chiF = 0.86 + 0.08 * sin( uWinTime * 2.3 + chiH * 40.0 )
        + 0.06 * sin( uWinTime * 5.1 + chiH * 91.0 );
      float chiWarm = 0.8 + 0.4 * fract( chiH * 7.31 );
      totalEmissiveRadiance += uWinColor * ( uWinIntensity * uWinGlow * chiF * chiWarm );
    }
  }
`;

/**
 * Patch a building's glass to glow by night. Safe on a material another patch
 * (glass.js panes) already holds: it chains the prior hook and joins its key.
 */
export function patchNightWindows(material) {
  if (!material || material.userData.nightWindows) return material;
  const batchHooks = captureHooks(material);
  const priorKey = material.customProgramCacheKey === THREE.Material.prototype.customProgramCacheKey
    ? '' : material.customProgramCacheKey();
  const prior = material.onBeforeCompile;
  material.userData.nightWindows = WINDOW_PATCH;
  material.onBeforeCompile = (shader, renderer) => {
    prior?.call(material, shader, renderer);
    Object.assign(shader.uniforms, WIN);
    shader.vertexShader = WINDOW_VERT_DECL + shader.vertexShader
      .replace('#include <project_vertex>', '#include <project_vertex>\n' + WINDOW_VERT);
    shader.fragmentShader = WINDOW_FRAG_DECL + shader.fragmentShader
      .replace('#include <emissivemap_fragment>', '#include <emissivemap_fragment>\n' + WINDOW_FRAG);
  };
  material.customProgramCacheKey = () => `${priorKey}|${WINDOW_PATCH}`;
  registerPatch(material, batchHooks, WINDOW_PATCH, { patch: WINDOW_PATCH, priorKey });
  material.needsUpdate = true;
  return material;
}

// ---- the lamps outside ----------------------------------------------------------

function glowTexture(size = 64, inner = 0.0) {
  const c = document.createElement('canvas');
  c.width = c.height = size;
  const g = c.getContext('2d');
  const grad = g.createRadialGradient(size / 2, size / 2, size * inner, size / 2, size / 2, size / 2);
  grad.addColorStop(0, 'rgba(255,255,255,1)');
  grad.addColorStop(0.25, 'rgba(255,255,255,0.55)');
  grad.addColorStop(0.6, 'rgba(255,255,255,0.12)');
  grad.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = grad;
  g.fillRect(0, 0, size, size);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

/** Each kind's look: flame sprite size and brightness, and the pool it throws. */
const KINDS = {
  lantern: { flameM: 0.8, flame: 1.3, poolM: 4.5, pool: 0.14, flicker: 0.06 },
  fire: { flameM: 1.4, flame: 1.2, poolM: 7.0, pool: 0.2, flicker: 0.16 },
  torch: { flameM: 0.8, flame: 1.2, poolM: 5.0, pool: 0.16, flicker: 0.14 },
  // A lighthouse's lamps behind reflectors: a large steady glow high up, no pool.
  beacon: { flameM: 5.0, flame: 2.4, poolM: 0, pool: 0, flicker: 0.02 },
};

async function getJSON(url) {
  const res = await fetch(url, { cache: 'no-cache' });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`${res.status} ${res.statusText} — ${url}`);
  return res.json();
}

/**
 * Read the scene's night lights and build the lamps. Windows are switched on for the
 * scene here (their colour and hours); the glass itself is patched by buildings.js.
 *
 * @param {object} o
 * @param {string} o.dataBase  published data root
 * @param {string} o.sceneId
 * @param {object} o.terrain   for the ground under a lamp
 * @param {(id:string)=>({at:number[]}|null)} [o.anchor] a named anchor's place (a gate)
 * @param {string[]} [o.problems]
 */
export async function createNightLights({ dataBase, sceneId, terrain, anchor = () => null, problems = [] }) {
  const group = new THREE.Group();
  group.name = 'night-lights';
  group.visible = false;
  let data = null;
  try {
    // A scene that does not list the layer has no file to ask for (no 404 in the log).
    if (dataBase) data = await getJSON(`${dataBase}/night_lights/${sceneId}.json`);
  } catch (err) {
    problems.push(`night lights: ${err?.message || err}`);
  }
  windowTable = data?.windows ?? null;
  if (windowTable) {
    WIN.uWinColor.value.setRGB(...windowTable.colour_linear, THREE.LinearSRGBColorSpace);
    WIN.uWinIntensity.value = Number(windowTable.intensity) || 1;
  }
  refreshWindows();

  const flameTex = glowTexture(64, 0.0);
  const poolTex = glowTexture(64, 0.0);
  const lamps = [];
  const placed = [];
  for (const L of data?.lights ?? []) {
    const kind = KINDS[L.kind];
    if (!kind) { problems.push(`night lights: ${L.id} is of no known kind (${L.kind})`); continue; }
    let e = L.local_e; let n = L.local_n;
    if (L.at?.gate) {
      const a = anchor(L.at.gate);
      if (!a) { problems.push(`night lights: ${L.id} hangs at ${L.at.gate}, which this scene does not have`); continue; }
      e = a.at[0] + (L.at.offset_en?.[0] ?? 0);
      n = a.at[1] + (L.at.offset_en?.[1] ?? 0);
    }
    if (!Number.isFinite(e) || !Number.isFinite(n)) { problems.push(`night lights: ${L.id} has no place`); continue; }
    const ground = terrain?.surfaceHeight?.(e, n) ?? 0;
    const colour = new THREE.Color().setRGB(...(L.colour_linear ?? data.windows?.colour_linear ?? [1, 0.55, 0.22]),
      THREE.LinearSRGBColorSpace);
    const flameMat = new THREE.SpriteMaterial({
      map: flameTex, color: colour.clone().multiplyScalar(kind.flame), blending: THREE.AdditiveBlending,
      depthWrite: false, transparent: true, fog: true, toneMapped: true,
    });
    const flame = new THREE.Sprite(flameMat);
    flame.scale.setScalar(kind.flameM);
    flame.position.set(e, ground + (L.height_m ?? 1.8), -n);
    flame.name = `night-light:${L.id}`;
    // A kind with no pool (a beacon high up) throws none: one draw, not two.
    const poolMat = kind.pool > 0 ? new THREE.MeshBasicMaterial({
      map: poolTex, color: colour.clone().multiplyScalar(kind.pool), blending: THREE.AdditiveBlending,
      depthWrite: false, transparent: true, fog: true, polygonOffset: true, polygonOffsetFactor: -4,
    }) : null;
    group.add(flame);
    if (poolMat) {
      const pool = new THREE.Mesh(new THREE.PlaneGeometry(kind.poolM * 2, kind.poolM * 2), poolMat);
      pool.rotation.x = -Math.PI / 2;
      pool.position.set(e, ground + 0.06, -n);
      pool.name = `night-light-pool:${L.id}`;
      pool.renderOrder = 2;
      group.add(pool);
    }
    lamps.push({ L, kind, flameMat, poolMat, base: colour, phase: (lamps.length * 2.399) % 6.283 });
    placed.push({ id: L.id, kind: L.kind, e, n });
  }

  let lampK = 0;
  const unhook = onDaylight(({ grade }) => {
    lampK = windowGlowFor(grade);
    group.visible = lampK > 0 && lamps.length > 0;
  });
  let t = 0;
  return {
    group,
    lights: placed,
    get windowTable() { return windowTable; },
    get state() {
      return { glow: WIN.uWinGlow.value, share: WIN.uWinShare.value, lamps: lampK, shown: group.visible };
    },
    /** The flicker; does nothing while the lamps are out. */
    update(dt) {
      t += dt;
      WIN.uWinTime.value = t;
      if (!group.visible) return;
      for (const l of lamps) {
        const f = 1 - l.kind.flicker * (0.5 + 0.5 * Math.sin(t * 7.3 + l.phase) * Math.sin(t * 3.1 + l.phase * 2));
        l.flameMat.color.copy(l.base).multiplyScalar(l.kind.flame * f * lampK);
        l.poolMat?.color.copy(l.base).multiplyScalar(l.kind.pool * f * lampK);
      }
    },
    dispose() {
      unhook();
      flameTex.dispose(); poolTex.dispose();
      for (const l of lamps) { l.flameMat.dispose(); l.poolMat?.dispose(); }
      group.traverse((o) => o.geometry?.dispose?.());
    },
  };
}
