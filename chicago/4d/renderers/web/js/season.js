/**
 * T-2481 — the Season setting: summer (the scene's own day), spring, fall and
 * winter, for the ground, the trees and the sun. 1904 first; T-2864 offers it in
 * every year, and adds the woods and the prairie (patchFoliage below).
 *
 * A VIEWING CHOICE, NEVER A CLAIM. The scene is dated 1 July 1904 and that is what
 * it reconstructs. A season other than summer moves the sun to that season's date
 * and repaints the ground and the leaves the way such a day generally looks in
 * Chicago; no record of the district on those days stands behind it (liberty
 * L-season-view-2481).
 *
 * The ground layers (terrain.js, street-grid.js) carry the GLSL below in their own
 * programs, switched by the shared uniforms here, so changing the season is a few
 * uniform writes and never a recompile. Off (summer) the code returns the colour it
 * was given.
 */

import * as THREE from 'three';

export const SEASONS = ['summer', 'spring', 'fall', 'winter'];

/**
 * The day each season shows, as month-day in the scene's own year. Summer is the
 * scene's date. The others are chosen to agree with what the leaves are doing:
 * elms in first leaf in the last week of April, elms yellow in the third week of
 * October, and the winter solstice for the lowest sun of the year.
 */
const SEASON_DAY = { spring: '04-25', fall: '10-20', winter: '12-21' };

/** The date the sun is computed for, given the scene's own target date. */
export function seasonDate(season, targetDate) {
  const day = SEASON_DAY[season];
  if (!day || !targetDate) return targetDate;
  return `${String(targetDate).slice(0, 4)}-${day}`;
}

/** T-2864: the grown woods' crown in each season (tree-model.js leafCover and
 *  leafScale), the parkway elms' own (street-trees.js SEASON): spring just leafing,
 *  fall a thinner crown, winter bare limbs and twigs. */
export const SEASON_CROWN = Object.freeze({
  summer: {},
  spring: { leafCover: 0.55, leafScale: 0.45 },
  fall: { leafCover: 0.72, leafScale: 0.9 },
  winter: { leafCover: 0 },
});

/** What the street elms show in each season (street-trees.js modes). */
export const SEASON_TREE_MODE = { summer: 'summer', spring: 'spring', fall: 'fall', winter: 'winter' };

/**
 * One uniforms object shared by every ground material, as confidence.js shares its
 * view: flipping the season is four writes however many materials there are.
 *   uChiSnow    0..1 snow on the ground
 *   uChiGreen   a multiplier on the green of grass (spring's fresher sward)
 *   uChiBrown   0..1 the sward browned toward straw (fall)
 *   uChiLitter  0..1 fallen leaves on the grass (fall)
 */
export const seasonUniforms = {
  uChiSnow: { value: 0 },
  uChiGreen: { value: new THREE.Vector3(1, 1, 1) },
  uChiBrown: { value: 0 },
  uChiLitter: { value: 0 },
  // T-2864, the plants (patchFoliage): 0..1 each.
  //   uChiFresh  spring's first leaf, paler and yellower, and no July flower yet
  //   uChiTurn   fall's turned leaves, yellow to orange to oak russet by place
  //   uChiStraw  the sward and the forbs dead to straw (fall partly, winter all)
  //   uChiBare   winter's leafless sprays: twig grey-brown
  uChiFresh: { value: 0 },
  uChiTurn: { value: 0 },
  uChiStraw: { value: 0 },
  uChiBare: { value: 0 },
};

const LOOK = {
  summer: { snow: 0, green: [1, 1, 1], brown: 0, litter: 0, fresh: 0, turn: 0, straw: 0, bare: 0 },
  // A fresher, yellower-green young sward: more green, less red, a little less blue.
  spring: { snow: 0, green: [0.96, 1.2, 0.82], brown: 0, litter: 0, fresh: 1, turn: 0, straw: 0, bare: 0 },
  fall: { snow: 0, green: [1, 1, 1], brown: 0.55, litter: 1, fresh: 0, turn: 1, straw: 0.85, bare: 0 },
  winter: { snow: 1, green: [1, 1, 1], brown: 0.8, litter: 0, fresh: 0, turn: 0, straw: 1, bare: 1 },
};

/** Set the shared uniforms for a season. Returns the season actually applied. */
export function applySeasonLook(season) {
  const s = SEASONS.includes(season) ? season : 'summer';
  const l = LOOK[s];
  seasonUniforms.uChiSnow.value = l.snow;
  seasonUniforms.uChiGreen.value.set(...l.green);
  seasonUniforms.uChiBrown.value = l.brown;
  seasonUniforms.uChiLitter.value = l.litter;
  seasonUniforms.uChiFresh.value = l.fresh;
  seasonUniforms.uChiTurn.value = l.turn;
  seasonUniforms.uChiStraw.value = l.straw;
  seasonUniforms.uChiBare.value = l.bare;
  return s;
}

/** Install the shared uniforms on a shader (inside an onBeforeCompile). */
export function seasonShaderUniforms(shader) {
  Object.assign(shader.uniforms, seasonUniforms);
}

/** Declarations: the uniforms, a world-space value noise, and the function. */
export const SEASON_HEAD = /* glsl */`
uniform float uChiSnow;
uniform vec3 uChiGreen;
uniform float uChiBrown;
uniform float uChiLitter;
uniform float uChiFresh;
uniform float uChiTurn;
uniform float uChiStraw;
uniform float uChiBare;
float chiSeasonHash(vec2 p) {
  vec3 p3 = fract(vec3(p.xyx) * 0.1031);
  p3 += dot(p3, p3.yzx + 33.33);
  return fract((p3.x + p3.y) * p3.z);
}
float chiSeasonNoise(vec2 p) {
  vec2 i = floor(p); vec2 f = fract(p); vec2 u = f * f * (3.0 - 2.0 * f);
  return mix(mix(chiSeasonHash(i), chiSeasonHash(i + vec2(1.0, 0.0)), u.x),
             mix(chiSeasonHash(i + vec2(0.0, 1.0)), chiSeasonHash(i + vec2(1.0, 1.0)), u.x), u.y);
}
// c: the surface's linear albedo. xz: world metres. kind: how much snow the surface
// keeps and whether it is grass — 1 lawn and parkway, about 0.5 an alley, 0.3 a
// travelled roadway, 0.15 a swept walk. up: the surface normal's world y.
vec3 chiSeason(vec3 c, vec2 xz, float kind, float up) {
  float chiFlat = smoothstep(0.7, 0.9, up);
  float grass = step(0.75, kind) * chiFlat * clamp((c.g - max(c.r, c.b)) / max(c.g, 0.001) * 5.0, 0.0, 1.0);
  c = mix(c, c * uChiGreen, grass);
  float luma = dot(c, vec3(0.2126, 0.7152, 0.0722));
  c = mix(c, vec3(luma) * vec3(1.42, 1.06, 0.58), uChiBrown * grass);
  if (uChiLitter > 0.0 && kind > 0.75) {
    float lit = chiSeasonNoise(xz * 1.9) * 0.55 + chiSeasonNoise(xz * 7.3) * 0.45;
    float leaf = smoothstep(0.58, 0.66, lit) * uChiLitter * grass;
    vec3 leafC = mix(vec3(0.46, 0.30, 0.05), vec3(0.24, 0.12, 0.04), chiSeasonNoise(xz * 21.0));
    c = mix(c, leafC, leaf);
  }
  if (uChiSnow > 0.0) {
    float n = chiSeasonNoise(xz * 0.31) * 0.5 + chiSeasonNoise(xz * 1.7) * 0.3 + chiSeasonNoise(xz * 6.1) * 0.2;
    float cover = clamp(kind * 1.15 + (n - 0.5) * 0.9, 0.0, 1.0) * smoothstep(0.45, 0.8, up) * uChiSnow;
    // Trodden snow on what is travelled, clean snow where nobody walks; what
    // is left on a swept walk is the clean snow banked at its edges.
    vec3 snow = mix(vec3(0.36, 0.35, 0.34), vec3(0.80, 0.83, 0.88),
      max(smoothstep(0.2, 0.9, kind), 1.0 - smoothstep(0.15, 0.25, kind)));
    c = mix(c, snow, cover);
  }
  return c;
}
`;

/** For a layer without a world-position varying of its own: where the fragment is,
 *  and which way its surface faces. Inserted after `#include <begin_vertex>`. */
export const SEASON_VERTEX_DECL = 'varying vec2 vChiSeasonXZ;\nvarying float vChiSeasonUp;\n';
export const SEASON_VERTEX_ASSIGN = `
  {
    vec4 chiSeasonP = vec4(transformed, 1.0);
    #ifdef USE_BATCHING
      chiSeasonP = batchingMatrix * chiSeasonP;
    #endif
    #ifdef USE_INSTANCING
      chiSeasonP = instanceMatrix * chiSeasonP;
    #endif
    vChiSeasonXZ = (modelMatrix * chiSeasonP).xz;
    // transformedNormal is in view space; the view matrix's transpose turns it back.
    vChiSeasonUp = normalize((vec4(transformedNormal, 0.0) * viewMatrix).xyz).y;
  }
`;
export const SEASON_FRAGMENT_DECL = 'varying vec2 vChiSeasonXZ;\nvarying float vChiSeasonUp;\nuniform float uChiSeasonKind;\n';
/** After `#include <color_fragment>`, where the albedo is final. */
export const SEASON_FRAGMENT_APPLY = `
  diffuseColor.rgb = chiSeason(diffuseColor.rgb, vChiSeasonXZ, uChiSeasonKind, vChiSeasonUp);
`;

/**
 * Wrap a material that was built without the season code (the structures'
 * merged materials, whose lawns, steps and roofs are in the building GLBs): the
 * same function, after its albedo is final. Patched only when a season other
 * than summer is first chosen, so a summer visit compiles nothing new. The
 * program key extends the material's own, so materials that shared a program
 * still share one.
 */
const seasonPatched = new WeakSet();
const surfacePatchHooks = new WeakMap();
const materialHooks = m => [m.onBeforeCompile,m.onBeforeRender,m.customProgramCacheKey];
/** The season wrapper only adds varyings and changes albedo, never positions or
 * coverage. Recognize precisely that wrapper over the captured source hooks;
 * another shader mutation must still invalidate an opaque-surface proof. */
export function seasonPreservesSurface(material, before) {
  const patch=surfacePatchHooks.get(material);
  return !!patch && before.length===3
    && patch.before.every((fn,i)=>fn===before[i])
    && materialHooks(material).every((fn,i)=>fn===patch.after[i]);
}
export function patchSeason(material, kind = 1) {
  if (!material || seasonPatched.has(material)) return false;
  seasonPatched.add(material);
  const before=materialHooks(material);
  const prior = material.onBeforeCompile;
  const priorKey = Object.prototype.hasOwnProperty.call(material, 'customProgramCacheKey')
    ? String(material.customProgramCacheKey()) : String(prior);
  const seasonKind = { value: kind };
  material.onBeforeCompile = (shader, renderer) => {
    if (typeof prior === 'function') prior.call(material, shader, renderer);
    seasonShaderUniforms(shader);
    shader.uniforms.uChiSeasonKind = seasonKind;
    shader.vertexShader = SEASON_VERTEX_DECL + shader.vertexShader.replace(
      '#include <begin_vertex>', '#include <begin_vertex>' + SEASON_VERTEX_ASSIGN);
    shader.fragmentShader = SEASON_FRAGMENT_DECL + SEASON_HEAD + shader.fragmentShader.replace(
      '#include <color_fragment>', '#include <color_fragment>' + SEASON_FRAGMENT_APPLY);
  };
  material.customProgramCacheKey = () => `${priorKey}|chicago4d-season`;
  surfacePatchHooks.set(material,{before,after:materialHooks(material)});
  material.needsUpdate = true;
  return true;
}

/**
 * T-2864 — THE PLANTS' SEASON, for the years whose woods and prairie are drawn by
 * trees.js and flora.js (1812, 1835). A plant's albedo is moved by how green it
 * is, so bark, stems and the far band's haze keep their colour and only leaf and
 * blade turn. Roles:
 *   FOLIAGE.leaf   a tree's or shrub's leaves: fresh in spring, turned in fall by
 *                  place (yellow, orange, oak russet), and in winter the sprays
 *                  that stand for many twigs go twig grey-brown (an oak thicket
 *                  keeps its dead leaves into winter). The grown trees are
 *                  re-grown leafless for winter (trees.js setSeason).
 *   FOLIAGE.grass  the sward and its forbs: fresh in spring with no July flower,
 *                  tawny in fall, straw in winter, flowers gone to seed heads.
 *   FOLIAGE.far    the horizon band of woods: olive-russet in fall, the grey
 *                  violet of bare woods at a distance in winter.
 */
export const FOLIAGE = Object.freeze({ leaf: 0, grass: 1, far: 2 });
const FOLIAGE_HEAD = /* glsl */`
uniform float uChiFoliageRole;
vec3 chiFoliage(vec3 c, vec2 xz, float role) {
  float mx = max(c.r, max(c.g, c.b));
  float green = clamp((c.g - max(c.r, c.b)) / max(c.g, 0.001) * 5.0, 0.0, 1.0);
  float luma = dot(c, vec3(0.2126, 0.7152, 0.0722));
  float sat = (mx - min(c.r, min(c.g, c.b))) / max(mx, 0.001);
  float petal = (1.0 - green) * smoothstep(0.3, 0.55, sat) * step(0.5, role) * step(role, 1.5);
  // Spring: first leaf is paler and yellower; a flower of July is still leaf.
  c = mix(c, c * vec3(1.06, 1.16, 0.70) + vec3(0.010, 0.016, 0.0), green * uChiFresh);
  c = mix(c, vec3(luma) * vec3(0.78, 1.18, 0.62), petal * uChiFresh * 0.85);
  if (role < 0.5) {
    // Fall: which colour a crown turns is a matter of place (species and soil),
    // so the noise is coarse: a stand reads as one tree yellow, the next orange.
    float pick = chiSeasonNoise(xz * 0.045) * 0.7 + chiSeasonNoise(xz * 0.31) * 0.3;
    vec3 turned = pick < 0.38 ? vec3(0.58, 0.40, 0.06)
      : pick < 0.58 ? vec3(0.55, 0.22, 0.05)
      : pick < 0.72 ? vec3(0.32, 0.15, 0.06)
      : vec3(0.40, 0.36, 0.10);
    c = mix(c, turned * (0.55 + 1.6 * luma), green * uChiTurn);
    // Winter: what a spray of leaves stood for is a mass of twigs.
    c = mix(c, vec3(0.20, 0.17, 0.14) * (0.6 + 2.0 * luma), green * uChiBare);
  } else if (role < 1.5) {
    // The sward: tawny with russet patches in fall (bluestem turns), straw in winter.
    float rus = smoothstep(0.45, 0.75, chiSeasonNoise(xz * 0.21));
    vec3 tawny = mix(vec3(luma) * vec3(1.40, 1.02, 0.56), vec3(luma) * vec3(1.55, 0.86, 0.52), rus);
    vec3 straw = vec3(0.42, 0.36, 0.24) * (0.55 + 1.5 * luma);
    float dead = max(green, petal) * uChiStraw;
    c = mix(c, mix(tawny, straw, uChiBare), dead);
    c = mix(c, vec3(0.13, 0.09, 0.05), petal * uChiStraw * 0.8);
  } else {
    c = mix(c, vec3(luma) * vec3(1.25, 1.0, 0.70), green * uChiTurn * 0.8);
    c = mix(c, vec3(luma) * vec3(1.08, 0.98, 1.06), green * uChiBare * 0.9);
  }
  return c;
}
`;
/** Where the fragment is, for a material without a world position of its own: as
 *  SEASON_VERTEX_ASSIGN without the normal, which an unlit material (the far band)
 *  does not compute. */
const FOLIAGE_VERTEX_DECL = 'varying vec2 vChiSeasonXZ;\n';
const FOLIAGE_VERTEX_ASSIGN = `
  {
    vec4 chiSeasonP = vec4(transformed, 1.0);
    #ifdef USE_BATCHING
      chiSeasonP = batchingMatrix * chiSeasonP;
    #endif
    #ifdef USE_INSTANCING
      chiSeasonP = instanceMatrix * chiSeasonP;
    #endif
    vChiSeasonXZ = (modelMatrix * chiSeasonP).xz;
  }
`;
/** After `#include <color_fragment>`, where the albedo is final. */
const foliageApply = (xz) => `
  diffuseColor.rgb = chiFoliage(diffuseColor.rgb, ${xz}, uChiFoliageRole);
`;

/**
 * Wrap a plant material with chiFoliage, the way patchSeason wraps a building's:
 * only once a season other than summer is chosen, so summer compiles nothing new
 * and draws what it drew. `xz` names a world-position expression the material's
 * fragment shader already has (flora.js `vChiPW.xz`); without one, the season's
 * own varying is added.
 */
const foliagePatched = new WeakSet();
export function patchFoliage(material, role = FOLIAGE.leaf, { xz = null } = {}) {
  if (!material || foliagePatched.has(material)) return false;
  foliagePatched.add(material);
  const prior = material.onBeforeCompile;
  const priorKey = Object.prototype.hasOwnProperty.call(material, 'customProgramCacheKey')
    ? String(material.customProgramCacheKey()) : String(prior);
  const roleU = { value: role };
  const at = xz ?? 'vChiSeasonXZ';
  material.onBeforeCompile = (shader, renderer) => {
    if (typeof prior === 'function') prior.call(material, shader, renderer);
    seasonShaderUniforms(shader);
    shader.uniforms.uChiFoliageRole = roleU;
    if (!xz) {
      shader.vertexShader = FOLIAGE_VERTEX_DECL + shader.vertexShader.replace(
        '#include <begin_vertex>', '#include <begin_vertex>' + FOLIAGE_VERTEX_ASSIGN);
    }
    shader.fragmentShader = (xz ? '' : FOLIAGE_VERTEX_DECL)
      + SEASON_HEAD + FOLIAGE_HEAD + shader.fragmentShader.replace(
        '#include <color_fragment>', '#include <color_fragment>' + foliageApply(at));
  };
  material.customProgramCacheKey = () => `${priorKey}|chicago4d-foliage-${role}`;
  material.needsUpdate = true;
  return true;
}
